"""Validate fuel-grain output against the exported Markdown workbook.

Usage:
    py -3.12 backend/validate_against_markdown.py <sheets1-9.md> [Data.md]

Data.md is authoritative only at its own fuel grain. It contains no model column,
so this validator never uses it to approve or infer a model Powertrain. Sheets 7-8
use human-approved BEV rows from config/model_powertrain_review.csv; the legacy
Markdown is not their release authority.
"""
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

import pandas as pd

from model_map import load_model_powertrain_review

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(__file__).resolve().parent
REPORT = BASE.parent / "frontend" / "public" / "data" / "manual_report.json"
FUEL_PARQUET = BASE / "test_fuel_cleaned.parquet"
DEFAULT_VEHICLE_TYPES = {"รย.1", "รย.2", "รย.3", "รย.6", "รย.9", "รย.10", "รย.11"}

DATA_COLUMNS = [
    "ปี", "เดือน", "ประเภทรถ", "จังหวัด", "ยี่ห้อรถ", "ยี่ห้อรถ2",
    "ชนิดเชื้อเพลิง", "Powertrain", "จำนวนรถ",
]
FUEL_FACT_COLUMNS = [
    "ปี", "เดือน", "ประเภทรถ", "จังหวัด", "ยี่ห้อรถ",
    "ชนิดเชื้อเพลิง", "Powertrain",
]

# Presentation checks for fuel-derived sheets.  Series-derived Sheets 7-8 are
# deliberately absent because the Markdown does not prove series-powertrain facts.
FUEL_CHECKS = [
    ("sheet1_powertrain", {"key": "Grand Total"}, "prev_ytd", 324368, "Sheet 1 Grand Total Jan-Jun 2568"),
    ("sheet1_powertrain", {"key": "Grand Total"}, "curr_ytd", 374424, "Sheet 1 Grand Total Jan-Jun 2569"),
    ("sheet1_powertrain", {"key": "BEV"}, "prev_total", 122559, "Sheet 1 BEV 2568 full year"),
    ("sheet1_powertrain", {"key": "BEV"}, "curr_ytd", 105558, "Sheet 1 BEV Jan-Jun 2569"),
    ("sheet2_brand_all", {"key": "BYD"}, "curr_ytd", 26069, "Sheet 2 BYD Jan-Jun 2569"),
    ("sheet4_brand_bev", {"key": "BYD"}, "prev_total", 33070, "Sheet 4 BYD 2568 full BEV"),
    ("sheet4_brand_bev", {"key": "BYD"}, "curr_ytd", 21450, "Sheet 4 BYD Jan-Jun 2569 BEV"),
]

SHEET_TITLE = {
    "sheet1_powertrain": "1.Reg by Powertrain",
    "sheet2_brand_all": "2.Rank by Brand",
    "sheet4_brand_bev": "4.BEV by Brand",
}
REQUIRED_HEADINGS = {
    "1.Reg by Powertrain", "2.Rank by Brand", "3.ICE by Brand", "4.BEV by Brand",
    "5.HEV by Brand", "6.PHEV by Brand", "7.BEV by Model", "8.Model Top Rank",
    "9.by Province",
}


def vehicle_code(label):
    match = re.match(r"รย\.\s*0*(\d+)", str(label).strip())
    return f"รย.{int(match.group(1))}" if match else str(label).strip()


def infer_data_path(sheets_path: Path) -> Path:
    name = sheets_path.name.replace("_sheets1-9.md", "_Data.md")
    return sheets_path.with_name(name)


def markdown_blocks(md_path: Path) -> dict:
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


def parse_data_markdown(path: Path):
    """Stream Data.md into an exact fuel-fact counter without loading 44MB at once."""
    facts = Counter()
    all_units = 0
    rows = 0
    header_found = False
    with path.open(encoding="utf-8") as handle:
        for line in handle:
            if not line.startswith("|"):
                continue
            cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
            if not header_found:
                if cells[:len(DATA_COLUMNS)] == DATA_COLUMNS:
                    header_found = True
                continue
            if len(cells) < len(DATA_COLUMNS) or not cells[0].isdigit():
                continue
            row = dict(zip(DATA_COLUMNS, cells[:len(DATA_COLUMNS)]))
            try:
                units = int(row["จำนวนรถ"].replace(",", ""))
            except ValueError as exc:
                raise ValueError(f"Invalid จำนวนรถ in Data.md row: {cells[:len(DATA_COLUMNS)]}") from exc
            rows += 1
            all_units += units
            if vehicle_code(row["ประเภทรถ"]) in DEFAULT_VEHICLE_TYPES:
                key = tuple(row[column].strip() for column in FUEL_FACT_COLUMNS)
                facts[key] += units
    if not header_found:
        raise ValueError(f"Data header not found in {path}")
    return facts, rows, all_units


def parquet_fuel_facts(path: Path):
    df = pd.read_parquet(path, columns=DATA_COLUMNS)
    missing = [column for column in DATA_COLUMNS if column not in df.columns]
    if missing:
        raise ValueError(f"Fuel parquet missing columns: {missing}")
    units = pd.to_numeric(df["จำนวนรถ"], errors="raise").astype(int)
    all_units = int(units.sum())
    scoped = df["ประเภทรถ"].map(vehicle_code).isin(DEFAULT_VEHICLE_TYPES)
    work = df.loc[scoped, FUEL_FACT_COLUMNS].copy()
    work["จำนวนรถ"] = units.loc[scoped]
    grouped = work.groupby(FUEL_FACT_COLUMNS, dropna=False, as_index=False)["จำนวนรถ"].sum()
    facts = Counter()
    for row in grouped.itertuples(index=False, name=None):
        key = tuple("" if pd.isna(value) else str(value).strip() for value in row[:-1])
        facts[key] += int(row[-1])
    return facts, len(df), all_units


def compare_fuel_grain(data_path: Path):
    markdown, md_rows, md_total = parse_data_markdown(data_path)
    parquet, pq_rows, pq_total = parquet_fuel_facts(FUEL_PARQUET)
    differences = markdown - parquet
    reverse = parquet - markdown
    ok = md_total == pq_total and not differences and not reverse
    print("\n--- Data.md fuel-grain gate ---")
    print(f"[{'OK  ' if md_total == pq_total else 'FAIL'}] all-vehicle total: Markdown={md_total:,} parquet={pq_total:,}")
    print(f"       source rows: Markdown={md_rows:,} parquet={pq_rows:,}")
    print(f"[{'OK  ' if not differences and not reverse else 'FAIL'}] report-scope facts "
          f"({', '.join(sorted(DEFAULT_VEHICLE_TYPES))}): Markdown={sum(markdown.values()):,} "
          f"parquet={sum(parquet.values()):,}")
    if differences or reverse:
        print("       first mismatches (Markdown-only / parquet-only):")
        for key, units in list(differences.items())[:5]:
            print(f"       MD +{units:,}: {key}")
        for key, units in list(reverse.items())[:5]:
            print(f"       PQ +{units:,}: {key}")
    print("[INFO] ยี่ห้อรถ2 is excluded: it is a maintained canonical mapping, not a raw fact.")
    print("[INFO] Data.md has no series column and cannot validate series Powertrain.")
    return ok


def find_row(rows, selector):
    return next((row for row in rows if all(str(row.get(k)) == str(v) for k, v in selector.items())), None)


def main():
    if len(sys.argv) >= 2:
        sheets_arg = sys.argv[1]
    elif os.environ.get("MARKDOWN_REPORT_PATH"):
        sheets_arg = os.environ["MARKDOWN_REPORT_PATH"]
    else:
        print("Usage: validate_against_markdown.py <sheets1-9.md> [Data.md]")
        print("       (or set the MARKDOWN_REPORT_PATH environment variable)")
        sys.exit(2)
    sheets_path = Path(sheets_arg)
    data_path = Path(sys.argv[2]) if len(sys.argv) > 2 else infer_data_path(sheets_path)
    failures = []

    if not sheets_path.exists() or not data_path.exists():
        missing = [str(path) for path in (sheets_path, data_path) if not path.exists()]
        print(f"VALIDATION FAILED: missing Markdown source(s): {missing}")
        sys.exit(1)
    if not REPORT.exists() or not FUEL_PARQUET.exists():
        print(f"VALIDATION FAILED: missing generated artifact: {REPORT if not REPORT.exists() else FUEL_PARQUET}")
        sys.exit(1)

    print("=== Markdown-backed validation (source grains kept separate) ===")
    blocks = markdown_blocks(sheets_path)
    missing_headings = sorted(REQUIRED_HEADINGS - set(blocks))
    print(f"[{'OK  ' if not missing_headings else 'FAIL'}] Sheets 1-9 headings present")
    if missing_headings:
        failures.append(f"missing headings: {missing_headings}")

    try:
        if not compare_fuel_grain(data_path):
            failures.append("Data.md does not exactly reconcile to the fuel parquet")
    except Exception as exc:
        print(f"[FAIL] Data.md fuel-grain gate: {exc}")
        failures.append(str(exc))

    report = json.loads(REPORT.read_text(encoding="utf-8"))
    sheets = report.get("sheets", {})
    print("\n--- Fuel-derived report presentation checks ---")
    for sheet, selector, field, expected, label in FUEL_CHECKS:
        row = find_row(sheets.get(sheet, []), selector)
        actual = row.get(field) if row else None
        title = SHEET_TITLE[sheet]
        located = str(expected) in blocks.get(title, "")
        ok = actual == expected and located
        print(f"[{'OK  ' if ok else 'FAIL'}] {label}: Markdown={expected:,} program={actual}")
        if not ok:
            failures.append(f"{label}: expected {expected}, got {actual}, markdown-located={located}")

    approved_bev = [
        row for row in load_model_powertrain_review().values()
        if row["review_status"] == "approved" and row["candidate_powertrain"] == "BEV"
    ]
    print("\n--- Model report authority ---")
    if approved_bev:
        print(f"[INFO] Model review CSV contains {len(approved_bev):,} approved BEV raw models.")
        print("[INFO] Sheets 7-8 are generated from those reviewed rows; legacy Markdown is comparison-only.")
    else:
        print("[BLOCKED] Sheets 7-8 accuracy: model review CSV has no approved BEV models.")
        print("          Keep these sheets empty until a maintainer records evidence and approves rows.")

    print("\n--- Summary ---")
    if failures:
        print(f"VALIDATION FAILED: {len(failures)} release-gate failure(s)")
        for failure in failures:
            print(f"  - {failure}")
        sys.exit(1)
    print("VALIDATION PASSED for fuel-grain facts and fuel-derived report cells.")
    print("MODEL REVIEW STATUS: pending rows remain excluded until human approval; no guessing performed.")


if __name__ == "__main__":
    main()
