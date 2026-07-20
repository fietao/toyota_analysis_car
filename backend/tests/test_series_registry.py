"""Tests for series_registry.py (plans/reliable-series-powertrain.md Step 2).

No pytest — matches the existing test_canonicalization.py convention. Every
test writes to a throwaway temp file; none of them touch the real
refer/series_registry.csv. Runs from any directory. Exits 0 on PASS, 1 on FAIL.
"""
import inspect
import sys
import tempfile
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

TESTS = Path(__file__).resolve().parent
BACKEND = TESTS.parent
sys.path.insert(0, str(BACKEND))

from series_registry import (
    COLUMNS, RegistryError, load_registry, write_registry, normalize_key,
)

failures = []


def row(canonical_brand="MITSUBISHI", raw_series="TRITON", canonical_series="Triton",
        powertrain="N/A", review_status="unreviewed", evidence="", reviewer="", reviewed_at=""):
    return {
        "canonical_brand": canonical_brand, "raw_series": raw_series,
        "canonical_series": canonical_series, "powertrain": powertrain,
        "review_status": review_status, "evidence": evidence,
        "reviewer": reviewer, "reviewed_at": reviewed_at,
    }


def expect_error(fn, msg):
    try:
        fn()
    except RegistryError:
        return
    failures.append(f"{msg}: expected RegistryError, none raised")


def run_tests():
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp) / "series_registry.csv"

        # 1. Valid registry loads
        valid_rows = [
            row(raw_series="TRITON", review_status="unreviewed", powertrain="N/A"),
            row(raw_series="ATTRAGE", canonical_series="Attrage", powertrain="ICE",
                review_status="verified", evidence="Mitsubishi Thailand spec sheet",
                reviewer="jet", reviewed_at="2026-07-16T10:00:00"),
        ]
        write_registry(valid_rows, tmp_path)
        loaded = load_registry(tmp_path)
        if len(loaded) != 2:
            failures.append(f"Valid registry loads: expected 2 rows, got {len(loaded)}")

        # 2. Invalid Powertrain fails
        expect_error(
            lambda: write_registry([row(powertrain="ELECTRIC")], tmp_path),
            "Invalid Powertrain fails",
        )

        # 3. Invalid status fails
        expect_error(
            lambda: write_registry([row(review_status="approved")], tmp_path),
            "Invalid status fails",
        )

        # 4. Duplicate normalized key fails (case/whitespace-insensitive)
        dup_rows = [
            row(canonical_brand="Mitsubishi", raw_series="Triton"),
            row(canonical_brand="MITSUBISHI", raw_series="  TRITON "),
        ]
        expect_error(lambda: write_registry(dup_rows, tmp_path), "Duplicate normalized key fails")

        # 5. Conflicting mapping fails (conflicting status must still be N/A)
        expect_error(
            lambda: write_registry([row(review_status="conflicting", powertrain="HEV")], tmp_path),
            "Conflicting mapping fails",
        )

        # 6. Verified row without evidence/reviewer/timestamp fails
        expect_error(
            lambda: write_registry([row(powertrain="ICE", review_status="verified",
                                         evidence="", reviewer="jet", reviewed_at="2026-07-16T10:00:00")], tmp_path),
            "Verified row without evidence fails",
        )
        expect_error(
            lambda: write_registry([row(powertrain="ICE", review_status="verified",
                                         evidence="spec sheet", reviewer="", reviewed_at="2026-07-16T10:00:00")], tmp_path),
            "Verified row without reviewer fails",
        )
        expect_error(
            lambda: write_registry([row(powertrain="ICE", review_status="verified",
                                         evidence="spec sheet", reviewer="jet", reviewed_at="")], tmp_path),
            "Verified row without reviewed_at fails",
        )

        # 7a. Empty canonical_series fails
        expect_error(
            lambda: write_registry([row(canonical_series="")], tmp_path),
            "Empty canonical_series fails",
        )
        expect_error(
            lambda: write_registry([row(canonical_series="   ")], tmp_path),
            "Whitespace-only canonical_series fails",
        )

        # 7. Unreviewed non-N/A row fails
        expect_error(
            lambda: write_registry([row(review_status="unreviewed", powertrain="ICE")], tmp_path),
            "Unreviewed non-N/A row fails",
        )

        # 8. Deterministic ordering works
        unordered = [
            row(canonical_brand="TOYOTA", raw_series="COROLLA"),
            row(canonical_brand="HONDA", raw_series="CIVIC"),
            row(canonical_brand="HONDA", raw_series="ACCORD"),
        ]
        write_registry(unordered, tmp_path)
        with open(tmp_path, encoding="utf-8-sig") as f:
            lines = [l.strip() for l in f.readlines()[1:] if l.strip()]
        brands_series = [tuple(l.split(",")[:2]) for l in lines]
        expected = [("HONDA", "ACCORD"), ("HONDA", "CIVIC"), ("TOYOTA", "COROLLA")]
        if brands_series != expected:
            failures.append(f"Deterministic ordering works: expected {expected}, got {brands_series}")

        # 9. Brand is part of the key — same raw_series under different brands must coexist
        same_series_different_brand = [
            row(canonical_brand="MITSUBISHI", raw_series="TRITON"),
            row(canonical_brand="TOYOTA", raw_series="TRITON"),
        ]
        try:
            write_registry(same_series_different_brand, tmp_path)
            loaded = load_registry(tmp_path)
            if len(loaded) != 2:
                failures.append(f"Brand is part of the key: expected 2 rows, got {len(loaded)}")
        except RegistryError as e:
            failures.append(f"Brand is part of the key: unexpected RegistryError: {e}")

    # 10. No dominant-fuel input is accepted or required
    for fn in (load_registry, write_registry):
        params = inspect.signature(fn).parameters
        fuel_like = [p for p in params if "fuel" in p.lower() or "dominant" in p.lower()]
        if fuel_like:
            failures.append(f"No dominant-fuel input: {fn.__name__} accepts fuel-shaped param(s) {fuel_like}")
    import series_registry
    src = inspect.getsource(series_registry)
    if "enrich_fuel_type" in src or "dominant" in src.lower():
        failures.append("No dominant-fuel input: series_registry.py references dominant-fuel logic")


if __name__ == "__main__":
    run_tests()
    if failures:
        print(f"FAIL — {len(failures)} issue(s) in series_registry tests:")
        for f in failures:
            print(f)
        sys.exit(1)
    print("PASS — All series_registry tests passed successfully.")
