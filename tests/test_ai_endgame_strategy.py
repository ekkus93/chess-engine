"""Task 9 regressions for technical rook-endgame play."""

from chess_game.chess import ai
from chess_game.chess.ai import get_best_move, get_evaluation_breakdown
from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, LegalMove, PieceType
from tests.helpers import sq
from tests.test_ai_quality import _move_order_score


def _build_board(pieces: list[tuple[str, Color, PieceType]], turn: Color = Color.WHITE) -> Board:
    board = Board()
    board.clear_board()
    for square, color, kind in pieces:
        board.set_piece(sq(square), create_piece(color, kind))
    board.turn = turn
    return board


def test_rook_endgame_breakdown_rewards_front_defense_against_enemy_passer() -> None:
    """A defender on the queening file should score better than a loose checking rook."""

    passive_board = _build_board(
        [
            ("f4", Color.WHITE, PieceType.KING),
            ("e1", Color.WHITE, PieceType.ROOK),
            ("d5", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("a4", Color.BLACK, PieceType.ROOK),
        ]
    )
    defensive_board = _build_board(
        [
            ("f4", Color.WHITE, PieceType.KING),
            ("e1", Color.WHITE, PieceType.ROOK),
            ("d5", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.ROOK),
        ]
    )

    assert (
        get_evaluation_breakdown(passive_board)["rook_endgame"]
        > get_evaluation_breakdown(defensive_board)["rook_endgame"]
    )


def test_search_prefers_reducing_counterplay_before_pawn_racing() -> None:
    """A winning rook ending should reduce counterplay before pushing the passer."""

    board = _build_board(
        [
            ("f4", Color.WHITE, PieceType.KING),
            ("e1", Color.WHITE, PieceType.ROOK),
            ("d5", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("a8", Color.BLACK, PieceType.ROOK),
        ]
    )

    assert get_best_move(board, depth=1) == LegalMove(start=sq("e1"), end=sq("e7"))


def test_search_prefers_king_improvement_before_harmless_check_in_rook_endgame() -> None:
    """The engine should improve king placement before giving a loose rook check."""

    board = _build_board(
        [
            ("g3", Color.WHITE, PieceType.KING),
            ("d1", Color.WHITE, PieceType.ROOK),
            ("d5", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("a8", Color.BLACK, PieceType.ROOK),
        ]
    )

    assert get_best_move(board, depth=1) == LegalMove(start=sq("g3"), end=sq("f4"))


def test_search_prefers_simple_rook_trade_in_easy_win() -> None:
    """A trivially winning rook trade should beat a messier continuation."""

    board = _build_board(
        [
            ("f4", Color.WHITE, PieceType.KING),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("d5", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("a8", Color.BLACK, PieceType.ROOK),
        ]
    )

    assert get_best_move(board, depth=1) == LegalMove(start=sq("a1"), end=sq("a8"))


def test_quiet_move_order_prefers_file_defense_when_worse_over_side_check() -> None:
    """The worse side should get behind the passer rather than drift into side checks."""

    board = _build_board(
        [
            ("f4", Color.WHITE, PieceType.KING),
            ("e1", Color.WHITE, PieceType.ROOK),
            ("d5", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("a8", Color.BLACK, PieceType.ROOK),
        ],
        turn=Color.BLACK,
    )

    file_defense = ai.Move(start=sq("a8"), end=sq("d8"))
    side_check = ai.Move(start=sq("a8"), end=sq("a4"))

    assert _move_order_score(board, file_defense, None) > _move_order_score(
        board,
        side_check,
        None,
    )


def test_progress_breakdown_rewards_active_king_in_simple_winning_heavy_piece_endgame() -> None:
    """Winning conversion scoring should prefer an active king over a passive one."""

    active_board = _build_board(
        [
            ("f5", Color.WHITE, PieceType.KING),
            ("d4", Color.WHITE, PieceType.QUEEN),
            ("a4", Color.WHITE, PieceType.ROOK),
            ("d5", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.ROOK),
        ]
    )
    passive_board = _build_board(
        [
            ("g2", Color.WHITE, PieceType.KING),
            ("d4", Color.WHITE, PieceType.QUEEN),
            ("a4", Color.WHITE, PieceType.ROOK),
            ("d5", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.ROOK),
        ]
    )

    assert (
        get_evaluation_breakdown(active_board)["progress"]
        > get_evaluation_breakdown(passive_board)["progress"]
    )


def test_quiet_move_order_prefers_king_activation_over_harmless_check_in_winning_ending() -> None:
    """A winning side should improve king geometry before a loose check."""

    board = _build_board(
        [
            ("g4", Color.WHITE, PieceType.KING),
            ("d4", Color.WHITE, PieceType.QUEEN),
            ("a4", Color.WHITE, PieceType.ROOK),
            ("d5", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.ROOK),
        ]
    )

    king_activation = ai.Move(start=sq("g4"), end=sq("f5"))
    harmless_check = ai.Move(start=sq("d4"), end=sq("h4"))

    assert _move_order_score(board, king_activation, None) > _move_order_score(
        board,
        harmless_check,
        None,
    )


def test_quiet_move_order_prefers_cutoff_support_over_harmless_check_in_winning_ending() -> None:
    """The winning side should reinforce the passer file before drifting into checks."""

    board = _build_board(
        [
            ("f4", Color.WHITE, PieceType.KING),
            ("d4", Color.WHITE, PieceType.QUEEN),
            ("a4", Color.WHITE, PieceType.ROOK),
            ("d6", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("a8", Color.BLACK, PieceType.ROOK),
        ]
    )

    support_move = ai.Move(start=sq("a4"), end=sq("d4"))
    harmless_check = ai.Move(start=sq("d4"), end=sq("h4"))

    assert _move_order_score(board, support_move, None) > _move_order_score(
        board,
        harmless_check,
        None,
    )


def test_search_prefers_king_shelter_over_rook_check_that_concedes_tempo() -> None:
    """The worse side should shelter the king rather than give a check that rebounds.

    Ra8-a5+ looks active but allows Re1-e5 interpose -> Ra5xe5 -> Kg5xe5: White's
    king wins back the rook and the d6 pawn advances. Kg7-f8 is objectively better —
    the king avoids Kg7-f7 (which allows Re1-e7+ gaining White a tempo) and keeps the
    king safe while eyeing e7 to stop the d-pawn.
    """

    board = _build_board(
        [
            ("g5", Color.WHITE, PieceType.KING),
            ("e1", Color.WHITE, PieceType.ROOK),
            ("d6", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("a8", Color.BLACK, PieceType.ROOK),
        ],
        turn=Color.BLACK,
    )

    assert get_best_move(board, depth=1) == LegalMove(start=sq("g7"), end=sq("f8"))


def test_quiet_move_order_prefers_critical_square_approach_in_pawn_ending() -> None:
    """The defender king should head toward the block square instead of corner drifting."""

    board = _build_board(
        [
            ("e5", Color.WHITE, PieceType.KING),
            ("d6", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
        ],
        turn=Color.BLACK,
    )

    approach = ai.Move(start=sq("g7"), end=sq("f7"))
    drift = ai.Move(start=sq("g7"), end=sq("h8"))

    assert _move_order_score(board, approach, None) > _move_order_score(
        board,
        drift,
        None,
    )


def test_quiet_move_order_prefers_draw_zone_over_side_pawn_chase_when_worse() -> None:
    """The worse side should approach the draw zone before chasing irrelevant pawns."""

    board = _build_board(
        [
            ("e5", Color.WHITE, PieceType.KING),
            ("d6", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("h1", Color.WHITE, PieceType.ROOK),
            ("g7", Color.BLACK, PieceType.KING),
            ("a8", Color.BLACK, PieceType.ROOK),
        ],
        turn=Color.BLACK,
    )

    approach = ai.Move(start=sq("g7"), end=sq("f7"))
    chase = ai.Move(start=sq("a8"), end=sq("a2"))

    assert _move_order_score(board, approach, None) > _move_order_score(
        board,
        chase,
        None,
    )


def test_quiet_move_order_prefers_passer_escort_over_cosmetic_check_in_rook_race() -> None:
    """An advanced passer should be escorted before giving a low-value rook check."""

    board = _build_board(
        [
            ("f4", Color.WHITE, PieceType.KING),
            ("h1", Color.WHITE, PieceType.ROOK),
            ("d6", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.ROOK),
        ]
    )

    escort = ai.Move(start=sq("f4"), end=sq("e5"))
    cosmetic_check = ai.Move(start=sq("h1"), end=sq("h7"))

    assert _move_order_score(board, escort, None) > _move_order_score(
        board,
        cosmetic_check,
        None,
    )


def test_quiet_move_order_prefers_stopping_enemy_passer_before_rook_lift() -> None:
    """Enemy promotion-square control should outrank a cosmetic rook lift."""

    board = _build_board(
        [
            ("g3", Color.WHITE, PieceType.KING),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("a5", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("d3", Color.BLACK, PieceType.PAWN),
        ]
    )

    stopper = ai.Move(start=sq("a1"), end=sq("d1"))
    cosmetic_lift = ai.Move(start=sq("a1"), end=sq("a3"))

    assert _move_order_score(board, stopper, None) > _move_order_score(
        board,
        cosmetic_lift,
        None,
    )


def test_quiet_move_order_prefers_direct_outside_passer_push_over_slow_king_drift() -> None:
    """A ready outside passer should be pushed before a slower king shuffle."""

    board = _build_board(
        [
            ("e5", Color.WHITE, PieceType.KING),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("a5", Color.WHITE, PieceType.PAWN),
            ("g7", Color.BLACK, PieceType.KING),
            ("h8", Color.BLACK, PieceType.ROOK),
        ]
    )

    direct_push = ai.Move(start=sq("a5"), end=sq("a6"))
    king_drift = ai.Move(start=sq("e5"), end=sq("d5"))

    assert _move_order_score(board, direct_push, None) > _move_order_score(
        board,
        king_drift,
        None,
    )
