import unittest
from chess_engine.board import Board
from chess_engine.search import alpha_beta

class TestAlphaBetaSearch(unittest.TestCase):
    def setUp(self):
        # Simple end‑game: White to move and can mate in one
        fen = "8/8/8/8/8/8/5k2/6Q1 w - - 0 1"
        self.board = Board.parse_fen(fen)

    def test_mate_in_one(self):
        best_move, best_score = alpha_beta(self.board, depth=1)
        self.assertEqual(best_score, 1000)  # a mate score (implementation dependent)
        self.assertIn(best_move, self.board.legal_moves)

if __name__ == "__main__":
    unittest.main()
