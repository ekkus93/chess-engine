"""Integration tests for repetition-aware root move selection."""

from __future__ import annotations

from chess_game.chess.ai import BestMoveOptions, get_best_move
from chess_game.chess.board import Board, create_piece
from chess_game.chess.position_utils import position_key
from chess_game.chess.types import Color, LegalMove, PieceType
from chess_game.chess.move import parse_move_notation
from tests.helpers import sq


def _board_from_move_texts(moves: list[str]) -> Board:
    board = Board()
    for text in moves:
        move = parse_move_notation(text)
        assert board.make_move(move.start, move.end, move.promotion)
    return board


def _as_move_key(move: LegalMove) -> tuple[object, object, object]:
    return move.start, move.end, move.promotion


def test_repetition_sensitive_position_counts_change_root_choice() -> None:
    """Supplying a repeated child key should alter a near-equal root choice."""

    board = _board_from_move_texts(
        [
            "d2d3",
            "g8h6",
            "b1a3",
            "b8a6",
            "g2g3",
            "g7g5",
            "c1g5",
            "a8b8",
            "e1d2",
            "d7d5",
            "c2c4",
            "f7f5",
        ]
    )
    options = BestMoveOptions(use_opening_book=False)
    baseline = get_best_move(board, depth=2, book_options=options)
    assert baseline is not None

    repeated_child = board.clone()
    assert repeated_child.make_move(baseline.start, baseline.end, baseline.promotion)
    repeated_key = position_key(repeated_child)

    with_counts = get_best_move(
        board,
        depth=2,
        position_counts={repeated_key: 3},
        book_options=options,
    )
    assert with_counts is not None
    assert _as_move_key(with_counts) != _as_move_key(baseline)


def test_winning_side_prefers_non_repeating_progress_move() -> None:
    """In a won position, search should prefer immediate pawn progress over rook checks."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("g6"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("h1"), create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(sq("b7"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("g8"), create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.WHITE

    rook_check_child = board.clone()
    assert rook_check_child.make_move(sq("h1"), sq("h8"))
    repeated_key = position_key(rook_check_child)

    best_move = get_best_move(
        board,
        depth=2,
        position_counts={repeated_key: 3},
        book_options=BestMoveOptions(use_opening_book=False),
    )
    assert best_move is not None
    # Best move should be immediate b-pawn promotion progress, not rook-check loop.
    assert best_move.start == sq("b7")
    assert best_move.end == sq("b8")

    chosen_child = board.clone()
    assert chosen_child.make_move(best_move.start, best_move.end, best_move.promotion)
    assert position_key(chosen_child) != repeated_key


def test_repetition_neutral_position_is_deterministic_and_legal() -> None:
    """Near-equal king ending should return a stable legal move across repeated calls."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("e2"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("e7"), create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.WHITE

    options = BestMoveOptions(use_opening_book=False)
    move_a = get_best_move(board, depth=2, book_options=options)
    move_b = get_best_move(board, depth=2, book_options=options)
    assert move_a is not None and move_b is not None
    assert _as_move_key(move_a) == _as_move_key(move_b)
    legal_move_keys = {
        (start, end, promotion) for start, end, promotion in board.get_legal_moves()
    }
    assert _as_move_key(move_a) in legal_move_keys

