from __future__ import annotations
from chess_game.chess.constants import (
    get_row_constant,
    get_col_constant,
    get_square_constant,
    COL_A,
    COL_B,
    COL_C,
    COL_D,
    COL_E,
    COL_F,
    COL_G,
    COL_H,
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
from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType


# =============================================================================
# Category 1: Castling Edge Cases
# =============================================================================
def test_castling_rook_captured_forbids_kingside() -> None:
    """T1.1: Castling forbidden when rook was captured on original square."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 7), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        get_square_constant(7, 7), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.turn = Color.BLACK
    # Black captures h1 rook
    board.make_move(
        get_square_constant(7, 7), get_square_constant(0, 7)
    )  # Black rook captures h1
    # White cannot castle kingside (rook no longer on h1)
    assert (
        board.make_move(get_square_constant(0, 4), get_square_constant(0, 6)) is False
    )


def test_castling_rook_moved_clears_castling_right() -> None:
    """T1.1: Verify rook removal clears castling right."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 7), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.turn = Color.WHITE
    # White moves rook from h1
    board.make_move(
        get_square_constant(0, 7), get_square_constant(0, 6)
    )  # Rook moves to g1
    # White cannot castle kingside (original rook moved)
    assert (
        board.make_move(get_square_constant(0, 4), get_square_constant(0, 6)) is False
    )


def test_castling_replaced_rook_does_not_restore_right() -> None:
    """T1.4: Replacement rook doesn't restore castling right."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 7), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.turn = Color.WHITE
    # White moves rook from h1, black replaces it
    board.make_move(
        get_square_constant(0, 7), get_square_constant(0, 6)
    )  # Rook moves to g1
    board.make_move(
        get_square_constant(7, 7), get_square_constant(0, 7)
    )  # Black rook captures on h1
    # White cannot castle kingside (original rook moved, replacement doesn't help)
    assert (
        board.make_move(get_square_constant(0, 4), get_square_constant(0, 6)) is False
    )


def test_castling_opponent_piece_in_path_blocks() -> None:
    """T1.2: Castling blocked by opponent piece in path."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 7), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        get_square_constant(7, 7), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.set_piece(
        get_square_constant(0, 6), create_piece(Color.BLACK, PieceType.PAWN)
    )  # Black pawn on g1
    board.turn = Color.WHITE
    # Cannot castle kingside (path blocked by black pawn on g1)
    assert (
        board.make_move(get_square_constant(0, 4), get_square_constant(0, 6)) is False
    )


def test_castling_enemy_piece_on_destination_blocked() -> None:
    """T1.2: Castling blocked if enemy piece on destination square."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 7), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        get_square_constant(7, 7), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.set_piece(
        get_square_constant(0, 6), create_piece(Color.BLACK, PieceType.PAWN)
    )  # Black pawn on f1
    board.turn = Color.WHITE
    # Cannot castle kingside (destination square occupied by enemy)
    assert (
        board.make_move(get_square_constant(0, 4), get_square_constant(0, 6)) is False
    )


def test_castling_queenside_rook_moved_forbids() -> None:
    """T1.3: Queenside castling forbidden if kingside rook moved."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 0), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        get_square_constant(0, 7), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.turn = Color.WHITE
    # White moves kingside rook
    board.make_move(
        get_square_constant(0, 7), get_square_constant(0, 6)
    )  # Rook moves to g1
    # White cannot castle queenside (kingside rook moved, clearing rights)
    assert (
        board.make_move(get_square_constant(0, 4), get_square_constant(0, 2)) is False
    )


def test_castling_kingside_rook_moved_forbids() -> None:
    """T1.3: Kingside castling forbidden if queenside rook moved."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 0), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        get_square_constant(0, 7), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.turn = Color.WHITE
    # White moves queenside rook
    board.make_move(
        get_square_constant(0, 0), get_square_constant(0, 1)
    )  # Rook moves to b1
    # White cannot castle kingside (queenside rook moved, clearing rights)
    assert (
        board.make_move(get_square_constant(0, 4), get_square_constant(0, 6)) is False
    )


def test_castling_kingside_rook_replaced_forbids() -> None:
    """T1.4: Kingside castling forbidden when original rook replaced."""
    board = Board()
    clear_board(board)
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        get_square_constant(0, 7), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.turn = Color.WHITE
    # White moves rook from h1
    board.make_move(
        get_square_constant(0, 7), get_square_constant(0, 6)
    )  # Rook moves to g1
    # Black replaces rook on h1
    board.make_move(
        get_square_constant(7, 7), get_square_constant(0, 7)
    )  # Black rook captures on h1
    # White cannot castle kingside (original rook moved)
    assert (
        board.make_move(get_square_constant(0, 4), get_square_constant(0, 6)) is False
    )
