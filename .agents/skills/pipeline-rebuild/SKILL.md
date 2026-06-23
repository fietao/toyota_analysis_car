---
name: pipeline-rebuild
description: Execute the Thai DLT car registration pipeline rebuild. Use when implementing build_cleaned.py refactor (B1-B4 bugs), building analyze.py for 8 analysis sheets, or running the full monthly pipeline update.
---

# Pipeline Rebuild Skill

See full plan: `plans/pipeline-rebuild.md`

## Fix Order

Always in this sequence — each fix unblocks the next:

1. **B2** — Add `ชนิดเชื้อเพลิง` to df_cleaned (join from fuel file)
2. **B4** — BEV detection via `ชนิดเชื้อเพลิง == "ไฟฟ้า"` (not Powertrain startswith)
3. **pipeline_state.json** — write at end of build_cleaned.py main()
4. **B1** — Incremental-first 13-step refactor (check parquet before enriching)
5. **B3** — Remove xlsxwriter pivot code from build_BEV.py (separate task)
6. **analyze.py** — NEW: generate 8 static analysis sheets from parquet

## Key Rules

- `master powertrain`, `BEV by Model`, `BEV by Model (2)`, `BMW` → **read-only to Python, never write**
- 8 analysis sheets in mastercal → **static tables, not pivots** — Python owns them entirely
- BEV detection → **print and continue, never block**
- Thai encoding → always `$env:PYTHONUTF8=1`
- AI coordination → **one AI per file at a time**

## 8 Analysis Sheets Structure

Each sheet: category rows × [count | share% | MoM growth% | YoY growth%]  
Growth columns: calculate in Python from parquet, write as static numbers.  
Missing prior period → write N/A, not 0 or error.

## Common Failure Modes

- Writing to pivot sheets → corrupts workbook (B3 was exactly this)
- BEV detection on Powertrain instead of ชนิดเชื้อเพลิง → misses unknown models (B4)
- Enriching all 50k rows before incremental check → slow every run (B1)
- pipeline_state.json missing → build_BEV.py crashes at startup
- Thai column name typos → always copy-paste from existing parquet, never retype

## Verify Done

```
python update_raw_data.py "fuel.xlsx" "model.xlsx"  # no crash
→ pipeline_state.json exists
→ ชนิดเชื้อเพลิง column in Data sheet
→ 8 analysis sheets updated in mastercal
→ MoM/YoY spot-checked against manual calc
```
