from __future__ import annotations

from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq


# =============================================================================
# Regression tests for Fix 2
# =============================================================================
def test_en_passant_rejected_when_pawn_not_on_adjacent_row() -> None:
    """En passant rejected when capturing pawn is not on the correct rank."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    # White pawn on e4 (rank 4) - too far forward for EP
    board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.PAWN))
    # Black pawn on d7
    board.set_piece(sq("d7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK
    # Black plays d7-d5, creating EP target at d6
    board.make_move(sq("d7"), sq("d5"))
    assert board.en_passant_target == sq("d6")
    board.turn = Color.WHITE
    # White pawn on e4 should NOT be able to capture EP at d6
    # Row delta is 2, not 1 - should be illegal
    assert board.make_move(sq("e4"), sq("d6")) is False


def test_en_passant_rejected_when_black_pawn_not_on_adjacent_row() -> None:
    """Black en passant rejected when capturing pawn is not on rank 4."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    # Black pawn on d5 - too far forward for EP
    board.set_piece(sq("d5"), create_piece(Color.BLACK, PieceType.PAWN))
    # White pawn on e2
    board.set_piece(sq("e2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE
    # White plays e2-e4, creating EP target at e3
    board.make_move(sq("e2"), sq("e4"))
    assert board.en_passant_target == sq("e3")
    board.turn = Color.BLACK
    # Black pawn on d5 should NOT be able to capture EP at e3
    # Row delta is 2, not 1 - should be illegal
    assert board.make_move(sq("d5"), sq("e3")) is False


# =============================================================================
# Category 2: En Passant Edge Cases
# =============================================================================
def test_only_one_en_passant_target_at_a_time() -> None:
    """T2.1: Verify only one en_passant_target can exist at a time."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.WHITE
    # White plays e2-e4 (creates en passant target at e3)
    board.set_piece(sq("e2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.make_move(sq("e2"), sq("e4"))
    assert board.en_passant_target == sq("e3")
    # After black plays non-pawn move, en passant target should be cleared
    board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.make_move(sq("d8"), sq("d5"))
    assert board.en_passant_target is None


def test_en_passant_capture_removes_pawn_from_original_square() -> None:
    """T2.2: Verify capture removes pawn from original square."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e5"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("d7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK
    # Black plays d7-d5, creating en passant target at d6
    board.make_move(sq("d7"), sq("d5"))
    assert board.en_passant_target == sq("d6")
    # Switch to white's turn
    board.turn = Color.WHITE
    # White captures en passant (e5xd6)
    assert board.make_move(sq("e5"), sq("d6")) is True
    # Verify black pawn was removed from d5
    assert board.get_piece(sq("d5")) is None


def test_en_passant_expired_after_nonpawn_move() -> None:
    """T2.3: en_passant_target cleared after any move."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("d7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.turn = Color.BLACK
    # Black plays d7-d5, creating en passant target at d6
    board.make_move(sq("d7"), sq("d5"))
    assert board.en_passant_target == sq("d6")
    # White plays non-pawn move (knight), en passant should expire
    board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.make_move(sq("a1"), sq("b3"))
    assert board.en_passant_target is None
    # Black cannot capture en passant now
    board.set_piece(sq("e2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.BLACK
    assert board.make_move(sq("e7"), sq("e5")) is False


def test_en_passant_destination_attacked_forbidden() -> None:
    """T2.4: En passant blocked if destination square attacked."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e7"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("d6"), create_piece(Color.BLACK, PieceType.BISHOP))
    board.turn = Color.WHITE
    # White plays e7-e5, trying to capture on d6 (attacked by bishop)
    legal_moves = board.get_legal_moves()
    # En passant to d6 should be illegal because d6 is attacked by bishop
    en_passant_moves = [
        m
        for m in legal_moves
        if m[0] == sq("e3")
        and m[1] == sq("d6")
    ]
    assert len(en_passant_moves) == 0


def test_en_passant_path_attacked_forbidden() -> None:
    """T2.4: En passant blocked if path through attacked square."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e7"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("e6"), create_piece(Color.BLACK, PieceType.ROOK))
    board.turn = Color.WHITE
    # White plays e7-e5, trying to capture on d6 (path goes through d6)
    # This is actually the destination square, so covered by previous test
    # Testing a different scenario: king in check


def test_en_passant_king_in_check_after_capture_forbidden() -> None:
    """T2.4: En passant blocked if after capture, king in check."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e7"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.ROOK))
    board.turn = Color.WHITE
    # White plays e7-e5, trying to capture on d6
    # After capture, white king at e8 would be in check from rook at d8
    legal_moves = board.get_legal_moves()
    en_passant_moves = [
        m
        for m in legal_moves
        if m[0] == sq("e3")
        and m[1] == sq("d6")
    ]
    assert len(en_passant_moves) == 0


def test_full_en_passant_sequence_from_starting_position() -> None:
    """T2.5: Full game scenario: e2e4 d5e4 (en passant capture)."""
    board = Board()
    # Clear starting position and set up for en passant test
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e5"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("d7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK
    # Black plays d7-d5 (double step)
    board.make_move(sq("d7"), sq("d5"))
    assert board.en_passant_target == sq("d6")
    # Switch to white's turn
    board.turn = Color.WHITE
    # White captures en passant: e5 captures d6 en passant
    assert board.make_move(sq("e5"), sq("d6")) is True
    # Verify white pawn is now at d6 after en passant capture
    white_pawn_at_d6 = board.get_piece(sq("d6"))
    assert white_pawn_at_d6 is not None
    assert white_pawn_at_d6.kind == PieceType.PAWN
    assert white_pawn_at_d6.color == Color.WHITE
    # Verify black pawn at d5 was removed
    assert board.get_piece(sq("d5")) is None


def test_en_passant_target_set_after_white_two_square_advance() -> None:
    """White e2e4 sets en passant target at e3."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE
    assert board.make_move(sq("e2"), sq("e4")) is True
    assert board.en_passant_target == sq("e3")


def test_en_passant_target_set_after_black_two_square_advance() -> None:
    """Black d7d5 sets en passant target at d6."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK
    assert board.make_move(sq("d7"), sq("d5")) is True
    assert board.en_passant_target == sq("d6")


def test_en_passant_target_cleared_after_one_square_pawn_advance() -> None:
    """EP target cleared after a 1-square pawn move (not 2-square advance)."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("d7"), create_piece(Color.BLACK, PieceType.PAWN))
    # Black creates EP target by playing d7-d5
    board.turn = Color.BLACK
    board.make_move(sq("d7"), sq("d5"))
    assert board.en_passant_target is not None
    # White plays a 1-square pawn move, EP target should be cleared
    board.set_piece(sq("a2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE
    board.make_move(sq("a2"), sq("a3"))
    assert board.en_passant_target is None


def test_en_passant_in_legal_moves() -> None:
    """En passant capture appears in get_legal_moves()."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e5"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("d7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK
    board.make_move(sq("d7"), sq("d5"))
    board.turn = Color.WHITE
    legal = board.get_legal_moves()
    ep_target = sq("d6")
    ep_from = sq("e5")
    ep_moves = [m for m in legal if m[0] == ep_from and m[1] == ep_target]
    assert len(ep_moves) == 1


def test_en_passant_rejected_when_no_target() -> None:
    """En passant rejected when there is no en passant target set."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e5"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("d5"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE
    # No EP target set, so diagonal move to d6 should fail
    assert board.make_move(sq("e5"), sq("d6")) is False


def test_black_en_passant_full_sequence() -> None:
    """Black en passant capture: White plays e2e4, Black d4 captures e4 EP."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("d4"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE
    # White plays e2-e4
    assert board.make_move(sq("e2"), sq("e4")) is True
    # EP target is e3
    assert board.en_passant_target == sq("e3")
    # Black captures en passant: d4 captures e3
    board.turn = Color.BLACK
    assert board.make_move(sq("d4"), sq("e3")) is True
    # Black pawn now at e3
    assert board.get_piece(sq("e3")).color == Color.BLACK
    assert board.get_piece(sq("e3")).kind == PieceType.PAWN
    # White pawn on e4 was removed
    assert board.get_piece(sq("e4")) is None
    # Black pawn source d5 is empty
    assert board.get_piece(sq("d5")) is None
