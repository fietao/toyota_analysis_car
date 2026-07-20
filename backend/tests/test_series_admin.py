"""Tests for series_admin.py (plans/reliable-series-powertrain.md Step 5A).

No pytest — matches the existing test_*.py convention. Every test uses a
throwaway temp registry and a small synthetic model parquet; none of them
touch backend/refer/series_registry.csv or the real cleaned parquet. Runs
from any directory. Exits 0 on PASS, 1 on FAIL.
"""
import hashlib
import os
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

TESTS = Path(__file__).resolve().parent
BACKEND = TESTS.parent
sys.path.insert(0, str(BACKEND))

from series_admin import ReviewValidationError, list_unresolved, save_review
from series_registry import load_registry

REAL_REGISTRY = BACKEND / "refer" / "series_registry.csv"

failures = []


def make_model_parquet(path):
    rows = [
        ("2569", "6", "รย.1", "กรุงเทพมหานคร", "MITSUBISHI", "MITSUBISHI", "TRITON", "TRITON", "N/A", 10),
        ("2569", "6", "รย.1", "ชลบุรี", "MITSUBISHI", "MITSUBISHI", "TRITON", "TRITON", "N/A", 5),
        ("2569", "6", "รย.1", "กรุงเทพมหานคร", "TOYOTA", "TOYOTA", "COROLLA", "COROLLA", "N/A", 7),
    ]
    cols = ["ปี", "เดือน", "ประเภทรถ", "จังหวัด", "ยี่ห้อรถ", "ยี่ห้อรถ2", "รุ่นรถ", "รุ่นรถ2", "Powertrain", "จำนวนรถ"]
    pd.DataFrame(rows, columns=cols).to_parquet(str(path))


def review_payload(**overrides):
    payload = dict(
        canonical_brand="MITSUBISHI", raw_series="TRITON", canonical_series="Triton",
        powertrain="ICE", evidence="Mitsubishi Thailand spec sheet", reviewer="jet",
    )
    payload.update(overrides)
    return payload


def expect_error(fn, msg):
    try:
        fn()
    except ReviewValidationError:
        return
    failures.append(f"{msg}: expected ReviewValidationError, none raised")


def run_tests():
    real_hash_before = hashlib.sha256(REAL_REGISTRY.read_bytes()).hexdigest()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_dir = Path(tmp)
        parquet_path = tmp_dir / "model.parquet"
        registry_path = tmp_dir / "series_registry.csv"
        make_model_parquet(parquet_path)

        # 1. Empty registry produces an unresolved queue with both series
        queue = list_unresolved(parquet_path, registry_path)
        keys = {(q["canonical_brand"], q["raw_series"]) for q in queue}
        if keys != {("MITSUBISHI", "TRITON"), ("TOYOTA", "COROLLA")}:
            failures.append(f"Empty registry produces unresolved queue: got {keys}")
        triton = next(q for q in queue if q["raw_series"] == "TRITON")
        if triton["total_units"] != 15 or triton["status"] != "unreviewed":
            failures.append(f"Empty registry queue row shape: got {triton}")

        # 2. Saving without evidence is rejected
        expect_error(
            lambda: save_review(review_payload(evidence=""), registry_path),
            "Saving without evidence is rejected",
        )

        # 3. Invalid Powertrain is rejected
        expect_error(
            lambda: save_review(review_payload(powertrain="ELECTRIC"), registry_path),
            "Invalid Powertrain is rejected",
        )
        expect_error(
            lambda: save_review(review_payload(powertrain="N/A"), registry_path),
            "N/A Powertrain is rejected on save",
        )

        # 4. Valid review persists to the temp CSV
        saved = save_review(review_payload(), registry_path)
        if saved["review_status"] != "verified" or not saved["reviewed_at"]:
            failures.append(f"Valid review persists: unexpected saved row {saved}")

        # 5. Restart/reload preserves the decision
        reloaded = load_registry(registry_path)
        match = next((r for r in reloaded if r["raw_series"] == "TRITON"), None)
        if match is None or match["powertrain"] != "ICE" or match["review_status"] != "verified":
            failures.append(f"Restart/reload preserves the decision: got {match}")

        # 6. Reviewed entry disappears from the unresolved queue
        queue_after = list_unresolved(parquet_path, registry_path)
        keys_after = {(q["canonical_brand"], q["raw_series"]) for q in queue_after}
        if ("MITSUBISHI", "TRITON") in keys_after:
            failures.append("Reviewed entry disappears from queue: TRITON still present")

        # 7. An unreviewed sibling remains unresolved
        if ("TOYOTA", "COROLLA") not in keys_after:
            failures.append("Unreviewed sibling remains unresolved: COROLLA missing")

        # 8. Concurrent/stale conflicting update is rejected
        expect_error(
            lambda: save_review(review_payload(powertrain="HEV", evidence="second look"), registry_path),
            "Concurrent/stale conflicting update is rejected",
        )

        # 9. No partial write on a rejected save (registry unchanged after failed attempts)
        rows_final = load_registry(registry_path)
        if len(rows_final) != 1:
            failures.append(f"No partial write on rejected save: expected 1 row, got {len(rows_final)}")

    # 10. Production series_registry.csv remains hash-identical
    real_hash_after = hashlib.sha256(REAL_REGISTRY.read_bytes()).hexdigest()
    if real_hash_before != real_hash_after:
        failures.append("Production series_registry.csv remains hash-identical: hash changed")


if __name__ == "__main__":
    run_tests()
    if failures:
        print(f"FAIL — {len(failures)} issue(s) in series_admin tests:")
        for f in failures:
            print(f)
        sys.exit(1)
    print("PASS — All series_admin tests passed successfully.")
