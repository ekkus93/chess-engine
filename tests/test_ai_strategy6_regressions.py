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
