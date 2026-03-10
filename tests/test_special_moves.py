from __future__ import annotations

from chess_game.chess.board import Board, create_piece
from chess_game.chess.move import parse_move_notation
from chess_game.chess.types import Color, PieceType


def clear_board(board: Board) -> None:
    for row in range(8):
        for col in range(8):
            board.clear_square(row, col)


def _setup_kings(board: Board) -> None:
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.KING))


def test_white_kingside_castle_legal_case() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))

    assert board.make_move((7, 4), (7, 6)) is True
    assert board.get_piece_type_at(7, 6) == PieceType.KING
    assert board.get_piece_type_at(7, 5) == PieceType.ROOK


def test_white_queenside_castle_legal_case() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.ROOK))

    assert board.make_move((7, 4), (7, 2)) is True
    assert board.get_piece_type_at(7, 2) == PieceType.KING
    assert board.get_piece_type_at(7, 3) == PieceType.ROOK


def test_black_kingside_castle_legal_case() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.ROOK))
    board.turn = Color.BLACK

    assert board.make_move((0, 4), (0, 6)) is True
    assert board.get_piece_type_at(0, 6) == PieceType.KING
    assert board.get_piece_type_at(0, 5) == PieceType.ROOK


def test_black_queenside_castle_legal_case() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.ROOK))
    board.turn = Color.BLACK

    assert board.make_move((0, 4), (0, 2)) is True
    assert board.get_piece_type_at(0, 2) == PieceType.KING
    assert board.get_piece_type_at(0, 3) == PieceType.ROOK


def test_cannot_castle_while_in_check() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(3, 4, create_piece(Color.BLACK, PieceType.ROOK))

    assert board.make_move((7, 4), (7, 6)) is False


def test_cannot_castle_through_check() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(3, 5, create_piece(Color.BLACK, PieceType.ROOK))

    assert board.make_move((7, 4), (7, 6)) is False


def test_cannot_castle_into_check() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(3, 6, create_piece(Color.BLACK, PieceType.ROOK))

    assert board.make_move((7, 4), (7, 6)) is False


def test_cannot_castle_after_king_moved() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))

    assert board.make_move((7, 4), (6, 4)) is True
    board.turn = Color.WHITE
    assert board.make_move((6, 4), (7, 4)) is True
    board.turn = Color.WHITE

    assert board.make_move((7, 4), (7, 6)) is False


def test_cannot_castle_after_rook_moved() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))

    assert board.make_move((7, 7), (7, 6)) is True
    board.turn = Color.WHITE
    assert board.make_move((7, 6), (7, 7)) is True
    board.turn = Color.WHITE

    assert board.make_move((7, 4), (7, 6)) is False


def test_cannot_castle_if_path_blocked() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(7, 7, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(7, 5, create_piece(Color.WHITE, PieceType.KNIGHT))

    assert board.make_move((7, 4), (7, 6)) is False


def test_white_en_passant_legal_example() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(3, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(1, 3, create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK

    assert board.make_move((1, 3), (3, 3)) is True
    assert board.en_passant_target == (2, 3)

    assert board.make_move((3, 4), (2, 3)) is True
    assert board.get_piece(3, 3) is None
    assert board.get_piece_type_at(2, 3) == PieceType.PAWN
    assert board.get_color_at(2, 3) == Color.WHITE


def test_black_en_passant_legal_example() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(4, 4, create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(6, 3, create_piece(Color.WHITE, PieceType.PAWN))

    assert board.make_move((6, 3), (4, 3)) is True
    assert board.en_passant_target == (5, 3)

    assert board.make_move((4, 4), (5, 3)) is True
    assert board.get_piece(4, 3) is None
    assert board.get_piece_type_at(5, 3) == PieceType.PAWN
    assert board.get_color_at(5, 3) == Color.BLACK


def test_en_passant_expires_after_one_turn() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(3, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(1, 3, create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.ROOK))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.ROOK))
    board.turn = Color.BLACK

    assert board.make_move((1, 3), (3, 3)) is True
    assert board.en_passant_target == (2, 3)

    assert board.make_move((7, 0), (7, 1)) is True
    assert board.en_passant_target is None

    assert board.make_move((0, 7), (0, 6)) is True

    assert board.make_move((3, 4), (2, 3)) is False


def test_en_passant_unavailable_if_last_move_not_two_step_pawn_move() -> None:
    board = Board()
    clear_board(board)
    _setup_kings(board)
    board.set_piece(3, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(3, 3, create_piece(Color.BLACK, PieceType.PAWN))

    assert board.en_passant_target is None
    assert board.is_valid_pawn_move((3, 4), (2, 3)) is False


def test_en_passant_cannot_be_used_if_it_leaves_own_king_in_check() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(7, 4, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 4, create_piece(Color.BLACK, PieceType.ROOK))
    board.set_piece(3, 4, create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(1, 3, create_piece(Color.BLACK, PieceType.PAWN))
    board.set_piece(0, 0, create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.BLACK

    assert board.make_move((1, 3), (3, 3)) is True
    assert board.make_move((3, 4), (2, 3)) is False


def test_white_promotion_to_queen() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(1, 4, create_piece(Color.WHITE, PieceType.PAWN))

    assert board.make_move((1, 4), (0, 4), promotion=PieceType.QUEEN) is True
    assert board.get_piece_type_at(0, 4) == PieceType.QUEEN
    assert board.get_color_at(0, 4) == Color.WHITE


def test_white_promotion_to_knight() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(1, 4, create_piece(Color.WHITE, PieceType.PAWN))

    assert board.make_move((1, 4), (0, 4), promotion=PieceType.KNIGHT) is True
    assert board.get_piece_type_at(0, 4) == PieceType.KNIGHT


def test_black_promotion_to_queen() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(6, 4, create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK

    assert board.make_move((6, 4), (7, 4), promotion=PieceType.QUEEN) is True
    assert board.get_piece_type_at(7, 4) == PieceType.QUEEN
    assert board.get_color_at(7, 4) == Color.BLACK


def test_invalid_promotion_piece_rejected() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(1, 4, create_piece(Color.WHITE, PieceType.PAWN))

    assert board.make_move((1, 4), (0, 4), promotion=PieceType.KING) is False


def test_default_promotion_is_queen_when_unspecified() -> None:
    board = Board()
    clear_board(board)
    board.set_piece(7, 0, create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(0, 7, create_piece(Color.BLACK, PieceType.KING))
    board.set_piece(1, 4, create_piece(Color.WHITE, PieceType.PAWN))

    assert board.make_move((1, 4), (0, 4)) is True
    assert board.get_piece_type_at(0, 4) == PieceType.QUEEN


def test_parse_move_notation_supports_promotion_choice() -> None:
    move = parse_move_notation("e7e8q")
    assert move.start == (1, 4)
    assert move.end == (0, 4)
    assert move.promotion == PieceType.QUEEN
