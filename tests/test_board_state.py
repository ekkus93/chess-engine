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
# Category 9: Board State Edge Cases
# =============================================================================


def test_board_handles_missing_white_king_gracefully() -> None:
    """T9.1: Engine handles board state with missing king gracefully."""
    board = Board()
    clear_board(board)
    # Only set black king, no white king
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(1, 4, create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK

    # Should not crash, just return no legal moves
    legal_moves = board.get_legal_moves()
    assert isinstance(legal_moves, list)


def test_board_handles_extra_king_gracefully() -> None:
    """T9.1: Engine handles board state with extra king gracefully."""
    board = Board()
    clear_board(board)
    # Set both kings plus an extra white king
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KING))
    board.turn = Color.WHITE

    # Should not crash
    legal_moves = board.get_legal_moves()
    assert isinstance(legal_moves, list)


def test_board_handles_missing_opponent_king() -> None:
    """T9.1: Engine handles board state with missing opponent king."""
    board = Board()
    clear_board(board)
    # Only white king present
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.turn = Color.WHITE

    # Should not crash
    legal_moves = board.get_legal_moves()
    assert isinstance(legal_moves, list)


def test_board_handles_all_pieces_captured() -> None:
    """T9.2: Engine handles board state with minimal pieces."""
    board = Board()
    clear_board(board)
    # Only kings remain
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.WHITE

    # Should work normally
    legal_moves = board.get_legal_moves()
    assert isinstance(legal_moves, list)


def test_board_handles_full_starting_position() -> None:
    """T9.3: Engine handles full board starting position."""
    board = Board()

    # Starting position is already set up by Board.__init__()
    board.turn = Color.WHITE

    # All pieces should be movable
    white_king_moves = board.get_legal_moves()
    assert len(white_king_moves) > 0
