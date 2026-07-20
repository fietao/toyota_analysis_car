# ai-reading-car-analysis

Monthly Thailand new-car registration analysis pipeline (DLT data) and Next.js frontend dashboard.

## Directory Structure

- `backend/`: The data processing pipeline (Python).
- `frontend/`: The Next.js dashboard application.
- `docs/`: Project/product docs (`ROADMAP.md`, `PRODUCT.md`, `DESIGN.md`, `SKILLS.md`).
- `_archive/`: Retired one-off scripts, kept for reference.

## Pipeline (Backend)

`backend/refer/series_registry.csv` is the sole canonical-series-name and model-powertrain
authority (see `plans/reliable-series-powertrain.md`). A raw model series resolves to its
registry entry if one exists, otherwise it displays as the raw source name — there is no other
name-mapping fallback.

```
build_cleaned.py      ← every month  →  test_model_cleaned.parquet (Data + master powertrain)
build_analyst.py      ← every month  →  YYYYMM_รถใหม่_...(analyst).xlsx
export_dashboard.py   ← every month  →  frontend/public/data/dashboard_summary.json, dashboard_models.json, cleaned_data_manifest.json
export_analyst.py     ← every month  →  frontend/public/data/analyst_data.json
export_manual_report.py ← every month → frontend/public/data/manual_report.json
```

Unresolved or ambiguous series display `N/A` until a local administrator reviews and verifies
them through the review panel (see `RUN_ADMIN.bat` below) — nothing infers a series' powertrain
from aggregate fuel data.

## Normal Operation

Four scripts at the project root cover everything day to day:

| Script | When | What it does |
|---|---|---|
| `SETUP.bat` | Once, or after pulling dependency changes | Installs backend Python packages (`backend/requirements.txt`) and frontend npm packages. |
| `RUN_ADMIN.bat` | To review/verify unresolved series | Starts the local-only admin review server (`127.0.0.1:8765`) and the Next.js dev server at `http://localhost:3000`. The admin server never ships in the public release build. |
| `UPDATE.bat` | Monthly, after dropping the 2 new DLT files into `backend/raw data/` | Runs `update_raw_data.py`: classifies new fuel types, rebuilds the pipeline, and exports dashboard data. |
| `BUILD_RELEASE.bat` | Before publishing | Runs the full deterministic pipeline, exports dashboard/analyst/manual-report data, validates against a markdown export and the public-release gate, then builds the Next.js production bundle. Set `MARKDOWN_REPORT_PATH` to point at the `*_sheets1-9.md` export directly; otherwise it looks for the newest one in `%USERPROFILE%\Downloads`. |

## Key files

| Path | Purpose |
|------|---------|
| `backend/raw data/รถใหม่_*.xlsx` | Raw DLT registration data |
| `backend/refer/*- Model.xlsx` | Template workbook (master powertrain, BEV Series Name Table) |
| `backend/refer/series_registry.csv` | Canonical series-name and powertrain authority (versioned; reviewed via `RUN_ADMIN.bat`) |
| `backend/config/brand_map.csv` | Raw brand → canonical brand mapping |
| `backend/config/powertrain_map.csv` | Raw fuel type → powertrain (ICE/HEV/PHEV/BEV) mapping |
| `backend/test_model_cleaned.parquet` | Pipeline intermediate output |
| `frontend/public/data/dashboard_summary.json` | General summary and powertrain data |
| `frontend/public/data/dashboard_models.json` | Brand and model data tree |
| `frontend/public/data/cleaned_data_manifest.json` | Cleaned dataset metadata manifest |
| `frontend/public/data/analyst_data.json` | Analyst pivot table calculations |
| `backend/specs/` | Sheet implementation specs |
