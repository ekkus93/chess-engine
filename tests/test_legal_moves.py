"""Tests for legal move generation (Task 4.3)."""

from chess_game.chess.board import Board
from chess_game.chess.coords import algebraic_to_index, index_to_algebraic
from chess_game.chess.types import Color


def _moves_to_strings(moves):
    """Convert list of move tuples to list of 'e2e4' strings."""
    return [
        index_to_algebraic(m[0]) + index_to_algebraic(m[1]) for m in moves
    ]


def test_starting_position_white_moves_only():
    """On the starting position, only White moves are generated."""
    board = Board()
    assert board.turn == Color.WHITE

    moves = board.get_legal_moves()
    move_strings = _moves_to_strings(moves)

    # White moves should be present
    assert "e2e3" in move_strings
    assert "e2e4" in move_strings
    assert "g1f3" in move_strings
    assert "b1c3" in move_strings

    # Black moves should NOT be present
    assert "e7e6" not in move_strings
    assert "e7e5" not in move_strings
    assert "g8f6" not in move_strings
    assert "b8c6" not in move_strings


def test_after_e2e4_black_moves_only():
    """After White plays e2e4, only Black moves are generated."""
    board = Board()
    move = algebraic_to_index("e2"), algebraic_to_index("e4")
    board.make_move(move[0], move[1])
    assert board.turn == Color.BLACK

    moves = board.get_legal_moves()
    move_strings = _moves_to_strings(moves)

    # Black moves should be present
    assert "e7e6" in move_strings
    assert "e7e5" in move_strings
    assert "g8f6" in move_strings
    assert "b8c6" in move_strings

    # White moves should NOT be present
    assert "e1e2" not in move_strings
    assert "g1f3" not in move_strings
    assert "b1c3" not in move_strings


def test_get_legal_moves_empty_square():
    """get_legal_moves on an empty square returns []."""
    board = Board()
    e3 = algebraic_to_index("e3")
    assert board.get_legal_moves(e3) == []


def test_get_legal_moves_opponent_piece():
    """get_legal_moves on opponent's piece returns []."""
    board = Board()
    # White's turn, query a Black piece
    e7 = algebraic_to_index("e7")
    assert board.get_legal_moves(e7) == []
