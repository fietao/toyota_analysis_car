IMPLEMENTATION NOTE: Read this spec completely before writing any code.
After each section is implemented, tick the verification check for that section.

# Masttercal Workbook Specification

## Goal
Document the structure, layout, and formulas of the `202605_รถใหม่_ยี่ห้อรถ-ชนิดเชื้อเพลิง-จังหวัด ปี 2564 - พฤษภาคม 2569(masttercal).xlsx` workbook. This workbook contains 12 sheets focusing on overall brand and powertrain ranking analytics over a ~221K row dataset.

## Scope
The workbook contains 12 sheets:
1. `1.Reg by Powertrain` - Total registrations grouped by Powertrain.
2. `2.Rank by Brand` - Registration rankings across all brands.
3. `3.ICE by Brand` - Internal Combustion Engine (ICE) vehicle registrations by brand.
4. `4.BEV by Brand` - Battery Electric Vehicle (BEV) registrations by brand.
5. `6.PHEV by Brand` - Plug-in Hybrid Electric Vehicle (PHEV) registrations by brand.
6. `7.BEV by Model` - Major BEV brand registrations by model.
7. `5.HEV by Brand` - Hybrid Electric Vehicle (HEV) registrations by brand.
8. `8.Rank by BEV Model` - Rankings of BEV models.
9. `Pivot` - A backend Pivot table summarizing data.
10. `Data` - Raw dataset (221,492 rows).
11. `master powertrain` - Mapping table for fuel types to powertrain categories.
12. `BEV Series Name Table` - Mapping table for BEV series and models.

## Inputs
**Data Source:** `Data` sheet
- Contains 221,492 rows and 16 columns.
- Key Columns: 
  - A: `ปี` (Year)
  - B: `เดือน` (Month)
  - C: `ประเภทรถ` (Vehicle Type)
  - F: `ยี่ห้อรถ2` (Brand cleaned)
  - I: `Powertrain` (e.g., ICE, BEV, OTH)
  - J: `จำนวนรถ` (Units)
  - O: `Brand1`
  - P: `Brand2`

**Mapping Sources:** 
- `master powertrain`: Maps `ชนิดเชื้อเพลิง` (Fuel Type) to `Powertrain` (e.g., CNG -> ICE).
- `BEV Series Name Table`: Maps `รุ่นรถ` (Model) to cleaned `รุ่นรถ2` and `Powertrain` = BEV.

## Output Sheet(s)
All output sheets (1 through 8) are pivot-table-like reports.

## Data Rules

### Sheet 1: `1.Reg by Powertrain`
- **Output:** Powertrain vs. Months (Jan-May 2568 vs 2569).
- **Layout:** 
  - Row 5: Powertrain | 2568 | 2569 | 2568 vs 2569 | Forecast 2026
  - Row 8: Grand Total row at the top.
  - Rows 9+: Data rows (ICE, BEV, etc.)

### Sheet 3/4/5/7: `[Powertrain] by Brand`
- **Output:** Monthly registrations for specific powertrains (ICE, BEV, PHEV, HEV) grouped by Brand.
- **Filters:** 
  - Powertrain filter applies strictly per sheet (e.g., `Powertrain : BEV`).
- **Layout:**
  - Row 7: Brand | 2568 | 2569 | Rank
  - Columns include monthly `Units` and `Share`, plus `Diff` and `Growth`.

### Sheet 6/8: `BEV by Model`
- **Output:** BEV registrations grouped by Brand/Model.
- **Filters:** Powertrain = `BEV Major`
- **Columns:** Similar monthly breakout and ranking/growth calculations.

## Layout And Formatting
- **Header Rows:** Typically rows 1 through 7 contain titles, filters, and complex multi-row headers.
- **Grand Total:** Placed at row 8 or 10 depending on the sheet. It MUST calculate totals for all subsequent data rows.
- **Growth/Share:** Represented as decimals (e.g., `0.524` for 52.4%), formatted as percentages in Excel.

## Filters And Interactions
- Filter labels are usually found in Row 3 and Row 4.
- `Powertrain` filter MUST be respected on all powertrain-specific sheets.

## Validation Checks
- [ ] CHECK: Sheet `1.Reg by Powertrain` exists and has headers in row 5.
- [ ] CHECK: Sheet `4.BEV by Brand` filters strictly by Powertrain = BEV.
- [ ] CHECK: `Data` sheet row count matches ~221,492 rows.
- [ ] CHECK: Grand Totals reconcile correctly to the underlying `Data` table.

## Open Questions
- Should the output be generated as actual Excel PivotTables or static tables mimicking PivotTable layouts?
- Are there specific color hex codes required for the headers from the reference file?
