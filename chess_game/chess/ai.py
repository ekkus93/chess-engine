"""AI/Minimax implementation for chess engine."""

from __future__ import annotations

import random
import time

from chess_game.chess.ai_board_utils import (
    clone_with_move as _make_copy_with_move,
)
from chess_game.chess.ai_board_utils import (
    get_legal_moves,
)
from chess_game.chess.ai_quiescence_helpers import (
    _quiescence_capture_score as _quiescence_capture_score_impl,
)
from chess_game.chess.ai_quiescence_helpers import (
    _quiescence_check_score as _quiescence_check_score_impl,
)
from chess_game.chess.ai_quiescence_helpers import (
    _quiescence_structure_follow_up_score as _quiescence_structure_follow_up_score_impl,
)
from chess_game.chess.ai_quiescence_helpers import (
    _quiescence_tactical_score as _quiescence_tactical_score_impl,
)
from chess_game.chess.ai_quiescence_search import _quiescence, quiescence
from chess_game.chess.ai_search_eval import (
    _terminal_score,
    make_repetition_policy,
)
from chess_game.chess.ai_search_helpers import (
    check_extension as _check_extension,
)
from chess_game.chess.ai_search_helpers import (
    initial_root_window as _initial_root_window,
)
from chess_game.chess.ai_search_helpers import (
    prefer_root_move as _prefer_root_move,
)
from chess_game.chess.ai_search_helpers import (
    record_depth_timing as _record_depth_timing,
)
from chess_game.chess.ai_search_helpers import (
    record_root_research as _record_root_research,
)
from chess_game.chess.ai_search_helpers import (
    record_selective_extension as _record_selective_extension,
)
from chess_game.chess.ai_search_helpers import (
    repetition_score as _repetition_score,
)
from chess_game.chess.ai_search_helpers import (
    rerun_full_window_if_needed as _rerun_full_window_if_needed,
)
from chess_game.chess.ai_search_helpers import (
    root_stability_adjustment as _root_stability_adjustment,
)
from chess_game.chess.ai_search_helpers import (
    search_position_counts as _search_position_counts,
)
from chess_game.chess.ai_search_helpers import (
    selective_extension_bonus as _selective_extension_bonus,
)
from chess_game.chess.ai_search_helpers import (
    update_alpha_beta as _update_alpha_beta,
)
from chess_game.chess.ai_search_ordering import (
    _move_order_score,
    _move_sort_key,
    _order_moves,
)
from chess_game.chess.ai_search_types import (
    ASPIRATION_WINDOW,
    DRAW_SCORE,
    INF,
    MATE_SCORE,
    BestMoveOptions,
    MinimaxParams,
    QuiescenceParams,
    SearchContext,
    SearchStats,
    TTFlag,
)
from chess_game.chess.ai_transposition import (
    _check_tt_cache,
    _is_mate_score,
    _record_tt_hit,
    _store_tt_cache,
    position_key,
)
from chess_game.chess.ai_weight_cache import (
    get as _wc_get,
)
from chess_game.chess.ai_weight_cache import (
    invalidate_weights_cache as _invalidate_weights_cache,
)
from chess_game.chess.ai_weight_cache import (
    is_loaded as _wc_is_loaded,
)
from chess_game.chess.ai_weight_cache import (
    set_cache as _wc_set,
)
from chess_game.chess.board import Board
from chess_game.chess.eval_weights import EvalWeights
from chess_game.chess.evaluation import (
    evaluate,
)
from chess_game.chess.evaluation import (
    get_evaluation_breakdown as _get_evaluation_breakdown,
)
from chess_game.chess.move import Move
from chess_game.chess.opening_book import get_bundled_opening_book
from chess_game.chess.position_utils import position_key as _shared_position_key
from chess_game.chess.types import Color, LegalMove
from chess_game.texel.weights_io import (
    TUNED_WEIGHTS_PATH as _TUNED_WEIGHTS_PATH,
)
from chess_game.texel.weights_io import (
    load_weights_or_default as _load_weights_or_default,
)

get_evaluation_breakdown = _get_evaluation_breakdown
_quiescence_capture_score = _quiescence_capture_score_impl
_quiescence_check_score = _quiescence_check_score_impl
_quiescence_structure_follow_up_score = _quiescence_structure_follow_up_score_impl
_quiescence_tactical_score = _quiescence_tactical_score_impl

# Public search facade. ai.py re-exports names that moved into the extracted
# low-level modules (ai_search_types, ai_transposition, ai_search_eval); declaring
# them here marks the intentional re-exports for the linters and documents the
# surface that tests and tooling import from chess_game.chess.ai.
__all__ = [
    "DRAW_SCORE",
    "INF",
    "MATE_SCORE",
    "BestMoveOptions",
    "MinimaxParams",
    "SearchContext",
    "SearchStats",
    "TTFlag",
    "_evaluate_child_move",
    "_is_mate_score",
    "_move_order_score",
    "_quiescence_capture_score",
    "_quiescence_check_score",
    "_quiescence_tactical_score",
    "_root_stability_adjustment",
    "_store_tt_cache",
    "_terminal_score",
    "evaluate",
    "get_best_move",
    "get_evaluation_breakdown",
    "get_legal_moves",
    "invalidate_weights_cache",
    "minimax",
    "minimax_no_prune",
    "position_key",
    "quiescence",
    "search_root_depth",
]


def _get_effective_weights(weights: EvalWeights | None) -> EvalWeights:
    """Resolve the effective weights to use, loading from disk if needed."""
    if weights is not None:
        return weights
    if not _wc_is_loaded():
        _wc_set(_load_weights_or_default(_TUNED_WEIGHTS_PATH))
    return _wc_get() or EvalWeights.default()


def invalidate_weights_cache() -> None:
    """Force reload of tuned weights on the next get_best_move call.

    Call this after saving new tuned weights to disk so the AI immediately
    picks them up without restarting the process.
    """
    _invalidate_weights_cache()


def _record_search_node(context: SearchContext | None) -> None:
    """Increment node counters when diagnostics are enabled."""

    if context is None:
        return
    if context.nodes_searched is not None:
        context.nodes_searched[0] += 1
    if context.stats is not None:
        context.stats.nodes += 1


def minimax(
    board: Board,
    params: MinimaxParams,
) -> tuple[int, LegalMove | None]:
    """Standard minimax with alpha-beta pruning."""

    _record_search_node(params.context)
    repetition_score = _repetition_score(
        board,
        params.context,
        params.line_history,
        make_repetition_policy(params.context),
    )
    if repetition_score is not None:
        return (repetition_score, None)
    cached = _check_tt_cache(board, params)
    if cached is not None:
        _record_tt_hit(params.context)
        return cached

    legal_moves = get_legal_moves(board)
    ply = max(0, len(params.line_history) - 1)
    terminal_score = _terminal_score(
        board,
        legal_moves,
        ply,
        params.context.position_counts if params.context else None,
    )
    if terminal_score is not None:
        return (terminal_score, None)
    if params.depth == 0:
        return (
            _quiescence(
                board,
                QuiescenceParams(
                    alpha=params.alpha,
                    beta=params.beta,
                    is_maximizing=params.is_maximizing,
                    context=params.context,
                    legal_moves=tuple(legal_moves),
                ),
            ),
            None,
        )

    ordered_moves = _order_moves(board, legal_moves, params)
    return _search_move_loop(board, ordered_moves, params)


def _tie_break(
    move: Move,
    current_best: LegalMove | None,
    deterministic: bool,
    rng: random.Random | None = None,
) -> bool:
    """Return True when the new move should replace the current best on equal score."""
    if deterministic:
        if current_best is None:
            return True
        return _move_sort_key(move) < _move_sort_key(current_best)
    # Use the search-local RNG when available so seeded runs are reproducible
    # without mutating the module-global random state.
    chooser = rng if rng is not None else random
    return chooser.random() < 0.5


def _anchored_selected_score(
    is_maximizing: bool,
    selected_score: int,
    search_best_score: int,
) -> int:
    """Return the better of selected_score and search_best_score.

    Prevents tiebreak cascades: if a prior tiebreak replacement left
    selected_score worse than the alpha-beta winner, subsequent candidates
    are compared against the true best to stop further degradation.
    """
    if is_maximizing:
        return max(selected_score, search_best_score)
    return min(selected_score, search_best_score)


def _fold_search_best(
    params: MinimaxParams,
    child_score: int,
    search_best_score: int,
    search_best_move: LegalMove | None,
    move: Move,
) -> tuple[int, LegalMove | None, bool]:
    """Fold one child result into the running search best.

    Returns ``(search_best_score, search_best_move, is_better)`` where ``is_better``
    reports whether ``child_score`` strictly improved on the prior best. Callers use
    ``is_better`` to detect a non-improving root move whose reported score is only an
    alpha-beta bound rather than its exact value.
    """

    is_det = params.context is not None and params.context.deterministic
    tie_rng = params.context.rng if params.context is not None else None
    if params.is_maximizing:
        is_better = child_score > search_best_score
        is_tie = child_score == search_best_score
    else:
        is_better = child_score < search_best_score
        is_tie = child_score == search_best_score
    if is_better or (is_tie and _tie_break(move, search_best_move, is_det, tie_rng)):
        return child_score, LegalMove(move.start, move.end, move.promotion), is_better
    return search_best_score, search_best_move, is_better


def _search_move_loop(
    board: Board,
    ordered_moves: list[Move],
    params: MinimaxParams,
) -> tuple[int, LegalMove | None]:
    """Search one ply of child moves with alpha-beta pruning."""

    search_best_score = -INF if params.is_maximizing else INF
    search_best_move: LegalMove | None = None
    selected_score = -INF if params.is_maximizing else INF
    best_root_tiebreak = -INF if params.is_maximizing else INF
    root_selected_move: LegalMove | None = None
    alpha = params.alpha
    beta = params.beta

    for move in ordered_moves:
        child_score, root_tiebreak = _evaluate_child_move(board, move, params, alpha, beta)
        is_det = params.context is not None and params.context.deterministic
        tie_rng = params.context.rng if params.context is not None else None
        search_best_score, search_best_move, is_better = _fold_search_best(
            params,
            child_score,
            search_best_score,
            search_best_move,
            move,
        )
        if len(params.line_history) == 1:
            # For non-improving moves: clamp the reference score to the alpha-beta
            # winner so that tiebreak replacements cannot cascade. Once a weaker
            # move wins the root tiebreak and selected_score drifts, subsequent
            # candidates are compared against the true best rather than the
            # tiebreak-degraded selection score. Improving moves (is_better=True)
            # use selected_score directly so a genuinely better move always wins.
            ref_score = (
                selected_score
                if is_better
                else _anchored_selected_score(
                    params.is_maximizing, selected_score, search_best_score
                )
            )
            replace_selected_move = _prefer_root_move(
                params.is_maximizing,
                child_score,
                root_tiebreak,
                ref_score,
                best_root_tiebreak,
            )
            if replace_selected_move and not is_better:
                # A non-improving root move's child_score is only an alpha-beta
                # *bound*, not its exact value, so it must be re-searched with a
                # full window before the root tie-break may promote it:
                #   * a strictly-worse move searched against a window raised by a
                #     better sibling returns a fail-low/high bound (FIX9: a2a4
                #     returned a fail-low bound of 3919 with a true value of
                #     2256), and
                #   * a move that merely *ties* the running best is sitting
                #     exactly on the alpha/beta cutoff boundary: the child search
                #     stopped as soon as it proved "no better than best", so the
                #     reported tie can hide a far worse true value (FIX9:
                #     Bb4-e1 returned -266 == beta but is truly +305).
                # Only improving moves keep their exact in-window score, so the
                # re-search is gated on ``not is_better``.
                child_score, root_tiebreak = _evaluate_child_move(
                    board, move, params, -INF, INF
                )
                # The exact full-window score supersedes the discarded bound, so
                # re-fold it into the search best before deciding root selection:
                # search_best_score / search_best_move feed alpha-beta, the TT
                # store, and the returned root score, and must reflect the exact
                # value, never the stale bound. (A bounded non-improving move can
                # only resolve to an exact value no better than search_best_score,
                # so this updates search_best_move on a genuine tie and can never
                # leave a bound in the search-best state.)
                search_best_score, search_best_move, _ = _fold_search_best(
                    params,
                    child_score,
                    search_best_score,
                    search_best_move,
                    move,
                )
                ref_score = _anchored_selected_score(
                    params.is_maximizing, selected_score, search_best_score
                )
                replace_selected_move = _prefer_root_move(
                    params.is_maximizing,
                    child_score,
                    root_tiebreak,
                    ref_score,
                    best_root_tiebreak,
                )
        else:
            if params.is_maximizing:
                replace_selected_move = child_score > selected_score or (
                    child_score == selected_score
                    and _tie_break(move, root_selected_move, is_det, tie_rng)
                )
            else:
                replace_selected_move = child_score < selected_score or (
                    child_score == selected_score
                    and _tie_break(move, root_selected_move, is_det, tie_rng)
                )
        if root_selected_move is None or replace_selected_move:
            selected_score = child_score
            best_root_tiebreak = root_tiebreak
            root_selected_move = LegalMove(move.start, move.end, move.promotion)
        alpha, beta, cutoff = _update_alpha_beta(
            params.is_maximizing,
            search_best_score,
            alpha,
            beta,
        )
        if cutoff:
            _record_cutoff(params.context, move)
            break

    _store_tt_cache(
        board,
        params,
        search_best_score,
        search_best_move,
        (params.alpha, params.beta),
    )
    return (
        search_best_score,
        root_selected_move if len(params.line_history) == 1 else search_best_move,
    )


def _evaluate_child_move(
    board: Board,
    move: Move,
    params: MinimaxParams,
    alpha: int,
    beta: int,
) -> tuple[int, int]:
    """Evaluate a single child move recursively."""

    child_board = _make_copy_with_move(board, move)
    extension_bonus = _leaf_extension_bonus(board, move, child_board, params)
    child_result, _ = minimax(
        child_board,
        MinimaxParams(
            depth=params.depth - 1 + extension_bonus,
            alpha=alpha,
            beta=beta,
            is_maximizing=not params.is_maximizing,
            context=params.context,
            line_history=params.line_history + (position_key(child_board),),
            extension_budget=params.extension_budget - extension_bonus,
        ),
    )
    root_tiebreak = 0
    if len(params.line_history) == 1:
        root_tiebreak = _root_stability_adjustment(
            board,
            move,
            child_board,
            params.context,
            position_key,
        )
    return child_result, root_tiebreak


def _leaf_extension_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    params: MinimaxParams,
) -> int:
    """Return a bounded extension bonus for critical near-horizon moves.

    Check extensions fire at any depth so forcing sequences through checks
    are not cut off mid-calculation.  Strategic extensions are reserved for
    moves near the leaf (depth <= 2).  The extension_budget cap (starts at 1,
    decremented on each extension) prevents cascading depth explosions.
    """
    # Check extensions only fire at depth >= 2.  At depth 1 the child falls
    # directly into quiescence, so extending there adds noise without helping
    # the engine follow a forcing line further.
    if params.depth >= 2:
        check_ext = _check_extension(child_board, params.extension_budget)
        if check_ext:
            _record_selective_extension(params.context)
            return check_ext
    if params.depth > 2:
        return 0
    extension_bonus = _selective_extension_bonus(
        board,
        move,
        child_board,
        params.extension_budget,
        allow_strategic_extensions=params.depth == 1,
    )
    if extension_bonus > 0:
        _record_selective_extension(params.context)
    return extension_bonus


def _record_cutoff(context: SearchContext | None, move: Move) -> None:
    """Record cutoff diagnostics and killer moves."""

    if context is None:
        return
    if context.stats is not None:
        context.stats.cutoffs += 1
    if context.killer_moves is None:
        return
    killer_move = (move.start, move.end, move.promotion)
    if killer_move not in context.killer_moves:
        context.killer_moves.append(killer_move)


def _iterative_deepening_best_move(
    board: Board,
    depth: int,
    is_maximizing: bool,
    context: SearchContext,
) -> LegalMove | None:
    best_move: LegalMove | None = None
    previous_score = 0
    for current_depth in range(1, depth + 1):
        context.last_best_move = best_move
        depth_start = time.monotonic()
        score, move = _search_root_depth(
            board, current_depth, is_maximizing, previous_score, context
        )
        _record_depth_timing(context, current_depth, time.monotonic() - depth_start)
        if move is None:
            # Terminal or draw detected at root (e.g., fifty-move rule or insufficient
            # material). Return the best move found so far, or fall back to the first
            # legal move. The engine must always return a move when legal moves exist.
            root_legal = get_legal_moves(board)
            fallback: LegalMove | None = (
                LegalMove(
                    start=root_legal[0].start,
                    end=root_legal[0].end,
                    promotion=root_legal[0].promotion,
                )
                if root_legal
                else None
            )
            return best_move if best_move is not None else fallback
        previous_score = score
        best_move = move
        _trim_killer_moves(context)
    return best_move


def get_best_move(
    board: Board,
    depth: int,
    stats: SearchStats | None = None,
    position_counts: dict[str, int] | None = None,
    book_options: BestMoveOptions | None = None,
) -> LegalMove | None:
    """Get the best move for the current position at the requested depth."""
    if depth < 1:
        raise ValueError("depth must be >= 1")
    legal_moves = get_legal_moves(board)
    if not legal_moves:
        return None
    options = book_options or BestMoveOptions()
    # Local RNG controls all random choices (opening-book selection and tie-breaks)
    # without mutating module-global random state. random.Random(None) seeds from
    # OS entropy, preserving unseeded random behavior.
    rng = random.Random(options.rng_seed)
    if options.use_opening_book:
        book = options.opening_book or get_bundled_opening_book()
        if options.random_opening_book:
            book_move = book.find_book_move_random(board, rng=rng)
        else:
            book_move = book.find_book_move(board)
        if book_move is not None:
            return book_move
    effective_weights = _get_effective_weights(options.weights)
    context = SearchContext(
        transposition_table={},
        stats=stats,
        killer_moves=[],
        position_counts=_search_position_counts(board, position_counts, _shared_position_key),
        weights=effective_weights,
        deterministic=options.deterministic,
        rng=rng,
    )
    is_maximizing = board.turn == Color.WHITE
    return _iterative_deepening_best_move(board, depth, is_maximizing, context)


def _trim_killer_moves(context: SearchContext) -> None:
    """Keep the killer-move list small and recent."""
    if context.killer_moves is not None and len(context.killer_moves) > 4:
        context.killer_moves[:] = context.killer_moves[-4:]


def _search_root_depth(
    board: Board,
    depth: int,
    is_maximizing: bool,
    previous_score: int,
    context: SearchContext,
) -> tuple[int, LegalMove | None]:
    """Search one iterative-deepening layer, rerunning on aspiration failure."""
    alpha, beta = _initial_root_window(depth, previous_score, ASPIRATION_WINDOW, INF)
    while True:
        score, move = minimax(
            board,
            MinimaxParams(
                depth=depth,
                alpha=alpha,
                beta=beta,
                is_maximizing=is_maximizing,
                context=context,
                line_history=(position_key(board),),
            ),
        )
        if not _rerun_full_window_if_needed(score, alpha, beta, context, INF):
            return score, move
        _record_root_research(context)
        alpha, beta = -INF, INF


def search_root_depth(
    board: Board,
    depth: int,
    is_maximizing: bool,
    previous_score: int,
    context: SearchContext,
) -> tuple[int, LegalMove | None]:
    """Public wrapper for root-depth search used by diagnostics and tests."""

    return _search_root_depth(board, depth, is_maximizing, previous_score, context)


def minimax_no_prune(
    board: Board,
    depth: int,
    is_maximizing: bool,
    nodes: list[int] | None = None,
) -> int:
    """No-prune minimax reference for tests and shallow benchmarks."""

    if nodes is not None:
        nodes[0] += 1
    legal_moves = get_legal_moves(board)
    terminal_score = _terminal_score(board, legal_moves)
    if terminal_score is not None:
        return terminal_score
    if depth == 0:
        return quiescence(board, -INF, INF, is_maximizing)

    best_score = -INF if is_maximizing else INF
    for move in legal_moves:
        child_score = minimax_no_prune(
            _make_copy_with_move(board, move),
            depth - 1,
            not is_maximizing,
            nodes,
        )
        if is_maximizing:
            best_score = max(best_score, child_score)
        else:
            best_score = min(best_score, child_score)
    return best_score
