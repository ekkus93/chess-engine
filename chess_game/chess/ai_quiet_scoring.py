"""Quiet move-ordering scoring helpers.

Extracted from ``ai_move_ordering``. The QuietOrderContext + make_quiet_order_context
context builder and the per-aspect quiet-move scoring helpers (positional, king-move,
heavy-piece, pawn/passer, luft, defensive-priority, coordination, check/activity). This
is the cycle-free helper layer below the public ``quiet_strategy_order_score`` entry,
which stays in ``ai_move_ordering`` and imports the names it uses from here.
"""

from __future__ import annotations

from dataclasses import dataclass

from chess_game.chess.board.attack_utils import piece_attacks_square
from chess_game.chess.board import Board
from chess_game.chess.constants import ConstantSquare, get_square_constant
from chess_game.chess.defensive_priorities import (
    DANGEROUS_KING_PRESSURE_THRESHOLD,
    KingDefenseProfile,
    king_defense_profile,
    king_danger_index,
    king_needs_shelter,
    h_pawn_exposure_penalty,
)
from chess_game.chess.evaluation_tables import MATERIAL_VALUES
from chess_game.chess.move import Move
from chess_game.chess.opening_move_ordering import (
    is_repeat_heavy_piece_move as _opening_repeat_heavy_piece_move,
    undeveloped_minor_count as _opening_undeveloped_minor_count,
)
from chess_game.chess.opponent_plans import OpponentPlanProfile, opponent_plan_profile
from chess_game.chess.piece_coordination import (
    bishop_coordination_bonus,
    queen_coordination_bonus,
    rook_coordination_bonus,
    square_has_friendly_support as _square_has_friendly_support,
)
from chess_game.chess.rook_endgame_guidance import non_king_piece_kinds
from chess_game.chess.strategy_utils import (
    center_distance,
    iter_color_pieces,
    king_coordinates,
    non_king_material_lead,
    non_king_piece_count_at_most,
    path_clear_between,
)
from chess_game.chess.types import Color, PieceType

from chess_game.chess.ai_quiet_ordering_constants import (
    ENDGAME_ORDER_MAX_NON_KING_PIECES,
    QUIET_ACTIVITY_CHASE_PENALTY,
    QUIET_ACTIVITY_COORDINATION_BONUS,
    QUIET_ACTIVITY_LINE_PRESSURE_BONUS,
    QUIET_ACTIVITY_LOOSEN_PENALTY,
    QUIET_ACTIVITY_REPEAT_PENALTY,
    QUIET_ACTIVITY_SIMPLIFY_BONUS,
    QUIET_ADD_DEFENDER_BONUS,
    QUIET_BISHOP_PASSIVE_RETREAT_PENALTY,
    QUIET_BLOCKADE_BONUS,
    QUIET_CASTLING_BONUS,
    QUIET_CENTRALIZATION_BONUS,
    QUIET_CONTEST_ATTACK_FILE_BONUS,
    QUIET_DANGER_RELIEF_BONUS,
    QUIET_ENTRY_SQUARE_BONUS,
    QUIET_H_EXPOSURE_LUFT_BONUS,
    QUIET_HEAVY_PIECE_PRESSURE_BONUS,
    QUIET_KING_CENTRALIZATION_BONUS,
    QUIET_KING_CUTOFF_BONUS,
    QUIET_KING_REFINEMENT_BONUS,
    QUIET_LUFT_BONUS,
    QUIET_MAJOR_TRADE_OFFER_BONUS,
    QUIET_NEGLECT_DANGER_PENALTY,
    QUIET_PASSED_PAWN_PUSH_BONUS,
    QUIET_PLAN_NEGLECT_PENALTY,
    QUIET_PLAN_RELIEF_BONUS,
    QUIET_PROPHYLACTIC_LUFT_BONUS,
    QUIET_RECONNECT_DEFENDER_BONUS,
    QUIET_RESTORE_BACK_RANK_BONUS,
    QUIET_ROOK_BEHIND_PASSER_BONUS,
    QUIET_URGENT_LUFT_BONUS,
    _ADVANTAGE_PRESERVATION_HANGING_PENALTY,
    _ADVANTAGE_PRESERVATION_MIN_LEAD,
    _KNIGHT_THREATENS_MINOR_BONUS,
)
from chess_game.chess.ai_check_ordering import (
    _offers_major_piece_trade,
    _piece_value,
)


@dataclass(frozen=True)
class QuietOrderContext:
    """Shared board-level state reused across quiet move scoring for one node."""

    defense_profile: KingDefenseProfile
    opponent_plan: OpponentPlanProfile
    endgame_order_position: bool
    heavy_piece_endgame: bool
    material_lead: int

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
        if _is_h_pawn_luft(color, move):
            if h_pawn_exposure_penalty(board, color) >= 15:
                score += QUIET_H_EXPOSURE_LUFT_BONUS
            elif is_prophylactic_h_luft(board, color):
                score += QUIET_PROPHYLACTIC_LUFT_BONUS
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
    enemy_king_coords = king_coordinates(board, enemy_color)
    if enemy_king_coords is None:
        return False
    return int(move.end.row) == enemy_king_coords[0] or int(move.end.col) == enemy_king_coords[1]

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

def _is_h_pawn_luft(color: Color, move: Move) -> bool:
    """Return True when the move specifically creates h-file luft (h2-h3 or h7-h6)."""
    home_row = 6 if color == Color.WHITE else 1
    return (
        int(move.start.row) == home_row
        and int(move.start.col) == 7
        and abs(int(move.end.row) - int(move.start.row)) == 1
    )

def is_prophylactic_h_luft(board: Board, color: Color) -> bool:
    """Return True when h2-h3 (h7-h6) is a good prophylactic move.

    Fires when the king is castled kingside with the h-pawn unmoved and queens
    are on the board — even before any bishop aims at h2.  This encourages the
    engine to play h3 shortly after castling as good prophylactic chess.
    """

    if not any(p is not None and p.kind == PieceType.QUEEN for row in board.board for p in row):
        return False
    king_sq = board.find_king(color)
    if king_sq is None:
        return False
    king_row = int(king_sq.row)
    king_col = int(king_sq.col)
    home_row = 7 if color == Color.WHITE else 0
    return king_row == home_row and king_col == 6

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

def _bishop_passive_retreat_penalty(board: Board, move: Move, color: Color) -> int:
    """Penalise bishop moves that retreat to the back rank or second rank in the middlegame.

    A bishop retreating to its own back rank (rank 1 for White, rank 8 for Black)
    or second rank (rank 2 for White, rank 7 for Black) when queens are still on
    the board is almost always passive — it gives up an active diagonal and is
    often blocked by its own pawns.  The classic example is Bf4-d2, which retreated
    the bishop to d2 in game 2 where it did nothing for the rest of the game.
    """

    if not any(
        piece is not None and piece.kind == PieceType.QUEEN
        for row in board.board
        for piece in row
    ):
        return 0
    back_rank_row = 7 if color == Color.WHITE else 0
    second_rank_row = 6 if color == Color.WHITE else 1
    end_row = int(move.end.row)
    start_row = int(move.start.row)
    if end_row == back_rank_row and start_row != back_rank_row:
        return QUIET_BISHOP_PASSIVE_RETREAT_PENALTY
    if end_row == second_rank_row and start_row not in {back_rank_row, second_rank_row}:
        return QUIET_BISHOP_PASSIVE_RETREAT_PENALTY // 2
    return 0

def _knight_threatens_minor_bonus(board: Board, move: Move, color: Color) -> int:
    """Return a bonus when a knight move's destination attacks an enemy bishop or
    knight (quiet threat — move must not itself be a capture)."""
    dest_row = int(move.end.row)
    dest_col = int(move.end.col)
    knight_deltas = [(-2, -1), (-2, 1), (-1, -2), (-1, 2), (1, -2), (1, 2), (2, -1), (2, 1)]
    for dr, dc in knight_deltas:
        r, c = dest_row + dr, dest_col + dc
        if 0 <= r <= 7 and 0 <= c <= 7:
            target = board.get_piece(get_square_constant(r, c))
            if (
                target is not None
                and target.color != color
                and target.kind in (PieceType.BISHOP, PieceType.KNIGHT)
            ):
                return _KNIGHT_THREATENS_MINOR_BONUS
    return 0
