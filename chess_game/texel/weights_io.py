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
    """Load weights from a JSON file. Raises FileNotFoundError or ValueError.

    Use this for explicit, user-supplied weight paths: a missing or malformed file
    is an error, never a silent fall back to defaults.
    """
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
    except json.JSONDecodeError as exc:
        raise ValueError(f"Malformed weights file {path}: invalid JSON: {exc}") from exc
    except (KeyError, TypeError, AttributeError) as exc:
        raise ValueError(f"Malformed weights file {path}: {exc}") from exc


def load_optional_weights(path: Path | None) -> EvalWeights:
    """Strict optional load: defaults only when no path is given.

    Returns ``EvalWeights.default()`` only when ``path is None``. When a path is
    supplied it is loaded strictly via :func:`load_weights`, so a missing or
    malformed explicit file fails loudly instead of silently using defaults.
    """
    if path is None:
        return EvalWeights.default()
    return load_weights(path)


def load_weights_or_default(path: Path | None) -> EvalWeights:
    """Lenient auto-load: defaults when the path is missing OR not present.

    INTENTIONALLY SILENT fallback — use ONLY for the engine's automatic tuned-weight
    cache (``TUNED_WEIGHTS_PATH``), where running with default weights when no tuned
    file has been produced yet is the desired behavior. For any explicit,
    user-supplied path use :func:`load_weights` or :func:`load_optional_weights`.
    """
    if path is None or not path.exists():
        return EvalWeights.default()
    return load_weights(path)
