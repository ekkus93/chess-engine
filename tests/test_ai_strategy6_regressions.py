"""Transcript-driven regressions for STRATEGY6 opening-discipline cleanup."""

from chess_game.chess import ai
from chess_game.chess.ai import get_best_move, get_evaluation_breakdown
from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, LegalMove, PieceType
from tests.helpers import sq
from tests.test_ai_quality import _move_order_score


def _board_from_moves(moves: list[tuple[str, str]]) -> Board:
    board = Board()
    for start, end in moves:
        board.make_move(sq(start), sq(end))
    return board


def _task4_castling_board() -> Board:
    board = Board()
    board.clear_board()
    for square, color, kind in [
        ("e1", Color.WHITE, PieceType.KING),
        ("a1", Color.WHITE, PieceType.ROOK),
        ("h1", Color.WHITE, PieceType.ROOK),
        ("c2", Color.WHITE, PieceType.QUEEN),
        ("g2", Color.WHITE, PieceType.BISHOP),
        ("f3", Color.WHITE, PieceType.KNIGHT),
        ("f2", Color.WHITE, PieceType.PAWN),
        ("g3", Color.WHITE, PieceType.PAWN),
        ("h2", Color.WHITE, PieceType.PAWN),
        ("g8", Color.BLACK, PieceType.KING),
        ("d7", Color.BLACK, PieceType.QUEEN),
        ("f8", Color.BLACK, PieceType.ROOK),
        ("c5", Color.BLACK, PieceType.BISHOP),
        ("f6", Color.BLACK, PieceType.KNIGHT),
        ("f7", Color.BLACK, PieceType.PAWN),
        ("g7", Color.BLACK, PieceType.PAWN),
        ("h7", Color.BLACK, PieceType.PAWN),
    ]:
        board.set_piece(sq(square), create_piece(color, kind))
    board.turn = Color.WHITE
    return board


def _task5_transition_board() -> Board:
    return _board_from_moves(
        [
            ("g1", "f3"),
            ("d7", "d5"),
            ("b1", "c3"),
            ("b8", "c6"),
            ("b2", "b3"),
            ("d5", "d4"),
            ("c3", "e4"),
            ("e7", "e5"),
            ("c1", "b2"),
            ("b7", "b6"),
            ("a1", "c1"),
            ("f8", "e7"),
            ("g2", "g3"),
            ("g8", "h6"),
            ("h2", "h4"),
            ("e8", "g8"),
            ("f1", "g2"),
            ("f7", "f5"),
            ("g2", "h3"),
            ("f5", "e4"),
        ]
    )


def _task6_conversion_board() -> Board:
    return _board_from_moves(
        [
            ("g1", "f3"),
            ("d7", "d5"),
            ("b1", "c3"),
            ("b8", "c6"),
            ("b2", "b3"),
            ("d5", "d4"),
            ("c3", "e4"),
            ("e7", "e5"),
            ("c1", "b2"),
            ("b7", "b6"),
            ("a1", "c1"),
            ("f8", "e7"),
            ("g2", "g3"),
            ("g8", "h6"),
            ("h2", "h4"),
            ("e8", "g8"),
            ("f1", "g2"),
            ("f7", "f5"),
            ("g2", "h3"),
            ("f5", "e4"),
            ("f3", "d4"),
            ("c6", "d4"),
            ("h3", "g2"),
            ("c8", "f5"),
            ("c2", "c3"),
            ("d4", "b5"),
            ("b3", "b4"),
            ("h6", "f7"),
            ("d1", "b3"),
            ("a7", "a5"),
            ("a2", "a4"),
            ("b5", "a7"),
            ("e1", "g1"),
            ("d8", "d2"),
            ("c1", "c2"),
            ("d2", "c2"),
            ("b3", "c2"),
            ("a5", "b4"),
            ("c3", "b4"),
            ("h7", "h5"),
            ("c2", "c7"),
            ("a7", "c8"),
            ("b2", "e5"),
            ("e7", "b4"),
            ("e5", "d4"),
        ]
    )


def _task7_review_board() -> Board:
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
        ]
    )


def test_strategy6_order_prefers_development_over_early_rc1_from_transcript() -> None:
    """The opening should score a normal kingside setup above the move-11 rook drift."""

    board = _board_from_moves(
        [
            ("g1", "f3"),
            ("d7", "d5"),
            ("b1", "c3"),
            ("b8", "c6"),
            ("b2", "b3"),
            ("d5", "d4"),
            ("c3", "e4"),
            ("e7", "e5"),
            ("c1", "b2"),
            ("b7", "b6"),
        ]
    )

    develop = ai.Move(start=sq("g2"), end=sq("g3"))
    rook_drift = ai.Move(start=sq("a1"), end=sq("c1"))

    assert _move_order_score(board, develop, None) > _move_order_score(
        board,
        rook_drift,
        None,
    )


def test_strategy6_search_rejects_early_rc1_from_transcript() -> None:
    """The transcript opening should no longer choose Rc1 before king safety."""

    board = _board_from_moves(
        [
            ("g1", "f3"),
            ("d7", "d5"),
            ("b1", "c3"),
            ("b8", "c6"),
            ("b2", "b3"),
            ("d5", "d4"),
            ("c3", "e4"),
            ("e7", "e5"),
            ("c1", "b2"),
            ("b7", "b6"),
        ]
    )

    assert get_best_move(board, depth=3) != LegalMove(start=sq("a1"), end=sq("c1"))


def test_strategy6_search_rejects_early_a_pawn_drift_after_rook_probe() -> None:
    """The same baseline opening should not replace Rc1 with aimless a-pawn drift."""

    board = _board_from_moves(
        [
            ("g1", "f3"),
            ("d7", "d5"),
            ("b1", "c3"),
            ("b8", "c6"),
            ("b2", "b3"),
            ("d5", "d4"),
            ("c3", "e4"),
            ("e7", "e5"),
            ("c1", "b2"),
            ("b7", "b6"),
        ]
    )

    best_move = get_best_move(board, depth=3)

    assert best_move not in [
        LegalMove(start=sq("a2"), end=sq("a3")),
        LegalMove(start=sq("a2"), end=sq("a4")),
    ]


def test_strategy6_order_prefers_bg2_over_h4_from_transcript() -> None:
    """The transcript position should finish kingside development before h4."""

    board = _board_from_moves(
        [
            ("g1", "f3"),
            ("d7", "d5"),
            ("b1", "c3"),
            ("b8", "c6"),
            ("b2", "b3"),
            ("d5", "d4"),
            ("c3", "e4"),
            ("e7", "e5"),
            ("c1", "b2"),
            ("b7", "b6"),
            ("a1", "c1"),
            ("f8", "e7"),
            ("g2", "g3"),
            ("g8", "h6"),
        ]
    )

    develop = ai.Move(start=sq("f1"), end=sq("g2"))
    pawn_lunge = ai.Move(start=sq("h2"), end=sq("h4"))

    assert _move_order_score(board, develop, None) > _move_order_score(
        board,
        pawn_lunge,
        None,
    )


def test_strategy6_search_rejects_h4_before_king_safety_from_transcript() -> None:
    """The transcript position should no longer choose h4 before kingside setup."""

    board = _board_from_moves(
        [
            ("g1", "f3"),
            ("d7", "d5"),
            ("b1", "c3"),
            ("b8", "c6"),
            ("b2", "b3"),
            ("d5", "d4"),
            ("c3", "e4"),
            ("e7", "e5"),
            ("c1", "b2"),
            ("b7", "b6"),
            ("a1", "c1"),
            ("f8", "e7"),
            ("g2", "g3"),
            ("g8", "h6"),
        ]
    )

    assert get_best_move(board, depth=3) != LegalMove(start=sq("h2"), end=sq("h4"))


def test_strategy6_prefers_central_knight_development_over_nh6_from_transcript() -> None:
    """Black should score and search normal knight development above the rim hop."""

    board = _board_from_moves(
        [
            ("g1", "f3"),
            ("d7", "d5"),
            ("b1", "c3"),
            ("b8", "c6"),
            ("b2", "b3"),
            ("d5", "d4"),
            ("c3", "e4"),
            ("e7", "e5"),
            ("c1", "b2"),
            ("b7", "b6"),
            ("a1", "c1"),
            ("f8", "e7"),
            ("g2", "g3"),
        ]
    )

    central_development = ai.Move(start=sq("g8"), end=sq("f6"))
    rim_development = ai.Move(start=sq("g8"), end=sq("h6"))

    assert _move_order_score(board, central_development, None) > _move_order_score(
        board,
        rim_development,
        None,
    )
    assert get_best_move(board, depth=3) != LegalMove(start=sq("g8"), end=sq("h6"))


def test_strategy6_search_castles_in_transcript_before_slow_side_play() -> None:
    """The late-opening transcript position should now resolve king safety immediately."""

    board = _board_from_moves(
        [
            ("g1", "f3"),
            ("d7", "d5"),
            ("b1", "c3"),
            ("b8", "c6"),
            ("b2", "b3"),
            ("d5", "d4"),
            ("c3", "e4"),
            ("e7", "e5"),
            ("c1", "b2"),
            ("b7", "b6"),
            ("a1", "c1"),
            ("f8", "e7"),
            ("g2", "g3"),
            ("g8", "h6"),
            ("h2", "h4"),
            ("e8", "g8"),
            ("f1", "g2"),
            ("f7", "f5"),
            ("g2", "h3"),
            ("f5", "e4"),
            ("f3", "d4"),
            ("c6", "d4"),
            ("h3", "g2"),
            ("c8", "f5"),
            ("c2", "c3"),
            ("d4", "b5"),
            ("b3", "b4"),
            ("h6", "f7"),
            ("d1", "b3"),
            ("a7", "a5"),
            ("a2", "a4"),
            ("b5", "a7"),
        ]
    )

    assert get_best_move(board, depth=3) == LegalMove(start=sq("e1"), end=sq("g1"))


def test_strategy6_order_prefers_castling_over_bishop_retreat_when_king_unsettled() -> None:
    """Castling should outrank bishop drift, rook drift, and flank play with queens on board."""

    board = _task4_castling_board()

    castle = ai.Move(start=sq("e1"), end=sq("g1"))
    bishop_retreat = ai.Move(start=sq("g2"), end=sq("h3"))
    rook_drift = ai.Move(start=sq("h1"), end=sq("g1"))
    flank_push = ai.Move(start=sq("h2"), end=sq("h4"))

    assert _move_order_score(board, castle, None) > _move_order_score(
        board,
        bishop_retreat,
        None,
    )
    assert _move_order_score(board, castle, None) > _move_order_score(board, rook_drift, None)
    assert _move_order_score(board, castle, None) > _move_order_score(board, flank_push, None)


def test_strategy6_order_rejects_king_walk_when_castling_is_available() -> None:
    """Castling should outrank the one-step king walk in a balanced opening shell."""

    board = _task4_castling_board()
    castle = ai.Move(start=sq("e1"), end=sq("g1"))
    king_walk = ai.Move(start=sq("e1"), end=sq("f1"))

    assert _move_order_score(board, castle, None) > _move_order_score(board, king_walk, None)


def test_strategy6_evaluation_penalizes_abandoned_castling_rights_without_compensation() -> None:
    """Opening evaluation should dislike losing castling rights on the home rank."""

    intact_board = _task4_castling_board()

    lost_rights_board = _task4_castling_board()
    king = lost_rights_board.get_piece(sq("e1"))
    assert king is not None
    lost_rights_board.clear_square(sq("e1"))
    lost_rights_board.set_piece(sq("f1"), king)
    lost_rights_board.castling_rights.white_kingside = False
    lost_rights_board.castling_rights.white_queenside = False

    assert get_evaluation_breakdown(intact_board)["development"] > get_evaluation_breakdown(
        lost_rights_board
    )["development"]


def test_strategy6_search_prefers_clean_central_recapture_in_transition() -> None:
    """Black should complete the central recapture instead of drifting after ...fxe4."""

    board = _task5_transition_board()
    board.make_move(sq("f3"), sq("d4"))

    assert get_best_move(board, depth=3) == LegalMove(start=sq("c6"), end=sq("d4"))


def test_strategy6_search_keeps_king_safer_than_g_pawn_lunge_in_transition() -> None:
    """The tactical transition should keep development pressure before a kingside pawn lunge."""

    board = _task5_transition_board()
    board.make_move(sq("f3"), sq("d4"))
    board.make_move(sq("c6"), sq("d4"))
    board.make_move(sq("h3"), sq("g2"))

    assert get_best_move(board, depth=3) == LegalMove(start=sq("c8"), end=sq("f5"))


def test_strategy6_search_prefers_clearer_knight_route_over_na7_in_transition() -> None:
    """The winning knight should head for d6 instead of retreating to the rim."""

    board = _task5_transition_board()
    for start, end in [
        ("f3", "d4"),
        ("c6", "d4"),
        ("h3", "g2"),
        ("c8", "f5"),
        ("c2", "c3"),
        ("d4", "b5"),
        ("b3", "b4"),
        ("h6", "f7"),
        ("d1", "b3"),
        ("a7", "a5"),
        ("a2", "a4"),
    ]:
        board.make_move(sq(start), sq(end))

    assert get_best_move(board, depth=3) == LegalMove(start=sq("b5"), end=sq("d6"))


def test_strategy6_search_rejects_h5_when_simpler_transition_exists() -> None:
    """Black should not loosen the castled shell with ...h5 when cleaner moves exist."""

    board = _task5_transition_board()
    for start, end in [
        ("f3", "d4"),
        ("c6", "d4"),
        ("h3", "g2"),
        ("c8", "f5"),
        ("c2", "c3"),
        ("d4", "b5"),
        ("b3", "b4"),
        ("h6", "f7"),
        ("d1", "b3"),
        ("a7", "a5"),
        ("a2", "a4"),
        ("b5", "d6"),
        ("e1", "g1"),
    ]:
        board.make_move(sq(start), sq(end))

    best_move = get_best_move(board, depth=3)

    assert best_move != LegalMove(start=sq("h7"), end=sq("h5"))


def test_strategy6_search_prefers_knight_redeployment_that_tightens_conversion() -> None:
    """Black should reroute the knight cleanly instead of drifting in the winning phase."""

    board = _task6_conversion_board()
    board.make_move(sq("g8"), sq("h8"))
    board.make_move(sq("c7"), sq("f4"))

    assert get_best_move(board, depth=3) == LegalMove(start=sq("c8"), end=sq("d6"))


def test_strategy6_search_prefers_clean_rook_capture_during_conversion() -> None:
    """The winning side should cash the queenside pawn instead of maneuvering harmlessly."""

    board = _task6_conversion_board()
    for start, end in [
        ("g8", "h8"),
        ("c7", "f4"),
        ("c8", "d6"),
        ("f1", "a1"),
        ("f5", "g4"),
        ("a1", "a2"),
        ("b6", "b5"),
        ("g2", "e4"),
        ("d6", "e4"),
        ("f4", "e4"),
    ]:
        board.make_move(sq(start), sq(end))

    assert get_best_move(board, depth=3) == LegalMove(start=sq("a8"), end=sq("a4"))


def test_strategy6_depth3_prefers_queen_trade_in_won_ending() -> None:
    """Depth-3 search should still simplify into a clearly won queenless ending."""

    board = Board()
    board.clear_board()
    for square, color, kind in [
        ("g3", Color.WHITE, PieceType.KING),
        ("d4", Color.WHITE, PieceType.QUEEN),
        ("a1", Color.WHITE, PieceType.ROOK),
        ("g7", Color.BLACK, PieceType.KING),
        ("d7", Color.BLACK, PieceType.QUEEN),
    ]:
        board.set_piece(sq(square), create_piece(color, kind))
    board.turn = Color.WHITE

    assert get_best_move(board, depth=3) == LegalMove(start=sq("d4"), end=sq("d7"))


def test_strategy6_review_rejects_knight_wing_drift_before_castling() -> None:
    """The review opening should keep central development ahead of Nh4 drift."""

    board = _task7_review_board()
    central_break = ai.Move(start=sq("d2"), end=sq("d4"))
    knight_drift = ai.Move(start=sq("f3"), end=sq("h4"))

    assert _move_order_score(board, central_break, None) > _move_order_score(
        board,
        knight_drift,
        None,
    )
    assert get_best_move(board, depth=3) != LegalMove(start=sq("f3"), end=sq("h4"))


def test_strategy6_review_rejects_bishop_wing_drift_with_uncastled_king() -> None:
    """The review line should keep central stabilization ahead of Bh3 drift."""

    board = _task7_review_board()
    for start, end in [
        ("f3", "h4"),
        ("f5", "e6"),
        ("b2", "b4"),
        ("c6", "b4"),
        ("a2", "a3"),
        ("f6", "g4"),
        ("f2", "f4"),
        ("e8", "g8"),
        ("h4", "g6"),
        ("f7", "f5"),
    ]:
        board.make_move(sq(start), sq(end))
    central_break = ai.Move(start=sq("d2"), end=sq("d4"))
    bishop_drift = ai.Move(start=sq("f1"), end=sq("h3"))

    assert _move_order_score(board, central_break, None) > _move_order_score(
        board,
        bishop_drift,
        None,
    )


def test_strategy6_review_prefers_clean_conversion_capture_over_rook_shuffle() -> None:
    """The review conversion phase should value the clean bishop capture over ...Re8."""

    board = _task7_review_board()
    for start, end in [
        ("f3", "h4"),
        ("f5", "e6"),
        ("b2", "b4"),
        ("c6", "b4"),
        ("a2", "a3"),
        ("f6", "g4"),
        ("f2", "f4"),
        ("e8", "g8"),
        ("h4", "g6"),
        ("f7", "f5"),
        ("f1", "h3"),
        ("g4", "f2"),
        ("c3", "d5"),
        ("h7", "g6"),
        ("h3", "f5"),
    ]:
        board.make_move(sq(start), sq(end))
    simplify = ai.Move(start=sq("g6"), end=sq("f5"))
    rook_shuffle = ai.Move(start=sq("f8"), end=sq("e8"))

    assert _move_order_score(board, simplify, None) > _move_order_score(
        board,
        rook_shuffle,
        None,
    )
