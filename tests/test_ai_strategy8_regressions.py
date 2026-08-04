"""Transcript-driven regressions for STRATEGY8 opening discipline priorities."""

from types import SimpleNamespace

import pytest

from chess_game.chess import ai
from chess_game.chess.ai import BestMoveOptions, _move_order_score, get_best_move
from chess_game.chess.ai_search_helpers import (
    RepetitionPolicy,
    _high_danger_root_bonus,
    _opening_root_bonus,
    repetition_score,
)
from chess_game.chess.board import Board, create_piece
from chess_game.chess.conversion_guidance import (
    _better_side_plan_switch_penalty,
    _conversion_context,
)
from chess_game.chess.endgame_choice_guidance import (
    _choice_context,
    _theater_switch_penalty,
)
from chess_game.chess.types import Color, LegalMove, PieceType
from tests.helpers import sq

# Regression targets must be stable across runs: disable the opening book and use
# deterministic equal-score tie-breaking rather than random selection.
_DETERMINISTIC = BestMoveOptions(use_opening_book=False, deterministic=True)


def _board_from_moves(moves: list[tuple[str, str]]) -> Board:
    board = Board()
    for start, end in moves:
        board.make_move(sq(start), sq(end))
    return board


def _transcript_opening_probe_board() -> Board:
    return _board_from_moves(
        [
            ("b1", "c3"),
            ("e7", "e5"),
            ("g1", "f3"),
            ("b8", "c6"),
            ("c3", "e4"),
            ("d7", "d5"),
            ("f3", "d4"),
            ("c6", "d4"),
            ("e4", "c3"),
            ("f8", "b4"),
            ("c3", "b1"),
            ("e5", "e4"),
            ("c2", "c3"),
            ("c8", "g4"),
            ("d1", "a4"),
            ("g4", "d7"),
        ]
    )


def test_strategy8_order_prefers_development_over_followup_queen_redeploy() -> None:
    """The opening probe should develop before making another quiet queen move."""

    board = _transcript_opening_probe_board()
    develop = ai.Move(start=sq("f1"), end=sq("e2"))
    queen_redeploy = ai.Move(start=sq("a4"), end=sq("d1"))

    assert _move_order_score(board, develop, None) > _move_order_score(
        board,
        queen_redeploy,
        None,
    )


def test_strategy8_order_penalizes_minor_retreat_before_king_is_settled() -> None:
    """Retreating a developed minor should lose to fresh development when uncastled."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("c4"), create_piece(Color.WHITE, PieceType.BISHOP))
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(sq("f2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("f8"), create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.turn = Color.WHITE

    develop = ai.Move(start=sq("g1"), end=sq("f3"))
    retreat = ai.Move(start=sq("c4"), end=sq("f1"))

    assert _move_order_score(board, develop, None) > _move_order_score(board, retreat, None)


@pytest.mark.slow
def test_strategy8_search_demotes_flank_poke_when_castling_is_available() -> None:
    """Near-equal opening roots should not prefer an aimless flank poke."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("f3"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(sq("e2"), create_piece(Color.WHITE, PieceType.BISHOP))
    board.set_piece(sq("a2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("f2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("f8"), create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.set_piece(sq("c5"), create_piece(Color.BLACK, PieceType.BISHOP))
    board.turn = Color.WHITE

    castle = ai.Move(start=sq("e1"), end=sq("g1"))
    flank_poke = ai.Move(start=sq("a2"), end=sq("a4"))

    assert _move_order_score(board, castle, None) > _move_order_score(board, flank_poke, None)

    best_move = get_best_move(board, depth=2, book_options=_DETERMINISTIC)

    assert best_move != LegalMove(start=sq("a2"), end=sq("a4"))


@pytest.mark.slow
def test_strategy8_conversion_prefers_simplification_over_side_activity() -> None:
    """When clearly ahead, practical simplification should beat side drift."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.set_piece(sq("a8"), create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE

    simplify = ai.Move(start=sq("d1"), end=sq("d8"))
    drift = ai.Move(start=sq("g2"), end=sq("g4"))

    assert _move_order_score(board, simplify, None) > _move_order_score(board, drift, None)
    assert get_best_move(board, depth=2) == LegalMove(start=sq("d1"), end=sq("d8"))


def test_strategy8_endgame_plan_continuity_prefers_passer_file_support() -> None:
    """In winning sparse endgames, support moves should beat theater switches."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("f4"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("a4"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("d6"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("a8"), create_piece(Color.BLACK, PieceType.ROOK))
    board.turn = Color.WHITE

    support = ai.Move(start=sq("a4"), end=sq("d4"))
    switch = ai.Move(start=sq("a4"), end=sq("h4"))

    assert _move_order_score(board, support, None) > _move_order_score(board, switch, None)


def test_strategy8_consistency_king_safety_aligns_eval_order_and_root_choice() -> None:
    """King-safety motif should align static eval, ordering, and root best move."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("g4"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(sq("h5"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE

    preferred = ai.Move(start=sq("d1"), end=sq("g4"))
    alternate = ai.Move(start=sq("d1"), end=sq("a4"))

    preferred_board = board.clone()
    preferred_board.make_move(preferred.start, preferred.end)
    alternate_board = board.clone()
    alternate_board.make_move(alternate.start, alternate.end)

    assert ai.evaluate(preferred_board) > ai.evaluate(alternate_board)
    assert _move_order_score(board, preferred, None) > _move_order_score(
        board,
        alternate,
        None,
    )
    assert get_best_move(board, depth=1) == LegalMove(start=sq("d1"), end=sq("g4"))


def test_strategy8_repetition_policy_penalizes_better_side_more_than_worse_side() -> None:
    """Better side should avoid repetition while worse side may accept it."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.WHITE

    key = "kings-only"
    winning_policy = RepetitionPolicy(
        position_key=lambda _: key,
        evaluate=lambda _: 420,
        progress=lambda _: 0,
        threshold=300,
        progress_threshold=120,
        penalty=90,
    )
    losing_policy = RepetitionPolicy(
        position_key=lambda _: key,
        evaluate=lambda _: -420,
        progress=lambda _: 0,
        threshold=300,
        progress_threshold=120,
        penalty=90,
    )
    context = SimpleNamespace(position_counts={key: 3})

    winning_repeat = repetition_score(board, context, tuple(), winning_policy)
    losing_repeat = repetition_score(board, context, tuple(), losing_policy)

    assert winning_repeat is not None and losing_repeat is not None
    assert winning_repeat < 0
    assert losing_repeat > 0


def test_strategy8_opening_root_penalizes_followup_queen_redeploy_harder() -> None:
    """Opening tie-break should heavily demote the same queen out-and-back motif."""

    board = _transcript_opening_probe_board()
    queen_redeploy = ai.Move(start=sq("a4"), end=sq("d1"))
    develop = ai.Move(start=sq("e2"), end=sq("e3"))

    assert _opening_root_bonus(
        board,
        queen_redeploy,
        PieceType.QUEEN,
    ) <= -50
    assert _opening_root_bonus(
        board,
        develop,
        PieceType.PAWN,
    ) > _opening_root_bonus(board, queen_redeploy, PieceType.QUEEN)


def test_strategy8_high_danger_root_bonus_prefers_forcing_relief() -> None:
    """Danger-mode tie-break should still reward direct pressure relief moves."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("f2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("g4"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(sq("h5"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE

    forcing_relief = ai.Move(start=sq("d1"), end=sq("g4"))
    sidestep = ai.Move(start=sq("d1"), end=sq("a4"))
    forcing_board = board.clone()
    forcing_board.make_move(forcing_relief.start, forcing_relief.end)
    sidestep_board = board.clone()
    sidestep_board.make_move(sidestep.start, sidestep.end)

    assert _high_danger_root_bonus(
        board,
        forcing_relief,
        forcing_board,
        Color.WHITE,
    ) > _high_danger_root_bonus(board, sidestep, sidestep_board, Color.WHITE)


def test_strategy8_conversion_penalizes_plan_switch_away_from_main_passer() -> None:
    """Winning conversion should penalize moving major support off the passer file."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.BISHOP))
    board.set_piece(sq("d6"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("a8"), create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(sq("h7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE

    context = _conversion_context(board)
    assert context is not None
    switch = ai.Move(start=sq("d1"), end=sq("a1"))
    stay = ai.Move(start=sq("d1"), end=sq("d4"))

    assert (
        _better_side_plan_switch_penalty(board, PieceType.ROOK, switch, context)
        > _better_side_plan_switch_penalty(board, PieceType.ROOK, stay, context)
    )


def test_strategy8_endgame_penalizes_big_theater_switch_in_won_passer_plan() -> None:
    """Won endgames should strongly penalize abandoning the passer theater."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("f4"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("d6"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.WHITE

    context = _choice_context(board, Color.WHITE)
    assert context is not None
    theater_switch = ai.Move(start=sq("d4"), end=sq("h4"))

    assert _theater_switch_penalty(theater_switch, context) == 36
