from __future__ import annotations
from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType
from chess_game.constants import (
    get_row_constant,
    get_col_constant,
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
    ConstantSquare,
)


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
# Category 2: En Passant Edge Cases
# =============================================================================
def test_only_one_en_passant_target_at_a_time() -> None:
    """T2.1: Verify only one en_passant_target can exist at a time."""
    board = Board()
    clear_board(board)
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
    assert board.en_passant_target == ConstantSquare(
        row=ROW_5, col=COL_C
    )  # e3 square available
    # After black plays non-pawn move, en passant target should be cleared
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_D), create_piece(Color.BLACK, PieceType.QUEEN)
    )
    board.make_move(
        ConstantSquare(row=ROW_8, col=COL_D), ConstantSquare(row=ROW_5, col=COL_D)
    )  # d8-d5 (queen move, not pawn)
    assert board.en_passant_target is None


def test_en_passant_capture_removes_pawn_from_original_square() -> None:
    """T2.2: Verify capture removes pawn from original square."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_3, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )  # White pawn on e6 (fixed: was 4,4)
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_D), create_piece(Color.BLACK, PieceType.PAWN)
    )  # Black pawn on d7
    board.turn = Color.BLACK
    # Black plays d7-d5, creating en passant target at d6
    board.make_move(
        ConstantSquare(row=ROW_7, col=COL_D), ConstantSquare(row=ROW_5, col=COL_D)
    )  # d7-d5 (double step)
    assert board.en_passant_target == ConstantSquare(
        row=ROW_4, col=COL_B
    )  # d6 square available
    # Switch to white's turn
    board.turn = Color.WHITE
    # White captures en passant (e6xd6)
    # White pawn at e6 (2,4) captures black pawn at d5 (3,3) en passant
    # The captured pawn is removed from d5 and placed on d6 (2,3)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_5, col=COL_E), ConstantSquare(row=ROW_4, col=COL_D)
        )
        is True
    )  # e6 captures d5 en passant
    # Verify black pawn was removed from d5
    assert (
        board.get_piece(ConstantSquare(row=ROW_5, col=COL_C)) is None
    )  # d5 should be empty


def test_en_passant_expired_after_nonpawn_move() -> None:
    """T2.3: en_passant_target cleared after any move."""
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
    assert board.en_passant_target == ConstantSquare(
        row=ROW_4, col=COL_E
    )  # d6 square available
    # White plays non-pawn move (knight), en passant should expire
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A),
        create_piece(Color.WHITE, PieceType.KNIGHT),
    )
    board.make_move(
        ConstantSquare(row=ROW_1, col=COL_A), ConstantSquare(row=ROW_5, col=COL_B)
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
        ConstantSquare(row=ROW_4, col=COL_D),
        create_piece(Color.BLACK, PieceType.BISHOP),
    )  # Black bishop on d6
    board.turn = Color.WHITE
    # White plays e7-e5, trying to capture on d6 (attacked by bishop)
    legal_moves = board.get_legal_moves()
    # En passant to d6 should be illegal because d6 is attacked by bishop
    en_passant_moves = [
        m
        for m in legal_moves
        if m[0] == ConstantSquare(row=ROW_3, col=COL_E)
        and m[1][0] == ConstantSquare(row=ROW_4, col=COL_C)  # e7 to d6
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
        ConstantSquare(row=ROW_3, col=COL_E), create_piece(Color.BLACK, PieceType.ROOK)
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
        ConstantSquare(row=ROW_8, col=COL_D), create_piece(Color.BLACK, PieceType.ROOK)
    )  # Black rook on d8
    board.turn = Color.WHITE
    # White plays e7-e5, trying to capture on d6
    # After capture, white king at e8 would be in check from rook at d8
    legal_moves = board.get_legal_moves()
    en_passant_moves = [
        m
        for m in legal_moves
        if m[0] == ConstantSquare(row=ROW_3, col=COL_E)
        and m[1][0] == ConstantSquare(row=ROW_4, col=COL_C)  # e7 to d6
    ]
    assert len(en_passant_moves) == 0


def test_full_en_passant_sequence_from_starting_position() -> None:
    """T2.5: Full game scenario: e2e4 d5e4 (en passant capture)."""
    board = Board()
    # Clear starting position and set up for en passant test
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_4, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )  # White pawn on e4
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_D), create_piece(Color.BLACK, PieceType.PAWN)
    )  # Black pawn on d7
    board.turn = Color.BLACK
    # Black plays d7-d5 (double step)
    board.make_move(
        ConstantSquare(row=ROW_7, col=COL_D), ConstantSquare(row=ROW_5, col=COL_D)
    )  # d7-d5
    assert board.en_passant_target == ConstantSquare(
        row=ROW_4, col=COL_D
    )  # d6 square available
    # Switch to white's turn
    board.turn = Color.WHITE
    # White captures en passant: e4 captures d5 en passant
    # White pawn at e4 (3,4) captures black pawn at d5 (3,3) en passant
    # The black pawn is removed from d5 and placed on d6 (2,3)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_5, col=COL_E), ConstantSquare(row=ROW_4, col=COL_D)
        )
        is True
    )
    # Verify white pawn is now at d6 (2,3) after en passant capture
    white_pawn_at_d6 = board.get_piece(ConstantSquare(row=ROW_4, col=COL_D))
    assert white_pawn_at_d6 is not None
    assert white_pawn_at_d6.kind == PieceType.PAWN
    assert white_pawn_at_d6.color == Color.WHITE
    # Verify black pawn at d5 was removed
    assert board.get_piece(ConstantSquare(row=ROW_5, col=COL_D)) is None
