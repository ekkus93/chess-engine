"""Castling validation logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

from chess_game.chess.constants import Color
from chess_game.chess.constants import (
    ROW_1,
    ROW_8,
    COL_E,
    COL_F,
    COL_G,
    COL_C,
    COL_B,
    COL_A,
    COL_D,
    COL_H,
    ConstantSquare,
    get_row_constant,
    get_col_constant,
)
from chess_game.chess.types import PieceType, CastlingRights
from chess_game.chess.board.attack_utils import piece_attacks_square

if TYPE_CHECKING:
    from chess_game.chess.board.board import Board


def _clear_castling_for_color(rights: CastlingRights, color: Color) -> None:
    """Clear both castling rights for a given color."""
    if color == Color.WHITE:
        rights.white_kingside = False
        rights.white_queenside = False
    else:
        rights.black_kingside = False
        rights.black_queenside = False


def _clear_rook_castling_right(
    rights: CastlingRights, start_pos: ConstantSquare, color: Color
) -> None:
    """Clear side-specific castling right when a rook leaves its home square."""
    row = int(start_pos.row)
    col = int(start_pos.col)
    if color == Color.WHITE and row == 7:
        if col == 7:
            rights.white_kingside = False
        elif col == 0:
            rights.white_queenside = False
    elif color != Color.WHITE and row == 0:
        if col == 7:
            rights.black_kingside = False
        elif col == 0:
            rights.black_queenside = False


def _clear_captured_rook_castling_right(
    rights: CastlingRights, end_pos: ConstantSquare
) -> None:
    """Clear castling right if a rook is captured on its home square."""
    row = int(end_pos.row)
    col = int(end_pos.col)
    if row == 0 and col == 7:
        rights.black_kingside = False
    elif row == 0 and col == 0:
        rights.black_queenside = False
    elif row == 7 and col == 7:
        rights.white_kingside = False
    elif row == 7 and col == 0:
        rights.white_queenside = False


class CastlingValidator:
    """Validates castling moves."""

    @staticmethod
    def is_castling_move(start_pos: ConstantSquare, end_pos: ConstantSquare) -> bool:
        """Return True if the move matches a kingside or queenside castling pattern."""
        if start_pos.col == COL_E and end_pos.col == COL_G:
            return start_pos.row in (ROW_1, ROW_8)

        if start_pos.col == COL_E and end_pos.col == COL_C:
            return start_pos.row in (ROW_1, ROW_8)

        return False

    @staticmethod
    def can_castle(
        board: Board,
        start_pos: ConstantSquare,
        end_pos: ConstantSquare,
        color: Color,
        _piece_color: Color,
    ) -> bool:
        """Return True if the king can castle from start_pos to end_pos."""
        if not CastlingValidator.is_castling_move(start_pos, end_pos):
            return False

        if end_pos.col > start_pos.col:
            rook_square = ConstantSquare(row=start_pos.row, col=COL_H)
        else:
            rook_square = ConstantSquare(row=start_pos.row, col=COL_A)

        return CastlingValidator._can_complete_castle(
            board, start_pos, rook_square, end_pos, color, _piece_color
        )

    @staticmethod
    def can_castle_kingside(
        board: Board,
        color: Color,
    ) -> bool:
        """Return True if the given color can castle kingside."""
        home_row = ROW_1 if color == Color.WHITE else ROW_8
        king_square = ConstantSquare(row=get_row_constant(int(home_row)), col=COL_E)
        rook_square = ConstantSquare(row=get_row_constant(int(home_row)), col=COL_H)
        destination = ConstantSquare(row=get_row_constant(int(home_row)), col=COL_G)

        return CastlingValidator._can_complete_castle(
            board, king_square, rook_square, destination, color, color
        )

    @staticmethod
    def can_castle_queenside(
        board: Board,
        color: Color,
    ) -> bool:
        """Return True if the given color can castle queenside."""
        home_row = ROW_1 if color == Color.WHITE else ROW_8
        king_square = ConstantSquare(row=get_row_constant(int(home_row)), col=COL_E)
        rook_square = ConstantSquare(row=get_row_constant(int(home_row)), col=COL_A)
        destination = ConstantSquare(row=get_row_constant(int(home_row)), col=COL_C)

        return CastlingValidator._can_complete_castle(
            board, king_square, rook_square, destination, color, color
        )

   # pylint: disable=too-many-return-statements
    @staticmethod
    def _can_complete_castle(
        board: Board,
        king_square: ConstantSquare,
        rook_square: ConstantSquare,
        destination: ConstantSquare,
        color: Color,
        _piece_color: Color,
    ) -> bool:
        """Return True if all castling preconditions are met."""
        # Check castling rights
        if int(destination.col) > int(king_square.col):
            right = (
                board.castling_rights.white_kingside
                if color == Color.WHITE
                else board.castling_rights.black_kingside
            )
        else:
            right = (
                board.castling_rights.white_queenside
                if color == Color.WHITE
                else board.castling_rights.black_queenside
            )
        if not right:
            return False

        # Verify king is on its starting square
        expected_king_sq = ConstantSquare(
            row=get_row_constant(int(king_square.row)), col=COL_E
        )
        king_piece = board.get_piece(expected_king_sq)
        if (
            king_piece is None
            or king_piece.kind != PieceType.KING
            or king_piece.color != color
        ):
            return False

        # Destination square must be empty
        if board.get_piece(destination) is not None:
            return False

        if not CastlingValidator._rook_at_original_square(board, color, rook_square):
            return False

        if not CastlingValidator._castling_path_is_clear(
            king_square, destination, board, _piece_color
        ):
            return False

        if not CastlingValidator._king_square_safe_during_castle(
            board, king_square, destination, color
        ):
            return False

        return True

    @staticmethod
    def _king_square_safe_during_castle(
        board: Board,
        king_square: ConstantSquare,
        destination: ConstantSquare,
        color: Color,
    ) -> bool:
        enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE

        # Determine intermediate square based on castling direction
        if int(destination.col) > int(king_square.col):
            # Kingside: king passes through f-file
            intermediate = ConstantSquare(row=king_square.row, col=COL_F)
        else:
            # Queenside: king passes through d-file
            intermediate = ConstantSquare(row=king_square.row, col=COL_D)

        king_path = [
            king_square,
            intermediate,
            destination,
        ]

        for square in king_path:
            if CastlingValidator.is_square_attacked(board, square, enemy_color):
                return False

        return True

    @staticmethod
    def _rook_at_original_square(
        board: Board, color: Color, rook_square: ConstantSquare
    ) -> bool:
        piece = board.get_piece(rook_square)
        return (
            piece is not None and piece.kind == PieceType.ROOK and piece.color == color
        )

   # pylint: disable=too-many-return-statements
    @staticmethod
    def _castling_path_is_clear(
        king_square: ConstantSquare,
        destination: ConstantSquare,
        board: Board,
        _piece_color: Color,
    ) -> bool:
        """Return True if all squares between king and destination are empty."""
        if king_square.col == COL_E and destination.col == COL_G:
            piece = board.get_piece(ConstantSquare(row=king_square.row, col=COL_F))
            if piece is not None:
                return False
            return True
        if king_square.col == COL_E and destination.col == COL_C:
            piece_b = board.get_piece(ConstantSquare(row=king_square.row, col=COL_B))
            piece_d = board.get_piece(ConstantSquare(row=king_square.row, col=COL_D))
            piece_c = board.get_piece(ConstantSquare(row=king_square.row, col=COL_C))
            if piece_b is not None:
                return False
            if piece_d is not None:
                return False
            if piece_c is not None:
                return False
            return True
        return True

    @staticmethod
    def is_square_attacked(
        board: Board, square: ConstantSquare, by_color: Color
    ) -> bool:
        """Check if a square is attacked by pieces of the given color."""
        for row in range(8):
            for col in range(8):
                piece_square = ConstantSquare(
                    row=get_row_constant(row), col=get_col_constant(col)
                )
                piece = board.get_piece(piece_square)
                if piece is None or piece.color != by_color:
                    continue

                if piece_attacks_square(piece, piece_square, square, board):
                    return True
        return False
