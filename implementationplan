mplementation Plan: Car Registration Data Analysis Automation & Dashboard
Based on our interactive /grill-me session, I understand the final product requires two primary components:

Automated Backend Pipeline: A seamless drop-folder workflow that ingests raw Excel data, automatically triggers the data cleaning and pivoting scripts, and still generates the heavily formatted Analyst Excel reports.
Interactive Frontend Dashboard: A Next.js/React web dashboard offering rich visual representations of the car registration data (Powertrain trends, Brand rankings, BEV models).
To achieve this, I've broken the work into three phases.

Phase 1: Pipeline Structural Fixes
The background research agent uncovered several structural issues in the existing codebase that must be fixed before automation can begin:

Remove Orphaned Code: A duplicated test script was accidentally appended to the end of build_analyst.py. I will remove it.
Fix Pipeline Runner: run_pipeline.py currently points to non-existent file paths. I will update it to point correctly to .claude/scripts/model/build_BEV.py and .claude/scripts/calculation/build_analyst.py.
I have also havea refer file I want the program to use, which is refer/202605_รถใหม่_ยี่ห้อรถ-ชนิดเชื้อเพลิง-จังหวัด ปี 2564 - พฤษภาคม 2569 - Model.xlsx. 
same as the on refer [ ](<refer/202605_รถใหม่_ยี่ห้อรถ-ชนิดเชื้อเพลิง-จังหวัด ปี 2564 - พฤษภาคม 2569(calculation).xlsx>) in this the phase 1, I will ensure that the scripts correctly reference this file for all source data.
and it will use the refer file to generate the template output file, which is test_model_1.xlsx.
but it will use the data from the raw file to generate the output file, which is test_model_1.xlsx.
not the data from the refer file, but the data from the raw file, which is refer/202605_รถใหม่_ยี่ห้อรถ-ชนิดเชื้อเพลิง-จังหวัด ปี 2564 - พฤษภาคม 2569 - Model.xlsx.
Preserve Formatting and Pivot Sheets: Currently, build_analyst.py creates a brand-new workbook and uses pandas to raw-copy sheets, which destroys table formatting and drops intermediate pivot sheets. I will rebuild this logic: the script will instead use openpyxl to append the new Analyst sheets into a fresh copy of test_model_1.xlsx, perfectly preserving all prior work.
Phase 2: The "Drop Folder" Backend Automation
I will orchestrate the backend so that it requires zero manual script wrangling:

Create an input/ folder and an output/ folder.
Create an overarching watch_and_run.py (or similar trigger script) that:
Detects new raw Excel files dropped in the input/ folder.
Automatically deduces the correct Month/Year.
Sequentially runs build_cleaned.py -> build_BEV.py -> build_analyst.py.
Saves the final formatted Analyst Excel report into the output/ directory.
Automatically exports the finalized pivot tables as clean JSON data ready for the web dashboard.
Phase 3: Next.js Interactive Dashboard
I will build a modern, rich web frontend to visualize the data:

Stack: Next.js (React), TailwindCSS, Recharts.
Aesthetics: Premium dark mode, glassmorphism, dynamic micro-animations, and responsive layouts.
Features:
Registration by Powertrain trend charts.
Rank by Brand leaderboards.
BEV by Model breakdowns.
The dashboard will be statically generated or client-rendered using the JSON data exported from Phase 2.
IMPORTANT

Please review this plan carefully. Once you approve, I will immediately begin executing Phase 1 (Pipeline Structural Fixes) and update you as I progress through the steps.