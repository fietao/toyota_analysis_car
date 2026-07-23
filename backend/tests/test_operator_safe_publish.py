"""test_operator_safe_publish.py — no-collapse guarantee for monthly_update.safe_publish.

Pure filesystem, stdlib only, no pandas — so the safe-publish/rollback contract is
verifiable without the build environment (this repo's local env has no pandas). Exits 0
on PASS, 1 on FAIL, matching the existing test_*.py convention.

Contract under test:
  * success  -> every public file holds the new (staged) content; no backup left behind.
  * failure  -> public is left byte-for-byte as it was before the call (rollback).
  * skip     -> building into staging never touches public (the "validation failed, do
                not publish" path leaves the live data intact).
"""
import os
import shutil
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

import monthly_update as mu  # stdlib-only top imports; safe without pandas

failures = []
NAMES = ["a.json", "b.json", "c.json"]


def _scratch():
    root = Path(tempfile.mkdtemp())
    public, staging, backup = root / "data", root / "data.staging", root / "data.bak"
    public.mkdir()
    staging.mkdir()
    return root, public, staging, backup


def _write_set(d, prefix):
    for n in NAMES:
        (d / n).write_text(f"{prefix}:{n}", encoding="utf-8")


def _read_all(d):
    return {n: (d / n).read_text(encoding="utf-8") for n in NAMES}


def test_success_replaces_and_cleans():
    root, public, staging, backup = _scratch()
    try:
        _write_set(public, "OLD")
        _write_set(staging, "NEW")
        mu.safe_publish(staging, public, backup, NAMES)
        if _read_all(public) != {n: f"NEW:{n}" for n in NAMES}:
            failures.append(f"success: public not updated to staged content: {_read_all(public)}")
        if backup.exists():
            failures.append("success: backup dir was not cleaned up")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_failure_rolls_back_public():
    root, public, staging, backup = _scratch()
    try:
        _write_set(public, "OLD")
        before = _read_all(public)
        # Stage only a,b — missing c forces os.replace to raise partway, after a,b moved.
        (staging / "a.json").write_text("NEW:a.json", encoding="utf-8")
        (staging / "b.json").write_text("NEW:b.json", encoding="utf-8")
        raised = False
        try:
            mu.safe_publish(staging, public, backup, NAMES)
        except OSError:
            raised = True
        if not raised:
            failures.append("failure: expected safe_publish to raise on a missing staged file")
        if _read_all(public) != before:
            failures.append(f"failure: public not restored to pre-call state: {_read_all(public)}")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_staging_build_does_not_touch_public():
    """The 'validation failed -> skip publish' path: writing staging leaves public intact."""
    root, public, staging, backup = _scratch()
    try:
        _write_set(public, "OLD")
        before = _read_all(public)
        _write_set(staging, "NEW")  # build produced staging, but we never call safe_publish
        if _read_all(public) != before:
            failures.append("skip: building staging must not mutate public")
    finally:
        shutil.rmtree(root, ignore_errors=True)


def test_first_run_no_existing_public():
    """No prior public files (first ever run): publish just creates them, no rollback needed."""
    root, public, staging, backup = _scratch()
    try:
        _write_set(staging, "NEW")
        mu.safe_publish(staging, public, backup, NAMES)
        if _read_all(public) != {n: f"NEW:{n}" for n in NAMES}:
            failures.append("first-run: public not created from staging")
        if backup.exists():
            failures.append("first-run: backup dir was not cleaned up")
    finally:
        shutil.rmtree(root, ignore_errors=True)


if __name__ == "__main__":
    test_success_replaces_and_cleans()
    test_failure_rolls_back_public()
    test_staging_build_does_not_touch_public()
    test_first_run_no_existing_public()
    if failures:
        print(f"FAIL — {len(failures)} issue(s) in safe-publish tests:")
        for f in failures:
            print(f)
        sys.exit(1)
    print("PASS — All safe-publish tests passed successfully.")
