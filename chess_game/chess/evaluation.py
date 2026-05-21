"""Position evaluation tables and heuristics for the chess AI."""

from __future__ import annotations

from chess_game.chess.board import Board
from chess_game.chess.constants import ConstantSquare, get_col_constant, get_row_constant
from chess_game.chess.pieces.piece_movers import PieceMovers
from chess_game.chess.types import Color, Piece, PieceType

MATERIAL_VALUES: dict[PieceType, int] = {
    PieceType.PAWN: 100,
    PieceType.KNIGHT: 320,
    PieceType.BISHOP: 330,
    PieceType.ROOK: 500,
    PieceType.QUEEN: 900,
    PieceType.KING: 20_000,
}

PAWN_TABLE: list[list[int]] = [
    [-8, -8, -8, -8, -8, -8, -8, -8],
    [-1, -1, -1, -1, -1, -1, -1, -1],
    [1, 2, 1, 3, 2, 3, 1, 2],
    [2, 3, 1, 2, 2, 2, 1, 2],
    [2, 3, 1, 2, 3, 1, 2, 2],
    [1, 1, 2, 1, 2, 1, 1, 0],
    [-1, 0, 0, 0, 0, 0, 0, -1],
    [-8, -8, -8, -8, -8, -8, -8, -8],
]

KNIGHT_TABLE: list[list[int]] = [
    [-3, -2, -1, 0, 0, -1, -2, -3],
    [-2, 0, 1, 1, 1, 1, 0, -2],
    [-1, 1, 3, 3, 3, 3, 1, -1],
    [0, 1, 4, 4, 4, 4, 1, 0],
    [0, 2, 4, 4, 4, 4, 2, 0],
    [0, 1, 3, 4, 4, 3, 1, 0],
    [-2, 0, 2, 3, 3, 2, 0, -2],
    [-3, -2, -1, 0, 0, -1, -2, -3],
]

BISHOP_TABLE: list[list[int]] = [
    [-5, -4, -3, -2, -2, -3, -4, -5],
    [-3, -2, 1, 2, 2, 1, -2, -3],
    [2, 2, 1, 1, 1, 1, 2, 2],
    [2, 3, 1, 5, 5, 1, 3, 2],
    [0, 1, 2, 2, 2, 2, 1, 0],
    [-2, 2, 3, 4, 4, 3, 2, -2],
    [-3, 2, 3, 4, 4, 3, 2, -3],
    [-5, -4, -3, -2, -2, -3, -4, -5],
]

ROOK_TABLE: list[list[int]] = [
    [-3, -3, -3, -3, -3, -3, -3, -3],
    [-2, -2, -1, -1, -1, -1, -2, -2],
    [-1, -1, 1, 3, 4, 3, -1, -1],
    [-2, 1, 3, 7, 7, 3, 1, -2],
    [-1, 2, 5, 8, 8, 5, 2, -1],
    [2, 3, 6, 9, 9, 6, 3, 2],
    [4, 1, 4, 2, 2, 4, 1, 5],
    [-3, -3, -3, -3, -3, -3, -3, -3],
]

QUEEN_TABLE: list[list[int]] = [
    [-2, 1, 2, 2, 2, 2, 1, -2],
    [-3, -2, 2, 4, 4, 2, -2, -3],
    [0, 0, 2, 3, 6, 3, 2, 0],
    [-5, 1, 3, 5, 8, 8, 3, 1],
    [1, 4, 7, 9, 10, 9, 7, 4],
    [-2, 5, 8, 8, 8, 8, 5, -2],
    [-2, 1, 3, 5, 6, 5, 3, -2],
    [-3, -4, -2, -2, -2, -2, -4, -3],
]

KING_TABLE: list[list[int]] = [
    [-8, -7, -6, -4, -2, 0, 1, 3],
    [-7, -6, -4, -2, -1, 1, 2, 3],
    [-7, -5, 0, 2, 5, 5, 2, 5],
    [2, 2, 3, 4, 4, 4, 2, 2],
    [2, 3, 3, 5, 6, 5, 3, 2],
    [-4, -3, -1, 0, 0, 0, -1, -3],
    [-6, -5, -3, -2, -1, 0, -2, -4],
    [-9, -8, -6, -5, -4, -3, -4, -7],
]

STARTING_NON_PAWN_MATERIAL = 6_400
ISOLATED_PAWN_PENALTY = 12
DOUBLED_PAWN_PENALTY = 10
BACKWARD_PAWN_PENALTY = 8
CONNECTED_PASSED_PAWN_BONUS = 10
BISHOP_PAIR_BONUS = 28
ROOK_OPEN_FILE_BONUS = 18
ROOK_SEMI_OPEN_FILE_BONUS = 10
ROOK_SEVENTH_RANK_BONUS = 12
CASTLED_KING_BONUS = 22
PAWN_SHIELD_BONUS = 7
OPEN_KING_FILE_PENALTY = 9
EXPOSED_CENTRAL_KING_PENALTY = 16
EARLY_QUEEN_MOVE_PENALTY = 10
EARLY_ROOK_MOVE_PENALTY = 7
UNDEVELOPED_MINOR_PIECE_PENALTY = 5

PASSED_PAWN_BONUS_BY_PROGRESS = {
    0: 0,
    1: 6,
    2: 12,
    3: 20,
    4: 32,
    5: 50,
    6: 80,
}

MOBILITY_WEIGHTS = {
    PieceType.KNIGHT: 4,
    PieceType.BISHOP: 4,
}

EvaluationBreakdown = dict[str, int]


def evaluate(board: Board) -> int:
    """Evaluate the board position from White's perspective."""

    return get_evaluation_breakdown(board)["total"]


def get_evaluation_breakdown(board: Board) -> EvaluationBreakdown:
    """Return a debug-friendly breakdown of evaluation components."""

    material_score, piece_square_score = _evaluate_material_and_piece_square(board)
    breakdown: EvaluationBreakdown = {
        "material": material_score,
        "piece_square": piece_square_score,
        "mobility": _evaluate_mobility(board),
        "pawn_structure": _evaluate_pawn_structure(board),
        "king_safety": _evaluate_king_safety(board),
        "rook_activity": _evaluate_rook_activity(board),
        "bishop_pair": _evaluate_bishop_pair(board),
        "development": _evaluate_development(board),
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
        if piece.kind == PieceType.QUEEN:
            move_count = min(move_count, 12)
        mobility_score += _color_sign(piece.color) * move_count * weight
    return mobility_score


def _evaluate_pawn_structure(board: Board) -> int:
    pawn_positions = _collect_pawn_positions(board)
    pawn_structure_score = 0
    for color in (Color.WHITE, Color.BLACK):
        sign = _color_sign(color)
        color_positions = pawn_positions[color]
        file_map = _group_rows_by_file(color_positions)
        enemy_positions = pawn_positions[_opponent(color)]
        passed_pawns: set[tuple[int, int]] = set()
        for row, col in color_positions:
            pawn_structure_score -= sign * _pawn_file_penalty(file_map, col)
            pawn_position = (row, col)
            if _is_backward_pawn(
                board, color, pawn_position, file_map, enemy_positions
            ):
                pawn_structure_score -= sign * BACKWARD_PAWN_PENALTY
            if _is_passed_pawn(color, row, col, enemy_positions):
                progress = _pawn_progress(color, row)
                pawn_structure_score += sign * PASSED_PAWN_BONUS_BY_PROGRESS[progress]
                passed_pawns.add((row, col))
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


def _is_passed_pawn(
    color: Color,
    row: int,
    col: int,
    enemy_positions: list[tuple[int, int]],
) -> bool:
    for enemy_row, enemy_col in enemy_positions:
        if abs(enemy_col - col) > 1:
            continue
        if color == Color.WHITE and enemy_row < row:
            return False
        if color == Color.BLACK and enemy_row > row:
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


def _pawn_progress(color: Color, row: int) -> int:
    return 6 - row if color == Color.WHITE else row - 1


def _pawn_direction(color: Color) -> int:
    return -1 if color == Color.WHITE else 1


def _evaluate_king_safety(board: Board) -> int:
    middlegame_phase = _middlegame_phase(board)
    if middlegame_phase == 0:
        return 0
    king_safety_score = 0
    for color in (Color.WHITE, Color.BLACK):
        king_square = _find_king(board, color)
        if king_square is None:
            continue
        color_score = 0
        if _is_castled_king(color, king_square):
            color_score += CASTLED_KING_BONUS
        color_score += _pawn_shield_score(board, color, king_square)
        color_score -= _open_king_file_penalty(board, color, king_square)
        if _is_exposed_central_king(king_square):
            color_score -= EXPOSED_CENTRAL_KING_PENALTY
        king_safety_score += _color_sign(color) * color_score
    return (king_safety_score * middlegame_phase) // 100


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


def _is_exposed_central_king(square: ConstantSquare) -> bool:
    return int(square.col) in {3, 4}


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
        rook_activity_score += _color_sign(piece.color) * color_score
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


def _evaluate_bishop_pair(board: Board) -> int:
    bishop_counts = {Color.WHITE: 0, Color.BLACK: 0}
    for piece, _, _ in _iter_board_pieces(board):
        if piece.kind == PieceType.BISHOP:
            bishop_counts[piece.color] += 1
    return (
        (BISHOP_PAIR_BONUS if bishop_counts[Color.WHITE] >= 2 else 0)
        - (BISHOP_PAIR_BONUS if bishop_counts[Color.BLACK] >= 2 else 0)
    )


def _evaluate_development(board: Board) -> int:
    middlegame_phase = _middlegame_phase(board)
    if middlegame_phase < 70:
        return 0
    development_score = 0
    for color in (Color.WHITE, Color.BLACK):
        sign = _color_sign(color)
        undeveloped = _undeveloped_minor_piece_count(board, color)
        development_score -= sign * undeveloped * UNDEVELOPED_MINOR_PIECE_PENALTY
        if undeveloped >= 2 and _queen_left_home_square(board, color):
            development_score -= sign * EARLY_QUEEN_MOVE_PENALTY
        if undeveloped >= 2 and _rook_left_home_square_early(board, color):
            development_score -= sign * EARLY_ROOK_MOVE_PENALTY
    return (development_score * middlegame_phase) // 100


def _undeveloped_minor_piece_count(board: Board, color: Color) -> int:
    starting_squares = {
        Color.WHITE: {
            PieceType.KNIGHT: {(7, 1), (7, 6)},
            PieceType.BISHOP: {(7, 2), (7, 5)},
        },
        Color.BLACK: {
            PieceType.KNIGHT: {(0, 1), (0, 6)},
            PieceType.BISHOP: {(0, 2), (0, 5)},
        },
    }
    undeveloped = 0
    for piece, row, col in _iter_board_pieces(board):
        piece_squares = starting_squares[color].get(piece.kind)
        if piece.color == color and piece_squares is not None and (row, col) in piece_squares:
            undeveloped += 1
    return undeveloped


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
