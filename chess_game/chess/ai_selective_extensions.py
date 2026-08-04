"""Selective single-ply search extensions for the AI.

Extracted from ``ai_search_helpers``. ``selective_extension_bonus`` (and the binary
``check_extension``) decide when a critical attack/defense move earns one extra
search ply, via a set of narrow ``_is_*_extension`` predicates. ``ai_search_helpers``
re-exports the public names so existing imports keep working.
"""

from __future__ import annotations

from chess_game.chess.ai_plan_guidance import (
    keeps_tactical_stability,
)
from chess_game.chess.ai_repetition_patterns import (
    move_undoes_last_own_move,
)
from chess_game.chess.ai_root_stability import (
    _is_simple_endgame,
)
from chess_game.chess.board import Board
from chess_game.chess.board.game_state import is_in_check
from chess_game.chess.defensive_containment_guidance import (
    heavy_piece_defense_extension_bonus,
)
from chess_game.chess.defensive_priorities import (
    DANGEROUS_KING_PRESSURE_THRESHOLD,
    king_danger_index,
    king_defense_profile,
    king_needs_shelter,
)
from chess_game.chess.endgame_emergency_defense import (
    endgame_emergency_extension_bonus,
)
from chess_game.chess.evaluation_tables import MATERIAL_VALUES
from chess_game.chess.low_material_race_guidance import endgame_race_extension_bonus
from chess_game.chess.middlegame_practicality_guidance import (
    middlegame_practicality_extension_bonus,
)
from chess_game.chess.move import Move
from chess_game.chess.opponent_plans import opponent_plan_profile
from chess_game.chess.passer_race_guidance import (
    passer_race_extension_bonus,
)
from chess_game.chess.strategy_utils import (
    is_capture_move,
    king_coordinates,
)
from chess_game.chess.types import Color, PieceType


def check_extension(child_board: Board, extension_budget: int) -> int:
    """Return 1 if the last move gave check to the opponent, 0 otherwise.

    Uses extension_budget to prevent cascading extensions — at most one
    check extension fires per search path.
    """
    if extension_budget <= 0:
        return 0
    return 1 if is_in_check(child_board, child_board.turn) else 0

def selective_extension_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    extension_budget: int,
    allow_strategic_extensions: bool = True,
) -> int:
    """Return a bounded one-ply extension for critical attack/defense moves.

    Extensions stay binary and narrow on purpose so king-danger signals do not
    double-count with static evaluation or root tie-break logic.
    """

    bonus = 0
    moving_piece = board.get_piece(move.start)
    if extension_budget <= 0 or moving_piece is None:
        return bonus
    moving_color = moving_piece.color
    enemy_color = Color.BLACK if moving_color == Color.WHITE else Color.WHITE
    current_danger = king_danger_index(board, moving_color)
    forced_extension = is_in_check(board, moving_color)
    forced_extension = forced_extension or (
        current_danger >= DANGEROUS_KING_PRESSURE_THRESHOLD
        and king_danger_index(child_board, moving_color) < current_danger
    )
    forced_extension = forced_extension or _is_danger_opening_capture(
        board,
        move,
        child_board,
        enemy_color,
    )
    forcing_attack = not king_needs_shelter(board, moving_color) and _is_forcing_attack_extension(
        board,
        move,
        child_board,
        moving_piece.kind,
        enemy_color,
    )
    if forcing_attack and move_undoes_last_own_move(board, move):
        forcing_attack = False
    strategic_extension = allow_strategic_extensions and (
        _is_central_prophylaxis_extension(
            board,
            move,
            child_board,
            moving_color,
        )
        or _is_king_file_shift_extension(
            board,
            move,
            child_board,
            moving_color,
        )
        or _is_king_shelter_recapture_extension(
            board,
            move,
            child_board,
            moving_color,
        )
        or _is_only_move_prophylaxis_extension(
            board,
            move,
            child_board,
            moving_color,
        )
        or _is_favorable_simplification_extension(
            board,
            move,
            child_board,
            moving_color,
        )
        or passer_race_extension_bonus(
            board,
            move,
            child_board,
            moving_color,
        )
        or endgame_race_extension_bonus(
            board,
            move,
            child_board,
            moving_color,
        )
        or middlegame_practicality_extension_bonus(
            board,
            move,
            child_board,
            moving_color,
        )
        or heavy_piece_defense_extension_bonus(
            board,
            move,
            child_board,
            moving_color,
        )
        or endgame_emergency_extension_bonus(
            board,
            move,
            child_board,
            moving_color,
        )
    )
    if strategic_extension and move_undoes_last_own_move(board, move):
        strategic_extension = False
    if forced_extension or forcing_attack or strategic_extension:
        bonus = 1
    return bonus

def _is_central_prophylaxis_extension(
    board: Board,
    move: Move,
    child_board: Board,
    moving_color: Color,
) -> bool:
    moving_piece = board.get_piece(move.start)
    if moving_piece is None or moving_piece.kind != PieceType.PAWN:
        return False
    if is_capture_move(board, move):
        return False
    if int(move.start.col) not in {2, 3, 4, 5} or int(move.end.col) not in {2, 3, 4, 5}:
        return False
    before_pressure = opponent_plan_profile(board, moving_color).pressure
    after_pressure = opponent_plan_profile(child_board, moving_color).pressure
    if before_pressure < 6 or before_pressure - after_pressure < 3:
        return False
    if not keeps_tactical_stability(board, child_board, moving_color):
        return False
    return _material_margin(child_board, moving_color) >= _material_margin(board, moving_color)

def _is_king_file_shift_extension(
    board: Board,
    move: Move,
    child_board: Board,
    moving_color: Color,
) -> bool:
    moving_piece = board.get_piece(move.start)
    if moving_piece is None or moving_piece.kind != PieceType.PAWN:
        return False
    king_position = king_coordinates(board, moving_color)
    if king_position is None:
        return False
    _, king_col = king_position
    if king_col not in {2, 6}:
        return False
    if abs(int(move.start.col) - king_col) > 1 or abs(int(move.end.col) - king_col) > 1:
        return False
    if not (king_needs_shelter(board, moving_color) or king_danger_index(board, moving_color) >= 2):
        return False
    return _significant_king_profile_change(board, child_board, moving_color)

def _is_king_shelter_recapture_extension(
    board: Board,
    move: Move,
    child_board: Board,
    moving_color: Color,
) -> bool:
    moving_piece = board.get_piece(move.start)
    is_valid_recapture = (
        moving_piece is not None
        and moving_piece.kind == PieceType.PAWN
        and is_capture_move(board, move)
    )
    if not is_valid_recapture:
        return False
    king_position = king_coordinates(board, moving_color)
    if king_position is None:
        return False
    king_row, king_col = king_position
    is_castled_king = king_col in {2, 6}
    is_local_recapture = (
        max(abs(int(move.start.row) - king_row), abs(int(move.start.col) - king_col)) <= 2
    )
    if not (is_castled_king and is_local_recapture):
        return False
    before = king_defense_profile(board, moving_color)
    after = king_defense_profile(child_board, moving_color)
    if max(before.danger, after.danger) < 2:
        return False
    return (
        before.danger != after.danger
        or before.invasion_lines != after.invasion_lines
        or before.back_rank_weak != after.back_rank_weak
    )

def _significant_king_profile_change(
    board: Board,
    child_board: Board,
    moving_color: Color,
) -> bool:
    before = king_defense_profile(board, moving_color)
    after = king_defense_profile(child_board, moving_color)
    return (
        before.danger != after.danger
        or before.invasion_lines != after.invasion_lines
        or before.back_rank_weak != after.back_rank_weak
    )

def _is_only_move_prophylaxis_extension(
    board: Board,
    move: Move,
    child_board: Board,
    moving_color: Color,
) -> bool:
    moving_piece = board.get_piece(move.start)
    king_position = king_coordinates(board, moving_color)
    if moving_piece is None or king_position is None:
        return False
    _, king_col = king_position
    is_candidate = moving_piece.kind == PieceType.PAWN and king_col in {2, 6}
    is_candidate = is_candidate and abs(int(move.start.col) - king_col) <= 1
    is_candidate = is_candidate and abs(int(move.end.col) - king_col) <= 1
    is_candidate = is_candidate and _is_back_rank_stabilizer(board, move, child_board, moving_color)
    if not is_candidate:
        return False
    stabilizer_count = 0
    for start, end, promotion in board.get_legal_moves():
        candidate = Move(start=start, end=end, promotion=promotion)
        candidate_board = board.clone()
        if not candidate_board.apply_legal_move(start, end, promotion=promotion):
            continue
        if _is_back_rank_stabilizer(board, candidate, candidate_board, moving_color):
            stabilizer_count += 1
            if stabilizer_count > 1:
                return False
    return stabilizer_count == 1

def _is_back_rank_stabilizer(
    board: Board,
    move: Move,
    child_board: Board,
    moving_color: Color,
) -> bool:
    if is_capture_move(board, move):
        return False
    before = king_defense_profile(board, moving_color)
    after = king_defense_profile(child_board, moving_color)
    if before.danger < DANGEROUS_KING_PRESSURE_THRESHOLD - 1:
        return False
    if not before.back_rank_weak or after.back_rank_weak:
        return False
    return after.safe_king_moves > before.safe_king_moves or after.danger < before.danger

def _is_favorable_simplification_extension(
    board: Board,
    move: Move,
    child_board: Board,
    moving_color: Color,
) -> bool:
    captured_piece = board.get_piece(move.end)
    if captured_piece is None or captured_piece.kind == PieceType.PAWN:
        return False
    if not is_capture_move(board, move) or not _is_simple_endgame(child_board):
        return False
    before_margin = _material_margin(board, moving_color)
    after_margin = _material_margin(child_board, moving_color)
    return after_margin >= 300 and after_margin >= before_margin

def _material_margin(board: Board, color: Color) -> int:
    own_total = 0
    enemy_total = 0
    enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
    for row in board.board:
        for piece in row:
            if piece is None or piece.kind == PieceType.KING:
                continue
            if piece.color == color:
                own_total += MATERIAL_VALUES[piece.kind]
            elif piece.color == enemy_color:
                enemy_total += MATERIAL_VALUES[piece.kind]
    return own_total - enemy_total

def _is_forcing_attack_extension(
    board: Board,
    move: Move,
    child_board: Board,
    moving_kind: PieceType,
    enemy_color: Color,
) -> bool:
    """Return True for forcing attacking moves worth one extra search ply."""

    enemy_danger_before = king_danger_index(board, enemy_color)
    enemy_danger_after = king_danger_index(child_board, enemy_color)
    gives_check = is_in_check(child_board, enemy_color)
    if (
        not gives_check
        or enemy_danger_after < DANGEROUS_KING_PRESSURE_THRESHOLD
        or not _is_heavy_piece_invasion(move, moving_kind, enemy_color)
    ):
        return False
    return enemy_danger_after > enemy_danger_before

def _is_danger_opening_capture(
    board: Board,
    move: Move,
    child_board: Board,
    enemy_color: Color,
) -> bool:
    """Return True for captures that clearly increase pressure on the enemy king."""

    if not is_capture_move(board, move):
        return False
    before = king_defense_profile(board, enemy_color)
    after = king_defense_profile(child_board, enemy_color)
    if after.danger < DANGEROUS_KING_PRESSURE_THRESHOLD:
        return False
    return after.danger > before.danger or after.invasion_lines > before.invasion_lines

def _is_heavy_piece_invasion(
    move: Move,
    moving_kind: PieceType,
    enemy_color: Color,
) -> bool:
    """Return True when a rook or queen reaches the enemy back-rank zone."""
    if moving_kind not in {PieceType.ROOK, PieceType.QUEEN}:
        return False
    enemy_back_rank_zone = {0, 1} if enemy_color == Color.BLACK else {6, 7}
    return int(move.end.row) in enemy_back_rank_zone
