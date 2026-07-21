"""export_unresolved_series_review.py — Phase 1 read-only export.

Groups the unresolved (non-verified) model-series review queue from
series_admin.list_unresolved() by canonical_brand + canonical_series, so we
can check whether the top 20 groups cover >=60% of unresolved N/A unit
volume. Read-only: no registry writes, no pipeline changes.
"""
from pathlib import Path

import pandas as pd

from series_admin import list_unresolved
from series_registry import ALLOWED_POWERTRAIN

BASE = Path(__file__).resolve().parent
OUT_DIR = BASE / "review"
COVERAGE_THRESHOLD = 0.60
TOP_N = 20

# Admin-edit columns appended to the export. decision values below;
# approved_powertrain must be one of ALLOWED_POWERTRAIN (series_registry.py).
ALLOWED_DECISIONS = {"approve", "keep_na", "skip"}
ADMIN_EDIT_COLUMNS = ["decision", "approved_powertrain", "evidence", "reviewer", "notes"]


def build_group_pivot(queue=None):
    queue = queue if queue is not None else list_unresolved()
    df = pd.DataFrame(queue)

    grouped = df.groupby(["canonical_brand", "canonical_series"]).agg(
        raw_variant_count=("raw_series", "nunique"),
        raw_series_examples=("raw_series", lambda s: "; ".join(sorted(set(s))[:5])),
        total_units=("total_units", "sum"),
    ).reset_index()

    grand_total = grouped["total_units"].sum()
    grouped = grouped.sort_values("total_units", ascending=False).reset_index(drop=True)
    grouped["share_of_unresolved_na"] = grouped["total_units"] / grand_total
    grouped["cumulative_share"] = grouped["share_of_unresolved_na"].cumsum()
    for col in ADMIN_EDIT_COLUMNS:
        grouped[col] = ""
    return grouped, int(grand_total)


def main():
    grouped, grand_total = build_group_pivot()
    OUT_DIR.mkdir(exist_ok=True)
    csv_path = OUT_DIR / "unresolved_group_pivot.csv"
    xlsx_path = OUT_DIR / "unresolved_group_pivot.xlsx"
    grouped.to_csv(csv_path, index=False, encoding="utf-8-sig")
    with pd.ExcelWriter(xlsx_path, engine="openpyxl") as writer:
        grouped.to_excel(writer, index=False, sheet_name="review")
        ws = writer.sheets["review"]
        ws.freeze_panes = "A2"
        ws.auto_filter.ref = ws.dimensions

    top20 = grouped.head(TOP_N)
    top20_units = int(top20["total_units"].sum())
    top20_coverage = top20_units / grand_total if grand_total else 0.0
    verdict = "PASS" if top20_coverage >= COVERAGE_THRESHOLD else "FAIL"

    print(f"total unresolved N/A units: {grand_total}")
    print(f"grouped rows: {len(grouped)}")
    print(f"top {TOP_N} total units: {top20_units}")
    print(f"top {TOP_N} coverage: {top20_coverage:.1%}")
    print(f"{verdict} (threshold {COVERAGE_THRESHOLD:.0%})")
    return grouped


if __name__ == "__main__":
    main()
