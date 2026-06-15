# CLAUDE.md Planning Notes
Created: 2026-06-15

---

## What CLAUDE.md files we need

### 1. Orchestrator CLAUDE.md (create first)
**Location:** `C:\dev\ai-reading-car-analysis\CLAUDE.md`
**Who uses it:** The dev/lead Claude — reviews final output, fixes what workers can't, decides strategy

**Sections to include:**
- Project overview
- File map (what each file is, what it's for)
- Pipeline overview (raw → model → final)
- Known data quality issues
- Worker agent responsibilities
- What orchestrator NEVER delegates (final approval, Brand2 mapping decisions)
- How to use the analyze-excel skill
- Language: English only

### 2. Worker CLAUDE.md files (create later)
- `workers/data-cleaner/CLAUDE.md` — transforms raw data, adds Brand2
- `workers/brand-mapper/CLAUDE.md` — maintains and expands Brand2 mapping table
- `workers/analyst/CLAUDE.md` — queries and analyzes the model data
- `workers/presenter/CLAUDE.md` — creates reports/presentations (later)

---

## Orchestrator CLAUDE.md — Proposed Structure

```
# Car Registration Analysis — Orchestrator

## Project Overview
[what the project does]

## File Map
[3 files, what each is]

## Data Pipeline
raw data → Brand2 mapping → Model format → Final output

## Key Data Facts
[561 brands, header=5, fuel types, vehicle types, data quality issues]

## Known Issues & Rules
[retroactive updates, typo brands, non-brand entries]

## Worker Agents
[what each worker does, when to call them]

## Skills Available
[analyze-excel skill]

## What Orchestrator Handles Directly
[Brand2 decisions, final review, fixing worker errors]

## Language
English only. Thai colleagues use worker agents, not the orchestrator.
```

---

## Open Questions Before Writing

1. **Orchestrator voice/personality** — still to decide
2. **Where do worker agent files live?** Subfolder per worker or flat?
3. **Brand2 full mapping** — needs to be built before workers can run
4. **Should orchestrator also have access to Ollama?** (yes, via analyze-excel skill)
5. **Who triggers orchestrator?** Dev only, or Thai colleagues too?
