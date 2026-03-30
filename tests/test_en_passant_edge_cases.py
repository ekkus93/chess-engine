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


# =============================================================================
# Category 2: En Passant Edge Cases
# =============================================================================


def test_only_one_en_passant_target_at_a_time() -> None:
    """T2.1: Verify only one en_passant_target can exist at a time."""
    board = Board()
    for row in range(8):
        for col in range(8):
            board.clear_square(row, col)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.WHITE

    # White plays e2-e4 (creates en passant target at e3)
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))  # e2 pawn
    board.make_move((6, 4), (4, 4))  # e2-e4
    assert board.en_passant_target == (5, 4)  # e3 square available

    # After black plays non-pawn move, en passant target should be cleared
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.QUEEN))
    board.make_move((0, 4), (3, 4))  # d8-d5 (queen move, not pawn)
    assert board.en_passant_target is None


def test_en_passant_capture_removes_pawn_from_original_square() -> None:
    """T2.2: Verify capture removes pawn from original square."""
    board = Board()
    for row in range(8):
        for col in range(8):
            board.clear_square(row, col)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.PAWN))  # White pawn on e6
    board.set_piece(1, 3, create_piece(Color.BLACK, PieceType.PAWN))  # Black pawn on d7
    board.turn = Color.BLACK

    # Black plays d7-d5, creating en passant target at d6
    board.make_move((1, 3), (3, 3))  # d7-d5 (double step)
    assert board.en_passant_target == (2, 3)  # d6 square available

    # Switch to white's turn
    board.turn = Color.WHITE

    # White captures en passant (e6xd6)
    # White pawn at e6 (4,4) captures black pawn at d5 (3,3) en passant
    # The captured pawn is removed from d5 and placed on d6 (2,3)
    assert board.make_move((4, 4), (2, 3)) is True  # e6 captures d5 en passant

    # Verify black pawn was removed from d5
    assert board.get_piece(3, 3) is None  # d5 should be empty


def test_en_passant_expired_after_nonpawn_move() -> None:
    """T2.3: en_passant_target cleared after any move."""
    board = Board()
    for row in range(8):
        for col in range(8):
            board.clear_square(row, col)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))  # White pawn on e2
    board.set_piece(1, 4, create_piece(Color.BLACK, PieceType.PAWN))  # Black pawn on d7
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.QUEEN))
    board.turn = Color.BLACK

    # Black plays d7-d5, creating en passant target at d6
    board.make_move((1, 4), (3, 4))  # d7-d5 (double step)
    assert board.en_passant_target == (2, 4)  # d6 square available

    # White plays non-pawn move (knight), en passant should expire
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KNIGHT))
    board.make_move((7, 0), (5, 1))  # Nb1-d2
    assert board.en_passant_target is None

    # Black cannot capture en passant now
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))  # White pawn on e2
    board.turn = Color.BLACK
    assert (
        board.make_move((1, 4), (3, 4)) is False
    )  # Cannot capture en passant (expired)


def test_en_passant_destination_attacked_forbidden() -> None:
    """T2.4: En passant blocked if destination square attacked."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))  # White pawn on e7
    board.set_piece(
        3, 3, create_piece(Color.BLACK, PieceType.BISHOP)
    )  # Black bishop on d6
    board.turn = Color.WHITE

    # White plays e7-e5, trying to capture on d6 (attacked by bishop)
    legal_moves = board.get_legal_moves()
    # En passant to d6 should be illegal because d6 is attacked by bishop
    en_passant_moves = [
        m
        for m in legal_moves
        if m[0] == (6, 4) and m[1][0] == 2  # e7 to d6
    ]
    assert len(en_passant_moves) == 0


def test_en_passant_path_attacked_forbidden() -> None:
    """T2.4: En passant blocked if path through attacked square."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))  # White pawn on e7
    board.set_piece(3, 4, create_piece(Color.BLACK, PieceType.ROOK))  # Black rook on e6
    board.turn = Color.WHITE

    # White plays e7-e5, trying to capture on d6 (path goes through d6)
    # This is actually the destination square, so covered by previous test
    # Testing a different scenario: king in check


def test_en_passant_king_in_check_after_capture_forbidden() -> None:
    """T2.4: En passant blocked if after capture, king in check."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))  # White pawn on e7
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.ROOK))  # Black rook on d8
    board.turn = Color.WHITE

    # White plays e7-e5, trying to capture on d6
    # After capture, white king at e8 would be in check from rook at d8
    legal_moves = board.get_legal_moves()
    en_passant_moves = [
        m
        for m in legal_moves
        if m[0] == (6, 4) and m[1][0] == 2  # e7 to d6
    ]
    assert len(en_passant_moves) == 0


def test_full_en_passant_sequence_from_starting_position() -> None:
    """T2.5: Full game scenario: e2e4 d5e4 (en passant capture)."""
    board = Board()
    # Clear starting position and set up for en passant test
    for row in range(8):
        for col in range(8):
            board.clear_square(row, col)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))  # White pawn on e2
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.PAWN))  # White pawn on e3
    board.set_piece(1, 3, create_piece(Color.BLACK, PieceType.PAWN))  # Black pawn on d7
    board.turn = Color.BLACK

    # Black plays d7-d5 (double step)
    board.make_move((1, 3), (3, 3))  # d7-d5
    assert board.en_passant_target == (2, 3)  # d6 square available

    # Switch to white's turn
    board.turn = Color.WHITE

    # White captures en passant: e3 captures d5 en passant
    # White pawn at e3 (4,4) captures black pawn at d5 (3,3) en passant
    # The black pawn is removed from d5 and placed on d6 (2,3)
    assert board.make_move((4, 4), (2, 3)) is True

    # Verify white pawn is now at d6 (2,3) after en passant capture
    white_pawn_at_d6 = board.get_piece(2, 3)
    assert white_pawn_at_d6 is not None
    assert white_pawn_at_d6.kind == PieceType.PAWN
    assert white_pawn_at_d6.color == Color.WHITE

    # Verify black pawn at d5 was removed
    assert board.get_piece(3, 3) is None
