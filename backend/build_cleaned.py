#!/usr/bin/env python3
"""
build_cleaned.py — Data Cleaner Agent script.

Steps:
  1. Read reference tables from Model.xlsx (powertrain map, BEV series name table)
  2. Read both raw DLT files (fuel + model)
  3. Add derived columns: ยี่ห้อรถ2, รุ่นรถ2, Powertrain
  4. Write Cleaned Data + master powertrain sheets
  5. Save df_cleaned as pickle for build_pivots.py

Output:
  test_model_1.xlsx  (Cleaned Data, master powertrain)
  test_model_cleaned.pkl  (intermediate for pivot builder)
"""

import csv, glob, sys, os, zipfile, re
from datetime import datetime
from pathlib import Path

import pandas as pd
from openpyxl import load_workbook

sys.stdout.reconfigure(encoding="utf-8")


def read_dlt_file(path: Path) -> pd.DataFrame:
    df = pd.read_excel(str(path), header=5, engine="calamine")
    if "จำนวนรถ" in df.columns:
        df["จำนวนรถ"] = pd.to_numeric(df["จำนวนรถ"], errors="coerce").fillna(0).astype(int)
    return df
    
BASE = Path(__file__).resolve().parent
RAW1_PATTERN  = str(BASE / "raw data" / "**" / "รถใหม่_ยี่ห้อรถ-ชนิดเชื้อเพลิง-จังหวัด ปี 2564*.xlsx")
RAW2_PATTERN  = str(BASE / "raw data" / "**" / "รถใหม่_ยี่ห้อรถ-รุ่นรถ-จังหวัด ปี 2564*.xlsx")
REVIEW_DIR = BASE / "output"
REVIEW_GLOB = "new_bev_models_review_*.xlsx"





THAI_MONTHS = {
    1:"มกราคม", 2:"กุมภาพันธ์", 3:"มีนาคม",    4:"เมษายน",
    5:"พฤษภาคม", 6:"มิถุนายน",  7:"กรกฎาคม",   8:"สิงหาคม",
    9:"กันยายน", 10:"ตุลาคม",   11:"พฤศจิกายน", 12:"ธันวาคม",
}
MONTH_ORDER = [THAI_MONTHS[i] for i in range(1, 13)]


FINAL_COLS = ["ปี", "เดือน", "ประเภทรถ", "จังหวัด",
              "ยี่ห้อรถ", "ยี่ห้อรถ2", "รุ่นรถ", "รุ่นรถ2",
              "ชนิดเชื้อเพลิง", "Powertrain", "จำนวนรถ"]
JOIN_KEYS = ["ปี", "เดือน", "ประเภทรถ", "จังหวัด", "ยี่ห้อรถ"]


# ── Helpers ───────────────────────────────────────────────────────────────────

def find_file(pattern, label):
    override = os.environ.get(f"{label.upper().replace(' ', '_')}_PATH")
    if override:
        path = Path(override)
        if not path.exists():
            print(f"ERROR: {label} override not found: {path}"); sys.exit(1)
        return path

    matches = [m for m in glob.glob(pattern, recursive=True)
               if not any(kw in Path(m).name.lower()
                          for kw in ["~$", "(cleaned data)", "analyst", "test_model", "output", "fake test"])]
    if not matches:
        print(f"ERROR: No {label} found: {pattern}"); sys.exit(1)
    return Path(max(matches, key=os.path.getmtime))


# what is kwargs 
def read_sheet_raw(path, sheet_name, **kwargs):
    try:
        return pd.read_excel(str(path), sheet_name=sheet_name, header=None, engine="calamine", **kwargs)
    except Exception as e:
        print(f"  Warning: could not read '{sheet_name}': {e}")
        return pd.DataFrame()


def read_brand2_rows(wb):
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
    except Exception as e:
        print(f"  Warning: could not read brand2 rows: {e}")
        return []


def add_brand2(df, brand_map):
    upper = df["ยี่ห้อรถ"].astype(str).str.strip().str.upper()
    df.insert(df.columns.get_loc("ยี่ห้อรถ") + 1, "ยี่ห้อรถ2",
              upper.map(brand_map).fillna(df["ยี่ห้อรถ"]))


def enrich_fuel_type(df_model, df_fuel):
    """Add ชนิดเชื้อเพลิง to model rows from the dominant matching fuel row."""
    if "ชนิดเชื้อเพลิง" in df_model.columns:
        return df_model

    lookup = (
        df_fuel.groupby(JOIN_KEYS + ["ชนิดเชื้อเพลิง"])["จำนวนรถ"]
        .sum()
        .reset_index()
        .sort_values("จำนวนรถ", ascending=False)
        .drop_duplicates(subset=JOIN_KEYS)
        .set_index(JOIN_KEYS)["ชนิดเชื้อเพลิง"]
    )
    df_model = df_model.copy()
    insert_at = df_model.columns.get_loc("ยี่ห้อรถ") + 1
    df_model.insert(
        insert_at,
        "ชนิดเชื้อเพลิง",
        df_model[JOIN_KEYS].apply(lambda r: lookup.get(tuple(r)), axis=1),
    )
    filled = df_model["ชนิดเชื้อเพลิง"].notna().sum()
    print(f"      ชนิดเชื้อเพลิง filled: {filled:,} / {len(df_model):,} rows")
    return df_model


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


def dump_map_to_csv(mapping: dict, path: str, key_field="fuel", value_field="powertrain"):
    with open(path, mode="w", encoding="utf-8", newline="") as file:
        writer = csv.writer(file)
        writer.writerow([key_field, value_field])
        for key in sorted(mapping.keys()):
            writer.writerow([key, mapping[key]])


def load_powertrain_map(path: str, key_field="fuel", value_field="powertrain") -> dict:
    powertrain_map = {}
    with open(path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)
        for row in reader:
            key = row[key_field].strip()
            value = row[value_field].strip()
            powertrain_map[key] = value
    return powertrain_map


def _normalise_key(value):
    return str(value).strip().upper() if pd.notna(value) else ""


def _cell_text(value):
    return str(value).strip() if pd.notna(value) else ""


def _review_paths():
    return sorted(REVIEW_DIR.glob(REVIEW_GLOB), key=lambda p: p.stat().st_mtime, reverse=True)


def _read_review_rows():
    review_paths = _review_paths()
    if not review_paths:
        return None, {}

    rows = {}
    used_path = None
    for review_path in review_paths:
        df_review = pd.read_excel(str(review_path), engine="calamine")
        if "approved" not in df_review.columns and len(df_review.columns) > 0:
            first_col = str(df_review.columns[0]).strip().lower()
            if first_col in {"yes", "y", "no", "n"}:
                df_review = df_review.rename(columns={df_review.columns[0]: "approved"})
                df_review["approved"] = first_col

        if "approved" not in df_review.columns:
            continue

        for _, row in df_review.iterrows():
            key = (_normalise_key(row.get("Brand")), _normalise_key(row.get("รุ่นรถ")))
            if not key[0] or not key[1] or key in rows:
                continue
            approved = _cell_text(row.get("approved", "")).lower()
            powertrain = _cell_text(row.get("Powertrain", "")).upper()
            if approved or powertrain == "OTH":
                rows[key] = row
                used_path = used_path or review_path
    return used_path, rows


def _write_bev_review_workbook(records):
    REVIEW_DIR.mkdir(exist_ok=True)
    review_path = REVIEW_DIR / f"new_bev_models_review_{datetime.now():%Y%m%d}.xlsx"
    suffix = 1
    while review_path.exists():
        review_path = REVIEW_DIR / f"new_bev_models_review_{datetime.now():%Y%m%d}_{suffix}.xlsx"
        suffix += 1

    df_review = pd.DataFrame(
        records,
        columns=["approved", "Brand", "รุ่นรถ", "รุ่นรถ2", "Powertrain"],
    )
    df_review.to_excel(str(review_path), index=False)
    return review_path


def resolve_bev_review(df_cleaned, known_bev_models, scope_mask=None):
    """Return approved BEV rows, optionally scanning only rows in scope_mask."""
    required = {"ชนิดเชื้อเพลิง", "ยี่ห้อรถ2", "รุ่นรถ", "รุ่นรถ2"}
    if not required.issubset(df_cleaned.columns):
        missing = ", ".join(sorted(required - set(df_cleaned.columns)))
        print(f"\nERROR: Cannot run BEV preflight; missing column(s): {missing}")
        sys.exit(1)

    if scope_mask is None:
        update_scope = pd.Series(True, index=df_cleaned.index)
    else:
        update_scope = scope_mask.reindex(df_cleaned.index, fill_value=False)
    scan_df = df_cleaned.loc[update_scope]
    electric_rows = scan_df[
        (scan_df["ชนิดเชื้อเพลิง"].astype(str).str.strip() == "ไฟฟ้า") &
        scan_df["รุ่นรถ"].notna() &
        (scan_df["รุ่นรถ"].astype(str).str.strip() != "")
    ][["ยี่ห้อรถ2", "รุ่นรถ", "รุ่นรถ2"]].drop_duplicates()

    unknown = electric_rows[
        ~electric_rows["รุ่นรถ"].map(_normalise_key).isin(known_bev_models)
    ].copy()
    if unknown.empty:
        return []

    review_path, reviewed = _read_review_rows()
    approved_rows = []
    blocking_rows = []
    resolved_rows = []

    for _, row in unknown.sort_values(["ยี่ห้อรถ2", "รุ่นรถ"]).iterrows():
        brand = str(row["ยี่ห้อรถ2"]).strip()
        model = str(row["รุ่นรถ"]).strip()
        default_model2 = str(row["รุ่นรถ2"]).strip()
        review = reviewed.get((_normalise_key(brand), _normalise_key(model)))

        if review is None:
            blocking_rows.append({
                "approved": "",
                "Brand": brand,
                "รุ่นรถ": model,
                "รุ่นรถ2": default_model2,
                "Powertrain": "BEV Major",
            })
            continue

        approved = _cell_text(review.get("approved", "")).lower()
        powertrain = _cell_text(review.get("Powertrain", "")) or "BEV Major"
        model2 = _cell_text(review.get("รุ่นรถ2", "")) or default_model2

        if powertrain.upper() == "OTH":
            resolved_rows.append({"รุ่นรถ": model, "รุ่นรถ2": model2, "Powertrain": "OTH"})
            continue
        if approved in {"yes", "y"}:
            approved_rows.append({
                "Brand": str(review.get("Brand", brand)).strip() or brand,
                "รุ่นรถ": model,
                "รุ่นรถ2": model2,
                "Powertrain": powertrain,
            })
            resolved_rows.append({"รุ่นรถ": model, "รุ่นรถ2": model2, "Powertrain": powertrain})
        else:
            blocking_rows.append({
                "approved": approved,
                "Brand": brand,
                "รุ่นรถ": model,
                "รุ่นรถ2": model2,
                "Powertrain": powertrain,
            })

    if blocking_rows:
        print(f"\n  Auto-approving {len(blocking_rows)} new BEV model(s) as 'BEV Major':")
        for row in blocking_rows:
            print(f"    {row['Brand']:<20}  {row['รุ่นรถ']}")
            approved_rows.append({
                "Brand": row["Brand"],
                "รุ่นรถ": row["รุ่นรถ"],
                "รุ่นรถ2": row["รุ่นรถ2"],
                "Powertrain": "BEV Major",
            })
            resolved_rows.append({
                "รุ่นรถ": row["รุ่นรถ"],
                "รุ่นรถ2": row["รุ่นรถ2"],
                "Powertrain": "BEV Major",
            })

    for row in resolved_rows:
        mask = (
            update_scope &
            (df_cleaned["ชนิดเชื้อเพลิง"].astype(str).str.strip() == "ไฟฟ้า") &
            (df_cleaned["รุ่นรถ"].map(_normalise_key) == _normalise_key(row["รุ่นรถ"]))
        )
        df_cleaned.loc[mask, "รุ่นรถ2"] = row["รุ่นรถ2"]
        df_cleaned.loc[mask, "Powertrain"] = row["Powertrain"]

    return approved_rows


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
        "Powertrain", "รุ่นรถ2", "รุ่นรถ",
    ]
    sort_cols = [col for col in sort_cols if col in out.columns]
    out = out.sort_values(sort_cols, kind="mergesort", na_position="last")
    return out.drop(columns=["_month_sort", "_source_sort", "_brand2_sort"], errors="ignore")



def enable_pivot_refresh(wb):
    """Set refreshOnLoad to True for all pivot tables in the workbook."""
    try:
        for ws in wb.worksheets:
            for pivot in ws._pivots:
                if pivot.cache:
                    pivot.cache.refreshOnLoad = True
    except Exception as e:
        print(f"  Warning: Could not set refreshOnLoad on pivots: {e}")


def _col(n):
    r = ""
    while n > 0:
        n, rem = divmod(n - 1, 26)
        r = chr(65 + rem) + r
    return r


def _esc(s):
    return (str(s).replace("&", "&amp;").replace("<", "&lt;")
                 .replace(">", "&gt;").replace('"', "&quot;"))


def _patch_pivot_table_def1(xml):
    """pivotTable1/2/3 (cache def1): ชนิดเชื้อเพลิง inserted at field 8, so
    Powertrain shifts 8→9, จำนวนรถ shifts 9→10. Insert blank pivotField at pos 8
    and increment all fld/x refs >= 8 by 1."""
    # Insert blank pivotField before the 8th <pivotField element (0-indexed)
    pos, count = 0, 0
    while True:
        idx = xml.find("<pivotField", pos)
        if idx == -1:
            break
        if count == 8:
            xml = xml[:idx] + "<pivotField/>" + xml[idx:]
            break
        pos = idx + 1
        count += 1

    xml = re.sub(
        r'(<pivotFields\s+count=")(\d+)(")',
        lambda m: m.group(1) + str(int(m.group(2)) + 1) + m.group(3),
        xml, count=1,
    )

    def _inc(val): return str(int(val) + 1) if int(val) >= 8 else val
    xml = re.sub(r'(\bfld=")(-?\d+)(")', lambda m: m.group(1) + _inc(m.group(2)) + m.group(3), xml)
    xml = re.sub(r'(<field\s+x=")(\d+)(")',  lambda m: m.group(1) + _inc(m.group(2)) + m.group(3), xml)
    return xml


def _patch_pivot_table_def2(xml):
    """pivotTable4 (cache def2, master powertrain): replace pivotFields block entirely
    so it aligns with the new 11-col layout (ชนิดเชื้อเพลิง=8, Powertrain=9, จำนวนรถ=10).
    Also fix rowField x refs and dataField fld ref."""
    new_pf = (
        '<pivotFields count="11">'
        '<pivotField compact="0" outline="0" showAll="0"/>'
        '<pivotField compact="0" outline="0" showAll="0"/>'
        '<pivotField compact="0" outline="0" showAll="0"/>'
        '<pivotField compact="0" outline="0" showAll="0"/>'
        '<pivotField compact="0" outline="0" showAll="0"/>'
        '<pivotField compact="0" outline="0" showAll="0"/>'
        '<pivotField compact="0" outline="0" showAll="0"/>'
        '<pivotField compact="0" outline="0" showAll="0"/>'
        '<pivotField axis="axisRow" compact="0" outline="0" showAll="0"/>'
        '<pivotField axis="axisRow" compact="0" outline="0" showAll="0"/>'
        '<pivotField dataField="1" compact="0" numFmtId="3" outline="0" showAll="0"/>'
        '</pivotFields>'
    )
    start = xml.find("<pivotFields")
    end   = xml.find("</pivotFields>") + len("</pivotFields>")
    if start >= 0 and end > start:
        xml = xml[:start] + new_pf + xml[end:]

    # ชนิดเชื้อเพลิง: old def2 row field x=7 → new pos x=8
    xml = re.sub(r'(<field\s+x=")7(")', r'\g<1>8\2', xml)
    # จำนวนรถ: old def2 data field fld=8 → new pos fld=10
    xml = re.sub(r'(<dataField\b[^>]*\bfld=")8(")', r'\g<1>10\2', xml)
    return xml


def rewrite_data_rows(workbook_path, dataframe, data_start_row):
    """Splice new data rows into Data sheet starting at data_start_row.
    Rows 1..(data_start_row-2) are preserved byte-for-byte (metadata, brand helper).
    The header row immediately above data_start_row is refreshed from dataframe columns.
    """
    path = Path(workbook_path)

    with zipfile.ZipFile(str(path), "r") as z:
        wb_xml   = z.read("xl/workbook.xml").decode("utf-8")
        rels_xml = z.read("xl/_rels/workbook.xml.rels").decode("utf-8")
    m = re.search(r'<sheet\b[^>]*\bname="Data"[^>]*\br:id="([^"]+)"', wb_xml)
    if not m:
        m = re.search(r'<sheet\b[^>]*\br:id="([^"]+)"[^>]*\bname="Data"', wb_xml)
    if not m:
        raise ValueError("'Data' sheet not found in xl/workbook.xml")
    rid = m.group(1)
    rel_m = re.search(rf'<Relationship\b(?=[^>]*\bId="{re.escape(rid)}")[^>]*/?>', rels_xml)
    m2 = re.search(r'\bTarget="([^"]+)"', rel_m.group(0)) if rel_m else None
    if not m2:
        raise ValueError(f"No relationship for Id='{rid}'")
    target = m2.group(1).lstrip("/")
    sheet_xml_name = f"xl/{target}" if not target.startswith("xl/") else target

    with zipfile.ZipFile(str(path), "r") as z:
        old_xml = z.read(sheet_xml_name).decode("utf-8")

    header_row = data_start_row - 1
    cut_m = re.search(rf'<row\b[^>]*\br="{header_row}"', old_xml)
    if not cut_m:
        cut_m = re.search(rf'<row\b[^>]*\br="{data_start_row}"', old_xml)
    prefix = old_xml[:cut_m.start()] if cut_m else old_xml[:old_xml.rfind("</sheetData>")]
    suffix = old_xml[old_xml.rfind("</sheetData>"):]

    rows_xml = []
    header_cells = []
    for c_idx, col_name in enumerate(dataframe.columns, 1):
        col = _col(c_idx)
        header_cells.append(
            f'<c r="{col}{header_row}" t="inlineStr"><is><t>{_esc(col_name)}</t></is></c>'
        )
    rows_xml.append(f'<row r="{header_row}">{"".join(header_cells)}</row>')

    for r_idx, row in enumerate(dataframe.itertuples(index=False), data_start_row):
        cells = []
        for c_idx, v in enumerate(row, 1):
            if pd.notna(v):
                col = _col(c_idx)
                if isinstance(v, (int, float)) and not isinstance(v, bool):
                    cells.append(f'<c r="{col}{r_idx}"><v>{v}</v></c>')
                else:
                    cells.append(
                        f'<c r="{col}{r_idx}" t="inlineStr"><is><t>{_esc(v)}</t></is></c>'
                    )
        if cells:
            rows_xml.append(f'<row r="{r_idx}">{"".join(cells)}</row>')

    new_xml = (prefix + "".join(rows_xml) + suffix).encode("utf-8")

    # Build pivot-table → cache-definition mapping so we can apply the right patch.
    pt_to_cache: dict[str, int] = {}
    with zipfile.ZipFile(str(path), "r") as _zr:
        for _name in _zr.namelist():
            if (_name.startswith("xl/pivotTables/") and _name.endswith(".xml")
                    and "_rels" not in _name):
                _rels = _name.replace("xl/pivotTables/", "xl/pivotTables/_rels/") + ".rels"
                if _rels in _zr.namelist():
                    _rd = _zr.read(_rels).decode("utf-8")
                    _cm = re.search(r"pivotCacheDefinition(\d+)\.xml", _rd)
                    pt_to_cache[_name] = int(_cm.group(1)) if _cm else 1

    tmp = path.with_suffix(".tmp.xlsx")
    with zipfile.ZipFile(str(path), "r") as zin, \
         zipfile.ZipFile(str(tmp), "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == sheet_xml_name:
                zout.writestr(item.filename, new_xml)
            elif item.filename == "xl/workbook.xml":
                raw = zin.read(item.filename).decode("utf-8")
                raw = re.sub(
                    r'<calcPr\b[^>]*/>',
                    '<calcPr calcMode="auto" fullCalcOnLoad="1" forceFullCalc="1"/>',
                    raw,
                    count=1,
                )
                zout.writestr(item.filename, raw.encode("utf-8"))
            elif item.filename == "xl/calcChain.xml":
                pass  # stale after row rewrite; Excel regenerates on open
            elif item.filename.startswith("xl/tables/") and item.filename.endswith(".xml"):
                raw = zin.read(item.filename).decode("utf-8")
                if re.search(r'\bref="A' + str(header_row) + r':', raw):
                    # Table now has 11 columns: cols A-K include ชนิดเชื้อเพลิง at col I.
                    last_col = _col(len(dataframe.columns))
                    last_row = header_row + len(dataframe)
                    raw = re.sub(
                        r'(ref=")([^"]+)(")',
                        rf'\g<1>A{header_row}:{last_col}{last_row}\g<3>',
                        raw,
                    )
                    # Extend tableColumns count 10 → 11
                    raw = raw.replace('tableColumns count="10"', 'tableColumns count="11"', 1)
                    # Insert ชนิดเชื้อเพลิง column before Powertrain (id=9)
                    new_tc = '<tableColumn id="11" name="ชนิดเชื้อเพลิง"/>'
                    raw = raw.replace('<tableColumn id="9" ', new_tc + '<tableColumn id="9" ', 1)
                zout.writestr(item.filename, raw.encode("utf-8"))
            elif "pivotCacheDefinition" in item.filename and item.filename.endswith(".xml"):
                raw = zin.read(item.filename).decode("utf-8")
                patched = re.sub(
                    r'(<pivotCacheDefinition\b)([^>]*?)(/?>)',
                    lambda m: (
                        m.group(1) + m.group(2)
                        + (' refreshOnLoad="1"' if "refreshOnLoad" not in m.group(2) else "")
                        + m.group(3)
                    ),
                    raw, count=1,
                )
                # For cache def1: insert ชนิดเชื้อเพลิง field at position 8 and update count.
                if "pivotCacheDefinition1.xml" in item.filename:
                    patched = re.sub(
                        r'(<cacheFields\s+count=")(\d+)(")',
                        lambda m: m.group(1) + str(int(m.group(2)) + 1) + m.group(3),
                        patched, count=1,
                    )
                    new_cf = ('<cacheField name="ชนิดเชื้อเพลิง" numFmtId="49">'
                              '<sharedItems/></cacheField>')
                    _pos, _cnt = 0, 0
                    while True:
                        _idx = patched.find("<cacheField", _pos)
                        if _idx == -1: break
                        if _cnt == 8:
                            patched = patched[:_idx] + new_cf + patched[_idx:]
                            break
                        _pos = _idx + 1; _cnt += 1
                zout.writestr(item.filename, patched.encode("utf-8"))
            elif (item.filename.startswith("xl/pivotTables/") and item.filename.endswith(".xml")
                  and "_rels" not in item.filename):
                raw = zin.read(item.filename).decode("utf-8")
                cache_num = pt_to_cache.get(item.filename, 1)
                raw = _patch_pivot_table_def2(raw) if cache_num == 2 else _patch_pivot_table_def1(raw)
                zout.writestr(item.filename, raw.encode("utf-8"))
            else:
                zout.writestr(item, zin.read(item.filename))
    tmp.replace(path)
    print(f"      Saved: {path.name} ({len(dataframe):,} rows from row {data_start_row})")


def _rewrite_bev_series_table(workbook_path, df_cleaned):
    """Replace the 'BEV Series Name Table' sheet with a clean mapping table
    built from df_cleaned (electric rows only).
    Columns: Brand (A) | รุ่นรถ (B) | รุ่นรถ2 (C) | Powertrain (D)
    Column B is the XLOOKUP key used by the Data sheet formulas.
    """
    path = Path(workbook_path)

    bev_mask = df_cleaned["ชนิดเชื้อเพลิง"].astype(str).str.strip() == "ไฟฟ้า"
    # Sort so the most common brand for each model comes first, then dedup by รุ่นรถ.
    # This guarantees one row per XLOOKUP key (column B), preventing first-match ambiguity.
    freq = (
        df_cleaned[bev_mask]
        .groupby(["ยี่ห้อรถ2", "รุ่นรถ", "รุ่นรถ2", "Powertrain"])["จำนวนรถ"]
        .sum()
        .reset_index()
        .sort_values(["ยี่ห้อรถ2", "รุ่นรถ2", "รุ่นรถ", "จำนวนรถ"],
                     ascending=[True, True, True, False])
    )
    tbl = (
        freq
        .drop_duplicates(subset=["รุ่นรถ"], keep="first")
        [["ยี่ห้อรถ2", "รุ่นรถ", "รุ่นรถ2", "Powertrain"]]
        .reset_index(drop=True)
    )

    HEADERS = ["Brand", "รุ่นรถ", "รุ่นรถ2", "Powertrain"]
    last_data_row = len(tbl) + 1

    def _cell_s(col_idx, row_idx, value):
        try:
            if pd.isna(value):
                return ""
        except (TypeError, ValueError):
            pass
        s = str(value).strip()
        if not s or s.lower() in ("nan", "none", "<na>"):
            return ""
        col = _col(col_idx)
        return f'<c r="{col}{row_idx}" t="inlineStr"><is><t>{_esc(s)}</t></is></c>'

    rows_xml = []
    hdr = "".join(_cell_s(i + 1, 1, h) for i, h in enumerate(HEADERS))
    rows_xml.append(f'<row r="1">{hdr}</row>')
    for idx, row in tbl.iterrows():
        r = idx + 2
        cells = "".join([
            _cell_s(1, r, row["ยี่ห้อรถ2"]),
            _cell_s(2, r, row["รุ่นรถ"]),
            _cell_s(3, r, row["รุ่นรถ2"]),
            _cell_s(4, r, row["Powertrain"]),
        ])
        if cells:
            rows_xml.append(f'<row r="{r}">{cells}</row>')

    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
        ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheetData>' + "".join(rows_xml) + "</sheetData>"
        f'<autoFilter ref="A1:D{last_data_row}"/>'
        "</worksheet>"
    ).encode("utf-8")

    with zipfile.ZipFile(str(path), "r") as z:
        wb_xml   = z.read("xl/workbook.xml").decode("utf-8")
        rels_xml = z.read("xl/_rels/workbook.xml.rels").decode("utf-8")

    rid_m = (
        re.search(r'<sheet name="BEV Series Name Table"[^>]*r:id="([^"]+)"', wb_xml)
        or re.search(r'<sheet[^>]*r:id="([^"]+)"[^>]*name="BEV Series Name Table"', wb_xml)
    )
    if not rid_m:
        print("      Warning: 'BEV Series Name Table' sheet not found in workbook — skipping")
        return

    rid = rid_m.group(1)
    rel_m = re.search(rf'<Relationship\b(?=[^>]*\bId="{re.escape(rid)}")[^>]*/?>', rels_xml)
    target_m = re.search(r'Target="([^"]+)"', rel_m.group(0)) if rel_m else None
    if not target_m:
        print("      Warning: Could not resolve BEV Series Name Table part — skipping")
        return
    target = target_m.group(1).lstrip("/")
    sheet_part = f"xl/{target}" if not target.startswith("xl/") else target

    tmp = path.with_suffix(".tmp3.xlsx")
    with zipfile.ZipFile(str(path), "r") as zin, \
         zipfile.ZipFile(str(tmp), "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            if item.filename == sheet_part:
                zout.writestr(item.filename, sheet_xml)
            else:
                zout.writestr(item, zin.read(item.filename))
    tmp.replace(path)
    print(f"      Rebuilt BEV Series Name Table: {len(tbl):,} unique model rows")


def _add_summary_sheet(workbook_path, sheet_name, df_cleaned):
    """Add a new sheet with two side-by-side tables from df_cleaned:
    Cols A-C: ชนิดเชื้อเพลิง | Powertrain | Total (all fuel types)
    Cols E-I: Brand | รุ่นรถ | รุ่นรถ2 | Powertrain | Total (BEV series only)
    """
    path = Path(workbook_path)

    tbl_a = (
        df_cleaned
        .groupby(["ชนิดเชื้อเพลิง", "Powertrain"], dropna=False)["จำนวนรถ"]
        .sum()
        .reset_index()
        .sort_values(["Powertrain", "ชนิดเชื้อเพลิง"])
        .reset_index(drop=True)
    )

    bev_mask = df_cleaned["ชนิดเชื้อเพลิง"].astype(str).str.strip() == "ไฟฟ้า"
    tbl_b = (
        df_cleaned[bev_mask]
        .groupby(["ยี่ห้อรถ2", "รุ่นรถ", "รุ่นรถ2", "Powertrain"], dropna=False)["จำนวนรถ"]
        .sum()
        .reset_index()
        .sort_values(["ยี่ห้อรถ2", "รุ่นรถ2", "รุ่นรถ"])
        .reset_index(drop=True)
    )

    A_HEADERS = ["ชนิดเชื้อเพลิง", "Powertrain", "Total"]
    B_HEADERS = ["Brand", "รุ่นรถ", "รุ่นรถ2", "Powertrain", "Total"]
    A_OFF, B_OFF = 1, 5

    def _fmt(v):
        try:
            return f"{int(v):,}"
        except (TypeError, ValueError):
            return ""

    def _cell(col_idx, row_idx, value):
        try:
            if pd.isna(value):
                return ""
        except (TypeError, ValueError):
            pass
        col = _col(col_idx)
        ref = f"{col}{row_idx}"
        s = str(value).strip()
        if not s or s.lower() in ("nan", "none", "<na>"):
            return ""
        return f'<c r="{ref}" t="inlineStr"><is><t>{_esc(s)}</t></is></c>'

    # Collect all cells keyed by row number to avoid duplicate <row> elements
    row_cells: dict[int, list[str]] = {}

    def _add(r, *cells):
        row_cells.setdefault(r, []).extend(c for c in cells if c)

    # Header row
    _add(1,
        *[_cell(A_OFF + i, 1, h) for i, h in enumerate(A_HEADERS)],
        *[_cell(B_OFF + i, 1, h) for i, h in enumerate(B_HEADERS)],
    )

    # Table A data rows
    for idx, row in tbl_a.reset_index(drop=True).iterrows():
        r = idx + 2
        _add(r,
            _cell(A_OFF,     r, row["ชนิดเชื้อเพลิง"]),
            _cell(A_OFF + 1, r, row["Powertrain"]),
            _cell(A_OFF + 2, r, _fmt(row["จำนวนรถ"])),
        )

    # Grand Total — placed in the row right after Table A data
    grand_total = int(tbl_a["จำนวนรถ"].sum())
    gt_r = len(tbl_a) + 2
    _add(gt_r,
        _cell(A_OFF,     gt_r, "Grand Total"),
        _cell(A_OFF + 2, gt_r, _fmt(grand_total)),
    )

    # Table B data rows
    for idx, row in tbl_b.reset_index(drop=True).iterrows():
        r = idx + 2
        _add(r,
            _cell(B_OFF,     r, row["ยี่ห้อรถ2"]),
            _cell(B_OFF + 1, r, row["รุ่นรถ"]),
            _cell(B_OFF + 2, r, row["รุ่นรถ2"]),
            _cell(B_OFF + 3, r, row["Powertrain"]),
            _cell(B_OFF + 4, r, _fmt(row["จำนวนรถ"])),
        )

    rows_xml = [
        f'<row r="{r}">{"".join(cells)}</row>'
        for r, cells in sorted(row_cells.items())
        if cells
    ]

    sheet_xml = (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"'
        ' xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
        '<sheetData>' + "".join(rows_xml) + "</sheetData>"
        "</worksheet>"
    ).encode("utf-8")

    with zipfile.ZipFile(str(path), "r") as z:
        wb_xml   = z.read("xl/workbook.xml").decode("utf-8")
        rels_xml = z.read("xl/_rels/workbook.xml.rels").decode("utf-8")
        ct_xml   = z.read("[Content_Types].xml").decode("utf-8")
        all_parts = set(z.namelist())

    used_ns  = {int(m) for m in re.findall(r'xl/worksheets/sheet(\d+)\.xml', " ".join(all_parts))}
    next_n   = max(used_ns, default=0) + 1
    new_part = f"xl/worksheets/sheet{next_n}.xml"

    used_rids = {int(r) for r in re.findall(r'Id="rId(\d+)"', rels_xml)}
    new_rid   = f"rId{max(used_rids, default=0) + 1}"

    used_sids = {int(s) for s in re.findall(r'sheetId="(\d+)"', wb_xml)}
    next_sid  = max(used_sids, default=0) + 1

    esc_name = _esc(sheet_name)
    wb_xml = wb_xml.replace(
        "</sheets>",
        f'<sheet name="{esc_name}" sheetId="{next_sid}" r:id="{new_rid}"/></sheets>',
    )
    rels_xml = rels_xml.replace(
        "</Relationships>",
        f'<Relationship Id="{new_rid}" '
        f'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" '
        f'Target="worksheets/sheet{next_n}.xml"/>'
        "</Relationships>",
    )
    ct_xml = ct_xml.replace(
        "</Types>",
        f'<Override PartName="/xl/worksheets/sheet{next_n}.xml" '
        f'ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>'
        "</Types>",
    )

    tmp = path.with_suffix(".tmp2.xlsx")
    with zipfile.ZipFile(str(path), "r") as zin, \
         zipfile.ZipFile(str(tmp), "w", compression=zipfile.ZIP_DEFLATED) as zout:
        for item in zin.infolist():
            fname = item.filename
            if fname == "xl/workbook.xml":
                zout.writestr(fname, wb_xml.encode("utf-8"))
            elif fname == "xl/_rels/workbook.xml.rels":
                zout.writestr(fname, rels_xml.encode("utf-8"))
            elif fname == "[Content_Types].xml":
                zout.writestr(fname, ct_xml.encode("utf-8"))
            else:
                zout.writestr(item, zin.read(fname))
        zout.writestr(new_part, sheet_xml)

    tmp.replace(path)
    print(f"      Added sheet '{sheet_name}': {len(tbl_a)} fuel rows | {len(tbl_b)} BEV series rows")


def _new_model_path(df_raw: "pd.DataFrame", current_model: Path) -> Path:
    """Build the test run output filename, incrementing the run counter."""
    parent = BASE / "output"
    parent.mkdir(exist_ok=True)
    n = 1
    while (parent / f"test_{n}_masterModel.xlsx").exists():
        n += 1
    return parent / f"test_{n}_masterModel.xlsx"


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    raw1_file  = find_file(RAW1_PATTERN,  "fuel raw data")
    raw2_file  = find_file(RAW2_PATTERN,  "model raw data")

    # Find master Model template. Prefer refer/ when the operator keeps masters there.
    model_matches = [
        p for pattern in [
            str(BASE / "refer" / "*master*Model.xlsx"),
            str(BASE / "*master*Model.xlsx"),
            str(BASE / "refer" / "*masterModel.xlsx"),
            str(BASE / "*masterModel.xlsx"),
            str(BASE / "refer" / "*master*Model*.xlsx"),
            str(BASE / "*master*Model*.xlsx"),
            str(BASE / "output" / "*masterModel*.xlsx"),
        ]
        for p in glob.glob(pattern)
        if "~$" not in Path(p).name
    ]
    if not model_matches:
        print("ERROR: No masterModel.xlsx found in project root."); sys.exit(1)
    model_file = Path(max(model_matches, key=os.path.getmtime))

    print(f"Raw 1 (Fuel) : {raw1_file.name}")
    print(f"Raw 2 (Model): {raw2_file.name}")
    print(f"Master Model : {model_file.name}")

    # ── Parquet path (used for rolling rebuild and final save) ────────────────
    pq_path = BASE / "test_model_cleaned.parquet"
    df_existing = None

    if pq_path.exists():
        print(f"\n[Rolling rebuild] Loading existing: {pq_path.name}")
        df_existing = pd.read_parquet(str(pq_path))
        required_existing_cols = {"ปี", "เดือน", "ชนิดเชื้อเพลิง"}
        missing_existing_cols = required_existing_cols - set(df_existing.columns)
        if missing_existing_cols:
            print(
                "  Existing parquet is stale; missing column(s): "
                + ", ".join(sorted(missing_existing_cols))
            )
            print("  Rebuilding from raw data.")
            df_existing = None
        else:
            ex_key_col = df_existing["ปี"].astype(str) + "_" + df_existing["เดือน"].astype(str)
            print(f"  {len(set(ex_key_col.unique()))} year-month pairs | {len(df_existing):,} rows")
    else:
        print("\n[Full build] No existing parquet — rebuilding from scratch.")

    # 1. Reference tables
    print("\n[1/4] Reading reference tables...", flush=True)
    wb_ref = load_workbook(str(model_file), read_only=True, data_only=True)

    powertrain_map = load_powertrain_map(str(BASE / "config" / "powertrain_map.csv"))
    unknown_fuels = set()
    print(f"      {len(powertrain_map)} powertrain mappings")

    brand_csv_map = load_powertrain_map(str(BASE / "config" / "brand_map.csv"), "brand", "brand2")
    ref_brand2_map = {k.upper(): v for k, v in brand_csv_map.items()}
    brand_rows = sorted(ref_brand2_map.items())
    brand2_order = list(dict.fromkeys(v for _, v in brand_rows))
    brand2_table = [("Brand1", "Brand2")] + brand_rows
    merged_brand2_map = ref_brand2_map
    print(f"      {len(brand_rows)} ยี่ห้อรถ2 entries from brand_map.csv")

    # Read BEV Series Name Table
    bev_rows = []
    ws_bev = wb_ref["BEV Series Name Table"]
    for row in ws_bev.iter_rows(values_only=True):
        bev_rows.append(row)
    df_bev_tbl = pd.DataFrame(bev_rows)
    _bev       = df_bev_tbl.iloc[1:, [1, 2, 3]].dropna(subset=[1])
    known_bev_models = set(_bev.iloc[:, 0].astype(str).str.strip().str.upper())
    model2_map        = {str(k).strip().upper(): str(v).strip() for k, v in zip(_bev.iloc[:, 0], _bev.iloc[:, 1])}
    pt_from_model_map = {str(k).strip().upper(): str(v).strip() for k, v in zip(_bev.iloc[:, 0], _bev.iloc[:, 2])}

    wb_ref.close()

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
    df_model = enrich_fuel_type(df_model, df_fuel)
    print(f"      {len(df_fuel):,} fuel rows | {len(df_model):,} model rows")

    # 3. Derived columns
    print("\n[3/4] Adding derived columns...", flush=True)

    # df_fuel used only for master powertrain summary — not included in cleaned data.
    add_brand2(df_fuel, merged_brand2_map)
    df_fuel.insert(df_fuel.columns.get_loc("ยี่ห้อรถ2") + 1, "รุ่นรถ",  None)
    df_fuel.insert(df_fuel.columns.get_loc("รุ่นรถ")    + 1, "รุ่นรถ2", None)
    fuel_values = df_fuel["ชนิดเชื้อเพลิง"].dropna().astype(str).str.strip()
    unknown_fuels.update(f for f in fuel_values.unique() if f not in powertrain_map)
    df_fuel["Powertrain"] = df_fuel["ชนิดเชื้อเพลิง"].apply(
        lambda f: powertrain_map.get(str(f).strip(), "OTH") if pd.notna(f) else None)

    # Model rows: brand2, model2, powertrain (fuel first, model fallback)
    add_brand2(df_model, merged_brand2_map)
    if "รุ่นรถ" in df_model.columns:
        upper = df_model["รุ่นรถ"].astype(str).str.strip().str.upper()
        df_model.insert(df_model.columns.get_loc("รุ่นรถ") + 1, "รุ่นรถ2",
                        upper.map(model2_map).fillna(df_model["รุ่นรถ"]))

    if "ชนิดเชื้อเพลิง" in df_model.columns:
        model_fuel_values = df_model["ชนิดเชื้อเพลิง"].dropna().astype(str).str.strip()
        unknown_fuels.update(f for f in model_fuel_values.unique() if f not in powertrain_map)
        pt_fuel = df_model["ชนิดเชื้อเพลิง"].astype(str).str.strip().map(powertrain_map)
    else:
        pt_fuel = pd.Series(dtype=object, index=df_model.index)
    pt_model = (df_model["รุ่นรถ"].astype(str).str.strip().str.upper().map(pt_from_model_map)
                if "รุ่นรถ" in df_model.columns
                else pd.Series(dtype=object, index=df_model.index))
    if "ชนิดเชื้อเพลิง" in df_model.columns:
        is_electric = df_model["ชนิดเชื้อเพลิง"].astype(str).str.strip() == "ไฟฟ้า"
        pt_model = pt_model.where(is_electric)
    # Model-level lookup wins over generic fuel-level lookup.
    # pt_model is NaN for non-electric rows (gated by where(is_electric)),
    # so ICE/HEV/PHEV always fall back to pt_fuel correctly.
    powertrain_col = pt_model.combine_first(pt_fuel).fillna("OTH")
    if "Powertrain" in df_model.columns:
        df_model["Powertrain"] = powertrain_col
    else:
        df_model.insert(df_model.columns.get_loc("รุ่นรถ2") + 1, "Powertrain", powertrain_col)

    # df_fuel is used above for the master powertrain summary sheet only.
    # Final cleaned data uses df_model only — matches refer file row count (636,333).
    df_cleaned = ordered_cols(df_model)
    df_cleaned = sort_cleaned_data(df_cleaned, brand2_order)
    print(f"      {len(df_cleaned):,} raw rows processed | cols: {list(df_cleaned.columns)}")

    # ── Rolling merge: rebuild latest raw year and the year before it ───────────
    raw_year = pd.to_numeric(df_cleaned["ปี"], errors="coerce")
    latest_raw_year = int(raw_year.max())
    rebuild_years = {latest_raw_year - 1, latest_raw_year}
    rebuild_year_labels = sorted(str(y) for y in rebuild_years)
    raw_rebuild_mask = raw_year.isin(rebuild_years)
    raw_key = df_cleaned["ปี"].astype(str) + "_" + df_cleaned["เดือน"].astype(str)
    rebuilt_keys = set(raw_key[raw_rebuild_mask].unique())
    new_keys = set()
    corrected_keys = rebuilt_keys

    print(
        f"  Rolling rebuild: BE years {rebuild_year_labels} | "
        f"{len(rebuilt_keys)} month(s) from raw data"
    )

    if df_existing is not None:
        existing_year = pd.to_numeric(df_existing["ปี"], errors="coerce")
        existing_rebuild_mask = existing_year.isin(rebuild_years)
        existing_rebuild_key = ex_key_col[existing_rebuild_mask]
        existing_rebuild_keys = set(existing_rebuild_key.unique())
        new_keys = rebuilt_keys - existing_rebuild_keys
        corrected_keys = rebuilt_keys & existing_rebuild_keys

        df_keep = df_existing[~existing_rebuild_mask]
        df_add = df_cleaned[raw_rebuild_mask]
        df_cleaned = ordered_cols(
            sort_cleaned_data(pd.concat([df_keep, df_add], ignore_index=True), brand2_order)
        )

        print(f"  Kept rows before {min(rebuild_years)}: {len(df_keep):,}")
        if new_keys:
            print(f"  Added {len(new_keys)} new month(s): {', '.join(sorted(new_keys))}")
        if corrected_keys:
            print(f"  Rebuilt {len(corrected_keys)} existing month(s): "
                  f"{', '.join(sorted(corrected_keys))}")
        print(f"  Final row count: {len(df_cleaned):,}")

    # ── BEV review preflight: only scan the rolling rebuild window ─────────────
    bev_scope_year = pd.to_numeric(df_cleaned["ปี"], errors="coerce")
    bev_scope_mask = bev_scope_year.isin(rebuild_years)
    new_bev_records = resolve_bev_review(df_cleaned, known_bev_models, bev_scope_mask)

    # Save intermediate for pivot builder (parquet: safe, fast, preserves dtypes)
    # Cast object columns to str to avoid mixed-type ArrowTypeError
    for col in df_cleaned.select_dtypes(include=["object", "str"]).columns:
        df_cleaned[col] = df_cleaned[col].astype(str).replace("nan", pd.NA)
    df_cleaned.to_parquet(str(pq_path), index=False)
    print(f"      Saved intermediate: {pq_path.name}")

    # ── Save fuel parquet (rolling merge — same rebuild_years as model) ───────────
    fuel_pq_path = BASE / "test_fuel_cleaned.parquet"
    df_fuel_save = ordered_cols(df_fuel).copy()
    for col in df_fuel_save.select_dtypes(include=["object", "str"]).columns:
        df_fuel_save[col] = df_fuel_save[col].astype(str).replace("nan", pd.NA)
    if fuel_pq_path.exists():
        df_fuel_existing = pd.read_parquet(str(fuel_pq_path))
        fuel_raw_year = pd.to_numeric(df_fuel_save["ปี"], errors="coerce")
        fuel_rebuild_mask = fuel_raw_year.isin(rebuild_years)
        fuel_existing_year = pd.to_numeric(df_fuel_existing["ปี"], errors="coerce")
        df_fuel_keep = df_fuel_existing[~fuel_existing_year.isin(rebuild_years)]
        df_fuel_save = ordered_cols(pd.concat([df_fuel_keep, df_fuel_save[fuel_rebuild_mask]], ignore_index=True))
    df_fuel_save.to_parquet(str(fuel_pq_path), index=False)
    print(f"      Saved fuel intermediate: {fuel_pq_path.name}")

    # 4. Write output — copy current master Model to new versioned filename, update Data rows
    import shutil
    out_file = _new_model_path(df_model, model_file)
    print(f"\n[4/4] Output: {out_file.name}", flush=True)

    if out_file.resolve() != model_file.resolve() and out_file.exists():
        ans = input(f"  {out_file.name} already exists. Overwrite? [Y/N]: ").strip().upper()
        if ans != "Y":
            print("  Skipped. Existing file unchanged.")
            return

    if out_file.resolve() != model_file.resolve():
        shutil.copy2(model_file, out_file)
        print(f"  Copied {model_file.name} → {out_file.name}")

    rewrite_data_rows(out_file, df_cleaned, data_start_row=8)

    import json, datetime
    state = {
        "master_model":    str(out_file.relative_to(BASE)),
        "run_date":        str(datetime.date.today()),
        "new_months":      sorted(new_keys) if df_existing is not None else [],
        "corrected_months": sorted(corrected_keys) if df_existing is not None else [],
        "new_bev_models":  new_bev_records,
    }
    (BASE / "pipeline_state.json").write_text(
        json.dumps(state, ensure_ascii=False, indent=2), "utf-8"
    )

    known_models_path = BASE / "config" / "known_models.txt"
    known_models_path.parent.mkdir(exist_ok=True, parents=True)
    
    if "รุ่นรถ" in df_cleaned.columns and "ยี่ห้อรถ2" in df_cleaned.columns:
        curr_models_df = df_cleaned[["รุ่นรถ", "ยี่ห้อรถ2"]].dropna().copy()
        curr_models_df["รุ่นรถ_clean"] = curr_models_df["รุ่นรถ"].astype(str).str.strip()
        curr_models_df["ยี่ห้อรถ2_clean"] = curr_models_df["ยี่ห้อรถ2"].astype(str).str.strip()
        curr_models_df = curr_models_df[curr_models_df["รุ่นรถ_clean"] != ""]
        curr_models_df = curr_models_df.drop_duplicates(subset=["รุ่นรถ_clean"])

        if not known_models_path.exists():
            unique_models = sorted(curr_models_df["รุ่นรถ_clean"].unique())
            with open(known_models_path, "w", encoding="utf-8") as f:
                for m in unique_models:
                    f.write(f"{m}\n")
            print(f"known_models.txt created with {len(unique_models)} models")
        else:
            with open(known_models_path, "r", encoding="utf-8") as f:
                known = {line.strip() for line in f if line.strip()}
            
            new_models = []
            for _, row in curr_models_df.iterrows():
                m = row["รุ่นรถ_clean"]
                if m not in known:
                    b = row["ยี่ห้อรถ2_clean"]
                    print(f"NEW MODEL DETECTED: {m} (brand: {b})")
                    new_models.append(m)
            
            if new_models:
                with open(known_models_path, "a", encoding="utf-8") as f:
                    for m in new_models:
                        f.write(f"{m}\n")

    print(f"\n  Rows : {len(df_cleaned):,}")
    print(f"  → {out_file.name}")
    print("  → pipeline_state.json updated")
    print(f"Unknown fuel types (->OTH): {sorted(unknown_fuels)}")


if __name__ == "__main__":
    main()
