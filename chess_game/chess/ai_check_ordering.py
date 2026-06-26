"""Check-quality scoring for quiet move ordering.

Extracted from ``ai_move_ordering``. Decides whether a quiet checking move is worth
prioritising (mating-net / material / king-driving value vs. empty or self-exposing
checks), with the supporting check-detection and attack/material query helpers. This
is the transitive closure of the check-quality subsystem, so it never calls back into
``ai_move_ordering``; ``ai_move_ordering`` re-imports the few names it still uses.
"""

from __future__ import annotations

from dataclasses import dataclass

from chess_game.chess.board.attack_utils import piece_attacks_square
from chess_game.chess.board import Board
from chess_game.chess.board.game_state import is_checkmate, is_in_check
from chess_game.chess.defensive_priorities import (
    DANGEROUS_KING_PRESSURE_THRESHOLD,
    king_defense_profile,
)
from chess_game.chess.move import Move
from chess_game.chess.strategy_utils import (
    king_coordinates,
    path_clear_between,
)
from chess_game.chess.types import Color, PieceType

from chess_game.chess.ai_quiet_ordering_constants import (
    QUIET_CHECK_BREAK_DEFENDER_BONUS,
    QUIET_CHECK_DRIVING_BONUS,
    QUIET_CHECK_MATE_NET_BONUS,
    QUIET_CHECK_MATERIAL_BONUS,
    QUIET_CHECK_SHRINK_BOX_BONUS,
    QUIET_CHECK_SIMPLIFY_BONUS,
    QUIET_EASY_SHUFFLE_CHECK_PENALTY,
    QUIET_EMPTY_CHECK_PENALTY,
    QUIET_SELF_EXPOSING_CHECK_PENALTY,
    QUIET_USEFUL_CHECK_BONUS,
)


@dataclass(frozen=True)
class CheckQuality:
    """Classify checks so only forcing ones receive strong quiet-order bonuses."""

    category: str
    enemy_safe_move_delta: int
    enemy_defender_delta: int
    enemy_connection_delta: int
    enemy_danger_delta: int
    self_danger_delta: int
    self_invasion_delta: int

def _offers_major_piece_trade(board: Board, move: Move) -> bool:
    if not _is_materially_ahead(board, board.turn):
        return False
    enemy_color = Color.BLACK if board.turn == Color.WHITE else Color.WHITE
    enemy_targets = {
        (row_index, col_index)
        for row_index, row in enumerate(board.board)
        for col_index, piece in enumerate(row)
        if (
            piece is not None
            and piece.color == enemy_color
            and piece.kind in (PieceType.ROOK, PieceType.QUEEN)
        )
    }
    if not enemy_targets:
        return False
    return _attacks_any_target(board, move, enemy_targets)

def _is_materially_ahead(board: Board, color: Color) -> bool:
    own_material = 0
    enemy_material = 0
    for row in board.board:
        for piece in row:
            if piece is None or piece.kind == PieceType.KING:
                continue
            value = _piece_value(piece.kind)
            if piece.color == color:
                own_material += value
            else:
                enemy_material += value
    return own_material > enemy_material

def _attacks_any_target(
    board: Board,
    move: Move,
    enemy_targets: set[tuple[int, int]],
) -> bool:
    start_row = int(move.start.row)
    start_col = int(move.start.col)
    end_row = int(move.end.row)
    end_col = int(move.end.col)
    piece = board.board[start_row][start_col]
    if piece is None:
        return False
    for target_row, target_col in enemy_targets:
        row_delta = target_row - end_row
        col_delta = target_col - end_col
        if piece.kind == PieceType.ROOK and _rook_attacks_delta(row_delta, col_delta):
            if not path_clear_between(board, (end_row, end_col), (target_row, target_col)):
                continue
            return True
        if piece.kind == PieceType.QUEEN and _queen_attacks_delta(row_delta, col_delta):
            if not path_clear_between(board, (end_row, end_col), (target_row, target_col)):
                continue
            return True
    return False

def _rook_attacks_delta(row_delta: int, col_delta: int) -> bool:
    return row_delta == 0 or col_delta == 0

def _queen_attacks_delta(row_delta: int, col_delta: int) -> bool:
    return _rook_attacks_delta(row_delta, col_delta) or abs(row_delta) == abs(col_delta)

def _piece_value(kind: PieceType) -> int:
    if kind == PieceType.PAWN:
        return 100
    if kind == PieceType.KNIGHT:
        return 320
    if kind == PieceType.BISHOP:
        return 330
    if kind == PieceType.ROOK:
        return 500
    if kind == PieceType.QUEEN:
        return 900
    return 0

def _check_quality_bonus(board: Board, kind: PieceType, move: Move) -> int:
    quality = _check_quality(board, kind, move)
    if quality is None:
        return 0
    score = 0
    if quality.category == "mating-net":
        score += QUIET_USEFUL_CHECK_BONUS + QUIET_CHECK_MATE_NET_BONUS
    elif quality.category == "forcing-material":
        score += QUIET_USEFUL_CHECK_BONUS + QUIET_CHECK_MATERIAL_BONUS
    elif quality.category == "driving":
        score += QUIET_USEFUL_CHECK_BONUS + QUIET_CHECK_DRIVING_BONUS
    elif quality.category == "simplifying":
        score += QUIET_USEFUL_CHECK_BONUS + QUIET_CHECK_SIMPLIFY_BONUS
    else:
        score -= QUIET_EMPTY_CHECK_PENALTY
    score += quality.enemy_safe_move_delta * QUIET_CHECK_SHRINK_BOX_BONUS
    score += (quality.enemy_defender_delta + quality.enemy_connection_delta) * (
        QUIET_CHECK_BREAK_DEFENDER_BONUS
    )
    score += quality.enemy_danger_delta * (QUIET_CHECK_DRIVING_BONUS // 2)
    if quality.category == "empty" and quality.enemy_safe_move_delta == 0:
        score -= QUIET_EASY_SHUFFLE_CHECK_PENALTY
    score -= quality.self_danger_delta * QUIET_SELF_EXPOSING_CHECK_PENALTY
    score -= quality.self_invasion_delta * (QUIET_SELF_EXPOSING_CHECK_PENALTY // 2)
    return score

def _check_quality(board: Board, kind: PieceType, move: Move) -> CheckQuality | None:
    """Classify checks as mating-net, forcing, driving, simplifying, or empty."""

    enemy_color = Color.BLACK if board.turn == Color.WHITE else Color.WHITE
    enemy_king_coords = king_coordinates(board, enemy_color)
    if enemy_king_coords is None or not _move_gives_check(board, kind, move, enemy_king_coords):
        return None
    child_board = board.clone()
    if not child_board.apply_legal_move(move.start, move.end, promotion=move.promotion):
        return None
    if not is_in_check(child_board, enemy_color):
        return None
    before_enemy = king_defense_profile(board, enemy_color)
    after_enemy = king_defense_profile(child_board, enemy_color)
    before_self = king_defense_profile(board, board.turn)
    after_self = king_defense_profile(child_board, board.turn)
    quality = CheckQuality(
        category=_check_category(board, kind, move, child_board, after_enemy),
        enemy_safe_move_delta=max(0, before_enemy.safe_king_moves - after_enemy.safe_king_moves),
        enemy_defender_delta=max(
            0,
            before_enemy.king_zone_defenders - after_enemy.king_zone_defenders,
        ),
        enemy_connection_delta=max(
            0,
            before_enemy.heavy_connections - after_enemy.heavy_connections,
        ),
        enemy_danger_delta=max(0, after_enemy.danger - before_enemy.danger),
        self_danger_delta=max(0, after_self.danger - before_self.danger),
        self_invasion_delta=max(0, after_self.invasion_lines - before_self.invasion_lines),
    )
    return quality

def _check_category(
    board: Board,
    kind: PieceType,
    move: Move,
    child_board: Board,
    enemy_profile,
) -> str:
    enemy_color = Color.BLACK if board.turn == Color.WHITE else Color.WHITE
    if is_checkmate(child_board, enemy_color):
        return "mating-net"
    if _move_creates_material_threat(child_board, move, enemy_color):
        return "forcing-material"
    if _offers_major_piece_trade(board, move):
        return "simplifying"
    if (
        enemy_profile.danger >= DANGEROUS_KING_PRESSURE_THRESHOLD
        and kind in {PieceType.QUEEN, PieceType.ROOK, PieceType.BISHOP}
    ):
        return "driving"
    return "empty"

def _move_creates_material_threat(
    child_board: Board,
    move: Move,
    enemy_color: Color,
) -> bool:
    moved_piece = child_board.get_piece(move.end)
    if moved_piece is None:
        return False
    for row in child_board.board:
        for piece in row:
            if (
                piece is None
                or piece.color != enemy_color
                or piece.kind in {PieceType.KING, PieceType.PAWN}
                or piece.square is None
            ):
                continue
            if piece_attacks_square(moved_piece, move.end, piece.square, child_board):
                return True
    return False

def _move_gives_check(
    board: Board,
    kind: PieceType,
    move: Move,
    enemy_king: tuple[int, int],
) -> bool:
    end_row = int(move.end.row)
    end_col = int(move.end.col)
    row_delta = enemy_king[0] - end_row
    col_delta = enemy_king[1] - end_col
    delta = (row_delta, col_delta)
    gives_check = False
    if kind == PieceType.QUEEN:
        gives_check = _slider_gives_check(board, move, enemy_king, delta, queen=True)
    elif kind == PieceType.ROOK:
        gives_check = _slider_gives_check(board, move, enemy_king, delta, queen=False)
    elif kind == PieceType.BISHOP:
        gives_check = abs(row_delta) == abs(col_delta) and _path_clear_after_move(
            board, move, enemy_king
        )
    elif kind == PieceType.KNIGHT:
        gives_check = sorted((abs(row_delta), abs(col_delta))) == [1, 2]
    elif kind == PieceType.PAWN:
        direction = -1 if board.turn == Color.WHITE else 1
        gives_check = row_delta == direction and abs(col_delta) == 1
    elif kind == PieceType.KING:
        gives_check = max(abs(row_delta), abs(col_delta)) == 1
    return gives_check

def _slider_gives_check(
    board: Board,
    move: Move,
    enemy_king: tuple[int, int],
    delta: tuple[int, int],
    queen: bool,
) -> bool:
    row_delta, col_delta = delta
    if row_delta == 0 or col_delta == 0:
        return _path_clear_after_move(board, move, enemy_king)
    if queen and abs(row_delta) == abs(col_delta):
        return _path_clear_after_move(board, move, enemy_king)
    return False

def _path_clear_after_move(
    board: Board,
    move: Move,
    enemy_king: tuple[int, int],
) -> bool:
    start = (int(move.start.row), int(move.start.col))
    end = (int(move.end.row), int(move.end.col))
    row_step = 0 if end[0] == enemy_king[0] else (1 if enemy_king[0] > end[0] else -1)
    col_step = 0 if end[1] == enemy_king[1] else (1 if enemy_king[1] > end[1] else -1)
    current_row = end[0] + row_step
    current_col = end[1] + col_step
    while (current_row, current_col) != enemy_king:
        if (
            (current_row, current_col) != start
            and board.board[current_row][current_col] is not None
        ):
            return False
        current_row += row_step
        current_col += col_step
    return True
