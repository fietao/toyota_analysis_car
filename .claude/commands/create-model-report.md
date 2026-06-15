Run the monthly model pipeline: read raw DLT data → build cleaned data + BEV pivot sheets → write output Excel file.

## Steps

1. **Check inputs exist**
   - Raw data: glob `รถใหม่_*.xlsx` in project root (skip `~$` files)
   - Model template: glob `*- Model.xlsx` in project root (skip `~$` files)
   - If either is missing, stop and tell the user which file is missing

2. **Run the script**
   ```powershell
   $env:PYTHONUTF8=1
   $py = (Get-Command python -ErrorAction SilentlyContinue).Source
   & $py ".claude/scripts/build_model.py"
   ```

3. **Verify output**
   - Confirm `test_model_1.xlsx` was created in project root
   - Print the sheet list and row counts as a summary

4. **Report to user**
   - Output filename
   - Data coverage (start month → end month from Cleaned Data title row)
   - Sheet count
   - Any warnings from the script (unmapped brands, missing months, etc.)

## Notes

- Output is always `test_model_1.xlsx` (test name) — rename manually when ready
- BEV pivot sheets (BEV by Model, BEV by Model (2), BMW) are built from the `Data` sheet inside the Model template — update that sheet first if DLT released new model-level data
- Raw data is cumulative: always run a full rebuild, never try to append
- DLT retroactively corrects old months — full rebuild captures all corrections automatically
