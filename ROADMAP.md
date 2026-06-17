# Project Roadmap

Last updated: 2026-06-17

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

---

## Blocked (fix first)

- [ ] **`pyarrow` not installed** — `build_cleaned.py` crashes on `to_parquet()`. Run `pip install pyarrow` in the correct venv before anything else.

---

## To Do

### 1. Generate `model2_map.csv` (prerequisite for รุ่นรถ2)
- [ ] Run `build_model2_map.py` once — needs Ollama + `qwen3:8b` running locally
- [ ] Output lands at `refer/model2_map.csv`; every subsequent run is incremental (new months only)

### 2. Unblock & verify pipeline
- [ ] Install pyarrow
- [ ] Run `build_cleaned.py` and check console output:
  - `X ยี่ห้อรถ2 entries from refer1 (E-F rows 0-6)` → brand table read from Excel ✓
  - `ยี่ห้อรถ2: using hardcoded table` → E-F rows 0-6 were empty; confirm actual row range in refer1 and fix offset
- [ ] Run `build_cleaned.py` → `build_pivots.py` end-to-end
- [ ] Verify `test_model_1.xlsx`: Cleaned Data sorted by ยี่ห้อรถ2 in refer1 order, master powertrain matches refer1 E-F exactly

### 3. Resolve Analyst vs Cleaner architecture (discussion first, then code)
Open questions:
- Is Analyst read-only (never runs a build script)?
- Does Analyst own `build_pivots.py` or does Cleaner own everything that writes xlsx?
- What triggers the Analyst — manual skill call or step 0 of `run_pipeline.py`?

Then redesign:
- [ ] Analyst: reads raw/refer → analyzes → writes structured brief
- [ ] Cleaner: reads brief → runs `build_cleaned.py` → runs `build_pivots.py`
- [ ] Update agent `.md` files accordingly

### 4. Fix `G6 → "G 6"` cosmetic bug
- [ ] In `build_cleaned.py` normalization: change letter-digit split regex so it only triggers on 3+ digit numbers (not `G6`, `X5`, etc.)

### 5. Full pipeline test
- [ ] Run `run_pipeline.py` end-to-end
- [ ] Verify `test_model_1.xlsx` → `build_analyst.py` → analyst xlsx looks correct
- [ ] Check pivot sheet formatting (openpyxl copy only copies values, not styles — may need fix)

### 6. Clean up `build_model.py`
- [ ] Nothing calls it anymore — delete or archive once pipeline is verified working

---

## Known Issues

- `build_pivots.py` copies sheets via openpyxl `append()` — values only, no cell formatting carried over from xlsxwriter
- Ollama `qwen3:8b` runs on CPU (~25s/call) because `qwen3:32b` occupies the GPU — slow for large LLM tasks
- Brand table row range in refer1 assumed to be E-F rows 0–6 — needs verification on first run
