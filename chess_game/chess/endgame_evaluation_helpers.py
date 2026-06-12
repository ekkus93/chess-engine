"""Helper layer for endgame evaluation.

Extracted from ``endgame_evaluation``. The board-query primitives, material/king
helpers and per-aspect endgame scoring functions below the public ``evaluate_*``
entry points (which stay in ``endgame_evaluation`` and import from here). Cycle-free:
nothing here calls back into ``endgame_evaluation``.
"""

from __future__ import annotations

from chess_game.chess.board import Board
from chess_game.chess.eval_weights import EvalWeights
from chess_game.chess.evaluation_tables import (
    MATERIAL_VALUES,
)
from chess_game.chess.rook_endgame_guidance import rook_positions

from chess_game.chess.strategy_utils import (
    center_distance,
    is_passed_pawn,
    iter_board_pieces,
    iter_color_pieces,
    iter_king_squares,
    path_clear_between,
    scale_signed,
)
from chess_game.chess.types import Color, PieceType

_HEAVY_ENDGAME_KING_ACTIVITY_BONUS_PER_STEP = 4
_QUEEN_VS_ROOK_QUEEN_SIDE_BONUS = 80
_QUEEN_VS_ROOK_KING_ACTIVITY_BONUS = 12
_QUEEN_VS_ROOK_PASSIVE_ROOK_PENALTY = 20
_ROOK_SEVENTH_RANK_ENDGAME_BONUS = 24
_ROOK_VS_BISHOP_KING_BONUS = 30
_ROOK_BISHOP_VS_ROOK_BONUS = 25


def _collect_pawn_positions(board: Board) -> dict[Color, list[tuple[int, int]]]:
    positions: dict[Color, list[tuple[int, int]]] = {
        Color.WHITE: [],
        Color.BLACK: [],
    }
    for piece, row, col in iter_board_pieces(board):
        if piece.kind == PieceType.PAWN:
            positions[piece.color].append((row, col))
    return positions

def _find_king(board: Board, color: Color):
    for piece, _, _ in iter_color_pieces(board, color):
        if piece.kind == PieceType.KING:
            return piece.square
    return None

def _passed_pawns_for_color(board: Board, color: Color) -> list[tuple[int, int]]:
    pawn_positions = _collect_pawn_positions(board)
    return [
        (row, col)
        for row, col in pawn_positions[color]
        if is_passed_pawn(color, row, col, pawn_positions[_opponent(color)])
    ]

def _has_conversion_assets(board: Board, color: Color) -> bool:
    return any(
        piece.kind in (PieceType.ROOK, PieceType.QUEEN)
        for piece, _, _ in iter_color_pieces(board, color)
    ) or any(_is_advanced_passer(color, row) for row, _ in _passed_pawns_for_color(board, color))

def _is_advanced_passer(color: Color, row: int) -> bool:
    return row <= 3 if color == Color.WHITE else row >= 4

def _active_king_score(board: Board, endgame_phase: int, weights: EvalWeights) -> int:
    eg = weights.endgame
    mt = weights.mating
    score = 0
    for color, king_square in iter_king_squares(board):
        distance = center_distance(int(king_square.row), int(king_square.col))
        score += _color_sign(color) * (
            eg.active_king_endgame_bonus - distance * mt.mating_king_distance_bonus
        )
    return scale_signed(score, endgame_phase)

def _heavy_endgame_king_activity_score(board: Board, endgame_phase: int) -> int:
    material_without_kings = _material_without_kings(board)
    lead = material_without_kings[Color.WHITE] - material_without_kings[Color.BLACK]
    if lead == 0:
        return 0
    leading_color = Color.WHITE if lead > 0 else Color.BLACK
    bonus = _heavy_endgame_king_activity_bonus(board, leading_color)
    return _color_sign(leading_color) * ((bonus * endgame_phase) // 100)

def _heavy_endgame_king_activity_bonus(board: Board, color: Color) -> int:
    if _has_queen(board, Color.WHITE) or _has_queen(board, Color.BLACK):
        return 0
    if _rook_count(board, Color.WHITE) + _rook_count(board, Color.BLACK) == 0:
        return 0
    if _rook_count(board, Color.WHITE) > 1 and _rook_count(board, Color.BLACK) > 1:
        return 0
    if _material_lead(board, color) < MATERIAL_VALUES[PieceType.BISHOP]:
        return 0
    king_square = _find_king(board, color)
    if king_square is None:
        return 0
    distance = _distance_to_center(int(king_square.row), int(king_square.col))
    return max(0, 20 - distance * _HEAVY_ENDGAME_KING_ACTIVITY_BONUS_PER_STEP)

def _passed_pawn_advancement_progress(board: Board, color: Color) -> int:
    if _material_lead(board, color) < MATERIAL_VALUES[PieceType.ROOK]:
        return 0
    bonus = 0
    for row, _ in _passed_pawns_for_color(board, color):
        advancement = (6 - row) if color == Color.WHITE else (row - 1)
        if advancement > 0:
            bonus += advancement * 6
    return bonus

def _blockaded_passed_pawn_score(
    board: Board, endgame_phase: int, weights: EvalWeights
) -> int:
    pawn_positions = _collect_pawn_positions(board)
    bonus = weights.endgame.blockaded_passed_pawn_bonus
    score = 0
    for color in (Color.WHITE, Color.BLACK):
        enemy_color = _opponent(color)
        for row, col in pawn_positions[enemy_color]:
            if not is_passed_pawn(enemy_color, row, col, pawn_positions[color]):
                continue
            block_row = row + _pawn_direction(enemy_color)
            if not 0 <= block_row < 8:
                continue
            piece = board.board[block_row][col]
            if piece is not None and piece.color == color:
                score += _color_sign(color) * bonus
    return scale_signed(score, endgame_phase)

def _mating_material_score(board: Board, weights: EvalWeights) -> int:
    mt = weights.mating
    mating_bases = mt.mating_material_base()
    for color in (Color.WHITE, Color.BLACK):
        endgame_type = _basic_mating_endgame(board, color)
        if endgame_type is None:
            continue
        king_square = _find_king(board, color)
        enemy_king = _find_king(board, _opponent(color))
        if king_square is None or enemy_king is None:
            continue
        edge_distance = _distance_to_edge(int(enemy_king.row), int(enemy_king.col))
        king_distance = abs(int(king_square.row) - int(enemy_king.row)) + abs(
            int(king_square.col) - int(enemy_king.col)
        )
        color_score = mating_bases[endgame_type]
        color_score += (3 - edge_distance) * mt.mating_edge_bonus
        color_score += max(0, 7 - king_distance) * mt.mating_king_distance_bonus
        if _heavy_piece_coordination(board, color):
            color_score += mt.heavy_piece_coordination_bonus
        return _color_sign(color) * color_score
    return 0

def _basic_mating_endgame(board: Board, color: Color) -> str | None:
    enemy_color = _opponent(color)
    enemy_non_king = [
        piece.kind
        for piece, _, _ in iter_color_pieces(board, enemy_color)
        if piece.kind != PieceType.KING
    ]
    if enemy_non_king:
        return None
    own_non_king = [
        piece.kind
        for piece, _, _ in iter_color_pieces(board, color)
        if piece.kind != PieceType.KING
    ]
    own_non_king.sort(key=int)
    if own_non_king == [PieceType.QUEEN]:
        return "KQK"
    if own_non_king == [PieceType.ROOK]:
        return "KRK"
    if own_non_king == [PieceType.ROOK, PieceType.ROOK]:
        return "KRRK"
    if own_non_king == [PieceType.QUEEN, PieceType.ROOK]:
        return "KQRK"
    return None

def _distance_to_edge(row: int, col: int) -> int:
    return min(row, col, 7 - row, 7 - col)

def _distance_to_center(row: int, col: int) -> int:
    return min(
        abs(row - center_row) + abs(col - center_col)
        for center_row in (3, 4)
        for center_col in (3, 4)
    )

def _heavy_piece_coordination(board: Board, color: Color) -> bool:
    heavy_pieces = [
        (row, col)
        for piece, row, col in iter_color_pieces(board, color)
        if piece.kind in (PieceType.ROOK, PieceType.QUEEN)
    ]
    if len(heavy_pieces) < 2:
        return False
    first_row, first_col = heavy_pieces[0]
    second_row, second_col = heavy_pieces[1]
    if first_row == second_row or first_col == second_col:
        return path_clear_between(
            board,
            (first_row, first_col),
            (second_row, second_col),
        )
    return False

def _king_cutoff_score(board: Board, color: Color, weights: EvalWeights) -> int:
    enemy_king = _find_king(board, _opponent(color))
    if enemy_king is None:
        return 0
    enemy_row = int(enemy_king.row)
    enemy_col = int(enemy_king.col)
    cutoff_bonus = weights.mating.king_cutoff_bonus
    score = 0
    for piece, row, col in iter_color_pieces(board, color):
        if piece.kind not in (PieceType.ROOK, PieceType.QUEEN):
            continue
        if row in {0, 7} or col in {0, 7}:
            continue
        row_distance = abs(row - enemy_row)
        col_distance = abs(col - enemy_col)
        if row == enemy_row and col_distance >= 2:
            score += cutoff_bonus
        if col == enemy_col and row_distance >= 2:
            score += cutoff_bonus
    return score

def _rook_behind_passed_pawn_score(board: Board, color: Color, weights: EvalWeights) -> int:
    rooks = rook_positions(board, color)
    if not rooks:
        return 0
    bonus = weights.mating.rook_behind_passed_pawn_bonus
    score = 0
    for pawn_row, pawn_col in _passed_pawns_for_color(board, color):
        if not _is_advanced_passer(color, pawn_row):
            continue
        for rook_row, rook_col in rooks:
            if rook_col != pawn_col:
                continue
            if color == Color.WHITE and rook_row <= pawn_row:
                continue
            if color == Color.BLACK and rook_row >= pawn_row:
                continue
            if path_clear_between(board, (rook_row, rook_col), (pawn_row, pawn_col)):
                score += bonus
    return score

def _king_escort_passed_pawn_score(board: Board, color: Color, weights: EvalWeights) -> int:
    king_square = _find_king(board, color)
    enemy_king = _find_king(board, _opponent(color))
    if king_square is None or enemy_king is None:
        return 0
    own_king = (int(king_square.row), int(king_square.col))
    enemy_king_pos = (int(enemy_king.row), int(enemy_king.col))
    escort_bonus = weights.mating.king_escort_passed_pawn_bonus
    score = 0
    for pawn_row, pawn_col in _passed_pawns_for_color(board, color):
        if not _is_advanced_passer(color, pawn_row):
            continue
        own_distance = abs(own_king[0] - pawn_row) + abs(own_king[1] - pawn_col)
        enemy_distance = abs(enemy_king_pos[0] - pawn_row) + abs(enemy_king_pos[1] - pawn_col)
        if own_distance + 1 < enemy_distance:
            score += escort_bonus
    return score

def _promotion_square_control_score(board: Board, color: Color, weights: EvalWeights) -> int:
    enemy_king = _find_king(board, _opponent(color))
    if enemy_king is None:
        return 0
    enemy_king_pos = (int(enemy_king.row), int(enemy_king.col))
    promo_bonus = weights.mating.promotion_square_control_bonus
    score = 0
    for pawn_row, pawn_col in _passed_pawns_for_color(board, color):
        if not _is_advanced_passer(color, pawn_row):
            continue
        promotion_row = 0 if color == Color.WHITE else 7
        promotion_square = (promotion_row, pawn_col)
        enemy_distance = abs(enemy_king_pos[0] - promotion_row) + abs(
            enemy_king_pos[1] - pawn_col
        )
        if enemy_distance > 2:
            score += promo_bonus
        for piece, row, col in iter_color_pieces(board, color):
            if piece.kind in (PieceType.ROOK, PieceType.QUEEN) and col == pawn_col:
                if color == Color.WHITE and row > pawn_row:
                    score += promo_bonus // 2
                if color == Color.BLACK and row < pawn_row:
                    score += promo_bonus // 2
        if _own_king_controls_square(board, color, promotion_square):
            score += promo_bonus // 2
    return score

def _own_king_controls_square(
    board: Board,
    color: Color,
    target: tuple[int, int],
) -> bool:
    king_square = _find_king(board, color)
    if king_square is None:
        return False
    return max(
        abs(int(king_square.row) - target[0]),
        abs(int(king_square.col) - target[1]),
    ) <= 1

def _enemy_king_box_score(board: Board, color: Color, weights: EvalWeights) -> int:
    enemy_color = _opponent(color)
    enemy_king = _find_king(board, enemy_color)
    if enemy_king is None:
        return 0
    enemy_moves = [
        move
        for move in board.get_legal_moves_for_color(enemy_color)
        if move[0] == enemy_king
    ]
    restricted = max(0, 8 - len(enemy_moves))
    return restricted * weights.mating.enemy_king_box_bonus

def _counterplay_reduction_score(board: Board, color: Color, weights: EvalWeights) -> int:
    enemy_color = _opponent(color)
    own_king = _find_king(board, color)
    if own_king is None:
        return 0
    own_king_row = int(own_king.row)
    own_king_col = int(own_king.col)
    cp_bonus = weights.mating.counterplay_reduction_bonus
    score = 0
    for piece, row, col in iter_color_pieces(board, enemy_color):
        if piece.kind not in (PieceType.ROOK, PieceType.QUEEN):
            continue
        if row == own_king_row or col == own_king_col:
            score -= cp_bonus
    return score

def _heavy_piece_activity_score(board: Board, color: Color, weights: EvalWeights) -> int:
    enemy_king = _find_king(board, _opponent(color))
    if enemy_king is None:
        return 0
    enemy_row = int(enemy_king.row)
    enemy_col = int(enemy_king.col)
    activity_bonus = weights.mating.heavy_piece_activity_bonus
    score = 0
    for piece, row, col in iter_color_pieces(board, color):
        if piece.kind not in (PieceType.ROOK, PieceType.QUEEN):
            continue
        distance = max(abs(row - enemy_row), abs(col - enemy_col))
        if distance <= 2:
            score += activity_bonus
    return score

def _material_without_kings(board: Board) -> dict[Color, int]:
    material = {Color.WHITE: 0, Color.BLACK: 0}
    for piece, _, _ in iter_board_pieces(board):
        if piece.kind != PieceType.KING:
            material[piece.color] += MATERIAL_VALUES[piece.kind]
    return material

def _total_non_pawn_material(board: Board) -> int:
    total = 0
    for piece, _, _ in iter_board_pieces(board):
        if piece.kind not in (PieceType.KING, PieceType.PAWN):
            total += MATERIAL_VALUES[piece.kind]
    return total

def _has_bishop(board: Board, color: Color) -> bool:
    return any(
        piece.kind == PieceType.BISHOP
        for piece, _, _ in iter_color_pieces(board, color)
    )

def _has_pawn(board: Board, color: Color) -> bool:
    return any(
        piece.kind == PieceType.PAWN
        for piece, _, _ in iter_color_pieces(board, color)
    )

def _has_queen(board: Board, color: Color) -> bool:
    return any(
        piece.kind == PieceType.QUEEN
        for piece, _, _ in iter_color_pieces(board, color)
    )

def _has_rook(board: Board, color: Color) -> bool:
    return any(
        piece.kind == PieceType.ROOK
        for piece, _, _ in iter_color_pieces(board, color)
    )

def _rook_count(board: Board, color: Color) -> int:
    return sum(
        1
        for piece, _, _ in iter_color_pieces(board, color)
        if piece.kind == PieceType.ROOK
    )

def _material_lead(board: Board, color: Color) -> int:
    own_material = 0
    enemy_material = 0
    enemy = _opponent(color)
    for piece, _, _ in iter_board_pieces(board):
        if piece.kind == PieceType.KING:
            continue
        if piece.color == color:
            own_material += MATERIAL_VALUES[piece.kind]
        elif piece.color == enemy:
            enemy_material += MATERIAL_VALUES[piece.kind]
    return own_material - enemy_material

def _color_sign(color: Color) -> int:
    return 1 if color == Color.WHITE else -1

def _is_rook_vs_bishop_king_endgame(board: Board, leading_color: Color) -> bool:
    """Return True when leading side has rook+pawns and enemy has bishop+king only."""
    enemy_color = _opponent(leading_color)
    if _has_queen(board, leading_color) or _has_queen(board, enemy_color):
        return False
    if not _has_rook(board, leading_color) or _has_rook(board, enemy_color):
        return False
    if _has_bishop(board, leading_color) or not _has_bishop(board, enemy_color):
        return False
    return _has_pawn(board, leading_color)

def _is_rook_bishop_vs_rook_endgame(board: Board, leading_color: Color) -> bool:
    """Return True when leading side has rook+bishop and enemy has rook+king only."""
    enemy_color = _opponent(leading_color)
    if _has_queen(board, leading_color) or _has_queen(board, enemy_color):
        return False
    if not _has_rook(board, leading_color) or not _has_rook(board, enemy_color):
        return False
    return _has_bishop(board, leading_color) and not _has_bishop(board, enemy_color)

def _rook_vs_bishop_king_conversion_bonus(board: Board, leading_color: Color) -> int:
    """Bonus when winning side has rook+pawns vs bishop+king.

    Pure R vs B+K (no pawns) is a theoretical draw, so we gate on pawn presence.
    """
    if not _is_rook_vs_bishop_king_endgame(board, leading_color):
        return 0
    if _material_lead(board, leading_color) < MATERIAL_VALUES[PieceType.PAWN]:
        return 0
    enemy_king = _find_king(board, _opponent(leading_color))
    if enemy_king is None:
        return 0
    edge_dist = min(
        int(enemy_king.row),
        7 - int(enemy_king.row),
        int(enemy_king.col),
        7 - int(enemy_king.col),
    )
    return _ROOK_VS_BISHOP_KING_BONUS + (3 - edge_dist) * 5

def _rook_bishop_vs_rook_conversion_bonus(board: Board, leading_color: Color) -> int:
    """Bonus when winning side has rook+bishop vs bare rook."""
    if not _is_rook_bishop_vs_rook_endgame(board, leading_color):
        return 0
    if _material_lead(board, leading_color) < MATERIAL_VALUES[PieceType.PAWN]:
        return 0
    enemy_king = _find_king(board, _opponent(leading_color))
    if enemy_king is None:
        return 0
    edge_dist = min(
        int(enemy_king.row),
        7 - int(enemy_king.row),
        int(enemy_king.col),
        7 - int(enemy_king.col),
    )
    return _ROOK_BISHOP_VS_ROOK_BONUS + (3 - edge_dist) * 4

def _rook_seventh_rank_endgame_score(board: Board, color: Color) -> int:
    """Endgame bonus for a rook on the 7th rank when enemy pawns are still there.

    Only fires when the enemy has at least one pawn in its home three ranks
    (rows 0-2 for White attacking Black, rows 5-7 for Black attacking White),
    so we don't reward a passive rook on an empty seventh rank.
    """
    seventh_row = 1 if color == Color.WHITE else 6
    enemy_color = _opponent(color)
    target_rows = {0, 1, 2} if color == Color.WHITE else {5, 6, 7}
    has_target = any(
        piece.kind == PieceType.PAWN and piece.color == enemy_color and row in target_rows
        for piece, row, _ in iter_board_pieces(board)
    )
    if not has_target:
        return 0
    return sum(
        _ROOK_SEVENTH_RANK_ENDGAME_BONUS
        for piece, row, _ in iter_board_pieces(board)
        if piece.kind == PieceType.ROOK and piece.color == color and row == seventh_row
    )

def _queen_vs_rook_score(
    board: Board, queen_color: Color, rook_color: Color, rook_row: int
) -> int:
    score = _QUEEN_VS_ROOK_QUEEN_SIDE_BONUS
    queen_king = next(
        (sq for sq in iter_king_squares(board) if sq[0] == queen_color), None
    )
    if queen_king is not None:
        king_sq = queen_king[1]
        dist = center_distance(int(king_sq.row), int(king_sq.col))
        score += max(0, 4 - dist) * _QUEEN_VS_ROOK_KING_ACTIVITY_BONUS
    rook_home_row = 7 if rook_color == Color.WHITE else 0
    if rook_row == rook_home_row:
        score -= _QUEEN_VS_ROOK_PASSIVE_ROOK_PENALTY
    return score

def _opponent(color: Color) -> Color:
    return Color.BLACK if color == Color.WHITE else Color.WHITE

def _pawn_direction(color: Color) -> int:
    return -1 if color == Color.WHITE else 1
