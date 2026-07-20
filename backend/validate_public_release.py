"""Release gates for source-grain separation and public static artifacts."""
import json
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

from build_cleaned import RAW1_PATTERN, RAW2_PATTERN, find_file, read_dlt_file
from schema import validate_fuel, validate_model
from series_registry import ALLOWED_POWERTRAIN, load_registry, normalize_key, verified_powertrain_map

sys.stdout.reconfigure(encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "frontend" / "public" / "data"
MODEL_PARQUET = BASE_DIR / "test_model_cleaned.parquet"
FUEL_PARQUET = BASE_DIR / "test_fuel_cleaned.parquet"
REQUIRED_FILES = {
    name: DATA_DIR / name for name in (
        "dashboard_summary.json", "dashboard_models.json", "analyst_data.json",
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


def _bool_series(series):
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    return series.astype(str).str.strip().str.lower().isin({"1", "true", "yes", "y"})


def validate_cleaned_source_grains(model: pd.DataFrame, fuel: pd.DataFrame, registry_path=None):
    """Validate facts before any JSON is eligible for release."""
    validate_model(model)
    validate_fuel(fuel)
    # Fuel grain maps raw ชนิดเชื้อเพลิง strings through powertrain_map.csv; an unmapped/unknown
    # fuel string legitimately produces OTH (build_cleaned.py). Model-series classification is
    # never allowed to fall back to OTH — it must be a registry-verified PT or N/A.
    allowed_by_grain = {"model": ALLOWED_POWERTRAIN, "fuel": ALLOWED_POWERTRAIN | {"OTH"}}
    for label, frame in (("model", model), ("fuel", fuel)):
        values = set(frame["Powertrain"].fillna("N/A").astype(str))
        invalid = sorted(values - allowed_by_grain[label])
        if invalid:
            raise ValueError(f"{label} grain has invalid Powertrain values: {invalid}")

    verified = verified_powertrain_map(registry_path) if registry_path else verified_powertrain_map()
    expected_by_key = verified
    keys = [normalize_key(brand, series) for brand, series in zip(model["ยี่ห้อรถ2"], model["รุ่นรถ"])]
    expected = pd.Series((expected_by_key.get(key, "N/A") for key in keys), index=model.index)
    actual = model["Powertrain"].fillna("N/A").astype(str)
    mismatch = actual.ne(expected)
    if mismatch.any():
        sample = model.loc[mismatch, ["ยี่ห้อรถ2", "รุ่นรถ", "รุ่นรถ2", "Powertrain"]].head(5)
        raise ValueError(
            f"model grain contains {int(mismatch.sum()):,} non-registry Powertrain row(s); "
            f"examples={sample.to_dict('records')}"
        )

    if "include_in_bev_model_report" not in model.columns:
        raise ValueError("model grain is missing include_in_bev_model_report")
    included = _bool_series(model["include_in_bev_model_report"])
    should_include = actual.eq("BEV")
    if not included.equals(should_include):
        raise ValueError("include_in_bev_model_report must be true exactly when verified Powertrain is BEV")

    # Segmenting a series by registry PT must preserve every source unit, including N/A.
    base = model.groupby(["ยี่ห้อรถ2", "รุ่นรถ2"], dropna=False)["จำนวนรถ"].sum().sort_index()
    segmented = (
        model.groupby(["ยี่ห้อรถ2", "รุ่นรถ2", "Powertrain"], dropna=False)["จำนวนรถ"]
        .sum().groupby(level=[0, 1]).sum().sort_index()
    )
    if not base.equals(segmented):
        raise ValueError("series Powertrain segments do not reconcile to source series totals")
    return {
        "model_rows": len(model), "fuel_rows": len(fuel),
        "model_units": int(model["จำนวนรถ"].sum()),
        "fuel_units": int(fuel["จำนวนรถ"].sum()),
        "verified_mappings": len(verified),
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


def validate_public_model_tree(models_data: dict, registry_rows: list[dict]):
    """Validate brand -> canonical series -> registry-backed Powertrain segments."""
    nodes = models_data.get("brand_model_tree", [])
    brands = [str(node.get("brand", "")) for node in nodes]
    duplicates = sorted({brand for brand in brands if brands.count(brand) > 1})
    if duplicates:
        raise ValueError(f"Deep Dive must contain one node per brand; duplicates: {duplicates[:10]}")

    approved = {
        (normalize_key(row["canonical_brand"], row["canonical_series"]), row["powertrain"])
        for row in registry_rows if row["review_status"] == "verified"
    }
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

            for powertrain in powertrains:
                if powertrain not in ALLOWED_POWERTRAIN:
                    raise ValueError(f"public model has invalid Powertrain: {brand.get('brand')} / {series.get('name')} / {powertrain}")
                if powertrain != "N/A":
                    key = normalize_key(brand.get("brand"), series.get("name"))
                    if (key, powertrain) not in approved:
                        raise ValueError(f"public model is not registry-approved: {brand.get('brand')} / {series.get('name')} / {powertrain}")
    if not series_count:
        raise ValueError("dashboard_models.json contains no model rows")
    return series_count


def validate_bev_report_sheets(sheets: dict, registry_rows: list[dict]):
    approved = {
        normalize_key(row["canonical_brand"], row["canonical_series"])
        for row in registry_rows
        if row["review_status"] == "verified" and row["powertrain"] == "BEV"
    }
    observed = []
    for row in sheets["sheet7_bev_by_model"]:
        if row.get("level") == "model":
            observed.append(normalize_key(row.get("brand") or row.get("group"), row.get("key")))
    for row in sheets["sheet8_model_top_rank"]:
        if row.get("brand") and row.get("model"):
            observed.append(normalize_key(row["brand"], row["model"]))
    unapproved = sorted(set(observed) - approved)
    if unapproved:
        raise ValueError(f"Sheets 7-8 contain non-verified BEV series: {unapproved[:10]}")
    if approved and not observed:
        raise ValueError("Sheets 7-8 are empty despite verified BEV registry rows")
    return len(observed)


def _period(name, data):
    if name == "analyst_data.json":
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
        f"fuel={grain['fuel_rows']:,} rows/{grain['fuel_units']:,} units; "
        f"verified series mappings={grain['verified_mappings']:,}."
    )

    payloads = {name: json.loads(path.read_text(encoding="utf-8")) for name, path in REQUIRED_FILES.items()}
    periods = {name: _period(name, data) for name, data in payloads.items()}
    if len(set(periods.values())) != 1:
        raise ValueError(f"reporting periods do not match: {periods}")

    registry = load_registry()
    model_count = validate_public_model_tree(payloads["dashboard_models.json"], registry)
    report = payloads["manual_report.json"]
    sheets = report.get("sheets", {})
    missing_sheets = [sheet for sheet in REQUIRED_REPORT_SHEETS if sheet not in sheets]
    if missing_sheets:
        raise ValueError(f"manual_report.json is missing sheet keys: {missing_sheets}")
    for sheet in [s for s in REQUIRED_REPORT_SHEETS if s not in {"sheet7_bev_by_model", "sheet8_model_top_rank"}]:
        if not sheets[sheet]:
            raise ValueError(f"manual_report.json has empty fuel-derived section: {sheet}")

    bev_rows = validate_bev_report_sheets(sheets, registry)

    period = next(iter(periods.values()))
    print(f"Public tree valid: {model_count:,} model nodes; {bev_rows:,} verified BEV report rows. Period={period[1]}/{period[0]}.")
    print("VALIDATION PASSED: source grains, registry mappings, report sections, and periods are release-safe.")


if __name__ == "__main__":
    try:
        validate_public_release()
    except Exception as exc:
        print(f"VALIDATION FAILED: {exc}")
        sys.exit(1)
