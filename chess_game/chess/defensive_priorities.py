"""Shared helpers for king-danger and defense-first move choices."""

from dataclasses import dataclass

from chess_game.chess.board import Board
from chess_game.chess.strategy_utils import (
    iter_color_pieces,
    king_coordinates,
    path_clear_between,
)
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
    safe_king_moves: int


def king_defense_profile(board: Board, color: Color) -> KingDefenseProfile:
    """Return the current defensive profile for one king."""

    return KingDefenseProfile(
        danger=king_danger_index(board, color),
        invasion_lines=open_heavy_invasion_lines(board, color),
        king_zone_defenders=_king_zone_defender_count(board, color),
        heavy_connections=_heavy_defender_connection_score(board, color),
        back_rank_weak=back_rank_is_weak(board, color),
        safe_king_moves=_safe_king_move_count(board, color),
    )


def king_danger_index(board: Board, color: Color) -> int:
    """Return a simple attack-pressure score around one king."""

    king_position = king_coordinates(board, color)
    if king_position is None:
        return 0
    king_row, king_col = king_position
    enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
    danger = _king_base_danger(board, color, king_row, king_col)
    enemy_queen_count, enemy_rook_count, proximity_danger, line_danger = _enemy_heavy_pressure(
        board,
        enemy_color,
        king_row,
        king_col,
    )
    danger += proximity_danger + line_danger
    danger += _heavy_invasion_adjustment(
        board,
        color,
        enemy_queen_count,
        enemy_rook_count,
        danger,
    )
    return danger


def _king_base_danger(
    board: Board,
    color: Color,
    king_row: int,
    king_col: int,
) -> int:
    danger = 0
    if _king_lacks_luft(board, color, king_row):
        danger += 1
    if _is_central_king(king_row, king_col) and _queens_remain(board):
        danger += 1
    if h_pawn_exposure_penalty(board, color) >= 30:
        danger += 2
    elif h_pawn_exposure_penalty(board, color) >= 15:
        danger += 1
    return danger


def _enemy_heavy_pressure(
    board: Board,
    enemy_color: Color,
    king_row: int,
    king_col: int,
) -> tuple[int, int, int, int]:
    enemy_queen_count = 0
    enemy_rook_count = 0
    proximity_danger = 0
    line_danger = 0
    for piece, row_index, col_index in iter_color_pieces(board, enemy_color):
        if piece.kind == PieceType.QUEEN:
            enemy_queen_count += 1
        if piece.kind == PieceType.ROOK:
            enemy_rook_count += 1
        if piece.kind in {PieceType.ROOK, PieceType.QUEEN} and (
            row_index == king_row or col_index == king_col
        ):
            if path_clear_between(board, (row_index, col_index), (king_row, king_col)):
                line_danger += 2
        distance = max(abs(row_index - king_row), abs(col_index - king_col))
        if piece.kind == PieceType.QUEEN and distance <= 3:
            proximity_danger += 2
        if piece.kind == PieceType.ROOK and distance <= 3:
            proximity_danger += 1
    return enemy_queen_count, enemy_rook_count, proximity_danger, line_danger


def _heavy_invasion_adjustment(
    board: Board,
    color: Color,
    enemy_queen_count: int,
    enemy_rook_count: int,
    current_danger: int,
) -> int:
    if enemy_queen_count == 0 or enemy_rook_count == 0 or current_danger < 3:
        return 0
    danger = 0
    invasion_lines = open_heavy_invasion_lines(board, color)
    if invasion_lines >= 2:
        danger += 2
    if invasion_lines > 0 and enemy_queen_count > 0 and enemy_rook_count > 0:
        danger += 1
    if king_needs_shelter(board, color) and enemy_queen_count + enemy_rook_count >= 2:
        danger += 1
    return danger


def king_needs_shelter(board: Board, color: Color) -> bool:
    """Return True when the king is still parked on a central home-rank square."""

    king_position = king_coordinates(board, color)
    home_row = 7 if color == Color.WHITE else 0
    return king_position is not None and king_position[0] == home_row and king_position[1] in {
        3,
        4,
        5,
    }


def back_rank_is_weak(board: Board, color: Color) -> bool:
    """Return True when the king lacks luft while enemy heavy pieces remain."""

    king_position = king_coordinates(board, color)
    if king_position is None or king_position[0] not in {0, 7}:
        return False
    enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
    return _king_lacks_luft(board, color, king_position[0]) and any(
        piece.kind in {PieceType.QUEEN, PieceType.ROOK}
        for piece, _, _ in iter_color_pieces(board, enemy_color)
    )


def open_heavy_invasion_lines(board: Board, color: Color) -> int:
    """Count enemy queen/rook lines that already point straight at the king."""

    king_position = king_coordinates(board, color)
    if king_position is None:
        return 0
    king_row, king_col = king_position
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

    king_position = king_coordinates(board, color)
    if king_position is None:
        return 0
    king_row, king_col = king_position
    return sum(
        1
        for piece, row_index, col_index in iter_color_pieces(board, color)
        if piece.kind != PieceType.KING
        and max(abs(row_index - king_row), abs(col_index - king_col)) <= 2
    )


def _heavy_defender_connection_score(board: Board, color: Color) -> int:
    """Count queen/rook defenders that stay connected to the king's file or rank."""

    king_position = king_coordinates(board, color)
    if king_position is None:
        return 0
    king_row, king_col = king_position
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


def _safe_king_move_count(board: Board, color: Color) -> int:
    """Count the legal king moves currently available to the side being defended."""

    king_position = king_coordinates(board, color)
    if king_position is None:
        return 0
    temp_board = board.clone()
    temp_board.turn = color
    king_square = temp_board.find_king(color)
    if king_square is None:
        return 0
    return len(temp_board.get_legal_moves(king_square))


def h_pawn_exposure_penalty(board: Board, color: Color) -> int:
    """Return a penalty when the h-pawn shelter is absent and an enemy piece threatens h2/h7.

    The classic Bxh2+ sacrifice only works when:
    1. The king has castled kingside (at g1/g8).
    2. The h-pawn is still on its home square (h2/h7) — if it has advanced, the
       king may already have luft; if it was captured, the weakness is structural.
    3. An enemy bishop or queen has a clear or near-clear diagonal to h2/h7.

    The penalty is 30 cp per threatening piece and scales with how clear the
    diagonal is (0 pieces in the way = full penalty, 1 piece = half).
    """

    king_pos = king_coordinates(board, color)
    if king_pos is None:
        return 0
    king_row, king_col = king_pos
    home_row = 7 if color == Color.WHITE else 0
    if king_row != home_row or king_col != 6:
        return 0
    if not _queens_remain(board):
        return 0
    h_col = 7
    h_row = home_row - 1 if color == Color.WHITE else home_row + 1
    h_piece = board.board[h_row][h_col]
    if h_piece is None or h_piece.color != color or h_piece.kind != PieceType.PAWN:
        return 0
    enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
    penalty = 0
    for piece, row, col in iter_color_pieces(board, enemy_color):
        if piece.kind not in {PieceType.BISHOP, PieceType.QUEEN}:
            continue
        d_row = h_row - row
        d_col = h_col - col
        if abs(d_row) != abs(d_col) or d_row == 0:
            continue
        step_r = 1 if h_row > row else -1
        step_c = 1 if h_col > col else -1
        blockers = 0
        r, c = row + step_r, col + step_c
        while (r, c) != (h_row, h_col):
            if board.board[r][c] is not None:
                blockers += 1
            r += step_r
            c += step_c
        if blockers == 0:
            penalty += 30
        elif blockers == 1:
            penalty += 15
    return penalty


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
