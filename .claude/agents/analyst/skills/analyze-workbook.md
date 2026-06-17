# Local Skill: Analyze Workbook

Owner: `analyst`

Use this skill when analyst work needs workbook structure, sheet names, columns,
formats, or quality observations before generating pivots or reports.

## Scope

- Inspect existing Excel workbooks.
- Summarize workbook structure for the analyst workflow.
- Use local LLM/script helpers when the workbook is large.

## Not This Skill

- Raw data cleaning belongs to `data-cleaner`.
- New helper script creation belongs to `dev-tooling`.
- General code review belongs to the global `scrutinize` skill.

## Reference

Use `.claude/commands/analyze-workbook.md` or `.claude/skills/analyze-excel.md`
for the runnable workflow.
