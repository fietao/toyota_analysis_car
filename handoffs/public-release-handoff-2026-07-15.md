# Handoff — public release / manual report parity

**Last updated:** 2026-07-15  
**Repo:** `C:\dev\ai-reading-car-analysis`  
**Current branch:** `main`  
**Audience:** next Codex / Gemini / Qwen agent continuing the public-release push  

This repo is in a large, dirty, multi-agent working tree. Preserve existing work. Do **not** run
`git reset`, `git checkout --`, `git clean`, `git add -A`, or broad process-kill commands. Commit
only scoped groups after the user explicitly asks.

---

## 1. Current goal

Prepare the Thai DLT car-registration dashboard for public static deployment:

- Static Next.js export, no upload API, no raw parquet data exposed.
- Data split into smaller public JSON files.
- Analyst page supports powertrain + vehicle-type slices.
- Models page uses correct model-table powertrain filtering.
- New `/report` page mirrors the manual markdown workbook sheets 1–9 as closely as possible.
- Release pipeline validates periods and markdown golden cells before build.

The user wants the app to “work similar as the md,” look professional, and be safe to public.

---

## 2. Very important domain decisions

### Sheet 4 BYD BEV total

Treat **33,070** as correct for Sheet 4 BYD BEV 2568.

Evidence:

- User manually summed `C:\Users\georg\Downloads\รถใหม่_มิถุนายน 2569 (2)_Data.md`.
- Program output matches all months:
  - Jan 4,382
  - Feb 1,121
  - Mar 1,990
  - Apr 2,142
  - May 4,225
  - Jun 5,807
  - Jul 2,824
  - Aug 2,223
  - Sep 2,119
  - Oct 1,633
  - Nov 1,944
  - Dec 2,660
  - Total 33,070

The old/manual model-sheet value **33,077** is a model-layer mismatch and should not block release.

### Sheets 7–8 known mismatch

Sheets 7–8 use model-table `Powertrain == "BEV Major"` and appear to come from a slightly different
BEV-review/model-master vintage than the markdown workbook. Current validators intentionally mark
these as **known, documented, non-blocking** mismatches:

- Sheet 8 JAECOO / 5 EV 2569: markdown 11,137, program 11,133.
- Sheet 8 BYD DOLPHIN 2569: markdown 8,696, program 8,608.
- Sheet 8 BYD ATTO 3 2569: markdown 7,357, program 7,264.

Do not “fix” this by corrupting fuel-derived totals. If the user wants perfect Sheet 7–8 parity,
the right fix is a reviewed model-master / BEV Series Name Table update workflow.

---

## 3. Key files and current architecture

### Release pipeline

- `C:\dev\ai-reading-car-analysis\BUILD_RELEASE.bat`
  - Runs the deterministic release pipeline.
  - Current expected stages include data pipeline/export, manual report export, public validators,
    lint, TypeScript, and Next static build.
- `C:\dev\ai-reading-car-analysis\backend\validate_public_release.py`
  - Checks all required public JSON files exist and share the same reporting period.
  - Also checks model powertrain annotations and all 9 manual report sections.
- `C:\dev\ai-reading-car-analysis\backend\validate_against_markdown.py`
  - Compares `manual_report.json` against golden markdown cells from
    `C:\Users\georg\Downloads\รถใหม่_มิถุนายน 2569 (2)_sheets1-9.md`.

### Public JSON

- `C:\dev\ai-reading-car-analysis\frontend\public\data\dashboard_summary.json`
  - Small summary/metadata/brand/fuel data.
- `C:\dev\ai-reading-car-analysis\frontend\public\data\dashboard_models.json`
  - Heavy brand/model tree.
- `C:\dev\ai-reading-car-analysis\frontend\public\data\analyst_data.json`
  - Analyst calculation table, now nested by view/powertrain/vehicle type.
- `C:\dev\ai-reading-car-analysis\frontend\public\data\manual_report.json`
  - New report JSON for all 9 manual workbook sections.
- `C:\dev\ai-reading-car-analysis\frontend\public\data\cleaned_data_manifest.json`
  - Public non-sensitive manifest and reporting period.

### Frontend pages

- `C:\dev\ai-reading-car-analysis\frontend\src\app\page.tsx`
  - Home/dashboard.
- `C:\dev\ai-reading-car-analysis\frontend\src\app\models\page.tsx`
  - Brand/model explorer.
- `C:\dev\ai-reading-car-analysis\frontend\src\app\analyst\page.tsx`
  - Analyst calculation table.
- `C:\dev\ai-reading-car-analysis\frontend\src\app\report\page.tsx`
  - Manual report route; should render all 9 sheets from `manual_report.json`.
- `C:\dev\ai-reading-car-analysis\frontend\src\app\selectors.ts`
  - Shared frontend selectors/types.

### Specs / docs

- `C:\dev\ai-reading-car-analysis\specs\public_dashboard_markdown_parity_spec.md`
  - Contract for manual markdown parity and sheet definitions.
- `C:\dev\ai-reading-car-analysis\docs\PUBLIC_RELEASE_CLEAN_MERGE_PLAN.md`
  - Clean merge/public release plan.
- `C:\dev\ai-reading-car-analysis\LIBRARY.md`
  - Lessons and project library notes.

---

## 4. What has been implemented so far

### Data split / public-safe footprint

- `backend/export_dashboard.py` exports:
  - `dashboard_summary.json`
  - `dashboard_models.json`
  - `cleaned_data_manifest.json`
- Raw parquet copies were removed from public assets.
- Legacy `dashboard_data.json` is deleted/obsolete.

### Static release

- `frontend/next.config.ts` uses static export mode.
- `BUILD_RELEASE.bat` exists for deterministic local release builds.
- Public output is generated under `C:\dev\ai-reading-car-analysis\frontend\out`.
- There is no public URL until the output is deployed to hosting.

### Upload removal

- Legacy upload UI/API was removed:
  - `frontend\public\analyst.html` deleted.
  - `frontend\public\models.html` deleted.
  - `frontend\src\app\api\upload\route.ts` deleted.
  - `frontend\src\components\UploadModal.tsx` deleted.

### Analyst page vehicle-type support

- `backend/export_analyst.py` now exports:
  - `meta.vehicle_types_list`
  - `data[view_by][powertrain][vehicle_type_code]`
- `frontend/src/app/analyst/page.tsx` has vehicle-type select beside powertrain.
- Client-only filtering was rejected because shares/ranks/growth need recalculation per slice.

### Models page powertrain fix

Root cause: model rows were filtered by fuel-derived `PT`, so rows like BYD SEALION 6 appeared
under BEV even when model-table `Powertrain` was OTH.

Fix:

- `backend/export_dashboard.py` groups model rows by both fuel-derived `PT` and model-table
  `Powertrain`.
- Model nodes include `powertrain`.
- `frontend/src/app/models/page.tsx` filters child model rows by model-level powertrain.
- `frontend/src/app/selectors.ts` includes optional `ModelNode.powertrain`.

Verified by validator: model powertrain annotations present on 9,690 model rows
`(BEV, BEV Major, HEV, ICE, N/A, OTH, PHEV)`.

### Sticky table hardening

- Sticky behavior moved from `tr` to `th`.
- Header backgrounds made opaque.
- `/analyst` avoids React state layout loops by using CSS variables + `ResizeObserver`.
- New skill exists: `C:\dev\ai-reading-car-analysis\.agents\skills\fix-sticky-tables`.

### Manual report page

The last pasted Gemini/Opus summary claims implementation is complete:

- `backend/export_manual_report.py`
- `backend/validate_against_markdown.py`
- `frontend/public/data/manual_report.json`
- `frontend/src/app/report/page.tsx`
- `BUILD_RELEASE.bat` updated to include manual report export/validation.

I inspected the files and verified the release validators below.

---

## 5. Verification run in this handoff update

These commands were run successfully on 2026-07-15:

```powershell
py -3.12 backend\validate_public_release.py
```

Result:

- All required data files present.
- Model powertrain annotations present on 9,690 model rows.
- `manual_report.json` has all 9 sheet sections.
- Reporting period matches across:
  - `dashboard_summary.json`
  - `dashboard_models.json`
  - `analyst_data.json`
  - `cleaned_data_manifest.json`
  - `manual_report.json`
- Validation passed for June 2569.

```powershell
py -3.12 backend\validate_against_markdown.py "C:\Users\georg\Downloads\รถใหม่_มิถุนายน 2569 (2)_sheets1-9.md"
```

Result:

- Fuel-derived golden cells pass:
  - Sheet 1 Grand Total Jan-Jun 2568 = 324,368.
  - Sheet 1 Grand Total Jan-Jun 2569 = 374,424.
  - Sheet 1 BEV 2568 full year = 122,559.
  - Sheet 1 BEV Jan-Jun 2569 = 105,558.
  - Sheet 2 BYD Jan-Jun 2569 = 26,069.
  - Sheet 4 BYD 2568 full BEV = 33,070.
  - Sheet 4 BYD Jan-Jun 2569 BEV = 21,450.
- Sheet 8 model mismatches are marked known/non-blocking.
- Validation passed.

Not rerun in this handoff update:

- `npm run lint`
- `npx tsc --noEmit`
- `npm run build`

The last pasted Gemini summary says all three passed, but a fresh agent should rerun them before
public deployment.

---

## 6. Dirty working tree warning

`git status --short` is very dirty. This is expected but risky.

High-signal changed/untracked files include:

- `.agents/skills/orchestrator/SKILL.md`
- `.agents/skills/fix-sticky-tables/`
- `.codex/config.toml`
- `.gemini/`
- `.mcp.json`
- `.vscode/mcp.json`
- `BUILD_RELEASE.bat`
- `LIBRARY.md`
- `backend/export_analyst.py`
- `backend/export_dashboard.py`
- `backend/export_manual_report.py`
- `backend/validate_against_markdown.py`
- `backend/validate_public_release.py`
- `backend/refer/model2_map.csv`
- `docs/PUBLIC_RELEASE_CLEAN_MERGE_PLAN.md`
- `frontend/package.json`
- `frontend/package-lock.json`
- `frontend/src/app/page.tsx`
- `frontend/src/app/selectors.ts`
- `frontend/src/app/analyst/`
- `frontend/src/app/models/`
- `frontend/src/app/report/`
- `frontend/public/data/dashboard_summary.json`
- `frontend/public/data/dashboard_models.json`
- `frontend/public/data/manual_report.json`
- deleted legacy files:
  - `frontend/public/analyst.html`
  - `frontend/public/models.html`
  - `frontend/public/data/dashboard_data.json`
  - `frontend/src/app/api/upload/route.ts`
  - `frontend/src/components/UploadModal.tsx`

Do not bundle everything into one commit unless the user explicitly asks for one giant release
commit. Prefer scoped commits:

1. data export + validators,
2. frontend report/analyst/models routes,
3. docs/specs/skills,
4. MCP/config if desired.

---

## 7. Next recommended steps

1. Rerun the full release gate:

   ```powershell
   .\BUILD_RELEASE.bat
   ```

2. If that passes, manually check local output:

   ```powershell
   cd frontend
   npx serve out
   ```

   Then open the printed local URL and check:

   - `/`
   - `/models`
   - `/analyst`
   - `/report`

3. Confirm `/report` user-facing behavior:

   - Sheet 1 totals match.
   - Sheet 4 BYD BEV 2568 shows 33,070.
   - Sheet 8 shows known mismatch banner or disclosure.
   - Sheet 9 Bangkok overall shows 559,073.

4. Rerun frontend checks:

   ```powershell
   cd frontend
   npm run lint
   npx tsc --noEmit
   npm run build
   ```

5. Decide deployment target:

   - GitHub Pages,
   - Netlify,
   - Vercel static output,
   - OpenAI Sites if configured.

6. Only after the user confirms scope, commit and deploy.

---

## 8. Suggested skills for next agent

- `qwenchance`
  - Required by repo instructions; also useful because the project is long-running and context-heavy.
- `orchestrator`
  - Use if planning assignment/order of work or writing a precise prompt for Gemini/Qwen.
- `impeccable`
  - Required by repo instructions for frontend polish/design changes.
- `fix-sticky-tables`
  - Use if sticky headers/frozen columns regress again.
- `spreadsheet-spec-writer`
  - Use if the manual markdown/report contract changes.
- `run-pipeline`
  - Use if regenerating monthly data or release outputs.
- `handoff`
  - Use again before context gets tight.

---

## 9. Sharp warnings

- Do not kill Node by name system-wide. Avoid:

  ```powershell
  taskkill /F /IM node.exe /T
  ```

  It can kill Playwright MCP, language servers, dev servers, and editor processes.

- Do not treat `C:\Users\georg\Downloads\รถใหม่_มิถุนายน 2569 (2)_Data.md` as model data.
  It is raw brand/fuel/province data and is valid for Sheets 1–6 and 9, not Sheets 7–8.

- Do not use the 33,077 value to override Sheet 4. Sheet 4/Data.md/program source of truth is
  33,070.

- Do not expose raw parquet files publicly.

- Do not assume a public link exists after `BUILD_RELEASE.bat`. It only builds local static files
  into `frontend\out`.

