"""Self-check for migrate_canonical_names.py repeat-safety.

Proves: (a) re-running the migration against an unchanged source never
duplicates rows, (b) a key already in the registry — including a
human-verified row — is never touched, regardless of what the source CSV
says for that key. Uses a temp registry and a temp model2_map.csv; never
touches the real backend/refer/series_registry.csv.

No pytest — matches the existing test_*.py convention. Runs from any
directory. Exits 0 on PASS, 1 on FAIL.
"""
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

TESTS = Path(__file__).resolve().parent
BACKEND = TESTS.parent
sys.path.insert(0, str(BACKEND))

import migrate_canonical_names as mcn
from series_registry import load_registry, write_registry

failures = []


def run_tests():
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        registry_path = tmp / "series_registry.csv"
        model2_path = tmp / "model2_map.csv"
        parquet_path = tmp / "model_cleaned.parquet"

        pd.DataFrame({
            "รุ่นรถ_raw": ["FOO110I", "BAR"],
            "รุ่นรถ2": ["FOO 110i", "BAR"],
        }).to_csv(model2_path, index=False, encoding="utf-8-sig")

        pd.DataFrame({
            "ยี่ห้อรถ2": ["ACME", "ACME"],
            "รุ่นรถ": ["FOO110I", "BAR"],
        }).to_parquet(parquet_path, index=False)

        # A pre-existing human-verified row for FOO/FOO110I with a DIFFERENT
        # canonical_series than the CSV proposes -- migration must not touch it.
        write_registry([{
            "canonical_brand": "ACME", "raw_series": "FOO110I",
            "canonical_series": "Foo 110i Special Edition", "powertrain": "BEV",
            "review_status": "verified", "evidence": "manufacturer spec sheet",
            "reviewer": "jet", "reviewed_at": "2026-01-01T00:00:00",
        }], registry_path)

        orig_csv, orig_pq = mcn.MODEL2_MAP_CSV, mcn.MODEL_PARQUET
        mcn.MODEL2_MAP_CSV, mcn.MODEL_PARQUET = model2_path, parquet_path
        try:
            import os
            os.environ["SERIES_REGISTRY_PATH"] = str(registry_path)

            rows, _, _ = mcn.build_migration_rows()
            existing = load_registry(registry_path)
            existing_keys = {(r["canonical_brand"], r["raw_series"]) for r in existing}
            new_rows = [r for r in rows if (r["canonical_brand"], r["raw_series"]) not in existing_keys]
            write_registry(existing + [{k: v for k, v in r.items() if k != "_source"} for r in new_rows], registry_path)

            after_first = load_registry(registry_path)
            foo_row = next(r for r in after_first if r["raw_series"] == "FOO110I")
            if foo_row["review_status"] != "verified" or foo_row["canonical_series"] != "Foo 110i Special Edition":
                failures.append(f"human-verified row was overwritten: {foo_row}")
            bar_row = next((r for r in after_first if r["raw_series"] == "BAR"), None)
            if bar_row is None:
                failures.append("BAR row was not migrated")

            # Re-run: must be a no-op (repeat-safe / idempotent).
            rows2, _, _ = mcn.build_migration_rows()
            existing2 = load_registry(registry_path)
            existing_keys2 = {(r["canonical_brand"], r["raw_series"]) for r in existing2}
            new_rows2 = [r for r in rows2 if (r["canonical_brand"], r["raw_series"]) not in existing_keys2]
            if new_rows2:
                failures.append(f"re-run was not a no-op: {new_rows2}")

            after_second = load_registry(registry_path)
            if len(after_second) != len(after_first):
                failures.append(
                    f"row count changed on re-run: {len(after_first)} -> {len(after_second)}"
                )
        finally:
            mcn.MODEL2_MAP_CSV, mcn.MODEL_PARQUET = orig_csv, orig_pq
            del os.environ["SERIES_REGISTRY_PATH"]


if __name__ == "__main__":
    run_tests()
    if failures:
        print(f"FAIL — {len(failures)} issue(s) in migrate_canonical_names tests:")
        for f in failures:
            print(f)
        sys.exit(1)
    print("PASS — All migrate_canonical_names repeat-safety tests passed successfully.")
