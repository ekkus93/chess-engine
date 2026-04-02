from __future__ import annotations
from chess_game.chess.board import Board, ConstantSquare, create_piece
from chess_game.chess.types import Color, PieceType
from chess_game.chess.constants import (
    get_row_constant,
    get_col_constant,
    COL_A,
    COL_B,
    COL_C,
    COL_D,
    COL_E,
    COL_F,
    COL_G,
    COL_H,
    ROW_1,
    ROW_2,
    ROW_3,
    ROW_4,
    ROW_5,
    ROW_6,
    ROW_7,
    ROW_8,
    ROW_0,
)


def clear_board(board: Board) -> None:
    for row in range(8):
        for col in range(8):
            board.clear_square(
                ConstantSquare(row=get_row_constant(row), col=get_col_constant(col))
            )


def test_rook_attack_on_open_file_and_rank() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(4, 4), create_piece(Color.WHITE, PieceType.ROOK)
    )
    assert (
        board.is_square_attacked(get_square_constant(4, 0), Color.WHITE)
        is True
    )  # Same rank as rook (ROW_5)
    assert (
        board.is_square_attacked(get_square_constant(4, 7), Color.WHITE)
        is True
    )  # Same rank as rook (ROW_5)


def test_bishop_attack_on_open_diagonal() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(4, 4),
        create_piece(Color.WHITE, PieceType.BISHOP),
    )
    assert (
        board.is_square_attacked(get_square_constant(7, 7), Color.WHITE)
        is True
    )  # Diagonal from E5: E5->F6->G7->H8


def test_knight_attack() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(4, 4),
        create_piece(Color.WHITE, PieceType.KNIGHT),
    )
    assert (
        board.is_square_attacked(get_square_constant(2, 3), Color.WHITE)
        is True
    )  # Knight moves: (4,4) -> (2,3) = C5 or (3,2) = D3 or (5,2) = D7


def test_pawn_attack_squares_for_white() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(1, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )
    assert (
        board.is_square_attacked(get_square_constant(2, 3), Color.WHITE)
        is True
    )
    assert (
        board.is_square_attacked(get_square_constant(2, 5), Color.WHITE)
        is True
    )
    assert (
        board.is_square_attacked(get_square_constant(0, 4), Color.WHITE)
        is False
    )


def test_pawn_attack_squares_for_black() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.PAWN)
    )
    assert (
        board.is_square_attacked(get_square_constant(6, 3), Color.BLACK)
        is True
    )
    assert (
        board.is_square_attacked(get_square_constant(6, 5), Color.BLACK)
        is True
    )
    assert (
        board.is_square_attacked(get_square_constant(1, 4), Color.BLACK)
        is False
    )


def test_king_adjacent_attack() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(4, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    assert (
        board.is_square_attacked(get_square_constant(5, 5), Color.WHITE)
        is True
    )


def test_simple_check_by_rook() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.ROOK)
    )
    assert board.is_in_check(Color.WHITE) is True


def test_simple_check_by_bishop() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(4, 0),
        create_piece(Color.BLACK, PieceType.BISHOP),
    )
    assert board.is_in_check(Color.WHITE) is True


def test_simple_check_by_knight() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(2, 5),
        create_piece(Color.BLACK, PieceType.KNIGHT),
    )
    assert board.is_in_check(Color.WHITE) is True


def test_simple_check_by_queen() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 0), create_piece(Color.BLACK, PieceType.QUEEN)
    )
    assert board.is_in_check(Color.WHITE) is True


def test_pinned_piece_cannot_move_exposing_king() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(2, 4), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.ROOK)
    )
    assert (
        board.make_move(
            get_square_constant(2, 4), get_square_constant(6, 5)
        )
        is False
    )


def test_king_cannot_move_into_check() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.ROOK)
    )
    assert (
        board.make_move(
            get_square_constant(0, 4), get_square_constant(6, 4)
        )
        is False
    )


def test_blocking_a_check_is_allowed() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(2, 4), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.set_piece(
        get_square_constant(1, 3), create_piece(Color.WHITE, PieceType.PAWN)
    )
    assert (
        board.make_move(
            get_square_constant(1, 3), get_square_constant(2, 4)
        )
        is True
    )


def test_capturing_checking_piece_is_allowed_when_resolves_check() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(1, 4), create_piece(Color.BLACK, PieceType.ROOK)
    )
    assert (
        board.make_move(
            get_square_constant(0, 4), get_square_constant(1, 4)
        )
        is True
    )
