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


def test_kingside_castling_in_legal_moves():
    """White kingside castling appears in legal moves when conditions are met."""
    board = Board()
    # e4, e5, Nf3, Nf6, Bc4, Bc5 - clears f1 and g1
    board.make_move(algebraic_to_index("e2"), algebraic_to_index("e4"))
    board.make_move(algebraic_to_index("e7"), algebraic_to_index("e5"))
    board.make_move(algebraic_to_index("g1"), algebraic_to_index("f3"))
    board.make_move(algebraic_to_index("g8"), algebraic_to_index("f6"))
    board.make_move(algebraic_to_index("f1"), algebraic_to_index("c4"))
    board.make_move(algebraic_to_index("f8"), algebraic_to_index("c5"))

    moves = board.get_legal_moves()
    move_strings = _moves_to_strings(moves)
    assert "e1g1" in move_strings


def test_queenside_castling_in_legal_moves():
    """White queenside castling appears in legal moves when conditions are met."""
    board = Board()
    # d4, d5, Nc3, Nc6, Bf4, e6, Qd2, Bc5 - clears b1, c1, d1
    board.make_move(algebraic_to_index("d2"), algebraic_to_index("d4"))
    board.make_move(algebraic_to_index("d7"), algebraic_to_index("d5"))
    board.make_move(algebraic_to_index("b1"), algebraic_to_index("c3"))
    board.make_move(algebraic_to_index("b8"), algebraic_to_index("c6"))
    board.make_move(algebraic_to_index("c1"), algebraic_to_index("f4"))
    board.make_move(algebraic_to_index("e7"), algebraic_to_index("e6"))
    board.make_move(algebraic_to_index("d1"), algebraic_to_index("d2"))
    board.make_move(algebraic_to_index("f8"), algebraic_to_index("c5"))

    moves = board.get_legal_moves()
    move_strings = _moves_to_strings(moves)
    assert "e1c1" in move_strings


def test_queenside_castling_blocked_by_occupied_b1():
    """Queenside castling not in legal moves when b1 is occupied."""
    board = Board()
    # Clear c1 and d1 but leave Nb1 in place, blocking queenside
    board.make_move(algebraic_to_index("d2"), algebraic_to_index("d4"))
    board.make_move(algebraic_to_index("d7"), algebraic_to_index("d5"))
    board.make_move(algebraic_to_index("g1"), algebraic_to_index("f3"))
    board.make_move(algebraic_to_index("g8"), algebraic_to_index("f6"))
    board.make_move(algebraic_to_index("c1"), algebraic_to_index("f4"))
    board.make_move(algebraic_to_index("c8"), algebraic_to_index("h3"))
    board.make_move(algebraic_to_index("d1"), algebraic_to_index("d2"))
    board.make_move(algebraic_to_index("e7"), algebraic_to_index("e6"))

    moves = board.get_legal_moves()
    move_strings = _moves_to_strings(moves)
    assert "e1c1" not in move_strings


def test_black_kingside_castling_in_legal_moves():
    """Black kingside castling appears in legal moves when conditions are met."""
    board = Board()
    # e4, e5, Nf3, Nc6, Bc4, Be7, Nc3, d6, d3, Nf6, a3 - clears f8, g8 for black
    board.make_move(algebraic_to_index("e2"), algebraic_to_index("e4"))
    board.make_move(algebraic_to_index("e7"), algebraic_to_index("e5"))
    board.make_move(algebraic_to_index("g1"), algebraic_to_index("f3"))
    board.make_move(algebraic_to_index("b8"), algebraic_to_index("c6"))
    board.make_move(algebraic_to_index("f1"), algebraic_to_index("c4"))
    board.make_move(algebraic_to_index("f8"), algebraic_to_index("e7"))
    board.make_move(algebraic_to_index("b1"), algebraic_to_index("c3"))
    board.make_move(algebraic_to_index("d7"), algebraic_to_index("d6"))
    board.make_move(algebraic_to_index("d2"), algebraic_to_index("d3"))
    board.make_move(algebraic_to_index("g8"), algebraic_to_index("f6"))
    board.make_move(algebraic_to_index("a2"), algebraic_to_index("a3"))

    moves = board.get_legal_moves()
    move_strings = _moves_to_strings(moves)
    assert "e8g8" in move_strings


def test_black_queenside_castling_in_legal_moves():
    """Black queenside castling appears in legal moves when conditions are met."""
    board = Board()
   # d4, d5, Nc3, Nc6, Bf4, Bg4, Qd2, e6, Nf3, Qd7, a3 - clears b8, c8, d8 for black
    board.make_move(algebraic_to_index("d2"), algebraic_to_index("d4"))
    board.make_move(algebraic_to_index("d7"), algebraic_to_index("d5"))
    board.make_move(algebraic_to_index("b1"), algebraic_to_index("c3"))
    board.make_move(algebraic_to_index("b8"), algebraic_to_index("c6"))
    board.make_move(algebraic_to_index("c1"), algebraic_to_index("f4"))
    board.make_move(algebraic_to_index("c8"), algebraic_to_index("g4"))
    board.make_move(algebraic_to_index("d1"), algebraic_to_index("d2"))
    board.make_move(algebraic_to_index("e7"), algebraic_to_index("e6"))
    board.make_move(algebraic_to_index("g1"), algebraic_to_index("f3"))
    board.make_move(algebraic_to_index("d8"), algebraic_to_index("d7"))
    board.make_move(algebraic_to_index("a2"), algebraic_to_index("a3"))

    moves = board.get_legal_moves()
    move_strings = _moves_to_strings(moves)
    assert "e8c8" in move_strings
