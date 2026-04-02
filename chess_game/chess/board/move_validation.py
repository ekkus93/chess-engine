"""Move validation logic for the chess engine."""

from __future__ import annotations

from typing import List, Optional, Tuple

from chess_game.chess.color import Color
from chess_game.chess.types import Piece, PieceType, ConstantSquare
from chess_game.chess.board.board_state import BoardState
from chess_game.chess.board.castling import CastlingValidator
from chess_game.chess.board.path_validator import PathValidator
from chess_game.chess.pieces.piece_movers import PieceMovers
from chess_game.chess.constants import (
    get_row_constant,
    get_col_constant,
    COL_A,
    COL_C,
    COL_D,
    COL_E,
    COL_F,
    COL_G,
)


class MoveValidator:
    """Validates whether a move is legal according to chess rules."""

    def __init__(self, board: BoardState):
        """Initialize with board state."""
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
        """Check if a move is valid."""
        piece = self.board.get_piece(from_square)
        if piece is None:
            return False

        # Check for special moves first (before checking valid moves list)
        if self._is_en_passant_move(piece, from_square, to_square):
            return self._validate_en_passant(piece, from_square, to_square)

        if self._is_castling_move(piece, from_square, to_square):
            result = self._validate_castling(piece, from_square, to_square)
            # Castling destination must be empty (cannot castle on occupied square)
            if self.board.get_piece(to_square) is not None:
                return False
            return result

        if self._is_en_passant_move(piece, from_square, to_square):
            print(f"DEBUG validate: en passant move detected")
            return self._validate_en_passant(piece, from_square, to_square)

        # Regular move: check if destination is valid (not own piece)
        if self.board.get_piece(to_square) is not None:
            if self.board.get_piece(to_square).color == piece.color:
                return False

        # Check that the move doesn't leave the king in check (pin detection)
        if self._would_expose_king_to_check(piece, from_square, to_square):
            return False

        return True

    def _is_castling_move(
        self, piece: Piece, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Check if this is a castling move."""
        if piece.kind != PieceType.KING:
            return False

        from_row = int(piece._square.row)

        # Kingside castling
        if from_square == ConstantSquare(
            row=get_row_constant(from_row), col=COL_E
        ) and to_square == ConstantSquare(row=get_row_constant(from_row), col=COL_G):
            return True

        # Queenside castling
        if from_square == ConstantSquare(
            row=get_row_constant(from_row), col=COL_E
        ) and to_square == ConstantSquare(row=get_row_constant(from_row), col=COL_C):
            return True

        return False

    def _is_en_passant_move(
        self, piece: Piece, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Check if this is an en passant capture."""
        if piece.kind != PieceType.PAWN:
            return False

        # En passant captures diagonal - one file over, two ranks (jump move)
        col_diff = abs(int(to_square.col) - int(from_square.col))
        row_diff = abs(int(to_square.row) - int(from_square.row))

        if col_diff != 1 or row_diff != 2:
            return False

        # Check if en passant target is set
        if self.board.en_passant_target is None:
            return False

        # En passant target is the square the capturing pawn will land on
        # The capturing pawn moves diagonally to this square
        ep_target_row = int(self.board.en_passant_target.row)
        ep_target_col = int(self.board.en_passant_target.col)
        to_row = int(to_square.row)
        to_col = int(to_square.col)

        # Check that the target matches the destination square
        if ep_target_row != to_row or ep_target_col != to_col:
            return False

        return True

    def _validate_castling(
        self, piece: Piece, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate castling move."""
        color = piece.color
        color_str = "white" if color == Color.WHITE else "black"

        if from_square.row != to_square.row:
            return False

        # Check castling rights
        if color == Color.WHITE:
            kingside = self.board.white_kingside
            queenside = self.board.white_queenside
        else:
            kingside = self.board.black_kingside
            queenside = self.board.black_queenside

        if not kingside and not queenside:
            return False

        # Check path is clear
        if not self._is_castling_path_clear(from_square, to_square):
            return False

        # Check king doesn't pass through attacked squares
        enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
        king_path = [
            from_square,
            ConstantSquare(
                row=get_row_constant(int(from_square.row)),
                col=get_col_constant(int(from_square.col) + 1),
            ),
            to_square,
        ]

        for square in king_path:
            if CastlingValidator._is_square_attacked(self.board, square, enemy_color):
                return False

        return True

    def _is_castling_path_clear(
        self, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Check if castling path is clear."""
        from_col = int(from_square.col)
        to_col = int(to_square.col)

        # Kingside: check f-file
        if to_col == 6:  # COL_G
            return self.path_validator.is_path_clear(
                self.board,
                from_square,
                ConstantSquare(row=get_row_constant(int(from_square.row)), col=COL_F),
            )  # COL_F

        # Queenside: check d and c files
        if to_col == 2:  # COL_C
            return (
                self.path_validator.is_path_clear(
                    self.board,
                    from_square,
                    ConstantSquare(
                        row=get_row_constant(int(from_square.row)), col=COL_D
                    ),
                )  # COL_D
                and self.path_validator.is_path_clear(
                    self.board,
                    from_square,
                    ConstantSquare(
                        row=get_row_constant(int(from_square.row)), col=COL_C
                    ),
                )  # COL_C
            )

        return True

    def _validate_en_passant(
        self, piece: Piece, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Validate en passant capture."""
        if self.board.en_passant_target is None:
            return False

        target_square = self.board.en_passant_target

        # En passant capture lands on the same row as the en passant target
        if int(to_square.row) != int(target_square.row):
            return False

        # Must be capturing on the en passant square
        if to_square != target_square:
            return False

        return True

    def get_legal_moves(
        self,
        from_square: Optional[Square] = None,
        piece_type: Optional[PieceType] = None,
    ) -> List[Tuple[Square, Square, Optional[PieceType]]]:
        """Get all legal moves (with check validation).

        Returns:
            List of (from_square, to_square, promotion) tuples, or empty list if no moves.
        """
        all_moves = []

        if from_square is not None:
            piece = self.board.get_piece(from_square)
            if piece is None:
                return []

            for to_square in self.piece_movers.get_valid_moves(piece, self.board):
                if self.is_valid_move(from_square, to_square):
                    promotion = None
                    if piece.kind == PieceType.PAWN:
                        promotion = self._get_promotion_piece(piece, to_square)
                    all_moves.append((from_square, to_square, promotion))
        else:
            # Get all legal moves for the current turn
            for row in range(8):
                for col in range(8):
                    from_square = ConstantSquare(
                        row=get_row_constant(row), col=get_col_constant(col)
                    )
                    piece = self.board.get_piece(from_square)
                    if piece is not None:
                        for to_square in self.piece_movers.get_valid_moves(
                            piece, self.board
                        ):
                            if self.is_valid_move(from_square, to_square):
                                promotion = None
                                if piece.kind == PieceType.PAWN:
                                    promotion = self._get_promotion_piece(
                                        piece, to_square
                                    )
                                all_moves.append((from_square, to_square, promotion))

        return all_moves

    def _get_promotion_piece(
        self, piece: Piece, to_square: ConstantSquare
    ) -> Optional[PieceType]:
        """Get the promotion piece type if pawn promotion is needed."""
        if piece.kind != PieceType.PAWN:
            return None

        # White promotes at row 7, Black at row 0
        if piece.color == Color.WHITE and int(to_square.row) == 7:
            return PieceType.QUEEN
        if piece.color == Color.BLACK and int(to_square.row) == 0:
            return PieceType.QUEEN

        return None

    def _would_expose_king_to_check(
        self, piece: Piece, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Check if making the move would expose the piece's king to check.

        A piece is pinned if moving it would expose its king to attack by an enemy piece.
        """
        piece_color = piece.color
        enemy_color = Color.BLACK if piece_color == Color.WHITE else Color.WHITE

        # Create a temporary board state to simulate the move
        # Make a DEEP COPY of the board to avoid modifying the original
        import copy

        temp_board_board = [row[:] for row in self.board.board]
        temp_board = BoardState(
            board=temp_board_board,
            turn=self.board.turn,
            en_passant_target=self.board.en_passant_target,
            white_kingside=self.board.white_kingside,
            white_queenside=self.board.white_queenside,
            black_kingside=self.board.black_kingside,
            black_queenside=self.board.black_queenside,
        )

        # Copy all pieces from the current board (don't modify piece._square)
        for row in range(8):
            for col in range(8):
                square = ConstantSquare(
                    row=get_row_constant(row), col=get_col_constant(col)
                )
                original_piece = self.board.get_piece(square)
                if original_piece is not None:
                    # Create a copy of the piece to avoid modifying original
                    temp_piece = Piece(
                        color=original_piece.color,
                        kind=original_piece.kind,
                        _square=square,
                    )
                    temp_board.board[int(square.row)][int(square.col)] = temp_piece

        # Make the simulated move - use original piece with updated square
        temp_piece = Piece(
            color=piece.color,
            kind=piece.kind,
            _square=to_square,
        )
        temp_board.board[int(to_square.row)][int(to_square.col)] = temp_piece
        temp_board.board[int(from_square.row)][int(from_square.col)] = None

        # Find the king of this color
        king_square = temp_board.find_king(piece_color)
        if king_square is None:
            return False

        # Check if any enemy piece can attack the king
        for row in range(8):
            for col in range(8):
                sq = ConstantSquare(
                    row=get_row_constant(row), col=get_col_constant(col)
                )
                attacker = temp_board.get_piece(sq)
                if attacker is not None and attacker.color == enemy_color:
                    if self._can_piece_attack(attacker, sq, king_square, piece_color):
                        return True

        return False

    def is_piece_pinned(self, square: ConstantSquare, piece_color: Color) -> bool:
        """Check if a piece is pinned to its king.

        A piece is pinned if moving it would expose the king to check.
        """
        # Find the king of the given color
        king_square = self.board.find_king(piece_color)
        if king_square is None:
            return False

        # Check if there's a piece on a line between the pinned piece and king
        # that can attack the king
        enemy_color = Color.BLACK if piece_color == Color.WHITE else Color.WHITE

        # Get all attacking pieces from enemy
        for row in range(8):
            for col in range(8):
                sq = ConstantSquare(
                    row=get_row_constant(row), col=get_col_constant(col)
                )
                attacker = self.board.get_piece(sq)
                if attacker and attacker.color == enemy_color:
                    # Check if attacker can attack king through this square
                    if self._can_piece_attack(attacker, sq, king_square, piece_color):
                        # Check if the attack line goes through our square
                        if self._attack_line_goes_through(sq, king_square, square):
                            return True

        return False

    def _can_piece_attack(
        self,
        attacker: Piece,
        attacker_square: ConstantSquare,
        target_square: ConstantSquare,
        ignore_color: Color,
    ) -> bool:
        """Check if attacker can attack target (used for pin detection)."""
        # Check different piece types
        if attacker.kind == PieceType.ROOK:
            return self._is_rook_attack(attacker_square, target_square, ignore_color)
        elif attacker.kind == PieceType.BISHOP:
            return self._is_bishop_attack(attacker_square, target_square, ignore_color)
        elif attacker.kind == PieceType.QUEEN:
            return self._is_queen_attack(attacker_square, target_square, ignore_color)
        elif attacker.kind == PieceType.KNIGHT:
            return self._is_knight_attack(attacker_square, target_square)
        elif attacker.kind == PieceType.KING:
            return self._is_king_attack(attacker_square, target_square)
        return False

    def _is_rook_attack(
        self,
        from_sq: ConstantSquare,
        to_sq: ConstantSquare,
        ignore_color: Color,
    ) -> bool:
        """Check if rook can attack from from_sq to to_sq."""
        if int(from_sq.row) != int(to_sq.row) and int(from_sq.col) != int(to_sq.col):
            return False

        return self.path_validator.is_path_clear(
            self.board, from_sq, to_sq, ignore_color
        )

    def _is_bishop_attack(
        self, from_sq: ConstantSquare, to_sq: ConstantSquare, ignore_color: Color
    ) -> bool:
        """Check if bishop can attack from from_sq to to_sq."""
        row_diff = abs(int(from_sq.row) - int(to_sq.row))
        col_diff = abs(int(from_sq.col) - int(to_sq.col))

        if row_diff != col_diff:
            return False

        return self.path_validator.is_path_clear(
            self.board, from_sq, to_sq, ignore_color
        )

    def _is_queen_attack(
        self, from_sq: ConstantSquare, to_sq: ConstantSquare, ignore_color: Color
    ) -> bool:
        """Check if queen can attack from from_sq to to_sq."""
        if int(from_sq.row) == int(to_sq.row) or int(from_sq.col) == int(to_sq.col):
            return self.path_validator.is_path_clear(
                self.board, from_sq, to_sq, ignore_color
            )
        return self._is_bishop_attack(from_sq, to_sq, ignore_color)

    def _is_knight_attack(self, from_sq: ConstantSquare, to_sq: ConstantSquare) -> bool:
        """Check if knight can attack from from_sq to to_sq."""
        row_diff = abs(int(from_sq.row) - int(to_sq.row))
        col_diff = abs(int(from_sq.col) - int(to_sq.col))
        return (row_diff == 2 and col_diff == 1) or (row_diff == 1 and col_diff == 2)

    def _is_king_attack(self, from_sq: ConstantSquare, to_sq: ConstantSquare) -> bool:
        """Check if king can attack from from_sq to to_sq."""
        return (
            abs(int(from_sq.row) - int(to_sq.row)) <= 1
            and abs(int(from_sq.col) - int(to_sq.col)) <= 1
        )

    def _attack_line_goes_through(
        self,
        attacker_sq: ConstantSquare,
        target_sq: ConstantSquare,
        check_sq: ConstantSquare,
    ) -> bool:
        """Check if the attack line from attacker to target goes through check_sq."""
        # For rook/queen on same row
        if int(attacker_sq.row) == int(target_sq.row):
            return int(check_sq.row) == int(attacker_sq.row) and (
                int(check_sq.col) > min(int(attacker_sq.col), int(target_sq.col))
                and int(check_sq.col) < max(int(attacker_sq.col), int(target_sq.col))
            )

        # For rook/queen on same column
        if int(attacker_sq.col) == int(target_sq.col):
            return int(check_sq.col) == int(attacker_sq.col) and (
                int(check_sq.row) > min(int(attacker_sq.row), int(target_sq.row))
                and int(check_sq.row) < max(int(attacker_sq.row), int(target_sq.row))
            )

        # For bishop on diagonal
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
