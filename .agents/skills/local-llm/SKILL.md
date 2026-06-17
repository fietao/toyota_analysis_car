---
name: local-llm
description: Delegate self-contained coding tasks to a local Ollama model when Claude is rate-limited or to save quota. Use when the user says "hit the limit", "use local", "send to local LLM", "use offline", or for mechanical low-risk work (bulk edits, grep/search, boilerplate, test scaffolding, single-file rewrites). Do NOT use for design decisions, debugging that needs reasoning, or tasks that require this conversation's context.
---

# local-llm

Offload self-contained tasks to a local Ollama model via `ask_local.py`. No internet needed.

## The command

```bash
python C:/dev/ai-reading-car-analysis/.claude/scripts/ask_local.py "<self-contained task prompt>"
```

With a specific model:

```bash
python C:/dev/ai-reading-car-analysis/.claude/scripts/ask_local.py --model devstral:latest "<task>"
```

Pipe a long prompt:

```bash
echo "<task>" | python C:/dev/ai-reading-car-analysis/.claude/scripts/ask_local.py
```

## Available models (already pulled)

| Model | Size | Best for |
|---|---|---|
| `qwen2.5-coder:7b` | 4.7 GB | Default — fast, coding |
| `qwen3:8b` | 5.2 GB | Stronger reasoning |
| `devstral:latest` | 14 GB | Best overall coding quality |
| `qwen3-coder:30b` | 18 GB | Most capable, slowest |

Default is `qwen2.5-coder:7b`. Use `devstral` for harder tasks when speed is less critical.

## Writing the task prompt

The local model has **zero** context from this conversation. Every prompt must be standalone:

- **Absolute paths** for every file (`C:/dev/ai-reading-car-analysis/...`, not `./foo.py`)
- **Explicit inputs, outputs, and acceptance criteria** — what to change, what done looks like
- **No references** to "the file we discussed", "above", or prior turns

Bad: `clean up the imports`  
Good: `In C:/dev/ai-reading-car-analysis/.claude/scripts/build_cleaned.py, remove unused imports and sort the remaining ones alphabetically. Do not change any other code.`

## Workflow

1. Confirm the task is self-contained and low-risk.
2. Write a fully standalone prompt with absolute paths.
3. Run `ask_local.py` and read the response.
4. Verify the output meets the acceptance criteria before using it.

## Interactive use (when Claude is rate-limited)

The user can open a local chat session directly:

```
local.cmd                     # uses qwen2.5-coder:7b
local.cmd devstral:latest     # uses devstral
```

This is in `C:/dev/ai-reading-car-analysis/local.cmd`.

## When NOT to use

- Architecture or design decisions
- Debugging that needs multi-step reasoning
- Tasks that require reading this conversation's context
- Large multi-file jobs where a wrong edit would be hard to catch
