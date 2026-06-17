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

---

## Blocked (fix first)

- [ ] **`pyarrow` not installed** — `build_cleaned.py` crashes on `to_parquet()`. Run `pip install pyarrow` in the correct venv before anything else.

---

## To Do

### 1. Unblock & verify pipeline
- [ ] Install pyarrow
- [ ] Run `build_cleaned.py` → `build_pivots.py` end-to-end
- [ ] Verify `test_model_1.xlsx` has all 6 sheets: Cleaned Data, master powertrain, BEV Series Name Table, BEV by Model, BEV by Model (2), BMW

### 2. Resolve Analyst vs Cleaner architecture (discussion first, then code)
Open questions to answer before touching anything:
- Is Analyst read-only (never runs a build script)?
- Does Analyst own `build_pivots.py` or does Cleaner own everything that writes xlsx?
- What does "send a brief to Cleaner" look like — a markdown file? a prompt?
- What triggers the Analyst — manual skill call or step 0 of `run_pipeline.py`?
- Who owns pivot sheets — Analyst (decides what to build) or Cleaner (executes the build)?

Then redesign:
- [ ] Analyst: reads raw/refer → analyzes → writes structured brief
- [ ] Cleaner: reads brief → runs `build_cleaned.py` → runs `build_pivots.py`
- [ ] Update agent `.md` files accordingly

### 3. Fix `G6 → "G 6"` cosmetic bug
- [ ] In `build_cleaned.py` normalization: change letter-digit split regex so it only triggers on 3+ digit numbers (not `G6`, `X5`, etc.)

### 4. Decide on `รุ่นรถ2` normalization (`build_model2_map.py`)
- [ ] Either integrate Python-only normalization into `build_cleaned.py`
- [ ] Or decide LLM approach (qwen3:8b incremental mapping) is worth it and wire it in
- [ ] `build_model2_map.py` exists but is not connected to the pipeline yet

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
- `build_model2_map.py` written but not integrated
