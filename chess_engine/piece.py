from dataclasses import dataclass

@dataclass(frozen=True)
class Piece:
    """Minimal representation of a chess piece."""
    kind: str  # 'p', 'n', 'b', 'r', 'q', 'k'
    color: str  # 'white' or 'black'

    @staticmethod
    def from_fen_char(ch: str) -> "Piece":
        color = "white" if ch.isupper() else "black"
        kind = ch.lower()
        return Piece(kind=kind, color=color)
