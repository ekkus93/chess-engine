"""Opening-phase development helpers shared by evaluation and ordering."""

from chess_game.chess.board import Board
from chess_game.chess.constants import ConstantSquare
from chess_game.chess.evaluation_tables import (
    CENTRAL_DUO_BONUS,
    CENTRAL_MINOR_PIECE_BONUS,
    CENTRAL_SQUARES,
    EARLY_FLANK_RAID_PENALTY,
    EXTENDED_CENTER_FILES,
    EXTENDED_CENTER_RANKS,
    MINOR_COORDINATION_BONUS,
)
from chess_game.chess.strategy_utils import iter_color_pieces
from chess_game.chess.types import Color, PieceType


def opening_central_control_bonus(board: Board, color: Color) -> int:
    """Reward early control of the center by pawns and minor pieces."""

    bonus = 0
    for piece, row, col in iter_color_pieces(board, color):
        if piece.kind == PieceType.PAWN and (row, col) in CENTRAL_SQUARES:
            bonus += CENTRAL_DUO_BONUS // 2
        if (
            piece.kind in {PieceType.KNIGHT, PieceType.BISHOP}
            and row in EXTENDED_CENTER_RANKS
            and col in EXTENDED_CENTER_FILES
        ):
            bonus += CENTRAL_MINOR_PIECE_BONUS // 2
    return bonus


def opening_piece_coordination_bonus(
    board: Board,
    color: Color,
    undeveloped: int,
) -> int:
    """Reward coordinated minor-piece development before the opening is finished."""

    if undeveloped > 2:
        return 0
    developed_minors = [
        (row, col)
        for piece, row, col in iter_color_pieces(board, color)
        if piece.kind in {PieceType.KNIGHT, PieceType.BISHOP}
        and not minor_on_home_square(color, piece.kind, row, col)
    ]
    if coordinated_minor_piece_setup(developed_minors):
        return MINOR_COORDINATION_BONUS // 2
    return 0


def early_flank_raid_penalty(board: Board, color: Color, undeveloped: int) -> int:
    """Penalize early queen/rook flank raids before king safety is secured."""

    king_square = board.find_king(color)
    if undeveloped < 2 or king_square is None or _is_castled_king(color, king_square):
        return 0
    penalty = 0
    for piece, row, col in iter_color_pieces(board, color):
        if piece.kind not in {PieceType.QUEEN, PieceType.ROOK}:
            continue
        if col not in {0, 1, 6, 7} or not _piece_in_enemy_half(color, row):
            continue
        penalty += (
            EARLY_FLANK_RAID_PENALTY
            if piece.kind == PieceType.QUEEN
            else EARLY_FLANK_RAID_PENALTY // 2
        )
    return penalty


def minor_on_home_square(color: Color, kind: PieceType, row: int, col: int) -> bool:
    """Return True when a minor piece still sits on its original square."""

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
    return (row, col) in starting_squares[color].get(kind, set())


def coordinated_minor_piece_setup(minor_squares: list[tuple[int, int]]) -> bool:
    """Return True when two developed minor pieces work near the center together."""

    central_squares = [
        square
        for square in minor_squares
        if square[1] in EXTENDED_CENTER_FILES and square[0] in EXTENDED_CENTER_RANKS
    ]
    if len(central_squares) < 2:
        return False
    first_row, first_col = central_squares[0]
    for second_row, second_col in central_squares[1:]:
        if abs(first_row - second_row) <= 2 and abs(first_col - second_col) <= 2:
            return True
    return False


def undeveloped_minor_piece_count(board: Board, color: Color) -> int:
    """Return how many knights and bishops still sit on their home squares."""

    undeveloped = 0
    for piece, row, col in iter_color_pieces(board, color):
        if piece.kind in {PieceType.KNIGHT, PieceType.BISHOP} and minor_on_home_square(
            color,
            piece.kind,
            row,
            col,
        ):
            undeveloped += 1
    return undeveloped


def _is_castled_king(color: Color, square: ConstantSquare) -> bool:
    """Return True when the king already sits on a castled home-rank square."""

    home_row = 7 if color == Color.WHITE else 0
    return int(square.row) == home_row and int(square.col) in {2, 6}


def _piece_in_enemy_half(color: Color, row: int) -> bool:
    """Return True when the piece has advanced far enough to count as a raid."""

    return row <= 3 if color == Color.WHITE else row >= 4
