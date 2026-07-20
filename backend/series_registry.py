"""series_registry.py — schema, validation, and I/O for refer/series_registry.csv.

plans/reliable-series-powertrain.md Step 2: registry definition and validation
only. Nothing in the production pipeline reads or writes through this module
yet — that integration is a later, separately reviewed slice.

A row may only be `verified` when evidence, reviewer, and reviewed_at are all
present and reviewed_at is a real ISO timestamp. `unreviewed` and
`conflicting` rows must carry powertrain `N/A` — this module never infers a
powertrain from fuel data of any kind; it only validates whatever a human
already wrote into the CSV.
"""
import csv
import os
import tempfile
from datetime import datetime
from pathlib import Path

BASE = Path(__file__).resolve().parent
REGISTRY_PATH = BASE / "refer" / "series_registry.csv"

COLUMNS = [
    "canonical_brand", "raw_series", "canonical_series", "powertrain",
    "review_status", "evidence", "reviewer", "reviewed_at",
]
ALLOWED_POWERTRAIN = {"ICE", "HEV", "PHEV", "BEV", "N/A"}
ALLOWED_STATUS = {"verified", "unreviewed", "conflicting"}


class RegistryError(Exception):
    """Carries every validation issue found, not just the first."""

    def __init__(self, issues):
        self.issues = list(issues)
        super().__init__("; ".join(self.issues))


def normalize_key(canonical_brand, raw_series):
    def _norm(v):
        return " ".join(str(v or "").strip().split()).upper()
    return _norm(canonical_brand), _norm(raw_series)


def sort_key(row):
    return normalize_key(row.get("canonical_brand", ""), row.get("raw_series", ""))


def _validate_rows(rows):
    """Return a list of issue strings; empty means the rows are valid."""
    issues = []
    seen_keys = {}
    for row_num, row in enumerate(rows, start=1):
        label = f"row {row_num}"
        missing_cols = [c for c in COLUMNS if c not in row]
        if missing_cols:
            issues.append(f"{label}: missing column(s) {missing_cols}")
            continue

        brand = (row["canonical_brand"] or "").strip()
        raw_series = (row["raw_series"] or "").strip()
        canonical_series = (row["canonical_series"] or "").strip()
        tag = f"{label} ({brand}/{raw_series})"
        if not brand:
            issues.append(f"{label}: canonical_brand is required")
        if not raw_series:
            issues.append(f"{label}: raw_series is required")
        if not canonical_series:
            issues.append(f"{label}: canonical_series is required")

        key = normalize_key(brand, raw_series)
        if key in seen_keys:
            issues.append(f"{tag}: duplicate key {key} also at row {seen_keys[key]}")
        else:
            seen_keys[key] = row_num

        powertrain = (row["powertrain"] or "").strip()
        if powertrain not in ALLOWED_POWERTRAIN:
            issues.append(
                f"{tag}: invalid powertrain {powertrain!r}, must be one of {sorted(ALLOWED_POWERTRAIN)}"
            )
            powertrain = None

        status = (row["review_status"] or "").strip()
        if status not in ALLOWED_STATUS:
            issues.append(
                f"{tag}: invalid review_status {status!r}, must be one of {sorted(ALLOWED_STATUS)}"
            )
            continue

        if status == "verified":
            if powertrain == "N/A":
                issues.append(f"{tag}: verified row must have a real powertrain, not N/A")
            if not (row["evidence"] or "").strip():
                issues.append(f"{tag}: verified row requires evidence")
            if not (row["reviewer"] or "").strip():
                issues.append(f"{tag}: verified row requires reviewer")
            reviewed_at = (row["reviewed_at"] or "").strip()
            if not reviewed_at:
                issues.append(f"{tag}: verified row requires reviewed_at")
            else:
                try:
                    datetime.fromisoformat(reviewed_at)
                except ValueError:
                    issues.append(f"{tag}: reviewed_at {reviewed_at!r} is not a valid ISO timestamp")
        else:
            if powertrain is not None and powertrain != "N/A":
                issues.append(
                    f"{tag}: {status} rows must have powertrain N/A, got {powertrain!r}"
                )
    return issues


def resolve_registry_path(path=None):
    """Centralized override resolution: explicit path > SERIES_REGISTRY_PATH env > production
    default. Every reader/writer (Admin service, pipeline, validators) must resolve through
    this so a temporary test registry is honored everywhere, and the production path is never
    silently swapped when the env var is unset."""
    if path:
        return Path(path)
    env = os.environ.get("SERIES_REGISTRY_PATH")
    return Path(env) if env else REGISTRY_PATH


def load_registry(path=None):
    """Load and validate series_registry.csv. Raises RegistryError with every issue found."""
    path = resolve_registry_path(path)
    if not path.exists():
        return []

    with open(path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames != COLUMNS:
            raise RegistryError([f"header mismatch: expected {COLUMNS}, got {reader.fieldnames}"])
        rows = list(reader)

    issues = _validate_rows(rows)
    if issues:
        raise RegistryError(issues)
    return rows


def verified_powertrain_map(path=None):
    """(canonical_brand, raw_series) normalized key -> powertrain, verified rows only."""
    return {
        normalize_key(row["canonical_brand"], row["raw_series"]): row["powertrain"]
        for row in load_registry(path)
        if row["review_status"] == "verified"
    }


def canonical_series_map(path=None):
    """(canonical_brand, raw_series) normalized key -> canonical_series, any review_status.

    Separate from verified_powertrain_map() by design: a canonical *name* is a
    display-only claim, not a powertrain claim, so unreviewed and conflicting
    rows may supply one. This function never returns a powertrain value."""
    return {
        normalize_key(row["canonical_brand"], row["raw_series"]): row["canonical_series"]
        for row in load_registry(path)
    }


def write_registry(rows, path=None):
    """Validate then write the registry atomically (tempfile + os.replace, deterministic order)."""
    issues = _validate_rows(rows)
    if issues:
        raise RegistryError(issues)

    path = resolve_registry_path(path)
    ordered = sorted(rows, key=sort_key)
    fd, tmp_path = tempfile.mkstemp(dir=str(path.parent), suffix=".tmp")
    try:
        with os.fdopen(fd, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=COLUMNS)
            writer.writeheader()
            for row in ordered:
                writer.writerow({c: row.get(c, "") for c in COLUMNS})
        os.replace(tmp_path, str(path))
    except Exception:
        os.unlink(tmp_path)
        raise
