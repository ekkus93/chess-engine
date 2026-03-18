"""Position evaluation tables for AI minimax search."""
from __future__ import annotations

from chess_game.chess.types import PieceType


# Material values (baseline)
MATERIAL_VALUES: dict[PieceType, int] = {
    PieceType.PAWN: 10,
    PieceType.KNIGHT: 30,
    PieceType.BISHOP: 30,
    PieceType.ROOK: 50,
    PieceType.QUEEN: 90,
    PieceType.KING: 1000,  # Safety value only, rarely used directly
}


# Piece-square tables for positional bias (8x8 boards)
# Coordinates are reversed from standard notation to align with board indices
# Row index 0 = rank 8 (black back rank), row index 7 = rank 1 (white back rank)
# Column index 0 = file a, column index 7 = file h

# Encourage central control and advance pawns toward promotion
# Black pawns (starting at row 6 moving down) should get positive values on white's side of board
PAWN_TABLE: list[list[int]] = [
    [-100, -100, -100, -100, -100, -100, -100, -100],  # rank 8 (row 0) - white starting
    [-20, -20, -20, -20, -20, -20, -20, -20],           # rank 7 (row 1)
    [20, 30, 10, 5, 40, 50, 10, 30],                     # rank 6 (row 2) - encourage advance, penalize edges
    [30, 50, 20, 0, 30, 30, 0, 30],                      # rank 5 (row 3) - central bias, penalize edges
    [30, 50, 20, 30, 50, 20, 30, 40],                    # rank 4 (row 4) - central bias
    [10, 20, 30, 20, 30, 20, 10, 0],                     # rank 3 (row 5)
    [-20, 0, 0, 0, 0, 0, 0, -20],                        # rank 2 (row 6)
    [-100, -100, -100, -100, -100, -100, -100, -100],   # rank 1 (row 7) - black starting
]


# Knights: favor open positions, avoid corners
KNIGHT_TABLE: list[list[int]] = [
    [-50, -40, -30, -20, -20, -30, -40, -50],           # rank 8 (row 0)
    [-40, -20, 10, 20, 20, 10, -20, -40],               # rank 7 (row 1)
    [-30, 20, 50, 60, 60, 50, 20, -30],                 # rank 6 (row 2) - central control
    [-20, 30, 60, 80, 80, 60, 30, -20],                 # rank 5 (row 3)
    [-10, 40, 70, 90, 90, 70, 40, -10],                 # rank 4 (row 4) - optimal central squares
    [20, 40, 70, 80, 80, 70, 40, 20],                   # rank 3 (row 5)
    [-30, 10, 40, 50, 50, 40, 10, -30],                 # rank 2 (row 6)
    [-50, -40, -30, -20, -20, -30, -40, -50],           # rank 1 (row 7)
]


# Bishops: prefer open diagonals, central squares
BISHOP_TABLE: list[list[int]] = [
    [-50, -40, -30, -20, -20, -30, -40, -50],           # rank 8 (row 0)
    [-30, -20, 10, 20, 20, 10, -20, -30],               # rank 7 (row 1)
    [20, 20, 10, 10, 10, 10, 20, 20],                   # rank 6 (row 2)
    [20, 30, 10, 5, 5, 10, 30, 20],                     # rank 5 (row 3)
    [0, 10, 20, 20, 20, 20, 10, 0],                     # rank 4 (row 4) - central bias
    [-20, 20, 30, 40, 40, 30, 20, -20],                 # rank 3 (row 5)
    [-30, 20, 30, 40, 40, 30, 20, -30],                 # rank 2 (row 6)
    [-50, -40, -30, -20, -20, -30, -40, -50],           # rank 1 (row 7)
]


# Rooks: prefer open files, central ranks
ROOK_TABLE: list[list[int]] = [
    [-30, -30, -30, -30, -30, -30, -30, -30],           # rank 8 (row 0)
    [-25, -20, -10, -10, -10, -10, -20, -25],           # rank 7 (row 1)
    [-10, -10, 10, 30, 40, 30, -10, -10],               # rank 6 (row 2)
    [-20, 10, 35, 70, 70, 35, 10, -20],                 # rank 5 (row 3) - central files
    [-10, 20, 50, 80, 80, 50, 20, -10],                 # rank 4 (row 4) - optimal
    [20, 30, 60, 90, 90, 60, 30, 20],                   # rank 3 (row 5)
    [40, 10, 40, 20, 20, 40, 10, 50],                   # rank 2 (row 6) - support central files
    [-30, -30, -30, -30, -30, -30, -30, -30],           # rank 1 (row 7)
]


# Queens: combine rook and bishop preferences
QUEEN_TABLE: list[list[int]] = [
    [-20, 10, 20, 20, 20, 20, 10, -20],                  # rank 8 (row 0)
    [-30, -20, 20, 40, 40, 20, -20, -30],                # rank 7 (row 1)
    [0, 0, 20, 30, 60, 30, 20, 0],                       # rank 6 (row 2)
    [-5, 10, 30, 50, 80, 80, 30, 10],                    # rank 5 (row 3) - strong center for queens
    [10, 40, 70, 90, 100, 90, 70, 40],                   # rank 4 (row 4) - optimal position
    [-20, 50, 80, 80, 80, 80, 50, -20],                  # rank 3 (row 5)
    [-20, 10, 30, 50, 60, 50, 30, -20],                  # rank 2 (row 6)
    [-30, -40, -20, -20, -20, -20, -40, -30],           # rank 1 (row 7)
]


# King safety table for middlegame/late middlegame
KING_TABLE: list[list[int]] = [
    [-85,-70,-60,-45,-25,0,10,30],                        # rank 8 (row 0)
    [-75,-65,-45,-20,-10,10,20,35],                      # rank 7 (row 1)
    [-75,-50,0,25,50,50,25,50],                           # rank 6 (row 2) - encourage centralization
    [20,25,30,40,45,40,25,20],                           # rank 5 (row 3)
    [25,30,35,50,60,50,35,25],                            # rank 4 (row 4)
    [-40,-30,-10,0,0,0,-10,-30],                          # rank 3 (row 5)
    [-60,-50,-30,-20,-10,0,-20,-40],                      # rank 2 (row 6)
    [-90,-80,-65,-55,-40,-35,-40,-70],                    # rank 1 (row 7)
]
