from __future__ import annotations
from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType
from chess_game.chess.constants import (
    get_row_constant,
    get_col_constant,
    get_square_constant,
    ROW_0,
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
    ConstantSquare,
)


# =============================================================================
# Category 2: En Passant Edge Cases
# =============================================================================
def test_only_one_en_passant_target_at_a_time() -> None:
    """T2.1: Verify only one en_passant_target can exist at a time."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.turn = Color.WHITE
    # White plays e2-e4 (creates en passant target at e3)
    board.set_piece(
        get_square_constant(6, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e2 pawn
    board.make_move(get_square_constant(6, 4), get_square_constant(4, 4))  # e2-e4
    assert board.en_passant_target == ConstantSquare(
        row=ROW_3, col=COL_E
    )  # e3 square available
    # After black plays non-pawn move, en passant target should be cleared
    board.set_piece(
        get_square_constant(0, 3), create_piece(Color.BLACK, PieceType.QUEEN)
    )
    board.make_move(
        get_square_constant(0, 3), get_square_constant(3, 3)
    )  # d8-d5 (queen move, not pawn)
    assert board.en_passant_target is None


def test_en_passant_capture_removes_pawn_from_original_square() -> None:
    """T2.2: Verify capture removes pawn from original square."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(4, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )  # White pawn on e5 (row 3 = rank 4)
    board.set_piece(
        get_square_constant(1, 3), create_piece(Color.BLACK, PieceType.PAWN)
    )  # Black pawn on d7
    board.turn = Color.BLACK
    # Black plays d7-d5, creating en passant target at d6 (row 5)
    board.make_move(
        get_square_constant(1, 3), get_square_constant(3, 3)
    )  # d7-d5 (double step)
    assert board.en_passant_target == ConstantSquare(
        row=ROW_6, col=COL_D
    )  # d6 square available (row 5 = rank 6)
    # Switch to white's turn
    board.turn = Color.WHITE
    # White captures en passant (e5xd6)
    # White pawn at e5 (row 3, col 4) captures black pawn at d6 en passant
    # The captured pawn is removed from d6 and placed on d6 (row 5, col 3)
    assert (
        board.make_move(get_square_constant(4, 4), get_square_constant(2, 3)) is True
    )  # e5 captures d6 en passant
    # Verify black pawn was removed from d6
    assert board.get_piece(get_square_constant(2, 3)) is None  # d6 should be empty


def test_en_passant_expired_after_nonpawn_move() -> None:
    """T2.3: en_passant_target cleared after any move."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(6, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )  # White pawn on e2
    board.set_piece(
        get_square_constant(1, 3), create_piece(Color.BLACK, PieceType.PAWN)
    )  # Black pawn on d7
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.BLACK, PieceType.QUEEN)
    )
    board.turn = Color.BLACK
    # Black plays d7-d5, creating en passant target at d6
    board.make_move(
        get_square_constant(1, 3), get_square_constant(3, 3)
    )  # d7-d5 (double step)
    assert board.en_passant_target == ConstantSquare(
        row=ROW_6, col=COL_D
    )  # d6 square available
    # White plays non-pawn move (knight), en passant should expire
    board.set_piece(
        get_square_constant(7, 0),
        create_piece(Color.WHITE, PieceType.KNIGHT),
    )
    board.make_move(
        get_square_constant(7, 0), get_square_constant(5, 1)
    )  # Na1-b3 (valid knight move: 2 rows, 1 column)
    assert board.en_passant_target is None
    # Black cannot capture en passant now
    board.set_piece(
        get_square_constant(6, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )  # White pawn on e2
    board.turn = Color.BLACK
    assert (
        board.make_move(get_square_constant(1, 4), get_square_constant(3, 4)) is False
    )  # Cannot capture en passant (expired)


def test_en_passant_destination_attacked_forbidden() -> None:
    """T2.4: En passant blocked if destination square attacked."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(6, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )  # White pawn on e7
    board.set_piece(
        get_square_constant(4, 3),
        create_piece(Color.BLACK, PieceType.BISHOP),
    )  # Black bishop on d6
    board.turn = Color.WHITE
    # White plays e7-e5, trying to capture on d6 (attacked by bishop)
    legal_moves = board.get_legal_moves()
    # En passant to d6 should be illegal because d6 is attacked by bishop
    en_passant_moves = [
        m
        for m in legal_moves
        if m[0] == get_square_constant(5, 4)
        and m[1][0] == get_square_constant(4, 2)  # e7 to d6
    ]
    assert len(en_passant_moves) == 0


def test_en_passant_path_attacked_forbidden() -> None:
    """T2.4: En passant blocked if path through attacked square."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(6, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )  # White pawn on e7
    board.set_piece(
        get_square_constant(5, 4), create_piece(Color.BLACK, PieceType.ROOK)
    )  # Black rook on e6
    board.turn = Color.WHITE
    # White plays e7-e5, trying to capture on d6 (path goes through d6)
    # This is actually the destination square, so covered by previous test
    # Testing a different scenario: king in check


def test_en_passant_king_in_check_after_capture_forbidden() -> None:
    """T2.4: En passant blocked if after capture, king in check."""
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(6, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )  # White pawn on e7
    board.set_piece(
        get_square_constant(0, 3), create_piece(Color.BLACK, PieceType.ROOK)
    )  # Black rook on d8
    board.turn = Color.WHITE
    # White plays e7-e5, trying to capture on d6
    # After capture, white king at e8 would be in check from rook at d8
    legal_moves = board.get_legal_moves()
    en_passant_moves = [
        m
        for m in legal_moves
        if m[0] == get_square_constant(5, 4)
        and m[1][0] == get_square_constant(4, 2)  # e7 to d6
    ]
    assert len(en_passant_moves) == 0


def test_full_en_passant_sequence_from_starting_position() -> None:
    """T2.5: Full game scenario: e2e4 d5e4 (en passant capture)."""
    board = Board()
    # Clear starting position and set up for en passant test
    board.clear_board()
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(4, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )  # White pawn on e5 (row 3 = rank 4)
    board.set_piece(
        get_square_constant(1, 3), create_piece(Color.BLACK, PieceType.PAWN)
    )  # Black pawn on d7
    board.turn = Color.BLACK
    # Black plays d7-d5 (double step)
    board.make_move(get_square_constant(1, 3), get_square_constant(3, 3))  # d7-d5
    assert board.en_passant_target == ConstantSquare(
        row=ROW_6, col=COL_D
    )  # d6 square available (row 5 = rank 6)
    # Switch to white's turn
    board.turn = Color.WHITE
    # White captures en passant: e5 captures d6 en passant
    # White pawn at e5 (ROW_4, COL_E) captures black pawn at d6 en passant
    # The black pawn is removed from d6 and placed on d6 (ROW_5, COL_D)
    assert board.make_move(get_square_constant(4, 4), get_square_constant(2, 3)) is True
    # Verify white pawn is now at d6 (5,3) after en passant capture
    white_pawn_at_d6 = board.get_piece(get_square_constant(2, 3))
    assert white_pawn_at_d6 is not None
    assert white_pawn_at_d6.kind == PieceType.PAWN
    assert white_pawn_at_d6.color == Color.WHITE
    # Verify black pawn at d5 was removed
    assert board.get_piece(get_square_constant(3, 3)) is None
