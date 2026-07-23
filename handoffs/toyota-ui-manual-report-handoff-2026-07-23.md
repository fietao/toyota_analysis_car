# Handoff: Toyota UI and Manual Report Slices

Date: 2026-07-23
Repository: `C:\dev\ai-reading-car-analysis`
Branch: `main`

## Current state

Slices 1-3 are implemented and locally verified. The worktree is intentionally dirty and
nothing has been committed, pushed, deployed, stashed, reset, or cleaned.

The next work should be **Slice 4: Historical Manual Report Years**.

## Read first

- `CLAUDE.md`
- `README.md`
- `handoffs/public-release-handoff-2026-07-21.md`
- `handoffs/bev-whitelist-runbook-2026-07-22.md`
- This file

## Non-negotiable data contract

- Model-grain output never carries `Powertrain` or fuel type.
- Fuel grain owns Powertrain.
- `backend/config/model_map.csv` owns canonical model names.
- `backend/config/model_powertrain_review.csv` owns reviewed model classifications.
- Sheets 7-8 include only keys returned by `model_map.approved_bev_keys()`.
- Do not infer model Powertrain from aggregate fuel totals, dominant fuel, or model names.
- Do not auto-approve pending model review rows.

## Completed slices

### Slice 1 - Deep-Dive Models UI

Changed files:

- `frontend/src/app/models/page.tsx`
- `frontend/src/app/selectors.ts`
- `frontend/src/app/selectors.deepdive.test.ts`
- `frontend/src/app/globals.css`

Behavior:

- Brand selection now narrows Model filter options to models owned by selected Brand(s).
- Changing Brand prunes stale selected Models that no longer belong to the Brand selection.
- Fuel Type remains removed from the Deep-Dive page.
- `.custom-scrollbar` now has dark app-matching styling.
- The Deep-Dive layout was tightened after visual QA:
  - compact header/filter band
  - full-width page shell
  - contained table overflow
  - stable month/YTD/Grand Total column widths

Evidence:

- `npm test` passed.
- `npm run lint` passed.
- `npm run build` passed.
- Browser QA showed `TOYOTA` Model options exactly matched Toyota's source model set.
- Latest visual snapshot: `frontend/.impeccable/models-layout-fix.png`.

### Slice 2 - Analyst Model Filter

Changed files:

- `frontend/src/app/analyst/page.tsx`
- `frontend/src/app/analystFilters.ts`
- `frontend/src/app/analystFilters.test.ts`

Behavior:

- Analyst has a Model filter.
- In Model view, Brand narrows available Model options.
- Changing Brand clears incompatible selected Model.
- Model filter only applies in Model view.
- Model view locks Powertrain to `ALL`.
- Analyst no longer loads `dashboard_models.json` for Excel export.
- Removed the old `Models Full Matrix` export that depended on `dashboard_models.json`.

Explicitly deferred:

- Province and Year filters for Analyst were not added. They require a backend/data-shape
  slice and should not be forced into the current frontend-only Analyst payload.

Evidence:

- Browser QA reported: BYD shows only BYD models, selecting `BYD ATTO 3` narrows rows to
  Grand Total plus that model, and switching to TESLA clears the BYD model automatically.

### Slice 3 - Manual Report Excel Export

Changed files:

- `frontend/src/app/report/page.tsx`
- `frontend/src/app/reportExport.ts`
- `frontend/src/app/reportExport.test.ts`

Behavior:

- `/report` now has an `Export this sheet (.xlsx)` button.
- Export downloads only the currently selected report tab/sheet, not the full 9-sheet workbook.
- Export respects the current active search filter because it uses the table's current `rows`.
- File names include the active sheet title and reporting period, e.g.
  `manual-report-7-BEV-by-Model-June-2569.xlsx`.
- Worksheet names are sanitized for Excel.
- Current-year export columns stop at `latest_month_num`; future month zeroes are not fabricated.
- Model-grain sheets do not expose Powertrain or fuel columns.

Evidence:

- Tests cover blank/null/zero export behavior, current-month column bounds, rank columns,
  model-grain no-Powertrain/no-fuel columns, safe sheet names, filenames, and all 9 sheet defs.

## Latest verification

After the final Models layout fix:

- Frontend tests: `23 passed`
- `npm run lint`: passed
- `npm run build`: passed

Known warnings:

- Node test emits `MODULE_TYPELESS_PACKAGE_JSON` warnings because tests import TypeScript
  ESM files without `"type": "module"` in `frontend/package.json`. This is pre-existing
  test-runtime noise and not a test failure.

## Current dirty files

Expected dirty files from slices 1-3:

- `frontend/src/app/analyst/page.tsx`
- `frontend/src/app/analystFilters.ts`
- `frontend/src/app/analystFilters.test.ts`
- `frontend/src/app/globals.css`
- `frontend/src/app/models/page.tsx`
- `frontend/src/app/report/page.tsx`
- `frontend/src/app/reportExport.ts`
- `frontend/src/app/reportExport.test.ts`
- `frontend/src/app/selectors.deepdive.test.ts`
- `frontend/src/app/selectors.ts`

Do not revert unrelated dirty work.

## Next slice - Slice 4

Goal: add historical Manual Report year choices:

- `2569`
- `2568`
- `2567`
- `2566`
- `2565`
- `2564`

Risk: medium. This likely requires backend export changes because
`frontend/public/data/manual_report.json` currently carries only the latest report period
(`2569` versus `2568`). Do not fake this in the frontend.

Requirements:

- Manual Report must let the user choose historical report years.
- `2564` comparison values must be `N/A` because no `2563` data exists.
- Do not fabricate missing prior-year values as zero.
- Keep all model Powertrain rules intact.
- Preserve the Slice 3 single-sheet Excel export for whatever report year/sheet is active.

Likely files:

- `backend/export_manual_report.py`
- backend tests around manual report export, if present
- `frontend/public/data/manual_report.json` generated output
- `frontend/src/app/report/page.tsx`
- `frontend/src/app/reportExport.ts`
- `frontend/src/app/reportExport.test.ts`

Suggested implementation shape:

1. Inspect current `manual_report.json` and `backend/export_manual_report.py`.
2. Decide a backward-compatible JSON shape for multiple report years.
3. Generate per-year report payloads for 2564-2569.
4. Ensure 2564 prior-year comparison fields are null/`N/A`, not zero.
5. Add a year selector in `/report`.
6. Keep the active sheet export scoped to the selected year and selected sheet.
7. Run backend focused tests/export checks, then frontend tests/lint/build.
8. Browser QA `/report` for year switching and Excel export.

## Suggested skills

- `orchestrator` for slice planning, risk gates, and executor prompts.
- `pipeline-rebuild` if backend report generation or full release export must be rerun.
- `impeccable` for `/report` UI changes or visual QA.
- `handoff` when stopping before commit/push/deploy.

No new skill was created in this handoff. Existing repository skills are sufficient for the
remaining Slice 4 work.

## Stop conditions

- Stop before commit, push, deploy, or GitHub Pages changes unless the owner explicitly asks.
- Stop and ask if the backend data cannot produce a historical year without changing the
  source-grain contract.
- Stop and ask before any destructive git or filesystem operation.
