"""Game result parsing utilities."""

from typing import Optional


def outcome_from_message(message: str) -> Optional[float]:
    """Convert a terminal-message string to a Texel outcome float.

    Returns 1.0 if White wins, 0.0 if Black wins, 0.5 for any draw,
    or None if the result cannot be determined.
    """
    if "White wins" in message:
        return 1.0
    if "Black wins" in message:
        return 0.0
    if any(kw in message for kw in ("Stalemate", "Draw", "draw", "repetition", "fifty")):
        return 0.5
    return None
