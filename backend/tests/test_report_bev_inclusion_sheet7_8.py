"""Tests for report sheet 7-8 BEV inclusion (Step 6C)."""
import sys
from pathlib import Path
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

TESTS = Path(__file__).resolve().parent
BACKEND = TESTS.parent
sys.path.insert(0, str(BACKEND))

from export_manual_report import (
    sheet_bev_by_model,
    sheet_model_top_rank,
    BEV_MODEL_REPORT_COL
)

failures = []

def test_sheets7_8_require_agreement_and_bev_powertrain():
    # DataFrame that simulates different conditions
    df = pd.DataFrame([
        # Row 1: Powertrain == 'BEV', include == True (Valid)
        {"ยี่ห้อรถ2": "TESLA", "รุ่นรถ2": "MODEL 3", "Powertrain": "BEV", BEV_MODEL_REPORT_COL: True, "ปี": 2024, "เดือน": "Jan", "จำนวนรถ": 10},
        # Row 2: Powertrain == 'BEV', include == False (Conflict)
        {"ยี่ห้อรถ2": "TESLA", "รุ่นรถ2": "MODEL Y", "Powertrain": "BEV", BEV_MODEL_REPORT_COL: False, "ปี": 2024, "เดือน": "Jan", "จำนวนรถ": 5},
    ])
    
    try:
        sheet_bev_by_model(df, 2024, 2023, 0)
        failures.append("Expected ValueError when Powertrain and include_in_bev_model_report disagree, but it passed.")
    except ValueError as e:
        if "agree exactly with" not in str(e).lower() and "must agree" not in str(e).lower():
            failures.append(f"Expected agreement error message, got: {e}")

def test_sheets7_8_empty_when_no_bev_rows():
    df = pd.DataFrame([
        {"ยี่ห้อรถ2": "TOYOTA", "รุ่นรถ2": "CAMRY", "Powertrain": "ICE", BEV_MODEL_REPORT_COL: False, "ปี": 2024, "เดือน": "Jan", "จำนวนรถ": 10},
        {"ยี่ห้อรถ2": "HONDA", "รุ่นรถ2": "ACCORD", "Powertrain": "HEV", BEV_MODEL_REPORT_COL: False, "ปี": 2024, "เดือน": "Jan", "จำนวนรถ": 5},
    ])
    
    res7 = sheet_bev_by_model(df, 2024, 2023, 0)
    res8 = sheet_model_top_rank(df, 2024, 2023, 0)
    
    if len(res7) > 0:
        failures.append(f"Sheet 7 should be empty, got {len(res7)} rows")
    if len(res8) > 0:
        failures.append(f"Sheet 8 should be empty, got {len(res8)} rows")

def test_sheets7_8_correct_totals():
    df = pd.DataFrame([
        # Included BEV
        {"ยี่ห้อรถ2": "TESLA", "รุ่นรถ2": "MODEL 3", "Powertrain": "BEV", BEV_MODEL_REPORT_COL: True, "ปี": 2024, "เดือน": "Jan", "จำนวนรถ": 10},
        # Another Included BEV
        {"ยี่ห้อรถ2": "TESLA", "รุ่นรถ2": "MODEL 3", "Powertrain": "BEV", BEV_MODEL_REPORT_COL: True, "ปี": 2024, "เดือน": "Jan", "จำนวนรถ": 5},
        # Excluded N/A row for same brand
        {"ยี่ห้อรถ2": "TESLA", "รุ่นรถ2": "UNKNOWN", "Powertrain": "N/A", BEV_MODEL_REPORT_COL: False, "ปี": 2024, "เดือน": "Jan", "จำนวนรถ": 100},
    ])
    
    res7 = sheet_bev_by_model(df, 2024, 2023, 0)
    
    # Grand total should be 15
    if res7[0]["curr_ytd"] != 15:
        failures.append(f"Sheet 7 total should be 15, got {res7[0]['curr_ytd']}")


if __name__ == "__main__":
    test_sheets7_8_require_agreement_and_bev_powertrain()
    test_sheets7_8_empty_when_no_bev_rows()
    test_sheets7_8_correct_totals()
    
    if failures:
        print(f"FAIL — {len(failures)} issue(s) in sheet 7-8 inclusion tests:")
        for f in failures:
            print(f)
        sys.exit(1)
    print("PASS — All sheet 7-8 inclusion tests passed successfully.")
