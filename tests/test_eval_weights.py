"""Unit tests for EvalWeights dataclass."""
from __future__ import annotations

import pytest

from chess_game.chess.eval_weights import EVAL_WEIGHTS_FLAT_LENGTH as FLAT_LIST_LENGTH
from chess_game.chess.eval_weights import EvalWeights


class TestEvalWeights:
    """Tests for EvalWeights round-trip and structural invariants."""

    def test_default_round_trips_through_dict(self) -> None:
        """EvalWeights.default() should round-trip through to_dict/from_dict."""
        w = EvalWeights.default()
        d1 = w.to_dict()
        w2 = EvalWeights.from_dict(d1)
        d2 = w2.to_dict()
        assert d1 == d2

    def test_default_round_trips_through_flat_list(self) -> None:
        """EvalWeights.default() should round-trip through to_flat_list/from_flat_list."""
        w = EvalWeights.default()
        w2 = EvalWeights.from_flat_list(w.to_flat_list())
        assert w == w2

    def test_flat_list_length_is_stable(self) -> None:
        """The flat list produced by EvalWeights.default() must have FLAT_LIST_LENGTH entries."""
        flat = EvalWeights.default().to_flat_list()
        assert len(flat) == FLAT_LIST_LENGTH

    def test_from_flat_list_rejects_wrong_length(self) -> None:
        """from_flat_list should raise ValueError for wrong-length input."""
        with pytest.raises(ValueError):
            EvalWeights.from_flat_list([0.0] * (FLAT_LIST_LENGTH - 1))
        with pytest.raises(ValueError):
            EvalWeights.from_flat_list([0.0] * (FLAT_LIST_LENGTH + 1))
