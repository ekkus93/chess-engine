import pytest
from chess_engine.board import Board

def test_board_copy_and_equality():
    board = Board()
    copy_board = board.copy()
    assert copy_board == board
    assert copy_board is not board
    # modify copy and ensure original unchanged
    copy_board.set_piece("e4", "P")
    assert board.get_piece("e4") is None
    assert copy_board.get_piece("e4") == "P"

if __name__ == "__main__":
    pytest.main([__file__])
