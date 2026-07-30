"""test_bev_candidates.py — build_candidates() / write_outputs() tests for the New BEV
Model Watchlist.

No pytest — matches the existing test_*.py convention. Runs from any directory. Exits 0
on PASS, 1 on FAIL.
"""
import csv
import json
import shutil
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

TESTS = Path(__file__).resolve().parent
BACKEND = TESTS.parent
sys.path.insert(0, str(BACKEND))

import bev_candidates as bc
import model_map

failures = []


def _check(label, cond, detail=""):
    if not cond:
        failures.append(f"{label}: {detail}")


def _row(brand2, raw_model, model2, units, year=2569, month="Jun"):
    return {"ยี่ห้อรถ2": brand2, "รุ่นรถ": raw_model, "รุ่นรถ2": model2, "ปี": year, "เดือน": month, "จำนวนรถ": units}


def _review_row(brand2, raw_model, model2, review_status, candidate_powertrain=""):
    return {
        "brand2": brand2, "raw_model": raw_model, "model2": model2,
        "candidate_powertrain": candidate_powertrain, "review_status": review_status,
        "evidence": "e" if review_status == "approved" else "",
        "reviewer": "r" if review_status == "approved" else "",
        "reviewed_at": "2026-07-01" if review_status == "approved" else "",
        "notes": "",
    }


def _review_dict(rows):
    return {model_map.normalize_key(r["brand2"], r["raw_model"]): r for r in rows}


# ---- 7. latest-period-only filtering ----------------------------------------------
def test_latest_period_only():
    df = pd.DataFrame([
        _row("BYD", "BYD SEAL EV", "SEAL", 50, year=2569, month="May"),  # older period
        _row("BYD", "BYD SEAL EV", "SEAL", 30, year=2569, month="Jun"),  # latest period
    ])
    review = _review_dict([_review_row("BYD", "BYD SEAL EV", "SEAL", "pending")])
    candidates, ly, lm = bc.build_candidates(df, review)
    _check("latest_period_year_month", (ly, lm) == (2569, 6), (ly, lm))
    _check("latest_period_units_only_latest_month", candidates and candidates[0]["units"] == 30, candidates)


# ---- 8. pending-only filtering -----------------------------------------------------
def test_pending_only():
    df = pd.DataFrame([
        _row("BYD", "BYD SEAL EV", "SEAL", 10),
        _row("BYD", "BYD DOLPHIN EV", "DOLPHIN", 10),
    ])
    review = _review_dict([
        _review_row("BYD", "BYD SEAL EV", "SEAL", "pending"),
        _review_row("BYD", "BYD DOLPHIN EV", "DOLPHIN", "approved", "BEV"),  # already approved -> not a candidate
    ])
    candidates, _, _ = bc.build_candidates(df, review)
    names = {c["raw_model"] for c in candidates}
    _check("pending_only_includes_pending", "BYD SEAL EV" in names, names)
    _check("pending_only_excludes_approved", "BYD DOLPHIN EV" not in names, names)


def test_pending_only_excludes_rejected():
    df = pd.DataFrame([_row("BYD", "BYD SEAL EV", "SEAL", 10)])
    review = _review_dict([_review_row("BYD", "BYD SEAL EV", "SEAL", "rejected")])
    candidates, _, _ = bc.build_candidates(df, review)
    _check("excludes_rejected", candidates == [], candidates)


# ---- 9. duplicate aggregation and unit totals -------------------------------------
def test_duplicate_aggregation():
    """Same brand2+raw_model+model2 across multiple provinces/vehicle-type rows in the
    latest period must collapse into one candidate with summed units."""
    df = pd.DataFrame([
        _row("BYD", "BYD SEAL EV", "SEAL", 10),
        _row("BYD", "BYD SEAL EV", "SEAL", 15),
        _row("BYD", "BYD SEAL EV", "SEAL", 7),
    ])
    review = _review_dict([_review_row("BYD", "BYD SEAL EV", "SEAL", "pending")])
    candidates, _, _ = bc.build_candidates(df, review)
    _check("duplicate_aggregation_single_row", len(candidates) == 1, candidates)
    _check("duplicate_aggregation_summed_units", candidates[0]["units"] == 32, candidates)


# ---- 10. stable sorting -------------------------------------------------------------
def test_stable_sorting():
    df = pd.DataFrame([
        _row("ZBRAND", "ZBRAND EV LOW", "EV LOW", 5),      # electric_name_marker, low units
        _row("ABRAND", "ABRAND EV HIGH", "EV HIGH", 500),  # electric_name_marker, high units
        _row("BYD", "BYD ATTO 3 PRO", "ATTO 3", 100),       # approved_family_match
    ])
    review = _review_dict([
        _review_row("ZBRAND", "ZBRAND EV LOW", "EV LOW", "pending"),
        _review_row("ABRAND", "ABRAND EV HIGH", "EV HIGH", "pending"),
        _review_row("BYD", "BYD ATTO 3 PRO", "ATTO 3", "pending"),
        _review_row("BYD", "BYD ATTO 3", "ATTO 3", "approved", "BEV"),
    ])
    candidates, _, _ = bc.build_candidates(df, review)
    order = [(c["reason_code"], c["brand"]) for c in candidates]
    _check(
        "stable_sort_family_first_then_units_desc",
        order == [("approved_family_match", "BYD"), ("electric_name_marker", "ABRAND"), ("electric_name_marker", "ZBRAND")],
        order,
    )


# ---- 11. empty watchlist ------------------------------------------------------------
def test_empty_watchlist_no_matches():
    df = pd.DataFrame([_row("BRAND", "BRAND DIESEL PICKUP", "PICKUP", 10)])
    review = _review_dict([_review_row("BRAND", "BRAND DIESEL PICKUP", "PICKUP", "pending")])
    candidates, ly, lm = bc.build_candidates(df, review)
    _check("empty_watchlist", candidates == [], candidates)
    _check("empty_watchlist_still_has_period", (ly, lm) == (2569, 6), (ly, lm))


def test_empty_dataframe():
    candidates, ly, lm = bc.build_candidates(pd.DataFrame(columns=["ปี", "เดือน", "ยี่ห้อรถ2", "รุ่นรถ", "รุ่นรถ2", "จำนวนรถ"]), {})
    _check("empty_df_no_candidates", candidates == [], candidates)
    _check("empty_df_no_period", (ly, lm) == (None, None), (ly, lm))


# ---- 12. JSON/CSV artifact schema --------------------------------------------------
def test_write_outputs_schema():
    df = pd.DataFrame([_row("BYD", "BYD SEAL EV", "SEAL", 12)])
    review = _review_dict([_review_row("BYD", "BYD SEAL EV", "SEAL", "pending")])
    candidates, ly, lm = bc.build_candidates(df, review)

    root = Path(tempfile.mkdtemp())
    try:
        out_csv = root / "new_bev_candidates.csv"
        out_json = root / "new_bev_candidates.json"
        meta = bc.write_outputs(candidates, ly, lm, output_csv=out_csv, output_json=out_json)

        _check("meta_year", meta["year"] == 2569, meta)
        _check("meta_month", meta["month"] == 6, meta)
        _check("meta_candidate_count", meta["candidate_count"] == 1, meta)
        _check("meta_total_units", meta["total_units"] == 12, meta)

        payload = json.loads(out_json.read_text(encoding="utf-8"))
        _check("json_meta_matches", payload["meta"] == meta, payload)
        _check("json_candidates_list", len(payload["candidates"]) == 1, payload)
        cand = payload["candidates"][0]
        for field in bc.CSV_FIELDS:
            _check(f"json_candidate_has_{field}", field in cand, cand)
        _check("json_reason_code_valid", cand["reason_code"] in ("approved_family_match", "approved_model_match", "electric_name_marker"), cand)
        _check("json_confidence_valid", cand["confidence"] in ("high", "medium"), cand)
        _check("json_review_status_pending", cand["review_status"] == "pending", cand)

        with open(out_csv, encoding="utf-8", newline="") as f:
            rows = list(csv.DictReader(f))
        _check("csv_header_matches", list(rows[0].keys()) == bc.CSV_FIELDS if rows else False, rows)
        _check("csv_row_count", len(rows) == 1, rows)
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_write_outputs_empty_candidates_still_writes_files():
    root = Path(tempfile.mkdtemp())
    try:
        out_csv = root / "new_bev_candidates.csv"
        out_json = root / "new_bev_candidates.json"
        meta = bc.write_outputs([], 2569, 6, output_csv=out_csv, output_json=out_json)
        _check("empty_meta_count_zero", meta["candidate_count"] == 0, meta)
        _check("empty_meta_units_zero", meta["total_units"] == 0, meta)
        _check("empty_csv_exists", out_csv.exists())
        _check("empty_json_exists", out_json.exists())
        payload = json.loads(out_json.read_text(encoding="utf-8"))
        _check("empty_json_candidates_list", payload["candidates"] == [], payload)
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    test_latest_period_only()
    test_pending_only()
    test_pending_only_excludes_rejected()
    test_duplicate_aggregation()
    test_stable_sorting()
    test_empty_watchlist_no_matches()
    test_empty_dataframe()
    test_write_outputs_schema()
    test_write_outputs_empty_candidates_still_writes_files()
    if failures:
        print(f"FAIL — {len(failures)} issue(s) in bev-candidates tests:")
        for f in failures:
            print(f)
        sys.exit(1)
    print("PASS — All bev-candidates tests passed successfully.")
