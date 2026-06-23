"""
Full monthly pipeline runner.

Usage:
    python run_pipeline.py                        # full run (incl. model2 map + analyst)
    python run_pipeline.py --skip-map             # skip model2_map rebuild
    python run_pipeline.py --skip-analyst         # master Model only (no analyst report)
    python run_pipeline.py --skip-map --skip-analyst

Steps:
  0. build_model2_map.py → refer/model2_map.csv      (skippable with --skip-map)
  1. build_cleaned.py    → master Model + master Cal Data sheet
  2. build_BEV.py        → appends approved BEV Series Name Table rows
  3. build_analyst.py    → YYYYMM analyst report     (skippable with --skip-analyst)
"""

import subprocess, sys, os
from pathlib import Path

BASE = Path(__file__).resolve().parent

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
    skip_map     = "--skip-map"     in sys.argv
    skip_analyst = "--skip-analyst" in sys.argv

    if not skip_map:
        run(BASE / "build_model2_map.py")
    else:
        print("\n[Skipping build_model2_map.py]")

    run(BASE / "build_cleaned.py")
    run(BASE / "build_BEV.py")

    if not skip_analyst:
        run(BASE / "build_analyst.py")
    else:
        print("\n[Skipping build_analyst.py]")

    print("\n\nPipeline complete.")
