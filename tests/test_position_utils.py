"""Unit tests for repetition position-key helpers."""

from __future__ import annotations

from chess_game.chess.board import Board, create_piece
from chess_game.chess.position_utils import position_key
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq


def test_position_key_changes_with_turn() -> None:
    """Position key must encode side to move."""

    board = Board()
    white_turn_key = position_key(board)
    board.turn = Color.BLACK
    black_turn_key = position_key(board)

    assert white_turn_key != black_turn_key


def test_position_key_changes_with_castling_rights() -> None:
    """Position key must encode castling availability."""

    board = Board()
    full_rights_key = position_key(board)
    board.castling_rights.white_kingside = False
    board.castling_rights.black_queenside = False
    reduced_rights_key = position_key(board)

    assert full_rights_key != reduced_rights_key


def test_position_key_changes_with_en_passant_target() -> None:
    """Position key must encode en-passant target square."""

    board = Board()
    no_target_key = position_key(board)
    board.en_passant_target = sq("e3")
    target_key = position_key(board)

    assert no_target_key != target_key


def test_position_key_changes_with_piece_placement() -> None:
    """Position key must encode piece arrangement."""

    board = Board()
    initial_key = position_key(board)
    board.clear_square(sq("b1"))
    board.set_piece(sq("c3"), create_piece(Color.WHITE, PieceType.KNIGHT))
    moved_key = position_key(board)

    assert initial_key != moved_key

