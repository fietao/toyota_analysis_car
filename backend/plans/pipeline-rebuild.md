# Pipeline Rebuild Plan

**Date:** 2026-06-20  
**Deadline:** 2 days  
**Owner:** Jet + Claude (+ Codex for parallel safe tasks)

---

## Goal

Automate the boss's monthly Excel report. Every month, two raw DLT files arrive. The pipeline should update both master Excel files — all numbers current, all 8 analysis sheets regenerated, MoM and YoY growth columns correct — with one command. Boss copies those 8 sheets to PowerPoint without touching them.

---

## Deliverable

- `UPDATE.bat` runs once → both master Excel files fully updated
- `*(master cal).xlsx` — Data sheet + 8 analysis sheets current
- `*(master Model).xlsx` — Data sheet + master powertrain sheet current
- Pipeline does not crash, does not block on unknown BEVs, does not reprocess 50k+ rows on every run

---

## Chosen Approach — Python-Friendly Template + Static Sheet Generation

Copy master files as template → Python writes Data sheet + regenerates 8 analysis sheets as static tables. The 8 sheets are **not pivot tables** — they are plain number tables with only two formula columns (MoM growth %, YoY growth %). Python calculates and writes everything. Boss's familiar format is preserved.

**Why this over alternatives:**
- Web dashboard: weeks of work, 2-day deadline rules it out
- Blank fresh Excel: boss wants familiar format, not new layout
- Pivot auto-refresh: sheets are static (confirmed), not wired to Data sheet — refresh does nothing
- xlwings/COM automation: fragile, requires desktop Excel, adds dependency

---

## Alternatives Considered

| Option | Why Rejected |
|--------|-------------|
| Web dashboard | Weeks of work vs 2-day deadline |
| Pivot auto-refresh | Sheets confirmed static, not linked |
| Keep manual workflow | Defeats the entire goal |
| Codex + Claude on same file simultaneously | Race condition — each undoes the other's edits |

---

## Key Constraints

- **AI coordination:** Claude owns one file at a time. Codex owns a different file. Never both editing the same script simultaneously.
- **Boss workflow:** Boss opens the output Excel, selects all 8 sheets, copies to PowerPoint. No Excel skills required on his end.
- **Thai encoding:** Always run with `$env:PYTHONUTF8=1` or `PYTHONIOENCODING=utf-8`.
- **Read-only sheets:** `master powertrain`, `BEV by Model`, `BEV by Model (2)`, `BMW` — Python MUST NOT write to these.

---

## Architecture — 5 Scripts

```
ingest          (update_raw_data.py)    — copy new DLT files in
clean           (build_cleaned.py)      — incremental merge → Data sheet → parquet
analyze         (analyze.py)            — NEW: read parquet → compute 8 analysis tables
export          (export.py / existing)  — write analysis tables to mastercal sheets
pipeline        (run_pipeline.py)       — orchestrates all 5 in order
```

---

## Fix Order (Day 1)

All fixes land in one `build_cleaned.py` refactor. Do them in this order — each one unblocks the next.

### B2 — Add ชนิดเชื้อเพลิง to df_cleaned
- During clean step: join model rows with fuel file on `เลขทะเบียน` (or matching key)
- Keep `ชนิดเชื้อเพลิง` column in df_cleaned all the way through to parquet and Data sheet
- **Never write to `master powertrain` sheet** — it's a pivot, read-only to Python
- 32-row mapping: ไฟฟ้า→BEV, เบนซิน/ดีเซล/CNG→ICE, *-ไฟฟ้า→HEV, *-ไฟฟ้าแบบเสียบปลั๊ก→PHEV, ไม่ระบุ/ไม่ใช้เชื้อเพลิง→N/A

### B4 — Fix BEV detection
- Detect by `ชนิดเชื้อเพลิง == "ไฟฟ้า"` (not `Powertrain.startswith("BEV")`)
- Print new unknown models to stdout — **continue pipeline, do not block**
- Operator updates BEV Series Name Table manually, then re-runs

### pipeline_state.json crash fix
- At end of `build_cleaned.py main()`, write:
  `{"master_model": "<filename>", "new_bev_models": [<list>]}`
- `build_BEV.py` currently crashes at startup if this file is missing

### B1 — Incremental-first refactor (13-step design, agreed session 7)
- Check parquet BEFORE any processing
- Enrich ONLY new/corrected months (not all 50k+ rows)
- Data sheet still fully rewritten each run (full sort requires merged result)
- Corrections: scope to last 2 BE years; row count OR total `จำนวนรถ` change = correction

### B3 — Remove xlsxwriter pivot-building from build_BEV.py
- Remove ALL xlsxwriter code that rebuilds BEV/BMW sheets
- build_BEV.py single job: append new rows to `BEV Series Name Table` only
- Separate task from B1 — do this after B1 is stable

---

## Day 2 — Build analyze.py (8 Analysis Sheets)

### What the 8 sheets look like
Each sheet is a static table: categories down rows, columns are current month count + share % + MoM growth % + YoY growth %. **Not pivot tables.** Only the growth % columns have formulas (or Python can calculate and write as static numbers).

### Sheet list (mastercal)
1. Reg by Powertrain
2. Reg by Brand
3. Reg by Segment
4. Reg by Body Type
5. Reg by Province
6. Reg by Model (BEV)
7. Reg by Fuel Type
8. Rank by BEV Model

### Write strategy (openpyxl)
1. Read parquet → `df_cleaned`
2. Filter to current month
3. For each of the 8 sheets: groupby + agg → DataFrame → write to sheet starting at correct row
4. Calculate MoM (current month vs previous month) and YoY (current month vs same month last year) in Python; write as numbers
5. Preserve column headers and any formatting in template — only overwrite data rows

### Template strategy
- Copy master Excel file as template at start of each run
- Python opens the copy, writes its sheets, saves
- Original master is never modified in place

---

## Done Criteria

- [ ] `$env:PYTHONUTF8=1; python update_raw_data.py "fuel.xlsx" "model.xlsx"` runs to completion without crash
- [ ] `pipeline_state.json` exists after run
- [ ] `ชนิดเชื้อเพลิง` column present in Data sheet of both masters
- [ ] BEV detection prints new unknown models; does NOT block pipeline
- [ ] 8 analysis sheets in mastercal show current month numbers
- [ ] MoM and YoY columns correct (spot-check 2–3 rows against manual calculation)
- [ ] Boss can copy 8 sheets to PowerPoint without any manual number edits
- [ ] No BEV/BMW/master powertrain pivot sheets overwritten

---

## Risks

| Risk | Mitigation |
|------|-----------|
| Claude + Codex editing same file → race condition | One AI per file at a time. Write in this file which AI owns which script. |
| Template redesign eating all of Day 1 | Start with minimal template change — don't redesign what doesn't need to change |
| Growth formula logic wrong (MoM/YoY edge cases: new month, missing prior year) | Handle missing prior period as N/A, not 0% or error |
| Thai column name typos | Always copy-paste Thai column names from existing parquet/Data sheet |
| openpyxl row offset wrong → numbers written to wrong cells | Spec the row/column offsets per sheet before writing code |

---

## AI Coordination Rule

> **Claude owns:** `build_cleaned.py`, `analyze.py`, plan docs  
> **Codex handles:** separate isolated tasks only (e.g., a standalone helper, a new file)  
> **Never:** both editing the same script in the same session

---

## Run Commands

```powershell
# Full monthly update
$env:PYTHONUTF8=1; python update_raw_data.py "fuel.xlsx" "model.xlsx"

# Pipeline only (no new files)
$env:PYTHONUTF8=1; python run_pipeline.py --skip-map

# Clean step only
$env:PYTHONUTF8=1; python build_cleaned.py
```
