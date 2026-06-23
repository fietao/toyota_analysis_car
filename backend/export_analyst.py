import os
import json
import pandas as pd
from dataclasses import asdict
import sys

# Adjust path to import calculation_builder
sys.path.append(os.path.dirname(__file__))
from calculation_builder import build_calculation_table, MONTH_TO_NUM, THAI_MONTHS

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

    # Determine current year and month from fuel data
    if "เดือน" in df_fuel.columns:
        df_fuel["month_num"] = df_fuel["เดือน"].map(MONTH_TO_NUM).fillna(0).astype(int)

    max_year = int(df_fuel["ปี"].max())
    current_month_num = int(df_fuel[df_fuel["ปี"] == max_year]["month_num"].max())
    current_month_th = THAI_MONTHS.get(current_month_num, "")
    print(f"Current period detected: Year {max_year}, Month {current_month_num}")

    results = {}

    view_bys = ["brand", "model"]
    powertrains = ["ALL", "ICE", "BEV", "HEV", "PHEV"]

    for vb in view_bys:
        # brand views use fuel parquet (accurate powertrain from ชนิดเชื้อเพลิง)
        # model views use model parquet (has รุ่นรถ2)
        df = df_fuel if vb == "brand" else df_model
        results[vb] = {}
        for pt in powertrains:
            print(f"Processing view_by={vb}, powertrain={pt}...")
            rows = build_calculation_table(
                df=df,
                view_by=vb, # type: ignore
                powertrain=pt,
                current_year=max_year,
                current_month_num=current_month_num
            )
            # convert rows to dict
            results[vb][pt] = [asdict(r) for r in rows]

    payload = {
        "meta": {
            "current_year": max_year,
            "current_month_num": current_month_num,
            "current_month_th": current_month_th
        },
        "data": results
    }

    print(f"Saving to {output_path}...")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)
    print("Done!")

if __name__ == "__main__":
    export_analyst_data()
