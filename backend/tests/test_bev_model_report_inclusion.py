"""test_bev_model_report_inclusion.py — model-grain Powertrain removal + BEV review contract.

Under the new contract (see .agents/skills/reliable-series-powertrain/SKILL.md and
backend/model_map.py):
  - General model rows produced by add_derived_columns never carry Powertrain or
    include_in_bev_model_report — that enrichment was removed entirely from the model
    foundation; Powertrain now belongs to the fuel grain only.
  - Approved BEV inclusion is decided solely by backend/config/model_powertrain_review.csv
    via model_map.approved_bev_keys(), which requires review_status=approved AND
    candidate_powertrain=BEV, plus evidence, reviewer, and reviewed_at on any approved
    row. That is tested here through a minimal isolated review file, not through the
    model pipeline.

No pytest — matches the existing test_*.py convention. Runs from any directory. Exits 0
on PASS, 1 on FAIL.
"""
import csv
import os
import sys
import tempfile
from pathlib import Path
import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

TESTS = Path(__file__).resolve().parent
BACKEND = TESTS.parent
sys.path.insert(0, str(BACKEND))

from build_cleaned import add_derived_columns, load_powertrain_map
import model_map
from export_manual_report import bev_model_report_slice

powertrain_map = load_powertrain_map(str(BACKEND / "config" / "powertrain_map.csv"))
brand_csv_map = load_powertrain_map(str(BACKEND / "config" / "brand_map.csv"), "brand", "brand2")
merged_brand2_map = {k.upper(): v for k, v in brand_csv_map.items()}

failures = []


def base_maps():
    return {
        "powertrain_map": powertrain_map,
        "merged_brand2_map": merged_brand2_map,
        "model_name_map": {},
        "unknown_fuels": set(),
    }


def test_model_rows_never_get_powertrain():
    """add_derived_columns must never attach Powertrain/include_in_bev_model_report to model rows,
    even for a model whose fuel-grain counterpart is electric."""
    df_model = pd.DataFrame([{"ยี่ห้อรถ": "BYD", "รุ่นรถ": "ATTO 3", "จำนวนรถ": 10}])
    df_fuel = pd.DataFrame([{"ยี่ห้อรถ": "BYD", "ชนิดเชื้อเพลิง": "ไฟฟ้า", "จำนวนรถ": 10}])

    df_model, _ = add_derived_columns(df_model, df_fuel, base_maps())

    if "Powertrain" in df_model.columns:
        failures.append("model rows carry a Powertrain column (must be fuel-only)")
    if "include_in_bev_model_report" in df_model.columns:
        failures.append("model rows carry include_in_bev_model_report (removed from model foundation)")


def _write_review(rows):
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    tmp = Path(path)
    with open(tmp, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=model_map.REVIEW_HEADERS)
        w.writeheader()
        w.writerows(rows)
    return tmp


def test_approved_bev_requires_evidence_reviewer_reviewed_at():
    """review_status=approved without evidence/reviewer/reviewed_at must raise, not silently pass."""
    tmp = _write_review([{
        "brand2": "BYD", "raw_model": "ATTO 3", "model2": "ATTO 3",
        "candidate_powertrain": "BEV", "review_status": "approved",
        "evidence": "", "reviewer": "", "reviewed_at": "", "notes": "",
    }])
    orig_path = model_map.MODEL_POWERTRAIN_REVIEW_PATH
    model_map.MODEL_POWERTRAIN_REVIEW_PATH = tmp
    try:
        model_map.load_model_powertrain_review()
        failures.append("approved BEV row missing evidence/reviewer/reviewed_at did not raise")
    except ValueError:
        pass
    finally:
        model_map.MODEL_POWERTRAIN_REVIEW_PATH = orig_path
        tmp.unlink()


def test_approved_bev_with_full_evidence_is_included():
    """A fully-evidenced approved BEV row surfaces through approved_bev_keys()."""
    tmp = _write_review([{
        "brand2": "BYD", "raw_model": "ATTO 3", "model2": "ATTO 3",
        "candidate_powertrain": "BEV", "review_status": "approved",
        "evidence": "brochure.pdf", "reviewer": "jet", "reviewed_at": "2026-07-22",
        "notes": "",
    }])
    orig_path = model_map.MODEL_POWERTRAIN_REVIEW_PATH
    model_map.MODEL_POWERTRAIN_REVIEW_PATH = tmp
    try:
        keys = model_map.approved_bev_keys()
        expected = model_map.normalize_key("BYD", "ATTO 3")
        if expected not in keys:
            failures.append(f"fully-evidenced approved row not in approved_bev_keys(): {keys}")
    finally:
        model_map.MODEL_POWERTRAIN_REVIEW_PATH = orig_path
        tmp.unlink()


def _model_rows():
    return pd.DataFrame([
        {"ยี่ห้อรถ2": "BYD", "รุ่นรถ": "ATTO 3", "รุ่นรถ2": "ATTO 3", "จำนวนรถ": 10},
        {"ยี่ห้อรถ2": "BYD", "รุ่นรถ": "DOLPHIN", "รุ่นรถ2": "DOLPHIN", "จำนวนรถ": 7},
    ])


def test_sheet7_8_slice_includes_whitelisted_excludes_others():
    """Sheets 7-8 must include only the whitelisted (Brand2, raw model) pair, not
    every model row for that brand — inclusion is per-model, not inferred."""
    tmp = _write_review([{
        "brand2": "BYD", "raw_model": "ATTO 3", "model2": "ATTO 3",
        "candidate_powertrain": "BEV", "review_status": "approved",
        "evidence": "brochure.pdf", "reviewer": "jet", "reviewed_at": "2026-07-22",
        "notes": "",
    }])
    orig_path = model_map.MODEL_POWERTRAIN_REVIEW_PATH
    model_map.MODEL_POWERTRAIN_REVIEW_PATH = tmp
    try:
        out = bev_model_report_slice(_model_rows())
        models = set(out["รุ่นรถ"])
        if models != {"ATTO 3"}:
            failures.append(f"sheet7/8 slice should contain only approved BEV models: {models}")
    finally:
        model_map.MODEL_POWERTRAIN_REVIEW_PATH = orig_path
        tmp.unlink()


def test_sheet7_8_slice_empty_whitelist_is_empty_not_crash():
    """No approved BEV rows must yield an empty Sheets 7-8 slice, not raise."""
    tmp = _write_review([])
    orig_path = model_map.MODEL_POWERTRAIN_REVIEW_PATH
    model_map.MODEL_POWERTRAIN_REVIEW_PATH = tmp
    try:
        out = bev_model_report_slice(_model_rows())
        if not out.empty:
            failures.append(f"empty review table should yield empty slice, got {len(out)} row(s)")
    finally:
        model_map.MODEL_POWERTRAIN_REVIEW_PATH = orig_path
        tmp.unlink()


if __name__ == "__main__":
    test_model_rows_never_get_powertrain()
    test_approved_bev_requires_evidence_reviewer_reviewed_at()
    test_approved_bev_with_full_evidence_is_included()
    test_sheet7_8_slice_includes_whitelisted_excludes_others()
    test_sheet7_8_slice_empty_whitelist_is_empty_not_crash()
    if failures:
        print(f"FAIL — {len(failures)} issue(s) in bev-model-report-inclusion tests:")
        for f in failures:
            print(f)
        sys.exit(1)
    print("PASS — All bev-model-report-inclusion tests passed successfully.")
