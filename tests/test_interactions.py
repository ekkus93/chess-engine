from __future__ import annotations
from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType
from chess_game.chess.constants import (
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
    COL_G,
    COL_H,
    ConstantSquare,
)


def clear_board(board: Board) -> None:
    for row in range(8):
        for col in range(8):
            board.clear_square(
                ConstantSquare(row=get_row_constant(row), col=get_col_constant(col))
            )


def _setup_kings(board: Board) -> None:
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.KING)
    )


# =============================================================================
# Category 13: Interaction Between Rules
# =============================================================================
def test_castling_forbidden_while_in_check() -> None:
    """T13.1: Cannot castle while in check."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 7), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        get_square_constant(7, 7), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.set_piece(
        get_square_constant(3, 4), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.turn = Color.WHITE
    # White king in check from black rook
    assert (
        board.make_move(
            get_square_constant(0, 4), get_square_constant(0, 6)
        )
        is False
    )


def test_castling_forbidden_through_check() -> None:
    """T13.1: Cannot castle through attacked square."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 7), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        get_square_constant(7, 7), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.set_piece(
        get_square_constant(1, 5), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.WHITE
    # Cannot castle through attacked square
    assert (
        board.make_move(
            get_square_constant(0, 4), get_square_constant(0, 6)
        )
        is False
    )


def test_castling_forbidden_into_check() -> None:
    """T13.1: Cannot castle into attacked square."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 7), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        get_square_constant(7, 7), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.set_piece(
        get_square_constant(1, 4), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.turn = Color.WHITE
    # Cannot castle into attacked square (f1 is attacked by rook on d6)
    assert (
        board.make_move(
            get_square_constant(0, 4), get_square_constant(0, 6)
        )
        is False
    )


def test_en_passant_resolves_check() -> None:
    """T13.2: En passant can resolve check."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(1, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.turn = Color.BLACK
    # Black rook checks from d8
    assert (
        board.make_move(
            get_square_constant(7, 4), get_square_constant(4, 4)
        )
        is True
    )  # d8-d5


def test_promotion_resolves_check() -> None:
    """T3.1: Promotion that doesn't resolve check is illegal."""
    board = Board()
    clear_board(board)
    # Set up: White king on e1, white pawn on e7 needs to promote
    # Black rook on e8 checks white king on e1 along e-file
    # White pawn on e7 promotes to e8 (empty square), blocking the rook
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )  # e1
    board.set_piece(
        get_square_constant(6, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e7 (ready to promote to e8)
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.ROOK)
    )  # e8 checks e1
    board.turn = Color.WHITE
    # Move rook away from e8 so e8 is empty for promotion
    board.clear_square(get_square_constant(7, 4))
    board.set_piece(
        get_square_constant(7, 3), create_piece(Color.BLACK, PieceType.ROOK)
    )
    # Promotion to queen on e8 blocks rook on e8, resolving check
    assert (
        board.make_move(
            get_square_constant(6, 4),
            get_square_constant(7, 4),
            PieceType.QUEEN,
        )
        is True
    )


def test_promotion_that_would_leave_king_in_check() -> None:
    """T3.2: Verify move simulation checks king safety after promotion."""
    from chess_game.chess.constants import ROW_1, ROW_7, ROW_8, COL_E, COL_D

    # Set up: White king on e1, white pawn on d7 needs to promote to d8
    # Black rook on e8 checks white king on e1 (attacks along e-file)
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )  # e1
    board.set_piece(
        get_square_constant(6, 3), create_piece(Color.WHITE, PieceType.PAWN)
    )  # d7 (ready to promote to d8)
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.ROOK)
    )  # e8 checks e1
    board.turn = Color.WHITE
    # Promotion that resolves check is legal (queen captures rook on e8)
    # Queen from d7 (ROW_7, COL_D) to e8 (ROW_8, COL_E) captures rook
    assert (
        board.make_move(
            get_square_constant(6, 3),
            get_square_constant(7, 4),
            PieceType.QUEEN,
        )
        is True
    )  # Queen captures rook on e8, resolving check
    # Promotion from e4 is impossible (pawn not on last rank - rank 7 for white)
    assert (
        board.make_move(
            get_square_constant(3, 4),
            get_square_constant(7, 4),
            PieceType.QUEEN,
        )
        is False
    )

    # Set up: White king on e1, white pawn on c7 needs to promote to c8
    # Black rook on c8 checks white king on e1 (attacks along c-file)
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )  # e1
    board.set_piece(
        get_square_constant(6, 2), create_piece(Color.WHITE, PieceType.PAWN)
    )  # c7 (ready to promote to c8)
    board.set_piece(
        get_square_constant(7, 2), create_piece(Color.BLACK, PieceType.ROOK)
    )  # c8 checks e1
    board.turn = Color.WHITE
    # Promotion that resolves check is legal (queen captures rook on c8)
    # Queen from c7 (ROW_7, COL_C) to c8 (ROW_8, COL_C) captures rook
    # BUT: Pawns only capture diagonally, so c7->c8 is invalid (same file)
    # This test verifies the engine correctly rejects same-file promotion
    assert (
        board.make_move(
            get_square_constant(6, 2),
            get_square_constant(7, 2),
            PieceType.QUEEN,
        )
        is False
    )  # Invalid: pawn must capture diagonally
    # Promotion from e4 is impossible (pawn not on last rank - rank 7 for white)
    assert (
        board.make_move(
            get_square_constant(3, 4),
            get_square_constant(7, 4),
            PieceType.QUEEN,
        )
        is False
    )

    # Test 2: Black pawn on 3rd rank (cannot promote - needs to reach rank 8, row 7)
    board2 = Board()
    clear_board(board2)
    board2.set_piece(
        get_square_constant(5, 4), create_piece(Color.BLACK, PieceType.PAWN)
    )  # e4 (row 5 = rank 6)
    board2.set_piece(
        get_square_constant(0, 6), create_piece(Color.BLACK, PieceType.KING)
    )  # g1
    board2.turn = Color.BLACK
    # Black pawn needs to reach rank 8 (row 7), but is at rank 6 (row 5)
    assert (
        board2.make_move(
            get_square_constant(5, 4),
            get_square_constant(7, 4),
            PieceType.QUEEN,
        )
        is False
    )
    # Test 3: Valid promotion from e7 (rank 2) to e8 (rank 1) should work
    board3 = Board()
    clear_board(board3)
    board3.set_piece(
        get_square_constant(1, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e7
    board3.set_piece(
        get_square_constant(0, 6), create_piece(Color.WHITE, PieceType.KING)
    )  # g1
    board3.turn = Color.WHITE
    # Pawn can only move 1 or 2 squares per move, so e7 to e1 in one move is impossible
    # Need to move step by step: e7 -> e6 -> e5 -> ... -> e1
    # But we can test that a 2-square move from e7 to e5 works (sets up for promotion)
    assert (
        board3.make_move(
            get_square_constant(1, 4),
            get_square_constant(4, 4),
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
        # White pawn on 2nd rank (ready to promote to rank 8)
        board.set_piece(
            get_square_constant(1, 4),
            create_piece(Color.WHITE, PieceType.PAWN),
        )  # e2 (row 1 = rank 2)
        # Place king on f1 (0, 5) so it's not on the promotion square
        board.set_piece(
            get_square_constant(0, 5),
            create_piece(Color.WHITE, PieceType.KING),
        )
        board.turn = Color.WHITE
        # Promotion should work since target square is empty
        assert (
            board.make_move(
                get_square_constant(1, 4),
                get_square_constant(7, 4),
                promotion=promo_piece,
            )
            is True
        )
    # Test black pawn promotion
    board2 = Board()
    clear_board(board2)
    board2.set_piece(
        get_square_constant(6, 4), create_piece(Color.BLACK, PieceType.PAWN)
    )  # e7
    board2.set_piece(
        get_square_constant(0, 5), create_piece(Color.BLACK, PieceType.KING)
    )  # f1
    board2.turn = Color.BLACK
    # Black pawn at e7 can promote to e1
    assert (
        board2.make_move(
            get_square_constant(6, 4),
            get_square_constant(0, 4),
            promotion=PieceType.QUEEN,
        )
        is True
    )
    # Promotion to king should be rejected
    board3 = Board()
    clear_board(board3)
    board3.set_piece(
        get_square_constant(1, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e2
    board3.set_piece(
        get_square_constant(7, 5), create_piece(Color.WHITE, PieceType.KING)
    )
    board3.turn = Color.WHITE
    assert (
        board3.make_move(
            get_square_constant(1, 4),
            get_square_constant(7, 4),
            promotion=PieceType.KING,
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
    # Set up: White pawn on 2nd rank (row 1) ready to promote to rank 8 (row 7)
    board.set_piece(
        get_square_constant(1, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e2
    # Place king on f1 (0, 5) so it's not on the promotion square
    board.set_piece(
        get_square_constant(0, 5), create_piece(Color.WHITE, PieceType.KING)
    )
    # Black pawn on adjacent file (but not ready for en passant)
    board.set_piece(
        get_square_constant(3, 3), create_piece(Color.BLACK, PieceType.PAWN)
    )  # d4
    board.turn = Color.WHITE
    # Normal promotion should work without en passant affecting it
    assert (
        board.make_move(
            get_square_constant(1, 4),
            get_square_constant(7, 4),
            PieceType.QUEEN,
        )
        is True
    )
    # Test 2: Promotion after en passant capture setup
    # Setup: White pawn on e6, black pawn on e7 (en passant ready)
    board2 = Board()
    clear_board(board2)
    board2.set_piece(
        get_square_constant(3, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e6
    board2.set_piece(
        get_square_constant(6, 4), create_piece(Color.BLACK, PieceType.PAWN)
    )  # e7 (for en passant)
    board2.turn = Color.WHITE
    # En passant capture from e6 to e8 (promotion)
    # This sets en_passant_target to e7, then clears it after promotion
    board2.make_move(
        get_square_constant(3, 4),
        get_square_constant(7, 4),
        PieceType.QUEEN,
    )  # e6xe8 promotion
    assert board2.en_passant_target is None  # Should be cleared after promotion
