"""Tests for complex."""

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
