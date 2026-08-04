"""Transcript-driven regressions for STRATEGY5 repetition and shuffle cleanup."""

import pytest

from chess_game.chess import ai
from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq
from tests.test_ai_quality import _move_order_score

pytestmark = pytest.mark.slow


def _board_from_moves(moves: list[tuple[str, str, None]]) -> Board:
    board = Board()
    for start, end, promotion in moves:
        board.make_move(sq(start), sq(end), promotion=promotion)
    return board


def test_strategy5_penalizes_immediate_rook_undo() -> None:
    """Quiet ordering should demote a rook move that simply undoes the prior rook lift."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.turn = Color.WHITE

    assert board.make_move(sq("a1"), sq("e1"))
    assert board.make_move(sq("h8"), sq("h7"))

    improving_move = ai.Move(start=sq("e1"), end=sq("e3"))
    undo_move = ai.Move(start=sq("e1"), end=sq("a1"))

    assert _move_order_score(board, improving_move, None) > _move_order_score(
        board,
        undo_move,
        None,
    )


def test_strategy5_penalizes_immediate_king_undo() -> None:
    """Quiet ordering should demote king oscillation in a quiet ending."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.WHITE

    assert board.make_move(sq("g1"), sq("f2"))
    assert board.make_move(sq("h8"), sq("h7"))

    improving_move = ai.Move(start=sq("f2"), end=sq("e3"))
    undo_move = ai.Move(start=sq("f2"), end=sq("g1"))

    assert _move_order_score(board, improving_move, None) > _move_order_score(
        board,
        undo_move,
        None,
    )


def test_strategy5_penalizes_black_king_oscillation_from_transcript() -> None:
    """The lost endgame loop should prefer king activity toward the passer over Ke4."""

    board = _board_from_moves(
        [
            ("g1", "f3", None),
            ("d7", "d5", None),
            ("b1", "c3", None),
            ("d5", "d4", None),
            ("c3", "e4", None),
            ("f7", "f5", None),
            ("e4", "c5", None),
            ("e7", "e5", None),
            ("c5", "d3", None),
            ("e5", "e4", None),
            ("a2", "a4", None),
            ("e4", "d3", None),
            ("c2", "d3", None),
            ("c8", "e6", None),
            ("b2", "b3", None),
            ("b8", "c6", None),
            ("c1", "b2", None),
            ("f8", "d6", None),
            ("h1", "g1", None),
            ("b7", "b6", None),
            ("a1", "c1", None),
            ("g8", "e7", None),
            ("g2", "g3", None),
            ("e8", "g8", None),
            ("f3", "g5", None),
            ("e6", "d5", None),
            ("f2", "f4", None),
            ("e7", "g6", None),
            ("f1", "h3", None),
            ("d8", "f6", None),
            ("e1", "f2", None),
            ("a8", "e8", None),
            ("g1", "e1", None),
            ("c6", "b4", None),
            ("e1", "g1", None),
            ("h7", "h5", None),
            ("g1", "f1", None),
            ("g8", "h8", None),
            ("f1", "g1", None),
            ("f6", "e7", None),
            ("g1", "e1", None),
            ("b4", "d3", None),
            ("f2", "f1", None),
            ("d3", "b2", None),
            ("d1", "c2", None),
            ("d6", "a3", None),
            ("e2", "e4", None),
            ("d5", "e4", None),
            ("g5", "e4", None),
            ("b2", "a4", None),
            ("c1", "a1", None),
            ("e7", "e4", None),
            ("e1", "e4", None),
            ("e8", "e4", None),
            ("a1", "a3", None),
            ("a4", "c5", None),
            ("a3", "a7", None),
            ("c5", "e6", None),
            ("h3", "f5", None),
            ("d4", "d3", None),
            ("c2", "c6", None),
            ("e4", "f4", None),
            ("g3", "f4", None),
            ("f8", "f5", None),
            ("c6", "e6", None),
            ("f5", "f4", None),
            ("f1", "g2", None),
            ("f4", "g4", None),
            ("g2", "f2", None),
            ("g4", "f4", None),
            ("f2", "g3", None),
            ("f4", "g4", None),
            ("g3", "f2", None),
            ("g4", "f4", None),
            ("f2", "g3", None),
            ("f4", "g4", None),
            ("g3", "f3", None),
            ("g4", "f4", None),
            ("f3", "g2", None),
            ("f4", "g4", None),
            ("g2", "h1", None),
            ("g6", "f8", None),
            ("e6", "f7", None),
            ("f8", "g6", None),
            ("f7", "c7", None),
            ("g6", "f4", None),
            ("c7", "b8", None),
            ("h8", "h7", None),
            ("a7", "e7", None),
            ("f4", "h3", None),
            ("b8", "b6", None),
            ("g4", "g1", None),
            ("b6", "g1", None),
            ("h3", "g1", None),
            ("h1", "g1", None),
            ("h5", "h4", None),
            ("e7", "e3", None),
            ("h7", "g6", None),
            ("e3", "d3", None),
            ("g6", "f6", None),
            ("b3", "b4", None),
            ("f6", "f5", None),
            ("d3", "f3", None),
            ("f5", "e5", None),
            ("f3", "e3", None),
            ("e5", "d6", None),
            ("d2", "d4", None),
            ("d6", "d5", None),
            ("e3", "e7", None),
            ("d5", "d4", None),
            ("e7", "d7", None),
            ("d4", "c3", None),
            ("b4", "b5", None),
            ("c3", "c4", None),
            ("b5", "b6", None),
            ("c4", "b4", None),
            ("b6", "b7", None),
            ("g7", "g6", None),
            ("d7", "d4", None),
            ("b4", "c3", None),
            ("d4", "e4", None),
            ("h4", "h3", None),
            ("e4", "e3", None),
            ("c3", "d4", None),
            ("e3", "h3", None),
            ("d4", "e4", None),
            ("h3", "h4", None),
            ("e4", "d3", None),
            ("h4", "h3", None),
        ]
    )

    purposeful_defense = ai.Move(start=sq("d3"), end=sq("c2"))
    oscillating_move = ai.Move(start=sq("d3"), end=sq("e4"))

    assert _move_order_score(board, purposeful_defense, None) > _move_order_score(
        board,
        oscillating_move,
        None,
    )


def test_strategy5_prefers_promotion_over_repetition_from_transcript() -> None:
    """Winning endgame search should promote immediately instead of Rh3h4 repetition."""

    board = _board_from_moves(
        [
            ("g1", "f3", None),
            ("d7", "d5", None),
            ("b1", "c3", None),
            ("d5", "d4", None),
            ("c3", "e4", None),
            ("f7", "f5", None),
            ("e4", "c5", None),
            ("e7", "e5", None),
            ("c5", "d3", None),
            ("e5", "e4", None),
            ("a2", "a4", None),
            ("e4", "d3", None),
            ("c2", "d3", None),
            ("c8", "e6", None),
            ("b2", "b3", None),
            ("b8", "c6", None),
            ("c1", "b2", None),
            ("f8", "d6", None),
            ("h1", "g1", None),
            ("b7", "b6", None),
            ("a1", "c1", None),
            ("g8", "e7", None),
            ("g2", "g3", None),
            ("e8", "g8", None),
            ("f3", "g5", None),
            ("e6", "d5", None),
            ("f2", "f4", None),
            ("e7", "g6", None),
            ("f1", "h3", None),
            ("d8", "f6", None),
            ("e1", "f2", None),
            ("a8", "e8", None),
            ("g1", "e1", None),
            ("c6", "b4", None),
            ("e1", "g1", None),
            ("h7", "h5", None),
            ("g1", "f1", None),
            ("g8", "h8", None),
            ("f1", "g1", None),
            ("f6", "e7", None),
            ("g1", "e1", None),
            ("b4", "d3", None),
            ("f2", "f1", None),
            ("d3", "b2", None),
            ("d1", "c2", None),
            ("d6", "a3", None),
            ("e2", "e4", None),
            ("d5", "e4", None),
            ("g5", "e4", None),
            ("b2", "a4", None),
            ("c1", "a1", None),
            ("e7", "e4", None),
            ("e1", "e4", None),
            ("e8", "e4", None),
            ("a1", "a3", None),
            ("a4", "c5", None),
            ("a3", "a7", None),
            ("c5", "e6", None),
            ("h3", "f5", None),
            ("d4", "d3", None),
            ("c2", "c6", None),
            ("e4", "f4", None),
            ("g3", "f4", None),
            ("f8", "f5", None),
            ("c6", "e6", None),
            ("f5", "f4", None),
            ("f1", "g2", None),
            ("f4", "g4", None),
            ("g2", "f2", None),
            ("g4", "f4", None),
            ("f2", "g3", None),
            ("f4", "g4", None),
            ("g3", "f2", None),
            ("g4", "f4", None),
            ("f2", "g3", None),
            ("f4", "g4", None),
            ("g3", "f3", None),
            ("g4", "f4", None),
            ("f3", "g2", None),
            ("f4", "g4", None),
            ("g2", "h1", None),
            ("g6", "f8", None),
            ("e6", "f7", None),
            ("f8", "g6", None),
            ("f7", "c7", None),
            ("g6", "f4", None),
            ("c7", "b8", None),
            ("h8", "h7", None),
            ("a7", "e7", None),
            ("f4", "h3", None),
            ("b8", "b6", None),
            ("g4", "g1", None),
            ("b6", "g1", None),
            ("h3", "g1", None),
            ("h1", "g1", None),
            ("h5", "h4", None),
            ("e7", "e3", None),
            ("h7", "g6", None),
            ("e3", "d3", None),
            ("g6", "f6", None),
            ("b3", "b4", None),
            ("f6", "f5", None),
            ("d3", "f3", None),
            ("f5", "e5", None),
            ("f3", "e3", None),
            ("e5", "d6", None),
            ("d2", "d4", None),
            ("d6", "d5", None),
            ("e3", "e7", None),
            ("d5", "d4", None),
            ("e7", "d7", None),
            ("d4", "c3", None),
            ("b4", "b5", None),
            ("c3", "c4", None),
            ("b5", "b6", None),
            ("c4", "b4", None),
            ("b6", "b7", None),
            ("g7", "g6", None),
            ("d7", "d4", None),
            ("b4", "c3", None),
            ("d4", "e4", None),
            ("h4", "h3", None),
            ("e4", "e3", None),
            ("c3", "d4", None),
            ("e3", "h3", None),
            ("d4", "e4", None),
            ("h3", "h4", None),
            ("e4", "d3", None),
            ("h4", "h3", None),
            ("d3", "e4", None),
        ]
    )

    best_move = ai.get_best_move(board, depth=3)

    assert best_move is not None
    assert best_move.start == sq("b7")
    assert best_move.end == sq("b8")
    assert best_move.promotion == PieceType.QUEEN
