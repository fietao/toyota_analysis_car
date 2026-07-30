# Local Capture: Next AI Handoff

Date: 2026-07-28
Repo: `C:\dev\ai-reading-car-analysis`
Branch: `main`

## Current State

The manual report comparison UX is already implemented, verified, committed, and pushed.
After that, a zero-tech Thai takeover package was prepared but is still uncommitted.

Important local changes:

- `TAKEOVER.bat` - root menu for non-technical handoff setup.
- `handoffs/release-summary-and-takeover-2026-07-24.md` - Thai takeover note.
- `handoffs/thai-takeover-training-2026-07-24.pptx` - Thai PowerPoint training deck.
- `README.md` - documents `TAKEOVER.bat`.
- `.gitignore` - ignores `.tmp/` build/QA scratch output.

Known local output:

- `.route-logs/` is untracked local execution output. Do not stage it.
- `.tmp/` is ignored scratch output from generating and QA-checking the PowerPoint.

## Important Concepts

- The recipient has zero technical stack. Handoff materials must be Thai-first, click-by-click,
  and avoid Git/terminal/code language where possible.
- `TAKEOVER.bat` is for setup, opening the dashboard, checks, and opening notes. It must not run
  `MONTHLY_UPDATE.bat`.
- `MONTHLY_UPDATE.bat` is the monthly data refresh. Do not run it unless the user explicitly wants
  data regeneration.
- The dashboard UI chrome stays English. Thai belongs only in operator docs and raw data values
  where there is no English form.
- Dates/months/years/YTD ranges must stay dynamic. Do not hardcode current periods.
- For model review, the only maintainer-editable file is
  `backend\config\model_powertrain_review.csv`. Use `BEV`, not `EV`; approved rows need evidence,
  reviewer, and date.

## Verification Already Done

- Thai PPTX generated successfully.
- PPTX render/overflow test passed: no slide overflow detected.
- Visual contact sheet was inspected.
- `git diff --check` passed with only LF/CRLF warnings.
- `MONTHLY_UPDATE.bat` was not run.

## What The Next AI Should Do

1. Read `CLAUDE.md`.
2. Run `git status --short --branch` and confirm only expected handoff changes are present.
3. Review the Thai note and PPTX at a high level for obvious wording or packaging issues.
4. If the user wants this finalized, stage only:
   - `.gitignore`
   - `README.md`
   - `TAKEOVER.bat`
   - `handoffs/release-summary-and-takeover-2026-07-24.md`
   - `handoffs/thai-takeover-training-2026-07-24.pptx`
   - `handoffs/local-capture-next-ai-2026-07-28.md`
5. Do not stage `.route-logs/`.
6. Commit with a message like `Add Thai takeover handoff package`.
7. Push to `origin/main` only if the user asks for push/finalization.

## Suggested Skills

- `handoff` for updating this local capture.
- `presentations:Presentations` or `academic-pptx` if the Thai deck needs edits.
- `review` for a read-only check before committing.
- `orchestrator` if the user asks what remaining release work should happen next.
