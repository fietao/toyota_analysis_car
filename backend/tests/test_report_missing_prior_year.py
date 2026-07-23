"""Regression test for Slice 4: a report year with no prior-year data (e.g. 2564 vs
2563) must carry null prior-year fields and null ranks, never a fabricated zero or a
rank computed against an all-zero baseline.
"""
import sys
from pathlib import Path
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

TESTS = Path(__file__).resolve().parent
BACKEND = TESTS.parent
sys.path.insert(0, str(BACKEND))

from export_manual_report import sheet_brand

failures = []


def _fuel_rows():
    return pd.DataFrame([
        {"ยี่ห้อรถ2": "TOYOTA", "PT": "ICE", "ปี": 2564, "เดือน": "Jan", "จำนวนรถ": 100},
        {"ยี่ห้อรถ2": "TOYOTA", "PT": "ICE", "ปี": 2564, "เดือน": "Feb", "จำนวนรถ": 50},
        {"ยี่ห้อรถ2": "HONDA", "PT": "ICE", "ปี": 2564, "เดือน": "Jan", "จำนวนรถ": 10},
    ])


def test_has_prev_year_false_nulls_every_prior_year_field():
    rows = sheet_brand(_fuel_rows(), 2564, 2563, 1, has_prev_year=False)
    grand = rows[0]
    if grand["prev_total"] is not None or grand["prev_ytd"] is not None:
        failures.append(f"Grand Total prev_total/prev_ytd should be null, got {grand['prev_total']}/{grand['prev_ytd']}")
    if any(m is not None for m in grand["prev_months"]):
        failures.append(f"Grand Total prev_months should be all-null, got {grand['prev_months']}")

    detail = next(r for r in rows if r["key"] == "TOYOTA")
    if detail["prev_total"] is not None or detail["prev_rank"] is not None:
        failures.append(f"TOYOTA prev_total/prev_rank should be null, got {detail['prev_total']}/{detail['prev_rank']}")
    if detail["rank_diff"] is not None:
        failures.append(f"TOYOTA rank_diff should be null when prev_rank is unavailable, got {detail['rank_diff']}")
    if detail["curr_rank"] != 1:
        failures.append(f"TOYOTA curr_rank should still rank on curr_ytd alone, got {detail['curr_rank']}")
    if detail["growth_vs_same_month_prev_year"] is not None or detail["growth_vs_prev_ytd"] is not None:
        failures.append("growth-vs-prev-year fields should be null, not computed against a fabricated zero")


if __name__ == "__main__":
    test_has_prev_year_false_nulls_every_prior_year_field()
    if failures:
        print(f"FAIL — {len(failures)} issue(s) in missing-prior-year report test:")
        for f in failures:
            print(f)
        sys.exit(1)
    print("PASS — missing-prior-year report fields are null, not fabricated.")
