"""Database of (position_key, outcome) pairs collected from self-play games."""
from __future__ import annotations

import json
import math
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _row_error(path: Path, line_no: int, reason: str) -> ValueError:
    """Build a line-numbered PositionDB row error."""
    return ValueError(f"{path}:{line_no}: invalid PositionDB row: {reason}")


def _require_pos(rec: dict[str, Any], path: Path, line_no: int) -> str:
    """Return a validated non-empty ``pos`` string or raise."""
    if "pos" not in rec:
        raise _row_error(path, line_no, "missing 'pos'")
    pos = rec["pos"]
    if not isinstance(pos, str) or not pos:
        raise _row_error(path, line_no, f"'pos' must be a non-empty string, got {pos!r}")
    return pos


def _parse_old_outcome(rec: dict[str, Any], path: Path, line_no: int) -> float:
    """Validate an old-format ``outcome`` (finite, in [0, 1])."""
    raw = rec["outcome"]
    if isinstance(raw, bool) or not isinstance(raw, (int, float)):
        raise _row_error(path, line_no, f"'outcome' must be a number, got {raw!r}")
    outcome = float(raw)
    if not math.isfinite(outcome):
        raise _row_error(path, line_no, "'outcome' must be finite")
    if not 0.0 <= outcome <= 1.0:
        raise _row_error(path, line_no, f"'outcome' must be in [0, 1], got {outcome}")
    return outcome


def _parse_new_stats(rec: dict[str, Any], path: Path, line_no: int) -> tuple[float, int]:
    """Validate new-format ``total``/``count`` (count int>0, 0<=total<=count)."""
    if "total" not in rec or "count" not in rec:
        raise _row_error(path, line_no, "new format requires both 'total' and 'count'")
    count = rec["count"]
    if isinstance(count, bool) or not isinstance(count, int):
        raise _row_error(path, line_no, f"'count' must be an int, got {count!r}")
    if count <= 0:
        raise _row_error(path, line_no, f"'count' must be > 0, got {count}")
    total_raw = rec["total"]
    if isinstance(total_raw, bool) or not isinstance(total_raw, (int, float)):
        raise _row_error(path, line_no, f"'total' must be a number, got {total_raw!r}")
    total = float(total_raw)
    if not math.isfinite(total):
        raise _row_error(path, line_no, "'total' must be finite")
    if not 0.0 <= total <= count:
        raise _row_error(path, line_no, f"'total' must be in [0, count={count}], got {total}")
    return total, count


@dataclass
class PositionStats:
    """Running statistics for a single position."""

    total: float = 0.0
    count: int = 0

    def add(self, outcome: float) -> None:
        """Accumulate one more outcome observation."""
        self.total += outcome
        self.count += 1

    @property
    def mean(self) -> float:
        """Return the mean outcome; 0.5 (draw) when no data."""
        if self.count == 0:
            return 0.5
        return self.total / self.count


@dataclass
class GameRecord:
    """A completed game's positions and outcome."""

    positions: list[str] = field(default_factory=list)
    outcome: float = 0.5


class PositionDB:
    """Stores (position_key, PositionStats) pairs from self-play games.

    Duplicate FENs are aggregated: their outcomes are averaged rather than
    overwritten.  The serialised format uses JSONL with ``total`` and ``count``
    fields.  The old ``{"pos": ..., "outcome": ...}`` format is still accepted
    on load and converted to an equivalent ``PositionStats(total=outcome, count=1)``.
    """

    def __init__(self) -> None:
        self._data: dict[str, PositionStats] = {}

    def add_game(self, record: GameRecord) -> None:
        """Add all positions from a game record to the database."""
        for pos in record.positions:
            if pos not in self._data:
                self._data[pos] = PositionStats()
            self._data[pos].add(record.outcome)

    def save(self, path: Path) -> None:
        """Save the database to a JSON-lines file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            for pos_key, stats in self._data.items():
                entry = {"pos": pos_key, "total": stats.total, "count": stats.count}
                f.write(json.dumps(entry) + "\n")

    @classmethod
    def load(cls, path: Path) -> PositionDB:
        """Load a database from a JSON-lines file.

        Accepts both the old ``{"pos": ..., "outcome": ...}`` format (converted
        to ``PositionStats(total=outcome, count=1)`` and aggregated) and the new
        ``{"pos": ..., "total": ..., "count": ...}`` format.
        """
        db = cls()
        with path.open("r", encoding="utf-8") as f:
            for line_no, raw in enumerate(f, start=1):
                line = raw.strip()
                if not line:
                    continue
                db._ingest_row(path, line_no, line)
        return db

    def _ingest_row(self, path: Path, line_no: int, line: str) -> None:
        """Parse, validate and merge one non-empty JSONL row into the DB."""
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as exc:
            raise _row_error(path, line_no, f"invalid JSON: {exc.msg}") from exc
        if not isinstance(rec, dict):
            raise _row_error(path, line_no, f"expected a JSON object, got {type(rec).__name__}")
        pos = _require_pos(rec, path, line_no)
        has_old = "outcome" in rec
        has_new = "total" in rec or "count" in rec
        if has_old and has_new:
            raise _row_error(
                path, line_no, "ambiguous row: has both 'outcome' and 'total'/'count'"
            )
        stats = self._data.setdefault(pos, PositionStats())
        if has_old:
            stats.add(_parse_old_outcome(rec, path, line_no))
        elif has_new:
            total, count = _parse_new_stats(rec, path, line_no)
            stats.total += total
            stats.count += count
        else:
            raise _row_error(path, line_no, "row has neither 'outcome' nor 'total'/'count'")

    def __len__(self) -> int:
        return len(self._data)

    def all_pairs(self) -> list[tuple[str, float]]:
        """Return (fen, mean_outcome) pairs for all positions."""
        return [(pos, stats.mean) for pos, stats in self._data.items()]

    def get_stats(self, fen: str) -> PositionStats | None:
        """Return the PositionStats for a given FEN, or None if not found."""
        return self._data.get(fen)

    def sample(self, n: int) -> list[tuple[str, float]]:
        """Return up to n randomly sampled (fen, mean_outcome) pairs."""
        pairs = self.all_pairs()
        if n >= len(pairs):
            return pairs
        return random.sample(pairs, n)

    def split(
        self,
        validation_fraction: float = 0.20,
        seed: int = 0,
    ) -> tuple[list[tuple[str, float]], list[tuple[str, float]]]:
        """Return (train_pairs, val_pairs) using a deterministic held-out split.

        Split is by FEN key so duplicates do not leak between sets.
        """
        pairs = self.all_pairs()
        rng = random.Random(seed)
        shuffled = list(pairs)
        rng.shuffle(shuffled)
        split_at = max(1, int(len(shuffled) * (1.0 - validation_fraction)))
        return shuffled[:split_at], shuffled[split_at:]
