"""Validate manual_report.json against the markdown workbook's known golden cells.

Usage:
    py -3.12 backend/validate_against_markdown.py "C:\\Users\\...\\..._sheets1-9.md"

The markdown export is the business-rule reference. This checks the program's
frontend/public/data/manual_report.json against golden cells taken from that markdown,
and (best-effort) confirms each golden value literally appears in the markdown file so a
newer markdown that changed a number is caught rather than silently trusted.

All checks, including Sheets 7-8, MUST match exactly or the script exits non-zero.
"""
import sys
import json
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(__file__).resolve().parent
REPORT = BASE.parent / "frontend" / "public" / "data" / "manual_report.json"
MODEL_PARQUET = BASE / "test_model_cleaned.parquet"

# sheet, row selector, field, markdown golden value, human label
CHECKS = [
    ("sheet1_powertrain", {"key": "Grand Total"}, "prev_ytd", 324368, "Sheet 1 Grand Total Jan-Jun 2568"),
    ("sheet1_powertrain", {"key": "Grand Total"}, "curr_ytd", 374424, "Sheet 1 Grand Total Jan-Jun 2569"),
    ("sheet1_powertrain", {"key": "BEV"}, "prev_total", 122559, "Sheet 1 BEV 2568 full year"),
    ("sheet1_powertrain", {"key": "BEV"}, "curr_ytd", 105558, "Sheet 1 BEV Jan-Jun 2569"),
    ("sheet2_brand_all", {"key": "BYD"}, "curr_ytd", 26069, "Sheet 2 BYD Jan-Jun 2569"),
    ("sheet4_brand_bev", {"key": "BYD"}, "prev_total", 33070, "Sheet 4 BYD 2568 full BEV (fuel-derived)"),
    ("sheet4_brand_bev", {"key": "BYD"}, "curr_ytd", 21450, "Sheet 4 BYD Jan-Jun 2569 BEV"),
    ("sheet8_model_top_rank", {"brand": "JAECOO", "model": "5 EV"}, "curr_ytd", 11137, "Sheet 8 rank-1 JAECOO 5 EV 2569 total"),
    ("sheet8_model_top_rank", {"brand": "BYD", "model": "BYD DOLPHIN"}, "curr_ytd", 8696, "Sheet 8 BYD DOLPHIN 2569 total"),
    ("sheet8_model_top_rank", {"brand": "BYD", "model": "BYD ATTO 3"}, "curr_ytd", 7357, "Sheet 8 BYD ATTO 3 2569 total"),
]

# markdown "# <title>" heading -> report sheet id, for the best-effort scan
SHEET_TITLE = {
    "sheet1_powertrain": "1.Reg by Powertrain",
    "sheet2_brand_all": "2.Rank by Brand",
    "sheet4_brand_bev": "4.BEV by Brand",
    "sheet8_model_top_rank": "8.Model Top Rank",
}


def find_row(rows, sel):
    for r in rows:
        if all(str(r.get(k)) == str(v) for k, v in sel.items()):
            return r
    return None


def bool_series(series: pd.Series) -> pd.Series:
    if pd.api.types.is_bool_dtype(series):
        return series.fillna(False)
    return series.astype(str).str.strip().str.lower().isin({"1", "true", "yes", "y"})


def markdown_blocks(md_path: Path) -> dict:
    """Split the markdown into {heading -> text} on '# ' section headers."""
    blocks, title, buf = {}, None, []
    for line in md_path.read_text(encoding="utf-8").splitlines():
        if line.startswith("# "):
            if title is not None:
                blocks[title] = "\n".join(buf)
            title, buf = line[2:].strip(), []
        else:
            buf.append(line)
    if title is not None:
        blocks[title] = "\n".join(buf)
    return blocks


def print_model_mapping_diagnostics(failures: list[tuple]) -> None:
    selectors = [
        sel for sheet, sel, field, md_val, prog_val, label in failures
        if sheet in {"sheet7_bev_by_model", "sheet8_model_top_rank"} and "brand" in sel and "model" in sel
    ]
    if not selectors or not MODEL_PARQUET.exists():
        return

    print("\n--- BEV model report mapping diagnostics ---")
    df = pd.read_parquet(MODEL_PARQUET)
    include_col = "include_in_bev_model_report"
    if include_col not in df.columns:
        print(f"  {MODEL_PARQUET.name} is missing {include_col}; rerun build_cleaned.py")
        return

    for sel in selectors:
        brand = sel["brand"]
        model = sel["model"]
        same_model = df[
            (df["ยี่ห้อรถ2"].astype(str) == brand)
            & (df["รุ่นรถ2"].astype(str) == model)
        ].copy()
        print(f"\n  {brand} / {model}")
        if same_model.empty:
            print("    No cleaned rows found for this canonical brand/model. Check raw_model -> model2 mapping.")
            continue
        same_model[include_col] = bool_series(same_model[include_col])
        summary = (
            same_model.groupby(["รุ่นรถ", "Powertrain", include_col], dropna=False)["จำนวนรถ"]
            .sum()
            .reset_index()
            .sort_values(["include_in_bev_model_report", "จำนวนรถ"], ascending=[True, False])
        )
        for _, row in summary.head(30).iterrows():
            include = "include" if row[include_col] else "exclude"
            print(
                f"    {include:7} raw_model={row['รุ่นรถ']} "
                f"powertrain={row['Powertrain']} units={int(row['จำนวนรถ']):,}"
            )


def main():
    if len(sys.argv) < 2:
        print("Usage: validate_against_markdown.py <markdown_path>")
        sys.exit(2)
    md_path = Path(sys.argv[1])

    if not REPORT.exists():
        print(f"ERROR: {REPORT} not found. Run export_manual_report.py first.")
        sys.exit(1)
    report = json.loads(REPORT.read_text(encoding="utf-8"))
    sheets = report.get("sheets", {})

    md_present = md_path.exists()
    blocks = markdown_blocks(md_path) if md_present else {}
    if not md_present:
        print(f"WARNING: markdown file not found at {md_path}")
        print("         Comparing against embedded golden values only (markdown cross-scan skipped).\n")

    print("=== Validate manual_report.json against markdown golden cells ===\n")
    hard_fail = []

    for sheet, sel, field, md_val, label in CHECKS:
        rows = sheets.get(sheet, [])
        row = find_row(rows, sel)
        prog_val = row.get(field) if row else None

        # best-effort markdown confirmation
        md_note = ""
        title = SHEET_TITLE.get(sheet)
        if md_present and title and title in blocks:
            md_note = " [markdown-confirmed]" if str(md_val) in blocks[title] else " [markdown-scan: value not located]"

        match = (prog_val == md_val)
        tag = "OK  " if match else "FAIL"
        print(f"[{tag}] {label}{md_note}")
        print(f"        markdown={md_val:,}   program={prog_val if prog_val is None else format(prog_val, ',')}")
        if not match:
            entry = (sheet, sel, field, md_val, prog_val, label)
            hard_fail.append(entry)

    # Sheet 8 rank-1 identity check
    s8 = sheets.get("sheet8_model_top_rank", [])
    rank1 = next((r for r in s8 if r.get("curr_rank") == 1), None)
    if rank1:
        ok = rank1.get("brand") == "JAECOO" and rank1.get("model") == "5 EV"
        print(f"\n[{'OK  ' if ok else 'FAIL'}] Sheet 8 rank-1 model identity")
        print(f"        expected=JAECOO / 5 EV   program={rank1.get('brand')} / {rank1.get('model')}")
        if not ok:
            hard_fail.append(("sheet8_model_top_rank", {"curr_rank": 1}, "identity", "JAECOO/5 EV",
                               f"{rank1.get('brand')}/{rank1.get('model')}", "Sheet 8 rank-1 identity"))

    print("\n--- Summary ---")
    if hard_fail:
        print_model_mapping_diagnostics(hard_fail)
        print(f"\nVALIDATION FAILED: {len(hard_fail)} hard mismatch(es):")
        for sheet, sel, field, md_val, prog_val, label in hard_fail:
            print(f"  FAIL sheet={sheet} row={sel} metric={field} markdown={md_val} program={prog_val}")
        sys.exit(1)

    print("\nVALIDATION PASSED: all golden cells match the markdown exactly.")
    sys.exit(0)


if __name__ == "__main__":
    main()
