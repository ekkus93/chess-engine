"""Move validation logic for the chess engine."""

from __future__ import annotations

from typing import TYPE_CHECKING, List, Optional, Tuple

from chess_game.chess.constants import Color, ConstantSquare
from chess_game.chess.types import Piece, PieceType
from chess_game.chess.board.attack_utils import piece_attacks_square
from chess_game.chess.board.castling import CastlingValidator
from chess_game.chess.board.en_passant import EnPassantValidator
from chess_game.chess.board.path_validator import PathValidator
from chess_game.chess.board.promotion import PROMOTION_PIECES
from chess_game.chess.pieces.piece_movers import PieceMovers
from chess_game.chess.constants import (
    get_row_constant,
    get_col_constant,
)

if TYPE_CHECKING:
    from chess_game.chess.board.board import Board


class MoveValidator:
    """Validates whether a move is legal according to chess rules."""

    def __init__(self, board: Board):
        """Initialize with board."""
        self.board = board
        self.path_validator = PathValidator()
        self.piece_movers = PieceMovers()

    def is_move_legal(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Check if a move is valid."""
        return self.is_valid_move(from_square, to_square)

    def is_valid_move(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Check if a move is valid.

        Validation flow:
        1. Source square must contain a piece.
        2. Destination must be on board.
        3. Destination must not contain a friendly piece.
        4. Castling must be detected and delegated to castling validation.
        5. En passant must be detected and delegated to en passant validation.
        6. For normal moves, destination must be in
           PieceMovers.get_valid_moves(piece, board_state).
        7. Simulate the move on a cloned state.
        8. Reject if it leaves the moving side's king in check.
        9. Otherwise return True.
        """
        piece = self._get_source_piece(from_square, to_square)
        if piece is None:
            return False

        # 4. Castling delegation
        if self._is_castling_move(piece, from_square, to_square):
            return self._validate_castling(piece, from_square, to_square)

        # 5. En passant delegation
        if self._is_en_passant_move(piece, from_square, to_square):
            return self._validate_en_passant(piece, from_square, to_square)

        # 6. Pseudo-legal geometry via PieceMovers
        valid_moves = self.piece_movers.get_valid_moves(piece, self.board)
        if to_square not in valid_moves:
            return False

        # 7-8. Simulate and reject if it leaves king in check
        if self._would_expose_king_to_check(piece, from_square, to_square):
            return False

        # 9. Otherwise return True
        return True

    def _get_source_piece(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> Optional[Piece]:
        """Get the piece at from_square, validating basic move constraints."""
        piece = self.board.get_piece(from_square)
        if piece is None:
            return None
        if not self.board.is_valid_position(to_square):
            return None
        dest_piece = self.board.get_piece(to_square)
        if dest_piece is not None and dest_piece.color == piece.color:
            return None
        if dest_piece is not None and dest_piece.kind == PieceType.KING:
            return None
        return piece

    def _is_castling_move(
        self, piece: Piece, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Check if this is a castling move."""
        if piece.kind != PieceType.KING:
            return False
        return CastlingValidator.is_castling_move(from_square, to_square)

    def _is_en_passant_move(
        self, piece: Piece, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Check if this is an en passant capture, delegating to EnPassantValidator."""
        if piece.kind != PieceType.PAWN:
            return False

        if self.board.en_passant_target is None:
            return False

        # Use EnPassantValidator to avoid duplicating its logic
        validator = EnPassantValidator(self.board)
        return validator.validate_en_passant_capture(
            from_square, to_square, piece
        )

    def _validate_castling(
        self, piece: Piece, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate castling move by delegating to CastlingValidator."""
        return CastlingValidator.can_castle(
            self.board, from_square, to_square, piece.color, piece.color
        )

    def _get_castling_moves(self, piece: Piece) -> List[ConstantSquare]:
        """Get castling destination squares if the piece is a king."""
        if piece.kind != PieceType.KING:
            return []
        assert piece.square is not None

        moves: List[ConstantSquare] = []
        king_row = int(piece.square.row)

        if CastlingValidator.can_castle_kingside(self.board, piece.color):
            moves.append(
                ConstantSquare(
                    row=get_row_constant(king_row),
                    col=get_col_constant(6),
                )
            )

        if CastlingValidator.can_castle_queenside(self.board, piece.color):
            moves.append(
                ConstantSquare(
                    row=get_row_constant(king_row),
                    col=get_col_constant(2),
                )
            )

        return moves

    def _validate_en_passant(
        self, piece: Piece, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate en passant capture."""
        if self.board.en_passant_target is None:
            return False

        target_square = self.board.en_passant_target

        if int(to_square.row) != int(target_square.row):
            return False

        if to_square != target_square:
            return False

        # Check that en passant capture doesn't expose king to check
        if self._would_expose_king_to_check_en_passant(piece, from_square, to_square):
            return False

        return True

    def get_legal_moves(
        self,
        from_square: Optional[ConstantSquare] = None,
    ) -> List[Tuple[ConstantSquare, ConstantSquare, Optional[PieceType]]]:
        """Get all legal moves (with check validation).

        When from_square is None, iterates only pieces of side-to-move.
        When from_square is provided, returns legal moves for that piece.
        """
        if from_square is not None:
            piece = self.board.get_piece(from_square)
            if piece is None:
                return []
            return self._get_legal_moves_for_piece(piece, from_square)

        all_moves: List[Tuple[ConstantSquare, ConstantSquare, Optional[PieceType]]] = []
        for row in range(8):
            for col in range(8):
                sq = ConstantSquare(
                    row=get_row_constant(row), col=get_col_constant(col)
                )
                piece = self.board.get_piece(sq)
                if piece is not None and piece.color == self.board.turn:
                    all_moves.extend(self._get_legal_moves_for_piece(piece, sq))
        return all_moves

    def _get_legal_moves_for_piece(
        self,
        piece: Piece,
        from_square: ConstantSquare,
    ) -> List[Tuple[ConstantSquare, ConstantSquare, Optional[PieceType]]]:
        """Get all legal moves for a given piece from a given square."""
        valid_moves = self.piece_movers.get_valid_moves(piece, self.board)
        if piece.kind == PieceType.KING:
            valid_moves.extend(self._get_castling_moves(piece))

        moves: List[Tuple[ConstantSquare, ConstantSquare, Optional[PieceType]]] = []
        for to_square in valid_moves:
            if self.is_valid_move(from_square, to_square):
                if piece.kind == PieceType.PAWN:
                    if self._is_promotion_dest(piece, to_square):
                        for pt in PROMOTION_PIECES:
                            moves.append((from_square, to_square, pt))
                    else:
                        moves.append((from_square, to_square, None))
                else:
                    moves.append((from_square, to_square, None))
        return moves

    def _is_promotion_dest(self, piece: Piece, to_square: ConstantSquare) -> bool:
        """Check if moving to this square triggers pawn promotion."""
        if piece.kind != PieceType.PAWN:
            return False
        if piece.color == Color.WHITE and int(to_square.row) == 0:
            return True
        if piece.color == Color.BLACK and int(to_square.row) == 7:
            return True
        return False

    def _get_promotion_piece(
        self, piece: Piece, to_square: ConstantSquare
    ) -> Optional[PieceType]:
        """Get the promotion piece type if pawn promotion is needed."""
        if piece.kind != PieceType.PAWN:
            return None

        # White promotes at row 0 (rank 8), Black at row 7 (rank 1)
        if piece.color == Color.WHITE and int(to_square.row) == 0:
            return PieceType.QUEEN
        if piece.color == Color.BLACK and int(to_square.row) == 7:
            return PieceType.QUEEN

        return None

    def _would_expose_king_to_check(
        self, piece: Piece, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Check if making the move would expose the piece's king to check."""
        temp_board = self.board.clone()
        temp_piece = Piece(
            color=piece.color,
            kind=piece.kind,
            _square=to_square,
        )
        temp_board.set_piece(to_square, temp_piece)
        temp_board.clear_square(from_square)

        king_square = temp_board.find_king(piece.color)
        if king_square is None:
            return False

        enemy_color = Color.BLACK if piece.color == Color.WHITE else Color.WHITE
        return self._is_square_attacked_by_color(temp_board, king_square, enemy_color)

    def _would_expose_king_to_check_en_passant(
        self, piece: Piece, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Check if en passant capture would expose king to check."""
        temp_board = self._simulate_en_passant(piece, from_square, to_square)
        king_square = temp_board.find_king(piece.color)
        if king_square is None:
            return False

        enemy_color = Color.BLACK if piece.color == Color.WHITE else Color.WHITE
        return self._is_square_attacked_by_color(temp_board, king_square, enemy_color)

    def _simulate_en_passant(
        self, piece: Piece, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> "Board":
        """Simulate en passant capture on a cloned board."""
        temp_board = self.board.clone()
        temp_piece = Piece(
            color=piece.color,
            kind=piece.kind,
            _square=to_square,
        )
        temp_board.set_piece(to_square, temp_piece)
        temp_board.clear_square(from_square)

        direction = -1 if piece.color == Color.WHITE else 1
        assert self.board.en_passant_target is not None
        captured_row = int(self.board.en_passant_target.row) - direction
        captured_square = ConstantSquare(
            row=get_row_constant(captured_row),
            col=get_col_constant(int(to_square.col)),
        )
        temp_board.clear_square(captured_square)
        return temp_board

    def _is_square_attacked_by_color(
        self, board: "Board", square: ConstantSquare, color: Color
    ) -> bool:
        """Check if square is attacked by any piece of the given color."""
        for row in range(8):
            for col in range(8):
                sq = ConstantSquare(
                    row=get_row_constant(row), col=get_col_constant(col)
                )
                attacker = board.get_piece(sq)
                if attacker is not None and attacker.color == color:
                    if self._can_piece_attack(attacker, sq, square, board):
                        return True
        return False

    def is_piece_pinned(self, square: ConstantSquare, piece_color: Color) -> bool:
        """Check if a piece is pinned to its king."""
        king_square = self.board.find_king(piece_color)
        if king_square is None:
            return False

        enemy_color = Color.BLACK if piece_color == Color.WHITE else Color.WHITE

        for row in range(8):
            for col in range(8):
                sq = ConstantSquare(
                    row=get_row_constant(row), col=get_col_constant(col)
                )
                attacker = self.board.get_piece(sq)
                if attacker and attacker.color == enemy_color:
                    if self._can_piece_attack(attacker, sq, king_square, self.board):
                        if self._attack_line_goes_through(sq, king_square, square):
                            return True

        return False

    def _can_piece_attack(
        self,
        attacker: Piece,
        attacker_square: ConstantSquare,
        target_square: ConstantSquare,
        board: "Board",
    ) -> bool:
        """Check if attacker can attack target via shared attack_utils."""
        return piece_attacks_square(
            attacker,
            attacker_square,
            target_square,
            board,
        )

    def _attack_line_goes_through(
        self,
        attacker_sq: ConstantSquare,
        target_sq: ConstantSquare,
        check_sq: ConstantSquare,
    ) -> bool:
        """Check if the attack line from attacker to target goes through check_sq."""
        if int(attacker_sq.row) == int(target_sq.row):
            return int(check_sq.row) == int(attacker_sq.row) and (
                int(check_sq.col) > min(int(attacker_sq.col), int(target_sq.col))
                and int(check_sq.col) < max(int(attacker_sq.col), int(target_sq.col))
            )

        if int(attacker_sq.col) == int(target_sq.col):
            return int(check_sq.col) == int(attacker_sq.col) and (
                int(check_sq.row) > min(int(attacker_sq.row), int(target_sq.row))
                and int(check_sq.row) < max(int(attacker_sq.row), int(target_sq.row))
            )

        if int(attacker_sq.row) - int(attacker_sq.col) == int(target_sq.row) - int(
            target_sq.col
        ):
            return int(check_sq.row) - int(check_sq.col) == int(attacker_sq.row) - int(
                attacker_sq.col
            ) and (
                int(check_sq.row) > min(int(attacker_sq.row), int(target_sq.row))
                and int(check_sq.row) < max(int(attacker_sq.row), int(target_sq.row))
            )

        if int(attacker_sq.row) + int(attacker_sq.col) == int(target_sq.row) + int(
            target_sq.col
        ):
            return int(check_sq.row) + int(check_sq.col) == int(attacker_sq.row) + int(
                attacker_sq.col
            ) and (
                int(check_sq.row) > min(int(attacker_sq.row), int(target_sq.row))
                and int(check_sq.row) < max(int(attacker_sq.row), int(target_sq.row))
            )

        return False
