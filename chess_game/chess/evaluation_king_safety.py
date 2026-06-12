"""King-safety evaluation component.

Extracted from ``evaluation``. Scores king safety, king exposure and defender
coordination (pawn shield, open king files, king-zone attack pressure, back-rank
tension, heavy-piece lane pressure). Imports shared primitives from
``evaluation_helpers``; ``evaluation`` re-imports the three component entry points
(_evaluate_king_safety/_evaluate_king_exposure/_evaluate_defender_coordination).
"""

from __future__ import annotations


from chess_game.chess.board import Board
from chess_game.chess.evaluation_helpers import (
    _color_sign,
    _find_king,
    _is_castled_king,
    _iter_board_pieces,
    _iter_color_pieces,
    _opponent,
)
from chess_game.chess.constants import ConstantSquare, get_col_constant, get_row_constant
from chess_game.chess.eval_weights import EvalWeights
from chess_game.chess.defensive_priorities import (
    h_pawn_exposure_penalty as _h_pawn_exposure_penalty,
)
from chess_game.chess.opening_development import (
    unforced_shelter_loosening_penalty as _unforced_shelter_loosening_penalty,
)
from chess_game.chess.tactical_transition_guidance import (
    tactical_transition_king_penalty as _tactical_transition_king_penalty,
)
from chess_game.chess.strategy_utils import (
    iter_king_squares as _iter_king_squares,
    path_clear_between as _path_clear_between,
    scale_signed as _scale_signed,
)
from chess_game.chess.evaluation_tables import (
    CENTER_FILES,
)
from chess_game.chess.types import Color, PieceType


def _evaluate_king_safety(
    board: Board,
    middlegame_phase: int,
    weights: EvalWeights,
) -> int:
    if middlegame_phase == 0:
        return 0
    k = weights.king
    king_safety_score = 0
    for color in (Color.WHITE, Color.BLACK):
        king_square = _find_king(board, color)
        if king_square is None:
            continue
        color_score = 0
        attack_pressure = _king_zone_attack_pressure(board, color, king_square, weights)
        if _is_castled_king(color, king_square):
            color_score += k.castled_king_bonus
        color_score += _pawn_shield_score(board, color, king_square, weights)
        color_score -= _open_king_file_penalty(board, color, king_square, weights)
        color_score -= _unforced_shelter_loosening_penalty(
            board,
            color,
            king_square,
            attack_pressure,
            weights,
        )
        color_score -= _tactical_transition_king_penalty(board, color)
        color_score -= attack_pressure
        color_score -= _back_rank_tension(board, color, king_square, weights)
        if _is_exposed_central_king(king_square):
            color_score -= k.exposed_central_king_penalty
        king_safety_score += _color_sign(color) * color_score
    return _scale_signed(king_safety_score, middlegame_phase)

def _evaluate_king_exposure(
    board: Board,
    middlegame_phase: int,
    weights: EvalWeights,
) -> int:
    if middlegame_phase == 0:
        return 0
    k = weights.king
    score = 0
    queens_on_board = _queens_on_board(board)
    for color in (Color.WHITE, Color.BLACK):
        king_square = _find_king(board, color)
        if king_square is None:
            continue
        color_score = 0
        if queens_on_board and _is_exposed_central_king(king_square):
            color_score -= k.central_king_with_queens_penalty
        color_score -= _heavy_piece_lane_pressure(board, color, king_square, weights)
        color_score -= _h_pawn_exposure_penalty(board, color)
        score += _color_sign(color) * color_score
    return _scale_signed(score, middlegame_phase)

def _evaluate_defender_coordination(
    board: Board,
    middlegame_phase: int,
    weights: EvalWeights,
) -> int:
    if middlegame_phase == 0 or not _queens_on_board(board):
        return 0
    score = 0
    for color, king_square in _iter_king_squares(board):
        score += _color_sign(color) * (
            -_heavy_defender_distance_penalty(board, color, king_square, weights)
        )
    return _scale_signed(score, middlegame_phase)

def _pawn_shield_score(
    board: Board,
    color: Color,
    square: ConstantSquare,
    weights: EvalWeights,
) -> int:
    if not _is_castled_king(color, square):
        return 0
    shield_row = 6 if color == Color.WHITE else 1
    king_col = int(square.col)
    score = 0
    for file_index in range(max(0, king_col - 1), min(7, king_col + 1) + 1):
        shield_square = ConstantSquare(
            row=get_row_constant(shield_row),
            col=get_col_constant(file_index),
        )
        piece = board.get_piece(shield_square)
        if piece is not None and piece.color == color and piece.kind == PieceType.PAWN:
            score += weights.king.pawn_shield_bonus
    return score

def _open_king_file_penalty(
    board: Board,
    color: Color,
    square: ConstantSquare,
    weights: EvalWeights,
) -> int:
    penalty = 0
    king_col = int(square.col)
    for file_index in range(max(0, king_col - 1), min(7, king_col + 1) + 1):
        if not _file_has_friendly_pawn(board, color, file_index):
            penalty += weights.king.open_king_file_penalty
    return penalty

def _file_has_friendly_pawn(board: Board, color: Color, file_index: int) -> bool:
    for rank_index in range(8):
        square = ConstantSquare(
            row=get_row_constant(rank_index),
            col=get_col_constant(file_index),
        )
        piece = board.get_piece(square)
        if piece is not None and piece.color == color and piece.kind == PieceType.PAWN:
            return True
    return False

def _king_zone_attack_pressure(
    board: Board,
    color: Color,
    square: ConstantSquare,
    weights: EvalWeights,
) -> int:
    enemy_color = _opponent(color)
    king_row = int(square.row)
    king_col = int(square.col)
    kzap = weights.king.king_zone_attack_penalty
    penalty = 0
    for piece, row, col in _iter_color_pieces(board, enemy_color):
        distance = max(abs(row - king_row), abs(col - king_col))
        if distance > 2:
            continue
        if piece.kind == PieceType.QUEEN:
            penalty += kzap * 3
        elif piece.kind == PieceType.ROOK:
            penalty += kzap * 2
        elif piece.kind in (PieceType.BISHOP, PieceType.KNIGHT):
            penalty += kzap
    return penalty

def _back_rank_tension(
    board: Board,
    color: Color,
    square: ConstantSquare,
    weights: EvalWeights,
) -> int:
    home_row = 7 if color == Color.WHITE else 0
    if int(square.row) != home_row:
        return 0
    forward_row = home_row - 1 if color == Color.WHITE else home_row + 1
    if not 0 <= forward_row < 8:
        return 0
    for file_index in range(max(0, int(square.col) - 1), min(7, int(square.col) + 1) + 1):
        luft_square = ConstantSquare(
            row=get_row_constant(forward_row),
            col=get_col_constant(file_index),
        )
        if board.get_piece(luft_square) is None:
            return 0
    return weights.king.back_rank_tension_penalty

def _is_exposed_central_king(square: ConstantSquare) -> bool:
    return int(square.col) in CENTER_FILES

def _queens_on_board(board: Board) -> bool:
    return any(piece.kind == PieceType.QUEEN for piece, _, _ in _iter_board_pieces(board))

def _heavy_piece_lane_pressure(
    board: Board,
    color: Color,
    square: ConstantSquare,
    weights: EvalWeights,
) -> int:
    enemy_color = _opponent(color)
    king_row = int(square.row)
    king_col = int(square.col)
    penalty = 0
    for piece, row, col in _iter_color_pieces(board, enemy_color):
        if piece.kind not in (PieceType.ROOK, PieceType.QUEEN):
            continue
        if row == king_row or col == king_col:
            if _path_clear_between(board, (row, col), (king_row, king_col)):
                penalty += weights.king.heavy_file_pressure_penalty
    return penalty

def _heavy_defender_distance_penalty(
    board: Board,
    color: Color,
    king_square: ConstantSquare,
    weights: EvalWeights,
) -> int:
    king_row = int(king_square.row)
    king_col = int(king_square.col)
    penalty = 0
    for piece, row, col in _iter_color_pieces(board, color):
        if piece.kind not in (PieceType.QUEEN, PieceType.ROOK):
            continue
        distance = max(abs(row - king_row), abs(col - king_col))
        if distance >= 4:
            penalty += weights.king.defender_distance_penalty
    return penalty
