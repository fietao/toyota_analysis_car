---
name: run-pipeline
description: Run the monthly car registration data pipeline. Use when the user says "run pipeline", "run cleaned", "run pivots", "run analyst", "build the report", "run the scripts", or asks to process/update the data. Runs build_cleaned.py → build_pivots.py → build_analyst.py in order. Can run individual steps or the full sequence.
---

# run-pipeline

Runs the monthly DLT car registration pipeline scripts in the correct order.

## Pipeline order

```
0. build_model2_map.py   ← one-time setup only (reads refer file, instant)
1. build_cleaned.py      ← every month (cleans raw data → test_model_1.xlsx)
2. build_pivots.py       ← every month (adds BEV/BMW pivot sheets)
3. build_analyst.py      ← every month (generates final analyst report)
```

## Commands

Full pipeline (includes map rebuild):
```bash
C:/Users/georg/AppData/Local/Programs/Python/Python312/python.exe C:/dev/ai-reading-car-analysis/.claude/scripts/run_pipeline.py
```

Full pipeline, skip map (normal monthly run):
```bash
C:/Users/georg/AppData/Local/Programs/Python/Python312/python.exe C:/dev/ai-reading-car-analysis/.claude/scripts/run_pipeline.py --skip-map
```

Individual steps:
```bash
C:/Users/georg/AppData/Local/Programs/Python/Python312/python.exe C:/dev/ai-reading-car-analysis/.claude/scripts/build_model2_map.py
C:/Users/georg/AppData/Local/Programs/Python/Python312/python.exe C:/dev/ai-reading-car-analysis/.claude/scripts/build_cleaned.py
C:/Users/georg/AppData/Local/Programs/Python/Python312/python.exe C:/dev/ai-reading-car-analysis/.claude/scripts/build_pivots.py
C:/Users/georg/AppData/Local/Programs/Python/Python312/python.exe C:/dev/ai-reading-car-analysis/.claude/scripts/build_analyst.py
```

## What each step produces

| Step | Output | Rows |
|---|---|---|
| build_model2_map | `refer/model2_map.csv` | 8,358 mappings |
| build_cleaned | `test_model_1.xlsx` (2 sheets: Data, master powertrain) | 636,333 rows |
| build_pivots | appends BEV Series Name Table + BEV/BMW sheets to `test_model_1.xlsx` | 6 sheets total |
| build_analyst | `YYYYMM_รถใหม่_...(analyst).xlsx` | final report |

## Rules

- Always run steps in order — each step depends on the previous output.
- Use `--skip-map` every month unless new models appeared in the raw data.
- If `build_cleaned` row count changes significantly from 636,333, investigate before continuing.
- If any step fails, stop and report the error — do not skip to the next step.
- Run each step as a background task and wait for completion before starting the next.
- Set `PYTHONUTF8=1` env var to avoid Thai character encoding errors.
