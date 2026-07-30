"""test_bev_candidates_release_validation.py — validate_bev_candidates_watchlist() tests.

No pytest — matches the existing test_*.py convention. Exits 0 on PASS, 1 on FAIL.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from validate_public_release import validate_bev_candidates_watchlist

failures = []


def _check(label, cond, detail=""):
    if not cond:
        failures.append(f"{label}: {detail}")


def _candidate(**overrides):
    base = {
        "brand": "BYD", "raw_model": "BYD SEAL EV", "model": "SEAL", "units": 10,
        "confidence": "high", "reason_code": "approved_family_match",
        "reason": "Same brand and canonical model family ('SEAL') as an already-approved BEV.",
        "review_status": "pending",
    }
    base.update(overrides)
    return base


def _payload(candidates, year=2569, month=6, candidate_count=None, total_units=None):
    if candidate_count is None:
        candidate_count = len(candidates)
    if total_units is None:
        total_units = sum(c["units"] for c in candidates)
    return {
        "meta": {
            "year": year, "month": month, "generated_at": "2026-07-30T00:00:00",
            "candidate_count": candidate_count, "total_units": total_units,
        },
        "candidates": candidates,
    }


def test_valid_payload_with_candidates_passes():
    """Candidate presence (count > 0) must not fail validation on its own."""
    payload = _payload([_candidate(), _candidate(brand="AVATR", units=5)])
    count = validate_bev_candidates_watchlist(payload, (2569, 6))
    _check("valid_with_candidates", count == 2, count)


def test_empty_candidates_passes():
    payload = _payload([])
    count = validate_bev_candidates_watchlist(payload, (2569, 6))
    _check("valid_empty", count == 0, count)


def test_period_mismatch_raises():
    payload = _payload([_candidate()])
    try:
        validate_bev_candidates_watchlist(payload, (2569, 5))
        failures.append("period_mismatch: expected ValueError, none raised")
    except ValueError:
        pass


def test_candidate_count_mismatch_raises():
    payload = _payload([_candidate()], candidate_count=5)
    try:
        validate_bev_candidates_watchlist(payload, (2569, 6))
        failures.append("candidate_count_mismatch: expected ValueError, none raised")
    except ValueError:
        pass


def test_total_units_mismatch_raises():
    payload = _payload([_candidate(units=10)], total_units=999)
    try:
        validate_bev_candidates_watchlist(payload, (2569, 6))
        failures.append("total_units_mismatch: expected ValueError, none raised")
    except ValueError:
        pass


def test_invalid_reason_code_raises():
    payload = _payload([_candidate(reason_code="brand_only_guess")])
    try:
        validate_bev_candidates_watchlist(payload, (2569, 6))
        failures.append("invalid_reason_code: expected ValueError, none raised")
    except ValueError:
        pass


def test_invalid_confidence_raises():
    payload = _payload([_candidate(confidence="low")])
    try:
        validate_bev_candidates_watchlist(payload, (2569, 6))
        failures.append("invalid_confidence: expected ValueError, none raised")
    except ValueError:
        pass


def test_non_pending_review_status_raises():
    """The watchlist must never carry an auto-approved/rejected row."""
    payload = _payload([_candidate(review_status="approved")])
    try:
        validate_bev_candidates_watchlist(payload, (2569, 6))
        failures.append("non_pending: expected ValueError, none raised")
    except ValueError:
        pass


def test_missing_meta_field_raises():
    payload = _payload([_candidate()])
    del payload["meta"]["generated_at"]
    try:
        validate_bev_candidates_watchlist(payload, (2569, 6))
        failures.append("missing_meta_field: expected ValueError, none raised")
    except ValueError:
        pass


if __name__ == "__main__":
    test_valid_payload_with_candidates_passes()
    test_empty_candidates_passes()
    test_period_mismatch_raises()
    test_candidate_count_mismatch_raises()
    test_total_units_mismatch_raises()
    test_invalid_reason_code_raises()
    test_invalid_confidence_raises()
    test_non_pending_review_status_raises()
    test_missing_meta_field_raises()
    if failures:
        print(f"FAIL — {len(failures)} issue(s) in bev-candidates-release-validation tests:")
        for f in failures:
            print(f)
        sys.exit(1)
    print("PASS — All bev-candidates-release-validation tests passed successfully.")
