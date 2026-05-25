"""AI/Minimax implementation for chess engine."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Optional

import sys
import time

from chess_game.chess.board import Board
from chess_game.chess.board.game_state import is_in_check as _gs_is_in_check
from chess_game.chess.ai_capture_ordering import capture_order_score as _shared_capture_order_score
from chess_game.chess.ai_move_ordering import quiet_strategy_order_score
from chess_game.chess.ai_quiescence_helpers import (
    _quiescence_capture_score as _quiescence_capture_score_impl,
    _quiescence_check_score as _quiescence_check_score_impl,
    _quiescence_structure_follow_up_score as _quiescence_structure_follow_up_score_impl,
    _quiescence_tactical_score as _quiescence_tactical_score_impl,
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
    selective_extension_bonus as _selective_extension_bonus,
    search_position_counts as _search_position_counts,
    update_alpha_beta as _update_alpha_beta,
)
from chess_game.chess.coords import index_to_algebraic
from chess_game.chess.evaluation import (
    MATERIAL_VALUES,
    evaluate,
    get_evaluation_breakdown as _get_evaluation_breakdown,
)
from chess_game.chess.evaluation_tables import (
    REPETITION_PROGRESS_ONLY_THRESHOLD,
    REPETITION_PROGRESS_THRESHOLD,
    VOLUNTARY_REPETITION_PENALTY,
)
from chess_game.chess.move import Move
from chess_game.chess.strategy_utils import is_capture_move as _is_capture_move
from chess_game.chess.types import Color, LegalMove, PieceType

sys.setrecursionlimit(50000)
INF = 10_000_000
MATE_SCORE = 100_000
ASPIRATION_WINDOW = 150
MAX_QUIESCENCE_DEPTH = 1
MAX_QUIESCENCE_MOVES = 4
LegalMoveKey = tuple[object, object, Optional[PieceType]]
get_evaluation_breakdown = _get_evaluation_breakdown
_quiescence_capture_score = _quiescence_capture_score_impl
_quiescence_check_score = _quiescence_check_score_impl
_quiescence_structure_follow_up_score = _quiescence_structure_follow_up_score_impl
_quiescence_tactical_score = _quiescence_tactical_score_impl
def _progress_score(board: Board) -> int:
    """Return the progress component used to discourage empty repetitions."""

    return _get_evaluation_breakdown(board)["progress"]


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


@dataclass
class SearchContext:
    """Shared search state reused across recursive calls."""

    transposition_table: Optional[dict[str, TTEntry]] = None
    last_best_move: Optional[LegalMove] = None
    nodes_searched: Optional[list[int]] = None
    stats: Optional[SearchStats] = None
    killer_moves: Optional[list[LegalMoveKey]] = None
    position_counts: Optional[dict[str, int]] = None


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


def get_legal_moves(board: Board) -> list[Move]:
    """Get all legal moves for the side to move."""

    return [
        Move(start=start, end=end, promotion=promotion)
        for start, end, promotion in board.get_legal_moves()
    ]


def _make_copy_with_move(board: Board, move: Move) -> Board:
    """Create a new board state after making a move."""

    simulated = shallow_clone_board(board)
    if not simulated.apply_legal_move(
        move.start,
        move.end,
        promotion=move.promotion,
    ):
        raise RuntimeError("Simulated move failed legality check")
    return simulated


def _check_tt_cache(
    board: Board,
    params: MinimaxParams,
) -> Optional[tuple[int, LegalMove | None]]:
    """Check transposition table for a cached result."""

    if _position_occurrence_count(board, params.context, params.line_history, position_key) > 1:
        return None
    context = params.context
    if context is None or context.transposition_table is None:
        return None
    entry = context.transposition_table.get(position_key(board))
    if entry is None or entry.depth < params.depth:
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
    """Store a result in the transposition table with the correct bound flag."""

    if _position_occurrence_count(board, params.context, params.line_history, position_key) > 1:
        return
    context = params.context
    if context is None or context.transposition_table is None:
        return
    alpha_orig, beta_orig = original_window
    if score <= alpha_orig:
        flag = TTFlag.UPPERBOUND
    elif score >= beta_orig:
        flag = TTFlag.LOWERBOUND
    else:
        flag = TTFlag.EXACT
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


def shallow_clone_board(board: Board) -> Board:
    """Create a search clone of the board."""

    return board.clone()


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


def _terminal_score(board: Board, legal_moves: list[Move]) -> Optional[int]:
    """Return a terminal score when the side to move is mated or stalemated."""

    if legal_moves:
        return None
    if _gs_is_in_check(board, board.turn):
        return -MATE_SCORE if board.turn == Color.WHITE else MATE_SCORE
    return 0


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
            evaluate=evaluate,
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
    terminal_score = _terminal_score(board, legal_moves)
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


def _search_move_loop(
    board: Board,
    ordered_moves: list[Move],
    params: MinimaxParams,
) -> tuple[int, Optional[LegalMove]]:
    """Search one ply of child moves with alpha-beta pruning."""

    is_root = len(params.line_history) == 1
    best_score = -INF if params.is_maximizing else INF
    selected_score = -INF if params.is_maximizing else INF
    best_root_tiebreak = -INF if params.is_maximizing else INF
    best_move: Optional[LegalMove] = None
    alpha = params.alpha
    beta = params.beta

    for move in ordered_moves:
        child_score, root_tiebreak = _evaluate_child_move(board, move, params, alpha, beta)
        if (
            child_score > best_score
            if params.is_maximizing
            else child_score < best_score
        ):
            best_score = child_score
        if is_root:
            replace_selected_move = _prefer_root_move(
                params.is_maximizing,
                child_score,
                root_tiebreak,
                selected_score,
                best_root_tiebreak,
            )
        else:
            replace_selected_move = (
                child_score > selected_score
                if params.is_maximizing
                else child_score < selected_score
            )
        if best_move is None or replace_selected_move:
            selected_score = child_score
            best_root_tiebreak = root_tiebreak
            best_move = LegalMove(move.start, move.end, move.promotion)
        alpha, beta, cutoff = _update_alpha_beta(
            params.is_maximizing,
            best_score,
            alpha,
            beta,
        )
        if cutoff:
            _record_cutoff(params.context, move)
            break

    _store_tt_cache(board, params, best_score, best_move, (params.alpha, params.beta))
    return (best_score, best_move)


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
    """Return a bounded extension bonus for critical near-horizon moves."""

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
    context: Optional[SearchContext] = None,
) -> int:
    """Extend tactical leaf nodes through captures and promotions."""

    return _quiescence(
        board,
        QuiescenceParams(
            alpha=alpha,
            beta=beta,
            is_maximizing=is_maximizing,
            context=context,
        ),
    )


def _quiescence(board: Board, params: QuiescenceParams) -> int:
    """Internal quiescence implementation with bounded recursion."""

    alpha = params.alpha
    beta = params.beta
    context = params.context
    _record_quiescence_node(context)
    repetition_score = _repetition_score(
        board,
        context,
        params.line_history,
        RepetitionPolicy(
            position_key=position_key,
            evaluate=evaluate,
            progress=_progress_score,
            threshold=REPETITION_PROGRESS_THRESHOLD,
            progress_threshold=REPETITION_PROGRESS_ONLY_THRESHOLD,
            penalty=VOLUNTARY_REPETITION_PENALTY,
        ),
    )
    if repetition_score is not None:
        return repetition_score
    stand_pat = evaluate(board)
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

    tactical_moves = _get_tactical_moves(
        board,
        list(params.legal_moves) if params.legal_moves else None,
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


def _get_tactical_moves(
    board: Board,
    legal_moves: list[Move] | None = None,
) -> list[Move]:
    """Return capture and promotion moves for quiescence search.

    Uses pre-computed legal_moves when available to avoid a redundant
    get_legal_moves() call at depth-0 leaf nodes.
    """

    moves = legal_moves if legal_moves is not None else get_legal_moves(board)
    tactical_moves = [move for move in moves if _is_tactical_move(board, move)]
    ordered_moves = _order_moves(board, tactical_moves)
    return ordered_moves[:MAX_QUIESCENCE_MOVES]


def _is_tactical_move(board: Board, move: Move) -> bool:
    """Return True when a move changes material immediately."""

    if move.promotion is not None:
        return True
    return _is_interesting_capture(board, move)


def _is_interesting_capture(board: Board, move: Move) -> bool:
    """Return True for tactical captures worth exploring in quiescence."""

    if not _is_capture_move(board, move):
        return False
    captured_piece = board.get_piece(move.end)
    attacker = board.get_piece(move.start)
    if attacker is None:
        return False
    if captured_piece is None:
        return False
    if MATERIAL_VALUES[captured_piece.kind] < MATERIAL_VALUES[PieceType.BISHOP]:
        return False
    return MATERIAL_VALUES[captured_piece.kind] >= MATERIAL_VALUES[attacker.kind]


def _order_moves(
    board: Board,
    legal_moves: list[Move],
    params: Optional[MinimaxParams] = None,
) -> list[Move]:
    """Sort moves for better pruning order."""

    scored_moves = [
        (_move_order_score(board, move, params), move)
        for move in legal_moves
    ]
    scored_moves.sort(key=lambda item: item[0], reverse=True)
    return [move for _, move in scored_moves]


def _move_order_score(
    board: Board,
    move: Move,
    params: Optional[MinimaxParams],
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
        score += quiet_strategy_order_score(board, move)
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


def get_best_move(
    board: Board,
    depth: int,
    stats: Optional[SearchStats] = None,
    position_counts: Optional[dict[str, int]] = None,
) -> Optional[LegalMove]:
    """Get the best move for the current position at given search depth."""

    if depth < 1:
        raise ValueError("depth must be >= 1")
    if not get_legal_moves(board):
        return None

    context = SearchContext(
        transposition_table={},
        stats=stats,
        killer_moves=[],
        position_counts=_search_position_counts(board, position_counts, position_key),
    )
    best_move: Optional[LegalMove] = None
    previous_score = 0
    is_maximizing = board.turn == Color.WHITE

    for current_depth in range(1, depth + 1):
        context.last_best_move = best_move
        depth_start = time.monotonic()
        score, move = _search_root_depth(
            board,
            current_depth,
            is_maximizing,
            previous_score,
            context,
        )
        _record_depth_timing(context, current_depth, time.monotonic() - depth_start)
        if move is None:
            return None
        previous_score = score
        best_move = move
        _trim_killer_moves(context)
    return best_move


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

    pieces = []
    for row in board.board:
        for piece in row:
            if piece is None:
                pieces.append(".")
            else:
                color_char = "w" if piece.color == Color.WHITE else "b"
                kind_char = {
                    PieceType.PAWN: "p",
                    PieceType.KNIGHT: "n",
                    PieceType.BISHOP: "b",
                    PieceType.ROOK: "r",
                    PieceType.QUEEN: "q",
                    PieceType.KING: "k",
                }[piece.kind]
                pieces.append(f"{color_char}{kind_char}")
    turn_char = "w" if board.turn == Color.WHITE else "b"
    castling = ""
    if board.castling_rights.white_kingside:
        castling += "K"
    if board.castling_rights.white_queenside:
        castling += "Q"
    if board.castling_rights.black_kingside:
        castling += "k"
    if board.castling_rights.black_queenside:
        castling += "q"
    ep_target = (
        "-"
        if board.en_passant_target is None
        else index_to_algebraic(board.en_passant_target)
    )
    castling = castling or "-"
    return "".join(pieces) + "|" + turn_char + "|" + castling + "|" + ep_target


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
