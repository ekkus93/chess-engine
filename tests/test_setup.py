from __future__ import annotations

from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType


def test_starting_position_key_squares() -> None:
    board = Board()

    assert board.get_piece_type_at(7, 0) == PieceType.ROOK
    assert board.get_color_at(7, 0) == Color.WHITE

    assert board.get_piece_type_at(7, 4) == PieceType.KING
    assert board.get_color_at(7, 4) == Color.WHITE

    assert board.get_piece_type_at(7, 3) == PieceType.QUEEN
    assert board.get_color_at(7, 3) == Color.WHITE

    assert board.get_piece_type_at(0, 0) == PieceType.ROOK
    assert board.get_color_at(0, 0) == Color.BLACK

    assert board.get_piece_type_at(0, 4) == PieceType.KING
    assert board.get_color_at(0, 4) == Color.BLACK

    assert board.get_piece_type_at(0, 3) == PieceType.QUEEN
    assert board.get_color_at(0, 3) == Color.BLACK

    assert board.get_piece_type_at(6, 4) == PieceType.PAWN
    assert board.get_color_at(6, 4) == Color.WHITE

    assert board.get_piece_type_at(1, 4) == PieceType.PAWN
    assert board.get_color_at(1, 4) == Color.BLACK


def test_get_set_and_clear_square_helpers(empty_board: Board) -> None:
    empty_board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.KNIGHT))

    assert empty_board.get_piece_type_at(4, 4) == PieceType.KNIGHT
    assert empty_board.get_color_at(4, 4) == Color.WHITE

    empty_board.clear_square(4, 4)

    assert empty_board.get_piece(4, 4) is None


def test_clone_creates_independent_copy(board_with_kings: Board) -> None:
    board_with_kings.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))

    cloned = board_with_kings.clone()
    cloned.make_move((6, 4), (4, 4))

    assert board_with_kings.get_piece_type_at(6, 4) == PieceType.PAWN
    assert board_with_kings.get_piece(4, 4) is None


def test_find_king_returns_expected_square(board_with_kings: Board) -> None:
    assert board_with_kings.find_king(Color.WHITE) == (7, 4)
    assert board_with_kings.find_king(Color.BLACK) == (0, 4)
