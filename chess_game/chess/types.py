"""Chess piece and move data types."""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional

from chess_game.chess.constants import (
    ConstantSquare,
    Color,
    PieceType,
    RowConstant,
    ColConstant,
)

if TYPE_CHECKING:
    from chess_game.chess.board.move_validation import MoveValidator
    from chess_game.chess.board.move_execution import MoveExecutor
    from chess_game.chess.board.promotion import PromotionValidator
    from chess_game.chess.board.en_passant import EnPassantValidator
    from chess_game.chess.board.piece_validation import PieceMoveChecker


@dataclass
class Piece:
    """A chess piece with its color, kind, and current board square."""

    color: Color
    kind: PieceType
    _square: Optional[ConstantSquare] = None

    @property
    def row(self) -> Optional[RowConstant]:
        """The row constant of the piece's current square, or None if unplaced."""
        return self._square.row if self._square else None

    @property
    def col(self) -> Optional[ColConstant]:
        """The column constant of the piece's current square, or None if unplaced."""
        return self._square.col if self._square else None

    @property
    def square(self) -> Optional[ConstantSquare]:
        """The ConstantSquare of the piece's current position, or None if unplaced."""
        return self._square

    @square.setter
    def square(self, value: Optional[ConstantSquare]) -> None:
        """Set the piece's current square."""
        self._square = value

    def clone(self) -> "Piece":
        """Create a cheap independent copy of the piece."""
        return Piece(color=self.color, kind=self.kind, _square=self._square)


@dataclass
class CastlingRights:
    """Tracks castling availability for both colors."""

    white_kingside: bool = True
    white_queenside: bool = True
    black_kingside: bool = True
    black_queenside: bool = True


@dataclass
class MoveCounters:
    """Tracks halfmove and fullmove counts for rule enforcement."""

    halfmove_clock: int = 0
    fullmove_number: int = 1


@dataclass
class GameMetadata:
    """Mutable board metadata that is separate from piece placement."""

    en_passant_target: Optional[ConstantSquare] = None
    castling_rights: CastlingRights = field(default_factory=CastlingRights)
    move_counters: MoveCounters = field(default_factory=MoveCounters)


@dataclass
class BoardValidators:
    """Holds the validator components for a Board instance."""

    move_validator: "MoveValidator"
    promotion_validator: "PromotionValidator"
    en_passant_validator: "EnPassantValidator"
    piece_move_checker: "PieceMoveChecker"
    move_executor: "MoveExecutor"


@dataclass
class LegalMove:
    """A legal move from one square to another, optionally with promotion."""

    start: ConstantSquare
    end: ConstantSquare
    promotion: Optional[PieceType] = None
