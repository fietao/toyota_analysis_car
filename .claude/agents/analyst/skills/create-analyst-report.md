# Local Skill: Create Analyst Report

Owner: `analyst`

Use this skill when the user needs analyst-facing pivot sheets or the final analyst
workbook.

## Scope

- Use `.claude/scripts/model/build_BEV.py` to append BEV/BMW pivot sheets when needed.
- Use `.claude/scripts/calculation/build_analyst.py` to create the final analyst report.
- Treat `test_model_1.xlsx`, `test_model_cleaned.parquet`, and `test_calculation.xlsx` as upstream inputs — do not read from `refer/` directly.
- **Stage 2 (`build_BEV.py`)**: reads data from `test_model_cleaned.parquet` (fast binary cache); reads BEV Series Name Table from `test_model_1.xlsx`. Does NOT read from `refer/` CSV or templates.
- **Stage 3 (`build_analyst.py`)**: reads data from `test_model_cleaned.parquet`. Copies master cal template (or `test_calculation.xlsx`) as the output base; replaces `Data` sheet with fresh sorted data (drops `รุ่นรถ`/`รุ่นรถ2`, keeps `ชนิดเชื้อเพลิง`). Does NOT read from `refer/` model file.
- The final analyst workbook must follow the calculation template exactly. Do not delete/recreate calculation sheets or rebuild their headers with xlsxwriter; copy `test_calculation.xlsx` and refresh only the `Data` sheet so formulas, styles, dimensions, row offsets, and sheet order survive.
- After changing calculation/report logic, compare generated sheets against `refer/*(calculation).xlsx` for sheet order, row/column counts, and key header/formula cells such as `A1`, `A3`, `A7`, `B7`, `G8`, and `H8`.

## Not This Skill

- Creating cleaned data belongs to `data-cleaner`.
- Script/tool creation belongs to `dev-tooling`.
- Pipeline coordination belongs to `reviewer` or the orchestrator.

## Reference

Use `.claude/commands/create-analyst-report.md` for the runnable command workflow.
