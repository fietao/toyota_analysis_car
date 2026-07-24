# Handoff: Install and Final-Test the Whole Program on Another Laptop

Date: 2026-07-24
Repository: `C:\dev\ai-reading-car-analysis`

## Purpose

This handoff is for setting up the full Thailand DLT car-registration dashboard on another
Windows laptop, then running one final test to confirm the program works for a non-coding
Thai maintainer.

The maintainer needs the whole program, not only the website. They need the repository folder,
backend scripts, frontend dashboard, batch files, config CSVs, and generated public data.

## Before Copying or Installing on Another Laptop

On the current development laptop:

1. Commit and push all intended changes.
2. Make sure `git status --short` does not show intended source changes.
3. Pay special attention to:
   - `frontend/src/components/FilterPillPopover.tsx`
     - This contains the dropdown layering fix so filter popovers appear above sticky tables.
   - `frontend/src/app/analyst/page.tsx`
     - This contains the final Analyst filter UI: Brand, Model, Vehicle Type, Powertrain.

Do not hand off a folder with uncommitted source changes unless you are intentionally copying
the working tree instead of using Git.

## Required Software on the New Laptop

Install once:

1. Python 3.12
   - The batch files expect `py -3.12`.
2. Node.js LTS, including `npm`.
3. Git, if the laptop will receive updates by pulling from GitHub.
4. Microsoft Excel, for reviewing DLT Excel files and `model_powertrain_review.csv`.

Recommended folder location:

```text
C:\dev\ai-reading-car-analysis
```

## Install the Program on the New Laptop

Preferred method:

```powershell
cd C:\dev
git clone <REPO_URL> ai-reading-car-analysis
cd C:\dev\ai-reading-car-analysis
SETUP.bat
```

If Git is not available, copy the full `ai-reading-car-analysis` folder to the new laptop,
then run:

```powershell
cd C:\dev\ai-reading-car-analysis
SETUP.bat
```

The folder must include:

- `backend/`
- `frontend/`
- `docs/`
- `MONTHLY_UPDATE.bat`
- `SETUP.bat`
- `BUILD_RELEASE.bat`
- `frontend/RUN.bat`
- `backend/config/model_map.csv`
- `backend/config/model_powertrain_review.csv`
- `backend/config/powertrain_map.csv`
- `frontend/public/data/*.json`

## First Local Dashboard Test

After `SETUP.bat` finishes, run:

```powershell
frontend\RUN.bat
```

Open:

```text
http://localhost:3001
```

Check these pages:

- `/`
- `/models`
- `/analyst`
- `/report`

Expected:

- The dashboard loads without errors.
- `/models` shows Brand, Model, Province, Vehicle Type, Active Years.
- `/analyst` shows searchable Brand, Model, Vehicle Type, Powertrain controls.
- `/analyst` has no fake Province or Year filter.
- `/report` year selector works.
- Excel export buttons download files.

## Final Maintenance Test

Use this to prove the non-coder monthly workflow works.

1. Put the two latest DLT Excel files into:

```text
backend\raw data\
```

2. Close Excel completely.

3. Double-click:

```text
MONTHLY_UPDATE.bat
```

4. Read:

```text
reports\monthly_operator_summary.txt
```

Expected summary result is one of:

```text
สำเร็จ: เผยแพร่ข้อมูลใหม่แล้ว
ต้องตรวจเพิ่ม: เผยแพร่ข้อมูลใหม่แล้ว แต่ Sheets 7-8 อาจยังไม่รวมรุ่น BEV ใหม่
ไม่สำเร็จ: ระบบยังใช้ข้อมูลเดิมอยู่ ไม่ได้เผยแพร่ข้อมูลใหม่
```

If pending model rows exist, open only:

```text
backend\config\model_powertrain_review.csv
```

Approve only evidence-backed BEV models. If unsure, leave rows as `pending`.

Then close Excel and run `MONTHLY_UPDATE.bat` again.

## What the Thai Maintainer Edits

Normally, the maintainer edits only this file:

```text
backend\config\model_powertrain_review.csv
```

For approved rows, the program accepts:

- `candidate_powertrain`: `BEV`, `HEV`, `PHEV`, `ICE`, `ambiguous`, or `unknown`
- `review_status`: `approved`, `rejected`, `ambiguous`, or `pending`
- `evidence`: required for `approved`
- `reviewer`: required for `approved`
- `reviewed_at`: required for `approved`, format `YYYY-MM-DD`

Important:

- Use `BEV`, not `EV`.
- Do not approve by guessing from model name.
- Do not use brand totals to decide model Powertrain.
- Do not edit code.
- Do not edit `frontend/public/data/*.json` by hand.

Full Thai instructions are in:

```text
docs\THAI_OPERATOR_MONTHLY_GUIDE.md
```

## No-Collapse Expectation

If a monthly update fails:

- current dashboard JSON should remain usable;
- new broken data should not be published;
- the Thai summary should explain the next action;
- technical details should be in logs for a developer.

The operator-facing failure message should say:

```text
ไม่สำเร็จ: ระบบยังใช้ข้อมูลเดิมอยู่ ไม่ได้เผยแพร่ข้อมูลใหม่
```

## Last Developer Checks Before Public Release

Run on the development laptop or the new laptop:

```powershell
cd C:\dev\ai-reading-car-analysis\frontend
npm test
npm run lint
npm run build
cd ..
```

Optional backend checks, if Python dependencies are installed:

```powershell
py -3.12 backend\tests\test_operator_preflight.py
py -3.12 backend\tests\test_operator_safe_publish.py
py -3.12 backend\export_manual_report.py
```

Then run the app and smoke-test:

- `/models`
  - Brand narrows Model.
  - Dropdowns appear above the table.
- `/analyst`
  - Brand, Model, Vehicle Type, Powertrain are searchable.
  - Model view locks Powertrain to `ALL`.
  - Dropdowns appear above the table.
- `/report`
  - Historical years work.
  - Excel export works for the active sheet/year.

## Suggested Skills for Future Agent

- `orchestrator`: planning, final release checks, and routing.
- `run-pipeline`: monthly data/build verification.
- `scrutinize`: final bug-risk review before publish.
- `impeccable`: frontend visual polish if the UI looks off.

