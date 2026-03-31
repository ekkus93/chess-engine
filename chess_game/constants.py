"""Chess board coordinate constants with type-safe enums."""

from enum import IntEnum
from typing import NamedTuple
from pydantic import BaseModel, field_validator, model_validator
from typing import Any


class Square(NamedTuple):
    """A board square in array coordinates (row, col).

    Note: This is the internal array coordinate system, not algebraic notation.
    Row 0 = rank 8 (top), Row 7 = rank 1 (bottom)
    Column 0 = file 'a', Column 7 = file 'h'
    """

    row: int
    col: int


class AlgebraicSquare(NamedTuple):
    """A board square in algebraic notation coordinates.

    This is the external coordinate system used for user-facing API.
    Uses files a-h and ranks 1-8.

    Examples:
        'a1' = white's back rank, leftmost square
        'h8' = black's back rank, rightmost square
    """

    file: str  # 'a' through 'h'
    rank: int  # 1 through 8


class Color(IntEnum):
    """Piece colors."""

    WHITE = 1
    BLACK = 0


class PieceType(IntEnum):
    """Types of chess pieces."""

    PAWN = 1
    KNIGHT = 2
    BISHOP = 3
    ROOK = 4
    QUEEN = 5
    KING = 6


# Board geometry constants
BOARD_SIZE = 8

# Array coordinate constants (internal system)
# Row 0 = rank 8 (black back rank)
# Row 7 = rank 1 (white back rank)
ROW_8 = 0  # rank 8
ROW_7 = 1  # rank 7
ROW_6 = 2  # rank 6
ROW_5 = 3  # rank 5
ROW_4 = 4  # rank 4
ROW_3 = 5  # rank 3
ROW_2 = 6  # rank 2
ROW_1 = 7  # rank 1

COL_A = 0  # file a
COL_B = 1  # file b
COL_C = 2  # file c
COL_D = 3  # file d
COL_E = 4  # file e
COL_F = 5  # file f
COL_G = 6  # file g
COL_H = 7  # file h

# Algebraic coordinate constants (external system)
# These map directly to the array coordinates
A1 = AlgebraicSquare("a", 1)
B1 = AlgebraicSquare("b", 1)
C1 = AlgebraicSquare("c", 1)
D1 = AlgebraicSquare("d", 1)
E1 = AlgebraicSquare("e", 1)
F1 = AlgebraicSquare("f", 1)
G1 = AlgebraicSquare("g", 1)
H1 = AlgebraicSquare("h", 1)

A2 = AlgebraicSquare("a", 2)
B2 = AlgebraicSquare("b", 2)
C2 = AlgebraicSquare("c", 2)
D2 = AlgebraicSquare("d", 2)
E2 = AlgebraicSquare("e", 2)
F2 = AlgebraicSquare("f", 2)
G2 = AlgebraicSquare("g", 2)
H2 = AlgebraicSquare("h", 2)


def algebraic_to_array(algebraic: AlgebraicSquare) -> Square:
    """Convert algebraic notation to array coordinates.

    Args:
        algebraic: Square in algebraic notation (e.g., 'e2')

    Returns:
        Square in array coordinates (row, col)
    """
    files = "abcdefgh"
    file_char = algebraic.file.lower()
    if file_char not in files:
        raise ValueError(f"Invalid file character: {file_char}")
    file_idx = files.index(file_char)
    return Square(algebraic.rank - 1, file_idx)


def array_to_algebraic(square: Square) -> AlgebraicSquare:
    """Convert array coordinates to algebraic notation.

    Args:
        square: Square in array coordinates (row, col)

    Returns:
        AlgebraicSquare in algebraic notation (e.g., 'e2')
    """
    files = "abcdefgh"
    if not (0 <= square.row <= 7):
        raise ValueError(f"Invalid row: {square.row}")
    if not (0 <= square.col <= 7):
        raise ValueError(f"Invalid column: {square.col}")
    return AlgebraicSquare(files[square.col], 8 - square.row)


class ConstantValueError(ValueError):
    """Raised when a raw integer value is used instead of a constant."""

    def __init__(self, msg: str) -> None:
        super().__init__(msg)


def _check_constant_usage(value: int, allowed_constants: list[int]) -> None:
    """Enforce use of constants instead of raw values.

    This function raises an error when raw values are used instead of
    the defined constants (ROW_* and COL_*).

    Args:
        value: The integer value to check
        allowed_constants: List of allowed constant values

    Raises:
        ConstantValueError: If value is not in allowed_constants
    """
    if value not in allowed_constants:
        raise ConstantValueError(
            f"Raw value {value} used instead of constant. "
            "Use ROW_1 through ROW_8 for row coordinates, "
            "or COL_A through COL_H for column coordinates."
        )


# Pre-compute allowed constants for validation
ALLOWED_ROW_VALUES = {ROW_1, ROW_2, ROW_3, ROW_4, ROW_5, ROW_6, ROW_7, ROW_8}
ALLOWED_COL_VALUES = {COL_A, COL_B, COL_C, COL_D, COL_E, COL_F, COL_G, COL_H}


class ConstantSquare(BaseModel):
    """A type-safe board square that enforces use of coordinate constants.

    This model validates that row and column values are the constant objects
    themselves (ROW_1, ROW_2, etc.), not raw integer values.

    Example usage:
        square = ConstantSquare(row=ROW_4, col=COL_E)  # Valid
        square = ConstantSquare(row=4, col=5)           # Raises ValueError
    """

    row: int
    col: int

    @model_validator(mode="before")
    @classmethod
    def validate_coordinates(cls, values):
        """Validate that coordinates are constant objects, not raw integers."""
        if not isinstance(values, dict):
            return values

        row = values.get("row")
        col = values.get("col")

        # Only accept constant objects, reject raw integers
        if row not in {ROW_1, ROW_2, ROW_3, ROW_4, ROW_5, ROW_6, ROW_7, ROW_8}:
            raise ValueError(
                f"Row coordinate {row} must be a constant (ROW_1 through ROW_8)"
            )
        if col not in {COL_A, COL_B, COL_C, COL_D, COL_E, COL_F, COL_G, COL_H}:
            raise ValueError(
                f"Column coordinate {col} must be a constant (COL_A through COL_H)"
            )
        return values


# Type alias that enforces use of constant coordinate objects
# This allows runtime validation through ConstantSquare while maintaining
# type safety with int values
RowType = int
ColType = int
