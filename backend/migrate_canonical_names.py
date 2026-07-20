"""migrate_canonical_names.py — plans/reliable-series-powertrain.md Step 7B/7C.

One-time, re-runnable migration of canonical-name data from the legacy
refer/model2_map.csv into refer/series_registry.csv, the sole canonical-name
and powertrain authority as of the final maintenance pass.

refer/model2_map.csv has since been deleted (its content is fully migrated;
series_registry.csv is the durable artifact). This script is kept, repeat-safe
and functioning, as the documented provenance of that migration and in case a
future legacy CSV needs the same treatment, but it can no longer actually run
— MODEL2_MAP_CSV.exists() is False from here on, and main() reports that
clearly instead of an unhandled traceback. Delete this file once nobody needs
that provenance/history reference (git history preserves it either way).

Scope: canonical NAME only. Every migrated row is written as
powertrain=N/A, review_status=unreviewed, evidence/reviewer/reviewed_at empty.
This module never infers or writes a powertrain — model2_map.csv never carried
powertrain data to migrate in the first place.

Repeat-safe / non-destructive: a key already present in series_registry.csv —
at ANY review_status, including a human-verified row from the admin UI — is
never touched, overwritten, or re-derived. Re-running only ever adds rows for
keys that don't exist yet.

Every model2_map.csv row is a migration candidate, including rows where the
CSV's own raw_series and canonical_series strings are byte-identical: the raw
DLT รุ่นรถ text is not reliably uppercase (e.g. a real row may read "mu-X"
while model2_map.csv keys it as "MU-X" -> "MU-X"), so even an "identity" CSV
row still fixes a display casing that a given data row may not itself carry.
Skipping identity rows silently regresses casing for any row whose exact
casing differs from the CSV's own key, which is a real, if quiet, canonical-
name regression -- this script migrates the full 8,376-row set instead.

A key is migrated only when: (a) it is observed under exactly one canonical
brand in the current cleaned model data, directly, OR (b) every raw variant
sharing its target canonical_series that IS present in current data agrees on
a single brand (sibling-group inheritance -- grounded in model2_map.csv's own
grouping plus real data, never a fabricated guess). Keys that remain
ambiguous or have no data-grounded brand at all are skipped.
"""
import sys
from pathlib import Path

import pandas as pd

sys.stdout.reconfigure(encoding="utf-8")

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE))

from series_registry import load_registry, normalize_key, write_registry

MODEL2_MAP_CSV = BASE / "refer" / "model2_map.csv"
MODEL_PARQUET = BASE / "test_model_cleaned.parquet"


def build_migration_rows():
    df_map = pd.read_csv(str(MODEL2_MAP_CSV), encoding="utf-8-sig")
    raw_key = df_map["รุ่นรถ_raw"].astype(str).str.strip().str.upper()
    canon = df_map["รุ่นรถ2"].astype(str).str.strip()

    renames = dict(zip(raw_key, canon))

    mdf = pd.read_parquet(str(MODEL_PARQUET))
    mdf["_raw_up"] = mdf["รุ่นรถ"].astype(str).str.strip().str.upper()
    mdf["_brand"] = mdf["ยี่ห้อรถ2"].astype(str).str.strip().str.upper()

    brands_by_raw = mdf[mdf["_raw_up"].isin(renames)].groupby("_raw_up")["_brand"].unique()
    direct_brand = {k: list(v)[0] for k, v in brands_by_raw.items() if len(v) == 1}
    ambiguous_raw = {k for k, v in brands_by_raw.items() if len(v) > 1}

    # Sibling-group inheritance: raw variants targeting the same canonical_series
    # that agree on a single data-confirmed brand across the group.
    by_target = {}
    for raw, target in renames.items():
        by_target.setdefault(target.strip().upper(), []).append(raw)

    rows, skipped_absent, skipped_multi_brand = [], [], []
    for raw, canonical in renames.items():
        brand = direct_brand.get(raw)
        source = "direct"
        if brand is None and raw not in ambiguous_raw:
            siblings = by_target[canonical.strip().upper()]
            sibling_brands = {direct_brand[s] for s in siblings if s in direct_brand}
            if len(sibling_brands) == 1:
                brand = next(iter(sibling_brands))
                source = "sibling-group"

        if brand is None:
            if raw in ambiguous_raw:
                skipped_multi_brand.append((raw, list(brands_by_raw[raw])))
            else:
                skipped_absent.append(raw)
            continue

        rows.append({
            "canonical_brand": brand,
            "raw_series": raw,
            "canonical_series": canonical,
            "powertrain": "N/A",
            "review_status": "unreviewed",
            "evidence": "",
            "reviewer": "",
            "reviewed_at": "",
            "_source": source,
        })

    # model2_map.csv has near-duplicate raw strings that differ only in internal
    # whitespace (e.g. "CONTINENTAL GT 650" vs "CONTINENTAL GT  650") and collapse
    # to the same normalize_key(); keep one deterministically (first by raw string).
    deduped, seen = [], set()
    for row in sorted(rows, key=lambda r: r["raw_series"]):
        key = normalize_key(row["canonical_brand"], row["raw_series"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(row)

    return deduped, skipped_absent, skipped_multi_brand


def main():
    if not MODEL2_MAP_CSV.exists():
        print(f"Nothing to migrate: {MODEL2_MAP_CSV} no longer exists.")
        print("series_registry.csv already holds everything this script could ever produce "
              "from it; this is expected, not an error.")
        return

    rows, skipped_absent, skipped_multi_brand = build_migration_rows()

    existing = load_registry()
    existing_keys = {normalize_key(r["canonical_brand"], r["raw_series"]) for r in existing}
    new_rows = [r for r in rows if normalize_key(r["canonical_brand"], r["raw_series"]) not in existing_keys]

    # write_registry() validates against a fixed column set; drop the diagnostic-only field.
    write_registry(existing + [{k: v for k, v in r.items() if k != "_source"} for r in new_rows])

    direct = sum(1 for r in new_rows if r["_source"] == "direct")
    sibling = sum(1 for r in new_rows if r["_source"] == "sibling-group")
    print(f"Migrated {len(new_rows)} canonical-name row(s) into series_registry.csv "
          f"({direct} direct, {sibling} sibling-group)")
    print(f"  skipped (no data-grounded brand at all):    {len(skipped_absent)}")
    print(f"  skipped (spans >1 brand, ambiguous):        {len(skipped_multi_brand)}")
    for raw, brands in skipped_multi_brand:
        print(f"    {raw}: {brands}")
    verified = [r for r in new_rows if r["review_status"] == "verified"]
    print(f"  verified rows written: {len(verified)} (must be 0)")


if __name__ == "__main__":
    main()
