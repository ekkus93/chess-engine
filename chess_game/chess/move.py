from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class Move:
    start: tuple[int, int]  # (row, col)
    end: tuple[int, int]  # (row, col)
    promotion: Optional[str] = None
