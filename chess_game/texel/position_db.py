"""Database of (position_key, outcome) pairs collected from self-play games."""
from __future__ import annotations

import json
import random
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class GameRecord:
    """A completed game's positions and outcome."""

    positions: list[str] = field(default_factory=list)
    outcome: float = 0.5


class PositionDB:
    """Stores (position_key, outcome) pairs from self-play games."""

    def __init__(self) -> None:
        # dict for deduplication: last-seen outcome wins
        self._data: dict[str, float] = {}

    def add_game(self, record: GameRecord) -> None:
        """Add all positions from a game record to the database."""
        for pos in record.positions:
            self._data[pos] = record.outcome

    def save(self, path: Path) -> None:
        """Save the database to a JSON-lines file."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            for pos_key, outcome in self._data.items():
                f.write(json.dumps({"pos": pos_key, "outcome": outcome}) + "\n")

    @classmethod
    def load(cls, path: Path) -> PositionDB:
        """Load a database from a JSON-lines file."""
        db = cls()
        with path.open("r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    rec = json.loads(line)
                    db._data[rec["pos"]] = rec["outcome"]
        return db

    def __len__(self) -> int:
        return len(self._data)

    def all_pairs(self) -> list[tuple[str, float]]:
        """Return all (position_key, outcome) pairs."""
        return list(self._data.items())

    def sample(self, n: int) -> list[tuple[str, float]]:
        """Return up to n randomly sampled (position_key, outcome) pairs."""
        pairs = self.all_pairs()
        if n >= len(pairs):
            return pairs
        return random.sample(pairs, n)
