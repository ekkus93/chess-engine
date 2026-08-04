#!/usr/bin/env python3
"""Fail-closed source audit for Task 24 performance architecture contracts."""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEARCH_ROOT = ROOT / "crates" / "chess-search" / "src"
RECURSIVE_FILES = (
    SEARCH_ROOT / "alpha_beta.rs",
    SEARCH_ROOT / "quiescence.rs",
    SEARCH_ROOT / "reference.rs",
    SEARCH_ROOT / "iterative_deepening.rs",
)


def production_prefix(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    marker = "#[cfg(test)]"
    return text.split(marker, 1)[0]


def fail(message: str) -> None:
    print(f"Task 24 performance audit failed: {message}", file=sys.stderr)
    raise SystemExit(1)


def main() -> None:
    for path in RECURSIVE_FILES:
        production = production_prefix(path)
        if re.search(r"\bposition\s*\.\s*clone\s*\(", production):
            fail(f"recursive search clones Position in {path.relative_to(ROOT)}")
        if re.search(r"\bto_fen\s*\(", production):
            fail(f"recursive search constructs a FEN/string position key in {path.relative_to(ROOT)}")
        if re.search(r"(?:HashMap|BTreeMap)\s*<\s*String\b", production):
            fail(f"recursive search uses String-keyed storage in {path.relative_to(ROOT)}")

    evaluation = production_prefix(SEARCH_ROOT / "evaluation.rs")
    match = re.search(
        r"pub fn evaluate_with_weights\([^)]*\)[^{]*\{(?P<body>.*?)\n\}",
        evaluation,
        flags=re.DOTALL,
    )
    if match is None:
        fail("could not locate evaluate_with_weights")
    body = match.group("body")
    forbidden = ("evaluate_trace", "Vec<", "Vec::", "String", "Box::", "format!(")
    for token in forbidden:
        if token in body:
            fail(f"normal evaluation contains allocation/trace token {token!r}")

    print("Task 24 performance source audit passed.")
    print("- recursive search has no Position clone")
    print("- recursive search has no FEN/String position key")
    print("- normal evaluation does not call tracing or allocation constructors")


if __name__ == "__main__":
    main()
