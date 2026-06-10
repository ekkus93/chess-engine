"""Root-candidate diagnostics for engine-strength triage (test-only, FIX9).

Reports, for each legal root move, the depth-N search score, the static
evaluation after the move, and the quiescence score after the move, so a failing
"search should prefer move X" regression can be explained (why does the engine
score the actual move higher than the expected move?).

White-relative convention throughout: positive favors White. White to move picks
the maximum score; Black to move picks the minimum.
"""
from __future__ import annotations

from dataclasses import dataclass

from chess_game.chess.ai import (
    INF,
    MinimaxParams,
    SearchContext,
    get_legal_moves,
    minimax,
    quiescence,
)
from chess_game.chess.ai_board_utils import clone_with_move
from chess_game.chess.board.board import Board
from chess_game.chess.coords import index_to_algebraic as _alg
from chess_game.chess.evaluation import evaluate
from chess_game.chess.types import Color


@dataclass
class RootCandidate:
    """Diagnostic record for one legal root move."""

    move: str
    score: int          # White-relative depth-N search score after the move
    static_after: int   # White-relative static eval of the resulting position
    qsearch_after: int  # White-relative quiescence score after the move
    selected: bool      # True for the move the diagnostic ranks best


def debug_root_candidates(
    board: Board,
    *,
    depth: int,
    top_n: int = 10,
    deterministic: bool = True,
) -> list[RootCandidate]:
    """Return the top root candidates ranked by White-relative search score.

    deterministic=True removes random tie-breaking so the ranking is stable.
    """
    context = SearchContext(weights=None, deterministic=deterministic)
    white_to_move = board.turn == Color.WHITE
    candidates: list[RootCandidate] = []

    for move in get_legal_moves(board):
        child = clone_with_move(board, move)
        child_is_max = child.turn == Color.WHITE
        score, _ = minimax(
            child,
            MinimaxParams(
                depth=max(0, depth - 1),
                alpha=-INF,
                beta=INF,
                is_maximizing=child_is_max,
                context=context,
            ),
        )
        candidates.append(
            RootCandidate(
                move=f"{_alg(move.start)}{_alg(move.end)}",
                score=int(score),
                static_after=int(evaluate(child)),
                qsearch_after=int(
                    quiescence(child, -INF, INF, child_is_max, context=context)
                ),
                selected=False,
            )
        )

    if candidates:
        best = (
            max(candidates, key=lambda c: c.score)
            if white_to_move
            else min(candidates, key=lambda c: c.score)
        )
        best.selected = True

    candidates.sort(key=lambda c: c.score, reverse=white_to_move)
    return candidates[:top_n]


def format_candidates(candidates: list[RootCandidate]) -> str:
    """Render candidates as an aligned table for quick reading."""
    lines = [f"{'move':6} {'score':>9} {'static':>8} {'qsearch':>8}  sel"]
    for cand in candidates:
        marker = "*" if cand.selected else ""
        lines.append(
            f"{cand.move:6} {cand.score:>9} {cand.static_after:>8} "
            f"{cand.qsearch_after:>8}  {marker}"
        )
    return "\n".join(lines)
