#!/usr/bin/env python3
"""
read_raw.py — Read any DLT raw Excel file and print a summary.

Standalone tool any agent can call with any file path.

Usage:
    python .claude/scripts/read_raw.py <path_to_xlsx>
    python .claude/scripts/read_raw.py  (auto-finds latest raw files)
"""

import sys
import glob
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(__file__).resolve().parents[2]


def read_dlt_file(path: Path) -> pd.DataFrame:
    """Read a DLT raw xlsx. Header is always at row index 5 (row 6 in Excel)."""
    df = pd.read_excel(str(path), header=5)
    if "จำนวนรถ" in df.columns:
        df["จำนวนรถ"] = pd.to_numeric(df["จำนวนรถ"], errors="coerce").fillna(0).astype(int)
    return df


def summarise(df: pd.DataFrame, label: str):
    print(f"\n{'='*60}")
    print(f"FILE: {label}")
    print(f"  Rows    : {len(df):,}")
    print(f"  Columns : {list(df.columns)}")
    if "ปี" in df.columns:
        print(f"  Years   : {sorted(df['ปี'].dropna().unique().tolist())}")
    if "เดือน" in df.columns:
        print(f"  Months  : {df['เดือน'].dropna().unique().tolist()}")
    if "จำนวนรถ" in df.columns:
        print(f"  Total registrations: {df['จำนวนรถ'].sum():,}")
    print(f"  Sample row:")
    print(f"    {df.iloc[0].to_dict()}")
    for col in df.columns:
        n_null   = int(df[col].isna().sum())
        n_unique = int(df[col].nunique())
        sample   = df[col].dropna().astype(str).unique()[:3].tolist()
        print(f"  {col}: {n_unique} unique, {n_null} nulls, sample={sample}")


def main():
    if len(sys.argv) > 1:
        # Explicit file path
        paths = [Path(sys.argv[1])]
    else:
        # Auto-find latest raw files
        raw1 = [f for f in glob.glob(str(BASE / "raw data" / "รถใหม่_ยี่ห้อรถ-ชนิดเชื้อเพลิง*.xlsx")) if "~$" not in f]
        raw2 = [f for f in glob.glob(str(BASE / "raw data" / "รถใหม่_ยี่ห้อรถ-รุ่นรถ*.xlsx")) if "~$" not in f]
        paths = []
        if raw1: paths.append(Path(sorted(raw1)[-1]))
        if raw2: paths.append(Path(sorted(raw2)[-1]))
        if not paths:
            print("No raw files found. Pass a file path as argument.")
            sys.exit(1)

    for p in paths:
        if not p.exists():
            print(f"ERROR: File not found: {p}")
            sys.exit(1)
        df = read_dlt_file(p)
        summarise(df, p.name)


if __name__ == "__main__":
    main()
