# Handoff: Market-Scope Safety and Next Month-Comparison Slice

Date: 2026-07-24
Repository: `C:\dev\ai-reading-car-analysis`
Branch: `main`
Remote: `https://github.com/fietao/toyota_analysis_car.git`

## Current outcome

The Manual Report layouts for Sheets 7-9 were previously implemented, tested, committed, and pushed in commit `41043be`.

Market-scope safety is now committed and pushed to `origin/main` in commit `0de7ede` (`Add market scope safety controls`).

The dashboard research phase is complete. The full external research report is at:

`C:\Users\georg\Downloads\vehicle_registration_dashboard_research_report.md`

Its accepted product direction is a quiet, high-density analyst workstation with:

- an executive overview that answers what changed, why, and where;
- dense analyst tables and drill-downs retained;
- formal Sheets 1-9 and governed exports retained;
- confusing cards, arbitrary chart colors, ambiguous periods, and hidden denominators removed over incremental slices.

## Market-Scope Safety: implemented, committed, and pushed

Files in scope:

- `frontend/src/app/marketProfiles.ts` (new)
- `frontend/src/app/marketProfiles.test.ts` (new)
- `frontend/src/app/page.tsx` (modified)

Implemented behavior:

- Homepage defaults to latest year and the Formal report vehicle scope:
  `รย.1, รย.2, รย.3, รย.6, รย.9, รย.10, รย.11`.
- The sidebar has a compact Market Profile control:
  - Formal report
  - All DLT
- The sticky header persistently shows:
  - selected year;
  - profile name;
  - selected vehicle-type count;
  - dynamic reporting period.
- Manually changing vehicle types identifies the scope as Custom selection.
- The vehicle popover's legacy empty-array "All" action is converted to all available codes before state is updated, preventing a header/denominator mismatch.
- Dashboard initialization verifies all seven formal-report codes exist. Missing codes produce a blocking data-contract error instead of activating a partial scope.

Reconciliation evidence:

- Formal report scope: `374,424` current YTD units.
- This exactly matches `manual_report.json`, Sheet 2 `curr_ytd`.
- All DLT scope: `1,349,088` units and motorcycle-heavy rankings.
- Formal scope: Toyota is the top brand.
- All DLT: Honda is the top brand.

Verification reported and reviewed:

- `npm test`: 45/45 passing.
- `npm run lint`: clean.
- `npm run build`: succeeds.
- `git diff --check`: clean.
- Python 3.12 public-release validator: passed.
- Independent mobile check at `390x844`: the new selector and scope bar fit and wrap; no page-level horizontal overflow.

## Git and workspace caution

The market-scope safety slice was committed in `0de7ede`. Future commits should keep this completed slice separate from unrelated workspace changes.

Do not accidentally stage unrelated existing workspace changes:

- `.route-logs/`

Read and follow repository `CLAUDE.md`. Do not revert user changes.

## Next implementation slice

Build a compact period-comparison experience without redesigning the entire dashboard yet.

Desired comparisons for a selected month:

- selected month versus previous month;
- selected month versus the same month in the prior year;
- current YTD through the selected month versus equivalent prior-year YTD;
- prior full year only as clearly labeled context;
- optional rolling three-month trend if existing data supports it cleanly.

The same selected period and comparison semantics should update market, powertrain, brand, model, and province analysis where the source grain supports them.

First-screen intent:

1. What changed?
2. Why did it change?
3. Where should the analyst investigate?

Preserve:

- dynamic period detection and Buddhist years;
- existing filters and market profiles;
- current selector/data-integrity logic;
- expandable tables, Analyst view, Manual Reports, and exports;
- English UI chrome and Thai raw/source values;
- the established DLT Terminal design tokens.

Remove or defer:

- no broad framework migration;
- no TanStack Table or ECharts adoption in the next small slice unless repository evidence proves it necessary;
- no forecasting;
- no map;
- no model powertrain inference beyond approved mappings;
- do not alter Sheets 1-9 in this slice.

## Important constraints

- Never run `MONTHLY_UPDATE.bat` without explicit user approval.
- Do not hardcode June, January-June, 2568, 2569, or any current period.
- Compare current YTD only with the equivalent prior-year YTD period.
- Do not visually present prior full-year totals as an equivalent comparison to current YTD.
- Do not regenerate datasets unless explicitly authorized.
- UI work requires tests, lint, build, live desktop/mobile checks, and screenshot evidence.

## Open business decision

Do not add "our company" highlighting yet. The repository contains conflicting identity signals:

- `backend/export_dashboard.py` has `TARGET_BRAND = "Deepal + Changan"`;
- repository naming/history references Toyota.

The user must confirm the intended company brand or configurable brand set before company-specific KPIs, highlighting, or province opportunity scoring are implemented.

## Suggested skills

- `implement`: execute the next approved period-comparison slice.
- `impeccable`: preserve the product design system and refine the comparison UI.
- `review`: review the resulting diff and verify acceptance criteria.
- `agent-browser` or `browser:control-in-app-browser`: live desktop/mobile QA and screenshots.
- `handoff`: compact the next completed slice for another session.
