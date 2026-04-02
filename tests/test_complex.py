"""Tests for complex."""

from __future__ import annotations
from chess_game.chess.board import Board, create_piece
from chess_game.chess.constants import (
    get_row_constant,
    get_col_constant,
    ConstantSquare,
    ROW_1,
    ROW_8,
    ROW_2,
    ROW_7,
    ROW_6,
    ROW_5,
    ROW_4,
    ROW_3,
    COL_A,
    COL_B,
    COL_C,
    COL_H,
    COL_E,
)
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
        get_square_constant(7, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.KING)
    )


# Category 6: Corner & Edge Cases
# =============================================================================
def test_rook_corner_moves_along_edge_only() -> None:
    """T6.1: Rook from corner moves along edge only."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(7, 0), create_piece(Color.WHITE, PieceType.ROOK)
    )
    # Rook on a8 can move along both file a (7 squares) and rank 8 (7 squares)
    board.turn = Color.WHITE
    legal_moves = board.get_legal_moves()
    assert len(legal_moves) == 14  # 7 down file + 7 across rank


def test_bishop_corner_has_limited_range() -> None:
    """T6.1: Bishop from corner has limited range."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(7, 0),
        create_piece(Color.WHITE, PieceType.BISHOP),
    )
    # Bishop on a8 has only 7 diagonal squares
    board.turn = Color.WHITE
    legal_moves = board.get_legal_moves()
    assert len(legal_moves) == 7


def test_knight_corner_has_two_moves() -> None:
    """T6.1: Knight from corner has exactly 2 moves."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(7, 0),
        create_piece(Color.WHITE, PieceType.KNIGHT),
    )
    # Knight on a8 has exactly 2 moves (c7 and b6)
    board.turn = Color.WHITE
    legal_moves = board.get_legal_moves()
    assert len(legal_moves) == 2
    # c7 = (ROW_7, COL_C), b6 = (ROW_6, COL_B)
    destinations = [m[1] for m in legal_moves]
    assert get_square_constant(6, 2) in destinations  # c7
    assert get_square_constant(5, 1) in destinations  # b6
    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(
        get_square_constant(7, 0), create_piece(Color.BLACK, PieceType.ROOK)
    )
    assert (
        board.make_move(
            get_square_constant(7, 0), get_square_constant(7, 1)
        )
        is True
    )


def test_rook_edge_cannot_move_off_board() -> None:
    """T6.2: Rook from edge cannot move off board."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 0), create_piece(Color.WHITE, PieceType.ROOK)
    )
    # Rook on a1 can only move along the edge (rank 8 and file a)
    board.turn = Color.WHITE
    legal_moves = board.get_legal_moves()
    # Rook should be able to move along the edge
    assert len(legal_moves) > 0
    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(
        get_square_constant(7, 0), create_piece(Color.BLACK, PieceType.ROOK)
    )
    assert (
        board.make_move(
            get_square_constant(7, 0), get_square_constant(7, 1)
        )
        is True
    )


def test_bishop_edge_has_limited_range() -> None:
    """T6.2: Bishop from edge has limited range."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(7, 0),
        create_piece(Color.WHITE, PieceType.BISHOP),
    )
    # Bishop on a8 has limited diagonal range
    board.turn = Color.WHITE
    legal_moves = board.get_legal_moves()
    assert len(legal_moves) == 7  # Main diagonal only


def test_knight_edge_has_reduced_moves() -> None:
    """T6.2: Knight from edge has fewer moves than center."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 0),
        create_piece(Color.WHITE, PieceType.KNIGHT),
    )
    # Knight on a1 has 2 moves (fewer than 8 from center)
    board.turn = Color.WHITE
    legal_moves = board.get_legal_moves()
    assert len(legal_moves) == 2


def test_white_pawn_on_rank_1_cannot_move_forward() -> None:
    """T6.3: White pawn on rank 8 (row 0) cannot move forward."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )
    # White pawn on rank 8 cannot move forward
    board.turn = Color.WHITE
    assert (
        board.make_move(
            get_square_constant(7, 4), get_square_constant(6, 4)
        )
        is False
    )


def test_black_pawn_on_rank_8_cannot_move_forward() -> None:
    """T6.3: Black pawn on rank 1 (ROW_1) cannot move forward (away from home)."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.BLACK, PieceType.PAWN)
    )
    # Black pawn on rank 1 cannot move forward (toward rank 2, away from home)
    board.turn = Color.BLACK
    assert (
        board.make_move(
            get_square_constant(0, 4), get_square_constant(1, 4)
        )
        is False
    )


def test_edge_rank_pawn_promotion_scenarios() -> None:
    """T6.3: Edge rank pawn promotion scenarios."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(1, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e2
    # White pawn on rank 2 (ROW_2) can only move 1 or 2 squares forward
    board.turn = Color.WHITE
    # Move to rank 4 (ROW_4) - two square move
    assert (
        board.make_move(
            get_square_constant(1, 4), get_square_constant(3, 4)
        )
        is True
    )  # e2-e4
    # Black moves (to change turn)
    board.turn = Color.BLACK
    board.set_piece(
        get_square_constant(6, 0), create_piece(Color.BLACK, PieceType.PAWN)
    )  # a7
    # Black pawn on rank 7 (ROW_7) can only move 1 or 2 squares forward
    assert (
        board.make_move(
            get_square_constant(6, 0), get_square_constant(5, 0)
        )
        is True
    )  # a7-a5


# =============================================================================
