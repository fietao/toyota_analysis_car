---
name: spreadsheet-spec-writer
description: Write clear implementation specs for spreadsheet workbooks or individual sheets. Use when the user asks to plan, reverse engineer, document, rewrite, or hand off spreadsheet requirements, especially from Excel workbooks, screenshots, raw data notes, pivot/table descriptions, filters, formulas, formatting, or sheet-by-sheet instructions.
---

# Spreadsheet Spec Writer

## Purpose

Create a plain-English implementation spec that another agent or developer can follow without guessing. The spec should describe what to build, where data comes from, how it is transformed, how the sheet should look, how filters/formulas behave, and how to verify the result.

Use this skill to write the spec only. Do not edit workbook/code unless the user explicitly asks for implementation.

## Workflow

1. Identify the requested workbook, sheet, or table scope.
2. Inspect only the needed source artifacts: workbook sheets, screenshots, CSVs, raw data files, existing scripts, or user notes.
3. Separate **template/format source** from **data source**.
4. Write assumptions and unresolved questions before the spec if they affect implementation.
5. Produce a spec with stable sections and concrete cell/range details.
6. Include verification checks that prove the implementation matches the spec.

## Required Spec Sections

Use these sections unless the user asks for another shape:

```text
Goal
Scope
Inputs
Output Sheet(s)
Data Rules
Layout And Formatting
Filters And Interactions
Formulas Or Calculations
Sorting And Grouping
Validation Checks
Open Questions
```

Keep each section short and direct. Prefer tables or bullet lists when they reduce ambiguity.

## Formulas Over Hard-Coded Values

Grand Total cells and any other summary/aggregate cells must always be written as Excel formulas (e.g., `=SUM(C8:C20)`), never as hard-coded numbers. The formula range should be derived from the actual data row range at write-time. This ensures the cell stays correct if rows are added or removed, and makes the formula visible and auditable in the formula bar.

## Rules For Spreadsheet Specs

- Save all generated specifications to the `specs/` directory in the root of the workspace (e.g., `specs/<sheet_name>_spec.md`).
- Name every workbook, sheet, and file path when known.
- Give exact sheet names, column names, header rows, and ranges when known.
- Say which artifact is only a visual template and which artifact is the live data source.
- Do not say "same as reference" by itself. List the actual column widths, headers, filters, formulas, hidden rows, colors, and row/column positions that matter.
- Mark stale, manual, or suspicious reference behavior as optional instead of copying it blindly.
- Describe fallback behavior for missing mappings or blanks.
- State whether the output should be a real Excel PivotTable, an Excel table, or a static pivot-like range.
- State whether filters are visual defaults, actual AutoFilter metadata, hidden rows, slicers, or pivot filters.
- Keep implementation language simple enough that the user can read it, but precise enough for a coder.

## Data Source Pattern

For each output column, specify:

```text
Output column | Source file/sheet/column | Transformation | Missing-value behavior
```

Example:

```text
รุ่นรถ2 | refer/model2_map.csv รุ่นรถ_raw -> รุ่นรถ2 | key by upper/trimmed รุ่นรถ | if missing, keep รุ่นรถ
```

## Filter Pattern

For every filter, specify:

```text
Filter label | Range/field | Default selected values | Hidden/excluded values | User interaction expected
```

Example:

```text
Powertrain | D:D / column 4 | BEV + BEV Major visible | OTH hidden by default | user can clear filter to see all
```

## Formatting Pattern

For formatting, specify only what matters:

```text
Range | Formatting
A1:D1 | bold, light blue fill, AutoFilter enabled
A:D | widths A=23.63, B=42.27, C=20.73, D=20.73
Data rows | height 17.5, normal font
```

Do not include empty styled ranges unless they are intentionally part of the output.

## Validation Pattern

Every spec must end with checks such as:

- Sheet exists with exact name.
- Header row matches expected labels.
- Row count matches source-derived expected count.
- Required filters exist on the expected range.
- Totals reconcile to source data.
- No unexpected blanks in key columns.
- Known sample records map correctly.

## Why Specs Get Ignored — And How To Prevent It

Agents drift from specs for these predictable reasons. Address each one while writing:

### 1. No MUST / MUST NOT signal
Agents treat everything as a suggestion unless you mark priority. Use:
- `MUST` — non-negotiable; fail the implementation if missing
- `MUST NOT` — explicitly forbidden; list the wrong thing the agent will naturally do
- `SHOULD` — default behavior unless the user overrides
- `MAY` — optional

Example:
```
B1 MUST contain the static text "(Multiple Items)".
B1 MUST NOT contain a comma-separated list of car types.
```

### 2. Visual description without machine-readable equivalent
"Grey column" tells a human what to see. It does not tell code what to write.
Every color, border, font, or fill in the spec MUST include the exact hex value and the property name.

Example:
```
Year-total and Grand Total columns: fill=solid, fgColor=#D9D9D9 (grey).
NOT: "make it grey".
```

### 3. No negative examples
Agents fill gaps with plausible-looking wrong behavior. For every non-obvious requirement, add a "DO NOT" line that names the thing the agent will naturally do wrong.

Example:
```
Grand Total row: MUST always exist as the last row. MUST NOT be omitted when data is empty.
Grey fill: MUST cover the header row AND all data rows below. MUST NOT apply only to data rows.
```

### 4. No verification gate in the spec
Verification checks that are vague (e.g., "totals reconcile") get skipped. Write checks the implementation agent can run deterministically:

```
CHECK: cell A{last_row} == "Grand Total"
CHECK: fill of N6 == #D9D9D9
CHECK: fill of N{last_row} == #D9D9D9
CHECK: len(unique fills in column N data rows) == 1 and that fill == #D9D9D9
```

### 5. Spec not referenced at implementation time
Agents re-derive requirements from memory rather than reading the spec. The spec MUST include this line at the top of every spec file:

```
IMPLEMENTATION NOTE: Read this spec completely before writing any code.
After each section is implemented, tick the verification check for that section.
```

### 6. No anti-pattern section
Document the specific wrong behaviors that were previously produced. Agents learn from negative examples as well as positive ones.

```
## Anti-Patterns (Previous Wrong Implementations)
- B1 showed "BEV Major, BEV, OTH" — this is wrong; it must be "(Multiple Items)"
- Grand Total row was missing — it must always be written, even if all values are 0
- Year-total column header row was blue — it must be grey (#D9D9D9) same as data rows
```

## Color Reference From Refer Sheet

When a `refer/` Excel workbook exists, always read actual cell fill colors from it — do not guess or hardcode hex values.
- Open the refer workbook and read the `fgColor` of the target cell.
- Record colors as hex `#RRGGBB` (from `refer/<filename>`, sheet `<sheetname>`, cell `<ref>`)
- If no refer sheet exists, document as `unknown` and list under Open Questions for the user to confirm visually.

## Tone

Write as a handoff to an implementation agent. Be plain, calm, and explicit. If the user is still exploring, call it a draft spec and list the questions that would make it final.
