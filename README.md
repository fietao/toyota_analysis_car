# ai-reading-car-analysis

Monthly Thailand new-car registration analysis pipeline (DLT data) and Next.js frontend dashboard.

## Use the dashboard

The repository includes the latest generated public JSON, so the dashboard can run without
the private/raw Excel inputs. For a non-technical user, double-click `START.bat` at the repo
root — it installs anything missing on first run, then opens the dashboard. Nothing else to
type or configure.

Technical users can run the same two steps by hand instead:

```powershell
INSTALL_FROM_ZERO.bat
frontend\RUN.bat
```

Open `http://localhost:3001`. The static site is also deployable through the included
GitHub Pages workflow.

## Directory Structure

- `backend/`: The data processing pipeline (Python).
- `frontend/`: The Next.js dashboard application.
- `docs/`: Project/product docs (`PRODUCT.md`, `DESIGN.md`, `SKILLS.md`).
- `handoffs/`: Current operator runbook and release handoff.

## Pipeline (Backend)

The two DLT sources remain at separate grains. Model rows never receive `Powertrain`;
fuel rows derive it from `backend/config/powertrain_map.csv`. Model maintenance is CSV-first:

- `backend/config/model_map.csv` maps `(brand2, raw_model)` to the canonical `model2` name.
- `backend/config/model_powertrain_review.csv` stores human review decisions. New model rows
  are appended as `pending`; approved BEV rows control Sheets 7-8 only.

```
build_cleaned.py      ← every month  →  separate model-grain and fuel-grain parquets
build_analyst.py      ← every month  →  YYYYMM_รถใหม่_...(analyst).xlsx
export_dashboard.py   ← every month  →  frontend/public/data/dashboard_summary.json, dashboard_models.json, cleaned_data_manifest.json
export_analyst.py     ← every month  →  frontend/public/data/analyst_data.json
export_manual_report.py ← every month → frontend/public/data/manual_report.json
```

Nothing infers a model Powertrain from aggregate fuel data. Dashboard and Analyst model views
remain unclassified; only explicitly approved BEV review rows enter Sheets 7-8. See
`handoffs/bev-whitelist-runbook-2026-07-22.md` for the review workflow.

## Normal Operation

These scripts at the project root cover normal operation and handoff:

| Script | When | What it does |
|---|---|---|
| `START.bat` | Any time, on any laptop, for a non-technical user | One double-click: installs anything missing (first run only), then opens the dashboard. No menu, no typing. |
| `INSTALL_FROM_ZERO.bat` | First time on a fresh Windows laptop | Checks or installs Python 3.12, Node.js LTS/npm, and Git with `winget`, then runs `SETUP.bat`. |
| `TAKEOVER.bat` | Handoff sessions on another laptop | Opens a plain-language menu: start the dashboard, run the monthly update, open the monthly guide/latest summary/model review file, run frontend checks, plus one-time install/setup and takeover notes. |
| `SETUP.bat` | Once, or after pulling dependency changes | Installs backend Python packages (`backend/requirements.txt`) and frontend npm packages. |
| `MONTHLY_UPDATE.bat` | Monthly, by anyone (operator or developer) | Guided double-click flow: checks the 2 raw files, preflights the model-review CSV, rebuilds the pipeline + dashboard + Sheets 7-8, builds into a staging copy, validates it, and only then atomically swaps the live JSON (rollback on any failure — the dashboard always keeps the last good data). Writes `reports/monthly_operator_summary.txt` and a timestamped `logs/` file, all with Thai messages. See `docs/THAI_OPERATOR_MONTHLY_GUIDE.md`. |
| `BUILD_RELEASE.bat` | Before publishing | Runs the full deterministic pipeline, exports dashboard/analyst/manual-report data, validates against a markdown export and the public-release gate, then builds the Next.js production bundle. Set `MARKDOWN_REPORT_PATH` to point at the `*_sheets1-9.md` export directly; otherwise it looks for the newest one in `%USERPROFILE%\Downloads`. |

After a monthly build, review newly appended `pending` rows in
`backend/config/model_powertrain_review.csv`, record evidence/reviewer/date, and set only
confirmed rows to `approved`. Run `BUILD_RELEASE.bat` again to refresh Sheets 7-8.

Raw DLT workbooks and generated parquet/Excel files are intentionally excluded from Git.
Maintainers who rebuild the data must supply those files locally; dashboard users do not
need them.

## Checks

Pull requests and pushes to `main` run backend unit tests plus frontend tests, linting,
type checking, and a static production build. The real-data reconciliation test is run by
`BUILD_RELEASE.bat` because its raw DLT inputs are intentionally not published.

## Key files

| Path | Purpose |
|------|---------|
| `backend/raw data/รถใหม่_*.xlsx` | Raw DLT registration data |
| `backend/refer/*- Model.xlsx` | Template workbook (master powertrain, BEV Series Name Table) |
| `backend/config/brand_map.csv` | Raw brand → canonical brand mapping |
| `backend/config/model_map.csv` | `(brand2, raw_model)` → canonical model name mapping |
| `backend/config/model_powertrain_review.csv` | Human-reviewed model classification; approved BEV rows feed Sheets 7-8 |
| `backend/config/powertrain_map.csv` | Raw fuel type → powertrain (ICE/HEV/PHEV/BEV) mapping |
| `backend/test_model_cleaned.parquet` | Model-grain output; never carries fuel or Powertrain columns |
| `backend/test_fuel_cleaned.parquet` | Fuel-grain output and Powertrain source |
| `frontend/public/data/dashboard_summary.json` | General summary and powertrain data |
| `frontend/public/data/dashboard_models.json` | Brand and model data tree |
| `frontend/public/data/cleaned_data_manifest.json` | Cleaned dataset metadata manifest |
| `frontend/public/data/analyst_data.json` | Analyst pivot table calculations |

## License

Released under the [MIT License](LICENSE).
