"""Load and save EvalWeights from/to JSON files."""
from __future__ import annotations

import json
from pathlib import Path

from chess_game.chess.eval_weights import EvalWeights

TUNED_WEIGHTS_PATH = Path("chess_game/chess/data/tuned_weights.json")


def save_weights(weights: EvalWeights, path: Path) -> None:
    """Serialize weights to pretty-printed JSON."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        json.dump(weights.to_dict(), f, indent=2)


def load_weights(path: Path) -> EvalWeights:
    """Load weights from a JSON file. Raises FileNotFoundError or ValueError."""
    if not path.exists():
        raise FileNotFoundError(f"Weights file not found: {path}")
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not isinstance(data, dict):
            kind = type(data).__name__
            raise ValueError(
                f"Malformed weights file {path}: expected dict, got {kind}"
            )
        return EvalWeights.from_dict(data)
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError(f"Malformed weights file {path}: {exc}") from exc


def load_weights_or_default(path: Path | None) -> EvalWeights:
    """Load weights if path exists, else return EvalWeights.default()."""
    if path is None or not path.exists():
        return EvalWeights.default()
    return load_weights(path)
