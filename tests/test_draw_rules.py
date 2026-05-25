"""Tests for draw-rule enforcement and move counters."""

from __future__ import annotations

from chess_game.chess.board import Board, create_piece
from chess_game.chess.board.game_state import (
    is_fifty_move_rule,
    is_fivefold_repetition,
    is_insufficient_material,
    is_seventy_five_move_rule,
    is_threefold_repetition,
    record_position,
    terminal_message,
)
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq


def test_move_counters_track_quiet_pawn_and_capture_moves() -> None:
    """Halfmove/fullmove counters should follow standard chess bookkeeping."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(sq("e2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("a7"), create_piece(Color.BLACK, PieceType.PAWN))

    assert board.halfmove_clock == 0
    assert board.fullmove_number == 1

    assert board.make_move(sq("a1"), sq("a3"))
    assert board.halfmove_clock == 1
    assert board.fullmove_number == 1

    assert board.make_move(sq("h8"), sq("h6"))
    assert board.halfmove_clock == 2
    assert board.fullmove_number == 2

    assert board.make_move(sq("e2"), sq("e4"))
    assert board.halfmove_clock == 0
    assert board.fullmove_number == 2

    assert board.make_move(sq("a7"), sq("a5"))
    assert board.halfmove_clock == 0
    assert board.fullmove_number == 3

    assert board.make_move(sq("a3"), sq("a5"))
    assert board.halfmove_clock == 0
    assert board.fullmove_number == 3


def test_terminal_message_reports_repetition_and_move_count_draws() -> None:
    """Terminal messaging should distinguish repetition and move-count rules."""

    board = Board()
    position_counts: dict[str, int] = {}
    record_position(board, position_counts)

    position_counts[next(iter(position_counts))] = 3
    assert is_threefold_repetition(board, position_counts)
    assert terminal_message(board, position_counts) == "Draw by threefold repetition."

    position_counts[next(iter(position_counts))] = 5
    assert is_fivefold_repetition(board, position_counts)
    assert terminal_message(board, position_counts) == "Draw by fivefold repetition."

    board.halfmove_clock = 100
    position_counts[next(iter(position_counts))] = 1
    assert is_fifty_move_rule(board)
    assert terminal_message(board, position_counts) == "Draw by fifty-move rule."

    board.halfmove_clock = 150
    assert is_seventy_five_move_rule(board)
    assert terminal_message(board, position_counts) == "Draw by seventy-five-move rule."


def test_insufficient_material_detects_basic_dead_positions() -> None:
    """Canonical insufficient-material cases should be recognized."""

    bare_kings = Board()
    bare_kings.clear_board()
    bare_kings.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    bare_kings.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    assert is_insufficient_material(bare_kings)
    assert terminal_message(bare_kings) == "Draw by insufficient material."

    bishop_vs_king = bare_kings.clone()
    bishop_vs_king.set_piece(sq("c1"), create_piece(Color.WHITE, PieceType.BISHOP))
    assert is_insufficient_material(bishop_vs_king)

    bishop_and_knight = bare_kings.clone()
    bishop_and_knight.set_piece(sq("c1"), create_piece(Color.WHITE, PieceType.BISHOP))
    bishop_and_knight.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KNIGHT))
    assert not is_insufficient_material(bishop_and_knight)

    opposite_sides_minor = bare_kings.clone()
    opposite_sides_minor.set_piece(sq("c1"), create_piece(Color.WHITE, PieceType.BISHOP))
    opposite_sides_minor.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KNIGHT))
    assert is_insufficient_material(opposite_sides_minor)
