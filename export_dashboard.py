import pandas as pd
import json
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
OUTPUT_DIR = BASE / "output"
FRONTEND_DATA_DIR = BASE / "dashboard" / "public" / "data"
FRONTEND_DATA_DIR.mkdir(parents=True, exist_ok=True)

def export_data():
    reports = list(BASE.glob("*(test analyst).xlsx"))
    if not reports:
        print("No analyst report found in base directory.")
        return
    
    # Use the latest report
    latest_report = max(reports, key=lambda p: p.stat().st_mtime)
    print(f"Exporting data from {latest_report.name}...")
    
    data = {}
    
    try:
        # 1. Reg by Powertrain (Skip headers and get raw data)
        df_powertrain = pd.read_excel(latest_report, sheet_name="1.Reg by Powertrain", header=4)
        # Clean up column names and rows based on formatting
        df_pt_clean = df_powertrain.dropna(subset=[df_powertrain.columns[0]])
        # Just grab the first few key columns for charting: Powertrain, current YTD, etc.
        # This will be refined as needed for the dashboard charts
        data["powertrain"] = json.loads(df_pt_clean.to_json(orient="records"))
        
        # 2. Rank by Brand
        try:
            df_brand = pd.read_excel(latest_report, sheet_name="2.Rank by Brand", header=4)
            df_brand_clean = df_brand.dropna(subset=[df_brand.columns[0]])
            data["brand_rank"] = json.loads(df_brand_clean.to_json(orient="records"))
        except Exception as e:
            print(f"Skipping Rank by Brand: {e}")
            
        # 3. BEV by Model
        try:
            df_bev_model = pd.read_excel(latest_report, sheet_name="7.BEV by Model", header=4)
            df_bev_model_clean = df_bev_model.dropna(subset=[df_bev_model.columns[0]])
            data["bev_model"] = json.loads(df_bev_model_clean.to_json(orient="records"))
        except Exception as e:
            print(f"Skipping BEV by Model: {e}")
            
    except Exception as e:
        print(f"Error parsing Excel: {e}")
        return

    out_file = FRONTEND_DATA_DIR / "dashboard_data.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"Successfully exported JSON to {out_file}")

if __name__ == "__main__":
    export_data()
