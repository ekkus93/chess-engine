"""Tests for castling."""

from __future__ import annotations

from chess_game.chess.board import Board, ConstantSquare, create_piece
from chess_game.chess.move import parse_move_notation
from chess_game.chess.types import Color, PieceType
from chess_game.chess.constants import (
    COL_A,
    COL_C,
    COL_D,
    COL_E,
    COL_G,
    ROW_1,
    ROW_2,
    ROW_3,
    ROW_4,
    ROW_5,
    ROW_7,
    get_square_constant,
)


def setup_castling_position(board: Board) -> None:
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    for col in range(8):
        board.set_piece(
            get_square_constant(1, col),
            create_piece(Color.BLACK, PieceType.PAWN),
        )
        board.set_piece(
            get_square_constant(6, col),
            create_piece(Color.WHITE, PieceType.PAWN),
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
            create_piece(Color.BLACK, piece_type),
        )
        board.set_piece(
            get_square_constant(7, col),
            create_piece(Color.WHITE, piece_type),
        )


def test_white_kingside_castle_legal_case() -> None:
    board = Board()
    board.clear_board()
    setup_castling_position(board)
    board.turn = Color.WHITE

    # Clear the pieces that block castling (f1 bishop and g1 knight)
    board.clear_square(get_square_constant(7, 5))
    board.clear_square(get_square_constant(7, 6))

    assert board.make_move(get_square_constant(7, 4), get_square_constant(7, 6)) is True
    assert board.get_piece_type_at(get_square_constant(7, 6)) == PieceType.KING
    assert board.get_piece_type_at(get_square_constant(7, 5)) == PieceType.ROOK


def test_white_queenside_castle_legal_case() -> None:
    board = Board()
    board.clear_board()
    setup_castling_position(board)
    board.turn = Color.WHITE

    # Clear the pieces that block castling (d1 queen and c1 bishop)
    board.clear_square(get_square_constant(7, 3))
    board.clear_square(get_square_constant(7, 2))

    assert board.make_move(get_square_constant(7, 4), get_square_constant(7, 2)) is True
    assert board.get_piece_type_at(get_square_constant(7, 2)) == PieceType.KING
    assert board.get_piece_type_at(get_square_constant(7, 3)) == PieceType.ROOK


def test_black_kingside_castle_legal_case() -> None:
    board = Board()
    board.clear_board()
    setup_castling_position(board)
    board.turn = Color.BLACK

    # Clear the pieces that block castling (f8 bishop and g8 knight)
    board.clear_square(get_square_constant(0, 5))
    board.clear_square(get_square_constant(0, 6))

    assert board.make_move(get_square_constant(0, 4), get_square_constant(0, 6)) is True
    assert board.get_piece_type_at(get_square_constant(0, 6)) == PieceType.KING
    assert board.get_piece_type_at(get_square_constant(0, 5)) == PieceType.ROOK


def test_black_queenside_castle_legal_case() -> None:
    board = Board()
    board.clear_board()
    setup_castling_position(board)
    board.turn = Color.BLACK

    # Clear the pieces that block castling (d8 queen and c8 bishop)
    board.clear_square(get_square_constant(0, 3))
    board.clear_square(get_square_constant(0, 2))

    assert board.make_move(get_square_constant(0, 4), get_square_constant(0, 2)) is True
    assert board.get_piece_type_at(get_square_constant(0, 2)) == PieceType.KING
    assert board.get_piece_type_at(get_square_constant(0, 3)) == PieceType.ROOK


def test_en_passant_available_after_double_pawn_advance() -> None:
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(6, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.turn = Color.WHITE

    assert board.make_move(get_square_constant(6, 4), get_square_constant(4, 4)) is True
    assert board.en_passant_target == get_square_constant(5, 4)


def test_en_passant_captures_pawn_on_same_square() -> None:
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(6, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        get_square_constant(3, 3), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.WHITE

    # White pawn moves 2 squares to create en passant target
    assert board.make_move(get_square_constant(6, 4), get_square_constant(4, 4)) is True
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
        get_square_constant(0, 7), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(1, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )

    assert (
        board.make_move(
            get_square_constant(1, 4),
            get_square_constant(0, 4),
            PieceType.QUEEN,
        )
        is True
    )
    assert board.get_piece_type_at(get_square_constant(0, 4)) == PieceType.QUEEN


def test_white_promotion_to_knight() -> None:
    board = Board()
    board.clear_board()
    board.set_piece(
        get_square_constant(7, 0), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 7), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(1, 4), create_piece(Color.WHITE, PieceType.PAWN)
    )

    assert (
        board.make_move(
            get_square_constant(1, 4),
            get_square_constant(0, 4),
            PieceType.KNIGHT,
        )
        is True
    )
    assert board.get_piece_type_at(get_square_constant(0, 4)) == PieceType.KNIGHT


def test_parse_move_notation_supports_promotion_choice() -> None:
    move = parse_move_notation("e7e8q")
    assert move.start == get_square_constant(1, 4)
    assert move.end == get_square_constant(0, 4)
    assert move.promotion == PieceType.QUEEN


def test_castling_through_check_is_illegal() -> None:
    board = Board()
    board.clear_board()
    setup_castling_position(board)
    board.set_piece(
        get_square_constant(3, 3), create_piece(Color.BLACK, PieceType.BISHOP)
    )
    board.turn = Color.WHITE

    assert (
        board.make_move(get_square_constant(7, 4), get_square_constant(7, 6)) is False
    )


def test_castling_avoiding_check_is_legal() -> None:
    board = Board()
    board.clear_board()
    setup_castling_position(board)
    board.turn = Color.WHITE
    # Place a black pawn to create a check situation
    board.set_piece(
        get_square_constant(4, 3), create_piece(Color.BLACK, PieceType.PAWN)
    )

    # Clear the pieces that block castling (d1 queen and c1 bishop)
    board.clear_square(get_square_constant(7, 3))
    board.clear_square(get_square_constant(7, 2))

    assert board.make_move(get_square_constant(7, 4), get_square_constant(7, 2)) is True


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


def test_castling_rejected_while_in_check() -> None:
    """Castling rejected when king is currently in check."""
    board = Board()
    board.clear_board()
    setup_castling_position(board)
    board.turn = Color.WHITE
    # Black bishop on d2 checks white king on e1 via diagonal (d2-e1)
    board.set_piece(
        get_square_constant(6, 3), create_piece(Color.BLACK, PieceType.BISHOP)
    )
    board.clear_square(get_square_constant(7, 5))
    board.clear_square(get_square_constant(7, 6))
    assert board.make_move(get_square_constant(7, 4), get_square_constant(7, 6)) is False


def test_castling_rejected_after_king_moved_away_and_back() -> None:
    """Castling rejected after king moved away from starting square."""
    board = Board()
    board.clear_board()
    setup_castling_position(board)
    board.turn = Color.WHITE
    board.clear_square(get_square_constant(7, 5))
    board.clear_square(get_square_constant(7, 6))
    # King moves to f1
    assert board.make_move(get_square_constant(7, 4), get_square_constant(7, 5)) is True
    # Black makes a dummy move (pawn a7 to a6)
    assert board.make_move(get_square_constant(1, 0), get_square_constant(2, 0)) is True
    # King moves back to e1
    assert board.make_move(get_square_constant(7, 5), get_square_constant(7, 4)) is True
    # White cannot castle (king already moved, rights cleared)
    assert board.make_move(get_square_constant(7, 4), get_square_constant(7, 6)) is False


def test_castling_rejected_after_rook_moved_away_and_back() -> None:
    """Castling rejected after rook moved away from starting square."""
    board = Board()
    board.clear_board()
    setup_castling_position(board)
    board.turn = Color.WHITE
    board.clear_square(get_square_constant(7, 5))
    board.clear_square(get_square_constant(7, 6))
    board.clear_square(get_square_constant(6, 7))  # Clear h2 pawn blocking rook path
    # Rook moves from h1 to h3
    assert board.make_move(get_square_constant(7, 7), get_square_constant(5, 7)) is True
    # Black makes a dummy move
    assert board.make_move(get_square_constant(1, 0), get_square_constant(2, 0)) is True
    # Rook moves back to h1
    assert board.make_move(get_square_constant(5, 7), get_square_constant(7, 7)) is True
    # White cannot castle kingside (rook already moved, right cleared)
    assert board.make_move(get_square_constant(7, 4), get_square_constant(7, 6)) is False
