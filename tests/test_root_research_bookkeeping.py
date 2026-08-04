"""Regression tests for root re-search score/move bookkeeping in ``_search_move_loop``.

FIX9 added a full-window re-search so a non-improving root move's *bounded*
``child_score`` (an alpha-beta fail-low/high value, not its exact value) cannot win
the root tie-break unless an exact re-search confirms it. FIX10 hardens the
*bookkeeping* around that re-search: once the exact score is known it must drive
the normal search-best update, so ``search_best_score`` / ``search_best_move`` —
and therefore alpha-beta, the TT store, and the returned root score — reflect the
exact value rather than the discarded bound.

These tests drive ``_search_move_loop`` directly with a scripted fake
``_evaluate_child_move`` that returns a *bounded* score on a move's first
evaluation and an *exact* score on the full-window re-search (its second
evaluation of the same move). They are deterministic and fast (no real search).
"""

import random
from collections import defaultdict

import pytest

from chess_game.chess import ai
from chess_game.chess.ai import INF, MinimaxParams, SearchContext, position_key
from chess_game.chess.board import Board
from chess_game.chess.move import Move
from chess_game.chess.types import LegalMove
from tests.helpers import sq


def _context() -> SearchContext:
    """A minimal deterministic search context with an empty transposition table."""
    return SearchContext(
        transposition_table={},
        killer_moves=[],
        position_counts={},
        deterministic=True,
        rng=random.Random(0),
    )


def _root_params(context: SearchContext, *, is_maximizing: bool = True) -> MinimaxParams:
    """Root-level params (``line_history`` length 1 enables the root selection path)."""
    return MinimaxParams(
        depth=2,
        alpha=-INF,
        beta=INF,
        is_maximizing=is_maximizing,
        context=context,
        line_history=("root",),
    )


class _ScriptedEval:
    """Fake ``_evaluate_child_move``.

    ``script`` maps ``(start, end)`` to ``(bounded, exact)`` where each value is a
    ``(score, root_tiebreak)`` pair. The first evaluation of a move returns its
    bounded value; the full-window re-search (the second evaluation of the same
    move) returns its exact value.
    """

    def __init__(self, script):
        self._script = script
        self._calls: dict = defaultdict(int)

    def __call__(self, board, move, params, alpha, beta):
        key = (move.start, move.end)
        self._calls[key] += 1
        bounded, exact = self._script[key]
        return exact if self._calls[key] >= 2 else bounded

    def call_count(self, move_key) -> int:
        return self._calls[move_key]


def _move(start: str, end: str) -> Move:
    return Move(start=sq(start), end=sq(end))


def test_bounded_high_tiebreak_move_cannot_promote_when_exact_is_worse(monkeypatch):
    """A fail-low bound dressed up with a high tie-break must not win the root.

    ``m_best`` is the genuine best (exact 100). ``m_poke`` looks like an 80-point
    near-tie with a huge tie-break (the FIX9 a2a4 pattern), but its exact
    full-window value is only 10. After the re-search it must be rejected and
    ``search_best`` must stay on ``m_best`` — both the returned move/score and the
    TT entry.
    """
    m_best = _move("d1", "d2")
    m_poke = _move("a1", "a2")
    fake = _ScriptedEval(
        {
            (m_best.start, m_best.end): ((100, 0), (100, 0)),
            (m_poke.start, m_poke.end): ((80, 999), (10, 999)),
        }
    )
    monkeypatch.setattr(ai, "_evaluate_child_move", fake)
    context = _context()

    score, move = ai._search_move_loop(Board(), [m_best, m_poke], _root_params(context))

    assert move == LegalMove(start=sq("d1"), end=sq("d2"))
    assert score == 100
    # The poke was actually re-searched (bounded + exact = 2 evaluations) ...
    assert fake.call_count((m_poke.start, m_poke.end)) == 2
    # ... and the TT stored the genuine best, not the discarded bound.
    entry = context.transposition_table[position_key(Board())]
    assert entry.score == 100
    assert entry.best_move == LegalMove(start=sq("d1"), end=sq("d2"))


def test_exact_better_rescore_updates_search_best_and_return(monkeypatch):
    """When the exact re-search proves a move is actually better, search-best follows.

    This is the core bookkeeping fix: before it, ``search_best_score`` /
    ``search_best_move`` kept the earlier move's value while ``root_selected_move``
    moved on, so the root returned a score belonging to a *different* move and the
    TT stored that stale pairing. The returned ``(score, move)`` and the TT entry
    must agree on the exact value (160) and the promoted move.
    """
    m_first = _move("d1", "d2")
    m_promoted = _move("h1", "h2")
    fake = _ScriptedEval(
        {
            (m_first.start, m_first.end): ((100, 0), (100, 0)),
            # Bounded 90 (non-improving) with a high tie-break triggers the
            # re-search; the exact value 160 proves it is genuinely best.
            (m_promoted.start, m_promoted.end): ((90, 999), (160, 999)),
        }
    )
    monkeypatch.setattr(ai, "_evaluate_child_move", fake)
    context = _context()

    score, move = ai._search_move_loop(
        Board(), [m_first, m_promoted], _root_params(context)
    )

    assert move == LegalMove(start=sq("h1"), end=sq("h2"))
    assert score == 160  # not the stale 100
    entry = context.transposition_table[position_key(Board())]
    assert entry.score == 160
    assert entry.best_move == LegalMove(start=sq("h1"), end=sq("h2"))


def test_genuine_exact_tie_is_resolved_deterministically(monkeypatch):
    """A re-search that confirms an exact tie is resolved the same way every run.

    ``m_tie`` is bounded a hair worse (90, high tie-break) so it is re-searched,
    and the exact value ties the running best (100). The deterministic tie-break
    must produce a stable result and the returned score must remain the tie value.
    """
    m_first = _move("d1", "d2")
    m_tie = _move("h1", "h2")
    script = {
        (m_first.start, m_first.end): ((100, 0), (100, 0)),
        (m_tie.start, m_tie.end): ((90, 999), (100, 999)),
    }
    monkeypatch.setattr(ai, "_evaluate_child_move", _ScriptedEval(script))
    score_a, move_a = ai._search_move_loop(
        Board(), [m_first, m_tie], _root_params(_context())
    )
    monkeypatch.setattr(ai, "_evaluate_child_move", _ScriptedEval(script))
    score_b, move_b = ai._search_move_loop(
        Board(), [m_first, m_tie], _root_params(_context())
    )

    assert score_a == 100
    assert (score_a, move_a) == (score_b, move_b)


def test_minimizing_side_bounded_move_cannot_promote_when_exact_is_worse(monkeypatch):
    """Mirror of the fail-low guard for the minimizing (Black-to-move) side.

    For the minimizer, ``m_best`` is exact -100; ``m_poke`` is bounded -80 with a
    high tie-break but truly +10 (much worse for Black). It must be rejected and
    ``search_best`` must stay on ``m_best``.
    """
    m_best = _move("d8", "d7")
    m_poke = _move("a8", "a7")
    fake = _ScriptedEval(
        {
            (m_best.start, m_best.end): ((-100, 0), (-100, 0)),
            (m_poke.start, m_poke.end): ((-80, 999), (10, 999)),
        }
    )
    monkeypatch.setattr(ai, "_evaluate_child_move", fake)
    context = _context()

    score, move = ai._search_move_loop(
        Board(), [m_best, m_poke], _root_params(context, is_maximizing=False)
    )

    assert move == LegalMove(start=sq("d8"), end=sq("d7"))
    assert score == -100
    entry = context.transposition_table[position_key(Board())]
    assert entry.score == -100
    assert entry.best_move == LegalMove(start=sq("d8"), end=sq("d7"))


if __name__ == "__main__":  # pragma: no cover - manual invocation convenience
    pytest.main([__file__, "-q"])
