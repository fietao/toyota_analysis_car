"""Regression checks for Sheet 1.

Goal 1: recompute _build_sheet1_data, compare every entry against sheet1_golden.json.
Goal 2: write a fresh standalone workbook to a temp path, assert text labels.

Run from any directory. Exits 0 on PASS, 1 on FAIL.
"""
import sys, json, math, tempfile
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

TESTS   = Path(__file__).resolve().parent
BACKEND = TESTS.parent
sys.path.insert(0, str(BACKEND))

import pandas as pd
from openpyxl import load_workbook
from build_analyst import _build_sheet1_data, filter_ry, write_sheet1_standalone

PARQUET    = BACKEND / "test_model_cleaned.parquet"
GOLDEN     = TESTS / "sheet1_golden.json"
CURR_YEAR  = 2569
PREV_YEAR  = 2568
CURR_MONTH = 5

failures = []

def fail(msg):
    failures.append(msg)


# ── shared load (same preprocessing as main() in build_analyst.py) ───────────
df_raw = pd.read_parquet(str(PARQUET))
df_raw["จำนวนรถ"] = pd.to_numeric(df_raw["จำนวนรถ"], errors="coerce").fillna(0).astype(int)
df_raw["ปี"]      = pd.to_numeric(df_raw["ปี"],      errors="coerce").dropna().astype(int)
df_raw = df_raw.dropna(subset=["ปี"]).copy()
df_raw["ปี"]      = df_raw["ปี"].astype(int)

df_ry = filter_ry(df_raw)
data  = _build_sheet1_data(df_ry, CURR_YEAR, PREV_YEAR, CURR_MONTH)


# ── Goal 1: numeric fixture comparison ───────────────────────────────────────
golden = json.loads(GOLDEN.read_text(encoding="utf-8"))

for key_str, expected in golden.items():
    pt, col = key_str.split("|", 1)
    actual  = data.get((pt, col))
    if expected is None and actual is None:
        continue
    if expected is None or actual is None:
        fail(f"  {key_str}: expected {expected!r}, got {actual!r}")
        continue
    if isinstance(expected, int):
        if actual != expected:
            fail(f"  {key_str}: expected {expected}, got {actual}")
    else:
        if not math.isclose(actual, expected, abs_tol=1e-12, rel_tol=0):
            fail(f"  {key_str}: expected {expected}, got {actual} (diff {abs(actual - expected):.3e})")

current_keys = {f"{pt}|{col}" for (pt, col) in data}
for k in sorted(current_keys - set(golden)):
    fail(f"  EXTRA KEY in computed (not in fixture): {k}")
for k in sorted(set(golden) - current_keys):
    fail(f"  MISSING KEY in computed (was in fixture): {k}")


# ── Goal 2: standalone label assertions ───────────────────────────────────────
tmp_path = Path(tempfile.gettempdir()) / "sheet1_standalone_labelcheck.xlsx"
write_sheet1_standalone(tmp_path, df_ry, CURR_YEAR, PREV_YEAR, CURR_MONTH)
wb = load_workbook(str(tmp_path))
ws = wb["1.Reg by Powertrain"]
wb.close()
tmp_path.unlink(missing_ok=True)

def chk_label(cell_ref, expected):
    actual = ws[cell_ref].value
    if actual != expected:
        fail(f"  label {cell_ref}: expected {expected!r}, got {actual!r}")

chk_label("A1",  "Registration by Powertrain")
chk_label("A3",  "ประเภทรถ : รย.1,2,3,6,9,10,11")
chk_label("A8",  "Grand Total")
chk_label("A9",  "ICE")
chk_label("A10", "BEV")
chk_label("A11", "HEV")
chk_label("A12", "PHEV")
chk_label("H14", "Grand Total")
chk_label("H15", "ICE")
chk_label("H16", "BEV")
chk_label("H17", "HEV")
chk_label("H18", "PHEV")
chk_label("F5",  "2568")
chk_label("S5",  "2569")
chk_label("F7",  "Units")
chk_label("G7",  "Share")


# ── Result ────────────────────────────────────────────────────────────────────
if failures:
    print(f"FAIL — {len(failures)} issue(s):")
    for f in failures:
        print(f)
    sys.exit(1)

print(f"PASS — {len(golden)} numeric entries match; all labels correct.")
