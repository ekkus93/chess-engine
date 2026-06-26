"""Quiescence search driver for the AI.

Extracted from ``ai.py``. Quiescence extends tactical leaf nodes through captures,
promotions and check evasions so the static evaluation is only applied to
relatively quiet positions. It is a call-graph leaf of the main search (it never
calls ``minimax``), and now imports only the lower-level extracted modules, so it
does not depend back on ``ai.py``. ``ai.py`` re-exports ``quiescence`` and calls
``_quiescence`` from ``minimax``.
"""

from __future__ import annotations

from typing import Optional

from chess_game.chess.ai_board_utils import (
    clone_with_move as _make_copy_with_move,
    get_legal_moves,
)
from chess_game.chess.ai_quiescence_helpers import (
    select_quiescence_moves as _select_quiescence_moves,
)
from chess_game.chess.ai_search_eval import (
    _ctx_evaluate,
    _terminal_score,
    make_repetition_policy,
)
from chess_game.chess.ai_search_helpers import (
    repetition_score as _repetition_score,
)
from chess_game.chess.ai_search_ordering import _capture_order_score, _order_moves
from chess_game.chess.ai_search_types import (
    INF,
    MATE_SCORE,
    MAX_QUIESCENCE_DEPTH,
    MAX_QUIESCENCE_MOVES,
    MinimaxParams,
    QuiescenceParams,
    SearchContext,
)
from chess_game.chess.ai_transposition import position_key
from chess_game.chess.board import Board
from chess_game.chess.board.game_state import is_in_check as _gs_is_in_check
from chess_game.chess.move import Move
from chess_game.chess.types import Color


def _record_quiescence_node(context: Optional[SearchContext]) -> None:
    """Increment quiescence counters when diagnostics are enabled."""

    if context is not None and context.stats is not None:
        context.stats.quiescence_nodes += 1


def _record_tactical_width(context: Optional[SearchContext], width: int) -> None:
    """Record tactical branching diagnostics."""

    if context is None or context.stats is None:
        return
    context.stats.tactical_positions += 1
    context.stats.tactical_move_sum += width
    context.stats.tactical_max_width = max(context.stats.tactical_max_width, width)


def _stand_pat_bounds(
    stand_pat: int,
    alpha: int,
    beta: int,
    is_maximizing: bool,
) -> tuple[int, int, int]:
    """Seed quiescence bounds from the stand-pat evaluation."""

    if is_maximizing:
        return stand_pat, max(alpha, stand_pat), beta
    return stand_pat, alpha, min(beta, stand_pat)


def _is_quiescence_cutoff(
    stand_pat: int,
    alpha: int,
    beta: int,
    is_maximizing: bool,
) -> bool:
    """Return True when quiescence can terminate before exploring captures."""

    if is_maximizing:
        return stand_pat >= beta
    return stand_pat <= alpha


def _quiescence_evasion_search(
    board: Board,
    params: QuiescenceParams,
    ply: int,
    legal_moves: list[Move],
) -> int:
    """Search all legal evasions when the side to move is in check."""
    if not legal_moves:
        return -MATE_SCORE + ply if board.turn == Color.WHITE else MATE_SCORE - ply
    alpha = params.alpha
    beta = params.beta
    context = params.context
    best_score = -INF if params.is_maximizing else INF
    order_params = MinimaxParams(
        depth=0,
        alpha=alpha,
        beta=beta,
        is_maximizing=params.is_maximizing,
        context=context,
    )
    for move in _order_moves(board, legal_moves, order_params):
        child_board = _make_copy_with_move(board, move)
        child_score = _quiescence(
            child_board,
            QuiescenceParams(
                alpha=alpha,
                beta=beta,
                is_maximizing=not params.is_maximizing,
                context=context,
                depth_remaining=params.depth_remaining - 1,
                line_history=params.line_history + (position_key(child_board),),
            ),
        )
        if params.is_maximizing:
            best_score = max(best_score, child_score)
            alpha = max(alpha, best_score)
        else:
            best_score = min(best_score, child_score)
            beta = min(beta, best_score)
        if alpha >= beta:
            break
    return best_score


def _quiescence(board: Board, params: QuiescenceParams) -> int:
    """Internal quiescence implementation with bounded recursion."""

    alpha = params.alpha
    beta = params.beta
    context = params.context
    ply = len(params.line_history)
    _record_quiescence_node(context)
    repetition_score = _repetition_score(
        board,
        context,
        params.line_history,
        make_repetition_policy(context),
    )
    if repetition_score is not None:
        return repetition_score

    # Get legal moves once for reuse
    legal_moves = (
        list(params.legal_moves) if params.legal_moves is not None
        else get_legal_moves(board)
    )

    # Check for terminal/draw states early
    terminal_score = _terminal_score(
        board, legal_moves, ply, context.position_counts if context else None
    )
    if terminal_score is not None:
        return terminal_score

    # Check-evasion path: no stand-pat when in check — search all legal evasions
    if _gs_is_in_check(board, board.turn):
        return _quiescence_evasion_search(board, params, ply, legal_moves)

    # Normal stand-pat path — not in check
    stand_pat = _ctx_evaluate(board, context)
    best_score, alpha, beta = _stand_pat_bounds(
        stand_pat,
        alpha,
        beta,
        params.is_maximizing,
    )
    cutoff = _is_quiescence_cutoff(stand_pat, alpha, beta, params.is_maximizing)
    if cutoff or params.depth_remaining <= 0:
        return stand_pat

    tactical_moves = _select_quiescence_moves(
        board,
        legal_moves,
        _capture_order_score,
        MAX_QUIESCENCE_MOVES,
    )
    if not tactical_moves:
        return stand_pat
    _record_tactical_width(context, len(tactical_moves))

    move_order_params = MinimaxParams(
        depth=0,
        alpha=alpha,
        beta=beta,
        is_maximizing=params.is_maximizing,
        context=context,
    )
    for move in _order_moves(board, tactical_moves, move_order_params):
        child_board = _make_copy_with_move(board, move)
        child_score = _quiescence(
            child_board,
            QuiescenceParams(
                alpha=alpha,
                beta=beta,
                is_maximizing=not params.is_maximizing,
                context=context,
                depth_remaining=params.depth_remaining - 1,
                line_history=params.line_history + (position_key(child_board),),
            ),
        )
        if params.is_maximizing:
            best_score = max(best_score, child_score)
            alpha = max(alpha, best_score)
        else:
            best_score = min(best_score, child_score)
            beta = min(beta, best_score)
        if alpha >= beta:
            break
    return best_score


def quiescence(
    board: Board,
    alpha: int,
    beta: int,
    is_maximizing: bool,
    *,
    context: Optional[SearchContext] = None,
    depth_remaining: int = MAX_QUIESCENCE_DEPTH,
) -> int:
    """Extend tactical leaf nodes through captures and promotions."""

    return _quiescence(
        board,
        QuiescenceParams(
            alpha=alpha,
            beta=beta,
            is_maximizing=is_maximizing,
            context=context,
            depth_remaining=depth_remaining,
        ),
    )
