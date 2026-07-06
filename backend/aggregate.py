from __future__ import annotations

from typing import Any

import pandas as pd


def current_period(
    df: pd.DataFrame,
    *,
    year_col: str,
    month_col: str,
    month_to_num: dict[Any, int] | None = None,
    month_order: list[Any] | None = None,
) -> tuple[int, int]:
    years = sorted(df[year_col].dropna().unique())
    curr_year = int(years[-1])
    curr = df[df[year_col] == curr_year]
    months = _month_numbers(curr[month_col], month_to_num=month_to_num, month_order=month_order)
    return curr_year, int(months.max())


def aggregate(df: pd.DataFrame, group_by: list[str], period: dict[str, Any]) -> pd.DataFrame:
    mode = period.get("mode", "calculation")
    if mode == "monthly":
        return _monthly(df, group_by, period)
    if mode == "calculation":
        return _calculation(df, group_by, period)
    raise ValueError(f"Unknown aggregate mode: {mode}")


def _month_numbers(
    months: pd.Series,
    *,
    month_to_num: dict[Any, int] | None = None,
    month_order: list[Any] | None = None,
) -> pd.Series:
    if month_to_num is not None:
        return months.map(month_to_num).fillna(0).astype(int)
    if month_order is not None:
        lookup = {m: i + 1 for i, m in enumerate(month_order)}
        return months.map(lookup).fillna(0).astype(int)
    return pd.to_numeric(months, errors="coerce").fillna(0).astype(int)


def _monthly(df: pd.DataFrame, group_by: list[str], period: dict[str, Any]) -> pd.DataFrame:
    units_col = period["units_col"]
    grouped = df.groupby(group_by)[units_col].sum().reset_index()
    return grouped[grouped[units_col] > 0]


def _calculation(df: pd.DataFrame, group_by: list[str], period: dict[str, Any]) -> pd.DataFrame:
    year_col = period["year_col"]
    month_col = period["month_col"]
    units_col = period["units_col"]
    current_year = period["current_year"]
    current_month_num = period["current_month_num"]
    prev_year = period.get("prev_year", current_year - 1)

    work = df.copy()
    work["_agg_month_num"] = _month_numbers(
        work[month_col],
        month_to_num=period.get("month_to_num"),
        month_order=period.get("month_order"),
    )

    if current_month_num == 1:
        prev_month_year = current_year - 1
        prev_month_num = 12
    else:
        prev_month_year = current_year
        prev_month_num = current_month_num - 1

    def get_units(condition: pd.Series) -> pd.Series:
        sub = work[condition]
        if sub.empty:
            return pd.Series(dtype=int)
        return sub.groupby(group_by)[units_col].sum()

    cond_prev_month = (work[year_col] == prev_year) & (work["_agg_month_num"] == current_month_num)
    cond_prev_ytd = (work[year_col] == prev_year) & (work["_agg_month_num"] <= current_month_num)
    cond_prev_full = work[year_col] == prev_year
    cond_curr_month = (work[year_col] == current_year) & (work["_agg_month_num"] == current_month_num)
    cond_curr_prev_month = (work[year_col] == prev_month_year) & (work["_agg_month_num"] == prev_month_num)
    cond_curr_ytd = (work[year_col] == current_year) & (work["_agg_month_num"] <= current_month_num)

    series = {
        "prev_month": get_units(cond_prev_month),
        "prev_ytd": get_units(cond_prev_ytd),
        "prev_full": get_units(cond_prev_full),
        "curr_month": get_units(cond_curr_month),
        "curr_prev_month": get_units(cond_curr_prev_month),
        "curr_ytd": get_units(cond_curr_ytd),
    }
    totals = {name: values.sum() for name, values in series.items()}

    all_identities = set()
    for values in series.values():
        all_identities.update(values.index.tolist())

    def safe_div(a: Any, b: Any) -> float | None:
        return (a / b) if pd.notna(a) and pd.notna(b) and b else None

    rows = []
    for ident in all_identities:
        row: dict[str, Any] = {"_identity": ident}
        if len(group_by) == 1:
            row[group_by[0]] = ident
        else:
            for col, value in zip(group_by, ident):
                row[col] = value

        for name, values in series.items():
            row[f"{name}_units"] = int(values.get(ident, 0)) if ident in values else None

        row["prev_month_share"] = safe_div(row["prev_month_units"], totals["prev_month"])
        row["prev_ytd_share"] = safe_div(row["prev_ytd_units"], totals["prev_ytd"])
        row["prev_full_share"] = safe_div(row["prev_full_units"], totals["prev_full"])
        row["curr_month_share"] = safe_div(row["curr_month_units"], totals["curr_month"])
        row["curr_ytd_share"] = safe_div(row["curr_ytd_units"], totals["curr_ytd"])

        row["curr_growth_vs_prev_month"] = (
            safe_div(row["curr_month_units"], row["curr_prev_month_units"]) - 1
            if row["curr_prev_month_units"] and row["curr_month_units"] is not None
            else None
        )
        row["curr_growth_vs_same_month_prev_year"] = (
            safe_div(row["curr_month_units"], row["prev_month_units"]) - 1
            if row["prev_month_units"] and row["curr_month_units"] is not None
            else None
        )
        row["curr_ytd_growth"] = (
            safe_div(row["curr_ytd_units"], row["prev_ytd_units"]) - 1
            if row["prev_ytd_units"] and row["curr_ytd_units"] is not None
            else None
        )
        row["curr_month_diff"] = (
            row["curr_month_share"] - row["prev_month_share"]
            if row["curr_month_share"] is not None and row["prev_month_share"] is not None
            else None
        )
        row["curr_ytd_diff"] = (
            row["curr_ytd_share"] - row["prev_ytd_share"]
            if row["curr_ytd_share"] is not None and row["prev_ytd_share"] is not None
            else None
        )
        rows.append(row)

    result = pd.DataFrame(rows, dtype=object)
    result.attrs["series"] = series
    result.attrs["totals"] = totals
    return result
