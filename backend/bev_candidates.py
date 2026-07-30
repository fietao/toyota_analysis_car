"""bev_candidates.py — New BEV Model Watchlist.

Candidate-only: this module never writes to config/model_powertrain_review.csv. It only
surfaces, every run, which currently-pending model rows from the latest reporting period
look like they might be BEVs, so a human reviewer knows exactly what to check. Approval
still happens by hand in model_powertrain_review.csv; pending rows stay excluded from
Sheets 7-8 (see export_manual_report.bev_model_report_slice / model_map.approved_bev_keys).

Recomputed from ALL latest-period pending rows every run (not just rows appended this
run), so re-running the monthly update before finishing a review still shows the full
picture. See bev_candidate_rules.py for the matching rules themselves.
"""
import csv
import datetime
import json
import os
import sys
from pathlib import Path

import pandas as pd

from export_dashboard import load_data, MONTH_MAP
from export_manual_report import DEFAULT_VEHICLE_TYPES
from aggregate import current_period
import model_map
import bev_candidate_rules as rules

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(__file__).resolve().parent
MODEL_PARQUET = BASE / "test_model_cleaned.parquet"
OUTPUT_CSV = BASE / "output" / "new_bev_candidates.csv"
# PUBLIC_DATA_DIR mirrors export_dashboard.py's staging convention (safe no-collapse publish).
OUTPUT_JSON_DIR = Path(os.environ.get("PUBLIC_DATA_DIR") or (BASE.parent / "frontend" / "public" / "data"))
OUTPUT_JSON = OUTPUT_JSON_DIR / "new_bev_candidates.json"

CSV_FIELDS = ["brand", "raw_model", "model", "units", "confidence", "reason_code", "reason", "review_status"]


def _approved_family_keys(review: dict) -> set:
    return {
        (rules.normalize(v.get("brand2")), rules.normalize(v.get("model2")))
        for v in review.values()
        if v.get("review_status") == "approved" and v.get("candidate_powertrain") == "BEV"
    }


def _approved_raw_by_brand(review: dict) -> dict:
    out: dict = {}
    for v in review.values():
        if v.get("review_status") == "approved" and v.get("candidate_powertrain") == "BEV":
            raw_model = v.get("raw_model", "")
            out.setdefault(rules.normalize(v.get("brand2")), []).append((raw_model, rules.tokenize(raw_model)))
    return out


def _reason_text(reason_code: str, model2: str, detail) -> str:
    if reason_code == "approved_family_match":
        return f"Same brand and canonical model family ('{model2}') as an already-approved BEV."
    if reason_code == "approved_model_match":
        return f"Raw model name closely resembles the approved BEV raw model '{detail}'."
    return "Raw model name contains an electric-vehicle name marker (EV/BEV/ELECTRIC)."


def build_candidates(df: pd.DataFrame, review: dict):
    """df must carry ปี (int), เดือน (English month abbrev), ยี่ห้อรถ2, รุ่นรถ, รุ่นรถ2,
    จำนวนรถ (int) — i.e. export_dashboard.load_data(..., is_fuel=False) output, already
    scoped to the vehicle types Sheets 7-8 draw from. review is a dict as returned by
    model_map.load_model_powertrain_review().

    Returns (candidates, latest_year, latest_month_num). candidates is already sorted by
    reason priority, then latest-period units descending, then brand/model.
    """
    if df.empty or not review:
        return [], None, None

    month_order = list(MONTH_MAP.values())
    latest_year, latest_month_num = current_period(df, year_col="ปี", month_col="เดือน", month_order=month_order)
    latest_month = month_order[latest_month_num - 1]

    latest = df[(df["ปี"] == latest_year) & (df["เดือน"] == latest_month)]
    grp = (
        latest.groupby(["ยี่ห้อรถ2", "รุ่นรถ", "รุ่นรถ2"], observed=True)["จำนวนรถ"]
        .sum()
        .reset_index()
    )

    approved_family_keys = _approved_family_keys(review)
    approved_raw_by_brand = _approved_raw_by_brand(review)

    candidates = []
    for _, row in grp.iterrows():
        brand2 = str(row["ยี่ห้อรถ2"])
        raw_model = str(row["รุ่นรถ"])
        model2 = str(row["รุ่นรถ2"])
        units = int(row["จำนวนรถ"])
        if units <= 0:
            continue

        key = model_map.normalize_key(brand2, raw_model)
        review_row = review.get(key)
        if review_row is None or review_row.get("review_status") != "pending":
            continue

        result = rules.classify(
            brand2, raw_model, model2,
            approved_family_keys=approved_family_keys,
            approved_raw_by_brand=approved_raw_by_brand,
        )
        if result is None:
            continue
        reason_code, detail = result

        candidates.append({
            "brand": brand2, "raw_model": raw_model, "model": model2, "units": units,
            "confidence": rules.CONFIDENCE[reason_code], "reason_code": reason_code,
            "reason": _reason_text(reason_code, model2, detail),
            "review_status": "pending",
        })

    candidates.sort(key=lambda c: (
        rules.REASON_PRIORITY[c["reason_code"]], -c["units"], c["brand"], c["model"],
    ))
    return candidates, latest_year, latest_month_num


def load_and_build(model_parquet: Path = MODEL_PARQUET):
    df = load_data(model_parquet, is_fuel=False)
    df = df[df["v_code"].isin(DEFAULT_VEHICLE_TYPES)]  # same scope as Sheets 7-8 eligibility
    review = model_map.load_model_powertrain_review()
    return build_candidates(df, review)


def write_outputs(candidates: list, latest_year, latest_month_num,
                   output_csv: Path = OUTPUT_CSV, output_json: Path = OUTPUT_JSON) -> dict:
    total_units = sum(c["units"] for c in candidates)
    meta = {
        "year": latest_year,
        "month": latest_month_num,
        "generated_at": datetime.datetime.now().isoformat(),
        "candidate_count": len(candidates),
        "total_units": total_units,
    }

    output_csv.parent.mkdir(parents=True, exist_ok=True)
    with open(output_csv, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        w.writerows(candidates)

    output_json.parent.mkdir(parents=True, exist_ok=True)
    output_json.write_text(
        json.dumps({"meta": meta, "candidates": candidates}, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return meta


def main():
    candidates, latest_year, latest_month_num = load_and_build()
    meta = write_outputs(candidates, latest_year, latest_month_num)
    print(
        f"BEV watchlist: {meta['candidate_count']} candidate(s), {meta['total_units']:,} unit(s) "
        f"for period {latest_month_num}/{latest_year}"
    )
    for c in candidates[:5]:
        print(f"  - {c['brand']} {c['raw_model']} ({c['units']:,} units, {c['confidence']}, {c['reason_code']})")


if __name__ == "__main__":
    main()
