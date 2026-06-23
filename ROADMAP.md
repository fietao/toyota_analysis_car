# Project Roadmap

Last updated: 2026-06-22 (session 10)

---

## What This Is

A monthly data processing system for Thailand DLT (กรมการขนส่งทางบก) car registration data.

Every month the DLT releases two Excel files. This system takes those two files,
cleans and enriches them, updates the master Excel workbooks, and produces a finished
analyst report — automatically, with one click.

**Who uses it:** a non-technical operator (not a programmer). They should never need to
open a terminal or know Python exists.

**Who reads the output:** an analyst or manager who opens the finished Excel report
to review registration trends, powertrain mix, BEV growth, and brand rankings.

---

## The Product (Full Spec)

### Inputs

Each month the operator receives two raw Excel files from DLT:

| File | Thai name | Contains |
|---|---|---|
| Fuel file | ยี่ห้อรถ-ชนิดเชื้อเพลิง-จังหวัด | Brand × fuel type × province × month counts |
| Model file | ยี่ห้อรถ-รุ่นรถ-จังหวัด | Brand × model × province × month counts |

Both files cover January 2564 (2021) through the current month.

### Processing

The pipeline joins, cleans, and enriches the two files:

1. **Fuel enrichment** — every model row gets a `ชนิดเชื้อเพลิง` (fuel type) from the fuel file by matching brand + province + month
2. **Powertrain mapping** — fuel type → `Powertrain` (ICE / BEV / HEV / PHEV / N/A) via reference table
3. **Brand normalisation** — `ยี่ห้อรถ2` canonical brand grouping (e.g. GWM TANK + HAVAL + ORA → GWM)
4. **Model normalisation** — `รุ่นรถ2` clean model name via `model2_map.csv` (8,358 entries)
5. **Filter** — keep only รย.1/2/3/6/9/10/11 vehicle types

### BEV Detection

After enriching new rows with `ชนิดเชื้อเพลิง`, `build_cleaned.py` detects unknown BEV models:

- rows where `ชนิดเชื้อเพลิง == "ไฟฟ้า"` AND model not already in `BEV Series Name Table`
- prints each new model to stdout
- **continues** — does not block the Excel write (per session 7 decision)

After the pipeline writes the Data sheet, `build_BEV.py` appends any approved rows from
`pipeline_state.json` to `BEV Series Name Table`.

> **Future enhancement (not yet scoped):** create a review workbook and block pipeline until
> operator approves new BEV models. For now, operator updates BEV Series Name Table manually
> then re-runs the pipeline.

### Outputs

| Output | Format | Updated how |
|---|---|---|
| **Master Model** | Excel (.xlsx) | Data rows replaced in-place (rows 8+); metadata rows 1-7 preserved |
| **Master Cal** | Excel (.xlsx) | Data rows replaced in-place (rows 7+); metadata rows 1-6 preserved |
| **Analyst Report** | Excel (.xlsx) | New timestamped file: copy of Master Cal with fresh Data sheet |
| **Dashboard data** | JSON | Serialised from analyst output; feeds the web dashboard |

All Excel formulas, pivot tables, charts, and formatting in the master files are
preserved — Python only touches the data rows.

### Analyst Report Contents

The finished report is a copy of the Master Cal template with these sheets:

- `Data` — cleaned data (all years, all months, all powertrain types)
- `1.Reg by Powertrain` — monthly registration totals by powertrain
- `2.Rank by Brand` — brand ranking table
- `3.ICE by Brand` through `6.PHEV by Brand` — powertrain-specific brand tables
- `7.BEV by Model` — BEV model-level detail
- `8.Rank BEV Model` — BEV model ranking
- Additional sheets: master powertrain summary, BEV Series Name Table, etc.

Pivots auto-refresh when the file is opened in Excel.

### The Web App (target state)

```
┌─────────────────────────────────────────────────┐
│  🚗 Car Registration Update                      │
│                                                  │
│  [ Drop fuel file here ]  [ Drop model file ]   │
│                                                  │
│  [ Run Update ]                                  │
│                                                  │
│  ● Stage 1 – Cleaning data...         ✅ Done    │
│  ● Stage 2 – BEV pivot sheets...     ✅ Done    │
│  ● Stage 3 – Analyst report...       ⏳ Running │
│                                                  │
│  [ ⬇ Download 202606_analyst.xlsx ]              │
│                                                  │
│  ────────────────────────────────────────────    │
│  Dashboard: BEV share 18.4% ▲2.1%  May 2569    │
└─────────────────────────────────────────────────┘
```

---

## Architecture

```
raw data/           ← operator drops two DLT xlsx files
    │
    ▼
update_raw_data.py  ← copies files, checks for new fuel types, runs pipeline
    │
    ├── build_cleaned.py      → incremental-first:
    │                            1. load parquet (baseline)
    │                            2. find new/corrected months in last 2 years
    │                            3. enrich ONLY those rows from fuel file
    │                            4. add brand2/model2/Powertrain to those rows
    │                            5. detect new BEVs (print-and-continue)
    │                            6. merge + sort → parquet + master Model/Cal
    │                            7. write pipeline_state.json
    │
    ├── build_BEV.py          → reads pipeline_state.json,
    │                           appends approved BEV rows to BEV Series Name Table
    │
    ├── build_analyst.py      → YYYYMM_...(test analyst).xlsx
    │
    └── export_dashboard.py   → dashboard/public/data/dashboard_data.json
                                          │
                                          ▼
                                  dashboard/   ← Next.js web app
```

**Key design rules:**
- Python only writes data rows. Excel owns all formulas, pivots, and formatting.
- Master files are rewritten in-place using direct ZIP manipulation — never loaded
  into openpyxl write mode (too slow on 50 MB+ files).
- The Data sheet is still fully rewritten each run (sort requires the full merged
  result). The incremental gain is in processing — only new/corrected rows are
  enriched and mapped; existing parquet rows are merged in as-is.

---

## Build Phases

### Phase 1 — Pipeline ✅ Core complete
Core data processing works. Incremental-first build confirmed working session 8.
- [x] Raw file reading + fuel enrichment
- [x] Brand / model / powertrain mapping
- [x] Parquet intermediate (`test_model_cleaned.parquet`)
- [x] Master Model written in-place (zipfile, rows preserved)
- [x] BEV Series Name Table append path exists (`build_BEV.py`)
- [x] **Incremental-first processing** — rolling rebuild scoped to last 2 BE years; new + corrected months rebuilt; existing parquet rows merged in as-is. Confirmed session 8.
- [x] **`pipeline_state.json`** — written by `build_cleaned.py`; `build_BEV.py` reads it successfully
- [x] **`ชนิดเชื้อเพลิง` in Data sheet** — column present in `df_cleaned` and written to master Model (confirmed session 8 cols output)
- [x] Corrected months tracked in `pipeline_state.json`
- [ ] **Analyst report** — BLOCKED: master cal (`*(master cal).xlsx`) file missing; `build_analyst.py` cannot run
- [x] **BEV detection fixed** — uses `ชนิดเชื้อเพลิง == "ไฟฟ้า"` (B4 fixed session 9)
- [x] **Fix B3** — `build_BEV.py` no longer overwrites pivot sheets; `next_row` correctly finds last data row (fixed session 9)
- [x] **Powertrain priority fixed** — model-level lookup (`BEV Major`) now wins over fuel-level (`BEV`); 46,084 rows correctly classified (fixed session 9)

#### Incremental-first design (agreed session 7, pending implementation)

```
1.  Load parquet → existing month keys + rows
2.  Read reference tables (powertrain map, brand2, BEV table, model2_map)
3.  Read both raw DLT files (df_fuel, df_model)
4.  Scope: last year (full Jan-Dec) + current year (Jan-now), BE years
    — first run (no parquet): process ALL months in raw file (no scope limit)
5.  new_months    = scoped keys NOT in parquet
    corrected     = scoped keys IN parquet where row count OR total changed
    update_months = new_months ∪ corrected
6.  If update_months is empty → skip processing; use df_existing as df_cleaned
7.  Extract ONLY update_months rows from df_model
8.  Join those rows with df_fuel → ชนิดเชื้อเพลิง (scoped to update_months only)
9.  Add brand2 / model2 / Powertrain to those rows only
10. Detect new BEVs: ชนิดเชื้อเพลิง == "ไฟฟ้า" AND not in BEV Series Name Table
    — print list; continue (no block)
11. Merge: parquet (minus corrected rows) + new processed rows
12. sort_cleaned_data() on full merged result
13. Save parquet; write pipeline_state.json; write Data sheet to Excel
```

### Phase 2 — Operator Trigger 🔄 Partial
Non-technical operator can run the pipeline without a terminal.
- [x] `UPDATE.bat` — double-click to run (Windows)
- [ ] Web UI file drop zone (operator drags the two DLT files in)
- [ ] "Run Update" button triggers pipeline via local API
- [ ] Progress display (per-stage status)
- [ ] Download link for finished analyst report

### Phase 3 — Local API 📋 Not started
Bridge between web UI and pipeline scripts.
- [ ] Flask or FastAPI server (`api.py`) runs locally
- [ ] `POST /upload` — receives two files, saves to `raw data/`
- [ ] `POST /run` — spawns pipeline process, streams stdout as SSE
- [ ] `GET /download` — returns finished analyst xlsx
- [ ] `GET /status` — last run result (success/fail, timestamp, row count)

### Phase 4 — Dashboard 📋 Not started
Live metrics view in the web app.
- [ ] `export_dashboard.py` serialises key metrics to JSON
- [ ] Next.js reads JSON and renders: BEV share %, top brands, monthly trend chart
- [ ] Dashboard auto-updates after each pipeline run

### Phase 5 — Deployment 📋 Not started
Hosted so the operator doesn't need a local Python install.
- [ ] Decide: local-only (just the .bat) vs. cloud (Vercel + cloud Python)
- [ ] If cloud: containerise the Python pipeline, deploy API, point Next.js at it
- [ ] If local: package as a Windows executable or installer

---

## Immediate Next Steps

1. **Restore master cal** — `*(master cal).xlsx` was deleted; restore it to the
   project root so `build_analyst.py` can run. This is the only blocker before
   a full end-to-end pipeline run.

2. **Full end-to-end run** — once master cal is restored, run from `backend/`:
   ```
   python build_cleaned.py && python build_BEV.py && python build_analyst.py
   ```
   Verify analyst report is produced with correct sheet order and pivot totals.

3. ~~**Investigate B6: +745 unit inflation**~~ ✅ **Closed session 11 — not a bug.**
   The +745 units / +59 rows were a data-version artifact: `diagnose_pipeline.py`
   compared the parquet against the stale `input/` copy (636,333 rows), but the
   pipeline reads the revised `raw data/` release (636,392 rows), to which DLT added
   59 `รย.1` records (745 units) in year 2569. Parquet vs revised raw Δ = 0; golden
   fixture PASS. Cleanup: point `diagnose_pipeline.py` at `raw data/` (or delete the
   stale `input/` copy) so it stops generating phantom bugs.

4. **B7 fuel-type shifts — decide the business rule (not a bug).** Confirmed session 11:
   `enrich_fuel_type` assigns each `(ปี/เดือน/ประเภทรถ/จังหวัด/ยี่ห้อรถ)` key its single
   dominant (highest-volume) fuel type, which produces the category shifts (เบนซิน +161K,
   ดีเซล -124K, PHEV -36K). Open question for the operator: is "dominant fuel per key"
   correct, or should model rows keep their own fuel type? Decision, not code fix.

5. **Remove dead code in `build_analyst.py`** — 8 functions never called by
   `main()`.

6. **Start Phase 2 web UI** — file drop + run button in Next.js + Flask API.
   Do not start until T1 full pipeline run passes.

---

## Known Issues

| # | Issue | Status | Fix |
|---|---|---|---|
| B1 | **All raw rows re-processed every run** | ✅ **Fixed session 8** — rolling rebuild scoped to last 2 BE years; only new/corrected months re-enriched | — |
| B2 | **`ชนิดเชื้อเพลิง` column missing from Data sheet** | ✅ **Fixed session 8** — column present in `df_cleaned` and written to master Model | — |
| B3 | **`build_BEV.py` `next_row` appends after pre-formatted empty rows** | ✅ **Fixed session 9** | — |
| B4 | **BEV detection broken** — `build_cleaned.py` used `Powertrain.startswith("BEV")` | ✅ **Fixed session 9** | — |
| B5 | **Powertrain priority wrong** — `pt_fuel.combine_first(pt_model)` showed `'BEV'` instead of `'BEV Major'` | ✅ **Fixed session 9** | — |
| B6 | ~~+745 unit inflation in parquet~~ — **not a bug.** Diagnostic compared parquet vs stale `input/` copy (636,333 rows); pipeline reads revised `raw data/` release (636,392 rows). Parquet correct (Δ=0 vs revised raw). | ✅ **Closed session 11** | Fix `diagnose_pipeline.py` to read `raw data/` (cleanup) |
| B7 | **Fuel-type shifts are structural, not a bug** — `enrich_fuel_type` collapses each key onto its dominant fuel type (hence เบนซิน +161K, ดีเซล -124K, PHEV -36K) | 🟡 **Decision needed** — confirm business rule with operator | — |
| — | **`pipeline_state.json` never written** | ✅ **Fixed** | — |
| — | **Master cal missing** — `*(master cal).xlsx` was deleted; `build_analyst.py` cannot run | 🔴 **Blocker** | Restore file to `backend/` |
| — | `select_dtypes(include="object")` deprecation warning | ✅ **Fixed session 9** | — |
| — | `pipeline_state.json` contains likely-wrong auto-approved BEV rows (BMW S 1000 RR, MG5 1.5 X, AUDI A5 TFSI) | ⚠️ **Do not append** to BEV Series Name Table without manual review | — |
| — | Web UI does not exist yet | Phase 2 | — |
| — | `1.Reg by Powertrain` output is 33 cols vs. 34 in reference template | 🟡 Investigate | Check trailing column before dashboard work |
