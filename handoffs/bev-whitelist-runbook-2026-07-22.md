# Runbook: Model Powertrain Review CSV (Sheets 7-8)

Date: 2026-07-22 (updated 2026-07-22, same day: BEV-only whitelist replaced by a
broader powertrain review workflow)

## What controls Sheets 7-8

Sheets 7-8 ("7.BEV by Model" and "8.Model Top Rank" in `manual_report.json`) show only
model rows whose `(Brand2, raw model)` pair is explicitly reviewed and approved as BEV
in **`backend/config/model_powertrain_review.csv`**. This file replaces the earlier
`bev_whitelist.csv` — same idea (a maintainer-edited CSV, nothing inferred from brand
fuel totals or model-name guessing), but broadened to track a candidate powertrain and
review status for every model the pipeline has ever seen, not just BEV candidates.

**The DLT model source does not prove Powertrain.** The build only ever appends new
rows as `pending` — it never infers or auto-approves a powertrain. A human reviewer must
edit the CSV to move a row to `approved`, `rejected`, or `ambiguous`.

## 1. Where the CSV is

`backend/config/model_powertrain_review.csv`, columns:

```csv
brand2,raw_model,model2,candidate_powertrain,review_status,evidence,reviewer,reviewed_at,notes
```

- `brand2` — canonical brand as it appears in `ยี่ห้อรถ2` (post `brand_map.csv`).
- `raw_model` — the raw `รุ่นรถ` string exactly as it appears in the source DLT data
  (case/whitespace-insensitive lookup, but the literal string must correspond to a real
  raw model value).
- `model2` — display name.
- `candidate_powertrain` — `BEV`, `HEV`, `PHEV`, `ICE`, `ambiguous`, `unknown`, or blank
  (blank only while `review_status=pending`).
- `review_status` — `pending`, `approved`, `rejected`, or `ambiguous`.
- `evidence`, `reviewer`, `reviewed_at` — required once `review_status=approved`.
- `notes` — free text; auto-added rows carry `auto-added from latest model data`.

## 2. How new pending rows appear

Every `build_cleaned.py` run collects the distinct `(ยี่ห้อรถ2, รุ่นรถ, รุ่นรถ2)` triples
from the model-grain data and appends any `(brand2, raw_model)` pair not already present
in the CSV as a new row: `review_status=pending`, `candidate_powertrain` blank,
`evidence`/`reviewer`/`reviewed_at` blank, `notes=auto-added from latest model data`.
Already-reviewed rows (`approved`/`rejected`/`ambiguous`) are never touched or reordered
by this sync — it only appends, never overwrites. Re-running the build on unchanged data
is a no-op (idempotent).

## 3. How to approve a model as BEV

Edit the pending row's `candidate_powertrain`, `evidence`, `reviewer`, and `reviewed_at`,
and set `review_status=approved`:

```csv
BYD,ATTO 3,ATTO 3,BEV,approved,brochure.pdf,jet,2026-07-22,
```

Only rows with **both** `review_status=approved` and `candidate_powertrain=BEV` appear
in Sheets 7-8 (`model_map.approved_bev_keys()`). An `approved` row with a non-BEV
`candidate_powertrain` (e.g. approved as `ICE`) is valid and will simply not surface in
Sheets 7-8 — that's expected, not a bug.

## 4. Validation rules (raised as `ValueError` on load)

- Required headers (all nine columns, exact order).
- No duplicate `(brand2, raw_model)` keys (normalized: strip/collapse whitespace/upper).
- `review_status` must be one of `pending`, `approved`, `rejected`, `ambiguous`.
- `candidate_powertrain` must be one of `BEV`, `HEV`, `PHEV`, `ICE`, `ambiguous`,
  `unknown`, or blank.
- `review_status=approved` rows require non-blank `candidate_powertrain`, `evidence`,
  `reviewer`, and `reviewed_at`.

## 5. Rerun command

```
py -3.12 backend/export_manual_report.py
```

(Also produced by the full pipeline / release build.) This regenerates
`manual_report.json` from whatever is currently approved. New pending rows are added by
`build_cleaned.py`, not by `export_manual_report.py` — run the full pipeline (starting
from `build_cleaned.py`) if you want the review CSV refreshed with newly observed
models before re-approving.

## 6. Warning

**AI-suggested or auto-added rows are not approved until a human reviews them.** A row
appearing in the CSV — even with a plausible `model2` name — carries no powertrain
inference; it is `pending` and blank until a reviewer sets `candidate_powertrain`,
`evidence`, `reviewer`, `reviewed_at`, and `review_status=approved`. Never bulk-edit
`review_status` to `approved` without checking each `candidate_powertrain` value.

### Current seed requires audit

The initial file currently contains 112 BEV rows seeded by an AI-assisted pass with
`reviewer=claude-code` and generic nameplate evidence. They populate Sheets 7-8, but they
must be treated as provisional until a maintainer verifies each row against model-specific
evidence and replaces the reviewer/evidence fields. Newly auto-added rows remain `pending`.

## Scope: Sheets 7-8 only

`model_powertrain_review.csv` affects only `sheet7_bev_by_model` and
`sheet8_model_top_rank` inside `manual_report.json` (via
`export_manual_report.py::bev_model_report_slice`). It does not:

- Add a `Powertrain` column back to the general model grain (`test_model_cleaned.parquet`
  still never carries `Powertrain`/`include_in_bev_model_report` — enforced by
  `schema.py::validate_model`).
- Affect Sheets 1-6 or 9 (fuel-derived Powertrain, unrelated to this CSV).
- Add Powertrain filtering to the Models page, Deep Dive model tree, or Analyst Model
  view. Those model-grain views remain unclassified; Analyst Model view exposes `ALL`
  only. Analyst Brand view keeps fuel-derived ICE/BEV/HEV/PHEV filters.

## Release validation

`backend/validate_public_release.py` now enforces the CSV-first contract:

- Model parquet rejects `Powertrain`, `ชนิดเชื้อเพลิง`, and the legacy inclusion flag.
- Fuel parquet owns Powertrain validation.
- Dashboard model nodes contain one unclassified (`N/A`) display segment.
- Sheets 7-8 may contain only canonical models backed by approved BEV review rows.
- Analyst Model views may expose only `ALL`; Analyst Brand views own Powertrain filters.

`BUILD_RELEASE.bat` passed all nine steps on 2026-07-22 with Sheets 7-8 populated.
