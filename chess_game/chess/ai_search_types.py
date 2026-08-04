"""Core search constants and data structures shared across the AI search.

Extracted from ``ai.py`` so the search constants, transposition-table types,
diagnostics, and parameter dataclasses live in one low-level module that the
search core and its helpers can all import without circular dependencies.
``ai.py`` re-exports every name here, so ``chess_game.chess.ai.<name>`` continues
to resolve unchanged.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from enum import Enum

from chess_game.chess.eval_weights import EvalWeights
from chess_game.chess.move import Move
from chess_game.chess.opening_book import OpeningBook
from chess_game.chess.types import LegalMove, PieceType

INF = 10_000_000
MATE_SCORE = 100_000
MATE_SCORE_MARGIN = 1_000  # Safe margin for ply adjustments
DRAW_SCORE = 0
ASPIRATION_WINDOW = 150
MAX_QUIESCENCE_DEPTH = 4
MAX_QUIESCENCE_MOVES = 8
LegalMoveKey = tuple[object, object, PieceType | None]


class TTFlag(Enum):
    """Transposition table entry flag."""
    EXACT = "exact"
    LOWERBOUND = "lowerbound"
    UPPERBOUND = "upperbound"


@dataclass(frozen=True)
class TTEntry:
    """Entry in the transposition table."""
    depth: int
    score: int
    best_move: LegalMove | None
    flag: TTFlag


@dataclass
class TTHitDiagnostics:
    """Diagnostics describing how TT entries were reused."""

    tt_exact_hits: int = 0
    tt_bound_hits: int = 0
    tt_depth_sum: int = 0
    tt_depth_uses: int = 0


@dataclass
class TacticalDiagnostics:
    """Diagnostics about quiescence branching."""

    tactical_move_sum: int = 0
    tactical_positions: int = 0
    tactical_max_width: int = 0


@dataclass
class SearchDiagnostics:
    """Detailed optional diagnostics gathered during search."""

    fail_high_retries: int = 0
    fail_low_retries: int = 0
    root_researches: int = 0
    selective_extensions: int = 0
    depth_timings: dict[int, float] | None = None
    tt: TTHitDiagnostics | None = None
    tactical: TacticalDiagnostics | None = None

    def __post_init__(self) -> None:
        """Ensure nested diagnostics are always available."""
        if self.tt is None:
            self.tt = TTHitDiagnostics()
        if self.tactical is None:
            self.tactical = TacticalDiagnostics()


@dataclass
class SearchStats:
    """Lightweight stats for search and diagnostics."""

    nodes: int = 0
    cutoffs: int = 0
    tt_hits: int = 0
    quiescence_nodes: int = 0
    diagnostics: SearchDiagnostics | None = None

    def __post_init__(self) -> None:
        """Ensure diagnostics are always available for callers."""
        if self.diagnostics is None:
            self.diagnostics = SearchDiagnostics()

    @property
    def fail_high_retries(self) -> int:
        """Expose fail-high retries without expanding top-level state."""
        assert self.diagnostics is not None
        return self.diagnostics.fail_high_retries

    @fail_high_retries.setter
    def fail_high_retries(self, value: int) -> None:
        assert self.diagnostics is not None
        self.diagnostics.fail_high_retries = value

    @property
    def fail_low_retries(self) -> int:
        """Expose fail-low retries without expanding top-level state."""
        assert self.diagnostics is not None
        return self.diagnostics.fail_low_retries

    @fail_low_retries.setter
    def fail_low_retries(self, value: int) -> None:
        assert self.diagnostics is not None
        self.diagnostics.fail_low_retries = value

    @property
    def root_researches(self) -> int:
        """Expose root re-search count without expanding top-level state."""
        assert self.diagnostics is not None
        return self.diagnostics.root_researches

    @root_researches.setter
    def root_researches(self, value: int) -> None:
        assert self.diagnostics is not None
        self.diagnostics.root_researches = value

    @property
    def tactical_move_sum(self) -> int:
        """Expose tactical move totals without expanding top-level state."""
        assert self.diagnostics is not None
        assert self.diagnostics.tactical is not None
        return self.diagnostics.tactical.tactical_move_sum

    @tactical_move_sum.setter
    def tactical_move_sum(self, value: int) -> None:
        assert self.diagnostics is not None
        assert self.diagnostics.tactical is not None
        self.diagnostics.tactical.tactical_move_sum = value

    @property
    def tactical_positions(self) -> int:
        """Expose tactical node count without expanding top-level state."""
        assert self.diagnostics is not None
        assert self.diagnostics.tactical is not None
        return self.diagnostics.tactical.tactical_positions

    @tactical_positions.setter
    def tactical_positions(self, value: int) -> None:
        assert self.diagnostics is not None
        assert self.diagnostics.tactical is not None
        self.diagnostics.tactical.tactical_positions = value

    @property
    def tactical_max_width(self) -> int:
        """Expose maximum tactical width without expanding top-level state."""
        assert self.diagnostics is not None
        assert self.diagnostics.tactical is not None
        return self.diagnostics.tactical.tactical_max_width

    @tactical_max_width.setter
    def tactical_max_width(self, value: int) -> None:
        assert self.diagnostics is not None
        assert self.diagnostics.tactical is not None
        self.diagnostics.tactical.tactical_max_width = value

    @property
    def depth_timings(self) -> dict[int, float] | None:
        """Expose per-depth timing diagnostics."""
        assert self.diagnostics is not None
        return self.diagnostics.depth_timings

    @depth_timings.setter
    def depth_timings(self, value: dict[int, float] | None) -> None:
        assert self.diagnostics is not None
        self.diagnostics.depth_timings = value

    @property
    def tt_exact_hits(self) -> int:
        """Expose exact TT hits."""
        assert self.diagnostics is not None
        assert self.diagnostics.tt is not None
        return self.diagnostics.tt.tt_exact_hits

    @tt_exact_hits.setter
    def tt_exact_hits(self, value: int) -> None:
        assert self.diagnostics is not None
        assert self.diagnostics.tt is not None
        self.diagnostics.tt.tt_exact_hits = value

    @property
    def tt_bound_hits(self) -> int:
        """Expose bound-based TT hits."""
        assert self.diagnostics is not None
        assert self.diagnostics.tt is not None
        return self.diagnostics.tt.tt_bound_hits

    @tt_bound_hits.setter
    def tt_bound_hits(self, value: int) -> None:
        assert self.diagnostics is not None
        assert self.diagnostics.tt is not None
        self.diagnostics.tt.tt_bound_hits = value

    @property
    def avg_tt_hit_depth(self) -> float:
        """Return the average depth of TT entries reused during search."""
        assert self.diagnostics is not None
        assert self.diagnostics.tt is not None
        if self.diagnostics.tt.tt_depth_uses == 0:
            return 0.0
        return self.diagnostics.tt.tt_depth_sum / self.diagnostics.tt.tt_depth_uses


@dataclass(frozen=True)
class BestMoveOptions:
    """Options that control opening-book lookup in get_best_move()."""

    use_opening_book: bool = True
    opening_book: OpeningBook | None = None
    random_opening_book: bool = False
    weights: EvalWeights | None = None
    deterministic: bool = False
    rng_seed: int | None = None


@dataclass
class SearchContext:
    """Shared search state reused across recursive calls."""

    transposition_table: dict[str, TTEntry] | None = None
    last_best_move: LegalMove | None = None
    nodes_searched: list[int] | None = None
    stats: SearchStats | None = None
    killer_moves: list[LegalMoveKey] | None = None
    position_counts: dict[str, int] | None = None
    weights: EvalWeights | None = None
    deterministic: bool = False
    rng: random.Random | None = None


@dataclass
class MinimaxParams:
    """Configuration for a minimax search."""

    depth: int
    alpha: int
    beta: int
    is_maximizing: bool
    context: SearchContext | None = None
    line_history: tuple[str, ...] = ()
    extension_budget: int = 1


@dataclass
class QuiescenceParams:
    """Parameters for quiescence search."""

    alpha: int
    beta: int
    is_maximizing: bool
    context: SearchContext | None = None
    depth_remaining: int = MAX_QUIESCENCE_DEPTH
    line_history: tuple[str, ...] = ()
    legal_moves: tuple[Move, ...] | None = None
