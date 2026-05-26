"""Guidance for practical heavy-piece defense against dangerous enemy passers."""

from chess_game.chess.board import Board
from chess_game.chess.board.attack_utils import piece_attacks_square
from chess_game.chess.constants import get_square_constant
from chess_game.chess.move import Move
from chess_game.chess.strategy_utils import (
    is_advanced_passer,
    iter_color_pieces,
    materially_behind_color,
    opposite_color,
    passed_pawns_for_color,
)
from chess_game.chess.types import Color, PieceType

_ROOT_SCALE = 6
_EVAL_SCALE = 4
_PASSER_NEUTRALIZED_SCORE = 100
_BLOCKADE_BONUS = 20
_CAPTURE_PRESSURE_BONUS = 18
_PROMOTION_CONTROL_BONUS = 14
_FILE_CONTEST_BONUS = 10
_KING_DISTANCE_BONUS = 4


def heavy_piece_defense_evaluation_score(board: Board) -> int:
    """Return a signed score for practical heavy-piece passer containment."""

    trailing_color = materially_behind_color(board)
    if trailing_color is None or not _has_heavy_piece_context(board):
        return 0
    enemy_color = opposite_color(trailing_color)
    dangerous_pawn = _most_dangerous_advanced_passer(board, enemy_color)
    if dangerous_pawn is None:
        return 0
    return _color_sign(trailing_color) * _containment_score(
        board, trailing_color, dangerous_pawn
    ) * _EVAL_SCALE


def heavy_piece_defense_root_bonus(board: Board, child_board: Board, color: Color) -> int:
    """Return a root-only bonus for practical passer containment while worse."""

    if materially_behind_color(board) != color or not _has_heavy_piece_context(board):
        return 0
    enemy_color = opposite_color(color)
    dangerous_before = _most_dangerous_advanced_passer(board, enemy_color)
    if dangerous_before is None:
        return 0
    before = _containment_score(board, color, dangerous_before)
    after = _containment_score(
        child_board,
        color,
        _most_dangerous_advanced_passer(child_board, enemy_color),
    )
    return (after - before) * _ROOT_SCALE


def heavy_piece_defense_extension_bonus(
    board: Board,
    move: Move,
    child_board: Board,
    color: Color,
) -> int:
    """Return 1 when a move deserves a narrow containment extension."""

    if materially_behind_color(board) != color or not _has_heavy_piece_context(board):
        return 0
    enemy_color = opposite_color(color)
    dangerous_pawn = _most_dangerous_advanced_passer(board, enemy_color)
    if dangerous_pawn is None:
        return 0
    if _move_neutralizes_passer(board, move, child_board, color, dangerous_pawn):
        return 1
    return 0


def _has_heavy_piece_context(board: Board) -> bool:
    heavy_piece_count = 0
    for piece, _, _ in iter_color_pieces(board, Color.WHITE):
        if piece.kind in {PieceType.ROOK, PieceType.QUEEN}:
            heavy_piece_count += 1
    for piece, _, _ in iter_color_pieces(board, Color.BLACK):
        if piece.kind in {PieceType.ROOK, PieceType.QUEEN}:
            heavy_piece_count += 1
    return heavy_piece_count >= 2


def _most_dangerous_advanced_passer(
    board: Board, color: Color
) -> tuple[int, int] | None:
    advanced_passers = [
        pawn
        for pawn in passed_pawns_for_color(board, color)
        if is_advanced_passer(color, pawn[0]) and _is_critical_passer(color, pawn[0])
    ]
    if not advanced_passers:
        return None
    if color == Color.WHITE:
        return min(advanced_passers, key=lambda pawn: pawn[0])
    return max(advanced_passers, key=lambda pawn: pawn[0])


def _containment_score(
    board: Board,
    color: Color,
    dangerous_pawn: tuple[int, int] | None,
) -> int:
    if dangerous_pawn is None:
        return _PASSER_NEUTRALIZED_SCORE
    enemy_color = opposite_color(color)
    pawn_row, pawn_col = dangerous_pawn
    pawn_square = get_square_constant(pawn_row, pawn_col)
    promotion_row = 0 if enemy_color == Color.WHITE else 7
    promotion_square = get_square_constant(promotion_row, pawn_col)
    block_square = _block_square(enemy_color, dangerous_pawn)
    score = _blockade_score(board, color, block_square)
    score += _heavy_piece_pressure_score(board, color, pawn_square, promotion_square, pawn_col)
    score += _king_distance_score(board, color, block_square)
    return score


def _blockade_score(board: Board, color: Color, block_square: tuple[int, int]) -> int:
    block_row, block_col = block_square
    if not 0 <= block_row < 8:
        return 0
    occupant = board.board[block_row][block_col]
    if occupant is None or occupant.color != color:
        return 0
    if occupant.kind in {PieceType.KING, PieceType.ROOK, PieceType.QUEEN}:
        return _BLOCKADE_BONUS
    return _BLOCKADE_BONUS // 2


def _heavy_piece_pressure_score(
    board: Board,
    color: Color,
    pawn_square,
    promotion_square,
    pawn_col: int,
) -> int:
    score = 0
    for piece, _, col in iter_color_pieces(board, color):
        if piece.kind not in {PieceType.ROOK, PieceType.QUEEN}:
            continue
        if piece_attacks_square(piece, piece.square, pawn_square, board):
            score += _CAPTURE_PRESSURE_BONUS
        if piece_attacks_square(piece, piece.square, promotion_square, board):
            score += _PROMOTION_CONTROL_BONUS
        if col == pawn_col:
            score += _FILE_CONTEST_BONUS
    return score


def _king_distance_score(board: Board, color: Color, block_square: tuple[int, int]) -> int:
    own_king = board.find_king(color)
    if own_king is None:
        return 0
    distance = abs(int(own_king.row) - block_square[0]) + abs(int(own_king.col) - block_square[1])
    return max(0, 6 - distance) * _KING_DISTANCE_BONUS


def _block_square(enemy_color: Color, dangerous_pawn: tuple[int, int]) -> tuple[int, int]:
    pawn_row, pawn_col = dangerous_pawn
    direction = -1 if enemy_color == Color.WHITE else 1
    return pawn_row + direction, pawn_col


def _is_critical_passer(color: Color, row: int) -> bool:
    return row <= 1 if color == Color.WHITE else row >= 6


def _move_neutralizes_passer(
    board: Board,
    move: Move,
    child_board: Board,
    color: Color,
    dangerous_pawn: tuple[int, int],
) -> bool:
    enemy_color = opposite_color(color)
    moving_piece = board.get_piece(move.start)
    if moving_piece is None or moving_piece.kind not in {
        PieceType.ROOK,
        PieceType.QUEEN,
        PieceType.KING,
    }:
        return False
    if _most_dangerous_advanced_passer(child_board, enemy_color) is None:
        return True
    return (
        (int(move.end.row), int(move.end.col)) == _block_square(enemy_color, dangerous_pawn)
        or int(move.end.col) == dangerous_pawn[1]
    )


def _color_sign(color: Color) -> int:
    return 1 if color == Color.WHITE else -1
