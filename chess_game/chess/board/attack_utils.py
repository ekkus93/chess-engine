"""Shared attack-checking utilities for piece-attack and path-clear logic."""

from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from chess_game.chess.types import Piece, PieceType

from chess_game.chess.constants import (
    Color,
    ConstantSquare,
)

if TYPE_CHECKING:
    from chess_game.chess.board.board import Board


def _is_pawn_attack_wrapper(
    attacker: Piece,
    attacker_square: ConstantSquare,
    target_square: ConstantSquare,
    _board: Board,
) -> bool:
    return _is_pawn_attack(attacker, attacker_square, target_square)


def _is_rook_attack_wrapper(
    _attacker: Piece,
    attacker_square: ConstantSquare,
    target_square: ConstantSquare,
    board: Board,
) -> bool:
    return _is_rook_attack(attacker_square, target_square, board)


def _is_bishop_attack_wrapper(
    _attacker: Piece,
    attacker_square: ConstantSquare,
    target_square: ConstantSquare,
    board: Board,
) -> bool:
    return _is_bishop_attack(attacker_square, target_square, board)


def _is_queen_attack_wrapper(
    _attacker: Piece,
    attacker_square: ConstantSquare,
    target_square: ConstantSquare,
    board: Board,
) -> bool:
    return _is_queen_attack(attacker_square, target_square, board)


def _is_knight_attack_wrapper(
    _attacker: Piece,
    attacker_square: ConstantSquare,
    target_square: ConstantSquare,
    _board: Board,
) -> bool:
    return _is_knight_attack(attacker_square, target_square)


def _is_king_attack_wrapper(
    _attacker: Piece,
    attacker_square: ConstantSquare,
    target_square: ConstantSquare,
    _board: Board,
) -> bool:
    return _is_king_attack(attacker_square, target_square)


def piece_attacks_square(
    attacker: Piece,
    attacker_square: ConstantSquare,
    target_square: ConstantSquare,
    board: Board,
) -> bool:
    """Check if the attacker piece can attack the target square.

    Delegates to the appropriate geometry check based on piece kind,
    including path-clear verification for sliding pieces.
    """
    checker = _ATTACK_CHECKERS.get(attacker.kind)
    if checker is None:
        return False
    return checker(attacker, attacker_square, target_square, board)


_ATTACK_CHECKERS: dict[
    PieceType, Callable[[Piece, ConstantSquare, ConstantSquare, Board], bool]
] = {
    PieceType.PAWN: _is_pawn_attack_wrapper,
    PieceType.ROOK: _is_rook_attack_wrapper,
    PieceType.BISHOP: _is_bishop_attack_wrapper,
    PieceType.QUEEN: _is_queen_attack_wrapper,
    PieceType.KNIGHT: _is_knight_attack_wrapper,
    PieceType.KING: _is_king_attack_wrapper,
}


def _is_pawn_attack(
    pawn: Piece,
    from_sq: ConstantSquare,
    to_sq: ConstantSquare,
) -> bool:
    """Check if pawn can attack from from_sq to to_sq."""
    direction = -1 if pawn.color == Color.WHITE else 1
    row_diff = int(to_sq.row) - int(from_sq.row)
    col_diff = int(to_sq.col) - int(from_sq.col)
    return row_diff == direction and abs(col_diff) == 1


def _is_rook_attack(
    from_sq: ConstantSquare,
    to_sq: ConstantSquare,
    board: Board,
) -> bool:
    """Check if rook can attack from from_sq to to_sq."""
    if int(from_sq.row) != int(to_sq.row) and int(from_sq.col) != int(to_sq.col):
        return False
    return _path_is_clear(board, from_sq, to_sq)


def _is_bishop_attack(
    from_sq: ConstantSquare,
    to_sq: ConstantSquare,
    board: Board,
) -> bool:
    """Check if bishop can attack from from_sq to to_sq."""
    row_diff = abs(int(from_sq.row) - int(to_sq.row))
    col_diff = abs(int(from_sq.col) - int(to_sq.col))
    if row_diff != col_diff:
        return False
    return _path_is_clear(board, from_sq, to_sq)


def _is_queen_attack(
    from_sq: ConstantSquare,
    to_sq: ConstantSquare,
    board: Board,
) -> bool:
    """Check if queen can attack from from_sq to to_sq."""
    if int(from_sq.row) == int(to_sq.row) or int(from_sq.col) == int(to_sq.col):
        return _path_is_clear(board, from_sq, to_sq)
    return _is_bishop_attack(from_sq, to_sq, board)


def _is_knight_attack(
    from_sq: ConstantSquare,
    to_sq: ConstantSquare,
) -> bool:
    """Check if knight can attack from from_sq to to_sq."""
    row_diff = abs(int(from_sq.row) - int(to_sq.row))
    col_diff = abs(int(from_sq.col) - int(to_sq.col))
    return (row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)


def _is_king_attack(
    from_sq: ConstantSquare,
    to_sq: ConstantSquare,
) -> bool:
    """Check if king can attack from from_sq to to_sq."""
    return (
        abs(int(from_sq.row) - int(to_sq.row)) <= 1
        and abs(int(from_sq.col) - int(to_sq.col)) <= 1
    )


def _path_is_clear(
    board: Board,
    from_sq: ConstantSquare,
    to_sq: ConstantSquare,
) -> bool:
    """Check if the path between two squares is clear of pieces."""
    from_row = int(from_sq.row)
    from_col = int(from_sq.col)
    to_row = int(to_sq.row)
    to_col = int(to_sq.col)

    row_diff = to_row - from_row
    col_diff = to_col - from_col

    if row_diff == 0:
        step_row = 0
        step_col = 1 if col_diff > 0 else -1
        steps = abs(col_diff)
    elif col_diff == 0:
        step_row = 1 if row_diff > 0 else -1
        step_col = 0
        steps = abs(row_diff)
    else:
        step_row = 1 if row_diff > 0 else -1
        step_col = 1 if col_diff > 0 else -1
        steps = max(abs(row_diff), abs(col_diff))

    current_row = from_row
    current_col = from_col

    for _ in range(1, steps):
        current_row += step_row
        current_col += step_col
        if board.board[current_row][current_col] is not None:
            return False

    return True
