from __future__ import annotations
from chess_game.chess.board import Board, ConstantSquare, create_piece
from chess_game.chess.types import Color, PieceType
from chess_game.chess.constants import (
    
        get_row_constant,
        get_col_constant,
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
        board.get_piece_type_at(get_square_constant(0, 0)) == PieceType.ROOK
    )
    assert board.get_color_at(get_square_constant(0, 0)) == Color.WHITE
    assert (
        board.get_piece_type_at(get_square_constant(0, 4)) == PieceType.KING
    )
    assert board.get_color_at(get_square_constant(0, 4)) == Color.WHITE
    assert (
        board.get_piece_type_at(get_square_constant(0, 3)) == PieceType.QUEEN
    )
    assert board.get_color_at(get_square_constant(0, 3)) == Color.WHITE
    assert (
        board.get_piece_type_at(get_square_constant(7, 0)) == PieceType.ROOK
    )
    assert board.get_color_at(get_square_constant(7, 0)) == Color.BLACK
    assert (
        board.get_piece_type_at(get_square_constant(7, 4)) == PieceType.KING
    )
    assert board.get_color_at(get_square_constant(7, 4)) == Color.BLACK
    assert (
        board.get_piece_type_at(get_square_constant(7, 3)) == PieceType.QUEEN
    )
    assert board.get_color_at(get_square_constant(7, 3)) == Color.BLACK
    assert (
        board.get_piece_type_at(get_square_constant(1, 4)) == PieceType.PAWN
    )
    assert board.get_color_at(get_square_constant(1, 4)) == Color.WHITE
def test_get_set_and_clear_square_helpers(empty_board: Board) -> None:
    empty_board.set_piece(
        get_square_constant(3, 4),
        create_piece(Color.WHITE, PieceType.KNIGHT),
    )
    assert (
        empty_board.get_piece_type_at(get_square_constant(3, 4))
        == PieceType.KNIGHT
    )
    assert empty_board.get_color_at(get_square_constant(3, 4)) == Color.WHITE
    empty_board.clear_square(get_square_constant(3, 4))
    assert empty_board.get_piece(get_square_constant(3, 4)) is None
def test_clone_creates_independent_copy(board_with_kings: Board) -> None:
    board_with_kings.set_piece(
        get_square_constant(1, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )
    cloned = board_with_kings.clone()
    cloned.make_move(
        get_square_constant(1, 4), get_square_constant(3, 4)
    )
    assert (
        board_with_kings.get_piece_type_at(get_square_constant(1, 4))
        == PieceType.PAWN
    )
    assert board_with_kings.get_piece(get_square_constant(3, 4)) is None
def test_find_king_returns_expected_square(board_with_kings: Board) -> None:
    assert board_with_kings.find_king(Color.WHITE) == ConstantSquare(
        row=ROW_1, col=COL_E
    )
    assert board_with_kings.find_king(Color.BLACK) == ConstantSquare(
        row=ROW_8, col=COL_E
    )
