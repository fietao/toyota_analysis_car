---
name: analyze-therefer
description: Analyst Agent skill — read the reference Model.xlsx and extract its full format blueprint: header colors, font styles, column widths, sort order, frozen panes, autofilter, table structure — sheet by sheet. Use this to understand exactly what the output workbook should look like so the Analyst can tell the Data Cleaner what format to match. Trigger on /analyze-therefer or when the analyst needs to know the reference format spec.
---

# Skill: Analyze the Reference (Analyst Agent only)

This skill reads the **reference file only** and produces a format blueprint.
Use it before `/analyze-workbook` to know what "correct" looks like, or whenever
the reference format needs to be documented for the Data Cleaner.

## Step 1 — Run the format reader

```powershell
$env:PYTHONUTF8=1
python .claude/scripts/read_refer_format.py
```

This opens the reference `*- Model.xlsx` once (with style access) and prints
per sheet:
- Dimensions
- Frozen panes and autofilter range
- Column widths
- Header row index + each column's value and cell format (bold, bg color, font color, alignment, number format)
- First 3 data rows
- Data row cell formats

## Step 2 — Feed to local LLM for interpretation

```python
import requests

blueprint = """[paste full script output here]"""

prompt = f"""/no_think
You are reading a format blueprint of a Thai DLT car data reference Excel file.
For each sheet, summarize:
1. What the header row looks like (colors, bold, alignment)
2. What the data rows look like (any conditional formatting, color coding)
3. Column order and widths
4. Sort order of the data
5. Any special structure (merged cells, frozen rows, autofilter)

Write a clear format spec the Data Cleaner Agent can use to reproduce this exactly.

---
{blueprint}
---"""

resp = requests.post("http://localhost:11434/api/generate", json={{
    "model": "qwen3:8b",
    "prompt": prompt,
    "stream": False,
    "options": {{"temperature": 0.1}}
}}, timeout=180)
print(resp.json()["response"])
```

## Step 3 — Write the Format Spec

Produce a format spec in this structure:

```
========================================
REFERENCE FORMAT SPEC
File: [ref filename]
========================================

SHEET: master powertrain
  Header row   : row 7
  Header style : bold, bg=#4472C4, font=white
  Columns      : A=ชนิดเชื้อเพลิง (width=25), B=Powertrain (width=15), C=Total (width=12)
                 E=ชนิดเชื้อเพลิง, F=Powertrain (reference copy, cols E:F)
  Data style   : active rows → bold, font=#4472C4
                 unknown rows → bold, bg=#FFF2CC, font=#9C6500
  Autofilter   : A7:C7
  Sort         : fixed order (MASTER_POWERTRAIN_ORDER)

SHEET: Cleaned Data (= "Data" in reference)
  Header row   : row 6
  Header style : bold, bg=#4472C4, font=white, border=1
  Columns      : ปี(8) | เดือน(12) | ประเภทรถ(35) | จังหวัด(20) | ยี่ห้อรถ(20) | ยี่ห้อรถ2(18) | ...
  Table style  : Table Style Medium 2
  Sort         : ปี asc → เดือน (month order) → ยี่ห้อรถ asc

[continue for each sheet]
========================================
```

## Step 4 — Save and hand off

Save the format spec to `.claude/refer_format_spec.md` in the project root.
Tell the user: "Format spec saved. The Data Cleaner can now use this as the target."
