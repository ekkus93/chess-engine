"""Tests for initial board setup and notation smoke tests."""

from __future__ import annotations

from chess_game.chess.board import Board
from chess_game.chess.constants import get_square_constant
from chess_game.chess.move import parse_move_notation
from chess_game.chess.types import Color, PieceType


class TestStartingPosition:
    """Task 2.2: Starting-position tests."""

    def test_white_rook_on_a1(self) -> None:
        board = Board()
        piece = board.get_piece(get_square_constant(7, 0))
        assert piece is not None
        assert piece.color == Color.WHITE
        assert piece.kind == PieceType.ROOK

    def test_white_king_on_e1(self) -> None:
        board = Board()
        piece = board.get_piece(get_square_constant(7, 4))
        assert piece is not None
        assert piece.color == Color.WHITE
        assert piece.kind == PieceType.KING

    def test_white_rook_on_h1(self) -> None:
        board = Board()
        piece = board.get_piece(get_square_constant(7, 7))
        assert piece is not None
        assert piece.color == Color.WHITE
        assert piece.kind == PieceType.ROOK

    def test_black_rook_on_a8(self) -> None:
        board = Board()
        piece = board.get_piece(get_square_constant(0, 0))
        assert piece is not None
        assert piece.color == Color.BLACK
        assert piece.kind == PieceType.ROOK

    def test_black_king_on_e8(self) -> None:
        board = Board()
        piece = board.get_piece(get_square_constant(0, 4))
        assert piece is not None
        assert piece.color == Color.BLACK
        assert piece.kind == PieceType.KING

    def test_black_rook_on_h8(self) -> None:
        board = Board()
        piece = board.get_piece(get_square_constant(0, 7))
        assert piece is not None
        assert piece.color == Color.BLACK
        assert piece.kind == PieceType.ROOK

    def test_white_pawn_on_a2(self) -> None:
        board = Board()
        piece = board.get_piece(get_square_constant(6, 0))
        assert piece is not None
        assert piece.color == Color.WHITE
        assert piece.kind == PieceType.PAWN

    def test_white_pawn_on_e2(self) -> None:
        board = Board()
        piece = board.get_piece(get_square_constant(6, 4))
        assert piece is not None
        assert piece.color == Color.WHITE
        assert piece.kind == PieceType.PAWN

    def test_white_pawn_on_h2(self) -> None:
        board = Board()
        piece = board.get_piece(get_square_constant(6, 7))
        assert piece is not None
        assert piece.color == Color.WHITE
        assert piece.kind == PieceType.PAWN

    def test_black_pawn_on_a7(self) -> None:
        board = Board()
        piece = board.get_piece(get_square_constant(1, 0))
        assert piece is not None
        assert piece.color == Color.BLACK
        assert piece.kind == PieceType.PAWN

    def test_black_pawn_on_e7(self) -> None:
        board = Board()
        piece = board.get_piece(get_square_constant(1, 4))
        assert piece is not None
        assert piece.color == Color.BLACK
        assert piece.kind == PieceType.PAWN

    def test_black_pawn_on_h7(self) -> None:
        board = Board()
        piece = board.get_piece(get_square_constant(1, 7))
        assert piece is not None
        assert piece.color == Color.BLACK
        assert piece.kind == PieceType.PAWN

    def test_center_squares_empty(self) -> None:
        board = Board()
        assert board.get_piece(get_square_constant(5, 4)) is None  # e3
        assert board.get_piece(get_square_constant(4, 4)) is None  # e4
        assert board.get_piece(get_square_constant(3, 4)) is None  # e5
        assert board.get_piece(get_square_constant(2, 4)) is None  # e6


class TestNotationSmoke:
    """Task 2.3: Notation smoke tests."""

    def test_standard_opening_moves(self) -> None:
        board = Board()

        move = parse_move_notation("e2e4")
        assert board.make_move(move.start, move.end, move.promotion) is True
        piece = board.get_piece(get_square_constant(4, 4))  # e4
        assert piece is not None
        assert piece.color == Color.WHITE
        assert piece.kind == PieceType.PAWN
        assert board.turn == Color.BLACK

        move = parse_move_notation("e7e5")
        assert board.make_move(move.start, move.end, move.promotion) is True
        piece = board.get_piece(get_square_constant(3, 4))  # e5
        assert piece is not None
        assert piece.color == Color.BLACK
        assert piece.kind == PieceType.PAWN
        assert board.turn == Color.WHITE

    def test_turn_is_white_at_start(self) -> None:
        board = Board()
        assert board.turn == Color.WHITE
