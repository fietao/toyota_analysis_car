import pandas as pd
import pytest

from import_unresolved_series_review import _norm_powertrain, build_live_groups, dry_run, validate_row, write
from series_registry import ALLOWED_POWERTRAIN, load_registry, write_registry

LIVE_GROUPS = build_live_groups(queue=[
    {"canonical_brand": "A", "raw_series": "X1", "canonical_series": "X", "total_units": 10, "status": "unreviewed"},
    {"canonical_brand": "A", "raw_series": "X2", "canonical_series": "X", "total_units": 5, "status": "unreviewed"},
])


def _row(**kw):
    base = {"canonical_brand": "A", "canonical_series": "X", "decision": "", "approved_powertrain": "",
            "evidence": "", "reviewer": "", "notes": ""}
    base.update(kw)
    return pd.Series(base)


def test_approve_valid():
    outcome, matches, error = validate_row(
        _row(decision="approve", approved_powertrain="BEV", evidence="brochure", reviewer="jet"), LIVE_GROUPS)
    assert outcome == "approve"
    assert error is None
    assert len(matches) == 2


def test_approve_missing_evidence_fails():
    outcome, matches, error = validate_row(
        _row(decision="approve", approved_powertrain="BEV", reviewer="jet"), LIVE_GROUPS)
    assert outcome == "error"
    assert "evidence" in error


def test_keep_na_valid():
    outcome, matches, error = validate_row(
        _row(decision="keep_na", reviewer="jet", notes="checked, unclear model"), LIVE_GROUPS)
    assert outcome == "keep_na"
    assert error is None
    assert len(matches) == 2


def test_invalid_powertrain_fails():
    outcome, matches, error = validate_row(
        _row(decision="approve", approved_powertrain="PETROL", evidence="x", reviewer="jet"), LIVE_GROUPS)
    assert outcome == "error"
    assert "approved_powertrain" in error


def test_not_applicable_valid():
    outcome, matches, error = validate_row(
        _row(decision="not_applicable", reviewer="jet", notes="checked, unclear model"), LIVE_GROUPS)
    assert outcome == "not_applicable"
    assert error is None
    assert len(matches) == 2


def test_approve_with_na_powertrain_fails():
    outcome, matches, error = validate_row(
        _row(decision="approve", approved_powertrain="N/A", evidence="x", reviewer="jet"), LIVE_GROUPS)
    assert outcome == "error"
    assert "approved_powertrain" in error


@pytest.mark.parametrize("raw,expected", [
    ("ice", "ICE"), ("ICE", "ICE"), ("Ice", "ICE"),
    ("hev", "HEV"), ("HEV", "HEV"), ("Hev", "HEV"),
    ("phev", "PHEV"), ("PHEV", "PHEV"), ("Phev", "PHEV"),
    ("bev", "BEV"), ("BEV", "BEV"), ("Bev", "BEV"),
    ("n/a", "N/A"), ("N/A", "N/A"),
    ("petrol", None), ("unknown", None), ("", None),
])
def test_approved_powertrain_normalization(raw, expected):
    normalized = _norm_powertrain(raw)
    if expected is None:
        assert normalized not in ALLOWED_POWERTRAIN
    else:
        assert normalized == expected
        assert normalized in ALLOWED_POWERTRAIN


def test_approve_lowercase_powertrain_normalized():
    outcome, matches, error = validate_row(
        _row(decision="approve", approved_powertrain="ice", evidence="brochure", reviewer="jet"), LIVE_GROUPS)
    assert outcome == "approve"
    assert error is None
    assert len(matches) == 2


def test_keep_na_lowercase_na_accepted():
    outcome, matches, error = validate_row(
        _row(decision="keep_na", approved_powertrain="n/a", reviewer="jet", notes="checked"), LIVE_GROUPS)
    assert outcome == "keep_na"
    assert error is None


def test_keep_na_with_real_powertrain_fails():
    outcome, matches, error = validate_row(
        _row(decision="keep_na", approved_powertrain="ICE", reviewer="jet", notes="n/a"), LIVE_GROUPS)
    assert outcome == "error"
    assert "approved_powertrain" in error


def test_blank_and_skip_ignored():
    for decision in ("", "skip"):
        outcome, matches, error = validate_row(_row(decision=decision), LIVE_GROUPS)
        assert outcome == "ignored"
        assert matches == []
        assert error is None


def test_stale_group_fails():
    outcome, matches, error = validate_row(
        _row(canonical_series="NO_LONGER_UNRESOLVED", decision="approve",
             approved_powertrain="BEV", evidence="x", reviewer="jet"),
        LIVE_GROUPS)
    assert outcome == "error"
    assert "stale" in error or "no longer unresolved" in error


def test_dry_run_end_to_end(tmp_path):
    csv_path = tmp_path / "review.csv"
    pd.DataFrame([
        {"canonical_brand": "A", "canonical_series": "X", "decision": "approve",
         "approved_powertrain": "BEV", "evidence": "brochure", "reviewer": "jet", "notes": ""},
        {"canonical_brand": "B", "canonical_series": "Y", "decision": "skip",
         "approved_powertrain": "", "evidence": "", "reviewer": "", "notes": ""},
    ]).to_csv(csv_path, index=False)

    queue = [
        {"canonical_brand": "A", "raw_series": "X1", "canonical_series": "X", "total_units": 10, "status": "unreviewed"},
        {"canonical_brand": "A", "raw_series": "X2", "canonical_series": "X", "total_units": 5, "status": "unreviewed"},
    ]
    result = dry_run(csv_path, queue=queue)
    assert result["rows_read"] == 2
    assert result["rows_ignored"] == 1
    assert result["approve_groups"] == 1
    assert result["raw_rows_to_write"] == 2
    assert result["errors"] == []


def test_dry_run_counts_not_applicable(tmp_path):
    queue = [
        {"canonical_brand": "A", "raw_series": "X1", "canonical_series": "X", "total_units": 10, "status": "unreviewed"},
        {"canonical_brand": "A", "raw_series": "X2", "canonical_series": "X", "total_units": 5, "status": "unreviewed"},
    ]
    csv_path = tmp_path / "review.csv"
    pd.DataFrame([
        {"canonical_brand": "A", "canonical_series": "X", "decision": "not_applicable",
         "approved_powertrain": "", "evidence": "", "reviewer": "jet", "notes": "reviewed, unclear"},
    ]).to_csv(csv_path, index=False)

    result = dry_run(csv_path, queue=queue)
    assert result["not_applicable_groups"] == 1
    assert result["keep_na_groups"] == 0
    assert result["raw_rows_to_write"] == 2
    assert result["errors"] == []


def test_write_mode_writes_not_applicable_rows(tmp_path):
    queue = [
        {"canonical_brand": "A", "raw_series": "X1", "canonical_series": "X", "total_units": 10, "status": "unreviewed"},
        {"canonical_brand": "A", "raw_series": "X2", "canonical_series": "X", "total_units": 5, "status": "unreviewed"},
    ]
    csv_path = tmp_path / "review.csv"
    pd.DataFrame([
        {"canonical_brand": "A", "canonical_series": "X", "decision": "not_applicable",
         "approved_powertrain": "", "evidence": "", "reviewer": "jet", "notes": "reviewed, unclear"},
    ]).to_csv(csv_path, index=False)

    registry_path = tmp_path / "series_registry.csv"
    write_registry([], registry_path)

    result = write(csv_path, queue=queue, registry_path=registry_path)
    assert result["errors"] == []
    assert result["written"] == 2

    rows = load_registry(registry_path)
    assert len(rows) == 2
    for r in rows:
        assert r["review_status"] == "not_applicable"
        assert r["powertrain"] == "N/A"
        assert r["evidence"] == "reviewed, unclear"
        assert r["reviewer"] == "jet"
        assert r["reviewed_at"]


def test_write_mode_writes_approve_rows(tmp_path):
    queue = [
        {"canonical_brand": "A", "raw_series": "X1", "canonical_series": "X", "total_units": 10, "status": "unreviewed"},
    ]
    csv_path = tmp_path / "review.csv"
    pd.DataFrame([
        {"canonical_brand": "A", "canonical_series": "X", "decision": "approve",
         "approved_powertrain": "BEV", "evidence": "brochure", "reviewer": "jet", "notes": ""},
    ]).to_csv(csv_path, index=False)

    registry_path = tmp_path / "series_registry.csv"
    write_registry([], registry_path)

    result = write(csv_path, queue=queue, registry_path=registry_path)
    assert result["written"] == 1

    rows = load_registry(registry_path)
    assert rows[0]["review_status"] == "verified"
    assert rows[0]["powertrain"] == "BEV"


def test_write_mode_normalizes_lowercase_powertrain(tmp_path):
    queue = [
        {"canonical_brand": "A", "raw_series": "X1", "canonical_series": "X", "total_units": 10, "status": "unreviewed"},
    ]
    csv_path = tmp_path / "review.csv"
    pd.DataFrame([
        {"canonical_brand": "A", "canonical_series": "X", "decision": "approve",
         "approved_powertrain": "ice", "evidence": "brochure", "reviewer": "jet", "notes": ""},
    ]).to_csv(csv_path, index=False)

    registry_path = tmp_path / "series_registry.csv"
    write_registry([], registry_path)

    result = write(csv_path, queue=queue, registry_path=registry_path)
    assert result["errors"] == []
    assert result["written"] == 1

    rows = load_registry(registry_path)
    assert rows[0]["powertrain"] == "ICE"


def test_write_mode_writes_nothing_on_error(tmp_path):
    queue = [
        {"canonical_brand": "A", "raw_series": "X1", "canonical_series": "X", "total_units": 10, "status": "unreviewed"},
    ]
    csv_path = tmp_path / "review.csv"
    pd.DataFrame([
        {"canonical_brand": "A", "canonical_series": "X", "decision": "approve",
         "approved_powertrain": "N/A", "evidence": "brochure", "reviewer": "jet", "notes": ""},
    ]).to_csv(csv_path, index=False)

    registry_path = tmp_path / "series_registry.csv"
    write_registry([], registry_path)

    result = write(csv_path, queue=queue, registry_path=registry_path)
    assert result["errors"] != []
    assert result["written"] == 0
    assert load_registry(registry_path) == []
