"""Tests for CSV-first source-grain separation (model-grain powertrain removal).

Proves:
  (a) model and fuel registration totals each reconcile independently against
      the real raw DLT files — add_derived_columns must not drop, duplicate,
      or cross-contaminate rows between the two source grains;
  (b) model rows carry NO Powertrain column (ever) and NO ชนิดเชื้อเพลิง column;
  (c) fuel rows DO carry Powertrain (from ชนิดเชื้อเพลิง).

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
    load_powertrain_map, rolling_merge, reapply_canonical_maps,
)
from model_map import normalize_key
from schema import validate_model

powertrain_map = load_powertrain_map(str(BACKEND / "config" / "powertrain_map.csv"))
brand_csv_map = load_powertrain_map(str(BACKEND / "config" / "brand_map.csv"), "brand", "brand2")
merged_brand2_map = {k.upper(): v for k, v in brand_csv_map.items()}

failures = []


def base_maps():
    return {
        "powertrain_map": powertrain_map,
        "merged_brand2_map": merged_brand2_map,
        "model_name_map": {},
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
        df_model_raw.copy(), df_fuel_raw.copy(), base_maps(),
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

    # Model grain must never carry fuel-type or powertrain columns
    if "ชนิดเชื้อเพลิง" in df_model.columns:
        failures.append("model rows carry a ชนิดเชื้อเพลิง column (fuel-only)")
    if "Powertrain" in df_model.columns:
        failures.append("model rows carry a Powertrain column (must be fuel-only)")


def test_model_grain_never_has_powertrain():
    """Model rows must never carry Powertrain, even with mapping present."""
    df_model = pd.DataFrame([
        {"ยี่ห้อรถ": "TOYOTA", "รุ่นรถ": "COROLLA", "จำนวนรถ": 5},
        {"ยี่ห้อรถ": "HONDA", "รุ่นรถ": "CIVIC", "จำนวนรถ": 3},
    ])
    df_fuel = pd.DataFrame([{"ยี่ห้อรถ": "TOYOTA", "ชนิดเชื้อเพลิง": "เบนซิน", "จำนวนรถ": 5}])

    df_model, _ = add_derived_columns(df_model, df_fuel, base_maps())

    if "Powertrain" in df_model.columns:
        failures.append(f"model grain should never have Powertrain column")
    if "ชนิดเชื้อเพลิง" in df_model.columns:
        failures.append("model grain: model rows carry a ชนิดเชื้อเพลิง column")


def test_fuel_grain_gets_powertrain():
    """Fuel rows get Powertrain from ชนิดเชื้อเพลิง mapping."""
    df_model = pd.DataFrame([
        {"ยี่ห้อรถ": "MITSUBISHI", "รุ่นรถ": "TRITON", "จำนวนรถ": 100},
    ])
    df_fuel = pd.DataFrame([
        {"ยี่ห้อรถ": "MITSUBISHI", "ชนิดเชื้อเพลิง": "ดีเซล", "จำนวนรถ": 100},
        {"ยี่ห้อรถ": "MITSUBISHI", "ชนิดเชื้อเพลิง": "เบนซิน", "จำนวนรถ": 50},
    ])

    _, df_fuel_out = add_derived_columns(df_model, df_fuel, base_maps())

    if "Powertrain" not in df_fuel_out.columns:
        failures.append(f"fuel grain missing Powertrain column")
    else:
        # Both fuel rows should have powertrain assigned (via powertrain_map)
        if df_fuel_out["Powertrain"].isna().any():
            failures.append(f"fuel rows have NaN Powertrain: {df_fuel_out['Powertrain'].tolist()}")


def test_stale_existing_parquet_columns_stripped_after_merge():
    """A pre-refactor model parquet can still carry ชนิดเชื้อเพลิง/Powertrain/
    include_in_bev_model_report for its untouched (non-rebuilt) rows. rolling_merge
    concatenates df_keep as-is, so those stale columns reappear in the merged frame
    — proving the cleanup in build_cleaned.main() (drop + validate_model, right
    before saving test_model_cleaned.parquet) is required, not redundant."""
    stale_row = {
        "ปี": 2567, "เดือน": "มกราคม", "ประเภทรถ": "รถกระบะ", "จังหวัด": "กรุงเทพมหานคร",
        "ยี่ห้อรถ": "MITSUBISHI", "ยี่ห้อรถ2": "MITSUBISHI", "รุ่นรถ": "TRITON", "รุ่นรถ2": "TRITON",
        "ชนิดเชื้อเพลิง": "ดีเซล", "Powertrain": "ICE", "include_in_bev_model_report": False,
        "จำนวนรถ": 50,
    }
    df_existing = pd.DataFrame([stale_row])

    new_row = {
        "ปี": 2569, "เดือน": "กรกฎาคม", "ประเภทรถ": "รถกระบะ", "จังหวัด": "กรุงเทพมหานคร",
        "ยี่ห้อรถ": "MITSUBISHI", "ยี่ห้อรถ2": "MITSUBISHI", "รุ่นรถ": "PAJERO", "รุ่นรถ2": "PAJERO",
        "จำนวนรถ": 20,
    }
    df_cleaned = pd.DataFrame([new_row])

    maps = {"brand2_order": ["MITSUBISHI"], "merged_brand2_map": merged_brand2_map, "model_name_map": {}}
    merged, _ = rolling_merge(df_cleaned, df_existing, {2569}, maps, is_fuel=False)
    merged = reapply_canonical_maps(merged, maps, is_fuel=False)

    if "Powertrain" not in merged.columns:
        failures.append("test setup invalid: stale Powertrain did not survive rolling_merge")

    cleaned = merged.drop(columns=["ชนิดเชื้อเพลิง", "Powertrain", "include_in_bev_model_report"], errors="ignore")
    try:
        validate_model(cleaned)
    except ValueError as e:
        failures.append(f"validate_model raised after cleanup, stale columns survived: {e}")


def test_rolling_merge_natural_row_counts():
    """rolling_merge must compute new/corrected month keys correctly even when the
    raw rebuild-year row count differs from the existing rebuild-year row count
    (no padding rows required) — proving keys are derived from each frame's own
    data, not misaligned masks from a different frame."""
    df_existing = pd.DataFrame([
        {"ปี": 2568, "เดือน": "ธันวาคม", "ยี่ห้อรถ": "MITSUBISHI", "ยี่ห้อรถ2": "MITSUBISHI",
         "รุ่นรถ": "TRITON", "รุ่นรถ2": "TRITON", "จำนวนรถ": 10},
        {"ปี": 2569, "เดือน": "มกราคม", "ยี่ห้อรถ": "MITSUBISHI", "ยี่ห้อรถ2": "MITSUBISHI",
         "รุ่นรถ": "TRITON", "รุ่นรถ2": "TRITON", "จำนวนรถ": 5},
    ])

    df_cleaned = pd.DataFrame([
        {"ปี": 2567, "เดือน": "มกราคม", "ยี่ห้อรถ": "MITSUBISHI", "ยี่ห้อรถ2": "MITSUBISHI",
         "รุ่นรถ": "TRITON", "รุ่นรถ2": "TRITON", "จำนวนรถ": 1},  # not in rebuild_years, must be excluded
        {"ปี": 2569, "เดือน": "มกราคม", "ยี่ห้อรถ": "MITSUBISHI", "ยี่ห้อรถ2": "MITSUBISHI",
         "รุ่นรถ": "TRITON", "รุ่นรถ2": "TRITON", "จำนวนรถ": 8},  # corrected
        {"ปี": 2569, "เดือน": "กุมภาพันธ์", "ยี่ห้อรถ": "MITSUBISHI", "ยี่ห้อรถ2": "MITSUBISHI",
         "รุ่นรถ": "PAJERO", "รุ่นรถ2": "PAJERO", "จำนวนรถ": 3},  # new
        {"ปี": 2569, "เดือน": "มีนาคม", "ยี่ห้อรถ": "MITSUBISHI", "ยี่ห้อรถ2": "MITSUBISHI",
         "รุ่นรถ": "PAJERO", "รุ่นรถ2": "PAJERO", "จำนวนรถ": 4},  # new
    ])

    maps = {"brand2_order": ["MITSUBISHI"], "merged_brand2_map": merged_brand2_map, "model_name_map": {}}
    merged, info = rolling_merge(df_cleaned, df_existing, {2569}, maps, is_fuel=False)

    if info["new_keys"] != {"2569_กุมภาพันธ์", "2569_มีนาคม"}:
        failures.append(f"unexpected new_keys: {info['new_keys']}")
    if info["corrected_keys"] != {"2569_มกราคม"}:
        failures.append(f"unexpected corrected_keys: {info['corrected_keys']}")
    if len(merged) != 4:  # kept 2568 row + 3 rebuild-year rows from raw (2567 row excluded)
        failures.append(f"unexpected merged row count: {len(merged)}")
    if (merged["ปี"] == 2567).any():
        failures.append("row outside rebuild_years leaked into merged frame")


if __name__ == "__main__":
    test_real_raw_totals_reconcile()
    test_model_grain_never_has_powertrain()
    test_fuel_grain_gets_powertrain()
    test_stale_existing_parquet_columns_stripped_after_merge()
    test_rolling_merge_natural_row_counts()
    if failures:
        print(f"FAIL — {len(failures)} issue(s) in source-grain-separation tests:")
        for f in failures:
            print(f)
        sys.exit(1)
    print("PASS — All source-grain-separation tests passed successfully.")
