# Handoff: CSV-First Model Review Release

Date: 2026-07-22
Repository: `C:\dev\ai-reading-car-analysis`
Branch: `main`

## Current state

The source-grain migration is implemented and release-verified. The worktree is
intentionally dirty; no commit, push, stash, or reset was performed in this slice.

The governing data contract is:

- Model DLT data proves brand, raw model, period, geography, vehicle type, and count.
- Fuel DLT data proves fuel and Powertrain totals at fuel grain.
- `backend/config/model_map.csv` maps raw model names to canonical model names.
- `backend/config/model_powertrain_review.csv` is the human review file. New models are
  appended as `pending`; reviewed rows are never overwritten by the build.
- A model Powertrain is never written into `test_model_cleaned.parquet`.
- Approved BEV rows control Sheets 7-8 only. Fuel-derived Powertrain controls Sheets
  1-6 and 9 and Analyst Brand views.

## What changed

- Migrated dashboard model export from the removed `Powertrain` column to the explicit
  model display field `PT=N/A`.
- Migrated public release gates from `series_registry.csv` to source-grain validation
  plus approved BEV keys from `model_powertrain_review.csv`.
- Added canonical approved-model validation for Sheets 7-8.
- Migrated Analyst output: Model views expose only `ALL`; Brand views retain
  `ALL/ICE/BEV/HEV/PHEV`. The UI resets and disables Powertrain when Model is selected.
- Added a hard failure when code attempts a Powertrain filter on data without a
  Powertrain column.
- Updated stale direct-run regression checks and pipeline/runbook documentation.
- Added the missing `HONDA / WAVE 125i -> WAVE 125i` canonical alias.

## Verified output

- Backend pytest: `46 passed` locally, including the real-data reconciliation test.
- Fresh-clone CI command: `45 passed, 1 deselected`; only the test requiring unpublished
  raw DLT workbooks is deselected.
- Focused release tests: `19 passed`.
- Direct regression runners passed:
  - `test_admin_to_cleaned_integration.py`
  - `test_build_analyst_sheet1_source.py`
  - `test_canonicalization.py`
  - `test_series_powertrain_regression.py`
  - `test_source_grain_separation.py`
  - `check_sheet1_golden.py`
- `BUILD_RELEASE.bat`: all nine steps passed, including Markdown parity, public release
  validation, lint, TypeScript, and the Next.js production build.
- Source totals reconcile: model and fuel both equal `13,966,182` units.
- Sheets 7-8 contain 41 and 28 rows respectively.
- Public validator observed 8,654 model nodes and 54 report row occurrences backed by
  approved BEV review entries.
- `analyst_data.json` model keys are only `ALL`; brand keys are
  `ALL/ICE/BEV/HEV/PHEV`.

## Monthly operator flow

1. Replace the monthly raw DLT files.
2. Close Excel or any editor holding `model_powertrain_review.csv` open.
3. Run `BUILD_RELEASE.bat`.
4. Open `backend/config/model_powertrain_review.csv` and review newly appended
   `pending` rows. Fill `candidate_powertrain`, `evidence`, `reviewer`, `reviewed_at`,
   and set `review_status=approved` only after checking evidence.
5. Run `BUILD_RELEASE.bat` again so Sheets 7-8 reflect newly approved BEV rows.

Detailed CSV instructions are in `handoffs/bev-whitelist-runbook-2026-07-22.md`.

## Remaining handoff actions

1. Audit the 112 initial AI-seeded BEV approvals and replace generic evidence where possible.
2. Commit the intended migration files and required generated public JSON together.
3. Push; CI and GitHub Pages deployment are configured in `.github/workflows/`.
4. Change GitHub Pages Source from the legacy `gh-pages` branch to **GitHub Actions**.
5. Smoke-test `/`, `/models`, `/analyst`, `/report`, and `/data/`.

## Cautions

- Never infer a model Powertrain from brand fuel totals, dominant fuel, or statistical
  matching.
- Never auto-approve newly observed models.
- Do not add `Powertrain` or `include_in_bev_model_report` back to model parquet.
- The legacy `series_registry` admin utilities were removed. Maintainers should use the
  two config CSVs documented above.
