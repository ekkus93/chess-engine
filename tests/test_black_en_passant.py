"""Tests for black en passant."""

from chess_game.chess.board import Board, create_piece
from chess_game.chess.color import Color
from chess_game.chess.types import PieceType
from tests.helpers import sq


def test_black_en_passant_legal_example() -> None:
    """Black moves e7-e5, White captures en passant d5xe6."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("d5"), create_piece(Color.WHITE, PieceType.PAWN))
    board.set_piece(sq("e7"), create_piece(Color.BLACK, PieceType.PAWN))
    board.turn = Color.BLACK

    # Black moves pawn two squares (e7 to e5)
    assert board.make_move(sq("e7"), sq("e5")) is True
    # En passant target is e6
    assert board.en_passant_target == sq("e6")

    # White captures en passant from d5 to e6
    board.turn = Color.WHITE
    assert board.make_move(sq("d5"), sq("e6")) is True
    assert board.get_piece(sq("d5")) is None
    assert board.get_piece_type_at(sq("e6")) == PieceType.PAWN
    assert board.get_color_at(sq("e6")) == Color.WHITE
