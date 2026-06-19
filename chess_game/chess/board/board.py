"""Main Board class - orchestrator for chess game logic.

This module provides the Board class which owns all game state and delegates
to specialized modules for validation, execution, and special rules.
"""

from __future__ import annotations
from typing import List, Optional, Tuple

from chess_game.chess.constants import Color
from chess_game.chess.types import (
    PieceType,
    Piece,
    CastlingRights,
    BoardValidators,
    GameMetadata,
    MoveCounters,
)
from chess_game.chess.board.move_validation import MoveValidator
from chess_game.chess.board.move_execution import MoveExecutor
from chess_game.chess.board.castling import (
    CastlingValidator,
    _clear_castling_for_color,
    _clear_captured_rook_castling_right,
    _clear_rook_castling_right,
)
from chess_game.chess.board.promotion import PromotionValidator
from chess_game.chess.board.en_passant import EnPassantValidator
from chess_game.chess.board.piece_validation import PieceMoveChecker
from chess_game.chess.board.game_state import (
    is_in_check as _gs_is_in_check,
    is_checkmate as _gs_is_checkmate,
    is_stalemate as _gs_is_stalemate,
)
from chess_game.chess.coords import index_to_algebraic
from chess_game.chess.constants import (
    ConstantSquare,
    get_row_constant,
    get_col_constant,
    get_square_constant,
)
from chess_game.chess.board.board_setup import create_piece, create_starting_grid
from chess_game.chess.board.board_fen import (
    _fen_init_state,
    _fen_parse_fields,
    _fen_parse_placement,
)

LegalMove = tuple[ConstantSquare, ConstantSquare, Optional[PieceType]]

# Public surface of this module (create_piece is re-exported from board_setup;
# the board package and external callers import it from chess_game.chess.board.board).
__all__ = ["Board", "create_piece", "offset_square", "forward_one", "LegalMove"]


def offset_square(s: ConstantSquare, dr: int, dc: int) -> ConstantSquare:
    """Offset square by delta row and column."""
    if isinstance(s, tuple):
        s = ConstantSquare(row=get_row_constant(s[0]), col=get_col_constant(s[1]))
    new_row = int(s.row) + dr
    new_col = int(s.col) + dc
    return ConstantSquare(row=get_row_constant(new_row), col=get_col_constant(new_col))


def forward_one(s: ConstantSquare, color: Color) -> ConstantSquare:
    """Move one square forward for a pawn."""
    if color == Color.WHITE:
        return offset_square(s, -1, 0)  # White moves toward rank 8 (row 0)
    return offset_square(s, 1, 0)  # Black moves toward rank 1 (row 7)


class Board:
    """Main Board class owning all game state.

    State attributes:
        board: 8x8 list of Piece or None
        turn: Color whose turn it is
        en_passant_target: Optional en passant square
        castling_rights: CastlingRights tracking castling availability
        halfmove_clock: Ply count since the last pawn move or capture
        fullmove_number: Full move number starting at 1 and incrementing after Black
    """

    en_passant_target: Optional[ConstantSquare]
    castling_rights: CastlingRights
    halfmove_clock: int
    fullmove_number: int

    def __init__(self) -> None:
        self.board: List[List[Optional[Piece]]] = create_starting_grid()
        self.turn = Color.WHITE
        self._state = GameMetadata()
        self._move_history: List[Tuple[ConstantSquare, ConstantSquare, Optional[PieceType]]] = []

    @property
    def _validators(self) -> BoardValidators:
        """Validator bundle, built lazily on first use.

        The search clones the board hundreds of thousands of times per move just to
        test king safety, and those throwaway clones never touch the validators.
        Building them eagerly in ``clone()`` was pure waste, so they are created on
        first access and cached instead.
        """
        validators = self.__dict__.get("_validators_cache")
        if validators is None:
            validators = BoardValidators(
                move_validator=MoveValidator(self),
                move_executor=MoveExecutor(self),
                promotion_validator=PromotionValidator(self),
                en_passant_validator=EnPassantValidator(self),
                piece_move_checker=PieceMoveChecker(self),
            )
            self.__dict__["_validators_cache"] = validators
        return validators

    @property
    def piece_move_checker(self) -> PieceMoveChecker:
        """Access to piece-specific move validation."""
        return self._validators.piece_move_checker

    def __getattr__(self, name: str) -> object:
        """Expose move-counter fields through the historical Board API."""

        if name == "en_passant_target":
            return self._state.en_passant_target
        if name == "castling_rights":
            return self._state.castling_rights
        if name in {"halfmove_clock", "fullmove_number"}:
            return getattr(self._state.move_counters, name)
        raise AttributeError(f"{type(self).__name__!s} has no attribute {name!r}")

    def __setattr__(self, name: str, value: object) -> None:
        """Route move-counter writes to the shared MoveCounters state."""

        if name == "en_passant_target" and "_state" in self.__dict__:
            if value is not None and not isinstance(value, ConstantSquare):
                raise TypeError("en_passant_target must be a ConstantSquare or None")
            self._state.en_passant_target = value
            return
        if name == "castling_rights" and "_state" in self.__dict__:
            if not isinstance(value, CastlingRights):
                raise TypeError("castling_rights must be a CastlingRights instance")
            self._state.castling_rights = value
            return
        if name in {"halfmove_clock", "fullmove_number"} and "_state" in self.__dict__:
            setattr(self._state.move_counters, name, value)
            return
        super().__setattr__(name, value)

    # ---- board accessors ----

    def get_piece(self, square: ConstantSquare) -> Optional[Piece]:
        """Get piece at square."""
        if isinstance(square, tuple):
            square = ConstantSquare(
                row=get_row_constant(square[0]), col=get_col_constant(square[1])
            )
        row = int(square.row)
        col = int(square.col)
        if 0 <= row < 8 and 0 <= col < 8:
            return self.board[row][col]
        return None

    def set_piece(self, square: ConstantSquare, piece: Optional[Piece]) -> None:
        """Set piece at square."""
        if isinstance(square, tuple):
            square = ConstantSquare(
                row=get_row_constant(square[0]), col=get_col_constant(square[1])
            )
        if not (0 <= int(square.row) < 8 and 0 <= int(square.col) < 8):
            raise ValueError(f"Invalid square: {square}")
        if piece is not None:
            piece.square = square
        self.board[int(square.row)][int(square.col)] = piece

    def clear_square(self, square: ConstantSquare) -> None:
        """Clear square."""
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

    def find_king(self, color: Color) -> Optional[ConstantSquare]:
        """Find king of given color."""
        for row in range(8):
            for col in range(8):
                piece = self.board[row][col]
                if (
                    piece is not None
                    and piece.color == color
                    and piece.kind == PieceType.KING
                ):
                    return get_square_constant(row, col)
        return None

    def is_valid_position(self, square: ConstantSquare) -> bool:
        """Validate square coordinates."""
        return 0 <= int(square.row) < 8 and 0 <= int(square.col) < 8

    def is_same_color(self, square1: ConstantSquare, square2: ConstantSquare) -> bool:
        """Check if pieces at both squares have same color."""
        piece1 = self.get_piece(square1)
        piece2 = self.get_piece(square2)
        return (
            piece1 is not None and piece2 is not None and piece1.color == piece2.color
        )

    def is_opponent(self, square1: ConstantSquare, square2: ConstantSquare) -> bool:
        """Check if pieces at both squares are opponents."""
        piece1 = self.get_piece(square1)
        piece2 = self.get_piece(square2)
        return (
            piece1 is not None and piece2 is not None and piece1.color != piece2.color
        )

    # ---- board creation ----

    def clear_board(self) -> None:
        """Clear all pieces from the board."""
        for row in range(8):
            for col in range(8):
                self.clear_square(get_square_constant(row, col))

    # ---- piece move validation (delegates to PieceMoveChecker) ----

    def is_valid_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate a move for the piece on from_square."""
        return self._validators.move_validator.is_valid_move(from_square, to_square)

    def _is_valid_rook_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        return self._validators.piece_move_checker.is_valid_rook_move(
            from_square, to_square
        )

    def _is_valid_bishop_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        return self._validators.piece_move_checker.is_valid_bishop_move(
            from_square, to_square
        )

    def _is_valid_queen_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        return self._validators.piece_move_checker.is_valid_queen_move(
            from_square, to_square
        )

    def _is_valid_knight_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        return self._validators.piece_move_checker.is_valid_knight_move(
            from_square, to_square
        )

    def _is_valid_king_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        return self._validators.piece_move_checker.is_valid_king_move(
            from_square, to_square
        )

    def _is_valid_pawn_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        return self._validators.piece_move_checker.is_valid_pawn_move(
            from_square, to_square
        )

    # ---- game state (delegates to game_state module) ----

    def _is_in_check(self, color: Color) -> bool:
        return _gs_is_in_check(self, color)

    def _is_checkmate(self, color: Optional[Color] = None) -> bool:
        return _gs_is_checkmate(self, color)

    def _is_stalemate(self, color: Optional[Color] = None) -> bool:
        return _gs_is_stalemate(self, color)

    # ---- clone ----

    def clone(self) -> Board:
        """Create a deep copy of the board."""
        cloned = Board.__new__(Board)
        cloned.board = [
            [piece.clone() if piece is not None else None for piece in row]
            for row in self.board
        ]
        cloned.turn = self.turn
        cloned.__dict__["_state"] = GameMetadata(
            en_passant_target=self.en_passant_target,
            castling_rights=CastlingRights(
                white_kingside=self.castling_rights.white_kingside,
                white_queenside=self.castling_rights.white_queenside,
                black_kingside=self.castling_rights.black_kingside,
                black_queenside=self.castling_rights.black_queenside,
            ),
            move_counters=MoveCounters(
                halfmove_clock=self.halfmove_clock,
                fullmove_number=self._state.move_counters.fullmove_number,
            ),
        )
        cloned.__dict__["_move_history"] = self._move_history_copy()
        return cloned

    def _move_history_copy(
        self,
    ) -> List[Tuple[ConstantSquare, ConstantSquare, Optional[PieceType]]]:
        """Return a copy of the move history."""
        return list(self._move_history)

    def _replace_move_history(
        self,
        moves: List[Tuple[ConstantSquare, ConstantSquare, Optional[PieceType]]],
    ) -> None:
        """Replace the move history with a copied list."""
        self._move_history = list(moves)

    # ---- legal moves ----

    def get_legal_moves(
        self, square: Optional[ConstantSquare] = None
    ) -> List[Tuple[ConstantSquare, ConstantSquare, Optional[PieceType]]]:
        """Get all legal moves from the specified square, or all side-to-move legal moves.

        When square is None, iterates only pieces of side-to-move.
        When square is provided and empty, returns [].
        When square is provided and contains an opponent's piece, returns [].
        """
        if square is None:
            return self._validators.move_validator.get_legal_moves()
        piece = self.get_piece(square)
        if piece is None:
            return []
        if piece.color != self.turn:
            return []
        return self._validators.move_validator.get_legal_moves(square)

    def get_legal_moves_for_color(
        self, color: Color
    ) -> List[Tuple[ConstantSquare, ConstantSquare, Optional[PieceType]]]:
        """Get all legal moves for a specific color regardless of turn."""
        saved_turn = self.turn
        try:
            self.turn = color
            return self._validators.move_validator.get_legal_moves()
        finally:
            self.turn = saved_turn

    # ---- make_move ----

    def make_move(
        self,
        start_pos: ConstantSquare,
        end_pos: ConstantSquare,
        promotion: Optional[PieceType] = None,
    ) -> bool:
        """Make a move on the board."""
        if isinstance(start_pos, tuple):
            start_pos = ConstantSquare(
                row=get_row_constant(start_pos[0]), col=get_col_constant(start_pos[1])
            )
        if isinstance(end_pos, tuple):
            end_pos = ConstantSquare(
                row=get_row_constant(end_pos[0]), col=get_col_constant(end_pos[1])
            )

        start_piece = self.get_piece(start_pos)
        if start_piece is None or start_piece.color != self.turn:
            return False

        if not self._validators.promotion_validator.is_valid_promotion_choice(
            start_piece, end_pos, promotion
        ):
            return False

        # Castling
        if start_piece.kind == PieceType.KING and CastlingValidator.is_castling_move(
            start_pos, end_pos
        ):
            if not CastlingValidator.can_castle(
                self, start_pos, end_pos, start_piece.color, start_piece.color
            ):
                return False

        # En passant
        is_en_passant = (
            start_piece.kind == PieceType.PAWN
            and self.en_passant_target == end_pos
            and start_pos.col != end_pos.col
        )

        if is_en_passant:
            move_valid = (
                self._validators.en_passant_validator.validate_en_passant_capture(
                    start_pos, end_pos, start_piece
                )
            )
        else:
            move_valid = self._validators.move_validator.is_move_legal(
                start_pos, end_pos
            )
        if not move_valid:
            return False

        return self.apply_legal_move(
            start_pos,
            end_pos,
            promotion=promotion,
            start_piece=start_piece,
        )

    def apply_legal_move(
        self,
        start_pos: ConstantSquare,
        end_pos: ConstantSquare,
        promotion: Optional[PieceType] = None,
        start_piece: Optional[Piece] = None,
    ) -> bool:
        """Apply a move that has already been validated as legal."""
        if start_piece is None:
            start_piece = self.get_piece(start_pos)
        if start_piece is None:
            return False
        moved_by_black = self.turn == Color.BLACK
        is_capture = self._is_capture_move(start_pos, end_pos, start_piece)

        success = self._validators.move_executor.execute_move(
            start_pos, end_pos, promotion, start_piece
        )
        if not success:
            return False

        self._move_history.append((start_pos, end_pos, promotion))
        self._update_castling_rights(start_pos, end_pos, start_piece)
        self._validators.en_passant_validator.clear_en_passant_target_if_needed(
            start_pos, end_pos, start_piece
        )
        self._validators.en_passant_validator.set_en_passant_target_if_valid(
            start_pos, end_pos, start_piece
        )
        self._update_move_counters(start_piece, is_capture, moved_by_black)
        self.turn = Color.BLACK if self.turn == Color.WHITE else Color.WHITE
        return True

    def _is_capture_move(
        self,
        start_pos: ConstantSquare,
        end_pos: ConstantSquare,
        start_piece: Piece,
    ) -> bool:
        """Return whether the move captures material, including en passant."""

        return self.get_piece(end_pos) is not None or (
            start_piece.kind == PieceType.PAWN
            and self.en_passant_target == end_pos
            and start_pos.col != end_pos.col
        )

    def _update_move_counters(
        self,
        start_piece: Piece,
        is_capture: bool,
        moved_by_black: bool,
    ) -> None:
        """Update halfmove and fullmove counters after a legal move."""

        if start_piece.kind == PieceType.PAWN or is_capture:
            self.halfmove_clock = 0
        else:
            self.halfmove_clock += 1
        if moved_by_black:
            self._state.move_counters.fullmove_number += 1

    def _update_castling_rights(
        self,
        start_pos: ConstantSquare,
        end_pos: ConstantSquare,
        start_piece: Piece,
    ) -> None:
        """Update castling rights after a move."""
        piece_color = start_piece.color

        # King moves -> lose both castling rights for that color
        if start_piece.kind == PieceType.KING:
            _clear_castling_for_color(self.castling_rights, piece_color)

        # Rook moves from starting square -> lose side-specific castling right
        if start_piece.kind == PieceType.ROOK:
            _clear_rook_castling_right(self.castling_rights, start_pos, piece_color)

        # Rook captured on its starting square
        _clear_captured_rook_castling_right(self.castling_rights, end_pos)

# ---- display ----

    def display(self) -> None:
        """Display the board with last moves on the right."""
        board_lines = self._build_board_lines()
        move_lines = self._build_recent_move_lines()
        print("    a   b   c   d   e   f   g   h")
        print("  +---+---+---+---+---+---+---+---+")

        for row_index, rank_line in enumerate(board_lines):
            move_note = move_lines[row_index] if row_index < len(move_lines) else ""
            print(rank_line + (f" {move_note}" if move_note else ""))
            print("  +---+---+---+---+---+---+---+---+")

        turn_label = self.turn.name.upper()
        print(f"  Turn: {turn_label}")

    def _build_board_lines(self) -> List[str]:
        """Build the board rows for display."""
        board_lines: List[str] = []
        for row_index, row in enumerate(self.board):
            rank = 8 - row_index
            cells = [self._display_cell(piece) for piece in row]
            board_lines.append(f"{rank} |{'|'.join(cells)}|")
        return board_lines

    def _display_cell(self, piece: Optional[Piece]) -> str:
        """Format one display cell."""
        if piece is None:
            return "   "
        symbol = piece.kind.name[0]
        if piece.kind == PieceType.KNIGHT:
            symbol = "N"
        if piece.color == Color.BLACK:
            symbol = symbol.lower()
        return f" {symbol} "

    def _build_recent_move_lines(self) -> List[str]:
        """Build move-history strings shown next to the board."""
        moves = self._move_history_copy()
        recent_moves = moves[-10:] if len(moves) > 10 else moves
        first_index = len(moves) - len(recent_moves)
        move_lines: List[str] = []
        index = 0
        while index < len(recent_moves):
            move_lines.append(self._format_move_pair(recent_moves, first_index, index))
            index += 2
        return move_lines

    def _format_move_pair(
        self,
        recent_moves: List[Tuple[ConstantSquare, ConstantSquare, Optional[PieceType]]],
        first_index: int,
        index: int,
    ) -> str:
        """Format one move pair from the recent move list."""
        start, end, promo = recent_moves[index]
        move_num = (first_index + index) // 2 + 1
        first_move = self._to_alg(start, end, promo)
        if index + 1 >= len(recent_moves):
            return f"{move_num}. {first_move}"
        second_start, second_end, second_promo = recent_moves[index + 1]
        second_move = self._to_alg(second_start, second_end, second_promo)
        return f"{move_num}. {first_move} {second_move}"

    def _to_alg(self, start, end, promotion) -> str:
        """Format a single move as algebraic notation."""
        base = index_to_algebraic(start) + index_to_algebraic(end)
        if promotion is not None:
            name = promotion.name.lower()
            base += name[0] if name else "q"
        return base

    def board_render_string(self) -> str:
        """Return the board as a plain ASCII string without move annotations."""
        sep = "  +---+---+---+---+---+---+---+---+"
        lines = ["    a   b   c   d   e   f   g   h", sep]
        for rank_line in self._build_board_lines():
            lines.append(rank_line)
            lines.append(sep)
        lines.append(f"  Turn: {self.turn.name.upper()}")
        return "\n".join(lines)

    # ---- FEN support ----

    _PIECE_TO_FEN: dict = {
        (Color.WHITE, PieceType.PAWN): "P",
        (Color.WHITE, PieceType.KNIGHT): "N",
        (Color.WHITE, PieceType.BISHOP): "B",
        (Color.WHITE, PieceType.ROOK): "R",
        (Color.WHITE, PieceType.QUEEN): "Q",
        (Color.WHITE, PieceType.KING): "K",
        (Color.BLACK, PieceType.PAWN): "p",
        (Color.BLACK, PieceType.KNIGHT): "n",
        (Color.BLACK, PieceType.BISHOP): "b",
        (Color.BLACK, PieceType.ROOK): "r",
        (Color.BLACK, PieceType.QUEEN): "q",
        (Color.BLACK, PieceType.KING): "k",
    }

    _FEN_TO_PIECE: dict = {
        "P": (Color.WHITE, PieceType.PAWN),
        "N": (Color.WHITE, PieceType.KNIGHT),
        "B": (Color.WHITE, PieceType.BISHOP),
        "R": (Color.WHITE, PieceType.ROOK),
        "Q": (Color.WHITE, PieceType.QUEEN),
        "K": (Color.WHITE, PieceType.KING),
        "p": (Color.BLACK, PieceType.PAWN),
        "n": (Color.BLACK, PieceType.KNIGHT),
        "b": (Color.BLACK, PieceType.BISHOP),
        "r": (Color.BLACK, PieceType.ROOK),
        "q": (Color.BLACK, PieceType.QUEEN),
        "k": (Color.BLACK, PieceType.KING),
    }

    def to_fen(self) -> str:
        """Serialize the board to a FEN string.

        Row 0 (rank 8) is the first rank in the FEN piece placement.
        """
        rows = []
        for row_idx in range(8):
            empty_count = 0
            row_str = ""
            for col_idx in range(8):
                piece = self.board[row_idx][col_idx]
                if piece is None:
                    empty_count += 1
                else:
                    if empty_count:
                        row_str += str(empty_count)
                        empty_count = 0
                    row_str += self._PIECE_TO_FEN[(piece.color, piece.kind)]
            if empty_count:
                row_str += str(empty_count)
            rows.append(row_str)
        placement = "/".join(rows)

        turn_char = "w" if self.turn == Color.WHITE else "b"

        castling = ""
        if self.castling_rights.white_kingside:
            castling += "K"
        if self.castling_rights.white_queenside:
            castling += "Q"
        if self.castling_rights.black_kingside:
            castling += "k"
        if self.castling_rights.black_queenside:
            castling += "q"
        castling = castling or "-"

        ep_sq = self.en_passant_target
        ep_str = index_to_algebraic(ep_sq) if ep_sq is not None else "-"

        halfmove = self.halfmove_clock
        fullmove = self._state.move_counters.fullmove_number
        return f"{placement} {turn_char} {castling} {ep_str} {halfmove} {fullmove}"

    @classmethod
    def from_fen(cls, fen: str) -> "Board":
        """Construct a Board from a FEN string.

        Supports all six FEN fields; the halfmove clock and fullmove number
        default to 0 and 1 respectively when omitted.
        """
        parts = fen.strip().split()
        if len(parts) < 2:
            raise ValueError(f"Invalid FEN (need at least 2 fields): {fen!r}")
        fields = _fen_parse_fields(parts)
        board = cls.__new__(cls)
        board.__dict__["board"] = [[None] * 8 for _ in range(8)]
        board.__dict__["_move_history"] = []
        _fen_init_state(board, fields)
        _fen_parse_placement(board, cls._FEN_TO_PIECE, fields[0])
        return board
