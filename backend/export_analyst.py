import os
import json
import pandas as pd
from dataclasses import asdict
import sys

# Adjust path to import calculation_builder
sys.path.append(os.path.dirname(__file__))
from aggregate import current_period
from calculation_builder import build_calculation_table, MONTH_TO_NUM, THAI_MONTHS
from schema import validate_model, validate_fuel
from export_dashboard import VEHICLE_TYPE_DICT

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

def export_analyst_data():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    fuel_path  = os.path.join(base_dir, "backend", "test_fuel_cleaned.parquet")
    model_path = os.path.join(base_dir, "backend", "test_model_cleaned.parquet")
    output_dir = os.path.join(base_dir, "frontend", "public", "data")
    output_path = os.path.join(output_dir, "analyst_data.json")

    os.makedirs(output_dir, exist_ok=True)

    print(f"Loading fuel data from {fuel_path}...")
    df_fuel = pd.read_parquet(fuel_path)

    print(f"Loading model data from {model_path}...")
    df_model = pd.read_parquet(model_path)
    validate_fuel(df_fuel)
    validate_model(df_model)

    # Determine current year and month from fuel data
    if "เดือน" in df_fuel.columns:
        df_fuel["month_num"] = df_fuel["เดือน"].map(MONTH_TO_NUM).fillna(0).astype(int)

    max_year, current_month_num = current_period(df_fuel, year_col="ปี", month_col="month_num")
    current_month_th = THAI_MONTHS.get(current_month_num, "")
    print(f"Current period detected: Year {max_year}, Month {current_month_num}")

    results = {}

    view_bys = ["brand", "model"]
    powertrains = ["ALL", "ICE", "BEV", "HEV", "PHEV"]

    for vb in view_bys:
        # brand views use fuel parquet (accurate powertrain from ชนิดเชื้อเพลิง)
        # model views use model parquet (has รุ่นรถ2, never Powertrain)
        df = df_fuel if vb == "brand" else df_model
        results[vb] = {}
        view_powertrains = powertrains if vb == "brand" else ["ALL"]
        for pt in view_powertrains:
            results[vb][pt] = {}
            for vt_code, vt_set in VEHICLE_TYPE_PRESETS.items():
                print(f"Processing view_by={vb}, powertrain={pt}, vehicle_type={vt_code}...")
                rows = build_calculation_table(
                    df=df,
                    view_by=vb, # type: ignore
                    powertrain=pt,
                    current_year=max_year,
                    current_month_num=current_month_num,
                    vehicle_types=vt_set
                )
                # convert rows to dict
                results[vb][pt][vt_code] = [asdict(r) for r in rows]

    vehicle_types_list = [
        {"code": code, "label": VEHICLE_TYPE_DICT[code]}
        for code in VEHICLE_TYPE_PRESETS if code != "ALL"
    ]

    payload = {
        "meta": {
            "current_year": max_year,
            "current_month_num": current_month_num,
            "current_month_th": current_month_th,
            "vehicle_types_list": vehicle_types_list
        },
        "data": results
    }

    print(f"Saving to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False)
    print("Done!")

if __name__ == "__main__":
    export_analyst_data()
