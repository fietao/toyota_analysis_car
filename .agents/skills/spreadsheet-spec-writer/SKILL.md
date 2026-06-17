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

## Tone

Write as a handoff to an implementation agent. Be plain, calm, and explicit. If the user is still exploring, call it a draft spec and list the questions that would make it final.
