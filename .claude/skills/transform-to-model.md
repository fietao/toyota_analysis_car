# Skill: transform-to-model

Reads raw vehicle registration data, adds Brand2 column, writes cleaned flat data into the Model file as a new sheet called "Cleaned Data".

## When to use
- Every month when a new raw data file is uploaded
- When Brand2 mapping has been updated and data needs to be re-processed
- Before any pivot or analysis work on the Model file

## How to run

```powershell
$env:PYTHONUTF8=1
$py = (Get-ChildItem "C:\Users\*\AppData\Local\Programs\Python\Python*\python.exe" | Select-Object -First 1).FullName
& $py .claude/scripts/transform_to_model.py
```

Run from the project root directory.

## What it does
1. Auto-detects raw file matching `รถใหม่_*.xlsx`
2. Auto-detects Model file matching `*Model*.xlsx`
3. Reads raw data (skips 5 header rows)
4. Adds `ยี่ห้อรถ2` column after `ยี่ห้อรถ` using Brand2 mapping
5. Writes result to `Cleaned Data` sheet in Model file
6. Reports all brands that had no explicit mapping (Brand2 = Brand1)

## After running
- Review the "no explicit mapping" list — escalate any ambiguous brands to orchestrator
- Do NOT proceed to pivot until Brand2 unknowns are reviewed and approved
