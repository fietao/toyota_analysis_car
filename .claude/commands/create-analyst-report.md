Build the analyst report from the model output.

## Steps

1. **Check inputs exist**
   - Model output: `test_model_1.xlsx` in project root
   - Model template: glob `*- Model.xlsx` in project root (skip `~$` files)
   - If either is missing, stop and tell the user what's needed

2. **Run the script**
   ```powershell
   $env:PYTHONUTF8=1
   $py = (Get-Command python -ErrorAction SilentlyContinue).Source
   & $py ".claude/scripts/build_analyst.py"
   ```

3. **Verify output**
   - Confirm `YYYYMM_รถใหม่_...(analyst).xlsx` was created in project root
   - Print sheet list as summary

4. **Report to user**
   - Output filename
   - Data coverage (prev year, current year/month)
   - Sheet count
   - Any warnings from the script

## Notes

- Requires `test_model_1.xlsx` from running `/create-model-report` first
- Output is auto-named from the data's end month: `YYYYMM_รถใหม่_...(analyst).xlsx`
- BEV model sheets (7.BEV by Model, 8.Rank by BEV Model) read from the Model template's Data sheet — update that sheet if new BEV models were released
- Close the output file in Excel before re-running
- Uses only File 1 (ชนิดเชื้อเพลิง) data for sheets 1–6; BEV Major data comes from the model template
