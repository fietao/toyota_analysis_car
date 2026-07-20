"""Tests for plans/reliable-series-powertrain.md, Step 3 (BEV model report inclusion).

include_in_bev_model_report must be derived solely from a verified
series_registry row with powertrain=BEV — never carried forward from a
stale/guessed value on a retained historical row. The legacy
refer/bev_series_name_table_template_rows.csv path and its loader
(_load_bev_model_report_map) were removed once series_registry.csv became
the sole canonical authority (final maintenance pass); the equivalent
"legacy input cannot override the registry" proof now lives in
test_source_grain_separation.py.

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

from build_cleaned import add_derived_columns, reapply_canonical_maps, load_powertrain_map
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


def test_verified_bev_included():
    df_model = pd.DataFrame([{"ยี่ห้อรถ": "BYD", "รุ่นรถ": "ATTO 3", "จำนวนรถ": 10}])
    df_fuel = pd.DataFrame([{"ยี่ห้อรถ": "BYD", "ชนิดเชื้อเพลิง": "ไฟฟ้า", "จำนวนรถ": 10}])
    series_powertrain_map = {normalize_key("BYD", "ATTO 3"): "BEV"}

    df_model, _ = add_derived_columns(df_model, df_fuel, base_maps(series_powertrain_map))

    included = bool(df_model["include_in_bev_model_report"].iloc[0])
    if not included:
        failures.append("verified BEV row: expected include_in_bev_model_report=True")


def test_every_other_powertrain_or_status_excluded():
    rows = [
        {"ยี่ห้อรถ": "TOYOTA", "รุ่นรถ": "COROLLA", "จำนวนรถ": 5},   # verified ICE
        {"ยี่ห้อรถ": "TOYOTA", "รุ่นรถ": "CAMRY_HEV", "จำนวนรถ": 5},  # verified HEV
        {"ยี่ห้อรถ": "TOYOTA", "รุ่นรถ": "RAV4_PHEV", "จำนวนรถ": 5},  # verified PHEV
        {"ยี่ห้อรถ": "TOYOTA", "รุ่นรถ": "UNREVIEWED_MODEL", "จำนวนรถ": 5},  # not in registry at all
    ]
    df_model = pd.DataFrame(rows)
    df_fuel = pd.DataFrame([{"ยี่ห้อรถ": "TOYOTA", "ชนิดเชื้อเพลิง": "เบนซิน", "จำนวนรถ": 20}])
    series_powertrain_map = {
        normalize_key("TOYOTA", "COROLLA"): "ICE",
        normalize_key("TOYOTA", "CAMRY_HEV"): "HEV",
        normalize_key("TOYOTA", "RAV4_PHEV"): "PHEV",
        # UNREVIEWED_MODEL intentionally absent -> N/A (covers missing/unreviewed/conflicting,
        # since verified_powertrain_map() only ever contains review_status=='verified' rows)
    }

    df_model, _ = add_derived_columns(df_model, df_fuel, base_maps(series_powertrain_map))

    if df_model["include_in_bev_model_report"].any():
        failures.append(
            "every other Powertrain/status: expected all include_in_bev_model_report=False, "
            f"got {df_model[['รุ่นรถ', 'Powertrain', 'include_in_bev_model_report']].to_dict('records')}"
        )


def test_historical_guess_overwritten():
    # Simulates a row retained across a rolling merge that still carries a
    # stale guess from the old dominant-fuel/legacy-CSV era.
    df = pd.DataFrame([{
        "ยี่ห้อรถ": "AION", "ยี่ห้อรถ2": "AION", "รุ่นรถ": "AION ES",
        "Powertrain": "BEV Major", "include_in_bev_model_report": True,
        "จำนวนรถ": 3,
    }])
    maps = base_maps(series_powertrain_map={})  # nothing verified for AION ES

    df = reapply_canonical_maps(df, maps, is_fuel=False)

    if df["Powertrain"].iloc[0] != "N/A":
        failures.append(
            f"historical guess overwrite: expected Powertrain='N/A', got {df['Powertrain'].iloc[0]!r}"
        )
    if bool(df["include_in_bev_model_report"].iloc[0]):
        failures.append(
            "historical guess overwrite: expected include_in_bev_model_report=False after reclassification"
        )


if __name__ == "__main__":
    test_verified_bev_included()
    test_every_other_powertrain_or_status_excluded()
    test_historical_guess_overwritten()
    if failures:
        print(f"FAIL — {len(failures)} issue(s) in bev-model-report-inclusion tests:")
        for f in failures:
            print(f)
        sys.exit(1)
    print("PASS — All bev-model-report-inclusion tests passed successfully.")
