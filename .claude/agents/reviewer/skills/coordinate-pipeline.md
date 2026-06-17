# Local Skill: Coordinate Pipeline

Owner: `reviewer`

Use this skill when the task is to coordinate multiple subagents, review pipeline
status, or decide what can run in parallel.

## Scope

- Decide whether the request needs `data-cleaner`, `analyst`, `dev-tooling`, or a
  global skill.
- Track dependencies between subagents.
- Run independent subagents in parallel when their inputs and outputs do not overlap.
- Keep dependent chains sequential.

## Parallel Rules

- `data-cleaner` must finish before `analyst` when analyst work depends on fresh
  cleaned/model output.
- `dev-tooling` can run in parallel with analysis only when it edits different files.
- Review-only work can usually run in parallel with read-only workbook inspection.

## Not This Skill

- Do not run scripts directly unless explicitly asked.
- Do not edit code or mappings without permission.
- Do not close work while warnings or errors are still unreported.
