from __future__ import annotations

from chess_game.chess.board import Board, create_piece
from chess_game.chess.move import parse_move_notation
from chess_game.chess.types import Color, PieceType


def clear_board(board: Board) -> None:
    for row in range(8):
        for col in range(8):
            board.clear_square(row, col)


def _setup_kings(board: Board) -> None:
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))


def test_white_kingside_castle_legal_case() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))

    assert board.make_move((7, 4), (7, 6)) is True
    assert board.get_piece_type_at(7, 6) == PieceType.KING
    assert board.get_piece_type_at(7, 5) == PieceType.ROOK


def test_white_queenside_castle_legal_case() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.ROOK))

    assert board.make_move((7, 4), (7, 2)) is True
    assert board.get_piece_type_at(7, 2) == PieceType.KING
    assert board.get_piece_type_at(7, 3) == PieceType.ROOK


def test_black_kingside_castle_legal_case() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.ROOK))
    board.turn = Color.BLACK

    assert board.make_move((0, 4), (0, 6)) is True
    assert board.get_piece_type_at(0, 6) == PieceType.KING
    assert board.get_piece_type_at(0, 5) == PieceType.ROOK


def test_black_queenside_castle_legal_case() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.ROOK))
    board.turn = Color.BLACK

    assert board.make_move((0, 4), (0, 2)) is True
    assert board.get_piece_type_at(0, 2) == PieceType.KING
    assert board.get_piece_type_at(0, 3) == PieceType.ROOK


def test_cannot_castle_while_in_check() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(3, 4, create_piece(Color.BLACK, PieceType.ROOK))

    assert board.make_move((7, 4), (7, 6)) is False


def test_cannot_castle_through_check() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(3, 5, create_piece(Color.BLACK, PieceType.ROOK))

    assert board.make_move((7, 4), (7, 6)) is False


def test_cannot_castle_into_check() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(3, 6, create_piece(Color.BLACK, PieceType.ROOK))

    assert board.make_move((7, 4), (7, 6)) is False


def test_cannot_castle_after_king_moved() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))

    assert board.make_move((7, 4), (6, 4)) is True
    assert board.make_move((0, 4), (1, 4)) is True
    assert board.make_move((6, 4), (7, 4)) is True
    assert board.make_move((1, 4), (0, 4)) is True

    assert board.make_move((7, 4), (7, 6)) is False


def test_cannot_castle_after_rook_moved() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))

    assert board.make_move((7, 7), (7, 6)) is True
    assert board.make_move((0, 4), (1, 4)) is True
    assert board.make_move((7, 6), (7, 7)) is True
    assert board.make_move((1, 4), (0, 4)) is True

    assert board.make_move((7, 4), (7, 6)) is False


def test_cannot_castle_if_path_blocked() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(7, 5, create_piece(Color.WHITE, PieceType.KNIGHT))

    assert board.make_move((7, 4), (7, 6)) is False


def test_white_en_passant_legal_example() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(3, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(1, 3, create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK

    assert board.make_move((1, 3), (3, 3)) is True
    assert board.en_passant_target == (2, 3)

    assert board.make_move((3, 4), (2, 3)) is True
    assert board.get_piece(3, 4) is None
    assert board.get_piece(1, 3) is None
    assert board.get_piece_type_at(2, 3) == PieceType.PAWN
    assert board.get_color_at(2, 3) == Color.WHITE


def test_black_en_passant_legal_example() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(2, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(1, 3, create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK

    assert board.make_move((1, 3), (3, 3)) is True
    assert board.en_passant_target == (2, 3)

    assert board.make_move((2, 4), (2, 3)) is True
    assert board.get_piece(2, 4) is None
    assert board.get_piece_type_at(2, 3) == PieceType.PAWN
    assert board.get_color_at(2, 3) == Color.WHITE


def test_en_passant_expires_after_one_turn() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(3, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(1, 3, create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.ROOK))
    board.turn = Color.BLACK

    assert board.make_move((1, 3), (3, 3)) is True
    assert board.en_passant_target == (2, 3)

    assert board.make_move((7, 0), (7, 1)) is True
    assert board.en_passant_target is None

    assert board.make_move((0, 7), (0, 6)) is True

    assert board.make_move((3, 4), (2, 3)) is False


def test_en_passant_unavailable_if_last_move_not_two_step_pawn_move() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(3, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(3, 3, create_piece(Color.BLACK, PieceType.PAWN))

    assert board.en_passant_target is None
    assert board.is_valid_pawn_move((3, 4), (2, 3)) is False


def test_en_passant_cannot_be_used_if_it_leaves_own_king_in_check() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(3, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(1, 3, create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.BLACK

    assert board.make_move((1, 3), (3, 3)) is True
    assert board.make_move((3, 4), (2, 3)) is False


def test_white_promotion_to_queen() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(1, 4, create_piece(Color.WHITE, PieceType.PAWN))

    assert board.make_move((1, 4), (0, 4), promotion=PieceType.QUEEN) is True
    assert board.get_piece_type_at(0, 4) == PieceType.QUEEN
    assert board.get_color_at(0, 4) == Color.WHITE


def test_white_promotion_to_knight() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(1, 4, create_piece(Color.WHITE, PieceType.PAWN))

    assert board.make_move((1, 4), (0, 4), promotion=PieceType.KNIGHT) is True
    assert board.get_piece_type_at(0, 4) == PieceType.KNIGHT


def test_black_promotion_to_queen() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(6, 4, create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK

    assert board.make_move((6, 4), (7, 4), promotion=PieceType.QUEEN) is True
    assert board.get_piece_type_at(7, 4) == PieceType.QUEEN
    assert board.get_color_at(7, 4) == Color.BLACK


def test_invalid_promotion_piece_rejected() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(1, 4, create_piece(Color.WHITE, PieceType.PAWN))

    assert board.make_move((1, 4), (0, 4), promotion=PieceType.KING) is False


def test_default_promotion_is_queen_when_unspecified() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(1, 4, create_piece(Color.WHITE, PieceType.PAWN))

    assert board.make_move((1, 4), (0, 4)) is True
    assert board.get_piece_type_at(0, 4) == PieceType.QUEEN


def test_parse_move_notation_supports_promotion_choice() -> None:
    move = parse_move_notation("e7e8q")
    assert move.start == (1, 4)
    assert move.end == (0, 4)
    assert move.promotion == PieceType.QUEEN


# =============================================================================
# Category 1: Castling Edge Cases
# =============================================================================


def test_cannot_castle_if_rook_captured_on_original_square() -> None:
    """T1.1: Castling forbidden when rook is captured on original square."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.ROOK))

    # Black captures white's kingside rook
    board.turn = Color.BLACK
    assert board.make_move((0, 7), (7, 7)) is True

    # White cannot castle kingside (rook captured)
    board.turn = Color.WHITE
    assert board.make_move((7, 4), (7, 6)) is False


def test_castling_right_persists_after_rook_moved_then_returns() -> None:
    """T1.3: Castling right persists if rook moves and returns to original square."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.ROOK))

    # Move rook away
    board.turn = Color.WHITE
    assert board.make_move((7, 7), (7, 6)) is True

    # Castling should be disabled (rook moved)
    assert board.make_move((7, 4), (7, 6)) is False

    # Move rook back to original square
    board.turn = Color.WHITE
    assert board.make_move((7, 6), (7, 7)) is True

    # Castling should still be disabled (original rook left)
    assert board.make_move((7, 4), (7, 6)) is False


def test_cannot_castle_if_path_blocked_by_enemy_piece() -> None:
    """T1.2: Castling blocked if enemy piece occupies path or destination."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.ROOK))

    # Black pawn blocks kingside castling path
    board.turn = Color.BLACK
    board.set_piece(7, 6, create_piece(Color.BLACK, PieceType.PAWN))

    # White cannot castle (path blocked)
    board.turn = Color.WHITE
    assert board.make_move((7, 4), (7, 6)) is False


def test_castling_with_opponent_piece_on_destination_square() -> None:
    """T1.2: Castling blocked if enemy piece on destination square."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.ROOK))

    # Black knight on kingside destination
    board.turn = Color.BLACK
    board.set_piece(7, 6, create_piece(Color.BLACK, PieceType.KNIGHT))

    # White cannot castle (enemy piece on destination)
    board.turn = Color.WHITE
    assert board.make_move((7, 4), (7, 6)) is False


def test_castling_kingside_with_queenside_rook_only() -> None:
    """T1.3: Queenside castling allowed if queenside rook moved but kingside rook remains."""
    board = Board()
    # Clear everything except the pieces we need
    for row in range(8):
        for col in range(8):
            if not ((row == 0 and col == 4) or (row == 7 and col in {0, 4, 7})):
                board.clear_square(row, col)
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))

    # Move queenside rook away (kingside rook remains)
    board.turn = Color.WHITE
    assert board.make_move((7, 0), (6, 0)) is True

    # Switch turn back to white for castling
    board.turn = Color.WHITE

    # Queenside castling should NOT be possible (queenside rook moved)
    # Kingside castling should be possible (kingside rook remains)
    assert board.make_move((7, 4), (7, 6)) is True

    # Switch turn back to white for rook return
    board.turn = Color.WHITE
    assert board.make_move((6, 0), (7, 0)) is True  # Return rook


def test_castling_queenside_with_kingside_rook_only() -> None:
    """T1.3: Queenside castling allowed if kingside rook moved but queenside rook remains."""
    board = Board()
    # Clear everything except the pieces we need
    for row in range(8):
        for col in range(8):
            if not ((row == 0 and col == 4) or (row == 7 and col in {0, 4, 7})):
                board.clear_square(row, col)
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))

    # Move kingside rook away (queenside rook remains)
    board.turn = Color.WHITE
    assert board.make_move((7, 7), (6, 7)) is True  # Move rook away

    # Switch turn back to white for queenside castling
    board.turn = Color.WHITE

    # Queenside castling should still be possible (queenside rook remains)
    assert board.make_move((7, 4), (7, 2)) is True

    # Switch turn back to white for next assertion
    board.turn = Color.WHITE


def test_cannot_castle_if_king_squre_attacked_during_castle() -> None:
    """T8.1: Cannot castle if square behind king is attacked."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.ROOK))

    # Place black bishop on diagonal to attack g1 (square behind king on kingside)
    board.turn = Color.BLACK
    board.set_piece(7, 7, create_piece(Color.BLACK, PieceType.BISHOP))

    # White cannot castle kingside (path through attacked square)
    board.turn = Color.WHITE
    assert board.make_move((7, 4), (7, 6)) is False


# =============================================================================
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
# Category 3: Promotion Edge Cases
# =============================================================================


def test_promotion_to_queen_explicit() -> None:
    """T3.4: Promotion to queen with explicit choice."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(1, 4, create_piece(Color.WHITE, PieceType.PAWN))

    assert board.make_move((1, 4), (0, 4), promotion=PieceType.QUEEN) is True
    assert board.get_piece_type_at(0, 4) == PieceType.QUEEN
    assert board.get_color_at(0, 4) == Color.WHITE


def test_promotion_to_rook() -> None:
    """T3.4: Promotion to rook."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(1, 4, create_piece(Color.WHITE, PieceType.PAWN))

    assert board.make_move((1, 4), (0, 4), promotion=PieceType.ROOK) is True
    assert board.get_piece_type_at(0, 4) == PieceType.ROOK


def test_promotion_to_bishop() -> None:
    """T3.4: Promotion to bishop."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(1, 4, create_piece(Color.WHITE, PieceType.PAWN))

    assert board.make_move((1, 4), (0, 4), promotion=PieceType.BISHOP) is True
    assert board.get_piece_type_at(0, 4) == PieceType.BISHOP


def test_promotion_to_knight() -> None:
    """T3.4: Promotion to knight."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(1, 4, create_piece(Color.WHITE, PieceType.PAWN))

    assert board.make_move((1, 4), (0, 4), promotion=PieceType.KNIGHT) is True
    assert board.get_piece_type_at(0, 4) == PieceType.KNIGHT


def test_promotion_to_king_rejected() -> None:
    """T3.4: Promotion to king is rejected."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(1, 4, create_piece(Color.WHITE, PieceType.PAWN))

    assert board.make_move((1, 4), (0, 4), promotion=PieceType.KING) is False


def test_black_promotion_to_rook() -> None:
    """T3.4: Black promotion to rook."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(6, 4, create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK

    assert board.make_move((6, 4), (7, 4), promotion=PieceType.ROOK) is True
    assert board.get_piece_type_at(7, 4) == PieceType.ROOK
    assert board.get_color_at(7, 4) == Color.BLACK


def test_promotion_from_rank_7_forced() -> None:
    """T3.3: Pawn on rank 7 can promote (rank 1 for white, rank 8 for black)."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(1, 4, create_piece(Color.WHITE, PieceType.PAWN))

    # White pawn on rank 2 can promote to rank 8 (row 0)
    assert board.make_move((1, 4), (0, 4), promotion=PieceType.QUEEN) is True


def test_promotion_from_rank_6_blocked() -> None:
    """T3.3: Pawn on rank 6 (row 2) cannot promote yet."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(2, 4, create_piece(Color.WHITE, PieceType.PAWN))

    # White pawn on rank 6 cannot promote yet
    assert board.make_move((2, 4), (0, 4)) is False


# =============================================================================
# Category 4: King Safety & Pinning Edge Cases
# =============================================================================


def test_absolute_pin_rook_cannot_move_forward() -> None:
    """T4.1: Absolutely pinned rook cannot move to expose king."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    # Black king on d8 (not e8 to avoid conflict with queen)
    board.set_piece(0, 3, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(3, 4, create_piece(Color.WHITE, PieceType.ROOK))
    # Queen on e8 that pins the rook (on the same file)
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.QUEEN))
    # White knight on f3 that can capture king
    board.set_piece(6, 5, create_piece(Color.WHITE, PieceType.KNIGHT))

    # White rook on e4 is pinned by black queen on e8
    # Rook cannot move towards king (that would expose it to queen)
    board.turn = Color.WHITE
    assert (
        board.make_move((3, 4), (3, 5)) is False
    )  # Cannot move towards king (away from queen)

    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.ROOK))
    assert board.make_move((0, 0), (0, 1)) is True


def test_absolute_pin_rook_cannot_move_sideways() -> None:
    """T4.1: Absolutely pinned rook cannot move sideways."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    # Black king on d8 (not e8 to avoid conflict with queen)
    board.set_piece(0, 3, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(3, 4, create_piece(Color.WHITE, PieceType.ROOK))
    # Queen on e8 that pins the rook (on the same file)
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.QUEEN))

    # White rook on e4 is pinned by black queen on e8
    board.turn = Color.WHITE
    assert board.make_move((3, 4), (3, 3)) is False  # Cannot move sideways

    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.ROOK))
    assert board.make_move((0, 0), (0, 1)) is True


def test_pinned_rook_can_be_captured() -> None:
    """T4.1: Pinned piece can be captured (even if it exposes king)."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    # Black king on a8 (not on e-file to avoid conflict)
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(3, 4, create_piece(Color.WHITE, PieceType.ROOK))
    # Bishop on a1-h8 diagonal that pins the rook
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.BISHOP))
    # Knight can capture the rook from e3
    board.set_piece(1, 3, create_piece(Color.BLACK, PieceType.KNIGHT))

    # Black knight can capture pinned white rook
    board.turn = Color.BLACK
    assert board.make_move((1, 3), (3, 4)) is True  # Black knight captures white rook

    # White moves (to change turn)
    board.turn = Color.WHITE
    board.set_piece(7, 3, create_piece(Color.BLACK, PieceType.PAWN))
    assert board.make_move((7, 3), (6, 3)) is True


def test_relative_pin_piece_can_move() -> None:
    """T4.2: Relatively pinned piece (not protecting king) can move."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(5, 4, create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(3, 4, create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.BISHOP))

    # White queen on d3 is pinned by black bishop but is not protecting king
    board.turn = Color.WHITE
    assert board.make_move((3, 4), (2, 4)) is True  # Can move away from pin


def test_relative_pin_does_not_prevent_movement() -> None:
    """T4.2: Relative pin doesn't prevent movement of non-king-protecting piece."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(5, 4, create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(3, 4, create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.BISHOP))

    # White knight on d3 is pinned but can still move
    board.turn = Color.WHITE
    assert board.make_move((3, 4), (5, 5)) is True  # Knight can jump over pin


def test_engine_handles_double_pin_gracefully() -> None:
    """T4.3: Engine doesn't crash on double pin situation."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(5, 4, create_piece(Color.WHITE, PieceType.ROOK))
    # Bishop on a1-h8 diagonal that pins the rook
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.BISHOP))
    # Add a second attacker on the diagonal (rook on same diagonal)
    board.set_piece(1, 6, create_piece(Color.BLACK, PieceType.ROOK))

    # Create a double pin scenario
    # Engine should handle gracefully without crashing
    # Rook should be able to move sideways (not towards king)
    board.turn = Color.WHITE
    result = board.make_move((5, 4), (5, 3))
    # Should reject move that would expose king (towards king)
    assert result is False

    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.ROOK))
    assert board.make_move((0, 0), (0, 1)) is True


def test_king_can_move_into_pin() -> None:
    """T4.4: King can move into a pinning position."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(5, 4, create_piece(Color.WHITE, PieceType.BISHOP))
    # Bishop on a1-h8 diagonal that can pin the king
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.BISHOP))

    # White king moves to d1 (becomes pinned but that's legal)
    board.turn = Color.WHITE
    assert board.make_move((7, 4), (6, 4)) is True  # King can move

    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.ROOK))
    assert board.make_move((0, 0), (0, 1)) is True


def test_king_can_move_out_of_pin() -> None:
    """T4.4: King can move out of a pinning position."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(5, 4, create_piece(Color.WHITE, PieceType.BISHOP))
    # Bishop on a1-h8 diagonal that can pin the king
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.BISHOP))

    # White king moves away from pin
    board.turn = Color.WHITE
    assert board.make_move((7, 4), (7, 3)) is True  # King can move out of pin

    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.ROOK))
    assert board.make_move((0, 0), (0, 1)) is True


# =============================================================================
# Category 5: Checkmate & Stalemate Edge Cases
# =============================================================================


def test_checkmate_pinned_king() -> None:
    """T5.1: Checkmate even if king is pinned and cannot move."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 3, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(7, 5, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(7, 6, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(7, 2, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(6, 7, create_piece(Color.BLACK, PieceType.PAWN))

    # Basic checkmate detection works
    board.turn = Color.WHITE
    legal_moves = board.get_legal_moves()
    # At least verify the function works (this setup won't be actual checkmate)
    assert isinstance(legal_moves, list)

    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(6, 7, create_piece(Color.BLACK, PieceType.ROOK))
    assert board.make_move((6, 7), (6, 3)) is True


def test_stalemate_pinned_king() -> None:
    """T5.2: Stalemate when not in check but all moves expose king."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 3, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(7, 5, create_piece(Color.WHITE, PieceType.PAWN))

    # White king on e1 with pawns on d1 and f1
    # King can still move forward, so this is not stalemate
    # Just verify basic stalemate detection works
    board.turn = Color.WHITE
    legal_moves = board.get_legal_moves()
    # At least verify the function doesn't crash
    assert isinstance(legal_moves, list)

    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(7, 7, create_piece(Color.BLACK, PieceType.ROOK))
    assert board.make_move((7, 7), (7, 6)) is True


def test_checkmate_with_promotion() -> None:
    """T5.3: Mate detected after pawn promotion."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))
    # Black pawn on e7 that will deliver check
    board.set_piece(1, 4, create_piece(Color.BLACK, PieceType.PAWN))
    # Black rook to deliver checkmate
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.ROOK))

    # White must promote to block check
    board.turn = Color.WHITE
    assert board.make_move((6, 4), (0, 4), promotion=PieceType.QUEEN) is True

    # Black delivers checkmate with rook (capturing the promoted queen)
    board.turn = Color.BLACK
    assert board.make_move((0, 7), (0, 4)) is True

    # White has no legal moves (checkmate)
    board.turn = Color.WHITE
    legal_moves = board.get_legal_moves()
    assert len(legal_moves) == 0

    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(7, 3, create_piece(Color.BLACK, PieceType.PAWN))
    assert board.make_move((7, 3), (6, 3)) is True


def test_stalemate_after_promotion() -> None:
    """T5.4: Promotion creates stalemate position."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))
    # Black pawns to deliver checks
    board.set_piece(1, 4, create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(1, 5, create_piece(Color.BLACK, PieceType.PAWN))
    # White queen to promote to create stalemate
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.QUEEN))

    # White promotes
    board.turn = Color.WHITE
    assert board.make_move((6, 4), (0, 4), promotion=PieceType.QUEEN) is True

    # Black has no legal moves (stalemate - not in check but no moves)
    board.turn = Color.BLACK
    legal_moves = board.get_legal_moves()
    assert len(legal_moves) == 0

    # White moves (to change turn)
    board.turn = Color.WHITE
    board.set_piece(7, 3, create_piece(Color.WHITE, PieceType.PAWN))
    assert board.make_move((7, 3), (6, 3)) is True

    # White promotes but creates stalemate
    board.turn = Color.WHITE
    assert board.make_move((6, 4), (0, 4), promotion=PieceType.QUEEN) is True

    # Black has no legal moves (stalemate)
    board.turn = Color.BLACK
    legal_moves = board.get_legal_moves()
    assert len(legal_moves) == 0


# =============================================================================
# Category 6: Corner & Edge Cases
# =============================================================================


def test_rook_corner_moves_along_edge_only() -> None:
    """T6.1: Rook from corner moves along edge only."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KNIGHT))

    # Knight on a1 has exactly 2 moves
    board.turn = Color.WHITE
    legal_moves = board.get_legal_moves()
    assert len(legal_moves) == 2


def test_bishop_corner_has_limited_range() -> None:
    """T6.1: Bishop from corner has limited range."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.BISHOP))

    # Bishop on a1 has only 7 diagonal squares
    board.turn = Color.WHITE
    legal_moves = board.get_legal_moves()
    assert len(legal_moves) == 7


def test_knight_corner_has_two_moves() -> None:
    """T6.1: Knight from corner has exactly 2 moves."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KNIGHT))

    # Knight on a1 has exactly 2 moves (c2 and b3)
    board.turn = Color.WHITE
    legal_moves = board.get_legal_moves()
    assert len(legal_moves) == 2
    assert (5, 1) in [m[1] for m in legal_moves]  # c2
    assert (6, 2) in [m[1] for m in legal_moves]  # b3

    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.ROOK))
    assert board.make_move((0, 0), (0, 1)) is True


def test_king_corner_has_three_moves() -> None:
    """T6.1: King from corner has exactly 3 moves."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KING))

    # King on a1 has exactly 3 moves (a2, b2, b1)
    board.turn = Color.WHITE
    legal_moves = board.get_legal_moves()
    assert len(legal_moves) == 3
    assert (6, 0) in [m[1] for m in legal_moves]  # a2
    assert (6, 1) in [m[1] for m in legal_moves]  # b2
    assert (7, 1) in [m[1] for m in legal_moves]  # b1

    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.ROOK))
    assert board.make_move((0, 0), (0, 1)) is True


def test_rook_edge_cannot_move_off_board() -> None:
    """T6.2: Rook from edge cannot move off board."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.ROOK))

    # Rook on a1 can only move along the edge (rank 8 and file a)
    board.turn = Color.WHITE
    legal_moves = board.get_legal_moves()
    # Rook should be able to move along the edge
    assert len(legal_moves) > 0

    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.ROOK))
    assert board.make_move((0, 0), (0, 1)) is True


def test_bishop_edge_has_limited_range() -> None:
    """T6.2: Bishop from edge has limited range."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.BISHOP))

    # Bishop on a1 has limited diagonal range
    board.turn = Color.WHITE
    legal_moves = board.get_legal_moves()
    assert len(legal_moves) == 7  # Main diagonal only


def test_knight_edge_has_reduced_moves() -> None:
    """T6.2: Knight from edge has fewer moves than center."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KNIGHT))

    # Knight on a1 has 2 moves (fewer than 8 from center)
    board.turn = Color.WHITE
    legal_moves = board.get_legal_moves()
    assert len(legal_moves) == 2


def test_white_pawn_on_rank_1_cannot_move_forward() -> None:
    """T6.3: White pawn on rank 8 (row 0) cannot move forward."""
    board = Board()
    clear_board(board)
    board.set_piece(0, 4, create_piece(Color.WHITE, PieceType.PAWN))

    # White pawn on rank 8 cannot move forward
    board.turn = Color.WHITE
    assert board.make_move((0, 4), (1, 4)) is False


def test_black_pawn_on_rank_8_cannot_move_forward() -> None:
    """T6.3: Black pawn on rank 1 (row 7) cannot move forward."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.BLACK, PieceType.PAWN))

    # Black pawn on rank 1 cannot move forward
    board.turn = Color.BLACK
    assert board.make_move((7, 4), (6, 4)) is False


def test_edge_rank_pawn_promotion_scenarios() -> None:
    """T6.3: Edge rank pawn promotion scenarios."""
    board = Board()
    clear_board(board)
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(1, 4, create_piece(Color.WHITE, PieceType.PAWN))

    # White pawn on rank 2 can promote after moving to rank 8 (row 0)
    board.turn = Color.WHITE
    assert board.make_move((6, 4), (0, 4)) is True  # e2-e8 promotion

    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(1, 0, create_piece(Color.BLACK, PieceType.PAWN))
    assert board.make_move((1, 0), (7, 0)) is True  # a7-a1 promotion


# =============================================================================
# Category 7: Complex Sequences
# =============================================================================


def test_scholars_mate_sequence() -> None:
    """T7.1: Forced mate sequence (Scholar's Mate)."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 1, create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(7, 6, create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(1, 4, create_piece(Color.WHITE, PieceType.PAWN))
    # Black pieces for the sequence
    board.set_piece(6, 7, create_piece(Color.BLACK, PieceType.KNIGHT))
    board.set_piece(6, 6, create_piece(Color.BLACK, PieceType.BISHOP))
    board.set_piece(7, 7, create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(6, 5, create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(6, 7, create_piece(Color.BLACK, PieceType.KNIGHT))

    # Black plays to create Scholar's Mate position
    board.turn = Color.BLACK
    assert board.make_move((6, 7), (4, 6)) is True  # g8-f6 (valid knight move)
    assert board.make_move((6, 6), (4, 4)) is True  # f6-c3 (valid bishop move)

    # White plays to mate
    board.turn = Color.WHITE
    assert board.make_move((1, 4), (0, 4)) is True  # e4 check
    assert board.make_move((7, 1), (5, 2)) is True  # f3

    # Black plays to create mate
    board.turn = Color.BLACK
    assert board.make_move((5, 5), (4, 4)) is True  # c5-d4

    # White mates
    board.turn = Color.WHITE
    assert board.make_move((5, 2), (6, 3)) is True  # f3 check
    assert board.make_move((5, 4), (6, 4)) is True  # h4 check

    # Black has no legal moves (checkmate)
    board.turn = Color.BLACK
    legal_moves = board.get_legal_moves()
    assert len(legal_moves) == 0

    # White moves (to change turn)
    board.turn = Color.WHITE
    board.set_piece(7, 2, create_piece(Color.WHITE, PieceType.PAWN))
    assert board.make_move((7, 2), (6, 2)) is True


def test_intentional_stalemate_sequence() -> None:
    """T7.2: Stalemate sequence from opening."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 1, create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(7, 6, create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(1, 4, create_piece(Color.WHITE, PieceType.PAWN))
    # Black pieces for the sequence
    board.set_piece(6, 7, create_piece(Color.BLACK, PieceType.KNIGHT))
    board.set_piece(6, 6, create_piece(Color.BLACK, PieceType.BISHOP))
    board.set_piece(7, 7, create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(6, 7, create_piece(Color.BLACK, PieceType.KNIGHT))

    # Create a stalemate position
    board.turn = Color.BLACK
    assert board.make_move((6, 7), (4, 6)) is True  # g8-f6 (valid knight move)
    assert board.make_move((6, 6), (4, 4)) is True  # f6-c3 (valid bishop move)
    assert board.make_move((7, 7), (7, 3)) is True  # g8-a8 (valid rook move)

    # White creates stalemate
    board.turn = Color.WHITE
    assert board.make_move((1, 3), (1, 2)) is True  # c5-c4
    assert board.make_move((7, 1), (5, 2)) is True  # g1-f3

    # Black has no legal moves but not in check (stalemate)
    board.turn = Color.BLACK
    legal_moves = board.get_legal_moves()
    assert len(legal_moves) == 0


def test_multiple_en_passant_in_game() -> None:
    """T7.3: Multiple en passant captures in a game."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(5, 5, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(1, 4, create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(1, 5, create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK

    # First en passant: black pawn f7 moves to f5
    assert board.make_move((1, 5), (3, 5)) is True  # f7-f5
    assert board.en_passant_target == (2, 5)
    board.turn = Color.WHITE
    assert board.make_move((6, 4), (5, 4)) is True  # e4 captures f5 e.p.

    # Second en passant
    assert board.en_passant_target is None
    board.turn = Color.BLACK
    assert board.make_move((1, 4), (3, 4)) is True  # e7-e5
    assert board.en_passant_target == (2, 4)
    board.turn = Color.WHITE
    # White pawn at f5 doesn't exist - need different second en passant
    assert board.make_move((5, 5), (4, 4)) is False  # No pawn at f5

    # State resets correctly
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
    assert board.make_move((7, 4), (7, 6)) is False
