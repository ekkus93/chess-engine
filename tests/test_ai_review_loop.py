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


def test_review_loop_rejects_task9_knight_lunge() -> None:
    """Task 9 review should stop replaying the unsupported Ng5 lunge."""

    board = _board_from_moves(
        [
            ("b1", "c3", None),
            ("e7", "e5", None),
            ("g1", "f3", None),
            ("b8", "c6", None),
            ("c3", "e4", None),
            ("d7", "d5", None),
            ("e4", "g5", None),
            ("e5", "e4", None),
            ("e2", "e3", None),
            ("e4", "f3", None),
            ("g5", "f3", None),
            ("c8", "f5", None),
            ("f1", "e2", None),
            ("f8", "d6", None),
            ("e1", "g1", None),
            ("g8", "f6", None),
        ]
    )

    steady_move = ai.Move(start=sq("f1"), end=sq("e1"))
    knight_lunge = ai.Move(start=sq("f3"), end=sq("g5"))
    steady_board = board.clone()
    lunge_board = board.clone()

    steady_board.make_move(steady_move.start, steady_move.end)
    lunge_board.make_move(knight_lunge.start, knight_lunge.end)

    assert get_evaluation_breakdown(steady_board)["review_loop"] > get_evaluation_breakdown(
        lunge_board
    )["review_loop"]
    assert ai.get_best_move(board, depth=3) != ai.LegalMove(
        start=knight_lunge.start,
        end=knight_lunge.end,
    )


def test_review_loop_rejects_task10_opening_knight_lunge() -> None:
    """Task 10 acceptance review should not replay the early Ne4g5 lunge."""

    board = _board_from_moves(
        [
            ("b1", "c3", None),
            ("e7", "e5", None),
            ("g1", "f3", None),
            ("b8", "c6", None),
            ("c3", "e4", None),
            ("d7", "d5", None),
        ]
    )

    central_move = ai.Move(start=sq("c2"), end=sq("c3"))
    knight_lunge = ai.Move(start=sq("e4"), end=sq("g5"))
    central_board = board.clone()
    lunge_board = board.clone()

    central_board.make_move(central_move.start, central_move.end)
    lunge_board.make_move(knight_lunge.start, knight_lunge.end)

    assert _move_order_score(board, central_move, None) > _move_order_score(
        board,
        knight_lunge,
        None,
    )
    assert get_evaluation_breakdown(central_board)["development"] > get_evaluation_breakdown(
        lunge_board
    )["development"]
    assert ai.get_best_move(board, depth=3) != ai.LegalMove(
        start=knight_lunge.start,
        end=knight_lunge.end,
    )


def test_review_loop_rejects_task9_blocked_rook_sidestep() -> None:
    """Task 9 review should prefer active kingside coordination over Rb1."""

    board = _board_from_moves(
        [
            ("b1", "c3", None),
            ("e7", "e5", None),
            ("g1", "f3", None),
            ("b8", "c6", None),
            ("c3", "e4", None),
            ("d7", "d5", None),
            ("e4", "g5", None),
            ("e5", "e4", None),
            ("e2", "e3", None),
            ("e4", "f3", None),
            ("g5", "f3", None),
            ("c8", "f5", None),
            ("f1", "e2", None),
            ("f8", "d6", None),
            ("e1", "g1", None),
            ("g8", "f6", None),
            ("f3", "g5", None),
            ("e8", "g8", None),
            ("f2", "f3", None),
            ("h7", "h6", None),
            ("e3", "e4", None),
            ("h6", "g5", None),
            ("g1", "h1", None),
            ("f8", "e8", None),
            ("e4", "f5", None),
            ("c6", "d4", None),
            ("e2", "d3", None),
            ("e8", "e7", None),
        ]
    )

    active_move = ai.Move(start=sq("f1"), end=sq("e1"))
    rook_shuffle = ai.Move(start=sq("a1"), end=sq("b1"))
    active_board = board.clone()
    shuffle_board = board.clone()

    active_board.make_move(active_move.start, active_move.end)
    shuffle_board.make_move(rook_shuffle.start, rook_shuffle.end)

    assert get_evaluation_breakdown(active_board)["review_loop"] > get_evaluation_breakdown(
        shuffle_board
    )["review_loop"]
    assert ai.get_best_move(board, depth=3) != ai.LegalMove(
        start=rook_shuffle.start,
        end=rook_shuffle.end,
    )


def test_review_loop_rejects_task9_castled_flank_pawn_march() -> None:
    """Task 9 review should stop preferring ...g4 over concrete piece play."""

    board = _board_from_moves(
        [
            ("b1", "c3", None),
            ("e7", "e5", None),
            ("g1", "f3", None),
            ("b8", "c6", None),
            ("c3", "e4", None),
            ("d7", "d5", None),
            ("e4", "g5", None),
            ("e5", "e4", None),
            ("e2", "e3", None),
            ("e4", "f3", None),
            ("g5", "f3", None),
            ("c8", "f5", None),
            ("f1", "e2", None),
            ("f8", "d6", None),
            ("e1", "g1", None),
            ("g8", "f6", None),
            ("f3", "g5", None),
            ("e8", "g8", None),
            ("f2", "f3", None),
            ("h7", "h6", None),
            ("e3", "e4", None),
            ("h6", "g5", None),
            ("g1", "h1", None),
            ("f8", "e8", None),
            ("e4", "f5", None),
            ("c6", "d4", None),
            ("e2", "d3", None),
            ("e8", "e7", None),
            ("a1", "b1", None),
        ]
    )

    concrete_move = ai.Move(start=sq("d4"), end=sq("f5"))
    pawn_march = ai.Move(start=sq("g5"), end=sq("g4"))
    concrete_board = board.clone()
    march_board = board.clone()

    concrete_board.make_move(concrete_move.start, concrete_move.end)
    march_board.make_move(pawn_march.start, pawn_march.end)

    assert get_evaluation_breakdown(concrete_board)["review_loop"] < get_evaluation_breakdown(
        march_board
    )["review_loop"]
    assert ai.get_best_move(board, depth=3) != ai.LegalMove(
        start=pawn_march.start,
        end=pawn_march.end,
    )
