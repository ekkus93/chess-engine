"""Pawn-structure evaluation helpers shared by the main evaluator."""

from dataclasses import dataclass

from chess_game.chess.board import Board
from chess_game.chess.constants import ConstantSquare, get_col_constant, get_row_constant
from chess_game.chess.opening_development import undeveloped_minor_piece_count
from chess_game.chess.evaluation_tables import (
    BACKWARD_PAWN_PENALTY,
    BLOCKED_CENTRAL_PAWN_PENALTY,
    CANDIDATE_PASSED_PAWN_BONUS,
    CENTER_FILES,
    CENTRAL_DUO_BONUS,
    CONNECTED_PASSED_PAWN_BONUS,
    DOUBLED_PAWN_PENALTY,
    ISOLATED_PAWN_PENALTY,
    KING_SHELTER_LOOSENING_PENALTY,
    PASSED_PAWN_BONUS_BY_PROGRESS,
    PAWN_ISLAND_PENALTY,
    PAWN_MAJORITY_ENDGAME_BONUS,
    WEAK_CHAIN_PAWN_PENALTY,
)
from chess_game.chess.strategy_utils import is_passed_pawn
from chess_game.chess.types import Color, PieceType


@dataclass(frozen=True)
class PawnStructureContext:
    """Shared per-color pawn-structure inputs."""

    color: Color
    sign: int
    color_positions: list[tuple[int, int]]
    enemy_positions: list[tuple[int, int]]
    file_map: dict[int, list[int]]
    endgame_phase: int
    middlegame_phase: int


@dataclass(frozen=True)
class PhaseWeights:
    """Phase weights used by pawn-structure scoring."""

    endgame: int
    middlegame: int


def evaluate_pawn_structure(board: Board, endgame_phase: int) -> int:
    """Return the signed pawn-structure score for both sides."""

    pawn_positions = collect_pawn_positions(board)
    phases = PhaseWeights(endgame=endgame_phase, middlegame=100 - endgame_phase)
    return sum(
        _pawn_structure_score_for_color(
            board,
            color,
            pawn_positions[color],
            pawn_positions[_opponent(color)],
            phases,
        )
        for color in (Color.WHITE, Color.BLACK)
    )


def collect_pawn_positions(board: Board) -> dict[Color, list[tuple[int, int]]]:
    """Return pawn coordinates for both colors."""

    pawn_positions: dict[Color, list[tuple[int, int]]] = {
        Color.WHITE: [],
        Color.BLACK: [],
    }
    for row_index, row in enumerate(board.board):
        for col_index, piece in enumerate(row):
            if piece is not None and piece.kind == PieceType.PAWN:
                pawn_positions[piece.color].append((row_index, col_index))
    return pawn_positions


def _pawn_structure_score_for_color(
    board: Board,
    color: Color,
    color_positions: list[tuple[int, int]],
    enemy_positions: list[tuple[int, int]],
    phases: PhaseWeights,
) -> int:
    context = PawnStructureContext(
        color=color,
        sign=_color_sign(color),
        color_positions=color_positions,
        enemy_positions=enemy_positions,
        file_map=_group_rows_by_file(color_positions),
        endgame_phase=phases.endgame,
        middlegame_phase=phases.middlegame,
    )
    passed_pawns: set[tuple[int, int]] = set()
    score = 0
    score -= context.sign * _pawn_island_penalty(context.file_map)
    score += context.sign * _central_duo_bonus(context.color_positions)
    score += context.sign * _pawn_majority_bonus(
        context.color_positions,
        context.enemy_positions,
        context.endgame_phase,
    )
    score += context.sign * _prepared_central_break_bonus(
        board,
        context.color,
        context.color_positions,
        context.middlegame_phase,
    )
    score -= context.sign * _overextended_chain_penalty(
        context.color,
        context.color_positions,
        context.middlegame_phase,
    )
    score -= context.sign * _loose_shelter_pawn_penalty(
        board,
        context.color,
        context.color_positions,
        context.middlegame_phase,
    )
    score -= context.sign * _shelter_file_gap_penalty(
        board,
        context.color,
        context.file_map,
        context.middlegame_phase,
    )
    score -= context.sign * _weak_shelter_square_complex_penalty(
        board,
        context.color,
        context.file_map,
        context.middlegame_phase,
    )
    for row, col in context.color_positions:
        score -= context.sign * _pawn_file_penalty(context.file_map, col)
        score += _pawn_square_structure_score(
            board,
            context,
            row,
            col,
            passed_pawns,
        )
    for row, col in passed_pawns:
        if _has_connected_passed_pawn(row, col, passed_pawns):
            score += context.sign * CONNECTED_PASSED_PAWN_BONUS
    return score


def _pawn_square_structure_score(
    board: Board,
    context: PawnStructureContext,
    row: int,
    col: int,
    passed_pawns: set[tuple[int, int]],
) -> int:
    score = 0
    if _is_backward_pawn(
        board,
        context.color,
        (row, col),
        context.file_map,
        context.enemy_positions,
    ):
        score -= context.sign * BACKWARD_PAWN_PENALTY
    if _is_weak_pawn_chain(context.color, row, col, context.color_positions):
        score -= context.sign * WEAK_CHAIN_PAWN_PENALTY
    if _is_blocked_central_pawn(board, context.color, row, col):
        score -= context.sign * BLOCKED_CENTRAL_PAWN_PENALTY
    if is_passed_pawn(context.color, row, col, context.enemy_positions):
        progress = _pawn_progress(context.color, row)
        score += context.sign * PASSED_PAWN_BONUS_BY_PROGRESS[progress]
        passed_pawns.add((row, col))
    elif _is_candidate_passed_pawn(context.color, row, col, context.enemy_positions):
        progress = _pawn_progress(context.color, row)
        score += context.sign * (CANDIDATE_PASSED_PAWN_BONUS + progress * 2)
    return score


def _group_rows_by_file(positions: list[tuple[int, int]]) -> dict[int, list[int]]:
    grouped: dict[int, list[int]] = {}
    for row, col in positions:
        grouped.setdefault(col, []).append(row)
    for rows in grouped.values():
        rows.sort()
    return grouped


def _pawn_file_penalty(file_map: dict[int, list[int]], col: int) -> int:
    penalty = 0
    if len(file_map.get(col, [])) > 1:
        penalty += DOUBLED_PAWN_PENALTY
    if not any(file_map.get(file_index) for file_index in (col - 1, col + 1)):
        penalty += ISOLATED_PAWN_PENALTY
    return penalty


def _pawn_island_penalty(file_map: dict[int, list[int]]) -> int:
    occupied_files = sorted(file_map)
    if not occupied_files:
        return 0
    islands = 1
    for current, previous in zip(occupied_files[1:], occupied_files):
        if current != previous + 1:
            islands += 1
    return max(0, islands - 1) * PAWN_ISLAND_PENALTY


def _central_duo_bonus(positions: list[tuple[int, int]]) -> int:
    position_set = set(positions)
    bonus = 0
    for row, col in positions:
        if col not in CENTER_FILES:
            continue
        if (row, col + 1) in position_set or (row, col - 1) in position_set:
            bonus += CENTRAL_DUO_BONUS
    return bonus // 2


def _pawn_majority_bonus(
    positions: list[tuple[int, int]],
    enemy_positions: list[tuple[int, int]],
    endgame_phase: int,
) -> int:
    if endgame_phase == 0:
        return 0
    bonus = 0
    for files in ({0, 1, 2}, {3, 4}, {5, 6, 7}):
        friendly = sum(1 for _, col in positions if col in files)
        enemy = sum(1 for _, col in enemy_positions if col in files)
        if friendly > enemy:
            bonus += (friendly - enemy) * PAWN_MAJORITY_ENDGAME_BONUS
    return (bonus * endgame_phase) // 100


def _loose_shelter_pawn_penalty(
    board: Board,
    color: Color,
    positions: list[tuple[int, int]],
    middlegame_phase: int,
) -> int:
    king_square = board.find_king(color)
    if king_square is None or middlegame_phase == 0 or not _is_castled_king(color, king_square):
        return 0
    shield_row = 6 if color == Color.WHITE else 1
    king_col = int(king_square.col)
    penalty = 0
    for row, col in positions:
        if col not in range(max(0, king_col - 1), min(7, king_col + 1) + 1):
            continue
        distance = abs(row - shield_row)
        if distance == 0:
            continue
        penalty += distance * KING_SHELTER_LOOSENING_PENALTY
        if distance >= 2:
            penalty += KING_SHELTER_LOOSENING_PENALTY // 2
    return (penalty * middlegame_phase) // 100


def _prepared_central_break_bonus(
    board: Board,
    color: Color,
    positions: list[tuple[int, int]],
    middlegame_phase: int,
) -> int:
    advanced_central_pawns = _advanced_central_pawn_count(color, positions)
    if advanced_central_pawns == 0 or middlegame_phase == 0:
        return 0
    undeveloped = undeveloped_minor_piece_count(board, color)
    total_minors = _minor_piece_count(board, color)
    developed = max(0, total_minors - undeveloped)
    raw_score = (advanced_central_pawns * developed * 4) - (
        advanced_central_pawns * max(0, undeveloped - 1) * 5
    )
    return (raw_score * middlegame_phase) // 100


def _shelter_file_gap_penalty(
    board: Board,
    color: Color,
    file_map: dict[int, list[int]],
    middlegame_phase: int,
) -> int:
    king_square = board.find_king(color)
    if king_square is None or middlegame_phase == 0 or not _is_castled_king(color, king_square):
        return 0
    king_col = int(king_square.col)
    gap_files = sum(
        1
        for file_index in range(max(0, king_col - 1), min(7, king_col + 1) + 1)
        if not file_map.get(file_index)
    )
    if gap_files == 0:
        return 0
    penalty = gap_files * KING_SHELTER_LOOSENING_PENALTY * 2
    if _enemy_has_queen(board, color):
        penalty += gap_files * KING_SHELTER_LOOSENING_PENALTY
    return (penalty * middlegame_phase) // 100


def _overextended_chain_penalty(
    color: Color,
    positions: list[tuple[int, int]],
    middlegame_phase: int,
) -> int:
    if middlegame_phase == 0:
        return 0
    overextended_count = sum(
        1
        for row, col in positions
        if _is_overextended_chain_pawn(color, row, col, positions)
    )
    penalty = overextended_count * WEAK_CHAIN_PAWN_PENALTY * 2
    return (penalty * middlegame_phase) // 100


def _weak_shelter_square_complex_penalty(
    board: Board,
    color: Color,
    file_map: dict[int, list[int]],
    middlegame_phase: int,
) -> int:
    king_square = board.find_king(color)
    if king_square is None or middlegame_phase == 0 or not _is_castled_king(color, king_square):
        return 0
    shield_row = 6 if color == Color.WHITE else 1
    king_col = int(king_square.col)
    exposed_counts = {0: 0, 1: 0}
    for file_index in range(max(0, king_col - 1), min(7, king_col + 1) + 1):
        if _shield_square_is_exposed(file_map, shield_row, file_index):
            exposed_counts[(shield_row + file_index) % 2] += 1
    penalty = 0
    for square_color, exposed_count in exposed_counts.items():
        if exposed_count < 2:
            continue
        penalty += (exposed_count - 1) * KING_SHELTER_LOOSENING_PENALTY
        if _enemy_has_bishop_on_color_complex(board, color, square_color):
            penalty += KING_SHELTER_LOOSENING_PENALTY
    return (penalty * middlegame_phase) // 100


def _advanced_central_pawn_count(color: Color, positions: list[tuple[int, int]]) -> int:
    return sum(
        1
        for row, col in positions
        if col in CENTER_FILES and _central_pawn_has_advanced(color, row)
    )


def _central_pawn_has_advanced(color: Color, row: int) -> bool:
    return row <= 4 if color == Color.WHITE else row >= 3


def _minor_piece_count(board: Board, color: Color) -> int:
    return sum(
        1
        for row in board.board
        for piece in row
        if piece is not None
        and piece.color == color
        and piece.kind in {PieceType.KNIGHT, PieceType.BISHOP}
    )


def _enemy_has_queen(board: Board, color: Color) -> bool:
    enemy = _opponent(color)
    return any(
        piece is not None and piece.color == enemy and piece.kind == PieceType.QUEEN
        for row in board.board
        for piece in row
    )


def _enemy_has_bishop_on_color_complex(
    board: Board,
    color: Color,
    square_color: int,
) -> bool:
    enemy = _opponent(color)
    return any(
        piece is not None
        and piece.color == enemy
        and piece.kind == PieceType.BISHOP
        and (row_index + col_index) % 2 == square_color
        for row_index, row in enumerate(board.board)
        for col_index, piece in enumerate(row)
    )


def _shield_square_is_exposed(
    file_map: dict[int, list[int]],
    shield_row: int,
    file_index: int,
) -> bool:
    rows = file_map.get(file_index, [])
    return not rows or min(abs(row - shield_row) for row in rows) >= 1


def _is_overextended_chain_pawn(
    color: Color,
    row: int,
    col: int,
    pawn_positions: list[tuple[int, int]],
) -> bool:
    if not _is_advanced_pawn(color, row):
        return False
    supporting_pawns = _rear_adjacent_supporters(color, row, col, pawn_positions)
    return bool(supporting_pawns) and all(
        not _rear_adjacent_supporters(color, support_row, support_col, pawn_positions)
        for support_row, support_col in supporting_pawns
    )


def _rear_adjacent_supporters(
    color: Color,
    row: int,
    col: int,
    pawn_positions: list[tuple[int, int]],
) -> list[tuple[int, int]]:
    support_row = row + 1 if color == Color.WHITE else row - 1
    return [
        (support_row, neighbor_col)
        for neighbor_col in (col - 1, col + 1)
        if (support_row, neighbor_col) in pawn_positions
    ]


def _is_weak_pawn_chain(
    color: Color,
    row: int,
    col: int,
    pawn_positions: list[tuple[int, int]],
) -> bool:
    if not _is_advanced_pawn(color, row):
        return False
    for neighbor_col in (col - 1, col + 1):
        if color == Color.WHITE and (row + 1, neighbor_col) in pawn_positions:
            return False
        if color == Color.BLACK and (row - 1, neighbor_col) in pawn_positions:
            return False
    return True


def _is_advanced_pawn(color: Color, row: int) -> bool:
    return row <= 3 if color == Color.WHITE else row >= 4


def _is_blocked_central_pawn(board: Board, color: Color, row: int, col: int) -> bool:
    if col not in CENTER_FILES:
        return False
    next_row = row + _pawn_direction(color)
    if not 0 <= next_row < 8:
        return False
    next_square = ConstantSquare(
        row=get_row_constant(next_row),
        col=get_col_constant(col),
    )
    return board.get_piece(next_square) is not None


def _is_candidate_passed_pawn(
    color: Color,
    row: int,
    col: int,
    enemy_positions: list[tuple[int, int]],
) -> bool:
    blockers = 0
    for enemy_row, enemy_col in enemy_positions:
        if enemy_col != col:
            continue
        if color == Color.WHITE and enemy_row < row:
            blockers += 1
        if color == Color.BLACK and enemy_row > row:
            blockers += 1
    if blockers != 0:
        return False
    for enemy_row, enemy_col in enemy_positions:
        if abs(enemy_col - col) != 1:
            continue
        if color == Color.WHITE and enemy_row < row - 1:
            return False
        if color == Color.BLACK and enemy_row > row + 1:
            return False
    return True


def _has_connected_passed_pawn(
    row: int,
    col: int,
    passed_pawns: set[tuple[int, int]],
) -> bool:
    for file_offset in (-1, 1):
        neighbor_col = col + file_offset
        if not 0 <= neighbor_col < 8:
            continue
        valid_rows = {row, row - 1, row + 1}
        if any((candidate_row, neighbor_col) in passed_pawns for candidate_row in valid_rows):
            return True
    return False


def _is_backward_pawn(
    board: Board,
    color: Color,
    pawn_position: tuple[int, int],
    file_map: dict[int, list[int]],
    enemy_positions: list[tuple[int, int]],
) -> bool:
    row, col = pawn_position
    if _has_supporting_adjacent_pawn(color, row, col, file_map):
        return False
    next_row = row + _pawn_direction(color)
    if not 0 <= next_row < 8:
        return False
    next_square = ConstantSquare(
        row=get_row_constant(next_row),
        col=get_col_constant(col),
    )
    if board.get_piece(next_square) is not None:
        return True
    return _enemy_pawn_controls_square(_opponent(color), next_row, col, enemy_positions)


def _has_supporting_adjacent_pawn(
    color: Color,
    row: int,
    col: int,
    file_map: dict[int, list[int]],
) -> bool:
    for file_offset in (-1, 1):
        for neighbor_row in file_map.get(col + file_offset, []):
            if color == Color.WHITE and neighbor_row >= row:
                return True
            if color == Color.BLACK and neighbor_row <= row:
                return True
    return False


def _enemy_pawn_controls_square(
    enemy_color: Color,
    target_row: int,
    target_col: int,
    enemy_positions: list[tuple[int, int]],
) -> bool:
    attack_step = _pawn_direction(enemy_color)
    for enemy_row, enemy_col in enemy_positions:
        if enemy_row + attack_step == target_row and abs(enemy_col - target_col) == 1:
            return True
    return False


def _is_castled_king(color: Color, square: ConstantSquare) -> bool:
    home_row = 7 if color == Color.WHITE else 0
    return int(square.row) == home_row and int(square.col) in {2, 6}


def _pawn_progress(color: Color, row: int) -> int:
    return 6 - row if color == Color.WHITE else row - 1


def _color_sign(color: Color) -> int:
    return 1 if color == Color.WHITE else -1


def _opponent(color: Color) -> Color:
    return Color.BLACK if color == Color.WHITE else Color.WHITE


def _pawn_direction(color: Color) -> int:
    return -1 if color == Color.WHITE else 1
