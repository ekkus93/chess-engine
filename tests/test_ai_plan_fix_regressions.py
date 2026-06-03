"""Regressions for practical plan quality (endgame king activation)."""

from __future__ import annotations

import pytest

from chess_game.chess.ai import get_best_move
from chess_game.chess.board import Board, create_piece
from chess_game.chess.coords import algebraic_to_index
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq


pytestmark = pytest.mark.slow


def _king_activation_board() -> Board:
    """KPvKP endgame where Black's king at h7 should centralize toward its pawn.

    White: King e5, Pawn d5.  Black: King h7, Pawn g5.
    Black king should step to g6 to escort the g5 passer rather than shuffle
    on the h-file.
    """
    board = Board()
    board.clear_board()
    board.set_piece(sq("e5"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d5"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h7"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("g5"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK
    return board


def test_depth3_prefers_active_king_step_over_passive_shuffle() -> None:
    """Depth-3 search should choose the more active king move in the late game."""

    board = _king_activation_board()
    assert board.turn == Color.BLACK

    best_move = get_best_move(board, depth=3)
    assert best_move.start == algebraic_to_index("h7")
    assert best_move.end in {
        algebraic_to_index("g6"),
        algebraic_to_index("g7"),
    }
