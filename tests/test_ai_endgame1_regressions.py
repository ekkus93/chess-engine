"""Transcript-backed regressions for ENDGAME1 simple-endgame cleanup."""

from chess_game.chess import ai
from chess_game.chess.ai import (
    _root_stability_adjustment,
    get_best_move,
    get_evaluation_breakdown,
    position_key,
)
from chess_game.chess.ai_search_helpers import RepetitionPolicy, repetition_score
from chess_game.chess.board import Board, create_piece
from chess_game.chess.move import Move
from chess_game.chess.types import Color, LegalMove, PieceType
from tests.helpers import sq
from tests.test_ai_quality import _move_order_score


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


def _task1_bishop_loop_board() -> Board:
    return _build_board(
        [
            ("h2", Color.WHITE, PieceType.KING),
            ("e4", Color.WHITE, PieceType.BISHOP),
            ("h4", Color.WHITE, PieceType.PAWN),
            ("c5", Color.BLACK, PieceType.KING),
            ("d7", Color.BLACK, PieceType.BISHOP),
            ("a7", Color.BLACK, PieceType.PAWN),
            ("b4", Color.BLACK, PieceType.PAWN),
            ("d4", Color.BLACK, PieceType.PAWN),
            ("h5", Color.BLACK, PieceType.PAWN),
        ]
    )


def _task1_king_activation_board() -> Board:
    return _build_board(
        [
            ("h2", Color.WHITE, PieceType.KING),
            ("d3", Color.WHITE, PieceType.BISHOP),
            ("h4", Color.WHITE, PieceType.PAWN),
            ("c6", Color.BLACK, PieceType.KING),
            ("f3", Color.BLACK, PieceType.BISHOP),
            ("a7", Color.BLACK, PieceType.PAWN),
            ("b4", Color.BLACK, PieceType.PAWN),
            ("d4", Color.BLACK, PieceType.PAWN),
            ("h5", Color.BLACK, PieceType.PAWN),
        ]
    )


def _task1_passer_priority_board() -> Board:
    return _build_board(
        [
            ("c2", Color.WHITE, PieceType.KING),
            ("h4", Color.WHITE, PieceType.PAWN),
            ("c6", Color.BLACK, PieceType.KING),
            ("a5", Color.BLACK, PieceType.PAWN),
            ("b2", Color.BLACK, PieceType.PAWN),
        ]
    )


def _task1_queen_conversion_board() -> Board:
    return _build_board(
        [
            ("c6", Color.WHITE, PieceType.KING),
            ("e7", Color.WHITE, PieceType.QUEEN),
            ("a8", Color.BLACK, PieceType.KING),
        ]
    )


def _task2_escort_far_board() -> Board:
    return _build_board(
        [
            ("c2", Color.WHITE, PieceType.KING),
            ("h4", Color.WHITE, PieceType.PAWN),
            ("c6", Color.BLACK, PieceType.KING),
        ]
    )


def _task2_escort_near_board() -> Board:
    return _build_board(
        [
            ("g3", Color.WHITE, PieceType.KING),
            ("h4", Color.WHITE, PieceType.PAWN),
            ("c6", Color.BLACK, PieceType.KING),
        ]
    )


def _task2_blockade_far_board() -> Board:
    return _build_board(
        [
            ("h2", Color.WHITE, PieceType.KING),
            ("d3", Color.WHITE, PieceType.BISHOP),
            ("c6", Color.BLACK, PieceType.KING),
            ("a7", Color.BLACK, PieceType.PAWN),
            ("d4", Color.BLACK, PieceType.PAWN),
        ]
    )


def _task2_blockade_near_board() -> Board:
    return _build_board(
        [
            ("g3", Color.WHITE, PieceType.KING),
            ("d3", Color.WHITE, PieceType.BISHOP),
            ("c6", Color.BLACK, PieceType.KING),
            ("a7", Color.BLACK, PieceType.PAWN),
            ("d4", Color.BLACK, PieceType.PAWN),
        ]
    )


def _task2_opposition_good_board() -> Board:
    return _build_board(
        [
            ("c3", Color.WHITE, PieceType.KING),
            ("c4", Color.WHITE, PieceType.PAWN),
            ("c5", Color.BLACK, PieceType.KING),
        ]
    )


def _task2_opposition_bad_board() -> Board:
    return _build_board(
        [
            ("b2", Color.WHITE, PieceType.KING),
            ("c4", Color.WHITE, PieceType.PAWN),
            ("c5", Color.BLACK, PieceType.KING),
        ]
    )


def _task2_king_lead_board() -> Board:
    return _build_board(
        [
            ("c2", Color.WHITE, PieceType.KING),
            ("e2", Color.WHITE, PieceType.BISHOP),
            ("h4", Color.WHITE, PieceType.PAWN),
            ("c6", Color.BLACK, PieceType.KING),
            ("a5", Color.BLACK, PieceType.PAWN),
        ]
    )


def _task3_one_tempo_board() -> Board:
    return _build_board(
        [
            ("f4", Color.WHITE, PieceType.KING),
            ("g6", Color.WHITE, PieceType.PAWN),
            ("c6", Color.BLACK, PieceType.KING),
            ("a5", Color.BLACK, PieceType.PAWN),
        ]
    )


def _task3_bishop_stop_board() -> Board:
    return _build_board(
        [
            ("a3", Color.WHITE, PieceType.KING),
            ("g6", Color.WHITE, PieceType.PAWN),
            ("b1", Color.BLACK, PieceType.KING),
            ("b2", Color.BLACK, PieceType.BISHOP),
        ],
        turn=Color.BLACK,
    )


def _task3_wrong_pawn_board() -> Board:
    return _build_board(
        [
            ("a3", Color.WHITE, PieceType.KING),
            ("a5", Color.WHITE, PieceType.PAWN),
            ("h6", Color.WHITE, PieceType.PAWN),
            ("e5", Color.BLACK, PieceType.KING),
            ("a4", Color.BLACK, PieceType.PAWN),
        ]
    )


def _task3_immediate_activation_board() -> Board:
    return _build_board(
        [
            ("d2", Color.WHITE, PieceType.KING),
            ("h5", Color.WHITE, PieceType.PAWN),
            ("f6", Color.BLACK, PieceType.KING),
            ("a4", Color.BLACK, PieceType.PAWN),
        ]
    )


def _task4_king_activity_board() -> Board:
    return _build_board(
        [
            ("b2", Color.WHITE, PieceType.KING),
            ("c4", Color.WHITE, PieceType.BISHOP),
            ("h4", Color.WHITE, PieceType.PAWN),
            ("b6", Color.BLACK, PieceType.KING),
            ("a5", Color.BLACK, PieceType.PAWN),
        ]
    )


def _task4_trade_minor_board() -> Board:
    return _build_board(
        [
            ("c4", Color.WHITE, PieceType.KING),
            ("e5", Color.WHITE, PieceType.BISHOP),
            ("h4", Color.WHITE, PieceType.PAWN),
            ("e7", Color.BLACK, PieceType.KING),
            ("d6", Color.BLACK, PieceType.BISHOP),
        ]
    )


def _task4_support_main_passer_board() -> Board:
    return _build_board(
        [
            ("c3", Color.WHITE, PieceType.KING),
            ("d3", Color.WHITE, PieceType.BISHOP),
            ("h5", Color.WHITE, PieceType.PAWN),
            ("a5", Color.WHITE, PieceType.PAWN),
            ("d6", Color.BLACK, PieceType.KING),
        ]
    )


def _task4_cutoff_before_race_board() -> Board:
    return _build_board(
        [
            ("d4", Color.WHITE, PieceType.KING),
            ("a5", Color.WHITE, PieceType.ROOK),
            ("g6", Color.WHITE, PieceType.PAWN),
            ("e7", Color.BLACK, PieceType.KING),
        ]
    )


def _task5_blockade_board() -> Board:
    return _build_board(
        [
            ("b6", Color.WHITE, PieceType.KING),
            ("a6", Color.WHITE, PieceType.PAWN),
            ("f1", Color.WHITE, PieceType.BISHOP),
            ("b8", Color.BLACK, PieceType.KING),
            ("c6", Color.BLACK, PieceType.BISHOP),
        ],
        turn=Color.BLACK,
    )


def _task5_active_king_defense_board() -> Board:
    return _build_board(
        [
            ("d5", Color.WHITE, PieceType.KING),
            ("g5", Color.WHITE, PieceType.PAWN),
            ("c4", Color.WHITE, PieceType.BISHOP),
            ("e7", Color.BLACK, PieceType.KING),
            ("d6", Color.BLACK, PieceType.BISHOP),
        ],
        turn=Color.BLACK,
    )


def _task5_checking_hold_board() -> Board:
    return _build_board(
        [
            ("f4", Color.WHITE, PieceType.KING),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("d5", Color.WHITE, PieceType.PAWN),
            ("f7", Color.BLACK, PieceType.KING),
            ("g8", Color.BLACK, PieceType.ROOK),
        ],
        turn=Color.BLACK,
    )


def _task5_avoid_bad_trade_board() -> Board:
    return _build_board(
        [
            ("c4", Color.WHITE, PieceType.KING),
            ("d4", Color.WHITE, PieceType.ROOK),
            ("g5", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.ROOK),
        ],
        turn=Color.BLACK,
    )


def _task6_correct_bishop_color_board() -> Board:
    return _build_board(
        [
            ("g6", Color.WHITE, PieceType.KING),
            ("c3", Color.WHITE, PieceType.BISHOP),
            ("h6", Color.WHITE, PieceType.PAWN),
            ("h8", Color.BLACK, PieceType.KING),
        ]
    )


def _task6_wrong_bishop_color_board() -> Board:
    return _build_board(
        [
            ("g6", Color.WHITE, PieceType.KING),
            ("g2", Color.WHITE, PieceType.BISHOP),
            ("h6", Color.WHITE, PieceType.PAWN),
            ("h8", Color.BLACK, PieceType.KING),
        ]
    )


def _task6_bishop_coordination_good_board() -> Board:
    return _build_board(
        [
            ("f4", Color.WHITE, PieceType.KING),
            ("d2", Color.WHITE, PieceType.BISHOP),
            ("h5", Color.WHITE, PieceType.PAWN),
            ("c5", Color.BLACK, PieceType.KING),
            ("a5", Color.BLACK, PieceType.PAWN),
        ]
    )


def _task6_bishop_coordination_bad_board() -> Board:
    return _build_board(
        [
            ("f4", Color.WHITE, PieceType.KING),
            ("a2", Color.WHITE, PieceType.BISHOP),
            ("h5", Color.WHITE, PieceType.PAWN),
            ("c5", Color.BLACK, PieceType.KING),
            ("a5", Color.BLACK, PieceType.PAWN),
        ]
    )


def _task6_rook_behind_passer_board() -> Board:
    return _build_board(
        [
            ("e3", Color.WHITE, PieceType.KING),
            ("h1", Color.WHITE, PieceType.ROOK),
            ("h5", Color.WHITE, PieceType.PAWN),
            ("d6", Color.BLACK, PieceType.KING),
            ("a6", Color.BLACK, PieceType.BISHOP),
        ]
    )


def _task6_rook_side_drift_board() -> Board:
    return _build_board(
        [
            ("e3", Color.WHITE, PieceType.KING),
            ("f1", Color.WHITE, PieceType.ROOK),
            ("h5", Color.WHITE, PieceType.PAWN),
            ("d6", Color.BLACK, PieceType.KING),
            ("a6", Color.BLACK, PieceType.BISHOP),
        ]
    )


def _task7_worse_repetition_rook_board() -> Board:
    return _build_board(
        [
            ("f4", Color.WHITE, PieceType.KING),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("d5", Color.WHITE, PieceType.PAWN),
            ("f7", Color.BLACK, PieceType.KING),
            ("g8", Color.BLACK, PieceType.ROOK),
        ],
        turn=Color.BLACK,
    )


def _task7_better_repetition_board() -> Board:
    return _build_board(
        [
            ("g3", Color.WHITE, PieceType.KING),
            ("c3", Color.WHITE, PieceType.BISHOP),
            ("h6", Color.WHITE, PieceType.PAWN),
            ("h8", Color.BLACK, PieceType.KING),
        ]
    )


def test_endgame1_rejects_bishop_loop_drift() -> None:
    """The late bishop loop should yield to immediate king activation."""

    board = _task1_bishop_loop_board()
    active_king = Move(start=sq("h2"), end=sq("g3"))
    bishop_loop = Move(start=sq("e4"), end=sq("g6"))

    assert _move_order_score(board, active_king, None) > _move_order_score(
        board,
        bishop_loop,
        None,
    )
    best_move = get_best_move(board, depth=3)
    assert best_move != LegalMove(start=bishop_loop.start, end=bishop_loop.end)


def test_endgame1_prefers_king_activation_over_passive_waiting() -> None:
    """The worse side should activate the king instead of drifting backward."""

    board = _task1_king_activation_board()
    active_king = Move(start=sq("h2"), end=sq("g3"))
    king_retreat = Move(start=sq("h2"), end=sq("g1"))

    assert _move_order_score(board, active_king, None) > _move_order_score(
        board,
        king_retreat,
        None,
    )
    best_move = get_best_move(board, depth=3)
    assert best_move == LegalMove(start=sq("h2"), end=sq("g3")) or best_move == LegalMove(
        start=sq("h2"),
        end=sq("h3"),
    )


def test_endgame1_prefers_passer_progress_over_passive_king_shuffle() -> None:
    """The king-and-pawn phase should keep the main passer ahead of empty waiting."""

    board = _task1_passer_priority_board()
    passer_push = Move(start=sq("h4"), end=sq("h5"))
    passive_shuffle = Move(start=sq("c2"), end=sq("d2"))

    assert _move_order_score(board, passer_push, None) > _move_order_score(
        board,
        passive_shuffle,
        None,
    )


def test_endgame1_prefers_forcing_mate_over_queen_drift() -> None:
    """A trivially won queen ending should keep the forcing mate move first."""

    board = _task1_queen_conversion_board()

    assert get_best_move(board, depth=3) == LegalMove(start=sq("e7"), end=sq("b7"))


def test_endgame1_repetition_score_penalizes_better_side_draw() -> None:
    """The better side should still avoid repeated draws in a won ending."""

    board = _task1_queen_conversion_board()
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


def test_endgame1_repetition_score_favors_worse_side_draw() -> None:
    """The worse side should still welcome repetition when it is the best hold."""

    board = _task1_bishop_loop_board()
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


def test_endgame1_king_activation_breakdown_prefers_king_near_own_passer() -> None:
    """The king-activation breakdown should reward escort geometry."""

    far_board = _task2_escort_far_board()
    near_board = _task2_escort_near_board()

    assert get_evaluation_breakdown(near_board)["king_activation"] > get_evaluation_breakdown(
        far_board
    )["king_activation"]


def test_endgame1_king_activation_breakdown_prefers_king_near_enemy_blockade_square() -> None:
    """The breakdown should reward reaching the blockade theater sooner."""

    far_board = _task2_blockade_far_board()
    near_board = _task2_blockade_near_board()

    assert get_evaluation_breakdown(near_board)["king_activation"] > get_evaluation_breakdown(
        far_board
    )["king_activation"]


def test_endgame1_king_activation_breakdown_rewards_opposition_geometry() -> None:
    """Opposition-like king geometry should be visible in the endgame breakdown."""

    good_board = _task2_opposition_good_board()
    bad_board = _task2_opposition_bad_board()

    assert get_evaluation_breakdown(good_board)["king_activation"] > get_evaluation_breakdown(
        bad_board
    )["king_activation"]


def test_endgame1_prefers_king_step_when_king_should_lead() -> None:
    """A king-led ending should keep king activation ahead of bishop drift."""

    board = _task2_king_lead_board()
    king_step = Move(start=sq("c2"), end=sq("d3"))
    bishop_drift = Move(start=sq("e2"), end=sq("d3"))

    assert _move_order_score(board, king_step, None) > _move_order_score(
        board,
        bishop_drift,
        None,
    )
    assert get_best_move(board, depth=3).start == sq("c2")


def test_endgame1_search_prefers_one_tempo_pawn_push_over_side_activity() -> None:
    """A passer one tempo from promotion should outrank king-side activity."""

    board = _task3_one_tempo_board()

    assert get_best_move(board, depth=3) == LegalMove(start=sq("g6"), end=sq("g7"))


def test_endgame1_order_prefers_one_tempo_pawn_push_over_side_activity() -> None:
    """Near-promotion passer pushes should outrank unrelated king moves in the race."""

    board = _task3_one_tempo_board()

    assert _move_order_score(board, Move(start=sq("g6"), end=sq("g7")), None) > _move_order_score(
        board,
        Move(start=sq("f4"), end=sq("e4")),
        None,
    )


def test_endgame1_order_prefers_immediate_king_activation_in_pawn_race() -> None:
    """King activation should outrank retreating away from the race."""

    board = _task3_immediate_activation_board()

    assert _move_order_score(board, Move(start=sq("d2"), end=sq("e3")), None) > _move_order_score(
        board,
        Move(start=sq("d2"), end=sq("e1")),
        None,
    )


def test_endgame1_search_prefers_bishop_blockade_over_counterplay_chase() -> None:
    """A minor piece should stop the passer when only the blockade move holds."""

    board = _task3_bishop_stop_board()

    assert get_best_move(board, depth=3) == LegalMove(start=sq("b2"), end=sq("g7"))


def test_endgame1_order_prefers_main_race_pawn_over_wrong_pawn_push() -> None:
    """Among two passers, the nearer promotion push should outrank the side pawn."""

    board = _task3_wrong_pawn_board()

    assert _move_order_score(board, Move(start=sq("h6"), end=sq("h7")), None) > _move_order_score(
        board,
        Move(start=sq("a5"), end=sq("a6")),
        None,
    )


def test_endgame1_search_prefers_king_activity_before_pawn_drift_in_winning_endgame() -> None:
    """The better side should activate the king before spending a tempo on pawn drift."""

    board = _task4_king_activity_board()

    assert get_best_move(board, depth=3).start == sq("b2")


def test_endgame1_search_prefers_trading_into_trivial_king_and_pawn_win() -> None:
    """A clean bishop trade should outrank a slower winning conversion."""

    board = _task4_trade_minor_board()

    assert get_best_move(board, depth=3) == LegalMove(start=sq("e5"), end=sq("d6"))


def test_endgame1_search_prefers_supporting_main_passer_over_side_pawn_push() -> None:
    """The winning side should push the main passer before the side pawn."""

    board = _task4_support_main_passer_board()

    assert get_best_move(board, depth=3) == LegalMove(start=sq("h5"), end=sq("h6"))


def test_endgame1_search_prefers_cutoff_before_starting_pawn_race() -> None:
    """A rook cutoff should come before the immediate pawn race when it kills counterplay."""

    board = _task4_cutoff_before_race_board()

    assert get_best_move(board, depth=3).start == sq("a5")


def test_endgame1_order_prefers_blockade_over_bishop_drift_when_worse() -> None:
    """The defender should keep the rook-pawn blockade instead of drifting the bishop away."""

    board = _task5_blockade_board()
    blockade = Move(start=sq("c6"), end=sq("a8"))
    drift = Move(start=sq("c6"), end=sq("e4"))

    assert _move_order_score(board, blockade, None) > _move_order_score(board, drift, None)


def test_endgame1_order_prefers_active_king_defense_over_bishop_shuffle() -> None:
    """The worse side should activate the king instead of spending a tempo on bishop drift."""

    board = _task5_active_king_defense_board()
    active_king = Move(start=sq("e7"), end=sq("f7"))
    bishop_shuffle = Move(start=sq("d6"), end=sq("f4"))

    assert _move_order_score(board, active_king, None) > _move_order_score(
        board,
        bishop_shuffle,
        None,
    )


def test_endgame1_eval_prefers_blockade_hold_over_bishop_drift_when_worse() -> None:
    """Static defense guidance should score the blockade hold as the better practical resistance."""

    board = _task5_blockade_board()
    blockade_child = board.clone()
    drift_child = board.clone()

    assert blockade_child.apply_legal_move(sq("c6"), sq("a8")) is True
    assert drift_child.apply_legal_move(sq("c6"), sq("e4")) is True

    assert ai.evaluate(blockade_child) < ai.evaluate(drift_child)
    assert (
        get_evaluation_breakdown(blockade_child)["endgame_technique"]
        < get_evaluation_breakdown(drift_child)["endgame_technique"]
    )


def test_endgame1_eval_prefers_active_king_defense_over_bishop_shuffle_when_worse() -> None:
    """Static defense guidance should reward the active king hold over bishop shuffling."""

    board = _task5_active_king_defense_board()
    active_king_child = board.clone()
    bishop_shuffle_child = board.clone()

    assert active_king_child.apply_legal_move(sq("e7"), sq("f7")) is True
    assert bishop_shuffle_child.apply_legal_move(sq("d6"), sq("f4")) is True

    assert ai.evaluate(active_king_child) < ai.evaluate(bishop_shuffle_child)
    assert (
        get_evaluation_breakdown(active_king_child)["endgame_technique"]
        < get_evaluation_breakdown(bishop_shuffle_child)["endgame_technique"]
    )


def test_endgame1_order_prefers_checking_hold_over_passive_king_move() -> None:
    """A live checking resource should beat passive king defense when worse."""

    board = _task5_checking_hold_board()
    checking_hold = Move(start=sq("g8"), end=sq("g4"))
    passive_king = Move(start=sq("f7"), end=sq("e7"))

    assert _move_order_score(board, checking_hold, None) > _move_order_score(
        board,
        passive_king,
        None,
    )


def test_endgame1_root_discourages_bad_rook_trade_into_lost_pawn_race() -> None:
    """Root tie-breaks should demote a rook trade that collapses into a lost pawn race."""

    board = _task5_avoid_bad_trade_board()
    keep_rook = Move(start=sq("d8"), end=sq("g8"))
    bad_trade = Move(start=sq("d8"), end=sq("d4"))
    keep_child = board.clone()
    trade_child = board.clone()

    assert keep_child.apply_legal_move(keep_rook.start, keep_rook.end) is True
    assert trade_child.apply_legal_move(bad_trade.start, bad_trade.end) is True

    assert _root_stability_adjustment(
        board,
        keep_rook,
        keep_child,
    ) < _root_stability_adjustment(
        board,
        bad_trade,
        trade_child,
    )


def test_endgame1_low_material_coordination_prefers_correct_bishop_complex() -> None:
    """The sparse-ending breakdown should reward the bishop complex that supports promotion."""

    good_board = _task6_correct_bishop_color_board()
    bad_board = _task6_wrong_bishop_color_board()

    assert (
        get_evaluation_breakdown(good_board)["low_material_coordination"]
        > get_evaluation_breakdown(bad_board)["low_material_coordination"]
    )


def test_endgame1_low_material_coordination_prefers_bishop_king_theater_coordination() -> None:
    """The bishop should score higher when it stays coordinated with the king near the outside passer."""

    good_board = _task6_bishop_coordination_good_board()
    bad_board = _task6_bishop_coordination_bad_board()

    assert (
        get_evaluation_breakdown(good_board)["low_material_coordination"]
        > get_evaluation_breakdown(bad_board)["low_material_coordination"]
    )


def test_endgame1_low_material_coordination_rewards_rook_behind_passer_in_rook_light_endgame() -> None:
    """Reduced-material rook play should reward staying behind the main passer file."""

    behind_board = _task6_rook_behind_passer_board()
    drift_board = _task6_rook_side_drift_board()

    assert (
        get_evaluation_breakdown(behind_board)["low_material_coordination"]
        > get_evaluation_breakdown(drift_board)["low_material_coordination"]
    )


def test_endgame1_order_prefers_bishop_staying_with_promotion_theater_over_central_drift() -> None:
    """Quiet ordering should prefer bishop coordination with the passer theater over aimless drift."""

    board = _task6_correct_bishop_color_board()
    coordinated_bishop = Move(start=sq("c3"), end=sq("g7"))
    central_drift = Move(start=sq("c3"), end=sq("e5"))

    assert _move_order_score(board, coordinated_bishop, None) > _move_order_score(
        board,
        central_drift,
        None,
    )


def test_endgame1_root_prefers_bishop_staying_with_promotion_theater_over_central_drift() -> None:
    """Root tie-breaks should keep the bishop tied to the promotion theater."""

    board = _task6_correct_bishop_color_board()
    coordinated_bishop = Move(start=sq("c3"), end=sq("g7"))
    central_drift = Move(start=sq("c3"), end=sq("e5"))
    coordinated_child = board.clone()
    drift_child = board.clone()

    assert coordinated_child.apply_legal_move(coordinated_bishop.start, coordinated_bishop.end) is True
    assert drift_child.apply_legal_move(central_drift.start, central_drift.end) is True

    assert _root_stability_adjustment(
        board,
        coordinated_bishop,
        coordinated_child,
    ) > _root_stability_adjustment(
        board,
        central_drift,
        drift_child,
    )


def test_endgame1_repetition_score_favors_worse_side_draw_from_side_to_move_perspective() -> None:
    """Repeated endgame holds should score as attractive when the side to move is behind."""

    board = _task7_worse_repetition_rook_board()
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


def test_endgame1_order_prefers_rook_cutoff_over_sideways_drift_in_endgame() -> None:
    """Endgame ordering should recognize rook cutoff geometry over sideways rook drift."""

    board = _task4_cutoff_before_race_board()
    cutoff = Move(start=sq("a5"), end=sq("a7"))
    sideways = Move(start=sq("a5"), end=sq("c5"))

    assert _move_order_score(board, cutoff, None) > _move_order_score(
        board,
        sideways,
        None,
    )


def test_endgame1_root_prefers_cutoff_that_narrows_endgame_replies() -> None:
    """Endgame root tie-breaks should reward cutoff moves that reduce the defender's options."""

    board = _task4_cutoff_before_race_board()
    cutoff = Move(start=sq("a5"), end=sq("a7"))
    sideways = Move(start=sq("a5"), end=sq("c5"))
    cutoff_child = board.clone()
    sideways_child = board.clone()

    assert cutoff_child.apply_legal_move(cutoff.start, cutoff.end) is True
    assert sideways_child.apply_legal_move(sideways.start, sideways.end) is True

    assert _root_stability_adjustment(
        board,
        cutoff,
        cutoff_child,
    ) > _root_stability_adjustment(
        board,
        sideways,
        sideways_child,
    )


def test_endgame1_root_penalizes_better_side_repeated_endgame_drift() -> None:
    """Repeated endgame shuffles should lose the root tie-break when the moving side is better."""

    board = _task7_better_repetition_board()
    repeated_drift = Move(start=sq("c3"), end=sq("b2"))
    progress = Move(start=sq("g3"), end=sq("g4"))
    repeated_child = board.clone()
    progress_child = board.clone()

    assert repeated_child.apply_legal_move(repeated_drift.start, repeated_drift.end) is True
    assert progress_child.apply_legal_move(progress.start, progress.end) is True

    assert _root_stability_adjustment(
        board,
        progress,
        progress_child,
    ) > _root_stability_adjustment(
        board,
        repeated_drift,
        repeated_child,
    )


def test_endgame1_seeded_task7_order_prefers_promotion_prep_over_bishop_detour() -> None:
    """Seeded continuation should prioritize immediate promotion progress over bishop reroutes."""

    board = _task7_better_repetition_board()
    promotion_prep = Move(start=sq("h6"), end=sq("h7"))
    bishop_detour = Move(start=sq("c3"), end=sq("e5"))

    assert _move_order_score(board, promotion_prep, None) > _move_order_score(
        board,
        bishop_detour,
        None,
    )


def test_endgame1_seeded_task7_root_prefers_promotion_prep_over_bishop_detour() -> None:
    """Root tie-breaks should keep the promoted-pawn plan ahead of bishop detours."""

    board = _task7_better_repetition_board()
    promotion_prep = Move(start=sq("h6"), end=sq("h7"))
    bishop_detour = Move(start=sq("c3"), end=sq("e5"))
    promotion_child = board.clone()
    bishop_child = board.clone()

    assert promotion_child.apply_legal_move(promotion_prep.start, promotion_prep.end) is True
    assert bishop_child.apply_legal_move(bishop_detour.start, bishop_detour.end) is True

    assert _root_stability_adjustment(
        board,
        promotion_prep,
        promotion_child,
    ) > _root_stability_adjustment(
        board,
        bishop_detour,
        bishop_child,
    )
