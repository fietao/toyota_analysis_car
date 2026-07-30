"""test_bev_candidate_rules.py — pure matching-rule tests for the New BEV Model Watchlist.

Stdlib only (bev_candidate_rules.py has no pandas dependency) — matches the existing
test_*.py convention. Exits 0 on PASS, 1 on FAIL.
"""
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

BACKEND = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BACKEND))

import bev_candidate_rules as rules

failures = []


def _check(label, cond, detail=""):
    if not cond:
        failures.append(f"{label}: {detail}")


# ---- 1. approved-family matching -------------------------------------------------
def test_approved_family_match():
    family_keys = {(rules.normalize("BYD"), rules.normalize("ATTO 3"))}
    result = rules.classify(
        "BYD", "BYD ATTO 3 EXTENDED RANGE", "ATTO 3",
        approved_family_keys=family_keys, approved_raw_by_brand={},
    )
    _check("approved_family_match", result == ("approved_family_match", "ATTO 3"), result)


# ---- 2. approved raw-model matching ------------------------------------------------
def test_approved_raw_model_match():
    approved_raw_by_brand = {rules.normalize("AVATR"): [("AVATR 07 MAX", rules.tokenize("AVATR 07 MAX"))]}
    result = rules.classify(
        "AVATR", "AVATR 07 ULTRA AWD", "AVATR 07",
        approved_family_keys=set(), approved_raw_by_brand=approved_raw_by_brand,
    )
    _check("approved_raw_model_match", result == ("approved_model_match", "AVATR 07 MAX"), result)


def test_approved_raw_model_no_match_different_model_number():
    """Same brand, different model number after the brand prefix -> no match."""
    approved_raw_by_brand = {rules.normalize("AVATR"): [("AVATR 07 MAX", rules.tokenize("AVATR 07 MAX"))]}
    result = rules.classify(
        "AVATR", "AVATR 11 PRO", "AVATR 11",
        approved_family_keys=set(), approved_raw_by_brand=approved_raw_by_brand,
    )
    _check("approved_raw_model_no_match", result is None, result)


# ---- 3. whole-token EV/BEV/ELECTRIC matching --------------------------------------
def test_whole_token_ev_marker():
    for raw in ("MODEL EV", "SOME CAR BEV", "SOME CAR ELECTRIC", "EV"):
        result = rules.classify(
            "ANYBRAND", raw, "SOME MODEL", approved_family_keys=set(), approved_raw_by_brand={},
        )
        _check(f"whole_token_marker[{raw}]", result == ("electric_name_marker", None), result)


# ---- 4. EV substring false positives ----------------------------------------------
def test_ev_substring_is_not_a_marker():
    for raw in ("REVO", "REVOLUTION", "SEVEN", "PREVIA"):
        _check(f"ev_substring_false_positive[{raw}]", not rules.has_name_marker(raw), raw)
        result = rules.classify(
            "ANYBRAND", raw, "SOME MODEL", approved_family_keys=set(), approved_raw_by_brand={},
        )
        _check(f"ev_substring_no_candidate[{raw}]", result is None, result)


# ---- 5. PHEV/HEV/HYBRID/DM-i/REEV/EREV suppression --------------------------------
def test_suppression_blocks_all_rules():
    family_keys = {(rules.normalize("BYD"), rules.normalize("ATTO 3"))}
    approved_raw_by_brand = {rules.normalize("BYD"): [("BYD ATTO 3", rules.tokenize("BYD ATTO 3"))]}
    suppressed_raw_models = [
        "BYD ATTO 3 PHEV", "BYD ATTO 3 HEV", "BYD SEAL HYBRID", "BYD SEAL DM-i",
        "BYD SEAL DM-I", "BYD SEAL DIESEL", "BYD SEAL PETROL", "BYD SEAL GASOLINE",
        "NISSAN KICKS e-POWER", "MG EREV RANGE EXTENDER", "DEEPAL S07 REEV", "DEEPAL S07 EREV",
    ]
    for raw in suppressed_raw_models:
        _check(f"is_suppressed[{raw}]", rules.is_suppressed(raw), raw)
        result = rules.classify(
            "BYD", raw, "ATTO 3", approved_family_keys=family_keys, approved_raw_by_brand=approved_raw_by_brand,
        )
        _check(f"suppressed_no_candidate[{raw}]", result is None, result)


def test_ev_marker_alone_is_not_suppressed():
    # sanity: a genuinely electric-marked model must NOT be caught by suppression.
    _check("ev_marker_not_suppressed", not rules.is_suppressed("MODEL EV"))


# ---- 6. no brand-only inference (multi-word brand) --------------------------------
def test_no_brand_only_inference_multiword_brand():
    """Approved family is a BEV under a two-word brand; a different, unrelated model
    under the SAME brand with no marker/suppression/raw-model closeness must not be
    flagged. Brand alone must never be sufficient."""
    family_keys = {(rules.normalize("GREAT WALL"), rules.normalize("ORA GOOD CAT"))}
    approved_raw_by_brand = {
        rules.normalize("GREAT WALL"): [("GREAT WALL ORA GOOD CAT", rules.tokenize("GREAT WALL ORA GOOD CAT"))]
    }
    result = rules.classify(
        "GREAT WALL", "GREAT WALL POER", "POER",
        approved_family_keys=family_keys, approved_raw_by_brand=approved_raw_by_brand,
    )
    _check("no_brand_only_inference", result is None, result)


def test_closely_matches_strips_shared_brand_prefix():
    """Directly exercise the token-comparison helper: a shared multi-word brand prefix
    must not itself count as a match once stripped."""
    brand_tokens = rules.tokenize("GREAT WALL")
    pending = rules.tokenize("GREAT WALL POER")
    approved = rules.tokenize("GREAT WALL ORA GOOD CAT")
    _check(
        "closely_matches_strips_brand_prefix",
        rules.closely_matches_raw_model(brand_tokens, pending, approved) is False,
    )


# ---- reason priority (used for sorting) -------------------------------------------
def test_reason_priority_order():
    _check(
        "reason_priority_order",
        rules.REASON_PRIORITY["approved_family_match"] < rules.REASON_PRIORITY["approved_model_match"]
        < rules.REASON_PRIORITY["electric_name_marker"],
    )


if __name__ == "__main__":
    test_approved_family_match()
    test_approved_raw_model_match()
    test_approved_raw_model_no_match_different_model_number()
    test_whole_token_ev_marker()
    test_ev_substring_is_not_a_marker()
    test_suppression_blocks_all_rules()
    test_ev_marker_alone_is_not_suppressed()
    test_no_brand_only_inference_multiword_brand()
    test_closely_matches_strips_shared_brand_prefix()
    test_reason_priority_order()
    if failures:
        print(f"FAIL — {len(failures)} issue(s) in bev-candidate-rules tests:")
        for f in failures:
            print(f)
        sys.exit(1)
    print("PASS — All bev-candidate-rules tests passed successfully.")
