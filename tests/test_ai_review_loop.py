"""Task 10 review-loop regressions from fresh self-play transcripts."""

from chess_game.chess import ai
from chess_game.chess.ai import get_evaluation_breakdown
from chess_game.chess.board import Board
from tests.helpers import sq
from tests.test_ai_quality import _move_order_score


def _board_from_moves(moves: list[tuple[str, str, None]]) -> Board:
    board = Board()
    for start, end, promotion in moves:
        board.make_move(sq(start), sq(end), promotion=promotion)
    return board


def test_review_loop_penalizes_flank_pawn_poke_from_task10_transcript() -> None:
    """Task 10 transcript review should keep flexible development ahead of a4."""

    board = _board_from_moves(
        [
            ("g1", "f3", None),
            ("d7", "d5", None),
            ("b1", "c3", None),
            ("d5", "d4", None),
            ("c3", "e4", None),
            ("f7", "f5", None),
            ("e4", "c5", None),
            ("e7", "e5", None),
            ("c5", "d3", None),
            ("e5", "e4", None),
        ]
    )

    human_move = ai.Move(start=sq("g2"), end=sq("g3"))
    embarrassing_move = ai.Move(start=sq("a2"), end=sq("a4"))

    assert _move_order_score(board, human_move, None) > _move_order_score(
        board,
        embarrassing_move,
        None,
    )


def test_review_loop_penalizes_rook_shuffle_from_task10_transcript() -> None:
    """Task 10 transcript review should keep useful rook improvement over Rh1g1."""

    board = _board_from_moves(
        [
            ("g1", "f3", None),
            ("d7", "d5", None),
            ("b1", "c3", None),
            ("d5", "d4", None),
            ("c3", "e4", None),
            ("f7", "f5", None),
            ("e4", "c5", None),
            ("e7", "e5", None),
            ("c5", "d3", None),
            ("e5", "e4", None),
            ("a2", "a4", None),
            ("e4", "d3", None),
            ("c2", "d3", None),
            ("c8", "e6", None),
            ("b2", "b3", None),
            ("b8", "c6", None),
            ("c1", "b2", None),
            ("f8", "d6", None),
        ]
    )

    human_move = ai.Move(start=sq("a1"), end=sq("c1"))
    embarrassing_move = ai.Move(start=sq("h1"), end=sq("g1"))

    assert _move_order_score(board, human_move, None) > _move_order_score(
        board,
        embarrassing_move,
        None,
    )


def test_review_loop_rejects_rim_knight_development_from_task9_transcript() -> None:
    """Task 9 transcript review should keep ...Nf6 ahead of the passive ...Nh6."""

    board = _board_from_moves(
        [
            ("g1", "f3", None),
            ("d7", "d5", None),
            ("b1", "c3", None),
            ("b8", "c6", None),
            ("g2", "g3", None),
            ("d5", "d4", None),
            ("c3", "e4", None),
            ("e7", "e5", None),
            ("a1", "b1", None),
            ("c8", "e6", None),
            ("b2", "b3", None),
            ("b7", "b5", None),
            ("c1", "b2", None),
            ("f8", "e7", None),
            ("h2", "h4", None),
            ("a7", "a6", None),
            ("f1", "g2", None),
        ]
    )

    human_move = ai.Move(start=sq("g8"), end=sq("f6"))
    embarrassing_move = ai.Move(start=sq("g8"), end=sq("h6"))

    assert _move_order_score(board, human_move, None) > _move_order_score(
        board,
        embarrassing_move,
        None,
    )


def test_review_loop_penalizes_early_rook_sidestep_in_task10_position() -> None:
    """Task 10 review should keep bishop development ahead of the early Rb1 shuffle."""

    board = _board_from_moves(
        [
            ("g1", "f3", None),
            ("d7", "d5", None),
            ("b1", "c3", None),
            ("b8", "c6", None),
            ("g2", "g3", None),
            ("d5", "d4", None),
            ("c3", "e4", None),
            ("e7", "e5", None),
        ]
    )

    bishop_board = board.clone()
    bishop_board.make_move(sq("f1"), sq("g2"))
    rook_board = board.clone()
    rook_board.make_move(sq("a1"), sq("b1"))

    assert get_evaluation_breakdown(bishop_board)["total"] > get_evaluation_breakdown(
        rook_board
    )["total"]
