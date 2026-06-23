import sys
import pandas as pd
from pathlib import Path
from calculation_builder import build_calculation_table

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(__file__).resolve().parent
CLEANED_FILE = BASE / "test_model_cleaned.parquet"

def print_spot_check(title, rows):
    print(f"\n{'='*80}\n{title}\n{'='*80}")
    # Print Grand Total
    gt = next((r for r in rows if r.is_grand_total), None)
    if gt:
        share_cm = gt.curr_month_share * 100 if gt.curr_month_share is not None else 0
        share_cytd = gt.curr_ytd_share * 100 if gt.curr_ytd_share is not None else 0
        print(f"GRAND TOTAL | CM Share: {share_cm:.1f}% | CYTD Share: {share_cytd:.1f}% | "
              f"CM Units: {gt.curr_month_units} | PM Units: {gt.prev_month_units}")
    
    # Find specific edge cases
    improved = next((r for r in rows if not r.is_grand_total and str(r.rank_diff).startswith("+")), None)
    worsened = next((r for r in rows if not r.is_grand_total and r.rank_diff not in ["—", "NEW"] and not str(r.rank_diff).startswith("+")), None)
    missing_prev = next((r for r in rows if not r.is_grand_total and r.prev_month_units is None), None)

    print("\n--- Edge Cases Spot Check ---")
    for r, label in [(improved, "Improved Rank"), (worsened, "Worsened Rank"), (missing_prev, "Missing Prev Period")]:
        if r:
            ident = f"{r.brand}" + (f" / {r.model}" if r.model else "")
            growth_yoy = f"{(r.curr_growth_vs_same_month_prev_year or 0)*100:.1f}%" if r.curr_growth_vs_same_month_prev_year is not None else "N/A"
            print(f"[{label:19s}] {ident:20s} | Rank: {r.prev_rank} -> {r.curr_rank} (Diff: {r.rank_diff:4s}) | "
                  f"CM Units: {r.curr_month_units} (YoY: {growth_yoy}) | PM Units: {r.prev_month_units}")
        else:
            print(f"[{label:19s}] None found in this cut")

def main():
    print("Loading cleaned data...")
    df_raw = pd.read_parquet(str(CLEANED_FILE))
    df_raw["จำนวนรถ"] = pd.to_numeric(df_raw["จำนวนรถ"], errors="coerce").fillna(0).astype(int)
    df_raw["ปี"] = pd.to_numeric(df_raw["ปี"], errors="coerce").dropna().astype(int)
    
    THAI_MONTHS = {
        1:"มกราคม", 2:"กุมภาพันธ์", 3:"มีนาคม",    4:"เมษายน",
        5:"พฤษภาคม", 6:"มิถุนายน",  7:"กรกฎาคม",   8:"สิงหาคม",
        9:"กันยายน", 10:"ตุลาคม",   11:"พฤศจิกายน", 12:"ธันวาคม",
    }
    MONTH_TO_NUM = {v: k for k, v in THAI_MONTHS.items()}
    
    INCLUDE_RY  = {'1','2','3','6','9','10','11'}
    codes = df_raw["ประเภทรถ"].str.extract(r"รย\.(\d+)")[0]
    df_ry = df_raw[codes.isin(INCLUDE_RY)].copy()
    
    curr_year = int(df_ry["ปี"].max())
    curr_month_num = int(df_ry[df_ry["ปี"] == curr_year]["เดือน"].map(MONTH_TO_NUM).max())
    
    # 1. view_by="model", powertrain="BEV"
    rows_model_bev = build_calculation_table(
        df_raw, view_by="model", powertrain="BEV", 
        current_year=curr_year, current_month_num=curr_month_num
    )
    print_spot_check("1. view_by='model', powertrain='BEV'", rows_model_bev)

    # 2. view_by="brand", powertrain="ALL"
    rows_brand_all = build_calculation_table(
        df_raw, view_by="brand", powertrain="ALL", 
        current_year=curr_year, current_month_num=curr_month_num
    )
    print_spot_check("2. view_by='brand', powertrain='ALL'", rows_brand_all)
    
    # 3. view_by="brand", powertrain="BEV"
    rows_brand_bev = build_calculation_table(
        df_raw, view_by="brand", powertrain="BEV", 
        current_year=curr_year, current_month_num=curr_month_num
    )
    print_spot_check("3. view_by='brand', powertrain='BEV'", rows_brand_bev)

if __name__ == "__main__":
    main()
