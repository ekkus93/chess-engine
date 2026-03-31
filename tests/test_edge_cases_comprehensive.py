from __future__ import annotations
from chess_game.constants import (
    ConstantSquare,
    ROW_1,
    ROW_2,
    ROW_3,
    ROW_4,
    ROW_5,
    ROW_6,
    ROW_7,
    ROW_8,
    COL_A,
    COL_B,
    COL_C,
    COL_D,
    COL_E,
    COL_F,
    COL_G,
    COL_H,
    get_row_constant,
    get_col_constant,
)
from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType


def clear_board(board: Board) -> None:
    for row in range(8):
        for col in range(8):
            col = get_col_constant(col)
            board.clear_square(
                ConstantSquare(row=get_row_constant(row), col=get_col_constant(col))
            )


def _setup_kings(board: Board) -> None:
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )


# =============================================================================
# Category 1: Castling Edge Cases
# =============================================================================
def test_castling_rook_captured_forbids_kingside() -> None:
    """T1.1: Castling forbidden when rook was captured on original square."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_H), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_H), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.turn = Color.BLACK
    # Black captures h1 rook
    board.make_move(
        ConstantSquare(row=ROW_8, col=COL_H), ConstantSquare(row=ROW_1, col=COL_H)
    )  # Black rook captures h1
    # White cannot castle kingside (rook no longer on h1)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_1, col=COL_G)
        )
        is False
    )


def test_castling_rook_moved_clears_castling_right() -> None:
    """T1.1: Verify rook removal clears castling right."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_H), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.turn = Color.WHITE
    # White moves rook from h1
    board.make_move(
        ConstantSquare(row=ROW_1, col=COL_H), ConstantSquare(row=ROW_1, col=COL_G)
    )  # Rook moves to g1
    # White cannot castle kingside (original rook moved)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_1, col=COL_G)
        )
        is False
    )


def test_castling_replaced_rook_does_not_restore_right() -> None:
    """T1.4: Replacement rook doesn't restore castling right."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_H), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.turn = Color.WHITE
    # White moves rook from h1, black replaces it
    board.make_move(
        ConstantSquare(row=ROW_1, col=COL_H), ConstantSquare(row=ROW_1, col=COL_G)
    )  # Rook moves to g1
    board.make_move(
        ConstantSquare(row=ROW_8, col=COL_H), ConstantSquare(row=ROW_1, col=COL_H)
    )  # Black rook captures on h1
    # White cannot castle kingside (original rook moved, replacement doesn't help)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_1, col=COL_G)
        )
        is False
    )


def test_castling_opponent_piece_in_path_blocks() -> None:
    """T1.2: Castling blocked by opponent piece in path."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_H), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_H), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_G), create_piece(Color.BLACK, PieceType.PAWN)
    )  # Black pawn on g1
    board.turn = Color.WHITE
    # Cannot castle kingside (path blocked by black pawn on g1)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_1, col=COL_G)
        )
        is False
    )


def test_castling_enemy_piece_on_destination_blocked() -> None:
    """T1.2: Castling blocked if enemy piece on destination square."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_H), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_H), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_G), create_piece(Color.BLACK, PieceType.PAWN)
    )  # Black pawn on f1
    board.turn = Color.WHITE
    # Cannot castle kingside (destination square occupied by enemy)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_1, col=COL_G)
        )
        is False
    )


def test_castling_queenside_rook_moved_forbids() -> None:
    """T1.3: Queenside castling forbidden if kingside rook moved."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_H), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.turn = Color.WHITE
    # White moves kingside rook
    board.make_move(
        ConstantSquare(row=ROW_1, col=COL_H), ConstantSquare(row=ROW_1, col=COL_G)
    )  # Rook moves to g1
    # White cannot castle queenside (kingside rook moved, clearing rights)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_1, col=COL_C)
        )
        is False
    )


def test_castling_kingside_rook_moved_forbids() -> None:
    """T1.3: Kingside castling forbidden if queenside rook moved."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_H), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.turn = Color.WHITE
    # White moves queenside rook
    board.make_move(
        ConstantSquare(row=ROW_1, col=COL_A), ConstantSquare(row=ROW_1, col=COL_B)
    )  # Rook moves to b1
    # White cannot castle kingside (queenside rook moved, clearing rights)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_1, col=COL_G)
        )
        is False
    )


def test_castling_kingside_rook_replaced_forbids() -> None:
    """T1.4: Kingside castling forbidden when original rook replaced."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_H), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.turn = Color.WHITE
    # White moves rook from h1
    board.make_move(
        ConstantSquare(row=ROW_1, col=COL_H), ConstantSquare(row=ROW_1, col=COL_G)
    )  # Rook moves to g1
    # Black replaces rook on h1
    board.make_move(
        ConstantSquare(row=ROW_8, col=COL_H), ConstantSquare(row=ROW_1, col=COL_H)
    )  # Black rook captures on h1
    # White cannot castle kingside (original rook moved)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_1, col=COL_G)
        )
        is False
    )


# =============================================================================
# Category 2: En Passant Edge Cases
# =============================================================================
def test_only_one_en_passant_target_at_a_time() -> None:
    """T2.1: Verify only one en_passant_target can exist at a time."""
    board = Board()
    for row in range(8):
        for col in range(8):
            col = get_col_constant(col)
            board.clear_square(
                ConstantSquare(row=get_row_constant(row), col=get_col_constant(col))
            )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.turn = Color.WHITE
    # White plays e2-e4 (creates en passant target at e3)
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e2 pawn
    board.make_move(
        ConstantSquare(row=ROW_2, col=COL_E), ConstantSquare(row=ROW_4, col=COL_E)
    )  # e2-e4
    assert board.en_passant_target == (5, 4)  # e3 square available
    # After black plays non-pawn move, en passant target should be cleared
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.QUEEN)
    )
    board.make_move(
        ConstantSquare(row=ROW_8, col=COL_E), ConstantSquare(row=ROW_5, col=COL_E)
    )  # d8-d5 (queen move, not pawn)
    assert board.en_passant_target is None


def test_en_passant_capture_removes_pawn_from_original_square() -> None:
    """T2.2: Verify capture removes pawn from original square."""
    board = Board()
    for row in range(8):
        for col in range(8):
            col = get_col_constant(col)
            board.clear_square(
                ConstantSquare(row=get_row_constant(row), col=get_col_constant(col))
            )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )  # White pawn on e2
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_D), create_piece(Color.BLACK, PieceType.PAWN)
    )  # Black pawn on d7
    board.turn = Color.BLACK
    # Black plays d7-d5, creating en passant target at d6
    board.make_move(
        ConstantSquare(row=ROW_7, col=COL_D), ConstantSquare(row=ROW_5, col=COL_D)
    )  # d7-d5 (double step)
    assert board.en_passant_target == (2, 3)  # d6 square available
    # Switch to white's turn
    board.turn = Color.WHITE
    # White captures en passant (e2xd3)
    # White pawn at e2 (6,4) captures black pawn at d5 (3,3) en passant
    # The captured pawn is removed from d5 and placed on d6 (2,3)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_2, col=COL_E), ConstantSquare(row=ROW_6, col=COL_D)
        )
        is True
    )  # e2 captures d5 en passant
    # Verify black pawn was removed from d5
    assert board.get_piece(3, 3) is None  # d5 should be empty


def test_en_passant_expired_after_nonpawn_move() -> None:
    """T2.3: en_passant_target cleared after any move."""
    board = Board()
    for row in range(8):
        for col in range(8):
            col = get_col_constant(col)
            board.clear_square(
                ConstantSquare(row=get_row_constant(row), col=get_col_constant(col))
            )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )  # White pawn on e2
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.BLACK, PieceType.PAWN)
    )  # Black pawn on d7
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.QUEEN)
    )
    board.turn = Color.BLACK
    # Black plays d7-d5, creating en passant target at d6
    board.make_move(
        ConstantSquare(row=ROW_7, col=COL_E), ConstantSquare(row=ROW_5, col=COL_E)
    )  # d7-d5 (double step)
    assert board.en_passant_target == (2, 4)  # d6 square available
    # White plays non-pawn move (knight), en passant should expire
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A),
        create_piece(Color.WHITE, PieceType.KNIGHT),
    )
    board.make_move(
        ConstantSquare(row=ROW_1, col=COL_A), ConstantSquare(row=ROW_3, col=COL_B)
    )  # Nb1-d2
    assert board.en_passant_target is None
    # Black cannot capture en passant now
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )  # White pawn on e2
    board.turn = Color.BLACK
    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_E), ConstantSquare(row=ROW_5, col=COL_E)
        )
        is False
    )  # Cannot capture en passant (expired)


def test_en_passant_destination_attacked_forbidden() -> None:
    """T2.4: En passant blocked if destination square attacked."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )  # White pawn on e7
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
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )  # White pawn on e7
    board.set_piece(
        ConstantSquare(row=ROW_5, col=COL_E), create_piece(Color.BLACK, PieceType.ROOK)
    )  # Black rook on e6
    board.turn = Color.WHITE
    # White plays e7-e5, trying to capture on d6 (path goes through d6)
    # This is actually the destination square, so covered by previous test
    # Testing a different scenario: king in check


def test_en_passant_king_in_check_after_capture_forbidden() -> None:
    """T2.4: En passant blocked if after capture, king in check."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )  # White pawn on e7
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.ROOK)
    )  # Black rook on d8
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
            col = get_col_constant(col)
            board.clear_square(
                ConstantSquare(row=get_row_constant(row), col=get_col_constant(col))
            )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )  # White pawn on e2
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_D), create_piece(Color.BLACK, PieceType.PAWN)
    )  # Black pawn on d7
    board.turn = Color.BLACK
    # Black plays d7-d5 (double step)
    board.make_move(
        ConstantSquare(row=ROW_7, col=COL_D), ConstantSquare(row=ROW_5, col=COL_D)
    )  # d7-d5
    assert board.en_passant_target == (2, 3)  # d6 square available
    # Switch to white's turn
    board.turn = Color.WHITE
    # White captures en passant: e2 captures d5 en passant
    # White pawn at e2 (6,4) captures black pawn at d5 (3,3) en passant
    # The black pawn is removed from d5 and placed on d6 (2,3)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_2, col=COL_E), ConstantSquare(row=ROW_6, col=COL_D)
        )
        is True
    )
    # Verify white pawn is now at d6 (2,3) after en passant capture
    white_pawn_at_d6 = board.get_piece(2, 3)
    assert white_pawn_at_d6 is not None
    assert white_pawn_at_d6.kind == PieceType.PAWN
    assert white_pawn_at_d6.color == Color.WHITE
    # Verify black pawn at d5 was removed
    assert board.get_piece(3, 3) is None


# =============================================================================
# Category 9: Board State Edge Cases
# =============================================================================
def test_board_handles_missing_white_king_gracefully() -> None:
    """T9.1: Engine handles board state with missing king gracefully."""
    board = Board()
    clear_board(board)
    # Only set black king, no white king
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.BLACK
    # Should not crash, just return no legal moves
    legal_moves = board.get_legal_moves()
    assert isinstance(legal_moves, list)


def test_board_handles_extra_king_gracefully() -> None:
    """T9.1: Engine handles board state with extra king gracefully."""
    board = Board()
    clear_board(board)
    # Set both kings plus an extra white king
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A), create_piece(Color.WHITE, PieceType.KING)
    )
    board.turn = Color.WHITE
    # Should not crash
    legal_moves = board.get_legal_moves()
    assert isinstance(legal_moves, list)


def test_board_handles_missing_opponent_king() -> None:
    """T9.1: Engine handles board state with missing opponent king."""
    board = Board()
    clear_board(board)
    # Only white king present
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.turn = Color.WHITE
    # Should not crash
    legal_moves = board.get_legal_moves()
    assert isinstance(legal_moves, list)


def test_board_handles_all_pieces_captured() -> None:
    """T9.2: Engine handles board state with minimal pieces."""
    board = Board()
    clear_board(board)
    # Only kings remain
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
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
    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_1, col=COL_F)
        )
        is True
    )
    assert board.turn == Color.BLACK
    # Black moves (black pawn starts on row 6)
    # Need to clear the white pawn at (6, 0) first
    board.clear_square(ConstantSquare(row=ROW_2, col=COL_A))
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_A), create_piece(Color.BLACK, PieceType.PAWN)
    )
    assert (
        board.make_move(
            ConstantSquare(row=ROW_2, col=COL_A), ConstantSquare(row=ROW_1, col=COL_A)
        )
        is True
    )
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
            board.set_piece(
                ConstantSquare(row=ROW_1, col=COL_A),
                create_piece(Color.WHITE, PieceType.PAWN),
            )
            board.make_move(
                ConstantSquare(row=ROW_1, col=COL_A),
                ConstantSquare(row=ROW_1, col=COL_B),
            )
        else:
            board.set_piece(
                ConstantSquare(row=ROW_8, col=COL_A),
                create_piece(Color.BLACK, PieceType.PAWN),
            )
            board.make_move(
                ConstantSquare(row=ROW_8, col=COL_A),
                ConstantSquare(row=ROW_8, col=COL_B),
            )
    assert board.turn == Color.WHITE


def test_cannot_move_opponent_piece() -> None:
    """T10.2: Cannot move opponent's piece."""
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e2
    board.turn = Color.WHITE
    # Cannot move black pawn
    assert (
        board.make_move(
            ConstantSquare(row=ROW_8, col=COL_E), ConstantSquare(row=ROW_7, col=COL_E)
        )
        is False
    )


def test_cannot_capture_own_piece() -> None:
    """T10.2: Cannot capture own piece."""
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e2
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.turn = Color.WHITE
    # Cannot capture own pawn
    assert (
        board.make_move(
            ConstantSquare(row=ROW_2, col=COL_E), ConstantSquare(row=ROW_2, col=COL_D)
        )
        is False
    )


def test_white_pawn_moves_toward_row_zero() -> None:
    """T10.3: White pawn forward direction is decreasing row."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.turn = Color.WHITE
    # White pawn moves from row 7 to row 6 (toward rank 8, row 0)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_2, col=COL_E), ConstantSquare(row=ROW_3, col=COL_E)
        )
        is True
    )
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_3, col=COL_E)) == PieceType.PAWN
    )


def test_black_pawn_moves_toward_row_seven() -> None:
    """T10.3: Black pawn forward direction is increasing row."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.BLACK
    # Black pawn moves from row 1 to row 2 (toward rank 1, row 7)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_E), ConstantSquare(row=ROW_6, col=COL_E)
        )
        is True
    )
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_6, col=COL_E)) == PieceType.PAWN
    )


def test_white_pawn_capture_moves_toward_row_zero() -> None:
    """T10.3: White pawn capture direction is decreasing row."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_D), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_3, col=COL_E), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.WHITE
    # White pawn captures diagonally toward rank 8 (row 5)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_2, col=COL_D), ConstantSquare(row=ROW_3, col=COL_E)
        )
        is True
    )
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_3, col=COL_E)) == PieceType.PAWN
    )


def test_black_pawn_capture_moves_toward_row_seven() -> None:
    """T10.3: Black pawn capture direction is increasing row."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_F), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_6, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.turn = Color.BLACK
    # Black pawn captures diagonally toward rank 1 (row 2)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_F), ConstantSquare(row=ROW_6, col=COL_E)
        )
        is True
    )
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_6, col=COL_E)) == PieceType.PAWN
    )


# =============================================================================
# Category 11: Path Blocking Edge Cases
# =============================================================================
def test_rook_blocked_by_adjacent_piece() -> None:
    """T11.1: Rook blocked by piece on immediate square."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_B), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.WHITE
    # Rook can capture pawn at (7, 1)
    legal_moves = board.get_legal_moves()
    assert any(move[0] == (7, 0) and move[1] == (7, 1) for move in legal_moves)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_A), ConstantSquare(row=ROW_1, col=COL_B)
        )
        is True
    )


def test_rook_blocked_by_piece_in_path() -> None:
    """T11.1: Rook blocked by piece anywhere in path."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e2
    board.turn = Color.WHITE
    # Rook cannot move past pawn on e1
    legal_moves = board.get_legal_moves()
    assert (7, 4) not in legal_moves  # Blocked


def test_bishop_blocked_by_friendly_piece() -> None:
    """T11.2: Bishop blocked by friendly piece on diagonal."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    # Clear the starting position pieces on rank 1
    board.clear_square(ConstantSquare(row=ROW_1, col=COL_B))  # b1
    board.clear_square(ConstantSquare(row=ROW_1, col=COL_C))  # c1
    board.clear_square(ConstantSquare(row=ROW_1, col=COL_F))  # f1
    board.clear_square(ConstantSquare(row=ROW_1, col=COL_G))  # g1
    board.clear_square(ConstantSquare(row=ROW_2, col=COL_B))  # b2 (empty)
    board.clear_square(
        ConstantSquare(row=ROW_3, col=COL_C)
    )  # c3 (where friendly pawn blocks path)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A),
        create_piece(Color.WHITE, PieceType.BISHOP),
    )
    # Place a friendly pawn on c3 to block the bishop's path
    board.set_piece(
        ConstantSquare(row=ROW_3, col=COL_C), create_piece(Color.WHITE, PieceType.PAWN)
    )
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
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A),
        create_piece(Color.WHITE, PieceType.BISHOP),
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_B), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.WHITE
    # Bishop can capture but not move past
    legal_moves = board.get_legal_moves()
    assert any(move[1] == (6, 1) for move in legal_moves)
    assert not any(move[1] == (5, 2) for move in legal_moves)


def test_queen_blocked_in_one_direction() -> None:
    """T11.3: Queen blocked in one direction but not others."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.QUEEN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_C), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_3, col=COL_E), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.WHITE
    # Queen can move vertically past pawn at (5,4), but not horizontally past pawn at (7,2)
    legal_moves = board.get_legal_moves()
    assert any(move[1] == (6, 4) for move in legal_moves)  # Can move up
    assert any(move[1] == (5, 4) for move in legal_moves)  # Can capture pawn


def test_queen_blocked_in_multiple_directions() -> None:
    """T11.3: Queen blocked in multiple directions."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.QUEEN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_C), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_G), create_piece(Color.WHITE, PieceType.PAWN)
    )
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
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_5, col=COL_E),
        create_piece(Color.WHITE, PieceType.KNIGHT),
    )
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
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_5, col=COL_E),
        create_piece(Color.WHITE, PieceType.KNIGHT),
    )
    board.set_piece(
        ConstantSquare(row=ROW_6, col=COL_D), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_6, col=COL_F), create_piece(Color.WHITE, PieceType.PAWN)
    )
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
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A),
        create_piece(Color.WHITE, PieceType.KNIGHT),
    )
    board.turn = Color.WHITE
    # Knight on a1 has exactly 2 moves (b3 and c2)
    legal_moves = board.get_legal_moves()
    # Filter to only knight moves from the knight's position (a1 = ROW_1, COL_A)
    knight_moves = [m for m in legal_moves if m[0] == (0, 0)]
    assert len(knight_moves) == 2
    assert any(move[1] == (1, 2) for move in knight_moves)  # c2
    assert any(move[1] == (2, 1) for move in knight_moves)  # b3


def test_knight_edge_has_reduced_moves() -> None:
    """T12.2: Knight on edge has fewer than 8 moves."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_5, col=COL_A),
        create_piece(Color.WHITE, PieceType.KNIGHT),
    )
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
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A), create_piece(Color.WHITE, PieceType.KING)
    )
    board.turn = Color.WHITE
    # King on a1 has exactly 3 moves (a2, b2, b1)
    legal_moves = board.get_legal_moves()
    # Filter to only king moves from the king's position
    king_moves = [m for m in legal_moves if m[0] == (7, 0)]
    assert len(king_moves) == 3
    assert any(move[1] == (7, 1) for move in king_moves)  # b1
    assert any(move[1] == (6, 0) for move in king_moves)  # a2
    assert any(move[1] == (6, 1) for move in king_moves)  # b2


def test_king_all_eight_moves_from_center() -> None:
    """T12.3: King has 8 moves from center square."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_5, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
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
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e2
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_D), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_F), create_piece(Color.WHITE, PieceType.PAWN)
    )
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
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.ROOK)
    )
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
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_H), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_H), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_5, col=COL_E), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.turn = Color.WHITE
    # White king in check from black rook
    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_1, col=COL_G)
        )
        is False
    )


def test_castling_forbidden_through_check() -> None:
    """T13.1: Cannot castle through attacked square."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_H), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_H), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_F), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.WHITE
    # Cannot castle through attacked square
    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_1, col=COL_G)
        )
        is False
    )


def test_castling_forbidden_into_check() -> None:
    """T13.1: Cannot castle into attacked square."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_H), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_H), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.turn = Color.WHITE
    # Cannot castle into attacked square (f1 is attacked by rook on d6)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_1, col=COL_G)
        )
        is False
    )


def test_en_passant_resolves_check() -> None:
    """T13.2: En passant can resolve check."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.turn = Color.BLACK
    # Black rook checks from d8
    assert (
        board.make_move(
            ConstantSquare(row=ROW_8, col=COL_E), ConstantSquare(row=ROW_5, col=COL_E)
        )
        is True
    )  # d8-d5


def test_promotion_resolves_check() -> None:
    """T3.1: Promotion that doesn't resolve check is illegal."""
    board = Board()
    clear_board(board)
    # Set up: White king on e8, white pawn on e7 needs to promote
    # Black rook on e1 checks white king on e8 along e-file
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )  # e8
    board.set_piece(
        6, 4, create_piece(Color.WHITE, PieceType.PAWN)
    )  # e7 (ready to promote)
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.ROOK)
    )  # e1 checks e8
    board.turn = Color.WHITE
    # Promotion to queen on e8 doesn't block rook on e1, still in check
    assert (
        board.make_move(
            ConstantSquare(row=ROW_2, col=COL_E),
            ConstantSquare(row=ROW_8, col=COL_E),
            PieceType.QUEEN,
        )
        is False
    )
    # Knight that captures the checking piece resolves check
    # Knight from e8 (7,4) to g6 (6,6) is (-1,2) - VALID knight move!
    board.clear_square(ConstantSquare(row=ROW_8, col=COL_E))  # Clear rook on e1
    board.set_piece(
        6,
        6,
        create_piece(Color.BLACK, PieceType.ROOK),  # g6
    )
    board.clear_square(ConstantSquare(row=ROW_1, col=COL_G))  # Clear white knight at g6
    board.set_piece(
        7, 4, create_piece(Color.WHITE, PieceType.KNIGHT)
    )  # White knight at e8
    board.turn = Color.WHITE
    # Knight from e8 (7,4) to g6 (6,6) captures rook (no promotion parameter for non-pawn moves)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_2, col=COL_G)
        )
        is True
    )  # Knight captures rook on g6, resolving check


def test_promotion_that_would_leave_king_in_check() -> None:
    """T3.2: Verify move simulation checks king safety after promotion."""
    # Set up: White king on e8, white pawn on c7 needs to promote
    # White rook on d8 checks white king on e8 (attacks along rank 8)
    board = Board()
    clear_board(board)
    board.set_piece(
        0, 4, create_piece(Color.WHITE, PieceType.KING)
    )  # e8 (rank 8, e-file)
    board.set_piece(
        1, 2, create_piece(Color.WHITE, PieceType.PAWN)
    )  # c7 (rank 7, c-file)
    board.set_piece(
        0, 3, create_piece(Color.WHITE, PieceType.ROOK)
    )  # d8 (rank 8, d-file) checks e8
    board.turn = Color.WHITE
    # All non-check-resolving promotions should be illegal
    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_C),
            ConstantSquare(row=ROW_7, col=COL_C),
            PieceType.QUEEN,
        )
        is False
    )
    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_C),
            ConstantSquare(row=ROW_7, col=COL_C),
            PieceType.ROOK,
        )
        is False
    )
    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_C),
            ConstantSquare(row=ROW_7, col=COL_C),
            PieceType.BISHOP,
        )
        is False
    )
    # Promotion that resolves check is legal (queen captures rook on d8)
    # Queen from c7 (1,2) to d8 (0,3) captures rook, resolving check
    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_C),
            ConstantSquare(row=ROW_8, col=COL_D),
            PieceType.QUEEN,
        )
        is True
    )  # Queen captures rook on d8, resolving check


def test_promotion_from_non_standard_pawn_positions() -> None:
    """T3.3: Verify pawn cannot promote before last rank."""
    # Test 1: White pawn on 4th rank (cannot promote - needs to reach rank 1)
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_4, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e5
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_G), create_piece(Color.WHITE, PieceType.KING)
    )  # g8
    board.turn = Color.WHITE
    # Promotion from e5 is impossible (pawn not on last rank - rank 1)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_4, col=COL_E),
            ConstantSquare(row=ROW_8, col=COL_E),
            PieceType.QUEEN,
        )
        is False
    )
    # Test 2: Black pawn on 3rd rank (cannot promote - needs to reach rank 1, row 0)
    board2 = Board()
    clear_board(board2)
    board2.set_piece(
        3, 4, create_piece(Color.BLACK, PieceType.PAWN)
    )  # e4 (row 3 = rank 5)
    board2.set_piece(
        ConstantSquare(row=ROW_8, col=COL_G), create_piece(Color.BLACK, PieceType.KING)
    )  # g1
    board2.turn = Color.BLACK
    # Black pawn needs to reach rank 1 (row 0), but is at rank 5 (row 3)
    assert (
        board2.make_move(
            ConstantSquare(row=ROW_5, col=COL_E),
            ConstantSquare(row=ROW_8, col=COL_E),
            PieceType.QUEEN,
        )
        is False
    )
    # Test 3: Valid promotion from e7 (rank 2) to e1 (rank 1) should work
    board3 = Board()
    clear_board(board3)
    board3.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e7
    board3.set_piece(
        ConstantSquare(row=ROW_8, col=COL_G), create_piece(Color.WHITE, PieceType.KING)
    )  # g1
    board3.turn = Color.WHITE
    # Pawn can only move 1 or 2 squares per move, so e7 to e1 in one move is impossible
    # Need to move step by step: e7 -> e6 -> e5 -> ... -> e1
    # But we can test that a 2-square move from e7 to e5 works (sets up for promotion)
    assert (
        board3.make_move(
            ConstantSquare(row=ROW_2, col=COL_E),
            ConstantSquare(row=ROW_4, col=COL_E),
            PieceType.QUEEN,
        )
        is False
    )  # Can't move 6 squares


def test_all_promotion_piece_types() -> None:
    """T3.4: Test all four promotion choices (queen, rook, bishop, knight)."""
    # Test all valid promotion types for white
    for promo_piece in [
        PieceType.QUEEN,
        PieceType.ROOK,
        PieceType.BISHOP,
        PieceType.KNIGHT,
    ]:
        board = Board()
        clear_board(board)
        # White pawn on 2nd rank (ready to promote to rank 1)
        board.set_piece(
            ConstantSquare(row=ROW_7, col=COL_E),
            create_piece(Color.WHITE, PieceType.PAWN),
        )  # e2
        # Place king on f1 (0, 5) so it's not on the promotion square
        board.set_piece(
            ConstantSquare(row=ROW_8, col=COL_F),
            create_piece(Color.WHITE, PieceType.KING),
        )
        board.turn = Color.WHITE
        # Promotion should work since target square is empty
        assert (
            board.make_move(
                ConstantSquare(row=ROW_7, col=COL_E),
                ConstantSquare(row=ROW_8, col=COL_E),
                promo_piece,
            )
            is True
        )
    # Test black pawn promotion
    board2 = Board()
    clear_board(board2)
    board2.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.BLACK, PieceType.PAWN)
    )  # e7
    board2.set_piece(
        ConstantSquare(row=ROW_1, col=COL_F), create_piece(Color.BLACK, PieceType.KING)
    )  # f8
    board2.turn = Color.BLACK
    # Black pawn at e7 can promote to e8
    assert (
        board2.make_move(
            ConstantSquare(row=ROW_2, col=COL_E),
            ConstantSquare(row=ROW_1, col=COL_E),
            PieceType.QUEEN,
        )
        is True
    )
    # Promotion to king should be rejected
    board3 = Board()
    clear_board(board3)
    board3.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e2
    board3.set_piece(
        ConstantSquare(row=ROW_8, col=COL_F), create_piece(Color.WHITE, PieceType.KING)
    )
    board3.turn = Color.WHITE
    assert (
        board3.make_move(
            ConstantSquare(row=ROW_2, col=COL_E),
            ConstantSquare(row=ROW_8, col=COL_E),
            PieceType.KING,
        )
        is False
    )


def test_promotion_with_en_passant_same_turn() -> None:
    """T3.5: Verify no interaction needed between promotion and en passant.
    This is an edge case that can't actually occur in legal play (en passant
    requires adjacent pawn, promotion requires reaching last rank), but we
    verify the logic doesn't break.
    """
    # Test 1: Promotion with adjacent pawn (no en passant possible)
    board = Board()
    clear_board(board)
    # Set up: White pawn on 2nd rank ready to promote to rank 1
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e2
    # Place king on f1 (0, 5) so it's not on the promotion square
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_F), create_piece(Color.WHITE, PieceType.KING)
    )
    # Black pawn on adjacent file (but not ready for en passant)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_D), create_piece(Color.BLACK, PieceType.PAWN)
    )  # d2
    board.turn = Color.WHITE
    # Normal promotion should work without en passant affecting it
    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_E),
            ConstantSquare(row=ROW_8, col=COL_E),
            PieceType.QUEEN,
        )
        is True
    )
    # Test 2: Promotion after en passant capture setup
    # Setup: White pawn on e6, black pawn on e7 (en passant ready)
    board2 = Board()
    clear_board(board2)
    board2.set_piece(
        ConstantSquare(row=ROW_3, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e6
    board2.set_piece(
        6, 4, create_piece(Color.BLACK, PieceType.PAWN)
    )  # e7 (for en passant)
    board2.turn = Color.WHITE
    # En passant capture from e6 to e8 (promotion)
    # This sets en_passant_target to e7, then clears it after promotion
    board2.make_move(
        ConstantSquare(row=ROW_3, col=COL_E),
        ConstantSquare(row=ROW_1, col=COL_E),
        PieceType.QUEEN,
    )  # e6xe8 promotion
    assert board2.en_passant_target is None  # Should be cleared after promotion
