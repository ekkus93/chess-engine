from __future__ import annotations

from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType


def clear_board(board: Board) -> None:
    for row in range(8):
        for col in range(8):
            board.clear_square(row, col)


def test_rook_attack_on_open_file_and_rank() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.ROOK))

    assert board.is_square_attacked((4, 0), Color.WHITE) is True
    assert board.is_square_attacked((0, 4), Color.WHITE) is True


def test_bishop_attack_on_open_diagonal() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.BISHOP))

    assert board.is_square_attacked((1, 1), Color.WHITE) is True


def test_knight_attack() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.KNIGHT))

    assert board.is_square_attacked((2, 3), Color.WHITE) is True


def test_pawn_attack_squares_for_white() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))

    assert board.is_square_attacked((5, 3), Color.WHITE) is True
    assert board.is_square_attacked((5, 5), Color.WHITE) is True
    assert board.is_square_attacked((5, 4), Color.WHITE) is False


def test_pawn_attack_squares_for_black() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(1, 4, create_piece(Color.BLACK, PieceType.PAWN))

    assert board.is_square_attacked((2, 3), Color.BLACK) is True
    assert board.is_square_attacked((2, 5), Color.BLACK) is True
    assert board.is_square_attacked((2, 4), Color.BLACK) is False


def test_king_adjacent_attack() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.KING))

    assert board.is_square_attacked((5, 5), Color.WHITE) is True


def test_simple_check_by_rook() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.ROOK))

    assert board.is_in_check(Color.WHITE) is True


def test_simple_check_by_bishop() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(4, 1, create_piece(Color.BLACK, PieceType.BISHOP))

    assert board.is_in_check(Color.WHITE) is True


def test_simple_check_by_knight() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(5, 5, create_piece(Color.BLACK, PieceType.KNIGHT))

    assert board.is_in_check(Color.WHITE) is True


def test_simple_check_by_queen() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(7, 0, create_piece(Color.BLACK, PieceType.QUEEN))

    assert board.is_in_check(Color.WHITE) is True


def test_pinned_piece_cannot_move_exposing_king() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.ROOK))

    assert board.make_move((6, 4), (6, 5)) is False


def test_king_cannot_move_into_check() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.ROOK))

    assert board.make_move((7, 4), (6, 4)) is False


def test_blocking_a_check_is_allowed() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(7, 2, create_piece(Color.WHITE, PieceType.BISHOP))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.ROOK))

    assert board.make_move((7, 2), (5, 4)) is True


def test_capturing_checking_piece_is_allowed_when_resolves_check() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(6, 4, create_piece(Color.BLACK, PieceType.ROOK))

    assert board.make_move((7, 4), (6, 4)) is True
