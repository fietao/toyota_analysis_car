"""Direct-run integration check for the model review boundary.

Human-approved model Powertrain lives in model_powertrain_review.csv and controls
Sheets 7-8 only. It must never enrich the general model-grain parquet.
"""
import csv
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

TESTS = Path(__file__).resolve().parent
BACKEND = TESTS.parent
sys.path.insert(0, str(BACKEND))

import model_map
from build_cleaned import add_derived_columns
from export_manual_report import bev_model_report_slice


def run_tests():
    failures = []
    raw_model = "MG4 ELECTRIC"
    key = model_map.normalize_key("MG", raw_model)
    maps = {
        "powertrain_map": {"ไฟฟ้า": "BEV"},
        "merged_brand2_map": {"MG": "MG"},
        "model_name_map": {key: "MG4 Electric"},
        "unknown_fuels": set(),
    }
    df_model = pd.DataFrame([
        {"ยี่ห้อรถ": "MG", "รุ่นรถ": raw_model, "จำนวนรถ": 20},
        {"ยี่ห้อรถ": "MG", "รุ่นรถ": "MG ZS", "จำนวนรถ": 8},
    ])
    df_fuel = pd.DataFrame([
        {"ยี่ห้อรถ": "MG", "ชนิดเชื้อเพลิง": "ไฟฟ้า", "จำนวนรถ": 20},
    ])

    cleaned_model, cleaned_fuel = add_derived_columns(df_model, df_fuel, maps)
    forbidden = {"ชนิดเชื้อเพลิง", "Powertrain", "include_in_bev_model_report"}
    leaked = forbidden.intersection(cleaned_model.columns)
    if leaked:
        failures.append(f"model grain contains forbidden columns: {sorted(leaked)}")
    if cleaned_fuel.iloc[0]["Powertrain"] != "BEV":
        failures.append("fuel grain did not derive BEV from the fuel map")
    if cleaned_model.iloc[0]["รุ่นรถ2"] != "MG4 Electric":
        failures.append("model_map.csv alias was not applied to รุ่นรถ2")

    with tempfile.TemporaryDirectory() as tmp:
        review_path = Path(tmp) / "model_powertrain_review.csv"
        with review_path.open("w", encoding="utf-8", newline="") as handle:
            writer = csv.DictWriter(handle, fieldnames=model_map.REVIEW_HEADERS)
            writer.writeheader()
            writer.writerow({
                "brand2": "MG", "raw_model": raw_model, "model2": "MG4 Electric",
                "candidate_powertrain": "BEV", "review_status": "approved",
                "evidence": "MG specification", "reviewer": "admin",
                "reviewed_at": "2026-07-22", "notes": "",
            })

        original_path = model_map.MODEL_POWERTRAIN_REVIEW_PATH
        model_map.MODEL_POWERTRAIN_REVIEW_PATH = review_path
        try:
            included = bev_model_report_slice(cleaned_model)
        finally:
            model_map.MODEL_POWERTRAIN_REVIEW_PATH = original_path

    if list(included["รุ่นรถ"]) != [raw_model]:
        failures.append("approved BEV review did not select exactly the reviewed raw model")

    return failures


if __name__ == "__main__":
    failures = run_tests()
    if failures:
        print(f"FAIL - {len(failures)} model review integration issue(s):")
        for failure in failures:
            print(failure)
        sys.exit(1)
    print("PASS - model review stays separate from model grain and controls Sheets 7-8.")
