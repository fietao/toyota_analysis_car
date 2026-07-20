"""series_admin.py — local Admin review backend (Step 5A).

plans/reliable-series-powertrain.md Step 5: computes the unresolved-series
review queue on the fly from model parquet rows minus verified
series_registry.csv rows, and validates + persists one review decision at a
time through series_registry.write_registry(). No queue file, no dominant-fuel
inference, no popup/UI here — that is a separate slice.
"""
from datetime import datetime
from pathlib import Path

import pandas as pd

from series_registry import (
    ALLOWED_POWERTRAIN, load_registry, normalize_key, resolve_registry_path, write_registry,
)

BASE = Path(__file__).resolve().parent
DEFAULT_MODEL_PARQUET = BASE / "test_model_cleaned.parquet"

REQUIRED_REVIEW_FIELDS = ["canonical_brand", "raw_series", "canonical_series", "powertrain", "evidence", "reviewer"]
VERIFIABLE_POWERTRAINS = ALLOWED_POWERTRAIN - {"N/A"}


class ReviewValidationError(Exception):
    """Carries every validation issue found; no partial write ever happens."""

    def __init__(self, issues):
        self.issues = list(issues)
        super().__init__("; ".join(self.issues))


def _norm_col(series):
    return series.astype(str).str.strip().str.split().str.join(" ").str.upper()


def list_unresolved(model_parquet_path=DEFAULT_MODEL_PARQUET, registry_path=None):
    """Unresolved/conflicting (canonical_brand, raw_series) pairs, verified rows excluded."""
    registry_path = resolve_registry_path(registry_path)
    df = pd.read_parquet(str(model_parquet_path), columns=["ยี่ห้อรถ2", "รุ่นรถ", "จำนวนรถ"])
    df["_bk"] = _norm_col(df["ยี่ห้อรถ2"])
    df["_sk"] = _norm_col(df["รุ่นรถ"])
    grouped = df.groupby(["_bk", "_sk"]).agg(
        canonical_brand=("ยี่ห้อรถ2", "first"),
        raw_series=("รุ่นรถ", "first"),
        total_units=("จำนวนรถ", "sum"),
    ).reset_index()

    registry_by_key = {
        normalize_key(row["canonical_brand"], row["raw_series"]): row
        for row in load_registry(registry_path)
    }

    queue = []
    for _, r in grouped.sort_values(["_bk", "_sk"]).iterrows():
        key = (r["_bk"], r["_sk"])
        existing = registry_by_key.get(key)
        if existing is not None and existing["review_status"] == "verified":
            continue
        queue.append({
            "canonical_brand": existing["canonical_brand"] if existing else str(r["canonical_brand"]).strip(),
            "raw_series": str(r["raw_series"]).strip(),
            "canonical_series": existing["canonical_series"] if existing else str(r["raw_series"]).strip(),
            "total_units": int(r["total_units"]),
            "status": existing["review_status"] if existing else "unreviewed",
        })
    return queue


def save_review(payload, registry_path=None):
    """Validate and persist one verified review decision. Raises ReviewValidationError,
    never writes partially."""
    registry_path = resolve_registry_path(registry_path)

    missing = [f for f in REQUIRED_REVIEW_FIELDS if not str(payload.get(f, "")).strip()]
    if missing:
        raise ReviewValidationError([f"missing required field(s): {missing}"])

    powertrain = str(payload["powertrain"]).strip()
    if powertrain not in VERIFIABLE_POWERTRAINS:
        raise ReviewValidationError(
            [f"invalid powertrain {powertrain!r}, must be one of {sorted(VERIFIABLE_POWERTRAINS)}"]
        )

    canonical_brand = str(payload["canonical_brand"]).strip()
    raw_series = str(payload["raw_series"]).strip()
    key = normalize_key(canonical_brand, raw_series)

    rows = load_registry(registry_path)
    existing = next((r for r in rows if normalize_key(r["canonical_brand"], r["raw_series"]) == key), None)
    if existing is not None and existing["review_status"] == "verified":
        raise ReviewValidationError(
            [f"{canonical_brand}/{raw_series} is already verified — reload the queue (stale or duplicate update)"]
        )

    new_row = {
        "canonical_brand": canonical_brand,
        "raw_series": raw_series,
        "canonical_series": str(payload["canonical_series"]).strip(),
        "powertrain": powertrain,
        "review_status": "verified",
        "evidence": str(payload["evidence"]).strip(),
        "reviewer": str(payload["reviewer"]).strip(),
        "reviewed_at": datetime.now().isoformat(),
    }

    remaining = [r for r in rows if normalize_key(r["canonical_brand"], r["raw_series"]) != key]
    write_registry(remaining + [new_row], registry_path)
    return new_row
