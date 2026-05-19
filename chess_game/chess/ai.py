"""AI/Minimax implementation for chess engine."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Optional

from chess_game.chess.board import Board
from chess_game.chess.board.game_state import is_in_check as _gs_is_in_check
from chess_game.chess.constants import ConstantSquare
from chess_game.chess.coords import index_to_algebraic
from chess_game.chess.evaluation import (
    MATERIAL_VALUES,
    PAWN_TABLE,
    KNIGHT_TABLE,
    BISHOP_TABLE,
    ROOK_TABLE,
    QUEEN_TABLE,
    KING_TABLE,
)
from chess_game.chess.types import Color, Piece, PieceType, LegalMove
from chess_game.chess.move import Move
from chess_game.chess.constants import (
    ROW_1,
    ROW_8,
    get_row_constant,
    get_col_constant,
)

LegalMoveKey = tuple[int, LegalMove]

LegalMoveKey = tuple[int, LegalMove]


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


@dataclass
class MinimaxParams:
    """Configuration for a minimax search."""

    depth: int
    alpha: int
    beta: int
    is_maximizing: bool
    transposition_table: Optional[dict[str, LegalMoveKey]] = None


def evaluate(board: Board) -> int:
    """Evaluate the board position from White's perspective.

    Args:
        board: The current board state

    Returns:
        Positive score if White is ahead, negative if Black is ahead,
        zero if equal. Score is in "centipawn" units (1/100 of a pawn).
    """
    total_score: int = 0

    # Iterate over all squares to evaluate material + position
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

    # Material value (baseline)
    material = MATERIAL_VALUES[piece.kind]

    # Mirror row for Black so White-centric tables apply correctly
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
    """Get all legal moves for the side to move.

    Args:
        board: The current board state

    Returns:
        List of Move objects with start, end, and promotion attributes.
    """
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
    if params.transposition_table is None or params.depth >= 20:
        return None
    key = _fen_key(board) + f":d{params.depth}"
    if key not in params.transposition_table:
        return None
    return params.transposition_table[key]


def _store_tt_cache(
    board: Board,
    params: MinimaxParams,
    score: int,
    move: LegalMove,
) -> None:
    """Store a result in the transposition table."""
    if params.transposition_table is None:
        return
    key = _fen_key(board) + f":d{params.depth}"
    params.transposition_table[key] = (score, move)


def _search_move_loop(
    board: Board,
    legal_moves: list[Move],
    scored_moves: list[MoveOrderingKey],
    params: MinimaxParams,
) -> tuple[int, Optional[LegalMove]]:
    """Execute the main minimax search loop with alpha-beta pruning."""
    best_score: int = -100_000_000 if params.is_maximizing else 100_000_000
    best_move: LegalMove | None = None
    alpha, beta = params.alpha, params.beta

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
        new_board = _make_copy_with_move(board, move.start, move.end, move.promotion)

        child_params = MinimaxParams(
            depth=params.depth - 1,
            alpha=alpha,
            beta=beta,
            is_maximizing=not params.is_maximizing,
            transposition_table=params.transposition_table,
        )
        child_result = minimax(new_board, child_params)
        child_score = int(child_result[0])

        if params.is_maximizing:
            if child_score > best_score:
                best_score = child_score
                best_move = LegalMove(move.start, move.end, move.promotion)
            alpha = max(alpha, child_score)
            if alpha >= beta:
                break
        else:
            if child_score < best_score:
                best_score = child_score
                best_move = LegalMove(move.start, move.end, move.promotion)
            beta = min(beta, child_score)
            if beta <= alpha:
                break

    return (best_score, best_move)


def minimax(
    board: Board,
    params: MinimaxParams,
) -> tuple[int, Optional[LegalMove]]:
    """Standard minimax with alpha-beta pruning.

    Args:
        board: The current board state
        params: Search configuration containing depth, alpha/beta bounds,
                maximizing flag, and optional transposition table.

    Returns:
        Tuple of (best_score, best_move). Best move may be None at leaf nodes.
    """
    # Check transposition table
    cached = _check_tt_cache(board, params)
    if cached is not None:
        return cached

    # Base case: reached maximum depth
    if params.depth == 0:
        score = evaluate(board)
        return (max(params.alpha, min(score, params.beta)) if params.is_maximizing else min(params.beta, max(score, params.alpha)), None)

    # Check for game-over states (no legal moves)
    legal_moves = get_legal_moves(board)
    if not legal_moves:
        # If in check -> checkmate; else stalemate
        in_check = _gs_is_in_check(board, board.turn)
        if in_check:
            # Checkmate: extreme value depending on side to move
            val = -100_000_000 if params.is_maximizing else 100_000_000
            return (val, None)
        else:
            # Stalemate: draw
            return (0, None)

    # Sort moves for better pruning: captures first, then promotions
    scored_moves = _order_moves(board, legal_moves)

    if not scored_moves:
        score = evaluate(board)
        if params.transposition_table is not None:
            _store_tt_cache(board, params, score, None)  # type: ignore[arg-type]
        return (score, None)

    best_score, best_move = _search_move_loop(board, legal_moves, scored_moves, params)

    # Store in transposition table only if we found a move
    if best_move is not None:
        _store_tt_cache(board, params, best_score, best_move)

    return (best_score, best_move)


def _order_moves(
    board: Board,
    legal_moves: list[Move],
) -> list[MoveOrderingKey]:
    """Sort moves for better pruning order.

    Move ordering strategy:
    1. Captures (especially high-value piece captures)
    2. Promotions
    3. Pawn pushes to empty squares
    4. Normal moves

    Args:
        board: The current board state
        legal_moves: List of all legal moves to order

    Returns:
        Sorted list of MoveOrderingKey objects with ConstantSquare start/end.
    """
    scored_moves: list[MoveOrderingKey] = []

    for move in legal_moves:
        start, end, promotion = move.start, move.end, move.promotion

        # Calculate capture gain if applicable (scaled down to avoid dominating)
        captured_piece = board.get_piece(end)
        capture_gain = (
            _captured_piece_value(captured_piece.kind)
            if captured_piece is not None
            else 0
        )

        # Bonus for promotion
        promoted_to = end.row in (ROW_1, ROW_8) and board.get_piece(start) is not None
        promotion_value = 25 if promoted_to else 0

        # Combine factors into ordering score
        order_score = capture_gain + promotion_value

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

    # Promotion + capture is excellent
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
    """Get the best move for the current position at given search depth.

    Args:
        board: The current board state
        depth: Search depth in plies. Evaluation always occurs after
               the opponent's move when using odd depths (recommended).

    Returns:
        Best legal move, or None if no moves exist.
    """
    # Create a transposition table to cache positions
    tt: dict[str, LegalMoveKey] = {}

    params = MinimaxParams(
        depth=depth,
        alpha=-10_000_000,
        beta=10_000_000,
        is_maximizing=board.turn == Color.WHITE,
        transposition_table=tt,
    )
    legal_moves = get_legal_moves(board)

    if not legal_moves:
        return None

    # Run minimax with alpha-beta pruning
    _, best_move = minimax(board, params)

    return best_move


def _fen_key(board: Board) -> str:
    """Generate a lightweight FEN-like key for transposition table.

    Includes board placement, side to move, castling rights, and en passant target
    to ensure distinct positions produce distinct keys.
    """
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
