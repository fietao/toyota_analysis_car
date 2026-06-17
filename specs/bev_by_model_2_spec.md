# Spreadsheet Specification: BEV by Model (2)

This specification defines the requirements for generating the **BEV by Model (2)** sheet in the car analysis workbook.

---

## Goal
To present registration counts of Battery Electric Vehicles (BEV) classified under the `BEV Major` powertrain category in a flat list format, showing the model series (รุ่นรถ2) and brand (ยี่ห้อรถ2) side-by-side, broken down by year, month, and totals for the last 2 years (2568 and 2569).

## Scope
* **Source Workbook**: `refer/202605_รถใหม่_ยี่ห้อรถ-ชนิดเชื้อเพลิง-จังหวัด ปี 2564 - พฤษภาคม 2569 - Model.xlsx`
* **Output Sheet**: `BEV by Model (2)` (Flat list format, ~82 rows)

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

## Layout and Formatting

* **Header Style (`fmt_h`):** Bold text, background color `#4472C4`, white text color, thin borders, centered alignment. Applied to all header rows (Rows 6 and 7).
* **Data Style:** Standard/regular font with normal row heights.
* **Auto-Filter:** Enabled for the range `A7:V82` (covering the header row 7 down to the last data row, from Column A to Column V).

### Cell-by-Cell Grid Reference

* **Filters Area:**
  * `A1`: `ประเภทรถ` | `B1`: `(Multiple Items)`
  * `A2`: `จังหวัด` | `B2`: `(All)`
  * `A3`: `Powertrain` | `B3`: `BEV Major`

* **Header Area (Row 5):**
  * `A5`: `Sum of จำนวนรถ`
  * `C5`: `ปี`
  * `D5`: `เดือน`

* **Year Label Row (Row 6):**
  * `C6`: `2568` (spans Columns C to N)
  * `O6`: `2568 Total`
  * `P6`: `2569` (spans Columns P to T)
  * `U6`: `2569 Total`
  * `V6`: `Grand Total`

* **Month & Label Row (Row 7):**
  * `A7`: `รุ่นรถ2` (Model series column header)
  * `B7`: `ยี่ห้อรถ2` (Brand column header)
  * `C7:N7`: Thai months for 2568 (`มกราคม`, `กุมภาพันธ์`, `มีนาคม`, `เมษายน`, `พฤษภาคม`, `มิถุนายน`, `กรกฎาคม`, `สิงหาคม`, `กันยายน`, `ตุลาคม`, `พฤศจิกายน`, `ธันวาคม`)
  * `O7`: Blank (matches `2568 Total` vertical alignment)
  * `P7:T7`: Thai months for 2569 (`มกราคม`, `กุมภาพันธ์`, `มีนาคม`, `เมษายน`, `พฤษภาคม`)
  * `U7`: Blank (matches `2569 Total` vertical alignment)
  * `V7`: Blank (matches `Grand Total` vertical alignment)

* **Data Rows (Row 8 to 82):**
  * **Column A:** `รุ่นรถ2` (e.g. `5 EV`, `BYD DOLPHIN`, `BYD ATTO 3`)
  * **Column B:** `ยี่ห้อรถ2` (e.g. `JAECOO`, `BYD`, `BYD`)
  * **Columns C to N:** Registration counts for 2568 months.
  * **Column O:** `2568 Total` (yearly sum for the model)
  * **Columns P to T:** Registration counts for 2569 months.
  * **Column U:** `2569 Total` (yearly sum for the model)
  * **Column V:** `Grand Total` (sum of 2568 and 2569 totals for the model)

---

## Data Rules & Calculations

### Filters
* **ประเภทรถ**: `(Multiple Items)` indicating filtering to specific passenger-type/common vehicle types.
* **จังหวัด**: `(All)` indicating all provinces are aggregated.
* **Powertrain**: Locked to `BEV Major`.

### Transformations
* **Pivot aggregation**: The `จำนวนรถ` values are grouped and summed by `[รุ่นรถ2, ยี่ห้อรถ2, ปี, เดือน]`.
* **Zero values**: Any month/total cell with a count of 0 is written as empty/blank (None) to match typical pivot table defaults.

### Year Totals and Grand Totals
* **Year Total** (`2568 Total`, `2569 Total`): Sum of the registration numbers for all active months of that year for the specific model row.
* **Grand Total**: Sum of registration numbers across both years (`2568` + `2569`) for the specific model row.

---

## Sorting and Grouping
* **Flat Row Order**: Unliked the hierarchical version, there is no brand grouping. All model series rows are flat.
* **Sorting**: Sorted in descending order of their `Grand Total` registration count (Column V).

---

## Validation Checks
To verify the correctness of the generated sheet, the following checks must pass:
1. **Sheet Name**: Sheet `BEV by Model (2)` must exist in the workbook.
2. **Filter Headers**: Cells `A1:B3` must contain `ประเภทรถ`, `จังหวัด`, and `Powertrain` with their corresponding filter labels.
3. **Data Columns**:
   * The years `2568` and `2569` must align with the correct month columns.
   * Column headers in Row 7 must match model and brand labels in A and B, followed by month names in C to T.
4. **Totals Reconciliation**:
   * For any row, the sum of Columns C to N must equal `2568 Total` (Column O).
   * For any row, the sum of Columns P to T must equal `2569 Total` (Column U).
   * For any row, Column O + Column U must equal `Grand Total` (Column V).
5. **Cross-Sheet Reconciliation**:
   * The sum of all model grand totals on this sheet must reconcile exactly with the sum of all brand parent grand totals in the hierarchical `BEV by Model` sheet.

---

## Open Questions
* **Filter Values**: Are there specific `ประเภทรถ` values excluded from the pivot, or does `(Multiple Items)` reflect a standard subset? (Implementation script currently defaults to filtering out fuel-only rows by checking `df["รุ่นรถ"].notna()`).
