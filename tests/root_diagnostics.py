"""Root-candidate diagnostics for engine-strength triage (test-only, FIX9).

Reports, for each legal root move, the depth-N search score, the root tie-break
value, the static evaluation after the move, and the quiescence score after the
move, so a failing "search should prefer move X" regression can be explained.

White-relative convention throughout: positive favors White. White to move picks
the maximum score; Black to move picks the minimum.
"""
from __future__ import annotations

from dataclasses import dataclass

from chess_game.chess.ai import (
    INF,
    MinimaxParams,
    SearchContext,
    _evaluate_child_move,
    get_legal_moves,
    position_key,
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
    tiebreak: int       # root_stability_adjustment tie-break value
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

    Uses the engine's own ``_evaluate_child_move`` at root-configured params so
    per-move scores include the same leaf/check extensions the real search
    applies (a naive per-move minimax does not match the engine). Each move gets
    a fresh full window, so the scores are exact rather than alpha-beta bounds.

    deterministic=True removes random tie-breaking so the ranking is stable.
    """
    context = SearchContext(weights=None, deterministic=deterministic)
    white_to_move = board.turn == Color.WHITE
    root_params = MinimaxParams(
        depth=depth,
        alpha=-INF,
        beta=INF,
        is_maximizing=white_to_move,
        context=context,
        line_history=(position_key(board),),
    )
    candidates: list[RootCandidate] = []

    for move in get_legal_moves(board):
        child_score, root_tiebreak = _evaluate_child_move(
            board, move, root_params, -INF, INF
        )
        child = clone_with_move(board, move)
        child_is_max = child.turn == Color.WHITE
        candidates.append(
            RootCandidate(
                move=f"{_alg(move.start)}{_alg(move.end)}",
                score=int(child_score),
                tiebreak=int(root_tiebreak),
                static_after=int(evaluate(child)),
                qsearch_after=int(
                    quiescence(child, -INF, INF, child_is_max, context=context)
                ),
                selected=False,
            )
        )

    if candidates:
        best = (
            max(candidates, key=lambda c: (c.score, c.tiebreak))
            if white_to_move
            else min(candidates, key=lambda c: (c.score, -c.tiebreak))
        )
        best.selected = True

    candidates.sort(key=lambda c: (c.score, c.tiebreak), reverse=white_to_move)
    return candidates[:top_n]


def format_candidates(candidates: list[RootCandidate]) -> str:
    """Render candidates as an aligned table for quick reading."""
    lines = [
        f"{'move':6} {'score':>9} {'tiebrk':>7} {'static':>8} {'qsearch':>8}  sel"
    ]
    for cand in candidates:
        marker = "*" if cand.selected else ""
        lines.append(
            f"{cand.move:6} {cand.score:>9} {cand.tiebreak:>7} "
            f"{cand.static_after:>8} {cand.qsearch_after:>8}  {marker}"
        )
    return "\n".join(lines)
