"""Step 4 release-gate regression tests."""
import sys
from pathlib import Path

import pandas as pd
import pytest

TESTS = Path(__file__).resolve().parent
BACKEND = TESTS.parent
sys.path.insert(0, str(BACKEND))

from model_map import normalize_key
from validate_public_release import (
    validate_analyst_views,
    validate_bev_report_sheets,
    validate_cleaned_source_grains,
)


def frames():
    common = {
        "ปี": 2569, "เดือน": "มิถุนายน", "ประเภทรถ": "รย.3", "จังหวัด": "กรุงเทพมหานคร",
        "ยี่ห้อรถ": "MITSUBISHI", "ยี่ห้อรถ2": "MITSUBISHI", "รุ่นรถ": "TRITON",
        "รุ่นรถ2": "TRITON", "จำนวนรถ": 10,
    }
    model = pd.DataFrame([common])
    fuel = pd.DataFrame([{**common, "Powertrain": "ICE", "ชนิดเชื้อเพลิง": "ดีเซล"}])
    return model, fuel


def test_clean_separate_grains_pass():
    model, fuel = frames()
    result = validate_cleaned_source_grains(model, fuel)
    assert result["model_units"] == result["fuel_units"] == 10


def test_model_fuel_column_is_a_release_failure():
    model, fuel = frames()
    model["ชนิดเชื้อเพลิง"] = "ดีเซล"
    with pytest.raises(ValueError, match="forbidden fuel/PT columns"):
        validate_cleaned_source_grains(model, fuel)


def test_model_powertrain_column_is_a_release_failure():
    model, fuel = frames()
    model["Powertrain"] = "HEV"
    with pytest.raises(ValueError, match="forbidden fuel/PT columns"):
        validate_cleaned_source_grains(model, fuel)


def test_fuel_grain_oth_is_accepted():
    model, fuel = frames()
    fuel["Powertrain"] = "OTH"
    result = validate_cleaned_source_grains(model, fuel)
    assert result["fuel_units"] == 10


def test_legacy_model_report_flag_is_a_release_failure():
    model, fuel = frames()
    model["include_in_bev_model_report"] = True
    with pytest.raises(ValueError, match="forbidden fuel/PT columns"):
        validate_cleaned_source_grains(model, fuel)


def test_bev_report_rejects_unverified_series():
    sheets = {
        "sheet7_bev_by_model": [{"level": "model", "brand": "MITSUBISHI", "key": "TRITON"}],
        "sheet8_model_top_rank": [],
    }
    with pytest.raises(ValueError, match="non-approved BEV models"):
        validate_bev_report_sheets(sheets, set())


def test_bev_report_accepts_verified_series():
    approved = {normalize_key("BYD", "ATTO 3")}
    sheets = {
        "sheet7_bev_by_model": [{"level": "model", "brand": "BYD", "key": "ATTO 3"}],
        "sheet8_model_top_rank": [{"brand": "BYD", "model": "ATTO 3"}],
    }
    assert validate_bev_report_sheets(sheets, approved) == 2


def test_analyst_model_views_expose_only_all():
    payload = {
        "data": {
            "brand": {key: {} for key in ("ALL", "ICE", "BEV", "HEV", "PHEV")},
            "model": {"ALL": {}},
        }
    }
    validate_analyst_views(payload)
    payload["data"]["model"]["BEV"] = {}
    with pytest.raises(ValueError, match="model views must contain only ALL"):
        validate_analyst_views(payload)
