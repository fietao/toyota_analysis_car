# Architecture Fix Plan — All 6 Candidates

**Date:** 2026-07-06
**Source:** architecture-review-20260630-175818.html (6 candidates)
**Verified against live code** 2026-07-06 (line numbers current).

---

## Golden rule for every candidate

There are **no tests in this repo**. So the safety net for the "pure refactor" candidates
(#2, #3, #4, #6) is a **byte-diff of the pipeline output**:

```powershell
# BEFORE any change — capture baseline
$env:PYTHONUTF8=1; py -3.12 backend\run_pipeline.py --skip-map --skip-analyst
py -3.12 backend\export_dashboard.py
Copy-Item frontend\public\data\dashboard_data.json  $env:TEMP\dash_before.json
Copy-Item frontend\public\data\analyst_data.json    $env:TEMP\analyst_before.json

# AFTER the change — re-run and diff
$env:PYTHONUTF8=1; py -3.12 backend\run_pipeline.py --skip-map --skip-analyst
py -3.12 backend\export_dashboard.py
fc.exe $env:TEMP\dash_before.json frontend\public\data\dashboard_data.json
```

- **Pure refactors (#2, #3, #4, #6): the diff must be EMPTY.** Any change = a bug.
- **#1 (classification): the diff is EXPECTED** — only the Deepal brand string and any
  OTH↔N/A reconciliation should move. Review the diff line-by-line; nothing else should change.

---

## Dependency order (do NOT reorder)

```
1. #1  Unify classification      ← highest value, fixes the live Deepal drift bug
2. #6  schema.py validate gate   ← cheap insurance, independent
3. #4  xlsx_util extraction      ← mechanical, unblocks nobody but cheap
4. #2  aggregate() selector      ← after #1 (shares the classified column)
5. #3  decompose build_cleaned   ← MUST come after #1 (review: #1 is its precondition)
6. #5  selectors.ts (frontend)   ← after #1 (removes the re-alias)
```

Run each fix, diff, commit, THEN start the next. Never batch two structural changes into one
unverified commit.

---

## FINDING 2026-07-06 — Candidate #1 was PARTLY WRONG (empirically disproven)

The review said "export_dashboard re-derives Powertrain from raw fuel; read the stored
`Powertrain` column instead, it's authoritative." **This is false at the model level.**

There are TWO parquets with DIFFERENT `Powertrain` semantics:
- `test_fuel_cleaned.parquet`: `Powertrain` set from `ชนิดเชื้อเพลิง` (build_cleaned.py:954).
  Agrees with FUEL_MAP. Safe to read.
- `test_model_cleaned.parquet`: `Powertrain` set by the BEV-series-name override
  (known BEV model → "BEV Major", else "OTH"). It is **BEV-series membership, NOT a fuel
  powertrain classifier.** Reading it collapsed all BEV models not in the series table to N/A.

Proof: switching to the stored column moved BEV 469,338 → 5,126 units in `model_monthly_all`
(e.g. AION, an all-EV brand, went BEV 28,683 → N/A). AION's `ชนิดเชื้อเพลิง` is `ไฟฟ้า`, so
FUEL_MAP → BEV is correct; the stored `OTH` is wrong for powertrain.

**Resolution:** KEEP the brand-string canonicalization (brand_map.csv + TARGET_BRAND +
remove frontend normalizeBrandName → all "Deepal + Changan"). REVERT the Powertrain
column-read; keep `FUEL_MAP` on `ชนิดเชื้อเพลิง` in load_data. The two "Powertrain"
concepts are distinct facts sharing a name — this is NOT the duplication the review claimed,
so #1 shrinks to just the brand-string fix. Do not attempt to "unify" the model-parquet
Powertrain column before the pitch.

---

## STATUS 2026-07-06 (verified against uncommitted working tree)

| # | Candidate | Status | Evidence |
|---|---|---|---|
| 1 | Unify classification (brand string only, per finding above) | **DONE** | `brand_map.csv` emits `Deepal + Changan`; `normalizeBrandName` removed from `page.tsx` (zero hits repo-wide) |
| 2 | Collapse aggregation into `aggregate()` | **DONE** | `backend/aggregate.py` (152 lines) wired into `build_analyst.py`, `calculation_builder.py`, `export_dashboard.py` (6 call sites) |
| 3 | Decompose `build_cleaned.main()` | **DONE** | Redone after an earlier `git checkout` accident wiped the first uncommitted attempt (see incident note below). `main()` is now 81 lines calling `find_master_model_file`, `load_existing_parquet`, `load_reference_maps`, `add_derived_columns`, `rolling_merge`, `resolve_bev_review_records`, `write_pipeline_state`, `update_known_models`. Verified byte-identical `dashboard_data.json` after a fresh pipeline run. Committed at `79db94e`. |

**Incident (2026-07-06):** an accidental `git checkout backend/build_cleaned.py` destroyed an uncommitted first attempt at this decomposition before it was committed — unrecoverable, since it was never staged. Redone from scratch. **Lesson: commit each candidate immediately after its byte-diff passes — do not start the next prompt on top of uncommitted work.**
| 4 | Seal the pivot-surgery leak | **PARTIAL** | `_col`/`_esc` extracted to `backend/xlsx_util.py` (the cheap win) — but `_patch_pivot_table_def1`/`_patch_pivot_table_def2` in `build_cleaned.py:379-435` still hardcode field position `8`, count `"11"`, id `"9"` instead of deriving from `FINAL_COLS` |
| 5 | Extract dashboard selector seam | **DONE** | `frontend/src/app/selectors.ts` (430 lines) wired into `page.tsx` |
| 6 | Name the cleaned-data schema | **DONE** | `backend/schema.py` (`COLS` + `validate(df)`) is called at all four stage entries: `build_cleaned.py` (both parquet saves), `build_analyst.py`, `export_dashboard.py`, `export_analyst.py` |

**Remaining work:** finish #3 (thin `main()`), finish #4 (derive field indices from `FINAL_COLS`), finish #6 (call `validate()` at every stage entry, including `build_cleaned.py` and `export_analyst.py`).
