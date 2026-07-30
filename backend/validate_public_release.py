"""Release gates for source-grain separation and public static artifacts."""
import json
import os
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

from build_cleaned import RAW1_PATTERN, RAW2_PATTERN, find_file, read_dlt_file
from model_map import approved_bev_model_keys, normalize_key
from schema import validate_fuel, validate_model

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = Path(os.environ.get("PUBLIC_DATA_DIR") or (BASE_DIR.parent / "frontend" / "public" / "data"))
MODEL_PARQUET = BASE_DIR / "test_model_cleaned.parquet"
FUEL_PARQUET = BASE_DIR / "test_fuel_cleaned.parquet"
REQUIRED_FILES = {
    name: DATA_DIR / name for name in (
        "dashboard_summary.json", "dashboard_models.json", "analyst_data.json", "analyst_province_data.json",
        "cleaned_data_manifest.json", "manual_report.json",
    )
}
REQUIRED_REPORT_SHEETS = [
    "sheet1_powertrain", "sheet2_brand_all", "sheet3_brand_ice", "sheet4_brand_bev",
    "sheet5_brand_hev", "sheet6_brand_phev", "sheet7_bev_by_model",
    "sheet8_model_top_rank", "sheet9_by_province",
]
MONTH_MAP = {
    "Jan": 1, "Feb": 2, "Mar": 3, "Apr": 4, "May": 5, "Jun": 6,
    "Jul": 7, "Aug": 8, "Sep": 9, "Oct": 10, "Nov": 11, "Dec": 12,
}
ALLOWED_FUEL_POWERTRAIN = {"ICE", "HEV", "PHEV", "BEV", "N/A", "OTH"}
BEV_CANDIDATES_FILE = DATA_DIR / "new_bev_candidates.json"
BEV_CANDIDATE_REASON_CODES = {"approved_family_match", "approved_model_match", "electric_name_marker"}
BEV_CANDIDATE_CONFIDENCE = {"high", "medium"}


def validate_cleaned_source_grains(model: pd.DataFrame, fuel: pd.DataFrame):
    """Validate facts before any JSON is eligible for release."""
    validate_model(model)
    validate_fuel(fuel)
    # Fuel grain maps raw ชนิดเชื้อเพลิง strings through powertrain_map.csv; an
    # unmapped/unknown fuel string legitimately produces OTH. Model grain is checked
    # by validate_model() and must not carry Powertrain at all.
    fuel_values = set(fuel["Powertrain"].fillna("N/A").astype(str))
    invalid = sorted(fuel_values - ALLOWED_FUEL_POWERTRAIN)
    if invalid:
        raise ValueError(f"fuel grain has invalid Powertrain values: {invalid}")

    return {
        "model_rows": len(model), "fuel_rows": len(fuel),
        "model_units": int(model["จำนวนรถ"].sum()),
        "fuel_units": int(fuel["จำนวนรถ"].sum()),
    }


def _monthly_cells(monthly: dict) -> Counter:
    cells = Counter()
    for vehicle_type, provinces in monthly.items():
        for province, years in provinces.items():
            for year, values in years.items():
                if not isinstance(values, list) or len(values) != 12:
                    raise ValueError(f"public model monthly values must contain 12 months: {vehicle_type}/{province}/{year}")
                for month, units in enumerate(values):
                    cells[(vehicle_type, province, str(year), month)] += int(units or 0)
    return cells


def _sum_monthly(nodes: list[dict]) -> Counter:
    total = Counter()
    for node in nodes:
        total.update(_monthly_cells(node.get("monthly", {})))
    return total


def validate_public_model_tree(models_data: dict):
    """Validate brand -> canonical series with model-grain N/A segments."""
    nodes = models_data.get("brand_model_tree", [])
    brands = [str(node.get("brand", "")) for node in nodes]
    duplicates = sorted({brand for brand in brands if brands.count(brand) > 1})
    if duplicates:
        raise ValueError(f"Deep Dive must contain one node per brand; duplicates: {duplicates[:10]}")

    series_count = 0
    for brand in nodes:
        series_nodes = brand.get("models", [])
        series_names = [str(series.get("name", "")) for series in series_nodes]
        if len(series_names) != len(set(series_names)):
            raise ValueError(f"Deep Dive brand contains duplicate canonical series: {brand.get('brand')}")
        if _monthly_cells(brand.get("monthly", {})) != _sum_monthly(series_nodes):
            raise ValueError(f"public brand series do not reconcile: {brand.get('brand')}")

        for series in series_nodes:
            series_count += 1
            segments = series.get("segments", [])
            powertrains = [str(segment.get("powertrain") or "N/A") for segment in segments]
            if not segments or len(powertrains) != len(set(powertrains)):
                raise ValueError(f"public series must contain unique Powertrain segments: {brand.get('brand')} / {series.get('name')}")
            if _monthly_cells(series.get("monthly", {})) != _sum_monthly(segments):
                raise ValueError(f"public series segments do not reconcile: {brand.get('brand')} / {series.get('name')}")

            if powertrains != ["N/A"]:
                raise ValueError(
                    f"public model must have only an N/A Powertrain segment: "
                    f"{brand.get('brand')} / {series.get('name')} / {powertrains}"
                )
    if not series_count:
        raise ValueError("dashboard_models.json contains no model rows")
    return series_count


def validate_bev_report_sheets(sheets: dict, approved=None):
    """Validate Sheets 7-8 against approved canonical BEV model keys."""
    approved = approved_bev_model_keys() if approved is None else approved
    observed = []
    for row in sheets["sheet7_bev_by_model"]:
        if row.get("level") == "model":
            observed.append(normalize_key(row.get("brand") or row.get("group"), row.get("key")))
    for row in sheets["sheet8_model_top_rank"]:
        if row.get("brand") and row.get("model"):
            observed.append(normalize_key(row["brand"], row["model"]))
    unapproved = sorted(set(observed) - approved)
    if unapproved:
        raise ValueError(f"Sheets 7-8 contain non-approved BEV models: {unapproved[:10]}")
    if approved and not observed:
        raise ValueError("Sheets 7-8 are empty despite approved BEV review rows")
    return len(observed)


def validate_bev_candidates_watchlist(payload: dict, canonical_period: tuple):
    """Validate new_bev_candidates.json's schema and reporting period.

    Candidate-only artifact: never required (missing/absent is fine — the caller only
    invokes this when the file exists), and its candidate_count must never gate release;
    only a malformed shape or a period mismatch does.
    """
    meta = payload.get("meta", {})
    for field in ("year", "month", "generated_at", "candidate_count", "total_units"):
        if field not in meta:
            raise ValueError(f"new_bev_candidates.json meta missing required field: {field}")
    if not isinstance(meta["year"], int) or not isinstance(meta["month"], int):
        raise ValueError(f"new_bev_candidates.json meta.year/month must be integers: {meta}")
    if (meta["year"], meta["month"]) != canonical_period:
        raise ValueError(
            f"new_bev_candidates.json period {(meta['year'], meta['month'])} does not match "
            f"the canonical release period {canonical_period}"
        )

    candidates = payload.get("candidates", [])
    if not isinstance(candidates, list):
        raise ValueError("new_bev_candidates.json 'candidates' must be a list")
    if meta["candidate_count"] != len(candidates):
        raise ValueError(
            f"new_bev_candidates.json candidate_count ({meta['candidate_count']}) "
            f"!= len(candidates) ({len(candidates)})"
        )
    total_units = sum(c.get("units", 0) for c in candidates)
    if meta["total_units"] != total_units:
        raise ValueError(
            f"new_bev_candidates.json total_units ({meta['total_units']}) != sum(units) ({total_units})"
        )

    required_fields = {"brand", "raw_model", "model", "units", "confidence", "reason_code", "reason", "review_status"}
    for c in candidates:
        missing = required_fields - set(c)
        if missing:
            raise ValueError(f"new_bev_candidates.json candidate missing fields: {missing}")
        if c["reason_code"] not in BEV_CANDIDATE_REASON_CODES:
            raise ValueError(f"new_bev_candidates.json candidate has invalid reason_code: {c['reason_code']!r}")
        if c["confidence"] not in BEV_CANDIDATE_CONFIDENCE:
            raise ValueError(f"new_bev_candidates.json candidate has invalid confidence: {c['confidence']!r}")
        if c["review_status"] != "pending":
            raise ValueError(
                f"new_bev_candidates.json candidate review_status must be 'pending' "
                f"(never auto-approved): {c['review_status']!r}"
            )
    return len(candidates)


def validate_analyst_views(analyst_data: dict):
    """Model views cannot expose fuel-derived Powertrain filters."""
    data = analyst_data.get("data", {})
    model_powertrains = set(data.get("model", {}))
    if model_powertrains != {"ALL"}:
        raise ValueError(f"analyst model views must contain only ALL, got {sorted(model_powertrains)}")

    expected_brand = {"ALL", "ICE", "BEV", "HEV", "PHEV"}
    brand_powertrains = set(data.get("brand", {}))
    if brand_powertrains != expected_brand:
        raise ValueError(f"analyst brand views have invalid Powertrain keys: {sorted(brand_powertrains)}")


def validate_analyst_province_views(province_data: dict):
    """Province analyst payload is compact monthly facts, not pre-rendered tables."""
    facts = province_data.get("facts", {})
    brand = facts.get("brand", [])
    model = facts.get("model", [])
    if not brand or not model:
        raise ValueError("analyst_province_data.json must contain brand and model facts")
    for name, rows, required in (
        ("brand", brand, {"p", "b", "y", "mo", "v", "pt", "u"}),
        ("model", model, {"p", "b", "m", "y", "mo", "v", "u"}),
    ):
        missing = [required - set(row) for row in rows[:100] if required - set(row)]
        if missing:
            raise ValueError(f"analyst province {name} facts missing keys: {missing[0]}")


def _period(name, data):
    if name in {"analyst_data.json", "analyst_province_data.json"}:
        meta = data.get("meta", {})
        return int(meta["current_year"]), int(meta["current_month_num"])
    meta = data.get("meta", data)
    return int(meta["latest_year"]), MONTH_MAP[meta["latest_month"]]


def validate_public_release():
    print("=== Validating Public Release Data ===")
    missing = [str(path) for path in [MODEL_PARQUET, FUEL_PARQUET, *REQUIRED_FILES.values()] if not path.exists()]
    if missing:
        raise ValueError(f"missing required release files: {missing}")

    model = pd.read_parquet(MODEL_PARQUET)
    fuel = pd.read_parquet(FUEL_PARQUET)
    grain = validate_cleaned_source_grains(model, fuel)
    raw_fuel = read_dlt_file(find_file(RAW1_PATTERN, "fuel raw data"))
    raw_model = read_dlt_file(find_file(RAW2_PATTERN, "model raw data"))
    raw_model_units = int(raw_model["จำนวนรถ"].sum())
    raw_fuel_units = int(raw_fuel["จำนวนรถ"].sum())
    if grain["model_units"] != raw_model_units:
        raise ValueError(f"model source total mismatch: raw={raw_model_units:,}, cleaned={grain['model_units']:,}")
    if grain["fuel_units"] != raw_fuel_units:
        raise ValueError(f"fuel source total mismatch: raw={raw_fuel_units:,}, cleaned={grain['fuel_units']:,}")
    print(
        f"Source grains valid: model={grain['model_rows']:,} rows/{grain['model_units']:,} units; "
        f"fuel={grain['fuel_rows']:,} rows/{grain['fuel_units']:,} units."
    )

    payloads = {name: json.loads(path.read_text(encoding="utf-8")) for name, path in REQUIRED_FILES.items()}
    periods = {name: _period(name, data) for name, data in payloads.items()}
    if len(set(periods.values())) != 1:
        raise ValueError(f"reporting periods do not match: {periods}")

    validate_analyst_views(payloads["analyst_data.json"])
    validate_analyst_province_views(payloads["analyst_province_data.json"])
    model_count = validate_public_model_tree(payloads["dashboard_models.json"])
    report = payloads["manual_report.json"]
    sheets = report.get("sheets", {})
    missing_sheets = [sheet for sheet in REQUIRED_REPORT_SHEETS if sheet not in sheets]
    if missing_sheets:
        raise ValueError(f"manual_report.json is missing sheet keys: {missing_sheets}")
    for sheet in [s for s in REQUIRED_REPORT_SHEETS if s not in {"sheet7_bev_by_model", "sheet8_model_top_rank"}]:
        if not sheets[sheet]:
            raise ValueError(f"manual_report.json has empty fuel-derived section: {sheet}")

    bev_rows = validate_bev_report_sheets(sheets)

    period = next(iter(periods.values()))

    # Candidate-only watchlist: never required (a missing/never-generated file is fine —
    # BEV_CANDIDATES_FILE is not in REQUIRED_FILES), but if present its schema and period
    # must reconcile with the release. Candidate presence itself never fails the release.
    if BEV_CANDIDATES_FILE.exists():
        watchlist = json.loads(BEV_CANDIDATES_FILE.read_text(encoding="utf-8"))
        candidate_count = validate_bev_candidates_watchlist(watchlist, period)
        print(f"BEV watchlist valid: {candidate_count} candidate(s) for period {period[1]}/{period[0]}.")

    print(f"Public tree valid: {model_count:,} model nodes; {bev_rows:,} approved BEV report rows. Period={period[1]}/{period[0]}.")
    print("VALIDATION PASSED: source grains, reviewed BEV report rows, report sections, and periods are release-safe.")


if __name__ == "__main__":
    try:
        validate_public_release()
    except Exception as exc:
        print(f"VALIDATION FAILED: {exc}")
        sys.exit(1)
