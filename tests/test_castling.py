"""Tests for castling."""

from __future__ import annotations

from chess_game.chess.board import Board, ConstantSquare, create_piece
from chess_game.chess.move import parse_move_notation
from chess_game.chess.types import Color, PieceType
from chess_game.chess.constants import (
    COL_A,
    COL_B,
    COL_C,
    COL_D,
    COL_E,
    COL_F,
    COL_G,
    COL_H,
    get_square_constant,
)


def setup_castling_position(board: Board) -> None:
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    for col in range(8):
        board.set_piece(
            get_square_constant(1, col),
            create_piece(Color.WHITE, PieceType.PAWN),
        )
        board.set_piece(
            get_square_constant(6, col),
            create_piece(Color.BLACK, PieceType.PAWN),
        )
    for col_idx in range(8):
        col = col_idx
        piece_type = (
            PieceType.ROOK
            if col == 0 or col == 7
            else PieceType.KNIGHT
            if col == 1 or col == 6
            else PieceType.BISHOP
            if col == 2 or col == 5
            else PieceType.QUEEN
            if col == 3
            else PieceType.KING
            if col == 4
            else None
        )
        if piece_type is None:
            continue
        board.set_piece(
            get_square_constant(0, col),
            create_piece(Color.WHITE, piece_type),
        )
        board.set_piece(
            get_square_constant(7, col),
            create_piece(Color.BLACK, piece_type),
        )


def test_white_kingside_castle_legal_case() -> None:
    board = Board()
    board.clear_board()
    setup_castling_position(board)
    board.turn = Color.WHITE

    # Clear the pieces that block castling (f1 bishop and g1 knight)
    board.clear_square(get_square_constant(0, 5))
    board.clear_square(get_square_constant(0, 6))

    assert board.make_move(get_square_constant(0, 4), get_square_constant(0, 6)) is True
    assert board.get_piece_type_at(get_square_constant(0, 6)) == PieceType.KING
    assert board.get_piece_type_at(get_square_constant(0, 5)) == PieceType.ROOK


def test_white_queenside_castle_legal_case() -> None:
    board = Board()
    board.clear_board()
    setup_castling_position(board)
    board.turn = Color.WHITE

    # Clear the pieces that block castling (d1 queen and c1 bishop)
    board.clear_square(get_square_constant(0, 3))
    board.clear_square(get_square_constant(0, 2))

    assert board.make_move(get_square_constant(0, 4), get_square_constant(0, 2)) is True
    assert board.get_piece_type_at(get_square_constant(0, 2)) == PieceType.KING
    assert board.get_piece_type_at(get_square_constant(0, 3)) == PieceType.ROOK


def test_black_kingside_castle_legal_case() -> None:
    board = Board()
    board.clear_board()
    setup_castling_position(board)
    board.turn = Color.BLACK

    # Clear the pieces that block castling (f8 bishop and g8 knight)
    board.clear_square(get_square_constant(7, 5))
    board.clear_square(get_square_constant(7, 6))

    assert board.make_move(get_square_constant(7, 4), get_square_constant(7, 6)) is True
    assert board.get_piece_type_at(get_square_constant(7, 6)) == PieceType.KING
    assert board.get_piece_type_at(get_square_constant(7, 5)) == PieceType.ROOK


def test_black_queenside_castle_legal_case() -> None:
    board = Board()
    board.clear_board()
    setup_castling_position(board)
    board.turn = Color.BLACK

    # Clear the pieces that block castling (d8 queen and c8 bishop)
    board.clear_square(get_square_constant(7, 3))
    board.clear_square(get_square_constant(7, 2))

    assert board.make_move(get_square_constant(7, 4), get_square_constant(7, 2)) is True
    assert board.get_piece_type_at(get_square_constant(7, 2)) == PieceType.KING
    assert board.get_piece_type_at(get_square_constant(7, 3)) == PieceType.ROOK


def test_en_passant_available_after_double_pawn_advance() -> None:
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(1, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.turn = Color.WHITE

    assert board.make_move(get_square_constant(1, 4), get_square_constant(3, 4)) is True
    assert board.en_passant_target == get_square_constant(2, 4)


def test_en_passant_captures_pawn_on_same_square() -> None:
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(1, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        get_square_constant(4, 3), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.WHITE

    # White pawn moves 2 squares to create en passant target
    assert board.make_move(get_square_constant(1, 4), get_square_constant(3, 4)) is True
    assert board.en_passant_target == ConstantSquare(row=ROW_3, col=COL_E)

    # Black captures en passant
    assert (
        board.make_move(
            ConstantSquare(row=ROW_5, col=COL_D), ConstantSquare(row=ROW_4, col=COL_E)
        )
        is True
    )
    assert board.get_piece(ConstantSquare(row=ROW_2, col=COL_E)) is None
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_4, col=COL_E)) == PieceType.PAWN
    )
    assert board.get_color_at(ConstantSquare(row=ROW_4, col=COL_E)) == Color.BLACK


def test_en_passant_unavailable_if_pawns_on_adjacent_files() -> None:
    board = Board()
    board.clear_board()
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
    board.clear_board()
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 7), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(6, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )

    assert (
        board.make_move(
            get_square_constant(6, 4),
            get_square_constant(7, 4),
            PieceType.QUEEN,
        )
        is True
    )
    assert board.get_piece_type_at(get_square_constant(7, 4)) == PieceType.QUEEN


def test_white_promotion_to_knight() -> None:
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(0, 0), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 7), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(6, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )

    assert (
        board.make_move(
            get_square_constant(6, 4),
            get_square_constant(7, 4),
            PieceType.KNIGHT,
        )
        is True
    )
    assert board.get_piece_type_at(get_square_constant(7, 4)) == PieceType.KNIGHT


def test_parse_move_notation_supports_promotion_choice() -> None:
    move = parse_move_notation("e7e8q")
    assert move.start == get_square_constant(6, 4)
    assert move.end == get_square_constant(7, 4)
    assert move.promotion == PieceType.QUEEN


def test_castling_through_check_is_illegal() -> None:
    board = Board()
    board.clear_board()
    setup_castling_position(board)
    board.set_piece(
        get_square_constant(4, 3), create_piece(Color.BLACK, PieceType.BISHOP)
    )
    board.turn = Color.WHITE

    assert (
        board.make_move(get_square_constant(0, 4), get_square_constant(0, 6)) is False
    )


def test_castling_avoiding_check_is_legal() -> None:
    board = Board()
    board.clear_board()
    setup_castling_position(board)
    board.turn = Color.WHITE
    # Place a black pawn to create a check situation
    board.set_piece(
        get_square_constant(3, 3), create_piece(Color.BLACK, PieceType.PAWN)
    )

    # Clear the pieces that block castling (d1 queen and c1 bishop)
    board.clear_square(get_square_constant(0, 3))
    board.clear_square(get_square_constant(0, 2))

    assert board.make_move(get_square_constant(0, 4), get_square_constant(0, 2)) is True


def test_castling_into_check_is_illegal() -> None:
    board = Board()
    board.clear_board()
    setup_castling_position(board)
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
