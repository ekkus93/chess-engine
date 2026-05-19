"""Tests for AI search correctness: mate-at-horizon, leaf evaluation, and depth validation."""

from __future__ import annotations

import pytest
from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType
from chess_game.chess.ai import get_best_move
from tests.helpers import sq


def move_to_str(move):
    """Helper to format a move tuple into algebraic string for assertions."""
    start, end, promotion = move
    suffix = ""
    if promotion is not None:
        suffix = str(promotion.name).lower()[0]
    return f"{index_to_str(start)}{index_to_str(end)}{suffix}"


def index_to_str(sq_obj):
    """Convert ConstantSquare to algebraic string."""
    file = chr(ord("a") + int(sq_obj.col))
    rank = str(8 - int(sq_obj.row))
    return f"{rank}{file}"


def make_mate_in_one_white_position():
    """Position:
    White king on g6
    White queen on f7
    Black king on h8
    White to move
    """
    board = Board()
    board.clear_board()
    board.set_piece(sq("g6"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("f7"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.WHITE
    return board


def make_mate_in_one_black_position():
    """Position:
    Black king on c2
    Black queen on d3
    White king on a1
    Black to move
    """
    board = Board()
    board.clear_board()
    board.set_piece(sq("c2"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d3"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
    board.turn = Color.BLACK
    return board


def test_mate_in_one_white_finds_checkmate():
    """White to move should find a mate-in-one at depth 1."""
    board = make_mate_in_one_white_position()
    move = get_best_move(board, depth=1)
    assert move is not None, "AI should find a checkmate at depth 1"

    # Verify it actually mates
    clone = board.clone()
    assert clone.make_move(move.start, move.end, promotion=move.promotion) is True
    assert clone._is_checkmate(Color.BLACK), "Black should be checkmated"


def test_mate_in_one_black_finds_checkmate():
    """Black to move should find a mate-in-one at depth 1."""
    board = make_mate_in_one_black_position()
    move = get_best_move(board, depth=1)
    assert move is not None, "AI should find a checkmate for Black at depth 1"

    clone = board.clone()
    assert clone.make_move(move.start, move.end, promotion=move.promotion) is True
    assert clone._is_checkmate(Color.WHITE), "White should be checkmated"


def test_mate_in_one_does_not_choose_non_mating_queen_move():
    """Ensure AI prefers a mating move over a non-mating queen move."""
    board = make_mate_in_one_white_position()
    move = get_best_move(board, depth=1)
    assert move is not None

    clone = board.clone()
    clone.make_move(move.start, move.end, promotion=move.promotion)
    # If it's not a checkmate, we failed to prioritize mate
    assert clone._is_checkmate(Color.BLACK), "Move should be checkmate, not random queen move"


def test_stalemate_returns_no_best_move():
    """Stalemate: no legal moves, get_best_move should return None."""
    board = Board()
    board.clear_board()
    # Black king: h8
    # White king: f7
    # White queen: g6
    # Black to move
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("f7"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g6"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.turn = Color.BLACK

    move = get_best_move(board, depth=1)
    assert move is None, "No move should be returned in stalemate"


def test_checkmate_side_to_move_returns_no_best_move():
    """Checkmate position: get_best_move should return None (no legal moves)."""
    board = Board()
    board.clear_board()
    # Black king: h8
    # White king: f6
    # White queen: g7
    # Black to move
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("f6"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g7"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.turn = Color.BLACK

    move = get_best_move(board, depth=1)
    assert move is None, "No move should be returned in checkmate"


def test_depth_validation_raises_value_error_for_zero():
    """depth=0 should raise ValueError."""
    board = Board()
    with pytest.raises(ValueError, match="depth"):
        get_best_move(board, depth=0)


def test_depth_validation_raises_value_error_for_negative():
    """Negative depth should raise ValueError."""
    board = Board()
    with pytest.raises(ValueError, match="depth"):
        get_best_move(board, depth=-1)


def test_get_best_move_does_not_mutate_board():
    """AI should not mutate the original board."""
    board = Board()

    # Capture initial key
    initial_key = _board_key(board)

    move = get_best_move(board, depth=2)
    # Just ensure it runs and does not mutate
    final_key = _board_key(board)
    assert initial_key == final_key, "Board state must not be mutated by AI search"


def _board_key(board: Board) -> str:
    """Helper to capture a board key for mutation checks."""
    parts = []
    for row in board.board:
        for p in row:
            if p is None:
                parts.append("-")
            else:
                parts.append(f"{p.color.name[0]}{p.kind.name[0].lower()}")
    parts.append(board.turn.name)
    return "".join(parts)
