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
# Category 11: Path Blocking Edge Cases
# =============================================================================


def test_rook_blocked_by_adjacent_piece() -> None:
    """T11.1: Rook blocked by piece on immediate square."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(7, 1, create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE

    # Rook can capture pawn at (7, 1)
    legal_moves = board.get_legal_moves()
    assert any(move[0] == (7, 0) and move[1] == (7, 1) for move in legal_moves)
    assert board.make_move((7, 0), (7, 1)) is True


def test_rook_blocked_by_piece_in_path() -> None:
    """T11.1: Rook blocked by piece anywhere in path."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE

    # Rook cannot move past pawn on e1
    legal_moves = board.get_legal_moves()
    assert (7, 4) not in legal_moves  # Blocked


def test_bishop_blocked_by_friendly_piece() -> None:
    """T11.2: Bishop blocked by friendly piece on diagonal."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    # Clear the starting position pieces on rank 1
    board.clear_square(7, 1)  # b1
    board.clear_square(7, 2)  # c1
    board.clear_square(7, 5)  # f1
    board.clear_square(7, 6)  # g1
    board.clear_square(6, 1)  # b2 (empty)
    board.clear_square(5, 2)  # c3 (where friendly pawn blocks path)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.BISHOP))
    # Place a friendly pawn on c3 to block the bishop's path
    board.set_piece(5, 2, create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE

    # Bishop on a1 can move to b2 (6,1) but not past it to c3
    legal_moves = board.get_legal_moves()
    assert any(move[0] == (7, 0) and move[1] == (6, 1) for move in legal_moves)
    assert not any(
        move[0] == (7, 0) and move[1] == (5, 2) for move in legal_moves
    )  # Blocked by pawn


def test_bishop_blocked_by_enemy_piece() -> None:
    """T11.2: Bishop blocked by enemy piece on diagonal."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.BISHOP))
    board.set_piece(6, 1, create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE

    # Bishop can capture but not move past
    legal_moves = board.get_legal_moves()
    assert any(move[1] == (6, 1) for move in legal_moves)
    assert not any(move[1] == (5, 2) for move in legal_moves)


def test_queen_blocked_in_one_direction() -> None:
    """T11.3: Queen blocked in one direction but not others."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(7, 2, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(5, 4, create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.WHITE

    # Queen can move vertically past pawn at (5,4), but not horizontally past pawn at (7,2)
    legal_moves = board.get_legal_moves()
    assert any(move[1] == (6, 4) for move in legal_moves)  # Can move up
    assert any(move[1] == (5, 4) for move in legal_moves)  # Can capture pawn


def test_queen_blocked_in_multiple_directions() -> None:
    """T11.3: Queen blocked in multiple directions."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(7, 2, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(7, 6, create_piece(Color.WHITE, PieceType.PAWN))
    board.turn = Color.WHITE

    # Queen blocked horizontally on both sides
    legal_moves = board.get_legal_moves()
    assert (7, 2) not in legal_moves  # Blocked by pawn


def test_bishop_diagonal_blocked_at_distance() -> None:
    """T11.2: Bishop blocked by friendly piece at distance on diagonal."""
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.BISHOP))
    board.set_piece(5, 2, create_piece(Color.WHITE, PieceType.PAWN))  # Pawn at c3 blocks
    board.turn = Color.WHITE

    # Bishop can move to b2 (6,1) but blocked by pawn at c3 (5,2)
    legal_moves = board.get_legal_moves()
    assert any(move[1] == (6, 1) for move in legal_moves)
    assert not any(move[1] == (5, 2) for move in legal_moves)
