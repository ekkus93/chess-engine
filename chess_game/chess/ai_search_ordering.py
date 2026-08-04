"""Move-ordering glue for the AI search.

Extracted from ``ai.py``. Combines the shared capture/promotion/quiet ordering
helpers with TT-move, killer-move and last-best-move bonuses into the move sort
used by both the main search and quiescence. Imports only lower-level modules, so
it never depends back on ``ai.py``.
"""

from __future__ import annotations

from chess_game.chess.ai_board_utils import clone_with_move as _make_copy_with_move
from chess_game.chess.ai_capture_ordering import (
    capture_order_score as _shared_capture_order_score,
)
from chess_game.chess.ai_move_ordering import (
    make_quiet_order_context,
    quiet_strategy_order_score,
)
from chess_game.chess.ai_search_helpers import (
    promotion_order_score as _promotion_order_score,
)
from chess_game.chess.ai_search_helpers import (
    same_legal_move as _same_legal_move,
)
from chess_game.chess.ai_search_types import MinimaxParams, SearchContext
from chess_game.chess.ai_transposition import position_key
from chess_game.chess.board import Board
from chess_game.chess.move import Move
from chess_game.chess.strategy_utils import is_capture_move as _is_capture_move
from chess_game.chess.types import LegalMove


def _move_sort_key(move: Move | LegalMove) -> tuple[int, int, str]:
    """Stable tie-break key for deterministic equal-score move selection.

    Returns only primitive comparable values (int, int, str) to avoid
    comparison errors with ConstantSquare objects.
    """
    start_idx = int(move.start.row) * 8 + int(move.start.col)
    end_idx = int(move.end.row) * 8 + int(move.end.col)
    promo_str = move.promotion.name if move.promotion else ""
    return (start_idx, end_idx, promo_str)


def _order_moves(
    board: Board,
    legal_moves: list[Move],
    params: MinimaxParams | None = None,
) -> list[Move]:
    """Sort moves for better pruning order."""

    quiet_order_context = make_quiet_order_context(board)
    scored_moves = [
        (_move_order_score(board, move, params, quiet_order_context), move)
        for move in legal_moves
    ]
    scored_moves.sort(key=lambda item: item[0], reverse=True)
    return [move for _, move in scored_moves]


def _move_order_score(
    board: Board,
    move: Move,
    params: MinimaxParams | None,
    quiet_order_context=None,
) -> int:
    """Return a move-ordering score.

    Placement audit:
    - quiet strategic heuristics live in `ai_move_ordering.py`
    - tactical capture ordering lives in this module
    - root-only tie-breaks stay in `root_stability_adjustment()`
    - selective extensions stay in `selective_extension_bonus()`
    """

    score = (
        _capture_order_score(board, move)
        + _promotion_order_score(move)
    )
    if not _is_capture_move(board, move) and move.promotion is None:
        score += quiet_strategy_order_score(board, move, quiet_order_context)
    context = None if params is None else params.context
    if context is None:
        return score
    move_key = (move.start, move.end, move.promotion)
    if context.killer_moves is not None and move_key in context.killer_moves:
        score += 1_500
    if context.last_best_move is not None and _same_legal_move(move, context.last_best_move):
        score += 2_000
    tt_best_move = _tt_best_move(board, context)
    if tt_best_move is not None and _same_legal_move(move, tt_best_move):
        score += 3_000
    return score


def _capture_order_score(board: Board, move: Move) -> int:
    """Return capture ordering score using the shared capture-order helper."""
    return _shared_capture_order_score(board, move, _make_copy_with_move)


def _tt_best_move(board: Board, context: SearchContext) -> LegalMove | None:
    """Return the TT move for the current board if one exists."""
    if context.transposition_table is None:
        return None
    entry = context.transposition_table.get(position_key(board))
    return None if entry is None else entry.best_move
