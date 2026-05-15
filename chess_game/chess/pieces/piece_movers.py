"""Piece-specific move validation logic."""

from __future__ import annotations

from typing import List, Optional

from chess_game.chess.constants import Color
from chess_game.chess.constants import (
    get_row_constant,
    get_col_constant,
)
from chess_game.chess.types import Piece, PieceType
from chess_game.chess.constants import ConstantSquare


def _pawn_direction(color: Color) -> int:
    """Return the forward direction for a pawn: -1 for WHITE, +1 for BLACK."""
    return -1 if color == Color.WHITE else 1


def _get_en_passant_moves(
    board,
    next_row,
    current_col,
    moves,
) -> None:
    """Append en-passant capture moves if applicable."""
    if hasattr(board, "en_passant_target") and board.en_passant_target is not None:
        ep_target = board.en_passant_target
        ep_row = int(ep_target.row)
        ep_col = int(ep_target.col)
        if ep_row == int(next_row) and abs(ep_col - int(current_col)) == 1:
            ep_square = ConstantSquare(
                row=next_row, col=get_col_constant(ep_col)
            )
            if PieceMovers.is_valid_position(ep_square):
                moves.append(ep_target)


def _get_pawn_captures(
    piece: Piece,
    board,
    next_row,
    current_col,
    moves,
) -> None:
    """Append regular diagonal capture moves for a pawn."""
    for col_offset in [-1, 1]:
        target_col_idx = int(current_col) + col_offset
        if target_col_idx < 0 or target_col_idx >= 8:
            continue

        target_col = get_col_constant(target_col_idx)
        cap_square = ConstantSquare(row=next_row, col=target_col)

        if PieceMovers.is_valid_position(cap_square):
            target_piece = board.get_piece(cap_square)
            if target_piece is not None and target_piece.color != piece.color:
                moves.append(cap_square)


class PieceMovers:
    """Contains move validation logic for each piece type."""

    _MOVEMENT_GETTERS = {
        PieceType.PAWN: "_get_pawn_moves",
        PieceType.KNIGHT: "_get_knight_moves",
        PieceType.BISHOP: "_get_bishop_moves",
        PieceType.ROOK: "_get_rook_moves",
        PieceType.QUEEN: "_get_queen_moves",
        PieceType.KING: "_get_king_moves",
    }

    @staticmethod
    def get_valid_moves(piece: Piece, board) -> List[ConstantSquare]:
        """Get all valid moves for a piece."""
        if piece.square is None:
            return []
        getter_name = PieceMovers._MOVEMENT_GETTERS.get(piece.kind)
        if getter_name is None:
            return []
        getter = getattr(PieceMovers, getter_name)
        return getter(piece, board)

    @staticmethod
    def is_valid_position(square: ConstantSquare) -> bool:
        """Check if a square is on the board."""
        return 0 <= int(square.row) < 8 and 0 <= int(square.col) < 8

    @staticmethod
    def _get_pawn_moves(piece: Piece, board) -> List[ConstantSquare]:
        """Get all valid pawn moves (forward, capture, 2-step, promotion)."""
        assert piece.square is not None
        moves = []
        direction = _pawn_direction(piece.color)
        current_row = int(piece.square.row)
        current_col = get_col_constant(int(piece.square.col))

        # Forward 1 square
        next_row = get_row_constant(current_row + direction)
        target_square = ConstantSquare(row=next_row, col=current_col)
        if PieceMovers.is_valid_position(target_square):
            if board.is_empty(target_square):
                moves.append(target_square)

        # Forward 2 squares (only on first move)
        is_first_move = (
            current_row == 6 if piece.color == Color.WHITE else current_row == 1
        )

        if is_first_move:
            target_row_2 = get_row_constant(current_row + 2 * direction)
            target_square_2 = ConstantSquare(row=target_row_2, col=current_col)
            if PieceMovers.is_valid_position(target_square_2):
                square_between = ConstantSquare(row=next_row, col=current_col)
                if board.is_empty(square_between) and board.is_empty(target_square_2):
                    moves.append(target_square_2)

        # Captures (regular diagonal capture)
        _get_pawn_captures(piece, board, next_row, current_col, moves)

        # En passant capture
        _get_en_passant_moves(board, next_row, current_col, moves)

        return moves

    @staticmethod
    def _get_knight_moves(piece: Piece, board) -> List[ConstantSquare]:
        """Get all valid knight moves (L-shaped)."""
        assert piece.square is not None
        moves = []
        valid_moves = [
            (-2, -1),
            (-2, 1),
            (-1, -2),
            (-1, 2),
            (1, -2),
            (1, 2),
            (2, -1),
            (2, 1),
        ]

        for row_offset, col_offset in valid_moves:
            target_row = int(piece.square.row) + row_offset
            target_col = int(piece.square.col) + col_offset

            if not (0 <= target_row < 8 and 0 <= target_col < 8):
                continue

            target_square = ConstantSquare(
                row=get_row_constant(target_row),
                col=get_col_constant(target_col),
            )

            if board.is_empty(target_square) or (
                board.get_piece(target_square) is not None
                and board.get_piece(target_square).color != piece.color
            ):
                moves.append(target_square)

        return moves

    @staticmethod
    def _get_bishop_moves(piece: Piece, board) -> List[ConstantSquare]:
        """Get all valid bishop moves (diagonal)."""
        assert piece.square is not None
        moves = []
        diagonals = [
            (1, 1),
            (1, -1),
            (-1, 1),
            (-1, -1),
        ]

        for row_offset, col_offset in diagonals:
            target_row = int(piece.square.row) + row_offset
            target_col = int(piece.square.col) + col_offset

            while 0 <= target_row < 8 and 0 <= target_col < 8:
                target_row_const = get_row_constant(target_row)
                target_col_const = get_col_constant(target_col)
                target_square = ConstantSquare(
                    row=target_row_const, col=target_col_const
                )
                target_piece = board.get_piece(target_square)

                if target_piece is None:
                    moves.append(target_square)
                elif target_piece.color != piece.color:
                    moves.append(target_square)
                    break
                else:
                    break

                target_row += row_offset
                target_col += col_offset

        return moves

    @staticmethod
    def _get_rook_moves(piece: Piece, board) -> List[ConstantSquare]:
        """Get all valid rook moves (straight lines)."""
        assert piece.square is not None
        moves = []
        directions = [
            (1, 0),
            (-1, 0),
            (0, 1),
            (0, -1),
        ]

        for row_offset, col_offset in directions:
            target_row = int(piece.square.row) + row_offset
            target_col = int(piece.square.col) + col_offset

            while 0 <= target_row < 8 and 0 <= target_col < 8:
                target_row_const = get_row_constant(target_row)
                target_col_const = get_col_constant(target_col)
                target_square = ConstantSquare(
                    row=target_row_const, col=target_col_const
                )
                target_piece = board.get_piece(target_square)

                if target_piece is None:
                    moves.append(target_square)
                elif target_piece.color != piece.color:
                    moves.append(target_square)
                    break
                else:
                    break

                target_row += row_offset
                target_col += col_offset

        return moves

    @staticmethod
    def _get_piece_row(piece: Piece) -> Optional[int]:
        """Get piece row, handling None square."""
        if piece.square is None:
            return None
        return int(piece.square.row)

    @staticmethod
    def _get_piece_col(piece: Piece) -> Optional[int]:
        """Get piece column, handling None square."""
        if piece.square is None:
            return None
        return int(piece.square.col)

    @staticmethod
    def _get_queen_moves(piece: Piece, board) -> List[ConstantSquare]:
        """Get all valid queen moves (rook + bishop combined)."""
        rook_moves = PieceMovers._get_rook_moves(piece, board)
        bishop_moves = PieceMovers._get_bishop_moves(piece, board)
        return rook_moves + bishop_moves

    @staticmethod
    def _get_king_moves(piece: Piece, board) -> List[ConstantSquare]:
        """Get all valid king moves (one square in any direction plus castling)."""
        assert piece.square is not None
        moves = []
        row_offsets = [-1, 0, 1]
        col_offsets = [-1, 0, 1]

        for row_offset, col_offset in [
            (ro, co) for ro in row_offsets for co in col_offsets
        ]:
            if row_offset == 0 and col_offset == 0:
                continue

            target_row = int(piece.square.row) + row_offset
            target_col = int(piece.square.col) + col_offset

            if not (0 <= target_row < 8 and 0 <= target_col < 8):
                continue

            target_square = ConstantSquare(
                row=get_row_constant(target_row),
                col=get_col_constant(target_col),
            )

            if board.is_empty(target_square) or (
                board.get_piece(target_square) is not None
                and board.get_piece(target_square).color != piece.color
            ):
                moves.append(target_square)

        return moves
