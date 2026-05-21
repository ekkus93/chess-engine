"""Helpers for scoring quiet strategic moves during search ordering."""

from chess_game.chess.board import Board
from chess_game.chess.move import Move
from chess_game.chess.strategy_utils import center_distance, is_capture_move
from chess_game.chess.types import Color, PieceType

QUIET_CASTLING_BONUS = 160
QUIET_PASSED_PAWN_PUSH_BONUS = 90
QUIET_KING_CENTRALIZATION_BONUS = 18
QUIET_HEAVY_PIECE_PRESSURE_BONUS = 24
QUIET_CENTRALIZATION_BONUS = 12


def quiet_strategy_order_score(board: Board, move: Move) -> int:
    """Return a bonus for strong quiet strategic moves."""

    if move.promotion is not None or is_capture_move(board, move):
        return 0
    piece = board.get_piece(move.start)
    if piece is None:
        return 0
    score = _centralization_bonus(piece.kind, move)
    if piece.kind == PieceType.KING and _is_castling_move(move):
        score += QUIET_CASTLING_BONUS
    if piece.kind == PieceType.KING and _is_heavy_piece_endgame(board):
        score += _king_centralization_bonus(move)
    if piece.kind == PieceType.PAWN and _is_passed_pawn_push(board, piece.color, move):
        score += QUIET_PASSED_PAWN_PUSH_BONUS + _pawn_push_progress(piece.color, move)
    if piece.kind in (PieceType.ROOK, PieceType.QUEEN) and _lines_up_with_enemy_king(board, move):
        score += QUIET_HEAVY_PIECE_PRESSURE_BONUS
    return score


def _centralization_bonus(kind: PieceType, move: Move) -> int:
    """Return a bonus for improving piece placement toward useful squares."""

    if kind == PieceType.ROOK:
        return _line_piece_bonus(move)
    if kind == PieceType.QUEEN:
        return _line_piece_bonus(move) // 2
    if kind in (PieceType.KNIGHT, PieceType.BISHOP):
        return _minor_piece_centralization(move)
    return 0


def _line_piece_bonus(move: Move) -> int:
    """Score rook/queen moves by improving central file or rank pressure."""

    start_distance = center_distance(int(move.start.row), int(move.start.col))
    end_distance = center_distance(int(move.end.row), int(move.end.col))
    return max(0, start_distance - end_distance) * QUIET_CENTRALIZATION_BONUS


def _minor_piece_centralization(move: Move) -> int:
    """Score quiet minor-piece moves by centralization gain."""

    start_distance = center_distance(int(move.start.row), int(move.start.col))
    end_distance = center_distance(int(move.end.row), int(move.end.col))
    return max(0, start_distance - end_distance) * QUIET_CENTRALIZATION_BONUS


def _is_castling_move(move: Move) -> bool:
    """Return True for king-side or queen-side castling geometry."""

    return int(move.start.col) == 4 and abs(int(move.start.col) - int(move.end.col)) == 2


def _is_heavy_piece_endgame(board: Board) -> bool:
    """Return True in simple endings where king centralization matters more."""

    non_king_pieces = [
        piece.kind
        for row in board.board
        for piece in row
        if piece is not None and piece.kind != PieceType.KING
    ]
    return len(non_king_pieces) <= 4


def _king_centralization_bonus(move: Move) -> int:
    """Reward king steps toward the center in quiet endgames."""

    start_distance = center_distance(int(move.start.row), int(move.start.col))
    end_distance = center_distance(int(move.end.row), int(move.end.col))
    return max(0, start_distance - end_distance) * QUIET_KING_CENTRALIZATION_BONUS


def _is_passed_pawn_push(board: Board, color: Color, move: Move) -> bool:
    """Return True when a quiet pawn push advances a passed pawn candidate."""

    if int(move.start.col) != int(move.end.col):
        return False
    start_row = int(move.start.row)
    end_row = int(move.end.row)
    if color == Color.WHITE and end_row >= start_row:
        return False
    if color == Color.BLACK and end_row <= start_row:
        return False
    enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
    for row_index, row in enumerate(board.board):
        for col_index, piece in enumerate(row):
            if (
                piece is not None
                and piece.color == enemy_color
                and piece.kind == PieceType.PAWN
                and abs(col_index - int(move.end.col)) <= 1
            ):
                if color == Color.WHITE and row_index < end_row:
                    return False
                if color == Color.BLACK and row_index > end_row:
                    return False
    return True


def _pawn_push_progress(color: Color, move: Move) -> int:
    """Return a bonus scaled by how advanced the pawn push becomes."""

    end_row = int(move.end.row)
    progress = 6 - end_row if color == Color.WHITE else end_row - 1
    return progress * 4


def _lines_up_with_enemy_king(board: Board, move: Move) -> bool:
    """Return True when a heavy piece move increases pressure on the enemy king."""

    enemy_color = Color.BLACK if board.turn == Color.WHITE else Color.WHITE
    enemy_king = next(
        (
            piece.square
            for row in board.board
            for piece in row
            if piece is not None
            and piece.color == enemy_color
            and piece.kind == PieceType.KING
        ),
        None,
    )
    if enemy_king is None:
        return False
    return int(move.end.row) == int(enemy_king.row) or int(move.end.col) == int(enemy_king.col)
