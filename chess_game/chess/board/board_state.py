"""Board state data structure."""

from __future__ import annotations

import copy
from typing import List, Optional, Union

from chess_game.chess.constants import Color
from chess_game.chess.types import Piece
from chess_game.chess.types import PieceType
from chess_game.chess.constants import (
    ConstantSquare,
    RowConstant,
    ColConstant,
    get_row_constant,
    get_col_constant,
)


class BoardState:
    """Immutables board state data structure.

    This is a pure data class with no behavior. It holds the board configuration
    and provides accessors for reading data.
    """

    __slots__ = (
        "board",
        "turn",
        "en_passant_target",
        "white_kingside",
        "white_queenside",
        "black_kingside",
        "black_queenside",
    )

    def __init__(
        self,
        board: List[List[Optional[Piece]]],
        turn: Color,
        en_passant_target: Optional[ConstantSquare],
        white_kingside: bool = True,
        white_queenside: bool = True,
        black_kingside: bool = True,
        black_queenside: bool = True,
    ) -> None:
        self.board = board
        self.turn = turn
        self.en_passant_target = en_passant_target
        self.white_kingside = white_kingside
        self.white_queenside = white_queenside
        self.black_kingside = black_kingside
        self.black_queenside = black_queenside

    def get_piece(self, square: ConstantSquare) -> Optional[Piece]:
        """Get piece at square."""
        if not (0 <= int(square.row) < 8 and 0 <= int(square.col) < 8):
            return None
        return self.board[int(square.row)][int(square.col)]

    def set_piece(self, square: ConstantSquare, piece: Optional[Piece]) -> None:
        """Set piece at square."""
        if not (0 <= int(square.row) < 8 and 0 <= int(square.col) < 8):
            raise ValueError(f"Invalid square: {square}")
        if piece is not None:
            # Set the piece's square to the new position
            piece._square = square
        self.board[int(square.row)][int(square.col)] = piece

    def clear_square(self, square: ConstantSquare) -> None:
        """Clear piece at square."""
        self.set_piece(square, None)

    def is_empty(self, square: ConstantSquare) -> bool:
        """Check if square is empty."""
        return self.get_piece(square) is None

    def get_color_at(self, square: ConstantSquare) -> Optional[Color]:
        """Get color of piece at square."""
        piece = self.get_piece(square)
        return piece.color if piece else None

    def get_piece_type_at(self, square: ConstantSquare) -> Optional[PieceType]:
        """Get piece type at square."""
        piece = self.get_piece(square)
        return piece.kind if piece else None

    def is_same_color(self, square1: ConstantSquare, square2: ConstantSquare) -> bool:
        """Check if two squares have pieces of the same color."""
        piece1 = self.get_piece(square1)
        piece2 = self.get_piece(square2)
        return (
            piece1 is not None and piece2 is not None and piece1.color == piece2.color
        )

    def is_opponent(self, square1: ConstantSquare, square2: ConstantSquare) -> bool:
        """Check if two squares have pieces of opposite colors."""
        piece1 = self.get_piece(square1)
        piece2 = self.get_piece(square2)
        return (
            piece1 is not None and piece2 is not None and piece1.color != piece2.color
        )

    def is_valid_position(self, square: ConstantSquare) -> bool:
        """Check if square is on board."""
        return 0 <= int(square.row) < 8 and 0 <= int(square.col) < 8

    def find_king(self, color: Color) -> Optional[ConstantSquare]:
        """Find king of given color."""
        for row in range(8):
            for col in range(8):
                square = ConstantSquare(
                    row=get_row_constant(row), col=get_col_constant(col)
                )
                piece = self.get_piece(square)
                if (
                    piece is not None
                    and piece.color == color
                    and piece.kind == PieceType.KING
                ):
                    return square
        return None

    def clone(self) -> BoardState:
        """Create a deep copy of the board state.

        Creates new Piece objects so cloned pieces are independent of originals.
        Each cloned piece's _square is updated to reference the cloned board.
        """
        board_copy: List[List[Optional[Piece]]] = []
        for row in self.board:
            cloned_row: List[Optional[Piece]] = []
            for piece in row:
                if piece is None:
                    cloned_row.append(None)
                else:
                    cloned_piece = copy.deepcopy(piece)
                    cloned_row.append(cloned_piece)
            board_copy.append(cloned_row)
        return BoardState(
            board=board_copy,
            turn=self.turn,
            en_passant_target=self.en_passant_target,
            white_kingside=self.white_kingside,
            white_queenside=self.white_queenside,
            black_kingside=self.black_kingside,
            black_queenside=self.black_queenside,
        )

    def set_en_passant_target(self, square: Optional[ConstantSquare]) -> None:
        """Set the en passant target square."""
        self.en_passant_target = square
