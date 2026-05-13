"""Chess board coordinate constants with type-safe enums."""

from dataclasses import dataclass
from enum import IntEnum
from typing import NamedTuple, List, Optional, Union
from pydantic import BaseModel, field_validator


# Board geometry constants
BOARD_SIZE = 8


# Color enum
class Color(IntEnum):
    WHITE = 1
    BLACK = 0


# PieceType enum
class PieceType(IntEnum):
    EMPTY = 0
    PAWN = 1
    KNIGHT = 2
    BISHOP = 3
    ROOK = 4
    QUEEN = 5
    KING = 6


# AlgebraicSquare is a NamedTuple for algebraic notation
AlgebraicSquare = NamedTuple("AlgebraicSquare", [("file", str), ("rank", int)])


class RowConstant:
    """Base class for row constant objects to enable type safety."""

    __slots__ = ("_value",)

    def __init__(self, value: int):
        self._value = value

    def __int__(self) -> int:
        return self._value

    def __eq__(self, other):
        if isinstance(other, RowConstant):
            return self._value == other._value
        if isinstance(other, int):
            return self._value == other
        return False

    def __hash__(self):
        return hash(self._value)

    def __repr__(self):
        # Return the rank name: row 0 = rank 8, row 7 = rank 1
        return f"ROW_{8 - self._value}"

    def __index__(self) -> int:
        """Enable use in range(), indexing, etc."""
        return self._value

    def __sub__(self, other: Union["RowConstant", int]) -> int:
        """Subtract another RowConstant or int, return int result."""
        other_value = int(other) if isinstance(other, RowConstant) else other
        return self._value - other_value

    def __add__(self, other: Union["RowConstant", int]) -> int:
        """Add another RowConstant or int, return int result."""
        other_value = int(other) if isinstance(other, RowConstant) else other
        return self._value + other_value

    def __rsub__(self, other: Union[int, "RowConstant"]) -> int:
        """Subtract this RowConstant from another int or RowConstant, return int result."""
        other_value = int(self) if isinstance(other, RowConstant) else other
        return other_value - self._value

    def __lt__(self, other: Union["RowConstant", int]) -> bool:
        """Compare less than another RowConstant or int."""
        other_value = int(other) if isinstance(other, RowConstant) else other
        return self._value < other_value

    def __gt__(self, other: Union["RowConstant", int]) -> bool:
        """Compare greater than another RowConstant or int."""
        other_value = int(other) if isinstance(other, RowConstant) else other
        return self._value > other_value

    def __le__(self, other: Union["RowConstant", int]) -> bool:
        """Compare less than or equal to another RowConstant or int."""
        other_value = int(other) if isinstance(other, RowConstant) else other
        return self._value <= other_value

    def __ne__(self, other: object) -> bool:
        if isinstance(other, RowConstant):
            return self._value != other._value
        if isinstance(other, int):
            return self._value != other
        return True


class ColConstant:
    """Base class for column constant objects to enable type safety."""

    __slots__ = ("_value",)

    def __init__(self, value: int):
        self._value = value

    def __int__(self) -> int:
        return self._value

    def __eq__(self, other: object) -> bool:
        if isinstance(other, ColConstant):
            return self._value == other._value
        if isinstance(other, int):
            return self._value == other
        return False

    def __hash__(self):
        return hash(self._value)

    def __repr__(self):
        # Return the file letter (a-h) instead of column index (0-7)
        return f"COL_{chr(ord('a') + self._value)}"

    def __index__(self) -> int:
        """Enable use in range(), indexing, etc."""
        return self._value

    def __sub__(self, other: Union["ColConstant", int]) -> int:
        """Subtract another ColConstant or int, return int result."""
        other_value = int(other) if isinstance(other, ColConstant) else other
        return self._value - other_value

    def __add__(self, other: Union["ColConstant", int]) -> int:
        """Add another ColConstant or int, return int result."""
        other_value = int(other) if isinstance(other, ColConstant) else other
        return self._value + other_value

    def __rsub__(self, other: Union[int, "ColConstant"]) -> int:
        """Subtract this ColConstant from another int or ColConstant, return int result."""
        other_value = int(self) if isinstance(other, ColConstant) else other
        return other_value - self._value

    def __lt__(self, other: Union["ColConstant", int]) -> bool:
        """Compare less than another ColConstant or int."""
        other_value = int(other) if isinstance(other, ColConstant) else other
        return self._value < other_value

    def __gt__(self, other: Union["ColConstant", int]) -> bool:
        """Compare greater than another ColConstant or int."""
        other_value = int(other) if isinstance(other, ColConstant) else other
        return self._value > other_value

    def __le__(self, other: Union["ColConstant", int]) -> bool:
        """Compare less than or equal to another ColConstant or int."""
        other_value = int(other) if isinstance(other, ColConstant) else other
        return self._value <= other_value

    def __ge__(self, other: Union["ColConstant", int]) -> bool:
        """Compare greater than or equal to another ColConstant or int."""
        other_value = int(other) if isinstance(other, ColConstant) else other
        return self._value >= other_value

    def __ne__(self, other: object) -> bool:
        if isinstance(other, ColConstant):
            return self._value != other._value
        if isinstance(other, int):
            return self._value != other
        return True


# Array coordinate constants (internal system)
# Canonical: row 0 = rank 8 (black back rank), row 7 = rank 1 (white back rank)
ROW_8 = RowConstant(0)  # array row 0 (rank 8)
ROW_7 = RowConstant(1)  # array row 1 (rank 7)
ROW_6 = RowConstant(2)  # array row 2 (rank 6)
ROW_5 = RowConstant(3)  # array row 3 (rank 5)
ROW_4 = RowConstant(4)  # array row 4 (rank 4)
ROW_3 = RowConstant(5)  # array row 5 (rank 3)
ROW_2 = RowConstant(6)  # array row 6 (rank 2)
ROW_1 = RowConstant(7)  # array row 7 (rank 1)

# ROW_0 as alias for ROW_8 (row 0)
ROW_0 = ROW_8  # array row 0 (alias for ROW_8)

# Mapping from array index to row constant
ROWS_BY_INDEX = [ROW_8, ROW_7, ROW_6, ROW_5, ROW_4, ROW_3, ROW_2, ROW_1]

COL_A = ColConstant(0)  # file a
COL_B = ColConstant(1)  # file b
COL_C = ColConstant(2)  # file c
COL_D = ColConstant(3)  # file d
COL_E = ColConstant(4)  # file e
COL_F = ColConstant(5)  # file f
COL_G = ColConstant(6)  # file g
COL_H = ColConstant(7)  # file h


# ConstantSquare is a Pydantic model for type-safe square coordinates
class ConstantSquare(BaseModel):
    """Type-safe representation of a board square using constant coordinate objects."""

    model_config = {"arbitrary_types_allowed": True}

    row: RowConstant
    col: ColConstant

    def __hash__(self) -> int:
        return hash((self.row, self.col))

    def __eq__(self, other):
        if isinstance(other, ConstantSquare):
            return self.row == other.row and self.col == other.col
        if isinstance(other, (list, tuple)):
            return (
                len(other) == 2
                and int(self.row) == int(other[0])
                and int(self.col) == int(other[1])
            )
        return False

    def __int__(self) -> int:
        """Convert to integer index: row * 8 + col."""
        return int(self.row) * 8 + int(self.col)

    def __repr__(self):
        return f"ConstantSquare(row={self.row}, col={self.col})"

    def __str__(self):
        return f"{self.col}{self.row}"


# Type alias that enforces use of constant coordinate objects
# This allows runtime validation through ConstantSquare while maintaining
# type safety with int values
RowType = int
ColType = int


# Helper functions for creating ConstantSquare
def get_row_constant(row: int) -> RowConstant:
    """Convert integer row (0-7) to RowConstant."""
    if not (0 <= row < 8):
        raise ValueError(f"Row must be between 0 and 7, got {row}")
    return RowConstant(row)


def get_col_constant(col: int) -> ColConstant:
    """Convert integer column (0-7) to ColConstant."""
    if not (0 <= col < 8):
        raise ValueError(f"Column must be between 0 and 7, got {col}")
    return ColConstant(col)


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


def get_square_constant(row: int, col: int) -> ConstantSquare:
    """Convert integer coordinates to ConstantSquare."""
    return ConstantSquare(row=get_row_constant(row), col=get_col_constant(col))


# Type alias that enforces use of constant coordinate objects
# This allows runtime validation through ConstantSquare while maintaining
# type safety with int values
RowType = int
ColType = int
