"""import_unresolved_series_review.py — Phase 3/4 importer.

Validates an edited grouped review file (CSV or XLSX, produced by
export_unresolved_series_review.py). --dry-run reports what WOULD be written
to series_registry.csv without touching it. Without --dry-run, validated
decisions are written for real via series_registry.write_registry().
"""
import argparse
from datetime import datetime
from pathlib import Path

import pandas as pd

from series_admin import list_unresolved
from series_registry import ALLOWED_POWERTRAIN, load_registry, normalize_key, write_registry

REQUIRED_COLUMNS = ["canonical_brand", "canonical_series", "decision", "approved_powertrain", "evidence", "reviewer", "notes"]
ALLOWED_DECISIONS = {"", "approve", "keep_na", "not_applicable", "skip"}
NA_DECISIONS = {"keep_na", "not_applicable"}
VERIFIABLE_POWERTRAINS = ALLOWED_POWERTRAIN - {"N/A"}


def _s(v):
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return ""
    return str(v).strip()


def _norm_powertrain(v):
    return _s(v).upper()


def load_review_file(path):
    path = Path(path)
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, dtype=str, keep_default_na=False)
    return pd.read_excel(path, dtype=str, keep_default_na=False)


def build_live_groups(queue=None):
    """(normalized canonical_brand, normalized canonical_series) -> currently-unresolved raw rows.

    Sourced from series_admin.list_unresolved(), which already excludes
    verified/not_applicable registry rows — so a group missing here is either
    stale (no longer unresolved) or already settled, and gets rejected below.
    """
    queue = queue if queue is not None else list_unresolved()
    groups = {}
    for item in queue:
        key = normalize_key(item["canonical_brand"], item["canonical_series"])
        groups.setdefault(key, []).append(item)
    return groups


def validate_row(row, live_groups):
    """Returns (outcome, raw_rows, error). outcome in
    {"ignored", "approve", "keep_na", "not_applicable", "error"}."""
    decision = _s(row.get("decision", "")).lower()
    if decision not in ALLOWED_DECISIONS:
        return "error", [], f"invalid decision {decision!r}"
    if decision in ("", "skip"):
        return "ignored", [], None

    approved_powertrain = _norm_powertrain(row.get("approved_powertrain", ""))
    evidence = _s(row.get("evidence", ""))
    reviewer = _s(row.get("reviewer", ""))
    notes = _s(row.get("notes", ""))

    if decision == "approve":
        if approved_powertrain not in VERIFIABLE_POWERTRAINS:
            return "error", [], f"approve requires approved_powertrain in {sorted(VERIFIABLE_POWERTRAINS)}, got {approved_powertrain!r}"
        if not evidence:
            return "error", [], "approve requires nonblank evidence"
        if not reviewer:
            return "error", [], "approve requires nonblank reviewer"
    else:  # keep_na / not_applicable
        if approved_powertrain not in ("", "N/A"):
            return "error", [], f"{decision} requires approved_powertrain blank or N/A, got {approved_powertrain!r}"
        if not reviewer:
            return "error", [], f"{decision} requires nonblank reviewer"
        if not evidence and not notes:
            return "error", [], f"{decision} requires evidence or notes"

    key = normalize_key(_s(row.get("canonical_brand", "")), _s(row.get("canonical_series", "")))
    matches = live_groups.get(key)
    if not matches:
        return "error", [], "group no longer unresolved (stale or already verified) — reload the export"

    return decision, matches, None


def _evaluate(df, live_groups):
    """Validate every row once. Returns (stats, errors, groups), where groups is
    [(outcome, matches, row), ...] for rows that passed validation."""
    stats = {
        "rows_read": len(df), "rows_ignored": 0, "approve_groups": 0,
        "keep_na_groups": 0, "not_applicable_groups": 0, "raw_rows_to_write": 0,
    }
    errors = []
    groups = []
    for i, row in df.iterrows():
        outcome, matches, error = validate_row(row, live_groups)
        if outcome == "ignored":
            stats["rows_ignored"] += 1
        elif outcome == "error":
            errors.append(f"row {i}: {error}")
        else:
            stats[f"{outcome}_groups"] += 1
            stats["raw_rows_to_write"] += len(matches)
            groups.append((outcome, matches, row))
    return stats, errors, groups


def _missing_columns_result(df, extra=None):
    result = {
        "rows_read": len(df), "rows_ignored": 0, "approve_groups": 0, "keep_na_groups": 0,
        "not_applicable_groups": 0, "raw_rows_to_write": 0,
    }
    if extra:
        result.update(extra)
    return result


def dry_run(path, queue=None):
    df = load_review_file(path)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        result = _missing_columns_result(df)
        result["errors"] = [f"missing required columns: {missing}"]
        return result

    live_groups = build_live_groups(queue)
    stats, errors, _ = _evaluate(df, live_groups)
    stats["errors"] = errors
    return stats


def write(path, queue=None, registry_path=None):
    """Validate then write real registry rows for approve/keep_na/not_applicable
    decisions. Nothing is written if any row fails validation."""
    df = load_review_file(path)
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        result = _missing_columns_result(df)
        result["errors"] = [f"missing required columns: {missing}"]
        result["written"] = 0
        return result

    live_groups = build_live_groups(queue)
    stats, errors, groups = _evaluate(df, live_groups)
    if errors:
        stats["errors"] = errors
        stats["written"] = 0
        return stats

    now = datetime.now().isoformat()
    existing_by_key = {
        normalize_key(r["canonical_brand"], r["raw_series"]): r
        for r in load_registry(registry_path)
    }
    for outcome, matches, row in groups:
        review_status = "verified" if outcome == "approve" else "not_applicable"
        powertrain = _norm_powertrain(row.get("approved_powertrain", "")) if outcome == "approve" else "N/A"
        evidence = _s(row.get("evidence", ""))
        notes = _s(row.get("notes", ""))
        merged_evidence = "; ".join(p for p in (evidence, notes) if p)
        reviewer = _s(row.get("reviewer", ""))
        for item in matches:
            key = normalize_key(item["canonical_brand"], item["raw_series"])
            existing_by_key[key] = {
                "canonical_brand": item["canonical_brand"],
                "raw_series": item["raw_series"],
                "canonical_series": item["canonical_series"],
                "powertrain": powertrain,
                "review_status": review_status,
                "evidence": merged_evidence,
                "reviewer": reviewer,
                "reviewed_at": now,
            }

    write_registry(list(existing_by_key.values()), registry_path)
    stats["errors"] = []
    stats["written"] = stats["raw_rows_to_write"]
    return stats


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("path")
    parser.add_argument("--dry-run", action="store_true", help="validate and report only, write nothing")
    args = parser.parse_args()

    result = dry_run(args.path) if args.dry_run else write(args.path)

    print(f"rows read: {result['rows_read']}")
    print(f"rows ignored: {result['rows_ignored']}")
    print(f"approve groups: {result['approve_groups']}")
    print(f"keep_na groups: {result['keep_na_groups']}")
    print(f"not_applicable groups: {result['not_applicable_groups']}")
    print(f"raw registry rows that would be written: {result['raw_rows_to_write']}")
    if not args.dry_run:
        print(f"raw registry rows written: {result.get('written', 0)}")
    print(f"validation errors: {len(result['errors'])}")
    print("PASS" if not result["errors"] else "FAIL")


if __name__ == "__main__":
    main()
