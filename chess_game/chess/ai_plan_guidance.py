"""Plan-continuity helpers for root move scoring."""

from chess_game.chess.board import Board
from chess_game.chess.defensive_priorities import king_defense_profile
from chess_game.chess.move import Move
from chess_game.chess.opponent_plans import opponent_plan_profile
from chess_game.chess.structure_recognition import structure_plan_bonus
from chess_game.chess.types import Color, PieceType


def practical_options_bonus(board: Board, child_board: Board, moving_color: Color) -> int:
    """Reward moves that reduce the opponent's practical options."""

    before_pressure = opponent_plan_profile(board, moving_color).pressure
    after_pressure = opponent_plan_profile(child_board, moving_color).pressure
    score = max(0, before_pressure - after_pressure) * 6
    score -= max(0, after_pressure - before_pressure) * 5
    return score


def plan_continuity_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    moving_kind: PieceType,
    moving_color: Color,
) -> int:
    """Reward moves that keep an existing practical plan on track."""

    continuity = structure_plan_bonus(board, moving_color, moving_kind, move)
    if continuity == 0:
        return 0
    score = continuity // 2
    if keeps_tactical_stability(board, child_board, moving_color):
        score += 8
    return score


def keeps_tactical_stability(board: Board, child_board: Board, moving_color: Color) -> bool:
    """Return True when a move does not loosen king safety or invasion lines."""

    before = king_defense_profile(board, moving_color)
    after = king_defense_profile(child_board, moving_color)
    return after.danger <= before.danger and after.invasion_lines <= before.invasion_lines
