"""Compare standalone sheet1 vs template-patched output for rows 8-12, 14-18."""
import sys, zipfile, re
from pathlib import Path
sys.stdout.reconfigure(encoding="utf-8")

BASE = Path("backend")

def find_file(pattern):
    matches = sorted(BASE.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[0] if matches else None

template_out = find_file("*test analyst*.xlsx")
standalone   = find_file("*standalone*.xlsx")

if not template_out or not standalone:
    print(f"template_out: {template_out}")
    print(f"standalone:   {standalone}")
    sys.exit(1)

print(f"Template output : {template_out.name}")
print(f"Standalone      : {standalone.name}")


def read_sheet_cells(xlsx_path, sheet_name, rows):
    with zipfile.ZipFile(str(xlsx_path), "r") as z:
        wb_xml   = z.read("xl/workbook.xml").decode("utf-8")
        rels_xml = z.read("xl/_rels/workbook.xml.rels").decode("utf-8")
        m = re.search(rf'<sheet\b[^>]*name="{re.escape(sheet_name)}"[^>]*r:id="([^"]+)"', wb_xml)
        if not m:
            m = re.search(rf'<sheet\b[^>]*r:id="([^"]+)"[^>]*name="{re.escape(sheet_name)}"', wb_xml)
        if not m:
            return {}
        rid = m.group(1)
        m2 = re.search(rf'<Relationship\b[^>]*Id="{re.escape(rid)}"[^>]*Target="([^"]+)"', rels_xml)
        if not m2:
            m2 = re.search(rf'<Relationship\b[^>]*Target="([^"]+)"[^>]*Id="{re.escape(rid)}"', rels_xml)
        target   = m2.group(1).lstrip("/")
        xml_name = target if target.startswith("xl/") else f"xl/{target}"
        sheet_xml = z.read(xml_name).decode("utf-8")

    cells = {}
    for row_num in rows:
        m = re.search(rf'<row r="{row_num}"[^>]*>.*?</row>', sheet_xml, re.DOTALL)
        if not m:
            continue
        row_xml = m.group(0)
        for cm in re.finditer(r'<c r="([A-Z]+)\d+"[^>]*>(.*?)</c>', row_xml, re.DOTALL):
            col = cm.group(1)
            inner = cm.group(2)
            v_m = re.search(r'<v>(.*?)</v>', inner)
            if v_m:
                try:
                    cells[(row_num, col)] = float(v_m.group(1))
                except ValueError:
                    cells[(row_num, col)] = v_m.group(1)
    return cells


DATA_ROWS = list(range(8, 13)) + list(range(14, 19))

# Only compare the numeric-data columns Python actually writes (B–AC).
# Labels (A, H) are stored as shared-string indices in template vs inline strings
# in standalone — semantically equal but structurally different.
# AE+ are Excel-formula columns beyond Python's write range.
DATA_COLS_PRIMARY   = set("B C D E F G H I J K L M N O P Q R S T U V W X Y Z AA AB AC".split())
DATA_COLS_SECONDARY = {"I"}  # rows 14-18: only I is numeric (H is a label)

t_cells = read_sheet_cells(template_out, "1.Reg by Powertrain", DATA_ROWS)
s_cells = read_sheet_cells(standalone,   "1.Reg by Powertrain", DATA_ROWS)

mismatches = 0
for key in sorted(t_cells.keys(), key=lambda k: (k[0], k[1])):
    row, col = key
    if row <= 12:
        if col not in DATA_COLS_PRIMARY:
            continue
    else:  # rows 14-18
        if col not in DATA_COLS_SECONDARY:
            continue
    t_val = t_cells[key]
    s_val = s_cells.get(key)
    if s_val is None:
        print(f"  MISSING  ({row},{col:3s}): template={t_val}")
        mismatches += 1
    elif abs(float(t_val) - float(s_val)) > 1e-9:
        print(f"  MISMATCH ({row},{col:3s}): template={t_val}  standalone={s_val}")
        mismatches += 1

if mismatches == 0:
    print(f"\nOK — all numeric data cells (B–AC) match between template output and standalone.")
else:
    print(f"\n{mismatches} mismatches found.")
