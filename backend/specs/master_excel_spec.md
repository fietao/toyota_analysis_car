IMPLEMENTATION NOTE: Read this spec completely before writing any code.
After each section is implemented, tick the verification check for that section.

---

# Master Excel Workbooks — Draft Spec

**Purpose:** Reverse-engineer the two existing master Excel files so the team can decide whether to keep Excel as the pipeline output format or switch to a web dashboard / fresh generated report.

**Status:** Draft — open questions at bottom must be resolved before implementation.

---

## Scope

Two workbooks inspected:

| Alias | Filename | Role |
|---|---|---|
| `modelmain` | `202605_...(master)Modelmain.xlsx` | BEV-focused analysis + raw Data sheet |
| `mastercal` | `202605_...(masttercal).xlsx` | Full powertrain breakdown analysis (ICE/BEV/HEV/PHEV) + raw Data sheet |

---

## Inputs

| Source | Description |
|---|---|
| DLT raw model file | Monthly car registration by model, year, month, province, fuel type |
| DLT raw fuel file | Fuel type lookup (ชนิดเชื้อเพลิง) |
| `BEV Series Name Table` | Brand/model → รุ่นรถ2/Powertrain mapping (manual, maintained by boss) |
| `master powertrain` sheet | ชนิดเชื้อเพลิง → Powertrain mapping (32-row lookup) |

---

## Workbook 1 — modelmain (master Model)

### Sheet Inventory

| Sheet | Type | Description |
|---|---|---|
| `Data` | Flat table | 636,340 rows of cleaned registration data. PRIMARY DATA SOURCE for pivots. |
| `BEV by Model` | Excel Pivot | BEV brand totals by month, filtered to BEV Major Powertrain |
| `BEV by Model (2)` | Excel Pivot | BEV by รุ่นรถ2 + ยี่ห้อรถ2, wider filter set |
| `BMW` | Excel Pivot | BMW brand/model breakdown by month + year total + Grand Total |
| `BEV Series Name Table` | Flat table | 31,905 rows: Brand / รุ่นรถ / รุ่นรถ2 / Powertrain. Manual reference. |
| `master powertrain` | Excel Pivot | ชนิดเชื้อเพลิง → Powertrain mapping with totals. Manual reference. |
| `Detail1` | Drilldown | Auto-generated pivot drilldown, usually empty (3 rows) |
| `Detail2` | Drilldown | Auto-generated pivot drilldown, usually empty (3 rows) |

### Data Sheet — modelmain

- **Header row:** R7
- **Data starts:** R8
- **Row count:** ~636,340 (grows monthly)
- **Key columns (A→J):**

| Col | Header | Example |
|---|---|---|
| A | ปี | 2564 |
| B | เดือน | มกราคม |
| C | ประเภทรถ | รย.1 รถยนต์นั่งส่วนบุคคล |
| D | จังหวัด | กรุงเทพมหานคร |
| E | ยี่ห้อรถ | ASTON MARTIN |
| F | ยี่ห้อรถ2 | ASTON MARTIN |
| G | รุ่นรถ | V8 VANTAGE COUPE |
| H | รุ่นรถ2 | V8 VANTAGE COUPE |
| I | Powertrain | OTH |
| J | จำนวนรถ | 1 |

**⚠ BUG B2 CONFIRMED:** `ชนิดเชื้อเพลิง` column is MISSING from this Data sheet. mastercal Data sheet has it (col G). This breaks the `master powertrain` pivot (pivot row field = ชนิดเชื้อเพลิง → goes blank).

- **Rows 1–5:** Title block (Thai header text, date, unit, notes). Not part of data.
- **Rows K–O:** Empty or unused columns up to max_column=15.

### BEV by Model Pivot

- **Pivot filters (R1–R3):** ประเภทรถ=(Multiple Items), จังหวัด=(All), Powertrain=BEV Major
- **Column structure:** R5=label row, R6=year (2568), R7=month names (Thai), R8+=brand rows
- **Row field:** Brand (ยี่ห้อรถ2 or similar)
- **Value:** Sum of จำนวนรถ

### BMW Pivot

- **Filters (R1–R3):** ประเภทรถ=(Multiple Items), จังหวัด=(All), Powertrain=(Multiple Items)
- **Column structure:** R5 label, R6=year, R7=month + year-total + Grand Total columns
- **Row fields:** ยี่ห้อรถ2, รุ่นรถ2

### master powertrain

- **Layout:** Pivot table starting at R6. Header at R7.
- **Columns:** ชนิดเชื้อเพลิง | Powertrain | Total | (blank) | ชนิดเชื้อเพลิง | Powertrain
- **Rows:** R8–R39 (32 mapping rows)
- **MUST NOT be written by Python** (read-only reference, boss maintains manually)

---

## Workbook 2 — mastercal (master cal)

### Sheet Inventory

| Sheet | Type | Description |
|---|---|---|
| `Data` | Flat table | 221,492 rows of cleaned data. Includes ชนิดเชื้อเพลิง column (col G). |
| `1.Reg by Powertrain` | Analysis table | Summary: all powertrains by month, Units + Share columns |
| `2.Rank by Brand` | Analysis pivot | All brands ranked by monthly Units + Share |
| `3.ICE by Brand` | Analysis pivot | ICE only, brand × month |
| `4.BEV by Brand` | Analysis pivot | BEV only, brand × month |
| `5.HEV by Brand` | Analysis pivot | HEV only, brand × month |
| `6.PHEV by Brand` | Analysis pivot | PHEV only, brand × month |
| `7.BEV by Model` | Analysis pivot | BEV Major only, brand/model × month |
| `8.Rank by BEV Model` | Analysis pivot | BEV Major models ranked, with Share |
| `Pivot` | Simple pivot | Powertrain × month summary (11 rows) |
| `master powertrain` | Pivot | Same ชนิดเชื้อเพลิง → Powertrain mapping as modelmain |
| `BEV Series Name Table` | Flat table | 31,926 rows: Brand / รุ่นรถ / รุ่นรถ2 / Powertrain |

### Data Sheet — mastercal

- **Header row:** R6 (one row earlier than modelmain)
- **Data starts:** R7
- **Row count:** ~221,492
- **Key columns (A→I):**

| Col | Header | Example |
|---|---|---|
| A | ปี | 2564 |
| B | เดือน | มกราคม |
| C | ประเภทรถ | รย.1 รถยนต์นั่งส่วนบุคคล |
| D | จังหวัด | กรุงเทพมหานคร |
| E | ยี่ห้อรถ | ASTON MARTIN |
| F | ยี่ห้อรถ2 | ASTON MARTIN |
| G | **ชนิดเชื้อเพลิง** | เบนซิน ← **present here, missing from modelmain** |
| H | Powertrain | ICE |
| I | จำนวนรถ | 2 |

### Analysis Sheet Pattern (sheets 1–8)

All analysis sheets follow this layout pattern:

```
R1:  Title text (e.g. "Registration by Powertrain")
R3:  Filter label: ประเภทรถ → (Multiple Items) or specific value
R4:  Filter label: Powertrain → (All) or specific value (ICE/BEV/HEV/PHEV)
R5:  Column group label (e.g. "2568" spanning monthly columns)
R6:  Sub-label (e.g. "May", "Jan-May")
R7:  Row headers + column headers: Brand/Model, then Jan/Feb/.../May, Share, Jan-May, Share, Jun...
R8:  Grand Total row
R9+: Data rows (brands or models)
```

**Units + Share pattern:** Each month has a `Units` column immediately followed by a `Share` column (ratio 0–1, e.g. 0.5242). Year-to-date subtotals (`Jan-May`) appear as a group with Units + Share.

### Pivot Sheet (mastercal)

Simple 11-row pivot: Powertrain (ICE/BEV/HEV/PHEV/N/A) × month columns (Thai month names). Header at R6, data R7–R11.

---

## Key Structural Differences Between the Two Workbooks

| Feature | modelmain | mastercal |
|---|---|---|
| Data header row | R7 | R6 |
| Has ชนิดเชื้อเพลิง col | NO (Bug B2) | YES (col G) |
| Focus | BEV deep-dive + BMW | Full powertrain breakdown |
| Analysis sheets | 3 pivots (BEV focus) | 8 numbered analysis sheets |
| Pivot source | Data sheet | Data sheet |

---

## Filters and Interactions

All pivot and analysis sheets use Excel slicer-style filter labels in rows 1–4:

| Filter label | Location | Behavior |
|---|---|---|
| ประเภทรถ | R1 or R3 | (Multiple Items) = user selects car types; (All) = no filter |
| จังหวัด | R2 | (All) or (Multiple Items) |
| Powertrain | R3 or R4 | Specific value (BEV, ICE, etc.) or (All) |

These are Excel PivotTable report filters — not AutoFilter. Boss interacts with them via Excel's pivot filter UI.

---

## Data Rules

| Output column | Source | Transformation | Missing-value behavior |
|---|---|---|---|
| ยี่ห้อรถ2 | model2_map | Mapped from raw ยี่ห้อรถ | Keep raw if missing |
| รุ่นรถ2 | model2_map | Mapped from raw รุ่นรถ | Keep raw if missing |
| Powertrain | master powertrain / BEV Series Name Table | ชนิดเชื้อเพลิง → Powertrain | N/A if not in map |
| ชนิดเชื้อเพลิง | DLT fuel file | Direct join by year/month/province/brand | Blank if not joined |

---

## Validation Checks

- [ ] modelmain `Data` sheet header is at R7, col A = "ปี"
- [ ] mastercal `Data` sheet header is at R6, col A = "ปี"
- [ ] mastercal `Data` col G = "ชนิดเชื้อเพลิง"
- [ ] modelmain `Data` has NO ชนิดเชื้อเพลิง column (confirms B2)
- [ ] `BEV Series Name Table` row 1 headers: Brand | รุ่นรถ | รุ่นรถ2 | Powertrain
- [ ] `master powertrain` starts at R6, has exactly 32 data rows (R8–R39)
- [ ] mastercal analysis sheets follow R1/R3/R4/R7/R8 layout pattern
- [ ] Grand Total row exists in every analysis sheet at R8 or R9

---

## Open Questions

1. **Which sheets does the boss copy into PowerPoint?** The 8 analysis sheets in mastercal (1.Reg by Powertrain, 2.Rank by Brand, etc.) look like the presentation-ready ones — confirm this.
2. **Are the Excel PivotTables live (connected to Data sheet) or static values?** If live, Python must not touch the pivot sheets. If static, Python could regenerate them.
3. **Does the boss filter the pivots himself before copying to PowerPoint**, or are the default filter states (already set) what he uses?
4. **Is modelmain used for presentation, or only mastercal?** mastercal has the cleaner analysis sheets.
5. **Color formatting:** Not captured here — need visual inspection to get hex values for header fills, Grand Total rows, Share columns.
