from __future__ import annotations
from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType
from chess_game.chess.constants import (
    get_row_constant,
    get_col_constant,
    ROW_1,
    ROW_2,
    ROW_3,
    ROW_4,
    ROW_5,
    ROW_6,
    ROW_7,
    ROW_8,
    COL_A,
    COL_B,
    COL_C,
    COL_D,
    COL_E,
    COL_F,
    COL_G,
    COL_H,
    ConstantSquare,
)


def clear_board(board: Board) -> None:
    for row in range(8):
        for col in range(8):
            board.clear_square(
                ConstantSquare(row=get_row_constant(row), col=get_col_constant(col))
            )


def test_start_position_has_expected_white_legal_moves() -> None:
    board = Board()
    legal_moves = board.get_legal_moves(Color.WHITE)
    assert len(legal_moves) == 20
    assert (
        get_square_constant(1, 3),
        get_square_constant(3, 3),
        None,
    ) in legal_moves
    # f2-f3: from f2 (row 1, col 6) to f3 (row 2, col 6)
    assert (
        get_square_constant(1, 5),
        get_square_constant(2, 5),
        None,
    ) in legal_moves


def test_fools_mate_is_checkmate_for_white() -> None:
    board = Board()
    assert (
        board.make_move(
            get_square_constant(1, 5), get_square_constant(2, 5)
        )
        is True
    )  # f2f3
    assert (
        board.make_move(
            get_square_constant(6, 4), get_square_constant(4, 4)
        )
        is True
    )  # e7e5
    assert (
        board.make_move(
            get_square_constant(1, 6), get_square_constant(3, 6)
        )
        is True
    )  # g2g4
    assert (
        board.make_move(
            get_square_constant(7, 3), get_square_constant(3, 7)
        )
        is True
    )  # Qd8h4#
    assert board.turn == Color.WHITE
    assert board.is_in_check(Color.WHITE) is True
    assert board.is_checkmate(Color.WHITE) is True


def test_in_check_with_one_escape_is_not_checkmate() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 7), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 3), create_piece(Color.BLACK, PieceType.KING)
    )
    # Queen on d5 checks h1 (diagonal from d5 to h1)
    board.set_piece(
        get_square_constant(4, 3), create_piece(Color.BLACK, PieceType.QUEEN)
    )
    board.turn = Color.WHITE
    assert board.is_in_check(Color.WHITE) is True
    assert board.is_checkmate(Color.WHITE) is False


def test_classic_stalemate_position() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 7), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(1, 5), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(2, 6), create_piece(Color.BLACK, PieceType.QUEEN)
    )
    board.turn = Color.WHITE
    assert board.is_in_check(Color.WHITE) is False
    assert board.is_stalemate(Color.WHITE) is True


def test_not_stalemate_when_one_legal_move_exists() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 7), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(1, 5), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(3, 6), create_piece(Color.BLACK, PieceType.QUEEN)
    )
    board.turn = Color.WHITE
    assert board.is_in_check(Color.WHITE) is False
    assert board.is_stalemate(Color.WHITE) is False
    assert len(board.get_legal_moves(Color.WHITE)) == 1
