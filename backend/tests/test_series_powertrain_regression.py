"""Regression test for plans/reliable-series-powertrain.md, Step 3.

Proves the dominant-fuel-per-brand-bucket defect is gone: `enrich_fuel_type`
used to pick one "dominant" ชนิดเชื้อเพลิง per (ปี, เดือน, ประเภทรถ, จังหวัด,
ยี่ห้อรถ) bucket from the fuel source and stamp it onto every model row in
that bucket — including series the fuel source never actually observed with
that fuel. That function is now deleted; model Powertrain comes only from a
verified row in series_registry.csv, defaulting to N/A otherwise. The fuel
source data below is kept only to prove it has zero influence on model rows
now — MITSUBISHI/TRITON (a diesel pickup) must resolve to N/A, not inherit
some other Mitsubishi model's "เบนซิน-ไฟฟ้า" bucket fuel as HEV.

Uses the real, production-configured config/powertrain_map.csv and
config/brand_map.csv (same convention as test_canonicalization.py) so this
test tracks drift in the authoritative maps. Runs against an empty
series_registry (the current production state), matching the intermediate
state approved for release: every model series is N/A until reviewed.

Runs from any directory. Exits 0 on PASS, 1 on FAIL.
"""
import sys
from pathlib import Path
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

TESTS = Path(__file__).resolve().parent
BACKEND = TESTS.parent
sys.path.insert(0, str(BACKEND))

from build_cleaned import add_derived_columns, load_powertrain_map

powertrain_map = load_powertrain_map(str(BACKEND / "config" / "powertrain_map.csv"))
brand_csv_map = load_powertrain_map(str(BACKEND / "config" / "brand_map.csv"), "brand", "brand2")
merged_brand2_map = {k.upper(): v for k, v in brand_csv_map.items()}

failures = []

def run_tests():
    join_key_values = {
        "ปี": 2569,
        "เดือน": "กรกฎาคม",
        "ประเภทรถ": "รถกระบะ",
        "จังหวัด": "กรุงเทพมหานคร",
        "ยี่ห้อรถ": "MITSUBISHI",
    }

    # Model source: only TRITON registrations in this bucket. The model
    # source never records a fuel type of its own.
    df_model = pd.DataFrame([{**join_key_values, "รุ่นรถ": "TRITON", "จำนวนรถ": 100}])

    # Fuel source: same bucket, but the aggregate is dominated by some other
    # Mitsubishi vehicle's hybrid fuel, not TRITON's actual diesel fuel. Kept
    # here only to prove this data can no longer reach the model Powertrain.
    df_fuel = pd.DataFrame([
        {**join_key_values, "ชนิดเชื้อเพลิง": "ดีเซล", "จำนวนรถ": 80},
        {**join_key_values, "ชนิดเชื้อเพลิง": "เบนซิน-ไฟฟ้า", "จำนวนรถ": 200},
    ])

    maps = {
        "powertrain_map": powertrain_map,
        "merged_brand2_map": merged_brand2_map,
        "series_powertrain_map": {},  # empty registry == current production state
        "series_name_map": {},
        "unknown_fuels": set(),
    }
    df_model, _ = add_derived_columns(df_model, df_fuel.copy(), maps)

    triton_row = df_model[df_model["รุ่นรถ"] == "TRITON"].iloc[0]
    powertrain = triton_row["Powertrain"]
    if powertrain != "N/A":
        failures.append(
            f"MITSUBISHI/TRITON emitted as {powertrain!r}, expected 'N/A' — "
            "dominant-fuel-per-brand-bucket must not decide series powertrain"
        )
    if "ชนิดเชื้อเพลิง" in df_model.columns:
        failures.append("model row still carries an inherited ชนิดเชื้อเพลิง column")


if __name__ == "__main__":
    run_tests()
    if failures:
        print(f"FAIL — {len(failures)} issue(s) in series-powertrain regression test:")
        for f in failures:
            print(f)
        sys.exit(1)
    print("PASS — All series-powertrain regression tests passed successfully.")
