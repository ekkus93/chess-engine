"""Coordinate conversion helpers for chess notation."""

from typing import Tuple

# Canonical coordinate definitions from THE_PLAN.md
# Files: a b c d e f g h
# Ranks: 1 2 3 4 5 6 7 8
# Internal board indexing:
# - row 0 = rank 8
# - row 7 = rank 1
# - col 0 = file a
# - col 7 = file h


def algebraic_to_index(algebraic: str) -> Tuple[int, int]:
    """Convert algebraic notation (e.g., 'e2') to board indices (row, col).

    Args:
        algebraic: Algebraic notation like 'e2'

    Returns:
        Tuple of (row, col) where row=0 is rank 8, col=0 is file a

    Raises:
        ValueError: If algebraic notation is invalid
    """
    if len(algebraic) != 2:
        raise ValueError(f"Invalid algebraic notation: {algebraic}")

    file_char = algebraic[0].lower()
    rank_char = algebraic[1]

    if file_char not in "abcdefgh":
        raise ValueError(f"Invalid file in algebraic notation: {file_char}")
    if rank_char not in "12345678":
        raise ValueError(f"Invalid rank in algebraic notation: {rank_char}")

    # Convert file (a-h) to column (0-7)
    col = ord(file_char) - ord("a")

    # Convert rank (1-8) to row (7-0) - reverse because row 0 = rank 8
    row = 8 - int(rank_char)

    return (row, col)


def index_to_algebraic(row: int, col: int) -> str:
    """Convert board indices (row, col) to algebraic notation.

    Args:
        row: Board row (0 = rank 8, 7 = rank 1)
        col: Board column (0 = file a, 7 = file h)

    Returns:
        Algebraic notation like 'e2'

    Raises:
        ValueError: If indices are out of bounds
    """
    if not (0 <= row <= 7 and 0 <= col <= 7):
        raise ValueError(f"Invalid board indices: ({row}, {col})")

    # Convert row (7-0) to rank (1-8) - reverse because row 0 = rank 8
    rank = 8 - row

    # Convert col (0-7) to file (a-h)
    file_char = chr(ord("a") + col)

    return f"{file_char}{rank}"


def parse_algebraic_move(move_str: str) -> Tuple[Tuple[int, int], Tuple[int, int]]:
    """Parse algebraic notation like 'e2e4' into start and end positions.

    Args:
        move_str: Algebraic notation like 'e2e4'

    Returns:
        Tuple of ((start_row, start_col), (end_row, end_col))

    Raises:
        ValueError: If move string is invalid
    """
    if len(move_str) != 4:
        raise ValueError(
            f"Invalid move format: {move_str}. Expected 4 characters like 'e2e4'"
        )

    start_pos = algebraic_to_index(move_str[0:2])
    end_pos = algebraic_to_index(move_str[2:4])

    return (start_pos, end_pos)
