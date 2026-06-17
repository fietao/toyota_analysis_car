# Spreadsheet Specification: BEV by Model Sheets

This specification defines the requirements for generating the **BEV by Model** sheets in the car analysis workbook. The workbook contains two versions of this sheet, sharing the same source data and filters but displaying different layout structures:
1. **BEV by Model**: A hierarchical (grouped) pivot-like table where brand (ยี่ห้อรถ2) acts as the parent row and model series (รุ่นรถ2) are nested under their respective brand.
2. **BEV by Model (2)**: A flat pivot-like table where each row displays the model series (รุ่นรถ2) and brand (ยี่ห้อรถ2) side-by-side in separate columns.

---

## Goal
To present registration counts of Battery Electric Vehicles (BEV) classified under the `BEV Major` powertrain category, broken down by year, month, brand, and model series for the last 2 years (2568 and 2569).

## Scope
* **Source Workbook**: `refer/202605_รถใหม่_ยี่ห้อรถ-ชนิดเชื้อเพลิง-จังหวัด ปี 2564 - พฤษภาคม 2569 - Model.xlsx`
* **Output Sheets**: 
  * `BEV by Model` (Hierarchical structure, ~110 rows)
  * `BEV by Model (2)` (Flat structure, ~82 rows)

---

## Inputs
1. **Cleaned Data Sheet (`Data`):**
   * Contains normalized vehicle registration records.
   * Key columns used:
     * `ปี` (Year: 2568, 2569)
     * `เดือน` (Month in Thai)
     * `ประเภทรถ` (Vehicle category)
     * `จังหวัด` (Province)
     * `ยี่ห้อรถ2` (Normalized Brand name)
     * `รุ่นรถ2` (Normalized Model series)
     * `Powertrain` (Powertrain category)
     * `จำนวนรถ` (Registration count)
   * Only rows where model details exist (`รุ่นรถ` is not null/blank) and `Powertrain` is equal to `BEV Major` are included.

---

## Output Sheets Structure

### 1. `BEV by Model` (Hierarchical Grouped Layout)
A grouped pivot-like structure where each brand has a summary header row, followed by its model series.

#### Layout and Formatting
* **Header Style (`fmt_h`):** Bold text, background color `#4472C4`, white text color, thin borders, centered alignment. Applied to Column headers (Row 7) and Brand parent rows.
* **Column widths:** Automatically sized or matching template defaults.
* **Auto-Filter:** Enabled from A7 to the last column and row (`A7:U110`).

#### Row-by-Row Layout Detail
* **Row 1:** 
  * `A1`: `ประเภทรถ`
  * `B1`: `(Multiple Items)` (Filter value)
* **Row 2:** 
  * `A2`: `จังหวัด`
  * `B2`: `(All)` (Filter value)
* **Row 3:** 
  * `A3`: `Powertrain`
  * `B3`: `BEV Major` (Filter value)
* **Row 5:** 
  * `A5`: `Sum of จำนวนรถ`
  * `B5`: `Column Labels`
* **Row 6 (Year Labels):**
  * `B6`: `2568`
  * `N6`: `2568 Total`
  * `O6`: `2569`
  * `T6`: `2569 Total`
  * `U6`: `Grand Total`
* **Row 7 (Month & Column Headers):**
  * `A7`: `Row Labels` (Header for brand/model names)
  * `B7:M7`: Thai months for 2568 (`มกราคม` to `ธันวาคม`)
  * `N7`: Blank (corresponds to `2568 Total` in Row 6)
  * `O7:S7`: Thai months for 2569 (`มกราคม` to `พฤษภาคม` or active months)
  * `T7`: Blank (corresponds to `2569 Total` in Row 6)
  * `U7`: Blank (corresponds to `Grand Total` in Row 6)
* **Row 8+ (Data Rows):**
  * Brand Parent Row (e.g., `BYD` in `A8`): Styled with `fmt_h`. Contains monthly sums and totals for that brand.
  * Model Child Rows (e.g., `BYD DOLPHIN` in `A9`): Regular font. Contains monthly counts and totals for that model series.

---

### 2. `BEV by Model (2)` (Flat Layout)
A flat pivot-like list where model and brand are placed side-by-side in separate columns.

#### Layout and Formatting
* **Header Style (`fmt_h`):** Bold text, background color `#4472C4`, white text color, thin borders, centered alignment. Applied to Column headers (Row 7).
* **Auto-Filter:** Enabled from A7 to the last column and row (`A7:V82`).

#### Row-by-Row Layout Detail
* **Row 1:** 
  * `A1`: `ประเภทรถ`
  * `B1`: `(Multiple Items)`
* **Row 2:** 
  * `A2`: `จังหวัด`
  * `B2`: `(All)`
* **Row 3:** 
  * `A3`: `Powertrain`
  * `B3`: `BEV Major`
* **Row 5:** 
  * `A5`: `Sum of จำนวนรถ`
  * `C5`: `ปี`
  * `D5`: `เดือน`
* **Row 6 (Year Labels):**
  * `C6`: `2568`
  * `O6`: `2568 Total`
  * `P6`: `2569`
  * `U6`: `2569 Total`
  * `V6`: `Grand Total`
* **Row 7 (Column Headers):**
  * `A7`: `รุ่นรถ2` (Model series)
  * `B7`: `ยี่ห้อรถ2` (Brand)
  * `C7:N7`: Thai months for 2568 (`มกราคม` to `ธันวาคม`)
  * `O7`: Blank (corresponds to `2568 Total` in Row 6)
  * `P7:T7`: Thai months for 2569 (`มกราคม` to `พฤษภาคม`)
  * `U7`: Blank (corresponds to `2569 Total` in Row 6)
  * `V7`: Blank (corresponds to `Grand Total` in Row 6)
* **Row 8+ (Data Rows):**
  * Flat rows displaying `รุ่นรถ2` in Column A and `ยี่ห้อรถ2` in Column B. All cells are standard formatting.

---

## Data Rules & Calculations

### Filters
* **ประเภทรถ**: `(Multiple Items)` indicates that the sheet data is filtered to include only specific passenger-type/common vehicle types.
* **จังหวัด**: `(All)` indicating no provincial filter is applied (summed over all provinces).
* **Powertrain**: Locked to `BEV Major`.

### Transformations
* **Pivot aggregation**: The `จำนวนรถ` values are grouped and summed by `[ยี่ห้อรถ2, รุ่นรถ2, ปี, เดือน]`.
* **Zero values**: Any month/total cell with a count of 0 is written as empty/blank (None) to match typical pivot table defaults.

### Year Totals and Grand Totals
* **Year Total** (`2568 Total`, `2569 Total`): Sum of the registration numbers for all active months of that year for the specific row.
* **Grand Total**: Sum of registration numbers across both years (`2568` + `2569`) for the specific row.

---

## Sorting and Grouping

### 1. `BEV by Model` (Hierarchical)
1. **Brand order**: Brands are sorted in descending order of their overall `Grand Total` registration count.
2. **Model order**: Under each brand, model series are sorted in descending order of their individual `Grand Total` registration count.

### 2. `BEV by Model (2)` (Flat)
1. Flat model series rows are sorted in descending order of their `Grand Total` registration count.

---

## Validation Checks
To verify the correctness of the generated sheets, the following checks must pass:
1. **Sheet Names**: Sheets `BEV by Model` and `BEV by Model (2)` must exist in the workbook.
2. **Filter Headers**:
   * Cells `A1:B3` must contain `ประเภทรถ`, `จังหวัด`, and `Powertrain` with their corresponding filter labels.
3. **Data Columns**:
   * The years `2568` and `2569` must align with the correct month columns.
   * Active month columns for `2569` must cover `มกราคม` to `พฤษภาคม`.
4. **Totals Reconciliation**:
   * For any row, the sum of month columns for 2568 must equal `2568 Total`.
   * For any row, the sum of month columns for 2569 must equal `2569 Total`.
   * For any row, `2568 Total` + `2569 Total` must equal `Grand Total`.
5. **Grand Totals Reconciliation**:
   * The sum of all brand parent totals in `BEV by Model` must equal the sum of all model totals in `BEV by Model (2)`.
   * These totals must reconcile exactly with the sum of `จำนวนรถ` in the `Data` sheet where `Powertrain == "BEV Major"` and `รุ่นรถ` is not null.

---

## Open Questions
* **Filter Values**: Are there specific `ประเภทรถ` values excluded from the pivot, or does `(Multiple Items)` reflect a standard subset? (Implementation script currently defaults to filtering out fuel-only rows by checking `df["รุ่นรถ"].notna()`).
