IMPLEMENTATION NOTE: Read this spec completely before writing any code.
After each section is implemented, tick the verification check for that section.

# Public Dashboard Markdown Parity Spec

## Goal

Make the public web program match the manual markdown workbook exported at:

`C:\Users\georg\Downloads\รถใหม่_มิถุนายน 2569 (2)_sheets1-9.md`

The markdown is the visual/business-rule reference for sheets 1–9. The program does not need to copy Excel formatting perfectly, but it MUST compute the same slices, filters, totals, shares, growths, ranks, and brand/model/province groupings.

## Scope

Sheets in the markdown:

| Sheet | Manual title | Web equivalent |
|---|---|---|
| 1 | `1.Reg by Powertrain` | Homepage powertrain summary / trend table |
| 2 | `2.Rank by Brand` | Brand ranking with Powertrain = All |
| 3 | `3.ICE by Brand` | Brand ranking filtered to ICE |
| 4 | `4.BEV by Brand` | Brand ranking filtered to BEV |
| 5 | `5.HEV by Brand` | Brand ranking filtered to HEV |
| 6 | `6.PHEV by Brand` | Brand ranking filtered to PHEV |
| 7 | `7.BEV by Model` | `/models` or analyst model view filtered to BEV Major |
| 8 | `8.Model Top Rank` | Model ranking filtered to BEV Major |
| 9 | `9.by Province` | Province breakdown table/chart |

## Inputs

| Input | Purpose |
|---|---|
| Markdown file | Golden manual output and expected business logic |
| `backend/test_fuel_cleaned.parquet` | Brand/powertrain/province source for sheets 1–6 and 9 |
| `backend/test_model_cleaned.parquet` | Model source for sheets 7–8 |
| `frontend/public/data/dashboard_summary.json` | Public summary export |
| `frontend/public/data/dashboard_models.json` | Public brand/model tree export |
| `frontend/public/data/analyst_data.json` | Public analyst export |

## Universal Data Rules

- Vehicle type filter MUST default to exactly `รย.1,2,3,6,9,10,11` for markdown-parity views.
- Province filter MUST default to all provinces unless a page explicitly selects one or more provinces.
- Year range MUST be derived from source data. Do not hardcode current year/month.
- Current reporting period in this markdown is June 2569, with comparison year 2568.
- 2569 totals are YTD through June.
- 2568 totals use all 12 months where the manual sheet shows `2568 Total`.
- Shares MUST be calculated within the active filtered slice, not within all public data.
- Growth calculations MUST use the same denominator as the manual sheet:
  - `Growth vs May 2569` = `(Jun 2569 - May 2569) / May 2569`
  - `Growth vs Jun 2568` = `(Jun 2569 - Jun 2568) / Jun 2568`
  - `Growth vs Jan-Jun 2568` = `(Jan-Jun 2569 - Jan-Jun 2568) / Jan-Jun 2568`
- Blank or missing numeric values SHOULD display as `—` in the UI, but validation MUST compare them as zero or null according to the source meaning.

## Sheet 1 — Reg by Powertrain

### Data Rules

- Source: `backend/test_fuel_cleaned.parquet`.
- Filter:
  - `ประเภทรถ` in `รย.1,2,3,6,9,10,11`
  - Powertrain rows: `ICE`, `BEV`, `HEV`, `PHEV`
- Grand Total row MUST equal the sum of ICE + BEV + HEV + PHEV.
- Markdown known checks:
  - Grand Total Jan-Jun 2568 = `324,368`
  - Grand Total Jan-Jun 2569 = `374,424`
  - BEV 2568 Total = `122,559`
  - BEV Jan-Jun 2569 = `105,558`

### Validation Checks

- CHECK: Powertrain rows are exactly `Grand Total`, `ICE`, `BEV`, `HEV`, `PHEV`.
- CHECK: All row/month values match markdown for 2568 Jan-Dec and 2569 Jan-Jun.
- CHECK: Shares per period sum to 1.0, allowing rounding tolerance.

## Sheets 2–6 — Rank by Brand

### Data Rules

- Source: `backend/test_fuel_cleaned.parquet`.
- Filter:
  - `ประเภทรถ` in `รย.1,2,3,6,9,10,11`
  - Sheet 2: Powertrain = All
  - Sheet 3: Powertrain = ICE
  - Sheet 4: Powertrain = BEV
  - Sheet 5: Powertrain = HEV
  - Sheet 6: Powertrain = PHEV
- Rows are grouped by canonical brand (`ยี่ห้อรถ2`).
- Row order MUST sort by active current-year YTD units descending, with `Grand Total` pinned first.
- Rank columns:
  - 2568 rank = rank by 2568 Total.
  - 2569 rank = rank by Jan-Jun 2569 Total.
  - Diff = 2568 rank - 2569 rank or the manual equivalent if confirmed from workbook formulas.

### Markdown Known Checks

- Sheet 2 Grand Total Jan-Jun 2569 = `374,424`.
- Sheet 2 BYD Jan-Jun 2569 = `26,069`.
- Sheet 4 Grand Total Jan-Jun 2569 = `105,558`.
- Sheet 4 BYD 2568 Total = `33,070` in current fuel source, while markdown shows `33,077`; this 7-unit mismatch MUST be investigated before claiming full parity.
- Sheet 4 BYD Jan-Jun 2569 = `21,450`.

### Validation Checks

- CHECK: Each sheet’s Grand Total equals the sum of visible brand rows.
- CHECK: For each powertrain-filtered sheet, rows contain no registrations from other powertrains.
- CHECK: BYD values in Sheet 4 match the manual markdown or the mismatch is documented with source-file evidence.

## Sheet 7 — BEV by Model

### Data Rules

- Source: `backend/test_model_cleaned.parquet`.
- Filter:
  - `ประเภทรถ` in `รย.1,2,3,6,9,10,11`
  - model-table `Powertrain == "BEV Major"`
- MUST NOT use only fuel-derived `PT == "BEV"` for model rows.
- Brand rows and child model rows MUST be generated from the same model-table filtered slice when this page is intended to match the markdown.
- The `/models` general explorer MAY also expose fuel-derived BEV data, but it must label that clearly and MUST NOT present it as “BEV Major”.

### Markdown Known Checks

For BYD:

| Row | 2568 Total | Jan-Jun 2569 |
|---|---:|---:|
| BYD brand row | `33,077` | `21,450` |
| BYD DOLPHIN | `12,435` | `8,696` |
| BYD ATTO 3 | `7,962` | `7,357` |
| BYD SEALION 7 | `8,372` | `2,291` |

### Anti-Patterns

- MUST NOT include `BYD SEALION 6` in BEV Major model rows when its model-table `Powertrain` is `OTH`.
- MUST NOT include `BYD SEAL 5 DM-i` in BEV Major model rows when its model-table `Powertrain` is `OTH`.
- MUST NOT mix fuel-parquet brand totals with model-parquet child rows on a markdown-parity BEV-by-model table unless the mismatch is visibly disclosed.

### Validation Checks

- CHECK: Every model row has model-level `Powertrain` available in `dashboard_models.json`.
- CHECK: BEV Major filtered model rows exclude `Powertrain == OTH`.
- CHECK: BYD DOLPHIN, BYD ATTO 3, and BYD SEALION 7 totals match the markdown.

## Sheet 8 — Model Top Rank

### Data Rules

- Source: `backend/test_model_cleaned.parquet`.
- Filter:
  - `ประเภทรถ` in `รย.1,2,3,6,9,10,11`
  - model-table `Powertrain == "BEV Major"`
- Rows are grouped by model + brand.
- Rows sort by 2569 YTD total descending.
- Rank columns:
  - 2568 rank = rank by 2568 Total.
  - 2569 rank = rank by Jan-Jun 2569 Total.
  - Diff = 2568 rank - 2569 rank or manual equivalent.
  - `Jun'69` = rank within June 2569 only.

### Markdown Known Checks

- Rank 1 in 2569 Total: `5 EV` / `JAECOO`, 2569 Total = `11,137`.
- Rank 2 in 2569 Total: `BYD DOLPHIN` / `BYD`, 2569 Total = `8,696`.
- Rank 3 in 2569 Total: `BYD ATTO 3` / `BYD`, 2569 Total = `7,357`.

### Validation Checks

- CHECK: Top 10 model ranks match markdown exactly.
- CHECK: No non-BEV-Major model appears in the ranking.

## Sheet 9 — by Province

### Data Rules

- Source: `backend/test_fuel_cleaned.parquet`.
- Filter:
  - `ประเภทรถ` = multiple items, expected to be the same canonical vehicle set unless workbook proves otherwise.
- Rows are grouped hierarchically:
  - Province row
  - Brand rows under each province
- Columns:
  - 2568 Jan-Dec + 2568 Total
  - 2569 Jan-Jun + 2569 Total
  - Overall total
- Province row MUST equal sum of child brand rows.

### Markdown Known Checks

- กรุงเทพมหานคร overall total = `559,073`.
- กรุงเทพมหานคร 2568 Total = `343,684`.
- กรุงเทพมหานคร 2569 Total = `215,389`.

### Validation Checks

- CHECK: Each province total equals sum of child brand totals.
- CHECK: National province totals reconcile to the same filtered source total used by sheets 1–6.

## Required Program Behavior

- The web program MUST clearly distinguish:
  - fuel-derived powertrain (`PT`, used for brand/powertrain pages)
  - model-table powertrain (`Powertrain`, used for BEV Major model pages)
- The UI MUST expose when a page is showing:
  - all public vehicle types
  - markdown default vehicle types only
  - BEV fuel-derived data
  - BEV Major model-table data
- Exported JSON MUST include enough metadata to verify which source and filter generated each table.

## Validation Gate

Add a deterministic validator that accepts the markdown path:

```powershell
py -3.12 backend\validate_against_markdown.py "C:\Users\georg\Downloads\รถใหม่_มิถุนายน 2569 (2)_sheets1-9.md"
```

The validator MUST:

1. Parse sheets 1–9 from markdown tables.
2. Recompute the same tables from parquet/JSON.
3. Compare selected golden cells first, then expand to full table equality.
4. Fail with a clear message showing:
   - sheet name
   - row key
   - column key
   - markdown value
   - program value
   - source file used

## Open Questions

- The markdown shows Sheet 7 BYD 2568 Total = `33,077`, while the current fuel-derived brand export gives `33,070` and strict model-table BEV Major gives a different sum. Confirm whether the markdown was exported from a newer workbook, a manual adjustment, or a different model mapping.
- Confirm whether Sheet 9 uses the same vehicle type filter `รย.1,2,3,6,9,10,11` or a broader “Multiple Items” filter.
- Confirm whether the public UI should default to markdown parity mode or offer it as a toggle separate from “all vehicle types”.
