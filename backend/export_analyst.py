import json
import os
import sys
from dataclasses import asdict

import pandas as pd

# Adjust path to import calculation_builder
sys.path.append(os.path.dirname(__file__))
from aggregate import current_period
from calculation_builder import MONTH_TO_NUM, THAI_MONTHS, build_calculation_table
from export_dashboard import VEHICLE_TYPE_DICT
from schema import validate_fuel, validate_model

VEHICLE_TYPE_PRESETS = {
    "ALL": {"1", "2", "3", "6", "9", "10", "11"},
    "รย.1": {"1"},
    "รย.2": {"2"},
    "รย.3": {"3"},
    "รย.6": {"6"},
    "รย.9": {"9"},
    "รย.10": {"10"},
    "รย.11": {"11"},
}


def vehicle_codes(df: pd.DataFrame) -> pd.Series:
    codes = df["ประเภทรถ"].astype(str).str.extract(r"รย\.(\d+)")[0].fillna("")
    return "รย." + codes


def province_brand_facts(df_fuel: pd.DataFrame, current_year: int) -> list[dict]:
    facts = df_fuel.copy()
    facts = facts[facts["ปี"].isin([current_year, current_year - 1])].copy()
    facts["Powertrain"] = facts["Powertrain"].replace("BEV Major", "BEV")
    facts = facts[facts["Powertrain"].notna() & (facts["Powertrain"] != "OTH")].copy()
    facts["v"] = vehicle_codes(facts)
    grouped = facts.groupby(
        ["จังหวัด", "ยี่ห้อรถ2", "ปี", "month_num", "v", "Powertrain"],
        dropna=True,
    )["จำนวนรถ"].sum().reset_index()
    grouped = grouped.rename(
        columns={
            "จังหวัด": "p",
            "ยี่ห้อรถ2": "b",
            "ปี": "y",
            "month_num": "mo",
            "Powertrain": "pt",
            "จำนวนรถ": "u",
        }
    )
    return grouped[["p", "b", "y", "mo", "v", "pt", "u"]].to_dict("records")


def province_model_facts(df_model: pd.DataFrame, current_year: int) -> list[dict]:
    facts = df_model.copy()
    facts = facts[facts["ปี"].isin([current_year, current_year - 1])].copy()
    facts["month_num"] = facts["เดือน"].map(MONTH_TO_NUM).fillna(0).astype(int)
    facts["v"] = vehicle_codes(facts)
    grouped = facts.dropna(subset=["ยี่ห้อรถ2", "รุ่นรถ2"]).groupby(
        ["จังหวัด", "ยี่ห้อรถ2", "รุ่นรถ2", "ปี", "month_num", "v"],
        dropna=True,
    )["จำนวนรถ"].sum().reset_index()
    grouped = grouped.rename(
        columns={
            "จังหวัด": "p",
            "ยี่ห้อรถ2": "b",
            "รุ่นรถ2": "m",
            "ปี": "y",
            "month_num": "mo",
            "จำนวนรถ": "u",
        }
    )
    return grouped[["p", "b", "m", "y", "mo", "v", "u"]].to_dict("records")


def export_analyst_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fuel_path = os.path.join(base_dir, "backend", "test_fuel_cleaned.parquet")
    model_path = os.path.join(base_dir, "backend", "test_model_cleaned.parquet")
    output_dir = os.environ.get("PUBLIC_DATA_DIR") or os.path.join(base_dir, "frontend", "public", "data")
    output_path = os.path.join(output_dir, "analyst_data.json")
    province_output_path = os.path.join(output_dir, "analyst_province_data.json")

    os.makedirs(output_dir, exist_ok=True)

    print(f"Loading fuel data from {fuel_path}...")
    df_fuel = pd.read_parquet(fuel_path)

    print(f"Loading model data from {model_path}...")
    df_model = pd.read_parquet(model_path)
    validate_fuel(df_fuel)
    validate_model(df_model)

    # Determine current year and month from fuel data.
    if "เดือน" in df_fuel.columns:
        df_fuel["month_num"] = df_fuel["เดือน"].map(MONTH_TO_NUM).fillna(0).astype(int)

    max_year, current_month_num = current_period(df_fuel, year_col="ปี", month_col="month_num")
    current_month_th = THAI_MONTHS.get(current_month_num, "")
    print(f"Current period detected: Year {max_year}, Month {current_month_num}")

    results = {}

    view_bys = ["brand", "model"]
    powertrains = ["ALL", "ICE", "BEV", "HEV", "PHEV"]

    for vb in view_bys:
        # Brand views use fuel parquet (accurate powertrain from fuel type).
        # Model views use model parquet (has model2, never Powertrain).
        df = df_fuel if vb == "brand" else df_model
        results[vb] = {}
        view_powertrains = powertrains if vb == "brand" else ["ALL"]
        for pt in view_powertrains:
            results[vb][pt] = {}
            for vt_code, vt_set in VEHICLE_TYPE_PRESETS.items():
                print(f"Processing view_by={vb}, powertrain={pt}, vehicle_type={vt_code}...")
                rows = build_calculation_table(
                    df=df,
                    view_by=vb,  # type: ignore
                    powertrain=pt,
                    current_year=max_year,
                    current_month_num=current_month_num,
                    vehicle_types=vt_set,
                )
                results[vb][pt][vt_code] = [asdict(r) for r in rows]

    provinces = sorted(df_model["จังหวัด"].dropna().astype(str).unique().tolist())
    vehicle_types_list = [
        {"code": code, "label": VEHICLE_TYPE_DICT[code]}
        for code in VEHICLE_TYPE_PRESETS if code != "ALL"
    ]

    payload = {
        "meta": {
            "current_year": max_year,
            "current_month_num": current_month_num,
            "current_month_th": current_month_th,
            "vehicle_types_list": vehicle_types_list,
            "provinces": provinces,
        },
        "data": results,
    }

    province_payload = {
        "meta": payload["meta"],
        "facts": {
            "brand": province_brand_facts(df_fuel, max_year),
            "model": province_model_facts(df_model, max_year),
        },
    }

    print(f"Saving to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    print(f"Saving to {province_output_path}...")
    with open(province_output_path, "w", encoding="utf-8") as f:
        json.dump(province_payload, f, ensure_ascii=False)
    print("Done!")


if __name__ == "__main__":
    export_analyst_data()
