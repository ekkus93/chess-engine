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
)


def clear_board(board: Board) -> None:
    for row in range(8):
        for col in range(8):
            board.clear_square(ConstantSquare(row=row, col=col))


def _setup_kings(board: Board) -> None:
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    for col in range(8):
        board.set_piece(
            ConstantSquare(row=ROW_6, col=col),
            create_piece(Color.WHITE, PieceType.PAWN),
        )
        board.set_piece(
            ConstantSquare(row=ROW_1, col=col),
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
            ConstantSquare(row=ROW_7, col=col),
            create_piece(Color.WHITE, piece_type),
        )
        board.set_piece(
            ConstantSquare(row=ROW_8, col=col),
            create_piece(Color.BLACK, piece_type),
        )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    # Set up white pieces on rank 1 (ROW_7)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_A), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_B),
        create_piece(Color.WHITE, PieceType.KNIGHT),
    )
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_C),
        create_piece(Color.WHITE, PieceType.BISHOP),
    )
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_D), create_piece(Color.WHITE, PieceType.QUEEN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_F),
        create_piece(Color.WHITE, PieceType.BISHOP),
    )
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_G),
        create_piece(Color.WHITE, PieceType.KNIGHT),
    )
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_H), create_piece(Color.WHITE, PieceType.ROOK)
    )
    # Set up black pieces on rank 8 (ROW_8)
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_A), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_B),
        create_piece(Color.BLACK, PieceType.KNIGHT),
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_C),
        create_piece(Color.BLACK, PieceType.BISHOP),
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_D), create_piece(Color.BLACK, PieceType.QUEEN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_F),
        create_piece(Color.BLACK, PieceType.BISHOP),
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_G),
        create_piece(Color.BLACK, PieceType.KNIGHT),
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_H), create_piece(Color.BLACK, PieceType.ROOK)
    )
    # Set up pawns
    board.set_piece(
        ConstantSquare(row=ROW_6, col=COL_A), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_6, col=COL_B), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_6, col=COL_C), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_6, col=COL_D), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_6, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_6, col=COL_F), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_6, col=COL_G), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_6, col=COL_H), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_B), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_C), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_D), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_F), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_G), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_H), create_piece(Color.BLACK, PieceType.PAWN)
    )


def test_white_kingside_castle_legal_case() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_H), create_piece(Color.WHITE, PieceType.ROOK)
    )

    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_E), ConstantSquare(row=ROW_7, col=COL_G)
        )
        is True
    )
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_7, col=COL_G)) == PieceType.KING
    )
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_7, col=COL_F)) == PieceType.ROOK
    )


def test_white_queenside_castle_legal_case() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_A), create_piece(Color.WHITE, PieceType.ROOK)
    )

    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_E), ConstantSquare(row=ROW_7, col=COL_C)
        )
        is True
    )
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_7, col=COL_C)) == PieceType.KING
    )
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_7, col=COL_D)) == PieceType.ROOK
    )


def test_black_kingside_castle_legal_case() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_H), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.turn = Color.BLACK

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
    board.turn = Color.BLACK

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


def test_cannot_castle_while_in_check() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_H), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_3, col=COL_E), create_piece(Color.BLACK, PieceType.ROOK)
    )

    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_E), ConstantSquare(row=ROW_7, col=COL_G)
        )
        is False
    )


def test_cannot_castle_through_check() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_H), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_3, col=COL_F), create_piece(Color.BLACK, PieceType.ROOK)
    )

    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_E), ConstantSquare(row=ROW_7, col=COL_G)
        )
        is False
    )


def test_cannot_castle_into_check() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_H), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_3, col=COL_G), create_piece(Color.BLACK, PieceType.ROOK)
    )

    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_E), ConstantSquare(row=ROW_7, col=COL_G)
        )
        is False
    )


def test_cannot_castle_after_king_moved() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_H), create_piece(Color.WHITE, PieceType.ROOK)
    )

    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_E), ConstantSquare(row=ROW_6, col=COL_E)
        )
        is True
    )
    assert (
        board.make_move(
            ConstantSquare(row=ROW_8, col=COL_E), ConstantSquare(row=ROW_1, col=COL_E)
        )
        is True
    )
    assert (
        board.make_move(
            ConstantSquare(row=ROW_6, col=COL_E), ConstantSquare(row=ROW_7, col=COL_E)
        )
        is True
    )
    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_8, col=COL_E)
        )
        is True
    )

    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_E), ConstantSquare(row=ROW_7, col=COL_G)
        )
        is False
    )


def test_cannot_castle_after_rook_moved() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_H), create_piece(Color.WHITE, PieceType.ROOK)
    )

    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_H), ConstantSquare(row=ROW_7, col=COL_G)
        )
        is True
    )
    assert (
        board.make_move(
            ConstantSquare(row=ROW_8, col=COL_E), ConstantSquare(row=ROW_1, col=COL_E)
        )
        is True
    )
    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_G), ConstantSquare(row=ROW_7, col=COL_H)
        )
        is True
    )
    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_8, col=COL_E)
        )
        is True
    )

    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_E), ConstantSquare(row=ROW_7, col=COL_G)
        )
        is False
    )


def test_cannot_castle_if_path_blocked() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_H), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_F),
        create_piece(Color.WHITE, PieceType.KNIGHT),
    )

    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_E), ConstantSquare(row=ROW_7, col=COL_G)
        )
        is False
    )


def test_white_en_passant_legal_example() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(
        ConstantSquare(row=ROW_3, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_D), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.BLACK

    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_D), ConstantSquare(row=ROW_3, col=COL_D)
        )
        is True
    )
    assert board.en_passant_target == ConstantSquare(row=ROW_2, col=COL_D)

    assert (
        board.make_move(
            ConstantSquare(row=ROW_3, col=COL_E), ConstantSquare(row=ROW_2, col=COL_D)
        )
        is True
    )
    assert board.get_piece(ConstantSquare(row=ROW_3, col=COL_E)) is None
    assert board.get_piece(ConstantSquare(row=ROW_1, col=COL_D)) is None
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_2, col=COL_D)) == PieceType.PAWN
    )
    assert board.get_color_at(ConstantSquare(row=ROW_2, col=COL_D)) == Color.WHITE


def test_black_en_passant_legal_example() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_D), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.BLACK

    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_D), ConstantSquare(row=ROW_3, col=COL_D)
        )
        is True
    )
    assert board.en_passant_target == ConstantSquare(row=ROW_2, col=COL_D)

    assert (
        board.make_move(
            ConstantSquare(row=ROW_2, col=COL_E), ConstantSquare(row=ROW_2, col=COL_D)
        )
        is True
    )
    assert board.get_piece(ConstantSquare(row=ROW_2, col=COL_E)) is None
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_2, col=COL_D)) == PieceType.PAWN
    )
    assert board.get_color_at(ConstantSquare(row=ROW_2, col=COL_D)) == Color.WHITE


def test_en_passant_expires_after_one_turn() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(
        ConstantSquare(row=ROW_3, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_D), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_A), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_H), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.turn = Color.BLACK

    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_D), ConstantSquare(row=ROW_3, col=COL_D)
        )
        is True
    )
    assert board.en_passant_target == ConstantSquare(row=ROW_2, col=COL_D)

    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_A), ConstantSquare(row=ROW_7, col=COL_B)
        )
        is True
    )
    assert board.en_passant_target is None

    assert (
        board.make_move(
            ConstantSquare(row=ROW_8, col=COL_H), ConstantSquare(row=ROW_8, col=COL_G)
        )
        is True
    )

    assert (
        board.make_move(
            ConstantSquare(row=ROW_3, col=COL_E), ConstantSquare(row=ROW_2, col=COL_D)
        )
        is False
    )


def test_en_passant_unavailable_if_last_move_not_two_step_pawn_move() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(
        ConstantSquare(row=ROW_3, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_3, col=COL_D), create_piece(Color.BLACK, PieceType.PAWN)
    )

    assert board.en_passant_target is None
    assert board.is_valid_pawn_move((3, 4), (2, 3)) is False


def test_en_passant_cannot_be_used_if_it_leaves_own_king_in_check() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_3, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_D), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_A), create_piece(Color.BLACK, PieceType.KING)
    )
    board.turn = Color.BLACK

    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_D), ConstantSquare(row=ROW_3, col=COL_D)
        )
        is True
    )
    assert (
        board.make_move(
            ConstantSquare(row=ROW_3, col=COL_E), ConstantSquare(row=ROW_2, col=COL_D)
        )
        is False
    )


def test_white_promotion_to_queen() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_A), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_H), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )

    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=4), (0, 4), promotion=PieceType.QUEEN
        )
        is True
    )
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_8, col=COL_E)) == PieceType.QUEEN
    )
    assert board.get_color_at(ConstantSquare(row=ROW_8, col=COL_E)) == Color.WHITE


def test_white_promotion_to_knight() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_A), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_H), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )

    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=4), (0, 4), promotion=PieceType.KNIGHT
        )
        is True
    )
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_8, col=COL_E))
        == PieceType.KNIGHT
    )


def test_black_promotion_to_queen() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_A), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_H), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_6, col=COL_E), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.BLACK

    assert (
        board.make_move(
            ConstantSquare(row=ROW_2, col=4), (7, 4), promotion=PieceType.QUEEN
        )
        is True
    )
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_7, col=COL_E)) == PieceType.QUEEN
    )
    assert board.get_color_at(ConstantSquare(row=ROW_7, col=COL_E)) == Color.BLACK


def test_invalid_promotion_piece_rejected() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_A), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_H), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )

    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=4), (0, 4), promotion=PieceType.KING
        )
        is False
    )


def test_default_promotion_is_queen_when_unspecified() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_A), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_H), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )

    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_8, col=COL_E)
        )
        is True
    )
    assert (
        board.get_piece_type_at(ConstantSquare(row=ROW_8, col=COL_E)) == PieceType.QUEEN
    )


def test_parse_move_notation_supports_promotion_choice() -> None:
    move = parse_move_notation("e7e8q")
    assert move.start == (1, 4)
    assert move.end == (0, 4)
    assert move.promotion == PieceType.QUEEN


# =============================================================================
