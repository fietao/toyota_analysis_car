"""bev_candidate_rules.py — pure matching rules for the New BEV Model Watchlist.

Stdlib-only (no pandas), so the rules are testable in isolation the same way
operator_preflight.py mirrors model_map.py's review contract without importing pandas.
This module never decides review_status; it only flags a *candidate* for human review —
model_map.py / model_powertrain_review.csv remain the only source of truth for approval.
"""
import re

# Suppression wins over every match rule below (checked first in classify()).
SUPPRESS_TOKENS = {"PHEV", "HEV", "HYBRID", "REEV", "EREV"}
SUPPRESS_SUBSTRINGS = ("DM-I", "DIESEL", "PETROL", "GASOLINE", "E-POWER", "RANGE EXTENDER")
NAME_MARKER_TOKENS = {"BEV", "EV", "ELECTRIC"}

REASON_PRIORITY = {
    "approved_family_match": 0,
    "approved_model_match": 1,
    "electric_name_marker": 2,
}
CONFIDENCE = {
    "approved_family_match": "high",
    "approved_model_match": "high",
    "electric_name_marker": "medium",
}


def normalize(value) -> str:
    """Collapse whitespace + uppercase, matching model_map.normalize_key's per-field rule."""
    return " ".join(str(value or "").strip().split()).upper()


def tokenize(text) -> list:
    """Uppercase word tokens, splitting on any non-alphanumeric boundary (space/hyphen/slash/etc)."""
    return [t for t in re.split(r"[^A-Z0-9]+", str(text or "").upper()) if t]


def is_suppressed(raw_model) -> bool:
    """Blanket non-BEV signal — overrides every match rule, even an approved-family match."""
    upper = str(raw_model or "").upper()
    if set(tokenize(raw_model)) & SUPPRESS_TOKENS:
        return True
    return any(sub in upper for sub in SUPPRESS_SUBSTRINGS)


def has_name_marker(raw_model) -> bool:
    """Whole-token EV/BEV/ELECTRIC only — 'EV' must not match inside e.g. 'REVO' or 'REEV'."""
    return bool(set(tokenize(raw_model)) & NAME_MARKER_TOKENS)


def _strip_brand_prefix(tokens: list, brand_tokens: list) -> list:
    if brand_tokens and tokens[: len(brand_tokens)] == brand_tokens:
        return tokens[len(brand_tokens):]
    return tokens


def closely_matches_raw_model(brand_tokens: list, pending_tokens: list, approved_tokens: list) -> bool:
    """True if the model *designation* — raw model tokens with the shared brand prefix
    stripped off — shares its first token with an approved BEV raw model.

    Comparing designation tokens (not the full raw-model string) matters for multi-word
    brands: 'GREAT WALL POER' vs 'GREAT WALL ORA GOOD CAT' share the 'GREAT WALL' prefix
    but are different model families, so brand tokens must be stripped before comparing —
    otherwise every model under a brand with an approved BEV would look like a raw-model
    match, degenerating into brand-only inference.
    """
    p = _strip_brand_prefix(pending_tokens, brand_tokens)
    a = _strip_brand_prefix(approved_tokens, brand_tokens)
    return bool(p) and bool(a) and p[0] == a[0]


def classify(brand2, raw_model, model2, *, approved_family_keys, approved_raw_by_brand):
    """Return (reason_code, detail) for the first matching rule (priority order), else None.

    approved_family_keys: set of (normalize(brand2), normalize(model2)) for approved BEV rows.
    approved_raw_by_brand: dict {normalize(brand2): [(raw_model_display, tokens), ...]} for
      approved BEV rows, used only for the raw-model closeness rule.
    detail carries the matched model2 / approved raw_model for the human-readable reason text.
    """
    if is_suppressed(raw_model):
        return None

    if (normalize(brand2), normalize(model2)) in approved_family_keys:
        return "approved_family_match", model2

    brand_tokens = tokenize(brand2)
    pending_tokens = tokenize(raw_model)
    for approved_raw, approved_tokens in approved_raw_by_brand.get(normalize(brand2), []):
        if closely_matches_raw_model(brand_tokens, pending_tokens, approved_tokens):
            return "approved_model_match", approved_raw

    if has_name_marker(raw_model):
        return "electric_name_marker", None

    return None
