"""Focused release-contract validation tests."""
import sys
from pathlib import Path

import pandas as pd
import pytest

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

from release_contracts import (
    validate_analyst_province_views,
    validate_analyst_views,
    validate_bev_candidates_watchlist,
    validate_bev_report_sheets,
    validate_cleaned_source_grains,
    validate_public_model_tree,
)
from schema import COMMON_COLS, FUEL_ONLY_COLS
from validate_public_release import validate_public_model_tree as legacy_validate_public_model_tree


def _monthly(units=1):
    return {"v": {"p": {"2569": [units] + [0] * 11}}}


def _model_tree(segment="N/A", brand_monthly=1, series_monthly=1, segment_monthly=1):
    return {
        "brand_model_tree": [{
            "brand": "ACME",
            "monthly": _monthly(brand_monthly),
            "models": [{
                "name": "ALPHA",
                "monthly": _monthly(series_monthly),
                "segments": [{"powertrain": segment, "monthly": _monthly(segment_monthly)}],
            }],
        }],
    }


def _candidate(**overrides):
    candidate = {
        "brand": "BYD", "raw_model": "SEAL EV", "model": "SEAL", "units": 1,
        "confidence": "high", "reason_code": "approved_model_match", "reason": "match",
        "review_status": "pending",
    }
    candidate.update(overrides)
    return candidate


def _watchlist(candidates):
    return {
        "meta": {"year": 2569, "month": 6, "generated_at": "2026-01-01T00:00:00", "candidate_count": len(candidates), "total_units": sum(c["units"] for c in candidates)},
        "candidates": candidates,
    }


def _frames():
    common = {column: "value" for column in COMMON_COLS}
    common["จำนวนรถ"] = 1
    model = pd.DataFrame([common])
    fuel = pd.DataFrame([{**common, FUEL_ONLY_COLS[0]: "fuel", "Powertrain": "ICE"}])
    return model, fuel


def test_legacy_validator_import_is_compatible():
    assert legacy_validate_public_model_tree is validate_public_model_tree


def test_model_grain_rejects_fuel_and_powertrain_fields():
    model, fuel = _frames()
    model["Powertrain"] = "BEV"
    with pytest.raises(ValueError, match="forbidden fuel/PT columns"):
        validate_cleaned_source_grains(model, fuel)


def test_fuel_grain_rejects_invalid_powertrain():
    model, fuel = _frames()
    fuel["Powertrain"] = "UNKNOWN"
    with pytest.raises(ValueError, match="invalid Powertrain"):
        validate_cleaned_source_grains(model, fuel)


def test_model_tree_rejects_duplicate_and_unreconciled_nodes():
    duplicate = _model_tree()
    duplicate["brand_model_tree"].append(duplicate["brand_model_tree"][0].copy())
    with pytest.raises(ValueError, match="one node per brand"):
        validate_public_model_tree(duplicate)
    with pytest.raises(ValueError, match="series do not reconcile"):
        validate_public_model_tree(_model_tree(brand_monthly=2))


def test_bev_report_rejects_non_approved_models():
    sheets = {"sheet7_bev_by_model": [{"level": "model", "brand": "ACME", "key": "ALPHA"}], "sheet8_model_top_rank": []}
    with pytest.raises(ValueError, match="non-approved BEV models"):
        validate_bev_report_sheets(sheets, set())


def test_watchlist_rejects_malformed_metadata_and_period_mismatch():
    malformed = _watchlist([_candidate()])
    del malformed["meta"]["generated_at"]
    with pytest.raises(ValueError, match="meta missing required field"):
        validate_bev_candidates_watchlist(malformed, (2569, 6))
    with pytest.raises(ValueError, match="does not match"):
        validate_bev_candidates_watchlist(_watchlist([_candidate()]), (2569, 5))


def test_analyst_payloads_reject_invalid_views_and_facts():
    with pytest.raises(ValueError, match="model views must contain only ALL"):
        validate_analyst_views({"data": {"brand": {key: {} for key in ("ALL", "ICE", "BEV", "HEV", "PHEV")}, "model": {"BEV": {}}}})
    with pytest.raises(ValueError, match="missing keys"):
        validate_analyst_province_views({"facts": {"brand": [{"p": 1}], "model": [{"p": 1}]}})
