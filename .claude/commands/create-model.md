Build this month's model output file from the latest raw data.

1. Find Python (auto-detect, never hardcode):
   `$py = (Get-ChildItem "C:\Users\*\AppData\Local\Programs\Python\Python*\python.exe" | Select-Object -First 1).FullName`

2. Run from project root:
   `$env:PYTHONUTF8=1; & $py .claude/scripts/build_model.py`

3. Report back:
   - Output filename created
   - Total rows written
   - Brands with no explicit Brand2 mapping (count + first 10) — these need orchestrator review
   - Whether all template sheets copied successfully

If Model template is locked (Excel open): tell user to close it and run /model again.
If raw data file not found: tell user to make sure the file matches pattern รถใหม่_*.xlsx
