# Project Roadmap

Last updated: 2026-06-18 (session 3)

---

## Done

- Split `build_model.py` → `build_cleaned.py` + `build_pivots.py` + `read_raw.py`
- Updated `run_pipeline.py` to call: `build_cleaned.py` → `build_pivots.py` → `build_analyst.py`
- Updated `data-cleaner.md` and `analyst.md` agent files to reflect split ownership
- Switched pickle → parquet for safe intermediate storage (`test_model_cleaned.parquet`)
- Installed 9arm-skills: `debug-mantra`, `post-mortem`, `qwen-agent`, `scrutinize`, `management-talk`, `qwenchance`
- CLAUDE.md: added grill-first rule (Section 0) + session-start rule (invoke `/qwenchance`)
- `analyst_read_workbook.py` — fixed memory leak, large-sheet skip, sort sample size
- `read_refer_format.py` — extracts format blueprint from reference Model.xlsx
- Skills: `analyze-workbook`, `analyze-therefer`
- **`build_model2_map.py` wired into `build_cleaned.py`** — `build_cleaned.py` now loads `refer/model2_map.csv` (if present) and merges it as the primary source for `รุ่นรถ2` mapping; BEV table in Excel is the fallback
- **ยี่ห้อรถ2 map/sort read from refer1** — brand → ยี่ห้อรถ2 map and sort order now read from E-F rows 0–6 of "master powertrain" sheet in refer1 (hardcoded BRAND2_MAP is fallback); reference table in Cleaned Data sheet (col N-O) also comes from Excel
- **pyarrow unblocked** — installed; pipeline runs successfully end-to-end (636,333 rows)
- **`build_model2_map.py` run** — `refer/model2_map.csv` exists with 8,358 mappings; confirmed wired into `build_cleaned.py`
- **master powertrain source-of-truth fix** — sheet now copied as-is from `*- Model.xlsx` template (not recomputed from raw data); Grand Total matches hand-calculated reference (14,601,983)
- **master powertrain formatting** — header row (A-C + E-F) highlighted blue bold; E-F rows whose fuel type appears in A-C summary are bold + light blue (`#BDD7EE`); Grand Total row fully highlighted; `(blank)` and `ไม่ใช้เชื้อเพลิง` Powertrain → `N/A`; `keep_default_na=False` preserves `N/A` strings from template
- **master powertrain col C comma format** — all numeric totals (data rows + Grand Total) use `#,##0` thousands-separator format
- **Status line configured** — persistent bar showing repo | model | ctx% | 5h% via `~/.claude/statusline-command.sh`
- **BEV Series Name Table built** — `build_pivots.py` creates the table from parquet + 24 OTH seed rows from `refer/bev_series_name_table_template_rows.csv`; 238 rows (BEV Major 188, BEV 26, OTH 24); OTH rows hidden; Aptos Narrow formatting
- **`build_model.py` deleted** — nothing called it; pipeline confirmed working without it
- **Repo root reorganized** — loose files moved to `refer/`, `specs/`, `tools/`; stale `.aider` artifacts deleted

---

## To Do

### 1. Resolve Analyst vs Cleaner architecture (discussion first, then code)
Open questions:
- Is Analyst read-only (never runs a build script)?
- Does Analyst own `build_pivots.py` or does Cleaner own everything that writes xlsx?
- What triggers the Analyst — manual skill call or step 0 of `run_pipeline.py`?

Then redesign:
- [ ] Analyst: reads raw/refer → analyzes → writes structured brief
- [ ] Cleaner: reads brief → runs `build_cleaned.py` → runs `build_pivots.py`
- [ ] Update agent `.md` files accordingly

### 2. Fix `G6 → "G 6"` cosmetic bug
- [ ] In `build_cleaned.py` normalization: change letter-digit split regex so it only triggers on 3+ digit numbers (not `G6`, `X5`, etc.)

### 3. Full pipeline test
- [ ] Run `run_pipeline.py` end-to-end
- [ ] Verify `test_model_1.xlsx` → `build_analyst.py` → analyst xlsx looks correct
- [ ] Check pivot sheet formatting (openpyxl copy only copies values, not styles — may need fix)

---

## Known Issues

- `build_pivots.py` copies sheets via openpyxl `append()` — values only, no cell formatting carried over from xlsxwriter
- Ollama `qwen3:8b` runs on CPU (~25s/call) because `qwen3:32b` occupies the GPU — slow for large LLM tasks
