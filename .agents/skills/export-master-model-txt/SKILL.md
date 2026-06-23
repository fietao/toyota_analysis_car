---
name: export-master-model-txt
description: Export all sheets (except Data) from a master model workbook to txt, diff against the 202605 baseline spec, score accuracy, fix bugs in build_cleaned.py, and loop until 90%+ accuracy. Use when the user says "export master model to txt", "validate master model output", "fix and loop till 90%", or wants to compare pipeline output against the spec baseline.
---

# export-master-model-txt

Exports every sheet in a master model `.xlsx` — except `Data` — to tab-separated `.txt`, diffs against the 202605 spec baseline, scores accuracy per sheet, fixes bugs in `build_cleaned.py`, and loops until all sheets hit 90%+ accuracy.

## When to use

- After a pipeline run: validate the output and fix bugs automatically
- User says "fix and loop till 90%" or "compare test output to spec"
- User wants to find what the pipeline bug is sheet by sheet

---

## Loop protocol

**Repeat until every sheet scores ≥ 90%:**

```
1. Export  → dump test output to txt
2. Score   → compute accuracy per sheet vs baseline
3. If all ≥ 90% → STOP, report pass
4. Else    → show diffs for the worst sheet
5. Fix     → edit build_cleaned.py to fix the root cause
6. Re-run  → python build_cleaned.py
7. Go to 1
```

**Cap: max 5 iterations.** If still below 90% after 5 fixes, stop and report what remains unsolved.

---

## Step 1 — Identify source file

Pick the most recently modified `test_*_masterModel.xlsx` in `output/`, excluding `~$` lock files.

```python
import glob, os
from pathlib import Path

BASE    = Path(r'C:\dev\ai-reading-car-analysis')
out_dir = BASE / 'output'
candidates = [p for p in glob.glob(str(out_dir / 'test_*_masterModel.xlsx'))
              if not os.path.basename(p).startswith('~$')]
if not candidates:
    print('ERROR: No test_N_masterModel.xlsx found in output/. Run the pipeline first.')
else:
    src = max(candidates, key=os.path.getmtime)
    print(f'Source: {src}')
```

---

## Step 2 — Export sheets to txt

```python
import openpyxl, os
from pathlib import Path

BASE        = Path(r'C:\dev\ai-reading-car-analysis')
skip_sheets = {'Data'}
sheets_dir  = BASE / 'output' / 'master_model_sheets'
sheets_dir.mkdir(exist_ok=True)

wb = openpyxl.load_workbook(src, read_only=True, data_only=True)
for name in wb.sheetnames:
    if name in skip_sheets:
        continue
    safe = name.replace('/', '-').replace('\\', '-').replace(':', '-')
    with open(sheets_dir / f'{safe}.txt', 'w', encoding='utf-8') as f:
        for row in wb[name].iter_rows(values_only=True):
            f.write('\t'.join('' if v is None else str(v) for v in row) + '\n')
    print(f'Exported: {name}')
wb.close()
```

---

## Step 3 — Score accuracy per sheet

```python
import os, difflib
from pathlib import Path

BASE         = Path(r'C:\dev\ai-reading-car-analysis')
sheets_dir   = BASE / 'output' / 'master_model_sheets'
baseline_dir = BASE / 'output' / 'master_model_baseline'

scores = {}
for fname in sorted(os.listdir(sheets_dir)):
    new_path  = sheets_dir / fname
    base_path = baseline_dir / fname
    if not base_path.exists():
        print(f'MISSING from baseline: {fname}')
        scores[fname] = 0.0
        continue
    new_lines  = new_path.read_text(encoding='utf-8').splitlines()
    base_lines = base_path.read_text(encoding='utf-8').splitlines()
    total      = max(len(base_lines), 1)
    matching   = sum(1 for a, b in zip(base_lines, new_lines) if a == b)
    pct        = round(matching / total * 100, 1)
    scores[fname] = pct
    status = 'PASS' if pct >= 90 else 'FAIL'
    print(f'[{status}] {fname}: {pct}%')

overall = round(sum(scores.values()) / max(len(scores), 1), 1)
print(f'\nOverall: {overall}%')
failing = {k: v for k, v in scores.items() if v < 90}
```

---

## Step 4 — Show diff for worst failing sheet (token-capped)

Only run if `failing` is non-empty. Show the sheet with the lowest score first.

```python
import difflib
from pathlib import Path

BASE         = Path(r'C:\dev\ai-reading-car-analysis')
sheets_dir   = BASE / 'output' / 'master_model_sheets'
baseline_dir = BASE / 'output' / 'master_model_baseline'

worst = min(failing, key=failing.get)
new_lines  = (sheets_dir   / worst).read_text(encoding='utf-8').splitlines(keepends=True)
base_lines = (baseline_dir / worst).read_text(encoding='utf-8').splitlines(keepends=True)
diff = list(difflib.unified_diff(base_lines, new_lines,
            fromfile=f'spec/{worst}', tofile=f'test/{worst}', lineterm=''))
print(f'\n=== {worst} ({failing[worst]}%) — first 60 diff lines ===')
print('\n'.join(diff[:60]))
if len(diff) > 60:
    print(f'... ({len(diff) - 60} more lines)')
```

---

## Step 5 — Fix and re-run

After reading the diff:
1. Identify the root cause in `build_cleaned.py` (wrong column, wrong sort, missing enrichment, etc.).
2. Edit the file with the minimal surgical fix.
3. Re-run the pipeline:

```powershell
$env:PYTHONUTF8=1; python C:\dev\ai-reading-car-analysis\build_cleaned.py
```

4. Go back to Step 1.

---

## Rules

- Always skip the `Data` sheet — too large; already in parquet.
- Source is always the latest `output/test_N_masterModel.xlsx` — never refer/ files.
- Set `PYTHONUTF8=1` to avoid Thai character encoding errors.
- Read diff output only — never read full txt files into context.
- Never update the baseline automatically — only on explicit user confirmation.
- Stop after 5 fix iterations and report remaining failures; don't loop forever.
- If the same sheet fails repeatedly with the same diff, escalate to user — don't repeat the same fix.
