"""Helper layer for passed-pawn race guidance.

Extracted from ``passer_race_guidance``: the tuning constants and the per-aspect
race-scoring / passer-classification helpers below the public entry points
(passer_race_evaluation_score / _order_bonus / _root_bonus / _extension_bonus,
is_pawn_race_tempo_position, explicit_pawn_race_tempo), which stay in
``passer_race_guidance`` and import from here. Cycle-free.
"""

from __future__ import annotations

from chess_game.chess.board import Board
from chess_game.chess.board.attack_utils import piece_attacks_square
from chess_game.chess.board.game_state import is_in_check
from chess_game.chess.constants import get_square_constant
from chess_game.chess.move import Move
from chess_game.chess.strategy_utils import (
    heavy_piece_file_support_rows,
    iter_color_pieces,
    king_coordinates,
    legal_move_count,
    materially_behind_color,
    non_king_piece_kinds,
    opposite_color,
    passed_pawns_for_color,
    pawn_path_to_promotion_is_clear,
    pawn_supports_square,
)
from chess_game.chess.types import Color, PieceType

_MAX_NON_KING_PIECES = 10
_EVAL_SCALE = 2
_ORDER_SCALE = 4
_ROOT_SCALE = 5
_PASSER_PROGRESS_BONUS = 20
_PROTECTED_PASSER_BONUS = 12
_CONNECTED_PASSER_BONUS = 14
_OUTSIDE_PASSER_BONUS = 12
_CLEAR_PATH_BONUS = 12
_KING_SUPPORT_BONUS = 8
_CRITICAL_ZONE_BONUS = 12
_HEAVY_SUPPORT_BONUS = 10
_ENEMY_PASSER_DANGER_BONUS = 28
_PROMOTION_SQUARE_PENALTY = 18
_BLOCKADE_PENALTY = 12
_DIRECT_PUSH_BONUS = 12
_HIGH_PRIORITY_PUSH_BONUS = 72
_ESCORT_BONUS = 16
_COSMETIC_CHECK_PENALTY = 96
_RACE_TEMPO_BONUS = 12
_UNSTOPPABLE_PASSER_BONUS = 28
_TIED_DOWN_DEFENDER_BONUS = 12
_ACTIVE_ENEMY_HEAVY_PENALTY = 48
_PROMOTION_RESOLUTION_BONUS = 120
_CHECK_DISRUPTION_PENALTY = 96
_EXPLICIT_TEMPO_MARGIN_BONUS = 10
_LOSING_SIDE_IRRELEVANT_ACTIVITY_PENALTY = 88
_LOSING_SIDE_BAD_RACE_PENALTY = 180
_CHECKMATE_RESOLUTION_BONUS = 240
_STALEMATE_RESOLUTION_PENALTY = 4000
_ALLOWED_RACE_KINDS = {PieceType.QUEEN, PieceType.ROOK, PieceType.PAWN}


def _passer_race_side_score(board: Board, color: Color) -> int:
    own_passers = passed_pawns_for_color(board, color)
    enemy_passers = passed_pawns_for_color(board, _opponent(color))
    score = sum(
        _own_passer_score(board, color, pawn, own_passers)
        for pawn in own_passers
        if _is_high_priority_passer(board, color, pawn, own_passers)
    )
    score -= sum(
        _enemy_passer_danger_score(board, color, pawn)
        for pawn in enemy_passers
        if _is_high_priority_passer(board, _opponent(color), pawn, enemy_passers)
    )
    return score

def _relative_race_score(board: Board, color: Color) -> int:
    return _passer_race_side_score(board, color) - _passer_race_side_score(
        board,
        _opponent(color),
    )

def _own_passer_score(
    board: Board,
    color: Color,
    pawn: tuple[int, int],
    own_passers: list[tuple[int, int]],
) -> int:
    row, col = pawn
    score = _promotion_progress(color, row) * _PASSER_PROGRESS_BONUS
    if _is_protected_passer(board, color, pawn):
        score += _PROTECTED_PASSER_BONUS
    if _is_connected_passer(pawn, own_passers):
        score += _CONNECTED_PASSER_BONUS
    if _is_outside_passer(col):
        score += _OUTSIDE_PASSER_BONUS
    if pawn_path_to_promotion_is_clear(board, color, pawn):
        score += _CLEAR_PATH_BONUS
    score += _king_support_score(board, color, pawn)
    score += _heavy_piece_support_score(board, color, pawn)
    score += _race_tempo_score(board, color, pawn)
    score += _unstoppable_passer_score(board, color, pawn)
    score += _defender_tied_down_score(board, color, pawn)
    score -= _enemy_heavy_counterplay_penalty(board, color, pawn)
    score -= _check_disruption_penalty(board, color, pawn)
    return score

def _enemy_passer_danger_score(
    board: Board,
    color: Color,
    enemy_pawn: tuple[int, int],
) -> int:
    enemy_color = _opponent(color)
    row, _ = enemy_pawn
    score = _promotion_progress(enemy_color, row) * _ENEMY_PASSER_DANGER_BONUS
    if pawn_path_to_promotion_is_clear(board, enemy_color, enemy_pawn):
        score += _CLEAR_PATH_BONUS
    if not _controls_promotion_square(board, color, enemy_pawn):
        score += _PROMOTION_SQUARE_PENALTY
    if not _blocks_enemy_pawn(board, color, enemy_pawn):
        score += _BLOCKADE_PENALTY
    return score

def _king_support_score(board: Board, color: Color, pawn: tuple[int, int]) -> int:
    own_king = king_coordinates(board, color)
    enemy_king = king_coordinates(board, _opponent(color))
    if own_king is None or enemy_king is None:
        return 0
    promotion_square = _promotion_square(color, pawn[1])
    score = max(0, _king_distance(enemy_king, pawn) - _king_distance(own_king, pawn))
    score *= _KING_SUPPORT_BONUS
    critical_gain = max(
        0,
        _king_distance(enemy_king, promotion_square)
        - _king_distance(own_king, promotion_square),
    )
    score += critical_gain * _CRITICAL_ZONE_BONUS
    return score

def _heavy_piece_support_score(
    board: Board,
    color: Color,
    pawn: tuple[int, int],
) -> int:
    score = 0
    pawn_row, _ = pawn
    for row in heavy_piece_file_support_rows(board, color, pawn):
        if color == Color.WHITE and row > pawn_row:
            score += _HEAVY_SUPPORT_BONUS
        if color == Color.BLACK and row < pawn_row:
            score += _HEAVY_SUPPORT_BONUS
    return score

def _is_protected_passer(board: Board, color: Color, pawn: tuple[int, int]) -> bool:
    row, col = pawn
    return pawn_supports_square(board, color, row, col)

def _is_connected_passer(
    pawn: tuple[int, int],
    own_passers: list[tuple[int, int]],
) -> bool:
    row, col = pawn
    return any(
        other_col != col and abs(other_col - col) == 1 and abs(other_row - row) <= 1
        for other_row, other_col in own_passers
    )

def _controls_promotion_square(
    board: Board,
    color: Color,
    enemy_pawn: tuple[int, int],
) -> bool:
    promotion_square = _square_tuple_to_constant(
        *_promotion_square(_opponent(color), enemy_pawn[1])
    )
    occupant = board.get_piece(promotion_square)
    if occupant is not None and occupant.color == color:
        return True
    return any(
        piece_attacks_square(piece, piece.square, promotion_square, board)
        for piece, _, _ in iter_color_pieces(board, color)
    )

def _blocks_enemy_pawn(
    board: Board,
    color: Color,
    enemy_pawn: tuple[int, int],
) -> bool:
    block_row, block_col = _block_square(_opponent(color), enemy_pawn)
    if not 0 <= block_row < 8:
        return False
    occupant = board.board[block_row][block_col]
    return occupant is not None and occupant.color == color

def _has_relevant_race_targets(board: Board, color: Color) -> bool:
    own_passers = passed_pawns_for_color(board, color)
    enemy_passers = passed_pawns_for_color(board, _opponent(color))
    return any(
        _is_high_priority_passer(board, color, pawn, own_passers)
        for pawn in own_passers
    ) or any(
        _is_high_priority_passer(board, _opponent(color), pawn, enemy_passers)
        for pawn in enemy_passers
    )

def _losing_side_urgent_defense_penalty(
    board: Board,
    child_board: Board,
    color: Color,
    move: Move,
) -> int:
    if materially_behind_color(board) != color:
        return 0
    enemy_color = _opponent(color)
    enemy_passers = passed_pawns_for_color(board, enemy_color)
    if not enemy_passers:
        return 0
    dangerous = max(enemy_passers, key=lambda pawn: _promotion_progress(enemy_color, pawn[0]))
    if _promotion_progress(enemy_color, dangerous[0]) < 6:
        return 0
    start_distance = abs(int(move.start.col) - dangerous[1])
    end_distance = abs(int(move.end.col) - dangerous[1])
    if end_distance <= start_distance:
        return 0
    if _passer_race_side_score(child_board, color) > _passer_race_side_score(board, color):
        return 0
    return _LOSING_SIDE_IRRELEVANT_ACTIVITY_PENALTY

def _losing_side_bad_race_penalty(
    board: Board,
    color: Color,
    piece_kind: PieceType,
    move: Move,
) -> int:
    if materially_behind_color(board) != color or piece_kind != PieceType.PAWN:
        return 0
    enemy_color = _opponent(color)
    enemy_passers = passed_pawns_for_color(board, enemy_color)
    if enemy_passers:
        dangerous = max(enemy_passers, key=lambda pawn: _promotion_progress(enemy_color, pawn[0]))
        if (
            _promotion_progress(enemy_color, dangerous[0]) >= 6
            and abs(int(move.end.col) - dangerous[1]) >= 2
        ):
            return _LOSING_SIDE_BAD_RACE_PENALTY
    white_tempo, black_tempo = _explicit_pawn_race_tempo(board)
    if white_tempo is None or black_tempo is None:
        return 0
    own_tempo = white_tempo if color == Color.WHITE else black_tempo
    enemy_tempo = black_tempo if color == Color.WHITE else white_tempo
    if own_tempo <= enemy_tempo:
        return 0
    return _LOSING_SIDE_BAD_RACE_PENALTY

def _is_near_promotion_passer_push(board: Board, move: Move, color: Color) -> bool:
    piece = board.get_piece(move.start)
    if piece is None or piece.kind != PieceType.PAWN:
        return False
    start = (int(move.start.row), int(move.start.col))
    if start not in passed_pawns_for_color(board, color):
        return False
    end_row = int(move.end.row)
    return end_row == (1 if color == Color.WHITE else 6)

def _move_directly_stops_enemy_near_promotion_pawn(
    board: Board,
    move: Move,
    child_board: Board,
    color: Color,
) -> bool:
    enemy_color = _opponent(color)
    for pawn in passed_pawns_for_color(board, enemy_color):
        row, _ = pawn
        if row not in {2, 5, 1, 6}:
            continue
        promotion_square = _promotion_square(enemy_color, pawn[1])
        block_square = _block_square(enemy_color, pawn)
        move_end = (int(move.end.row), int(move.end.col))
        if move_end not in {promotion_square, block_square}:
            continue
        if _controls_promotion_square(child_board, color, pawn):
            return True
        if _blocks_enemy_pawn(child_board, color, pawn):
            return True
    return False

def _is_relevant_passer_race(board: Board) -> bool:
    if not _passes_material_gate(board):
        return False
    return (
        _has_race_critical_passer(board, Color.WHITE)
        and _has_meaningful_enemy_counterplay(board, Color.WHITE)
    ) or (
        _has_race_critical_passer(board, Color.BLACK)
        and _has_meaningful_enemy_counterplay(board, Color.BLACK)
    )

def _is_relevant_passer_race_evaluation(board: Board) -> bool:
    return _is_relevant_passer_race(board) and (
        _has_immediate_race_pressure(board, Color.WHITE)
        or _has_immediate_race_pressure(board, Color.BLACK)
    )

def _passes_material_gate(board: Board) -> bool:
    non_king_kinds = non_king_piece_kinds(board)
    qualifying_piece_count = sum(
        1
        for kind in non_king_kinds
        if kind in _ALLOWED_RACE_KINDS
    )
    has_heavy_piece = any(
        kind in {PieceType.ROOK, PieceType.QUEEN}
        for kind in non_king_kinds
    )
    return has_heavy_piece and qualifying_piece_count <= _MAX_NON_KING_PIECES

def _high_priority_push_bonus(board: Board, color: Color, move: Move) -> int:
    end_square = (int(move.end.row), int(move.end.col))
    own_passers = passed_pawns_for_color(board, color)
    if end_square not in own_passers:
        return 0
    if not _is_high_priority_passer(board, color, end_square, own_passers):
        return 0
    return _HIGH_PRIORITY_PUSH_BONUS

def _is_high_priority_passer(
    board: Board,
    color: Color,
    pawn: tuple[int, int],
    own_passers: list[tuple[int, int]],
) -> bool:
    row, col = pawn
    return (
        _promotion_progress(color, row) >= 4
        or _is_outside_passer(col)
        or _is_protected_passer(board, color, pawn)
        or _is_connected_passer(pawn, own_passers)
    )

def _has_race_critical_passer(board: Board, color: Color) -> bool:
    own_passers = passed_pawns_for_color(board, color)
    return any(
        _is_high_priority_passer(board, color, pawn, own_passers)
        and _is_race_critical_progress(color, pawn[0])
        for pawn in own_passers
    )

def _has_meaningful_enemy_counterplay(board: Board, color: Color) -> bool:
    enemy_color = _opponent(color)
    return bool(passed_pawns_for_color(board, enemy_color)) or any(
        piece.kind in {PieceType.ROOK, PieceType.QUEEN}
        for piece, _, _ in iter_color_pieces(board, enemy_color)
    )

def _has_immediate_race_pressure(board: Board, color: Color) -> bool:
    own_passers = passed_pawns_for_color(board, color)
    enemy_has_passer = bool(passed_pawns_for_color(board, _opponent(color)))
    return any(
        _is_high_priority_passer(board, color, pawn, own_passers)
        and _is_race_critical_progress(color, pawn[0])
        and _is_immediate_race_passer(board, color, pawn, enemy_has_passer)
        for pawn in own_passers
    )

def _is_immediate_race_passer(
    board: Board,
    color: Color,
    pawn: tuple[int, int],
    enemy_has_passer: bool,
) -> bool:
    if enemy_has_passer:
        return True
    if _promotion_pushes_remaining(color, pawn[0]) <= 1:
        return True
    if _defender_tied_down_score(board, color, pawn) > 0:
        return True
    own_king = king_coordinates(board, color)
    return own_king is not None and _king_distance(own_king, pawn) <= 4

def _is_race_critical_progress(color: Color, row: int) -> bool:
    return _promotion_progress(color, row) >= 4

def _race_tempo_score(board: Board, color: Color, pawn: tuple[int, int]) -> int:
    own_tempo = _promotion_tempo_ply(board, color, pawn[0])
    enemy_fastest = _fastest_promotion_tempo(board, _opponent(color))
    if enemy_fastest is None:
        return _RACE_TEMPO_BONUS
    margin = max(-2, min(2, enemy_fastest - own_tempo))
    score = margin * _RACE_TEMPO_BONUS
    white_tempo, black_tempo = _explicit_pawn_race_tempo(board)
    own_explicit = white_tempo if color == Color.WHITE else black_tempo
    enemy_explicit = black_tempo if color == Color.WHITE else white_tempo
    if own_explicit is not None and enemy_explicit is not None:
        explicit_margin = max(-2, min(2, enemy_explicit - own_explicit))
        score += explicit_margin * _EXPLICIT_TEMPO_MARGIN_BONUS
    return score

def _unstoppable_passer_score(
    board: Board,
    color: Color,
    pawn: tuple[int, int],
) -> int:
    if not pawn_path_to_promotion_is_clear(board, color, pawn):
        return 0
    enemy_king = king_coordinates(board, _opponent(color))
    if enemy_king is None or _enemy_heavy_stops_pawn(board, color, pawn):
        return 0
    own_tempo = _promotion_pushes_remaining(color, pawn[0])
    promotion_square = _promotion_square(color, pawn[1])
    block_square = _block_square(color, pawn)
    enemy_stop_tempo = min(
        _king_distance(enemy_king, promotion_square),
        _king_distance(enemy_king, block_square),
    )
    if own_tempo < enemy_stop_tempo:
        return _UNSTOPPABLE_PASSER_BONUS
    return 0

def _defender_tied_down_score(
    board: Board,
    color: Color,
    pawn: tuple[int, int],
) -> int:
    enemy_color = _opponent(color)
    block_row, block_col = _block_square(color, pawn)
    promotion_row, promotion_col = _promotion_square(color, pawn[1])
    score = 0
    block_occupant = board.board[block_row][block_col] if 0 <= block_row < 8 else None
    promotion_occupant = board.board[promotion_row][promotion_col]
    if block_occupant is not None and block_occupant.color == enemy_color:
        score += _TIED_DOWN_DEFENDER_BONUS
    if promotion_occupant is not None and promotion_occupant.color == enemy_color:
        score += _TIED_DOWN_DEFENDER_BONUS
    return score

def _enemy_heavy_stops_pawn(board: Board, color: Color, pawn: tuple[int, int]) -> bool:
    enemy_color = _opponent(color)
    promotion_square = _square_tuple_to_constant(*_promotion_square(color, pawn[1]))
    block_row, block_col = _block_square(color, pawn)
    block_square = (
        None
        if not 0 <= block_row < 8
        else _square_tuple_to_constant(block_row, block_col)
    )
    for piece, _, _ in iter_color_pieces(board, enemy_color):
        if piece.kind not in {PieceType.ROOK, PieceType.QUEEN}:
            continue
        if piece_attacks_square(piece, piece.square, promotion_square, board):
            return True
        if (
            block_square is not None
            and piece_attacks_square(piece, piece.square, block_square, board)
        ):
            return True
    return False

def _enemy_heavy_counterplay_penalty(
    board: Board,
    color: Color,
    pawn: tuple[int, int],
) -> int:
    enemy_heavy = [
        piece
        for piece, _, _ in iter_color_pieces(board, _opponent(color))
        if piece.kind in {PieceType.ROOK, PieceType.QUEEN}
    ]
    if not enemy_heavy or _promotion_pushes_remaining(color, pawn[0]) <= 1:
        return 0
    if _unstoppable_passer_score(board, color, pawn) > 0:
        return 0
    if _defender_tied_down_score(board, color, pawn) > 0:
        return 0
    return len(enemy_heavy) * _ACTIVE_ENEMY_HEAVY_PENALTY

def _check_disruption_penalty(
    board: Board,
    color: Color,
    pawn: tuple[int, int],
) -> int:
    if not is_in_check(board, color) or _promotion_pushes_remaining(color, pawn[0]) <= 1:
        return 0
    return _CHECK_DISRUPTION_PENALTY

def _fastest_promotion_tempo(board: Board, color: Color) -> int | None:
    own_passers = passed_pawns_for_color(board, color)
    tempos = [
        _promotion_tempo_ply(board, color, row)
        for row, col in own_passers
        if _is_high_priority_passer(board, color, (row, col), own_passers)
        and _is_race_critical_progress(color, row)
    ]
    return min(tempos, default=None)

def _explicit_pawn_race_tempo(board: Board) -> tuple[int | None, int | None]:
    return (
        _fastest_promotion_tempo_for_side(board, Color.WHITE),
        _fastest_promotion_tempo_for_side(board, Color.BLACK),
    )

def _fastest_promotion_tempo_for_side(board: Board, color: Color) -> int | None:
    passers = passed_pawns_for_color(board, color)
    tempos = [_promotion_tempo_ply(board, color, row) for row, _ in passers]
    return min(tempos, default=None)

def _promotion_tempo_ply(board: Board, color: Color, row: int) -> int:
    pushes = _promotion_pushes_remaining(color, row)
    if pushes <= 0:
        return 0
    return pushes * 2 - (1 if board.turn == color else 0)

def _is_pawn_race_tempo_position(board: Board) -> bool:
    if not passed_pawns_for_color(board, Color.WHITE):
        return False
    if not passed_pawns_for_color(board, Color.BLACK):
        return False
    non_king = [
        piece.kind
        for row in board.board
        for piece in row
        if piece is not None and piece.kind != PieceType.KING
    ]
    if not non_king or len(non_king) > 6:
        return False
    return all(kind == PieceType.PAWN for kind in non_king)

def _promotion_pushes_remaining(color: Color, row: int) -> int:
    return row if color == Color.WHITE else 7 - row

def _promotion_progress(color: Color, row: int) -> int:
    return 6 - row if color == Color.WHITE else row - 1

def _promotion_square(color: Color, col: int) -> tuple[int, int]:
    return (0, col) if color == Color.WHITE else (7, col)

def _block_square(color: Color, pawn: tuple[int, int]) -> tuple[int, int]:
    row, col = pawn
    return (row - 1, col) if color == Color.WHITE else (row + 1, col)

def _is_outside_passer(col: int) -> bool:
    return col in {0, 1, 6, 7}

def _square_tuple_to_constant(row: int, col: int):
    return get_square_constant(row, col)

def _king_distance(first: tuple[int, int], second: tuple[int, int]) -> int:
    return abs(first[0] - second[0]) + abs(first[1] - second[1])

def _move_checks_opponent(board: Board, color: Color) -> bool:
    return is_in_check(board, _opponent(color))

def _defender_escape_bonus(board: Board, color: Color) -> int:
    enemy_color = _opponent(color)
    enemy_moves = legal_move_count(board, enemy_color)
    if enemy_moves == 0:
        return (
            _CHECKMATE_RESOLUTION_BONUS
            if is_in_check(board, enemy_color)
            else -_STALEMATE_RESOLUTION_PENALTY
        )
    return 0

def _opponent(color: Color) -> Color:
    return opposite_color(color)
