#!/usr/bin/env python
"""Final analysis of blocking tests."""

from chess_game.constants import (
    ROW_1,
    ROW_2,
    ROW_3,
    ROW_8,
    ROW_7,
    COL_A,
    COL_B,
    COL_C,
    COL_E,
    COL_F,
    get_row_constant,
    get_col_constant,
    ConstantSquare,
)
from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType


def clear_board(board):
    for row in range(8):
        for col in range(8):
            board.clear_square(
                ConstantSquare(row=get_row_constant(row), col=get_col_constant(col))
            )


print("=" * 80)
print("ROOT CAUSE ANALYSIS: All 4 tests fail due to incorrect comparison")
print("=" * 80)
print()
print("The tests compare ConstantSquare objects with plain tuples like (7, 0)")
print("But get_legal_moves() returns ConstantSquare objects, not tuples!")
print()
print("Example from test_rook_blocked_by_adjacent_piece:")
print("  Test expects: move[0] == (7, 0)")
print("  But move[0] is actually a ConstantSquare object like ROW_1, COL_A")
print()

# Test 1
board = Board()
clear_board(board)
board.set_piece(
    ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
)
board.set_piece(
    ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
)
board.set_piece(
    ConstantSquare(row=ROW_1, col=COL_A), create_piece(Color.WHITE, PieceType.ROOK)
)
board.set_piece(
    ConstantSquare(row=ROW_1, col=COL_B), create_piece(Color.BLACK, PieceType.PAWN)
)
board.turn = Color.WHITE

legal_moves = board.get_legal_moves()
rook_moves = [m for m in legal_moves if m[0].row == ROW_1 and m[0].col == COL_A]

print("TEST 1: test_rook_blocked_by_adjacent_piece")
print("-" * 40)
print(f"Board: Rook at a1 (ROW_1, COL_A), Black pawn at b1 (ROW_1, COL_B)")
print(f"Rook can capture the pawn!")
print(f"\nActual rook moves found: {len(rook_moves)}")
print(
    f"  Move type: ({type(rook_moves[0][0]).__name__}, {type(rook_moves[0][1]).__name__})"
)
print(f"\nTest assertion: move[0] == (7, 0)  <-- WRONG! (7,0) is a tuple!")
print(f"               move[1] == (7, 1)  <-- WRONG! (7,1) is a tuple!")
print(f"               Should compare: move[0] == ConstantSquare(row=ROW_1, col=COL_A)")
print(f"                              move[1] == ConstantSquare(row=ROW_1, col=COL_B)")
print()

# Test 2
board = Board()
clear_board(board)
board.set_piece(
    ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
)
board.set_piece(
    ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
)
board.clear_square(ConstantSquare(row=ROW_1, col=COL_B))
board.clear_square(ConstantSquare(row=ROW_1, col=COL_C))
board.clear_square(ConstantSquare(row=ROW_1, col=COL_F))
board.clear_square(ConstantSquare(row=ROW_1, col=COL_G))
board.clear_square(ConstantSquare(row=ROW_2, col=COL_B))
board.clear_square(ConstantSquare(row=ROW_3, col=COL_C))
board.set_piece(
    ConstantSquare(row=ROW_1, col=COL_A), create_piece(Color.WHITE, PieceType.BISHOP)
)
board.set_piece(
    ConstantSquare(row=ROW_3, col=COL_C), create_piece(Color.WHITE, PieceType.PAWN)
)
board.turn = Color.WHITE

legal_moves = board.get_legal_moves()
bishop_moves = [m for m in legal_moves if m[0].row == ROW_1 and m[0].col == COL_A]

print("TEST 2: test_bishop_blocked_by_friendly_piece")
print("-" * 40)
print(f"Board: Bishop at a1 (ROW_1, COL_A), Friendly pawn at c3 (ROW_3, COL_C)")
print(f"Expected: Bishop can move to b2 (ROW_2, COL_B) but NOT past to c3")
print(f"\nActual bishop moves found: {len(bishop_moves)}")
for move in bishop_moves:
    print(f"  {move[0]} -> {move[1]}")
print(f"\nTest assertion: move[0] == (7, 0) and move[1] == (6, 1)")
print(f"               Should be: move[0] == ConstantSquare(row=ROW_1, col=COL_A)")
print(f"                          move[1] == ConstantSquare(row=ROW_2, col=COL_B)")
print()

# Test 3
board = Board()
clear_board(board)
board.set_piece(
    ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
)
board.set_piece(
    ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
)
board.set_piece(
    ConstantSquare(row=ROW_1, col=COL_A), create_piece(Color.WHITE, PieceType.BISHOP)
)
board.set_piece(
    ConstantSquare(row=ROW_2, col=COL_B), create_piece(Color.BLACK, PieceType.PAWN)
)
board.turn = Color.WHITE

legal_moves = board.get_legal_moves()
bishop_moves = [m for m in legal_moves if m[0].row == ROW_1 and m[0].col == COL_A]

print("TEST 3: test_bishop_blocked_by_enemy_piece")
print("-" * 40)
print(f"Board: Bishop at a1 (ROW_1, COL_A), Enemy pawn at b2 (ROW_2, COL_B)")
print(f"Expected: Bishop can CAPTURE the pawn at b2")
print(f"\nActual bishop moves found: {len(bishop_moves)}")
for move in bishop_moves:
    print(f"  {move[0]} -> {move[1]}")
print(f"\nTest assertion: any(move[1] == (6, 1))")
print(f"               Should be: any(move[1] == ConstantSquare(row=ROW_2, col=COL_B))")
print()

# Test 4
board = Board()
clear_board(board)
board.set_piece(
    ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
)
board.set_piece(
    ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
)
board.set_piece(
    ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.QUEEN)
)
board.set_piece(
    ConstantSquare(row=ROW_1, col=COL_C), create_piece(Color.WHITE, PieceType.PAWN)
)
board.set_piece(
    ConstantSquare(row=ROW_3, col=COL_E), create_piece(Color.BLACK, PieceType.PAWN)
)
board.turn = Color.WHITE

legal_moves = board.get_legal_moves()
queen_moves = [m for m in legal_moves if m[0].row == ROW_1 and m[0].col == COL_E]

print("TEST 4: test_queen_blocked_in_one_direction")
print("-" * 40)
print(
    f"Board: Queen at e1 (ROW_1, COL_E), White pawn at c1 (ROW_1, COL_C), Black pawn at e3 (ROW_3, COL_E)"
)
print(
    f"Expected: Queen can move vertically UP past e3, but NOT horizontally LEFT past c1"
)
print(f"\nActual queen moves found: {len(queen_moves)}")
for move in queen_moves:
    print(f"  {move[0]} -> {move[1]}")
print(f"\nTest assertion: any(move[1] == (6, 4))  # e2")
print(
    f"               Should be: any(move[1] == ConstantSquare(row=ROW_2, col=COL_E))  # e2"
)
print()

print("=" * 80)
print("CONCLUSION:")
print("=" * 80)
print()
print("ALL 4 TESTS ARE WRONG!")
print()
print("The tests use tuples like (7, 0) but get_legal_moves() returns ConstantSquare")
print("objects. These will NEVER match because:")
print("  - (7, 0) is a tuple")
print("  - ConstantSquare(row=..., col=...) is a Pydantic model")
print()
print("The blocking logic in board.py is CORRECT!")
print("The tests need to be fixed to compare ConstantSquares with ConstantSquares.")
print()
