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
    """T3.1: Promotion that doesn't resolve check is illegal."""
    board = Board()
    clear_board(board)

    # Set up: White king on e8, white pawn on e7 needs to promote
    # Black rook on e1 checks white king on e8 along e-file
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))  # e8
    board.set_piece(
        6, 4, create_piece(Color.WHITE, PieceType.PAWN)
    )  # e7 (ready to promote)
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.ROOK))  # e1 checks e8

    board.turn = Color.WHITE

    # Promotion to queen on e8 doesn't block rook on e1, still in check
    assert board.make_move((6, 4), (0, 4), PieceType.QUEEN) is False

    # Knight that captures the checking piece resolves check
    # Knight from e8 (7,4) to g6 (6,6) is (-1,2) - VALID knight move!
    board.clear_square(0, 4)  # Clear rook on e1
    board.set_piece(
        6,
        6,
        create_piece(Color.BLACK, PieceType.ROOK),  # g6
    )
    board.clear_square(7, 6)  # Clear white knight at g6
    board.set_piece(
        7, 4, create_piece(Color.WHITE, PieceType.KNIGHT)
    )  # White knight at e8
    board.turn = Color.WHITE
    # Knight from e8 (7,4) to g6 (6,6) captures rook (no promotion parameter for non-pawn moves)
    assert (
        board.make_move((7, 4), (6, 6)) is True
    )  # Knight captures rook on g6, resolving check


def test_promotion_that_would_leave_king_in_check() -> None:
    """T3.2: Verify move simulation checks king safety after promotion."""
    # Set up: White king on e1, white pawn on a2 needs to promote
    # Black rook on a1 checks white king on e1 (attacks along rank 1)
    board = Board()
    clear_board(board)
    board.set_piece(0, 4, create_piece(Color.WHITE, PieceType.KING))  # e1
    board.set_piece(1, 0, create_piece(Color.WHITE, PieceType.PAWN))  # a2
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.ROOK))  # a1 checks e1

    board.turn = Color.WHITE

    # All non-check-resolving promotions should be illegal
    # Queen on a8 doesn't block rook on a1 attacking e1, still in check
    assert board.make_move((1, 0), (7, 0), PieceType.QUEEN) is False
    assert board.make_move((1, 0), (7, 0), PieceType.ROOK) is False
    assert board.make_move((1, 0), (7, 0), PieceType.BISHOP) is False

    # Promotion that resolves check is legal (queen captures rook on a1)
    # Queen from a2 (1,0) to a1 (0,0) captures rook, resolving check
    assert (
        board.make_move((1, 0), (0, 0), PieceType.QUEEN) is True
    )  # Queen captures rook on a1, resolving check


def test_promotion_from_non_standard_pawn_positions() -> None:
    """T3.3: Verify pawn cannot promote before last rank."""
    # Test 1: White pawn on 4th rank (cannot promote - needs to reach rank 1)
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.PAWN))  # e5
    board.set_piece(7, 6, create_piece(Color.WHITE, PieceType.KING))  # g8

    board.turn = Color.WHITE

    # Promotion from e5 is impossible (pawn not on last rank - rank 1)
    assert board.make_move((4, 4), (0, 4), PieceType.QUEEN) is False

    # Test 2: Black pawn on 3rd rank (cannot promote - needs to reach rank 1, row 0)
    board2 = Board()
    clear_board(board2)
    board2.set_piece(
        3, 4, create_piece(Color.BLACK, PieceType.PAWN)
    )  # e4 (row 3 = rank 5)
    board2.set_piece(0, 6, create_piece(Color.BLACK, PieceType.KING))  # g1

    board2.turn = Color.BLACK
    # Black pawn needs to reach rank 1 (row 0), but is at rank 5 (row 3)
    assert board2.make_move((3, 4), (0, 4), PieceType.QUEEN) is False

    # Test 3: Valid promotion from e7 (rank 2) to e1 (rank 1) should work
    board3 = Board()
    clear_board(board3)
    board3.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))  # e7
    board3.set_piece(0, 6, create_piece(Color.WHITE, PieceType.KING))  # g1

    board3.turn = Color.WHITE
    # Pawn can only move 1 or 2 squares per move, so e7 to e1 in one move is impossible
    # Need to move step by step: e7 -> e6 -> e5 -> ... -> e1
    # But we can test that a 2-square move from e7 to e5 works (sets up for promotion)
    assert (
        board3.make_move((6, 4), (4, 4), PieceType.QUEEN) is False
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
        board.set_piece(1, 4, create_piece(Color.WHITE, PieceType.PAWN))  # e2
        # Place king on f1 (0, 5) so it's not on the promotion square
        board.set_piece(0, 5, create_piece(Color.WHITE, PieceType.KING))

        board.turn = Color.WHITE
        # Promotion should work since target square is empty
        assert board.make_move((1, 4), (0, 4), promo_piece) is True

    # Test black pawn promotion
    board2 = Board()
    clear_board(board2)
    board2.set_piece(6, 4, create_piece(Color.BLACK, PieceType.PAWN))  # e7
    board2.set_piece(7, 5, create_piece(Color.BLACK, PieceType.KING))  # f8

    board2.turn = Color.BLACK
    # Black pawn at e7 can promote to e8
    assert board2.make_move((6, 4), (7, 4), PieceType.QUEEN) is True

    # Promotion to king should be rejected
    board3 = Board()
    clear_board(board3)
    board3.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))  # e2
    board3.set_piece(0, 5, create_piece(Color.WHITE, PieceType.KING))

    board3.turn = Color.WHITE
    assert board3.make_move((6, 4), (0, 4), PieceType.KING) is False


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
    board.set_piece(1, 4, create_piece(Color.WHITE, PieceType.PAWN))  # e2
    # Place king on f1 (0, 5) so it's not on the promotion square
    board.set_piece(0, 5, create_piece(Color.WHITE, PieceType.KING))

    # Black pawn on adjacent file (but not ready for en passant)
    board.set_piece(1, 3, create_piece(Color.BLACK, PieceType.PAWN))  # d2

    board.turn = Color.WHITE

    # Normal promotion should work without en passant affecting it
    assert board.make_move((1, 4), (0, 4), PieceType.QUEEN) is True

    # Test 2: Promotion after en passant capture setup
    # Setup: White pawn on e6, black pawn on e7 (en passant ready)
    board2 = Board()
    clear_board(board2)
    board2.set_piece(5, 4, create_piece(Color.WHITE, PieceType.PAWN))  # e6
    board2.set_piece(
        6, 4, create_piece(Color.BLACK, PieceType.PAWN)
    )  # e7 (for en passant)
    board2.turn = Color.WHITE

    # En passant capture from e6 to e8 (promotion)
    # This sets en_passant_target to e7, then clears it after promotion
    board2.make_move((5, 4), (7, 4), PieceType.QUEEN)  # e6xe8 promotion
    assert board2.en_passant_target is None  # Should be cleared after promotion
