"""Shared helpers for strategic evaluation and move ordering."""

from chess_game.chess.board import Board
from chess_game.chess.constants import ConstantSquare, get_col_constant, get_row_constant
from chess_game.chess.evaluation_tables import MATERIAL_VALUES
from chess_game.chess.move import Move
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


def legal_move_count(board: Board, color: Color) -> int:
    """Return the total number of legal moves for one side."""

    temp_board = board.clone()
    temp_board.turn = color
    return sum(
        len(temp_board.get_legal_moves(piece.square))
        for piece, _, _ in iter_color_pieces(temp_board, color)
    )


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


def is_castled_king(color: Color, square: ConstantSquare) -> bool:
    """Return True when a king occupies a standard castled square."""

    row = int(square.row)
    col = int(square.col)
    return (color == Color.WHITE and row == 7 and col in {2, 6}) or (
        color == Color.BLACK and row == 0 and col in {2, 6}
    )


def both_queens_on_board(board: Board) -> bool:
    """Return True when both sides still have their queens."""

    white_queen = False
    black_queen = False
    for row in board.board:
        for piece in row:
            if piece is None or piece.kind != PieceType.QUEEN:
                continue
            if piece.color == Color.WHITE:
                white_queen = True
            else:
                black_queen = True
            if white_queen and black_queen:
                return True
    return False


def exposed_shield_files(board: Board, color: Color, king_col: int) -> list[int]:
    """Return king-adjacent files missing both the home and advanced shield pawn."""

    exposed_files: list[int] = []
    for file_index in _king_shield_files(king_col):
        has_home_pawn, has_advanced_pawn = shield_pawn_support_state(board, color, file_index)
        if has_home_pawn or has_advanced_pawn:
            continue
        exposed_files.append(file_index)
    return exposed_files


def shield_pawn_support_state(board: Board, color: Color, file_index: int) -> tuple[bool, bool]:
    """Return whether a file still has its home or one-step-advanced shield pawn."""

    shield_row = 6 if color == Color.WHITE else 1
    advance_row = shield_row - 1 if color == Color.WHITE else shield_row + 1
    home_square = ConstantSquare(
        row=get_row_constant(shield_row),
        col=get_col_constant(file_index),
    )
    advanced_square = ConstantSquare(
        row=get_row_constant(advance_row),
        col=get_col_constant(file_index),
    )
    home_pawn = board.get_piece(home_square)
    advanced_pawn = board.get_piece(advanced_square)
    has_home_pawn = (
        home_pawn is not None and home_pawn.color == color and home_pawn.kind == PieceType.PAWN
    )
    has_advanced_pawn = (
        advanced_pawn is not None
        and advanced_pawn.color == color
        and advanced_pawn.kind == PieceType.PAWN
    )
    return has_home_pawn, has_advanced_pawn


def _king_shield_files(king_col: int) -> range:
    return range(max(0, king_col - 1), min(7, king_col + 1) + 1)


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


def passed_pawns_for_color(board: Board, color: Color) -> list[tuple[int, int]]:
    """Return coordinates for one side's passed pawns."""

    own_pawns = [
        (row, col)
        for piece, row, col in iter_color_pieces(board, color)
        if piece.kind == PieceType.PAWN
    ]
    enemy_pawns = [
        (row, col)
        for piece, row, col in iter_color_pieces(board, opposite_color(color))
        if piece.kind == PieceType.PAWN
    ]
    return [
        (row, col)
        for row, col in own_pawns
        if is_passed_pawn(color, row, col, enemy_pawns)
    ]


def is_advanced_passer(color: Color, row: int) -> bool:
    """Return True when a passed pawn has reached an advanced rank."""

    return row <= 3 if color == Color.WHITE else row >= 4


def non_king_piece_kinds(board: Board) -> list[PieceType]:
    """Return the non-king piece kinds currently on the board."""

    return [
        piece.kind
        for row in board.board
        for piece in row
        if piece is not None and piece.kind != PieceType.KING
    ]


def materially_ahead_color(board: Board) -> Color | None:
    """Return the side with a non-king material lead, or None when equal."""

    material = {Color.WHITE: 0, Color.BLACK: 0}
    for row in board.board:
        for piece in row:
            if piece is None or piece.kind == PieceType.KING:
                continue
            material[piece.color] += MATERIAL_VALUES[piece.kind]
    lead = material[Color.WHITE] - material[Color.BLACK]
    if lead == 0:
        return None
    return Color.WHITE if lead > 0 else Color.BLACK


def materially_behind_color(board: Board) -> Color | None:
    """Return the side that is behind in non-king material, or None when equal."""

    leading_color = materially_ahead_color(board)
    if leading_color is None:
        return None
    return opposite_color(leading_color)


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


def heavy_piece_file_support_rows(
    board: Board,
    color: Color,
    pawn: tuple[int, int],
) -> list[int]:
    """Return heavy-piece rows that support a pawn from the same file."""

    pawn_row, pawn_col = pawn
    return [
        row
        for piece, row, col in iter_color_pieces(board, color)
        if (
            piece.kind in {PieceType.ROOK, PieceType.QUEEN}
            and col == pawn_col
            and path_clear_between(board, (row, col), (pawn_row, pawn_col))
        )
    ]


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


def opposite_color(color: Color) -> Color:
    """Return the opposite color."""

    return Color.BLACK if color == Color.WHITE else Color.WHITE
