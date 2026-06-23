import pandas as pd
from dataclasses import dataclass
from typing import Literal, Optional, List

@dataclass
class CalculationRow:
    # Identity
    brand: str
    model: Optional[str]
    is_grand_total: bool
    
    # Prev year month
    prev_month_units: Optional[int]
    prev_month_share: Optional[float]
    
    # Prev year YTD
    prev_ytd_units: Optional[int]
    prev_ytd_share: Optional[float]
    
    # Prev full year
    prev_full_units: Optional[int]
    prev_full_share: Optional[float]
    
    # Curr year month
    curr_month_units: Optional[int]
    curr_month_share: Optional[float]
    curr_month_diff: Optional[float]
    curr_growth_vs_prev_month: Optional[float]
    curr_growth_vs_same_month_prev_year: Optional[float]
    
    # Curr year YTD
    curr_ytd_units: Optional[int]
    curr_ytd_share: Optional[float]
    curr_ytd_diff: Optional[float]
    curr_ytd_growth: Optional[float]
    
    # Rank
    prev_rank: Optional[int]
    curr_rank: Optional[int]
    rank_diff: Optional[str]


THAI_MONTHS = {
    1: "มกราคม", 2: "กุมภาพันธ์", 3: "มีนาคม", 4: "เมษายน",
    5: "พฤษภาคม", 6: "มิถุนายน", 7: "กรกฎาคม", 8: "สิงหาคม",
    9: "กันยายน", 10: "ตุลาคม", 11: "พฤศจิกายน", 12: "ธันวาคม",
}
MONTH_TO_NUM = {v: k for k, v in THAI_MONTHS.items()}

def build_calculation_table(
    df: pd.DataFrame,
    view_by: Literal["brand", "model"],
    powertrain: str,
    current_year: int,
    current_month_num: int,
    vehicle_types: set[str] = {"1", "2", "3", "6", "9", "10", "11"}
) -> List[CalculationRow]:
    
    df = df.copy()
    
    # Filter by vehicle types
    if "ประเภทรถ" in df.columns:
        codes = df["ประเภทรถ"].astype(str).str.extract(r"รย\.(\d+)")[0]
        df = df[codes.isin(vehicle_types)].copy()
        
    # Map Powertrain
    if "Powertrain" in df.columns:
        df["Powertrain"] = df["Powertrain"].replace("BEV Major", "BEV")
        df = df[df["Powertrain"].notna() & (df["Powertrain"] != "OTH")]
        if powertrain != "ALL":
            df = df[df["Powertrain"] == powertrain]

    # Map month numbers
    if "เดือน" in df.columns:
        df["month_num"] = df["เดือน"].map(MONTH_TO_NUM).fillna(0).astype(int)
    
    # Prepare previous month (chronological) for MoM growth
    if current_month_num == 1:
        prev_month_year = current_year - 1
        prev_month_num = 12
    else:
        prev_month_year = current_year
        prev_month_num = current_month_num - 1

    # Identity Columns
    if view_by == "model":
        groupby_cols = ["ยี่ห้อรถ2", "รุ่นรถ2"]
    else:
        groupby_cols = ["ยี่ห้อรถ2"]

    # Filter out records without an identity
    df = df.dropna(subset=groupby_cols)

    # Function to get aggregated units for a specific condition
    def get_units(condition) -> pd.Series:
        sub = df[condition]
        if sub.empty:
            return pd.Series(dtype=int)
        return sub.groupby(groupby_cols)["จำนวนรถ"].sum()

    # Pre-calculate periods
    cond_prev_month_same = (df["ปี"] == current_year - 1) & (df["month_num"] == current_month_num)
    cond_prev_ytd = (df["ปี"] == current_year - 1) & (df["month_num"] <= current_month_num)
    cond_prev_full = (df["ปี"] == current_year - 1)
    
    cond_curr_month = (df["ปี"] == current_year) & (df["month_num"] == current_month_num)
    cond_curr_prev_month = (df["ปี"] == prev_month_year) & (df["month_num"] == prev_month_num)
    cond_curr_ytd = (df["ปี"] == current_year) & (df["month_num"] <= current_month_num)

    s_prev_month = get_units(cond_prev_month_same)
    s_prev_ytd = get_units(cond_prev_ytd)
    s_prev_full = get_units(cond_prev_full)
    s_curr_month = get_units(cond_curr_month)
    s_curr_prev_month = get_units(cond_curr_prev_month)
    s_curr_ytd = get_units(cond_curr_ytd)

    # Identify all unique identities
    all_identities = set()
    for s in [s_prev_month, s_prev_ytd, s_prev_full, s_curr_month, s_curr_prev_month, s_curr_ytd]:
        all_identities.update(s.index.tolist())
        
    # Totals
    gt_prev_month = s_prev_month.sum()
    gt_prev_ytd = s_prev_ytd.sum()
    gt_prev_full = s_prev_full.sum()
    gt_curr_month = s_curr_month.sum()
    gt_curr_prev_month = s_curr_prev_month.sum()
    gt_curr_ytd = s_curr_ytd.sum()

    def safe_div(a, b):
        return (a / b) if pd.notna(a) and pd.notna(b) and b else None
    
    def format_rank_diff(prev_rank: Optional[int], curr_rank: Optional[int]) -> str:
        if pd.isna(prev_rank) or prev_rank is None or prev_rank == 0:
            return "NEW"
        if pd.isna(curr_rank) or curr_rank is None:
            return "—"
        diff = prev_rank - curr_rank
        if diff == 0:
            return "—"
        elif diff > 0:
            return f"+{diff}"
        else:
            return str(diff)

    # Calculate Rank Series based on YTD/Full Year
    s_curr_rank = s_curr_ytd.rank(method="min", ascending=False)
    s_prev_rank = s_prev_full.rank(method="min", ascending=False)

    rows = []
    for ident in all_identities:
        if isinstance(ident, tuple):
            brand, model = str(ident[0]), str(ident[1])
        else:
            brand, model = str(ident), None
            
        u_pm = s_prev_month.get(ident, 0)
        u_pytd = s_prev_ytd.get(ident, 0)
        u_pfull = s_prev_full.get(ident, 0)
        u_cm = s_curr_month.get(ident, 0)
        u_cpm = s_curr_prev_month.get(ident, 0)
        u_cytd = s_curr_ytd.get(ident, 0)
        
        # We store Nones if the value is 0 and it represents an entirely missing period for this brand. 
        # But wait, 0 is fine. Let's keep 0 to match totals, but safe_div will handle it.
        # Actually, let's treat missing as None so we can distinguish 0 sales vs missing.
        u_pm_val = int(u_pm) if ident in s_prev_month else None
        u_pytd_val = int(u_pytd) if ident in s_prev_ytd else None
        u_pfull_val = int(u_pfull) if ident in s_prev_full else None
        u_cm_val = int(u_cm) if ident in s_curr_month else None
        u_cpm_val = int(u_cpm) if ident in s_curr_prev_month else None
        u_cytd_val = int(u_cytd) if ident in s_curr_ytd else None

        sh_pm = safe_div(u_pm_val, gt_prev_month)
        sh_pytd = safe_div(u_pytd_val, gt_prev_ytd)
        sh_pfull = safe_div(u_pfull_val, gt_prev_full)
        sh_cm = safe_div(u_cm_val, gt_curr_month)
        sh_cytd = safe_div(u_cytd_val, gt_curr_ytd)

        growth_prev_month = safe_div(u_cm_val, u_cpm_val) - 1 if (u_cpm_val and u_cm_val is not None) else None
        growth_prev_year_month = safe_div(u_cm_val, u_pm_val) - 1 if (u_pm_val and u_cm_val is not None) else None
        ytd_growth = safe_div(u_cytd_val, u_pytd_val) - 1 if (u_pytd_val and u_cytd_val is not None) else None

        diff_cm = (sh_cm - sh_pm) if sh_cm is not None and sh_pm is not None else None
        diff_cytd = (sh_cytd - sh_pytd) if sh_cytd is not None and sh_pytd is not None else None

        c_rank = int(s_curr_rank.get(ident, 0)) if ident in s_curr_rank else None
        p_rank = int(s_prev_rank.get(ident, 0)) if ident in s_prev_rank else None

        rows.append(CalculationRow(
            brand=brand,
            model=model,
            is_grand_total=False,
            prev_month_units=u_pm_val,
            prev_month_share=sh_pm,
            prev_ytd_units=u_pytd_val,
            prev_ytd_share=sh_pytd,
            prev_full_units=u_pfull_val,
            prev_full_share=sh_pfull,
            curr_month_units=u_cm_val,
            curr_month_share=sh_cm,
            curr_month_diff=diff_cm,
            curr_growth_vs_prev_month=growth_prev_month,
            curr_growth_vs_same_month_prev_year=growth_prev_year_month,
            curr_ytd_units=u_cytd_val,
            curr_ytd_share=sh_cytd,
            curr_ytd_diff=diff_cytd,
            curr_ytd_growth=ytd_growth,
            prev_rank=p_rank,
            curr_rank=c_rank,
            rank_diff=format_rank_diff(p_rank, c_rank)
        ))

    # Sort rows by current YTD units (descending) as default, fallback to current month, then brand name
    rows.sort(key=lambda x: (x.curr_ytd_units or -1, x.curr_month_units or -1, x.brand), reverse=True)

    # Calculate Grand Total Row
    gt_sh_pm = 1.0 if gt_prev_month else None
    gt_sh_pytd = 1.0 if gt_prev_ytd else None
    gt_sh_pfull = 1.0 if gt_prev_full else None
    gt_sh_cm = 1.0 if gt_curr_month else None
    gt_sh_cytd = 1.0 if gt_curr_ytd else None

    gt_growth_prev_month = safe_div(gt_curr_month, gt_curr_prev_month) - 1 if gt_curr_prev_month else None
    gt_growth_prev_year_month = safe_div(gt_curr_month, gt_prev_month) - 1 if gt_prev_month else None
    gt_ytd_growth = safe_div(gt_curr_ytd, gt_prev_ytd) - 1 if gt_prev_ytd else None

    gt_diff_cm = (gt_sh_cm - gt_sh_pm) if gt_sh_cm is not None and gt_sh_pm is not None else None
    gt_diff_cytd = (gt_sh_cytd - gt_sh_pytd) if gt_sh_cytd is not None and gt_sh_pytd is not None else None

    gt_row = CalculationRow(
        brand="Grand Total",
        model=None,
        is_grand_total=True,
        prev_month_units=int(gt_prev_month) if gt_prev_month else None,
        prev_month_share=gt_sh_pm,
        prev_ytd_units=int(gt_prev_ytd) if gt_prev_ytd else None,
        prev_ytd_share=gt_sh_pytd,
        prev_full_units=int(gt_prev_full) if gt_prev_full else None,
        prev_full_share=gt_sh_pfull,
        curr_month_units=int(gt_curr_month) if gt_curr_month else None,
        curr_month_share=gt_sh_cm,
        curr_month_diff=gt_diff_cm,
        curr_growth_vs_prev_month=gt_growth_prev_month,
        curr_growth_vs_same_month_prev_year=gt_growth_prev_year_month,
        curr_ytd_units=int(gt_curr_ytd) if gt_curr_ytd else None,
        curr_ytd_share=gt_sh_cytd,
        curr_ytd_diff=gt_diff_cytd,
        curr_ytd_growth=gt_ytd_growth,
        prev_rank=None,
        curr_rank=None,
        rank_diff=None
    )
    
    rows.insert(0, gt_row)
    
    return rows
