"""Validate public release data files.

This script ensures that all required public release data files are present
and that their reporting periods (year and month) match exactly.
"""

import json
import sys
from pathlib import Path

# Set stdout to UTF-8
sys.stdout.reconfigure(encoding="utf-8")

# Define paths
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR.parent / "frontend" / "public" / "data"

REQUIRED_FILES = {
    "dashboard_summary.json": DATA_DIR / "dashboard_summary.json",
    "dashboard_models.json": DATA_DIR / "dashboard_models.json",
    "analyst_data.json": DATA_DIR / "analyst_data.json",
    "cleaned_data_manifest.json": DATA_DIR / "cleaned_data_manifest.json",
    "manual_report.json": DATA_DIR / "manual_report.json",
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

def validate_model_powertrain_annotations(models_data: dict):
    """Ensure model rows preserve model-table Powertrain, not only fuel-derived PT."""
    missing = []
    model_count = 0
    powertrains = set()

    for brand in models_data.get("brand_model_tree", []):
        brand_name = brand.get("brand", "<unknown brand>")
        for model in brand.get("models", []):
            model_count += 1
            model_powertrain = model.get("powertrain")
            if not model_powertrain:
                missing.append(f"{brand_name} / {model.get('name', '<unknown model>')}")
            else:
                powertrains.add(str(model_powertrain))

    if missing:
        examples = ", ".join(missing[:10])
        raise ValueError(
            "dashboard_models.json model rows are missing model-level powertrain "
            f"annotations. Examples: {examples}"
        )

    if model_count == 0:
        raise ValueError("dashboard_models.json contains no model rows")

    print(
        f"Model powertrain annotations present on {model_count:,} model rows "
        f"({', '.join(sorted(powertrains))})."
    )

def validate_public_release():
    print("=== Validating Public Release Data ===")
    
    # 1. Check file existence
    missing_files = []
    for name, path in REQUIRED_FILES.items():
        if not path.exists():
            missing_files.append(name)
            print(f"Error: Missing required file: {name} (path: {path})")
    
    if missing_files:
        print("\nVALIDATION FAILED: One or more required data files are missing.")
        sys.exit(1)
        
    print("All required data files are present.")
    
    # 2. Load and parse files
    periods = {}
    
    # Load dashboard_summary.json
    try:
        with open(REQUIRED_FILES["dashboard_summary.json"], "r", encoding="utf-8") as f:
            data = json.load(f)
            meta = data.get("meta", {})
            year = meta.get("latest_year")
            month_str = meta.get("latest_month")
            generated_at = meta.get("generated_at")
            month_num = MONTH_MAP.get(month_str)
            if year is None or month_num is None:
                raise ValueError(f"Missing latest_year or valid latest_month in meta. Found year={year}, month={month_str}")
            if not generated_at:
                raise ValueError("Missing meta.generated_at")
            periods["dashboard_summary.json"] = {
                "year": int(year),
                "month_num": month_num,
                "display": f"{month_str} {year}"
            }
    except Exception as e:
        print(f"Error reading dashboard_summary.json: {e}")
        sys.exit(1)

    # Load dashboard_models.json
    try:
        with open(REQUIRED_FILES["dashboard_models.json"], "r", encoding="utf-8") as f:
            data = json.load(f)
            meta = data.get("meta", {})
            year = meta.get("latest_year")
            month_str = meta.get("latest_month")
            month_num = MONTH_MAP.get(month_str)
            if year is None or month_num is None:
                raise ValueError(f"Missing latest_year or valid latest_month in meta. Found year={year}, month={month_str}")
            periods["dashboard_models.json"] = {
                "year": int(year),
                "month_num": month_num,
                "display": f"{month_str} {year}"
            }
            validate_model_powertrain_annotations(data)
    except Exception as e:
        print(f"Error reading dashboard_models.json: {e}")
        sys.exit(1)

    # Load analyst_data.json
    try:
        with open(REQUIRED_FILES["analyst_data.json"], "r", encoding="utf-8") as f:
            data = json.load(f)
            meta = data.get("meta", {})
            year = meta.get("current_year")
            month_num = meta.get("current_month_num")
            if year is None or month_num is None:
                raise ValueError(f"Missing current_year or current_month_num in meta. Found year={year}, month_num={month_num}")
            periods["analyst_data.json"] = {
                "year": int(year),
                "month_num": int(month_num),
                "display": f"Month#{month_num} {year}"
            }
    except Exception as e:
        print(f"Error reading analyst_data.json: {e}")
        sys.exit(1)

    # Load cleaned_data_manifest.json
    try:
        with open(REQUIRED_FILES["cleaned_data_manifest.json"], "r", encoding="utf-8") as f:
            data = json.load(f)
            generated_at = data.get("generated_at")
            year = data.get("latest_year")
            month_str = data.get("latest_month")
            month_num = MONTH_MAP.get(month_str)
            if year is None or month_num is None:
                raise ValueError(f"Missing latest_year or valid latest_month. Found year={year}, month={month_str}")
            if not generated_at:
                raise ValueError("Missing generated_at")
            periods["cleaned_data_manifest.json"] = {
                "year": int(year),
                "month_num": month_num,
                "display": f"{month_str} {year}"
            }
    except Exception as e:
        print(f"Error reading cleaned_data_manifest.json: {e}")
        print("Tip: Make sure you run the updated export_dashboard.py to generate manifest with reporting period metadata.")
        sys.exit(1)

    # Load manual_report.json
    try:
        with open(REQUIRED_FILES["manual_report.json"], "r", encoding="utf-8") as f:
            data = json.load(f)
            meta = data.get("meta", {})
            year = meta.get("latest_year")
            month_str = meta.get("latest_month")
            month_num = MONTH_MAP.get(month_str)
            if year is None or month_num is None:
                raise ValueError(f"Missing latest_year or valid latest_month in meta. Found year={year}, month={month_str}")
            for required_key in ("reporting_period", "default_vehicle_types", "source_files", "generated_at"):
                if not meta.get(required_key):
                    raise ValueError(f"manual_report.json meta is missing '{required_key}'")
            sheets = data.get("sheets", {})
            missing_sheets = [s for s in REQUIRED_REPORT_SHEETS if s not in sheets or not sheets[s]]
            if missing_sheets:
                raise ValueError(f"manual_report.json is missing required sheet sections: {missing_sheets}")
            periods["manual_report.json"] = {
                "year": int(year),
                "month_num": month_num,
                "display": f"{month_str} {year}",
            }
            print(
                f"manual_report.json has all {len(REQUIRED_REPORT_SHEETS)} sheet sections "
                f"(period {meta.get('reporting_period')})."
            )
    except Exception as e:
        print(f"Error reading manual_report.json: {e}")
        print("Tip: run export_manual_report.py to regenerate the canonical manual report.")
        sys.exit(1)

    # 3. Compare reporting periods
    print("\nReporting periods found:")
    for name, p in periods.items():
        print(f"  - {name}: {p['display']} (Year: {p['year']}, Month: {p['month_num']})")

    mismatch = False
    ref_file = list(periods.keys())[0]
    ref_period = periods[ref_file]

    for name, p in periods.items():
        if p["year"] != ref_period["year"] or p["month_num"] != ref_period["month_num"]:
            print(f"\nMismatch detected: {name} does not match {ref_file}!")
            mismatch = True

    if mismatch:
        print("\nVALIDATION FAILED: Reporting periods do not match across all files.")
        sys.exit(1)

    print("\nVALIDATION PASSED: All reporting periods match exactly.")
    sys.exit(0)

if __name__ == "__main__":
    validate_public_release()
