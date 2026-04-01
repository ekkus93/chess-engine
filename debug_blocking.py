#!/usr/bin/env python
"""Debug script for blocking tests."""

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
from chess_game.chess.types import Color, PieceType
from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType


def clear_board(board):
    for row in range(8):
        for col in range(8):
            col = get_col_constant(col)
            board.clear_square(
                ConstantSquare(row=get_row_constant(row), col=get_col_constant(col))
            )


def print_board(board):
    print("\n  a b c d e f g h")
    for row in range(8):
        rank = 8 - row
        symbols = []
        for col in range(8):
            col = get_col_constant(col)
            piece = board.get_piece(ConstantSquare(row=get_row_constant(row), col=col))
            if piece is None:
                symbols.append(".")
            else:
                kind = piece.kind
                color = piece.color
                kind_str = {
                    PieceType.PAWN: "p",
                    PieceType.KNIGHT: "n",
                    PieceType.BISHOP: "b",
                    PieceType.ROOK: "r",
                    PieceType.QUEEN: "q",
                    PieceType.KING: "k",
                }
                symbols.append(
                    kind_str[kind].upper()
                    if color == Color.WHITE
                    else kind_str[kind].lower()
                )
        print(f"{rank} {' '.join(symbols)}")
    print("  a b c d e f g h")


# =============================================================================
# Test 1: test_rook_blocked_by_adjacent_piece
# =============================================================================
print("=" * 80)
print("TEST 1: test_rook_blocked_by_adjacent_piece")
print("=" * 80)

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

print("Board state:")
print_board(board)
print("\nRook is at a1 (ROW_1, COL_A), pawn is at b1 (ROW_1, COL_B)")
print("Expected: Rook can capture pawn at b1")
print("Test expects move: a1 -> b1 (from (7,0) to (7,1))")

legal_moves = board.get_legal_moves()
print(f"\nTotal legal moves: {len(legal_moves)}")

# Check if rook can move to b1
rook_moves = [m for m in legal_moves if m[0].row == ROW_1 and m[0].col == COL_A]
print(f"Rook moves: {len(rook_moves)}")
for move in rook_moves:
    print(f"  From {move[0]} to {move[1]} with {move[2]}")

# Check what the test is looking for
expected_move = (get_row_constant(ROW_1), get_col_constant(COL_B))  # (7, 1)
print(f"\nTest expects move to square: {expected_move}")
found = any(move[0] == expected_move for move in legal_moves)
print(f"Found expected move: {found}")

# =============================================================================
# Test 2: test_bishop_blocked_by_friendly_piece
# =============================================================================
print("\n" + "=" * 80)
print("TEST 2: test_bishop_blocked_by_friendly_piece")
print("=" * 80)

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
    ConstantSquare(row=ROW_1, col=COL_A),
    create_piece(Color.WHITE, PieceType.BISHOP),
)
board.set_piece(
    ConstantSquare(row=ROW_3, col=COL_C), create_piece(Color.WHITE, PieceType.PAWN)
)
board.turn = Color.WHITE

print("Board state:")
print_board(board)
print("\nBishop is at a1 (ROW_1, COL_A), friendly pawn at c3 (ROW_3, COL_C)")
print("Expected: Bishop can move to b2 (6,1) but not to c3 (5,2)")

legal_moves = board.get_legal_moves()
print(f"\nTotal legal moves: {len(legal_moves)}")

# Check bishop moves
bishop_moves = [m for m in legal_moves if m[0].row == ROW_1 and m[0].col == COL_A]
print(f"Bishop moves: {len(bishop_moves)}")
for move in bishop_moves:
    print(f"  From {move[0]} to {move[1]}")

# Check what the test expects
print(f"\nTest expects bishop move to b2 (6,1): (7,0) -> (6,1)")
found_b2 = any(move[0] == (7, 0) and move[1] == (6, 1) for move in legal_moves)
print(f"Found b2 move: {found_b2}")

# =============================================================================
# Test 3: test_bishop_blocked_by_enemy_piece
# =============================================================================
print("\n" + "=" * 80)
print("TEST 3: test_bishop_blocked_by_enemy_piece")
print("=" * 80)

board = Board()
clear_board(board)
board.set_piece(
    ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
)
board.set_piece(
    ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
)
board.set_piece(
    ConstantSquare(row=ROW_1, col=COL_A),
    create_piece(Color.WHITE, PieceType.BISHOP),
)
board.set_piece(
    ConstantSquare(row=ROW_2, col=COL_B), create_piece(Color.BLACK, PieceType.PAWN)
)
board.turn = Color.WHITE

print("Board state:")
print_board(board)
print("\nBishop is at a1 (ROW_1, COL_A), enemy pawn at b2 (ROW_2, COL_B)")
print("Expected: Bishop can capture pawn at b2")

legal_moves = board.get_legal_moves()
print(f"\nTotal legal moves: {len(legal_moves)}")

# Check bishop moves
bishop_moves = [m for m in legal_moves if m[0].row == ROW_1 and m[0].col == COL_A]
print(f"Bishop moves: {len(bishop_moves)}")
for move in bishop_moves:
    print(f"  From {move[0]} to {move[1]}")

# Check what the test expects
print(f"\nTest expects bishop move to b2 (6,1): any move[1] == (6, 1)")
found_b2 = any(move[1] == (6, 1) for move in legal_moves)
print(f"Found b2 move: {found_b2}")

# =============================================================================
# Test 4: test_queen_blocked_in_one_direction
# =============================================================================
print("\n" + "=" * 80)
print("TEST 4: test_queen_blocked_in_one_direction")
print("=" * 80)

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

print("Board state:")
print_board(board)
print("\nQueen is at e1 (ROW_1, COL_E)")
print("Pawn at c1 (ROW_1, COL_C) - blocks horizontal left")
print("Black pawn at e3 (ROW_3, COL_E)")
print(
    "Expected: Queen can move vertically up (past e3), but not horizontally left (blocked by c1)"
)

legal_moves = board.get_legal_moves()
print(f"\nTotal legal moves: {len(legal_moves)}")

# Check queen moves
queen_moves = [m for m in legal_moves if m[0].row == ROW_1 and m[0].col == COL_E]
print(f"Queen moves: {len(queen_moves)}")
for move in queen_moves:
    print(f"  From {move[0]} to {move[1]}")

# Check what the test expects
print(f"\nTest expects queen move to e2 (6,4): any move[1] == (6, 4)")
found_e2 = any(move[1] == (6, 4) for move in legal_moves)
print(f"Found e2 move: {found_e2}")

print(f"\nTest expects queen move to e3 (5,4) - capture: any move[1] == (5, 4)")
found_e3 = any(move[1] == (5, 4) for move in legal_moves)
print(f"Found e3 move: {found_e3}")
