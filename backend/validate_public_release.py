"""Release gates for source-grain separation and public static artifacts."""
import json
import os
import sys
from pathlib import Path

import pandas as pd

from build_cleaned import RAW1_PATTERN, RAW2_PATTERN, find_file, read_dlt_file
from release_contracts import (
    ALLOWED_FUEL_POWERTRAIN,
    BEV_CANDIDATE_CONFIDENCE,
    BEV_CANDIDATE_REASON_CODES,
    MONTH_MAP,
    REQUIRED_REPORT_SHEETS,
    _monthly_cells,
    _sum_monthly,
    validate_analyst_province_views,
    validate_analyst_views,
    validate_bev_candidates_watchlist,
    validate_bev_report_sheets,
    validate_cleaned_source_grains,
    validate_public_model_tree,
)

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
BEV_CANDIDATES_FILE = DATA_DIR / "new_bev_candidates.json"


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
