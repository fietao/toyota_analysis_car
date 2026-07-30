"""
Focused tests: build_analyst.py Sheet 1 must be sourced from fuel-derived
Powertrain data. Model grain has no Powertrain field.

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

from build_analyst import (
    _build_sheet1_data, filter_ry, MONTH_ORDER,
    check_period_match, check_nonzero_recognized_total,
)
from aggregate import current_period
from calculation_builder import build_calculation_table, THAI_MONTHS

failures = []


def _row(year, month, pt, units, fuel=None):
    row = {
        "ปี": year, "เดือน": month, "ประเภทรถ": "รย.1",
        "จังหวัด": "กรุงเทพมหานคร", "ยี่ห้อรถ": "TOYOTA", "ยี่ห้อรถ2": "TOYOTA",
        "รุ่นรถ": "YARIS", "รุ่นรถ2": "YARIS",
        "Powertrain": pt, "จำนวนรถ": units,
    }
    if fuel is not None:
        row["ชนิดเชื้อเพลิง"] = fuel
    return row


def _model_row(year, month, units):
    row = _row(year, month, "", units)
    row.pop("Powertrain")
    return row


def test_sheet1_uses_fuel_powertrain():
    df_fuel = pd.DataFrame([
        _row(2568, "มกราคม", "ICE", 10, fuel="เบนซิน"),
        _row(2569, "มกราคม", "ICE", 12, fuel="เบนซิน"),
    ])

    fuel_data = _build_sheet1_data(filter_ry(df_fuel), 2569, 2568, 1)

    if fuel_data.get(("grand", "W")) != 12:
        failures.append(f"expected fuel-sourced Sheet 1 curr-month total 12, got {fuel_data.get(('grand', 'W'))}")


def test_model_grain_rejects_powertrain_filter():
    df_model = pd.DataFrame([_model_row(2569, "มกราคม", 12)])
    try:
        build_calculation_table(df_model, "model", "BEV", 2569, 1)
        failures.append("model grain accepted a Powertrain filter")
    except ValueError as exc:
        if "fuel-grain" not in str(exc):
            failures.append(f"model Powertrain filter raised the wrong error: {exc}")


def test_fuel_ice_bev_hev_phev_produces_nonzero_totals():
    df_fuel = pd.DataFrame([
        _row(2568, "มกราคม", "ICE", 10, fuel="เบนซิน"),
        _row(2569, "มกราคม", "ICE", 5, fuel="เบนซิน"),
        _row(2569, "มกราคม", "BEV", 3, fuel="ไฟฟ้า"),
        _row(2569, "มกราคม", "HEV", 2, fuel="ไฮบริด"),
        _row(2569, "มกราคม", "PHEV", 1, fuel="ปลั๊กอินไฮบริด"),
    ])
    data = _build_sheet1_data(filter_ry(df_fuel), 2569, 2568, 1)
    if data.get(("grand", "W")) != 11:
        failures.append(f"expected nonzero grand total 11 for ICE/BEV/HEV/PHEV fuel data, got {data.get(('grand', 'W'))}")


def test_calculation_table_can_filter_by_province():
    jan = THAI_MONTHS[1]
    bangkok = _row(2569, jan, "ICE", 12, fuel="à¹€à¸šà¸™à¸‹à¸´à¸™")
    chiang_mai = _row(2569, jan, "ICE", 7, fuel="à¹€à¸šà¸™à¸‹à¸´à¸™")
    chiang_mai["จังหวัด"] = "CHIANG MAI"
    df_fuel = pd.DataFrame([bangkok, chiang_mai])

    rows = build_calculation_table(df_fuel, "brand", "ALL", 2569, 1, {"1"}, province="CHIANG MAI")
    grand = rows[0]
    if grand.curr_month_units != 7:
        failures.append(f"expected province-filtered current month total 7, got {grand.curr_month_units}")


def test_zero_recognized_total_guard_raises():
    # Every row is an unrecognized powertrain -> the guard's grand total is zero.
    df_fuel = pd.DataFrame([
        _row(2568, "มกราคม", "N/A", 10, fuel="ไม่ทราบ"),
        _row(2569, "มกราคม", "N/A", 12, fuel="ไม่ทราบ"),
    ])
    guard_data = _build_sheet1_data(filter_ry(df_fuel), 2569, 2568, 1)
    try:
        check_nonzero_recognized_total(guard_data, "มกราคม", 2569)
        failures.append("expected check_nonzero_recognized_total to raise for an all-zero recognized total")
    except ValueError:
        pass


def test_nonzero_recognized_total_guard_passes():
    df_fuel = pd.DataFrame([_row(2569, "มกราคม", "ICE", 5, fuel="เบนซิน")])
    guard_data = _build_sheet1_data(filter_ry(df_fuel), 2569, 2568, 1)
    try:
        check_nonzero_recognized_total(guard_data, "มกราคม", 2569)
    except ValueError as e:
        failures.append(f"expected check_nonzero_recognized_total to pass for a nonzero total, raised: {e}")


def test_period_mismatch_guard_raises():
    df_fuel_ry = filter_ry(pd.DataFrame([_row(2569, "มกราคม", "ICE", 10, fuel="เบนซิน")]))
    df_model_ry = filter_ry(pd.DataFrame([_model_row(2569, "กุมภาพันธ์", 10)]))

    fuel_year, fuel_month = current_period(df_fuel_ry, year_col="ปี", month_col="เดือน", month_order=MONTH_ORDER)
    model_year, model_month = current_period(df_model_ry, year_col="ปี", month_col="เดือน", month_order=MONTH_ORDER)

    try:
        check_period_match(fuel_year, fuel_month, model_year, model_month)
        failures.append("expected check_period_match to raise for a fuel/model month mismatch")
    except ValueError:
        pass


def test_period_match_guard_passes():
    df_fuel_ry = filter_ry(pd.DataFrame([_row(2569, "มกราคม", "ICE", 10, fuel="เบนซิน")]))
    df_model_ry = filter_ry(pd.DataFrame([_model_row(2569, "มกราคม", 10)]))

    fuel_year, fuel_month = current_period(df_fuel_ry, year_col="ปี", month_col="เดือน", month_order=MONTH_ORDER)
    model_year, model_month = current_period(df_model_ry, year_col="ปี", month_col="เดือน", month_order=MONTH_ORDER)

    try:
        check_period_match(fuel_year, fuel_month, model_year, model_month)
    except ValueError as e:
        failures.append(f"expected check_period_match to pass for matching periods, raised: {e}")


if __name__ == "__main__":
    test_sheet1_uses_fuel_powertrain()
    test_model_grain_rejects_powertrain_filter()
    test_fuel_ice_bev_hev_phev_produces_nonzero_totals()
    test_calculation_table_can_filter_by_province()
    test_zero_recognized_total_guard_raises()
    test_nonzero_recognized_total_guard_passes()
    test_period_mismatch_guard_raises()
    test_period_match_guard_passes()
    if failures:
        print(f"FAIL — {len(failures)} issue(s) in build_analyst Sheet 1 source tests:")
        for f in failures:
            print(f)
        sys.exit(1)
    print("PASS — All build_analyst Sheet 1 source tests passed successfully.")
    sys.exit(0)
