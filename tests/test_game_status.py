from __future__ import annotations

from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType


def clear_board(board: Board) -> None:
    for row in range(8):
        for col in range(8):
            board.clear_square(row, col)


def test_start_position_has_expected_white_legal_moves() -> None:
    board = Board()

    legal_moves = board.get_legal_moves(Color.WHITE)

    assert len(legal_moves) == 20
    assert ((6, 4), (4, 4), None) in legal_moves
    assert ((7, 6), (5, 5), None) in legal_moves


def test_fools_mate_is_checkmate_for_white() -> None:
    board = Board()

    assert board.make_move((6, 5), (5, 5)) is True  # f2f3
    assert board.make_move((1, 4), (3, 4)) is True  # e7e5
    assert board.make_move((6, 6), (4, 6)) is True  # g2g4
    assert board.make_move((0, 3), (4, 7)) is True  # Qd8h4#

    assert board.turn == Color.WHITE
    assert board.is_in_check(Color.WHITE) is True
    assert board.is_checkmate(Color.WHITE) is True


def test_in_check_with_one_escape_is_not_checkmate() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(6, 6, create_piece(Color.BLACK, PieceType.QUEEN))
    board.turn = Color.WHITE

    assert board.is_in_check(Color.WHITE) is True
    assert board.is_checkmate(Color.WHITE) is False


def test_classic_stalemate_position() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(6, 5, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(5, 6, create_piece(Color.BLACK, PieceType.QUEEN))
    board.turn = Color.WHITE

    assert board.is_in_check(Color.WHITE) is False
    assert board.is_stalemate(Color.WHITE) is True


def test_not_stalemate_when_one_legal_move_exists() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(6, 5, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(4, 6, create_piece(Color.BLACK, PieceType.QUEEN))
    board.turn = Color.WHITE

    assert board.is_in_check(Color.WHITE) is False
    assert board.is_stalemate(Color.WHITE) is False
    assert len(board.get_legal_moves(Color.WHITE)) == 1
