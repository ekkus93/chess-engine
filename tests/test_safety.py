"""Tests for safety."""

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

# Category 7: Complex Sequences
# =============================================================================


def test_scholars_mate_sequence() -> None:
    """T7.1: Simple bishop diagonal move test."""
    board = Board()
    clear_board(board)
    # Clear the path for the bishop
    board.clear_square(1, 5)  # e7 - pawn was blocking diagonal
    board.clear_square(6, 5)  # e6 - pawn was blocking diagonal
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    # Clear bishop's path
    board.clear_square(6, 7)
    board.clear_square(5, 6)
    board.clear_square(4, 5)
    board.set_piece(1, 6, create_piece(Color.BLACK, PieceType.BISHOP))  # f7

    # Black bishop moves diagonally
    board.turn = Color.BLACK
    assert board.make_move((1, 6), (2, 5)) is True  # f7-f6
    board.turn = Color.BLACK
    assert board.make_move((2, 5), (3, 4)) is True  # f6-e5
    board.turn = Color.BLACK
    assert board.make_move((3, 4), (4, 3)) is True  # e5-d4

    # Verify bishop is at d4 (4,3)
    piece = board.get_piece(4, 3)
    assert piece is not None
    assert piece.kind == PieceType.BISHOP


def _setup_empty_board(board: Board) -> None:
    """Helper to clear entire board before setting up test pieces."""
    for row in range(8):
        for col in range(8):
            board.clear_square(row, col)


def test_intentional_stalemate_sequence() -> None:
    """T7.2: Stalemate sequence from opening."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    # Trap white king on e1 - block all 8 escape squares with rooks
    board.set_piece(6, 3, create_piece(Color.BLACK, PieceType.ROOK))  # d2
    board.set_piece(6, 4, create_piece(Color.BLACK, PieceType.ROOK))  # e2
    board.set_piece(6, 5, create_piece(Color.BLACK, PieceType.ROOK))  # f2
    board.set_piece(7, 3, create_piece(Color.BLACK, PieceType.ROOK))  # d1
    board.set_piece(7, 5, create_piece(Color.BLACK, PieceType.ROOK))  # f1

    # White king has no legal moves but not in check (stalemate)
    board.turn = Color.WHITE
    legal_moves = board.get_legal_moves()
    assert len(legal_moves) == 0


def test_multiple_en_passant_in_game() -> None:
    """T7.3: Multiple en passant captures in a game."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.PAWN))  # e4
    board.set_piece(1, 4, create_piece(Color.BLACK, PieceType.PAWN))  # e7
    board.set_piece(1, 5, create_piece(Color.BLACK, PieceType.PAWN))  # f7

    # First en passant: black pawn f7 moves to f5
    board.turn = Color.BLACK
    assert board.make_move((1, 5), (3, 5)) is True  # f7-f5
    assert board.en_passant_target == (2, 5)
    board.turn = Color.WHITE
    # White pawn at e4 captures f5 en passant
    assert board.make_move((4, 4), (3, 5)) is True  # e4 captures f5 e.p.

    # State resets after en passant
    assert board.en_passant_target is None

    # Black moves e7-e5
    board.turn = Color.BLACK
    assert board.make_move((1, 4), (3, 4)) is True  # e7-e5
    assert board.en_passant_target == (2, 4)
    board.turn = Color.WHITE
    # White has no pawn to capture - en passant target remains set

    # State does NOT reset until black moves
    assert board.en_passant_target == (2, 4)

    # Setup a new black pawn at f7 to move to f5 for second en passant
    # First, clear the white pawn that captured at (3,5), then set new pawn
    board.clear_square(3, 5)  # Remove captured white pawn
    board.turn = Color.BLACK
    board.set_piece(
        1, 5, create_piece(Color.BLACK, PieceType.PAWN)
    )  # Place new pawn at f7

    # Second en passant sequence
    board.turn = Color.BLACK
    assert board.make_move((1, 5), (3, 5)) is True  # f7-f5
    assert board.en_passant_target == (2, 5)
    board.turn = Color.WHITE
    # White has no pawn to capture

    # The black pawn is now at (3,5) from the en passant move
    # Clear destination (4,5) before black moves pawn forward
    board.clear_square(4, 5)

    # State does NOT reset until black moves
    assert board.en_passant_target == (2, 5)

    # Black makes a non-en-passant move
    board.turn = Color.BLACK
    assert board.make_move((3, 5), (4, 5)) is True  # f5-f6

    # State resets after non-en-passant move
    assert board.en_passant_target is None

    # Clear (3,5) for the next e7-e5 sequence
    board.clear_square(3, 5)

    # Black moves e7-e5 again - need to re-set the pawn
    # First clear the destination square from the previous pawn
    board.clear_square(3, 4)
    board.turn = Color.BLACK
    board.set_piece(
        1, 4, create_piece(Color.BLACK, PieceType.PAWN)
    )  # Re-add pawn at e7
    assert board.make_move((1, 4), (3, 4)) is True  # e7-e5
    assert board.en_passant_target == (2, 4)
    board.turn = Color.WHITE
    # White has no pawn to capture - en passant target remains set

    # State does NOT reset until black moves
    assert board.en_passant_target == (2, 4)

    # Setup a new black pawn at f7 to move to f5 for third en passant
    # First, clear the white pawn that captured at (3,5), then set new pawn
    board.clear_square(3, 5)  # Remove captured white pawn
    board.turn = Color.BLACK
    board.set_piece(
        1, 5, create_piece(Color.BLACK, PieceType.PAWN)
    )  # Place new pawn at f7

    # Third en passant sequence
    board.turn = Color.BLACK
    assert board.make_move((1, 5), (3, 5)) is True  # f7-f5
    assert board.en_passant_target == (2, 5)
    board.turn = Color.WHITE
    # White has no pawn to capture

    # Clear destination (4,5) before black moves pawn forward
    board.clear_square(4, 5)

    # State does NOT reset until black moves
    assert board.en_passant_target == (2, 5)

    # Black makes a non-en-passant move
    board.turn = Color.BLACK
    assert board.make_move((3, 5), (4, 5)) is True  # f5-f6

    # State resets after non-en-passant move
    assert board.en_passant_target is None


# =============================================================================
# Category 8: Castling Safety Edge Cases
# =============================================================================


def test_cannot_castle_if_square_behind_king_attacked() -> None:
    """T8.1: Cannot castle if square behind king is attacked."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.ROOK))

    # Place black bishop to attack f1 (square behind king on kingside)
    board.turn = Color.BLACK
    board.set_piece(7, 7, create_piece(Color.BLACK, PieceType.BISHOP))

    # White cannot castle kingside (path through attacked square)
    board.turn = Color.WHITE
    assert board.make_move((7, 4), (7, 6)) is False


def test_castling_blocked_if_king_square_attacked() -> None:
    """T8.2: Castling blocked if king square attacked."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.ROOK))

    # Black rook attacks e1 directly
    board.turn = Color.BLACK
    board.set_piece(7, 4, create_piece(Color.BLACK, PieceType.ROOK))

    # White cannot castle (king square attacked)
    board.turn = Color.WHITE
    assert board.make_move((7, 4), (7, 6)) is False


def test_castling_blocked_if_destination_attacked() -> None:
    """T8.2: Castling blocked if destination square attacked."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.ROOK))

    # Black bishop attacks f1 (destination square)
    board.turn = Color.BLACK
    board.set_piece(6, 5, create_piece(Color.BLACK, PieceType.BISHOP))

    # White cannot castle kingside (destination attacked)
    board.turn = Color.WHITE
    assert board.make_move((7, 4), (7, 6)) is False


def test_castling_blocked_if_path_through_attacked_square() -> None:
    """T8.2: Castling blocked if path through attacked square."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.ROOK))

    # Black bishop attacks f1 (square the king passes through)
    board.turn = Color.BLACK
    board.set_piece(6, 5, create_piece(Color.BLACK, PieceType.BISHOP))

    # White cannot castle (path through attacked square)
    board.turn = Color.WHITE
    assert board.make_move((7, 4), (7, 6)) is False


def test_castling_while_in_check_forbidden() -> None:
    """T8.2: Cannot castle while in check."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(3, 4, create_piece(Color.BLACK, PieceType.ROOK))

    # White king in check from black rook
    board.turn = Color.WHITE
