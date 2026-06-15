"""
Builds the monthly model output file from raw data.

Steps:
  1. Read raw data -> add Brand2 + Powertrain -> write Cleaned Data sheet
  2. Copy: master powertrain, BEV Series Name Table (as-is)
  3. Build: BEV by Model, BEV by Model (2), BMW (pivoted from Data sheet in template)

Output: test_model_1.xlsx in project root
"""

import glob, sys, os
from datetime import date
from pathlib import Path
import pandas as pd
import xlsxwriter

# ── Project root ──────────────────────────────────────────────────────────────
def _find_project_root():
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / "CLAUDE.md").exists():
            return parent
    raise RuntimeError(f"Could not find project root (no CLAUDE.md above {p})")

BASE = _find_project_root()
RAW_PATTERN   = str(BASE / "รถใหม่_*.xlsx")
MODEL_PATTERN = str(BASE / "*- Model.xlsx")   # hyphen required → avoids lowercase model.xlsx

# ── Brand2 mapping ────────────────────────────────────────────────────────────
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

# ── Powertrain mapping (for Cleaned Data sheet) ───────────────────────────────
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

BRAND2_TABLE = [
    ("Brand1",    "Brand2"),
    ("GWM",       "GWM"),
    ("GWM Tank",  "GWM"),
    ("Haval",     "GWM"),
    ("ORA",       "GWM"),
    ("GAC",       "AION"),
    ("Deepal",    "Deepal+ChangAn"),
]

THAI_MONTHS = {
    1:"มกราคม", 2:"กุมภาพันธ์", 3:"มีนาคม",    4:"เมษายน",
    5:"พฤษภาคม", 6:"มิถุนายน",  7:"กรกฎาคม",   8:"สิงหาคม",
    9:"กันยายน", 10:"ตุลาคม",   11:"พฤศจิกายน", 12:"ธันวาคม",
}
MONTH_ORDER = [THAI_MONTHS[i] for i in range(1, 13)]


# ── File helpers ──────────────────────────────────────────────────────────────
def find_file(pattern, label):
    matches = glob.glob(pattern)
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


# ── Data sheet reader ─────────────────────────────────────────────────────────
def read_data_sheet(model_file):
    """Read the Data sheet (brand+model DLT source). Header is at row index 6."""
    df = pd.read_excel(str(model_file), sheet_name="Data", header=6,
                       usecols=range(10))
    df.columns = ["ปี", "เดือน", "ประเภทรถ", "จังหวัด", "ยี่ห้อรถ",
                  "ยี่ห้อรถ2", "รุ่นรถ", "รุ่นรถ2", "Powertrain", "จำนวนรถ"]
    df = df.dropna(subset=["ปี"]).copy()
    df["ปี"] = df["ปี"].astype(int)
    df["จำนวนรถ"] = pd.to_numeric(df["จำนวนรถ"], errors="coerce").fillna(0).astype(int)
    return df


# ── Pivot helpers ─────────────────────────────────────────────────────────────
def _ym_structure(df, last_n_years=None):
    """Return {year: [ordered months present in df]}, optionally capped to last N years."""
    all_years = sorted(df["ปี"].unique())
    if last_n_years:
        all_years = all_years[-last_n_years:]
    months_by_yr = df.groupby("ปี")["เดือน"].apply(set)
    return {yr: [m for m in MONTH_ORDER if m in months_by_yr.get(yr, set())]
            for yr in all_years}


def _col_specs(ym, bmw_style=False):
    """Return list of (year, col_type) where col_type is a month name, 'ytotal', or 'grand'."""
    specs = []
    years = sorted(ym.keys())
    max_yr = years[-1] if years else None
    for yr in years:
        if bmw_style and yr != max_yr:
            specs.append((yr, "ytotal"))
        else:
            for m in ym[yr]:
                specs.append((yr, m))
            specs.append((yr, "ytotal"))
    specs.append(("grand", "grand"))
    return specs


def _pivot_wide(df, index_cols):
    """Pivot df to wide format: index=index_cols, columns=(ปี, เดือน)."""
    return df.pivot_table(
        index=index_cols,
        columns=["ปี", "เดือน"],
        values="จำนวนรถ",
        aggfunc="sum",
        fill_value=0,
    )


def _row_values(row_series, specs):
    """Convert a pivot row Series to a list of cell values matching specs."""
    counts = row_series.to_dict()
    grand_total = int(row_series.sum())
    result = []
    for yr, ctype in specs:
        if yr == "grand":
            result.append(grand_total if grand_total else None)
        elif ctype == "ytotal":
            yr_sum = int(sum(counts.get((yr, m), 0) for m in MONTH_ORDER))
            result.append(yr_sum if yr_sum else None)
        else:
            val = int(counts.get((yr, ctype), 0))
            result.append(val if val else None)
    return result


def _write_vals(ws, row, vals, start):
    """Write a list of cell values to a worksheet row, skipping None."""
    for c, v in enumerate(vals, start=start):
        if v is not None:
            ws.write(row, c, v)


def _write_col_headers(ws, ym, specs, data_start_col, fmt_h):
    """Write year header (row 5) and month header (row 6) for a pivot sheet."""
    col = data_start_col
    last_yr_written = None
    for yr, ctype in specs:
        if yr == "grand":
            ws.write(5, col, "Grand Total", fmt_h)
        elif ctype == "ytotal":
            if yr != last_yr_written:
                ws.write(5, col, yr, fmt_h)
                last_yr_written = yr
            else:
                ws.write(5, col, f"{yr} Total", fmt_h)
        else:
            if yr != last_yr_written:
                ws.write(5, col, yr, fmt_h)
                last_yr_written = yr
            ws.write(6, col, ctype, fmt_h)
        col += 1


# ── BEV sheet builders ────────────────────────────────────────────────────────
def build_bev_by_model(workbook, bev, fmt_h):
    """BEV by Model: grouped by Brand2 (parent) then รุ่นรถ2 (child). bev pre-filtered."""
    ym = _ym_structure(bev, last_n_years=2)
    bev = bev[bev["ปี"].isin(ym.keys())]
    specs = _col_specs(ym)
    data_start = 1

    ws = workbook.add_worksheet("BEV by Model")
    ws.write(0, 0, "ประเภทรถ");   ws.write(0, 1, "(Multiple Items)")
    ws.write(1, 0, "จังหวัด");    ws.write(1, 1, "(All)")
    ws.write(2, 0, "Powertrain"); ws.write(2, 1, "BEV Major")
    ws.write(4, 0, "Sum of จำนวนรถ"); ws.write(4, 1, "Column Labels")
    ws.write(6, 0, "Row Labels", fmt_h)
    _write_col_headers(ws, ym, specs, data_start, fmt_h)

    model_piv = _pivot_wide(bev, ["ยี่ห้อรถ2", "รุ่นรถ2"])
    brand_piv = model_piv.groupby(level="ยี่ห้อรถ2").sum()
    brand_order = brand_piv.sum(axis=1).sort_values(ascending=False).index.tolist()

    data_row = 7
    for brand in brand_order:
        ws.write(data_row, 0, brand, fmt_h)
        _write_vals(ws, data_row, _row_values(brand_piv.loc[brand], specs), data_start)
        data_row += 1

        models_df = model_piv.loc[[brand]]
        model_order = models_df.sum(axis=1).sort_values(ascending=False).index.tolist()
        for (_, model) in model_order:
            ws.write(data_row, 0, model)
            _write_vals(ws, data_row, _row_values(models_df.loc[(brand, model)], specs), data_start)
            data_row += 1

    print("      BEV by Model done")


def _build_flat_pivot_sheet(workbook, df, sheet_name, index_cols, label_names,
                             powertrain_label, bmw_style, fmt_h):
    """Build a flat (non-grouped) pivot sheet. df must be pre-filtered."""
    ym = _ym_structure(df, last_n_years=2)
    df = df[df["ปี"].isin(ym.keys())]
    specs = _col_specs(ym, bmw_style=bmw_style)
    data_start = len(label_names)

    ws = workbook.add_worksheet(sheet_name)
    ws.write(0, 0, "ประเภทรถ");   ws.write(0, 1, "(Multiple Items)")
    ws.write(1, 0, "จังหวัด");    ws.write(1, 1, "(All)")
    ws.write(2, 0, "Powertrain"); ws.write(2, 1, powertrain_label)
    ws.write(4, 0, "Sum of จำนวนรถ")
    ws.write(4, data_start, "ปี"); ws.write(4, data_start + 1, "เดือน")
    for i, name in enumerate(label_names):
        ws.write(6, i, name, fmt_h)
    _write_col_headers(ws, ym, specs, data_start, fmt_h)

    piv = _pivot_wide(df, index_cols)
    row_order = piv.sum(axis=1).sort_values(ascending=False).index.tolist()

    data_row = 7
    for key in row_order:
        key_vals = key if isinstance(key, tuple) else (key,)
        for i, v in enumerate(key_vals):
            ws.write(data_row, i, v)
        _write_vals(ws, data_row, _row_values(piv.loc[key], specs), data_start)
        data_row += 1

    print(f"      {sheet_name} done")


def build_bev_by_model_2(workbook, bev, fmt_h):
    _build_flat_pivot_sheet(workbook, bev, "BEV by Model (2)",
                            ["รุ่นรถ2", "ยี่ห้อรถ2"], ["รุ่นรถ2", "ยี่ห้อรถ2"],
                            "BEV Major", bmw_style=False, fmt_h=fmt_h)


def build_bmw(workbook, bmw, fmt_h):
    _build_flat_pivot_sheet(workbook, bmw, "BMW",
                            ["ยี่ห้อรถ2", "รุ่นรถ2"], ["ยี่ห้อรถ2", "รุ่นรถ2"],
                            "(All)", bmw_style=True, fmt_h=fmt_h)


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    sys.stdout.reconfigure(encoding="utf-8")

    raw_file   = find_file(RAW_PATTERN,   "raw data")
    model_file = find_file(MODEL_PATTERN, "Model template")

    print(f"Raw   : {raw_file.name}")
    print(f"Model : {model_file.name}")

    # ── 1. Read & transform raw data ─────────────────────────────────────────
    print("\n[1/5] Reading raw data...", flush=True)
    df = pd.read_excel(raw_file, header=5)
    print(f"      {len(df):,} rows loaded")

    brand_stripped = df["ยี่ห้อรถ"].str.strip()
    df.insert(df.columns.get_loc("ยี่ห้อรถ") + 1, "ยี่ห้อรถ2",
              brand_stripped.map(BRAND2_MAP).fillna(brand_stripped).fillna("ไม่ระบุ"))
    df.insert(df.columns.get_loc("ชนิดเชื้อเพลิง") + 1, "Powertrain",
              df["ชนิดเชื้อเพลิง"].str.strip().map(POWERTRAIN_MAP).fillna("Other"))

    # ── 2. Read template sheets ───────────────────────────────────────────────
    print("\n[2/5] Reading template sheets...", flush=True)
    df_powertrain = read_sheet_raw(model_file, "master powertrain")
    df_bev_table  = read_sheet_raw(model_file, "BEV Series Name Table")
    print("      Done")

    # ── 3. Read Data sheet; pre-filter subsets for BEV pivot builders ─────────
    print("\n[3/5] Reading Data sheet...", flush=True)
    df_data  = read_data_sheet(model_file)
    bev_data = df_data[df_data["Powertrain"] == "BEV Major"]
    bmw_data = df_data[df_data["ยี่ห้อรถ2"] == "BMW"]
    print(f"      {len(df_data):,} rows | years: {sorted(df_data['ปี'].unique())}")
    print(f"      BEV Major rows: {len(bev_data):,}")

    # ── 4. Build output file ──────────────────────────────────────────────────
    out_file = BASE / "test_model_1.xlsx"
    print(f"\n[4/5] Writing {out_file.name}...", flush=True)
    workbook = xlsxwriter.Workbook(str(out_file))

    fmt_header = workbook.add_format({
        "bold": True, "bg_color": "#4472C4", "font_color": "#FFFFFF",
        "border": 1, "align": "center", "valign": "vcenter",
    })
    fmt_title = workbook.add_format({"bold": True, "font_size": 12})

    # ── Cleaned Data sheet ────────────────────────────────────────────────────
    ws = workbook.add_worksheet("Cleaned Data")
    DATA_ROW = 5

    max_yr_raw = int(df["ปี"].max())
    last_yr_rows = df[df["ปี"] == max_yr_raw]
    end_month = [m for m in MONTH_ORDER if m in last_yr_rows["เดือน"].unique()][-1]
    end_year  = max_yr_raw

    today = date.today()
    proc_month = THAI_MONTHS.get(today.month, "")
    proc_year  = today.year + 543

    ws.write(0, 0, "สถิติการจดทะเบียนรถใหม่ ตามกฎหมายว่าด้วยรถยนต์ จำแนกตามยี่ห้อรถ ชนิดเชื้อเพลิง และจังหวัด", fmt_title)
    ws.write(1, 0, f"เดือนมกราคม ปี พ.ศ. 2564 - เดือน{end_month} ปี พ.ศ. {end_year}")
    ws.write(2, 0, "หน่วย: คัน")
    ws.write(3, 0, f"ประมวลผลข้อมูล วันที่ {today.day} เดือน{proc_month} ปี พ.ศ. {proc_year}")
    ws.write(4, 0, "หมายเหตุ: นับเฉพาะรถใหม่ ไม่รวมรถที่ใช้แล้วนำกลับมาจดทะเบียนใหม่")

    for r, (b1, b2) in enumerate(BRAND2_TABLE):
        fmt = fmt_header if r == 0 else None
        ws.write(r, 13, b1, fmt)
        ws.write(r, 14, b2, fmt)

    for c, col in enumerate(df.columns):
        ws.write(DATA_ROW, c, col, fmt_header)

    total = len(df)
    CHUNK = 10000
    for i in range(0, total, CHUNK):
        write_rows(ws, df.iloc[i:i+CHUNK], start_row=DATA_ROW + 1 + i)
        print(f"      Written {min(i+CHUNK, total):,} / {total:,} rows...", flush=True)

    ws.autofilter(DATA_ROW, 0, DATA_ROW + total, len(df.columns) - 1)
    ws.set_column(0, 0, 8);  ws.set_column(1, 1, 12); ws.set_column(2, 2, 35)
    ws.set_column(3, 3, 20); ws.set_column(4, 4, 20); ws.set_column(5, 5, 20)
    ws.set_column(6, 6, 22); ws.set_column(7, 7, 12); ws.set_column(8, 8, 12)
    ws.set_column(13, 14, 18)
    print("      Cleaned Data done")

    # ── Static template sheets ────────────────────────────────────────────────
    for sheet_name, df_sheet in [
        ("master powertrain",     df_powertrain),
        ("BEV Series Name Table", df_bev_table),
    ]:
        ws_t = workbook.add_worksheet(sheet_name)
        if not df_sheet.empty:
            write_rows(ws_t, df_sheet)
        print(f"      {sheet_name} done")

    # ── 5. BEV pivot sheets ───────────────────────────────────────────────────
    print("\n[5/5] Building BEV pivot sheets...", flush=True)
    build_bev_by_model(workbook, bev_data, fmt_header)
    build_bev_by_model_2(workbook, bev_data, fmt_header)
    build_bmw(workbook, bmw_data, fmt_header)

    workbook.close()
    print(f"\nOutput: {out_file}")
    print("Done.")


if __name__ == "__main__":
    main()
