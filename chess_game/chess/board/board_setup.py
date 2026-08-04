"""Board construction helpers: the piece factory and the starting-position grid.

Extracted from ``board.py``. ``create_piece`` is re-exported by ``board.py`` (and the
``board`` package) so existing imports keep working; ``create_starting_grid`` replaces
the old ``Board._create_board`` instance method (it never used ``self``).
"""


from chess_game.chess.constants import (
    COL_A,
    COL_B,
    COL_C,
    COL_D,
    COL_E,
    COL_F,
    COL_G,
    COL_H,
    ROW_1,
    ROW_2,
    ROW_7,
    ROW_8,
    Color,
    ConstantSquare,
    get_col_constant,
    get_row_constant,
)
from chess_game.chess.types import Piece, PieceType


def create_piece(
    color: Color, piece_type: PieceType, square: ConstantSquare | None = None
) -> Piece:
    """Create a typed chess piece."""
    if isinstance(square, tuple):
        square = ConstantSquare(
            row=get_row_constant(square[0]), col=get_col_constant(square[1])
        )
    piece = Piece(color=color, kind=piece_type)
    if square is not None:
        piece.square = square
    return piece


def create_starting_grid() -> list[list[Piece | None]]:
    """Create a standard chess board grid with the starting position.

    Canonical layout: row 0 = rank 8 (black), row 7 = rank 1 (white).
    """
    board: list[list[Piece | None]] = [
        [None for _ in range(8)] for _ in range(8)
    ]

    # Black pieces (rows 0-1 = ranks 8-7)
    board[0] = [
        create_piece(Color.BLACK, PieceType.ROOK, ConstantSquare(row=ROW_8, col=COL_A)),
        create_piece(Color.BLACK, PieceType.KNIGHT, ConstantSquare(row=ROW_8, col=COL_B)),
        create_piece(Color.BLACK, PieceType.BISHOP, ConstantSquare(row=ROW_8, col=COL_C)),
        create_piece(Color.BLACK, PieceType.QUEEN, ConstantSquare(row=ROW_8, col=COL_D)),
        create_piece(Color.BLACK, PieceType.KING, ConstantSquare(row=ROW_8, col=COL_E)),
        create_piece(Color.BLACK, PieceType.BISHOP, ConstantSquare(row=ROW_8, col=COL_F)),
        create_piece(Color.BLACK, PieceType.KNIGHT, ConstantSquare(row=ROW_8, col=COL_G)),
        create_piece(Color.BLACK, PieceType.ROOK, ConstantSquare(row=ROW_8, col=COL_H)),
    ]
    board[1] = [
        create_piece(Color.BLACK, PieceType.PAWN, ConstantSquare(row=ROW_7, col=COL_A)),
        create_piece(Color.BLACK, PieceType.PAWN, ConstantSquare(row=ROW_7, col=COL_B)),
        create_piece(Color.BLACK, PieceType.PAWN, ConstantSquare(row=ROW_7, col=COL_C)),
        create_piece(Color.BLACK, PieceType.PAWN, ConstantSquare(row=ROW_7, col=COL_D)),
        create_piece(Color.BLACK, PieceType.PAWN, ConstantSquare(row=ROW_7, col=COL_E)),
        create_piece(Color.BLACK, PieceType.PAWN, ConstantSquare(row=ROW_7, col=COL_F)),
        create_piece(Color.BLACK, PieceType.PAWN, ConstantSquare(row=ROW_7, col=COL_G)),
        create_piece(Color.BLACK, PieceType.PAWN, ConstantSquare(row=ROW_7, col=COL_H)),
    ]

    # White pieces (rows 6-7 = ranks 2-1)
    board[6] = [
        create_piece(Color.WHITE, PieceType.PAWN, ConstantSquare(row=ROW_2, col=COL_A)),
        create_piece(Color.WHITE, PieceType.PAWN, ConstantSquare(row=ROW_2, col=COL_B)),
        create_piece(Color.WHITE, PieceType.PAWN, ConstantSquare(row=ROW_2, col=COL_C)),
        create_piece(Color.WHITE, PieceType.PAWN, ConstantSquare(row=ROW_2, col=COL_D)),
        create_piece(Color.WHITE, PieceType.PAWN, ConstantSquare(row=ROW_2, col=COL_E)),
        create_piece(Color.WHITE, PieceType.PAWN, ConstantSquare(row=ROW_2, col=COL_F)),
        create_piece(Color.WHITE, PieceType.PAWN, ConstantSquare(row=ROW_2, col=COL_G)),
        create_piece(Color.WHITE, PieceType.PAWN, ConstantSquare(row=ROW_2, col=COL_H)),
    ]
    board[7] = [
        create_piece(Color.WHITE, PieceType.ROOK, ConstantSquare(row=ROW_1, col=COL_A)),
        create_piece(Color.WHITE, PieceType.KNIGHT, ConstantSquare(row=ROW_1, col=COL_B)),
        create_piece(Color.WHITE, PieceType.BISHOP, ConstantSquare(row=ROW_1, col=COL_C)),
        create_piece(Color.WHITE, PieceType.QUEEN, ConstantSquare(row=ROW_1, col=COL_D)),
        create_piece(Color.WHITE, PieceType.KING, ConstantSquare(row=ROW_1, col=COL_E)),
        create_piece(Color.WHITE, PieceType.BISHOP, ConstantSquare(row=ROW_1, col=COL_F)),
        create_piece(Color.WHITE, PieceType.KNIGHT, ConstantSquare(row=ROW_1, col=COL_G)),
        create_piece(Color.WHITE, PieceType.ROOK, ConstantSquare(row=ROW_1, col=COL_H)),
    ]

    return board
