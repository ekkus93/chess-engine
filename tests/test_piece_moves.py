from __future__ import annotations

from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType


def clear_board(board: Board) -> None:
    for row in range(8):
        for col in range(8):
            board.clear_square(row, col)


def test_rook_valid_horizontal_move() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.ROOK))

    assert board.is_valid_rook_move((4, 4), (4, 0)) is True


def test_rook_valid_vertical_move() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.ROOK))

    assert board.is_valid_rook_move((4, 4), (0, 4)) is True


def test_rook_blocked_by_friendly_piece_in_path() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(4, 2, create_piece(Color.WHITE, PieceType.PAWN))

    assert board.is_valid_rook_move((4, 4), (4, 0)) is False


def test_rook_blocked_by_enemy_piece_before_destination() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(4, 2, create_piece(Color.BLACK, PieceType.PAWN))

    assert board.is_valid_rook_move((4, 4), (4, 0)) is False


def test_rook_cannot_move_diagonally() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.ROOK))

    assert board.is_valid_rook_move((4, 4), (2, 2)) is False


def test_rook_cannot_capture_friendly_piece() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(4, 0, create_piece(Color.WHITE, PieceType.BISHOP))

    assert board.is_valid_rook_move((4, 4), (4, 0)) is False


def test_bishop_valid_diagonal_move() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.BISHOP))

    assert board.is_valid_bishop_move((4, 4), (1, 1)) is True


def test_bishop_blocked_diagonal() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.BISHOP))
    board.set_piece(3, 3, create_piece(Color.BLACK, PieceType.PAWN))

    assert board.is_valid_bishop_move((4, 4), (1, 1)) is False


def test_bishop_cannot_move_straight() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.BISHOP))

    assert board.is_valid_bishop_move((4, 4), (4, 1)) is False


def test_bishop_cannot_capture_friendly_piece() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.BISHOP))
    board.set_piece(1, 1, create_piece(Color.WHITE, PieceType.KNIGHT))

    assert board.is_valid_bishop_move((4, 4), (1, 1)) is False


def test_queen_straight_move() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.QUEEN))

    assert board.is_valid_queen_move((4, 4), (4, 0)) is True


def test_queen_diagonal_move() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.QUEEN))

    assert board.is_valid_queen_move((4, 4), (1, 1)) is True


def test_queen_blocked_path() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(3, 3, create_piece(Color.BLACK, PieceType.PAWN))

    assert board.is_valid_queen_move((4, 4), (1, 1)) is False


def test_queen_illegal_knight_like_move() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.QUEEN))

    assert board.is_valid_queen_move((4, 4), (2, 3)) is False


def test_knight_valid_l_move_both_orientations() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.KNIGHT))

    assert board.is_valid_knight_move((4, 4), (2, 3)) is True
    assert board.is_valid_knight_move((4, 4), (3, 2)) is True


def test_knight_can_jump_over_pieces() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(3, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(4, 3, create_piece(Color.WHITE, PieceType.PAWN))

    assert board.is_valid_knight_move((4, 4), (2, 3)) is True


def test_knight_illegal_straight_move() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.KNIGHT))

    assert board.is_valid_knight_move((4, 4), (4, 2)) is False


def test_knight_illegal_diagonal_move() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.KNIGHT))

    assert board.is_valid_knight_move((4, 4), (2, 2)) is False


def test_knight_cannot_capture_friendly_piece() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(2, 3, create_piece(Color.WHITE, PieceType.PAWN))

    assert board.is_valid_knight_move((4, 4), (2, 3)) is False


def test_king_one_step_orthogonal() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.KING))

    assert board.is_valid_king_move((4, 4), (4, 5)) is True


def test_king_one_step_diagonal() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.KING))

    assert board.is_valid_king_move((4, 4), (5, 5)) is True


def test_king_cannot_move_two_squares() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(4, 4, create_piece(Color.WHITE, PieceType.KING))

    assert board.is_valid_king_move((4, 4), (4, 6)) is False


def test_white_pawn_one_step_from_e2_to_e3() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))

    assert board.is_valid_pawn_move((6, 4), (5, 4)) is True


def test_white_pawn_two_step_from_e2_to_e4() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))

    assert board.is_valid_pawn_move((6, 4), (4, 4)) is True


def test_white_pawn_blocked_on_one_step() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(5, 4, create_piece(Color.BLACK, PieceType.KNIGHT))

    assert board.is_valid_pawn_move((6, 4), (5, 4)) is False


def test_white_pawn_blocked_on_two_step_intermediate_square() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(5, 4, create_piece(Color.BLACK, PieceType.KNIGHT))

    assert board.is_valid_pawn_move((6, 4), (4, 4)) is False


def test_white_pawn_capture_diagonally() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(5, 5, create_piece(Color.BLACK, PieceType.BISHOP))

    assert board.is_valid_pawn_move((6, 4), (5, 5)) is True


def test_white_pawn_cannot_capture_forward() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(5, 4, create_piece(Color.BLACK, PieceType.BISHOP))

    assert board.is_valid_pawn_move((6, 4), (5, 4)) is False


def test_white_pawn_cannot_move_backward() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))

    assert board.is_valid_pawn_move((6, 4), (7, 4)) is False


def test_black_pawn_one_step_from_e7_to_e6() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(1, 4, create_piece(Color.BLACK, PieceType.PAWN))

    assert board.is_valid_pawn_move((1, 4), (2, 4)) is True


def test_black_pawn_two_step_from_e7_to_e5() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(1, 4, create_piece(Color.BLACK, PieceType.PAWN))

    assert board.is_valid_pawn_move((1, 4), (3, 4)) is True


def test_black_pawn_diagonal_capture() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(1, 4, create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(2, 3, create_piece(Color.WHITE, PieceType.KNIGHT))

    assert board.is_valid_pawn_move((1, 4), (2, 3)) is True


def test_black_pawn_cannot_move_backward() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(1, 4, create_piece(Color.BLACK, PieceType.PAWN))

    assert board.is_valid_pawn_move((1, 4), (0, 4)) is False
