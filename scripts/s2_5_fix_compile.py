#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def replace_exact(path: str, old: str, new: str, expected: int = 1) -> None:
    target = ROOT / path
    text = target.read_text()
    count = text.count(old)
    if count != expected:
        raise SystemExit(
            f"{path}: expected {expected} replacement(s), found {count}: {old[:140]!r}"
        )
    target.write_text(text.replace(old, new))


MOVE_ORDERING = "crates/chess-search/src/move_ordering.rs"
ALPHA_BETA = "crates/chess-search/src/alpha_beta.rs"

# These compatibility wrappers remain useful only to the in-module regression tests.
for signature in [
    "pub(crate) fn ordered_legal_moves_with_state(\n",
    "pub(crate) fn ordered_legal_moves_with_state_and_tt_move(\n",
    "fn order_legal_moves_with_hints(\n",
]:
    replace_exact(MOVE_ORDERING, signature, f"#[cfg(test)]\n{signature}")

# Refined priority hints are one explicit tuple.
replace_exact(
    MOVE_ORDERING,
    "            Some(tt_move),\n            None,\n            true,\n",
    "            (Some(tt_move), None),\n            true,\n",
)
replace_exact(
    MOVE_ORDERING,
    "            None,\n            None,\n            true,\n",
    "            (None, None),\n            true,\n",
)

# Legal-token generation currently takes a mutable position even though it restores state.
for old, new in [
    (
        "    fn see_candidate_preserves_tt_and_promotion_precedence() {\n        let root = position(\"3r3k/P7/8/8/8/8/8/K2Q4 w - - 0 1\");\n",
        "    fn see_candidate_preserves_tt_and_promotion_precedence() {\n        let mut root = position(\"3r3k/P7/8/8/8/8/8/K2Q4 w - - 0 1\");\n",
    ),
    (
        "    fn see_classes_and_signed_values_order_exactly() {\n        let root = position(\"4k3/8/2p5/3p4/4P3/8/8/4K3 w - - 0 1\");\n",
        "    fn see_classes_and_signed_values_order_exactly() {\n        let mut root = position(\"4k3/8/2p5/3p4/4P3/8/8/4K3 w - - 0 1\");\n",
    ),
    (
        "    fn see_is_computed_once_per_capture_and_classified() {\n        let root = position(\"7k/8/8/1p2q3/2P1Q3/8/K7/8 w - - 0 1\");\n",
        "    fn see_is_computed_once_per_capture_and_classified() {\n        let mut root = position(\"7k/8/8/1p2q3/2P1Q3/8/K7/8 w - - 0 1\");\n",
    ),
    (
        "    fn contradictory_internal_see_input_fails_loudly() {\n        let root = position(\"7k/8/8/1p2q3/2P1Q3/8/K7/8 w - - 0 1\");\n",
        "    fn contradictory_internal_see_input_fails_loudly() {\n        let mut root = position(\"7k/8/8/1p2q3/2P1Q3/8/K7/8 w - - 0 1\");\n",
    ),
    (
        "    fn quiet_ties_use_packed_move_order() {\n        let position = Position::starting();\n",
        "    fn quiet_ties_use_packed_move_order() {\n        let mut position = Position::starting();\n",
    ),
]:
    replace_exact(MOVE_ORDERING, old, new)

# Avoid imposing a Debug implementation on a fixed-capacity internal container solely for a test.
replace_exact(
    MOVE_ORDERING,
    "        let error = try_order_legal_moves_with_hints(\n"
    "            &contradictory,\n"
    "            &tokens,\n"
    "            MoveOrdering::Tactical,\n"
    "            0,\n"
    "            None,\n"
    "            (None, None),\n"
    "            true,\n"
    "        )\n"
    "        .expect_err(\"contradictory capture source must fail\");\n",
    "        let error = match try_order_legal_moves_with_hints(\n"
    "            &contradictory,\n"
    "            &tokens,\n"
    "            MoveOrdering::Tactical,\n"
    "            0,\n"
    "            None,\n"
    "            (None, None),\n"
    "            true,\n"
    "        ) {\n"
    "            Ok(_) => panic!(\"contradictory capture source must fail\"),\n"
    "            Err(error) => error,\n"
    "        };\n",
)

# Every test-only search context explicitly keeps the candidate inactive.
replace_exact(
    ALPHA_BETA,
    "            maximum_quiescence_ply: MAX_QUIESCENCE_PLY,\n            weights:",
    "            maximum_quiescence_ply: MAX_QUIESCENCE_PLY,\n"
    "            see_capture_ordering: false,\n"
    "            weights:",
    expected=3,
)

# First-party lint suppressions are forbidden for this task.
for path in [MOVE_ORDERING, ALPHA_BETA]:
    text = (ROOT / path).read_text()
    if "#[allow(" in text or "#[expect(" in text:
        raise SystemExit(f"{path}: first-party lint suppression detected")

print("S2-5 compile integration fixes applied")
