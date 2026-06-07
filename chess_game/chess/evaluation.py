"""Position evaluation tables and strategic heuristics for the chess AI."""

from __future__ import annotations
from collections.abc import Iterator

from chess_game.chess.board import Board
from chess_game.chess.constants import ConstantSquare, get_col_constant, get_row_constant
from chess_game.chess.endgame_evaluation import (
    evaluate_conversion as _evaluate_conversion,
    evaluate_endgame_technique as _evaluate_endgame_technique,
    evaluate_endgame_races as _evaluate_endgame_races,
    evaluate_heavy_piece_endgames as _evaluate_heavy_piece_endgames,
    evaluate_queen_vs_rook as _evaluate_queen_vs_rook,
    evaluate_low_material_coordination as _evaluate_low_material_coordination,
    evaluate_passer_races as _evaluate_passer_races,
    evaluate_progress as _evaluate_progress,
    evaluate_rook_endgames as _evaluate_rook_endgames,
)
from chess_game.chess.eval_weights import EvalWeights
from chess_game.chess.middlegame_practicality_guidance import (
    middlegame_practicality_evaluation_score as _middlegame_practicality_evaluation_score,
)
from chess_game.chess.defensive_priorities import (
    king_defense_profile,
    h_pawn_exposure_penalty as _h_pawn_exposure_penalty,
)
from chess_game.chess.pawn_structure_evaluation import (
    collect_pawn_positions as _collect_pawn_positions,
    evaluate_pawn_structure as _evaluate_pawn_structure,
)
from chess_game.chess.opening_development import (
    early_shelter_pawn_push_penalty as _early_shelter_pawn_push_penalty,
    coordinated_minor_piece_setup as _coordinated_minor_piece_setup,
    opening_central_rook_bonus as _opening_central_rook_bonus,
    opening_king_urgency_penalty as _opening_king_urgency_penalty,
    early_flank_queen_sortie_penalty as _early_flank_queen_sortie_penalty,
    early_flank_pawn_poke_penalty as _early_flank_pawn_poke_penalty,
    early_flank_raid_penalty as _early_flank_raid_penalty,
    opening_wing_knight_lunge_penalty as _opening_wing_knight_lunge_penalty,
    _opening_drift_penalties,
    opening_king_safety_score as _opening_king_safety_score,
    opening_queen_restraint_bonus as _opening_queen_restraint_bonus,
    opening_rook_connection_bonus as _opening_rook_connection_bonus,
    early_queen_raid_penalty as _early_queen_raid_penalty,
    opening_central_control_bonus as _opening_central_control_bonus,
    opening_piece_coordination_bonus as _opening_piece_coordination_bonus,
    unforced_shelter_loosening_penalty as _unforced_shelter_loosening_penalty,
    undeveloped_minor_piece_count as _undeveloped_minor_piece_count,
    middlegame_rim_knight_penalty as _middlegame_rim_knight_penalty,
    late_castling_urgency_penalty as _late_castling_urgency_penalty,
    castling_path_blocked_penalty as _castling_path_blocked_penalty,
)
from chess_game.chess.tactical_transition_guidance import (
    tactical_transition_king_penalty as _tactical_transition_king_penalty,
)
from chess_game.chess.defensive_containment_guidance import (
    heavy_piece_defense_evaluation_score as _heavy_piece_defense_evaluation_score,
)
from chess_game.chess.endgame_emergency_defense import (
    defensive_king_danger_evaluation_score as _defensive_king_danger_evaluation_score,
    endgame_holdability_evaluation_score as _endgame_holdability_evaluation_score,
)
from chess_game.chess.pieces.piece_movers import PieceMovers
from chess_game.chess.review_loop_guidance import review_loop_evaluation_score
from chess_game.chess.simple_endgame_guidance import simple_endgame_evaluation_score
from chess_game.chess.strategy_utils import (
    file_pawn_state as _file_pawn_state,
    iter_king_squares as _iter_king_squares,
    path_clear_between as _path_clear_between,
    scale_signed as _scale_signed,
)
from chess_game.chess.evaluation_tables import (
    CENTER_FILES,
    CENTRAL_SQUARES,
    EXTENDED_CENTER_FILES,
    STARTING_NON_PAWN_MATERIAL,
)
from chess_game.chess.types import Color, Piece, PieceType

EvaluationBreakdown = dict[str, int]


def evaluate(board: Board, weights: EvalWeights | None = None) -> int:
    """Evaluate the board position from White's perspective."""

    return get_evaluation_breakdown(board, weights)["total"]


def get_evaluation_breakdown(
    board: Board,
    weights: EvalWeights | None = None,
) -> EvaluationBreakdown:
    """Return a debug-friendly breakdown of evaluation components."""

    if weights is None:
        weights = EvalWeights.default()

    middlegame_phase = _middlegame_phase(board, weights)
    endgame_phase = 100 - middlegame_phase
    material_score, piece_square_score = _evaluate_material_and_piece_square(board, weights)
    breakdown: EvaluationBreakdown = {
        "material": material_score,
        "piece_square": piece_square_score,
        "mobility": _evaluate_mobility(board, weights),
        "pawn_structure": _evaluate_pawn_structure(board, endgame_phase, weights),
        "king_safety": _evaluate_king_safety(board, middlegame_phase, weights),
        "king_exposure": _evaluate_king_exposure(board, middlegame_phase, weights),
        "defender_coordination": _evaluate_defender_coordination(board, middlegame_phase, weights),
        "rook_activity": _evaluate_rook_activity(board, weights),
        "bishop_pair": _evaluate_bishop_pair(board, weights),
        "minor_piece_activity": _evaluate_minor_piece_activity(board, weights),
        "space": _evaluate_space(board, middlegame_phase, weights),
        "endgame_technique": _evaluate_endgame_technique(board, endgame_phase, weights),
        "conversion": _evaluate_conversion(board, endgame_phase, weights),
        "progress": _evaluate_progress(board, endgame_phase, weights),
        "rook_endgame": _evaluate_rook_endgames(board, endgame_phase, weights),
        "heavy_piece_endgame": _evaluate_heavy_piece_endgames(board, endgame_phase, weights),
        "queen_vs_rook": _evaluate_queen_vs_rook(board, endgame_phase, weights),
        "passer_race": _evaluate_passer_races(board, endgame_phase, weights),
        "endgame_race": _evaluate_endgame_races(board, endgame_phase, weights),
        "low_material_coordination": _evaluate_low_material_coordination(
            board,
            endgame_phase,
            weights,
        ),
        "endgame_choice": _evaluate_endgame_choice(board),
        "defensive_containment": _heavy_piece_defense_evaluation_score(board),
        "defensive_king_danger": _defensive_king_danger_evaluation_score(board),
        "holdability": _endgame_holdability_evaluation_score(board),
        "middlegame_practicality": _middlegame_practicality_evaluation_score(board),
        "king_activation": (
            simple_endgame_evaluation_score(board) if endgame_phase >= 70 else 0
        ),
        "review_loop": review_loop_evaluation_score(board),
        "development": _evaluate_development(board, middlegame_phase, weights),
    }
    eval_only = {"endgame_race", "middlegame_practicality"}
    breakdown["total"] = sum(v for k, v in breakdown.items() if k not in eval_only)
    return breakdown


def _evaluate_material_and_piece_square(
    board: Board,
    weights: EvalWeights,
) -> tuple[int, int]:
    material_score = 0
    piece_square_score = 0
    material_dict = weights.material.as_dict()
    for piece, row, col in _iter_board_pieces(board):
        sign = _color_sign(piece.color)
        # King is not tunable material; only non-king pieces are in material_dict
        if piece.kind != PieceType.KING:
            material_score += sign * material_dict[piece.kind]
        piece_square_score += sign * _piece_square_value(piece, row, col, weights)
    return material_score, piece_square_score


def _iter_board_pieces(board: Board) -> Iterator[tuple[Piece, int, int]]:
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


def _piece_square_value(piece: Piece, row: int, col: int, weights: EvalWeights) -> int:
    mirrored_row = _mirror_row_for_color(piece.color, row)
    t = weights.tables
    if piece.kind == PieceType.PAWN:
        return t.pawn_table[mirrored_row][col]
    if piece.kind == PieceType.KNIGHT:
        return t.knight_table[mirrored_row][col]
    if piece.kind == PieceType.BISHOP:
        return t.bishop_table[mirrored_row][col]
    if piece.kind == PieceType.ROOK:
        return t.rook_table[mirrored_row][col]
    if piece.kind == PieceType.QUEEN:
        return t.queen_table[mirrored_row][col]
    return t.king_table[mirrored_row][col]


def _evaluate_mobility(board: Board, weights: EvalWeights) -> int:
    mobility_weights = weights.pieces.mobility_weights()
    mobility_score = 0
    for piece, _, _ in _iter_board_pieces(board):
        weight = mobility_weights.get(piece.kind)
        if weight is None:
            continue
        move_count = len(PieceMovers.get_valid_moves(piece, board))
        mobility_score += _color_sign(piece.color) * move_count * weight
    return mobility_score


def _pawn_direction(color: Color) -> int:
    return -1 if color == Color.WHITE else 1


def _evaluate_king_safety(
    board: Board,
    middlegame_phase: int,
    weights: EvalWeights,
) -> int:
    if middlegame_phase == 0:
        return 0
    k = weights.king
    king_safety_score = 0
    for color in (Color.WHITE, Color.BLACK):
        king_square = _find_king(board, color)
        if king_square is None:
            continue
        color_score = 0
        attack_pressure = _king_zone_attack_pressure(board, color, king_square, weights)
        if _is_castled_king(color, king_square):
            color_score += k.castled_king_bonus
        color_score += _pawn_shield_score(board, color, king_square, weights)
        color_score -= _open_king_file_penalty(board, color, king_square, weights)
        color_score -= _unforced_shelter_loosening_penalty(
            board,
            color,
            king_square,
            attack_pressure,
            weights,
        )
        color_score -= _tactical_transition_king_penalty(board, color)
        color_score -= attack_pressure
        color_score -= _back_rank_tension(board, color, king_square, weights)
        if _is_exposed_central_king(king_square):
            color_score -= k.exposed_central_king_penalty
        king_safety_score += _color_sign(color) * color_score
    return _scale_signed(king_safety_score, middlegame_phase)


def _evaluate_king_exposure(
    board: Board,
    middlegame_phase: int,
    weights: EvalWeights,
) -> int:
    if middlegame_phase == 0:
        return 0
    k = weights.king
    score = 0
    queens_on_board = _queens_on_board(board)
    for color in (Color.WHITE, Color.BLACK):
        king_square = _find_king(board, color)
        if king_square is None:
            continue
        color_score = 0
        if queens_on_board and _is_exposed_central_king(king_square):
            color_score -= k.central_king_with_queens_penalty
        color_score -= _heavy_piece_lane_pressure(board, color, king_square, weights)
        color_score -= _h_pawn_exposure_penalty(board, color)
        score += _color_sign(color) * color_score
    return _scale_signed(score, middlegame_phase)


def _evaluate_defender_coordination(
    board: Board,
    middlegame_phase: int,
    weights: EvalWeights,
) -> int:
    if middlegame_phase == 0 or not _queens_on_board(board):
        return 0
    score = 0
    for color, king_square in _iter_king_squares(board):
        score += _color_sign(color) * (
            -_heavy_defender_distance_penalty(board, color, king_square, weights)
        )
    return _scale_signed(score, middlegame_phase)


def _middlegame_phase(board: Board, weights: EvalWeights) -> int:
    material_dict = weights.material.as_dict()
    non_pawn_material = 0
    for piece, _, _ in _iter_board_pieces(board):
        if piece.kind not in (PieceType.KING, PieceType.PAWN):
            non_pawn_material += material_dict[piece.kind]
    return min((non_pawn_material * 100) // STARTING_NON_PAWN_MATERIAL, 100)


def _find_king(board: Board, color: Color) -> ConstantSquare | None:
    for piece, _, _ in _iter_board_pieces(board):
        if (
            piece.color == color
            and piece.kind == PieceType.KING
            and isinstance(piece.square, ConstantSquare)
        ):
            return piece.square
    return None


def _is_castled_king(color: Color, square: ConstantSquare) -> bool:
    row = int(square.row)
    col = int(square.col)
    return (color == Color.WHITE and row == 7 and col in {2, 6}) or (
        color == Color.BLACK and row == 0 and col in {2, 6}
    )


def _pawn_shield_score(
    board: Board,
    color: Color,
    square: ConstantSquare,
    weights: EvalWeights,
) -> int:
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
            score += weights.king.pawn_shield_bonus
    return score


def _evaluate_endgame_choice(board: Board) -> int:
    if _has_rook(board):
        return 0
    if _non_king_piece_count(board) > 8:
        return 0
    white_profile = king_defense_profile(board, Color.WHITE)
    black_profile = king_defense_profile(board, Color.BLACK)
    white_score = white_profile.safe_king_moves + white_profile.king_zone_defenders
    black_score = black_profile.safe_king_moves + black_profile.king_zone_defenders
    return (white_score - black_score) * 2


def _has_rook(board: Board) -> bool:
    for row in board.board:
        for piece in row:
            if piece is not None and piece.kind == PieceType.ROOK:
                return True
    return False


def _non_king_piece_count(board: Board) -> int:
    count = 0
    for row in board.board:
        for piece in row:
            if piece is not None and piece.kind != PieceType.KING:
                count += 1
    return count


def _open_king_file_penalty(
    board: Board,
    color: Color,
    square: ConstantSquare,
    weights: EvalWeights,
) -> int:
    penalty = 0
    king_col = int(square.col)
    for file_index in range(max(0, king_col - 1), min(7, king_col + 1) + 1):
        if not _file_has_friendly_pawn(board, color, file_index):
            penalty += weights.king.open_king_file_penalty
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
    weights: EvalWeights,
) -> int:
    enemy_color = _opponent(color)
    king_row = int(square.row)
    king_col = int(square.col)
    kzap = weights.king.king_zone_attack_penalty
    penalty = 0
    for piece, row, col in _iter_color_pieces(board, enemy_color):
        distance = max(abs(row - king_row), abs(col - king_col))
        if distance > 2:
            continue
        if piece.kind == PieceType.QUEEN:
            penalty += kzap * 3
        elif piece.kind == PieceType.ROOK:
            penalty += kzap * 2
        elif piece.kind in (PieceType.BISHOP, PieceType.KNIGHT):
            penalty += kzap
    return penalty


def _back_rank_tension(
    board: Board,
    color: Color,
    square: ConstantSquare,
    weights: EvalWeights,
) -> int:
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
    return weights.king.back_rank_tension_penalty


def _is_exposed_central_king(square: ConstantSquare) -> bool:
    return int(square.col) in CENTER_FILES


def _queens_on_board(board: Board) -> bool:
    return any(piece.kind == PieceType.QUEEN for piece, _, _ in _iter_board_pieces(board))
def _heavy_piece_lane_pressure(
    board: Board,
    color: Color,
    square: ConstantSquare,
    weights: EvalWeights,
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
                penalty += weights.king.heavy_file_pressure_penalty
    return penalty


def _heavy_defender_distance_penalty(
    board: Board,
    color: Color,
    king_square: ConstantSquare,
    weights: EvalWeights,
) -> int:
    king_row = int(king_square.row)
    king_col = int(king_square.col)
    penalty = 0
    for piece, row, col in _iter_color_pieces(board, color):
        if piece.kind not in (PieceType.QUEEN, PieceType.ROOK):
            continue
        distance = max(abs(row - king_row), abs(col - king_col))
        if distance >= 4:
            penalty += weights.king.defender_distance_penalty
    return penalty


def _evaluate_rook_activity(board: Board, weights: EvalWeights) -> int:
    p = weights.pieces
    rook_activity_score = 0
    for piece, row, col in _iter_board_pieces(board):
        if piece.kind != PieceType.ROOK:
            continue
        color_score = 0
        file_state = _rook_file_state(board, piece.color, col)
        if file_state == "open":
            color_score += p.rook_open_file_bonus
        elif file_state == "semi-open":
            color_score += p.rook_semi_open_file_bonus
        if _rook_on_seventh_rank(piece.color, row):
            color_score += p.rook_seventh_rank_bonus
        if _rook_is_trapped(board, piece.color, row, col):
            color_score -= p.rook_trapped_penalty
        rook_activity_score += _color_sign(piece.color) * color_score
    for color in (Color.WHITE, Color.BLACK):
        rook_activity_score += _color_sign(color) * _connected_rooks_bonus(board, color, weights)
        rook_activity_score += _color_sign(color) * _queen_rook_battery_bonus(board, color, weights)
    return rook_activity_score


def _rook_file_state(board: Board, color: Color, file_index: int) -> str:
    return _file_pawn_state(board, color, file_index)


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


def _connected_rooks_bonus(board: Board, color: Color, weights: EvalWeights) -> int:
    rooks = _collect_piece_positions(board, color, PieceType.ROOK)
    if len(rooks) < 2:
        return 0
    row_a, col_a = rooks[0]
    row_b, col_b = rooks[1]
    if row_a != row_b and col_a != col_b:
        return 0
    if _path_clear_between(board, (row_a, col_a), (row_b, col_b)):
        return weights.pieces.connected_rooks_bonus
    return 0


def _queen_rook_battery_bonus(board: Board, color: Color, weights: EvalWeights) -> int:
    queens = _collect_piece_positions(board, color, PieceType.QUEEN)
    rooks = _collect_piece_positions(board, color, PieceType.ROOK)
    if len(queens) != 1 or not rooks:
        return 0
    queen_row, queen_col = queens[0]
    for rook_row, rook_col in rooks:
        if queen_row == rook_row or queen_col == rook_col:
            if _path_clear_between(board, (queen_row, queen_col), (rook_row, rook_col)):
                return weights.pieces.queen_rook_battery_bonus
    return 0


def _evaluate_bishop_pair(board: Board, weights: EvalWeights) -> int:
    bishop_counts = {Color.WHITE: 0, Color.BLACK: 0}
    for piece, _, _ in _iter_board_pieces(board):
        if piece.kind == PieceType.BISHOP:
            bishop_counts[piece.color] += 1
    bp = weights.pieces.bishop_pair_bonus
    return (
        (bp if bishop_counts[Color.WHITE] >= 2 else 0)
        - (bp if bishop_counts[Color.BLACK] >= 2 else 0)
    )


def _evaluate_minor_piece_activity(board: Board, weights: EvalWeights) -> int:
    pawn_positions = _collect_pawn_positions(board)
    score = 0
    for color in (Color.WHITE, Color.BLACK):
        sign = _color_sign(color)
        minor_squares: list[tuple[int, int]] = []
        for piece, row, col in _iter_color_pieces(board, color):
            if piece.kind == PieceType.KNIGHT:
                score += sign * _knight_activity_score(color, row, col, pawn_positions, weights)
                minor_squares.append((row, col))
            if piece.kind == PieceType.BISHOP:
                score += sign * _bishop_activity_score(
                    board, piece, (row, col), pawn_positions, weights
                )
                minor_squares.append((row, col))
        if _coordinated_minor_piece_setup(minor_squares):
            score += sign * weights.pieces.minor_coordination_bonus
    return score


def _knight_activity_score(
    color: Color,
    row: int,
    col: int,
    pawn_positions: dict[Color, list[tuple[int, int]]],
    weights: EvalWeights,
) -> int:
    p = weights.pieces
    friendly_pawns = pawn_positions[color]
    enemy_pawns = pawn_positions[_opponent(color)]
    score = 0
    if col in {0, 7}:
        score -= p.knight_rim_penalty
    if _occupies_central_square(row, col):
        score += p.central_minor_piece_bonus
    if _is_knight_outpost(color, row, col, friendly_pawns, enemy_pawns):
        score += p.knight_outpost_bonus
    elif _is_knight_strong_square(color, row, col, enemy_pawns):
        score += p.knight_strong_square_bonus
    return score


def _bishop_activity_score(
    board: Board,
    piece: Piece,
    square: tuple[int, int],
    pawn_positions: dict[Color, list[tuple[int, int]]],
    weights: EvalWeights,
) -> int:
    p = weights.pieces
    row, col = square
    friendly_pawns = pawn_positions[piece.color]
    score = 0
    mobility = len(PieceMovers.get_valid_moves(piece, board))
    bishop_color = (row + col) % 2
    same_color_pawns = sum(
        1 for pawn_row, pawn_col in friendly_pawns if (pawn_row + pawn_col) % 2 == bishop_color
    )
    score -= same_color_pawns * p.bad_bishop_pawn_penalty
    if mobility >= 7 and _on_long_diagonal(row, col):
        score += p.long_diagonal_bishop_bonus
    if _occupies_central_square(row, col):
        score += p.central_minor_piece_bonus
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


def _is_knight_strong_square(
    color: Color,
    row: int,
    col: int,
    enemy_pawns: list[tuple[int, int]],
) -> bool:
    """Return True when the knight occupies an advanced square no enemy pawn can
    attack, even without own pawn support."""
    advanced = row <= 3 if color == Color.WHITE else row >= 4
    if not advanced:
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


def _evaluate_space(board: Board, middlegame_phase: int, weights: EvalWeights) -> int:
    if middlegame_phase == 0:
        return 0
    white_space = _space_score_for_color(board, Color.WHITE, weights)
    black_space = _space_score_for_color(board, Color.BLACK, weights)
    return _scale_signed(white_space - black_space, middlegame_phase)


def _space_score_for_color(board: Board, color: Color, weights: EvalWeights) -> int:
    p = weights.pieces
    score = 0
    for piece, row, col in _iter_color_pieces(board, color):
        if piece.kind == PieceType.PAWN and _supports_space(color, row, col):
            score += p.space_advantage_bonus * 2
        elif piece.kind in (PieceType.KNIGHT, PieceType.BISHOP):
            if _piece_supports_space(color, row, col):
                score += p.space_advantage_bonus
    for piece, row, col in _iter_color_pieces(board, color):
        if piece.kind in (PieceType.KNIGHT, PieceType.BISHOP, PieceType.ROOK):
            if _is_cramped_piece(color, row, col):
                score -= p.cramped_piece_penalty
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


def _evaluate_development(
    board: Board,
    middlegame_phase: int,
    weights: EvalWeights,
) -> int:
    if middlegame_phase < 70:
        return 0
    d = weights.development
    development_score = 0
    for color in (Color.WHITE, Color.BLACK):
        sign = _color_sign(color)
        undeveloped = _undeveloped_minor_piece_count(board, color)
        development_score -= sign * undeveloped * d.undeveloped_minor_piece_penalty
        development_score += sign * _opening_central_control_bonus(board, color, weights)
        development_score += sign * _opening_piece_coordination_bonus(
            board, color, undeveloped, weights
        )
        development_score += sign * _opening_king_safety_score(board, color, undeveloped, weights)
        development_score -= sign * _opening_king_urgency_penalty(
            board, color, undeveloped, weights
        )
        development_score += sign * _opening_rook_connection_bonus(
            board, color, undeveloped, weights
        )
        development_score += sign * _opening_central_rook_bonus(board, color, undeveloped, weights)
        development_score += sign * _opening_queen_restraint_bonus(
            board, color, undeveloped, weights
        )
        development_score -= sign * _early_shelter_pawn_push_penalty(
            board, color, undeveloped, weights
        )
        if undeveloped >= 2 and _queen_left_home_square(board, color):
            development_score -= sign * d.early_queen_move_penalty
        development_score -= sign * _early_flank_queen_sortie_penalty(
            board, color, undeveloped, weights
        )
        development_score -= sign * _early_queen_raid_penalty(board, color, undeveloped, weights)
        if undeveloped >= 2 and _rook_left_home_square_early(board, color):
            development_score -= sign * d.early_rook_move_penalty
        development_score -= sign * _rook_home_rank_sidestep_penalty(
            board,
            color,
            undeveloped,
            weights,
        )
        development_score -= sign * _early_flank_pawn_poke_penalty(
            board, color, undeveloped, weights
        )
        development_score -= sign * _early_flank_raid_penalty(board, color, undeveloped, weights)
        development_score -= sign * _opening_wing_knight_lunge_penalty(
            board, color, undeveloped, weights
        )
        (
            kingside_lunge_penalty,
            rook_sidestep_penalty,
            rim_knight_penalty,
            edge_space_grab_penalty,
        ) = _opening_drift_penalties(board, color, undeveloped, weights)
        development_score -= sign * kingside_lunge_penalty
        development_score -= sign * rook_sidestep_penalty
        development_score -= sign * rim_knight_penalty
        development_score -= sign * edge_space_grab_penalty
        development_score -= sign * _middlegame_rim_knight_penalty(board, color, weights)
        development_score -= sign * _late_castling_urgency_penalty(board, color)
        development_score -= sign * _castling_path_blocked_penalty(board, color)
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


def _rook_home_rank_sidestep_penalty(
    board: Board,
    color: Color,
    undeveloped: int,
    weights: EvalWeights,
) -> int:
    if undeveloped < 1:
        return 0
    home_row = 7 if color == Color.WHITE else 0
    king_square = _find_king(board, color)
    if king_square is None or _is_castled_king(color, king_square):
        return 0
    sidestep_squares = {(home_row, 1), (home_row, 6)}
    penalty = 0
    d = weights.development
    for square in sidestep_squares:
        if _piece_on_square(board, color, PieceType.ROOK, square):
            penalty += d.early_rook_move_penalty + d.early_queen_move_penalty
    return penalty


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
