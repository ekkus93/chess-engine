"""AI/Minimax implementation for chess engine."""

from __future__ import annotations

import copy
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import sys
from chess_game.chess.board import Board
from chess_game.chess.board.game_state import is_in_check as _gs_is_in_check
from chess_game.chess.constants import (
    ROW_1,
    ROW_8,
    ConstantSquare,
    get_col_constant,
    get_row_constant,
)
from chess_game.chess.coords import index_to_algebraic
from chess_game.chess.evaluation import (
    KING_TABLE,
    KNIGHT_TABLE,
    MATERIAL_VALUES,
    PAWN_TABLE,
    QUEEN_TABLE,
    BISHOP_TABLE,
    ROOK_TABLE,
)
from chess_game.chess.move import Move
from chess_game.chess.types import Color, LegalMove, Piece, PieceType

sys.setrecursionlimit(50000)

LegalMoveKey = tuple[int, LegalMove]

INF = 10_000_000
MATE_SCORE = 100_000


@dataclass
class MoveOrderingKey:
    """Score for move ordering (higher = prioritize first)."""

    score: int
    start: ConstantSquare
    end: ConstantSquare
    promotion: Optional[PieceType] = None

    def __init__(
        self,
        score: int,
        start: ConstantSquare,
        end: ConstantSquare,
        promotion: Optional[PieceType] = None,
    ):
        self.score = score
        self.start = start
        self.end = end
        self.promotion = promotion

    def __lt__(self, other: MoveOrderingKey) -> bool:
        return self.score < other.score


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
class SearchStats:
    """Lightweight stats for search (for tests/benchmarks only)."""
    nodes: int = 0
    cutoffs: int = 0
    tt_hits: int = 0


@dataclass
class MinimaxParams:
    """Configuration for a minimax search."""

    depth: int
    alpha: int
    beta: int
    is_maximizing: bool
    transposition_table: Optional[dict[str, TTEntry]] = None
    last_best_move: Optional[LegalMove] = None
    nodes_searched: Optional[list[int]] = None
    stats: Optional[SearchStats] = None


def evaluate(board: Board) -> int:
    """Evaluate the board position from White's perspective."""
    total_score: int = 0

    for row in range(8):
        for col in range(8):
            piece = board.get_piece(
                ConstantSquare(row=get_row_constant(row), col=get_col_constant(col))
            )
            if piece is None:
                continue

            color_bonus = 1 if piece.color == Color.WHITE else -1
            piece_score = _evaluate_piece(piece, row, col)
            total_score += color_bonus * piece_score

    return total_score


def _evaluate_piece(piece: Piece, row: int, col: int) -> int:
    """Get evaluation score for a single piece."""
    material = MATERIAL_VALUES[piece.kind]

    if piece.color == Color.BLACK:
        row = 7 - row

    positional_bias = 0
    if piece.kind == PieceType.PAWN:
        positional_bias = PAWN_TABLE[row][col]
    elif piece.kind == PieceType.KNIGHT:
        positional_bias = KNIGHT_TABLE[row][col]
    elif piece.kind == PieceType.BISHOP:
        positional_bias = BISHOP_TABLE[row][col]
    elif piece.kind == PieceType.ROOK:
        positional_bias = ROOK_TABLE[row][col]
    elif piece.kind == PieceType.QUEEN:
        positional_bias = QUEEN_TABLE[row][col]
    elif piece.kind == PieceType.KING:
        positional_bias = KING_TABLE[row][col]

    return material + positional_bias


def get_legal_moves(board: Board) -> list[Move]:
    """Get all legal moves for the side to move."""
    legal_moves = board.get_legal_moves()
    return [
        Move(
            start=move[0],
            end=move[1],
            promotion=move[2],
        )
        for move in legal_moves
    ]


def _make_copy_with_move(
    board: Board,
    start: ConstantSquare,
    end: ConstantSquare,
    promotion: Optional[PieceType] = None,
) -> Board:
    """Create a new board state after making a move."""
    simulated = board.clone()
    success = simulated.make_move(start, end, promotion=promotion)
    if not success:
        raise RuntimeError("Simulated move failed legality check")
    return simulated


def _check_tt_cache(
    board: Board,
    params: MinimaxParams,
) -> Optional[tuple[int, LegalMove]]:
    """Check transposition table for a cached result."""
    tt = params.transposition_table
    if not tt:
        return None

    key = _position_key(board)
    if key not in tt:
        return None

    entry = tt[key]
    if entry.depth < params.depth:
        return None

    alpha = params.alpha
    beta = params.beta

    if entry.flag == TTFlag.EXACT:
        return (entry.score, entry.best_move)

    # LOWERBOUND: useful if score >= beta
    if entry.flag == TTFlag.LOWERBOUND and entry.score >= beta:
        return (entry.score, entry.best_move)

    # UPPERBOUND: useful if score <= alpha
    if entry.flag == TTFlag.UPPERBOUND and entry.score <= alpha:
        return (entry.score, entry.best_move)

    return None


def _store_tt_cache(
    board: Board,
    params: MinimaxParams,
    score: int,
    move: LegalMove | None,
    alpha_orig: int,
    beta_orig: int,
) -> None:
    """Store a result in the transposition table with correct flag."""
    tt = params.transposition_table
    if tt is None:
        return

    key = _position_key(board)

    if score <= alpha_orig:
        flag = TTFlag.UPPERBOUND
    elif score >= beta_orig:
        flag = TTFlag.LOWERBOUND
    else:
        flag = TTFlag.EXACT

    entry = TTEntry(
        depth=params.depth,
        score=score,
        best_move=move,
        flag=flag,
    )

    existing = tt.get(key)
    if existing is None or params.depth >= existing.depth:
        tt[key] = entry


def shallow_clone_board(board: Board) -> Board:
    """Create a shallow clone of board for search."""
    new_board = Board.__new__(Board)

    new_board.board = [
        [
            copy.deepcopy(p) if p is not None else None
            for p in row
        ]
        for row in board.board
    ]

    new_board.turn = board.turn
    new_board.en_passant_target = board.en_passant_target
    new_board.castling_rights = copy.copy(board.castling_rights)
    new_board._move_history = list(board._move_history)
    new_board.init_validators()
    return new_board


def _search_move_loop(
    board: Board,
    legal_moves: list[Move],
    scored_moves: list[MoveOrderingKey],
    params: MinimaxParams,
) -> tuple[int, Optional[LegalMove]]:
    """Execute the main minimax search loop with alpha-beta pruning."""
    best_score: int = -100_000_000 if params.is_maximizing else 100_000_000
    best_move: LegalMove | None = None

    alpha = params.alpha
    beta = params.beta

    alpha_orig = alpha
    beta_orig = beta

    for move_key in scored_moves:
        move = next(
            m
            for m in legal_moves
            if (
                m.start == move_key.start
                and m.end == move_key.end
                and m.promotion == move_key.promotion
            )
        )

        new_board = shallow_clone_board(board)
        new_board.make_move(move.start, move.end, promotion=move.promotion)

        child_params = MinimaxParams(
            depth=params.depth - 1,
            alpha=alpha,
            beta=beta,
            is_maximizing=not params.is_maximizing,
            transposition_table=params.transposition_table,
            nodes_searched=params.nodes_searched,
            stats=params.stats,
        )
        child_result = minimax(new_board, child_params)
        child_score = int(child_result[0])

        if params.is_maximizing:
            if child_score > best_score:
                best_score = child_score
                best_move = LegalMove(move.start, move.end, move.promotion)
            alpha = max(alpha, child_score)
            if alpha >= beta:
                if params.stats is not None:
                    params.stats.cutoffs += 1
                break
        else:
            if child_score < best_score:
                best_score = child_score
                best_move = LegalMove(move.start, move.end, move.promotion)
            beta = min(beta, child_score)
            if beta <= alpha:
                if params.stats is not None:
                    params.stats.cutoffs += 1
                break

    _store_tt_cache(board, params, best_score, best_move, alpha_orig, beta_orig)

    return (best_score, best_move)


def minimax(
    board: Board,
    params: MinimaxParams,
) -> tuple[int, Optional[LegalMove]]:
    """Standard minimax with alpha-beta pruning."""
    # Node counter for tests (no-op when not used)
    if params.nodes_searched is not None:
        params.nodes_searched[0] += 1

    # Use SearchStats if present
    if params.stats is not None:
        params.stats.nodes += 1

    # Check transposition table
    cached = _check_tt_cache(board, params)
    if cached is not None:
        if params.stats is not None:
            params.stats.tt_hits += 1
        return cached

    # Generate legal moves FIRST (terminal handling before depth cutoff).
    legal_moves = get_legal_moves(board)

    # No legal moves: checkmate or stalemate.
    if not legal_moves:
        in_check = _gs_is_in_check(board, board.turn)
        if in_check:
            # Checkmate: large score depending on whose king is mated.
            # board.turn is the side to move (the checkmated side).
            if board.turn == Color.WHITE:
                # White is checkmated => great for Black.
                return (-MATE_SCORE, None)
            # Black is checkmated => great for White.
            return (MATE_SCORE, None)
        # Stalemate: draw.
        return (0, None)

    # Base case: reached maximum depth => raw evaluation.
    if params.depth == 0:
        score = evaluate(board)
        return (score, None)

    # Sort moves for better pruning: captures first, then promotions.
    scored_moves = _order_moves(board, legal_moves, params)

    best_score, best_move = _search_move_loop(board, legal_moves, scored_moves, params)

    return (best_score, best_move)


def _order_moves(
    board: Board,
    legal_moves: list[Move],
    params: MinimaxParams | None = None,
) -> list[MoveOrderingKey]:
    """Sort moves for better pruning order."""
    promotion_order_bonus = {
        PieceType.QUEEN: 900,
        PieceType.ROOK: 500,
        PieceType.BISHOP: 330,
        PieceType.KNIGHT: 320,
    }

    scored_moves: list[MoveOrderingKey] = []

    last_best_move = (
        params.last_best_move if params is not None else None
    )

    tt_best_move: LegalMove | None = None
    tt_entry = None
    if params is not None and params.transposition_table is not None:
        key = _position_key(board)
        tt_entry = params.transposition_table.get(key)

    if tt_entry is not None and tt_entry.best_move is not None:
        tt_best_move = tt_entry.best_move

    for move in legal_moves:
        start, end, promotion = move.start, move.end, move.promotion

        captured_piece = board.get_piece(end)
        capture_gain = (
            _captured_piece_value(captured_piece.kind)
            if captured_piece is not None
            else 0
        )

        promotion_value = 0
        if promotion is not None:
            promotion_value = promotion_order_bonus.get(promotion, 0)

        order_score = capture_gain + promotion_value

        if last_best_move is not None and (
            start == last_best_move.start
            and end == last_best_move.end
            and promotion == last_best_move.promotion
        ):
            order_score += 1000

        if tt_best_move is not None and (
            start == tt_best_move.start
            and end == tt_best_move.end
            and promotion == tt_best_move.promotion
        ):
            order_score += 2000

        move_key = MoveOrderingKey(
            score=order_score, start=start, end=end, promotion=promotion
        )
        scored_moves.append(move_key)

    return sorted(scored_moves, key=lambda x: x.score, reverse=True)


def _captured_piece_value(piece_type: PieceType) -> int:
    """Get capture value for material count."""
    values = {
        PieceType.PAWN: 5,
        PieceType.KNIGHT: 18,
        PieceType.BISHOP: 20,
        PieceType.ROOK: 35,
        PieceType.QUEEN: 60,
    }
    return values.get(piece_type, 0)


def _promotion_bonus(_end_rank: int, captured_piece: Optional[Piece]) -> int:
    """Bonus for pawn promotion (simplified)."""
    if captured_piece is None:
        return -100

    values = {
        PieceType.PAWN: 100,
        PieceType.KNIGHT: 320,
        PieceType.BISHOP: 320,
        PieceType.ROOK: 500,
        PieceType.QUEEN: 900,
    }
    return (
        values.get(captured_piece.kind if captured_piece else PieceType.PAWN, 100) - 100
    )


def get_best_move(board: Board, depth: int) -> Optional[LegalMove]:
    """Get the best move for the current position at given search depth."""
    if depth < 1:
        raise ValueError("depth must be >= 1")

    tt: dict[str, TTEntry] = {}

    best_move: LegalMove | None = None
    score = 0

    for d in range(1, depth + 1):
        # Use full-width alpha-beta for correctness.
        # Aspiration windows require fail-high/fail-low re-search.
        alpha = -INF
        beta = INF

        params = MinimaxParams(
            depth=d,
            alpha=alpha,
            beta=beta,
            is_maximizing=board.turn == Color.WHITE,
            transposition_table=tt,
            last_best_move=best_move,
        )
        legal_moves = get_legal_moves(board)
        if not legal_moves:
            return None

        score, move = minimax(board, params)
        best_move = move

    return best_move


def _position_key(board: Board) -> str:
    """Generate a position key for transposition table."""
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
    if not castling:
        castling = "-"

    if board.en_passant_target is not None:
        ep = index_to_algebraic(board.en_passant_target)
    else:
        ep = "-"

    return "".join(pieces) + "|" + turn_char + "|" + castling + "|" + ep


def _fen_key(board: Board) -> str:
    return _position_key(board)


def minimax_no_prune(
    board: Board,
    depth: int,
    is_maximizing: bool,
    nodes: Optional[list[int]] = None,
) -> int:
    """No-prune minimax reference for tests/benchmarks only.

    Does not use alpha-beta pruning.
    Uses the same terminal handling and evaluator as production search.
    """
    # Node counter for tests
    if nodes is not None:
        nodes[0] += 1

    # Generate legal moves FIRST (terminal handling before depth cutoff).
    legal_moves = get_legal_moves(board)

    # No legal moves: checkmate or stalemate.
    if not legal_moves:
        in_check = _gs_is_in_check(board, board.turn)
        if in_check:
            # Checkmate: large score depending on whose king is mated.
            if board.turn == Color.WHITE:
                return -MATE_SCORE
            else:
                return MATE_SCORE
        # Stalemate: draw.
        return 0

    # Base case: reached maximum depth => raw evaluation.
    if depth == 0:
        return evaluate(board)

    if is_maximizing:
        best = -INF
        for move in legal_moves:
            new_board = shallow_clone_board(board)
            new_board.make_move(move.start, move.end, promotion=move.promotion)
            val = minimax_no_prune(new_board, depth - 1, False, nodes)
            if val > best:
                best = val
        return best
    else:
        best = INF
        for move in legal_moves:
            new_board = shallow_clone_board(board)
            new_board.make_move(move.start, move.end, promotion=move.promotion)
            val = minimax_no_prune(new_board, depth - 1, True, nodes)
            if val < best:
                best = val
        return best
