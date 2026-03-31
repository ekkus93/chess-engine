"""Chess board coordinate constants with type-safe enums."""

from enum import IntEnum
from typing import NamedTuple, List, Union, Any
from pydantic import BaseModel, field_validator, model_validator


class Square(NamedTuple):
    """A board square in array coordinates (row, col).

    Note: This is the internal array coordinate system, not algebraic notation.
    Row 0 = rank 1 (white back rank), Row 7 = rank 8 (black back rank)
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
        # Return the rank (1-8) instead of array row (0-7)
        # ROW_1 (rank 1) has value 0, ROW_8 (rank 8) has value 7
        return f"ROW_{self._value + 1}"

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

    def __ge__(self, other: Union["RowConstant", int]) -> bool:
        """Compare greater than or equal to another RowConstant or int."""
        other_value = int(other) if isinstance(other, RowConstant) else other
        return self._value >= other_value

    def __eq__(self, other: Union["RowConstant", int]) -> bool:
        if isinstance(other, RowConstant):
            return self._value == other._value
        if isinstance(other, int):
            return self._value == other
        return False

    def __ne__(self, other: Union["RowConstant", int]) -> bool:
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

    def __eq__(self, other):
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

    def __eq__(self, other: Union["ColConstant", int]) -> bool:
        if isinstance(other, ColConstant):
            return self._value == other._value
        if isinstance(other, int):
            return self._value == other
        return False

    def __ne__(self, other: Union["ColConstant", int]) -> bool:
        if isinstance(other, ColConstant):
            return self._value != other._value
        if isinstance(other, int):
            return self._value != other
        return True


# Array coordinate constants (internal system)
# ROW_N = array row (N-1)
# ROW_1 (rank 1) = row 0, ROW_8 (rank 8) = row 7
ROW_0 = RowConstant(7)  # array row 7 (rank 8)
ROW_1 = RowConstant(0)  # array row 0 (rank 1)
ROW_2 = RowConstant(1)  # array row 1 (rank 2)
ROW_3 = RowConstant(2)  # array row 2 (rank 3)
ROW_4 = RowConstant(3)  # array row 3 (rank 4)
ROW_5 = RowConstant(4)  # array row 4 (rank 5)
ROW_6 = RowConstant(5)  # array row 5 (rank 6)
ROW_7 = RowConstant(6)  # array row 6 (rank 7)
ROW_8 = RowConstant(7)  # array row 7 (rank 8)

# Add ROW_0 as alias for ROW_8 for compatibility
# Tests expect ROW_0 and ROW_8 to both represent rank 8 (row 7)
ROW_0 = ROW_8  # array row 7 (alias for ROW_8)

COL_A = ColConstant(0)  # file a
COL_B = ColConstant(1)  # file b
COL_C = ColConstant(2)  # file c
COL_D = ColConstant(3)  # file d
COL_E = ColConstant(4)  # file e
COL_F = ColConstant(5)  # file f
COL_G = ColConstant(6)  # file g
COL_H = ColConstant(7)  # file h

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
ALLOWED_ROW_VALUES = {ROW_0, ROW_1, ROW_2, ROW_3, ROW_4, ROW_5, ROW_6, ROW_7, ROW_8}
ALLOWED_COL_VALUES = {COL_A, COL_B, COL_C, COL_D, COL_E, COL_F, COL_G, COL_H}

# Ensure sets contain only constant objects, not raw integers
ALLOWED_ROW_VALUES = {row for row in ALLOWED_ROW_VALUES if isinstance(row, RowConstant)}
ALLOWED_COL_VALUES = {col for col in ALLOWED_COL_VALUES if isinstance(col, ColConstant)}


def get_row_constant(row: int) -> RowConstant:
    """Convert integer row index to RowConstant."""
    row_to_constant = {
        0: ROW_1,  # array row 0 = ROW_1 (rank 1)
        1: ROW_2,  # array row 1 = ROW_2 (rank 2)
        2: ROW_3,  # array row 2 = ROW_3 (rank 3)
        3: ROW_4,  # array row 3 = ROW_4 (rank 4)
        4: ROW_5,  # array row 4 = ROW_5 (rank 5)
        5: ROW_6,  # array row 5 = ROW_6 (rank 6)
        6: ROW_7,  # array row 6 = ROW_7 (rank 7)
        7: ROW_8,  # array row 7 = ROW_8 (rank 8)
    }
    try:
        return row_to_constant[row]
    except KeyError:
        raise ValueError(
            f"Invalid row index: {row}. Must be between 0 and 7."
        ) from None


def get_col_constant(col: int) -> ColConstant:
    """Convert integer col index to ColConstant."""
    col_to_constant = {
        0: COL_A,
        1: COL_B,
        2: COL_C,
        3: COL_D,
        4: COL_E,
        5: COL_F,
        6: COL_G,
        7: COL_H,
    }
    try:
        return col_to_constant[col]
    except KeyError:
        raise ValueError(
            f"Invalid column index: {col}. Must be between 0 and 7."
        ) from None


class ConstantSquare(BaseModel):
    """A type-safe board square that enforces use of coordinate constants.

    This model validates that row and column values are the constant objects
    themselves (ROW_1, ROW_2, etc.), not raw integer values.

    Example usage:
        square = ConstantSquare(row=ROW_4, col=COL_E)  # Valid
        square = ConstantSquare(row=4, col=5)           # Raises ValueError immediately
    """

    model_config = {"arbitrary_types_allowed": True}

    row: Union[int, RowConstant]
    col: Union[int, ColConstant]

    @field_validator("row", "col")
    @classmethod
    def validate_coordinate_type(cls, v, info):
        """Validate that coordinates are constant objects, not raw integers.

        This check happens IMMEDIATELY upon construction to catch errors early.
        """
        field_name = info.field_name
        # Check if it's a raw integer (not a constant object)
        if isinstance(v, int) and not isinstance(
            v, RowConstant if field_name == "row" else ColConstant
        ):
            raise ValueError(
                f"{field_name.capitalize()} coordinate {v} is a raw integer. "
                f"Use ROW_1 through ROW_8 (constant objects) for rows, "
                f"or COL_A through COL_H (constant objects) for columns. "
                f"Example: ConstantSquare(row=ROW_2, col=COL_E), not ConstantSquare(row=2, col=5)"
            )
        return v


def get_square_constant(row: int, col: int) -> ConstantSquare:
    """Convert integer coordinates to ConstantSquare."""
    return ConstantSquare(row=get_row_constant(row), col=get_col_constant(col))


def clear_board(board: List[PieceType]) -> None:
    """Clear all pieces from the board."""
    for i in range(len(board)):
        board[i] = PieceType.EMPTY


# Type alias that enforces use of constant coordinate objects
# This allows runtime validation through ConstantSquare while maintaining
# type safety with int values
RowType = int
ColType = int
