"""
Builds the monthly model output file from raw data.

Steps:
  1. Read raw data -> add Brand2 + Powertrain columns
  2. Write Cleaned Data sheet (with header rows, autofilter, blue header, Brand2 table)
  3. Copy: master powertrain, BEV Series Name Table (as-is)
  4. Copy: BEV by Model, BEV by Model (2) (as blank templates)

Output: YYYYMM_model_output.xlsx in project root
"""

import glob, sys, os
from datetime import date
from pathlib import Path
import pandas as pd
import xlsxwriter

# ── Project root (walk up from this file to find CLAUDE.md marker) ───────────
def _find_project_root():
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / "CLAUDE.md").exists():
            return parent
    raise RuntimeError(f"Could not find project root (no CLAUDE.md found above {p})")

BASE = _find_project_root()
RAW_PATTERN   = str(BASE / "รถใหม่_*.xlsx")
MODEL_PATTERN = str(BASE / "*Model*.xlsx")

# ── Brand2 mapping ───────────────────────────────────────────────────────────
BRAND2_MAP = {
    "GWM TANK":             "GWM",
    "HAVAL":                "GWM",
    "ORA":                  "GWM",
    "GAC":                  "AION",
    "DEEPAL":               "Deepal+ChangAn",
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

# ── Powertrain mapping (from master powertrain sheet) ────────────────────────
POWERTRAIN_MAP = {
    "CNG": "ICE", "CNG-LPG": "ICE", "CNG-ดีเซล": "ICE", "CNG-เบนซิน": "ICE",
    "CNG-LPG-ดีเซล": "ICE", "CNG-LPG-เบนซิน": "ICE", "CNG-เบนซิน-ไฟฟ้า": "HEV",
    "CNG-ดีเซล-ไฟฟ้า": "HEV", "CNG-ดีเซล-ไฟฟ้าแบบเสียบปลั๊ก": "PHEV",
    "CNG-เบนซิน-ไฟฟ้าแบบเสียบปลั๊ก": "PHEV",
    "LPG-ดีเซล-ไฟฟ้าแบบเสียบปลั๊ก": "PHEV",
    "LPG-เบนซิน-ไฟฟ้า": "HEV", "LPG-เบนซิน-ไฟฟ้าแบบเสียบปลั๊ก": "PHEV",
    "LPGและดีเซล": "ICE", "LPGและเบนซิน": "ICE", "ก๊าซ LPG": "ICE",
    "LNG": "ICE", "LNG-ดีเซล": "ICE", "LPG-ดีเซล-ไฟฟ้า": "HEV",
    "ดีเซล": "ICE", "ดีเซล-ไฟฟ้า": "HEV", "ดีเซล-ไฟฟ้าแบบเสียบปลั๊ก": "PHEV",
    "เบนซิน": "ICE", "เบนซิน-E20": "ICE", "เบนซิน-เอทานอล": "ICE",
    "เบนซิน-ไฟฟ้า": "HEV", "เบนซิน-ไฟฟ้าแบบเสียบปลั๊ก": "PHEV",
    "ไฟฟ้า": "BEV",
    "ไฮโดรเจน": "ICE",
    "ไม่ใช้เชื้อเพลิง": "Other", "เชื้อเพลิงอื่น ๆ": "Other", "ไม่ระบุ": "Other",
}

# ── Brand2 table for side display ────────────────────────────────────────────
BRAND2_TABLE = [
    ("Brand1",    "Brand2"),
    ("GWM",       "GWM"),
    ("GWM Tank",  "GWM"),
    ("Haval",     "GWM"),
    ("ORA",       "GWM"),
    ("GAC",       "AION"),
    ("Deepal",    "Deepal+ChangAn"),
]

# ── Thai month names ──────────────────────────────────────────────────────────
THAI_MONTHS = {
    1:"มกราคม", 2:"กุมภาพันธ์", 3:"มีนาคม",    4:"เมษายน",
    5:"พฤษภาคม", 6:"มิถุนายน",  7:"กรกฎาคม",   8:"สิงหาคม",
    9:"กันยายน", 10:"ตุลาคม",   11:"พฤศจิกายน", 12:"ธันวาคม",
}


def find_file(pattern, label):
    matches = glob.glob(pattern)
    # exclude Excel lock files
    matches = [m for m in matches if not Path(m).name.startswith("~$")]
    if not matches:
        print(f"ERROR: No {label} file found: {pattern}"); sys.exit(1)
    return Path(max(matches, key=os.path.getmtime))


def read_sheet_raw(model_file, sheet_name):
    try:
        return pd.read_excel(model_file, sheet_name=sheet_name, header=None)
    except Exception as e:
        print(f"  Warning: could not read sheet '{sheet_name}': {e}")
        return pd.DataFrame()


def write_rows(ws, df, start_row=0):
    for r_idx, row in enumerate(df.itertuples(index=False, name=None), start=start_row):
        for c_idx, val in enumerate(row):
            if pd.isna(val):
                continue
            ws.write(r_idx, c_idx, val)


def main():
    sys.stdout.reconfigure(encoding="utf-8")

    raw_file   = find_file(RAW_PATTERN, "raw data")
    model_file = find_file(MODEL_PATTERN, "Model template")

    print(f"Raw   : {raw_file.name}")
    print(f"Model : {model_file.name}")

    # ── 1. Read & transform raw data ─────────────────────────────────────────
    print("\n[1/4] Reading raw data...", flush=True)
    df = pd.read_excel(raw_file, header=5)
    print(f"      {len(df):,} rows loaded")

    # Vectorized Brand2 + Powertrain mapping (5-10x faster than .apply)
    brand_stripped = df["ยี่ห้อรถ"].str.strip()
    df.insert(df.columns.get_loc("ยี่ห้อรถ") + 1, "ยี่ห้อรถ2",
              brand_stripped.map(BRAND2_MAP).fillna(brand_stripped).fillna("ไม่ระบุ"))

    df.insert(df.columns.get_loc("ชนิดเชื้อเพลิง") + 1, "Powertrain",
              df["ชนิดเชื้อเพลิง"].str.strip().map(POWERTRAIN_MAP).fillna("Other"))

    print(f"      Columns: {list(df.columns)}")

    # ── 2. Read template sheets ───────────────────────────────────────────────
    print("\n[2/4] Reading template sheets...", flush=True)
    df_powertrain = read_sheet_raw(model_file, "master powertrain")
    df_bev_table  = read_sheet_raw(model_file, "BEV Series Name Table")
    df_bev1       = read_sheet_raw(model_file, "BEV by Model")
    df_bev2       = read_sheet_raw(model_file, "BEV by Model (2)")
    print("      Done")

    # ── 3. Build output file ──────────────────────────────────────────────────
    today = date.today()
    out_name = f"{today.year + 543}{today.month:02d}_model_output.xlsx"
    out_file = BASE / out_name

    print(f"\n[3/4] Writing {out_name}...", flush=True)
    workbook = xlsxwriter.Workbook(str(out_file))

    fmt_header = workbook.add_format({
        "bold": True, "bg_color": "#4472C4", "font_color": "#FFFFFF",
        "border": 1, "align": "center", "valign": "vcenter",
    })
    fmt_title = workbook.add_format({"bold": True, "font_size": 12})

    # ── Cleaned Data sheet ────────────────────────────────────────────────────
    ws = workbook.add_worksheet("Cleaned Data")
    DATA_ROW = 5

    # Derive date range from data
    end_month = THAI_MONTHS.get(today.month, "")
    end_year  = today.year + 543

    ws.write(0, 0, "สถิติการจดทะเบียนรถใหม่ ตามกฎหมายว่าด้วยรถยนต์ จำแนกตามยี่ห้อรถ ชนิดเชื้อเพลิง และจังหวัด", fmt_title)
    ws.write(1, 0, f"เดือนมกราคม ปี พ.ศ. 2564 - เดือน{end_month} ปี พ.ศ. {end_year}")
    ws.write(2, 0, "หน่วย: คัน")
    ws.write(3, 0, f"ประมวลผลข้อมูล วันที่ {today.day} เดือน{end_month} ปี พ.ศ. {end_year}")
    ws.write(4, 0, "หมายเหตุ: นับเฉพาะรถใหม่ ไม่รวมรถที่ใช้แล้วนำกลับมาจดทะเบียนใหม่")

    # Brand2 side table
    for r, (b1, b2) in enumerate(BRAND2_TABLE):
        fmt = fmt_header if r == 0 else None
        ws.write(r, 13, b1, fmt)
        ws.write(r, 14, b2, fmt)

    # Column headers
    for c, col in enumerate(df.columns):
        ws.write(DATA_ROW, c, col, fmt_header)

    # Data rows
    total = len(df)
    CHUNK = 10000
    for i in range(0, total, CHUNK):
        write_rows(ws, df.iloc[i:i+CHUNK], start_row=DATA_ROW + 1 + i)
        print(f"      Written {min(i+CHUNK, total):,} / {total:,} rows...", flush=True)

    ws.autofilter(DATA_ROW, 0, DATA_ROW + total, len(df.columns) - 1)
    ws.set_column(0, 0, 8)
    ws.set_column(1, 1, 12)
    ws.set_column(2, 2, 35)
    ws.set_column(3, 3, 20)
    ws.set_column(4, 4, 20)
    ws.set_column(5, 5, 20)
    ws.set_column(6, 6, 22)
    ws.set_column(7, 7, 12)
    ws.set_column(8, 8, 12)
    ws.set_column(13, 14, 18)
    print("      Cleaned Data sheet done")

    # ── Template sheets ───────────────────────────────────────────────────────
    print("\n[4/4] Copying template sheets...", flush=True)
    for sheet_name, df_sheet in [
        ("master powertrain",     df_powertrain),
        ("BEV Series Name Table", df_bev_table),
        ("BEV by Model",          df_bev1),
        ("BEV by Model (2)",      df_bev2),
    ]:
        ws_t = workbook.add_worksheet(sheet_name)
        if not df_sheet.empty:
            write_rows(ws_t, df_sheet, start_row=0)
        print(f"      {sheet_name} done")

    workbook.close()
    print(f"\nOutput: {out_file}")
    print("Done.")


if __name__ == "__main__":
    main()
