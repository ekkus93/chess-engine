"""Data-driven opening book for the chess engine.

The opening book is loaded from a JSON file and indexed by position key.
Moves are validated during load to ensure they are legal.
Lookup is deterministic: highest weight wins, with tie-breaking by line_index, ply_index, and move string.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from pathlib import Path
from typing import TYPE_CHECKING, Mapping, Optional

from chess_game.chess.coords import index_to_algebraic
from chess_game.chess.move import parse_move_notation
from chess_game.chess.position_utils import position_key
from chess_game.chess.types import LegalMove

if TYPE_CHECKING:
    from chess_game.chess.board import Board


class OpeningBookError(ValueError):
    """Error loading or validating opening book."""

    pass


@dataclass(frozen=True)
class OpeningLine:
    """A parsed opening line from the book."""

    name: str
    side: str
    eco: Optional[str]
    moves: tuple[str, ...]
    weight: int
    tags: tuple[str, ...]


@dataclass(frozen=True)
class BookMove:
    """A move from the opening book for a specific position."""

    move: LegalMove
    name: str
    eco: Optional[str]
    weight: int
    line_index: int
    ply_index: int
    tags: tuple[str, ...]


def load_opening_book_data(path: Optional[Path | str] = None) -> dict:
    """Load opening book JSON data.

    If path is None, load bundled JSON using importlib.resources.
    If path is provided, load from that file.
    """
    if path is None:
        # Load bundled JSON using importlib.resources
        try:
            book_json = resources.files("chess_game.chess").joinpath("data/opening_book.json")
            with book_json.open("r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except Exception as e:
            raise OpeningBookError(f"Failed to load bundled opening book: {e}") from e
    else:
        # Load from provided file path
        try:
            path_obj = Path(path) if isinstance(path, str) else path
            with open(path_obj, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, dict) else {}
        except json.JSONDecodeError as e:
            raise OpeningBookError(f"Invalid JSON in opening book file {path}: {e}") from e
        except Exception as e:
            raise OpeningBookError(f"Failed to load opening book from {path}: {e}") from e


def parse_opening_lines(data: Mapping[str, object]) -> list[OpeningLine]:
    """Parse and validate opening lines from raw JSON data."""
    if not isinstance(data, dict):
        raise OpeningBookError("Opening book data must be a JSON object")

    # Validate version
    version = data.get("version")
    if version != 1:
        raise OpeningBookError(f"Expected version 1, got {version}")

    # Validate lines
    lines_data = data.get("lines")
    if not isinstance(lines_data, list):
        raise OpeningBookError("'lines' must be a list")

    if not lines_data:
        raise OpeningBookError("'lines' must be non-empty")

    opening_lines: list[OpeningLine] = []

    for line_index, line_data in enumerate(lines_data):
        if not isinstance(line_data, dict):
            raise OpeningBookError(f"Line at index {line_index} must be a JSON object")

        # Validate required fields
        name = line_data.get("name")
        if not isinstance(name, str) or not name:
            raise OpeningBookError(f"Line at index {line_index}: 'name' must be a non-empty string")

        side = line_data.get("side")
        if side not in ("white", "black", "both"):
            raise OpeningBookError(
                f"Line at index {line_index} ({name!r}): 'side' must be 'white', 'black', or 'both', got {side!r}"
            )

        moves_data = line_data.get("moves")
        if not isinstance(moves_data, list):
            raise OpeningBookError(f"Line at index {line_index} ({name!r}): 'moves' must be a list")

        if not moves_data:
            raise OpeningBookError(f"Line at index {line_index} ({name!r}): 'moves' must be non-empty")

        for move in moves_data:
            if not isinstance(move, str):
                raise OpeningBookError(
                    f"Line at index {line_index} ({name!r}): all moves must be strings, got {type(move).__name__}"
                )

        weight = line_data.get("weight")
        if not isinstance(weight, int) or weight <= 0:
            raise OpeningBookError(
                f"Line at index {line_index} ({name!r}): 'weight' must be a positive integer, got {weight!r}"
            )

        # Validate optional fields
        eco = line_data.get("eco")
        if eco is not None and not isinstance(eco, str):
            raise OpeningBookError(f"Line at index {line_index} ({name!r}): 'eco' must be a string or null")

        tags_data = line_data.get("tags", [])
        if not isinstance(tags_data, list):
            raise OpeningBookError(f"Line at index {line_index} ({name!r}): 'tags' must be a list")

        for tag in tags_data:
            if not isinstance(tag, str):
                raise OpeningBookError(
                    f"Line at index {line_index} ({name!r}): all tags must be strings, got {type(tag).__name__}"
                )

        opening_lines.append(
            OpeningLine(
                name=name,
                side=side,
                eco=eco,
                moves=tuple(moves_data),
                weight=weight,
                tags=tuple(tags_data),
            )
        )

    return opening_lines


class OpeningBook:
    """Opening book indexed by position key for fast lookup."""

    def __init__(self, lines: list[OpeningLine], data: dict):
        """Initialize opening book with parsed lines.

        Args:
            lines: List of parsed OpeningLine objects (already validated).
            data: Raw JSON data (for reference/debugging).
        """
        self.lines = lines
        self.data = data
        self._position_index: dict[str, list[BookMove]] = {}
        self._build_index()

    @classmethod
    def from_file(cls, path: Path | str) -> OpeningBook:
        """Load opening book from a file."""
        data = load_opening_book_data(path)
        lines = parse_opening_lines(data)
        return cls(lines, data)

    @classmethod
    def bundled(cls) -> OpeningBook:
        """Load the bundled opening book."""
        data = load_opening_book_data(None)
        lines = parse_opening_lines(data)
        return cls(lines, data)

    def _move_identity(self, move) -> tuple[object, object, Optional[object]]:
        """Extract move identity from either LegalMove dataclass or tuple format.

        Returns (start, end, promotion) tuple.
        """
        if isinstance(move, LegalMove):
            return move.start, move.end, move.promotion
        # Assume it's a tuple
        if isinstance(move, tuple) and len(move) == 3:
            return move
        return None, None, None

    def _build_index(self) -> None:
        """Build position index by replaying all opening lines.

        For each line, replay moves from the initial board and index
        BookMove candidates by position key.
        """
        from chess_game.chess.board import Board

        for line_index, line in enumerate(self.lines):
            board = Board()

            for ply_index, move_text in enumerate(line.moves):
                # Compute position key for current position
                pos_key = position_key(board)

                # Parse move notation
                try:
                    parsed_move = parse_move_notation(move_text)
                except ValueError as e:
                    raise OpeningBookError(
                        f"Invalid move notation {move_text!r} "
                        f"in line {line.name!r} "
                        f"(line_index={line_index}, ply_index={ply_index}): {e}"
                    ) from e

                # Convert parsed Move to LegalMove
                # parse_move_notation returns a Move with the same structure as LegalMove
                legal_move = LegalMove(
                    start=parsed_move.start, end=parsed_move.end, promotion=parsed_move.promotion
                )

                # Verify move is legal
                legal_moves = board.get_legal_moves()
                book_move_identity = self._move_identity(legal_move)
                is_legal = any(
                    self._move_identity(m) == book_move_identity
                    for m in legal_moves
                )

                if not is_legal:
                    raise OpeningBookError(
                        f"Illegal move {move_text!r} "
                        f"in line {line.name!r} "
                        f"(line_index={line_index}, ply_index={ply_index}): "
                        f"move not in legal moves for position"
                    )

                # Store book move candidate
                book_move = BookMove(
                    move=legal_move,
                    name=line.name,
                    eco=line.eco,
                    weight=line.weight,
                    line_index=line_index,
                    ply_index=ply_index,
                    tags=line.tags,
                )

                if pos_key not in self._position_index:
                    self._position_index[pos_key] = []

                self._position_index[pos_key].append(book_move)

                # Apply move to replay board
                board.make_move(legal_move.start, legal_move.end, legal_move.promotion)

    def candidates_for(self, board: Board) -> list[BookMove]:
        """Get all book move candidates for the current position.

        Returns candidates filtered to legal moves only.
        """
        pos_key = position_key(board)
        candidates = self._position_index.get(pos_key, [])

        # Filter to legal moves
        legal_moves = board.get_legal_moves()
        legal_candidates = [
            candidate
            for candidate in candidates
            if any(
                self._move_identity(m) == self._move_identity(candidate.move)
                for m in legal_moves
            )
        ]

        return legal_candidates

    def find_book_move(self, board: Board) -> Optional[LegalMove]:
        """Find the best book move for the current position.

        Deterministic selection: highest weight, then lowest line_index,
        then lowest ply_index, then coordinate move string.
        """
        candidates = self.candidates_for(board)

        if not candidates:
            return None

        # Sort by: weight (desc), line_index (asc), ply_index (asc), move string (asc)
        def sort_key(candidate: BookMove) -> tuple:
            from chess_game.chess.coords import index_to_algebraic

            start_alg = index_to_algebraic(candidate.move.start)
            end_alg = index_to_algebraic(candidate.move.end)
            move_str = f"{start_alg}{end_alg}"
            return (-candidate.weight, candidate.line_index, candidate.ply_index, move_str)

        sorted_candidates = sorted(candidates, key=sort_key)
        return sorted_candidates[0].move


@lru_cache(maxsize=1)
def get_bundled_opening_book() -> OpeningBook:
    """Get the bundled opening book (cached).

    This avoids repeated JSON parsing and validation.
    """
    return OpeningBook.bundled()
