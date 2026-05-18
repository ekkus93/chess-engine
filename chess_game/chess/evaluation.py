"""Position evaluation tables for AI minimax search."""

from __future__ import annotations

from chess_game.chess.types import PieceType

# Material values (baseline)
MATERIAL_VALUES: dict[PieceType, int] = {
    PieceType.PAWN: 100,
    PieceType.KNIGHT: 320,
    PieceType.BISHOP: 330,
    PieceType.ROOK: 500,
    PieceType.QUEEN: 900,
    PieceType.KING: 20000,  # Safety value only, rarely used directly
}


# Piece-square tables for positional bias (8x8 boards)
# Coordinates are reversed from standard notation to align with board indices
# Row index 0 = rank 8 (black back rank), row index 7 = rank 1 (white back rank)
# Column index 0 = file a, column index 7 = file h
# Values scaled down so material dominates over positional bias.

# Encourage central control and advance pawns toward promotion
# Black pawns (starting at row 6 moving down) should get positive values on white's side of board
PAWN_TABLE: list[list[int]] = [
    [-10, -10, -10, -10, -10, -10, -10, -10],  # rank 8 (row 0) - white starting
    [-2, -2, -2, -2, -2, -2, -2, -2],  # rank 7 (row 1)
    [2, 3, 1, 5, 4, 5, 1, 3],  # rank 6 (row 2)
    [3, 5, 2, 0, 3, 3, 0, 3],  # rank 5 (row 3)
    [3, 5, 2, 3, 5, 2, 3, 4],  # rank 4 (row 4) - central bias
    [1, 2, 3, 2, 3, 2, 1, 0],  # rank 3 (row 5)
    [-2, 0, 0, 0, 0, 0, 0, -2],  # rank 2 (row 6)
    [-10, -10, -10, -10, -10, -10, -10, -10],  # rank 1 (row 7) - black starting
]


# Knights: favor open positions, avoid corners
KNIGHT_TABLE: list[list[int]] = [
    [-5, -4, -3, -2, -2, -3, -4, -5],  # rank 8 (row 0)
    [-4, -2, 1, 2, 2, 1, -2, -4],  # rank 7 (row 1)
    [-3, 2, 5, 6, 6, 5, 2, -3],  # rank 6 (row 2) - central control
    [-2, 3, 6, 8, 8, 6, 3, -2],  # rank 5 (row 3)
    [-1, 4, 7, 9, 9, 7, 4, -1],  # rank 4 (row 4) - optimal central squares
    [2, 4, 7, 8, 8, 7, 4, 2],  # rank 3 (row 5)
    [-3, 1, 4, 5, 5, 4, 1, -3],  # rank 2 (row 6)
    [-5, -4, -3, -2, -2, -3, -4, -5],  # rank 1 (row 7)
]


# Bishops: prefer open diagonals, central squares
BISHOP_TABLE: list[list[int]] = [
    [-5, -4, -3, -2, -2, -3, -4, -5],  # rank 8 (row 0)
    [-3, -2, 1, 2, 2, 1, -2, -3],  # rank 7 (row 1)
    [2, 2, 1, 1, 1, 1, 2, 2],  # rank 6 (row 2)
    [2, 3, 1, 5, 5, 1, 3, 2],  # rank 5 (row 3)
    [0, 1, 2, 2, 2, 2, 1, 0],  # rank 4 (row 4) - central bias
    [-2, 2, 3, 4, 4, 3, 2, -2],  # rank 3 (row 5)
    [-3, 2, 3, 4, 4, 3, 2, -3],  # rank 2 (row 6)
    [-5, -4, -3, -2, -2, -3, -4, -5],  # rank 1 (row 7)
]


# Rooks: prefer open files, central ranks
ROOK_TABLE: list[list[int]] = [
    [-3, -3, -3, -3, -3, -3, -3, -3],  # rank 8 (row 0)
    [-2, -2, -1, -1, -1, -1, -2, -2],  # rank 7 (row 1)
    [-1, -1, 1, 3, 4, 3, -1, -1],  # rank 6 (row 2)
    [-2, 1, 3, 7, 7, 3, 1, -2],  # rank 5 (row 3) - central files
    [-1, 2, 5, 8, 8, 5, 2, -1],  # rank 4 (row 4) - optimal
    [2, 3, 6, 9, 9, 6, 3, 2],  # rank 3 (row 5)
    [4, 1, 4, 2, 2, 4, 1, 5],  # rank 2 (row 6) - support central files
    [-3, -3, -3, -3, -3, -3, -3, -3],  # rank 1 (row 7)
]


# Queens: combine rook and bishop preferences
QUEEN_TABLE: list[list[int]] = [
    [-2, 1, 2, 2, 2, 2, 1, -2],  # rank 8 (row 0)
    [-3, -2, 2, 4, 4, 2, -2, -3],  # rank 7 (row 1)
    [0, 0, 2, 3, 6, 3, 2, 0],  # rank 6 (row 2)
    [-5, 1, 3, 5, 8, 8, 3, 1],  # rank 5 (row 3) - strong center for queens
    [1, 4, 7, 9, 10, 9, 7, 4],  # rank 4 (row 4) - optimal position
    [-2, 5, 8, 8, 8, 8, 5, -2],  # rank 3 (row 5)
    [-2, 1, 3, 5, 6, 5, 3, -2],  # rank 2 (row 6)
    [-3, -4, -2, -2, -2, -2, -4, -3],  # rank 1 (row 7)
]


# King safety table for middlegame/late middlegame
KING_TABLE: list[list[int]] = [
    [-8, -7, -6, -4, -2, 0, 1, 3],  # rank 8 (row 0)
    [-7, -6, -4, -2, -1, 1, 2, 3],  # rank 7 (row 1)
    [-7, -5, 0, 2, 5, 5, 2, 5],  # rank 6 (row 2)
    [2, 2, 3, 4, 4, 4, 2, 2],  # rank 5 (row 3)
    [2, 3, 3, 5, 6, 5, 3, 2],  # rank 4 (row 4)
    [-4, -3, -1, 0, 0, 0, -1, -3],  # rank 3 (row 5)
    [-6, -5, -3, -2, -1, 0, -2, -4],  # rank 2 (row 6)
    [-9, -8, -6, -5, -4, -3, -4, -7],  # rank 1 (row 7)
]
