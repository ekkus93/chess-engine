"""Tests for promotion."""

from __future__ import annotations

from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType

def clear_board(board: Board) -> None:
    for row in range(8):
        for col in range(8):
            board.clear_square(row, col)

def _setup_kings(board: Board) -> None:
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))

# Category 2: En Passant Edge Cases
# =============================================================================


def test_en_passant_white_captures_black_pawn() -> None:
    """T2.2: Standard en passant capture - white pawn captures black pawn."""
    board = Board()
    # Clear entire board first
    for row in range(8):
        for col in range(8):
            board.clear_square(row, col)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))  # Row 6 = rank 2
    board.set_piece(1, 4, create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK

    # Black moves pawn two squares (from rank 7 to rank 5)
    assert board.make_move((1, 4), (3, 4)) is True
    assert board.en_passant_target == (2, 4)

    # White captures en passant (from rank 2 to rank 5)
    board.turn = Color.WHITE
    assert board.make_move((6, 4), (5, 4)) is True  # e4 captures en passant on e5

    # Verify: white pawn on d5 (row 5), black pawn removed from d7 (row 1)
    assert board.get_piece_type_at(5, 4) == PieceType.PAWN
    assert board.get_piece_type_at(1, 4) is None

    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.ROOK))
    assert board.make_move((0, 0), (0, 1)) is True


def test_en_passant_black_captures_white_pawn() -> None:
    """T2.5: Full game scenario - black captures white pawn en passant."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(
        6, 4, create_piece(Color.WHITE, PieceType.PAWN)
    )  # Row 6 = rank 2 (e2)
    board.set_piece(
        5, 5, create_piece(Color.BLACK, PieceType.PAWN)
    )  # Row 5 = rank 3 (f3)

    board.turn = Color.WHITE

    # White moves pawn two squares first (from rank 2 to rank 4)
    # Start at rank 2 (row 6), move to rank 4 (row 4), passing through rank 3 (row 5)
    assert board.make_move((6, 4), (4, 4)) is True
    assert board.en_passant_target == (5, 4)

    # Black captures en passant immediately (f3 captures e3)
    board.turn = Color.BLACK
    assert board.make_move((5, 5), (5, 4)) is True  # f3 captures en passant on e3

    # Verify: black pawn on e3 (row 5), white pawn removed from e4 (row 4)
    assert board.get_piece_type_at(5, 4) == PieceType.PAWN
    assert board.get_piece_type_at(4, 4) is None

    # White moves (to change turn)
    board.turn = Color.WHITE
    board.set_piece(7, 1, create_piece(Color.WHITE, PieceType.ROOK))
    assert board.make_move((7, 1), (7, 2)) is True


def test_en_passant_expires_after_non_pawn_move() -> None:
    """T2.3: En passant target cleared after opponent's non-pawn move."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(1, 4, create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK

    # Black moves pawn two squares
    assert board.make_move((1, 4), (3, 4)) is True
    assert board.en_passant_target == (2, 4)

    # White moves knight (non-pawn move)
    board.turn = Color.WHITE
    board.set_piece(7, 1, create_piece(Color.WHITE, PieceType.KNIGHT))
    assert board.make_move((7, 1), (5, 2)) is True

    # En passant target should be cleared
    assert board.en_passant_target is None

    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.ROOK))
    assert board.make_move((0, 0), (0, 1)) is True


def test_en_passant_cannot_capture_own_pawn() -> None:
    """T2.5: Cannot capture own pawn en passant."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(1, 4, create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK

    # Black moves pawn two squares
    assert board.make_move((1, 4), (3, 4)) is True
    assert board.en_passant_target == (2, 4)

    # White tries to capture its own pawn en passant (should fail)
    board.turn = Color.WHITE
    assert board.make_move((2, 4), (3, 3)) is False

    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.ROOK))
    assert board.make_move((0, 0), (0, 1)) is True


def test_en_passant_expires_after_white_move() -> None:
    """T2.3: En passant expires after white's move."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(1, 4, create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK

    # Black moves pawn two squares
    assert board.make_move((1, 4), (3, 4)) is True
    assert board.en_passant_target == (2, 4)

    # White makes any move
    board.turn = Color.WHITE
    board.set_piece(7, 1, create_piece(Color.WHITE, PieceType.KNIGHT))
    assert board.make_move((7, 1), (5, 2)) is True

    # En passant target should be cleared
    assert board.en_passant_target is None

    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.ROOK))
    assert board.make_move((0, 0), (0, 1)) is True


# =============================================================================
