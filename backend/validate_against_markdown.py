"""Validate manual_report.json against the markdown workbook's known golden cells.

Usage:
    py -3.12 backend/validate_against_markdown.py "C:\\Users\\...\\..._sheets1-9.md"

The markdown export is the business-rule reference. This checks the program's
frontend/public/data/manual_report.json against golden cells taken from that markdown,
and (best-effort) confirms each golden value literally appears in the markdown file so a
newer markdown that changed a number is caught rather than silently trusted.

Hard checks (fuel-derived, sheets 1-6/9) MUST match exactly or the script exits non-zero.
Known-issue checks (model-table BEV Major, sheets 7-8) are reported but do NOT fail the
gate — they are the documented BEV-review vintage gap (see the spec's Known Open Issue).
"""
import sys
import json
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(__file__).resolve().parent
REPORT = BASE.parent / "frontend" / "public" / "data" / "manual_report.json"

# sheet, row selector, field, markdown golden value, human label, known-issue flag
CHECKS = [
    ("sheet1_powertrain", {"key": "Grand Total"}, "prev_ytd", 324368, "Sheet 1 Grand Total Jan-Jun 2568", False),
    ("sheet1_powertrain", {"key": "Grand Total"}, "curr_ytd", 374424, "Sheet 1 Grand Total Jan-Jun 2569", False),
    ("sheet1_powertrain", {"key": "BEV"}, "prev_total", 122559, "Sheet 1 BEV 2568 full year", False),
    ("sheet1_powertrain", {"key": "BEV"}, "curr_ytd", 105558, "Sheet 1 BEV Jan-Jun 2569", False),
    ("sheet2_brand_all", {"key": "BYD"}, "curr_ytd", 26069, "Sheet 2 BYD Jan-Jun 2569", False),
    ("sheet4_brand_bev", {"key": "BYD"}, "prev_total", 33070, "Sheet 4 BYD 2568 full BEV (fuel-derived)", False),
    ("sheet4_brand_bev", {"key": "BYD"}, "curr_ytd", 21450, "Sheet 4 BYD Jan-Jun 2569 BEV", False),
    ("sheet8_model_top_rank", {"brand": "JAECOO", "model": "5 EV"}, "curr_ytd", 11137, "Sheet 8 rank-1 JAECOO 5 EV 2569 total", True),
    ("sheet8_model_top_rank", {"brand": "BYD", "model": "BYD DOLPHIN"}, "curr_ytd", 8696, "Sheet 8 BYD DOLPHIN 2569 total", True),
    ("sheet8_model_top_rank", {"brand": "BYD", "model": "BYD ATTO 3"}, "curr_ytd", 7357, "Sheet 8 BYD ATTO 3 2569 total", True),
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
    known_diff = []

    for sheet, sel, field, md_val, label, known in CHECKS:
        rows = sheets.get(sheet, [])
        row = find_row(rows, sel)
        prog_val = row.get(field) if row else None

        # best-effort markdown confirmation
        md_note = ""
        title = SHEET_TITLE.get(sheet)
        if md_present and title and title in blocks:
            md_note = " [markdown-confirmed]" if str(md_val) in blocks[title] else " [markdown-scan: value not located]"

        match = (prog_val == md_val)
        tag = "OK  " if match else ("KNOWN" if known else "FAIL")
        print(f"[{tag}] {label}{md_note}")
        print(f"        markdown={md_val:,}   program={prog_val if prog_val is None else format(prog_val, ',')}")
        if not match:
            entry = (sheet, sel, field, md_val, prog_val, label)
            (known_diff if known else hard_fail).append(entry)

    # Sheet 8 rank-1 identity check
    s8 = sheets.get("sheet8_model_top_rank", [])
    rank1 = next((r for r in s8 if r.get("curr_rank") == 1), None)
    if rank1:
        ok = rank1.get("brand") == "JAECOO" and rank1.get("model") == "5 EV"
        print(f"\n[{'OK  ' if ok else 'KNOWN'}] Sheet 8 rank-1 model identity")
        print(f"        expected=JAECOO / 5 EV   program={rank1.get('brand')} / {rank1.get('model')}")
        if not ok:
            known_diff.append(("sheet8_model_top_rank", {"curr_rank": 1}, "identity", "JAECOO/5 EV",
                               f"{rank1.get('brand')}/{rank1.get('model')}", "Sheet 8 rank-1 identity"))

    print("\n--- Summary ---")
    if known_diff:
        print(f"KNOWN mismatches (documented, non-blocking): {len(known_diff)}")
        for sheet, sel, field, md_val, prog_val, label in known_diff:
            print(f"  - sheet={sheet} row={sel} metric={field} markdown={md_val} program={prog_val}")
        print("  Reason: sheets 7-8 use model-table Powertrain=='BEV Major', a slightly older BEV-review")
        print("  vintage than the workbook (see meta.known_mismatches). Fuel-derived sheets match exactly.")

    if hard_fail:
        print(f"\nVALIDATION FAILED: {len(hard_fail)} hard mismatch(es):")
        for sheet, sel, field, md_val, prog_val, label in hard_fail:
            print(f"  FAIL sheet={sheet} row={sel} metric={field} markdown={md_val} program={prog_val}")
        sys.exit(1)

    print("\nVALIDATION PASSED: all fuel-derived golden cells match the markdown exactly.")
    sys.exit(0)


if __name__ == "__main__":
    main()
