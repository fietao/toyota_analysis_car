"""Tests for plans/reliable-series-powertrain.md, Step 3 (source grain separation).

Proves:
  (a) model and fuel registration totals each reconcile independently against
      the real raw DLT files — add_derived_columns must not drop, duplicate,
      or cross-contaminate rows between the two source grains;
  (b) with an empty series_registry (current production state), every model
      row's Powertrain is 'N/A' and no model row carries a ชนิดเชื้อเพลิง column;
  (c) a verified series_registry row does flow through to the matching model
      row's Powertrain, proving the lookup mechanism itself works.

No pytest — matches the existing test_*.py convention. Runs from any
directory. Exits 0 on PASS, 1 on FAIL.
"""
import sys
from pathlib import Path
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

TESTS = Path(__file__).resolve().parent
BACKEND = TESTS.parent
sys.path.insert(0, str(BACKEND))

from build_cleaned import (
    RAW1_PATTERN, RAW2_PATTERN, find_file, read_dlt_file, add_derived_columns,
    load_powertrain_map,
)
from series_registry import normalize_key

powertrain_map = load_powertrain_map(str(BACKEND / "config" / "powertrain_map.csv"))
brand_csv_map = load_powertrain_map(str(BACKEND / "config" / "brand_map.csv"), "brand", "brand2")
merged_brand2_map = {k.upper(): v for k, v in brand_csv_map.items()}

failures = []


def base_maps(series_powertrain_map):
    return {
        "powertrain_map": powertrain_map,
        "merged_brand2_map": merged_brand2_map,
        "series_powertrain_map": series_powertrain_map,
        "series_name_map": {},
        "unknown_fuels": set(),
    }


def test_real_raw_totals_reconcile():
    raw1_file = find_file(RAW1_PATTERN, "fuel raw data")
    raw2_file = find_file(RAW2_PATTERN, "model raw data")
    df_fuel_raw = read_dlt_file(raw1_file)
    df_model_raw = read_dlt_file(raw2_file)

    raw_model_total = int(df_model_raw["จำนวนรถ"].sum())
    raw_fuel_total = int(df_fuel_raw["จำนวนรถ"].sum())

    df_model, df_fuel = add_derived_columns(
        df_model_raw.copy(), df_fuel_raw.copy(), base_maps({}),
    )

    model_total = int(df_model["จำนวนรถ"].sum())
    fuel_total = int(df_fuel["จำนวนรถ"].sum())

    if model_total != raw_model_total:
        failures.append(
            f"model total reconciliation: raw={raw_model_total:,} vs derived={model_total:,}"
        )
    if fuel_total != raw_fuel_total:
        failures.append(
            f"fuel total reconciliation: raw={raw_fuel_total:,} vs derived={fuel_total:,}"
        )

    if "ชนิดเชื้อเพลิง" in df_model.columns:
        failures.append("real model rows still carry an inherited ชนิดเชื้อเพลิง column")

    # Registry is currently empty in production, so every model row must be N/A.
    non_na = set(df_model["Powertrain"].dropna().unique()) - {"N/A"}
    if non_na:
        failures.append(
            f"model rows resolved to non-N/A powertrain with an empty registry: {sorted(non_na)}"
        )


def test_empty_registry_defaults_to_na():
    df_model = pd.DataFrame([
        {"ยี่ห้อรถ": "TOYOTA", "รุ่นรถ": "COROLLA", "จำนวนรถ": 5},
        {"ยี่ห้อรถ": "HONDA", "รุ่นรถ": "CIVIC", "จำนวนรถ": 3},
    ])
    df_fuel = pd.DataFrame([{"ยี่ห้อรถ": "TOYOTA", "ชนิดเชื้อเพลิง": "เบนซิน", "จำนวนรถ": 5}])

    df_model, _ = add_derived_columns(df_model, df_fuel, base_maps({}))

    if not (df_model["Powertrain"] == "N/A").all():
        failures.append(f"empty registry: expected all N/A, got {df_model['Powertrain'].tolist()}")
    if "ชนิดเชื้อเพลิง" in df_model.columns:
        failures.append("empty registry: model rows carry a ชนิดเชื้อเพลิง column")


def test_verified_registry_row_flows_through():
    df_model = pd.DataFrame([
        {"ยี่ห้อรถ": "MITSUBISHI", "รุ่นรถ": "TRITON", "จำนวนรถ": 100},
        {"ยี่ห้อรถ": "MITSUBISHI", "รุ่นรถ": "ATTRAGE", "จำนวนรถ": 10},
    ])
    df_fuel = pd.DataFrame([{"ยี่ห้อรถ": "MITSUBISHI", "ชนิดเชื้อเพลิง": "ดีเซล", "จำนวนรถ": 100}])

    series_powertrain_map = {normalize_key("MITSUBISHI", "TRITON"): "ICE"}
    df_model, _ = add_derived_columns(df_model, df_fuel, base_maps(series_powertrain_map))

    triton_pt = df_model.loc[df_model["รุ่นรถ"] == "TRITON", "Powertrain"].iloc[0]
    attrage_pt = df_model.loc[df_model["รุ่นรถ"] == "ATTRAGE", "Powertrain"].iloc[0]
    if triton_pt != "ICE":
        failures.append(f"verified registry row: expected TRITON -> ICE, got {triton_pt!r}")
    if attrage_pt != "N/A":
        failures.append(f"verified registry row: unverified ATTRAGE should stay N/A, got {attrage_pt!r}")


if __name__ == "__main__":
    test_real_raw_totals_reconcile()
    test_empty_registry_defaults_to_na()
    test_verified_registry_row_flows_through()
    if failures:
        print(f"FAIL — {len(failures)} issue(s) in source-grain-separation tests:")
        for f in failures:
            print(f)
        sys.exit(1)
    print("PASS — All source-grain-separation tests passed successfully.")
