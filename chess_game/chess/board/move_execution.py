"""Move execution logic for the chess engine."""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

from chess_game.chess.color import Color
from chess_game.chess.types import Piece, PieceType, ConstantSquare
from chess_game.chess.board.castling import CastlingValidator
from chess_game.chess.board.promotion import PromotionValidator
from chess_game.chess.constants import get_row_constant, get_col_constant

if TYPE_CHECKING:
    from chess_game.chess.board.board import Board


class MoveExecutor:
    """Executes moves on the board."""

    def __init__(self, board: Board):
        self.board = board
        self.castling_validator = CastlingValidator()
        self.promotion_validator = PromotionValidator(board)

    def execute_move(
        self,
        from_square: ConstantSquare,
        to_square: ConstantSquare,
        promotion_piece: Optional[PieceType] = None,
        start_piece: Optional[Piece] = None,
    ) -> bool:
        piece = self.board.get_piece(from_square)
        if piece is None:
            raise ValueError(f"No piece at {from_square}")

        if piece.kind == PieceType.PAWN:
            promotion_required = self.promotion_validator.is_promotion_required(
                piece, from_square, to_square
            )
            if promotion_required or promotion_piece is not None:
                self._handle_promotion(piece, from_square, to_square, promotion_piece)
            else:
                self._execute_regular_move(piece, from_square, to_square)
        else:
            if self._is_castling_move(piece, from_square, to_square):
                self._execute_castling(piece, from_square, to_square)
            else:
                self._execute_regular_move(piece, from_square, to_square)

        return True

    def _handle_promotion(
        self,
        piece: Piece,
        from_square: ConstantSquare,
        to_square: ConstantSquare,
        promotion_piece: Optional[PieceType],
    ) -> None:
        if promotion_piece is None:
            promotion_piece = self.promotion_validator.get_default_promotion_piece(
                piece.color
            )

        self._move_piece(piece, from_square, to_square)

        new_piece = Piece(piece.color, promotion_piece, to_square)
        self.board.set_piece(to_square, new_piece)
        self.board.clear_square(from_square)

    def _is_castling_move(
        self, piece: Piece, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        return self.castling_validator.is_castling_move(from_square, to_square)

    def _execute_castling(
        self, piece: Piece, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> None:
        if from_square.col == 4 and to_square.col == 6:
            from_row = int(from_square.row)
            rook = self.board.get_piece(
                ConstantSquare(row=get_row_constant(from_row), col=get_col_constant(7))
            )
            if rook is not None:
                self.board.set_piece(
                    ConstantSquare(
                        row=get_row_constant(from_row), col=get_col_constant(5)
                    ),
                    rook,
                )
                self.board.clear_square(
                    ConstantSquare(
                        row=get_row_constant(from_row), col=get_col_constant(7)
                    )
                )
        elif from_square.col == 4 and to_square.col == 2:
            from_row = int(from_square.row)
            rook = self.board.get_piece(
                ConstantSquare(row=get_row_constant(from_row), col=get_col_constant(0))
            )
            if rook is not None:
                self.board.set_piece(
                    ConstantSquare(
                        row=get_row_constant(from_row), col=get_col_constant(3)
                    ),
                    rook,
                )
                self.board.clear_square(
                    ConstantSquare(
                        row=get_row_constant(from_row), col=get_col_constant(0)
                    )
                )

        self._move_piece(piece, from_square, to_square)

    def _execute_regular_move(
        self, piece: Piece, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> None:
        self._move_piece(piece, from_square, to_square)

        if self._is_en_passant_capture(piece, from_square, to_square):
            self._execute_en_passant_capture(from_square, to_square)

        self.board.clear_square(from_square)

    def _is_en_passant_capture(
        self, piece: Piece, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        return (
            self.board.en_passant_target is not None
            and to_square == self.board.en_passant_target
        )

    def _execute_en_passant_capture(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> None:
        capture_row = int(from_square.row)
        capture_col = int(to_square.col)
        captured_square = ConstantSquare(
            row=get_row_constant(capture_row), col=get_col_constant(capture_col)
        )
        self.board.clear_square(captured_square)

    def _move_piece(
        self, piece: Piece, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> None:
        self.board.set_piece(to_square, piece)
        piece._square = to_square

    def update_turn(self) -> None:
        self.board.turn = Color.BLACK if self.board.turn == Color.WHITE else Color.WHITE
