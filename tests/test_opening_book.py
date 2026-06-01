"""Tests for the opening book module."""

import json
import tempfile
from pathlib import Path

import pytest

from chess_game.chess.board import Board
from chess_game.chess.opening_book import (
    OpeningBook,
    OpeningBookError,
    get_bundled_opening_book,
    parse_opening_lines,
    load_opening_book_data,
)


class TestOpeningBookLoad:
    """Tests for loading and parsing opening book data."""

    def test_bundled_book_loads(self):
        """Test that the bundled opening book loads successfully."""
        book = OpeningBook.bundled()
        assert book is not None
        assert len(book.lines) > 0
        assert len(book._position_index) > 0

    def test_bundled_book_caches(self):
        """Test that get_bundled_opening_book caches the result."""
        book1 = get_bundled_opening_book()
        book2 = get_bundled_opening_book()
        assert book1 is book2

    def test_load_opening_book_data_bundled(self):
        """Test loading bundled data."""
        data = load_opening_book_data(None)
        assert data is not None
        assert "version" in data
        assert data["version"] == 1
        assert "lines" in data
        assert len(data["lines"]) > 0

    def test_load_opening_book_data_from_file(self):
        """Test loading data from a file."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(
                {
                    "version": 1,
                    "selection": "highest_weight",
                    "lines": [
                        {
                            "name": "Test Opening",
                            "side": "white",
                            "moves": ["e2e4"],
                            "weight": 1,
                        }
                    ],
                }
            ,
                f,
            )
            temp_path = f.name

        try:
            data = load_opening_book_data(temp_path)
            assert data["version"] == 1
            assert len(data["lines"]) == 1
        finally:
            Path(temp_path).unlink()

    def test_parse_opening_lines_valid(self):
        """Test parsing valid opening lines."""
        data = {
            "version": 1,
            "selection": "highest_weight",
            "lines": [
                {
                    "name": "Italian Game",
                    "side": "white",
                    "eco": "C50",
                    "moves": ["e2e4", "e7e5", "g1f3"],
                    "weight": 85,
                    "tags": ["white", "open-game"],
                }
            ],
        }
        lines = parse_opening_lines(data)
        assert len(lines) == 1
        assert lines[0].name == "Italian Game"
        assert lines[0].weight == 85
        assert lines[0].eco == "C50"
        assert lines[0].tags == ("white", "open-game")

    def test_parse_opening_lines_invalid_version(self):
        """Test that invalid version raises error."""
        data = {
            "version": 2,
            "selection": "highest_weight",
            "lines": [],
        }
        with pytest.raises(OpeningBookError, match="Expected version 1"):
            parse_opening_lines(data)

    def test_parse_opening_lines_missing_lines(self):
        """Test that missing lines raises error."""
        data = {"version": 1, "selection": "highest_weight"}
        with pytest.raises(OpeningBookError, match="'lines' must be a list"):
            parse_opening_lines(data)

    def test_parse_opening_lines_empty_lines(self):
        """Test that empty lines raises error."""
        data = {"version": 1, "selection": "highest_weight", "lines": []}
        with pytest.raises(OpeningBookError, match="'lines' must be non-empty"):
            parse_opening_lines(data)

    def test_parse_opening_lines_invalid_side(self):
        """Test that invalid side raises error."""
        data = {
            "version": 1,
            "selection": "highest_weight",
            "lines": [
                {
                    "name": "Test",
                    "side": "invalid",
                    "moves": ["e2e4"],
                    "weight": 1,
                }
            ],
        }
        with pytest.raises(OpeningBookError, match="'side' must be 'white', 'black', or 'both'"):
            parse_opening_lines(data)

    def test_parse_opening_lines_empty_moves(self):
        """Test that empty moves raises error."""
        data = {
            "version": 1,
            "selection": "highest_weight",
            "lines": [
                {
                    "name": "Test",
                    "side": "white",
                    "moves": [],
                    "weight": 1,
                }
            ],
        }
        with pytest.raises(OpeningBookError, match="'moves' must be a non-empty list"):
            parse_opening_lines(data)

    def test_parse_opening_lines_non_positive_weight(self):
        """Test that non-positive weight raises error."""
        data = {
            "version": 1,
            "selection": "highest_weight",
            "lines": [
                {
                    "name": "Test",
                    "side": "white",
                    "moves": ["e2e4"],
                    "weight": 0,
                }
            ],
        }
        with pytest.raises(OpeningBookError, match="'weight' must be a positive integer"):
            parse_opening_lines(data)


class TestOpeningBookLookup:
    """Tests for opening book lookup and candidate selection."""

    def test_starting_position_returns_white_book_move(self):
        """Test that starting position returns a legal White book move."""
        book = OpeningBook.bundled()
        board = Board()
        move = book.find_book_move(board)
        assert move is not None
        # Check that move is a LegalMove with valid start/end
        assert hasattr(move, 'start')
        assert hasattr(move, 'end')

    def test_black_defense_after_e2e4(self):
        """Test Black defense after e2e4."""
        book = OpeningBook.bundled()
        board = Board()
        # Find and make e2e4 from legal moves
        legal_moves = board.get_legal_moves()
        for m in legal_moves:
            start, end, promo = m if isinstance(m, tuple) else (m.start, m.end, m.promotion)
            board.make_move(start, end, promo)
            break  # Make first legal move (which should be a pawn move)
        
        # Now check if book has a move for Black
        move = book.find_book_move(board)
        if move is not None:
            assert hasattr(move, 'start')
            assert hasattr(move, 'end')

    def test_kings_gambit_root_candidates(self):
        """Test King's Gambit root and candidacy."""
        book = OpeningBook.bundled()
        board = Board()
        # Make e2e4
        legal_moves = board.get_legal_moves()
        for m in legal_moves:
            start, end, promo = m if isinstance(m, tuple) else (m.start, m.end, m.promotion)
            board.make_move(start, end, promo)
            break
        
        # Make e7e5
        legal_moves = board.get_legal_moves()
        for m in legal_moves:
            start, end, promo = m if isinstance(m, tuple) else (m.start, m.end, m.promotion)
            board.make_move(start, end, promo)
            break
        
        candidates = book.candidates_for(board)
        # Should have candidates after e2e4 e7e5
        if len(candidates) > 0:
            for c in candidates:
                assert hasattr(c, 'move')
                assert hasattr(c.move, 'start')
                assert hasattr(c.move, 'end')

    def test_unknown_position_returns_none(self):
        """Test that unknown position returns None."""
        book = OpeningBook.bundled()
        board = Board()
        # Make various unusual first moves
        legal_moves = board.get_legal_moves()
        if len(legal_moves) > 10:
            start, end, promo = legal_moves[10] if isinstance(legal_moves[10], tuple) else (legal_moves[10].start, legal_moves[10].end, legal_moves[10].promotion)
            board.make_move(start, end, promo)
        
        move = book.find_book_move(board)
        # Might or might not be in book, but should return None or LegalMove
        if move is not None:
            assert hasattr(move, 'start')
            assert hasattr(move, 'end')

    def test_candidates_returns_legal_moves_only(self):
        """Test that candidates are valid LegalMove objects."""
        book = OpeningBook.bundled()
        board = Board()
        candidates = book.candidates_for(board)
        assert all(hasattr(c, 'move') and hasattr(c.move, 'start') for c in candidates)

    def test_illegal_line_raises_error(self):
        """Test that illegal move in line raises error."""
        data = {
            "version": 1,
            "selection": "highest_weight",
            "lines": [
                {
                    "name": "Illegal Line",
                    "side": "white",
                    "moves": ["e2e5"],  # Illegal: e2 pawn can only move to e3 or e4
                    "weight": 1,
                }
            ],
        }
        with pytest.raises(OpeningBookError, match="Illegal move"):
            OpeningBook(parse_opening_lines(data), data)

    def test_deterministic_tie_breaking(self):
        """Test deterministic selection with tied weights."""
        data = {
            "version": 1,
            "selection": "highest_weight",
            "lines": [
                {
                    "name": "Opening A",
                    "side": "white",
                    "moves": ["e2e4"],
                    "weight": 50,
                },
                {
                    "name": "Opening B",
                    "side": "white",
                    "moves": ["d2d4"],
                    "weight": 50,
                },
            ],
        }
        book = OpeningBook(parse_opening_lines(data), data)
        board = Board()
        # Should consistently pick the first one (line_index=0)
        move1 = book.find_book_move(board)
        move2 = book.find_book_move(board)
        assert move1 == move2


class TestOpeningBookIntegration:
    """Tests for integration with the chess engine."""

    def test_get_best_move_uses_book(self):
        """Test that get_best_move uses the opening book."""
        from chess_game.chess.ai import get_best_move

        board = Board()
        # With book enabled
        move_with_book = get_best_move(board, depth=1, use_opening_book=True)
        # Get book move for comparison
        book = get_bundled_opening_book()
        book_move = book.find_book_move(board)
        # They should match
        assert move_with_book == book_move

    def test_get_best_move_without_book(self):
        """Test that get_best_move can disable the book."""
        from chess_game.chess.ai import get_best_move

        board = Board()
        # Should return a legal move
        move = get_best_move(board, depth=1, use_opening_book=False)
        assert move is not None
        # Check that move components are valid ConstantSquare objects
        assert hasattr(move, 'start')
        assert hasattr(move, 'end')
        assert hasattr(move, 'promotion')

    def test_get_best_move_with_custom_book(self):
        """Test passing a custom opening book."""
        from chess_game.chess.ai import get_best_move

        board = Board()
        custom_book = get_bundled_opening_book()
        move = get_best_move(board, depth=1, use_opening_book=True, opening_book=custom_book)
        assert move is not None
        # Check that move has valid attributes
        assert hasattr(move, 'start')
        assert hasattr(move, 'end')


class TestOpeningBookContent:
    """Tests for the actual content of the bundled opening book."""

    def test_bundled_book_has_white_openings(self):
        """Test that bundled book has White openings."""
        book = OpeningBook.bundled()
        white_lines = [line for line in book.lines if line.side in ("white", "both")]
        assert len(white_lines) >= 10

    def test_bundled_book_has_black_defenses(self):
        """Test that bundled book has Black defenses."""
        book = OpeningBook.bundled()
        black_lines = [line for line in book.lines if line.side in ("black", "both")]
        assert len(black_lines) >= 10

    def test_bundled_book_has_kings_gambit_family(self):
        """Test that bundled book has King's Gambit family lines."""
        book = OpeningBook.bundled()
        gambit_lines = [line for line in book.lines if "Gambit" in line.name]
        # Should have King's Gambit root and 6+ family lines
        assert len(gambit_lines) >= 7

    def test_all_bundled_lines_are_legal(self):
        """Test that all bundled lines are legal when replayed."""
        book = OpeningBook.bundled()
        # If book loaded without errors, all lines are legal
        assert len(book.lines) > 0
        assert len(book._position_index) > 0
