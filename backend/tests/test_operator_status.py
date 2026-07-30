"""test_operator_status.py — unit tests for monthly_update.write_operator_status.

Stdlib only, no pytest — matches the existing test_*.py convention. Exits 0 on PASS,
1 on FAIL. Monkeypatches monthly_update's module-level paths to a scratch dir so it
runs without pandas or a real pipeline build.
"""
import csv
import json
import os
import shutil
import sys
import tempfile
import time
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

import monthly_update as mu
import operator_preflight as op

failures = []

REVIEW_ROW = {
    "brand2": "TESLA", "raw_model": "MODEL Y", "model2": "MODEL Y",
    "candidate_powertrain": "", "review_status": "pending",
    "evidence": "", "reviewer": "", "reviewed_at": "", "notes": "",
}


def _scratch():
    root = Path(tempfile.mkdtemp())
    data_dir = root / "data"
    data_dir.mkdir()
    reports_dir = root / "reports"
    return root, data_dir, reports_dir


def _write_csv(path, rows):
    with open(path, "w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=op.REVIEW_HEADERS)
        w.writeheader()
        w.writerows(rows)


def _patch(data_dir, reports_dir, review_csv):
    """Monkeypatch module-level paths; returns the originals for restoration.

    operator_preflight.count_pending(path=DEFAULT_CSV) binds its default at def time,
    so reassigning op.DEFAULT_CSV alone would not redirect a no-arg call — replace the
    function itself with one bound to the scratch CSV instead.
    """
    orig = (
        mu.DATA_DIR, mu.MANIFEST_PATH, mu.STATUS_PATH, mu.REPORTS_DIR, mu.SUMMARY_PATH,
        mu.BEV_CANDIDATES_PATH, op.count_pending,
    )
    mu.DATA_DIR = data_dir
    mu.MANIFEST_PATH = data_dir / "cleaned_data_manifest.json"
    mu.STATUS_PATH = data_dir / "operator_status.json"
    mu.REPORTS_DIR = reports_dir
    mu.SUMMARY_PATH = reports_dir / "monthly_operator_summary.txt"
    mu.BEV_CANDIDATES_PATH = data_dir / "new_bev_candidates.json"
    real_count_pending = orig[6]
    op.count_pending = lambda path=review_csv: real_count_pending(path)
    return orig


def _restore(orig):
    (
        mu.DATA_DIR, mu.MANIFEST_PATH, mu.STATUS_PATH, mu.REPORTS_DIR, mu.SUMMARY_PATH,
        mu.BEV_CANDIDATES_PATH, op.count_pending,
    ) = orig


def test_success_no_pending_is_ok():
    root, data_dir, reports_dir = _scratch()
    orig = _patch(data_dir, reports_dir, root / "review.csv")
    try:
        _write_csv(root / "review.csv", [])
        (data_dir / "cleaned_data_manifest.json").write_text(json.dumps({
            "reporting_period": "June 2569", "model_row_count": 100, "fuel_row_count": 90,
            "model_total_units": 5000, "fuel_total_units": 5000,
        }), encoding="utf-8")
        run_start = time.time()
        mu.write_operator_status(run_start, mu.RESULT_OK)
        status = json.loads(mu.STATUS_PATH.read_text(encoding="utf-8"))
        if status["status"] != "ok":
            failures.append(f"ok: expected status=ok, got {status['status']}")
        if status["pending_review_count"] != 0:
            failures.append(f"ok: expected 0 pending, got {status['pending_review_count']}")
        if status["totals_match"] is not True:
            failures.append(f"ok: expected totals_match=True, got {status['totals_match']}")
        if status["safe_live_data"] is not True:
            failures.append("ok: expected safe_live_data=True")
        if status["reporting_period"] != "June 2569":
            failures.append(f"ok: reporting_period not carried from manifest: {status}")
        if "No action needed" not in status["next_action"]:
            failures.append(f"ok: unexpected next_action: {status['next_action']!r}")
    finally:
        _restore(orig)
        shutil.rmtree(root, ignore_errors=True)


def test_pending_reviews_is_review_needed():
    root, data_dir, reports_dir = _scratch()
    orig = _patch(data_dir, reports_dir, root / "review.csv")
    try:
        _write_csv(root / "review.csv", [REVIEW_ROW])
        (data_dir / "cleaned_data_manifest.json").write_text(json.dumps({
            "reporting_period": "June 2569", "model_row_count": 100, "fuel_row_count": 90,
            "model_total_units": 5000, "fuel_total_units": 5000,
        }), encoding="utf-8")
        run_start = time.time()
        mu.write_operator_status(run_start, mu.RESULT_REVIEW)
        status = json.loads(mu.STATUS_PATH.read_text(encoding="utf-8"))
        if status["status"] != "review_needed":
            failures.append(f"review: expected status=review_needed, got {status['status']}")
        if status["pending_review_count"] != 1:
            failures.append(f"review: expected 1 pending, got {status['pending_review_count']}")
        if "1 new model row" not in status["next_action"]:
            failures.append(f"review: unexpected next_action: {status['next_action']!r}")
    finally:
        _restore(orig)
        shutil.rmtree(root, ignore_errors=True)


def test_failure_is_safe():
    """On failure, public data (manifest) is untouched -> old period/counts still show,
    and safe_live_data must be True (safe-publish never leaves a half-written state)."""
    root, data_dir, reports_dir = _scratch()
    orig = _patch(data_dir, reports_dir, root / "review.csv")
    try:
        _write_csv(root / "review.csv", [])
        (data_dir / "cleaned_data_manifest.json").write_text(json.dumps({
            "reporting_period": "May 2569", "model_row_count": 90, "fuel_row_count": 80,
            "model_total_units": 4000, "fuel_total_units": 4000,
        }), encoding="utf-8")
        run_start = time.time()
        mu.write_operator_status(run_start, mu.RESULT_FAIL)
        status = json.loads(mu.STATUS_PATH.read_text(encoding="utf-8"))
        if status["status"] != "failed":
            failures.append(f"fail: expected status=failed, got {status['status']}")
        if status["safe_live_data"] is not True:
            failures.append("fail: expected safe_live_data=True (old data untouched)")
        if status["reporting_period"] != "May 2569":
            failures.append(f"fail: expected last-good period to still show: {status}")
        if "Monthly update failed" not in status["next_action"]:
            failures.append(f"fail: unexpected next_action: {status['next_action']!r}")
    finally:
        _restore(orig)
        shutil.rmtree(root, ignore_errors=True)


def test_totals_mismatch_flagged():
    root, data_dir, reports_dir = _scratch()
    orig = _patch(data_dir, reports_dir, root / "review.csv")
    try:
        _write_csv(root / "review.csv", [])
        (data_dir / "cleaned_data_manifest.json").write_text(json.dumps({
            "reporting_period": "June 2569", "model_row_count": 100, "fuel_row_count": 90,
            "model_total_units": 5000, "fuel_total_units": 4999,
        }), encoding="utf-8")
        run_start = time.time()
        mu.write_operator_status(run_start, mu.RESULT_OK)
        status = json.loads(mu.STATUS_PATH.read_text(encoding="utf-8"))
        if status["totals_match"] is not False:
            failures.append(f"mismatch: expected totals_match=False, got {status['totals_match']}")
    finally:
        _restore(orig)
        shutil.rmtree(root, ignore_errors=True)


def test_published_files_reflect_this_run():
    root, data_dir, reports_dir = _scratch()
    orig = _patch(data_dir, reports_dir, root / "review.csv")
    try:
        _write_csv(root / "review.csv", [])
        (data_dir / "cleaned_data_manifest.json").write_text(json.dumps({
            "reporting_period": "June 2569", "model_row_count": 1, "fuel_row_count": 1,
            "model_total_units": 1, "fuel_total_units": 1,
        }), encoding="utf-8")
        # Small buffer: in production the build takes seconds between run_start and the
        # first write; here they'd otherwise land within float/mtime rounding of each other.
        run_start = time.time() - 1
        # A file the run wrote (fresh) vs one predating the run (stale).
        (data_dir / "dashboard_summary.json").write_text("{}", encoding="utf-8")
        stale = data_dir / "manual_report.json"
        stale.write_text("{}", encoding="utf-8")
        os.utime(stale, (run_start - 3600, run_start - 3600))
        mu.write_operator_status(run_start, mu.RESULT_OK)
        status = json.loads(mu.STATUS_PATH.read_text(encoding="utf-8"))
        flags = {f["file"]: f["updated_this_run"] for f in status["published_files"]}
        if flags.get("dashboard_summary.json") is not True:
            failures.append(f"published_files: expected dashboard_summary.json fresh, got {flags}")
        if flags.get("manual_report.json") is not False:
            failures.append(f"published_files: expected manual_report.json stale, got {flags}")
    finally:
        _restore(orig)
        shutil.rmtree(root, ignore_errors=True)


def test_finish_writes_status_file():
    """Wiring check: finish() (called by every exit path in main()) must write the
    status JSON itself, not just write_operator_status() in isolation."""
    root, data_dir, reports_dir = _scratch()
    orig = _patch(data_dir, reports_dir, root / "review.csv")
    try:
        _write_csv(root / "review.csv", [])
        (data_dir / "cleaned_data_manifest.json").write_text(json.dumps({
            "reporting_period": "June 2569", "model_row_count": 1, "fuel_row_count": 1,
            "model_total_units": 1, "fuel_total_units": 1,
        }), encoding="utf-8")
        run_start = time.time()
        mu.finish(mu.RESULT_FAIL, run_start)
        if not mu.STATUS_PATH.exists():
            failures.append("finish: operator_status.json was not written")
        else:
            status = json.loads(mu.STATUS_PATH.read_text(encoding="utf-8"))
            if status["status"] != "failed":
                failures.append(f"finish: expected status=failed, got {status['status']}")
    finally:
        _restore(orig)
        shutil.rmtree(root, ignore_errors=True)


def test_crash_still_writes_failed_status():
    """An unhandled exception inside main() must not leave operator_status.json holding
    a stale (possibly healthy-looking) status from a previous run."""
    root, data_dir, reports_dir = _scratch()
    logs_dir = root / "logs"
    orig = _patch(data_dir, reports_dir, root / "review.csv")
    orig_logs_dir, orig_check_inputs = mu.LOGS_DIR, mu.check_inputs
    mu.LOGS_DIR = logs_dir
    mu.check_inputs = lambda: (_ for _ in ()).throw(RuntimeError("boom"))
    try:
        _write_csv(root / "review.csv", [])
        (data_dir / "cleaned_data_manifest.json").write_text(json.dumps({
            "reporting_period": "June 2569", "model_row_count": 1, "fuel_row_count": 1,
            "model_total_units": 1, "fuel_total_units": 1,
        }), encoding="utf-8")
        rc = mu.main()
        if rc != 1:
            failures.append(f"crash: expected exit code 1, got {rc}")
        if not mu.STATUS_PATH.exists():
            failures.append("crash: operator_status.json was not written")
        else:
            status = json.loads(mu.STATUS_PATH.read_text(encoding="utf-8"))
            if status["status"] != "failed":
                failures.append(f"crash: expected status=failed, got {status['status']}")
    finally:
        mu.LOGS_DIR, mu.check_inputs = orig_logs_dir, orig_check_inputs
        _restore(orig)
        shutil.rmtree(root, ignore_errors=True)


def _write_bev_candidates(data_dir, candidate_count, total_units):
    (data_dir / "new_bev_candidates.json").write_text(json.dumps({
        "meta": {
            "year": 2569, "month": 6, "generated_at": "2026-07-30T00:00:00",
            "candidate_count": candidate_count, "total_units": total_units,
        },
        "candidates": [],
    }), encoding="utf-8")


def test_bev_candidates_present_sets_watchlist_message_and_next_action():
    root, data_dir, reports_dir = _scratch()
    orig = _patch(data_dir, reports_dir, root / "review.csv")
    try:
        _write_csv(root / "review.csv", [REVIEW_ROW])
        _write_bev_candidates(data_dir, 2, 55)
        (data_dir / "cleaned_data_manifest.json").write_text(json.dumps({
            "reporting_period": "June 2569", "model_row_count": 100, "fuel_row_count": 90,
            "model_total_units": 5000, "fuel_total_units": 5000,
        }), encoding="utf-8")
        mu.write_operator_status(time.time(), mu.RESULT_REVIEW)
        status = json.loads(mu.STATUS_PATH.read_text(encoding="utf-8"))
        watchlist = status.get("bev_watchlist", {})
        if watchlist.get("candidate_count") != 2:
            failures.append(f"watchlist: expected candidate_count=2, got {watchlist}")
        if watchlist.get("total_units") != 55:
            failures.append(f"watchlist: expected total_units=55, got {watchlist}")
        expected_msg = "2 possible new BEV models need checking. Published data remains safe."
        if watchlist.get("message") != expected_msg:
            failures.append(f"watchlist: unexpected message: {watchlist.get('message')!r}")
        expected_action = (
            "Review the possible BEV models listed in the watchlist. Approve only "
            "models supported by reliable evidence."
        )
        if status["next_action"] != expected_action:
            failures.append(f"watchlist: unexpected next_action: {status['next_action']!r}")
    finally:
        _restore(orig)
        shutil.rmtree(root, ignore_errors=True)


def test_bev_candidates_zero_is_green_wording():
    root, data_dir, reports_dir = _scratch()
    orig = _patch(data_dir, reports_dir, root / "review.csv")
    try:
        _write_csv(root / "review.csv", [])
        _write_bev_candidates(data_dir, 0, 0)
        (data_dir / "cleaned_data_manifest.json").write_text(json.dumps({
            "reporting_period": "June 2569", "model_row_count": 100, "fuel_row_count": 90,
            "model_total_units": 5000, "fuel_total_units": 5000,
        }), encoding="utf-8")
        mu.write_operator_status(time.time(), mu.RESULT_OK)
        status = json.loads(mu.STATUS_PATH.read_text(encoding="utf-8"))
        watchlist = status.get("bev_watchlist", {})
        if watchlist.get("message") != "No new BEV candidates.":
            failures.append(f"zero-candidates: unexpected message: {watchlist.get('message')!r}")
        if "No action needed" not in status["next_action"]:
            failures.append(f"zero-candidates: unexpected next_action: {status['next_action']!r}")
    finally:
        _restore(orig)
        shutil.rmtree(root, ignore_errors=True)


def test_bev_candidates_never_forces_failed_status():
    """Candidate presence alone must never turn the run red — only a real RESULT_FAIL does."""
    root, data_dir, reports_dir = _scratch()
    orig = _patch(data_dir, reports_dir, root / "review.csv")
    try:
        _write_csv(root / "review.csv", [REVIEW_ROW])
        _write_bev_candidates(data_dir, 5, 200)
        (data_dir / "cleaned_data_manifest.json").write_text(json.dumps({
            "reporting_period": "June 2569", "model_row_count": 100, "fuel_row_count": 90,
            "model_total_units": 5000, "fuel_total_units": 5000,
        }), encoding="utf-8")
        mu.write_operator_status(time.time(), mu.RESULT_OK)
        status = json.loads(mu.STATUS_PATH.read_text(encoding="utf-8"))
        if status["status"] != "ok":
            failures.append(f"candidates-never-red: expected status=ok despite candidates, got {status['status']}")
    finally:
        _restore(orig)
        shutil.rmtree(root, ignore_errors=True)


def test_bev_candidates_missing_file_defaults_to_zero():
    """A missing/never-generated watchlist file must never crash write_operator_status."""
    root, data_dir, reports_dir = _scratch()
    orig = _patch(data_dir, reports_dir, root / "review.csv")
    try:
        _write_csv(root / "review.csv", [])
        (data_dir / "cleaned_data_manifest.json").write_text(json.dumps({
            "reporting_period": "June 2569", "model_row_count": 100, "fuel_row_count": 90,
            "model_total_units": 5000, "fuel_total_units": 5000,
        }), encoding="utf-8")
        mu.write_operator_status(time.time(), mu.RESULT_OK)
        status = json.loads(mu.STATUS_PATH.read_text(encoding="utf-8"))
        if status["bev_watchlist"]["candidate_count"] != 0:
            failures.append(f"missing-file: expected candidate_count=0, got {status['bev_watchlist']}")
    finally:
        _restore(orig)
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    test_success_no_pending_is_ok()
    test_pending_reviews_is_review_needed()
    test_failure_is_safe()
    test_totals_mismatch_flagged()
    test_published_files_reflect_this_run()
    test_finish_writes_status_file()
    test_crash_still_writes_failed_status()
    test_bev_candidates_present_sets_watchlist_message_and_next_action()
    test_bev_candidates_zero_is_green_wording()
    test_bev_candidates_never_forces_failed_status()
    test_bev_candidates_missing_file_defaults_to_zero()
    if failures:
        print(f"FAIL — {len(failures)} issue(s) in operator-status tests:")
        for f in failures:
            print(f)
        sys.exit(1)
    print("PASS — All operator-status tests passed successfully.")
