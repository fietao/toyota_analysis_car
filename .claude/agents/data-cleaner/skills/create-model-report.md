# Local Skill: Create Model Report

Owner: `data-cleaner`

Use this skill when the user needs the cleaned model workbook or asks for
`/create-model-report`.

## Scope

- Owns the raw-data to cleaned-model part of the pipeline.
- Uses `.claude/scripts/build_cleaned.py`.
- Produces or updates `test_model_1.xlsx`.
- Produces `test_model_cleaned.parquet` for downstream analyst work.

## Not This Skill

- Analyst report generation belongs to `analyst`.
- Pivot/report script repair belongs to `dev-tooling` unless the fix is trivial and
  already inside the data-cleaner-owned script.
- Domain mapping decisions should be escalated or asked, not guessed.

## Reference

Use `.claude/commands/create-model-report.md` for the runnable command workflow.
