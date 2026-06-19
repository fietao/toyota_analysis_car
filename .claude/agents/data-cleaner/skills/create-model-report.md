# Local Skill: Create Model Report

Owner: `data-cleaner`

Use this skill when the user needs the cleaned model workbook or asks for
`/create-model-report`.

## Scope

- Owns the raw-data to cleaned-model part of the pipeline.
- Uses `.claude/scripts/build_cleaned.py`.
- Finds templates via glob: `refer/*- Model.xlsx` and `refer/*(calculation).xlsx`.
- Copies Model template → `test_model_1.xlsx`; replaces its `Data` sheet with all cleaned model rows (includes `Powertrain`).
- Copies Calculation template → `test_calculation.xlsx`; replaces its `Data` sheet with cleaned fuel rows **without** the `Powertrain` column.
- Produces `test_model_cleaned.parquet` (model rows) and `test_fuel_cleaned.parquet` (fuel rows) for downstream use.
- When updating `test_calculation.xlsx`, preserve the calculation template layout: keep title/metadata rows, write headers at Excel row 6, and keep `Powertrain` only in `test_model_1.xlsx`.

## Not This Skill

- Analyst report generation belongs to `analyst`.
- Pivot/report script repair belongs to `dev-tooling` unless the fix is trivial and
  already inside the data-cleaner-owned script.
- Domain mapping decisions should be escalated or asked, not guessed.

## Reference

Use `.claude/commands/create-model-report.md` for the runnable command workflow.
