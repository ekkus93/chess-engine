"""Annotated position database: PositionDB rows extended with Stockfish scores.

Extends the JSONL format with an optional ``sf_score_cp`` field (integer,
White-relative centipawns) written by the Stockfish annotator and consumed by
the SF-targeted fast-tune pipeline.

On-disk format (new rows have ``sf_score_cp``; old rows remain valid)::

    {"pos": "<fen>", "total": 0.5, "count": 1, "sf_score_cp": 42}
    {"pos": "<fen>", "total": 1.0, "count": 2}              # unannotated
    {"pos": "<fen>", "total": 0.0, "count": 1, "sf_score_cp": null}  # mate
"""
from __future__ import annotations

import json
import math
from pathlib import Path

from chess_game.texel.position_db import PositionDB, PositionStats


class AnnotatedPositionDB(PositionDB):
    """PositionDB extended with optional per-position Stockfish scores.

    ``sf_scores`` maps FEN → centipawn score (White-relative int) or ``None``
    for positions where Stockfish returned a mate score.  FENs absent from
    ``sf_scores`` are treated as unannotated.
    """

    def __init__(self) -> None:
        super().__init__()
        self.sf_scores: dict[str, int | None] = {}

    def has_annotations(self) -> bool:
        """Return True if any position has a non-None ``sf_score_cp``."""
        return any(v is not None for v in self.sf_scores.values())

    def annotated_pairs(self) -> list[tuple[str, int | None]]:
        """Return ``(fen, sf_score_cp)`` for every position in the DB.

        Positions with no entry in ``sf_scores`` yield ``None`` as the score.
        """
        return [(fen, self.sf_scores.get(fen)) for fen, _ in self.all_pairs()]

    def save(self, path: Path) -> None:
        """Save all positions to a JSONL file, including ``sf_score_cp`` when present."""
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as f:
            for pos_key, stats in self._data.items():
                entry: dict = {
                    "pos": pos_key,
                    "total": stats.total,
                    "count": stats.count,
                }
                if pos_key in self.sf_scores:
                    entry["sf_score_cp"] = self.sf_scores[pos_key]
                f.write(json.dumps(entry) + "\n")

    def _ingest_row(self, path: Path, line_no: int, line: str) -> None:
        """Parse one JSONL row, reading ``sf_score_cp`` when present."""
        super()._ingest_row(path, line_no, line)
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            return
        if not isinstance(rec, dict) or "pos" not in rec:
            return
        pos = rec["pos"]
        if "sf_score_cp" in rec:
            self.sf_scores[pos] = _parse_sf_score(rec["sf_score_cp"])

    @classmethod
    def load(cls, path: Path) -> AnnotatedPositionDB:
        """Load an annotated DB from a JSONL file."""
        db = cls()
        db._read_rows(path)
        return db


def _parse_sf_score(raw: object) -> int | None:
    """Return a validated sf_score_cp integer or None."""
    if raw is None:
        return None
    if isinstance(raw, bool) or not isinstance(raw, int):
        return None
    if not math.isfinite(raw):
        return None
    return raw


def save_annotated(
    db: PositionDB,
    scores: dict[str, int | None],
    path: Path,
) -> None:
    """Merge *db* with Stockfish *scores* and save to *path*.

    Positions where ``scores[fen]`` is ``None`` (mate score) are written with
    ``"sf_score_cp": null``.  Positions not in *scores* are written without the
    field (treated as unannotated on reload).

    Args:
        db: Source position database (game-outcome fields preserved).
        scores: Dict from ``annotate_db``; maps FEN → score or None.
        path: Output JSONL path.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    pairs = db.all_pairs()
    stats_map = {fen: db.get_stats(fen) for fen, _ in pairs}

    with path.open("w", encoding="utf-8") as f:
        for fen, _ in pairs:
            stats: PositionStats | None = stats_map[fen]
            if stats is None:
                continue
            entry: dict = {
                "pos": fen,
                "total": stats.total,
                "count": stats.count,
            }
            if fen in scores:
                entry["sf_score_cp"] = _parse_sf_score(scores[fen])
            f.write(json.dumps(entry) + "\n")
