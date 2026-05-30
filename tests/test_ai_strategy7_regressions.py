"""Transcript-driven regressions for STRATEGY7 defense and conversion cleanup."""

import pytest

from chess_game.chess import ai
from chess_game.chess.ai import get_best_move, get_evaluation_breakdown
from chess_game.chess.ai_search_helpers import root_stability_adjustment
from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, LegalMove, PieceType
from tests.helpers import sq
from tests.test_ai_quality import _move_order_score

pytestmark = pytest.mark.slow


def _board_from_moves(moves: list[tuple[str, str]]) -> Board:
    board = Board()
    for start, end in moves:
        board.make_move(sq(start), sq(end))
    return board


def _build_board(
    pieces: list[tuple[str, Color, PieceType]],
    turn: Color = Color.WHITE,
) -> Board:
    board = Board()
    board.clear_board()
    for square, color, kind in pieces:
        board.set_piece(sq(square), create_piece(color, kind))
    board.turn = turn
    return board


def _task1_passer_containment_board() -> Board:
    return _board_from_moves(
        [
            ("b1", "c3"),
            ("e7", "e5"),
            ("g1", "f3"),
            ("b8", "c6"),
            ("c3", "e4"),
            ("d7", "d5"),
            ("e4", "g5"),
            ("e5", "e4"),
            ("g5", "e4"),
            ("c8", "f5"),
            ("e4", "c3"),
            ("f8", "c5"),
            ("g2", "g3"),
            ("g8", "f6"),
            ("d2", "d4"),
            ("c6", "d4"),
            ("f3", "d4"),
            ("f5", "d7"),
            ("c1", "g5"),
            ("e8", "g8"),
            ("c3", "d5"),
            ("h7", "h5"),
            ("g5", "f6"),
            ("g7", "f6"),
            ("e2", "e4"),
            ("f8", "e8"),
            ("d1", "d3"),
            ("h5", "h4"),
            ("e1", "c1"),
            ("e8", "e5"),
            ("f2", "f4"),
            ("e5", "d5"),
            ("e4", "d5"),
            ("c5", "b6"),
            ("g3", "h4"),
            ("g8", "h8"),
            ("f1", "h3"),
            ("d7", "h3"),
            ("d3", "h3"),
            ("c7", "c6"),
            ("d5", "c6"),
            ("b6", "d4"),
            ("c6", "b7"),
            ("a8", "b8"),
            ("h3", "b3"),
        ]
    )


def _task1_heavy_piece_threat_board() -> Board:
    board = _task1_passer_containment_board()
    for start, end in [("a7", "a5"), ("a2", "a4"), ("d8", "d6"), ("h1", "f1")]:
        board.make_move(sq(start), sq(end))
    return board


def _task3_bishop_drift_board() -> Board:
    return _board_from_moves(
        [
            ("b1", "c3"),
            ("e7", "e5"),
            ("g1", "f3"),
            ("b8", "c6"),
            ("c3", "e4"),
            ("d7", "d5"),
            ("e4", "g5"),
            ("e5", "e4"),
            ("g5", "e4"),
            ("c8", "f5"),
            ("e4", "c3"),
            ("f8", "c5"),
            ("g2", "g3"),
            ("g8", "f6"),
            ("d2", "d4"),
            ("c6", "d4"),
            ("f3", "d4"),
            ("f5", "d7"),
            ("c1", "g5"),
            ("e8", "g8"),
            ("c3", "d5"),
            ("h7", "h5"),
            ("g5", "f6"),
            ("g7", "f6"),
            ("e2", "e4"),
            ("f8", "e8"),
            ("d1", "d3"),
            ("h5", "h4"),
            ("e1", "c1"),
            ("e8", "e5"),
            ("f2", "f4"),
            ("e5", "d5"),
            ("e4", "d5"),
            ("c5", "b6"),
            ("g3", "h4"),
            ("g8", "h8"),
        ]
    )


def _task3_queen_trade_board() -> Board:
    return _build_board(
        [
            ("f4", Color.WHITE, PieceType.KING),
            ("d4", Color.WHITE, PieceType.QUEEN),
            ("a4", Color.WHITE, PieceType.ROOK),
            ("b7", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.QUEEN),
            ("b8", Color.BLACK, PieceType.ROOK),
        ]
    )


def _task3_rook_trade_board() -> Board:
    return _build_board(
        [
            ("f4", Color.WHITE, PieceType.KING),
            ("d4", Color.WHITE, PieceType.QUEEN),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("d6", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("a8", Color.BLACK, PieceType.ROOK),
        ]
    )


def _task3_piece_trade_board() -> Board:
    return _build_board(
        [
            ("f4", Color.WHITE, PieceType.KING),
            ("b1", Color.WHITE, PieceType.ROOK),
            ("e5", Color.WHITE, PieceType.BISHOP),
            ("b7", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("b8", Color.BLACK, PieceType.ROOK),
            ("d6", Color.BLACK, PieceType.BISHOP),
        ]
    )


def _task3_rook_support_board() -> Board:
    return _build_board(
        [
            ("f4", Color.WHITE, PieceType.KING),
            ("h1", Color.WHITE, PieceType.ROOK),
            ("b7", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("b8", Color.BLACK, PieceType.ROOK),
        ]
    )


def _task3_queen_escort_board() -> Board:
    return _build_board(
        [
            ("f4", Color.WHITE, PieceType.KING),
            ("d4", Color.WHITE, PieceType.QUEEN),
            ("b7", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("b8", Color.BLACK, PieceType.ROOK),
        ]
    )


def _task5_h5_threat_board() -> Board:
    return _board_from_moves(
        [
            ("b1", "c3"),
            ("e7", "e5"),
            ("g1", "f3"),
            ("b8", "c6"),
            ("c3", "e4"),
            ("d7", "d5"),
            ("e4", "g5"),
            ("e5", "e4"),
            ("g5", "e4"),
            ("c8", "f5"),
            ("e4", "c3"),
            ("f8", "c5"),
            ("g2", "g3"),
            ("g8", "f6"),
            ("d2", "d4"),
            ("c6", "d4"),
            ("f3", "d4"),
            ("f5", "d7"),
            ("c1", "g5"),
            ("e8", "g8"),
            ("c3", "d5"),
        ]
    )


def _task5_passer_response_board() -> Board:
    return _build_board(
        [
            ("g2", Color.WHITE, PieceType.KING),
            ("d4", Color.WHITE, PieceType.QUEEN),
            ("g1", Color.WHITE, PieceType.ROOK),
            ("a2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("b8", Color.BLACK, PieceType.ROOK),
            ("b2", Color.BLACK, PieceType.PAWN),
        ]
    )


def _task5_back_rank_threat_board() -> Board:
    return _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("h1", Color.WHITE, PieceType.ROOK),
            ("d1", Color.WHITE, PieceType.QUEEN),
            ("a2", Color.WHITE, PieceType.PAWN),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("h8", Color.BLACK, PieceType.KING),
            ("h4", Color.BLACK, PieceType.QUEEN),
        ]
    )


def _task6_rook_behind_passer_board() -> Board:
    return _build_board(
        [
            ("g2", Color.WHITE, PieceType.KING),
            ("d4", Color.WHITE, PieceType.QUEEN),
            ("h1", Color.WHITE, PieceType.ROOK),
            ("b6", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("f7", Color.BLACK, PieceType.QUEEN),
            ("a8", Color.BLACK, PieceType.ROOK),
        ]
    )


def _task6_queen_escort_board() -> Board:
    return _build_board(
        [
            ("g2", Color.WHITE, PieceType.KING),
            ("d4", Color.WHITE, PieceType.QUEEN),
            ("d1", Color.WHITE, PieceType.ROOK),
            ("b7", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("f7", Color.BLACK, PieceType.QUEEN),
            ("b8", Color.BLACK, PieceType.ROOK),
        ]
    )


def _task6_king_shelter_board() -> Board:
    return _build_board(
        [
            ("g2", Color.WHITE, PieceType.KING),
            ("d7", Color.WHITE, PieceType.QUEEN),
            ("f6", Color.WHITE, PieceType.ROOK),
            ("c2", Color.WHITE, PieceType.PAWN),
            ("d2", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("h4", Color.BLACK, PieceType.ROOK),
            ("b5", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.BLACK,
    )


def _task6_holdable_queen_trade_board() -> Board:
    return _build_board(
        [
            ("g2", Color.WHITE, PieceType.KING),
            ("d7", Color.WHITE, PieceType.QUEEN),
            ("f6", Color.WHITE, PieceType.ROOK),
            ("c2", Color.WHITE, PieceType.PAWN),
            ("d2", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("h4", Color.BLACK, PieceType.ROOK),
            ("b5", Color.BLACK, PieceType.PAWN),
            ("e7", Color.BLACK, PieceType.QUEEN),
        ],
        turn=Color.BLACK,
    )


def _task7_unstoppable_passer_board() -> Board:
    return _build_board(
        [
            ("g5", Color.WHITE, PieceType.KING),
            ("d4", Color.WHITE, PieceType.QUEEN),
            ("b6", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("h8", Color.BLACK, PieceType.ROOK),
        ]
    )


def _task7_only_blockadable_board() -> Board:
    return _build_board(
        [
            ("g5", Color.WHITE, PieceType.KING),
            ("b6", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("a8", Color.BLACK, PieceType.ROOK),
        ],
        turn=Color.BLACK,
    )


def _task7_queen_escort_race_board() -> Board:
    return _build_board(
        [
            ("g2", Color.WHITE, PieceType.KING),
            ("d4", Color.WHITE, PieceType.QUEEN),
            ("b6", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("b8", Color.BLACK, PieceType.ROOK),
        ]
    )


def _task7_wrong_side_activity_board() -> Board:
    return _build_board(
        [
            ("g5", Color.WHITE, PieceType.KING),
            ("b7", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("e5", Color.BLACK, PieceType.QUEEN),
        ],
        turn=Color.BLACK,
    )


def _task8_queen_drift_board() -> Board:
    return _build_board(
        [
            ("g2", Color.WHITE, PieceType.KING),
            ("d4", Color.WHITE, PieceType.QUEEN),
            ("e2", Color.WHITE, PieceType.BISHOP),
            ("e1", Color.WHITE, PieceType.ROOK),
            ("b7", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("a4", Color.BLACK, PieceType.ROOK),
        ]
    )


def _task8_pawn_drift_board() -> Board:
    return _build_board(
        [
            ("g2", Color.WHITE, PieceType.KING),
            ("d4", Color.WHITE, PieceType.QUEEN),
            ("e1", Color.WHITE, PieceType.ROOK),
            ("b7", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("a4", Color.BLACK, PieceType.ROOK),
        ]
    )


def test_strategy7_order_prefers_capturing_b7_passer_over_a5() -> None:
    """The defending side should tie its rook to the passer instead of drifting on the wing."""

    board = _task1_passer_containment_board()
    contain = ai.Move(start=sq("b8"), end=sq("b7"))
    side_play = ai.Move(start=sq("a7"), end=sq("a5"))

    assert _move_order_score(board, contain, None) > _move_order_score(board, side_play, None)


def test_strategy7_search_rejects_a5_and_stays_on_b_file() -> None:
    """The baseline defense should stay focused on the passer instead of drifting with ...a5."""

    board = _task1_passer_containment_board()
    best_move = get_best_move(board, depth=3)

    assert best_move != LegalMove(start=sq("a7"), end=sq("a5"))
    assert best_move in [
        LegalMove(start=sq("b8"), end=sq("b7")),
        LegalMove(start=sq("d8"), end=sq("d7")),
        LegalMove(start=sq("d8"), end=sq("e7")),
        LegalMove(start=sq("d8"), end=sq("c7")),
    ]


def test_strategy7_order_prefers_rook_containment_over_queen_drift() -> None:
    """Heavy-piece defense should keep the rook tied to the passer over Qa6 drift."""

    board = _task1_heavy_piece_threat_board()
    contain = ai.Move(start=sq("b8"), end=sq("b7"))
    queen_drift = ai.Move(start=sq("d6"), end=sq("a6"))

    assert _move_order_score(board, contain, None) > _move_order_score(board, queen_drift, None)


def test_strategy7_order_prefers_queen_reinforcement_over_a5_panic() -> None:
    """Even non-capturing defense should beat the old side-pawn panic in the baseline."""

    board = _task1_passer_containment_board()
    reinforce = ai.Move(start=sq("d8"), end=sq("d7"))
    side_play = ai.Move(start=sq("a7"), end=sq("a5"))

    assert _move_order_score(board, reinforce, None) > _move_order_score(board, side_play, None)


def test_strategy7_search_rejects_qa6_in_later_heavy_piece_defense() -> None:
    """Later heavy-piece defense should no longer drift into the old Qa6 side line."""

    board = _task1_heavy_piece_threat_board()

    assert get_best_move(board, depth=3) != LegalMove(start=sq("d6"), end=sq("a6"))


def test_strategy7_breakdown_prefers_covering_key_defenders_over_qa6_drift() -> None:
    """Containment should reward covering overloaded defenders over the old queen drift."""

    drift_board = _task1_heavy_piece_threat_board()
    support_board = drift_board.clone()
    support_board.make_move(sq("d6"), sq("d7"))
    drift_board.make_move(sq("d6"), sq("a6"))

    assert (
        get_evaluation_breakdown(support_board)["defensive_containment"]
        < get_evaluation_breakdown(drift_board)["defensive_containment"]
    )


def test_strategy7_search_prefers_queen_trade_in_winning_heavy_piece_probe() -> None:
    """A clearly winning heavy-piece probe should simplify with the queen trade."""

    board = _task3_queen_trade_board()

    assert get_best_move(board, depth=3) == LegalMove(start=sq("d4"), end=sq("d8"))


def test_strategy7_search_prefers_rook_trade_into_winning_queen_ending() -> None:
    """A trivially winning queen ending should justify the immediate rook trade."""

    board = _task3_rook_trade_board()

    assert get_best_move(board, depth=3) == LegalMove(start=sq("a1"), end=sq("a8"))


def test_strategy7_search_prefers_piece_trade_that_leaves_passer_decisive() -> None:
    """The winning side should trade the last minor blocker when the passer survives."""

    board = _task3_piece_trade_board()

    assert get_best_move(board, depth=3) == LegalMove(start=sq("e5"), end=sq("d6"))


def test_strategy7_order_prefers_rook_behind_outside_passer_over_idle_shuffle() -> None:
    """The winning side should get behind the outside passer before harmless rook drift."""

    board = _task3_rook_support_board()
    support = ai.Move(start=sq("h1"), end=sq("b1"))
    drift = ai.Move(start=sq("h1"), end=sq("g1"))

    assert _move_order_score(board, support, None) > _move_order_score(board, drift, None)


def test_strategy7_order_prefers_queen_escort_over_harmless_side_check() -> None:
    """The winning side should escort the main passer rather than throw a side check."""

    board = _task3_queen_escort_board()
    escort = ai.Move(start=sq("d4"), end=sq("d7"))
    side_check = ai.Move(start=sq("d4"), end=sq("h4"))

    assert _move_order_score(board, escort, None) > _move_order_score(
        board,
        side_check,
        None,
    )


def test_strategy7_order_prefers_stabilizing_bishop_move_over_bh3_drift() -> None:
    """The winning side should stabilize before replaying the transcript's Bh3 drift."""

    board = _task3_bishop_drift_board()
    stabilize = ai.Move(start=sq("f1"), end=sq("e2"))
    bishop_drift = ai.Move(start=sq("f1"), end=sq("h3"))

    assert _move_order_score(board, stabilize, None) > _move_order_score(
        board,
        bishop_drift,
        None,
    )


def test_strategy7_search_rejects_bh3_in_winning_conversion_position() -> None:
    """The winning side should stop replaying the transcript's decorative Bh3 drift."""

    board = _task3_bishop_drift_board()
    best_move = get_best_move(board, depth=3)

    assert best_move != LegalMove(start=sq("f1"), end=sq("h3"))
    assert best_move in [
        LegalMove(start=sq("f1"), end=sq("e2")),
        LegalMove(start=sq("f1"), end=sq("g2")),
        LegalMove(start=sq("d3"), end=sq("g3")),
        LegalMove(start=sq("h1"), end=sq("g1")),
    ]


def test_strategy7_order_prefers_c6_over_h5_when_white_threat_is_urgent() -> None:
    """Black should answer White's d5 threat before another speculative h-pawn lunge."""

    board = _task5_h5_threat_board()
    answer_threat = ai.Move(start=sq("c7"), end=sq("c6"))
    side_pawn = ai.Move(start=sq("h7"), end=sq("h5"))

    assert _move_order_score(board, answer_threat, None) > _move_order_score(board, side_pawn, None)


def test_strategy7_order_prefers_luft_over_harmless_check_under_back_rank_threat() -> None:
    """Quiet ordering should fix mate squares before rewarding a decorative queen check."""

    board = _task5_back_rank_threat_board()
    luft = ai.Move(start=sq("g2"), end=sq("g3"))
    harmless_check = ai.Move(start=sq("d1"), end=sq("h5"))

    assert _move_order_score(board, luft, None) > _move_order_score(board, harmless_check, None)


def test_strategy7_root_prefers_contesting_promotion_square_over_side_pawn_push() -> None:
    """Root tie-breaks should answer the enemy passer before a wing pawn push."""

    board = _task5_passer_response_board()
    contest = ai.Move(start=sq("g1"), end=sq("b1"))
    side_pawn = ai.Move(start=sq("a2"), end=sq("a3"))
    contest_child = board.clone()
    side_pawn_child = board.clone()

    assert contest_child.apply_legal_move(contest.start, contest.end) is True
    assert side_pawn_child.apply_legal_move(side_pawn.start, side_pawn.end) is True
    assert root_stability_adjustment(board, contest, contest_child) > root_stability_adjustment(
        board,
        side_pawn,
        side_pawn_child,
    )


def test_strategy7_root_prefers_queen_trade_when_ahead_over_speculative_pressure() -> None:
    """Root tie-breaks should keep preferring simplification over speculative queen drift."""

    board = _task3_queen_trade_board()
    trade = ai.Move(start=sq("d4"), end=sq("d8"))
    speculative = ai.Move(start=sq("d4"), end=sq("h4"))
    trade_child = board.clone()
    speculative_child = board.clone()

    assert trade_child.apply_legal_move(trade.start, trade.end) is True
    assert speculative_child.apply_legal_move(speculative.start, speculative.end) is True
    assert root_stability_adjustment(board, trade, trade_child) > root_stability_adjustment(
        board,
        speculative,
        speculative_child,
    )


def test_strategy7_root_prefers_rook_behind_passer_in_heavy_piece_ending() -> None:
    """Root tie-breaks should favor getting the rook behind the passer over queen drift."""

    board = _task6_rook_behind_passer_board()
    support = ai.Move(start=sq("h1"), end=sq("b1"))
    drift = ai.Move(start=sq("d4"), end=sq("e4"))
    support_child = board.clone()
    drift_child = board.clone()

    assert support_child.apply_legal_move(support.start, support.end) is True
    assert drift_child.apply_legal_move(drift.start, drift.end) is True
    assert root_stability_adjustment(board, support, support_child) > root_stability_adjustment(
        board,
        drift,
        drift_child,
    )


def test_strategy7_root_prefers_queen_escort_toward_promotion_in_heavy_piece_ending() -> None:
    """Root tie-breaks should favor queen escort over harmless rook drift."""

    board = _task6_queen_escort_board()
    escort = ai.Move(start=sq("d4"), end=sq("d7"))
    drift = ai.Move(start=sq("d1"), end=sq("f1"))
    escort_child = board.clone()
    drift_child = board.clone()

    assert escort_child.apply_legal_move(escort.start, escort.end) is True
    assert drift_child.apply_legal_move(drift.start, drift.end) is True
    assert root_stability_adjustment(board, escort, escort_child) > root_stability_adjustment(
        board,
        drift,
        drift_child,
    )


def test_strategy7_eval_defends_king_shelter_before_side_pawn_push() -> None:
    """Heavy-piece evaluation should rate shelter repair above a side-pawn push."""

    board = _task6_king_shelter_board()
    shelter_child = board.clone()
    side_pawn_child = board.clone()

    assert shelter_child.apply_legal_move(sq("g8"), sq("h8")) is True
    assert side_pawn_child.apply_legal_move(sq("b5"), sq("b4")) is True
    assert (
        get_evaluation_breakdown(shelter_child)["heavy_piece_endgame"]
        < get_evaluation_breakdown(side_pawn_child)["heavy_piece_endgame"]
    )


def test_strategy7_search_prefers_queen_trade_into_holdable_heavy_piece_ending() -> None:
    """The worse side should still simplify into the holdable queenless ending."""

    board = _task6_holdable_queen_trade_board()

    assert get_best_move(board, depth=3) == LegalMove(start=sq("e7"), end=sq("d7"))


def test_strategy7_eval_rewards_creating_unstoppable_passer() -> None:
    """Passed-pawn race evaluation should value the push that wins the tempo race."""

    board = _task7_unstoppable_passer_board()
    push_child = board.clone()
    side_check_child = board.clone()

    assert push_child.apply_legal_move(sq("b6"), sq("b7")) is True
    assert side_check_child.apply_legal_move(sq("d4"), sq("e5")) is True
    assert (
        get_evaluation_breakdown(push_child)["passer_race"]
        > get_evaluation_breakdown(side_check_child)["passer_race"]
    )


def test_strategy7_search_prefers_only_blockade_move_in_passer_race() -> None:
    """When the passer can only be stopped by a blockade, search should find it."""

    board = _task7_only_blockadable_board()

    assert get_best_move(board, depth=3) == LegalMove(start=sq("a8"), end=sq("b8"))


def test_strategy7_root_prefers_queen_escort_when_it_wins_the_race() -> None:
    """Root tie-breaks should favor escorting the pawn over a decorative queen move."""

    board = _task7_queen_escort_race_board()
    escort = ai.Move(start=sq("d4"), end=sq("b2"))
    drift = ai.Move(start=sq("d4"), end=sq("e5"))
    escort_child = board.clone()
    drift_child = board.clone()

    assert escort_child.apply_legal_move(escort.start, escort.end) is True
    assert drift_child.apply_legal_move(drift.start, drift.end) is True
    assert root_stability_adjustment(board, escort, escort_child) > root_stability_adjustment(
        board,
        drift,
        drift_child,
    )


def test_strategy7_search_prefers_stopping_enemy_race_over_wrong_side_check() -> None:
    """Search should stop the b-pawn race instead of spending a move on a flashy check."""

    board = _task7_wrong_side_activity_board()

    assert get_best_move(board, depth=3) == LegalMove(start=sq("e5"), end=sq("b8"))


def test_strategy7_order_prefers_queen_support_over_idle_queen_drift() -> None:
    """Clearly won endings should reject queen moves that change nothing."""

    board = _task8_queen_drift_board()
    support = ai.Move(start=sq("d4"), end=sq("d7"))
    drift = ai.Move(start=sq("d4"), end=sq("e5"))
    support_child = board.clone()
    drift_child = board.clone()

    assert support_child.apply_legal_move(support.start, support.end) is True
    assert drift_child.apply_legal_move(drift.start, drift.end) is True
    assert root_stability_adjustment(board, support, support_child) > root_stability_adjustment(
        board,
        drift,
        drift_child,
    )


def test_strategy7_order_prefers_bishop_support_over_bishop_shuffle() -> None:
    """A bishop should support the main passer instead of shuffling away from it."""

    board = _task8_queen_drift_board()
    support = ai.Move(start=sq("e2"), end=sq("d3"))
    shuffle = ai.Move(start=sq("e2"), end=sq("f1"))
    support_child = board.clone()
    shuffle_child = board.clone()

    assert support_child.apply_legal_move(support.start, support.end) is True
    assert shuffle_child.apply_legal_move(shuffle.start, shuffle.end) is True
    assert root_stability_adjustment(board, support, support_child) > root_stability_adjustment(
        board,
        shuffle,
        shuffle_child,
    )


def test_strategy7_order_prefers_rook_support_over_rook_drift() -> None:
    """A rook should stay tied to the winning passer instead of sliding sideways."""

    board = _task8_queen_drift_board()
    support = ai.Move(start=sq("e1"), end=sq("b1"))
    drift = ai.Move(start=sq("e1"), end=sq("f1"))
    support_child = board.clone()
    drift_child = board.clone()

    assert support_child.apply_legal_move(support.start, support.end) is True
    assert drift_child.apply_legal_move(drift.start, drift.end) is True
    assert root_stability_adjustment(board, support, support_child) > root_stability_adjustment(
        board,
        drift,
        drift_child,
    )


def test_strategy7_order_prefers_main_passer_push_over_side_pawn_drift() -> None:
    """A side pawn push should lose to the ready outside passer in a practical ending."""

    board = _task8_pawn_drift_board()
    direct_push = ai.Move(start=sq("b7"), end=sq("b8"), promotion=PieceType.QUEEN)
    side_push = ai.Move(start=sq("h2"), end=sq("h3"))
    direct_child = board.clone()
    side_child = board.clone()

    assert direct_child.apply_legal_move(
        direct_push.start,
        direct_push.end,
        promotion=direct_push.promotion,
    ) is True
    assert side_child.apply_legal_move(side_push.start, side_push.end) is True
    assert root_stability_adjustment(board, direct_push, direct_child) > root_stability_adjustment(
        board,
        side_push,
        side_child,
    )
