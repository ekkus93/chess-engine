from chess_game.chess.board import Board, create_piece
from chess_game.chess.types import Color, PieceType


def clear_board(board: Board) -> None:
    for row in range(8):
        for col in range(8):
            board.clear_square(row, col)


def test_starting_position_key_squares() -> None:
    board = Board()

    assert board.get_piece_type_at(7, 0) == PieceType.ROOK
    assert board.get_color_at(7, 0) == Color.WHITE

    assert board.get_piece_type_at(7, 4) == PieceType.KING
    assert board.get_color_at(7, 4) == Color.WHITE

    assert board.get_piece_type_at(0, 4) == PieceType.KING
    assert board.get_color_at(0, 4) == Color.BLACK

    assert board.get_piece_type_at(6, 4) == PieceType.PAWN
    assert board.get_color_at(6, 4) == Color.WHITE

    assert board.get_piece_type_at(1, 4) == PieceType.PAWN
    assert board.get_color_at(1, 4) == Color.BLACK


def test_rook_move_with_clear_path() -> None:
    board = Board()
    clear_board(board)

    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.ROOK))

    assert board.make_move((7, 0), (3, 0)) is True
    assert board.get_piece_type_at(3, 0) == PieceType.ROOK
    assert board.get_color_at(3, 0) == Color.WHITE
    assert board.get_piece(7, 0) is None


def test_knight_move_l_shape() -> None:
    board = Board()
    clear_board(board)

    board.set_piece(7, 1, create_piece(Color.WHITE, PieceType.KNIGHT))

    assert board.make_move((7, 1), (5, 2)) is True
    assert board.get_piece_type_at(5, 2) == PieceType.KNIGHT


def test_bishop_move_diagonal_clear_path() -> None:
    board = Board()
    clear_board(board)

    board.set_piece(6, 2, create_piece(Color.WHITE, PieceType.BISHOP))

    assert board.make_move((6, 2), (3, 5)) is True
    assert board.get_piece_type_at(3, 5) == PieceType.BISHOP


def test_queen_move_straight() -> None:
    board = Board()
    clear_board(board)

    board.set_piece(6, 3, create_piece(Color.WHITE, PieceType.QUEEN))

    assert board.make_move((6, 3), (3, 3)) is True
    assert board.get_piece_type_at(3, 3) == PieceType.QUEEN


def test_king_move_one_square() -> None:
    board = Board()
    clear_board(board)

    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))

    assert board.make_move((7, 4), (6, 5)) is True
    assert board.get_piece_type_at(6, 5) == PieceType.KING


def test_white_pawn_moves_forward_and_two_step_from_start() -> None:
    board = Board()
    clear_board(board)

    board.set_piece(6, 4, create_piece(Color.WHITE, PieceType.PAWN))

    assert board.make_move((6, 4), (4, 4)) is True
    assert board.get_piece_type_at(4, 4) == PieceType.PAWN


def test_black_pawn_moves_forward_after_turn_change() -> None:
    board = Board()
    clear_board(board)

    board.set_piece(6, 0, create_piece(Color.WHITE, PieceType.KNIGHT))
    board.set_piece(1, 4, create_piece(Color.BLACK, PieceType.PAWN))

    assert board.make_move((6, 0), (4, 1)) is True
    assert board.turn == Color.BLACK

    assert board.make_move((1, 4), (3, 4)) is True
    assert board.get_piece_type_at(3, 4) == PieceType.PAWN
    assert board.get_color_at(3, 4) == Color.BLACK


def test_reject_moving_opponent_piece() -> None:
    board = Board()

    assert board.turn == Color.WHITE
    assert board.make_move((1, 0), (2, 0)) is False


def test_reject_friendly_capture() -> None:
    board = Board()
    clear_board(board)

    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(5, 0, create_piece(Color.WHITE, PieceType.KNIGHT))

    assert board.make_move((7, 0), (5, 0)) is False
