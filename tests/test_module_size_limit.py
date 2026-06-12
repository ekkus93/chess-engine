"""Guard against source modules growing back into unmaintainable hubs.

Several files (ai.py, ai_search_helpers.py, ai_move_ordering.py, evaluation.py,
conversion_guidance.py, ...) had grown to 800-1300 lines and were split into
one-concern modules (2026-06). This test fails if any module creeps back over the
ceiling, so file bloat is caught here (and by the matching pylint ``max-module-lines``
gate) rather than during review.

When this fails: split the offending module into a helper / constants / types
submodule (keep the original as a thin facade that re-exports). Do NOT just raise the
limit.
"""

from pathlib import Path

# Keep source modules at one-concern size. Mirrors pyproject's pylint
# [tool.pylint.format] max-module-lines.
MAX_MODULE_LINES = 800

_PACKAGE_ROOT = Path(__file__).resolve().parent.parent / "chess_game"


def _line_count(path: Path) -> int:
    with path.open("rb") as handle:
        return sum(1 for _ in handle)


def test_no_source_module_exceeds_line_limit() -> None:
    """Every chess_game/*.py module must stay at or under MAX_MODULE_LINES."""
    offenders = []
    for path in sorted(_PACKAGE_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        lines = _line_count(path)
        if lines > MAX_MODULE_LINES:
            offenders.append(f"  {path.relative_to(_PACKAGE_ROOT.parent)}: {lines} lines")
    assert not offenders, (
        f"These modules exceed {MAX_MODULE_LINES} lines — split each into a "
        f"helper/constants/types module (keep the original as a thin re-export "
        f"facade) instead of raising the limit:\n" + "\n".join(offenders)
    )
