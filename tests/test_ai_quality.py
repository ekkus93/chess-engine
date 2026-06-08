"""Quality-focused tests for evaluator tuning, repetition keys, and root search."""

from __future__ import annotations

import pytest

from chess_game.chess import ai
from chess_game.chess.ai import (
    INF,
    SearchContext,
    SearchStats,
    _move_order_score,
    _quiescence_capture_score,
    _quiescence_check_score,
    _quiescence_tactical_score,
    get_best_move,
    get_evaluation_breakdown,
    minimax,
    position_key,
    quiescence,
)
from chess_game.chess.ai_search_helpers import RepetitionPolicy, repetition_score
from chess_game.chess.board import Board, create_piece
from chess_game.chess.move import Move
from chess_game.chess.types import Color, LegalMove, PieceType
from tests.helpers import sq


def _empty_board_with_kings() -> Board:
    board = Board()
    board.clear_board()
    board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.WHITE
    return board


def test_mobility_bonus_prefers_active_knight() -> None:
    """An active central knight should outscore a cramped edge knight."""

    active_board = _empty_board_with_kings()
    active_board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.KNIGHT))

    passive_board = _empty_board_with_kings()
    passive_board.set_piece(sq("a2"), create_piece(Color.WHITE, PieceType.KNIGHT))

    assert ai.evaluate(active_board) > ai.evaluate(passive_board)


def test_isolated_pawn_penalty_prefers_connected_pawns() -> None:
    """Connected pawns should outscore isolated pawns with equal material."""

    connected_board = _empty_board_with_kings()
    connected_board.set_piece(sq("c4"), create_piece(Color.WHITE, PieceType.PAWN))
    connected_board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.PAWN))

    isolated_board = _empty_board_with_kings()
    isolated_board.set_piece(sq("c4"), create_piece(Color.WHITE, PieceType.PAWN))
    isolated_board.set_piece(sq("f4"), create_piece(Color.WHITE, PieceType.PAWN))

    assert ai.evaluate(connected_board) > ai.evaluate(isolated_board)


def test_doubled_pawn_penalty_prefers_healthier_files() -> None:
    """Doubled pawns should score worse than a healthy pawn chain."""

    healthy_board = _empty_board_with_kings()
    healthy_board.set_piece(sq("c4"), create_piece(Color.WHITE, PieceType.PAWN))
    healthy_board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.PAWN))

    doubled_board = _empty_board_with_kings()
    doubled_board.set_piece(sq("c4"), create_piece(Color.WHITE, PieceType.PAWN))
    doubled_board.set_piece(sq("c3"), create_piece(Color.WHITE, PieceType.PAWN))

    assert ai.evaluate(healthy_board) > ai.evaluate(doubled_board)


def test_passed_pawn_bonus_scales_with_advancement() -> None:
    """A more advanced passed pawn should outscore a less advanced one."""

    advanced_board = _empty_board_with_kings()
    advanced_board.set_piece(sq("e6"), create_piece(Color.WHITE, PieceType.PAWN))

    less_advanced_board = _empty_board_with_kings()
    less_advanced_board.set_piece(sq("e3"), create_piece(Color.WHITE, PieceType.PAWN))

    assert ai.evaluate(advanced_board) > ai.evaluate(less_advanced_board)


def test_castled_king_scores_better_than_exposed_king() -> None:
    """King shelter should matter in middlegame-like positions."""

    castled_board = _empty_board_with_kings()
    castled_board.clear_board()
    castled_board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    castled_board.set_piece(sq("f2"), create_piece(Color.WHITE, PieceType.PAWN))
    castled_board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.PAWN))
    castled_board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))
    castled_board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.ROOK))
    castled_board.set_piece(sq("f1"), create_piece(Color.WHITE, PieceType.ROOK))
    castled_board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.QUEEN))
    castled_board.set_piece(sq("c4"), create_piece(Color.WHITE, PieceType.BISHOP))
    castled_board.set_piece(sq("f3"), create_piece(Color.WHITE, PieceType.KNIGHT))
    castled_board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    castled_board.set_piece(sq("a8"), create_piece(Color.BLACK, PieceType.ROOK))
    castled_board.set_piece(sq("f8"), create_piece(Color.BLACK, PieceType.ROOK))
    castled_board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))
    castled_board.set_piece(sq("c8"), create_piece(Color.BLACK, PieceType.BISHOP))
    castled_board.set_piece(sq("f6"), create_piece(Color.BLACK, PieceType.KNIGHT))

    exposed_board = castled_board.clone()
    exposed_board.clear_square(sq("g1"))
    exposed_board.clear_square(sq("f1"))
    exposed_board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    exposed_board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))

    assert ai.evaluate(castled_board) > ai.evaluate(exposed_board)


def test_king_exposure_breakdown_penalizes_central_king_with_queens() -> None:
    """A central king with queens and rooks on the board should look more exposed."""

    safe_board = _empty_board_with_kings()
    safe_board.clear_board()
    safe_board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    safe_board.set_piece(sq("f2"), create_piece(Color.WHITE, PieceType.PAWN))
    safe_board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.PAWN))
    safe_board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))
    safe_board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    safe_board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.ROOK))
    safe_board.set_piece(sq("f1"), create_piece(Color.WHITE, PieceType.ROOK))
    safe_board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    safe_board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))
    safe_board.set_piece(sq("a8"), create_piece(Color.BLACK, PieceType.ROOK))
    safe_board.set_piece(sq("f8"), create_piece(Color.BLACK, PieceType.ROOK))

    exposed_board = safe_board.clone()
    exposed_board.clear_square(sq("g1"))
    exposed_board.clear_square(sq("f1"))
    exposed_board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.KING))
    exposed_board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))

    assert (
        get_evaluation_breakdown(safe_board)["king_exposure"]
        > get_evaluation_breakdown(exposed_board)["king_exposure"]
    )


def test_defender_coordination_breakdown_prefers_nearby_heavy_pieces() -> None:
    """Heavy pieces should score better when they stay connected to king defense."""

    connected_board = _empty_board_with_kings()
    connected_board.clear_board()
    connected_board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    connected_board.set_piece(sq("d2"), create_piece(Color.WHITE, PieceType.QUEEN))
    connected_board.set_piece(sq("f1"), create_piece(Color.WHITE, PieceType.ROOK))
    connected_board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    connected_board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))

    disconnected_board = connected_board.clone()
    disconnected_board.clear_square(sq("d2"))
    disconnected_board.clear_square(sq("f1"))
    disconnected_board.set_piece(sq("h6"), create_piece(Color.WHITE, PieceType.QUEEN))
    disconnected_board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.ROOK))

    assert (
        get_evaluation_breakdown(connected_board)["defender_coordination"]
        > get_evaluation_breakdown(disconnected_board)["defender_coordination"]
    )


def test_bishop_pair_breakdown_reports_bonus() -> None:
    """Evaluation breakdown should expose the bishop-pair bonus."""

    board = _empty_board_with_kings()
    board.set_piece(sq("c4"), create_piece(Color.WHITE, PieceType.BISHOP))
    board.set_piece(sq("f4"), create_piece(Color.WHITE, PieceType.BISHOP))

    assert get_evaluation_breakdown(board)["bishop_pair"] > 0


def test_rook_on_open_file_breakdown_reports_bonus() -> None:
    """Rook activity should reward an open file."""

    open_file_board = _empty_board_with_kings()
    open_file_board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.ROOK))

    blocked_file_board = open_file_board.clone()
    blocked_file_board.set_piece(sq("d2"), create_piece(Color.WHITE, PieceType.PAWN))

    assert (
        get_evaluation_breakdown(open_file_board)["rook_activity"]
        > get_evaluation_breakdown(blocked_file_board)["rook_activity"]
    )


def test_position_key_distinguishes_castling_rights() -> None:
    """Threefold repetition keys must include castling rights."""

    board_a = Board()
    board_b = Board()
    board_b.castling_rights.white_kingside = False

    assert position_key(board_a) != position_key(board_b)


def test_position_key_distinguishes_en_passant_targets() -> None:
    """Threefold repetition keys must include the en passant square."""

    board_a = Board()
    board_b = Board()
    board_b.en_passant_target = sq("e3")

    assert position_key(board_a) != position_key(board_b)


@pytest.mark.slow
def test_iterative_deepening_matches_full_width_root_result() -> None:
    """Iterative deepening should agree with the full-width root result on a simple tactic."""

    board = _empty_board_with_kings()
    board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("d5"), create_piece(Color.BLACK, PieceType.ROOK))

    direct_score, direct_move = ai.search_root_depth(
        board,
        depth=2,
        is_maximizing=True,
        previous_score=0,
        context=SearchContext(transposition_table={}, killer_moves=[]),
    )
    best_move = get_best_move(board, depth=2)

    assert direct_score > 0
    assert best_move == direct_move


def test_root_fail_high_reruns_full_window(monkeypatch) -> None:
    """A fail-high aspiration result should trigger one full-window re-search."""

    calls: list[tuple[int, int]] = []
    legal_move = LegalMove(start=sq("e2"), end=sq("e4"))

    def fake_minimax(_board, params):
        calls.append((params.alpha, params.beta))
        if len(calls) == 1:
            return params.beta, legal_move
        return 12, legal_move

    monkeypatch.setattr(ai, "minimax", fake_minimax)
    stats = SearchStats()
    board = Board()
    score, move = ai.search_root_depth(
        board,
        depth=2,
        is_maximizing=True,
        previous_score=0,
        context=SearchContext(stats=stats),
    )

    assert calls[0] == (-ai.ASPIRATION_WINDOW, ai.ASPIRATION_WINDOW)
    assert calls[1] == (-ai.INF, ai.INF)
    assert stats.fail_high_retries == 1
    assert score == 12
    assert move == legal_move


def test_root_fail_low_reruns_full_window(monkeypatch) -> None:
    """A fail-low aspiration result should trigger one full-window re-search."""

    calls: list[tuple[int, int]] = []
    legal_move = LegalMove(start=sq("e2"), end=sq("e4"))

    def fake_minimax(_board, params):
        calls.append((params.alpha, params.beta))
        if len(calls) == 1:
            return params.alpha, legal_move
        return -12, legal_move

    monkeypatch.setattr(ai, "minimax", fake_minimax)
    stats = SearchStats()
    score, move = ai.search_root_depth(
        Board(),
        depth=2,
        is_maximizing=True,
        previous_score=0,
        context=SearchContext(stats=stats),
    )

    assert calls[0] == (-ai.ASPIRATION_WINDOW, ai.ASPIRATION_WINDOW)
    assert calls[1] == (-ai.INF, ai.INF)
    assert stats.fail_low_retries == 1
    assert score == -12
    assert move == legal_move


def test_quiescence_counts_tactical_leaf_nodes() -> None:
    """Depth-zero search should enter quiescence on tactical positions."""

    board = _empty_board_with_kings()
    board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("d5"), create_piece(Color.BLACK, PieceType.ROOK))
    stats = SearchStats()

    minimax(
        board,
        ai.MinimaxParams(
            depth=0,
            alpha=-INF,
            beta=INF,
            is_maximizing=True,
            context=SearchContext(stats=stats),
        ),
    )

    assert stats.quiescence_nodes > 0


def test_quiescence_values_undefended_capture_above_defended_capture() -> None:
    """Quiescence should downgrade captures that lose material to recapture."""

    undefended_board = _empty_board_with_kings()
    undefended_board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.QUEEN))
    undefended_board.set_piece(sq("d5"), create_piece(Color.BLACK, PieceType.ROOK))

    defended_board = undefended_board.clone()
    defended_board.set_piece(sq("e5"), create_piece(Color.BLACK, PieceType.QUEEN))

    score_undefended = quiescence(undefended_board, -INF, INF, True)
    score_defended = quiescence(defended_board, -INF, INF, True)

    assert score_undefended > score_defended


def test_quiescence_capture_score_prefers_king_shelter_recovery() -> None:
    """Quiescence should keep a shelter-restoring capture over a side pawn grab."""

    board = _empty_board_with_kings()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("a2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("h3"), create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(sq("a3"), create_piece(Color.BLACK, PieceType.PAWN))

    shelter_move = Move(start=sq("g2"), end=sq("h3"))
    side_move = Move(start=sq("a2"), end=sq("a3"))
    shelter_board = board.clone()
    side_board = board.clone()
    assert shelter_board.apply_legal_move(shelter_move.start, shelter_move.end) is True
    assert side_board.apply_legal_move(side_move.start, side_move.end) is True

    shelter_score = _quiescence_capture_score(
        board,
        shelter_move,
        shelter_board,
        Color.WHITE,
    )
    side_score = _quiescence_capture_score(board, side_move, side_board, Color.WHITE)

    assert shelter_score > side_score
    assert shelter_score > 0


def test_quiescence_check_score_ignores_harmless_knight_check() -> None:
    """Quiescence should skip checks that do not materially change king safety."""

    board = _empty_board_with_kings()
    board.clear_board()
    board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(sq("f7"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("c5"), create_piece(Color.BLACK, PieceType.ROOK))
    board.turn = Color.WHITE

    checking_move = Move(start=sq("e4"), end=sq("d6"))
    child_board = board.clone()
    assert child_board.apply_legal_move(checking_move.start, checking_move.end) is True

    assert _quiescence_check_score(board, child_board, Color.BLACK) == 0


def test_quiescence_tactical_score_prefers_structural_capture_followup() -> None:
    """Quiescence should keep captures that change pawn structure ahead of side grabs."""

    board = _empty_board_with_kings()
    board.clear_board()
    board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("b5"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d5"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("c6"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE

    target_capture = Move(start=sq("e4"), end=sq("d5"))
    structural_capture = Move(start=sq("b5"), end=sq("c6"))
    target_board = board.clone()
    structural_board = board.clone()
    assert target_board.apply_legal_move(target_capture.start, target_capture.end) is True
    assert (
        structural_board.apply_legal_move(
            structural_capture.start,
            structural_capture.end,
        )
        is True
    )

    target_score = _quiescence_tactical_score(board, target_capture)
    structural_score = _quiescence_tactical_score(board, structural_capture)

    assert structural_score > target_score
    assert structural_score > 0


@pytest.mark.slow
def test_simple_quality_benchmark_prefers_hanging_rook_capture() -> None:
    """The search should take an obvious hanging rook in a simple benchmark."""

    board = _empty_board_with_kings()
    board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("d5"), create_piece(Color.BLACK, PieceType.ROOK))

    best_move = get_best_move(board, depth=2)

    assert best_move == LegalMove(start=sq("d4"), end=sq("d5"))


def test_knight_outpost_scores_better_than_loose_knight() -> None:
    """A supported knight outpost should outscore a loose central knight."""

    outpost_board = _empty_board_with_kings()
    outpost_board.set_piece(sq("d6"), create_piece(Color.WHITE, PieceType.KNIGHT))
    outpost_board.set_piece(sq("e5"), create_piece(Color.WHITE, PieceType.PAWN))

    loose_board = _empty_board_with_kings()
    loose_board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.KNIGHT))

    assert ai.evaluate(outpost_board) > ai.evaluate(loose_board)


def test_bad_bishop_scores_worse_than_active_bishop() -> None:
    """A bishop boxed in by same-color pawns should be penalized."""

    active_board = _empty_board_with_kings()
    active_board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.BISHOP))
    active_board.set_piece(sq("c4"), create_piece(Color.WHITE, PieceType.PAWN))
    active_board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.PAWN))
    active_board.set_piece(sq("g3"), create_piece(Color.WHITE, PieceType.PAWN))

    bad_board = _empty_board_with_kings()
    bad_board.set_piece(sq("c1"), create_piece(Color.WHITE, PieceType.BISHOP))
    bad_board.set_piece(sq("b2"), create_piece(Color.WHITE, PieceType.PAWN))
    bad_board.set_piece(sq("d2"), create_piece(Color.WHITE, PieceType.PAWN))
    bad_board.set_piece(sq("e3"), create_piece(Color.WHITE, PieceType.PAWN))

    assert ai.evaluate(active_board) > ai.evaluate(bad_board)


def test_trapped_rook_scores_worse_than_active_rook() -> None:
    """A rook boxed behind its own pawns should be penalized."""

    active_board = _empty_board_with_kings()
    active_board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.ROOK))
    active_board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.PAWN))
    active_board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))

    trapped_board = _empty_board_with_kings()
    trapped_board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))
    trapped_board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.PAWN))
    trapped_board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))

    assert ai.evaluate(active_board) > ai.evaluate(trapped_board)


def test_active_king_in_endgame_scores_better_than_passive_king() -> None:
    """Endgame king centralization should be rewarded."""

    active_board = _empty_board_with_kings()
    active_board.clear_board()
    active_board.set_piece(sq("f5"), create_piece(Color.WHITE, PieceType.KING))
    active_board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    active_board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.ROOK))

    passive_board = active_board.clone()
    passive_board.clear_square(sq("f5"))
    passive_board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))

    assert ai.evaluate(active_board) > ai.evaluate(passive_board)


def test_space_advantage_scores_better_than_cramped_setup() -> None:
    """A side with stable central space should be rewarded."""

    space_board = _empty_board_with_kings()
    space_board.set_piece(sq("c4"), create_piece(Color.WHITE, PieceType.PAWN))
    space_board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.PAWN))
    space_board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.PAWN))
    space_board.set_piece(sq("f4"), create_piece(Color.WHITE, PieceType.PAWN))
    space_board.set_piece(sq("c3"), create_piece(Color.WHITE, PieceType.KNIGHT))
    space_board.set_piece(sq("f3"), create_piece(Color.WHITE, PieceType.KNIGHT))

    cramped_board = _empty_board_with_kings()
    cramped_board.set_piece(sq("c2"), create_piece(Color.WHITE, PieceType.PAWN))
    cramped_board.set_piece(sq("d2"), create_piece(Color.WHITE, PieceType.PAWN))
    cramped_board.set_piece(sq("e2"), create_piece(Color.WHITE, PieceType.PAWN))
    cramped_board.set_piece(sq("f2"), create_piece(Color.WHITE, PieceType.PAWN))
    cramped_board.set_piece(sq("b1"), create_piece(Color.WHITE, PieceType.KNIGHT))
    cramped_board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KNIGHT))

    assert ai.evaluate(space_board) > ai.evaluate(cramped_board)


def test_minor_piece_coordination_scores_better_than_scattered_pieces() -> None:
    """Coordinated minor pieces should outscore awkward scattered ones."""

    coordinated_board = _empty_board_with_kings()
    coordinated_board.set_piece(sq("d5"), create_piece(Color.WHITE, PieceType.KNIGHT))
    coordinated_board.set_piece(sq("c4"), create_piece(Color.WHITE, PieceType.BISHOP))
    coordinated_board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.PAWN))

    scattered_board = _empty_board_with_kings()
    scattered_board.set_piece(sq("a2"), create_piece(Color.WHITE, PieceType.KNIGHT))
    scattered_board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.BISHOP))
    scattered_board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.PAWN))

    assert ai.evaluate(coordinated_board) > ai.evaluate(scattered_board)


def test_simplified_winning_position_scores_better_when_ahead() -> None:
    """When ahead, a simplified winning position should be preferred."""

    simplified_board = _empty_board_with_kings()
    simplified_board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.ROOK))

    unsimplified_board = simplified_board.clone()
    unsimplified_board.set_piece(sq("d5"), create_piece(Color.WHITE, PieceType.QUEEN))
    unsimplified_board.set_piece(sq("d7"), create_piece(Color.BLACK, PieceType.QUEEN))

    assert ai.evaluate(simplified_board) > ai.evaluate(unsimplified_board)


def test_conversion_breakdown_rewards_rooks_off_when_ahead() -> None:
    """A winning side should value trading off the defender's last rook."""

    rookless_board = _empty_board_with_kings()
    rookless_board.clear_board()
    rookless_board.set_piece(sq("g3"), create_piece(Color.WHITE, PieceType.KING))
    rookless_board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.ROOK))
    rookless_board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))
    rookless_board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.KING))

    defended_board = rookless_board.clone()
    defended_board.clear_square(sq("h1"))
    defended_board.set_piece(sq("a8"), create_piece(Color.BLACK, PieceType.ROOK))

    assert (
        get_evaluation_breakdown(rookless_board)["conversion"]
        > get_evaluation_breakdown(defended_board)["conversion"]
    )


def test_endgame_technique_rewards_driving_king_to_edge() -> None:
    """Basic mating-material endings should reward reducing the enemy king box."""

    edge_board = _empty_board_with_kings()
    edge_board.clear_board()
    edge_board.set_piece(sq("f5"), create_piece(Color.WHITE, PieceType.KING))
    edge_board.set_piece(sq("d5"), create_piece(Color.WHITE, PieceType.QUEEN))
    edge_board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))

    center_board = edge_board.clone()
    center_board.clear_square(sq("h8"))
    center_board.set_piece(sq("e5"), create_piece(Color.BLACK, PieceType.KING))

    assert (
        get_evaluation_breakdown(edge_board)["endgame_technique"]
        > get_evaluation_breakdown(center_board)["endgame_technique"]
    )


def test_two_rooks_mating_material_reports_endgame_bonus() -> None:
    """KRR vs K should register a positive endgame-technique bonus."""

    board = _empty_board_with_kings()
    board.clear_board()
    board.set_piece(sq("f5"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("a5"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("h5"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))

    assert get_evaluation_breakdown(board)["endgame_technique"] > 0


def test_development_breakdown_penalizes_unsupported_early_queen_raid() -> None:
    """An advanced unsupported queen raid should score worse than a restrained queen."""

    restrained_board = _empty_board_with_kings()
    restrained_board.clear_board()
    restrained_board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    restrained_board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    restrained_board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.ROOK))
    restrained_board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))
    restrained_board.set_piece(sq("b1"), create_piece(Color.WHITE, PieceType.KNIGHT))
    restrained_board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KNIGHT))
    restrained_board.set_piece(sq("c1"), create_piece(Color.WHITE, PieceType.BISHOP))
    restrained_board.set_piece(sq("f1"), create_piece(Color.WHITE, PieceType.BISHOP))
    restrained_board.set_piece(sq("e8"), create_piece(Color.BLACK, PieceType.KING))
    restrained_board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.QUEEN))
    restrained_board.set_piece(sq("a8"), create_piece(Color.BLACK, PieceType.ROOK))
    restrained_board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.ROOK))
    restrained_board.set_piece(sq("b8"), create_piece(Color.BLACK, PieceType.KNIGHT))
    restrained_board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KNIGHT))
    restrained_board.set_piece(sq("c8"), create_piece(Color.BLACK, PieceType.BISHOP))
    restrained_board.set_piece(sq("f8"), create_piece(Color.BLACK, PieceType.BISHOP))

    raiding_board = restrained_board.clone()
    raiding_board.clear_square(sq("d1"))
    raiding_board.set_piece(sq("h6"), create_piece(Color.WHITE, PieceType.QUEEN))

    assert (
        get_evaluation_breakdown(restrained_board)["development"]
        > get_evaluation_breakdown(raiding_board)["development"]
    )


def test_development_breakdown_rewards_castling_ready_setup() -> None:
    """A setup ready to castle should score better than an undeveloped queen-first setup."""

    ready_board = Board()
    ready_board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KNIGHT))
    ready_board.clear_square(sq("g1"))
    ready_board.set_piece(sq("f3"), create_piece(Color.WHITE, PieceType.KNIGHT))
    ready_board.clear_square(sq("f1"))
    ready_board.set_piece(sq("c4"), create_piece(Color.WHITE, PieceType.BISHOP))

    unready_board = Board()
    unready_board.clear_square(sq("d1"))
    unready_board.set_piece(sq("h5"), create_piece(Color.WHITE, PieceType.QUEEN))

    assert (
        get_evaluation_breakdown(ready_board)["development"]
        > get_evaluation_breakdown(unready_board)["development"]
    )


def test_development_breakdown_penalizes_early_rook_wander() -> None:
    """A rook wander before development and castling should be penalized."""

    stable_board = Board()

    wandering_board = Board()
    wandering_board.clear_square(sq("h1"))
    wandering_board.set_piece(sq("h3"), create_piece(Color.WHITE, PieceType.ROOK))

    assert (
        get_evaluation_breakdown(stable_board)["development"]
        > get_evaluation_breakdown(wandering_board)["development"]
    )




def test_search_prefers_castling_in_quiet_position() -> None:
    """Search should choose castling when it is the best quiet king-safety improvement."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))
    # Bishop at e3 (not c4) so the diagonal to g8 is not open and the
    # initial position is legal (Black king not already in check).
    board.set_piece(sq("e3"), create_piece(Color.WHITE, PieceType.BISHOP))
    board.set_piece(sq("f3"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(sq("d2"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("f2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("a8"), create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(sq("b7"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.set_piece(sq("c8"), create_piece(Color.BLACK, PieceType.BISHOP))
    board.set_piece(sq("f6"), create_piece(Color.BLACK, PieceType.KNIGHT))
    board.turn = Color.WHITE

    best_move = get_best_move(board, depth=1)

    assert best_move == LegalMove(start=sq("e1"), end=sq("g1"))


def test_quiet_move_order_prefers_castling_over_idle_rook_move() -> None:
    """Quiet move ordering should prefer castling over low-value rook shuffles."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("c4"), create_piece(Color.WHITE, PieceType.BISHOP))
    board.set_piece(sq("f3"), create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(sq("d2"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("f2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.WHITE

    castling_move = ai.Move(start=sq("e1"), end=sq("g1"))
    rook_shuffle = ai.Move(start=sq("h1"), end=sq("h3"))

    assert _move_order_score(board, castling_move, None) > _move_order_score(
        board,
        rook_shuffle,
        None,
    )


def test_quiet_move_order_prefers_developing_knight_over_early_queen_sortie() -> None:
    """Opening move ordering should favor development over a premature queen sortie."""

    board = Board()
    developing_move = ai.Move(start=sq("g1"), end=sq("f3"))
    queen_sortie = ai.Move(start=sq("d1"), end=sq("h5"))

    assert _move_order_score(board, developing_move, None) > _move_order_score(
        board,
        queen_sortie,
        None,
    )




def test_quiet_move_order_prefers_useful_check_over_flank_queen_drift() -> None:
    """A direct checking move should outrank a harmless queen drift."""

    board = _empty_board_with_kings()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("c4"), create_piece(Color.WHITE, PieceType.BISHOP))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("h7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(sq("a8"), create_piece(Color.BLACK, PieceType.ROOK))
    board.turn = Color.WHITE

    useful_check = ai.Move(start=sq("d1"), end=sq("d8"))
    queen_drift = ai.Move(start=sq("d1"), end=sq("h5"))

    assert _move_order_score(board, useful_check, None) > _move_order_score(
        board,
        queen_drift,
        None,
    )


def test_quiet_move_order_prefers_urgent_luft_under_back_rank_pressure() -> None:
    """Back-rank pressure should make a luft move outrank an idle pawn move."""

    board = _empty_board_with_kings()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(sq("h4"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.turn = Color.WHITE

    luft_move = ai.Move(start=sq("h2"), end=sq("h3"))
    idle_move = ai.Move(start=sq("a2"), end=sq("a3"))

    assert _move_order_score(board, luft_move, None) > _move_order_score(
        board,
        idle_move,
        None,
    )


def test_quiet_move_order_prefers_contesting_attack_file_over_side_pawn_push() -> None:
    """Defensive interposition on an attack file should outrank an idle side pawn push."""

    board = _empty_board_with_kings()
    board.clear_board()
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("a2"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("e2"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("a3"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d8"), create_piece(Color.BLACK, PieceType.ROOK))
    board.turn = Color.WHITE

    contest_move = ai.Move(start=sq("a2"), end=sq("d2"))
    side_pawn_push = ai.Move(start=sq("a3"), end=sq("a4"))

    assert _move_order_score(board, contest_move, None) > _move_order_score(
        board,
        side_pawn_push,
        None,
    )


@pytest.mark.slow
def test_search_prefers_luft_over_empty_check_under_back_rank_pressure() -> None:
    """Under back-rank pressure, the search should prefer luft over a harmless queen check."""

    board = _empty_board_with_kings()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("h4"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.turn = Color.WHITE

    best_move = get_best_move(board, depth=2)

    assert best_move == LegalMove(start=sq("g2"), end=sq("g3"))




def test_progress_breakdown_rewards_rook_cutoff() -> None:
    """A rook cutting off the enemy king should improve the progress breakdown."""

    cutoff_board = _empty_board_with_kings()
    cutoff_board.clear_board()
    cutoff_board.set_piece(sq("f5"), create_piece(Color.WHITE, PieceType.KING))
    cutoff_board.set_piece(sq("e7"), create_piece(Color.WHITE, PieceType.ROOK))
    cutoff_board.set_piece(sq("d5"), create_piece(Color.WHITE, PieceType.PAWN))
    cutoff_board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.KING))

    loose_board = cutoff_board.clone()
    loose_board.clear_square(sq("e7"))
    loose_board.set_piece(sq("a7"), create_piece(Color.WHITE, PieceType.ROOK))

    assert (
        get_evaluation_breakdown(cutoff_board)["progress"]
        > get_evaluation_breakdown(loose_board)["progress"]
    )


def test_progress_breakdown_rewards_rook_behind_passed_pawn() -> None:
    """A rook behind its own passed pawn should be rewarded."""

    behind_board = _empty_board_with_kings()
    behind_board.clear_board()
    behind_board.set_piece(sq("f4"), create_piece(Color.WHITE, PieceType.KING))
    behind_board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.ROOK))
    behind_board.set_piece(sq("d5"), create_piece(Color.WHITE, PieceType.PAWN))
    behind_board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.KING))

    side_board = behind_board.clone()
    side_board.clear_square(sq("d1"))
    side_board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.ROOK))

    assert (
        get_evaluation_breakdown(behind_board)["progress"]
        > get_evaluation_breakdown(side_board)["progress"]
    )


def test_progress_breakdown_rewards_king_escort_of_passed_pawn() -> None:
    """A king escorting its passed pawn should improve progress scoring."""

    escorted_board = _empty_board_with_kings()
    escorted_board.clear_board()
    escorted_board.set_piece(sq("e5"), create_piece(Color.WHITE, PieceType.KING))
    escorted_board.set_piece(sq("d6"), create_piece(Color.WHITE, PieceType.PAWN))
    escorted_board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))

    distant_board = escorted_board.clone()
    distant_board.clear_square(sq("e5"))
    distant_board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.KING))

    assert (
        get_evaluation_breakdown(escorted_board)["progress"]
        > get_evaluation_breakdown(distant_board)["progress"]
    )


def test_quiet_move_order_prefers_rook_behind_passed_pawn_move() -> None:
    """Quiet move ordering should prefer bringing a rook behind a passed pawn."""

    board = _empty_board_with_kings()
    board.clear_board()
    board.set_piece(sq("f4"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("d5"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.WHITE

    behind_move = ai.Move(start=sq("a1"), end=sq("d1"))
    side_move = ai.Move(start=sq("a1"), end=sq("a5"))

    assert _move_order_score(board, behind_move, None) > _move_order_score(
        board,
        side_move,
        None,
    )


def test_search_prefers_king_centralization_in_winning_rook_endgame() -> None:
    """Search should activate the king rather than drift in a winning rook ending."""

    board = _empty_board_with_kings()
    board.clear_board()
    board.set_piece(sq("g3"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("d5"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.WHITE

    best_move = get_best_move(board, depth=1)

    assert best_move == LegalMove(start=sq("g3"), end=sq("f4"))


def test_search_prefers_queen_trade_in_clearly_won_ending() -> None:
    """When already ahead, the search should simplify into a winning queenless ending."""

    board = _empty_board_with_kings()
    board.clear_board()
    board.set_piece(sq("g3"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d7"), create_piece(Color.BLACK, PieceType.QUEEN))
    board.turn = Color.WHITE

    best_move = get_best_move(board, depth=1)

    assert best_move == LegalMove(start=sq("d4"), end=sq("d7"))


def test_quiet_move_order_prefers_blockading_enemy_passed_pawn() -> None:
    """Quiet ordering should favor stepping in front of an enemy passed pawn."""

    board = _empty_board_with_kings()
    board.clear_board()
    board.set_piece(sq("e4"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("a1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("g7"), create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(sq("d6"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE

    blockade_move = ai.Move(start=sq("e4"), end=sq("d5"))
    drift_move = ai.Move(start=sq("e4"), end=sq("f5"))

    assert _move_order_score(board, blockade_move, None) > _move_order_score(
        board,
        drift_move,
        None,
    )


def test_quiet_move_order_prefers_creating_luft() -> None:
    """Quiet ordering should prefer a useful luft move over an idle king sidestep."""

    board = _empty_board_with_kings()
    board.clear_board()
    board.set_piece(sq("g1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("g2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("h2"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.WHITE

    luft_move = ai.Move(start=sq("h2"), end=sq("h3"))
    king_drift = ai.Move(start=sq("g1"), end=sq("f1"))

    assert _move_order_score(board, luft_move, None) > _move_order_score(
        board,
        king_drift,
        None,
    )


def test_repetition_score_penalizes_equal_repetition_when_progress_exists() -> None:
    """Equal material should still avoid repetition when one side has a clear plan."""

    board = _empty_board_with_kings()
    key = position_key(board)

    assert repetition_score(
        board,
        None,
        (key, key, key),
        RepetitionPolicy(
            position_key=position_key,
            evaluate=lambda _board: 0,
            progress=lambda _board: 32,
            threshold=120,
            progress_threshold=24,
            penalty=32,
        ),
    ) < 0


def test_repetition_score_penalizes_draw_when_better_side_is_ahead() -> None:
    """Threefold repetition should be biased against the materially better side."""

    board = _empty_board_with_kings()
    board.set_piece(sq("d4"), create_piece(Color.WHITE, PieceType.ROOK))
    key = position_key(board)

    assert repetition_score(
        board,
        None,
        (key, key, key),
        RepetitionPolicy(
            position_key=position_key,
            evaluate=ai.evaluate,
            progress=lambda _board: 0,
            threshold=120,
            progress_threshold=24,
            penalty=32,
        ),
    ) < 0


def test_repetition_score_preserves_draw_when_position_is_equal() -> None:
    """Equal repeated positions should still score as a neutral draw."""

    board = _empty_board_with_kings()
    key = position_key(board)

    assert repetition_score(
        board,
        None,
        (key, key, key),
        RepetitionPolicy(
            position_key=position_key,
            evaluate=ai.evaluate,
            progress=lambda _board: 0,
            threshold=120,
            progress_threshold=24,
            penalty=32,
        ),
    ) == 0


def test_repetition_score_favors_drawing_resource_when_behind() -> None:
    """A repeated draw should be attractive to the materially worse side."""

    board = _empty_board_with_kings()
    board.set_piece(sq("d4"), create_piece(Color.BLACK, PieceType.ROOK))
    key = position_key(board)

    assert repetition_score(
        board,
        None,
        (key, key, key),
        RepetitionPolicy(
            position_key=position_key,
            evaluate=ai.evaluate,
            progress=lambda _board: 0,
            threshold=120,
            progress_threshold=24,
            penalty=32,
        ),
    ) > 0
