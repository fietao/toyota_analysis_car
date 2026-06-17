---
name: analyze-workbook
description: Analyst Agent skill — inspect the output workbook and reference file sheet by sheet, use a local LLM to interpret findings, compare structure/format/color against the reference, and produce a structured brief for the Data Cleaner Agent. Use this whenever the Analyst Agent needs to understand what is in the workbook and communicate what the Data Cleaner should fix, add, or change. Trigger on /analyze-workbook or when the analyst needs to inspect or compare workbook sheets.
---

# Skill: Analyze Workbook (Analyst Agent only)

You are the **Analyst Agent**. This skill does NOT belong to the Data Cleaner Agent.

## Step 1 — Run the Python reader

Run the inspection script from the project root:

```powershell
$env:PYTHONUTF8=1
python .claude/scripts/analyst_read_workbook.py
```

This reads both `test_model_1.xlsx` (output) and `*- Model.xlsx` (reference) and prints:
- Sheet names in both files
- Sheets missing from output or extra vs reference
- Per sheet: dimensions, column headers, header styles, sort order, sample row
- Column-level stats for data sheets: data type, null count, unique count, sample values

Capture the full output. If the script errors, report the error and stop.

## Step 2 — Feed output to local LLM for interpretation

Send the script output to the local LLM for analysis:

```python
import requests, json

script_output = """[paste the full script output here]"""

prompt = f"""/no_think
You are analyzing a Thai DLT car registration data pipeline.
Below is the inspection output from comparing the generated workbook against the reference.

Your job:
1. For each sheet, note what looks correct vs what differs from the reference
2. Identify data quality issues (nulls, unmapped values, wrong sort order, missing columns)
3. Note any format/color differences from the reference
4. Write specific action items for the Data Cleaner Agent

Be specific. Name the exact columns, sheets, and values that need attention.

---
{script_output}
---

Write your analysis:"""

resp = requests.post("http://localhost:11434/api/generate", json={
    "model": "qwen3:8b",
    "prompt": prompt,
    "stream": False,
    "options": {"temperature": 0.1}
}, timeout=180)

print(resp.json()["response"])
```

## Step 3 — Verify accuracy

Compare the LLM's interpretation against the raw script output.
Correct anything the LLM got wrong or missed. The script output is the ground truth.

## Step 4 — Write the Data Cleaner Brief

Produce a brief in this exact format:

```
========================================
WORKBOOK ANALYSIS BRIEF
Date: [today]
Output file : test_model_1.xlsx
Reference   : [ref file name]
========================================

SHEET COMPARISON
┌─────────────────────────┬──────────┬──────────┬──────────┐
│ Sheet                   │ Out dims │ Ref dims │ Status   │
├─────────────────────────┼──────────┼──────────┼──────────┤
│ Cleaned Data            │ 857k×11  │ 636k×15  │ ⚠ diff   │
│ master powertrain       │ 39×6     │ 39×6     │ ✓ match  │
│ ...                     │          │          │          │
└─────────────────────────┴──────────┴──────────┴──────────┘

ISSUES FOR DATA CLEANER
------------------------

[Sheet: Cleaned Data]
- รุ่นรถ2: 6,200 rows showing raw model name → populate refer/model2_map.csv
- Powertrain: 400 rows = "Other" → check unmapped fuel types in master powertrain
- ชนิดเชื้อเพลิง col: blank for all model rows (expected, not an issue)

[Sheet: master powertrain]
- Dimensions match reference ✓
- "ไม่ระบุ" row: 6 registrations, highlighted yellow — confirm with user

[Sheet: BEV by Model]
- 1 row fewer than reference (109 vs 110) → check if BEV brand missing

COLUMNS TO ADD / CHANGE
-----------------------
- [list any columns that need to be added, renamed, reordered, or removed]

FORMAT / COLOR NOTES
--------------------
- [any cell style differences vs reference that Data Cleaner should match]

SORT ORDER
----------
- [any sheets where sort is wrong or missing]

READY FOR DATA CLEANER: YES / NO (with reason if NO)
========================================
```

## Step 5 — Hand off

Show the brief to the user and say:
"Analysis complete. Should I pass this brief to the Data Cleaner Agent?"

Wait for confirmation before escalating. This skill does not run any cleaning itself.
