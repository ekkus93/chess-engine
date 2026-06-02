"""Regression coverage for ENDGAME2 anti-stalemate conversion work."""

from __future__ import annotations

from pathlib import Path

import pytest

from chess_game.chess.ai import get_best_move, get_evaluation_breakdown
from chess_game.chess.board import Board
from chess_game.chess.move import Move, parse_move_notation
from chess_game.chess.passer_race_guidance import (
    passer_race_order_bonus,
    passer_race_root_bonus,
)
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq


pytestmark = pytest.mark.slow

_TRANSCRIPT = Path(__file__).resolve().parents[1] / "tmp" / "strategy14_depth3_20260602T095859Z.txt"


def _transcript_board(move_number: int) -> Board:
    board = Board()
    for line in _TRANSCRIPT.read_text().splitlines():
        if not line.startswith("Move ") or " plays " not in line:
            continue
        current_move = int(line.split(":", 1)[0].split()[1])
        move = parse_move_notation(line.split(" plays ", 1)[1].strip())
        assert board.make_move(move.start, move.end, promotion=move.promotion) is True
        if current_move == move_number:
            return board
    raise AssertionError(f"Move {move_number} not found in {_TRANSCRIPT}")


def _apply(board: Board, move: Move) -> Board:
    child = board.clone()
    assert child.apply_legal_move(move.start, move.end, promotion=move.promotion) is True
    return child


def test_endgame2_black_prefers_escape_over_stalemate_capture() -> None:
    """Black should keep a winning endgame alive instead of boxing White into stalemate."""

    board = _transcript_board(111)
    escape = Move(start=sq("g6"), end=sq("h7"))
    capture = Move(start=sq("g7"), end=sq("f6"))
    king_capture = Move(start=sq("g6"), end=sq("f6"))
    knight_capture = Move(start=sq("g4"), end=sq("f6"))

    escape_child = _apply(board, escape)
    capture_child = _apply(board, capture)
    king_capture_child = _apply(board, king_capture)
    knight_capture_child = _apply(board, knight_capture)

    best_move = get_best_move(board, depth=3)
    assert best_move is not None
    assert best_move.start == escape.start
    assert best_move.end == escape.end
    assert best_move.promotion == escape.promotion
    assert passer_race_order_bonus(
        board,
        Color.BLACK,
        PieceType.KING,
        escape,
    ) > passer_race_order_bonus(board, Color.BLACK, PieceType.PAWN, capture)
    assert passer_race_root_bonus(
        board,
        escape,
        escape_child,
        Color.BLACK,
    ) > passer_race_root_bonus(board, capture, capture_child, Color.BLACK)
    assert passer_race_root_bonus(
        board,
        escape,
        escape_child,
        Color.BLACK,
    ) > passer_race_root_bonus(board, king_capture, king_capture_child, Color.BLACK)
    assert passer_race_root_bonus(
        board,
        escape,
        escape_child,
        Color.BLACK,
    ) > passer_race_root_bonus(board, knight_capture, knight_capture_child, Color.BLACK)


def test_endgame2_white_prefers_active_checking_defense_after_escape() -> None:
    """White should answer the safer conversion line with active checking play."""

    board = _transcript_board(111)
    escape_child = _apply(board, Move(start=sq("g6"), end=sq("h7")))
    checking = Move(start=sq("f6"), end=sq("h6"))
    passive = Move(start=sq("f6"), end=sq("f5"))

    checking_child = _apply(escape_child, checking)
    passive_child = _apply(escape_child, passive)

    best_move = get_best_move(escape_child, depth=3)
    assert best_move is not None
    assert best_move.start == checking.start
    assert best_move.end == checking.end
    assert best_move.promotion == checking.promotion
    assert get_evaluation_breakdown(checking_child)["total"] > get_evaluation_breakdown(
        passive_child,
    )["total"]
