from __future__ import annotations

from chess_game.chess.board import Board, ConstantSquare, create_piece
from chess_game.chess.types import Color, PieceType
from chess_game.constants import (
    COL_A,
    COL_D,
    COL_E,
    ROW_1,
    ROW_2,
    ROW_3,
    ROW_4,
    ROW_5,
    ROW_6,
    ROW_7,
    ROW_8,
)


def test_starting_position_key_squares() -> None:
    board = Board()

    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_1, col=COL_A)) == PieceType.ROOK
    )
    assert board.get_color_at(ConstantSquare(row=ROW_1, col=COL_A)) == Color.WHITE

    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_1, col=COL_E)) == PieceType.KING
    )
    assert board.get_color_at(ConstantSquare(row=ROW_1, col=COL_E)) == Color.WHITE

    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_1, col=COL_D)) == PieceType.QUEEN
    )
    assert board.get_color_at(ConstantSquare(row=ROW_1, col=COL_D)) == Color.WHITE

    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_8, col=COL_A)) == PieceType.ROOK
    )
    assert board.get_color_at(ConstantSquare(row=ROW_8, col=COL_A)) == Color.BLACK

    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_8, col=COL_E)) == PieceType.KING
    )
    assert board.get_color_at(ConstantSquare(row=ROW_8, col=COL_E)) == Color.BLACK

    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_8, col=COL_D)) == PieceType.QUEEN
    )
    assert board.get_color_at(ConstantSquare(row=ROW_8, col=COL_D)) == Color.BLACK

    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_2, col=COL_E)) == PieceType.PAWN
    )
    assert board.get_color_at(ConstantSquare(row=ROW_2, col=COL_E)) == Color.WHITE


def test_get_set_and_clear_square_helpers(empty_board: Board) -> None:
    empty_board.set_piece(
        ConstantSquare(row=ROW_4, col=COL_E),
        create_piece(Color.WHITE, PieceType.KNIGHT),
    )

    assert (
        empty_board.get_piece_type_at(ConstantSquare(row=ROW_4, col=COL_E))
        == PieceType.KNIGHT
    )
    assert empty_board.get_color_at(ConstantSquare(row=ROW_4, col=COL_E)) == Color.WHITE

    empty_board.clear_square(ConstantSquare(row=ROW_4, col=COL_E))

    assert empty_board.get_piece(ConstantSquare(row=ROW_4, col=COL_E)) is None


def test_clone_creates_independent_copy(board_with_kings: Board) -> None:
    board_with_kings.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )

    cloned = board_with_kings.clone()

    cloned.make_move(
        ConstantSquare(row=ROW_2, col=COL_E), ConstantSquare(row=ROW_4, col=COL_E)
    )

    assert (
        board_with_kings.get_piece_type_at(ConstantSquare(row=ROW_2, col=COL_E))
        == PieceType.PAWN
    )
    assert board_with_kings.get_piece(ConstantSquare(row=ROW_4, col=COL_E)) is None


def test_find_king_returns_expected_square(board_with_kings: Board) -> None:
    assert board_with_kings.find_king(Color.WHITE) == ConstantSquare(
        row=ROW_7, col=COL_E
    )
    assert board_with_kings.find_king(Color.BLACK) == ConstantSquare(
        row=ROW_8, col=COL_E
    )
