"""Tests for report sheet 7-8 BEV inclusion.

Sheets 7-8 include a model row only when (Brand2, raw model) is explicitly approved as
BEV (review_status=approved, candidate_powertrain=BEV) in
backend/config/model_powertrain_review.csv (model_map.approved_bev_keys()) — never
inferred from Powertrain, brand fuel totals, or model-name guessing.
"""
import csv
import os
import sys
import tempfile
from pathlib import Path
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

TESTS = Path(__file__).resolve().parent
BACKEND = TESTS.parent
sys.path.insert(0, str(BACKEND))

from export_manual_report import sheet_bev_by_model, sheet_model_top_rank
import model_map

failures = []


def _write_review(rows):
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    tmp = Path(path)
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=model_map.REVIEW_HEADERS)
        w.writeheader()
        w.writerows(rows)
    return tmp


def _with_whitelist(rows, fn):
    tmp = _write_review(rows)
    orig_path = model_map.MODEL_POWERTRAIN_REVIEW_PATH
    model_map.MODEL_POWERTRAIN_REVIEW_PATH = tmp
    try:
        return fn()
    finally:
        model_map.MODEL_POWERTRAIN_REVIEW_PATH = orig_path
        tmp.unlink()


def test_sheets7_8_only_include_whitelisted_models():
    df = pd.DataFrame([
        {"ยี่ห้อรถ2": "TESLA", "รุ่นรถ": "MODEL 3", "รุ่นรถ2": "MODEL 3", "ปี": 2024, "เดือน": "Jan", "จำนวนรถ": 10},
        {"ยี่ห้อรถ2": "TESLA", "รุ่นรถ": "MODEL Y", "รุ่นรถ2": "MODEL Y", "ปี": 2024, "เดือน": "Jan", "จำนวนรถ": 5},
    ])
    whitelist = [{
        "brand2": "TESLA", "raw_model": "MODEL 3", "model2": "MODEL 3",
        "candidate_powertrain": "BEV", "review_status": "approved",
        "evidence": "brochure.pdf", "reviewer": "jet", "reviewed_at": "2026-07-22",
        "notes": "",
    }]

    res7 = _with_whitelist(whitelist, lambda: sheet_bev_by_model(df, 2024, 2023, 0))
    res8 = _with_whitelist(whitelist, lambda: sheet_model_top_rank(df, 2024, 2023, 0))

    models7 = {r["key"] for r in res7 if r.get("level") == "model"}
    if models7 != {"MODEL 3"}:
        failures.append(f"Sheet 7 should contain only the whitelisted model, got {models7}")

    models8 = {r["model"] for r in res8[1:]}  # [0] is Grand Total
    if models8 != {"MODEL 3"}:
        failures.append(f"Sheet 8 should contain only the whitelisted model, got {models8}")


def test_sheets7_8_empty_when_whitelist_is_empty():
    df = pd.DataFrame([
        {"ยี่ห้อรถ2": "TOYOTA", "รุ่นรถ": "CAMRY", "รุ่นรถ2": "CAMRY", "ปี": 2024, "เดือน": "Jan", "จำนวนรถ": 10},
        {"ยี่ห้อรถ2": "HONDA", "รุ่นรถ": "ACCORD", "รุ่นรถ2": "ACCORD", "ปี": 2024, "เดือน": "Jan", "จำนวนรถ": 5},
    ])

    res7 = _with_whitelist([], lambda: sheet_bev_by_model(df, 2024, 2023, 0))
    res8 = _with_whitelist([], lambda: sheet_model_top_rank(df, 2024, 2023, 0))

    if len(res7) > 0:
        failures.append(f"Sheet 7 should be empty with no whitelist rows, got {len(res7)} rows")
    if len(res8) > 0:
        failures.append(f"Sheet 8 should be empty with no whitelist rows, got {len(res8)} rows")


def test_sheets7_8_correct_totals():
    df = pd.DataFrame([
        {"ยี่ห้อรถ2": "TESLA", "รุ่นรถ": "MODEL 3", "รุ่นรถ2": "MODEL 3", "ปี": 2024, "เดือน": "Jan", "จำนวนรถ": 10},
        {"ยี่ห้อรถ2": "TESLA", "รุ่นรถ": "MODEL 3", "รุ่นรถ2": "MODEL 3", "ปี": 2024, "เดือน": "Jan", "จำนวนรถ": 5},
        # Non-whitelisted model for the same brand must not contribute to the total.
        {"ยี่ห้อรถ2": "TESLA", "รุ่นรถ": "MODEL Y", "รุ่นรถ2": "MODEL Y", "ปี": 2024, "เดือน": "Jan", "จำนวนรถ": 100},
    ])
    whitelist = [{
        "brand2": "TESLA", "raw_model": "MODEL 3", "model2": "MODEL 3",
        "candidate_powertrain": "BEV", "review_status": "approved",
        "evidence": "brochure.pdf", "reviewer": "jet", "reviewed_at": "2026-07-22",
        "notes": "",
    }]

    res7 = _with_whitelist(whitelist, lambda: sheet_bev_by_model(df, 2024, 2023, 0))

    if res7[0]["curr_ytd"] != 15:
        failures.append(f"Sheet 7 total should be 15, got {res7[0]['curr_ytd']}")


if __name__ == "__main__":
    test_sheets7_8_only_include_whitelisted_models()
    test_sheets7_8_empty_when_whitelist_is_empty()
    test_sheets7_8_correct_totals()

    if failures:
        print(f"FAIL — {len(failures)} issue(s) in sheet 7-8 inclusion tests:")
        for f in failures:
            print(f)
        sys.exit(1)
    print("PASS — All sheet 7-8 inclusion tests passed successfully.")
