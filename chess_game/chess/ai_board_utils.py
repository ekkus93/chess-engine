"""Shared board and move utilities used by AI search helpers."""

from chess_game.chess.board import Board
from chess_game.chess.move import Move
from chess_game.chess.types import Color


def get_legal_moves(board: Board) -> list[Move]:
    """Get all legal moves for the side to move."""

    return [
        Move(start=start, end=end, promotion=promotion)
        for start, end, promotion in board.get_legal_moves()
    ]


def clone_with_move(board: Board, move: Move) -> Board:
    """Create a cloned board state after applying a legal move."""

    simulated = board.clone()
    if not simulated.apply_legal_move(
        move.start,
        move.end,
        promotion=move.promotion,
    ):
        raise RuntimeError("Simulated move failed legality check")
    return simulated


def move_colors(board: Board, move: Move) -> tuple[Color, Color] | None:
    """Return moving and enemy colors for a move, if the mover exists."""

    moving_piece = board.get_piece(move.start)
    if moving_piece is None:
        return None
    moving_color = moving_piece.color
    enemy_color = Color.BLACK if moving_color == Color.WHITE else Color.WHITE
    return moving_color, enemy_color
