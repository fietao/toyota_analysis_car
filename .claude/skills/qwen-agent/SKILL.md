---
name: qwen-agent
description: Delegate menial, well-scoped coding tasks to a cheap local Qwen (Ollama) via the `claude-9arm` command instead of burning Claude tokens/quota. Use when the work is mechanical and low-risk — bulk renames, formatting, boilerplate, find-replace, grep-style search & summarization, reading/condensing logs or files, test/docstring/comment scaffolding. Also use when the user says "use qwen", "delegate this", "send it to 9arm/qwen", or "do this cheaply". Do NOT use for architecture, design, debugging judgment, security-sensitive edits, or anything needing this conversation's context.
---

# qwen-agent

Offload **menial, self-contained** codegen/text tasks to a **local Qwen running in Ollama**, via the `claude-9arm` command. Keeps expensive Claude reasoning for work that needs it.

## What `claude-9arm` is (and isn't)

`claude-9arm` is a local wrapper (`C:\Users\georg\bin\claude-9arm` + `.cmd` + `.py`) that sends a prompt to the local Ollama model and prints its reply. **It is text-in / text-out — NOT an agent.** Qwen does **not** read, edit, or run anything itself.

```bash
claude-9arm -p "<self-contained task prompt>"     # prints qwen's answer to stdout
claude-9arm "<task>"                               # positional also works
echo "<task>" | claude-9arm                        # or stdin
claude-9arm --json -p "<task>"                      # full JSON; parse .response
claude-9arm -m qwen2.5-coder:3b -p "<task>"         # override model (faster on low VRAM)
claude-9arm --stats -p "<task>"                     # also print tok/s to stderr
```

Because qwen can't touch the filesystem, the **delegating agent (you) must**:
1. Put any needed file content **inside the prompt** — qwen sees only what you paste.
2. Take qwen's returned code/text and **apply the edits yourself** (Write/Edit).
3. **Verify** the result (run it / run tests) before reporting success.

## Model & config

- Default model `qwen2.5-coder:7b` (fits this 6 GB-VRAM laptop). Set `QWEN_MODEL` to switch.
- For speed on low VRAM: `ollama pull qwen2.5-coder:3b`, then `-m qwen2.5-coder:3b` (or `QWEN_MODEL`). Avoid models bigger than ~7B here — they spill from VRAM to CPU and crawl (see the 6 GB constraint).
- Requires Ollama running (`ollama serve`, normally a background service). Endpoint override: `OLLAMA_HOST`.
- Runs via the **Bash tool** (Git Bash, where `~/bin` is on PATH). For PowerShell, add `C:\Users\georg\bin` to the user PATH.

## Writing the task prompt (most important step)

qwen has **zero** context from this conversation. A vague prompt is the #1 failure mode. Every prompt must be standalone:

- **Paste the exact input** (the code/text to transform) into the prompt — qwen can't open files.
- **Explicit output + acceptance criteria** — what to produce, what "done" looks like.
- **No references** to "the file we discussed", "above", or prior turns.
- Treat qwen as a capable-but-literal junior: spell out steps, keep scope tight, ask for code only (it may still wrap output in ```` ``` ```` fences — strip them).

Bad: `clean up the imports`
Good: `Here is a Python file:\n<paste full contents>\nReturn the same file with unused imports removed and the remaining imports sorted alphabetically. Change nothing else. Output only the code.`

## Size each task to the model

Local Qwen has a far smaller context window than Claude and limited VRAM. Keep each delegation bounded:

- One file (or a few small ones) per run; one directory or one log segment per run.
- Don't paste huge files or many files at once — split into independent chunks, one `claude-9arm` call each.
- Overflow symptoms: truncated output, ignored later instructions, omitted parts → split smaller and retry.
- If a job needs whole-codebase context to do correctly, it isn't a qwen task — keep it yourself.

## Return contract

- **Default:** qwen's reply prints to stdout — read it, then apply + verify.
- **Parse it:** add `--json` and read the `.response` field.
- **Parallel (2+ unrelated jobs):** redirect to a log and use the Bash tool's `run_in_background: true`, then read each log on completion:

  ```bash
  claude-9arm -p "<task>" > /tmp/qwen-<label>.log 2>&1
  ```

## Workflow checklist

1. Confirm the task is menial and low-risk (see description). If it needs design judgment or this chat's context, **do it yourself**.
2. Size it to the model — split large jobs into bounded per-file chunks.
3. Write a fully self-contained prompt with the input pasted in and clear acceptance criteria.
4. Run `claude-9arm -p "..."` (foreground), or background-redirect for parallel jobs.
5. **Apply** qwen's output to the repo yourself (Write/Edit).
6. **Verify** it meets the acceptance criteria (run it / tests) before reporting success — qwen is cheaper and less reliable.

## One-time setup (optional, removes repeated prompts)

To stop per-call permission prompts on delegated runs, add a Bash allow rule (via the `update-config` skill, or by editing settings):

```json
{ "permissions": { "allow": ["Bash(claude-9arm:*)"] } }
```

## When NOT to delegate

Architecture/design, debugging that needs reasoning, security-sensitive changes, anything requiring this conversation's context, or tasks where a wrong cheap-model edit is costly to catch. When in doubt, keep it.

> Future upgrade (not set up): a local Anthropic-compatible gateway (e.g. LiteLLM / claude-code-router) fronting Ollama would let `claude-9arm` run the full agentic Claude Code harness on a local model — making qwen able to read/edit/run on its own. Out of scope on this hardware (the headless harness + a usable model won't fit 6 GB VRAM).
