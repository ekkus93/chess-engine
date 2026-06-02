"""Transcript-backed regressions for practical plan quality."""

from __future__ import annotations

import re
from pathlib import Path

import pytest

from chess_game.chess.ai import get_best_move
from chess_game.chess.board import Board
from chess_game.chess.coords import algebraic_to_index
from chess_game.chess.types import Color, LegalMove, PieceType


pytestmark = pytest.mark.slow

_TRANSCRIPT_PATH = Path("tmp/selfplay_depth3_20260602T031019Z.txt")
_MOVE_PATTERN = re.compile(
    r"^Move (?P<move_no>\d+): (?P<side>White|Black) plays "
    r"(?P<start>[a-h][1-8])(?P<end>[a-h][1-8])(?P<promotion>[qrnb]?)$"
)


def _promotion_from_symbol(symbol: str) -> PieceType | None:
    if symbol == "q":
        return PieceType.QUEEN
    if symbol == "r":
        return PieceType.ROOK
    if symbol == "b":
        return PieceType.BISHOP
    if symbol == "n":
        return PieceType.KNIGHT
    return None


def _board_after_move(move_no: int) -> Board:
    board = Board()
    with _TRANSCRIPT_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            match = _MOVE_PATTERN.match(line.strip())
            if match is None:
                continue
            start = algebraic_to_index(match.group("start"))
            end = algebraic_to_index(match.group("end"))
            promotion = _promotion_from_symbol(match.group("promotion"))
            if not board.make_move(start, end, promotion):
                raise AssertionError(f"Could not replay transcript move: {line.strip()}")
            if int(match.group("move_no")) == move_no:
                return board
    raise AssertionError(f"Transcript did not reach move {move_no}")


def test_depth3_prefers_active_king_step_over_passive_shuffle() -> None:
    """Depth-3 search should choose the more active king move in the late game."""

    board = _board_after_move(101)
    assert board.turn == Color.BLACK

    best_move = get_best_move(board, depth=3)
    assert best_move == LegalMove(
        start=algebraic_to_index("h7"),
        end=algebraic_to_index("g6"),
    )
