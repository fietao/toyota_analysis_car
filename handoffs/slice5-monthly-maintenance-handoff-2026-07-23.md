# Handoff: Slice 5 — Non-Coder Monthly Maintenance Hardening

Date: 2026-07-23
Repository: `C:\dev\ai-reading-car-analysis`
Branch: `main`

Nothing committed, pushed, deployed, stashed, reset, or cleaned. Worktree intentionally dirty.

## What this slice delivers

A safe, double-click monthly update for a Thai non-coding operator. They drop the 2 DLT
files into `backend/raw data/`, double-click `MONTHLY_UPDATE.bat`, read Thai messages, and
(if needed) edit only `backend/config/model_powertrain_review.csv` before running again.

## New / changed files

| File | Change |
|---|---|
| `MONTHLY_UPDATE.bat` | New. Thin wrapper → `py -3.12 backend/monthly_update.py`; `pause`. ASCII only (Thai lives in Python to dodge codepage issues). |
| `backend/monthly_update.py` | New. Orchestrator: input-file + lock check, CSV preflight, runs `update_raw_data.py` then `export_manual_report.py`, writes summary, timestamped `logs/` file. Subprocess output → log only; curated Thai → console. |
| `backend/operator_preflight.py` | New. **Stdlib-only** validator for `model_powertrain_review.csv`. Collects *all* errors (file/row/column/fix) in Thai. Rows numbered to match Excel row numbers. |
| `backend/tests/test_operator_preflight.py` | New. Stdlib, no-pytest convention. Covers headers, dup keys, bad status/candidate, approved-missing-fields, blank required, multi-error, count, BOM tolerance, and a drift guard vs `model_map`. |
| `backend/model_map.py` | **Changed (beyond literal task — see coupling below).** The 3 read paths for the operator-edited config CSVs now use `encoding='utf-8-sig'` to tolerate Excel's "CSV UTF-8" BOM. Writes stay plain `utf-8`, so the BOM self-heals on the next build. |
| `docs/OPERATOR_GUIDE.md` | New. Thai/English operator guide. |
| `README.md` | Added `MONTHLY_UPDATE.bat` row to the operations table. |
| `.gitignore` | Ignore `logs/` and `reports/` (per-run artifacts). |

## Requirement coverage

1. Guided script — `MONTHLY_UPDATE.bat` + `monthly_update.py`. ✓
2. CSV preflight — `operator_preflight.py` (exact headers, dup normalized keys, valid
   status/candidate, approved-row required fields; pending allowed). ✓
3. Operator summary — `reports/monthly_operator_summary.txt` (period, row counts, pending
   count, approved-BEV **model** count, JSON-regenerated checklist, Thai next-action). ✓
4. Safe default for pending — **confirmed in code**: `export_manual_report.bev_model_report_slice`
   includes only `approved_bev_keys()` (approved+BEV); pending/blank rows are filtered out and
   `load_model_powertrain_review` permits them → pending never fails the build. ✓
5. Documentation — `docs/OPERATOR_GUIDE.md`. ✓

## ⚠️ model_map coupling — read before touching either file

`operator_preflight` and `model_map` **must move together on encoding**. Both now read the
review/model CSVs as `utf-8-sig`. If someone reverts the `model_map` change but leaves
preflight tolerant, preflight would give a false OK on a BOM file the build then rejects.
Keeping both (current state) is the correct choice for a non-coder-edits-in-Excel slice and
is near-zero risk (utf-8-sig is a strict superset for reading plain utf-8). The
`OPERATOR_GUIDE.md` "CSV UTF-8 handled automatically" line depends on this pair staying in sync.

The preflight contract constants are hand-mirrored from `model_map` (kept pandas-free on
purpose); `test_operator_preflight.test_contract_matches_model_map` drift-guards them (runs in
CI where pandas is present; skips locally without it).

## Verification (this environment: no `py` launcher, no pandas)

- `python backend/tests/test_operator_preflight.py` → **PASS** (drift guard auto-skipped, no pandas).
- `python backend/operator_preflight.py` on the live CSV → **OK, exit 0** (8598 pending).
- Preflight on a malformed fixture → **exit 1** with Thai file/row/column/fix messages.
- `monthly_update.write_summary(0)` run against the committed `cleaned_data_manifest.json` →
  produced a correct Thai summary (numbers formatted, `?` BEV-count fallback graceful since
  pandas absent; real env shows the model-grain count).
- `py_compile` clean on all new/changed `.py`.

**Not run locally** (no pandas / `py` launcher here): the full pipeline, the `.bat` end-to-end,
`update_raw_data.py`, `export_manual_report.py`, and the pandas-dependent backend tests
(`test_model_map.py`, `test_model_powertrain_review.py`) that exercise the `model_map`
encoding change. Those rely on CI / an operator-env run. The orchestrator and `.bat` were
verified by compile + path inspection only, not executed end to end.

## Update — no-collapse hardening (same date)

The first draft published in-place; a mid-build failure could half-update the served JSON.
Hardened to the required flow: **build → staging → validate → atomic per-file publish → rollback.**

Changed since the draft above:
- `export_dashboard.py`, `export_analyst.py`, `export_manual_report.py`, `validate_public_release.py`:
  output dir now honors `PUBLIC_DATA_DIR` (unset = live dir, so normal runs are unchanged).
- `backend/monthly_update.py`: builds into `frontend/public/data.staging`, runs
  `validate_public_release.py` as a gate, then `safe_publish()` swaps the 5 JSON per-file
  (`os.replace`, same volume) with backup+rollback. Three verbatim result lines
  (`สำเร็จ:` / `ต้องตรวจเพิ่ม:` / `ไม่สำเร็จ:`); summary now carries the result line + smoke-test checklist.
- `backend/tests/test_operator_safe_publish.py`: new, stdlib-only — proves success, rollback-on-failure,
  staging-does-not-touch-public, and first-run.
- `MONTHLY_UPDATE.bat`: added a `py -3.12` prerequisite check with Thai guidance.
- `docs/OPERATOR_GUIDE.md` → renamed `docs/THAI_OPERATOR_MONTHLY_GUIDE.md` (spec name), folded in
  the accepted/rejected CSV examples, "close Excel first," and the three result lines. README pointer updated.
- New optional openers: `OPEN_OPERATOR_SUMMARY.bat`, `OPEN_MODEL_REVIEW_CSV.bat`.
- `.gitignore`: ignore `data.staging/` and `data.bak/`.

Verification status: **integration-verified on real Python 3.12 (pandas 3.0.1)** — 2026-07-23.
- Happy path: real `monthly_update.py` end-to-end → build to `data.staging`, validate on staging,
  safe-publish → all 5 live JSON updated, staging/bak cleaned, result `ต้องตรวจเพิ่ม` (8598 pending,
  30 approved BEV models, period June 2569). Config CSVs byte-identical (no side effects).
- No-collapse F1: real `validate_public_release.py` with `PUBLIC_DATA_DIR`→corrupted staging exits 1;
  live JSON fingerprint unchanged.
- No-collapse F2: real orchestrator with a forced-failing validate stub → never reached publish,
  emitted `ไม่สำเร็จ: …`, live JSON byte-identical, staging/bak cleaned. (Stub reverted; validator hash restored.)
- Rollback (publish-stage): `test_operator_safe_publish.py` (restore-from-backup) PASS.
- Backend contract tests PASS on 3.12: `test_model_map`, `test_model_powertrain_review`,
  `test_operator_preflight` (drift guard now runs), `test_operator_safe_publish`.
- Frontend: `npm test` 28/28, `npm run lint` clean, `npm run build` OK (5 routes prerendered).
- Final live validate (no override): PASSED — source grains, BEV rows, periods release-safe.

Ceilings left deliberately (see `ponytail:` comments): a hard process-kill between the 5 `os.replace`
calls has no auto-restore (inherent to any non-journaled swap); `safe_publish`'s `except OSError`
covers the realistic locked-file case.

`.bat` launcher hardened after a real-env finding: this machine has **no `py` launcher** and `python`
resolves to a 3.11 venv, so `MONTHLY_UPDATE.bat` now tries `py -3.12` then falls back to
`%LOCALAPPDATA%\Programs\Python\Python312\python.exe`, else a Thai "install Python 3.12" message.

## Next steps for the maintainer

1. Run `BUILD_RELEASE.bat` (or `MONTHLY_UPDATE.bat`) once in the real `py -3.12` env to
   exercise the pandas paths and confirm the summary's real BEV-model count.
2. Confirm `test_model_map.py` / `test_model_powertrain_review.py` still pass with the
   `utf-8-sig` change (expected: yes).
3. Commit when satisfied. Stop conditions (no push/deploy/contract change) were honored.
