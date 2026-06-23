# Handoff — Car Analysis Pipeline & Frontend

_Written 2026-06-23, grounded in the actual working tree (not memory)._

## TL;DR for the next agent

The repo has been **substantially restructured** and **none of it is committed yet**.
`git log -- backend frontend` returns nothing — the entire backend/ + frontend/ rework
lives only in the working tree. **Read this before you touch anything; then decide what to
commit.**

## Repo state (verified)

- **Scripts moved** `.claude/scripts/` → `backend/`. The old paths show as deleted in
  `git status`; the new `backend/*.py` files are untracked.
- **Frontend replaced.** Old `dashboard/` (Next.js) is being deleted; new app is `frontend/`
  (Next.js + impeccable styling). Pages: `frontend/public/analyst.html`,
  `frontend/public/models.html`; app shell in `frontend/src/app/` with `UploadModal.tsx`
  and `api/upload/route.ts`.
- Large uncommitted surface overall — many docs (README, ROADMAP, AGENTS, CLAUDE), skills,
  and root scratch files are also modified/added.

## What landed — Bug fix: hardcoded mappings → CSV

- `backend/config/brand_map.csv` (20 rows, `brand,brand2`) now holds the brand-grouping
  mappings: GAC→AION, the GWM family (GWM/GWM TANK/HAVAL/ORA), Deepal+ChangAn,
  the Mercedes-Benz family, ZX Auto, etc.
- **Wired, not stray:** `backend/build_cleaned.py:905` loads it; `add_brand2`
  (`build_cleaned.py:106`) applies `upper.map(brand_map)` with a fallback to the original
  brand. A companion `backend/config/powertrain_map.csv` sits beside it.

## What landed — analyst.html table scrolling

In `frontend/public/analyst.html`:
- Scroll container: `overflow-x-auto overflow-y-auto max-h-[75vh]` (line ~88).
- Sticky header row: `sticky top-0 z-30` (line ~90).
- Sticky first column ("Brand" / "Brand / Model" / "Identity"): `sticky left-0` with a
  right-edge shadow `shadow-[4px_0_10px_rgba(0,0,0,0.2)]` (lines ~197, 238, 244).
- Custom thin scrollbar via `.custom-scrollbar` (lines 13–16).

## Not verified in this session (next agent should confirm)

- Pipeline was **not run** — I did not execute `backend/run_pipeline.py` or confirm outputs.
- `models.html` scroll behavior was not inspected (only `analyst.html`).
- Whether the dashboard/ deletion is intended to be committed as-is.

## Suggested next steps

1. **Decide the commit story.** The working tree mixes a backend move, a frontend rewrite,
   and doc churn. Stage these as separate, coherent commits rather than one blob.
2. Run `backend/run_pipeline.py` end-to-end and confirm `frontend/public/data/` is populated.
3. Spot-check the brand grouping in the generated output matches `brand_map.csv`.
