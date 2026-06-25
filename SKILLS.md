# Skill Library

Browse and pick a skill. Invoke any skill by typing `/<name>` (e.g. `/run-pipeline`).

**Legend:** 🔧 project-specific (built for this car-analysis repo) · ⚠️ stale/broken — needs a fix before use · everything else is a general-purpose skill.

> Skills live in two folders: `.agents/skills/` (the master — all skills, read by every AI agent) and `.claude/skills/` (a runtime mirror Claude Code auto-syncs on use). Maintain skills in **`.agents/skills/`**.

---

## 1. 🔧 Project Pipeline (car-registration data)
The core monthly-data workflow for this repo.

| Skill | What it does |
|---|---|
| `run-pipeline` ⚠️ | Run the monthly pipeline (`build_cleaned → build_BEV → build_analyst`) in order, or individual steps. *Paths point at repo root; scripts moved to `backend/`.* |
| `pipeline-rebuild` ⚠️ | Playbook for the B1–B4 `build_cleaned.py` refactor. *B1–B6 are closed — largely obsolete.* |
| `export-master-model-txt` ⚠️ | Export master-model sheets to txt, diff vs the 202605 baseline, score accuracy, fix bugs, loop to 90%+. *References `build_cleaned.py` at root.* |
| `spreadsheet-spec-writer` | Write clear implementation specs for Excel workbooks / individual sheets. |

## 2. 🔧 AI Orchestration & Delegation
Coordinate work across Claude / Qwen / Gemini / Codex and manage context.

| Skill | What it does |
|---|---|
| `orchestrator` | Central planner — routes each task to the right executor and writes copy-paste prompts. Never writes code itself. |
| `qwen-agent` | Delegate mechanical, low-risk coding to local Qwen (`claude-9arm`) to save quota. |
| `local-llm` ⚠️ | Offload self-contained tasks to a local Ollama model. *Points at missing `ask_local.py` / `local.cmd`.* |
| `qwenchance` | Keep a long task on-track — breaks loops, watches context budget, triggers clean handoff. |
| `handoff` | Compact the current conversation into a handoff doc for another agent. |

## 3. Frontend / UI Design
| Skill | What it does |
|---|---|
| `impeccable` | Design, redesign, audit, polish any frontend UI — layout, color, typography, motion, accessibility, design systems. **Required by CLAUDE.md for all frontend work.** |

## 4. Planning & Requirements
Turn a fuzzy idea into a sharp, sequenced plan.

| Skill | What it does |
|---|---|
| `plan-master` | Research best approaches, grill until airtight, write a plan doc + a task-specific skill. |
| `grilling` | Relentlessly interview you to stress-test a plan before building. |
| `grill-me` | A relentless interview to sharpen a plan or design. |
| `grill-with-docs` | Same grilling, but also writes ADRs + glossary as you go. |
| `decision-mapping` | Turn a loose idea into a sequenced map of investigation tickets, driven one at a time. |
| `to-prd` | Turn the current conversation into a PRD and publish to the issue tracker. |
| `to-issues` | Break a plan/spec/PRD into independently-grabbable issues (vertical slices). |
| `request-refactor-plan` | Build a refactor plan of tiny commits via interview, file as a GitHub issue. |
| `implement` | Implement a piece of work from a PRD or set of issues. |
| `prototype` | Build a throwaway prototype (runnable terminal app, or toggleable UI variations). |

## 5. Debugging & Diagnosis
| Skill | What it does |
|---|---|
| `debug-mantra` | Four-mantra debugging discipline — reproduce, trace fail path, falsify hypothesis, cross-reference. |
| `diagnosing-bugs` | Diagnosis loop for hard bugs and performance regressions. |
| `post-mortem` | Write the canonical record of a fixed bug — root cause, mechanism, fix, validation. |

## 6. Code Review & Quality
| Skill | What it does |
|---|---|
| `review` | Review changes since a point along two axes — Standards + Spec — in parallel. |
| `scrutinize` | Outsider end-to-end review — questions intent, traces the real code path, concise + actionable. |
| `migrate-to-shoehorn` | Migrate test `as` assertions to `@total-typescript/shoehorn`. |
| `setup-pre-commit` | Set up Husky + lint-staged (Prettier, type-check, tests). |

## 7. Architecture & Domain Design
| Skill | What it does |
|---|---|
| `codebase-design` | Shared vocabulary for designing deep modules — seams, interfaces, testability. |
| `design-an-interface` | Generate radically different interface designs for a module via parallel sub-agents ("design it twice"). |
| `improve-codebase-architecture` | Scan for deepening opportunities, present as an HTML report, grill the one you pick. |
| `domain-modeling` | Build/sharpen the domain model — terminology, ADRs. |
| `ubiquitous-language` | Extract a DDD glossary to `UBIQUITOUS_LANGUAGE.md`, flag ambiguities. |

## 8. Testing
| Skill | What it does |
|---|---|
| `tdd` | Test-driven development — red-green-refactor, integration tests. |

## 9. Git & Safety
| Skill | What it does |
|---|---|
| `git-guardrails-claude-code` | Hooks that block dangerous git commands (push, reset --hard, clean, branch -D). |
| `resolving-merge-conflicts` | Resolve an in-progress git merge/rebase conflict. |

## 10. Issue Tracking & Triage
| Skill | What it does |
|---|---|
| `qa` | Interactive QA — report bugs conversationally, agent files GitHub issues. |
| `triage` | Move issues/PRs through a triage state machine — categorise, verify, write agent-ready briefs. |
| `setup-matt-pocock-skills` | One-time: configure issue tracker, triage labels, domain doc layout for the engineering skills. |

## 11. Writing & Docs
| Skill | What it does |
|---|---|
| `writing-fragments` | Mine you for raw writing fragments, append to one doc as future-article material. |
| `writing-shape` | Shape a markdown pile of notes into an article, paragraph by paragraph. |
| `writing-beats` | Assemble an article as a journey of beats, choose-your-own-adventure style. |
| `edit-article` | Restructure, clarify, and tighten an article draft. |
| `management-talk` | Rewrite engineer content for leadership (VP/PM/exec) and shape per channel (JIRA/Slack/email). |
| `teach` | Teach you a new skill or concept within this workspace. |
| `scaffold-exercises` | Create exercise directory structures (sections, problems, solutions, explainers) that pass linting. |
| `obsidian-vault` | Search, create, manage Obsidian notes with wikilinks and index notes. |
| `writing-great-skills` | Reference for writing/editing skills well — vocabulary and principles. |

## 12. Meta / Router
| Skill | What it does |
|---|---|
| `ask-matt` | A router — ask which skill or flow fits your situation. |
