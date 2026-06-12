"""Leaf helper predicates for opening-development guidance.

Extracted from ``opening_development``: self-contained king-safety / queen-exposure /
castling-state predicate helpers (each calls no other opening_development function).
``opening_development`` re-imports the ones it uses. Cycle-free.
"""

from __future__ import annotations

from chess_game.chess.board import Board
from chess_game.chess.constants import ConstantSquare, get_col_constant, get_row_constant
from chess_game.chess.eval_weights import EvalWeights
from chess_game.chess.strategy_utils import (
    iter_color_pieces,
)
from chess_game.chess.types import Color, PieceType




def _is_wing_knight_lunge(color: Color, row: int, col: int) -> bool:
    return col in {1, 6} and (row <= 3 if color == Color.WHITE else row >= 4)

def _is_castled_king(color: Color, square: ConstantSquare) -> bool:
    """Return True when the king already sits on a castled home-rank square."""

    home_row = 7 if color == Color.WHITE else 0
    return int(square.row) == home_row and int(square.col) in {2, 6}

def _piece_in_enemy_half(color: Color, row: int) -> bool:
    """Return True when the piece has advanced far enough to count as a raid."""

    return row <= 3 if color == Color.WHITE else row >= 4

def _queen_on_flank_sortie(color: Color, row: int) -> bool:
    return row <= 4 if color == Color.WHITE else row >= 3

def _flank_pawn_is_overextended(color: Color, row: int) -> bool:
    return row <= 4 if color == Color.WHITE else row >= 3

def _edge_space_grab(color: Color, row: int) -> bool:
    return row == 5 if color == Color.WHITE else row == 2

def _queen_in_enemy_half(color: Color, queen_row: int) -> bool:
    return queen_row <= 2 if color == Color.WHITE else queen_row >= 5

def _queens_on_board(board: Board) -> bool:
    white_has_queen = any(
        piece.kind == PieceType.QUEEN
        for piece, _, _ in iter_color_pieces(board, Color.WHITE)
    )
    black_has_queen = any(
        piece.kind == PieceType.QUEEN
        for piece, _, _ in iter_color_pieces(board, Color.BLACK)
    )
    return white_has_queen or black_has_queen

def _queen_has_nearby_support(
    board: Board,
    color: Color,
    queen_row: int,
    queen_col: int,
) -> bool:
    for piece, row, col in iter_color_pieces(board, color):
        if piece.kind == PieceType.QUEEN:
            continue
        if max(abs(row - queen_row), abs(col - queen_col)) <= 1:
            return True
    return False

def _distant_queen_from_king_penalty(
    board: Board,
    color: Color,
    queen_row: int,
    queen_col: int,
    weights: EvalWeights | None = None,
) -> int:
    king_square = board.find_king(color)
    if king_square is None:
        return 0
    if weights is None:
        weights = EvalWeights.default()
    king_distance = max(
        abs(int(king_square.row) - queen_row),
        abs(int(king_square.col) - queen_col),
    )
    return weights.king.defender_distance_penalty if king_distance >= 4 else 0

def _king_zone_attack_pressure(
    board: Board,
    color: Color,
    square: ConstantSquare,
) -> int:
    enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
    king_row = int(square.row)
    king_col = int(square.col)
    penalty = 0
    for piece, row, col in iter_color_pieces(board, enemy_color):
        distance = max(abs(row - king_row), abs(col - king_col))
        if distance > 2:
            continue
        if piece.kind == PieceType.QUEEN:
            penalty += 15
        elif piece.kind == PieceType.ROOK:
            penalty += 10
        elif piece.kind in (PieceType.BISHOP, PieceType.KNIGHT):
            penalty += 5
    return penalty

def _castling_options_remaining(board: Board, color: Color) -> int:
    rights = board.castling_rights
    if color == Color.WHITE:
        return int(rights.white_kingside) + int(rights.white_queenside)
    return int(rights.black_kingside) + int(rights.black_queenside)

def _uncastled_shell_penalty(
    board: Board, color: Color, king_col: int, weights: EvalWeights | None = None
) -> int:
    if weights is None:
        weights = EvalWeights.default()
    flank_penalty = weights.development.early_flank_raid_penalty
    shield_row = 6 if color == Color.WHITE else 1
    penalty = 0
    for file_index in range(max(0, king_col - 1), min(7, king_col + 1) + 1):
        square = ConstantSquare(
            row=get_row_constant(shield_row),
            col=get_col_constant(file_index),
        )
        pawn = board.get_piece(square)
        if pawn is None or pawn.color != color or pawn.kind != PieceType.PAWN:
            penalty += flank_penalty
    return penalty
