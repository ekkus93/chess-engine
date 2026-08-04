from __future__ import annotations

from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType
from tests.helpers import assert_empty, sq


# =============================================================================
# Regression tests for Fix 2
# =============================================================================
def test_queenside_castling_blocked_by_piece_on_b1() -> None:
    """Queenside castling forbidden when b1 is occupied."""
    board = Board()
    board.clear_board()
    board.set_piece(
        sq("e1"), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        sq("e8"), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        sq("a1"), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        sq("b1"), create_piece(Color.WHITE, PieceType.KNIGHT)
    )  # White knight on b1 blocks queenside castling
    board.turn = Color.WHITE
    assert (
        board.make_move(sq("e1"), sq("c1")) is False
    )


def test_queenside_castling_blocked_by_piece_on_b8() -> None:
    """Black queenside castling forbidden when b8 is occupied by own piece."""
    board = Board()
    board.clear_board()
    board.set_piece(
        sq("e1"), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        sq("e8"), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        sq("a8"), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.set_piece(
        sq("b8"), create_piece(Color.BLACK, PieceType.KNIGHT)
    )  # Black knight on b8 blocks queenside castling
    board.turn = Color.BLACK
    assert (
        board.make_move(sq("e8"), sq("c8")) is False
    )


# =============================================================================
# Category 1: Castling Edge Cases
# =============================================================================
def test_castling_rook_captured_forbids_kingside() -> None:
    """T1.1: Castling forbidden when rook was captured on original square."""
    board = Board()
    board.clear_board()
    board.set_piece(
        sq("e1"), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        sq("e8"), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        sq("h1"), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        sq("h8"), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.turn = Color.BLACK
    # Black captures h1 rook
    board.make_move(
        sq("h8"), sq("h1")
    )  # Black rook captures h1
    # White cannot castle kingside (rook no longer on h1)
    assert (
        board.make_move(sq("e1"), sq("g1")) is False
    )


def test_castling_rook_moved_clears_castling_right() -> None:
    """T1.1: Verify rook removal clears castling right."""
    board = Board()
    board.clear_board()
    board.set_piece(
        sq("e1"), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        sq("e8"), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        sq("h1"), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.turn = Color.WHITE
    # White moves rook from h1
    board.make_move(
        sq("h1"), sq("g1")
    )  # Rook moves to g1
    # White cannot castle kingside (original rook moved)
    assert (
        board.make_move(sq("e1"), sq("g1")) is False
    )


def test_castling_replaced_rook_does_not_restore_right() -> None:
    """T1.4: Replacement rook doesn't restore castling right."""
    board = Board()
    board.clear_board()
    board.set_piece(
        sq("e1"), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        sq("e8"), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        sq("h1"), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.turn = Color.WHITE
    # White moves rook from h1, black replaces it
    board.make_move(
        sq("h1"), sq("g1")
    )  # Rook moves to g1
    board.make_move(
        sq("h8"), sq("h1")
    )  # Black rook captures on h1
    # White cannot castle kingside (original rook moved, replacement doesn't help)
    assert (
        board.make_move(sq("e1"), sq("g1")) is False
    )


def test_castling_opponent_piece_in_path_blocks() -> None:
    """T1.2: Castling blocked by opponent piece in path."""
    board = Board()
    board.clear_board()
    board.set_piece(
        sq("e1"), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        sq("e8"), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        sq("h1"), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        sq("h8"), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.set_piece(
        sq("f1"), create_piece(Color.BLACK, PieceType.PAWN)
    )  # Black pawn on f1
    board.turn = Color.WHITE
    # Cannot castle kingside (path blocked by black pawn on g1)
    assert (
        board.make_move(sq("e1"), sq("g1")) is False
    )


def test_castling_enemy_piece_on_destination_blocked() -> None:
    """T1.2: Castling blocked if enemy piece on destination square."""
    board = Board()
    board.clear_board()
    board.set_piece(
        sq("e1"), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        sq("e8"), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        sq("h1"), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        sq("h8"), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.set_piece(
        sq("g1"), create_piece(Color.BLACK, PieceType.PAWN)
    )  # Black pawn on f1
    board.turn = Color.WHITE
    # Cannot castle kingside (destination square occupied by enemy)
    assert (
        board.make_move(sq("e1"), sq("g1")) is False
    )


def test_castling_kingside_rook_moved_forbids_kingside() -> None:
    """Kingside castling forbidden when kingside rook moved."""
    board = Board()
    board.clear_board()
    board.set_piece(
        sq("e1"), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        sq("e8"), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        sq("a1"), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        sq("h1"), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.turn = Color.WHITE
    # White moves kingside rook
    board.make_move(
        sq("h1"), sq("g1")
    )  # Rook moves to g1
    # White cannot castle kingside (kingside rook moved)
    assert (
        board.make_move(sq("e1"), sq("g1")) is False
    )


def test_castling_queenside_rook_moved_forbids_queenside() -> None:
    """Queenside castling forbidden when queenside rook moved."""
    board = Board()
    board.clear_board()
    board.set_piece(
        sq("e1"), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        sq("e8"), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        sq("a1"), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        sq("h1"), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.turn = Color.WHITE
    # White moves queenside rook
    board.make_move(
        sq("a1"), sq("b1")
    )  # Rook moves to b1
    # White cannot castle queenside (queenside rook moved)
    assert (
        board.make_move(sq("e1"), sq("c1")) is False
    )


def test_castling_kingside_rook_replaced_forbids() -> None:
    """T1.4: Kingside castling forbidden when original rook replaced."""
    board = Board()
    board.clear_board()
    board.set_piece(
        sq("e1"), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        sq("e8"), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        sq("h1"), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.turn = Color.WHITE
    # White moves rook from h1
    board.make_move(
        sq("h1"), sq("g1")
    )  # Rook moves to g1
    # Black replaces rook on h1
    board.make_move(
        sq("h8"), sq("h1")
    )  # Black rook captures on h1
    # White cannot castle kingside (original rook moved)
    assert (
        board.make_move(sq("e1"), sq("g1")) is False
    )


# =============================================================================
# Regression tests for Bug 3: castling execution for non-kings
# =============================================================================
def test_non_king_on_e1_does_not_execute_kingside_castling() -> None:
    """A non-king piece on e1 moving to g1 must NOT trigger castling execution."""
    board = Board()
    board.clear_board()
    board.set_piece(
        sq("e1"), create_piece(Color.WHITE, PieceType.QUEEN)
    )
    board.set_piece(
        sq("e8"), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        sq("h1"), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.turn = Color.WHITE
    board.make_move(sq("e1"), sq("g1"))
    assert board.get_piece_type_at(sq("g1")) == PieceType.QUEEN
    assert board.get_piece_type_at(sq("h1")) == PieceType.ROOK
    assert_empty(board, "e1")
    assert_empty(board, "d1")


def test_non_king_on_e1_does_not_execute_queenside_castling() -> None:
    """A non-king piece on e1 moving to c1 must NOT trigger queenside castling."""
    board = Board()
    board.clear_board()
    board.set_piece(
        sq("e1"), create_piece(Color.WHITE, PieceType.QUEEN)
    )
    board.set_piece(
        sq("e8"), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        sq("a1"), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.turn = Color.WHITE
    board.make_move(sq("e1"), sq("c1"))
    assert board.get_piece_type_at(sq("c1")) == PieceType.QUEEN
    assert board.get_piece_type_at(sq("a1")) == PieceType.ROOK
    assert_empty(board, "e1")
    assert_empty(board, "d1")
