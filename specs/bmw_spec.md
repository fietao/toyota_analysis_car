# Spreadsheet Specification: BMW

This specification defines the requirements for generating the **BMW** sheet in the car analysis workbook.

---

## Goal
To present registration counts of all BMW model series, broken down by year, month, and totals, using a compressed year layout where prior years are shown only as yearly totals, and only the current year (2569) is expanded to show monthly counts.

## Scope
* **Source Workbook**: `refer/202605_รถใหม่_ยี่ห้อรถ-ชนิดเชื้อเพลิง-จังหวัด ปี 2564 - พฤษภาคม 2569 - Model.xlsx`
* **Output Sheet**: `BMW` (Flat list with compressed columns format, ~126 rows)

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
     * `จำนวนรถ` (Registration count)
   * Only rows where the brand `ยี่ห้อรถ2` is equal to `BMW` and model details exist (`รุ่นรถ` is not null/blank) are included.
   * Powertrain filter is NOT applied (includes all powertrains like ICE, HEV, PHEV, BEV).

---

## Layout and Formatting

* **Header Style (`fmt_h`):** Bold text, background color `#4472C4`, white text color, thin borders, centered alignment. Applied to all header rows (Rows 6 and 7).
* **Data Style:** Standard/regular font with normal row heights.
* **Auto-Filter:** Enabled for the range `A7:J126` (covering the header row 7 down to the last data row, from Column A to Column J).

### Cell-by-Cell Grid Reference

* **Filters Area:**
  * `A1`: `ประเภทรถ` | `B1`: `(Multiple Items)`
  * `A2`: `จังหวัด` | `B2`: `(All)`
  * `A3`: `Powertrain` | `B3`: `(All)`

* **Header Area (Row 5):**
  * `A5`: `Sum of จำนวนรถ`
  * `C5`: `ปี`
  * `D5`: `เดือน`

* **Year Label Row (Row 6):**
  * `C6`: `2568` (Single column representing the entire year total)
  * `D6`: `2569` (Spans Columns D to H for months)
  * `I6`: `2569 Total`
  * `J6`: `Grand Total`

* **Month & Label Row (Row 7):**
  * `A7`: `ยี่ห้อรถ2` (Brand column header)
  * `B7`: `รุ่นรถ2` (Model series column header)
  * `C7`: Blank (corresponds to `2568` total column)
  * `D7:H7`: Thai months for 2569 (`มกราคม`, `กุมภาพันธ์`, `มีนาคม`, `เมษายน`, `พฤษภาคม`)
  * `I7`: Blank (corresponds to `2569 Total` in Row 6)
  * `J7`: Blank (corresponds to `Grand Total` in Row 6)

* **Data Rows (Row 8 to 126):**
  * **Column A:** `ยี่ห้อรถ2` (Always `BMW` or empty cell for merged row if applicable, but implementation script writes `BMW` to each row in Col A).
  * **Column B:** `รุ่นรถ2` (e.g. `X1 sDrive20i M Sport`, `320d M Sport`)
  * **Column C:** `2568` registration total (all 12 months summed).
  * **Columns D to H:** Registration counts for individual months of 2569 (Jan to May).
  * **Column I:** `2569 Total` (sum of Jan to May 2569).
  * **Column J:** `Grand Total` (Column C + Column I).

---

## Data Rules & Calculations

### Filters
* **ประเภทรถ**: `(Multiple Items)` indicating filtering to specific passenger-type/common vehicle types.
* **จังหวัด**: `(All)` indicating all provinces are aggregated.
* **Powertrain**: `(All)` (includes ICE, PHEV, HEV, BEV).

### Transformations
* **Pivot aggregation**: The `จำนวนรถ` values are grouped and summed by `[ยี่ห้อรถ2, รุ่นรถ2, ปี, เดือน]`.
* **Column Compression**: 
  * Prior year (2568) values are aggregated into a single year total column (Column C).
  * Current year (2569) is split into monthly columns (Columns D-H) and a year total column (Column I).
* **Zero values**: Any month/total cell with a count of 0 is written as empty/blank (None) to match typical pivot table defaults.

---

## Sorting and Grouping
* **Flat Row Order**: Shows all BMW models in a flat table layout.
* **Sorting**: Sorted in descending order of their `Grand Total` registration count (Column J).

---

## Validation Checks
To verify the correctness of the generated sheet, the following checks must pass:
1. **Sheet Name**: Sheet `BMW` must exist in the workbook.
2. **Filter Headers**: Cells `A1:B3` must contain `ประเภทรถ`, `จังหวัด`, and `Powertrain` with their corresponding filter labels.
3. **Data Columns**:
   * Column C must contain the total counts for year 2568.
   * Month headers in D7 to H7 must cover `มกราคม` to `พฤษภาคม` for year 2569.
4. **Totals Reconciliation**:
   * For any row, the sum of Columns D to H must equal `2569 Total` (Column I).
   * For any row, Column C + Column I must equal `Grand Total` (Column J).
5. **Brand Validation**:
   * Column A must contain `BMW` for all rows.
   * The sum of `Grand Total` on the `BMW` sheet must equal the sum of `จำนวนรถ` in the cleaned `Data` sheet where `ยี่ห้อรถ2 == "BMW"` and `รุ่นรถ` is not null.
