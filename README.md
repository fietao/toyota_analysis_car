# ai-reading-car-analysis

Monthly Thailand new-car registration analysis pipeline (DLT data) and Next.js frontend dashboard.

## Directory Structure

- `backend/`: The data processing pipeline (Python).
- `frontend/`: The Next.js dashboard application.

## Pipeline (Backend)

```
build_model2_map.py   ← one-time or when new models appear
build_cleaned.py      ← every month  →  test_model_cleaned.parquet (Data + master powertrain)
build_BEV.py          ← every month  →  appends BEV Series Name Table
build_analyst.py      ← every month  →  YYYYMM_รถใหม่_...(analyst).xlsx
export_dashboard.py   ← every month  →  frontend/public/data/dashboard_data.json
```

Run via `/run-pipeline` or directly from root:

```cmd
UPDATE.bat
```

Or manually:

```bash
cd backend
python run_pipeline.py --skip-map
```

## Key files

| Path | Purpose |
|------|---------|
| `backend/raw data/รถใหม่_*.xlsx` | Raw DLT registration data |
| `backend/refer/*- Model.xlsx` | Template workbook (master powertrain, BEV Series Name Table) |
| `backend/refer/model2_map.csv` | Normalized model name mappings (8,358 rows) |
| `backend/test_model_cleaned.parquet` | Pipeline intermediate output |
| `frontend/public/data/dashboard_data.json` | Dashboard data |
| `backend/specs/` | Sheet implementation specs |
