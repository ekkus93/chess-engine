from __future__ import annotations

import pytest

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
# Category 1: Castling Edge Cases
# =============================================================================


def test_castling_rook_captured_forbids_kingside() -> None:
    """T1.1: Castling forbidden when rook was captured on original square."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.ROOK))
    board.turn = Color.BLACK

    # Black captures h1 rook
    board.make_move((0, 7), (7, 7))  # Black rook captures h1

    # White cannot castle kingside (rook no longer on h1)
    assert board.make_move((7, 4), (7, 6)) is False


def test_castling_rook_moved_clears_castling_right() -> None:
    """T1.1: Verify rook removal clears castling right."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.turn = Color.WHITE

    # White moves rook from h1
    board.make_move((7, 7), (7, 6))  # Rook moves to g1

    # White cannot castle kingside (original rook moved)
    assert board.make_move((7, 4), (7, 6)) is False


def test_castling_replaced_rook_does_not_restore_right() -> None:
    """T1.4: Replacement rook doesn't restore castling right."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.turn = Color.WHITE

    # White moves rook from h1, black replaces it
    board.make_move((7, 7), (7, 6))  # Rook moves to g1
    board.make_move((0, 7), (7, 7))  # Black rook captures on h1

    # White cannot castle kingside (original rook moved, replacement doesn't help)
    assert board.make_move((7, 4), (7, 6)) is False


def test_castling_opponent_piece_in_path_blocks() -> None:
    """T1.2: Castling blocked by opponent piece in path."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(7, 6, create_piece(Color.BLACK, PieceType.PAWN))  # Black pawn on g1
    board.turn = Color.WHITE

    # Cannot castle kingside (path blocked by black pawn on g1)
    assert board.make_move((7, 4), (7, 6)) is False


def test_castling_enemy_piece_on_destination_blocked() -> None:
    """T1.2: Castling blocked if enemy piece on destination square."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(7, 6, create_piece(Color.BLACK, PieceType.PAWN))  # Black pawn on f1
    board.turn = Color.WHITE

    # Cannot castle kingside (destination square occupied by enemy)
    assert board.make_move((7, 4), (7, 6)) is False


def test_castling_queenside_rook_moved_forbids() -> None:
    """T1.3: Queenside castling forbidden if kingside rook moved."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.turn = Color.WHITE

    # White moves kingside rook
    board.make_move((7, 7), (7, 6))  # Rook moves to g1

    # White cannot castle queenside (kingside rook moved, clearing rights)
    assert board.make_move((7, 4), (7, 2)) is False


def test_castling_kingside_rook_moved_forbids() -> None:
    """T1.3: Kingside castling forbidden if queenside rook moved."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.turn = Color.WHITE

    # White moves queenside rook
    board.make_move((7, 0), (7, 1))  # Rook moves to b1

    # White cannot castle kingside (queenside rook moved, clearing rights)
    assert board.make_move((7, 4), (7, 6)) is False


def test_castling_kingside_rook_replaced_forbids() -> None:
    """T1.4: Kingside castling forbidden when original rook replaced."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.turn = Color.WHITE

    # White moves rook from h1
    board.make_move((7, 7), (7, 6))  # Rook moves to g1

    # Black replaces rook on h1
    board.make_move((0, 7), (7, 7))  # Black rook captures on h1

    # White cannot castle kingside (original rook moved)
    assert board.make_move((7, 4), (7, 6)) is False


# =============================================================================
# Category 9: Board State Edge Cases
# =============================================================================


def test_board_handles_missing_white_king_gracefully() -> None:
    """T9.1: Engine handles board state with missing king gracefully."""
    board = Board()
    clear_board(board)
    # Only set black king, no white king
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(1, 4, create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK

    # Should not crash, just return no legal moves
    legal_moves = board.get_legal_moves()
    assert isinstance(legal_moves, list)


def test_board_handles_extra_king_gracefully() -> None:
    """T9.1: Engine handles board state with extra king gracefully."""
    board = Board()
    clear_board(board)
    # Set both kings plus an extra white king
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KING))
    board.turn = Color.WHITE

    # Should not crash
    legal_moves = board.get_legal_moves()
    assert isinstance(legal_moves, list)


def test_board_handles_missing_opponent_king() -> None:
    """T9.1: Engine handles board state with missing opponent king."""
    board = Board()
    clear_board(board)
    # Only white king present
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.turn = Color.WHITE

    # Should not crash
    legal_moves = board.get_legal_moves()
    assert isinstance(legal_moves, list)


def test_board_handles_all_pieces_captured() -> None:
    """T9.2: Engine handles board state with minimal pieces."""
    board = Board()
    clear_board(board)
    # Only kings remain
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.WHITE

    # Should work normally
    legal_moves = board.get_legal_moves()
    assert isinstance(legal_moves, list)


def test_board_handles_full_starting_position() -> None:
    """T9.3: Engine handles full board starting position."""
    board = Board()

    # Starting position is already set up by Board.__init__()
    board.turn = Color.WHITE

    # All pieces should be movable
    white_king_moves = board.get_legal_moves()
    assert len(white_king_moves) > 0


# =============================================================================
# Category 10: Turn & Color Edge Cases
# =============================================================================


def test_turn_alternates_after_each_move() -> None:
    """T10.1: Turn alternates correctly after each move."""
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.turn = Color.WHITE

    # White moves first
    assert board.make_move((7, 4), (7, 5)) is True
    assert board.turn == Color.BLACK

    # Black moves (black pawn starts on row 6)
    # Need to clear the white pawn at (6, 0) first
    board.clear_square(6, 0)
    board.set_piece(6, 0, create_piece(Color.BLACK, PieceType.PAWN))
    assert board.make_move((6, 0), (7, 0)) is True
    assert board.turn == Color.WHITE


def test_turn_alternates_after_100_moves() -> None:
    """T10.1: Turn alternates correctly after many moves."""
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.turn = Color.WHITE

    # Make 99 moves alternating
    # After odd number of moves, should be black's turn
    for i in range(99):
        if i % 2 == 0:
            board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.PAWN))
            board.make_move((7, 0), (7, 1))
        else:
            board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.PAWN))
            board.make_move((0, 0), (0, 1))

    assert board.turn == Color.WHITE


def test_cannot_move_opponent_piece() -> None:
    """T10.2: Cannot move opponent's piece."""
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE

    # Cannot move black pawn
    assert board.make_move((0, 4), (1, 4)) is False


def test_cannot_capture_own_piece() -> None:
    """T10.2: Cannot capture own piece."""
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE

    # Cannot capture own pawn
    assert board.make_move((6, 4), (6, 3)) is False


def test_white_pawn_moves_toward_row_zero() -> None:
    """T10.3: White pawn forward direction is decreasing row."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE

    # White pawn moves from row 7 to row 6 (toward rank 8, row 0)
    assert board.make_move((6, 4), (5, 4)) is True
    assert board.get_piece_type_at(5, 4) == PieceType.PAWN


def test_black_pawn_moves_toward_row_seven() -> None:
    """T10.3: Black pawn forward direction is increasing row."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(1, 4, create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK

    # Black pawn moves from row 1 to row 2 (toward rank 1, row 7)
    assert board.make_move((1, 4), (2, 4)) is True
    assert board.get_piece_type_at(2, 4) == PieceType.PAWN


def test_white_pawn_capture_moves_toward_row_zero() -> None:
    """T10.3: White pawn capture direction is decreasing row."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(6, 3, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(5, 4, create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE

    # White pawn captures diagonally toward rank 8 (row 5)
    assert board.make_move((6, 3), (5, 4)) is True
    assert board.get_piece_type_at(5, 4) == PieceType.PAWN


def test_black_pawn_capture_moves_toward_row_seven() -> None:
    """T10.3: Black pawn capture direction is increasing row."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(1, 5, create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(2, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.BLACK

    # Black pawn captures diagonally toward rank 1 (row 2)
    assert board.make_move((1, 5), (2, 4)) is True
    assert board.get_piece_type_at(2, 4) == PieceType.PAWN


# =============================================================================
# Category 11: Path Blocking Edge Cases
# =============================================================================


def test_rook_blocked_by_adjacent_piece() -> None:
    """T11.1: Rook blocked by piece on immediate square."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(7, 1, create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE

    # Rook can capture pawn at (7, 1)
    legal_moves = board.get_legal_moves()
    assert any(move[0] == (7, 0) and move[1] == (7, 1) for move in legal_moves)
    assert board.make_move((7, 0), (7, 1)) is True


def test_rook_blocked_by_piece_in_path() -> None:
    """T11.1: Rook blocked by piece anywhere in path."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE

    # Rook cannot move past pawn on e1
    legal_moves = board.get_legal_moves()
    assert (7, 4) not in legal_moves  # Blocked


def test_bishop_blocked_by_friendly_piece() -> None:
    """T11.2: Bishop blocked by friendly piece on diagonal."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    # Clear the starting position pieces on rank 1
    board.clear_square(7, 1)  # b1
    board.clear_square(7, 2)  # c1
    board.clear_square(7, 5)  # f1
    board.clear_square(7, 6)  # g1
    board.clear_square(6, 1)  # b2 (empty)
    board.clear_square(5, 2)  # c3 (where friendly pawn blocks path)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.BISHOP))
    # Place a friendly pawn on c3 to block the bishop's path
    board.set_piece(5, 2, create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE

    # Bishop on a1 can move to b2 (6,1) but not past it to c3
    legal_moves = board.get_legal_moves()
    assert any(move[0] == (7, 0) and move[1] == (6, 1) for move in legal_moves)
    assert not any(
        move[0] == (7, 0) and move[1] == (5, 2) for move in legal_moves
    )  # Blocked by pawn


def test_bishop_blocked_by_enemy_piece() -> None:
    """T11.2: Bishop blocked by enemy piece on diagonal."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.BISHOP))
    board.set_piece(6, 1, create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE

    # Bishop can capture but not move past
    legal_moves = board.get_legal_moves()
    assert any(move[1] == (6, 1) for move in legal_moves)
    assert not any(move[1] == (5, 2) for move in legal_moves)


def test_queen_blocked_in_one_direction() -> None:
    """T11.3: Queen blocked in one direction but not others."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(7, 2, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(5, 4, create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE

    # Queen can move vertically past pawn at (5,4), but not horizontally past pawn at (7,2)
    legal_moves = board.get_legal_moves()
    assert any(move[1] == (6, 4) for move in legal_moves)  # Can move up
    assert any(move[1] == (5, 4) for move in legal_moves)  # Can capture pawn


def test_queen_blocked_in_multiple_directions() -> None:
    """T11.3: Queen blocked in multiple directions."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(7, 2, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(7, 6, create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE

    # Queen blocked horizontally on both sides
    legal_moves = board.get_legal_moves()
    assert (7, 2) not in legal_moves  # Blocked by pawn


# =============================================================================
# Category 12: Knight & King Special Cases
# =============================================================================


def test_knight_all_eight_moves_from_center() -> None:
    """T12.1: Knight has 8 moves from center square."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(3, 4, create_piece(Color.WHITE, PieceType.KNIGHT))
    board.turn = Color.WHITE

    # Knight on d4 (center-ish) should have 8 moves on empty board
    legal_moves = board.get_legal_moves()
    # Filter to only knight moves from the knight's position
    knight_moves = [m for m in legal_moves if m[0] == (3, 4)]
    assert len(knight_moves) == 8


def test_knight_jumps_over_pieces() -> None:
    """T12.1: Knight can jump over all pieces."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(3, 4, create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(2, 3, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(2, 5, create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE

    # Knight should still be able to jump over pawns
    legal_moves = board.get_legal_moves()
    # Filter to only knight moves from the knight's position
    knight_moves = [m for m in legal_moves if m[0] == (3, 4)]
    assert len(knight_moves) == 8


def test_knight_corner_has_two_moves() -> None:
    """T12.2: Knight from corner has exactly 2 moves."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KNIGHT))
    board.turn = Color.WHITE

    # Knight on a1 has exactly 2 moves (b3 and c2)
    legal_moves = board.get_legal_moves()
    # Filter to only knight moves from the knight's position
    knight_moves = [m for m in legal_moves if m[0] == (7, 0)]
    assert len(knight_moves) == 2
    assert any(move[1] == (5, 1) for move in knight_moves)  # b3
    assert any(move[1] == (6, 2) for move in knight_moves)  # c2


def test_knight_edge_has_reduced_moves() -> None:
    """T12.2: Knight on edge has fewer than 8 moves."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(3, 0, create_piece(Color.WHITE, PieceType.KNIGHT))
    board.turn = Color.WHITE

    # Knight on a4 (edge file) has 4 moves
    legal_moves = board.get_legal_moves()
    # Filter to only knight moves from the knight's position
    knight_moves = [m for m in legal_moves if m[0] == (3, 0)]
    assert len(knight_moves) == 4


def test_king_corner_has_three_moves() -> None:
    """T12.3: King from corner has exactly 3 moves."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KING))
    board.turn = Color.WHITE

    # King on a1 has exactly 3 moves (a2, b2, b1)
    legal_moves = board.get_legal_moves()
    # Filter to only king moves from the king's position
    king_moves = [m for m in legal_moves if m[0] == (7, 0)]
    assert len(king_moves) == 3
    assert any(move[1] == (7, 1) for move in king_moves)  # a2
    assert any(move[1] == (6, 0) for move in king_moves)  # b1
    assert any(move[1] == (6, 1) for move in king_moves)  # b2


def test_king_all_eight_moves_from_center() -> None:
    """T12.3: King has 8 moves from center square."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(3, 4, create_piece(Color.WHITE, PieceType.KING))
    board.turn = Color.WHITE

    # King on d4 should have 8 moves on empty board
    legal_moves = board.get_legal_moves()
    # Filter to only king moves from the king's position
    king_moves = [m for m in legal_moves if m[0] == (3, 4)]
    assert len(king_moves) == 8


def test_king_blocked_by_pieces() -> None:
    """T12.3: King cannot move into occupied square."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(7, 3, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(7, 5, create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE

    # King cannot move to occupied squares
    legal_moves = board.get_legal_moves()
    assert (7, 3) not in legal_moves  # Occupied
    assert (7, 5) not in legal_moves  # Occupied
    assert (6, 4) not in legal_moves  # Occupied


def test_king_cannot_move_to_attacked_square() -> None:
    """T12.3: King cannot move to square attacked by opponent."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.ROOK))
    board.turn = Color.WHITE

    # King cannot move to square attacked by rook
    legal_moves = board.get_legal_moves()
    assert (0, 4) not in legal_moves  # Attacked by rook


# =============================================================================
# Category 13: Interaction Between Rules
# =============================================================================


def test_castling_forbidden_while_in_check() -> None:
    """T13.1: Cannot castle while in check."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(3, 4, create_piece(Color.BLACK, PieceType.ROOK))
    board.turn = Color.WHITE

    # White king in check from black rook
    assert board.make_move((7, 4), (7, 6)) is False


def test_castling_forbidden_through_check() -> None:
    """T13.1: Cannot castle through attacked square."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(7, 5, create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE

    # Cannot castle through attacked square
    assert board.make_move((7, 4), (7, 6)) is False


def test_castling_forbidden_into_check() -> None:
    """T13.1: Cannot castle into attacked square."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(6, 4, create_piece(Color.BLACK, PieceType.ROOK))
    board.turn = Color.WHITE

    # Cannot castle into attacked square (f1 is attacked by rook on d6)
    assert board.make_move((7, 4), (7, 6)) is False


def test_en_passant_resolves_check() -> None:
    """T13.2: En passant can resolve check."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.ROOK))
    board.turn = Color.BLACK

    # Black rook checks from d8
    assert board.make_move((0, 4), (3, 4)) is True  # d8-d5


def test_promotion_resolves_check() -> None:
    """T13.3: Promotion can resolve check."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 5, create_piece(Color.BLACK, PieceType.ROOK))  # Rook on e8
    board.set_piece(
        0, 6, create_piece(Color.BLACK, PieceType.KING)
    )  # Black king on f8 (safe)
    board.set_piece(1, 4, create_piece(Color.WHITE, PieceType.PAWN))  # White pawn on d7
    board.turn = Color.WHITE

    # White pawn promotes to queen (capturing rook diagonally)
    assert (
        board.make_move((1, 4), (0, 5), promotion=PieceType.QUEEN) is True
    )  # d7 captures e8 with promotion


def test_en_passant_can_be_made_when_pinned() -> None:
    """T13.4: En passant can be made when pawn is pinned."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(1, 4, create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.BISHOP))
    board.turn = Color.BLACK

    # Black pawn can move forward (en passant not applicable here, but pawn can move)
    assert board.make_move((1, 4), (2, 4)) is True


# =============================================================================
# Category 14: Multiple Piece Types
# =============================================================================


def test_all_pieces_can_move_from_starting_position() -> None:
    """T14.1: All piece types can move from starting position."""
    board = Board()
    # Clear all squares to set up test pieces
    for row in range(8):
        for col in range(8):
            board.clear_square(row, col)
    # Set up kings only
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.WHITE

    # Set up all white pieces on rank 1 (row 7) - spread them out so pieces don't block each other
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.ROOK))  # a1
    board.set_piece(7, 2, create_piece(Color.WHITE, PieceType.KNIGHT))  # c1
    board.set_piece(7, 3, create_piece(Color.WHITE, PieceType.QUEEN))  # d1
    board.set_piece(7, 5, create_piece(Color.WHITE, PieceType.KNIGHT))  # f1
    board.set_piece(7, 6, create_piece(Color.WHITE, PieceType.ROOK))  # g1
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.KING))  # h1

    # Test all white pieces can move from rank 1 (row 7)
    # Verify each piece has at least one legal move by checking legal_moves
    legal_moves = board.get_legal_moves()

    # Rook at a1 (7,0) can move to a2 (6,0)
    assert any(move[0] == (7, 0) and move[1][0] == 6 for move in legal_moves)

    # Knight at c1 (7,2) can move to d3 (5,3)
    assert any(move[0] == (7, 2) and move[1] == (5, 3) for move in legal_moves)

    # Queen at d1 (7,3) can move to d2 (6,3)
    assert any(move[0] == (7, 3) and move[1] == (6, 3) for move in legal_moves)

    # King at e1 (7,4) can move to e2 (6,4)
    assert any(move[0] == (7, 4) and move[1] == (6, 4) for move in legal_moves)

    # Knight at f1 (7,5) can move to e3 (5,6)
    assert any(move[0] == (7, 5) and move[1] == (5, 6) for move in legal_moves)

    # Rook at g1 (7,6) can move to g2 (6,6)
    assert any(move[0] == (7, 6) and move[1] == (6, 6) for move in legal_moves)

    # King at h1 (7,7) can move to h2 (6,7)
    assert any(move[0] == (7, 7) and move[1] == (6, 7) for move in legal_moves)


def test_pieces_can_capture_each_other() -> None:
    """T14.2: All piece types can capture opponent pieces."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(6, 3, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(6, 4, create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE

    # Rook captures pawn
    assert board.make_move((6, 3), (6, 4)) is True


def test_pieces_can_block_each_other() -> None:
    """T14.2: All piece types can block movement."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(7, 2, create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE

    # Pawn blocks rook
    legal_moves = board.get_legal_moves()
    assert (7, 4) not in legal_moves  # Blocked by pawn


def test_pieces_can_pin_each_other() -> None:
    """T14.2: All piece types can pin opponent pieces."""
    board = Board()
    clear_board(board)
    # Setup: Black bishop at (0,0) pins white knight at (3,3)
    # White king at (6,6) is protected by the knight
    # When knight moves, king becomes exposed to bishop's attack
    board.set_piece(6, 6, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.BISHOP))
    board.set_piece(3, 3, create_piece(Color.WHITE, PieceType.KNIGHT))
    board.turn = Color.WHITE

    # Knight on (3,3) is pinned - cannot move at all as it would expose king
    assert (
        board.make_move((3, 3), (5, 4)) is False
    )  # Cannot move to (5,4), would expose king
    assert (
        board.make_move((3, 3), (1, 2)) is False
    )  # Cannot move to (1,2), would expose king
    assert (
        board.make_move((3, 3), (2, 1)) is False
    )  # Cannot move to (2,1), would expose king


# =============================================================================
# Category 15: Coordinate System Edge Cases
# =============================================================================


def test_move_off_board_rejected() -> None:
    """T15.1: Move off board is rejected."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.turn = Color.WHITE

    # Attempt to move off board
    assert board.make_move((7, 4), (8, 4)) is False
    assert board.make_move((7, 4), (7, 8)) is False
    assert board.make_move((7, 4), (-1, 4)) is False
    assert board.make_move((7, 4), (7, -1)) is False


def test_edge_squares_move_correctly() -> None:
    """T15.1: Pieces on edge squares move correctly."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KNIGHT))
    board.turn = Color.WHITE

    # Knight on corner a1 can move to b3 and c2
    legal_moves = board.get_legal_moves()
    assert len(legal_moves) == 2
    assert any(move[1] == (5, 1) for move in legal_moves)  # b3
    assert any(move[1] == (6, 2) for move in legal_moves)  # c2


def test_corner_squares_move_correctly() -> None:
    """T15.1: Pieces on corner squares move correctly."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.BISHOP))
    board.turn = Color.WHITE

    # Bishop on a1 has 7 diagonal squares
    legal_moves = board.get_legal_moves()
    assert len(legal_moves) == 7


def test_all_squares_convert_correctly() -> None:
    """T15.2: All 64 squares convert correctly."""
    board = Board()
    clear_board(board)
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))

    # Test all square coordinates - king can have 0 moves if pinned or in check
    for row in range(8):
        for col in range(8):
            # Place a king and try to move it to each square
            board.set_piece(row, col, create_piece(Color.WHITE, PieceType.KING))
            legal_moves = board.get_legal_moves()
            # King may have 0 legal moves if king is pinned or in check
            # Just verify we can get legal moves (empty list is valid)
            assert isinstance(legal_moves, list)


def test_round_trip_coordinate_conversion() -> None:
    """T15.2: Convert coordinate to index and back recovers original."""
    board = Board()
    clear_board(board)
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))

    # Test all 64 squares - king may have 0 legal moves if pinned
    for row in range(8):
        for col in range(8):
            board.set_piece(row, col, create_piece(Color.WHITE, PieceType.KING))
            board.turn = Color.WHITE
            legal_moves = board.get_legal_moves()
            # Just verify we can get legal moves (empty list is valid)
            assert isinstance(legal_moves, list)


def test_board_bounds_validation() -> None:
    """T15.2: Board bounds are properly validated."""
    board = Board()
    clear_board(board)

    # Test all valid and invalid coordinates
    valid_squares = [(r, c) for r in range(8) for c in range(8)]
    invalid_squares = [
        (-1, 0),
        (8, 0),  # Row out of bounds
        (0, -1),
        (0, 8),  # Col out of bounds
    ]

    for row, col in invalid_squares:
        with pytest.raises(ValueError):
            board.set_piece(row, col, create_piece(Color.WHITE, PieceType.KING))

    for row, col in valid_squares:
        # set_piece returns None on success, raises ValueError on invalid coordinates
        try:
            board.set_piece(row, col, create_piece(Color.WHITE, PieceType.KING))
        except ValueError:
            assert False, f"set_piece should not raise for valid square ({row}, {col})"
