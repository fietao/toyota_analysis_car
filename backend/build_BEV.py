#!/usr/bin/env python3
"""
build_BEV.py — Append approved BEV review rows to BEV Series Name Table.

Reads:  pipeline_state.json
Writes: BEV Series Name Table in the current master Model workbook

All BEV/BMW pivot sheets are read-only to Python. Excel owns those pivots.
"""

import json
import re
import sys
import zipfile
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(__file__).resolve().parent
STATE_PATH = BASE / "pipeline_state.json"


def _col(n):
    r = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        r = chr(65 + rem) + r
    return r


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
                 .replace(">", "&gt;").replace('"', "&quot;"))


def _find_sheet_xml_paths(wb_xml, rels_xml, sheet_name):
    """Return all xl/... paths for a named sheet."""
    rids = re.findall(
        rf'<sheet\b[^>]*\bname="{re.escape(sheet_name)}"[^>]*\br:id="([^"]+)"[^>]*/>',
        wb_xml,
    )
    rids += re.findall(
        rf'<sheet\b[^>]*\br:id="([^"]+)"[^>]*\bname="{re.escape(sheet_name)}"[^>]*/>',
        wb_xml,
    )
    paths = []
    for rid in dict.fromkeys(rids):
        rel_m = re.search(rf'<Relationship\b(?=[^>]*\bId="{re.escape(rid)}")[^>]*/?>',  rels_xml)
        target_m = re.search(r'\bTarget="([^"]+)"', rel_m.group(0)) if rel_m else None
        if target_m:
            target = target_m.group(1).lstrip("/")
            paths.append(f"xl/{target}" if not target.startswith("xl/") else target)
    return paths


def append_bev_rows_zip(master_path, new_bev_records):
    """Append approved BEV model rows to BEV Series Name Table via ZIP manipulation."""
    if not new_bev_records:
        print("  BEV Series Name Table — no approved rows to append")
        return

    with zipfile.ZipFile(str(master_path), "r") as z:
        wb_xml = z.read("xl/workbook.xml").decode("utf-8")
        rels_xml = z.read("xl/_rels/workbook.xml.rels").decode("utf-8")

    paths = _find_sheet_xml_paths(wb_xml, rels_xml, "BEV Series Name Table")
    sheet_path = paths[0] if paths else None
    if not sheet_path:
        print("  WARNING: BEV Series Name Table not found — skipping")
        return

    with zipfile.ZipFile(str(master_path), "r") as z:
        old_xml = z.read(sheet_path).decode("utf-8")

    # Find the last row that has actual cell content.
    # The sheet may have thousands of pre-formatted empty rows; we must not
    # use those to determine where to append — only rows with a <c ...> element count.
    row_nums = [int(n) for n in re.findall(r'<row\b[^>]*\br="(\d+)"[^>]*><c\b', old_xml)]
    next_row = max(row_nums) + 1 if row_nums else 2

    df_new = pd.DataFrame(new_bev_records)[["Brand", "รุ่นรถ", "รุ่นรถ2", "Powertrain"]]
    df_new = df_new.drop_duplicates().sort_values(["Brand", "รุ่นรถ2", "รุ่นรถ"]).reset_index(drop=True)

    rows_xml = []
    for r_idx, row in enumerate(df_new.itertuples(index=False), next_row):
        cells = [
            f'<c r="{_col(c_idx)}{r_idx}" t="inlineStr"><is><t>{_esc(str(v))}</t></is></c>'
            for c_idx, v in enumerate(row, 1)
        ]
        rows_xml.append(f'<row r="{r_idx}">{"".join(cells)}</row>')

    last_row = next_row + len(df_new) - 1
    new_xml = old_xml.replace("</sheetData>", "".join(rows_xml) + "</sheetData>")
    if re.search(r'<dimension\b[^>]*\bref="[^"]+"', new_xml):
        new_xml = re.sub(
            r'(<dimension\b[^>]*\bref=")[^"]+"',
            rf'\g<1>A1:D{last_row}"',
            new_xml,
            count=1,
        )

    tmp = master_path.with_suffix(".tmp.xlsx")
    with zipfile.ZipFile(str(master_path), "r") as zin, \
         zipfile.ZipFile(str(tmp), "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            zout.writestr(
                item,
                new_xml.encode("utf-8") if item.filename == sheet_path else zin.read(item.filename),
            )
    tmp.replace(master_path)
    print(f"  BEV Series Name Table — appended {len(df_new)} approved row(s)")


def main():
    if not STATE_PATH.exists():
        print("ERROR: pipeline_state.json not found — run build_cleaned.py first")
        sys.exit(1)

    state = json.loads(STATE_PATH.read_text("utf-8"))
    out_path = BASE / state["master_model"]
    if not out_path.exists():
        print(f"ERROR: {out_path.name} not found — run build_cleaned.py first")
        sys.exit(1)

    new_bev_records = state.get("new_bev_models", [])
    print(f"Updating {out_path.name} via ZIP...", flush=True)
    print(f"  Approved BEV rows from state: {len(new_bev_records)}")
    append_bev_rows_zip(out_path, new_bev_records)
    print(f"\nDone: {out_path.name}")


if __name__ == "__main__":
    main()
