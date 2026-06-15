"""
Reads raw vehicle registration data, adds Brand2 column, writes to Model file as 'Cleaned Data' sheet.
Usage: python transform_to_model.py
"""

import glob
import sys
import os
import pandas as pd
from pathlib import Path

# ── Config ──────────────────────────────────────────────────────────────────
RAW_PATTERN = "รถใหม่_*.xlsx"
MODEL_PATTERN = "*Model*.xlsx"
OUTPUT_SHEET = "Cleaned Data"
RAW_HEADER_ROW = 5

# ── Brand2 mapping ───────────────────────────────────────────────────────────
BRAND2_MAP = {
    "GWM TANK": "GWM",
    "HAVAL": "GWM",
    "ORA": "GWM",
    "GAC": "AION",
    "DEEPAL": "Deepal+ChangAn",
    "MERCEDES": "Mercedes-Benz",
    "MERCEDES BENZ": "Mercedes-Benz",
    "MERCEDES-AMG": "Mercedes-Benz",
    "MERCEDESBENZ-MAYBACH": "Mercedes-Benz",
    "ZX AUTO": "ZX Auto",
    "ZXAUTO": "ZX Auto",
    "STAR8": "Star8",
    "STAR 8": "Star8",
    "STAR8-V": "Star8",
    "ไม่ระบุ": "ไม่ระบุ",
    "พ่วง/กึ่งพ่วง": "ไม่ระบุ",
}


def find_file(pattern: str, label: str) -> Path:
    matches = glob.glob(pattern)
    if not matches:
        print(f"ERROR: No {label} file found matching '{pattern}'")
        sys.exit(1)
    if len(matches) > 1:
        print(f"WARNING: Multiple {label} files found — using most recent: {matches[0]}")
    return Path(sorted(matches)[-1])


def map_brand2(brand: str) -> str:
    if pd.isna(brand):
        return "ไม่ระบุ"
    b = str(brand).strip()
    return BRAND2_MAP.get(b, b)  # default: Brand2 = Brand1 (already top-level)


def unknown_mappings(df: pd.DataFrame) -> list:
    """Return brands that were not in BRAND2_MAP and may need review."""
    mapped = set(BRAND2_MAP.keys())
    all_brands = set(df["ยี่ห้อรถ"].dropna().unique())
    return sorted(all_brands - mapped)


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    base = Path(__file__).resolve().parent.parent.parent  # project root (scripts/ → .claude/ → project)

    raw_file = find_file(str(base / RAW_PATTERN), "raw data")
    model_file = find_file(str(base / MODEL_PATTERN), "Model")

    print(f"Raw file  : {raw_file.name}")
    print(f"Model file: {model_file.name}")
    print()

    # ── Read ─────────────────────────────────────────────────────────────────
    print("Reading raw data...", flush=True)
    df = pd.read_excel(raw_file, header=RAW_HEADER_ROW)
    print(f"  {len(df):,} rows loaded")

    # ── Transform ────────────────────────────────────────────────────────────
    print("Adding Brand2 column...", flush=True)
    df.insert(
        df.columns.get_loc("ยี่ห้อรถ") + 1,
        "ยี่ห้อรถ2",
        df["ยี่ห้อรถ"].apply(map_brand2)
    )

    # ── Report unknowns ──────────────────────────────────────────────────────
    unknowns = unknown_mappings(df)
    if unknowns:
        print(f"\n  {len(unknowns)} brands used Brand1 as Brand2 (no explicit mapping):")
        for b in unknowns[:20]:
            print(f"    - {b}")
        if len(unknowns) > 20:
            print(f"    ... and {len(unknowns) - 20} more")
        print()

    # ── Write cleaned data ───────────────────────────────────────────────────
    # openpyxl is too slow for 200k+ rows with pivot-table workbooks.
    # Write to a separate cleaned_data.xlsx using xlsxwriter (10-50x faster).
    out_file = base / "cleaned_data.xlsx"
    print(f"Writing '{OUTPUT_SHEET}' to {out_file.name} (fast mode)...", flush=True)

    with pd.ExcelWriter(out_file, engine="xlsxwriter") as writer:
        df.to_excel(writer, sheet_name=OUTPUT_SHEET, index=False)

    print(f"  Done — {len(df):,} rows written to {out_file.name}")
    print()
    print("Next step: review Brand2 unknowns above with orchestrator before pivoting.")


if __name__ == "__main__":
    main()
