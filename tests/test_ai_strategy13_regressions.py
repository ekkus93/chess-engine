"""Regression tests for STRATEGY13: conversion quality and defensive practicality."""

from __future__ import annotations

import pytest

from chess_game.chess.ai import get_best_move
from chess_game.chess.ai_search_helpers import _opening_root_bonus
from chess_game.chess.anti_drift_guidance import (
    anti_drift_order_bonus,
    anti_drift_root_bonus,
)
from chess_game.chess.board import Board, create_piece
from chess_game.chess.conversion_guidance import (
    winning_conversion_order_bonus,
    winning_conversion_root_bonus,
)
from chess_game.chess.defensive_containment_guidance import (
    heavy_piece_defense_order_bonus,
    heavy_piece_defense_root_bonus,
)
from chess_game.chess.move import Move
from chess_game.chess.passer_race_guidance import passer_race_order_bonus
from chess_game.chess.types import Color, LegalMove, PieceType
from tests.helpers import sq


def _build_board(
    pieces: list[tuple[str, Color, PieceType]],
    turn: Color,
) -> Board:
    board = Board()
    board.clear_board()
    for square, color, kind in pieces:
        board.set_piece(sq(square), create_piece(color, kind))
    board.turn = turn
    return board


def test_strategy13_black_prefers_forcing_trade_in_won_endgame() -> None:
    board = _build_board(
        [
            ("e2", Color.WHITE, PieceType.KING),
            ("d2", Color.WHITE, PieceType.ROOK),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("e6", Color.BLACK, PieceType.KING),
            ("d5", Color.BLACK, PieceType.QUEEN),
            ("g5", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.BLACK,
    )
    forcing_trade = Move(start=sq("d5"), end=sq("d2"))
    drift = Move(start=sq("d5"), end=sq("f5"))
    trade_child = board.clone()
    drift_child = board.clone()
    assert trade_child.apply_legal_move(forcing_trade.start, forcing_trade.end)
    assert drift_child.apply_legal_move(drift.start, drift.end)
    trade_bonus = winning_conversion_root_bonus(
        board,
        forcing_trade,
        trade_child,
        Color.BLACK,
    )
    drift_bonus = winning_conversion_root_bonus(
        board,
        drift,
        drift_child,
        Color.BLACK,
    )
    assert trade_bonus > drift_bonus


def test_strategy13_black_prefers_passer_push_with_king_support() -> None:
    board = _build_board(
        [
            ("g2", Color.WHITE, PieceType.KING),
            ("a6", Color.WHITE, PieceType.PAWN),
            ("e6", Color.BLACK, PieceType.KING),
            ("a8", Color.BLACK, PieceType.ROOK),
            ("f5", Color.BLACK, PieceType.PAWN),
            ("g5", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.BLACK,
    )
    passer_push = Move(start=sq("f5"), end=sq("f6"))
    rook_shuffle = Move(start=sq("a8"), end=sq("a7"))
    push_bonus = winning_conversion_order_bonus(
        board,
        Color.BLACK,
        PieceType.PAWN,
        passer_push,
    )
    shuffle_bonus = winning_conversion_order_bonus(
        board,
        Color.BLACK,
        PieceType.ROOK,
        rook_shuffle,
    )
    assert push_bonus > shuffle_bonus


def test_strategy13_black_prefers_king_cutoff_before_side_shuffle() -> None:
    board = _build_board(
        [
            ("e2", Color.WHITE, PieceType.KING),
            ("h2", Color.WHITE, PieceType.ROOK),
            ("f6", Color.BLACK, PieceType.KING),
            ("a8", Color.BLACK, PieceType.ROOK),
            ("g5", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.BLACK,
    )
    cutoff = Move(start=sq("a8"), end=sq("e8"))
    side_shuffle = Move(start=sq("a8"), end=sq("b8"))
    cutoff_child = board.clone()
    shuffle_child = board.clone()
    assert cutoff_child.apply_legal_move(cutoff.start, cutoff.end)
    assert shuffle_child.apply_legal_move(side_shuffle.start, side_shuffle.end)
    cutoff_bonus = winning_conversion_root_bonus(
        board,
        cutoff,
        cutoff_child,
        Color.BLACK,
    )
    shuffle_bonus = winning_conversion_root_bonus(
        board,
        side_shuffle,
        shuffle_child,
        Color.BLACK,
    )
    assert cutoff_bonus > shuffle_bonus


def test_strategy13_black_rejects_nonforcing_check_loop_when_winning() -> None:
    board = _build_board(
        [
            ("g2", Color.WHITE, PieceType.KING),
            ("h1", Color.WHITE, PieceType.ROOK),
            ("c1", Color.WHITE, PieceType.BISHOP),
            ("g7", Color.BLACK, PieceType.KING),
            ("d6", Color.BLACK, PieceType.QUEEN),
            ("b8", Color.BLACK, PieceType.ROOK),
            ("d4", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.BLACK,
    )
    assert board.make_move(sq("d6"), sq("a6"))
    assert board.make_move(sq("c1"), sq("b2"))
    undo = Move(start=sq("a6"), end=sq("d6"))
    force_progress = Move(start=sq("d4"), end=sq("d3"))
    undo_bonus = anti_drift_order_bonus(board, Color.BLACK, PieceType.QUEEN, undo)
    progress_bonus = anti_drift_order_bonus(
        board,
        Color.BLACK,
        PieceType.PAWN,
        force_progress,
    )
    assert progress_bonus > undo_bonus


def test_strategy13_black_rejects_lateral_queen_drift_with_direct_win_available() -> None:
    board = _build_board(
        [
            ("g2", Color.WHITE, PieceType.KING),
            ("h1", Color.WHITE, PieceType.ROOK),
            ("c1", Color.WHITE, PieceType.BISHOP),
            ("g7", Color.BLACK, PieceType.KING),
            ("d6", Color.BLACK, PieceType.QUEEN),
            ("b8", Color.BLACK, PieceType.ROOK),
            ("d4", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.BLACK,
    )
    drift = Move(start=sq("d6"), end=sq("h6"))
    forcing = Move(start=sq("d4"), end=sq("d3"))
    drift_child = board.clone()
    forcing_child = board.clone()
    assert drift_child.apply_legal_move(drift.start, drift.end)
    assert forcing_child.apply_legal_move(forcing.start, forcing.end)
    drift_bonus = anti_drift_root_bonus(board, drift, drift_child, Color.BLACK)
    forcing_bonus = anti_drift_root_bonus(board, forcing, forcing_child, Color.BLACK)
    assert forcing_bonus > drift_bonus


@pytest.mark.slow
def test_strategy13_black_keeps_forcing_line_over_repetition() -> None:
    board = _build_board(
        [
            ("g2", Color.WHITE, PieceType.KING),
            ("h1", Color.WHITE, PieceType.ROOK),
            ("c1", Color.WHITE, PieceType.BISHOP),
            ("g7", Color.BLACK, PieceType.KING),
            ("d6", Color.BLACK, PieceType.QUEEN),
            ("b8", Color.BLACK, PieceType.ROOK),
            ("d4", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.BLACK,
    )
    assert board.make_move(sq("d6"), sq("a6"))
    assert board.make_move(sq("c1"), sq("b2"))
    best_move = get_best_move(board, depth=2)
    assert best_move is not None
    assert best_move != LegalMove(start=sq("a6"), end=sq("d6"))


def test_strategy13_white_prefers_active_king_defense_over_waiting() -> None:
    board = _build_board(
        [
            ("g2", Color.WHITE, PieceType.KING),
            ("h2", Color.WHITE, PieceType.ROOK),
            ("a2", Color.WHITE, PieceType.PAWN),
            ("e5", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.QUEEN),
            ("d2", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.WHITE,
    )
    king_step = Move(start=sq("g2"), end=sq("f3"))
    waiting = Move(start=sq("a2"), end=sq("a3"))
    king_bonus = heavy_piece_defense_order_bonus(board, Color.WHITE, PieceType.KING, king_step)
    wait_bonus = heavy_piece_defense_order_bonus(board, Color.WHITE, PieceType.PAWN, waiting)
    assert king_bonus > wait_bonus


def test_strategy13_white_prefers_blockade_square_over_side_pawn_push() -> None:
    board = _build_board(
        [
            ("g2", Color.WHITE, PieceType.KING),
            ("h2", Color.WHITE, PieceType.ROOK),
            ("a2", Color.WHITE, PieceType.PAWN),
            ("e5", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.QUEEN),
            ("d2", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.WHITE,
    )
    blockade = Move(start=sq("h2"), end=sq("d2"))
    side_pawn = Move(start=sq("a2"), end=sq("a3"))
    block_bonus = heavy_piece_defense_order_bonus(board, Color.WHITE, PieceType.ROOK, blockade)
    side_bonus = heavy_piece_defense_order_bonus(board, Color.WHITE, PieceType.PAWN, side_pawn)
    assert block_bonus > side_bonus


def test_strategy13_white_prefers_practical_check_resource_when_worse() -> None:
    board = _build_board(
        [
            ("g2", Color.WHITE, PieceType.KING),
            ("h2", Color.WHITE, PieceType.ROOK),
            ("a2", Color.WHITE, PieceType.PAWN),
            ("e5", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.QUEEN),
            ("d2", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.WHITE,
    )
    check_resource = Move(start=sq("h2"), end=sq("h5"))
    passive = Move(start=sq("h2"), end=sq("h3"))
    check_child = board.clone()
    passive_child = board.clone()
    assert check_child.apply_legal_move(check_resource.start, check_resource.end)
    assert passive_child.apply_legal_move(passive.start, passive.end)
    check_bonus = heavy_piece_defense_root_bonus(board, check_child, Color.WHITE)
    passive_bonus = heavy_piece_defense_root_bonus(board, passive_child, Color.WHITE)
    assert check_bonus > passive_bonus


def test_strategy13_white_prioritizes_most_dangerous_enemy_passer() -> None:
    board = _build_board(
        [
            ("c1", Color.WHITE, PieceType.KING),
            ("d1", Color.WHITE, PieceType.ROOK),
            ("a5", Color.WHITE, PieceType.PAWN),
            ("e4", Color.BLACK, PieceType.KING),
            ("h8", Color.BLACK, PieceType.ROOK),
            ("b7", Color.BLACK, PieceType.PAWN),
            ("g2", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.WHITE,
    )
    contain_danger = Move(start=sq("d1"), end=sq("g1"))
    slow_shift = Move(start=sq("d1"), end=sq("a1"))
    contain_bonus = passer_race_order_bonus(board, Color.WHITE, PieceType.ROOK, contain_danger)
    shift_bonus = passer_race_order_bonus(board, Color.WHITE, PieceType.ROOK, slow_shift)
    assert contain_bonus > shift_bonus


def test_strategy13_white_races_only_when_tempo_favorable() -> None:
    board = _build_board(
        [
            ("c1", Color.WHITE, PieceType.KING),
            ("d1", Color.WHITE, PieceType.ROOK),
            ("a3", Color.WHITE, PieceType.PAWN),
            ("e4", Color.BLACK, PieceType.KING),
            ("h8", Color.BLACK, PieceType.ROOK),
            ("b7", Color.BLACK, PieceType.PAWN),
            ("g2", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.WHITE,
    )
    bad_race = Move(start=sq("a3"), end=sq("a4"))
    contain_danger = Move(start=sq("d1"), end=sq("g1"))
    race_bonus = passer_race_order_bonus(board, Color.WHITE, PieceType.PAWN, bad_race)
    contain_bonus = passer_race_order_bonus(board, Color.WHITE, PieceType.ROOK, contain_danger)
    assert contain_bonus > race_bonus


def test_strategy13_white_rejects_irrelevant_side_activity_in_losing_endgame() -> None:
    board = _build_board(
        [
            ("c1", Color.WHITE, PieceType.KING),
            ("d1", Color.WHITE, PieceType.ROOK),
            ("a5", Color.WHITE, PieceType.PAWN),
            ("e4", Color.BLACK, PieceType.KING),
            ("h8", Color.BLACK, PieceType.ROOK),
            ("b7", Color.BLACK, PieceType.PAWN),
            ("g2", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.WHITE,
    )
    contain_danger = Move(start=sq("d1"), end=sq("g1"))
    side_activity = Move(start=sq("d1"), end=sq("b1"))
    contain_bonus = passer_race_order_bonus(board, Color.WHITE, PieceType.ROOK, contain_danger)
    side_bonus = passer_race_order_bonus(board, Color.WHITE, PieceType.ROOK, side_activity)
    assert contain_bonus > side_bonus


def test_strategy13_transition_prefers_king_activation_after_simplification() -> None:
    board = _build_board(
        [
            ("e2", Color.WHITE, PieceType.KING),
            ("h2", Color.WHITE, PieceType.ROOK),
            ("a2", Color.WHITE, PieceType.PAWN),
            ("e5", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.QUEEN),
            ("d2", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.WHITE,
    )
    king_step = Move(start=sq("e2"), end=sq("e3"))
    rook_shuffle = Move(start=sq("h2"), end=sq("h3"))
    king_bonus = heavy_piece_defense_order_bonus(board, Color.WHITE, PieceType.KING, king_step)
    shuffle_bonus = heavy_piece_defense_order_bonus(
        board,
        Color.WHITE,
        PieceType.ROOK,
        rook_shuffle,
    )
    assert king_bonus > shuffle_bonus


def test_strategy13_transition_prefers_passer_theater_commitment() -> None:
    board = _build_board(
        [
            ("c1", Color.WHITE, PieceType.KING),
            ("d1", Color.WHITE, PieceType.ROOK),
            ("a5", Color.WHITE, PieceType.PAWN),
            ("e4", Color.BLACK, PieceType.KING),
            ("h8", Color.BLACK, PieceType.ROOK),
            ("b7", Color.BLACK, PieceType.PAWN),
            ("g2", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.WHITE,
    )
    commit = Move(start=sq("d1"), end=sq("g1"))
    drift = Move(start=sq("d1"), end=sq("b1"))
    commit_bonus = passer_race_order_bonus(board, Color.WHITE, PieceType.ROOK, commit)
    drift_bonus = passer_race_order_bonus(board, Color.WHITE, PieceType.ROOK, drift)
    assert commit_bonus > drift_bonus


def test_strategy13_transition_demotes_opening_shuffle_in_endgame_context() -> None:
    opening_board = Board()
    opening_board.turn = Color.WHITE
    knight_dev = Move(start=sq("g1"), end=sq("f3"))
    opening_bonus = _opening_root_bonus(opening_board, knight_dev, PieceType.KNIGHT)
    endgame_board = _build_board(
        [
            ("e1", Color.WHITE, PieceType.KING),
            ("g1", Color.WHITE, PieceType.KNIGHT),
            ("e8", Color.BLACK, PieceType.KING),
        ],
        turn=Color.WHITE,
    )
    endgame_bonus = _opening_root_bonus(endgame_board, knight_dev, PieceType.KNIGHT)
    assert opening_bonus != 0
    assert endgame_bonus == 0
