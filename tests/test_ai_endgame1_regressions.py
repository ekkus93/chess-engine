"""Transcript-backed regressions for ENDGAME1 simple-endgame cleanup."""

from chess_game.chess import ai
from chess_game.chess.ai import get_best_move, position_key
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
