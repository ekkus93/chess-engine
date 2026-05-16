"""Task 7: Promotion multiplicity perft-style tests

Verifies that each promotion destination contributes exactly 4 legal moves
(one per promotion type: queen, rook, bishop, knight).
"""

from chess_game.chess.board.board import Board, create_piece
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq


def _count_legal_moves(board: Board) -> int:
    """Count total legal moves for the side to move."""
    return len(board.get_legal_moves())


def _count_promo_moves(board: Board, start_str: str, end_str: str) -> int:
    """Count promotion moves from start to end."""
    start = sq(start_str)
    end = sq(end_str)
    return sum(
        1 for s, e, p in board.get_legal_moves()
        if s == start and e == end and p is not None
    )


def _setup_quiet_promo() -> Board:
    """White pawn on e7, e8 empty, kings on c1/g8, white to move."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("c1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e7"), create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE
    return board


def test_one_quiet_promo_destination_gives_4_moves() -> None:
    """One quiet promotion destination = exactly 4 legal moves."""
    board = _setup_quiet_promo()
    promo_count = _count_promo_moves(board, "e7", "e8")
    assert promo_count == 4


def test_one_capture_promo_destination_gives_4_moves() -> None:
    """One capture promotion destination = exactly 4 legal moves."""
    board = _setup_quiet_promo()
    board.set_piece(sq("f8"), create_piece(Color.BLACK, PieceType.KNIGHT))
    promo_count = _count_promo_moves(board, "e7", "f8")
    assert promo_count == 4


def test_two_promo_destinations_give_8_moves() -> None:
    """Two promotion destinations (quiet + capture) = exactly 8 legal moves."""
    board = _setup_quiet_promo()
    board.set_piece(sq("f8"), create_piece(Color.BLACK, PieceType.KNIGHT))
    quiet = _count_promo_moves(board, "e7", "e8")
    capture = _count_promo_moves(board, "e7", "f8")
    assert quiet == 4
    assert capture == 4
    # Total legal moves = quiet promo (4) + capture promo (4)
    # (plus any non-promo moves if applicable, but in this minimal board there are none)
    assert quiet + capture == 8


def test_black_quiet_promo_gives_4_moves() -> None:
    """Black quiet promotion destination = exactly 4 legal moves."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("c8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e2"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK
    promo_count = _count_promo_moves(board, "e2", "e1")
    assert promo_count == 4


def test_black_capture_promo_gives_4_moves() -> None:
    """Black capture promotion destination = exactly 4 legal moves."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("c8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e2"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("f1"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.turn = Color.BLACK
    promo_count = _count_promo_moves(board, "e2", "f1")
    assert promo_count == 4
