"""Shared helpers for king-danger and defense-first move choices."""

from dataclasses import dataclass

from chess_game.chess.board import Board
from chess_game.chess.strategy_utils import iter_color_pieces, path_clear_between
from chess_game.chess.types import Color, PieceType

DANGEROUS_KING_PRESSURE_THRESHOLD = 3


@dataclass(frozen=True)
class KingDefenseProfile:
    """Lightweight summary of how safe one king currently is."""

    danger: int
    invasion_lines: int
    king_zone_defenders: int
    heavy_connections: int
    back_rank_weak: bool


def king_defense_profile(board: Board, color: Color) -> KingDefenseProfile:
    """Return the current defensive profile for one king."""

    return KingDefenseProfile(
        danger=king_danger_index(board, color),
        invasion_lines=_open_heavy_invasion_lines(board, color),
        king_zone_defenders=_king_zone_defender_count(board, color),
        heavy_connections=_heavy_defender_connection_score(board, color),
        back_rank_weak=back_rank_is_weak(board, color),
    )


def king_danger_index(board: Board, color: Color) -> int:
    """Return a simple attack-pressure score around one king."""

    king_square = board.find_king(color)
    if king_square is None:
        return 0
    king_row = int(king_square.row)
    king_col = int(king_square.col)
    enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
    danger = 0
    if _king_lacks_luft(board, color, king_row):
        danger += 1
    if _is_central_king(king_row, king_col) and _queens_remain(board):
        danger += 1
    for piece, row_index, col_index in iter_color_pieces(board, enemy_color):
        if piece.kind in {PieceType.ROOK, PieceType.QUEEN} and (
            row_index == king_row or col_index == king_col
        ):
            if path_clear_between(board, (row_index, col_index), (king_row, king_col)):
                danger += 2
        distance = max(abs(row_index - king_row), abs(col_index - king_col))
        if piece.kind == PieceType.QUEEN and distance <= 3:
            danger += 2
        if piece.kind == PieceType.ROOK and distance <= 3:
            danger += 1
    return danger


def king_needs_shelter(board: Board, color: Color) -> bool:
    """Return True when the king is still parked on a central home-rank square."""

    king_square = board.find_king(color)
    home_row = 7 if color == Color.WHITE else 0
    return king_square is not None and int(king_square.row) == home_row and int(
        king_square.col
    ) in {3, 4, 5}


def back_rank_is_weak(board: Board, color: Color) -> bool:
    """Return True when the king lacks luft while enemy heavy pieces remain."""

    king_square = board.find_king(color)
    if king_square is None or int(king_square.row) not in {0, 7}:
        return False
    enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
    return _king_lacks_luft(board, color, int(king_square.row)) and any(
        piece.kind in {PieceType.QUEEN, PieceType.ROOK}
        for piece, _, _ in iter_color_pieces(board, enemy_color)
    )


def _open_heavy_invasion_lines(board: Board, color: Color) -> int:
    """Count enemy queen/rook lines that already point straight at the king."""

    king_square = board.find_king(color)
    if king_square is None:
        return 0
    king_row = int(king_square.row)
    king_col = int(king_square.col)
    enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
    return sum(
        1
        for piece, row_index, col_index in iter_color_pieces(board, enemy_color)
        if piece.kind in {PieceType.QUEEN, PieceType.ROOK}
        and (row_index == king_row or col_index == king_col)
        and path_clear_between(board, (row_index, col_index), (king_row, king_col))
    )


def _king_zone_defender_count(board: Board, color: Color) -> int:
    """Count friendly non-king pieces actively covering the king's zone."""

    king_square = board.find_king(color)
    if king_square is None:
        return 0
    king_row = int(king_square.row)
    king_col = int(king_square.col)
    return sum(
        1
        for piece, row_index, col_index in iter_color_pieces(board, color)
        if piece.kind != PieceType.KING
        and max(abs(row_index - king_row), abs(col_index - king_col)) <= 2
    )


def _heavy_defender_connection_score(board: Board, color: Color) -> int:
    """Count queen/rook defenders that stay connected to the king's file or rank."""

    king_square = board.find_king(color)
    if king_square is None:
        return 0
    king_row = int(king_square.row)
    king_col = int(king_square.col)
    score = 0
    for piece, row_index, col_index in iter_color_pieces(board, color):
        if piece.kind not in {PieceType.QUEEN, PieceType.ROOK}:
            continue
        if max(abs(row_index - king_row), abs(col_index - king_col)) <= 2:
            score += 1
            continue
        if (row_index == king_row or col_index == king_col) and path_clear_between(
            board,
            (row_index, col_index),
            (king_row, king_col),
        ):
            score += 1
    return score


def _king_lacks_luft(board: Board, color: Color, king_row: int) -> bool:
    """Return True when the king sits on the home rank without a pawn escape square."""

    luft_row = 5 if color == Color.WHITE else 2
    home_row = 7 if color == Color.WHITE else 0
    if king_row != home_row:
        return False
    return not any(
        piece.kind == PieceType.PAWN and row_index == luft_row
        for piece, row_index, _ in iter_color_pieces(board, color)
    )


def _is_central_king(king_row: int, king_col: int) -> bool:
    """Return True when the king is not tucked near an edge."""

    return king_row in {2, 3, 4, 5} and king_col in {2, 3, 4, 5}


def _queens_remain(board: Board) -> bool:
    """Return True when at least one queen is still on the board."""

    return any(piece.kind == PieceType.QUEEN for row in board.board for piece in row if piece)
