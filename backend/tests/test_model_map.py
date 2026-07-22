"""test_model_map.py — unit tests for model_map.py loaders."""
import sys
from pathlib import Path

TESTS = Path(__file__).resolve().parent
BACKEND = TESTS.parent
sys.path.insert(0, str(BACKEND))

import pytest
from model_map import approved_bev_keys, approved_bev_model_keys, model2_map, normalize_key


def test_normalize_key():
    """Composite key normalization: strip, collapse whitespace, uppercase."""
    assert normalize_key("AION", "AION UT  420  STANDARD") == ("AION", "AION UT 420 STANDARD")
    assert normalize_key("  aion  ", "  aion ut 420 standard  ") == ("AION", "AION UT 420 STANDARD")
    assert normalize_key("", "") == ("", "")


def test_model2_map_loads():
    """model2_map() loads and returns a dict."""
    m = model2_map()
    assert isinstance(m, dict)
    assert len(m) > 0  # Sparse alias set loaded from config/model_map.csv


def test_model2_map_composite_key():
    """Model map uses normalized composite key (brand2, raw_model)."""
    m = model2_map()
    # Find a known alias: AION, "AION UT 420 STANDARD" -> "AION UT"
    key = normalize_key("AION", "AION UT 420 STANDARD")
    assert key in m
    assert m[key] == "AION UT"


def test_model2_map_unknown_key():
    """Unknown composite key is not in the map."""
    m = model2_map()
    key = normalize_key("UNKNOWN_BRAND", "UNKNOWN_MODEL")
    assert key not in m  # No error, just not found


def test_approved_bev_keys_type():
    """approved_bev_keys() returns a set of tuples."""
    keys = approved_bev_keys()
    assert isinstance(keys, set)
    for k in keys:
        assert isinstance(k, tuple) and len(k) == 2


def test_approved_bev_model_keys_type():
    """Approved report keys use canonical model names and normalized tuples."""
    keys = approved_bev_model_keys()
    assert isinstance(keys, set)
    for k in keys:
        assert isinstance(k, tuple) and len(k) == 2


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
