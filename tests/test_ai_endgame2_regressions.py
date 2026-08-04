"""Regression coverage for ENDGAME2 anti-stalemate conversion work."""

from __future__ import annotations

import pytest

from chess_game.chess.ai import get_best_move, get_evaluation_breakdown
from chess_game.chess.board import Board, create_piece
from chess_game.chess.move import Move
from chess_game.chess.passer_race_guidance import (
    passer_race_order_bonus,
    passer_race_root_bonus,
)
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq

pytestmark = pytest.mark.slow


def _stalemate_trap_board() -> Board:
    """Endgame where Black is winning but risks stalemating White.

    White: King a1 (completely stalemated if the f6 rook is captured),
           Rook f6.  The White king cannot move: a2 is occupied by a Black
           pawn defended by b3, b1 is attacked by the a2 pawn, and b2 is
           attacked by the c3 pawn.

    Black: King g6, Pawn g7, Pawn g5 (blocks g5 king escape), Knight g4,
           Pawn a2 (advanced passer, defended by b3), Pawn b3, Pawn c3.

    Black's only king escape that doesn't stalemate White is Kg6-h7.
    All three captures at f6 (pawn, king, knight) leave White with zero
    legal moves (stalemate), so the guidance should heavily penalise them.
    """
    board = Board()
    board.clear_board()
    board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("f6"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("g6"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("g5"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("g4"), create_piece(Color.BLACK, PieceType.KNIGHT))
    board.set_piece(sq("a2"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("b3"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("c3"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK
    return board


def _apply(board: Board, move: Move) -> Board:
    child = board.clone()
    assert child.apply_legal_move(move.start, move.end, promotion=move.promotion) is True
    return child


def test_endgame2_black_prefers_escape_over_stalemate_capture() -> None:
    """Black should keep a winning endgame alive instead of boxing White into stalemate."""

    board = _stalemate_trap_board()
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

    board = _stalemate_trap_board()
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
