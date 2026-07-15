# ai-reading-car-analysis — Project Knowledge Library

Thai DLT car-registration data pipeline (Python backend + Next.js dashboard) that cleans raw
registration data, classifies brand/powertrain, and builds analyst/dashboard reports.

The permanent book of this project. Only write here when something is **confirmed done and understood**.

- **HANDOFF.md** = what we're working on right now, what's pending
- **LIBRARY.md** = what we've solved, what we've learned, what we've built

Three sections:
1. **Solved Problems (SP)** — confirmed bug fixes: symptom → root cause → fix → verify
2. **Lessons Learned (LL)** — process or workflow mistakes, never to repeat
3. **Architecture Decisions (AD)** — why things are built the way they are

Search by keyword, area, or date. Add entries at the bottom of each section.

---

# Part 1 — Solved Problems

*No entries yet. Add one when the first confirmed fix is in.*

---

# Part 2 — Lessons Learned

## LL-001 — Uncommitted refactor work is unrecoverable if another session runs `git checkout`

**Date:** 2026-07-06

**What happened:**
While working through `backend/plans/2026-07-06-architecture-fix-plan.md` (a 6-candidate
architecture refactor), candidate #3 (decomposing `build_cleaned.main()` into
`load_reference_maps`, `add_derived_columns`, `rolling_merge`, `resolve_bev_review_records`)
was completed but left uncommitted. A separate, concurrent agent session (Claude Code
orchestrator, Qwen, and a Gemini Antigravity session were all operating on the same working
directory `C:\dev\ai-reading-car-analysis` at once) ran `git checkout backend/build_cleaned.py`
to "clean up" a botched edit in a different task, not realizing it would silently discard
another session's unrelated in-flight work on the same file. The extraction was gone —
git had no object to recover from, since the changes were never `git add`ed, let alone
committed. It had to be redone from scratch.

**The rule:**
Commit immediately after each verified pure-refactor step passes its check (byte-diff, test,
whatever the verification gate is) — do not batch multiple candidates/steps into one long
uncommitted session. This matters more than usual on this repo because multiple AI tool
sessions run concurrently against the same working directory with no coordination between
them; any one of them can run a destructive git command (`checkout`, `reset --hard`, `stash`)
without knowing another session has uncommitted work riding on the same files. Bake "never
run git checkout/reset/stash to bail out of a bad edit — fix it by editing again" into every
executor prompt for this repo.

## LL-002 — A clean build is not a frontend performance gate

**Date:** 2026-07-14

**What happened:**
The public-release refactor passed lint, TypeScript, and the production build, but the resulting
dashboard still felt globally sluggish. Runtime measurement showed that the lightweight summary
path completed in roughly 9–12 ms, while loading and processing the full model hierarchy took
roughly 140–179 ms on the main thread. The new React tables could also render about 27,000 cells
at their default settings. Static correctness checks did not expose either cost.

**The rule:**
For frontend changes involving large datasets or table rewrites, the release gate must include
runtime measurements in addition to lint, type checking, and build success. Measure JSON parse and
selector time, initial rendered row/cell count, and shipped JavaScript size. Keep large datasets
lazy, paginate or virtualize large tables, and load export-only libraries only when the user
exports. Do not declare the performance issue fixed until the same measurements improve and the
totals/export behavior remains correct.

---

# Part 3 — Architecture Decisions

*No entries yet.*

---

*Add entries at the bottom of each section when something is confirmed done.*
