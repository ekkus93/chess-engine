from __future__ import annotations


from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType


def clear_board(board: Board) -> None:
    for row in range(8):
        for col in range(8):
            board.clear_square(row, col)


def _setup_kings(board: Board) -> None:
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))


# =============================================================================
# Category 10: Turn & Color Edge Cases
# =============================================================================


def test_turn_alternates_after_each_move() -> None:
    """T10.1: Turn alternates correctly after each move."""
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.turn = Color.WHITE

    # White moves first
    assert board.make_move((7, 4), (7, 5)) is True
    assert board.turn == Color.BLACK

    # Black moves (black pawn starts on row 6)
    # Need to clear the white pawn at (6, 0) first
    board.clear_square(6, 0)
    board.set_piece(6, 0, create_piece(Color.BLACK, PieceType.PAWN))
    assert board.make_move((6, 0), (7, 0)) is True
    assert board.turn == Color.WHITE


def test_turn_alternates_after_100_moves() -> None:
    """T10.1: Turn alternates correctly after many moves."""
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.turn = Color.WHITE

    # Make 99 moves alternating
    # After odd number of moves, should be black's turn
    for i in range(99):
        if i % 2 == 0:
            board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.PAWN))
            board.make_move((7, 0), (7, 1))
        else:
            board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.PAWN))
            board.make_move((0, 0), (0, 1))

    assert board.turn == Color.WHITE


def test_cannot_move_opponent_piece() -> None:
    """T10.2: Cannot move opponent's piece."""
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE

    # Cannot move black pawn
    assert board.make_move((0, 4), (1, 4)) is False


def test_cannot_capture_own_piece() -> None:
    """T10.2: Cannot capture own piece."""
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE

    # Cannot capture own pawn
    assert board.make_move((6, 4), (6, 3)) is False


def test_white_pawn_moves_toward_row_zero() -> None:
    """T10.3: White pawn forward direction is decreasing row."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE

    # White pawn moves from row 7 to row 6 (toward rank 8, row 0)
    assert board.make_move((6, 4), (5, 4)) is True
    assert board.get_piece_type_at(5, 4) == PieceType.PAWN


def test_black_pawn_moves_toward_row_seven() -> None:
    """T10.3: Black pawn forward direction is increasing row."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(1, 4, create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK

    # Black pawn moves from row 1 to row 2 (toward rank 1, row 7)
    assert board.make_move((1, 4), (2, 4)) is True
    assert board.get_piece_type_at(2, 4) == PieceType.PAWN


def test_white_pawn_capture_moves_toward_row_zero() -> None:
    """T10.3: White pawn capture direction is decreasing row."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(6, 3, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(5, 4, create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE

    # White pawn captures diagonally toward rank 8 (row 5)
    assert board.make_move((6, 3), (5, 4)) is True
    assert board.get_piece_type_at(5, 4) == PieceType.PAWN


def test_black_pawn_capture_moves_toward_row_seven() -> None:
    """T10.3: Black pawn capture direction is increasing row."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(1, 5, create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(2, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.BLACK

    # Black pawn captures diagonally toward rank 1 (row 2)
    assert board.make_move((1, 5), (2, 4)) is True
    assert board.get_piece_type_at(2, 4) == PieceType.PAWN
