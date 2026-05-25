"""Module-level game-state predicates extracted from Board.

Provides `is_in_check`, `is_checkmate`, and `is_stalemate` so that Board
doesn't have to carry them as instance methods.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from chess_game.chess.board.castling import CastlingValidator
from chess_game.chess.position_utils import position_key
from chess_game.chess.types import Color, Piece, PieceType

if TYPE_CHECKING:
    from chess_game.chess.board.board import Board


def is_in_check(board: "Board", color: Color) -> bool:  # noqa: F821
    """Check if the given color's king is currently in check."""
    king_sq = board.find_king(color)
    if king_sq is None:
        return False
    enemy = Color.BLACK if color == Color.WHITE else Color.WHITE
    return CastlingValidator.is_square_attacked(board, king_sq, enemy)


def is_checkmate(board: "Board", color: Optional[Color] = None) -> bool:  # noqa: F821
    """Check if the given color (or side-to-move) is in checkmate."""
    c = color if color is not None else board.turn
    if not is_in_check(board, c):
        return False
    return len(board.get_legal_moves_for_color(c)) == 0


def is_stalemate(board: "Board", color: Optional[Color] = None) -> bool:  # noqa: F821
    """Check if the given color (or side-to-move) is in stalemate."""
    c = color if color is not None else board.turn
    if is_in_check(board, c):
        return False
    return len(board.get_legal_moves_for_color(c)) == 0


def is_threefold_repetition(board: "Board", position_counts: dict[str, int]) -> bool:
    """Check whether the current position has occurred at least three times."""

    return position_counts.get(position_key(board), 0) >= 3


def is_fivefold_repetition(board: "Board", position_counts: dict[str, int]) -> bool:
    """Check whether the current position has occurred at least five times."""

    return position_counts.get(position_key(board), 0) >= 5


def is_fifty_move_rule(board: "Board") -> bool:
    """Check whether fifty full moves have elapsed without a pawn move or capture."""

    return board.halfmove_clock >= 100


def is_seventy_five_move_rule(board: "Board") -> bool:
    """Check whether seventy-five full moves have elapsed without a pawn move or capture."""

    return board.halfmove_clock >= 150


def is_insufficient_material(board: "Board") -> bool:
    """Check whether neither side has enough material to ever force checkmate."""

    pieces = [piece for row in board.board for piece in row if piece is not None]
    non_kings = [piece for piece in pieces if piece.kind != PieceType.KING]
    if not non_kings:
        return True
    if any(
        piece.kind in {PieceType.PAWN, PieceType.ROOK, PieceType.QUEEN}
        for piece in non_kings
    ):
        return False
    if len(non_kings) == 1:
        return True
    if len(non_kings) == 2:
        return _two_minor_pieces_are_insufficient(non_kings)
    return _same_color_bishops_only(non_kings)


def terminal_message(
    board: "Board",
    position_counts: Optional[dict[str, int]] = None,
) -> Optional[str]:
    """Return an end-of-game message when the current board is terminal."""

    message = _mate_or_stalemate_message(board)
    if message is not None:
        return message
    return _draw_message(board, position_counts)


def record_position(board: "Board", position_counts: dict[str, int]) -> None:
    """Record the current position for repetition tracking."""

    key = position_key(board)
    position_counts[key] = position_counts.get(key, 0) + 1


def _mate_or_stalemate_message(board: "Board") -> Optional[str]:
    """Return a terminal non-draw message when the side to move is mated."""

    if is_checkmate(board):
        winner = "Black" if board.turn == Color.WHITE else "White"
        return f"Checkmate! {winner} wins."
    if is_stalemate(board):
        return "Stalemate! The game is a draw."
    return None


def _draw_message(
    board: "Board",
    position_counts: Optional[dict[str, int]],
) -> Optional[str]:
    """Return the first matching draw-state message, if any."""

    if position_counts is not None and is_fivefold_repetition(board, position_counts):
        return "Draw by fivefold repetition."
    if is_seventy_five_move_rule(board):
        return "Draw by seventy-five-move rule."
    if position_counts is not None and is_threefold_repetition(board, position_counts):
        return "Draw by threefold repetition."
    if is_fifty_move_rule(board):
        return "Draw by fifty-move rule."
    if is_insufficient_material(board):
        return "Draw by insufficient material."
    return None


def _two_minor_pieces_are_insufficient(pieces: list[Piece]) -> bool:
    """Handle standard two-minor-piece dead positions."""

    kinds = {piece.kind for piece in pieces}
    if kinds == {PieceType.BISHOP}:
        return True
    if kinds == {PieceType.KNIGHT}:
        return pieces[0].color != pieces[1].color
    return pieces[0].color != pieces[1].color


def _same_color_bishops_only(pieces: list[Piece]) -> bool:
    """Detect bishop-only positions where every bishop lives on the same color complex."""

    if any(piece.kind != PieceType.BISHOP for piece in pieces):
        return False
    square_colors = {_square_color(piece) for piece in pieces}
    return len(square_colors) == 1


def _square_color(piece: Piece) -> int:
    """Return 0 for dark squares and 1 for light squares."""

    square = piece.square
    assert square is not None
    return (int(square.row) + int(square.col)) % 2
