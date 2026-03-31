"""Tests for castling."""

from __future__ import annotations

from chess_game.chess.board import Board, ConstantSquare, create_piece
from chess_game.chess.move import parse_move_notation
from chess_game.chess.types import Color, PieceType
from chess_game.constants import (
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


def clear_board(board: Board) -> None:
    for row in range(8):
        for col in range(8):
            col = get_col_constant(col)
            board.clear_square(
                ConstantSquare(row=get_row_constant(row), col=get_col_constant(col))
            )


def _setup_kings(board: Board) -> None:
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    for col in range(8):
        col = get_col_constant(col)
        board.set_piece(
            ConstantSquare(row=ROW_2, col=col),
            create_piece(Color.WHITE, PieceType.PAWN),
        )
        board.set_piece(
            ConstantSquare(row=ROW_7, col=col),
            create_piece(Color.BLACK, PieceType.PAWN),
        )
    for col_idx, (col, piece_type) in enumerate(
        [
            (COL_A, PieceType.ROOK),
            (COL_B, PieceType.KNIGHT),
            (COL_C, PieceType.BISHOP),
            (COL_D, PieceType.QUEEN),
            (COL_F, PieceType.BISHOP),
            (COL_G, PieceType.KNIGHT),
            (COL_H, PieceType.ROOK),
        ]
    ):
        board.set_piece(
            ConstantSquare(row=ROW_1, col=col),
            create_piece(Color.WHITE, piece_type),
        )
        board.set_piece(
            ConstantSquare(row=ROW_8, col=col),
            create_piece(Color.BLACK, piece_type),
        )


def test_white_kingside_castle_legal_case() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_H), create_piece(Color.WHITE, PieceType.ROOK)
    )

    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_1, col=COL_G)
        )
        is True
    )
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_1, col=COL_G)) == PieceType.KING
    )
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_1, col=COL_F)) == PieceType.ROOK
    )


def test_white_queenside_castle_legal_case() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A), create_piece(Color.WHITE, PieceType.ROOK)
    )

    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_1, col=COL_C)
        )
        is True
    )
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_1, col=COL_C)) == PieceType.KING
    )
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_1, col=COL_D)) == PieceType.ROOK
    )


def test_black_kingside_castle_legal_case() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_H), create_piece(Color.BLACK, PieceType.ROOK)
    )

    assert (
        board.make_move(
            ConstantSquare(row=ROW_8, col=COL_E), ConstantSquare(row=ROW_8, col=COL_G)
        )
        is True
    )
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_8, col=COL_G)) == PieceType.KING
    )
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_8, col=COL_F)) == PieceType.ROOK
    )


def test_black_queenside_castle_legal_case() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_A), create_piece(Color.BLACK, PieceType.ROOK)
    )

    assert (
        board.make_move(
            ConstantSquare(row=ROW_8, col=COL_E), ConstantSquare(row=ROW_8, col=COL_C)
        )
        is True
    )
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_8, col=COL_C)) == PieceType.KING
    )
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_8, col=COL_D)) == PieceType.ROOK
    )


def test_en_passant_available_after_double_pawn_advance() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.turn = Color.WHITE

    assert (
        board.make_move(
            ConstantSquare(row=ROW_2, col=COL_E), ConstantSquare(row=ROW_4, col=COL_E)
        )
        is True
    )
    assert board.en_passant_target == ConstantSquare(row=ROW_3, col=COL_E)


def test_en_passant_captures_pawn_on_same_square() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_4, col=COL_D), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.BLACK

    assert (
        board.make_move(
            ConstantSquare(row=ROW_4, col=COL_D), ConstantSquare(row=ROW_3, col=COL_D)
        )
        is True
    )
    assert board.en_passant_target == ConstantSquare(row=ROW_4, col=COL_D)

    assert (
        board.make_move(
            ConstantSquare(row=ROW_2, col=COL_E), ConstantSquare(row=ROW_4, col=COL_D)
        )
        is True
    )
    assert board.get_piece(ConstantSquare(row=ROW_2, col=COL_E)) is None
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_4, col=COL_D)) == PieceType.PAWN
    )
    assert board.get_color_at(ConstantSquare(row=ROW_4, col=COL_D)) == Color.WHITE


def test_en_passant_unavailable_if_pawns_on_adjacent_files() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_D), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.turn = Color.WHITE

    assert board.en_passant_target is None


def test_white_promotion_to_queen() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_H), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )

    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_E),
            ConstantSquare(row=ROW_8, col=COL_E),
            PieceType.QUEEN,
        )
        is True
    )
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_8, col=COL_E)) == PieceType.QUEEN
    )


def test_white_promotion_to_knight() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_H), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )

    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_E),
            ConstantSquare(row=ROW_8, col=COL_E),
            PieceType.KNIGHT,
        )
        is True
    )
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_8, col=COL_E))
        == PieceType.KNIGHT
    )


def test_parse_move_notation_supports_promotion_choice() -> None:
    move = parse_move_notation("e7e8q")
    assert move.start == ConstantSquare(row=ROW_7, col=COL_E)
    assert move.end == ConstantSquare(row=ROW_8, col=COL_E)
    assert move.promotion == PieceType.QUEEN


def test_castling_through_check_is_illegal() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(
        ConstantSquare(row=ROW_5, col=COL_D),
        create_piece(Color.BLACK, PieceType.BISHOP),
    )
    board.turn = Color.WHITE

    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_1, col=COL_G)
        )
        is False
    )


def test_castling_avoiding_check_is_legal() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(
        ConstantSquare(row=ROW_5, col=COL_F),
        create_piece(Color.BLACK, PieceType.BISHOP),
    )
    board.turn = Color.WHITE

    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_1, col=COL_C)
        )
        is True
    )


def test_castling_into_check_is_illegal() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(
        ConstantSquare(row=ROW_5, col=COL_G),
        create_piece(Color.BLACK, PieceType.BISHOP),
    )
    board.turn = Color.WHITE

    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_1, col=COL_C)
        )
        is False
    )
