# Local Skill: Build Or Repair Tool

Owner: `dev-tooling`

Use this skill when another subagent needs a script, helper, validator, or repeatable
tool to do its job safely.

## Scope

- Build small, focused scripts under `.claude/scripts`.
- Repair existing scripts when the issue is technical and reproducible.
- Add validation/reporting helpers for subagents.
- Provide a clear command and success check.

## Required Inputs

- Requesting subagent.
- Target script or new helper name.
- Exact input files and expected outputs.
- Whether the tool may write files.
- Verification command or observable success result.

## Boundaries

- Do not decide domain mappings or analyst calculations.
- Do not rewrite large workflows without explicit approval.
- Do not move scripts unless the orchestrator asks for a layout migration.
