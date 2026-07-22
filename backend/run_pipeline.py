"""
Full monthly pipeline runner.

Usage:
    python run_pipeline.py                        # full run
    python run_pipeline.py --skip-analyst         # master Model only (no analyst report)

Steps:
  1. build_cleaned.py    → cleaned model/fuel parquets (model names from model_map.csv;
                            fuel Powertrain from powertrain_map.csv; model grain has no Powertrain)
  2. build_analyst.py    → YYYYMM analyst report     (skippable with --skip-analyst)

New model rows are appended as pending to config/model_powertrain_review.csv for
human review. Approved BEV rows from that file control Sheets 7-8 only.
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
    skip_analyst = "--skip-analyst" in sys.argv

    run(BASE / "build_cleaned.py")

    if not skip_analyst:
        run(BASE / "build_analyst.py")
    else:
        print("\n[Skipping build_analyst.py]")

    print("\n\nPipeline complete.")
