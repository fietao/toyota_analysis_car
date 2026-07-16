# Public Release Clean Merge Plan

## Goal

Make the public dashboard feel like one professional report product, not separate pages with slightly different data rules.

The product must clearly answer: “Which report slice am I looking at, what source created it, and can I trust the numbers?”

## Current State

- `/` is the main dashboard using `dashboard_summary.json` and lazy `dashboard_models.json`.
- `/models` is a model explorer using `dashboard_models.json`.
- `/analyst` is a calculation-table explorer using `analyst_data.json`.
- `/report` is the new markdown-style report mode for sheets 1–6.
- `dashboard_models.json` now preserves model-level `powertrain`, which is required for BEV Major model pages.
- `validate_public_release.py` now checks reporting periods and model powertrain annotations.

## Product Direction

The site should have three clear modes:

| Mode | Purpose | Data source |
|---|---|---|
| Dashboard | Fast visual overview | `dashboard_summary.json` |
| Manual Report | Public report generated from DLT raw files plus mapping, validated against golden markdown cells | canonical report export |
| Deep Dive | Interactive exploration beyond the manual workbook | `dashboard_models.json`, `analyst_data.json` |

## Data Merge Rule

Do not physically merge everything into one huge JSON file.

Instead, create one canonical report export with explicit sections:

```json
{
  "meta": {
    "reporting_period": "June 2569",
    "default_vehicle_types": ["รย.1", "รย.2", "รย.3", "รย.6", "รย.9", "รย.10", "รย.11"],
    "source_files": {
      "brand_powertrain": "test_fuel_cleaned.parquet",
      "model": "test_model_cleaned.parquet"
    }
  },
  "sheets": {
    "sheet1_powertrain": [],
    "sheet2_brand_all": [],
    "sheet3_brand_ice": [],
    "sheet4_brand_bev": [],
    "sheet5_brand_hev": [],
    "sheet6_brand_phev": [],
    "sheet7_bev_by_model": [],
    "sheet8_model_top_rank": [],
    "sheet9_by_province": []
  }
}
```

Recommended file:

```text
frontend/public/data/manual_report.json
```

Why this is better:

- `/report` becomes simple and fast.
- Validation can compare one JSON to markdown golden cells; markdown/workbook files are validation references, not data sources.
- The UI does not recompute spreadsheet logic in React.
- Each section can declare its source and filter.

## Implementation Phases

### Phase 1 — Canonical Manual Report Export

Create:

```text
backend/export_manual_report.py
frontend/public/data/manual_report.json
```

Rules:

- Sheets 1–6 use `backend/test_fuel_cleaned.parquet`.
- Sheets 7–8 use `backend/test_model_cleaned.parquet` with `include_in_bev_model_report == true`.
- Sheet 9 uses `backend/test_fuel_cleaned.parquet` grouped by province and brand.
- Default vehicle types are exactly `รย.1,2,3,6,9,10,11`.
- Every sheet row includes:
  - row key
  - row label
  - 2568 Jan-Dec
  - 2568 Total
  - 2568 Share where relevant
  - 2569 Jan-Jun
  - 2569 YTD
  - 2569 Share where relevant
  - growth/rank fields where relevant

Verification:

```powershell
py -3.12 backend\export_manual_report.py
py -3.12 backend\validate_against_markdown.py "C:\Users\georg\Downloads\รถใหม่_มิถุนายน 2569 (2)_sheets1-9.md"
```

### Phase 2 — `/report` Reads Manual Report JSON

Change:

```text
frontend/src/app/report/page.tsx
```

Rules:

- Stop recalculating report logic in React.
- Fetch `/data/manual_report.json`.
- Render sections from the canonical JSON.
- Show source/filter metadata in the header.
- Sheets 1–9 should all be available, even if some sections are marked with validation warnings.

Verification:

```powershell
npm run lint
npx tsc --noEmit
npm run build
```

### Phase 3 — Professional Report UI Polish

Apply DLT Terminal design system:

- No hero cards.
- No decorative gradients.
- Use compact table controls.
- Use one visual vocabulary across `/`, `/report`, `/models`, and `/analyst`.
- Add report status strip:
  - reporting period
  - vehicle filter
  - source file
  - validation status
- Fail the release for Sheet 7-8 mismatches; do not ship known unresolved cells.

Verification:

- Screenshot `/report`.
- Check table sticky headers.
- Keyboard-tab through sheet selector and search.
- Confirm contrast on muted labels.

### Phase 4 — Release Gate

Update:

```text
BUILD_RELEASE.bat
backend/validate_public_release.py
```

Add steps:

```powershell
py -3.12 backend\export_manual_report.py
py -3.12 backend\validate_against_markdown.py "<markdown path or known fixture>"
```

If the live markdown path is not available in CI, commit a small golden JSON fixture extracted from the markdown.

## Acceptance Criteria

- `/report` shows all 9 manual sections.
- Sheets 1–9 match the markdown golden cells.
- Sheets 7–8 use `include_in_bev_model_report == true`, derived from raw_model -> model2 -> report inclusion mapping.
- Sheet 9 province rows reconcile to child brand rows.
- UI visibly distinguishes:
  - Manual Report Mode
  - Dashboard Mode
  - Deep Dive Mode
- Public release build fails if report periods or required report sections are missing.

## First Task To Assign

Implement `backend/export_manual_report.py` and `frontend/public/data/manual_report.json` for sheets 1–6 only.

Do not touch UI yet except if needed for local verification. Once the canonical report export exists, the UI becomes much easier and safer to polish.

## Resolved Sheet 7-8 Contract

Sheets 7-8 are generated from `test_model_cleaned.parquet` rows where
`include_in_bev_model_report == true`. That flag is derived from the repo mapping table, not
from workbook/manual data and not from `Powertrain == "BEV Major"`. Sheet 7-8 mismatches are
hard release failures.
