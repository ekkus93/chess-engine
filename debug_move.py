#!/usr/bin/env python3

from chess_game.chess.board import Board

# Test rook movement
board = Board()
print("Initial board state:")
board.display()

# Let's test a simple rook move
board.board[7][0] = "Rook"
board.board[7][1] = "Knight"
board.turn = "black"
print("\nTesting rook move from (7,0) to (0,0):")
print(f"Rook at {7, 0} to {0, 0}")
success = board.make_move((7, 0), (0, 0))
print(f"Move successful: {success}")

board.display()
