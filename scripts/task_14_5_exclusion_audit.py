#!/usr/bin/env python3
"""Enforce the Rust search-ordering exclusions defined by Task 14.5."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEARCH_SOURCE = ROOT / "crates/chess-search/src"
MOVE_ORDERING = SEARCH_SOURCE / "move_ordering.rs"
ALPHA_BETA = SEARCH_SOURCE / "alpha_beta.rs"
SEARCH_EQUIVALENCE = ROOT / "crates/chess-search/tests/search_equivalence.rs"


class AuditFailure(RuntimeError):
    """Raised when a Task 14.5 exclusion is no longer enforceable."""


def read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except OSError as error:
        raise AuditFailure(f"cannot read {path.relative_to(ROOT)}: {error}") from error


def production_prefix(path: Path) -> str:
    """Return Rust source before the first cfg(test) module.

    Test-only helper functions may be interleaved with production items. Stopping at
    the first cfg(test) attribute would therefore hide later production code. The
    module boundary is the stable point after which the file contains only tests.
    """
    source = read(path)
    test_module = re.search(
        r"^#\[cfg\(test\)\]\s*\n\s*mod\s+[A-Za-z_][A-Za-z0-9_]*\s*\{",
        source,
        flags=re.MULTILINE,
    )
    return source[: test_module.start()] if test_module is not None else source


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AuditFailure(message)


def require_regex(text: str, pattern: str, message: str) -> None:
    require(re.search(pattern, text, flags=re.MULTILINE | re.DOTALL) is not None, message)


def audit_forbidden_scenario_identifiers() -> int:
    patterns = {
        "transcript/review-loop ordering": (
            r"\btranscript_(?:score|bonus|penalty|ordering|guidance)\b",
            r"\breview_(?:loop|score|bonus|penalty|order|ordering|guidance)\b",
        ),
        "anti-drift scenario scoring": (
            r"\banti_drift\b",
            r"\bdrift_(?:score|bonus|penalty|scenario|ordering)\b",
            r"\bscenario_(?:score|bonus|penalty|ordering|guidance)\b",
        ),
    }
    files = sorted(SEARCH_SOURCE.glob("*.rs"))
    require(files, "no chess-search production Rust files were found")

    for path in files:
        source = production_prefix(path)
        for exclusion, exclusion_patterns in patterns.items():
            for pattern in exclusion_patterns:
                match = re.search(pattern, source, flags=re.IGNORECASE)
                require(
                    match is None,
                    f"{path.relative_to(ROOT)} contains forbidden {exclusion} identifier: "
                    f"{match.group(0) if match else pattern}",
                )
    return len(files)


def audit_move_ordering_boundary() -> tuple[list[str], list[str]]:
    source = production_prefix(MOVE_ORDERING)

    key_match = re.search(
        r"struct\s+MoveOrderKey\s*\{(?P<body>.*?)^\}",
        source,
        flags=re.MULTILINE | re.DOTALL,
    )
    require(key_match is not None, "MoveOrderKey definition was not found")
    fields = re.findall(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s*:", key_match.group("body"), re.MULTILINE)
    expected_fields = [
        "transposition_table",
        "previous_principal_variation",
        "category",
        "promotion",
        "see_class",
        "see_value",
        "victim",
        "attacker_preference",
        "killer",
        "history",
        "encoded_tie_break",
    ]
    require(
        fields == expected_fields,
        "MoveOrderKey escaped the bounded ordering contract: "
        f"expected {expected_fields}, found {fields}",
    )

    position_methods = sorted(
        set(re.findall(r"\bposition\s*\.\s*([A-Za-z_][A-Za-z0-9_]*)\s*\(", source))
    )
    allowed_position_methods = {"piece_at", "side_to_move"}
    unexpected_methods = sorted(set(position_methods) - allowed_position_methods)
    require(
        not unexpected_methods,
        "move ordering reads strategic position state through unexpected methods: "
        + ", ".join(unexpected_methods),
    )

    forbidden_evaluator_identifiers = {
        "evaluate",
        "evaluation",
        "evaluation_trace",
        "weights",
        "phase",
        "mobility",
        "pawn_structure",
        "passed_pawn",
        "isolated_pawn",
        "doubled_pawn",
        "bishop_pair",
        "rook_activity",
        "king_safety",
        "king_activity",
        "piece_square",
        "space_bonus",
        "tempo_bonus",
    }
    identifiers = {identifier.lower() for identifier in re.findall(r"\b[A-Za-z_][A-Za-z0-9_]*\b", source)}
    duplicated = sorted(forbidden_evaluator_identifiers & identifiers)
    require(
        not duplicated,
        "move ordering duplicates or imports strategic evaluation identifiers: "
        + ", ".join(duplicated),
    )

    require_regex(
        source,
        r"const\s+fn\s+piece_value\s*\([^)]*PieceKind[^)]*\)\s*->\s*u16",
        "the bounded local tactical piece-value table is missing",
    )
    require_regex(
        source,
        r"history:\s*if\s+quiet\s*\{\s*history\s*\}\s*else\s*\{\s*0\s*\}",
        "history must remain a quiet-move ordering term only",
    )
    return fields, position_methods


def audit_exact_root_score_dominance() -> list[str]:
    source = production_prefix(ALPHA_BETA)
    require_regex(
        source,
        r"let\s+alpha\s*=\s*Score::mated_in\(0\)",
        "root alpha no longer starts at the complete supported lower bound",
    )
    require_regex(
        source,
        r"let\s+beta\s*=\s*Score::mate_in\(0\)",
        "root beta no longer starts at the complete supported upper bound",
    )
    require_regex(
        source,
        r"Some\s*\(\s*previous\s*\)\s*=>\s*score\s*>\s*previous",
        "best-move replacement is not governed by a strictly better searched score",
    )
    require(
        re.search(r"score\s*>=\s*previous", source) is None,
        "equal searched scores must not replace the deterministic first best move",
    )
    require_regex(
        source,
        r"if\s+replace_best\s*\{\s*best_score\s*=\s*Some\(score\);\s*best_move\s*=\s*Some\(current\);\s*\}",
        "best score and best move are no longer updated atomically from the searched score",
    )
    require("MoveOrderKey" not in source and ".key" not in source, "alpha-beta result selection depends on an ordering key")

    witness_sources = "\n".join(
        [
            read(ALPHA_BETA),
            read(SEARCH_SOURCE / "quiescence.rs"),
            read(SEARCH_EQUIVALENCE),
        ]
    )
    witnesses = [
        "quiet_ordering_preserves_full_window_result_deterministically",
        "seeded_quiet_cutoff_reduces_a_fixed_narrow_window_tree",
        "tactical_ordering_reduces_a_fixed_cutoff_tree_without_changing_the_result",
        "uniquely_best_tactical_move_matches_the_independent_root_score_oracle",
    ]
    missing = [name for name in witnesses if name not in witness_sources]
    require(not missing, "required exact-score or node-reduction witnesses are missing: " + ", ".join(missing))
    return witnesses


def main() -> int:
    try:
        scanned = audit_forbidden_scenario_identifiers()
        fields, position_methods = audit_move_ordering_boundary()
        witnesses = audit_exact_root_score_dominance()
    except AuditFailure as error:
        print(f"Task 14.5 exclusion audit failed: {error}", file=sys.stderr)
        return 1

    print("Task 14.5 exclusion audit passed")
    print(f"production Rust files scanned: {scanned}")
    print("MoveOrderKey fields: " + ", ".join(fields))
    print("ordering Position queries: " + ", ".join(position_methods))
    print("exact-score/node-reduction witnesses: " + ", ".join(witnesses))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())