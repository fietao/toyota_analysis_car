#!/usr/bin/env python3
"""
build_cleaned.py — Data Cleaner Agent script.

Steps:
  1. Read reference tables from Model.xlsx (powertrain map, BEV series name table)
  2. Read both raw DLT files (fuel + model)
  3. Add derived columns: ยี่ห้อรถ2, รุ่นรถ2, Powertrain
  4. Write Cleaned Data + master powertrain + BEV Series Name Table sheets
  5. Save df_cleaned as pickle for build_pivots.py

Output:
  test_model_1.xlsx  (Cleaned Data, master powertrain, BEV Series Name Table)
  test_model_cleaned.pkl  (intermediate for pivot builder)
"""

import glob, sys, os
from datetime import date
from pathlib import Path

import pandas as pd
import xlsxwriter
from openpyxl import load_workbook

sys.stdout.reconfigure(encoding="utf-8")


def read_dlt_file(path: Path) -> pd.DataFrame:
    df = pd.read_excel(str(path), header=5)
    if "จำนวนรถ" in df.columns:
        df["จำนวนรถ"] = pd.to_numeric(df["จำนวนรถ"], errors="coerce").fillna(0).astype(int)
    return df
    
BASE = Path(__file__).resolve().parents[2]
RAW1_PATTERN  = str(BASE / "raw data" / "รถใหม่_ยี่ห้อรถ-ชนิดเชื้อเพลิง-จังหวัด ปี 2564*.xlsx")
RAW2_PATTERN  = str(BASE / "raw data" / "รถใหม่_ยี่ห้อรถ-รุ่นรถ-จังหวัด ปี 2564*.xlsx")
MODEL_PATTERN = str(BASE / "refer" / "*- Model.xlsx")

BRAND2_MAP = {
    "GWM TANK":             "GWM",
    "HAVAL":                "GWM",
    "ORA":                  "GWM",
    "GAC":                  "AION",
    "DEEPAL":               "Deepal+ChangAn",
    "CHANGAN":              "ChangAn+Deepal",
    "CHANG AN":             "ChangAn+Deepal",
    "MERCEDES":             "Mercedes-Benz",
    "MERCEDES BENZ":        "Mercedes-Benz",
    "MERCEDES-AMG":         "Mercedes-Benz",
    "MERCEDESBENZ-MAYBACH": "Mercedes-Benz",
    "ZX AUTO":              "ZX Auto",
    "ZXAUTO":               "ZX Auto",
    "STAR8":                "Star8",
    "STAR 8":               "Star8",
    "STAR8-V":              "Star8",
    "ไม่ระบุ":              "ไม่ระบุ",
    "พ่วง/กึ่งพ่วง":        "ไม่ระบุ",
}

BRAND2_TABLE = [
    ("Brand1",  "Brand2"),
    ("GWM",     "GWM"),    ("GWM Tank", "GWM"),  ("Haval",   "GWM"),
    ("ORA",     "GWM"),    ("GAC",      "AION"),  ("Deepal",  "Deepal+ChangAn"),
    ("ChangAn", "ChangAn+Deepal"), ("Mercedes", "Mercedes-Benz"),
    ("ZX Auto", "ZX Auto"), ("Star8",   "Star8"), ("ไม่ระบุ", "ไม่ระบุ"),
]

THAI_MONTHS = {
    1:"มกราคม", 2:"กุมภาพันธ์", 3:"มีนาคม",    4:"เมษายน",
    5:"พฤษภาคม", 6:"มิถุนายน",  7:"กรกฎาคม",   8:"สิงหาคม",
    9:"กันยายน", 10:"ตุลาคม",   11:"พฤศจิกายน", 12:"ธันวาคม",
}
MONTH_ORDER = [THAI_MONTHS[i] for i in range(1, 13)]


FINAL_COLS = ["ปี", "เดือน", "ประเภทรถ", "จังหวัด",
              "ยี่ห้อรถ", "ยี่ห้อรถ2", "รุ่นรถ", "รุ่นรถ2",
              "ชนิดเชื้อเพลิง", "Powertrain", "จำนวนรถ"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def find_file(pattern, label):
    matches = [m for m in glob.glob(pattern)
               if not any(kw in Path(m).name.lower()
                          for kw in ["~$", "(cleaned data)", "analyst", "test_model", "output"])]
    if not matches:
        print(f"ERROR: No {label} found: {pattern}"); sys.exit(1)
    return Path(max(matches, key=os.path.getmtime))


def read_sheet_raw(path, sheet_name, **kwargs):
    try:
        return pd.read_excel(str(path), sheet_name=sheet_name, header=None, **kwargs)
    except Exception as e:
        print(f"  Warning: could not read '{sheet_name}': {e}")
        return pd.DataFrame()


def read_brand2_rows(model_file):
    wb = load_workbook(str(model_file), read_only=True, data_only=True)
    try:
        ws = wb["Data"]
        rows = []
        for raw_brand, brand2 in ws.iter_rows(
            min_row=1, max_row=8, min_col=14, max_col=15, values_only=True
        ):
            e = str(raw_brand).strip() if raw_brand is not None else ""
            f = str(brand2).strip() if brand2 is not None else ""
            if (
                e
                and e.upper() not in ("NAN", "BRAND1", "ยี่ห้อรถ", "E", "BRAND")
                and f
                and f.upper() not in ("NAN", "BRAND2", "ยี่ห้อรถ2", "F")
            ):
                rows.append((e, f))
        return rows
    finally:
        wb.close()


def add_brand2(df, brand_map):
    upper = df["ยี่ห้อรถ"].astype(str).str.strip().str.upper()
    df.insert(df.columns.get_loc("ยี่ห้อรถ") + 1, "ยี่ห้อรถ2",
              upper.map(brand_map).fillna(df["ยี่ห้อรถ"]))


def ordered_cols(df):
    cols  = [c for c in FINAL_COLS if c in df.columns]
    extra = [c for c in df.columns if c not in FINAL_COLS]
    return df[cols + extra]


def write_rows(ws, df, start_row=0):
    for r_idx, row in enumerate(df.itertuples(index=False, name=None), start=start_row):
        for c_idx, val in enumerate(row):
            if not pd.isna(val):
                ws.write(r_idx, c_idx, val)


def clean_powertrain_value(value):
    if pd.isna(value):
        return "OTH"
    value = str(value).strip()
    return value if value and value.lower() != "nan" and value != "(blank)" else "OTH"


def sort_cleaned_data(df, brand2_order=None):
    out = df.copy()
    month_rank = {month: idx for idx, month in enumerate(MONTH_ORDER, start=1)}
    out["_month_sort"] = out["เดือน"].map(month_rank).fillna(99)
    out["_source_sort"] = out["รุ่นรถ"].notna().astype(int)

    if brand2_order:
        brand_rank = {b: i for i, b in enumerate(brand2_order)}
        out["_brand2_sort"] = out["ยี่ห้อรถ2"].map(brand_rank).fillna(len(brand2_order))
    else:
        out["_brand2_sort"] = 0

    sort_cols = [
        "ปี", "_month_sort", "ประเภทรถ", "จังหวัด",
        "_brand2_sort", "ยี่ห้อรถ2", "ยี่ห้อรถ", "_source_sort",
        "ชนิดเชื้อเพลิง", "รุ่นรถ2", "รุ่นรถ",
    ]
    sort_cols = [col for col in sort_cols if col in out.columns]
    out = out.sort_values(sort_cols, kind="mergesort", na_position="last")
    return out.drop(columns=["_month_sort", "_source_sort", "_brand2_sort"], errors="ignore")


# ── Sheet builders ────────────────────────────────────────────────────────────

def build_master_powertrain(workbook, df_fuel, df_template, fmt_h, powertrain_map):
    ws = workbook.add_worksheet("master powertrain")

    fmt_ef_match = workbook.add_format({"bold": True, "bg_color": "#BDD7EE"})
    fmt_num      = workbook.add_format({"num_format": "#,##0"})
    fmt_h_num    = workbook.add_format({"bold": True, "bg_color": "#4472C4", "font_color": "#FFFFFF",
                                        "border": 1, "align": "center", "valign": "vcenter",
                                        "num_format": "#,##0"})

    # Collect fuel types present in the A-C summary (col A, rows 7+)
    ac_fuels = set()
    for r_idx, tup in enumerate(df_template.itertuples(index=False, name=None)):
        if r_idx >= 7:
            val_a = tup[0] if tup else None
            if not pd.isna(val_a) and str(val_a).strip() != "Grand Total":
                ac_fuels.add(str(val_a).strip())

    last_data_row = 6
    for r_idx, tup in enumerate(df_template.itertuples(index=False, name=None)):
        val_a = tup[0] if tup else None
        val_e = tup[4] if len(tup) > 4 else None
        is_grand_total = not pd.isna(val_a) and str(val_a).strip() == "Grand Total"
        ef_matches_ac  = r_idx >= 7 and not pd.isna(val_e) and str(val_e).strip() in ac_fuels

        for c_idx, val in enumerate(tup):
            if pd.isna(val):
                continue
            # Replace any (blank) in the Powertrain column (B) with N/A
            if c_idx == 1 and str(val).strip() == "(blank)":
                val = "N/A"
            if r_idx == 5 and c_idx == 0:
                fmt = fmt_h                          # "Sum of จำนวนรถ" title
            elif r_idx == 6 and c_idx in (0, 1, 2, 4, 5):
                fmt = fmt_h                          # header row — both A-C and E-F
            elif is_grand_total and c_idx in (0, 1, 2):
                fmt = fmt_h                          # Grand Total — full row highlight
            elif c_idx in (4, 5) and ef_matches_ac:
                fmt = fmt_ef_match                   # E-F row whose fuel type is in A-C summary
            else:
                fmt = None
            ws.write(r_idx, c_idx, val, fmt) if fmt else ws.write(r_idx, c_idx, val)

        val_a = tup[0] if tup else None
        if r_idx >= 7 and not pd.isna(val_a) and str(val_a).strip() != "Grand Total":
            last_data_row = r_idx

    ws.autofilter(6, 0, last_data_row, 2)
    print("      master powertrain done")


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    raw1_file  = find_file(RAW1_PATTERN,  "fuel raw data")
    raw2_file  = find_file(RAW2_PATTERN,  "model raw data")
    model_file = find_file(MODEL_PATTERN, "Model template")

    print(f"Raw 1 (Fuel) : {raw1_file.name}")
    print(f"Raw 2 (Model): {raw2_file.name}")
    print(f"Model Temp   : {model_file.name}")

    # 1. Reference tables
    print("\n[1/4] Reading reference tables...", flush=True)
    df_pt  = read_sheet_raw(model_file, "master powertrain", keep_default_na=False)
    _pt    = df_pt.iloc[7:, [4, 5]].dropna(subset=[4])
    powertrain_map = {str(k).strip(): clean_powertrain_value(v)
                      for k, v in zip(_pt.iloc[:, 0], _pt.iloc[:, 1]) if not pd.isna(k)}
    print(f"      {len(powertrain_map)} powertrain mappings")

    # Read brand → ยี่ห้อรถ2 table from refer1 Data!N:O rows 1-8.
    brand_rows = read_brand2_rows(model_file)

    if brand_rows:
        ref_brand2_map = {e.upper(): f for e, f in brand_rows}
        brand2_order   = list(dict.fromkeys(f for _, f in brand_rows))
        brand2_table   = [("Brand1", "Brand2")] + brand_rows
        merged_brand2_map = {**BRAND2_MAP, **ref_brand2_map}
        print(f"      {len(brand_rows)} ยี่ห้อรถ2 entries from refer1 (Data!N:O rows 1-8)")
    else:
        merged_brand2_map = BRAND2_MAP
        brand2_order = list(dict.fromkeys(v for v in BRAND2_MAP.values()))
        brand2_table = list(BRAND2_TABLE)
        print("      ยี่ห้อรถ2: using hardcoded table (Data!N:O rows 1-8 empty)")

    df_bev_tbl = read_sheet_raw(model_file, "BEV Series Name Table")
    _bev       = df_bev_tbl.iloc[1:, [1, 2, 3]].dropna(subset=[1])
    model2_map        = {str(k).strip().upper(): str(v).strip() for k, v in zip(_bev.iloc[:, 0], _bev.iloc[:, 1])}
    pt_from_model_map = {str(k).strip().upper(): str(v).strip() for k, v in zip(_bev.iloc[:, 0], _bev.iloc[:, 2])}

    csv_map_path = BASE / "refer" / "model2_map.csv"
    if csv_map_path.exists():
        df_csv = pd.read_csv(str(csv_map_path), encoding="utf-8-sig")
        csv_model2_map = dict(zip(
            df_csv["รุ่นรถ_raw"].astype(str).str.strip().str.upper(),
            df_csv["รุ่นรถ2"].astype(str).str.strip()
        ))
        model2_map.update(csv_model2_map)
        print(f"      Loaded {len(csv_model2_map)} mappings from model2_map.csv")

    print(f"      {len(model2_map)} รุ่นรถ2 mappings")

    # 2. Raw files
    print("\n[2/4] Reading raw data...", flush=True)
    df_fuel  = read_dlt_file(raw1_file)
    df_model = read_dlt_file(raw2_file)
    print(f"      {len(df_fuel):,} fuel rows | {len(df_model):,} model rows")

    # 3. Derived columns
    print("\n[3/4] Adding derived columns...", flush=True)

    # df_fuel used only for master powertrain summary — not included in cleaned data.
    add_brand2(df_fuel, merged_brand2_map)
    df_fuel.insert(df_fuel.columns.get_loc("ยี่ห้อรถ2") + 1, "รุ่นรถ",  None)
    df_fuel.insert(df_fuel.columns.get_loc("รุ่นรถ")    + 1, "รุ่นรถ2", None)
    df_fuel["Powertrain"] = df_fuel["ชนิดเชื้อเพลิง"].apply(
        lambda f: powertrain_map.get(str(f).strip(), "OTH") if pd.notna(f) else None)

    # Model rows: brand2, model2, powertrain (fuel first, model fallback)
    add_brand2(df_model, merged_brand2_map)
    if "รุ่นรถ" in df_model.columns:
        upper = df_model["รุ่นรถ"].astype(str).str.strip().str.upper()
        df_model.insert(df_model.columns.get_loc("รุ่นรถ") + 1, "รุ่นรถ2",
                        upper.map(model2_map).fillna(df_model["รุ่นรถ"]))

    pt_fuel  = (df_model["ชนิดเชื้อเพลิง"].astype(str).str.strip().map(powertrain_map)
                if "ชนิดเชื้อเพลิง" in df_model.columns
                else pd.Series(dtype=object, index=df_model.index))
    pt_model = (df_model["รุ่นรถ"].astype(str).str.strip().str.upper().map(pt_from_model_map)
                if "รุ่นรถ" in df_model.columns
                else pd.Series(dtype=object, index=df_model.index))
    powertrain_col = pt_fuel.combine_first(pt_model).fillna("OTH")
    if "Powertrain" in df_model.columns:
        df_model["Powertrain"] = powertrain_col
    else:
        df_model.insert(df_model.columns.get_loc("รุ่นรถ2") + 1, "Powertrain", powertrain_col)

    # df_fuel is used above for the master powertrain summary sheet only.
    # Final cleaned data uses df_model only — matches refer file row count (636,333).
    df_cleaned = ordered_cols(df_model)
    df_cleaned = sort_cleaned_data(df_cleaned, brand2_order)
    print(f"      {len(df_cleaned):,} combined rows | cols: {list(df_cleaned.columns)}")

    # Save intermediate for pivot builder (parquet: safe, fast, preserves dtypes)
    # Cast object columns to str to avoid mixed-type ArrowTypeError
    pq_path = BASE / "test_model_cleaned.parquet"
    for col in df_cleaned.select_dtypes(include="object").columns:
        df_cleaned[col] = df_cleaned[col].astype(str).replace("nan", pd.NA)
    df_cleaned.to_parquet(str(pq_path), index=False)
    print(f"      Saved intermediate: {pq_path.name}")

    # 4. Write output xlsx (cleaned sheets only)
    out_file = BASE / "test_model_1.xlsx"
    print(f"\n[4/4] Writing {out_file.name}...", flush=True)
    workbook = xlsxwriter.Workbook(str(out_file))

    fmt_h         = workbook.add_format({"bold": True, "bg_color": "#4472C4",
                                         "font_color": "#FFFFFF", "border": 1,
                                         "align": "center", "valign": "vcenter"})
    fmt_title     = workbook.add_format({"bold": True, "font_size": 12})
    fmt_bold_blue = workbook.add_format({"bold": True, "font_color": "#4472C4"})
    fmt_warn      = workbook.add_format({"bold": True, "bg_color": "#FFF2CC",
                                         "font_color": "#9C6500"})

    # Data
    ws = workbook.add_worksheet("Data")
    DATA_ROW = 5

    max_yr    = int(df_cleaned["ปี"].max())
    end_month = [m for m in MONTH_ORDER
                 if m in df_cleaned[df_cleaned["ปี"] == max_yr]["เดือน"].unique()][-1]
    today     = date.today()
    proc_mon  = THAI_MONTHS.get(today.month, "")
    proc_yr   = today.year + 543

    ws.write(0, 0, "สถิติการจดทะเบียนรถใหม่ ตามกฎหมายว่าด้วยรถยนต์ จำแนกตามยี่ห้อรถ ชนิดเชื้อเพลิง และจังหวัด", fmt_title)
    ws.write(1, 0, f"เดือนมกราคม ปี พ.ศ. 2564 - เดือน{end_month} ปี พ.ศ. {max_yr}")
    ws.write(2, 0, "หน่วย: คัน")
    ws.write(3, 0, f"ประมวลผลข้อมูล วันที่ {today.day} เดือน{proc_mon} ปี พ.ศ. {proc_yr}")
    ws.write(4, 0, "หมายเหตุ: นับเฉพาะรถใหม่ ไม่รวมรถที่ใช้แล้วนำกลับมาจดทะเบียนใหม่")

    for r, (b1, b2) in enumerate(brand2_table):
        ws.write(r, 13, b1, fmt_h if r == 0 else None)
        ws.write(r, 14, b2, fmt_h if r == 0 else None)

    total = len(df_cleaned)
    for i in range(0, total, 10000):
        chunk = df_cleaned.iloc[i:i+10000]
        for r_idx, row in enumerate(chunk.itertuples(index=False, name=None), start=DATA_ROW + 1 + i):
            for c_idx, val in enumerate(row):
                if not pd.isna(val):
                    ws.write(r_idx, c_idx, val)
        print(f"      Written {min(i+10000, total):,} / {total:,} rows...", flush=True)

    ws.add_table(DATA_ROW, 0, DATA_ROW + total, len(df_cleaned.columns) - 1, {
        "style": "Table Style Medium 2",
        "columns": [{"header": c, "header_format": fmt_h} for c in df_cleaned.columns],
    })
    col_widths = {"ปี": 8, "เดือน": 12, "ประเภทรถ": 35, "จังหวัด": 20,
                  "ยี่ห้อรถ": 20, "ยี่ห้อรถ2": 20, "รุ่นรถ": 28, "รุ่นรถ2": 25,
                  "ชนิดเชื้อเพลิง": 25, "Powertrain": 15, "จำนวนรถ": 12}
    for i, col in enumerate(df_cleaned.columns):
        if col in col_widths:
            ws.set_column(i, i, col_widths[col])
    ws.set_column(13, 14, 18)
    print("      Data done")
    

    build_master_powertrain(workbook, df_fuel, df_pt, fmt_h, powertrain_map)

    ws_bev = workbook.add_worksheet("BEV Series Name Table")
    if not df_bev_tbl.empty:
        write_rows(ws_bev, df_bev_tbl)
    print("      BEV Series Name Table done")

    workbook.close()
    print(f"\nOutput : {out_file}")
    print(f"  Rows : {len(df_cleaned):,}")
    print(f"  Sheets: Data | master powertrain | BEV Series Name Table")
    print("  → Run build_pivots.py to add BEV/BMW sheets")


if __name__ == "__main__":
    main()
