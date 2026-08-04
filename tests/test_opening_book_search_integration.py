"""Integration tests for opening-book hit/miss and search fallback behavior."""

from __future__ import annotations

import json

from chess_game.chess.ai import BestMoveOptions, get_best_move
from chess_game.chess.board import Board
from chess_game.chess.move import parse_move_notation
from chess_game.chess.opening_book import OpeningBook
from chess_game.chess.position_utils import position_key


def _apply_moves(board: Board, *move_texts: str) -> None:
    for text in move_texts:
        move = parse_move_notation(text)
        assert board.make_move(move.start, move.end, move.promotion)


def _is_legal(board: Board, move) -> bool:
    legal = {(start, end, promotion) for start, end, promotion in board.get_legal_moves()}
    return (move.start, move.end, move.promotion) in legal


def test_opening_book_hit_returns_book_candidate() -> None:
    """Starting position should return the bundled book candidate when enabled."""

    board = Board()
    book = OpeningBook.bundled()
    expected_book_move = book.find_book_move(board)
    assert expected_book_move is not None

    move = get_best_move(
        board,
        depth=2,
        book_options=BestMoveOptions(use_opening_book=True, opening_book=book),
    )
    assert move == expected_book_move


def test_opening_book_miss_falls_back_to_search_with_legal_move() -> None:
    """Off-book positions should still return legal search moves with book enabled."""

    board = Board()
    _apply_moves(board, "a2a3", "h7h6", "a3a4", "h6h5")
    book = OpeningBook.bundled()
    assert book.find_book_move(board) is None

    move = get_best_move(
        board,
        depth=2,
        book_options=BestMoveOptions(use_opening_book=True, opening_book=book),
    )
    assert move is not None
    assert _is_legal(board, move)


def test_custom_book_miss_still_falls_back_to_search(tmp_path) -> None:
    """Custom book load should not block fallback search when no line matches."""

    custom_book_path = tmp_path / "custom_book.json"
    custom_book_path.write_text(
        json.dumps(
            {
                "version": 1,
                "selection": "highest_weight",
                "lines": [
                    {
                        "name": "Only e4",
                        "side": "white",
                        "moves": ["e2e4"],
                        "weight": 1,
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    custom_book = OpeningBook.from_file(custom_book_path)

    board = Board()
    _apply_moves(board, "d2d4")
    assert custom_book.find_book_move(board) is None

    move = get_best_move(
        board,
        depth=2,
        book_options=BestMoveOptions(use_opening_book=True, opening_book=custom_book),
    )
    assert move is not None
    assert _is_legal(board, move)


def test_book_to_offbook_transition_keeps_repetition_aware_search() -> None:
    """After a book move then off-book branch, search should still honor position counts."""

    book = OpeningBook.bundled()
    board = Board()
    book_move = book.find_book_move(board)
    assert book_move is not None
    assert board.make_move(book_move.start, book_move.end, book_move.promotion)
    _apply_moves(board, "a7a6")
    assert book.find_book_move(board) is None

    baseline = get_best_move(
        board,
        depth=2,
        book_options=BestMoveOptions(use_opening_book=True, opening_book=book),
    )
    assert baseline is not None

    repeated_child = board.clone()
    assert repeated_child.make_move(baseline.start, baseline.end, baseline.promotion)
    repeated_key = position_key(repeated_child)
    with_counts = get_best_move(
        board,
        depth=2,
        position_counts={repeated_key: 3},
        book_options=BestMoveOptions(use_opening_book=True, opening_book=book),
    )
    assert with_counts is not None
    assert _is_legal(board, with_counts)

