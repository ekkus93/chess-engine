"""Helpers for endgame technique and conversion scoring."""

from chess_game.chess.board import Board
from chess_game.chess.conversion_guidance import winning_conversion_evaluation_score
from chess_game.chess.defensive_endgame_guidance import defensive_endgame_evaluation_score
from chess_game.chess.evaluation_tables import (
    ACTIVE_KING_ENDGAME_BONUS,
    BLOCKADED_PASSED_PAWN_BONUS,
    COUNTERPLAY_REDUCTION_BONUS,
    ENEMY_KING_BOX_BONUS,
    HEAVY_PIECE_COORDINATION_BONUS,
    HEAVY_PIECE_ACTIVITY_BONUS,
    KING_CUTOFF_BONUS,
    KING_ESCORT_PASSED_PAWN_BONUS,
    MATERIAL_VALUES,
    MATING_EDGE_BONUS,
    MATING_KING_DISTANCE_BONUS,
    MATING_MATERIAL_BASE,
    PROMOTION_SQUARE_CONTROL_BONUS,
    QUEENS_OFF_WHEN_AHEAD_BONUS,
    ROOK_BEHIND_PASSED_PAWN_BONUS,
    ROOKS_OFF_WHEN_AHEAD_BONUS,
    SIMPLIFICATION_BONUS_SCALE,
    STARTING_NON_PAWN_MATERIAL,
)
from chess_game.chess.rook_endgame_guidance import rook_endgame_evaluation_score
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


def evaluate_endgame_technique(board: Board, endgame_phase: int) -> int:
    """Return endgame-technique bonuses such as king activity and mating method."""

    if endgame_phase == 0:
        return 0
    score = _active_king_score(board, endgame_phase)
    score += _blockaded_passed_pawn_score(board, endgame_phase)
    score += _mating_material_score(board)
    score += scale_signed(defensive_endgame_evaluation_score(board), endgame_phase)
    return score


def evaluate_conversion(board: Board, endgame_phase: int) -> int:
    """Return simplification and conversion bonuses when materially ahead."""

    material_without_kings = _material_without_kings(board)
    lead = material_without_kings[Color.WHITE] - material_without_kings[Color.BLACK]
    if lead == 0:
        return 0
    leading_color = Color.WHITE if lead > 0 else Color.BLACK
    lead_value = abs(lead)
    total_non_pawn_material = _total_non_pawn_material(board)
    simplification = max(0, STARTING_NON_PAWN_MATERIAL - total_non_pawn_material)
    bonus = (lead_value * simplification) // (STARTING_NON_PAWN_MATERIAL * 2)
    bonus *= SIMPLIFICATION_BONUS_SCALE
    if not _has_queen(board, _opponent(leading_color)):
        bonus += QUEENS_OFF_WHEN_AHEAD_BONUS
    if not _has_rook(board, _opponent(leading_color)):
        bonus += ROOKS_OFF_WHEN_AHEAD_BONUS
    if endgame_phase > 0:
        bonus = (bonus * (50 + endgame_phase)) // 100
    return _color_sign(leading_color) * bonus


def evaluate_progress(board: Board, endgame_phase: int) -> int:
    """Return progress and restriction bonuses for practical endgame play."""

    material_without_kings = _material_without_kings(board)
    lead = material_without_kings[Color.WHITE] - material_without_kings[Color.BLACK]
    if lead == 0:
        return 0
    leading_color = Color.WHITE if lead > 0 else Color.BLACK
    if not _has_conversion_assets(board, leading_color):
        return 0
    bonus = 0
    bonus += _king_cutoff_score(board, leading_color)
    bonus += _rook_behind_passed_pawn_score(board, leading_color)
    bonus += _king_escort_passed_pawn_score(board, leading_color)
    bonus += _promotion_square_control_score(board, leading_color)
    bonus += _enemy_king_box_score(board, leading_color)
    bonus += _counterplay_reduction_score(board, leading_color)
    bonus += _heavy_piece_activity_score(board, leading_color)
    bonus += abs(winning_conversion_evaluation_score(board))
    phase_scale = max(40, 40 + endgame_phase)
    return _color_sign(leading_color) * ((bonus * phase_scale) // 100)


def evaluate_rook_endgames(board: Board, endgame_phase: int) -> int:
    """Return rook-endgame placement and defense bonuses."""

    if endgame_phase == 0:
        return 0
    return scale_signed(rook_endgame_evaluation_score(board), endgame_phase)


def _collect_pawn_positions(board: Board) -> dict[Color, list[tuple[int, int]]]:
    positions = {Color.WHITE: [], Color.BLACK: []}
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


def _active_king_score(board: Board, endgame_phase: int) -> int:
    score = 0
    for color, king_square in iter_king_squares(board):
        distance = center_distance(int(king_square.row), int(king_square.col))
        score += _color_sign(color) * (
            ACTIVE_KING_ENDGAME_BONUS - distance * MATING_KING_DISTANCE_BONUS
        )
    return scale_signed(score, endgame_phase)


def _blockaded_passed_pawn_score(board: Board, endgame_phase: int) -> int:
    pawn_positions = _collect_pawn_positions(board)
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
                score += _color_sign(color) * BLOCKADED_PASSED_PAWN_BONUS
    return scale_signed(score, endgame_phase)


def _mating_material_score(board: Board) -> int:
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
        color_score = MATING_MATERIAL_BASE[endgame_type]
        color_score += (3 - edge_distance) * MATING_EDGE_BONUS
        color_score += max(0, 7 - king_distance) * MATING_KING_DISTANCE_BONUS
        if _heavy_piece_coordination(board, color):
            color_score += HEAVY_PIECE_COORDINATION_BONUS
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


def _king_cutoff_score(board: Board, color: Color) -> int:
    enemy_king = _find_king(board, _opponent(color))
    if enemy_king is None:
        return 0
    enemy_row = int(enemy_king.row)
    enemy_col = int(enemy_king.col)
    score = 0
    for piece, row, col in iter_color_pieces(board, color):
        if piece.kind not in (PieceType.ROOK, PieceType.QUEEN):
            continue
        if row in {0, 7} or col in {0, 7}:
            continue
        row_distance = abs(row - enemy_row)
        col_distance = abs(col - enemy_col)
        if row == enemy_row and col_distance >= 2:
            score += KING_CUTOFF_BONUS
        if col == enemy_col and row_distance >= 2:
            score += KING_CUTOFF_BONUS
    return score


def _rook_behind_passed_pawn_score(board: Board, color: Color) -> int:
    rooks = rook_positions(board, color)
    if not rooks:
        return 0
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
                score += ROOK_BEHIND_PASSED_PAWN_BONUS
    return score


def _king_escort_passed_pawn_score(board: Board, color: Color) -> int:
    king_square = _find_king(board, color)
    enemy_king = _find_king(board, _opponent(color))
    if king_square is None or enemy_king is None:
        return 0
    own_king = (int(king_square.row), int(king_square.col))
    enemy_king_pos = (int(enemy_king.row), int(enemy_king.col))
    score = 0
    for pawn_row, pawn_col in _passed_pawns_for_color(board, color):
        if not _is_advanced_passer(color, pawn_row):
            continue
        own_distance = abs(own_king[0] - pawn_row) + abs(own_king[1] - pawn_col)
        enemy_distance = abs(enemy_king_pos[0] - pawn_row) + abs(enemy_king_pos[1] - pawn_col)
        if own_distance + 1 < enemy_distance:
            score += KING_ESCORT_PASSED_PAWN_BONUS
    return score


def _promotion_square_control_score(board: Board, color: Color) -> int:
    enemy_king = _find_king(board, _opponent(color))
    if enemy_king is None:
        return 0
    enemy_king_pos = (int(enemy_king.row), int(enemy_king.col))
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
            score += PROMOTION_SQUARE_CONTROL_BONUS
        for piece, row, col in iter_color_pieces(board, color):
            if piece.kind in (PieceType.ROOK, PieceType.QUEEN) and col == pawn_col:
                if color == Color.WHITE and row > pawn_row:
                    score += PROMOTION_SQUARE_CONTROL_BONUS // 2
                if color == Color.BLACK and row < pawn_row:
                    score += PROMOTION_SQUARE_CONTROL_BONUS // 2
        if _own_king_controls_square(board, color, promotion_square):
            score += PROMOTION_SQUARE_CONTROL_BONUS // 2
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


def _enemy_king_box_score(board: Board, color: Color) -> int:
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
    return restricted * ENEMY_KING_BOX_BONUS


def _counterplay_reduction_score(board: Board, color: Color) -> int:
    enemy_color = _opponent(color)
    own_king = _find_king(board, color)
    if own_king is None:
        return 0
    own_king_row = int(own_king.row)
    own_king_col = int(own_king.col)
    score = 0
    for piece, row, col in iter_color_pieces(board, enemy_color):
        if piece.kind not in (PieceType.ROOK, PieceType.QUEEN):
            continue
        if row == own_king_row or col == own_king_col:
            score -= COUNTERPLAY_REDUCTION_BONUS
    return score


def _heavy_piece_activity_score(board: Board, color: Color) -> int:
    enemy_king = _find_king(board, _opponent(color))
    if enemy_king is None:
        return 0
    enemy_row = int(enemy_king.row)
    enemy_col = int(enemy_king.col)
    score = 0
    for piece, row, col in iter_color_pieces(board, color):
        if piece.kind not in (PieceType.ROOK, PieceType.QUEEN):
            continue
        distance = max(abs(row - enemy_row), abs(col - enemy_col))
        if distance <= 2:
            score += HEAVY_PIECE_ACTIVITY_BONUS
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


def _color_sign(color: Color) -> int:
    return 1 if color == Color.WHITE else -1


def _opponent(color: Color) -> Color:
    return Color.BLACK if color == Color.WHITE else Color.WHITE


def _pawn_direction(color: Color) -> int:
    return -1 if color == Color.WHITE else 1
