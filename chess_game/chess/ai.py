"""AI/Minimax implementation for chess engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import random
import time

from chess_game.chess.board import Board
from chess_game.chess.board.game_state import (
    is_dead_position as _gs_is_dead_position,
    is_fifty_move_rule as _gs_is_fifty_move_rule,
    is_in_check as _gs_is_in_check,
    is_insufficient_material as _gs_is_insufficient_material,
    is_seventy_five_move_rule as _gs_is_seventy_five_move_rule,
)
from chess_game.chess.ai_capture_ordering import capture_order_score as _shared_capture_order_score
from chess_game.chess.ai_board_utils import (
    clone_with_move as _make_copy_with_move,
    get_legal_moves,
)
from chess_game.chess.ai_move_ordering import (
    make_quiet_order_context,
    quiet_strategy_order_score,
)
from chess_game.chess.ai_quiescence_helpers import (
    _quiescence_capture_score as _quiescence_capture_score_impl,
    _quiescence_check_score as _quiescence_check_score_impl,
    _quiescence_structure_follow_up_score as _quiescence_structure_follow_up_score_impl,
    _quiescence_tactical_score as _quiescence_tactical_score_impl,
    select_quiescence_moves as _select_quiescence_moves,
)
from chess_game.chess.ai_search_helpers import (
    RepetitionPolicy,
    promotion_order_score as _promotion_order_score,
    initial_root_window as _initial_root_window,
    position_occurrence_count as _position_occurrence_count,
    record_depth_timing as _record_depth_timing,
    record_root_research as _record_root_research,
    record_selective_extension as _record_selective_extension,
    repetition_score as _repetition_score,
    prefer_root_move as _prefer_root_move,
    root_stability_adjustment as _root_stability_adjustment,
    rerun_full_window_if_needed as _rerun_full_window_if_needed,
    same_legal_move as _same_legal_move,
    check_extension as _check_extension,
    selective_extension_bonus as _selective_extension_bonus,
    search_position_counts as _search_position_counts,
    update_alpha_beta as _update_alpha_beta,
)
from chess_game.chess.ai_weight_cache import (
    get as _wc_get,
    invalidate_weights_cache as _invalidate_weights_cache,
    is_loaded as _wc_is_loaded,
    set_cache as _wc_set,
)
from chess_game.chess.eval_weights import EvalWeights
from chess_game.chess.evaluation import (
    evaluate,
    get_evaluation_breakdown as _get_evaluation_breakdown,
)
from chess_game.texel.weights_io import (
    TUNED_WEIGHTS_PATH as _TUNED_WEIGHTS_PATH,
    load_weights_or_default as _load_weights_or_default,
)
from chess_game.chess.evaluation_tables import (
    REPETITION_PROGRESS_ONLY_THRESHOLD,
    REPETITION_PROGRESS_THRESHOLD,
    VOLUNTARY_REPETITION_PENALTY,
)
from chess_game.chess.move import Move
from chess_game.chess.opening_book import OpeningBook, get_bundled_opening_book
from chess_game.chess.position_utils import position_key as _shared_position_key
from chess_game.chess.strategy_utils import is_capture_move as _is_capture_move
from chess_game.chess.types import Color, LegalMove, PieceType

INF = 10_000_000
MATE_SCORE = 100_000
MATE_SCORE_MARGIN = 1_000  # Safe margin for ply adjustments
DRAW_SCORE = 0
ASPIRATION_WINDOW = 150
MAX_QUIESCENCE_DEPTH = 4
MAX_QUIESCENCE_MOVES = 8
LegalMoveKey = tuple[object, object, Optional[PieceType]]
get_evaluation_breakdown = _get_evaluation_breakdown
_quiescence_capture_score = _quiescence_capture_score_impl
_quiescence_check_score = _quiescence_check_score_impl
_quiescence_structure_follow_up_score = _quiescence_structure_follow_up_score_impl
_quiescence_tactical_score = _quiescence_tactical_score_impl


def _get_effective_weights(weights: Optional[EvalWeights]) -> EvalWeights:
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


def _progress_score(board: Board) -> int:
    """Return the progress component used to discourage empty repetitions."""

    return _get_evaluation_breakdown(board)["progress"]


def _ctx_evaluate(board: Board, context: Optional[SearchContext]) -> int:
    """Evaluate board using the weights stored in context (or defaults)."""
    weights = context.weights if context is not None else None
    return evaluate(board, weights)


def _make_evaluate_fn(context: Optional[SearchContext]):
    """Return an evaluate callable that captures context weights."""

    def _fn(board: Board) -> int:
        return _ctx_evaluate(board, context)

    return _fn


class TTFlag(Enum):
    """Transposition table entry flag."""
    EXACT = "exact"
    LOWERBOUND = "lowerbound"
    UPPERBOUND = "upperbound"


@dataclass(frozen=True)
class TTEntry:
    """Entry in the transposition table."""
    depth: int
    score: int
    best_move: LegalMove | None
    flag: TTFlag


@dataclass
class TTHitDiagnostics:
    """Diagnostics describing how TT entries were reused."""

    tt_exact_hits: int = 0
    tt_bound_hits: int = 0
    tt_depth_sum: int = 0
    tt_depth_uses: int = 0


@dataclass
class TacticalDiagnostics:
    """Diagnostics about quiescence branching."""

    tactical_move_sum: int = 0
    tactical_positions: int = 0
    tactical_max_width: int = 0


@dataclass
class SearchDiagnostics:
    """Detailed optional diagnostics gathered during search."""

    fail_high_retries: int = 0
    fail_low_retries: int = 0
    root_researches: int = 0
    selective_extensions: int = 0
    depth_timings: dict[int, float] | None = None
    tt: TTHitDiagnostics | None = None
    tactical: TacticalDiagnostics | None = None

    def __post_init__(self) -> None:
        """Ensure nested diagnostics are always available."""
        if self.tt is None:
            self.tt = TTHitDiagnostics()
        if self.tactical is None:
            self.tactical = TacticalDiagnostics()


@dataclass
class SearchStats:
    """Lightweight stats for search and diagnostics."""

    nodes: int = 0
    cutoffs: int = 0
    tt_hits: int = 0
    quiescence_nodes: int = 0
    diagnostics: SearchDiagnostics | None = None

    def __post_init__(self) -> None:
        """Ensure diagnostics are always available for callers."""
        if self.diagnostics is None:
            self.diagnostics = SearchDiagnostics()

    @property
    def fail_high_retries(self) -> int:
        """Expose fail-high retries without expanding top-level state."""
        assert self.diagnostics is not None
        return self.diagnostics.fail_high_retries

    @fail_high_retries.setter
    def fail_high_retries(self, value: int) -> None:
        assert self.diagnostics is not None
        self.diagnostics.fail_high_retries = value

    @property
    def fail_low_retries(self) -> int:
        """Expose fail-low retries without expanding top-level state."""
        assert self.diagnostics is not None
        return self.diagnostics.fail_low_retries

    @fail_low_retries.setter
    def fail_low_retries(self, value: int) -> None:
        assert self.diagnostics is not None
        self.diagnostics.fail_low_retries = value

    @property
    def root_researches(self) -> int:
        """Expose root re-search count without expanding top-level state."""
        assert self.diagnostics is not None
        return self.diagnostics.root_researches

    @root_researches.setter
    def root_researches(self, value: int) -> None:
        assert self.diagnostics is not None
        self.diagnostics.root_researches = value

    @property
    def tactical_move_sum(self) -> int:
        """Expose tactical move totals without expanding top-level state."""
        assert self.diagnostics is not None
        assert self.diagnostics.tactical is not None
        return self.diagnostics.tactical.tactical_move_sum

    @tactical_move_sum.setter
    def tactical_move_sum(self, value: int) -> None:
        assert self.diagnostics is not None
        assert self.diagnostics.tactical is not None
        self.diagnostics.tactical.tactical_move_sum = value

    @property
    def tactical_positions(self) -> int:
        """Expose tactical node count without expanding top-level state."""
        assert self.diagnostics is not None
        assert self.diagnostics.tactical is not None
        return self.diagnostics.tactical.tactical_positions

    @tactical_positions.setter
    def tactical_positions(self, value: int) -> None:
        assert self.diagnostics is not None
        assert self.diagnostics.tactical is not None
        self.diagnostics.tactical.tactical_positions = value

    @property
    def tactical_max_width(self) -> int:
        """Expose maximum tactical width without expanding top-level state."""
        assert self.diagnostics is not None
        assert self.diagnostics.tactical is not None
        return self.diagnostics.tactical.tactical_max_width

    @tactical_max_width.setter
    def tactical_max_width(self, value: int) -> None:
        assert self.diagnostics is not None
        assert self.diagnostics.tactical is not None
        self.diagnostics.tactical.tactical_max_width = value

    @property
    def depth_timings(self) -> dict[int, float] | None:
        """Expose per-depth timing diagnostics."""
        assert self.diagnostics is not None
        return self.diagnostics.depth_timings

    @depth_timings.setter
    def depth_timings(self, value: dict[int, float] | None) -> None:
        assert self.diagnostics is not None
        self.diagnostics.depth_timings = value

    @property
    def tt_exact_hits(self) -> int:
        """Expose exact TT hits."""
        assert self.diagnostics is not None
        assert self.diagnostics.tt is not None
        return self.diagnostics.tt.tt_exact_hits

    @tt_exact_hits.setter
    def tt_exact_hits(self, value: int) -> None:
        assert self.diagnostics is not None
        assert self.diagnostics.tt is not None
        self.diagnostics.tt.tt_exact_hits = value

    @property
    def tt_bound_hits(self) -> int:
        """Expose bound-based TT hits."""
        assert self.diagnostics is not None
        assert self.diagnostics.tt is not None
        return self.diagnostics.tt.tt_bound_hits

    @tt_bound_hits.setter
    def tt_bound_hits(self, value: int) -> None:
        assert self.diagnostics is not None
        assert self.diagnostics.tt is not None
        self.diagnostics.tt.tt_bound_hits = value

    @property
    def avg_tt_hit_depth(self) -> float:
        """Return the average depth of TT entries reused during search."""
        assert self.diagnostics is not None
        assert self.diagnostics.tt is not None
        if self.diagnostics.tt.tt_depth_uses == 0:
            return 0.0
        return self.diagnostics.tt.tt_depth_sum / self.diagnostics.tt.tt_depth_uses


@dataclass(frozen=True)
class BestMoveOptions:
    """Options that control opening-book lookup in get_best_move()."""

    use_opening_book: bool = True
    opening_book: OpeningBook | None = None
    random_opening_book: bool = False
    weights: Optional[EvalWeights] = None
    deterministic: bool = False
    rng_seed: int | None = None


@dataclass
class SearchContext:
    """Shared search state reused across recursive calls."""

    transposition_table: Optional[dict[str, TTEntry]] = None
    last_best_move: Optional[LegalMove] = None
    nodes_searched: Optional[list[int]] = None
    stats: Optional[SearchStats] = None
    killer_moves: Optional[list[LegalMoveKey]] = None
    position_counts: Optional[dict[str, int]] = None
    weights: Optional[EvalWeights] = None
    deterministic: bool = False


@dataclass
class MinimaxParams:
    """Configuration for a minimax search."""

    depth: int
    alpha: int
    beta: int
    is_maximizing: bool
    context: Optional[SearchContext] = None
    line_history: tuple[str, ...] = ()
    extension_budget: int = 1


@dataclass
class QuiescenceParams:
    """Parameters for quiescence search."""

    alpha: int
    beta: int
    is_maximizing: bool
    context: Optional[SearchContext] = None
    depth_remaining: int = MAX_QUIESCENCE_DEPTH
    line_history: tuple[str, ...] = ()
    legal_moves: tuple[Move, ...] | None = None


def _is_mate_score(score: int) -> bool:
    """Return true if score is close to a mate score.

    Mate scores are not stored in TT until proper ply-based normalization exists.
    """
    return abs(score) >= MATE_SCORE - MATE_SCORE_MARGIN


def _check_tt_cache(
    board: Board,
    params: MinimaxParams,
) -> Optional[tuple[int, LegalMove | None]]:
    """Check transposition table for a cached result.

    Mate-score entries are ignored until proper normalization exists.
    """

    if _position_occurrence_count(board, params.context, params.line_history, position_key) > 1:
        return None
    context = params.context
    if context is None or context.transposition_table is None:
        return None
    entry = context.transposition_table.get(position_key(board))
    if entry is None or entry.depth < params.depth:
        return None
    if _is_mate_score(entry.score):
        # Mate scores are not stored/used until normalization exists
        return None
    if entry.flag == TTFlag.EXACT:
        _record_tt_usage(context, entry)
        return (entry.score, entry.best_move)
    lower_bound_hit = entry.flag == TTFlag.LOWERBOUND and entry.score >= params.beta
    upper_bound_hit = entry.flag == TTFlag.UPPERBOUND and entry.score <= params.alpha
    if lower_bound_hit or upper_bound_hit:
        _record_tt_usage(context, entry)
        return (entry.score, entry.best_move)
    return None


def _store_tt_cache(
    board: Board,
    params: MinimaxParams,
    score: int,
    move: LegalMove | None,
    original_window: tuple[int, int],
) -> None:
    """Store a result in the transposition table with the correct bound flag.

    Mate scores are skipped until proper TT mate-score normalization exists.
    """

    if _position_occurrence_count(board, params.context, params.line_history, position_key) > 1:
        return
    context = params.context
    if context is None or context.transposition_table is None:
        return
    if _is_mate_score(score):
        # TODO: Implement mate-score normalization for TT storage/retrieval.
        # Mate scores are ply-relative and corrupt when stored/retrieved without
        # proper adjustment. Skip storage until normalization is implemented.
        return
    alpha_orig, beta_orig = original_window
    if score <= alpha_orig:
        flag = TTFlag.UPPERBOUND
    elif score >= beta_orig:
        flag = TTFlag.LOWERBOUND
    else:
        flag = TTFlag.EXACT
    # TODO: Implement mate-score normalization for TT storage/retrieval.
    # Mate scores are currently not normalized on store/retrieve, which can corrupt
    # mate distance across different search plies. Full normalization is a separate patch.
    new_entry = TTEntry(
        depth=params.depth,
        score=score,
        best_move=move,
        flag=flag,
    )
    key = position_key(board)
    existing = context.transposition_table.get(key)
    if existing is None or params.depth >= existing.depth:
        context.transposition_table[key] = new_entry

def _record_search_node(context: Optional[SearchContext]) -> None:
    """Increment node counters when diagnostics are enabled."""

    if context is None:
        return
    if context.nodes_searched is not None:
        context.nodes_searched[0] += 1
    if context.stats is not None:
        context.stats.nodes += 1


def _record_quiescence_node(context: Optional[SearchContext]) -> None:
    """Increment quiescence counters when diagnostics are enabled."""

    if context is not None and context.stats is not None:
        context.stats.quiescence_nodes += 1


def _terminal_score(
    board: Board,
    legal_moves: list[Move],
    ply: int = 0,
    position_counts: Optional[dict[str, int]] = None,
) -> Optional[int]:
    """Return a terminal score for draws and checkmate; None when non-terminal.

    Covers all draw states supported by the board/game-state API:
    - fifty-move rule
    - seventy-five move rule
    - insufficient material
    - dead position
    - fivefold repetition (if position_counts provided)
    - stalemate
    - checkmate (via ply-adjusted mate score)
    """

    # Draw states checked before legal move availability
    if _gs_is_fifty_move_rule(board):
        return DRAW_SCORE
    if _gs_is_seventy_five_move_rule(board):
        return DRAW_SCORE
    if _gs_is_insufficient_material(board):
        return DRAW_SCORE
    if _gs_is_dead_position(board):
        return DRAW_SCORE
    if position_counts is not None:
        from chess_game.chess.board.game_state import is_fivefold_repetition as _gs_is_fivefold
        if _gs_is_fivefold(board, position_counts):
            return DRAW_SCORE

    # If legal moves exist, position is not terminal
    if legal_moves:
        return None

    # No legal moves: either checkmate or stalemate
    if _gs_is_in_check(board, board.turn):
        # Side to move is checkmated; prefer closer mates
        return -MATE_SCORE + ply if board.turn == Color.WHITE else MATE_SCORE - ply

    # Stalemate: no legal moves and not in check
    return DRAW_SCORE


def minimax(
    board: Board,
    params: MinimaxParams,
) -> tuple[int, Optional[LegalMove]]:
    """Standard minimax with alpha-beta pruning."""

    _record_search_node(params.context)
    repetition_score = _repetition_score(
        board,
        params.context,
        params.line_history,
        RepetitionPolicy(
            position_key=position_key,
            evaluate=_make_evaluate_fn(params.context),
            progress=_progress_score,
            threshold=REPETITION_PROGRESS_THRESHOLD,
            progress_threshold=REPETITION_PROGRESS_ONLY_THRESHOLD,
            penalty=VOLUNTARY_REPETITION_PENALTY,
        ),
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


def _record_tt_hit(context: Optional[SearchContext]) -> None:
    """Record a transposition-table hit when stats are enabled."""

    if context is not None and context.stats is not None:
        context.stats.tt_hits += 1


def _record_tt_usage(context: Optional[SearchContext], entry: TTEntry) -> None:
    """Record the kind and depth of a TT reuse."""

    if context is None or context.stats is None:
        return
    if entry.flag == TTFlag.EXACT:
        context.stats.tt_exact_hits += 1
    else:
        context.stats.tt_bound_hits += 1
    assert context.stats.diagnostics is not None
    assert context.stats.diagnostics.tt is not None
    context.stats.diagnostics.tt.tt_depth_sum += entry.depth
    context.stats.diagnostics.tt.tt_depth_uses += 1


def _tie_break(
    move: Move,
    current_best: Optional[LegalMove],
    deterministic: bool,
) -> bool:
    """Return True when the new move should replace the current best on equal score."""
    if deterministic:
        if current_best is None:
            return True
        return _move_sort_key(move) < _move_sort_key(current_best)
    return random.random() < 0.5


def _search_move_loop(
    board: Board,
    ordered_moves: list[Move],
    params: MinimaxParams,
) -> tuple[int, Optional[LegalMove]]:
    """Search one ply of child moves with alpha-beta pruning."""

    search_best_score = -INF if params.is_maximizing else INF
    search_best_move: Optional[LegalMove] = None
    selected_score = -INF if params.is_maximizing else INF
    best_root_tiebreak = -INF if params.is_maximizing else INF
    root_selected_move: Optional[LegalMove] = None
    alpha = params.alpha
    beta = params.beta

    for move in ordered_moves:
        child_score, root_tiebreak = _evaluate_child_move(board, move, params, alpha, beta)
        if params.is_maximizing:
            is_better = child_score > search_best_score
            is_tie = child_score == search_best_score
        else:
            is_better = child_score < search_best_score
            is_tie = child_score == search_best_score
        is_det = params.context is not None and params.context.deterministic
        if is_better or (is_tie and _tie_break(move, search_best_move, is_det)):
            search_best_score = child_score
            search_best_move = LegalMove(move.start, move.end, move.promotion)
        if len(params.line_history) == 1:
            replace_selected_move = _prefer_root_move(
                params.is_maximizing,
                child_score,
                root_tiebreak,
                selected_score,
                best_root_tiebreak,
            )
        else:
            if params.is_maximizing:
                replace_selected_move = child_score > selected_score or (
                    child_score == selected_score
                    and _tie_break(move, root_selected_move, is_det)
                )
            else:
                replace_selected_move = child_score < selected_score or (
                    child_score == selected_score
                    and _tie_break(move, root_selected_move, is_det)
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


def _record_cutoff(context: Optional[SearchContext], move: Move) -> None:
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
        RepetitionPolicy(
            position_key=position_key,
            evaluate=_make_evaluate_fn(context),
            progress=_progress_score,
            threshold=REPETITION_PROGRESS_THRESHOLD,
            progress_threshold=REPETITION_PROGRESS_ONLY_THRESHOLD,
            penalty=VOLUNTARY_REPETITION_PENALTY,
        ),
    )
    if repetition_score is not None:
        return repetition_score

    # Get legal moves once for reuse
    legal_moves = (
        list(params.legal_moves) if params.legal_moves is not None
        else get_legal_moves(board)
    )

    # Check for terminal/draw states early
    terminal_score = _terminal_score(board, legal_moves, ply, context.position_counts if context else None)
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
    if _is_quiescence_cutoff(stand_pat, alpha, beta, params.is_maximizing):
        return stand_pat
    if params.depth_remaining <= 0:
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


def _record_tactical_width(context: Optional[SearchContext], width: int) -> None:
    """Record tactical branching diagnostics."""

    if context is None or context.stats is None:
        return
    context.stats.tactical_positions += 1
    context.stats.tactical_move_sum += width
    context.stats.tactical_max_width = max(context.stats.tactical_max_width, width)



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
    params: Optional[MinimaxParams] = None,
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
    params: Optional[MinimaxParams],
    quiet_order_context=None,
) -> int:
    """Return a move-ordering score.

    Placement audit:
    - quiet strategic heuristics live in `ai_move_ordering.py`
    - tactical capture ordering lives here
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


def _tt_best_move(board: Board, context: SearchContext) -> Optional[LegalMove]:
    """Return the TT move for the current board if one exists."""
    if context.transposition_table is None:
        return None
    entry = context.transposition_table.get(position_key(board))
    return None if entry is None else entry.best_move


def _iterative_deepening_best_move(
    board: Board,
    depth: int,
    is_maximizing: bool,
    context: SearchContext,
) -> Optional[LegalMove]:
    best_move: Optional[LegalMove] = None
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
            fallback: Optional[LegalMove] = (
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
    stats: Optional[SearchStats] = None,
    position_counts: Optional[dict[str, int]] = None,
    book_options: Optional[BestMoveOptions] = None,
) -> Optional[LegalMove]:
    """Get the best move for the current position at the requested depth."""
    if depth < 1:
        raise ValueError("depth must be >= 1")
    legal_moves = get_legal_moves(board)
    if not legal_moves:
        return None
    options = book_options or BestMoveOptions()
    # Apply seed early to control all random choices, including opening-book selection
    if options.rng_seed is not None:
        random.seed(options.rng_seed)
    if options.use_opening_book:
        book = options.opening_book or get_bundled_opening_book()
        if options.random_opening_book:
            book_move = book.find_book_move_random(board)
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
) -> tuple[int, Optional[LegalMove]]:
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
) -> tuple[int, Optional[LegalMove]]:
    """Public wrapper for root-depth search used by diagnostics and tests."""

    return _search_root_depth(board, depth, is_maximizing, previous_score, context)


def position_key(board: Board) -> str:
    """Generate a full position key including turn, castling rights, and en passant."""

    return _shared_position_key(board)


def _position_key(board: Board) -> str:
    """Backward-compatible internal alias for the full position key."""

    return position_key(board)


def _fen_key(board: Board) -> str:
    """Compatibility alias for older tests and scripts."""

    return position_key(board)


def minimax_no_prune(
    board: Board,
    depth: int,
    is_maximizing: bool,
    nodes: Optional[list[int]] = None,
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
