"""Generate backend/tests/sheet1_golden.json from the real parquet.

Sanity-gates computed values against known-correct numbers before writing.
Run once to mint the fixture; use check_sheet1_golden.py for ongoing regression checks.
"""
import sys, json
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

import pandas as pd
from build_analyst import _build_sheet1_data, filter_ry

PARQUET    = BACKEND / "test_model_cleaned.parquet"
OUT        = Path(__file__).resolve().parent / "sheet1_golden.json"
CURR_YEAR  = 2569
PREV_YEAR  = 2568
CURR_MONTH = 5

# Exact same preprocessing as main() in build_analyst.py for df_ry_all
df_raw = pd.read_parquet(str(PARQUET))
df_raw["จำนวนรถ"] = pd.to_numeric(df_raw["จำนวนรถ"], errors="coerce").fillna(0).astype(int)
df_raw["ปี"]      = pd.to_numeric(df_raw["ปี"],      errors="coerce").dropna().astype(int)
df_raw = df_raw.dropna(subset=["ปี"]).copy()
df_raw["ปี"]      = df_raw["ปี"].astype(int)

df_ry = filter_ry(df_raw)
data  = _build_sheet1_data(df_ry, CURR_YEAR, PREV_YEAR, CURR_MONTH)

# --- Sanity gate against known-correct values ---
failures = []

def chk_exact(pt, col, expected):
    val = data.get((pt, col))
    if val != expected:
        failures.append(f"  {pt}|{col}: expected {expected!r}, got {val!r}")

def chk_close(pt, col, expected, tol):
    val = data.get((pt, col))
    if val is None or abs(val - expected) >= tol:
        failures.append(f"  {pt}|{col}: expected ~{expected} (tol={tol}), got {val!r}")

chk_exact("grand", "W",  60018)
chk_exact("grand", "F",  53532)
chk_exact("grand", "AA", 306432)
chk_exact("grand", "H",  264427)
chk_exact("grand", "Q",  593551)
chk_close("grand", "Y",      0.246376,            1e-5)
chk_close("grand", "Z",      0.121161,            1e-5)
chk_close("grand", "AC",     0.158853,            1e-5)
chk_close("grand", "SEC_I",  264427 / 593551,     1e-9)

if failures:
    print("SANITY GATE FAILED — fixture not written:")
    for f in failures:
        print(f)
    sys.exit(1)

print("Sanity gate passed.")

# Serialize: (pt_key, col) -> "pt_key|col": value  (None -> null)
out_dict = {f"{pt}|{col}": val for (pt, col), val in sorted(data.items())}
OUT.write_text(json.dumps(out_dict, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Written: {OUT.relative_to(BACKEND.parent)} ({len(out_dict)} entries)")
