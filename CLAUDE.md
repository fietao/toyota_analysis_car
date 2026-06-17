# Claude Instructions

Claude should follow the shared project rules in `AGENTS.md`.

## Session Start

At the start of every conversation:
1. Read `AGENTS.md`.
2. Read this file.
3. Invoke `/qwenchance` before taking action on the user's request.
4. Check whether a skill, tool, plugin, connector, or subagent is a better fit than doing the work directly.

## Skill And Agent Selection

For every request, Claude should decide whether to use:
- A global skill from `.agents/skills`.
- A local subagent skill.
- A plugin or connector.
- A cheaper or narrower subagent.
- The dev-tooling agent for missing scripts, helpers, validators, or repeatable tools.
- Direct Claude implementation.

Use the smallest capable option. If a skill or subagent is used, say so briefly and explain why.

## Subagent Team

Claude is the orchestrator unless the user asks for a specialist directly.

- Delegate Excel/data cleaning details to `data-cleaner`.
- Delegate analyst workbook, pivot, and report details to `analyst`.
- Delegate coordination/review of the data pipeline to `reviewer`.
- Delegate script/tool creation or repair to `dev-tooling`.
- Run subagents in parallel only when their work is independent.
- Keep dependent chains sequential, such as `data-cleaner` before `analyst`.

## Clarify Before Non-Trivial Changes

Before writing code or editing files for non-trivial requests:
- Ask 3-5 sharp questions when the request is vague, risky, or has multiple valid interpretations.
- Name assumptions, edge cases, and tradeoffs.
- Wait for answers when the decision materially affects the implementation.
- For small, clear, low-risk tasks, proceed with the minimal change and verify it.

## Keep This File Thin

Do not duplicate the shared coding rules here.
Update `AGENTS.md` when changing rules that should apply to every AI agent.
