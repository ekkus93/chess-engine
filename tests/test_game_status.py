from __future__ import annotations
from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType
from chess_game.constants import (
    
        get_row_constant,
        get_col_constant,
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
        ConstantSquare,
    
)
def clear_board(board: Board) -> None:
    for row in range(8):
        for col in range(8):
            board.clear_square(ConstantSquare(row=get_row_constant(row), col=get_col_constant(col)))
def test_start_position_has_expected_white_legal_moves() -> None:
    board = Board()
    legal_moves = board.get_legal_moves(Color.WHITE)
    assert len(legal_moves) == 20
    assert (
        ConstantSquare(row=ROW_2, col=COL_D),
        ConstantSquare(row=ROW_4, col=COL_D),
        None,
    ) in legal_moves
    # f2-f3: from f2 (row 7, col 6) to f3 (row 6, col 6)
    assert (
        ConstantSquare(row=ROW_7, col=COL_F),
        ConstantSquare(row=ROW_6, col=COL_F),
        None,
    ) in legal_moves
def test_fools_mate_is_checkmate_for_white() -> None:
    board = Board()
    assert (
        board.make_move(
            ConstantSquare(row=ROW_2, col=COL_D), ConstantSquare(row=ROW_4, col=COL_D)
        )
        is True
    )  # e2e4
    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_E), ConstantSquare(row=ROW_5, col=COL_E)
        )
        is True
    )  # e7e5
    assert (
        board.make_move(
            ConstantSquare(row=ROW_2, col=COL_G), ConstantSquare(row=ROW_4, col=COL_G)
        )
        is True
    )  # g2g4
    assert (
        board.make_move(
            ConstantSquare(row=ROW_8, col=COL_D), ConstantSquare(row=ROW_4, col=COL_H)
        )
        is True
    )  # Qd8h4#
    assert board.turn == Color.WHITE
    assert board.is_in_check(Color.WHITE) is True
    assert board.is_checkmate(Color.WHITE) is True
def test_in_check_with_one_escape_is_not_checkmate() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_H), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_D), create_piece(Color.BLACK, PieceType.KING)
    )
    # Queen on d6 checks h8 (diagonal from d6 to h8)
    board.set_piece(
        ConstantSquare(row=ROW_4, col=COL_D), create_piece(Color.BLACK, PieceType.QUEEN)
    )
    board.turn = Color.WHITE
    assert board.is_in_check(Color.WHITE) is True
    assert board.is_checkmate(Color.WHITE) is False
def test_classic_stalemate_position() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_H), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_F), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_3, col=COL_G), create_piece(Color.BLACK, PieceType.QUEEN)
    )
    board.turn = Color.WHITE
    assert board.is_in_check(Color.WHITE) is False
    assert board.is_stalemate(Color.WHITE) is True
def test_not_stalemate_when_one_legal_move_exists() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_H), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_F), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_4, col=COL_G), create_piece(Color.BLACK, PieceType.QUEEN)
    )
    board.turn = Color.WHITE
    assert board.is_in_check(Color.WHITE) is False
    assert board.is_stalemate(Color.WHITE) is False
    assert len(board.get_legal_moves(Color.WHITE)) == 1
