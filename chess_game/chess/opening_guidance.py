"""Lightweight opening move preferences for very early move-order sanity."""

from chess_game.chess.board import Board
from chess_game.chess.move import Move
from chess_game.chess.opening_development import undeveloped_minor_piece_count
from chess_game.chess.types import Color, PieceType

OPENING_GUIDANCE_BONUSES = {
    PieceType.PAWN: 14,
    PieceType.KNIGHT: 18,
    PieceType.BISHOP: 12,
}

_OPENING_GUIDANCE_PATTERNS = {
    Color.WHITE: {
        PieceType.PAWN: {
            ((6, 4), (4, 4)),  # e2-e4
            ((6, 3), (4, 3)),  # d2-d4
            ((6, 2), (4, 2)),  # c2-c4
            ((6, 6), (5, 6)),  # g2-g3
            ((6, 1), (5, 1)),  # b2-b3
        },
        PieceType.KNIGHT: {
            ((7, 6), (5, 5)),  # g1-f3
            ((7, 1), (5, 2)),  # b1-c3
        },
        PieceType.BISHOP: {
            ((7, 5), (4, 2)),  # f1-c4
            ((7, 5), (3, 1)),  # f1-b5
            ((7, 5), (6, 6)),  # f1-g2
            ((7, 2), (4, 5)),  # c1-f4
            ((7, 2), (3, 6)),  # c1-g5
            ((7, 2), (6, 1)),  # c1-b2
        },
    },
    Color.BLACK: {
        PieceType.PAWN: {
            ((1, 4), (3, 4)),  # e7-e5
            ((1, 3), (3, 3)),  # d7-d5
            ((1, 2), (3, 2)),  # c7-c5
            ((1, 6), (2, 6)),  # g7-g6
            ((1, 1), (2, 1)),  # b7-b6
        },
        PieceType.KNIGHT: {
            ((0, 6), (2, 5)),  # g8-f6
            ((0, 1), (2, 2)),  # b8-c6
        },
        PieceType.BISHOP: {
            ((0, 5), (3, 2)),  # f8-c5
            ((0, 5), (4, 1)),  # f8-b4
            ((0, 5), (1, 6)),  # f8-g7
            ((0, 2), (3, 5)),  # c8-f5
            ((0, 2), (4, 6)),  # c8-g4
            ((0, 2), (1, 1)),  # c8-b7
        },
    },
}


def opening_guidance_bonus(
    board: Board,
    color: Color,
    kind: PieceType,
    move: Move,
) -> int:
    """Return a small fixed bonus for classical early developing moves."""

    if not _opening_guidance_active(board, color):
        return 0
    patterns = _OPENING_GUIDANCE_PATTERNS[color].get(kind)
    if patterns is None:
        return 0
    geometry = (
        (int(move.start.row), int(move.start.col)),
        (int(move.end.row), int(move.end.col)),
    )
    if geometry not in patterns:
        return 0
    return OPENING_GUIDANCE_BONUSES[kind]


def _opening_guidance_active(board: Board, color: Color) -> bool:
    king_square = board.find_king(color)
    enemy_king = board.find_king(Color.BLACK if color == Color.WHITE else Color.WHITE)
    home_row = 7 if color == Color.WHITE else 0
    enemy_home_row = 0 if color == Color.WHITE else 7
    return (
        undeveloped_minor_piece_count(board, color) >= 3
        and king_square is not None
        and enemy_king is not None
        and int(king_square.row) == home_row
        and int(king_square.col) == 4
        and int(enemy_king.row) == enemy_home_row
        and int(enemy_king.col) == 4
        and _both_queens_on_board(board)
    )


def _both_queens_on_board(board: Board) -> bool:
    return (
        _piece_exists(board, Color.WHITE, PieceType.QUEEN)
        and _piece_exists(board, Color.BLACK, PieceType.QUEEN)
    )


def _piece_exists(board: Board, color: Color, kind: PieceType) -> bool:
    for row in board.board:
        for piece in row:
            if piece is not None and piece.color == color and piece.kind == kind:
                return True
    return False
