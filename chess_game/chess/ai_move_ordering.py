"""Helpers for scoring quiet strategic moves during search ordering."""

from dataclasses import dataclass

from chess_game.chess.board.attack_utils import piece_attacks_square
from chess_game.chess.ai_repetition_patterns import quiet_cycle_penalty
from chess_game.chess.board import Board
from chess_game.chess.board.game_state import is_checkmate, is_in_check
from chess_game.chess.constants import ConstantSquare
from chess_game.chess.conversion_guidance import winning_conversion_order_bonus
from chess_game.chess.defensive_containment_guidance import (
    heavy_piece_defense_order_bonus,
)
from chess_game.chess.defensive_endgame_guidance import defensive_endgame_order_bonus
from chess_game.chess.heavy_piece_endgame_guidance import heavy_piece_endgame_order_bonus
from chess_game.chess.low_material_race_guidance import low_material_race_order_bonus
from chess_game.chess.endgame_choice_guidance import endgame_choice_order_bonus
from chess_game.chess.low_material_coordination_guidance import (
    low_material_coordination_order_bonus,
)
from chess_game.chess.simple_endgame_guidance import simple_endgame_order_bonus
from chess_game.chess.defensive_priorities import (
    DANGEROUS_KING_PRESSURE_THRESHOLD,
    KingDefenseProfile,
    king_defense_profile,
    king_danger_index,
    king_needs_shelter,
)
from chess_game.chess.evaluation_tables import MATERIAL_VALUES
from chess_game.chess.move import Move
from chess_game.chess.opening_move_ordering import (
    is_repeat_heavy_piece_move as _opening_repeat_heavy_piece_move,
    opening_discipline_order_score,
    undeveloped_minor_count as _opening_undeveloped_minor_count,
)
from chess_game.chess.opponent_plans import OpponentPlanProfile, opponent_plan_profile
from chess_game.chess.passer_race_guidance import passer_race_order_bonus
from chess_game.chess.pawn_race_move_ordering import pawn_race_move_bonus
from chess_game.chess.piece_coordination import (
    bishop_coordination_bonus,
    improves_worst_piece,
    queen_coordination_bonus,
    rook_coordination_bonus,
    square_has_friendly_support as _square_has_friendly_support,
)
from chess_game.chess.rook_endgame_guidance import non_king_piece_kinds, rook_endgame_order_bonus
from chess_game.chess.structure_recognition import structure_plan_bonus
from chess_game.chess.strategy_utils import (
    center_distance,
    is_capture_move,
    iter_color_pieces,
    non_king_material_lead,
    non_king_piece_count_at_most,
    path_clear_between,
)
from chess_game.chess.threat_awareness import threat_response_order_bonus
from chess_game.chess.tactical_transition_guidance import tactical_transition_order_bonus
from chess_game.chess.types import Color, PieceType

QUIET_CASTLING_BONUS = 160
QUIET_PASSED_PAWN_PUSH_BONUS = 90
QUIET_KING_CENTRALIZATION_BONUS = 18
QUIET_HEAVY_PIECE_PRESSURE_BONUS = 24
QUIET_CENTRALIZATION_BONUS = 12
QUIET_KING_CUTOFF_BONUS = 32
QUIET_ROOK_BEHIND_PASSER_BONUS = 40
QUIET_LUFT_BONUS = 16
QUIET_WORST_PIECE_BONUS = 18
QUIET_BLOCKADE_BONUS = 28
QUIET_MAJOR_TRADE_OFFER_BONUS = 26
QUIET_KING_REFINEMENT_BONUS = 10
QUIET_USEFUL_CHECK_BONUS = 34
QUIET_URGENT_LUFT_BONUS = 24
QUIET_CONTEST_ATTACK_FILE_BONUS = 44
QUIET_DANGER_RELIEF_BONUS = 52
QUIET_ENTRY_SQUARE_BONUS = 28
QUIET_ADD_DEFENDER_BONUS = 22
QUIET_RECONNECT_DEFENDER_BONUS = 18
QUIET_RESTORE_BACK_RANK_BONUS = 26
QUIET_NEGLECT_DANGER_PENALTY = 34
QUIET_PLAN_RELIEF_BONUS = 8
QUIET_PLAN_NEGLECT_PENALTY = 7
QUIET_ACTIVITY_LINE_PRESSURE_BONUS = 16
QUIET_ACTIVITY_COORDINATION_BONUS = 14
QUIET_ACTIVITY_SIMPLIFY_BONUS = 18
QUIET_ACTIVITY_CHASE_PENALTY = 22
QUIET_ACTIVITY_REPEAT_PENALTY = 28
QUIET_ACTIVITY_LOOSEN_PENALTY = 18
QUIET_CHECK_MATE_NET_BONUS = 64
QUIET_CHECK_MATERIAL_BONUS = 30
QUIET_CHECK_DRIVING_BONUS = 22
QUIET_CHECK_SIMPLIFY_BONUS = 16
QUIET_CHECK_SHRINK_BOX_BONUS = 16
QUIET_CHECK_BREAK_DEFENDER_BONUS = 12
QUIET_EMPTY_CHECK_PENALTY = 40
QUIET_EASY_SHUFFLE_CHECK_PENALTY = 20
QUIET_SELF_EXPOSING_CHECK_PENALTY = 22
ENDGAME_ORDER_MAX_NON_KING_PIECES = 8
_ADVANTAGE_PRESERVATION_HANGING_PENALTY = 30
_ADVANTAGE_PRESERVATION_MIN_LEAD = 400  # 4 pawns


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


@dataclass(frozen=True)
class QuietOrderContext:
    """Shared board-level state reused across quiet move scoring for one node."""

    defense_profile: KingDefenseProfile
    opponent_plan: OpponentPlanProfile
    endgame_order_position: bool
    heavy_piece_endgame: bool
    material_lead: int


def quiet_strategy_order_score(
    board: Board,
    move: Move,
    order_context: QuietOrderContext | None = None,
) -> int:
    """Return a bonus for strong quiet strategic moves.

    Placement audit: this file scores only quiet candidates. It intentionally
    avoids capture-ordering and root-only tie-break work so king-danger signals
    are not rewarded the same way in every search stage.
    """

    if move.promotion is not None or is_capture_move(board, move):
        return 0
    piece = board.get_piece(move.start)
    if piece is None:
        return 0
    quiet_context = order_context or make_quiet_order_context(board)
    score = _centralization_bonus(piece.kind, move)
    score += opening_discipline_order_score(board, piece.kind, move)
    score += _defensive_priority_bonus(board, move, quiet_context)
    score += _king_move_bonus(board, piece.kind, move, quiet_context.heavy_piece_endgame)
    score += _heavy_piece_bonus(board, piece.kind, piece.color, move)
    score += _pawn_bonus(board, piece.color, piece.kind, move)
    if quiet_context.endgame_order_position:
        score += endgame_choice_order_bonus(board, piece.color, piece.kind, move)
        score += winning_conversion_order_bonus(board, piece.color, piece.kind, move)
        score += heavy_piece_defense_order_bonus(board, piece.color, piece.kind, move)
        score += heavy_piece_endgame_order_bonus(board, piece.color, piece.kind, move)
        score += simple_endgame_order_bonus(board, piece.color, piece.kind, move)
        score += low_material_coordination_order_bonus(board, piece.color, piece.kind, move)
        score += low_material_race_order_bonus(board, piece.color, piece.kind, move)
        score += defensive_endgame_order_bonus(board, piece.color, piece.kind, move)
        score += passer_race_order_bonus(board, piece.color, piece.kind, move)
        score += pawn_race_move_bonus(board, move, piece.color)
    score += threat_response_order_bonus(board, piece.color, piece.kind, move)
    score += tactical_transition_order_bonus(board, move)
    score += _piece_coordination_bonus(board, piece.color, piece.kind, move)
    score += structure_plan_bonus(board, piece.color, piece.kind, move)
    if quiet_context.endgame_order_position:
        score += rook_endgame_order_bonus(board, piece.color, piece.kind, move)
    score -= quiet_cycle_penalty(board, move, piece.kind)
    if improves_worst_piece(board, move):
        score += QUIET_WORST_PIECE_BONUS
    score += _check_quality_bonus(board, piece.kind, move)
    score -= _advantage_preservation_penalty(board, piece, move, quiet_context)
    return score


def make_quiet_order_context(board: Board) -> QuietOrderContext:
    """Build shared quiet-order state once per node."""

    return QuietOrderContext(
        defense_profile=king_defense_profile(board, board.turn),
        opponent_plan=opponent_plan_profile(board, board.turn),
        endgame_order_position=_is_endgame_order_position(board),
        heavy_piece_endgame=_is_heavy_piece_endgame(board),
        material_lead=non_king_material_lead(board, board.turn),
    )


def _advantage_preservation_penalty(
    board: Board,
    piece,
    move: Move,
    context: QuietOrderContext,
) -> int:
    """Return a penalty when a clearly-winning side drops a piece to a cheap attacker."""
    if context.material_lead < _ADVANTAGE_PRESERVATION_MIN_LEAD:
        return 0
    if piece.kind in (PieceType.PAWN, PieceType.KING):
        return 0
    own_value = MATERIAL_VALUES.get(piece.kind, 0)
    enemy_color = Color.BLACK if piece.color == Color.WHITE else Color.WHITE
    for enemy_piece, _, _ in iter_color_pieces(board, enemy_color):
        if MATERIAL_VALUES.get(enemy_piece.kind, 0) >= own_value:
            continue
        if piece_attacks_square(enemy_piece, enemy_piece.square, move.end, board):
            return _ADVANTAGE_PRESERVATION_HANGING_PENALTY
    return 0


def _centralization_bonus(kind: PieceType, move: Move) -> int:
    """Return a bonus for improving piece placement toward useful squares."""

    if kind == PieceType.ROOK:
        return _line_piece_bonus(move)
    if kind == PieceType.QUEEN:
        return _line_piece_bonus(move) // 2
    if kind in (PieceType.KNIGHT, PieceType.BISHOP):
        return _minor_piece_centralization(move)
    return 0


def _line_piece_bonus(move: Move) -> int:
    """Score rook/queen moves by improving central file or rank pressure."""

    start_distance = center_distance(int(move.start.row), int(move.start.col))
    end_distance = center_distance(int(move.end.row), int(move.end.col))
    return max(0, start_distance - end_distance) * QUIET_CENTRALIZATION_BONUS


def _minor_piece_centralization(move: Move) -> int:
    """Score quiet minor-piece moves by centralization gain."""

    start_distance = center_distance(int(move.start.row), int(move.start.col))
    end_distance = center_distance(int(move.end.row), int(move.end.col))
    return max(0, start_distance - end_distance) * QUIET_CENTRALIZATION_BONUS


def _is_castling_move(move: Move) -> bool:
    """Return True for king-side or queen-side castling geometry."""

    return int(move.start.col) == 4 and abs(int(move.start.col) - int(move.end.col)) == 2


def _king_move_bonus(
    board: Board,
    kind: PieceType,
    move: Move,
    heavy_piece_endgame: bool,
) -> int:
    score = 0
    if kind == PieceType.KING and _is_castling_move(move):
        score += QUIET_CASTLING_BONUS
    if kind == PieceType.KING and heavy_piece_endgame:
        score += _king_centralization_bonus(move)
    if kind == PieceType.KING and not heavy_piece_endgame:
        score += _king_refinement_bonus(board, move)
    return score


def _heavy_piece_bonus(board: Board, kind: PieceType, color: Color, move: Move) -> int:
    score = 0
    if _contests_attack_line(board, color, move):
        score += QUIET_CONTEST_ATTACK_FILE_BONUS
    if kind in (PieceType.ROOK, PieceType.QUEEN) and _lines_up_with_enemy_king(board, move):
        score += QUIET_HEAVY_PIECE_PRESSURE_BONUS
    if kind in (PieceType.ROOK, PieceType.QUEEN) and _improves_king_cutoff(board, move):
        score += QUIET_KING_CUTOFF_BONUS
    if kind in (PieceType.ROOK, PieceType.QUEEN) and _offers_major_piece_trade(board, move):
        score += QUIET_MAJOR_TRADE_OFFER_BONUS
    if kind in (PieceType.ROOK, PieceType.QUEEN):
        score += _heavy_piece_activity_bonus(board, color, kind, move)
    if kind == PieceType.ROOK and _moves_rook_behind_passer(board, color, move):
        score += QUIET_ROOK_BEHIND_PASSER_BONUS
    if kind in (PieceType.KING, PieceType.ROOK, PieceType.QUEEN) and _blockades_enemy_passer(
        board, color, move
    ):
        score += QUIET_BLOCKADE_BONUS
    return score


def _pawn_bonus(board: Board, color: Color, kind: PieceType, move: Move) -> int:
    score = 0
    if kind == PieceType.PAWN and _is_passed_pawn_push(board, color, move):
        score += QUIET_PASSED_PAWN_PUSH_BONUS + _pawn_push_progress(color, move)
    if kind == PieceType.PAWN and _creates_luft(color, move):
        score += QUIET_LUFT_BONUS
        if _is_urgent_luft(board, color):
            score += QUIET_URGENT_LUFT_BONUS
    return score


def _defensive_priority_bonus(
    board: Board,
    move: Move,
    order_context: QuietOrderContext,
) -> int:
    """Reward defense-first quiet moves when the side to move is under pressure."""

    piece = board.get_piece(move.start)
    if piece is None:
        return 0
    before = order_context.defense_profile
    assess_plan = _requires_plan_assessment(piece.kind, move)
    if before.danger < DANGEROUS_KING_PRESSURE_THRESHOLD and not assess_plan:
        return 0
    child_board = board.clone()
    if not child_board.apply_legal_move(move.start, move.end, promotion=move.promotion):
        return 0
    before_plan = None
    if assess_plan or before.danger >= DANGEROUS_KING_PRESSURE_THRESHOLD:
        before_plan = order_context.opponent_plan
        after_plan = opponent_plan_profile(child_board, board.turn)
    else:
        after_plan = None
    if before.danger < DANGEROUS_KING_PRESSURE_THRESHOLD:
        return 0 if before_plan is None or after_plan is None else _plan_pressure_delta_score(
            before_plan.pressure,
            after_plan.pressure,
        )
    after = king_defense_profile(child_board, board.turn)
    danger_reduction = max(0, before.danger - after.danger)
    score = danger_reduction * QUIET_DANGER_RELIEF_BONUS
    score += max(0, before.invasion_lines - after.invasion_lines) * QUIET_ENTRY_SQUARE_BONUS
    score += max(
        0,
        after.king_zone_defenders - before.king_zone_defenders,
    ) * QUIET_ADD_DEFENDER_BONUS
    score += max(
        0,
        after.heavy_connections - before.heavy_connections,
    ) * QUIET_RECONNECT_DEFENDER_BONUS
    score += max(0, after.safe_king_moves - before.safe_king_moves) * QUIET_ADD_DEFENDER_BONUS
    if before.back_rank_weak and not after.back_rank_weak:
        score += QUIET_RESTORE_BACK_RANK_BONUS
    score -= max(0, after.danger - before.danger) * QUIET_NEGLECT_DANGER_PENALTY
    score -= max(0, after.invasion_lines - before.invasion_lines) * QUIET_ENTRY_SQUARE_BONUS
    score -= max(0, before.safe_king_moves - after.safe_king_moves) * QUIET_NEGLECT_DANGER_PENALTY
    if after.king_zone_defenders < before.king_zone_defenders:
        score -= QUIET_ADD_DEFENDER_BONUS
    if after.heavy_connections < before.heavy_connections:
        score -= QUIET_RECONNECT_DEFENDER_BONUS
    if before_plan is not None and after_plan is not None:
        score += _plan_pressure_delta_score(before_plan.pressure, after_plan.pressure)
    return score


def _plan_pressure_delta_score(before_pressure: int, after_pressure: int) -> int:
    score = max(0, before_pressure - after_pressure) * QUIET_PLAN_RELIEF_BONUS
    score -= max(0, after_pressure - before_pressure) * QUIET_PLAN_NEGLECT_PENALTY
    return score


def _requires_plan_assessment(kind: PieceType, move: Move) -> bool:
    if kind in {PieceType.KING, PieceType.QUEEN, PieceType.ROOK}:
        return True
    if kind == PieceType.PAWN:
        return int(move.start.col) in {3, 4, 5, 6, 7} or int(move.end.col) in {3, 4}
    return False


def _is_heavy_piece_endgame(board: Board) -> bool:
    """Return True in simple endings where king centralization matters more."""

    return len(non_king_piece_kinds(board)) <= 4


def _is_endgame_order_position(board: Board) -> bool:
    """Return True when endgame-only quiet-order heuristics are worth considering."""

    return non_king_piece_count_at_most(board, ENDGAME_ORDER_MAX_NON_KING_PIECES)


def _king_centralization_bonus(move: Move) -> int:
    """Reward king steps toward the center in quiet endgames."""

    start_distance = center_distance(int(move.start.row), int(move.start.col))
    end_distance = center_distance(int(move.end.row), int(move.end.col))
    return max(0, start_distance - end_distance) * QUIET_KING_CENTRALIZATION_BONUS


def _is_passed_pawn_push(board: Board, color: Color, move: Move) -> bool:
    """Return True when a quiet pawn push advances a passed pawn candidate."""

    if int(move.start.col) != int(move.end.col):
        return False
    start_row = int(move.start.row)
    end_row = int(move.end.row)
    if color == Color.WHITE and end_row >= start_row:
        return False
    if color == Color.BLACK and end_row <= start_row:
        return False
    enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
    for row_index, row in enumerate(board.board):
        for col_index, piece in enumerate(row):
            if (
                piece is not None
                and piece.color == enemy_color
                and piece.kind == PieceType.PAWN
                and abs(col_index - int(move.end.col)) <= 1
            ):
                if color == Color.WHITE and row_index < end_row:
                    return False
                if color == Color.BLACK and row_index > end_row:
                    return False
    return True


def _pawn_push_progress(color: Color, move: Move) -> int:
    """Return a bonus scaled by how advanced the pawn push becomes."""

    end_row = int(move.end.row)
    progress = 6 - end_row if color == Color.WHITE else end_row - 1
    return progress * 4


def _lines_up_with_enemy_king(board: Board, move: Move) -> bool:
    """Return True when a heavy piece move increases pressure on the enemy king."""

    enemy_color = Color.BLACK if board.turn == Color.WHITE else Color.WHITE
    enemy_king = next(
        (
            piece.square
            for row in board.board
            for piece in row
            if piece is not None
            and piece.color == enemy_color
            and piece.kind == PieceType.KING
        ),
        None,
    )
    if enemy_king is None:
        return False
    return int(move.end.row) == int(enemy_king.row) or int(move.end.col) == int(enemy_king.col)


def _improves_king_cutoff(board: Board, move: Move) -> bool:
    enemy_color = Color.BLACK if board.turn == Color.WHITE else Color.WHITE
    enemy_king = next(
        (
            piece.square
            for row in board.board
            for piece in row
            if piece is not None
            and piece.color == enemy_color
            and piece.kind == PieceType.KING
        ),
        None,
    )
    if enemy_king is None:
        return False
    start_same_line = (
        int(move.start.row) == int(enemy_king.row)
        or int(move.start.col) == int(enemy_king.col)
    )
    end_same_line = (
        int(move.end.row) == int(enemy_king.row)
        or int(move.end.col) == int(enemy_king.col)
    )
    return not start_same_line and end_same_line


def _moves_rook_behind_passer(board: Board, color: Color, move: Move) -> bool:
    for row_index, row in enumerate(board.board):
        for col_index, piece in enumerate(row):
            if piece is None or piece.color != color or piece.kind != PieceType.PAWN:
                continue
            if not _is_passed_pawn_candidate(board, color, row_index, col_index):
                continue
            if int(move.end.col) != col_index:
                continue
            if color == Color.WHITE and int(move.end.row) > row_index:
                return True
            if color == Color.BLACK and int(move.end.row) < row_index:
                return True
    return False


def _is_passed_pawn_candidate(board: Board, color: Color, row: int, col: int) -> bool:
    enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
    for row_index, board_row in enumerate(board.board):
        for col_index, piece in enumerate(board_row):
            if (
                piece is not None
                and piece.color == enemy_color
                and piece.kind == PieceType.PAWN
                and abs(col_index - col) <= 1
            ):
                if color == Color.WHITE and row_index < row:
                    return False
                if color == Color.BLACK and row_index > row:
                    return False
    return True


def _creates_luft(color: Color, move: Move) -> bool:
    home_row = 6 if color == Color.WHITE else 1
    return (
        int(move.start.row) == home_row
        and int(move.start.col) in {5, 6, 7}
        and abs(int(move.end.row) - int(move.start.row)) == 1
    )


def _is_urgent_luft(board: Board, color: Color) -> bool:
    return king_danger_index(board, color) >= DANGEROUS_KING_PRESSURE_THRESHOLD


def _piece_coordination_bonus(
    board: Board,
    color: Color,
    kind: PieceType,
    move: Move,
) -> int:
    if kind == PieceType.ROOK:
        return rook_coordination_bonus(board, color, move)
    if kind == PieceType.BISHOP:
        return bishop_coordination_bonus(board, move)
    if kind == PieceType.QUEEN:
        return queen_coordination_bonus(board, color, move)
    return 0


def _king_refinement_bonus(board: Board, move: Move) -> int:
    """Reward quiet king improvements that tighten safety in stable middlegames."""

    if king_needs_shelter(board, board.turn):
        return 0
    child_board = board.clone()
    if not child_board.apply_legal_move(move.start, move.end, promotion=move.promotion):
        return 0
    before = king_defense_profile(board, board.turn)
    after = king_defense_profile(child_board, board.turn)
    score = max(0, before.invasion_lines - after.invasion_lines) * QUIET_KING_REFINEMENT_BONUS
    score += max(0, after.king_zone_defenders - before.king_zone_defenders) * (
        QUIET_KING_REFINEMENT_BONUS // 2
    )
    score += max(0, after.safe_king_moves - before.safe_king_moves) * (
        QUIET_KING_REFINEMENT_BONUS // 2
    )
    if before.back_rank_weak and not after.back_rank_weak:
        score += QUIET_KING_REFINEMENT_BONUS * 2
    score -= max(0, after.danger - before.danger) * QUIET_KING_REFINEMENT_BONUS
    return score


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


def _blockades_enemy_passer(board: Board, color: Color, move: Move) -> bool:
    enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
    target_square = (int(move.end.row), int(move.end.col))
    for row_index, board_row in enumerate(board.board):
        for col_index, piece in enumerate(board_row):
            if piece is None or piece.color != enemy_color or piece.kind != PieceType.PAWN:
                continue
            if not _is_passed_pawn_candidate(board, enemy_color, row_index, col_index):
                continue
            blockade_row = row_index + (-1 if enemy_color == Color.WHITE else 1)
            if target_square == (blockade_row, col_index):
                return True
    return False


def _contests_attack_line(board: Board, color: Color, move: Move) -> bool:
    king_square = next(
        (
            piece.square
            for row in board.board
            for piece in row
            if piece is not None and piece.color == color and piece.kind == PieceType.KING
        ),
        None,
    )
    if king_square is None:
        return False
    end_square = (int(move.end.row), int(move.end.col))
    king_row = int(king_square.row)
    king_col = int(king_square.col)
    enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
    for row_index, row in enumerate(board.board):
        for col_index, piece in enumerate(row):
            if (
                piece is None
                or piece.color != enemy_color
                or piece.kind not in (PieceType.ROOK, PieceType.QUEEN)
            ):
                continue
            attacker_square = (row_index, col_index)
            if not _attacks_king_line(attacker_square, (king_row, king_col)):
                continue
            if not path_clear_between(board, attacker_square, (king_row, king_col)):
                continue
            if _lies_between(attacker_square, (king_row, king_col), end_square):
                return True
    return False


def _attacks_king_line(
    attacker_square: tuple[int, int],
    king_square: tuple[int, int],
) -> bool:
    return (
        attacker_square[0] == king_square[0]
        or attacker_square[1] == king_square[1]
    )


def _lies_between(
    attacker_square: tuple[int, int],
    king_square: tuple[int, int],
    target_square: tuple[int, int],
) -> bool:
    if target_square in {attacker_square, king_square}:
        return False
    if attacker_square[0] == king_square[0] == target_square[0]:
        start_col = min(attacker_square[1], king_square[1])
        end_col = max(attacker_square[1], king_square[1])
        return start_col < target_square[1] < end_col
    if attacker_square[1] == king_square[1] == target_square[1]:
        start_row = min(attacker_square[0], king_square[0])
        end_row = max(attacker_square[0], king_square[0])
        return start_row < target_square[0] < end_row
    return False


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
    enemy_king = next(
        (
            piece.square
            for row in board.board
            for piece in row
            if piece is not None
            and piece.color == enemy_color
            and piece.kind == PieceType.KING
        ),
        None,
    )
    if enemy_king is None or not _move_gives_check(
        board,
        kind,
        move,
        (int(enemy_king.row), int(enemy_king.col)),
    ):
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


def _heavy_piece_activity_bonus(
    board: Board,
    color: Color,
    kind: PieceType,
    move: Move,
) -> int:
    """Reward real heavy-piece pressure and penalize flashy loosening moves.

    Real activity means the move creates a direct tactical threat, improves
    pressure on king-entry lines, coordinates with other attackers, offers
    simplifying concessions when ahead, or reduces enemy counterplay.
    """

    child_board = board.clone()
    if not child_board.apply_legal_move(move.start, move.end, promotion=move.promotion):
        return 0
    enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
    before_self = king_defense_profile(board, color)
    after_self = king_defense_profile(child_board, color)
    before_enemy = king_defense_profile(board, enemy_color)
    after_enemy = king_defense_profile(child_board, enemy_color)
    score = max(0, after_enemy.invasion_lines - before_enemy.invasion_lines)
    score *= QUIET_ACTIVITY_LINE_PRESSURE_BONUS
    score += max(0, after_enemy.danger - before_enemy.danger) * (
        QUIET_ACTIVITY_LINE_PRESSURE_BONUS // 2
    )
    score += max(0, before_enemy.king_zone_defenders - after_enemy.king_zone_defenders) * (
        QUIET_ACTIVITY_COORDINATION_BONUS
    )
    score += max(0, before_enemy.heavy_connections - after_enemy.heavy_connections) * (
        QUIET_ACTIVITY_COORDINATION_BONUS
    )
    if _offers_major_piece_trade(board, move):
        score += QUIET_ACTIVITY_SIMPLIFY_BONUS
    if _square_has_friendly_support(child_board, color, move.end):
        score += QUIET_ACTIVITY_COORDINATION_BONUS // 2
    if _opening_repeat_heavy_piece_move(
        board,
        kind,
        move,
        _opening_undeveloped_minor_count(board),
        king_needs_shelter(board, board.turn),
    ) and score == 0:
        score -= QUIET_ACTIVITY_REPEAT_PENALTY
    if (
        _is_forward_heavy_move(board.turn, move)
        and not _square_has_friendly_support(child_board, color, move.end)
        and _enemy_can_chase_square(child_board, enemy_color, move.end, kind)
    ):
        score -= QUIET_ACTIVITY_CHASE_PENALTY
    score -= max(0, after_self.danger - before_self.danger) * QUIET_ACTIVITY_LOOSEN_PENALTY
    score -= max(0, after_self.invasion_lines - before_self.invasion_lines) * (
        QUIET_ACTIVITY_LOOSEN_PENALTY
    )
    score -= max(0, before_self.heavy_connections - after_self.heavy_connections) * (
        QUIET_ACTIVITY_LOOSEN_PENALTY
    )
    if after_self.back_rank_weak and not before_self.back_rank_weak:
        score -= QUIET_ACTIVITY_CHASE_PENALTY
    return score


def _enemy_can_chase_square(
    board: Board,
    enemy_color: Color,
    target_square: ConstantSquare,
    moving_kind: PieceType,
) -> bool:
    moving_value = _piece_value(moving_kind)
    for row in board.board:
        for piece in row:
            if piece is None or piece.color != enemy_color or piece.square is None:
                continue
            if _piece_value(piece.kind) >= moving_value:
                continue
            if piece_attacks_square(piece, piece.square, target_square, board):
                return True
    return False


def _is_forward_heavy_move(color: Color, move: Move) -> bool:
    return int(move.end.row) < int(move.start.row) if color == Color.WHITE else int(
        move.end.row
    ) > int(move.start.row)


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
