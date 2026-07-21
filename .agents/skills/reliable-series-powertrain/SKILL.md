---
name: reliable-series-powertrain
description: Repair or extend this repository's series and powertrain pipeline without guessing joint facts from separate DLT model and fuel aggregates.
---

# Reliable Series and Powertrain

Use this workflow whenever changing model normalization, powertrain classification, the local
series-review UI, Deep Dive, or BEV model reports.

## Non-negotiable data boundary

- The model DLT source proves brand, raw series, geography, period, vehicle type, and count.
- The fuel DLT source proves brand, fuel, geography, period, vehicle type, and count.
- Neither source proves the joint series-powertrain count.
- Never restore dominant-fuel enrichment, statistical matching, probabilistic linkage, or silent
  fallbacks as factual data.

## Canonical approach

1. Preserve each source at its own grain.
2. Resolve raw series through `backend/refer/series_registry.csv`, keyed by canonical brand plus
   normalized raw series.
3. Treat missing, ambiguous, conflicting, or unreviewed mappings as `N/A`.
4. Mark a powertrain verified only when the raw variant unambiguously identifies one powertrain
   and evidence, reviewer, and review time are recorded.
5. Allow one canonical series to contain several verified powertrains through distinct raw
   variants. Never split an ambiguous raw row.
6. Compute the review queue from source rows minus verified registry rows; do not create another
   persistent queue file.

## Execution order

1. Add or run a red-capable regression check for the reported misclassification.
2. Trace source row -> registry -> cleaned data -> export -> UI before editing.
3. Validate registry schema, enum values, composite-key uniqueness, and evidence requirements.
4. Change one pipeline boundary at a time and immediately run its reconciliation check.
5. Update local admin behavior separately from public static behavior.
6. Update Deep Dive, Excel export, and Sheets 7-8 only after backend facts validate.
7. Remove obsolete maps and dead paths only after all consumers have migrated.
8. Run the complete release gate and manually inspect public output.

## Required invariants

- Model totals equal the raw model source.
- Brand/powertrain totals equal the raw fuel source.
- For each brand and canonical series:

  `ICE + HEV + PHEV + BEV + N/A = source series total`

- Unverified values are never displayed as verified.
- Sheets 7-8 include only explicitly verified BEV raw variants.
- Public output contains no admin writer or write endpoint.
- Local registry writes are schema-validated, atomic, and conflict-safe.

## Deep Dive rules

- Keep one brand -> canonical-series hierarchy.
- Show source-derived series total plus verified PT and `N/A` segments.
- Filter on verified classifications and `N/A`; never use brand fuel to filter children.
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
longer reproduces, local review persists correctly, the public site remains read-only, the Deep
Dive and Excel export agree, and obsolete mapping paths are removed without disturbing unrelated
working-tree changes.
