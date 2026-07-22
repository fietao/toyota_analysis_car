"""Focused regression tests for historical canonicalization in build_cleaned.py.

Loads the real, production-configured mapping files (config/brand_map.csv and
config/model_map.csv), so this test fails if canonical model aliases drift.

Runs from any directory. Exits 0 on PASS, 1 on FAIL.
"""
import sys
from pathlib import Path
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

TESTS = Path(__file__).resolve().parent
BACKEND = TESTS.parent
sys.path.insert(0, str(BACKEND))

from build_cleaned import reapply_canonical_maps, load_powertrain_map
from model_map import model2_map

# Load the real, production-configured mapping files (same loading logic as
# load_reference_maps in build_cleaned.py) instead of a duplicated dummy map.
brand_csv_map = load_powertrain_map(str(BACKEND / "config" / "brand_map.csv"), "brand", "brand2")
merged_brand2_map = {k.upper(): v for k, v in brand_csv_map.items()}

real_maps = {
    "merged_brand2_map": merged_brand2_map,
    "model_name_map": model2_map(),
}

failures = []

def assert_equal(actual, expected, msg):
    if isinstance(actual, pd.DataFrame) and isinstance(expected, pd.DataFrame):
        try:
            pd.testing.assert_frame_equal(actual, expected)
        except AssertionError as e:
            failures.append(f"{msg}: {e}")
    else:
        if actual != expected:
            failures.append(f"{msg}: expected {expected!r}, got {actual!r}")

def run_tests():
    # 1. Historical and current Deepal aliases produce one brand2
    df_brand_test = pd.DataFrame({
        "ยี่ห้อรถ": ["DEEPAL", "CHANGAN", "CHANG AN", "Deepal + Changan"],
        "ยี่ห้อรถ2": ["DEEPAL", "CHANGAN", "CHANG AN", "Deepal + Changan"],
        "รุ่นรถ": ["S7", "L07", "L07", "S7"]
    })

    df_brand_res = reapply_canonical_maps(df_brand_test.copy(), real_maps, is_fuel=False)
    assert_equal(list(df_brand_res["ยี่ห้อรถ2"]), ["Deepal + Changan"] * 4, "Deepal normalization")

    # 1b. MOTOGUZZI/MOTO GUZZI aliases produce one brand2
    df_moto_test = pd.DataFrame({
        "ยี่ห้อรถ": ["MOTOGUZZI", "MOTO GUZZI"],
        "ยี่ห้อรถ2": ["MOTOGUZZI", "MOTO GUZZI"],
        "รุ่นรถ": ["V7", "V7"]
    })
    df_moto_res = reapply_canonical_maps(df_moto_test.copy(), real_maps, is_fuel=False)
    assert_equal(list(df_moto_res["ยี่ห้อรถ2"]), ["MOTO GUZZI"] * 2, "Moto Guzzi normalization")

    # 2. Confirmed model aliases produce one model2
    df_model_test = pd.DataFrame({
        "ยี่ห้อรถ": ["HONDA"] * 5,
        "ยี่ห้อรถ2": ["Honda"] * 5,
        "รุ่นรถ": ["WAVE 125 I", "WAVE 125i", "WAVE125I", "wave 125i", "WAVE 125i"],
        "รุ่นรถ2": ["WAVE 125 I", "WAVE 125i", "WAVE125I", "wave 125i", "WAVE 125i"]
    })
    df_model_res = reapply_canonical_maps(df_model_test.copy(), real_maps, is_fuel=False)
    assert_equal(list(df_model_res["รุ่นรถ2"]), ["WAVE 125i"] * 5, "WAVE 125i normalization")

    # 2b. Confirmed WAVE 110i / STEPWGN SPADA / CLICK 150i / PCX 150 aliases
    # (registry-migrated, data-driven set only — "CLICK 150I" with an internal
    # space has no current-data occurrence to derive a brand from, so it is not
    # in the registry and is intentionally excluded here.)
    df_model2_test = pd.DataFrame({
        "ยี่ห้อรถ": ["HONDA"] * 5,
        "ยี่ห้อรถ2": ["Honda"] * 5,
        "รุ่นรถ": ["WAVE 110 I", "WAVE110I", "STEPWGN SPADA", "CLICK150I", "PCX150"],
        "รุ่นรถ2": ["WAVE 110 I", "WAVE110I", "STEPWGN SPADA", "CLICK150I", "PCX150"]
    })
    df_model2_res = reapply_canonical_maps(df_model2_test.copy(), real_maps, is_fuel=False)
    assert_equal(
        list(df_model2_res["รุ่นรถ2"]),
        ["WAVE 110i", "WAVE 110i", "STEP WGN SPADA", "CLICK 150i", "PCX 150"],
        "WAVE 110i/STEPWGN SPADA/CLICK 150i/PCX 150 normalization",
    )

    # 3. จำนวนรถ total is unchanged
    df_units_test = pd.DataFrame({
        "ยี่ห้อรถ": ["DEEPAL", "HONDA"],
        "ยี่ห้อรถ2": ["DEEPAL", "HONDA"],
        "รุ่นรถ": ["S7", "WAVE125I"],
        "รุ่นรถ2": ["S7", "WAVE125I"],
        "จำนวนรถ": [10, 20]
    })
    df_units_res = reapply_canonical_maps(df_units_test.copy(), real_maps, is_fuel=False)
    assert_equal(df_units_res["จำนวนรถ"].sum(), 30, "จำนวนรถ total sum")

    # 4. Fuel and powertrain values are unchanged
    df_fuel_test = pd.DataFrame({
        "ยี่ห้อรถ": ["DEEPAL", "HONDA"],
        "ยี่ห้อรถ2": ["DEEPAL", "HONDA"],
        "ชนิดเชื้อเพลิง": ["ไฟฟ้า", "เบนซิน"],
        "Powertrain": ["BEV", "ICE"],
        "จำนวนรถ": [5, 15]
    })
    df_fuel_res = reapply_canonical_maps(df_fuel_test.copy(), real_maps, is_fuel=True)
    assert_equal(list(df_fuel_res["ชนิดเชื้อเพลิง"]), ["ไฟฟ้า", "เบนซิน"], "Fuel types unchanged")
    assert_equal(list(df_fuel_res["Powertrain"]), ["BEV", "ICE"], "Powertrains unchanged")
    assert_equal(list(df_fuel_res["จำนวนรถ"]), [5, 15], "Fuel units unchanged")

    # 5. Already-canonical rows remain unchanged
    df_canonical = pd.DataFrame({
        "ยี่ห้อรถ": ["DEEPAL", "HONDA"],
        "ยี่ห้อรถ2": ["Deepal + Changan", "HONDA"],
        "รุ่นรถ": ["S7", "WAVE 125i"],
        "รุ่นรถ2": ["S7", "WAVE 125i"],
    })
    df_canonical_res = reapply_canonical_maps(df_canonical.copy(), real_maps, is_fuel=False)
    try:
        pd.testing.assert_frame_equal(df_canonical_res, df_canonical, check_dtype=False)
    except AssertionError as e:
        failures.append(f"Canonical rows unchanged: {e}")

    # 6. Reapplying canonicalization is idempotent
    df_once = reapply_canonical_maps(df_brand_test.copy(), real_maps, is_fuel=False)
    df_twice = reapply_canonical_maps(df_once.copy(), real_maps, is_fuel=False)
    assert_equal(df_once, df_twice, "Idempotency check")

if __name__ == "__main__":
    run_tests()
    if failures:
        print(f"FAIL — {len(failures)} issue(s) in canonicalization tests:")
        for f in failures:
            print(f)
        sys.exit(1)
    print("PASS — All canonicalization tests passed successfully.")
