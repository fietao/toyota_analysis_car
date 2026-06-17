#!/usr/bin/env python3
"""
build_model2_map.py — Build refer/model2_map.csv from the refer Model.xlsx.

Extracts the รุ่นรถ → รุ่นรถ2 mapping directly from columns G and H of the
Data sheet in the refer Model.xlsx. No LLM needed — the refer file already
has the canonical names.

Any raw model names in the raw data that are NOT in the refer file get
title-cased as a fallback.

Usage:
    python .claude/scripts/build_model2_map.py
"""

import glob
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")


def _find_project_root():
    p = Path(__file__).resolve()
    for parent in [p, *p.parents]:
        if (parent / "CLAUDE.md").exists():
            return parent
    raise RuntimeError("Could not find project root")


BASE         = _find_project_root()
REFER_PATTERN = str(BASE / "refer" / "*- Model.xlsx")
RAW2_PATTERN  = str(BASE / "raw data" / "รถใหม่_ยี่ห้อรถ-รุ่นรถ*.xlsx")
MAP_FILE      = BASE / "refer" / "model2_map.csv"


def find_file(pattern, label):
    files = [f for f in glob.glob(pattern) if "~$" not in f]
    if not files:
        raise FileNotFoundError(f"No {label} file found: {pattern}")
    return Path(sorted(files)[-1])


def to_title(name: str) -> str:
    return " ".join(w.capitalize() for w in str(name).strip().split())


def main():
    refer_file = find_file(REFER_PATTERN, "refer Model")
    raw2_file  = find_file(RAW2_PATTERN,  "raw model")

    print(f"Refer file : {refer_file.name}")
    print(f"Raw file   : {raw2_file.name}")

    # Extract G→H mapping from refer Data sheet (header at row 6)
    ref = pd.read_excel(str(refer_file), sheet_name="Data", header=6, usecols=[6, 7])
    ref.columns = ["รุ่นรถ_raw", "รุ่นรถ2"]
    ref = ref.dropna(subset=["รุ่นรถ_raw", "รุ่นรถ2"])
    ref["รุ่นรถ_raw"] = ref["รุ่นรถ_raw"].astype(str).str.strip().str.upper()
    ref["รุ่นรถ2"]    = ref["รุ่นรถ2"].astype(str).str.strip()
    refer_map = dict(zip(ref["รุ่นรถ_raw"], ref["รุ่นรถ2"]))
    print(f"Refer mappings extracted : {len(refer_map):,}")

    # Get all unique raw model names from raw data
    df_raw = pd.read_excel(str(raw2_file), header=5)
    all_raw = sorted({
        str(m).strip().upper()
        for m in df_raw["รุ่นรถ"].dropna().unique()
    })
    print(f"Unique รุ่นรถ in raw data : {len(all_raw):,}")

    # Build final map: refer mapping first, title-case fallback for unknowns
    missing = [k for k in all_raw if k not in refer_map]
    print(f"Not in refer (fallback)  : {len(missing):,}")

    final_map = {k: refer_map.get(k, to_title(k)) for k in all_raw}

    # Save
    rows = sorted(final_map.items())
    df_out = pd.DataFrame(rows, columns=["รุ่นรถ_raw", "รุ่นรถ2"])
    MAP_FILE.parent.mkdir(parents=True, exist_ok=True)
    df_out.to_csv(str(MAP_FILE), index=False, encoding="utf-8-sig")

    unique_canonical = df_out["รุ่นรถ2"].nunique()
    print(f"\nSaved {len(final_map):,} mappings → {MAP_FILE.name}")
    print(f"Unique รุ่นรถ2 values : {unique_canonical:,}  "
          f"({len(final_map) / unique_canonical:.1f}x compression)")


if __name__ == "__main__":
    main()
