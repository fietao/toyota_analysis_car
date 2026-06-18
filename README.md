# ai-reading-car-analysis

Monthly Thailand new-car registration analysis pipeline (DLT data).

## Pipeline

```
build_model2_map.py   ← one-time or when new models appear
build_cleaned.py      ← every month  →  test_model_1.xlsx (Data + master powertrain)
build_pivots.py       ← every month  →  appends BEV Series Name Table + BEV/BMW pivots
build_analyst.py      ← every month  →  YYYYMM_รถใหม่_...(analyst).xlsx
```

Run via `/run-pipeline` or directly:

```bash
python .claude/scripts/run_pipeline.py --skip-map
```

## Key files

| Path | Purpose |
|------|---------|
| `raw data/รถใหม่_*.xlsx` | Raw DLT registration data |
| `refer/*- Model.xlsx` | Template workbook (master powertrain, BEV Series Name Table) |
| `refer/model2_map.csv` | Normalized model name mappings (8,358 rows) |
| `test_model_1.xlsx` | Pipeline output (6 sheets) |
| `.claude/scripts/` | Pipeline scripts |
| `specs/` | Sheet implementation specs |
