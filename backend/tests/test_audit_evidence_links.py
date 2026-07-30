"""test_audit_evidence_links.py — offline unit tests for audit_evidence_links.py."""
import sys
import os
import pytest
import pandas as pd
from unittest.mock import patch, MagicMock
from pathlib import Path

# Setup paths to import audit_evidence_links
TESTS = Path(__file__).resolve().parent
BACKEND = TESTS.parent
sys.path.insert(0, str(BACKEND))

import audit_evidence_links

@pytest.fixture
def base_approved_row():
    return {
        "brand2": "BYD",
        "raw_model": "SEAL",
        "review_status": "approved",
        "evidence": "https://example.com/models/byd-seal"
    }

def test_audit_200(capsys, base_approved_row):
    mock_df = pd.DataFrame([base_approved_row])
    with patch('pandas.read_csv', return_value=mock_df), \
         patch('requests.get') as mock_get:

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.url = "https://example.com/models/byd-seal"
        mock_get.return_value = mock_resp

        with pytest.raises(SystemExit) as excinfo:
            audit_evidence_links.audit()

        assert excinfo.value.code == 0

        captured = capsys.readouterr()
        assert "BYD | SEAL | 200 | https://example.com/models/byd-seal | article" in captured.out
        assert "Approved rows: 1" in captured.out
        assert "Checked URLs: 1" in captured.out
        assert "Passed: 1" in captured.out
        assert "Failed: 0" in captured.out
        assert "Skipped: 0" in captured.out

def test_audit_301_to_model_page(capsys, base_approved_row):
    # Simulated 301 redirecting to a model page
    mock_df = pd.DataFrame([base_approved_row])
    with patch('pandas.read_csv', return_value=mock_df), \
         patch('requests.get') as mock_get:

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.url = "https://example.com/models/byd-seal/deep"
        mock_get.return_value = mock_resp

        with pytest.raises(SystemExit) as excinfo:
            audit_evidence_links.audit()

        assert excinfo.value.code == 0

        captured = capsys.readouterr()
        assert "Passed: 1" in captured.out
        assert "Failed: 0" in captured.out

def test_audit_301_to_homepage(capsys, base_approved_row):
    # Simulated 301 redirecting to homepage (generic URL)
    mock_df = pd.DataFrame([base_approved_row])
    with patch('pandas.read_csv', return_value=mock_df), \
         patch('requests.get') as mock_get:

        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.url = "https://example.com/en-us/home"
        mock_get.return_value = mock_resp

        with pytest.raises(SystemExit) as excinfo:
            audit_evidence_links.audit()

        assert excinfo.value.code == 1

        captured = capsys.readouterr()
        assert "Passed: 0" in captured.out
        assert "Failed: 1" in captured.out
        assert "redirected to generic URL" in captured.out

def test_audit_403(capsys, base_approved_row):
    mock_df = pd.DataFrame([base_approved_row])
    with patch('pandas.read_csv', return_value=mock_df), \
         patch('requests.get') as mock_get:

        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.url = "https://example.com/models/byd-seal"
        mock_get.return_value = mock_resp

        with pytest.raises(SystemExit) as excinfo:
            audit_evidence_links.audit()

        assert excinfo.value.code == 1

        captured = capsys.readouterr()
        assert "BYD | SEAL | UNVERIFIED | https://example.com/models/byd-seal | article" in captured.out
        assert "Passed: 0" in captured.out
        assert "Failed: 1" in captured.out
        assert "is UNVERIFIED (403)" in captured.out

def test_audit_404(capsys, base_approved_row):
    mock_df = pd.DataFrame([base_approved_row])
    with patch('pandas.read_csv', return_value=mock_df), \
         patch('requests.get') as mock_get:

        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.url = "https://example.com/models/byd-seal"
        mock_get.return_value = mock_resp

        with pytest.raises(SystemExit) as excinfo:
            audit_evidence_links.audit()

        assert excinfo.value.code == 1

        captured = capsys.readouterr()
        assert "Passed: 0" in captured.out
        assert "Failed: 1" in captured.out

def test_audit_500(capsys, base_approved_row):
    mock_df = pd.DataFrame([base_approved_row])
    with patch('pandas.read_csv', return_value=mock_df), \
         patch('requests.get') as mock_get:

        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.url = "https://example.com/models/byd-seal"
        mock_get.return_value = mock_resp

        with pytest.raises(SystemExit) as excinfo:
            audit_evidence_links.audit()

        assert excinfo.value.code == 1

        captured = capsys.readouterr()
        assert "Passed: 0" in captured.out
        assert "Failed: 1" in captured.out

def test_audit_missing_url(capsys):
    mock_df = pd.DataFrame([
        {
            "brand2": "BYD",
            "raw_model": "SEAL",
            "review_status": "approved",
            "evidence": "brochure.pdf"
        }
    ])
    with patch('pandas.read_csv', return_value=mock_df), \
         patch('requests.get') as mock_get:

        with pytest.raises(SystemExit) as excinfo:
            audit_evidence_links.audit()

        assert excinfo.value.code == 0

        mock_get.assert_not_called()

        captured = capsys.readouterr()
        assert "BYD | SEAL | SKIPPED_NO_URL | | " in captured.out
        assert "Passed: 0" in captured.out
        assert "Failed: 0" in captured.out
        assert "Skipped: 1" in captured.out

def test_audit_execution_from_repository_root(capsys):
    # Save the current CWD
    old_cwd = os.getcwd()
    # Find the repo root by traversing up from this test file
    repo_root = str(Path(__file__).resolve().parents[2])

    mock_df = pd.DataFrame([{
        "brand2": "BYD",
        "raw_model": "SEAL",
        "review_status": "approved",
        "evidence": "https://example.com/models/byd-seal"
    }])

    with patch('pandas.read_csv') as mock_read_csv, \
         patch('requests.get') as mock_get:

        mock_read_csv.return_value = mock_df
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.url = "https://example.com/models/byd-seal"
        mock_get.return_value = mock_resp

        try:
            os.chdir(repo_root)
            with pytest.raises(SystemExit) as excinfo:
                audit_evidence_links.audit()

            assert excinfo.value.code == 0

            mock_read_csv.assert_called_once()
            called_path = mock_read_csv.call_args[0][0]

            # Assert that the CSV path passed is absolute and resolves to backend/config/model_powertrain_review.csv
            assert os.path.isabs(called_path)
            assert Path(called_path).name == "model_powertrain_review.csv"
            assert "backend" in called_path

        finally:
            os.chdir(old_cwd)

if __name__ == '__main__':
    pytest.main([__file__, "-v"])
