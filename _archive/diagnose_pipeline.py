"""
diagnose_pipeline.py
Run from the project root: python diagnose_pipeline.py
Prints a plain-text comparison of raw data vs parquet vs master totals.
Save the output to a .txt file: python diagnose_pipeline.py > diagnosis.txt
"""

import glob
import os
import sys
from pathlib import Path

import pandas as pd

BASE = Path(__file__).parent

# ── File paths ────────────────────────────────────────────────────────────────
# Must match build_cleaned.py RAW1_PATTERN / RAW2_PATTERN exactly: source of
# truth is "backend/raw data/" (recursive), NOT "backend/input/" (stale copy).
RAW_FUEL_PATTERN  = str(BASE / "backend" / "raw data" / "**" / "รถใหม่_ยี่ห้อรถ-ชนิดเชื้อเพลิง-จังหวัด ปี 2564*.xlsx")
RAW_MODEL_PATTERN = str(BASE / "backend" / "raw data" / "**" / "รถใหม่_ยี่ห้อรถ-รุ่นรถ-จังหวัด ปี 2564*.xlsx")
PARQUET_PATH      = BASE / "backend" / "test_model_cleaned.parquet"
MASTER_PATTERN    = str(BASE / "refer" / "*master*Model*.xlsx")

SEP = "=" * 70


def find_file(pattern, label):
    matches = [m for m in glob.glob(pattern, recursive=True) if "~$" not in m]
    if not matches:
        print(f"  NOT FOUND: {label} ({pattern})")
        return None
    path = max(matches, key=os.path.getmtime)
    print(f"  Found {label}: {Path(path).name}")
    return path


def read_raw(path, label):
    try:
        df = pd.read_excel(path, header=5)
        df["จำนวนรถ"] = pd.to_numeric(df["จำนวนรถ"], errors="coerce").fillna(0)
        print(f"\n{SEP}")
        print(f"RAW FILE: {label}")
        print(f"  Path     : {Path(path).name}")
        print(f"  Rows     : {len(df):,}")
        print(f"  Total    : {int(df['จำนวนรถ'].sum()):,}")
        print(f"  Years    : {sorted(df['ปี'].dropna().unique().astype(int).tolist())}")
        print(f"  Columns  : {list(df.columns)}")

        if "ชนิดเชื้อเพลิง" in df.columns:
            print(f"\n  By Fuel Type (จำนวนรถ):")
            fuel_totals = df.groupby("ชนิดเชื้อเพลิง")["จำนวนรถ"].sum().sort_values(ascending=False)
            for fuel, total in fuel_totals.items():
                print(f"    {fuel:<40} {int(total):>12,}")

        if "รุ่นรถ" in df.columns:
            print(f"\n  Top 20 Models by units:")
            model_totals = df.groupby("รุ่นรถ")["จำนวนรถ"].sum().sort_values(ascending=False).head(20)
            for model, total in model_totals.items():
                print(f"    {str(model):<40} {int(total):>12,}")

        if "ประเภทรถ" in df.columns:
            print(f"\n  By Vehicle Type (ประเภทรถ):")
            type_totals = df.groupby("ประเภทรถ")["จำนวนรถ"].sum().sort_values(ascending=False)
            for vtype, total in type_totals.items():
                print(f"    {str(vtype):<50} {int(total):>12,}")

        return df
    except Exception as e:
        print(f"  ERROR reading {label}: {e}")
        return None


def read_parquet(path):
    try:
        df = pd.read_parquet(str(path))
        df["จำนวนรถ"] = pd.to_numeric(df["จำนวนรถ"], errors="coerce").fillna(0)

        print(f"\n{SEP}")
        print(f"PARQUET: {path.name}")
        print(f"  Rows     : {len(df):,}")
        print(f"  Total    : {int(df['จำนวนรถ'].sum()):,}")
        print(f"  Columns  : {list(df.columns)}")
        print(f"  Years    : {sorted(df['ปี'].dropna().unique().astype(int).tolist())}")

        print(f"\n  By Powertrain:")
        pt_totals = df.groupby("Powertrain")["จำนวนรถ"].sum().sort_values(ascending=False)
        for pt, total in pt_totals.items():
            print(f"    {str(pt):<20} {int(total):>12,}")

        print(f"\n  By Fuel Type (ชนิดเชื้อเพลิง):")
        fuel_totals = df.groupby("ชนิดเชื้อเพลิง", dropna=False)["จำนวนรถ"].sum().sort_values(ascending=False)
        for fuel, total in fuel_totals.items():
            print(f"    {str(fuel):<40} {int(total):>12,}")

        print(f"\n  Null fuel rows  : {df['ชนิดเชื้อเพลิง'].isna().sum():,}")
        print(f"  Null fuel units : {int(df[df['ชนิดเชื้อเพลิง'].isna()]['จำนวนรถ'].sum()):,}")

        print(f"\n  By Vehicle Type (ประเภทรถ):")
        type_totals = df.groupby("ประเภทรถ")["จำนวนรถ"].sum().sort_values(ascending=False)
        for vtype, total in type_totals.items():
            print(f"    {str(vtype):<50} {int(total):>12,}")

        return df
    except Exception as e:
        print(f"  ERROR reading parquet: {e}")
        return None


def compare_totals(df_fuel, df_model, df_parquet):
    print(f"\n{SEP}")
    print("SUMMARY COMPARISON")
    print(SEP)

    fuel_total    = int(df_fuel["จำนวนรถ"].sum())    if df_fuel    is not None else 0
    model_total   = int(df_model["จำนวนรถ"].sum())   if df_model   is not None else 0
    parquet_total = int(df_parquet["จำนวนรถ"].sum()) if df_parquet is not None else 0

    print(f"  Raw Fuel file total   : {fuel_total:>15,}")
    print(f"  Raw Model file total  : {model_total:>15,}")
    print(f"  Parquet total         : {parquet_total:>15,}")
    print(f"  Model vs Parquet gap  : {model_total - parquet_total:>15,}  ← units dropped during cleaning")
    print(f"  Fuel vs Model gap     : {model_total - fuel_total:>15,}  ← model has more detail than fuel")

    if df_parquet is not None and df_model is not None:
        print(f"\n  Parquet null fuel units dropped in Stage 3 filter:")
        null_units = int(df_parquet[df_parquet["ชนิดเชื้อเพลิง"].isna()]["จำนวนรถ"].sum())
        oth_units  = int(df_parquet[df_parquet["Powertrain"] == "OTH"]["จำนวนรถ"].sum())
        print(f"    Null ชนิดเชื้อเพลิง : {null_units:>12,}")
        print(f"    OTH Powertrain     : {oth_units:>12,}")
        print(f"    Combined           : {null_units + oth_units:>12,}  ← likely source of gap")


def main():
    print("PIPELINE DIAGNOSIS")
    print(SEP)
    print("Finding files...")

    fuel_path    = find_file(RAW_FUEL_PATTERN,  "Raw Fuel file")
    model_path   = find_file(RAW_MODEL_PATTERN, "Raw Model file")

    df_fuel    = read_raw(fuel_path,  "FUEL (ชนิดเชื้อเพลิง)")  if fuel_path  else None
    df_model   = read_raw(model_path, "MODEL (รุ่นรถ)")           if model_path else None
    df_parquet = read_parquet(PARQUET_PATH)                       if PARQUET_PATH.exists() else None

    compare_totals(df_fuel, df_model, df_parquet)

    print(f"\n{SEP}")
    print("DONE. Save output: python diagnose_pipeline.py > diagnosis.txt")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    main()
