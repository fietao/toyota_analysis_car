# 2026-06-21 Codex Error Log And Claude Handoff

## Final Outputs

- Master model: `output/test_15_masterModel.xlsx`
- Analyst workbook: `202606_รถใหม่_ยี่ห้อรถ-ชนิดเชื้อเพลิง-จังหวัด ปี 2564 - มิถุนายน 2569(test analyst).xlsx`

## Validation Passed

- Master model non-Data sheets match `output/master_model_baseline/` at 100.0%.
- Master `Data` headers at row 7:
  `ปี, เดือน, ประเภทรถ, จังหวัด, ยี่ห้อรถ, ยี่ห้อรถ2, รุ่นรถ, รุ่นรถ2, ชนิดเชื้อเพลิง, Powertrain, จำนวนรถ`
- Analyst `Data` headers at row 6:
  `ปี, เดือน, ประเภทรถ, จังหวัด, ยี่ห้อรถ, ยี่ห้อรถ2, ชนิดเชื้อเพลิง, Powertrain, จำนวนรถ`
- `BEV Series Name Table` row counts match templates:
  - Master: 31,905 rows
  - Analyst: 31,926 rows
- Pivot cache definitions in both final workbooks have `refreshOnLoad="1"`.
- Both workbooks have:
  `<calcPr calcMode="auto" fullCalcOnLoad="1" forceFullCalc="1"/>`
- Final hard formula-error scan found no `#REF!`, `#DIV/0!`, `#VALUE!`, or `#NAME?` tokens.

## Errors Found And Fixed

1. `build_cleaned.py` rewrote `BEV Series Name Table` from current data.
   - Symptom: generated table shrank from 31,905 rows to 870 rows.
   - Fix: stop calling `_rewrite_bev_series_table`; preserve the template sheet.

2. `build_cleaned.py` added a non-spec `powertrain summary` sheet.
   - Symptom: baseline export reported `powertrain summary.txt` missing from baseline.
   - Fix: stop calling `_add_summary_sheet`.

3. Master workbooks did not force recalculation on open.
   - Symptom: workbook kept template `<calcPr calcId="191028"/>`.
   - Fix: writer now replaces it with full recalculation flags.

4. `build_analyst.py` wrote the refreshed `Data` sheet with the wrong worksheet namespace.
   - Symptom: openpyxl could not read the analyst `Data` headers/dimensions after refresh.
   - Fix: use `http://schemas.openxmlformats.org/spreadsheetml/2006/main`.

5. Analyst workbook did not force recalculation on open.
   - Symptom: preserved formulas could retain stale cached values.
   - Fix: writer now replaces workbook `calcPr` with full recalculation flags and drops stale `calcChain.xml`.

6. Analyst workbook preserved hard cached formula errors in `7.BEV by Model`.
   - Symptom: cached `#DIV/0!` values remained in rows with zero denominators.
   - Fix: `build_analyst.py` clears hard cached formula-error cells in preserved worksheet XML.

7. Initial hard-error sanitizer was too slow.
   - Symptom: first regex version hung while scanning large worksheet XML.
   - Fix: short-circuit sheets without hard-error strings and sanitize cell-by-cell only when needed.

8. Local LLM inspection was unreliable for `_rewrite_bev_series_table`.
   - Symptom: it described nonexistent paths and behavior.
   - Action: discarded that result; use direct source/validation evidence.

9. Auto BEV approval is risky.
   - Symptom: `pipeline_state.json` includes likely-wrong BEV Major classifications such as `BMW S 1000 RR`, `MG5 1.5 X`, and `AUDI A5 ... TFSI`.
   - Action: do not blindly append these to `BEV Series Name Table`; require human review.

10. Reading a workbook while `build_analyst.py` was overwriting it caused a transient `BadZipFile`.
    - Action: avoid opening generated `.xlsx` files until the writer process exits.

## Map Updates Made

Updated `refer/model2_map.csv` with the missing raw model-name aliases from the latest run. These are model-name normalizations only; they do not set Powertrain.

- `ATTO 3 (480KM-ER)` -> `BYD ATTO 3`
- `DOLPHIN (490KM)` -> `BYD DOLPHIN`
- `M6 EXTENDED` -> `BYD M6`
- `SEAL AWD PERFORMANCE` -> `BYD SEAL`
- `SEALION 6 DM-i` -> `BYD SEALION 6`
- `JAECOO 6 EV` -> `6 EV`
- `OMODA C5 EV` -> `C5 EV`
- `DEEPAL L07` -> `L07`
- `DEEPAL S07` -> `S07`
- `LUMIN DC` -> `LUMIN`
- `MG EP PLUS` -> `EP`
- `MG4 XPOWER` -> `MG4 ELECTRIC`
- `MG5 1.5 X` -> `MG5`
- `Cooper SE` -> `Cooper SE`
- `EX30 Ultra Single Motor` -> `EX30`
- `XC40 RECHARGE` -> `XC40`
- `X Flagship` -> `ZEEKR X`

Already present before this handoff:

- `A5 CP 40 TFSI S line eo`
- `S 1000 RR`

Verification after map update: all 19 latest-run model aliases are now present in `refer/model2_map.csv`; duplicate raw-key count is 0.

## Be Careful Next

- Do not regenerate or shrink `BEV Series Name Table`; it is a maintained template/reference table.
- Do not update Powertrain/BEV classifications from `pipeline_state.json` without human review.
- The output depends on real Excel opening the workbook to refresh pivots/recalculate formulas; the files are marked correctly for that.
- Wait for writer processes to finish before validation reads.
- Use `PYTHONUTF8=1` for every pipeline/validation command.
