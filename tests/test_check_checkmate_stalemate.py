"""Tests for check, checkmate, and stalemate detection."""

from __future__ import annotations

from chess_game.chess.board import Board, ConstantSquare, create_piece
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
    get_square_constant,
)
from chess_game.chess.types import Color, PieceType


def test_rook_checks_king_on_same_file() -> None:
    """Rook checking king on same file."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.BLACK, PieceType.ROOK)
    )
    assert board.is_in_check(Color.WHITE) is True


def test_bishop_checks_king_on_diagonal() -> None:
    """Bishop checking king on diagonal."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(4, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 0), create_piece(Color.BLACK, PieceType.BISHOP)
    )
    assert board.is_in_check(Color.WHITE) is True


def test_knight_checks_king() -> None:
    """Knight checking king."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(4, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(2, 5), create_piece(Color.BLACK, PieceType.KNIGHT)
    )
    assert board.is_in_check(Color.WHITE) is True


def test_pawn_checks_king() -> None:
    """Black pawn on d6 checks white king on e5."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(2, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(1, 3), create_piece(Color.BLACK, PieceType.PAWN)
    )
    assert board.is_in_check(Color.WHITE) is True


def test_blocked_sliding_attack_is_not_check() -> None:
    """Blocked sliding attack does not constitute check."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.set_piece(
        get_square_constant(3, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )
    assert board.is_in_check(Color.WHITE) is False


def test_king_not_in_check_when_no_attackers() -> None:
    """King not in check when no enemy pieces can attack."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(4, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 0), create_piece(Color.BLACK, PieceType.PAWN)
    )
    assert board.is_in_check(Color.WHITE) is False


def test_back_rank_mate() -> None:
    """Back-rank mate: black king on e8, white rook on a8, pawns on d7/e7/f7 block escape."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(1, 3), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.set_piece(
        get_square_constant(1, 4), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.set_piece(
        get_square_constant(1, 5), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.set_piece(
        get_square_constant(0, 0), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.turn = Color.BLACK
    assert board.is_checkmate() is True
    assert board.is_checkmate(Color.BLACK) is True


def test_not_checkmate_when_escape_exists() -> None:
    """Not checkmate when king has an escape square."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(1, 3), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.set_piece(
        get_square_constant(1, 4), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.set_piece(
        get_square_constant(1, 5), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        get_square_constant(0, 5), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.BLACK
    assert board.is_checkmate() is False


def test_not_checkmate_when_can_capturer_attacker() -> None:
    """Not checkmate when king can capture the checking piece."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(4, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(2, 5), create_piece(Color.WHITE, PieceType.KNIGHT)
    )
    board.turn = Color.BLACK
    assert board.is_checkmate() is False


def test_stalemate_known_position() -> None:
    """Known stalemate: black king on a1, white queen on c2, white king on c1."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(7, 0), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(6, 2), create_piece(Color.WHITE, PieceType.QUEEN)
    )
    board.set_piece(
        get_square_constant(7, 2), create_piece(Color.WHITE, PieceType.KING)
    )
    board.turn = Color.BLACK
    assert board.is_stalemate() is True
    assert board.is_stalemate(Color.BLACK) is True


def test_not_stalemate_when_in_check() -> None:
    """Not stalemate when the side is in check (that would be checkmate if no moves)."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(1, 3), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.set_piece(
        get_square_constant(1, 4), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.set_piece(
        get_square_constant(1, 5), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.turn = Color.BLACK
    assert board.is_stalemate() is False
    assert board.is_stalemate(Color.BLACK) is False


def test_not_stalemate_when_moves_exist() -> None:
    """Not stalemate when the side has legal moves."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(3, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.turn = Color.BLACK
    assert board.is_stalemate() is False


def test_is_checkmate_with_explicit_color() -> None:
    """is_checkmate works with explicit color argument."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(1, 3), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.set_piece(
        get_square_constant(1, 4), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.set_piece(
        get_square_constant(1, 5), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.set_piece(
        get_square_constant(0, 0), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.turn = Color.WHITE
    assert board.is_checkmate(Color.BLACK) is True
    assert board.is_checkmate(Color.WHITE) is False


def test_is_stalemate_with_explicit_color() -> None:
    """is_stalemate works with explicit color argument."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(7, 0), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(6, 2), create_piece(Color.WHITE, PieceType.QUEEN)
    )
    board.set_piece(
        get_square_constant(7, 2), create_piece(Color.WHITE, PieceType.KING)
    )
    board.turn = Color.WHITE
    assert board.is_stalemate(Color.BLACK) is True
    assert board.is_stalemate(Color.WHITE) is False
