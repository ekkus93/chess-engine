"""Data-driven opening book for the chess engine.

The opening book is loaded from a JSON file and indexed by position key.
Two selection modes are supported:
- "highest_weight": deterministic — always picks the highest-weight candidate.
- "weighted_random": stochastic — samples a candidate proportional to weight,
  so varied self-play games naturally explore different opening lines.
"""

from __future__ import annotations

import json
import random
from collections.abc import Mapping
from dataclasses import dataclass
from functools import lru_cache
from importlib import resources
from pathlib import Path

from chess_game.chess.board import Board
from chess_game.chess.coords import index_to_algebraic
from chess_game.chess.move import parse_move_notation
from chess_game.chess.position_utils import position_key
from chess_game.chess.types import Color, LegalMove


class OpeningBookError(ValueError):
    """Error loading or validating opening book."""


@dataclass(frozen=True)
class OpeningLine:
    """A parsed opening line from the book."""

    name: str
    side: str
    eco: str | None
    moves: tuple[str, ...]
    weight: int
    tags: tuple[str, ...]


@dataclass(frozen=True)
class BookMove:
    """A move from the opening book for a specific position."""

    move: LegalMove
    name: str
    eco: str | None
    weight: int
    line_index: int
    ply_index: int
    tags: tuple[str, ...]


def load_opening_book_data(path: Path | str | None = None) -> dict:
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
        except json.JSONDecodeError as e:
            raise OpeningBookError(f"Invalid JSON in bundled opening book: {e}") from e
        except OSError as e:
            raise OpeningBookError(f"Failed to load bundled opening book: {e}") from e
    else:
        # Load from provided file path
        path_obj = Path(path) if isinstance(path, str) else path
        try:
            with path_obj.open("r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise OpeningBookError(f"Invalid JSON in opening book file {path_obj}: {e}") from e
        except OSError as e:
            raise OpeningBookError(f"Failed to load opening book from {path_obj}: {e}") from e

    if not isinstance(data, dict):
        raise OpeningBookError("Opening book data must be a JSON object")
    return data


def parse_opening_lines(data: Mapping[str, object]) -> list[OpeningLine]:
    """Parse and validate opening lines from raw JSON data."""
    if not isinstance(data, dict):
        raise OpeningBookError("Opening book data must be a JSON object")

    # Validate version
    version = data.get("version")
    if version != 1:
        raise OpeningBookError(f"Expected version 1, got {version}")

    # Validate selection
    selection = data.get("selection")
    if selection not in {"highest_weight", "weighted_random"}:
        raise OpeningBookError(
            f"'selection' must be 'highest_weight' or 'weighted_random', got {selection!r}"
        )

    # Validate lines
    lines_data = data.get("lines")
    if not isinstance(lines_data, list):
        raise OpeningBookError("'lines' must be a list")

    if not lines_data:
        raise OpeningBookError("'lines' must be non-empty")

    opening_lines: list[OpeningLine] = []
    for line_index, line_data in enumerate(lines_data):
        line = _validate_line(line_index, line_data)
        opening_lines.append(line)

    return opening_lines


def _validate_line(line_index: int, line_data: object) -> OpeningLine:
    """Validate and build a single opening line."""
    if not isinstance(line_data, dict):
        raise OpeningBookError(f"Line at index {line_index} must be a JSON object")

    # Validate required fields
    name = line_data.get("name")
    if not isinstance(name, str) or not name:
        raise OpeningBookError(f"Line at index {line_index}: 'name' must be a non-empty string")

    side = line_data.get("side")
    if side not in ("white", "black", "both"):
        msg = (
            f"Line at index {line_index} ({name!r}): 'side' must be "
            f"'white', 'black', or 'both', got {side!r}"
        )
        raise OpeningBookError(msg)

    moves_data = line_data.get("moves")
    if not isinstance(moves_data, list) or not moves_data:
        msg = (
            f"Line at index {line_index} ({name!r}): "
            "'moves' must be a non-empty list"
        )
        raise OpeningBookError(msg)

    for move in moves_data:
        if not isinstance(move, str):
            msg = (
                f"Line at index {line_index} ({name!r}): all moves must be "
                f"strings, got {type(move).__name__}"
            )
            raise OpeningBookError(msg)

    weight = line_data.get("weight")
    if not isinstance(weight, int) or weight <= 0:
        msg = (
            f"Line at index {line_index} ({name!r}): 'weight' must be "
            f"a positive integer, got {weight!r}"
        )
        raise OpeningBookError(msg)

    # Validate optional fields
    eco = line_data.get("eco")
    if eco is not None and not isinstance(eco, str):
        msg = (
            f"Line at index {line_index} ({name!r}): "
            "'eco' must be a string or null"
        )
        raise OpeningBookError(msg)

    tags_data = line_data.get("tags", [])
    if not isinstance(tags_data, list):
        msg = (
            f"Line at index {line_index} ({name!r}): "
            "'tags' must be a list"
        )
        raise OpeningBookError(msg)

    for tag in tags_data:
        if not isinstance(tag, str):
            msg = (
                f"Line at index {line_index} ({name!r}): all tags must be "
                f"strings, got {type(tag).__name__}"
            )
            raise OpeningBookError(msg)

    return OpeningLine(
        name=name,
        side=side,
        eco=eco,
        moves=tuple(moves_data),
        weight=weight,
        tags=tuple(tags_data),
    )


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

    def _move_identity(self, move) -> tuple[object, object, object | None]:
        """Extract move identity from either LegalMove dataclass or tuple format.

        Returns (start, end, promotion) tuple.
        """
        if isinstance(move, LegalMove):
            return move.start, move.end, move.promotion
        # Assume it's a tuple
        if isinstance(move, tuple) and len(move) == 3:
            return move
        return None, None, None

    def _should_index_line_move(self, line: OpeningLine, board: Board) -> bool:
        """Check if this line's move should be indexed for current board position."""
        if line.side == "both":
            return True
        if line.side == "white":
            return board.turn == Color.WHITE
        if line.side == "black":
            return board.turn == Color.BLACK
        return False

    def _build_index(self) -> None:
        """Build position index by replaying all opening lines.

        For each line, replay moves from the initial board and index
        BookMove candidates by position key.
        """
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

                # Store book move candidate only if side matches current position
                book_move = BookMove(
                    move=legal_move,
                    name=line.name,
                    eco=line.eco,
                    weight=line.weight,
                    line_index=line_index,
                    ply_index=ply_index,
                    tags=line.tags,
                )

                if self._should_index_line_move(line, board):
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

    def find_book_move(self, board: Board) -> LegalMove | None:
        """Find the best book move for the current position.

        Deterministic selection: highest weight, then lowest line_index,
        then lowest ply_index, then coordinate move string.
        """
        candidates = self.candidates_for(board)

        if not candidates:
            return None

        # Sort by: weight (desc), line_index (asc), ply_index (asc), move string (asc)
        def sort_key(candidate: BookMove) -> tuple:
            start_alg = index_to_algebraic(candidate.move.start)
            end_alg = index_to_algebraic(candidate.move.end)
            promotion_suffix = ""
            if candidate.move.promotion is not None:
                promotion_suffix = candidate.move.promotion.name.lower()[0]
            move_str = f"{start_alg}{end_alg}{promotion_suffix}"
            return (-candidate.weight, candidate.line_index, candidate.ply_index, move_str)

        sorted_candidates = sorted(candidates, key=sort_key)
        return sorted_candidates[0].move

    def find_book_move_random(
        self, board: Board, rng: random.Random | None = None
    ) -> LegalMove | None:
        """Sample a book move for the current position proportional to candidate weights.

        This produces varied self-play games while still favouring higher-weighted
        (more theoretically sound) moves.  Black candidates are automatically
        restricted to responses that are valid for the current position, so a
        Sicilian Defence will only appear if White played 1.e4, a King's Indian
        only if White played 1.d4, etc.

        When ``rng`` is provided, selection draws from that local generator so
        seeded callers are reproducible without mutating module-global RNG state.
        """
        candidates = self.candidates_for(board)
        if not candidates:
            return None
        weights = [c.weight for c in candidates]
        chooser = rng if rng is not None else random
        chosen = chooser.choices(candidates, weights=weights, k=1)[0]
        return chosen.move


@lru_cache(maxsize=1)
def get_bundled_opening_book() -> OpeningBook:
    """Get the bundled opening book (cached).

    This avoids repeated JSON parsing and validation.
    """
    return OpeningBook.bundled()
