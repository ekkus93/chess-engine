import pytest
from chess_game.chess.board import Board, create_piece
from chess_game.chess.color import Color
from chess_game.chess.pieces.piece import PieceType
from chess_game.chess.types import ConstantSquare
from chess_game.chess.constants import (
    ROW_1,
    ROW_2,
    ROW_3,
    ROW_4,
    ROW_5,
    ROW_6,
    ROW_7,
    ROW_8,
    COL_A,
    COL_B,
    COL_C,
    COL_D,
    COL_E,
    COL_F,
    COL_G,
    COL_H,
    get_row_constant,
    get_col_constant,
)


def test_black_en_passant_legal_example() -> None:
    board = Board()
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_D),
        create_piece(Color.WHITE, PieceType.PAWN, ConstantSquare(row=ROW_2, col=COL_D)),
    )  # White pawn on d2
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_E),
        create_piece(Color.BLACK, PieceType.PAWN, ConstantSquare(row=ROW_7, col=COL_E)),
    )  # Black pawn on e8 (rank 8 is array row 7)
    board.turn = Color.BLACK

    # Black moves pawn two squares (from rank 8 to rank 6, array rows 7 to 5)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_E), ConstantSquare(row=ROW_5, col=COL_E)
        )
        is True
    )
    assert board.en_passant_target == ConstantSquare(row=ROW_6, col=COL_E)

    # White captures en passant from d2 to e6 (the en passant target)
    board.turn = Color.WHITE
    assert (
        board.make_move(
            ConstantSquare(row=ROW_2, col=COL_D), ConstantSquare(row=ROW_6, col=COL_E)
        )
        is True
    )
    assert board.get_piece(ConstantSquare(row=ROW_2, col=COL_D)) is None
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_6, col=COL_E)) == PieceType.PAWN
    )
    assert board.get_color_at(ConstantSquare(row=ROW_6, col=COL_E)) == Color.WHITE
