---
name: run-pipeline
description: Run the monthly car registration data pipeline. Use when the user says "run pipeline", "run cleaned", "run pivots", "run analyst", "build the report", "run the scripts", or asks to process/update the data. Runs build_cleaned.py -> model/build_BEV.py -> calculation/build_analyst.py in order. Can run individual steps or the full sequence.
---

# run-pipeline

Runs the monthly DLT car registration pipeline scripts in the correct order.

## Pipeline order

```text
0. build_model2_map.py          -> one-time setup only; skip for normal monthly runs
1. build_cleaned.py             -> raw data to model/calculation intermediates
2. model/build_BEV.py           -> append BEV/BMW pivot sheets to test_model_1.xlsx
3. calculation/build_analyst.py -> copy calculation template and refresh Data
```

## Commands

Full pipeline, including map rebuild:
```bash
C:/Users/georg/AppData/Local/Programs/Python/Python312/python.exe C:/dev/ai-reading-car-analysis/.claude/scripts/run_pipeline.py
```

Full pipeline, skip map for normal monthly run:
```bash
C:/Users/georg/AppData/Local/Programs/Python/Python312/python.exe C:/dev/ai-reading-car-analysis/.claude/scripts/run_pipeline.py --skip-map
```

Individual steps:
```bash
C:/Users/georg/AppData/Local/Programs/Python/Python312/python.exe C:/dev/ai-reading-car-analysis/.claude/scripts/build_model2_map.py
C:/Users/georg/AppData/Local/Programs/Python/Python312/python.exe C:/dev/ai-reading-car-analysis/.claude/scripts/build_cleaned.py
C:/Users/georg/AppData/Local/Programs/Python/Python312/python.exe C:/dev/ai-reading-car-analysis/.claude/scripts/model/build_BEV.py
C:/Users/georg/AppData/Local/Programs/Python/Python312/python.exe C:/dev/ai-reading-car-analysis/.claude/scripts/calculation/build_analyst.py
```

## What each step produces

| Step | Output | Notes |
|---|---|---|
| build_model2_map | `refer/model2_map.csv` | Model-name mappings |
| build_cleaned | `test_model_1.xlsx`, `test_calculation.xlsx`, `test_model_cleaned.parquet`, `test_fuel_cleaned.parquet` | Copies refer templates; replaces Data sheets; calc Data has no Powertrain column |
| model/build_BEV | BEV Series Name Table + BEV/BMW sheets appended to `test_model_1.xlsx` | Reads data from `test_model_cleaned.parquet` (fast); reads BEV table from `test_model_1.xlsx` |
| calculation/build_analyst | `YYYYMM_รถใหม่_...(test analyst).xlsx` | Copies `test_calculation.xlsx`; refreshes Data; no refer/ reads |

## Drop-folder automation

`watch_and_run.py` monitors `input/` for new `.xlsx` files:
- Automatically deletes the old matching raw file from `raw data/` before moving the new one in.
- Triggers the full pipeline and moves the analyst report to `output/`.
- Raw files are cumulative (full history since 2018); each new file replaces the previous month's.

## Refer folder

`refer/` files are structure-only templates — all numeric data has been stripped.
Pipeline scripts read mappings (text labels) and use them as copy templates only.
Do not manually add numeric data back to refer files.

## Rules

- Always run steps in order; each step depends on the previous output.
- Use `--skip-map` every month unless new models appeared in the raw data.
- If row counts change significantly from the last known-good run, investigate before continuing.
- If any step fails, stop and report the error; do not skip to the next step.
- Run each step as a background task and wait for completion before starting the next.
- Set `PYTHONUTF8=1` env var to avoid Thai character encoding errors.
- Calculation report sheets must follow `refer/*(calculation).xlsx`. Do not delete/recreate those sheets; refresh only the `Data` sheet while preserving formulas, styles, dimensions, and sheet order.
