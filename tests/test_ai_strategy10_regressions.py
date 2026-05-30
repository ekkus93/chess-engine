"""Transcript-driven regressions for STRATEGY10 white and black strategy."""

from chess_game.chess.ai_search_helpers import root_stability_adjustment
from chess_game.chess.board import Board, create_piece
from chess_game.chess.conversion_guidance import (
    _conversion_context,
    winning_conversion_order_bonus,
)
from chess_game.chess.endgame_evaluation import (
    _heavy_endgame_king_activity_bonus,
    evaluate_progress,
)
from chess_game.chess.move import Move
from chess_game.chess.opening_move_ordering import opening_discipline_order_score
from chess_game.chess.types import Color, PieceType
from tests.helpers import sq


def _build_board(
    pieces: list[tuple[str, Color, PieceType]],
    turn: Color,
) -> Board:
    board = Board()
    board.clear_board()
    for square, color, kind in pieces:
        board.set_piece(sq(square), create_piece(color, kind))
    board.turn = turn
    return board


def test_strategy10_white_prefers_central_pawn_over_minor_reroute() -> None:
    board = Board()
    board.make_move(sq("b1"), sq("c3"))
    board.make_move(sq("b8"), sq("c6"))
    central = Move(start=sq("d2"), end=sq("d4"))
    reroute = Move(start=sq("c3"), end=sq("d5"))
    assert root_stability_adjustment(board, central, _child_board(board, central)) > root_stability_adjustment(
        board,
        reroute,
        _child_board(board, reroute),
    )


def test_strategy10_white_penalises_second_minor_piece_move_before_development_is_complete() -> None:
    board = Board()
    board.make_move(sq("b1"), sq("c3"))
    repeat = Move(start=sq("c3"), end=sq("d5"))
    develop = Move(start=sq("g1"), end=sq("f3"))
    assert opening_discipline_order_score(board, PieceType.KNIGHT, repeat) < opening_discipline_order_score(
        board,
        PieceType.KNIGHT,
        develop,
    )


def test_strategy10_black_prefers_main_passer_push_over_shuffle() -> None:
    board = _build_board(
        [
            ("b2", Color.WHITE, PieceType.KING),
            ("d2", Color.WHITE, PieceType.ROOK),
            ("g7", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.ROOK),
            ("f6", Color.BLACK, PieceType.BISHOP),
            ("d5", Color.BLACK, PieceType.PAWN),
            ("a6", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.BLACK,
    )
    push = Move(start=sq("d5"), end=sq("d4"))
    shuffle = Move(start=sq("d8"), end=sq("d7"))
    assert root_stability_adjustment(board, push, _child_board(board, push)) > root_stability_adjustment(
        board,
        shuffle,
        _child_board(board, shuffle),
    )


def test_strategy10_black_conversion_bonus_requires_clear_material_edge() -> None:
    board = _build_board(
        [
            ("b2", Color.WHITE, PieceType.KING),
            ("d2", Color.WHITE, PieceType.ROOK),
            ("g7", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.ROOK),
        ],
        turn=Color.BLACK,
    )
    shuffle = Move(start=sq("d8"), end=sq("d7"))
    assert _conversion_context(board) is None
    assert winning_conversion_order_bonus(board, Color.BLACK, PieceType.ROOK, shuffle) == 0


def test_strategy10_winning_positions_reward_progress_over_shuffling() -> None:
    board = _build_board(
        [
            ("b2", Color.WHITE, PieceType.KING),
            ("d2", Color.WHITE, PieceType.ROOK),
            ("g7", Color.BLACK, PieceType.KING),
            ("d8", Color.BLACK, PieceType.ROOK),
            ("f6", Color.BLACK, PieceType.BISHOP),
            ("d5", Color.BLACK, PieceType.PAWN),
            ("a6", Color.BLACK, PieceType.PAWN),
        ],
        turn=Color.BLACK,
    )
    push = Move(start=sq("d5"), end=sq("d4"))
    shuffle = Move(start=sq("d8"), end=sq("d7"))
    assert evaluate_progress(_child_board(board, push), 80) > evaluate_progress(board, 80)
    assert root_stability_adjustment(board, push, _child_board(board, push)) > root_stability_adjustment(
        board,
        shuffle,
        _child_board(board, shuffle),
    )


def test_strategy10_winning_side_activates_king_earlier() -> None:
    active = _build_board(
        [
            ("b2", Color.WHITE, PieceType.KING),
            ("d2", Color.WHITE, PieceType.ROOK),
            ("e5", Color.BLACK, PieceType.KING),
            ("d6", Color.BLACK, PieceType.ROOK),
            ("f6", Color.BLACK, PieceType.BISHOP),
        ],
        turn=Color.BLACK,
    )
    passive = active.clone()
    passive.set_piece(sq("e5"), None)
    passive.set_piece(sq("h7"), create_piece(Color.BLACK, PieceType.KING))
    assert _heavy_endgame_king_activity_bonus(active, Color.BLACK) > _heavy_endgame_king_activity_bonus(
        passive,
        Color.BLACK,
    )


def _child_board(board: Board, move: Move) -> Board:
    child = board.clone()
    assert child.apply_legal_move(move.start, move.end, promotion=move.promotion)
    return child
