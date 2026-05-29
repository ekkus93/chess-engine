"""Defensive coordination regressions for STRATEGY3."""

from chess_game.chess import ai
from chess_game.chess.ai import get_best_move
from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, LegalMove, PieceType
from tests.test_ai_quality import _move_order_score, _empty_board_with_kings
from tests.helpers import sq


def _build_board(pieces: list[tuple[str, Color, PieceType]], turn: Color) -> Board:
    board = _empty_board_with_kings()
    board.clear_board()
    for square, color, kind in pieces:
        board.set_piece(sq(square), create_piece(color, kind))
    board.turn = turn
    return board


def test_quiet_move_order_prefers_holding_file_over_harmless_check() -> None:
    """When the king is under pressure, holding the file should beat a showy check."""

    board = _build_board(
        [
            ("d1", Color.WHITE, PieceType.KING),
            ("a2", Color.WHITE, PieceType.ROOK),
            ("e2", Color.WHITE, PieceType.QUEEN),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.ROOK),
        ],
        Color.WHITE,
    )

    hold_file = ai.Move(start=sq("a2"), end=sq("d2"))
    harmless_check = ai.Move(start=sq("e2"), end=sq("e8"))

    assert _move_order_score(board, hold_file, None) > _move_order_score(
        board,
        harmless_check,
        None,
    )


def test_quiet_move_order_prefers_reconnecting_queen_to_king_zone() -> None:
    """A queen move that reconnects defense should beat a fresh flank drift."""

    board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("a5", Color.WHITE, PieceType.QUEEN),
            ("h1", Color.WHITE, PieceType.ROOK),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("h4", Color.BLACK, PieceType.QUEEN),
        ],
        Color.WHITE,
    )

    reconnect = ai.Move(start=sq("a5"), end=sq("e1"))
    drift = ai.Move(start=sq("a5"), end=sq("a7"))

    assert _move_order_score(board, reconnect, None) > _move_order_score(
        board,
        drift,
        None,
    )


def test_search_prefers_queen_trade_to_reduce_king_danger() -> None:
    """A danger-reducing queen trade should beat keeping the enemy attack alive."""

    board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("d1", Color.WHITE, PieceType.QUEEN),
            ("h1", Color.WHITE, PieceType.ROOK),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("d4", Color.BLACK, PieceType.QUEEN),
            ("e8", Color.BLACK, PieceType.ROOK),
        ],
        Color.WHITE,
    )

    best_move = get_best_move(board, depth=1)

    assert best_move == LegalMove(start=sq("d1"), end=sq("d4"))


def test_search_prefers_luft_over_pawn_grab_under_pressure() -> None:
    """Back-rank pressure should make luft outrank a loose pawn grab."""

    board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("h1", Color.WHITE, PieceType.ROOK),
            ("d1", Color.WHITE, PieceType.QUEEN),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("h8", Color.BLACK, PieceType.KING),
            ("h4", Color.BLACK, PieceType.QUEEN),
            ("h5", Color.BLACK, PieceType.PAWN),
        ],
        Color.WHITE,
    )

    best_move = get_best_move(board, depth=1)

    assert best_move == LegalMove(start=sq("g2"), end=sq("g3"))


def test_quiet_move_order_penalizes_moves_that_reduce_safe_king_squares() -> None:
    """A defensive move that increases king mobility should beat a loose queen drift."""

    board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("e2", Color.WHITE, PieceType.QUEEN),
            ("h1", Color.WHITE, PieceType.ROOK),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("h4", Color.BLACK, PieceType.QUEEN),
        ],
        Color.WHITE,
    )

    safer_move = ai.Move(start=sq("h1"), end=sq("e1"))
    loose_drift = ai.Move(start=sq("e2"), end=sq("a6"))

    assert _move_order_score(board, safer_move, None) > _move_order_score(
        board,
        loose_drift,
        None,
    )


def test_quiet_move_order_prefers_stopping_pawn_break_before_rook_improvement() -> None:
    """A move that kills the enemy central break should beat quiet piece improvement."""

    board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("d1", Color.WHITE, PieceType.QUEEN),
            ("a1", Color.WHITE, PieceType.ROOK),
            ("f1", Color.WHITE, PieceType.ROOK),
            ("c4", Color.WHITE, PieceType.BISHOP),
            ("f3", Color.WHITE, PieceType.KNIGHT),
            ("d4", Color.WHITE, PieceType.PAWN),
            ("e4", Color.WHITE, PieceType.PAWN),
            ("f2", Color.WHITE, PieceType.PAWN),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("g8", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.QUEEN),
            ("c5", Color.BLACK, PieceType.PAWN),
            ("d6", Color.BLACK, PieceType.PAWN),
            ("e5", Color.BLACK, PieceType.PAWN),
            ("f6", Color.BLACK, PieceType.KNIGHT),
            ("a7", Color.BLACK, PieceType.PAWN),
            ("h7", Color.BLACK, PieceType.PAWN),
        ],
        Color.WHITE,
    )

    stop_break = ai.Move(start=sq("d4"), end=sq("d5"))
    improve_rook = ai.Move(start=sq("a1"), end=sq("b1"))

    assert _move_order_score(board, stop_break, None) > _move_order_score(
        board,
        improve_rook,
        None,
    )


def test_strategy8_order_prefers_luft_when_queen_and_rook_battery_is_forming() -> None:
    """King shelter fixes should beat side activity under heavy-piece battery pressure."""

    board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("d1", Color.WHITE, PieceType.QUEEN),
            ("f1", Color.WHITE, PieceType.ROOK),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("h8", Color.BLACK, PieceType.KING),
            ("g4", Color.BLACK, PieceType.QUEEN),
            ("e8", Color.BLACK, PieceType.ROOK),
        ],
        Color.WHITE,
    )

    luft = ai.Move(start=sq("g2"), end=sq("g3"))
    side_play = ai.Move(start=sq("d1"), end=sq("a4"))

    assert _move_order_score(board, luft, None) > _move_order_score(board, side_play, None)


def test_strategy8_search_prefers_king_zone_defense_over_side_activity() -> None:
    """Depth-1 defensive choice should reinforce king safety before side play."""

    board = _build_board(
        [
            ("g1", Color.WHITE, PieceType.KING),
            ("d1", Color.WHITE, PieceType.QUEEN),
            ("h1", Color.WHITE, PieceType.ROOK),
            ("g2", Color.WHITE, PieceType.PAWN),
            ("h2", Color.WHITE, PieceType.PAWN),
            ("h8", Color.BLACK, PieceType.KING),
            ("g4", Color.BLACK, PieceType.QUEEN),
            ("e8", Color.BLACK, PieceType.ROOK),
            ("h5", Color.BLACK, PieceType.PAWN),
        ],
        Color.WHITE,
    )

    best_move = get_best_move(board, depth=1)

    assert best_move in [
        LegalMove(start=sq("d1"), end=sq("g4")),
        LegalMove(start=sq("g2"), end=sq("g3")),
        LegalMove(start=sq("h2"), end=sq("h3")),
        LegalMove(start=sq("h1"), end=sq("e1")),
    ]
