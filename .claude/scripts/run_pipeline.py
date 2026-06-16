"""
Full monthly pipeline runner.

Usage:
    python .claude/scripts/run_pipeline.py

Steps:
  1. Run build_model.py   → test_model_1.xlsx
  2. Run build_analyst.py → YYYYMM_รถใหม่_...(analyst).xlsx
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
    run(SCRIPTS / "build_model.py")
    run(SCRIPTS / "build_analyst.py")
    print("\n\nPipeline complete.")
