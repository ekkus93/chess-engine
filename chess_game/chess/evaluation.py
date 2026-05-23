"""Position evaluation tables and strategic heuristics for the chess AI."""

from __future__ import annotations

from chess_game.chess.board import Board
from chess_game.chess.constants import ConstantSquare, get_col_constant, get_row_constant
from chess_game.chess.endgame_evaluation import (
    evaluate_conversion as _evaluate_conversion,
    evaluate_endgame_technique as _evaluate_endgame_technique,
    evaluate_progress as _evaluate_progress,
)
from chess_game.chess.opening_development import (
    early_shelter_pawn_push_penalty as _early_shelter_pawn_push_penalty,
    coordinated_minor_piece_setup as _coordinated_minor_piece_setup,
    early_flank_queen_sortie_penalty as _early_flank_queen_sortie_penalty,
    early_flank_raid_penalty as _early_flank_raid_penalty,
    early_queen_raid_penalty as _early_queen_raid_penalty,
    opening_central_control_bonus as _opening_central_control_bonus,
    opening_piece_coordination_bonus as _opening_piece_coordination_bonus,
    unforced_shelter_loosening_penalty as _unforced_shelter_loosening_penalty,
    undeveloped_minor_piece_count as _undeveloped_minor_piece_count,
)
from chess_game.chess.pieces.piece_movers import PieceMovers
from chess_game.chess.strategy_utils import (
    is_passed_pawn as _is_passed_pawn,
    iter_king_squares as _iter_king_squares,
    path_clear_between as _path_clear_between,
    scale_signed as _scale_signed,
)
from chess_game.chess.evaluation_tables import (
    BACKWARD_PAWN_PENALTY,
    BACK_RANK_TENSION_PENALTY,
    BAD_BISHOP_PAWN_PENALTY,
    BISHOP_TABLE,
    BISHOP_PAIR_BONUS,
    BLOCKED_CENTRAL_PAWN_PENALTY,
    CANDIDATE_PASSED_PAWN_BONUS,
    CASTLED_KING_BONUS,
    CENTER_FILES,
    CENTRAL_DUO_BONUS,
    CENTRAL_MINOR_PIECE_BONUS,
    CENTRAL_SQUARES,
    CONNECTED_PASSED_PAWN_BONUS,
    CONNECTED_ROOKS_BONUS,
    CENTRAL_KING_WITH_QUEENS_PENALTY,
    CRAMPED_PIECE_PENALTY,
    DEFENDER_DISTANCE_PENALTY,
    DOUBLED_PAWN_PENALTY,
    EARLY_QUEEN_MOVE_PENALTY,
    EARLY_ROOK_MOVE_PENALTY,
    EXPOSED_CENTRAL_KING_PENALTY,
    HEAVY_FILE_PRESSURE_PENALTY,
    EXTENDED_CENTER_FILES,
    ISOLATED_PAWN_PENALTY,
    KING_TABLE,
    KING_ZONE_ATTACK_PENALTY,
    KNIGHT_OUTPOST_BONUS,
    KNIGHT_RIM_PENALTY,
    KNIGHT_TABLE,
    LONG_DIAGONAL_BISHOP_BONUS,
    MATERIAL_VALUES,
    MINOR_COORDINATION_BONUS,
    MOBILITY_WEIGHTS,
    OPEN_KING_FILE_PENALTY,
    PASSED_PAWN_BONUS_BY_PROGRESS,
    PAWN_ISLAND_PENALTY,
    PAWN_MAJORITY_ENDGAME_BONUS,
    PAWN_SHIELD_BONUS,
    PAWN_TABLE,
    QUEEN_ROOK_BATTERY_BONUS,
    QUEEN_TABLE,
    ROOK_OPEN_FILE_BONUS,
    ROOK_SEMI_OPEN_FILE_BONUS,
    ROOK_SEVENTH_RANK_BONUS,
    ROOK_TABLE,
    ROOK_TRAPPED_PENALTY,
    SPACE_ADVANTAGE_BONUS,
    STARTING_NON_PAWN_MATERIAL,
    UNDEVELOPED_MINOR_PIECE_PENALTY,
    WEAK_CHAIN_PAWN_PENALTY,
)
from chess_game.chess.types import Color, Piece, PieceType

EvaluationBreakdown = dict[str, int]


def evaluate(board: Board) -> int:
    """Evaluate the board position from White's perspective."""

    return get_evaluation_breakdown(board)["total"]


def get_evaluation_breakdown(board: Board) -> EvaluationBreakdown:
    """Return a debug-friendly breakdown of evaluation components."""

    middlegame_phase = _middlegame_phase(board)
    endgame_phase = 100 - middlegame_phase
    material_score, piece_square_score = _evaluate_material_and_piece_square(board)
    breakdown: EvaluationBreakdown = {
        "material": material_score,
        "piece_square": piece_square_score,
        "mobility": _evaluate_mobility(board),
        "pawn_structure": _evaluate_pawn_structure(board, endgame_phase),
        "king_safety": _evaluate_king_safety(board, middlegame_phase),
        "king_exposure": _evaluate_king_exposure(board, middlegame_phase),
        "defender_coordination": _evaluate_defender_coordination(board, middlegame_phase),
        "rook_activity": _evaluate_rook_activity(board),
        "bishop_pair": _evaluate_bishop_pair(board),
        "minor_piece_activity": _evaluate_minor_piece_activity(board),
        "space": _evaluate_space(board, middlegame_phase),
        "endgame_technique": _evaluate_endgame_technique(board, endgame_phase),
        "conversion": _evaluate_conversion(board, endgame_phase),
        "progress": _evaluate_progress(board, endgame_phase),
        "development": _evaluate_development(board, middlegame_phase),
    }
    breakdown["total"] = sum(breakdown.values())
    return breakdown


def _evaluate_material_and_piece_square(board: Board) -> tuple[int, int]:
    material_score = 0
    piece_square_score = 0
    for piece, row, col in _iter_board_pieces(board):
        sign = _color_sign(piece.color)
        material_score += sign * MATERIAL_VALUES[piece.kind]
        piece_square_score += sign * _piece_square_value(piece, row, col)
    return material_score, piece_square_score


def _iter_board_pieces(board: Board):
    for row_index, row in enumerate(board.board):
        for col_index, piece in enumerate(row):
            if piece is not None:
                yield piece, row_index, col_index


def _iter_color_pieces(board: Board, color: Color):
    for piece, row, col in _iter_board_pieces(board):
        if piece.color == color:
            yield piece, row, col


def _collect_piece_positions(
    board: Board,
    color: Color,
    kind: PieceType | None = None,
) -> list[tuple[int, int]]:
    positions: list[tuple[int, int]] = []
    for piece, row, col in _iter_color_pieces(board, color):
        if kind is None or piece.kind == kind:
            positions.append((row, col))
    return positions


def _color_sign(color: Color) -> int:
    return 1 if color == Color.WHITE else -1


def _mirror_row_for_color(color: Color, row: int) -> int:
    return row if color == Color.WHITE else 7 - row


def _piece_square_value(piece: Piece, row: int, col: int) -> int:
    mirrored_row = _mirror_row_for_color(piece.color, row)
    if piece.kind == PieceType.PAWN:
        return PAWN_TABLE[mirrored_row][col]
    if piece.kind == PieceType.KNIGHT:
        return KNIGHT_TABLE[mirrored_row][col]
    if piece.kind == PieceType.BISHOP:
        return BISHOP_TABLE[mirrored_row][col]
    if piece.kind == PieceType.ROOK:
        return ROOK_TABLE[mirrored_row][col]
    if piece.kind == PieceType.QUEEN:
        return QUEEN_TABLE[mirrored_row][col]
    return KING_TABLE[mirrored_row][col]


def _evaluate_mobility(board: Board) -> int:
    mobility_score = 0
    for piece, _, _ in _iter_board_pieces(board):
        weight = MOBILITY_WEIGHTS.get(piece.kind)
        if weight is None:
            continue
        move_count = len(PieceMovers.get_valid_moves(piece, board))
        mobility_score += _color_sign(piece.color) * move_count * weight
    return mobility_score


def _evaluate_pawn_structure(board: Board, endgame_phase: int) -> int:
    pawn_positions = _collect_pawn_positions(board)
    pawn_structure_score = 0
    for color in (Color.WHITE, Color.BLACK):
        sign = _color_sign(color)
        color_positions = pawn_positions[color]
        file_map = _group_rows_by_file(color_positions)
        enemy_positions = pawn_positions[_opponent(color)]
        passed_pawns: set[tuple[int, int]] = set()
        pawn_structure_score -= sign * _pawn_island_penalty(file_map)
        pawn_structure_score += sign * _central_duo_bonus(color_positions)
        pawn_structure_score += sign * _pawn_majority_bonus(
            color_positions,
            enemy_positions,
            endgame_phase,
        )
        for row, col in color_positions:
            pawn_structure_score -= sign * _pawn_file_penalty(file_map, col)
            pawn_position = (row, col)
            if _is_backward_pawn(
                board,
                color,
                pawn_position,
                file_map,
                enemy_positions,
            ):
                pawn_structure_score -= sign * BACKWARD_PAWN_PENALTY
            if _is_weak_pawn_chain(color, row, col, color_positions):
                pawn_structure_score -= sign * WEAK_CHAIN_PAWN_PENALTY
            if _is_blocked_central_pawn(board, color, row, col):
                pawn_structure_score -= sign * BLOCKED_CENTRAL_PAWN_PENALTY
            if _is_passed_pawn(color, row, col, enemy_positions):
                progress = _pawn_progress(color, row)
                pawn_structure_score += (
                    sign * PASSED_PAWN_BONUS_BY_PROGRESS[progress]
                )
                passed_pawns.add((row, col))
            elif _is_candidate_passed_pawn(color, row, col, enemy_positions):
                progress = _pawn_progress(color, row)
                pawn_structure_score += (
                    sign * (CANDIDATE_PASSED_PAWN_BONUS + progress * 2)
                )
        for row, col in passed_pawns:
            if _has_connected_passed_pawn(row, col, passed_pawns):
                pawn_structure_score += sign * CONNECTED_PASSED_PAWN_BONUS
    return pawn_structure_score


def _collect_pawn_positions(board: Board) -> dict[Color, list[tuple[int, int]]]:
    pawn_positions = {Color.WHITE: [], Color.BLACK: []}
    for piece, row, col in _iter_board_pieces(board):
        if piece.kind == PieceType.PAWN:
            pawn_positions[piece.color].append((row, col))
    return pawn_positions


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
    piece = board.get_piece(next_square)
    return piece is not None


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
        if any(
            (candidate_row, neighbor_col) in passed_pawns
            for candidate_row in valid_rows
        ):
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


def _pawn_progress(color: Color, row: int) -> int:
    return 6 - row if color == Color.WHITE else row - 1


def _pawn_direction(color: Color) -> int:
    return -1 if color == Color.WHITE else 1


def _evaluate_king_safety(board: Board, middlegame_phase: int) -> int:
    if middlegame_phase == 0:
        return 0
    king_safety_score = 0
    for color in (Color.WHITE, Color.BLACK):
        king_square = _find_king(board, color)
        if king_square is None:
            continue
        color_score = 0
        attack_pressure = _king_zone_attack_pressure(board, color, king_square)
        if _is_castled_king(color, king_square):
            color_score += CASTLED_KING_BONUS
        color_score += _pawn_shield_score(board, color, king_square)
        color_score -= _open_king_file_penalty(board, color, king_square)
        color_score -= _unforced_shelter_loosening_penalty(
            board,
            color,
            king_square,
            attack_pressure,
        )
        color_score -= attack_pressure
        color_score -= _back_rank_tension(board, color, king_square)
        if _is_exposed_central_king(king_square):
            color_score -= EXPOSED_CENTRAL_KING_PENALTY
        king_safety_score += _color_sign(color) * color_score
    return _scale_signed(king_safety_score, middlegame_phase)


def _evaluate_king_exposure(board: Board, middlegame_phase: int) -> int:
    if middlegame_phase == 0:
        return 0
    score = 0
    queens_on_board = _queens_on_board(board)
    for color in (Color.WHITE, Color.BLACK):
        king_square = _find_king(board, color)
        if king_square is None:
            continue
        color_score = 0
        if queens_on_board and _is_exposed_central_king(king_square):
            color_score -= CENTRAL_KING_WITH_QUEENS_PENALTY
        color_score -= _heavy_piece_lane_pressure(board, color, king_square)
        score += _color_sign(color) * color_score
    return _scale_signed(score, middlegame_phase)
def _evaluate_defender_coordination(board: Board, middlegame_phase: int) -> int:
    if middlegame_phase == 0 or not _queens_on_board(board):
        return 0
    score = 0
    for color, king_square in _iter_king_squares(board):
        score += _color_sign(color) * (-_heavy_defender_distance_penalty(board, color, king_square))
    return _scale_signed(score, middlegame_phase)
def _middlegame_phase(board: Board) -> int:
    non_pawn_material = 0
    for piece, _, _ in _iter_board_pieces(board):
        if piece.kind not in (PieceType.KING, PieceType.PAWN):
            non_pawn_material += MATERIAL_VALUES[piece.kind]
    return min((non_pawn_material * 100) // STARTING_NON_PAWN_MATERIAL, 100)


def _find_king(board: Board, color: Color) -> ConstantSquare | None:
    for piece, _, _ in _iter_board_pieces(board):
        if piece.color == color and piece.kind == PieceType.KING:
            return piece.square
    return None


def _is_castled_king(color: Color, square: ConstantSquare) -> bool:
    row = int(square.row)
    col = int(square.col)
    return (color == Color.WHITE and row == 7 and col in {2, 6}) or (
        color == Color.BLACK and row == 0 and col in {2, 6}
    )


def _pawn_shield_score(board: Board, color: Color, square: ConstantSquare) -> int:
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
            score += PAWN_SHIELD_BONUS
    return score


def _open_king_file_penalty(board: Board, color: Color, square: ConstantSquare) -> int:
    penalty = 0
    king_col = int(square.col)
    for file_index in range(max(0, king_col - 1), min(7, king_col + 1) + 1):
        if not _file_has_friendly_pawn(board, color, file_index):
            penalty += OPEN_KING_FILE_PENALTY
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
) -> int:
    enemy_color = _opponent(color)
    king_row = int(square.row)
    king_col = int(square.col)
    penalty = 0
    for piece, row, col in _iter_color_pieces(board, enemy_color):
        distance = max(abs(row - king_row), abs(col - king_col))
        if distance > 2:
            continue
        if piece.kind == PieceType.QUEEN:
            penalty += KING_ZONE_ATTACK_PENALTY * 3
        elif piece.kind == PieceType.ROOK:
            penalty += KING_ZONE_ATTACK_PENALTY * 2
        elif piece.kind in (PieceType.BISHOP, PieceType.KNIGHT):
            penalty += KING_ZONE_ATTACK_PENALTY
    return penalty


def _back_rank_tension(board: Board, color: Color, square: ConstantSquare) -> int:
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
    return BACK_RANK_TENSION_PENALTY


def _is_exposed_central_king(square: ConstantSquare) -> bool:
    return int(square.col) in CENTER_FILES


def _queens_on_board(board: Board) -> bool:
    return any(piece.kind == PieceType.QUEEN for piece, _, _ in _iter_board_pieces(board))
def _heavy_piece_lane_pressure(
    board: Board,
    color: Color,
    square: ConstantSquare,
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
                penalty += HEAVY_FILE_PRESSURE_PENALTY
    return penalty


def _heavy_defender_distance_penalty(
    board: Board,
    color: Color,
    king_square: ConstantSquare,
) -> int:
    king_row = int(king_square.row)
    king_col = int(king_square.col)
    penalty = 0
    for piece, row, col in _iter_color_pieces(board, color):
        if piece.kind not in (PieceType.QUEEN, PieceType.ROOK):
            continue
        distance = max(abs(row - king_row), abs(col - king_col))
        if distance >= 4:
            penalty += DEFENDER_DISTANCE_PENALTY
    return penalty


def _evaluate_rook_activity(board: Board) -> int:
    rook_activity_score = 0
    for piece, row, col in _iter_board_pieces(board):
        if piece.kind != PieceType.ROOK:
            continue
        color_score = 0
        file_state = _rook_file_state(board, piece.color, col)
        if file_state == "open":
            color_score += ROOK_OPEN_FILE_BONUS
        elif file_state == "semi-open":
            color_score += ROOK_SEMI_OPEN_FILE_BONUS
        if _rook_on_seventh_rank(piece.color, row):
            color_score += ROOK_SEVENTH_RANK_BONUS
        if _rook_is_trapped(board, piece.color, row, col):
            color_score -= ROOK_TRAPPED_PENALTY
        rook_activity_score += _color_sign(piece.color) * color_score
    for color in (Color.WHITE, Color.BLACK):
        rook_activity_score += _color_sign(color) * _connected_rooks_bonus(board, color)
        rook_activity_score += _color_sign(color) * _queen_rook_battery_bonus(board, color)
    return rook_activity_score


def _rook_file_state(board: Board, color: Color, file_index: int) -> str:
    has_friendly_pawn = False
    has_enemy_pawn = False
    enemy_color = _opponent(color)
    for rank_index in range(8):
        square = ConstantSquare(
            row=get_row_constant(rank_index),
            col=get_col_constant(file_index),
        )
        piece = board.get_piece(square)
        if piece is None or piece.kind != PieceType.PAWN:
            continue
        if piece.color == color:
            has_friendly_pawn = True
        elif piece.color == enemy_color:
            has_enemy_pawn = True
    if not has_friendly_pawn and not has_enemy_pawn:
        return "open"
    if not has_friendly_pawn:
        return "semi-open"
    return "closed"


def _rook_on_seventh_rank(color: Color, row: int) -> bool:
    return (color == Color.WHITE and row == 1) or (color == Color.BLACK and row == 6)


def _rook_is_trapped(board: Board, color: Color, row: int, col: int) -> bool:
    home_row = 7 if color == Color.WHITE else 0
    home_col = 0 if col < 4 else 7
    if row != home_row or col != home_col:
        return False
    piece = board.get_piece(
        ConstantSquare(row=get_row_constant(row), col=get_col_constant(col))
    )
    if piece is None:
        return False
    if len(PieceMovers.get_valid_moves(piece, board)) > 4:
        return False
    blocker_files = {col}
    if col == 0:
        blocker_files.add(1)
    else:
        blocker_files.add(6)
    pawn_row = 6 if color == Color.WHITE else 1
    for file_index in blocker_files:
        pawn_square = ConstantSquare(
            row=get_row_constant(pawn_row),
            col=get_col_constant(file_index),
        )
        pawn = board.get_piece(pawn_square)
        if pawn is not None and pawn.color == color and pawn.kind == PieceType.PAWN:
            return True
    return False


def _connected_rooks_bonus(board: Board, color: Color) -> int:
    rooks = _collect_piece_positions(board, color, PieceType.ROOK)
    if len(rooks) < 2:
        return 0
    row_a, col_a = rooks[0]
    row_b, col_b = rooks[1]
    if row_a != row_b and col_a != col_b:
        return 0
    if _path_clear_between(board, (row_a, col_a), (row_b, col_b)):
        return CONNECTED_ROOKS_BONUS
    return 0


def _queen_rook_battery_bonus(board: Board, color: Color) -> int:
    queens = _collect_piece_positions(board, color, PieceType.QUEEN)
    rooks = _collect_piece_positions(board, color, PieceType.ROOK)
    if len(queens) != 1 or not rooks:
        return 0
    queen_row, queen_col = queens[0]
    for rook_row, rook_col in rooks:
        if queen_row == rook_row or queen_col == rook_col:
            if _path_clear_between(board, (queen_row, queen_col), (rook_row, rook_col)):
                return QUEEN_ROOK_BATTERY_BONUS
    return 0


def _evaluate_bishop_pair(board: Board) -> int:
    bishop_counts = {Color.WHITE: 0, Color.BLACK: 0}
    for piece, _, _ in _iter_board_pieces(board):
        if piece.kind == PieceType.BISHOP:
            bishop_counts[piece.color] += 1
    return (
        (BISHOP_PAIR_BONUS if bishop_counts[Color.WHITE] >= 2 else 0)
        - (BISHOP_PAIR_BONUS if bishop_counts[Color.BLACK] >= 2 else 0)
    )


def _evaluate_minor_piece_activity(board: Board) -> int:
    pawn_positions = _collect_pawn_positions(board)
    score = 0
    for color in (Color.WHITE, Color.BLACK):
        sign = _color_sign(color)
        color_positions = pawn_positions[color]
        enemy_positions = pawn_positions[_opponent(color)]
        minor_squares: list[tuple[int, int]] = []
        for piece, row, col in _iter_color_pieces(board, color):
            if piece.kind == PieceType.KNIGHT:
                color_score = _knight_activity_score(
                    color,
                    row,
                    col,
                    color_positions,
                    enemy_positions,
                )
                score += sign * color_score
                minor_squares.append((row, col))
            if piece.kind == PieceType.BISHOP:
                color_score = _bishop_activity_score(board, piece, row, col, color_positions)
                score += sign * color_score
                minor_squares.append((row, col))
        if _coordinated_minor_piece_setup(minor_squares):
            score += sign * MINOR_COORDINATION_BONUS
    return score


def _knight_activity_score(
    color: Color,
    row: int,
    col: int,
    friendly_pawns: list[tuple[int, int]],
    enemy_pawns: list[tuple[int, int]],
) -> int:
    score = 0
    if col in {0, 7}:
        score -= KNIGHT_RIM_PENALTY
    if _occupies_central_square(row, col):
        score += CENTRAL_MINOR_PIECE_BONUS
    if _is_knight_outpost(color, row, col, friendly_pawns, enemy_pawns):
        score += KNIGHT_OUTPOST_BONUS
    return score


def _bishop_activity_score(
    board: Board,
    piece: Piece,
    row: int,
    col: int,
    friendly_pawns: list[tuple[int, int]],
) -> int:
    score = 0
    mobility = len(PieceMovers.get_valid_moves(piece, board))
    bishop_color = (row + col) % 2
    same_color_pawns = sum(
        1 for pawn_row, pawn_col in friendly_pawns if (pawn_row + pawn_col) % 2 == bishop_color
    )
    score -= same_color_pawns * BAD_BISHOP_PAWN_PENALTY
    if mobility >= 7 and _on_long_diagonal(row, col):
        score += LONG_DIAGONAL_BISHOP_BONUS
    if _occupies_central_square(row, col):
        score += CENTRAL_MINOR_PIECE_BONUS
    return score


def _on_long_diagonal(row: int, col: int) -> bool:
    return row == col or row + col == 7


def _occupies_central_square(row: int, col: int) -> bool:
    return (row, col) in CENTRAL_SQUARES


def _is_knight_outpost(
    color: Color,
    row: int,
    col: int,
    friendly_pawns: list[tuple[int, int]],
    enemy_pawns: list[tuple[int, int]],
) -> bool:
    advanced = row <= 3 if color == Color.WHITE else row >= 4
    if not advanced:
        return False
    supported = any(
        _pawn_attacks_square(color, pawn_row, pawn_col, row, col)
        for pawn_row, pawn_col in friendly_pawns
    )
    if not supported:
        return False
    return not any(abs(enemy_col - col) == 1 for _, enemy_col in enemy_pawns)


def _pawn_attacks_square(
    color: Color,
    pawn_row: int,
    pawn_col: int,
    target_row: int,
    target_col: int,
) -> bool:
    return (
        pawn_row + _pawn_direction(color) == target_row
        and abs(pawn_col - target_col) == 1
    )


def _evaluate_space(board: Board, middlegame_phase: int) -> int:
    if middlegame_phase == 0:
        return 0
    white_space = _space_score_for_color(board, Color.WHITE)
    black_space = _space_score_for_color(board, Color.BLACK)
    return _scale_signed(white_space - black_space, middlegame_phase)


def _space_score_for_color(board: Board, color: Color) -> int:
    score = 0
    for piece, row, col in _iter_color_pieces(board, color):
        if piece.kind == PieceType.PAWN and _supports_space(color, row, col):
            score += SPACE_ADVANTAGE_BONUS * 2
        elif piece.kind in (PieceType.KNIGHT, PieceType.BISHOP):
            if _piece_supports_space(color, row, col):
                score += SPACE_ADVANTAGE_BONUS
    for piece, row, col in _iter_color_pieces(board, color):
        if piece.kind in (PieceType.KNIGHT, PieceType.BISHOP, PieceType.ROOK):
            if _is_cramped_piece(color, row, col):
                score -= CRAMPED_PIECE_PENALTY
    return score


def _supports_space(color: Color, row: int, col: int) -> bool:
    if col not in EXTENDED_CENTER_FILES:
        return False
    return row <= 4 if color == Color.WHITE else row >= 3


def _piece_supports_space(color: Color, row: int, col: int) -> bool:
    if col not in EXTENDED_CENTER_FILES:
        return False
    return row <= 5 if color == Color.WHITE else row >= 2


def _is_cramped_piece(color: Color, row: int, col: int) -> bool:
    if color == Color.WHITE:
        return row == 7 and col not in CENTER_FILES
    return row == 0 and col not in CENTER_FILES


def _evaluate_development(board: Board, middlegame_phase: int) -> int:
    if middlegame_phase < 70:
        return 0
    development_score = 0
    for color in (Color.WHITE, Color.BLACK):
        sign = _color_sign(color)
        undeveloped = _undeveloped_minor_piece_count(board, color)
        development_score -= sign * undeveloped * UNDEVELOPED_MINOR_PIECE_PENALTY
        development_score += sign * _opening_central_control_bonus(board, color)
        development_score += sign * _opening_piece_coordination_bonus(
            board,
            color,
            undeveloped,
        )
        development_score -= sign * _early_shelter_pawn_push_penalty(
            board,
            color,
            undeveloped,
        )
        if undeveloped >= 2 and _queen_left_home_square(board, color):
            development_score -= sign * EARLY_QUEEN_MOVE_PENALTY
        development_score -= sign * _early_flank_queen_sortie_penalty(
            board,
            color,
            undeveloped,
        )
        development_score -= sign * _early_queen_raid_penalty(board, color, undeveloped)
        if undeveloped >= 2 and _rook_left_home_square_early(board, color):
            development_score -= sign * EARLY_ROOK_MOVE_PENALTY
        development_score -= sign * _early_flank_raid_penalty(board, color, undeveloped)
    return _scale_signed(development_score, middlegame_phase)


def _queen_left_home_square(board: Board, color: Color) -> bool:
    home_square = (7, 3) if color == Color.WHITE else (0, 3)
    return not _piece_on_square(board, color, PieceType.QUEEN, home_square)


def _rook_left_home_square_early(board: Board, color: Color) -> bool:
    home_squares = {(7, 0), (7, 7)} if color == Color.WHITE else {(0, 0), (0, 7)}
    rooks_on_home = sum(
        1
        for square in home_squares
        if _piece_on_square(board, color, PieceType.ROOK, square)
    )
    king_square = _find_king(board, color)
    return rooks_on_home < 2 and (
        king_square is None or not _is_castled_king(color, king_square)
    )


def _piece_on_square(
    board: Board,
    color: Color,
    kind: PieceType,
    square: tuple[int, int],
) -> bool:
    target_square = ConstantSquare(
        row=get_row_constant(square[0]),
        col=get_col_constant(square[1]),
    )
    piece = board.get_piece(target_square)
    return piece is not None and piece.color == color and piece.kind == kind


def _opponent(color: Color) -> Color:
    return Color.BLACK if color == Color.WHITE else Color.WHITE
