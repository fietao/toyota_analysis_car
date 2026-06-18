"""
Full monthly pipeline runner.

Usage:
    python .claude/scripts/run_pipeline.py           # full run (incl. model2 map)
    python .claude/scripts/run_pipeline.py --skip-map  # skip model2_map (already built)

Steps:
  0. build_model2_map.py → refer/model2_map.csv      (incremental, skippable)
  1. build_cleaned.py    → test_model_1.xlsx          (Data + master powertrain + BEV table)
  2. build_pivots.py     → appends BEV/BMW pivot sheets to test_model_1.xlsx
  3. build_analyst.py    → YYYYMM_รถใหม่_...(analyst).xlsx
"""

import subprocess, sys, os
from pathlib import Path

def _find_root():
    p = Path(__file__).resolve()
    for parent in p.parents:
        if (parent / "CLAUDE.md").exists():
            return parent
    raise RuntimeError("No project root found")

BASE = _find_root()
SCRIPTS = BASE / ".claude" / "scripts"

def run(script):
    print(f"\n{'='*60}")
    print(f"Running: {script.name}")
    print('='*60)
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(BASE),
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    if result.returncode != 0:
        print(f"\nERROR: {script.name} failed (exit {result.returncode})")
        sys.exit(result.returncode)

if __name__ == "__main__":
    skip_map = "--skip-map" in sys.argv

    if not skip_map:
        run(SCRIPTS / "build_model2_map.py")
    else:
        print("\n[Skipping build_model2_map.py — remove --skip-map to include]")

    run(SCRIPTS / "build_cleaned.py")
    run(SCRIPTS / "model" / "build_BEV.py")
    run(SCRIPTS / "calculation" / "build_analyst.py")
    print("\n\nPipeline complete.")
