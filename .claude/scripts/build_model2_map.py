#!/usr/bin/env python3
"""
build_model2_map.py — Generate / update refer/model2_map.csv incrementally.

Rules (same as the existing BEV Series Name Table):
  - Strip trim/spec suffixes (PREMIUM, DYNAMIC, LONG RANGE, AWD, RWD, 4WD, etc.)
  - Keep model identity markers (numbers, letters that make it a distinct product)
  - Example: "WAVE125i" / "WAVE 125i" / "WAVE 125" → "Wave 125i"
             "WAVE110i" stays separate from "Wave 125i"
             "HILUX REVO Z" / "HILUX REVO ROCCO" → "Hilux Revo"

Incremental: only model names NOT already in model2_map.csv are sent to the LLM.
First run processes all ~8k names; every run after is tiny (new months only).

Usage:
    python .claude/scripts/build_model2_map.py
"""

import json
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests

# ── Project root ──────────────────────────────────────────────────────────────
def _find_project_root():
    p = Path(__file__).resolve()
    for parent in [p, *p.parents]:
        if (parent / "CLAUDE.md").exists():
            return parent
    raise RuntimeError("Could not find project root")

BASE        = _find_project_root()
RAW2_PATTERN = str(BASE / "raw data" / "รถใหม่_ยี่ห้อรถ-รุ่นรถ*.xlsx")
MAP_FILE     = BASE / "refer" / "model2_map.csv"
OLLAMA_URL   = "http://localhost:11434/api/generate"
MODEL        = "qwen3:8b"
BATCH_SIZE   = 50   # model names per LLM call


# ── File helpers ──────────────────────────────────────────────────────────────
def find_raw_file():
    import glob
    files = [f for f in glob.glob(RAW2_PATTERN) if "~$" not in f]
    if not files:
        raise FileNotFoundError(f"No file matching: {RAW2_PATTERN}")
    return Path(sorted(files)[-1])


def load_existing_map():
    if MAP_FILE.exists():
        df = pd.read_csv(MAP_FILE, encoding="utf-8-sig")
        return dict(zip(df["รุ่นรถ_raw"], df["รุ่นรถ2"]))
    return {}


def save_map(mapping):
    rows = sorted(mapping.items(), key=lambda x: x[0])
    df = pd.DataFrame(rows, columns=["รุ่นรถ_raw", "รุ่นรถ2"])
    MAP_FILE.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(MAP_FILE, index=False, encoding="utf-8-sig")


# ── Clustering ────────────────────────────────────────────────────────────────
def normalize_key(name: str) -> str:
    return str(name).strip().upper()


def cluster_by_prefix(names: list[str]) -> dict[str, list[str]]:
    """Group by first word — rough but effective for car names."""
    clusters: dict[str, list[str]] = {}
    for name in names:
        words = name.split()
        key = words[0] if words else name
        clusters.setdefault(key, []).append(name)
    return clusters


# ── LLM call ─────────────────────────────────────────────────────────────────
SYSTEM_PROMPT = """/no_think
You are cleaning Thai DLT (Department of Land Transport) car registration model names.

Rules (match the BYD/Tesla/MG naming convention in the data):
1. Strip trim and spec suffixes: PREMIUM, DYNAMIC, STANDARD, LONG RANGE, SHORT RANGE,
   AWD, RWD, FWD, 4WD, 2WD, 4x4, 4x2, MAX, PLUS, PRO, ELITE, LUXURY, ENTRY,
   range numbers like (410KM), (500KM), and similar.
2. Keep model identity markers: numbers and letters that distinguish different products.
   "Wave 110i" and "Wave 125i" are DIFFERENT models — keep them separate.
   "Hilux Revo" and "Hilux Revo Rocco" → same base → "Hilux Revo".
3. Use clean title case: "Wave 125i", "Hilux Revo", "D-Max", "PCX 160".
4. Output ONLY a valid JSON object — no explanation, no markdown fences.
   Keys are the exact input names. Values are the canonical names."""


def ask_llm(names: list[str]) -> dict[str, str]:
    names_str = "\n".join(f"- {n}" for n in names)
    prompt = f"{SYSTEM_PROMPT}\n\nModel names:\n{names_str}\n\nJSON:"

    try:
        resp = requests.post(
            OLLAMA_URL,
            json={"model": MODEL, "prompt": prompt, "stream": False,
                  "options": {"temperature": 0.1}},
            timeout=180,
        )
        resp.raise_for_status()
        raw = resp.json()["response"].strip()
        # Strip <think>...</think> blocks (qwen3 thinking mode)
        raw = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        # Strip markdown fences
        raw = re.sub(r"^```(?:json)?\s*", "", raw)
        raw = re.sub(r"\s*```$", "", raw)
        result = json.loads(raw)
        return {str(k): str(v) for k, v in result.items()}
    except json.JSONDecodeError as e:
        print(f"      JSON parse error: {e}", file=sys.stderr)
        print(f"      Raw response: {raw[:300]}", file=sys.stderr)
        return {}
    except Exception as e:
        print(f"      LLM error: {e}", file=sys.stderr)
        return {}


def to_title(name: str) -> str:
    return " ".join(w.capitalize() for w in name.strip().split())


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    sys.stdout.reconfigure(encoding="utf-8")

    raw_file = find_raw_file()
    print(f"Raw file : {raw_file.name}")

    df = pd.read_excel(str(raw_file), header=5)
    all_keys = sorted({
        normalize_key(m) for m in df["รุ่นรถ"].dropna().unique()
    })
    print(f"Unique รุ่นรถ in raw data : {len(all_keys):,}")

    existing = load_existing_map()
    print(f"Existing mappings        : {len(existing):,}")

    new_keys = [k for k in all_keys if k not in existing]
    print(f"New models to map        : {len(new_keys):,}")

    if not new_keys:
        print("Nothing to do — all models already mapped.")
        return

    # Cluster new keys by first word
    clusters = cluster_by_prefix(new_keys)
    singles = [members[0] for members in clusters.values() if len(members) == 1]
    multi_clusters = {k: v for k, v in clusters.items() if len(v) > 1}
    multi_names = [name for members in multi_clusters.values() for name in members]

    print(f"  Single-member (auto)   : {len(singles):,}")
    print(f"  Multi-member clusters  : {len(multi_clusters):,} clusters, "
          f"{len(multi_names):,} names")

    new_mappings: dict[str, str] = {}

    # Auto title-case singletons — no LLM needed
    for name in singles:
        new_mappings[name] = to_title(name)

    # Send multi-member clusters to LLM in batches
    total = len(multi_names)
    done = 0
    batch_num = 0

    for i in range(0, total, BATCH_SIZE):
        batch = multi_names[i:i + BATCH_SIZE]
        batch_num += 1
        pct = (i / total * 100) if total else 100
        print(f"  Batch {batch_num:>3} ({pct:4.0f}%): {len(batch)} models...",
              end=" ", flush=True)

        result = ask_llm(batch)
        for raw_key in batch:
            new_mappings[raw_key] = result.get(raw_key, to_title(raw_key))

        done += len(batch)
        print(f"done  [{done}/{total}]")

    # Merge and save
    existing.update(new_mappings)
    save_map(existing)

    total_saved = len(existing)
    unique_canonical = len(set(existing.values()))
    print(f"\nSaved {total_saved:,} mappings → {MAP_FILE.name}")
    print(f"Unique รุ่นรถ2 values : {unique_canonical:,}  "
          f"({total_saved / unique_canonical:.1f}x compression)")


if __name__ == "__main__":
    main()
