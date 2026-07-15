# ai-reading-car-analysis

Monthly Thailand new-car registration analysis pipeline (DLT data) and Next.js frontend dashboard.

## Directory Structure

- `backend/`: The data processing pipeline (Python).
- `frontend/`: The Next.js dashboard application.
- `docs/`: Project/product docs (`ROADMAP.md`, `PRODUCT.md`, `DESIGN.md`, `SKILLS.md`).
- `_archive/`: Retired one-off scripts, kept for reference.

## Pipeline (Backend)

```
build_model2_map.py   ← one-time or when new models appear
build_cleaned.py      ← every month  →  test_model_cleaned.parquet (Data + master powertrain)
build_BEV.py          ← every month  →  appends BEV Series Name Table
build_analyst.py      ← every month  →  YYYYMM_รถใหม่_...(analyst).xlsx
export_dashboard.py   ← every month  →  frontend/public/data/dashboard_summary.json, dashboard_models.json, cleaned_data_manifest.json
export_analyst.py     ← every month  →  frontend/public/data/analyst_data.json
```

## Running Builds

- **Local Development**: Run `RUN_ALL.bat` at the project root to start the local Next.js dev server (runs frontend on `http://localhost:3000` using local static data, skipping the full backend pipeline).
- **Public Release Build**: Run `BUILD_RELEASE.bat` at the project root. This command runs the full deterministic pipeline (`run_pipeline.py --skip-map`), exports the dashboard and analyst data, runs validation (`validate_public_release.py`), and compiles the Next.js production build.

## Key files

| Path | Purpose |
|------|---------|
| `backend/raw data/รถใหม่_*.xlsx` | Raw DLT registration data |
| `backend/refer/*- Model.xlsx` | Template workbook (master powertrain, BEV Series Name Table) |
| `backend/refer/model2_map.csv` | Normalized model name mappings (8,358 rows) |
| `backend/test_model_cleaned.parquet` | Pipeline intermediate output |
| `frontend/public/data/dashboard_summary.json` | General summary and powertrain data |
| `frontend/public/data/dashboard_models.json` | Brand and model data tree |
| `frontend/public/data/cleaned_data_manifest.json` | Cleaned dataset metadata manifest |
| `frontend/public/data/analyst_data.json` | Analyst pivot table calculations |
| `backend/specs/` | Sheet implementation specs |
