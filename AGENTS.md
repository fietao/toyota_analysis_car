# Shared Agent Instructions

These instructions apply to every AI agent working in this repository, including Claude,
Codex, subagents, and any other coding assistant.

## 0. Read The Right Context

At the start of each conversation:
- Read this file first when the agent supports `AGENTS.md`.
- If the agent has its own file, such as `CLAUDE.md`, read that too.
- Treat this file as the shared source of truth.
- Use agent-specific files only for behavior that applies to that agent.

## 1. Pick The Right Capability

Before starting work, decide whether the request needs:
- A global skill from `.agents/skills`.
- A local subagent skill.
- A built-in tool.
- A plugin or connector.
- A cheaper or narrower subagent.
- The dev-tooling agent to create or repair a script/tool.
- Direct implementation by the current agent.

Use the smallest capable option. If a skill or subagent is clearly relevant, use it.
If several options could work, briefly say which one you picked and why.

## 2. Team Boundaries

The orchestrating agent coordinates the work. It should understand what capability is
needed, not the full implementation details of every capability.

- Use global skills for reusable workflows such as debugging, review, handoff,
  delegation, and management summaries.
- Use local subagent skills for project-specific execution details such as Excel
  cleaning, workbook analysis, pivot creation, and report generation.
- Keep subagent-specific skills near the subagent that owns them.
- When a subagent needs a missing script, helper, validator, or repeatable tool,
  route that work to the dev-tooling agent instead of expanding the subagent's role.
- Run subagents in parallel only when their inputs, outputs, and edited files do not
  depend on each other.
- Do not run dependent work in parallel. If analyst output depends on data-cleaner
  output, data-cleaner must finish first.

## 3. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them; don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 4. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No flexibility or configurability that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 5. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't improve adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it; don't delete it.

When your changes create orphans:
- Remove imports, variables, or functions that your changes made unused.
- Don't remove pre-existing dead code unless asked.

Every changed line should trace directly to the user's request.

## 6. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" -> write tests for invalid inputs, then make them pass.
- "Fix the bug" -> write a test that reproduces it, then make it pass.
- "Refactor X" -> ensure tests pass before and after.

For multi-step tasks, state a brief plan:

```text
1. [Step] -> verify: [check]
2. [Step] -> verify: [check]
3. [Step] -> verify: [check]
```

Strong success criteria let you loop independently. Weak criteria require clarification.
