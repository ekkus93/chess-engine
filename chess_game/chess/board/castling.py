"""Castling validation logic."""

from __future__ import annotations

from typing import TYPE_CHECKING

from chess_game.chess.color import Color
from chess_game.chess.constants import (
    ROW_1,
    ROW_8,
    COL_E,
    COL_F,
    COL_G,
    COL_C,
    COL_A,
    COL_D,
    COL_H,
    ConstantSquare,
    get_row_constant,
    get_col_constant,
)
from chess_game.chess.types import Piece
from chess_game.chess.types import PieceType

if TYPE_CHECKING:
    from chess_game.chess.board.board import Board


class CastlingValidator:
    """Validates castling moves."""

    @staticmethod
    def is_castling_move(start_pos: ConstantSquare, end_pos: ConstantSquare) -> bool:
        if start_pos.col == 4 and end_pos.col == 6:
            return start_pos.row == 0 or start_pos.row == 7

        if start_pos.col == 4 and end_pos.col == 2:
            return start_pos.row == 0 or start_pos.row == 7

        return False

    @staticmethod
    def can_castle(
        board: Board,
        start_pos: ConstantSquare,
        end_pos: ConstantSquare,
        color: Color,
        _piece_color: Color,
    ) -> bool:
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
        home_row = ROW_1 if color == Color.WHITE else ROW_8
        king_square = ConstantSquare(row=get_row_constant(int(home_row)), col=COL_E)
        rook_square = ConstantSquare(row=get_row_constant(int(home_row)), col=COL_A)
        destination = ConstantSquare(row=get_row_constant(int(home_row)), col=COL_C)

        return CastlingValidator._can_complete_castle(
            board, king_square, rook_square, destination, color, color
        )

    @staticmethod
    def _can_complete_castle(
        board: Board,
        king_square: ConstantSquare,
        rook_square: ConstantSquare,
        destination: ConstantSquare,
        color: Color,
        _piece_color: Color,
    ) -> bool:
        # Check castling rights
        if int(destination.col) > int(king_square.col):
            right = board.white_kingside if color == Color.WHITE else board.black_kingside
        else:
            right = board.white_queenside if color == Color.WHITE else board.black_queenside
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
            if CastlingValidator._is_square_attacked(board, square, enemy_color):
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

    @staticmethod
    def _castling_path_is_clear(
        king_square: ConstantSquare,
        destination: ConstantSquare,
        board: Board,
        _piece_color: Color,
    ) -> bool:
        if king_square.col == COL_E and destination.col == COL_G:
            piece = board.get_piece(ConstantSquare(row=king_square.row, col=COL_F))
            if piece is not None:
                return False
            return True
        elif king_square.col == COL_E and destination.col == COL_C:
            piece_d = board.get_piece(ConstantSquare(row=king_square.row, col=COL_D))
            piece_c = board.get_piece(ConstantSquare(row=king_square.row, col=COL_C))
            if piece_d is not None:
                return False
            if piece_c is not None:
                return False
            return True
        return True

    @staticmethod
    def _is_square_attacked(
        board: Board, square: ConstantSquare, by_color: Color
    ) -> bool:
        for row in range(8):
            for col in range(8):
                piece_square = ConstantSquare(
                    row=get_row_constant(row), col=get_col_constant(col)
                )
                piece = board.get_piece(piece_square)
                if piece is None or piece.color != by_color:
                    continue

                if CastlingValidator._piece_attacks_square(
                    piece, piece_square, square, board
                ):
                    return True
        return False

    @staticmethod
    def _piece_attacks_square(
        piece: Piece,
        from_square: ConstantSquare,
        to_square: ConstantSquare,
        board: Board,
    ) -> bool:
        row_diff = to_square.row - from_square.row
        col_diff = to_square.col - from_square.col

        if piece.kind == PieceType.PAWN:
            # White moves toward row 0 (direction -1), Black toward row 7 (direction +1)
            direction = -1 if piece.color == Color.WHITE else 1
            return row_diff == direction and abs(col_diff) == 1

        if piece.kind == PieceType.KNIGHT:
            return (abs(row_diff), abs(col_diff)) in {(2, 1), (1, 2)}

        if piece.kind == PieceType.BISHOP:
            if abs(row_diff) != abs(col_diff):
                return False
            return CastlingValidator._path_is_clear(from_square, to_square, board)

        if piece.kind == PieceType.ROOK:
            if from_square.row != to_square.row and from_square.col != to_square.col:
                return False
            return CastlingValidator._path_is_clear(from_square, to_square, board)

        if piece.kind == PieceType.QUEEN:
            if from_square.row != to_square.row and from_square.col != to_square.col:
                if abs(row_diff) != abs(col_diff):
                    return False
            return CastlingValidator._path_is_clear(from_square, to_square, board)

        if piece.kind == PieceType.KING:
            return from_square != to_square and max(abs(row_diff), abs(col_diff)) == 1

        return False

    @staticmethod
    def _path_is_clear(
        from_square: ConstantSquare, to_square: ConstantSquare, board: Board
    ) -> bool:
        if from_square == to_square:
            return True

        row_diff = to_square.row - from_square.row
        col_diff = to_square.col - from_square.col

        step_row = 0 if row_diff == 0 else (1 if row_diff > 0 else -1)
        step_col = 0 if col_diff == 0 else (1 if col_diff > 0 else -1)

        current_row = int(from_square.row) + step_row
        current_col = int(from_square.col) + step_col

        while (current_row, current_col) != (int(to_square.row), int(to_square.col)):
            if (
                board.get_piece(
                    ConstantSquare(
                        row=get_row_constant(current_row),
                        col=get_col_constant(current_col),
                    )
                )
                is not None
            ):
                return False
            current_row += step_row
            current_col += step_col

        return True
