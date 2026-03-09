import sys
from chess_game.chess.board import Board


def test_rook_move():
    board = Board()
    # Make a valid rook move (white rook at a1 to a8)
    # We need to be careful - in the starting position, it's not the right piece at (0,0)
    # Let's start the board in a proper state with a rook at (7,0)
    board.board[7][0] = "Rook"
    board.board[7][1] = "Knight"
    board.turn = "black"
    # Move from position (7,0) (rook) to (0,0)
    success = board.make_move((7, 0), (0, 0))
    assert success == True
    assert board.board[0][0] == "Rook"
    assert board.board[7][0] == ""


def test_knight_move():
    board = Board()
    board.board[7][1] = "Knight"
    board.board[7][0] = "Rook"
    board.turn = "black"
    success = board.make_move((7, 1), (5, 2))
    assert success == True
    assert board.board[5][2] == "Knight"
    assert board.board[7][1] == ""


def test_bishop_move():
    board = Board()
    board.board[7][2] = "Bishop"
    board.board[7][0] = "Rook"
    board.turn = "black"
    success = board.make_move((7, 2), (0, 5))
    assert success == True
    assert board.board[0][5] == "Bishop"
    assert board.board[7][2] == ""


def test_queen_move():
    board = Board()
    board.board[7][3] = "Queen"
    board.board[7][0] = "Rook"
    board.turn = "black"
    success = board.make_move((7, 3), (0, 3))
    assert success == True
    assert board.board[0][3] == "Queen"
    assert board.board[7][3] == ""


def test_king_move():
    board = Board()
    board.board[7][4] = "King"
    board.board[7][0] = "Rook"
    board.turn = "black"
    success = board.make_move((7, 4), (6, 5))
    assert success == True
    assert board.board[6][5] == "King"
    assert board.board[7][4] == ""


def test_pawn_move():
    board = Board()
    # Make a simple pawn move - white pawn at e2 (row 6, col 4) to e3 (row 5, col 4)
    board.board[6][4] = "Pawn"
    board.board[7][0] = "Rook"
    board.turn = "white"
    success = board.make_move((6, 4), (5, 4))
    assert success == True
    assert board.board[5][4] == "Pawn"
    assert board.board[6][4] == ""
