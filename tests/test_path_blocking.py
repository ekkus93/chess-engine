from __future__ import annotations

from chess_game.chess.board import Board, ConstantSquare, create_piece
from chess_game.constants import (
    ROW_1,
    ROW_2,
    ROW_3,
    ROW_4,
    ROW_5,
    ROW_6,
    ROW_7,
    ROW_8,
    COL_A,
    COL_B,
    COL_C,
    COL_D,
    COL_E,
    COL_F,
    COL_G,
    COL_H,
)
from chess_game.chess.types import Color, PieceType


def clear_board(board: Board) -> None:
    for row in [ROW_1, ROW_2, ROW_3, ROW_4, ROW_5, ROW_6, ROW_7, ROW_8]:
        for col in [COL_A, COL_B, COL_C, COL_D, COL_E, COL_F, COL_G, COL_H]:
            board.clear_square(ConstantSquare(row=row, col=col))


def _setup_kings(board: Board) -> None:
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )


# =============================================================================
# Category 11: Path Blocking Edge Cases
# =============================================================================


def test_rook_blocked_by_adjacent_piece() -> None:
    """T11.1: Rook blocked by piece on immediate square."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_B), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.WHITE
    # Rook can capture pawn at (7, 1)
    legal_moves = board.get_legal_moves()
    assert any(
        move[0].row == ROW_1
        and move[0].col == COL_A
        and move[1].row == ROW_1
        and move[1].col == COL_B
        for move in legal_moves
    )
    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_A), ConstantSquare(row=ROW_1, col=COL_B)
        )
        is True
    )


def test_rook_blocked_by_piece_in_path() -> None:
    """T11.1: Rook blocked by piece anywhere in path."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e2
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_B), create_piece(Color.BLACK, PieceType.PAWN)
    )  # b1 - blocks rook from moving to b1
    board.turn = Color.WHITE
    # Rook cannot move past pawn on b1 to reach e1
    legal_moves = board.get_legal_moves()
    # Rook can move to b1 but not to e1 (blocked by pawn on b1)
    assert not any(
        move[0].row == ROW_1
        and move[0].col == COL_A
        and move[1].row == ROW_1
        and move[1].col == COL_E
        for move in legal_moves
    )  # Blocked


def test_bishop_blocked_by_friendly_piece() -> None:
    """T11.2: Bishop blocked by friendly piece on diagonal."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    # Clear the starting position pieces on rank 1
    board.clear_square(ConstantSquare(row=ROW_1, col=COL_B))  # b1
    board.clear_square(ConstantSquare(row=ROW_1, col=COL_C))  # c1
    board.clear_square(ConstantSquare(row=ROW_1, col=COL_F))  # f1
    board.clear_square(ConstantSquare(row=ROW_1, col=COL_G))  # g1
    board.clear_square(ConstantSquare(row=ROW_2, col=COL_B))  # b2 (empty)
    board.clear_square(
        ConstantSquare(row=ROW_3, col=COL_C)
    )  # c3 (where friendly pawn blocks path)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A),
        create_piece(Color.WHITE, PieceType.BISHOP),
    )
    # Place a friendly pawn on c3 to block the bishop's path
    board.set_piece(
        ConstantSquare(row=ROW_3, col=COL_C), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.turn = Color.WHITE
    # Bishop on a1 can move to b2 (6,1) but not past it to c3
    legal_moves = board.get_legal_moves()
    assert any(
        move[0].row == ROW_1
        and move[0].col == COL_A
        and move[1].row == ROW_2
        and move[1].col == COL_B
        for move in legal_moves
    )
    assert not any(
        move[0].row == ROW_1
        and move[0].col == COL_A
        and move[1].row == ROW_3
        and move[1].col == COL_C
        for move in legal_moves
    )  # Blocked by pawn


def test_bishop_blocked_by_enemy_piece() -> None:
    """T11.2: Bishop blocked by enemy piece on diagonal."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A),
        create_piece(Color.WHITE, PieceType.BISHOP),
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_B), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.WHITE
    # Bishop can capture pawn on b2 but not move past to c3
    legal_moves = board.get_legal_moves()
    assert any(move[1].row == ROW_2 and move[1].col == COL_B for move in legal_moves)
    assert not any(
        move[1].row == ROW_3 and move[1].col == COL_C for move in legal_moves
    )


def test_queen_blocked_in_one_direction() -> None:
    """T11.3: Queen blocked in one direction but not others."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.QUEEN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_B), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_6, col=COL_E), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.turn = Color.WHITE
    # Queen can move vertically past pawn at (5,4), but not horizontally past pawn at (7,2)
    legal_moves = board.get_legal_moves()
    assert any(
        move[1].row == ROW_2 and move[1].col == COL_E for move in legal_moves
    )  # Can move up
    assert any(
        move[1].row == ROW_4 and move[1].col == COL_E for move in legal_moves
    )  # Can capture pawn


def test_queen_blocked_in_multiple_directions() -> None:
    """T11.3: Queen blocked in multiple directions."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.QUEEN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_B), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_F), create_piece(Color.WHITE, PieceType.PAWN)
    )
    board.turn = Color.WHITE
    # Queen blocked horizontally on both sides
    legal_moves = board.get_legal_moves()
    assert (ROW_1, COL_B) not in legal_moves  # Blocked by pawn


def test_bishop_diagonal_blocked_at_distance() -> None:
    """T11.2: Bishop blocked by friendly piece at distance on diagonal."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_A),
        create_piece(Color.WHITE, PieceType.BISHOP),
    )
    board.set_piece(
        ConstantSquare(row=ROW_3, col=COL_C), create_piece(Color.WHITE, PieceType.PAWN)
    )  # Pawn at c3 blocks
    board.turn = Color.WHITE
    # Bishop can move to b2 (6,1) but blocked by pawn at c3 (5,2)
    legal_moves = board.get_legal_moves()
    assert any(move[1].row == ROW_2 and move[1].col == COL_B for move in legal_moves)
    assert not any(
        move[1].row == ROW_3 and move[1].col == COL_C for move in legal_moves
    )
