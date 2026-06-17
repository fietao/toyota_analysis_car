# Local Skill: Create Analyst Report

Owner: `analyst`

Use this skill when the user needs analyst-facing pivot sheets or the final analyst
workbook.

## Scope

- Use `.claude/scripts/build_pivots.py` to append BEV/BMW pivot sheets when needed.
- Use `.claude/scripts/build_analyst.py` to create the final analyst report.
- Treat `test_model_1.xlsx` and `test_model_cleaned.parquet` as upstream inputs.

## Not This Skill

- Creating cleaned data belongs to `data-cleaner`.
- Script/tool creation belongs to `dev-tooling`.
- Pipeline coordination belongs to `reviewer` or the orchestrator.

## Reference

Use `.claude/commands/create-analyst-report.md` for the runnable command workflow.
