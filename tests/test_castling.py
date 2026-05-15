"""Tests for castling."""

from __future__ import annotations

from chess_game.chess.board import Board, create_piece
from chess_game.chess.move import parse_move_notation
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq


def setup_castling_position(board: Board) -> None:
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    for col in range(8):
        file = chr(ord("a") + col)
        board.set_piece(
            sq(f"{file}7"),
            create_piece(Color.BLACK, PieceType.PAWN),
        )
        board.set_piece(
            sq(f"{file}2"),
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
        file = chr(ord("a") + col)
        board.set_piece(
            sq(f"{file}8"),
            create_piece(Color.BLACK, piece_type),
        )
        board.set_piece(
            sq(f"{file}1"),
            create_piece(Color.WHITE, piece_type),
        )


def test_white_kingside_castle_legal_case() -> None:
    board = Board()
    board.clear_board()
    setup_castling_position(board)
    board.turn = Color.WHITE

    # Clear the pieces that block castling (f1 bishop and g1 knight)
    board.clear_square(sq("f1"))
    board.clear_square(sq("g1"))

    assert board.make_move(sq("e1"), sq("g1")) is True
    assert board.get_piece_type_at(sq("g1")) == PieceType.KING
    assert board.get_piece_type_at(sq("f1")) == PieceType.ROOK


def test_white_queenside_castle_legal_case() -> None:
    board = Board()
    board.clear_board()
    setup_castling_position(board)
    board.turn = Color.WHITE

    # Clear the pieces that block castling (b1 knight, d1 queen, c1 bishop)
    board.clear_square(sq("b1"))
    board.clear_square(sq("d1"))
    board.clear_square(sq("c1"))

    assert board.make_move(sq("e1"), sq("c1")) is True
    assert board.get_piece_type_at(sq("c1")) == PieceType.KING
    assert board.get_piece_type_at(sq("d1")) == PieceType.ROOK


def test_black_kingside_castle_legal_case() -> None:
    board = Board()
    board.clear_board()
    setup_castling_position(board)
    board.turn = Color.BLACK

    # Clear the pieces that block castling (f8 bishop and g8 knight)
    board.clear_square(sq("f8"))
    board.clear_square(sq("g8"))

    assert board.make_move(sq("e8"), sq("g8")) is True
    assert board.get_piece_type_at(sq("g8")) == PieceType.KING
    assert board.get_piece_type_at(sq("f8")) == PieceType.ROOK


def test_black_queenside_castle_legal_case() -> None:
    board = Board()
    board.clear_board()
    setup_castling_position(board)
    board.turn = Color.BLACK

    # Clear the pieces that block castling (b8 knight, d8 queen, c8 bishop)
    board.clear_square(sq("b8"))
    board.clear_square(sq("d8"))
    board.clear_square(sq("c8"))

    assert board.make_move(sq("e8"), sq("c8")) is True
    assert board.get_piece_type_at(sq("c8")) == PieceType.KING
    assert board.get_piece_type_at(sq("d8")) == PieceType.ROOK


def test_en_passant_available_after_double_pawn_advance() -> None:
    board = Board()
    board.clear_board()
    board.set_piece(sq("e2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE

    assert board.make_move(sq("e2"), sq("e4")) is True
    assert board.en_passant_target == sq("e3")


def test_en_passant_captures_pawn_on_same_square() -> None:
    """White plays e2-e4, Black on d4 captures en passant d4xe3."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("d4"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE

    # White pawn moves 2 squares to create en passant target
    assert board.make_move(sq("e2"), sq("e4")) is True
    assert board.en_passant_target == sq("e3")

    # Black captures en passant d4xe3
    board.turn = Color.BLACK
    assert board.make_move(sq("d4"), sq("e3")) is True
    assert board.get_piece(sq("e4")) is None
    assert board.get_piece_type_at(sq("e3")) == PieceType.PAWN
    assert board.get_color_at(sq("e3")) == Color.BLACK


def test_en_passant_unavailable_if_pawns_on_adjacent_files() -> None:
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE

    assert board.en_passant_target is None


def test_white_promotion_to_queen() -> None:
    board = Board()
    board.clear_board()
    board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e7"), create_piece(Color.WHITE, PieceType.PAWN))

    assert board.make_move(sq("e7"), sq("e8"), PieceType.QUEEN) is True
    assert board.get_piece_type_at(sq("e8")) == PieceType.QUEEN


def test_white_promotion_to_knight() -> None:
    board = Board()
    board.clear_board()
    board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("e7"), create_piece(Color.WHITE, PieceType.PAWN))

    assert board.make_move(sq("e7"), sq("e8"), PieceType.KNIGHT) is True
    assert board.get_piece_type_at(sq("e8")) == PieceType.KNIGHT


def test_parse_move_notation_supports_promotion_choice() -> None:
    move = parse_move_notation("e7e8q")
    assert move.start == sq("e7")
    assert move.end == sq("e8")
    assert move.promotion == PieceType.QUEEN


def test_castling_through_check_is_illegal() -> None:
    board = Board()
    board.clear_board()
    setup_castling_position(board)
    board.set_piece(sq("d5"), create_piece(Color.BLACK, PieceType.BISHOP))
    board.turn = Color.WHITE

    assert board.make_move(sq("e1"), sq("g1")) is False


def test_castling_avoiding_check_is_legal() -> None:
    board = Board()
    board.clear_board()
    setup_castling_position(board)
    board.turn = Color.WHITE
    # Place a black pawn to create a check situation
    board.set_piece(sq("d4"), create_piece(Color.BLACK, PieceType.PAWN))

    # Clear the pieces that block castling (b1 knight, d1 queen, c1 bishop)
    board.clear_square(sq("b1"))
    board.clear_square(sq("d1"))
    board.clear_square(sq("c1"))

    assert board.make_move(sq("e1"), sq("c1")) is True


def test_castling_into_check_is_illegal() -> None:
    board = Board()
    board.clear_board()
    setup_castling_position(board)
    board.set_piece(sq("f3"), create_piece(Color.BLACK, PieceType.BISHOP))
    board.turn = Color.WHITE

    assert board.make_move(sq("e1"), sq("c1")) is False


def test_castling_rejected_while_in_check() -> None:
    """Castling rejected when king is currently in check."""
    board = Board()
    board.clear_board()
    setup_castling_position(board)
    board.turn = Color.WHITE
    # Black bishop on d2 checks white king on e1 via diagonal (d2-e1)
    board.set_piece(sq("d2"), create_piece(Color.BLACK, PieceType.BISHOP))
    board.clear_square(sq("f1"))
    board.clear_square(sq("g1"))
    assert board.make_move(sq("e1"), sq("g1")) is False


def test_castling_rejected_after_king_moved_away_and_back() -> None:
    """Castling rejected after king moved away from starting square."""
    board = Board()
    board.clear_board()
    setup_castling_position(board)
    board.turn = Color.WHITE
    board.clear_square(sq("f1"))
    board.clear_square(sq("g1"))
    # King moves to f1
    assert board.make_move(sq("e1"), sq("f1")) is True
    # Black makes a dummy move (pawn a7 to a6)
    assert board.make_move(sq("a7"), sq("a6")) is True
    # King moves back to e1
    assert board.make_move(sq("f1"), sq("e1")) is True
    # White cannot castle (king already moved, rights cleared)
    assert board.make_move(sq("e1"), sq("g1")) is False


def test_castling_rejected_after_rook_moved_away_and_back() -> None:
    """Castling rejected after rook moved away from starting square."""
    board = Board()
    board.clear_board()
    setup_castling_position(board)
    board.turn = Color.WHITE
    board.clear_square(sq("f1"))
    board.clear_square(sq("g1"))
    board.clear_square(sq("h2"))  # Clear h2 pawn blocking rook path
    # Rook moves from h1 to h3
    assert board.make_move(sq("h1"), sq("h3")) is True
    # Black makes a dummy move
    assert board.make_move(sq("a7"), sq("a6")) is True
    # Rook moves back to h1
    assert board.make_move(sq("h3"), sq("h1")) is True
    # White cannot castle kingside (rook already moved, right cleared)
    assert board.make_move(sq("e1"), sq("g1")) is False
