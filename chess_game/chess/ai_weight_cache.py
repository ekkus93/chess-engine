"""Shared weight-cache state for the AI evaluator.

Kept in its own module so that the texel online-learning package can call
:func:`invalidate_weights_cache` without creating a circular import through
``ai.py`` (which imports ``chess_game.texel.weights_io``).

Only ``ai.py`` should call :func:`get_cached_weights`; all other code should
use :func:`invalidate_weights_cache` to signal that the on-disk file has
been updated.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from chess_game.chess.eval_weights import EvalWeights

# List-boxing makes the values mutable across module re-imports and allows
# both ai.py and online_learning.py to share the same cache without globals.
_cache: list[EvalWeights | None] = [None]
_loaded: list[bool] = [False]


def is_loaded() -> bool:
    """Return True if the cache has already been populated."""
    return _loaded[0]


def get() -> EvalWeights | None:
    """Return the cached weights (may be None if not yet loaded)."""
    return _cache[0]


def set_cache(weights: EvalWeights | None) -> None:
    """Store *weights* in the cache and mark it as loaded."""
    _cache[0] = weights
    _loaded[0] = True


def invalidate_weights_cache() -> None:
    """Force reload of tuned weights on the next get_best_move call.

    Call this after saving new tuned weights to disk so the AI immediately
    picks them up without restarting the process.
    """
    _cache[0] = None
    _loaded[0] = False
