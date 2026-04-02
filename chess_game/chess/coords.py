"""Coordinate conversion helpers for chess notation."""

from typing import Tuple

from chess_game.chess.constants import (
    ConstantSquare,
    ROW_1,
    ROW_2,
    ROW_3,
    ROW_4,
    ROW_5,
    ROW_6,
    ROW_7,
    ROW_8,
)

from chess_game.chess.constants import get_col_constant

# Canonical coordinate definitions from THE_PLAN.md
# Files: a b c d e f g h
# Ranks: 1 2 3 4 5 6 7 8
# Internal board indexing:
# - row 0 = rank 1
# - row 7 = rank 8
# - col 0 = file a
# - col 7 = file h


def algebraic_to_index(algebraic: str) -> ConstantSquare:
    """Convert algebraic notation (e.g., 'e2') to board indices (row, col).

    Args:
        algebraic: Algebraic notation like 'e2'

    Returns:
        ConstantSquare of (row, col) where row=0 is rank 1, col=0 is file a

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

    # Convert file (a-h) to column constant - col 0 = file a
    col = get_col_constant(ord(file_char) - ord("a"))

    # Convert rank (1-8) to row constant - row 0 = rank 1
    row_map = {
        "1": ROW_1,
        "2": ROW_2,
        "3": ROW_3,
        "4": ROW_4,
        "5": ROW_5,
        "6": ROW_6,
        "7": ROW_7,
        "8": ROW_8,
    }
    row = row_map[rank_char]

    return ConstantSquare(row=row, col=col)


def index_to_algebraic(square: ConstantSquare) -> str:
    """Convert board indices (row, col) to algebraic notation.

    Args:
        square: ConstantSquare with row and col properties

    Returns:
        Algebraic notation like 'e2'

    Raises:
        ValueError: If indices are out of bounds
    """
    row = int(square.row)
    col = int(square.col)

    if not (0 <= row <= 7 and 0 <= col <= 7):
        raise ValueError(f"Invalid board indices: ({row}, {col})")

    # Convert row (0-7) to rank (1-8) - row 0 = rank 1
    rank = row + 1

    # Convert col (0-7) to file (a-h)
    file_char = chr(ord("a") + col)

    return f"{file_char}{rank}"


def parse_algebraic_move(move_str: str) -> Tuple[ConstantSquare, ConstantSquare]:
    """Parse algebraic notation like 'e2e4' into start and end positions.

    Args:
        move_str: Algebraic notation like 'e2e4'

    Returns:
        Tuple of (start_square, end_square)

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
