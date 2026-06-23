IMPLEMENTATION NOTE: Read this spec completely before writing any code.
After each section is implemented, tick the verification check for that section.

# Modelmain Workbook Specification

## Goal
Document the structure and layout of the `202605_รถใหม่_ยี่ห้อรถ-ชนิดเชื้อเพลิง-จังหวัด ปี 2564 - พฤษภาคม 2569 - (master)Modelmain.xlsx` workbook. This 57 MB workbook contains the massive 636K row dataset and focuses heavily on BEV model analysis and BMW-specific tracking.

## Scope
The workbook contains 6 sheets:
1. `BEV by Model` - Registration totals grouped by Brand and specific Model.
2. `BEV by Model (2)` - Detailed BEV tracking mapping models to specific brands and counts.
3. `BMW` - Deep dive into BMW model registrations (e.g., X1, 320d, X3).
4. `BEV Series Name Table` - Mapping table matching full series names to abbreviated series and powertrains.
5. `Data` - Massive 636,340 row raw dataset.
6. `master powertrain` - Mapping table from fuel/hybrid types to ICE/BEV categories.

## Inputs
**Data Source:** `Data` sheet
- Contains 636,340 rows and 15 columns.
- Key Columns: 
  - A: Year (`ปี`)
  - B: Month (`เดือน`)
  - G: Raw Model (`รุ่นรถ`)
  - H: Cleaned Model (`รุ่นรถ2`)
  - I: Powertrain
  - J: Units (`จำนวนรถ`)
  - N: Brand1
  - O: Brand2

**Mapping Sources:** 
- `BEV Series Name Table`: Massive lookup table (31,905 rows). Key columns: `Brand` (A), `รุ่นรถ` (B), `รุ่นรถ2` (C), `Powertrain` (D).
- `master powertrain`: Maps complex fuel combinations (e.g., `CNG-LPG`, `CNG-ดีเซล`) to `Powertrain` = `ICE`.

## Output Sheet(s)

### Sheet 1 & 2: `BEV by Model`
- **Output:** Pivot-style aggregations of BEV registrations grouped by Brand -> Model.
- **Filters:** 
  - `Powertrain` MUST be set to `BEV Major` or `(Multiple Items)` depending on the sheet.
- **Layout:**
  - Row 8+: Data rows where Column A represents the Brand (e.g., `BYD`), followed by sub-rows for Models (e.g., `BYD DOLPHIN`).
  - Columns contain monthly aggregation from 2568 to 2569.

### Sheet 3: `BMW`
- **Output:** BMW-specific registrations broken down by model configuration (e.g., `X1 sDrive20i M Sport`).
- **Filters:** Implicitly filtered for Brand = `BMW`.
- **Layout:** 
  - Row 7: Headers matching month-over-month comparisons between 2568 and 2569.

## Data Rules
- The `Data` sheet represents the un-filtered universe of all registrations across Thailand.
- The `BEV Series Name Table` is required to clean messy raw models (e.g., normalizing `AION Y PLUS 410 PREMIUM` to simply `AION Y`).
- Grand Totals MUST accurately roll up unit counts across the millions of aggregated cell boundaries without hard-coding static values.

## Layout And Formatting
- Reports are structured as dense tables with months spanned horizontally across multiple years (2568/2569).
- The top 6 rows of reporting sheets act as metadata/filter rows. Row 7 acts as the start of the data columns header.

## Validation Checks
- [ ] CHECK: `Data` sheet row count matches ~636,340 rows.
- [ ] CHECK: `BEV Series Name Table` contains ~31,905 mapping entries.
- [ ] CHECK: Sheet `BMW` exists and contains model variants like `X1 sDrive20i M Sport`.
- [ ] CHECK: Master powertrain properly remaps minor fuels (like `CNG-LPG`) to `ICE`.

## Open Questions
- Is there a specific sort order required for the models inside the `BEV by Model` pivot table?
- Should the `Data` sheet be exported exactly as-is, or filtered down during processing?
