# Sheet Structure Reference

Last updated: 2026-06-20

Two master Excel files. Python writes only the marked columns/rows.
Everything else (pivots, formatting, formulas) is owned by Excel.

---

## masterModel.xlsx

6 sheets total.

### Data ✍️ Python writes this
- Rows 1–5: Thai metadata text (title, date range, units, note) — preserved as-is
- Row 6: blank
- Row 7: column headers — `ปี | เดือน | ประเภทรถ | จังหวัด | ยี่ห้อรถ | ยี่ห้อรถ2 | รุ่นรถ | รุ่นรถ2 | ชนิดเชื้อเพลิง | Powertrain | จำนวนรถ`
- Row 8+: data rows (636,000+ rows)

### BEV Series Name Table ✍️ Python appends rows
- Row 1: header — `Brand | รุ่นรถ | รุ่นรถ2 | Powertrain`
- Row 2+: one row per known BEV model
- Python only appends new rows at the bottom (never rewrites existing rows)

### master powertrain ✍️ Python appends rows (cols E,F only)
- Rows 1–7: pivot table summary (left side, cols A-C) — DO NOT TOUCH
- Row 7: col E = `ชนิดเชื้อเพลิง`, col F = `Powertrain` (mapping table header)
- Row 8+: col E = fuel type string, col F = ICE / BEV / HEV / PHEV / N/A
- Python appends new fuel types here when DLT introduces new fuel categories

### BEV by Model 🔒 READ-ONLY pivot
- Pivot table: rows = model names, filtered by Powertrain
- Refreshes automatically when Excel opens the file
- Python must never write to this sheet

### BEV by Model (2) 🔒 READ-ONLY pivot
- Pivot table: rows = รุ่นรถ2 × ยี่ห้อรถ2, columns = ปี × เดือน (monthly counts)
- Python must never write to this sheet

### BMW 🔒 READ-ONLY pivot
- Pivot table: rows = ยี่ห้อรถ2 × รุ่นรถ2, columns = ปี × เดือน
- Python must never write to this sheet

---

## mastercal.xlsx (master cal)

12 sheets total. Python currently writes only Data.
The 8 analysis sheets (1–8) are the target for auto-generation.

### Data ✍️ Python writes this
- Rows 1–5: Thai metadata text — preserved as-is
- Row 6: column headers — `ปี | เดือน | ประเภทรถ | จังหวัด | ยี่ห้อรถ | ยี่ห้อรถ2 | ชนิดเชื้อเพลิง | Powertrain | จำนวนรถ`
  - Note: no รุ่นรถ / รุ่นรถ2 columns (fuel-file layout, not model-file layout)
- Row 7+: data rows

### 1.Reg by Powertrain 🎯 Target for auto-generation
- Title row 1: "Registration by Powertrain"
- Filter rows 3–4: ประเภทรถ รย.1,2,3,6,9,10,11 | Powertrain: ALL
- Row 5: year span headers (2568 | 2569)
- Row 6: period sub-headers (May | Jan-May | ...)
- Row 7: Units/Share labels
- Row 8+: data rows — Grand Total, then ICE, BEV, HEV, PHEV
- Columns: prev year months + curr month Units/Share + YTD Units/Share + remaining months + full year + curr year months + Share + MoM growth + YoY growth + YTD

### 2.Rank by Brand 🎯 Target for auto-generation
- Title: "Registration by Brand" | Powertrain: ALL
- Row 7: year headers | Row 8: month headers (Jan Feb Mar Apr May...)
- Row 9+: Grand Total, then brands sorted by current month volume descending
- Columns: monthly units per brand + share% + diff vs prev year

### 3.ICE by Brand 🎯 Target for auto-generation
- Same layout as 2.Rank by Brand but filtered to Powertrain = ICE only

### 4.BEV by Brand 🎯 Target for auto-generation
- Same layout as 2.Rank by Brand but filtered to Powertrain = BEV only

### 5.HEV by Brand 🎯 Target for auto-generation
- Same layout as 2.Rank by Brand but filtered to Powertrain = HEV only

### 6.PHEV by Brand 🎯 Target for auto-generation
- Same layout as 2.Rank by Brand but filtered to Powertrain = PHEV only

### 7.BEV by Model 🎯 Target for auto-generation
- Title: "Registration of Major BEV Brand by Model" | Powertrain: BEV Major only
- Hierarchical rows: Grand Total → Brand (bold) → Model (indented)
- Row 7: year headers | Row 8: month + Units/Share labels
- Columns: monthly units + share% + MoM growth + YoY growth + YTD

### 8.Rank by BEV Model 🎯 Target for auto-generation
- Title: "Ranking of Registration of Major BEV Models"
- Two label columns: Model | Brand
- Row 7: year headers | Row 8: month headers
- Rows: Grand Total, then models sorted by current month volume descending

### Pivot 🔒 READ-ONLY pivot
- Rows: ICE / BEV / HEV / PHEV
- Columns: monthly counts for prev year + curr year
- Refreshes when Excel opens

### master powertrain 🔒 Same as masterModel — READ-ONLY
### BEV Series Name Table 🔒 Same as masterModel — READ-ONLY

---

## What Python currently writes

| File | Sheet | Status |
|---|---|---|
| masterModel | Data | ✅ Done |
| masterModel | BEV Series Name Table | ✅ Done (append) |
| masterModel | master powertrain | ✅ Done (append new fuel types) |
| mastercal | Data | ✅ Done |
| mastercal | 1–8 analysis sheets | ⬜ Not yet — next task |
