"""Database of (position_key, outcome) pairs collected from self-play games."""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path


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
            for line in f:
                line = line.strip()
                if not line:
                    continue
                rec = json.loads(line)
                pos = rec["pos"]
                if pos not in db._data:
                    db._data[pos] = PositionStats()
                if "outcome" in rec:
                    # Old format: treat as one observation
                    db._data[pos].add(float(rec["outcome"]))
                else:
                    # New format: merge aggregated stats
                    db._data[pos].total += float(rec["total"])
                    db._data[pos].count += int(rec["count"])
        return db

    def __len__(self) -> int:
        return len(self._data)

    def all_pairs(self) -> list[tuple[str, float]]:
        """Return (fen, mean_outcome) pairs for all positions."""
        return [(pos, stats.mean) for pos, stats in self._data.items()]

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
