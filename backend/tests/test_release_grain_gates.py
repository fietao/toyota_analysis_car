"""Step 4 release-gate regression tests."""
import sys
from pathlib import Path

import pandas as pd
import pytest

TESTS = Path(__file__).resolve().parent
BACKEND = TESTS.parent
sys.path.insert(0, str(BACKEND))

from series_registry import write_registry
from validate_public_release import validate_bev_report_sheets, validate_cleaned_source_grains


def frames():
    common = {
        "ปี": 2569, "เดือน": "มิถุนายน", "ประเภทรถ": "รย.3", "จังหวัด": "กรุงเทพมหานคร",
        "ยี่ห้อรถ": "MITSUBISHI", "ยี่ห้อรถ2": "MITSUBISHI", "รุ่นรถ": "TRITON",
        "รุ่นรถ2": "TRITON", "จำนวนรถ": 10,
    }
    model = pd.DataFrame([{**common, "Powertrain": "N/A", "include_in_bev_model_report": False}])
    fuel = pd.DataFrame([{**common, "Powertrain": "ICE", "ชนิดเชื้อเพลิง": "ดีเซล"}])
    return model, fuel


def empty_registry(tmp_path):
    path = tmp_path / "series_registry.csv"
    write_registry([], path)
    return path


def test_clean_separate_grains_pass(tmp_path):
    model, fuel = frames()
    result = validate_cleaned_source_grains(model, fuel, empty_registry(tmp_path))
    assert result["model_units"] == result["fuel_units"] == 10
    assert result["verified_mappings"] == 0


def test_model_fuel_column_is_a_release_failure(tmp_path):
    model, fuel = frames()
    model["ชนิดเชื้อเพลิง"] = "ดีเซล"
    with pytest.raises(ValueError, match="forbidden fuel columns"):
        validate_cleaned_source_grains(model, fuel, empty_registry(tmp_path))


def test_unverified_series_powertrain_is_a_release_failure(tmp_path):
    model, fuel = frames()
    model["Powertrain"] = "HEV"
    with pytest.raises(ValueError, match="non-registry Powertrain"):
        validate_cleaned_source_grains(model, fuel, empty_registry(tmp_path))


def test_fuel_grain_oth_is_accepted(tmp_path):
    model, fuel = frames()
    fuel["Powertrain"] = "OTH"
    result = validate_cleaned_source_grains(model, fuel, empty_registry(tmp_path))
    assert result["fuel_units"] == 10


def test_model_grain_oth_is_a_release_failure(tmp_path):
    model, fuel = frames()
    model["Powertrain"] = "OTH"
    with pytest.raises(ValueError, match="invalid Powertrain values"):
        validate_cleaned_source_grains(model, fuel, empty_registry(tmp_path))


def test_bev_report_rejects_unverified_series():
    sheets = {
        "sheet7_bev_by_model": [{"level": "model", "brand": "MITSUBISHI", "key": "TRITON"}],
        "sheet8_model_top_rank": [],
    }
    with pytest.raises(ValueError, match="non-verified BEV series"):
        validate_bev_report_sheets(sheets, [])


def test_bev_report_accepts_verified_series():
    registry = [{
        "canonical_brand": "BYD", "raw_series": "ATTO 3 EV", "canonical_series": "ATTO 3",
        "powertrain": "BEV", "review_status": "verified", "evidence": "source",
        "reviewer": "admin", "reviewed_at": "2026-07-16T12:00:00+07:00",
    }]
    sheets = {
        "sheet7_bev_by_model": [{"level": "model", "brand": "BYD", "key": "ATTO 3"}],
        "sheet8_model_top_rank": [{"brand": "BYD", "model": "ATTO 3"}],
    }
    assert validate_bev_report_sheets(sheets, registry) == 2
