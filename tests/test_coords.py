"""Comprehensive unit tests for fundamental helper functions."""

from __future__ import annotations

import pytest
from chess_game.chess.coords import (
    algebraic_to_index,
    index_to_algebraic,
    parse_algebraic_move,
)
from chess_game.chess.constants import (
    get_row_constant,
    get_col_constant,
    get_square_constant,
    ROW_1,
    ROW_2,
    ROW_3,
    ROW_4,
    ROW_5,
    ROW_6,
    ROW_7,
    ROW_8,
    ConstantSquare,
    COL_A,
    COL_B,
    COL_C,
    COL_D,
    COL_E,
    COL_F,
    COL_G,
    COL_H,
    Color,
    PieceType,
)
from chess_game.chess.board import Board
from chess_game.chess.board import create_piece


# =============================================================================
# Tests for algebraic_to_index()
# =============================================================================


def test_algebraic_to_index_all_squares() -> None:
    """Test algebraic_to_index for all 64 squares."""
    # White back rank (rank 1 = row 0)
    assert algebraic_to_index("a1") == ConstantSquare(row=ROW_1, col=COL_A)
    assert algebraic_to_index("b1") == ConstantSquare(row=ROW_1, col=COL_B)
    assert algebraic_to_index("c1") == ConstantSquare(row=ROW_1, col=COL_C)
    assert algebraic_to_index("d1") == ConstantSquare(row=ROW_1, col=COL_D)
    assert algebraic_to_index("e1") == ConstantSquare(row=ROW_1, col=COL_E)
    assert algebraic_to_index("f1") == ConstantSquare(row=ROW_1, col=COL_F)
    assert algebraic_to_index("g1") == ConstantSquare(row=ROW_1, col=COL_G)
    assert algebraic_to_index("h1") == ConstantSquare(row=ROW_1, col=COL_H)

    # White front rank (rank 2 = row 1)
    assert algebraic_to_index("a2") == ConstantSquare(row=ROW_2, col=COL_A)
    assert algebraic_to_index("e2") == ConstantSquare(row=ROW_2, col=COL_E)

    # Black back rank (rank 8 = row 7)
    assert algebraic_to_index("a8") == ConstantSquare(row=ROW_8, col=COL_A)
    assert algebraic_to_index("h8") == ConstantSquare(row=ROW_8, col=COL_H)


def test_algebraic_to_index_uppercase() -> None:
    """Test that algebraic_to_index accepts uppercase notation."""
    assert algebraic_to_index("E2") == ConstantSquare(row=ROW_2, col=COL_E)
    assert algebraic_to_index("A1") == ConstantSquare(row=ROW_1, col=COL_A)


def test_algebraic_to_index_mixed_case() -> None:
    """Test mixed case notation."""
    assert algebraic_to_index("e2") == ConstantSquare(row=ROW_2, col=COL_E)
    assert algebraic_to_index("E2") == ConstantSquare(row=ROW_2, col=COL_E)
    assert algebraic_to_index("e2") == ConstantSquare(row=ROW_2, col=COL_E)


# =============================================================================
# Tests for index_to_algebraic()
# =============================================================================


def test_index_to_algebraic_all_squares() -> None:
    """Test index_to_algebraic for all 64 squares."""
    # Test all files for rank 1
    assert index_to_algebraic(ConstantSquare(row=ROW_1, col=COL_A)) == "a1"
    assert index_to_algebraic(ConstantSquare(row=ROW_1, col=COL_E)) == "e1"
    assert index_to_algebraic(ConstantSquare(row=ROW_1, col=COL_H)) == "h1"

    # Test all ranks for file e
    assert index_to_algebraic(ConstantSquare(row=ROW_1, col=COL_E)) == "e1"
    assert index_to_algebraic(ConstantSquare(row=ROW_2, col=COL_E)) == "e2"
    assert index_to_algebraic(ConstantSquare(row=ROW_8, col=COL_E)) == "e8"

    # Test corners
    assert index_to_algebraic(ConstantSquare(row=ROW_1, col=COL_A)) == "a1"
    assert index_to_algebraic(ConstantSquare(row=ROW_8, col=COL_H)) == "h8"


def test_index_to_algebraic_round_trip() -> None:
    """Test that algebraic_to_index and index_to_algebraic are inverses."""
    test_squares = [
        "a1",
        "a8",
        "e1",
        "e2",
        "h1",
        "h8",
        "a2",
        "e2",
        "a5",
        "h5",
    ]
    for algebraic in test_squares:
        square = algebraic_to_index(algebraic)
        result = index_to_algebraic(square)
        assert result == algebraic, f"Round trip failed for {algebraic}"


def test_index_to_algebraic_with_tuple() -> None:
    """Test that index_to_algebraic works with tuple inputs."""
    square = (1, 4)  # row 1, col 4 = e2

    class MockSquare:
        def __init__(self, row, col):
            self.row = row
            self.col = col

    result = index_to_algebraic(MockSquare(1, 4))
    assert result == "e2"


# =============================================================================
# Tests for parse_algebraic_move()
# =============================================================================


def test_parse_algebraic_move_valid_moves() -> None:
    """Test parse_algebraic_move with valid moves."""
    # Basic move
    result = parse_algebraic_move("e2e4")
    assert result[0] == ConstantSquare(row=ROW_2, col=COL_E)
    assert result[1] == ConstantSquare(row=ROW_4, col=COL_E)

    # Diagonal move
    result = parse_algebraic_move("e2g4")
    assert result[0] == ConstantSquare(row=ROW_2, col=COL_E)
    assert result[1] == ConstantSquare(row=ROW_4, col=COL_G)

    # King move
    result = parse_algebraic_move("e1e2")
    assert result[0] == ConstantSquare(row=ROW_1, col=COL_E)
    assert result[1] == ConstantSquare(row=ROW_2, col=COL_E)


def test_parse_algebraic_move_rejects_invalid() -> None:
    """Test that parse_algebraic_move rejects invalid input."""
    invalid_inputs = [
        "",  # Empty
        "e",  # Too short
        "e2",  # Too short
        "e2e",  # Too short
        "e2e",  # Too short
        "e2-e4",  # Contains dash
        "e2x4",  # Contains x
        "e9e4",  # Invalid rank
        "a9a4",  # Invalid rank
        "i2e4",  # Invalid file
        "h2i4",  # Invalid file
    ]
    for invalid in invalid_inputs:
        with pytest.raises((ValueError, AssertionError)):
            parse_algebraic_move(invalid)


# =============================================================================
# Tests for get_row_constant()
# =============================================================================


def test_get_row_constant_returns_correct_constants() -> None:
    """Test that get_row_constant returns the correct RowConstant objects."""
    assert get_row_constant(0) == ROW_1
    assert get_row_constant(1) == ROW_2
    assert get_row_constant(2) == ROW_3
    assert get_row_constant(3) == ROW_4
    assert get_row_constant(4) == ROW_5
    assert get_row_constant(5) == ROW_6
    assert get_row_constant(6) == ROW_7
    assert get_row_constant(7) == ROW_8


def test_get_row_constant_invalid() -> None:
    """Test that get_row_constant raises error for invalid values."""
    invalid_values = [-1, 8, 9, -10, 100]
    for invalid in invalid_values:
        with pytest.raises(ValueError):
            get_row_constant(invalid)


# =============================================================================
# Tests for get_col_constant()
# =============================================================================


def test_get_col_constant_returns_correct_constants() -> None:
    """Test that get_col_constant returns the correct ColConstant objects."""
    assert get_col_constant(0) == COL_A
    assert get_col_constant(1) == COL_B
    assert get_col_constant(2) == COL_C
    assert get_col_constant(3) == COL_D
    assert get_col_constant(4) == COL_E
    assert get_col_constant(5) == COL_F
    assert get_col_constant(6) == COL_G
    assert get_col_constant(7) == COL_H


def test_get_col_constant_invalid() -> None:
    """Test that get_col_constant raises error for invalid values."""
    invalid_values = [-1, 8, 9, -10, 100]
    for invalid in invalid_values:
        with pytest.raises(ValueError):
            get_col_constant(invalid)


# =============================================================================
# Tests for get_square_constant()
# =============================================================================


def test_get_square_constant_all_squares() -> None:
    """Test get_square_constant for all 64 squares."""
    # Test some key squares
    assert get_square_constant(0, 0) == ConstantSquare(row=ROW_1, col=COL_A)
    assert get_square_constant(0, 4) == ConstantSquare(row=ROW_1, col=COL_E)
    assert get_square_constant(7, 7) == ConstantSquare(row=ROW_8, col=COL_H)
    assert get_square_constant(1, 4) == ConstantSquare(row=ROW_2, col=COL_E)


def test_get_square_constant_invalid() -> None:
    """Test that get_square_constant raises error for invalid values."""
    # Invalid row
    with pytest.raises(ValueError):
        get_square_constant(-1, 4)
    with pytest.raises(ValueError):
        get_square_constant(8, 4)

    # Invalid col
    with pytest.raises(ValueError):
        get_square_constant(4, -1)
    with pytest.raises(ValueError):
        get_square_constant(4, 8)


# =============================================================================
# Tests for Board.create_piece()
# =============================================================================


def test_create_piece_white() -> None:
    """Test create_piece for white pieces."""
    piece = create_piece(Color.WHITE, PieceType.PAWN)
    assert piece.kind == PieceType.PAWN
    assert piece.color == Color.WHITE


def test_create_piece_black() -> None:
    """Test create_piece for black pieces."""
    piece = create_piece(Color.BLACK, PieceType.QUEEN)
    assert piece.kind == PieceType.QUEEN
    assert piece.color == Color.BLACK


# =============================================================================
# Tests for Board.set_piece()
# =============================================================================


def test_board_set_piece() -> None:
    """Test Board.set_piece helper."""
    board = Board()
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A), create_piece(Color.WHITE, PieceType.PAWN)
    )
    piece = board.get_piece(ConstantSquare(row=ROW_1, col=COL_A))
    assert piece.kind == PieceType.PAWN
    assert piece.color == Color.WHITE


def test_board_get_piece() -> None:
    """Test Board.get_piece helper."""
    board = Board()
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A), create_piece(Color.WHITE, PieceType.PAWN)
    )
    piece = board.get_piece(ConstantSquare(row=ROW_1, col=COL_A))
    assert piece.kind == PieceType.PAWN
    assert piece.color == Color.WHITE


# =============================================================================
# Tests for Board.get_piece()
# =============================================================================


def test_board_get_piece() -> None:
    """Test Board.get_piece helper."""
    board = Board()
    # Clear a1 which has a rook
    board.clear_square(ConstantSquare(row=ROW_1, col=COL_A))
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A), create_piece(Color.WHITE, PieceType.PAWN)
    )
    piece = board.get_piece(ConstantSquare(row=ROW_1, col=COL_A))
    assert piece == create_piece(
        Color.WHITE, PieceType.PAWN, ConstantSquare(row=ROW_1, col=COL_A)
    )


def test_board_get_piece_none() -> None:
    """Test Board.get_piece returns None for empty square."""
    board = Board()
    # Check a square that is actually empty (row 3 is empty)
    piece = board.get_piece(ConstantSquare(row=ROW_3, col=COL_A))
    assert piece is None


# =============================================================================
# Integration tests
# =============================================================================


def test_full_coordinate_conversion() -> None:
    """Test full coordinate conversion round trip."""
    # White setup
    board = Board()
    board.turn = Color.WHITE

    # Clear a1 which has a rook, clear e1 which has a king
    board.clear_square(ConstantSquare(row=ROW_1, col=COL_A))
    board.clear_square(ConstantSquare(row=ROW_1, col=COL_E))

    # Set up white pieces
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )

    # Verify
    pawn = board.get_piece(ConstantSquare(row=ROW_1, col=COL_A))
    king = board.get_piece(ConstantSquare(row=ROW_1, col=COL_E))
    assert pawn == create_piece(
        Color.WHITE, PieceType.PAWN, ConstantSquare(row=ROW_1, col=COL_A)
    )
    assert king == create_piece(
        Color.WHITE, PieceType.KING, ConstantSquare(row=ROW_1, col=COL_E)
    )
