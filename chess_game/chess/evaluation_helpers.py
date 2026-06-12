"""Shared low-level helpers for board evaluation.

Extracted from ``evaluation``. Small board-query primitives (piece iteration, king
location, color/castling helpers) used across several evaluation components and by
the extracted component modules. ``evaluation`` re-imports the ones it uses.
"""

from __future__ import annotations

from collections.abc import Iterator

from chess_game.chess.board import Board
from chess_game.chess.constants import ConstantSquare
from chess_game.chess.types import Color, Piece, PieceType


def _iter_board_pieces(board: Board) -> Iterator[tuple[Piece, int, int]]:
    for row_index, row in enumerate(board.board):
        for col_index, piece in enumerate(row):
            if piece is not None:
                yield piece, row_index, col_index

def _iter_color_pieces(board: Board, color: Color):
    for piece, row, col in _iter_board_pieces(board):
        if piece.color == color:
            yield piece, row, col

def _color_sign(color: Color) -> int:
    return 1 if color == Color.WHITE else -1

def _find_king(board: Board, color: Color) -> ConstantSquare | None:
    for piece, _, _ in _iter_board_pieces(board):
        if (
            piece.color == color
            and piece.kind == PieceType.KING
            and isinstance(piece.square, ConstantSquare)
        ):
            return piece.square
    return None

def _is_castled_king(color: Color, square: ConstantSquare) -> bool:
    row = int(square.row)
    col = int(square.col)
    return (color == Color.WHITE and row == 7 and col in {2, 6}) or (
        color == Color.BLACK and row == 0 and col in {2, 6}
    )

def _opponent(color: Color) -> Color:
    return Color.BLACK if color == Color.WHITE else Color.WHITE
