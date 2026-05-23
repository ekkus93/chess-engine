"""Shared helpers for strategic evaluation and move ordering."""

from chess_game.chess.board import Board
from chess_game.chess.move import Move
from chess_game.chess.constants import ConstantSquare
from chess_game.chess.types import Color, PieceType


def iter_board_pieces(board: Board):
    """Yield all occupied squares as piece, row, col triples."""

    for row_index, row in enumerate(board.board):
        for col_index, piece in enumerate(row):
            if piece is not None:
                yield piece, row_index, col_index


def iter_color_pieces(board: Board, color: Color):
    """Yield occupied squares for one color."""

    for piece, row, col in iter_board_pieces(board):
        if piece.color == color:
            yield piece, row, col


def iter_king_squares(board: Board):
    """Yield king squares as color, square pairs."""

    for piece, _, _ in iter_board_pieces(board):
        if piece.kind == PieceType.KING and isinstance(piece.square, ConstantSquare):
            yield piece.color, piece.square


def king_coordinates(board: Board, color: Color) -> tuple[int, int] | None:
    """Return a king's board coordinates, or None when that king is absent."""

    king_square = board.find_king(color)
    if king_square is None:
        return None
    return int(king_square.row), int(king_square.col)


def center_distance(row: int, col: int) -> int:
    """Return a simple Manhattan distance to the board center."""

    return min(
        abs(row - 3) + abs(col - 3),
        abs(row - 3) + abs(col - 4),
        abs(row - 4) + abs(col - 3),
        abs(row - 4) + abs(col - 4),
    )


def is_passed_pawn(
    color: Color,
    row: int,
    col: int,
    enemy_positions: list[tuple[int, int]],
) -> bool:
    """Return True when no opposing pawn can stop the pawn on adjacent files."""

    for enemy_row, enemy_col in enemy_positions:
        if abs(enemy_col - col) > 1:
            continue
        if color == Color.WHITE and enemy_row < row:
            return False
        if color == Color.BLACK and enemy_row > row:
            return False
    return True


def path_clear_between(
    board: Board,
    start: tuple[int, int],
    end: tuple[int, int],
) -> bool:
    """Return True when squares between start and end are empty."""

    row_step = 0 if start[0] == end[0] else (1 if end[0] > start[0] else -1)
    col_step = 0 if start[1] == end[1] else (1 if end[1] > start[1] else -1)
    current_row = start[0] + row_step
    current_col = start[1] + col_step
    while (current_row, current_col) != end:
        if board.board[current_row][current_col] is not None:
            return False
        current_row += row_step
        current_col += col_step
    return True


def is_capture_move(board: Board, move: Move) -> bool:
    """Return True for regular captures and en passant."""

    if board.get_piece(move.end) is not None:
        return True
    moving_piece = board.get_piece(move.start)
    return (
        moving_piece is not None
        and moving_piece.kind == PieceType.PAWN
        and board.en_passant_target == move.end
        and move.start.col != move.end.col
    )


def file_pawn_state(board: Board, color: Color, file_index: int) -> str:
    """Return whether a file is open, semi-open, or closed for one side."""

    has_friendly_pawn = False
    has_enemy_pawn = False
    enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
    for rank_index in range(8):
        piece = board.board[rank_index][file_index]
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


def scale_signed(value: int, factor: int) -> int:
    """Scale a signed value by a percentage without floor-bias asymmetry."""

    sign = 1 if value >= 0 else -1
    return sign * ((abs(value) * factor) // 100)
