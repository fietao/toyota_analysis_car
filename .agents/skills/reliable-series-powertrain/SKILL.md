---
name: reliable-series-powertrain
description: Repair or extend this repository's series and powertrain pipeline without guessing joint facts from separate DLT model and fuel aggregates.
---

# Reliable Series and Powertrain

Use this workflow whenever changing model normalization, powertrain classification, Deep Dive,
or BEV model reports.

## Non-negotiable data boundary

- The model DLT source proves brand, raw series, geography, period, vehicle type, and count.
- The fuel DLT source proves brand, fuel, geography, period, vehicle type, and count.
- Neither source proves the joint series-powertrain count.
- Never restore dominant-fuel enrichment, statistical matching, probabilistic linkage, or silent
  fallbacks as factual data.

## Canonical approach

1. Preserve each source at its own grain.
2. Resolve raw model names through `backend/config/model_map.csv`, keyed by canonical brand plus
   normalized raw model.
3. Keep model-grain output free of `Powertrain`; unresolved names fall back to the raw model name.
4. Append newly observed models as `pending` in `backend/config/model_powertrain_review.csv`.
5. Approve a classification only when the raw variant unambiguously identifies one powertrain
   and evidence, reviewer, and review time are recorded.
6. Use approved BEV review rows only for Sheets 7-8. Never split an ambiguous model count or
   enrich the general model grain.

## Execution order

1. Add or run a red-capable regression check for the reported misclassification.
2. Trace source row -> mapping/review CSV -> cleaned data -> export -> UI before editing.
3. Validate both CSV schemas, enum values, composite-key uniqueness, and evidence requirements.
4. Change one pipeline boundary at a time and immediately run its reconciliation check.
5. Keep the human-edited review CSV out of the public static write path.
6. Update Deep Dive, Excel export, and Sheets 7-8 only after backend facts validate.
7. Remove obsolete maps and dead paths only after all consumers have migrated.
8. Run the complete release gate and manually inspect public output.

## Required invariants

- Model totals equal the raw model source.
- Brand/powertrain totals equal the raw fuel source.
- Unverified values are never displayed as verified.
- Sheets 7-8 include only explicitly verified BEV raw variants.
- Public output contains no admin writer or write endpoint.
- Review CSV updates never overwrite existing human decisions.

## Deep Dive rules

- Keep one brand -> canonical-series hierarchy.
- Show source-derived model totals without Powertrain segmentation.
- Never use brand fuel to filter model children.
- Excel download and UI must use the same selector and totals.

## Common failure modes

- Using year/month/vehicle type/province/brand as if it identifies a model's fuel.
- Keying a model map by raw series without brand.
- Migrating contaminated inferred values as reviewed truth.
- Auto-approving new electric models.
- Hiding `N/A`, which makes totals appear cleaner but breaks reconciliation.
- Treating a series capability such as `[ICE, HEV]` as permission to split an ambiguous count.
- Keeping duplicate CSV, Excel, and hard-coded mapping sources after migration.
- Shipping local admin controls in the static public build.

## Done criteria

Work is complete only when every required invariant passes, the original misclassification no
longer reproduces, CSV review persists correctly, the public site remains read-only, model totals
reconcile, and obsolete mapping paths are removed without disturbing unrelated working-tree changes.
