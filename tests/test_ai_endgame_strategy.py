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
