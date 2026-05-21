"""Helpers for endgame technique and conversion scoring."""

from chess_game.chess.board import Board
from chess_game.chess.evaluation_tables import (
    ACTIVE_KING_ENDGAME_BONUS,
    BLOCKADED_PASSED_PAWN_BONUS,
    HEAVY_PIECE_COORDINATION_BONUS,
    MATERIAL_VALUES,
    MATING_EDGE_BONUS,
    MATING_KING_DISTANCE_BONUS,
    MATING_MATERIAL_BASE,
    QUEENS_OFF_WHEN_AHEAD_BONUS,
    SIMPLIFICATION_BONUS_SCALE,
    STARTING_NON_PAWN_MATERIAL,
)
from chess_game.chess.strategy_utils import (
    center_distance,
    is_passed_pawn,
    iter_board_pieces,
    iter_color_pieces,
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
    if endgame_phase > 0:
        bonus = (bonus * (50 + endgame_phase)) // 100
    return _color_sign(leading_color) * bonus


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


def _active_king_score(board: Board, endgame_phase: int) -> int:
    score = 0
    for color in (Color.WHITE, Color.BLACK):
        king_square = _find_king(board, color)
        if king_square is None:
            continue
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


def _color_sign(color: Color) -> int:
    return 1 if color == Color.WHITE else -1


def _opponent(color: Color) -> Color:
    return Color.BLACK if color == Color.WHITE else Color.WHITE


def _pawn_direction(color: Color) -> int:
    return -1 if color == Color.WHITE else 1
