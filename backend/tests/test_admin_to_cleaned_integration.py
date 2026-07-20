"""Integration test for plans/reliable-series-powertrain.md Step 5C.

Proves the full path from an Admin review decision through to the cleaned
model output: Step 5A save -> Admin boundary reload/restart -> the pipeline's
own canonical-mapping seam (build_cleaned.add_derived_columns), all reading
the SAME temporary registry via SERIES_REGISTRY_PATH. If build_cleaned.py's
verified_powertrain_map() call ever ignores the env override again (e.g. a
default re-bound at import time), this test goes red because the pipeline
seam would see an empty/production registry instead of the reviewed row.

No pytest — matches the existing test_*.py convention. Uses a temp registry
and temp model/fuel frames only; never touches backend/refer/series_registry.csv
or a real parquet. Exits 0 on PASS, 1 on FAIL.
"""
import hashlib
import os
import sys
import tempfile
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

TESTS = Path(__file__).resolve().parent
BACKEND = TESTS.parent
sys.path.insert(0, str(BACKEND))

from build_cleaned import add_derived_columns
from series_admin import save_review
from series_registry import RegistryError, load_registry, verified_powertrain_map

REAL_REGISTRY = BACKEND / "refer" / "series_registry.csv"

failures = []


def base_maps(series_powertrain_map):
    return {
        "powertrain_map": {},
        "merged_brand2_map": {},
        "series_powertrain_map": series_powertrain_map,
        "series_name_map": {},
        "unknown_fuels": set(),
    }


def run_tests():
    real_hash_before = hashlib.sha256(REAL_REGISTRY.read_bytes()).hexdigest()

    with tempfile.TemporaryDirectory() as tmp:
        registry_path = Path(tmp) / "series_registry.csv"
        os.environ["SERIES_REGISTRY_PATH"] = str(registry_path)
        try:
            # 1. Save the reviewed decision through the Step 5A boundary (env-resolved path).
            save_review({
                "canonical_brand": "MG", "raw_series": "MG4 ELECTRIC",
                "canonical_series": "MG4 Electric", "powertrain": "BEV",
                "evidence": "MG Thailand official spec sheet", "reviewer": "jet",
            })

            # 2. Reload/restart the Admin boundary: a fresh load_registry() call must see it.
            reloaded = load_registry()
            match = next((r for r in reloaded if r["raw_series"] == "MG4 ELECTRIC"), None)
            if match is None or match["review_status"] != "verified" or match["powertrain"] != "BEV":
                failures.append(f"Reload/restart preserves the decision: got {match}")

            # 3. Run the canonical mapping/rebuild seam against the SAME temp registry,
            #    via the exact function build_cleaned.py's pipeline calls with no path arg.
            series_pt_map = verified_powertrain_map()

            df_model = pd.DataFrame([
                {"ยี่ห้อรถ": "MG", "รุ่นรถ": "MG4 ELECTRIC", "จำนวนรถ": 20},
                {"ยี่ห้อรถ": "MG", "รุ่นรถ": "MG ZS", "จำนวนรถ": 8},
            ])
            df_fuel = pd.DataFrame([{"ยี่ห้อรถ": "MG", "ชนิดเชื้อเพลิง": "ไฟฟ้า", "จำนวนรถ": 20}])

            df_model, _ = add_derived_columns(df_model, df_fuel, base_maps(series_pt_map))

            reviewed = df_model[df_model["รุ่นรถ"] == "MG4 ELECTRIC"].iloc[0]
            sibling = df_model[df_model["รุ่นรถ"] == "MG ZS"].iloc[0]

            if reviewed["Powertrain"] != "BEV":
                failures.append(f"Reviewed row receives its verified Powertrain: got {reviewed['Powertrain']!r}")
            if reviewed["include_in_bev_model_report"] != True:  # noqa: E712
                failures.append("include_in_bev_model_report is true for the reviewed BEV: got False")
            if sibling["Powertrain"] != "N/A":
                failures.append(f"Unreviewed sibling remains N/A: got {sibling['Powertrain']!r}")
            if sibling["include_in_bev_model_report"] != False:  # noqa: E712
                failures.append("Unreviewed sibling must not be flagged for the BEV report")

            # 4. An invalid/conflicting registry must fail the build, never silently fall back.
            bad_registry = Path(tmp) / "bad_series_registry.csv"
            bad_registry.write_text(
                "canonical_brand,raw_series,canonical_series,powertrain,review_status,evidence,reviewer,reviewed_at\r\n"
                "MG,MG4 ELECTRIC,MG4 Electric,ELECTRIC,verified,spec,jet,2026-07-17T10:00:00\r\n",
                encoding="utf-8",
            )
            os.environ["SERIES_REGISTRY_PATH"] = str(bad_registry)
            try:
                verified_powertrain_map()
                failures.append("Invalid registry prevents build: no error raised for invalid powertrain")
            except RegistryError:
                pass
        finally:
            del os.environ["SERIES_REGISTRY_PATH"]

    real_hash_after = hashlib.sha256(REAL_REGISTRY.read_bytes()).hexdigest()
    if real_hash_before != real_hash_after:
        failures.append("Production series_registry.csv remains hash-identical: hash changed")


if __name__ == "__main__":
    run_tests()
    if failures:
        print(f"FAIL — {len(failures)} issue(s) in admin-to-cleaned integration test:")
        for f in failures:
            print(f)
        sys.exit(1)
    print("PASS — Admin-to-cleaned integration test passed successfully.")
