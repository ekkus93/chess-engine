import unittest

from chess_engine.board import Board

class TestBoard(unittest.TestCase):
    def setUp(self):
        self.board = Board()

    def test_starting_position(self):
        board = self.board
        # check ranks 1 and 8
        self.assertEqual(board.get_piece("a1"), "R")
        self.assertEqual(board.get_piece("h1"), "R")
        self.assertEqual(board.get_piece("e1"), "K")
        self.assertEqual(board.get_piece("a8"), "r")
        self.assertEqual(board.get_piece("h8"), "r")
        self.assertEqual(board.get_piece("e8"), "k")
        # pawns
        for file in "abcdefgh":
            self.assertEqual(board.get_piece(file + "2"), "P")
            self.assertEqual(board.get_piece(file + "7"), "p")
        # empty squares
        for file in "abcdefgh":
            self.assertIsNone(board.get_piece(file + "4"))

    def test_move_piece(self):
        board = self.board
        board.move_piece("e2", "e4")
        self.assertEqual(board.get_piece("e4"), "P")
        self.assertIsNone(board.get_piece("e2"))

    def test_repr_contains_rows(self):
        board = self.board
        rep = str(board)
        lines = rep.split("\n")
        # 8 rows
        self.assertEqual(len(lines), 8)
        # first row should have black pieces
        self.assertEqual(lines[0], "♜ ♞ ♝ ♛ ♚ ♝ ♞ ♜")
        # last row should have white pieces
        self.assertEqual(lines[7], "♖ ♘ ♗ ♕ ♔ ♗ ♘ ♖")
        # middle empty rows
        for i in range(2, 6):
            self.assertEqual(lines[i], ". . . . . . . .")

    def test_capture(self):
        board = self.board
        board.move_piece("e2", "e4")
        board.move_piece("e7", "e5")
        board.move_piece("e4", "e5")  # capture pawn
        self.assertEqual(board.get_piece("e5"), "P")
        self.assertIsNone(board.get_piece("e4"))

    def test_invalid_move(self):
        board = self.board
        with self.assertRaises(ValueError):
            board.move_piece("a3", "a4")  # no piece at a3

if __name__ == "__main__":
    unittest.main()
