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

# Increase recursion limit for deep search
sys.setrecursionlimit(50000)

LegalMoveKey = tuple[int, LegalMove]

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
class MinimaxParams:
    """Configuration for a minimax search."""

    depth: int
    alpha: int
    beta: int
    is_maximizing: bool
    transposition_table: Optional[dict[str, TTEntry]] = None
    last_best_move: Optional[LegalMove] = None
    nodes_searched: Optional[list[int]] = None  # for tests; only used when set


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


# Undo-based move application for fast search (no clone)

def apply_move_for_search(
    board: Board,
    start: ConstantSquare,
    end: ConstantSquare,
    promotion: Optional[PieceType],
) -> dict:
    """Apply a move on the board in-place for search.

    Returns a snapshot dict that can be used to undo the move.
    Assumes the move is already known to be legal.
    """
    piece = board.get_piece(start)
    if not piece:
        raise RuntimeError(
            f"apply_move_for_search: no piece at start {start}, end {end}, promotion {promotion}"
        )

    info: dict = {}

    # Save pre-move values that must be restored on undo
    info["from_piece"] = piece  # piece object reference
    info["to_piece_before"] = board.get_piece(end)
    info["turn_before"] = board.turn

    # En passant
    info["ep_before"] = board.en_passant_target

    # Castling rights snapshot (we'll restore them on undo)
    cr = board.castling_rights
    info["cr_before"] = type(cr)(
        white_kingside=cr.white_kingside,
        white_queenside=cr.white_queenside,
        black_kingside=cr.black_kingside,
        black_queenside=cr.black_queenside,
    )

    # En passant capture
    ep_captured = None
    if piece.kind == PieceType.PAWN and board.en_passant_target == end:
        # Captured pawn square is same rank as start, same file as end
        ep_captured = ConstantSquare(
            row=start.row,
            col=end.col,
        )
        ep_captured_piece = board.get_piece(ep_captured)
        info["ep_captured_sq"] = ep_captured
        info["ep_captured_piece"] = ep_captured_piece
        board.board[int(ep_captured.row)][int(ep_captured.col)] = None

    # Castling
    is_castling = (
        piece.kind == PieceType.KING
        and (end.col - start.col) not in (-1, 0, 1)
    )

    # Castling rook move tracking
    info["rook_from"] = None
    info["rook_to"] = None
    info["rook_piece"] = None
    if is_castling:
        r = int(start.row)
        if end.col == 6:  # kingside
            rook_from = ConstantSquare(row=start.row, col=7)
            rook_to = ConstantSquare(row=start.row, col=5)
        else:  # queenside, end.col == 2
            rook_from = ConstantSquare(row=start.row, col=0)
            rook_to = ConstantSquare(row=start.row, col=3)
        rook = board.get_piece(rook_from)
        info["rook_from"] = rook_from
        info["rook_to"] = rook_to
        info["rook_piece"] = rook

        board.board[r][int(rook_to.col)] = rook
        board.board[r][int(rook_from.col)] = None
        if rook:
            rook.square = rook_to

    # Promotion
    info["promotion"] = promotion
    if piece.kind == PieceType.PAWN and end.row in (ROW_1, ROW_8):
        prom = promotion or QUEEN_TABLE  # fallback (should never occur)
        # Normalize to PieceType
        if isinstance(prom, int):
            prom = PieceType.PAWN  # safe default; won't happen if logic correct
        # Actually: promotion is PieceType (from move.promotion)
        # We'll treat it as PieceType directly.

    # Move piece
    board.board[int(end.row)][int(end.col)] = piece
    piece.square = end

    # Capture / clear
    board.board[int(start.row)][int(start.col)] = None

    # Handle promotion
    if piece.kind == PieceType.PAWN and end.row in (ROW_1, ROW_8):
        prom_kind = promotion
        if not prom_kind:
            # default queen if missing
            prom_kind = PieceType.QUEEN

        new_piece = Piece(piece.color, prom_kind, end)
        board.board[int(end.row)][int(end.col)] = new_piece
        piece.square = end

    # Update castling rights
    # King move -> clear both for that color
    if piece.kind == PieceType.KING:
        c = piece.color
        if c == Color.WHITE:
            board.castling_rights.white_kingside = False
            board.castling_rights.white_queenside = False
        else:
            board.castling_rights.black_kingside = False
            board.castling_rights.black_queenside = False

    # Rook move from home square
    if piece.kind == PieceType.ROOK:
        c = piece.color
        r = int(start.row)
        if c == Color.WHITE:
            if r == 7 and start.col == 0:
                board.castling_rights.white_queenside = False
            elif r == 7 and start.col == 7:
                board.castling_rights.white_kingside = False
        else:
            if r == 0 and start.col == 0:
                board.castling_rights.black_queenside = False
            elif r == 0 and start.col == 7:
                board.castling_rights.black_kingside = False

    # If landing on rook home square, clear opponent castling right
    r, _ = int(end.row), int(end.col)
    if end.row == ROW_8 and end.col == 0:
        board.castling_rights.black_queenside = False
    elif end.row == ROW_8 and end.col == 7:
        board.castling_rights.black_kingside = False
    elif end.row == ROW_1 and end.col == 0:
        board.castling_rights.white_queenside = False
    elif end.row == ROW_1 and end.col == 7:
        board.castling_rights.white_kingside = False

    # En passant target
    board.en_passant_target = None
    if piece.kind == PieceType.PAWN and (end.row - start.row) in (-2, 2):
        # Valid en passant target: square between start and end
        ep = ConstantSquare(
            row=end.row,
            col=end.col,
        )
        # Only set if opponent has a pawn that can capture en passant
        # (We keep it simple and mirror board logic.)
        board.en_passant_target = ep

    # Switch turn
    board.turn = Color.BLACK if board.turn == Color.WHITE else Color.WHITE

    return info


def unapply_move_for_search(board: Board, info: dict) -> None:
    """Undo a move that was applied with apply_move_for_search."""
    piece = info["from_piece"]
    start = piece.square  # temporary; we restore square below

    # Restore board squares
    board.board[int(start.row)][int(start.col)] = piece
    piece.square = start

    # Restore captured piece
    info.get("to_piece_before")

    # Restore en passant captured pawn
    ep_captured = info.get("ep_captured")
    if ep_captured is not None:
        ep_captured_piece = info["ep_captured_piece"]
        board.board[int(ep_captured.row)][int(ep_captured.col)] = ep_captured_piece

    # Restore rook for castling
    rook_from = info.get("rook_from")
    rook_to = info.get("rook_to")
    rook_piece = info.get("rook_piece")
    if rook_from is not None and rook_to is not None and rook_piece is not None:
        board.board[int(rook_from.row)][int(rook_from.col)] = rook_piece
        rook_piece.square = rook_from

    # Restore castling rights
    cr_before = info["cr_before"]
    board.castling_rights = cr_before

    # Restore en passant target
    board.en_passant_target = info["ep_before"]

    # Restore turn
    board.turn = info["turn_before"]


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
    tt = params.transposition_table
    if not tt:
        return None

    key = _position_key(board) + f":d{params.depth}"
    if key not in tt:
        return None

    entry = tt[key]
    # Only use cached result if depth is sufficient.
    if entry.depth < params.depth:
        return None

    score = entry.score
    alpha = params.alpha
    beta = params.beta

    # TSCP-style lookup:
    if entry.flag == TTFlag.EXACT:
        return (score, entry.best_move)
    if entry.flag == TTFlag.LOWERBOUND:
        alpha = max(alpha, score)
    elif entry.flag == TTFlag.UPPERBOUND:
        beta = min(beta, score)

    if alpha >= beta:
        return (score, entry.best_move)

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
    key = _position_key(board) + f":d{params.depth}"

    # Determine flag based on original alpha/beta
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

    # Only overwrite if no entry or new depth >= existing depth
    existing = tt.get(key)
    if existing is None or params.depth >= existing.depth:
        tt[key] = entry


def shallow_clone_board(board: Board) -> Board:
    """Create a shallow clone of board for search (no deepcopy).

    This copies the board array (row lists) and creates new Piece instances
    to avoid mutating shared state. Fast enough for alpha-beta search at depth 5.
    """
    new_board = Board.__new__(Board)

    # Deep copy the board array with new Piece instances
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
    alpha, beta = params.alpha, params.beta

    # Save original alpha/beta for TT flag calculation.
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

        # Use shallow clone + make_move for correctness and speed
        new_board = shallow_clone_board(board)
        new_board.make_move(move.start, move.end, promotion=move.promotion)

        child_params = MinimaxParams(
            depth=params.depth - 1,
            alpha=alpha,
            beta=beta,
            is_maximizing=not params.is_maximizing,
            transposition_table=params.transposition_table,
            nodes_searched=params.nodes_searched,
        )
        child_result = minimax(new_board, child_params)
        child_score = int(child_result[0])

        # Alpha-beta pruning: if score exceeds bounds, prune remaining moves
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

    # Store in TT using original alpha/beta.
    _store_tt_cache(board, params, best_score, best_move, alpha_orig, beta_orig)

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
    # Node counter for tests (no-op when not used)
    if params.nodes_searched is not None:
        params.nodes_searched[0] += 1

    # Check transposition table
    cached = _check_tt_cache(board, params)
    if cached is not None:
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

    # Store in transposition table only if we found a move.
    if best_move is not None:
        _store_tt_cache(board, params, best_score, best_move, params.alpha, params.beta)

    return (best_score, best_move)


def _order_moves(
    board: Board,
    legal_moves: list[Move],
    params: MinimaxParams | None = None,
) -> list[MoveOrderingKey]:
    """Sort moves for better pruning order.

    Move ordering strategy:
    1. Best move from previous search or TT.
    2. Captures (especially high-value piece captures).
    3. Promotions (use promotion.promotion, not rank-based heuristic).
    4. Normal moves.

    Args:
        board: The current board state
        legal_moves: List of all legal moves to order
        params: Optional MinimaxParams for previous best move

    Returns:
        Sorted list of MoveOrderingKey objects with ConstantSquare start/end.
    """
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

    for move in legal_moves:
        start, end, promotion = move.start, move.end, move.promotion

        # Calculate capture gain if applicable (scaled down to avoid dominating)
        captured_piece = board.get_piece(end)
        capture_gain = (
            _captured_piece_value(captured_piece.kind)
            if captured_piece is not None
            else 0
        )

        # Promotion bonus based on move.promotion (not rank-based)
        promotion_value = 0
        if promotion is not None:
            promotion_value = promotion_order_bonus.get(promotion, 0)

        # Combine factors into ordering score
        order_score = capture_gain + promotion_value

        # Prioritize last best move or TT-suggested move
        if last_best_move is not None and (
            start == last_best_move.start
            and end == last_best_move.end
            and promotion == last_best_move.promotion
        ):
            order_score += 1000

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

    Raises:
        ValueError if depth < 1.
    """
    if depth < 1:
        raise ValueError("depth must be >= 1")

    # Use iterative deepening to gradually increase depth
    tt: dict[str, TTEntry] = {}

    best_move: LegalMove | None = None
    score = 0  # For iterative deepening window

    for d in range(1, depth + 1):
        # Use a wider window around last best score for iterative deepening
        alpha = score - 1000
        beta = score + 1000

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

        # Run minimax with alpha-beta pruning
        score, move = minimax(board, params)
        best_move = move

    return best_move


def _position_key(board: Board) -> str:
    """Generate a position key for transposition table.

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


# Compatibility wrapper (no-op) if external callers expect _fen_key.
def _fen_key(board: Board) -> str:
    return _position_key(board)
