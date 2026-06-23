# Agent Meeting Board

Shared coordination board for Claude, Codex, and any other AI agent working in this repo.

## Meeting Rules

- Read `AGENTS.md`, then this file, before doing work.
- Run `git status --short` before editing.
- Claim the files you plan to edit before changing them.
- Do not edit files claimed by another active agent unless the board says the work is handed off.
- Append updates; do not rewrite another agent's notes except to fix obvious typos.
- When finished, record changed files, commands run, verification results, blockers, and next recommended action.

---

## Current State (2026-06-22, session 10)

Pipeline scripts are in **`backend/`**. Old paths (project root, `.claude/scripts/`) are stale — ignore them.

| Script | Status | Notes |
|---|---|---|
| `backend/build_cleaned.py` | ✅ Working | 636,392 rows, 13,722,286 units — matches revised raw release (B6 closed, not a bug) |
| `backend/build_BEV.py` | ✅ Working | 0 new BEV rows this run; all 888 models already in table |
| `backend/build_analyst.py` | 🔴 Blocked | Needs `*(master cal).xlsx` restored |
| `diagnose_pipeline.py` | ✅ New tool | Run from project root; prints raw vs parquet vs master comparison |

**Active blockers:**
- 🔴 `*(master cal).xlsx` missing — operator must restore before `build_analyst.py` runs
- ✅ B6 closed (not a bug): the +745 was a data-version artifact — `diagnose_pipeline.py` compared the parquet against the **stale** `input/` copy (636,333 rows) instead of the revised `raw data/` release (636,392 rows) the pipeline actually reads. Parquet is correct.

**Confirmed parquet state (session 10):**
- 636,392 rows | 13,722,286 total units | years 2564–2569
- Powertrain: ICE 12,699,523 | HEV 518,623 | BEV Major 435,830 | PHEV 29,127 | OTH 28,539 | N/A 5,512 | BEV 5,132
- 6 null fuel rows (6 units)
- Raw model file: 636,333 rows | 13,721,541 units — parquet is 59 rows and 745 units heavier

---

## Active Claims

| Agent | Status | Claimed Files | Task |
|---|---|---|---|
| — | — | — | Board is clear |

---

## Task Queue

### T1 — Restore master cal and run full pipeline

Owner: unassigned (operator action needed first)
Status: 🔴 Blocked on file restore
Priority: Critical

1. Operator restores `*(master cal).xlsx` to `backend/`.
2. Run from `backend/`: `python build_cleaned.py && python build_BEV.py && python build_analyst.py`
3. Verify analyst report produced with correct sheet order and pivot totals.

**Do not start T5 until this passes.**

### T2 — Fix B3: `build_BEV.py` overwrites real pivot sheets

Owner: unassigned
Status: ✅ Fixed session 9
Priority: —

### T3 — Fix B4: BEV detection logic

Owner: unassigned
Status: ✅ Fixed session 9
Priority: —

### T4 — Dead code cleanup in `build_analyst.py`

Owner: unassigned
Status: Ready
Priority: Medium

Remove the 8 functions in `build_analyst.py` that are never called by `main()`.
No behaviour change — pure cleanup before Phase 2 work begins.

File: `backend/build_analyst.py`

### T6 — ✅ CLOSED (B6 was not a bug)

Owner: Claude (session 11)
Status: Done — no code change needed
Resolution: 2026-06-23

**Resolution:** The +745-unit / +59-row "inflation" was a **diagnostic artifact, not a
pipeline bug.** `diagnose_pipeline.py` compared the parquet against the `input/` directory's
copy of the raw model file (24.8 MB, 636,333 rows). The pipeline actually reads from
`raw data/`, which holds a **revised DLT release** of the same file (25.29 MB, 636,392 rows).
DLT added 59 passenger-car records (745 units) to year 2569 / `รย.1` between those two
releases. The parquet correctly reflects the revised release.

**Hypothesis refuted:** `enrich_fuel_type` ([build_cleaned.py:137](backend/build_cleaned.py:137)–159)
uses a **scalar lookup** (groupby→sum→drop_duplicates→set_index→`.get()`), not a merge — it
cannot produce duplicate rows.

**Gates:** parquet vs revised raw Δ = 0 ✅ · golden fixture PASS (145 entries, labels correct) ✅.

**Follow-up (cleanup, low priority):** `diagnose_pipeline.py` points at the stale `input/`
copy — fix it to read `raw data/` (or delete the stale copy) so it can't mislead a future
session.

### T7 — B7: fuel-type shifts are structural, not a bug

Owner: unassigned
Status: Decision needed (not a defect)
Priority: Medium

**Finding (session 11):** B7 is **independent of B6** and is **expected behavior**, not a
join bug. `enrich_fuel_type` assigns each `(ปี/เดือน/ประเภทรถ/จังหวัด/ยี่ห้อรถ)` key its
**single highest-volume fuel type**, collapsing all model-file registrations for that key
onto one fuel bucket. That collapse is what produces the category shifts
(เบนซิน +161K, ดีเซล -124K, PHEV -36K).

**Open question (for next session):** is "assign each key its dominant fuel type" the correct
business rule, or should model rows retain their own fuel type? This is a **product decision**,
not a code fix — confirm with the operator before changing anything.

File: `backend/build_cleaned.py` ([enrich_fuel_type](backend/build_cleaned.py:137))

### T5 — Phase 2 Web UI (kickoff)

Owner: unassigned
Status: Blocked on T1 (real-data validation)
Priority: Medium

Start operator-facing web UI:
- File drop zone for two DLT files
- "Run Update" button
- Per-stage progress display
- Download link for finished analyst report

Stack: Next.js front end + Flask/FastAPI local API (`api.py`).
**Do not start until T1 full pipeline run passes.**

---

## Handoff Log

### 2026-06-22 — Claude (session 10)

**Status: Diagnosis run; two new bugs surfaced (B6, B7)**

Actions taken:
- Created `diagnose_pipeline.py` at project root — compares raw files vs parquet totals.
- Ran diagnosis; output saved below.

Findings:
- Raw fuel file and raw model file totals match exactly: **13,721,541 units** each.
- Parquet total is **13,722,286** — **+745 units vs raw** (B6). Gap is 100% in `รย.1`.
- Parquet has 59 more rows than raw model file (636,392 vs 636,333).
- Large fuel-type shifts raw→parquet (B7): เบนซิน +161K, ดีเซล -124K, PHEV -36K.
- OTH powertrain: 28,539 units — unclassified; will be dropped in any powertrain filter.
- 6 null fuel rows (6 units) in parquet.

Updated files: `ROADMAP.md`, `AGENT_BOARD.md`, `diagnose_pipeline.py` (new).

Next recommended action for Codex:
1. Fix T6 (B6) first — trace the +745 inflation in `backend/build_cleaned.py` join.
2. Then fix T7 (B7) — confirm fuel-type remapping is correct after T6 fix.
3. T1 (master cal restore) is operator-dependent; no code action possible until operator provides the file.
4. Do NOT touch `pipeline_state.json` BEV auto-approvals — flagged as wrong in Codex 2026-06-21 handoff.

### 2026-06-23 — Claude (session 11)

**Status: B6 closed (not a bug); B7 explained (structural, decision needed)**

- **B6:** the +745 units / +59 rows were a data-version artifact, not a pipeline defect.
  `diagnose_pipeline.py` compared the parquet against the stale `input/` copy of the raw
  model file (636,333 rows); the pipeline reads the revised `raw data/` release (636,392 rows),
  to which DLT added 59 รย.1 records (745 units) in year 2569. Parquet vs revised raw Δ = 0;
  golden fixture PASS. No code change. Refuted the duplicate-join hypothesis —
  `enrich_fuel_type` is a scalar lookup, not a merge.
- **B7:** independent of B6 and expected — `enrich_fuel_type` collapses each key onto its
  dominant fuel type. Whether that's the right business rule is an open product decision.
- **Cleanup flagged:** `diagnose_pipeline.py` reads the stale `input/` copy — point it at
  `raw data/` (or delete the stale copy) so it stops generating phantom bugs.
- **Next up:** template-independence track (brand_map → CSV is #1) — see ROADMAP.

---

### 2026-06-21 — Codex

**Status: Output/spec loop passed; final workbooks generated**

Final outputs:
- `output/test_15_masterModel.xlsx`
- `202606_รถใหม่_ยี่ห้อรถ-ชนิดเชื้อเพลิง-จังหวัด ปี 2564 - มิถุนายน 2569(test analyst).xlsx`

Changed files:
- `build_cleaned.py`
- `build_analyst.py`
- `refer/model2_map.csv`
- `plans/2026-06-21-codex-error-handoff.md`

Errors found/fixed:
- `build_cleaned.py` was rewriting `BEV Series Name Table`, shrinking it from 31,905 rows to 870 rows. Fixed by preserving the template sheet.
- `build_cleaned.py` added a non-spec `powertrain summary` sheet. Fixed by removing that output call.
- Master/analyst outputs did not force recalculation on open. Fixed with `calcMode="auto" fullCalcOnLoad="1" forceFullCalc="1"`.
- `build_analyst.py` wrote `Data` with the wrong worksheet namespace. Fixed to standard SpreadsheetML namespace.
- Analyst workbook preserved hard cached formula errors in `7.BEV by Model`. Fixed by clearing hard cached formula-error cells and removing stale `calcChain.xml`.
- First sanitizer attempt was too slow; replaced with a targeted cell sanitizer.
- Local LLM inspection hallucinated `_rewrite_bev_series_table` behavior; ignored and used direct source/validation.

Map updates:
- Updated `refer/model2_map.csv` with 17 missing raw model aliases from the latest run.
- Verified all 19 latest-run aliases are now present; duplicate raw-key count is 0.
- Did **not** update `BEV Series Name Table`/Powertrain classifications from auto-approval output.

Validation:
- Master non-Data sheets vs `output/master_model_baseline/`: 100.0%.
- Master `Data` row 7 headers match spec.
- Analyst `Data` row 6 headers match spec.
- `BEV Series Name Table` row counts match templates: master 31,905; analyst 31,926.
- Pivot caches refresh on open in both outputs.
- Full recalculation on open in both outputs.
- Final hard formula-error scan: none.

Be careful:
- `pipeline_state.json` contains likely-wrong auto-approved BEV Major rows (`BMW S 1000 RR`, `MG5 1.5 X`, `AUDI A5 ... TFSI`). Do not blindly append these to `BEV Series Name Table`.
- Wait for workbook writer processes to exit before opening/validating `.xlsx` files, or reads can hit transient `BadZipFile`.
- More detail is in `plans/2026-06-21-codex-error-handoff.md`.

---

### 2026-06-19 — Claude (session 8)

**Status: Partial run — analyst blocked**

Pipeline run:
- `build_cleaned.py` ✅ — 636,392 rows; incremental rolling rebuild (18 months rebuilt); `pipeline_state.json` written
- `build_BEV.py` ✅ — 0 approved BEV rows; clean exit
- `build_analyst.py` ❌ — `test_calculation.xlsx not found — run build_cleaned.py first`

Root cause: `*(master cal).xlsx` was deleted and not restored. `build_analyst.py` looks for this file in the project root (pattern `*(master cal).xlsx`) or `refer/*(calculation).xlsx` as fallback; neither exists.

Bugs confirmed fixed this session: B1 (incremental processing), B2 (`ชนิดเชื้อเพลิง` in Data sheet), `pipeline_state.json` writing.

Bugs still open: B3 (BEV by Model overwrite), B4 (BEV detection logic).

Next recommended action: Operator restores `*(master cal).xlsx` → run T1 full pipeline → then T2/T3 bug fixes.

---

### 2026-06-18 — Claude (T1 review, session 7)

Pipeline run with old script paths (`python .claude/scripts/run_pipeline.py --skip-map`) — exit 0.
Column gap noted: `1.Reg by Powertrain` output=33 cols vs template=34 cols.
Pre-existing dirty files noted. No blocking issues found.

---

### 2026-06-18 — Codex

Created this meeting board. Fixed calculation template preservation in `build_analyst.py` (copy template, refresh only Data). Updated skills.
