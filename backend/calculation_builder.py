import pandas as pd
from dataclasses import dataclass
from typing import Literal, Optional, List

from aggregate import aggregate

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
    elif powertrain != "ALL":
        raise ValueError("Powertrain filters require fuel-grain data")

    # Map month numbers
    if "เดือน" in df.columns:
        df["month_num"] = df["เดือน"].map(MONTH_TO_NUM).fillna(0).astype(int)

    # Identity Columns
    if view_by == "model":
        groupby_cols = ["ยี่ห้อรถ2", "รุ่นรถ2"]
    else:
        groupby_cols = ["ยี่ห้อรถ2"]

    # Filter out records without an identity
    df = df.dropna(subset=groupby_cols)
    
    summary = aggregate(
        df,
        groupby_cols,
        {
            "year_col": "ปี",
            "month_col": "month_num",
            "units_col": "จำนวนรถ",
            "current_year": current_year,
            "current_month_num": current_month_num,
        },
    )
    series = summary.attrs["series"]
    totals = summary.attrs["totals"]

    s_prev_full = series["prev_full"]
    s_curr_ytd = series["curr_ytd"]

    gt_prev_month = totals["prev_month"]
    gt_prev_ytd = totals["prev_ytd"]
    gt_prev_full = totals["prev_full"]
    gt_curr_month = totals["curr_month"]
    gt_curr_prev_month = totals["curr_prev_month"]
    gt_curr_ytd = totals["curr_ytd"]

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
    for _, summary_row in summary.iterrows():
        ident = summary_row["_identity"]
        if isinstance(ident, tuple):
            brand, model = str(ident[0]), str(ident[1])
        else:
            brand, model = str(ident), None

        u_pm_val = summary_row["prev_month_units"]
        u_pytd_val = summary_row["prev_ytd_units"]
        u_pfull_val = summary_row["prev_full_units"]
        u_cm_val = summary_row["curr_month_units"]
        u_cytd_val = summary_row["curr_ytd_units"]

        sh_pm = summary_row["prev_month_share"]
        sh_pytd = summary_row["prev_ytd_share"]
        sh_pfull = summary_row["prev_full_share"]
        sh_cm = summary_row["curr_month_share"]
        sh_cytd = summary_row["curr_ytd_share"]

        growth_prev_month = summary_row["curr_growth_vs_prev_month"]
        growth_prev_year_month = summary_row["curr_growth_vs_same_month_prev_year"]
        ytd_growth = summary_row["curr_ytd_growth"]
        diff_cm = summary_row["curr_month_diff"]
        diff_cytd = summary_row["curr_ytd_diff"]

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
