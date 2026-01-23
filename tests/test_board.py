import pytest

from chess_engine.board import Board

# Helper to compare board string representation

def board_repr(board):
    return str(board)

# Test that starting position is correct

def test_starting_position():
    board = Board()
    # check ranks 1 and 8
    assert board.get_piece("a1") == "R"
    assert board.get_piece("h1") == "R"
    assert board.get_piece("e1") == "K"
    assert board.get_piece("a8") == "r"
    assert board.get_piece("h8") == "r"
    assert board.get_piece("e8") == "k"
    # pawns
    for file in "abcdefgh":
        assert board.get_piece(file + "2") == "P"
        assert board.get_piece(file + "7") == "p"
    # empty squares
    for file in "abcdefgh":
        assert board.get_piece(file + "4") is None

# Test moving a piece

def test_move_piece():
    board = Board()
    board.move_piece("e2", "e4")
    assert board.get_piece("e4") == "P"
    assert board.get_piece("e2") is None

# Test string representation contains expected rows

def test_repr_contains_rows():
    board = Board()
    rep = board_repr(board)
    lines = rep.split("\n")
    # 8 rows
    assert len(lines) == 8
    # first row should have black pieces
    assert lines[0] == "♜ ♞ ♝ ♛ ♚ ♝ ♞ ♜"
    # last row should have white pieces
    assert lines[7] == "♖ ♘ ♗ ♕ ♔ ♗ ♘ ♖"
    # middle empty rows
    for i in range(2, 6):
        assert lines[i] == ". . . . . . . ."

# Test that moving to occupied square replaces it

def test_capture():
    board = Board()
    board.move_piece("e2", "e4")
    board.move_piece("e7", "e5")
    board.move_piece("e4", "e5")  # capture pawn
    assert board.get_piece("e5") == "P"
    assert board.get_piece("e4") is None

# Test invalid move raises error

def test_invalid_move():
    board = Board()
    with pytest.raises(ValueError):
        board.move_piece("a3", "a4")  # no piece at a3
