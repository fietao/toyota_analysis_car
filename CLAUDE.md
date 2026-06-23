# Agent Instructions (Primary — All AI Agents)

**This is the primary, authoritative instruction file for *every* AI agent working in this
repository** — Claude Code, Codex, Gemini, local Qwen, subagents, and any other assistant.
Other entry files (`AGENTS.md`, `GEMINI.md`) are thin redirects that point here. Read and
follow this file.

> Local Qwen (via `claude-9arm`) is not agentic and will not read this file — the caller must
> paste any relevant rules directly into its prompt.

## Session Start

At the start of every conversation:
1. Read this file (`CLAUDE.md`) fully.
2. Invoke `/qwenchance` before taking action on the user's request.
3. Decide whether a skill, subagent, tool, plugin, or connector is a better fit than doing the
   work directly.

## Pick The Right Capability

For every request, decide whether the work needs:
- A global skill from `.agents/skills`.
- A local subagent skill.
- A built-in tool.
- A plugin or connector.
- A cheaper or narrower subagent.
- The `dev-tooling` agent for missing scripts, helpers, validators, or repeatable tools.
- Direct implementation by the current agent.

Use the smallest capable option. If a skill or subagent is used, say so briefly and explain why.

## Subagent Team & Boundaries

The orchestrating agent (Claude unless the user asks for a specialist directly) coordinates the
work — it understands what capability is needed, not the full implementation details of each one.

- Delegate Excel / data-cleaning details to `data-cleaner`.
- Delegate analyst workbook, pivot, and report details to `analyst`.
- Delegate coordination / review of the data pipeline to `reviewer`.
- Delegate script/tool creation or repair to `dev-tooling` — don't expand a subagent's role to
  cover a missing tool.
- Use global skills for reusable workflows (debugging, review, handoff, delegation, summaries);
  use local subagent skills for project-specific execution (Excel cleaning, workbook analysis,
  pivots, report generation). Keep subagent-specific skills near the subagent that owns them.
- Run subagents in parallel only when their inputs, outputs, and edited files are independent.
- Keep dependent chains sequential — e.g. `data-cleaner` must finish before `analyst`.

## Think Before Coding — Clarify

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before writing code or editing files for non-trivial requests:
- State assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them; don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- Ask 3-5 sharp questions when the request is vague, risky, or has multiple valid
  interpretations, and wait for answers when the decision materially affects implementation.
- For small, clear, low-risk tasks, proceed with the minimal change and verify it.

## Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No flexibility or configurability that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't improve adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it; don't delete it.

When your changes create orphans, remove imports, variables, or functions that your changes made
unused. Don't remove pre-existing dead code unless asked. Every changed line should trace
directly to the user's request.

## Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → write tests for invalid inputs, then make them pass.
- "Fix the bug" → write a test that reproduces it, then make it pass.
- "Refactor X" → ensure tests pass before and after.

For multi-step tasks, state a brief plan:

```text
1. [Step] -> verify: [check]
2. [Step] -> verify: [check]
3. [Step] -> verify: [check]
```

Strong success criteria let you loop independently. Weak criteria require clarification.

## Development Guardrails

**Never hardcode dates or periods.**
- Do not hardcode "current" years or months (e.g. `CURR_MONTH = 5`) to match a test template.
- Auto-detect the current period dynamically from the underlying dataset (e.g. the latest
  parquet) so the pipeline runs autonomously in the future.

**Offload boilerplate to the local LLM.**
- For mechanical, low-risk subjobs (scaffolding HTML tables, extracting CSS classes, bulk
  renames), delegate to the local LLM (`qwen-agent` / `claude-9arm`). Save your context window
  for high-level reasoning.

**Always use `impeccable` for frontend UI.**
- Don't manually scaffold raw HTML/CSS for web pages or dashboards from scratch.
- For designing, redesigning, or polishing the frontend, invoke the `impeccable` skill
  (e.g. `/impeccable craft`) for premium styling, correct Tailwind tokens, and professional layout.

**Frontend language — English chrome, consistent, no bilingual labels.**
- This is NOT an international/bilingual product. All UI chrome — labels, buttons, headers, nav,
  filter names, month names — is **English**, applied consistently across every page
  (`page.tsx`, `models.html`, `analyst.html`, and any new page).
- NEVER use dual "Thai / English" labels (e.g. `อัพเดทข้อมูล / Upload Data` → `Upload Data`).
- Months are always English (Jan…Dec) — never Thai, never mixed across pages.
- Keep Thai ONLY for data values that have no English form (fuel types `ชนิดเชื้อเพลิง`, รย vehicle-type
  descriptions). Brand names stay Latin. Tech terms stay English abbreviations (BEV, HEV, PHEV, ICE,
  YTD, MoM, YoY).
