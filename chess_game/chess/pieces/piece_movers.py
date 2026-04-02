"""Piece-specific move validation logic."""

from __future__ import annotations

from typing import List, Optional

from chess_game.chess.color import Color
from chess_game.chess.constants import ROW_1, ROW_8, get_row_constant, get_col_constant
from chess_game.chess.pieces.piece import Piece, PieceType, ConstantSquare


class PieceMovers:
    """Contains move validation logic for each piece type."""

    @staticmethod
    def get_valid_moves(piece: Piece, board) -> List[ConstantSquare]:
        """Get all valid moves for a piece."""
        if piece.kind == PieceType.PAWN:
            return PieceMovers._get_pawn_moves(piece, board)
        elif piece.kind == PieceType.KNIGHT:
            return PieceMovers._get_knight_moves(piece, board)
        elif piece.kind == PieceType.BISHOP:
            return PieceMovers._get_bishop_moves(piece, board)
        elif piece.kind == PieceType.ROOK:
            return PieceMovers._get_rook_moves(piece, board)
        elif piece.kind == PieceType.QUEEN:
            return PieceMovers._get_queen_moves(piece, board)
        elif piece.kind == PieceType.KING:
            return PieceMovers._get_king_moves(piece, board)
        return []

    @staticmethod
    def _get_pawn_moves(piece: Piece, board) -> List[ConstantSquare]:
        """Get all valid pawn moves (forward, capture, 2-step)."""
        moves = []
        direction = 1 if piece.color == Color.WHITE else -1
        start_row = ROW_1 if piece.color == Color.WHITE else ROW_8

        current_row = int(piece.square.row)
        current_col = get_col_constant(int(piece.square.col))

        # Forward 1 square
        next_row = get_row_constant(current_row + direction)
        target_square = ConstantSquare(row=next_row, col=current_col)
        if PieceMovers._is_valid_position(board, target_square):
            if board.is_empty(target_square):
                moves.append(target_square)

        # Forward 2 squares (only on first move)
        if current_row == int(start_row):
            target_row_2 = get_row_constant(current_row + 2 * direction)
            target_square_2 = ConstantSquare(row=target_row_2, col=current_col)
            if PieceMovers._is_valid_position(board, target_square_2):
                square_between = ConstantSquare(row=next_row, col=current_col)
                if board.is_empty(square_between) and board.is_empty(target_square_2):
                    moves.append(target_square_2)

        # Captures
        for col_offset in [-1, 1]:
            target_col_idx = int(current_col) + col_offset

            # Check bounds before creating ConstantSquare
            if not (0 <= target_col_idx < 8):
                continue

            target_col = get_col_constant(target_col_idx)
            target_square = ConstantSquare(row=next_row, col=target_col)

            if PieceMovers._is_valid_position(board, target_square):
                target_piece = board.get_piece(target_square)
                if target_piece is not None and target_piece.color != piece.color:
                    moves.append(target_square)

        return moves

    @staticmethod
    def _is_valid_position(board, square: ConstantSquare) -> bool:
        """Check if a square is on the board."""
        return 0 <= int(square.row) < 8 and 0 <= int(square.col) < 8

    @staticmethod
    def _get_knight_moves(piece: Piece, board) -> List[ConstantSquare]:
        """Get all valid knight moves (L-shaped)."""
        moves = []
        row_offsets = [-2, -1, 1, 2]
        col_offsets = [-2, -1, 1, 2]

        for row_offset, col_offset in [
            (ro, co) for ro in row_offsets for co in col_offsets
        ]:
            if row_offset * col_offset == 0:  # Skip adjacent squares
                continue

            target_row = int(piece.square.row) + row_offset
            target_col = int(piece.square.col) + col_offset

            # Check bounds before converting to ConstantSquare
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
    def _piece_attacks_square(
        piece: Piece, from_square: ConstantSquare, to_square: ConstantSquare
    ) -> bool:
        """Check if a piece attacks a target square."""
        row_diff = to_square.row - from_square.row
        col_diff = to_square.col - from_square.col

        if piece.kind == PieceType.PAWN:
            direction = 1 if piece.color == Color.WHITE else -1
            return row_diff == direction and abs(col_diff) == 1

        if piece.kind == PieceType.KNIGHT:
            return (abs(row_diff), abs(col_diff)) in {(2, 1), (1, 2)}

        if piece.kind == PieceType.BISHOP:
            if abs(row_diff) != abs(col_diff):
                return False
            # Check path is clear
            if from_square.row == to_square.row or from_square.col == to_square.col:
                return False
            return PieceMovers._path_is_clear(from_square, to_square, piece)

        if piece.kind == PieceType.ROOK:
            if from_square.row != to_square.row and from_square.col != to_square.col:
                return False
            return PieceMovers._path_is_clear(from_square, to_square, piece)

        if piece.kind == PieceType.QUEEN:
            if from_square.row != to_square.row and from_square.col != to_square.col:
                return False
            if abs(row_diff) != abs(col_diff):
                return False
            return PieceMovers._path_is_clear(from_square, to_square, piece)

        if piece.kind == PieceType.KING:
            return from_square != to_square and max(abs(row_diff), abs(col_diff)) == 1

        return False

    @staticmethod
    def _path_is_clear(
        from_square: ConstantSquare, to_square: ConstantSquare, board
    ) -> bool:
        """Check if path between two squares is clear."""
        if from_square == to_square:
            return True

        row_diff = to_square.row - from_square.row
        col_diff = to_square.col - from_square.col

        step_row = 0 if row_diff == 0 else (1 if row_diff > 0 else -1)
        step_col = 0 if col_diff == 0 else (1 if col_diff > 0 else -1)

        current_row = int(from_square.row) + step_row
        current_col = int(from_square.col) + step_col

        while (current_row, current_col) != (int(to_square.row), int(to_square.col)):
            if board.get_piece(ConstantSquare(current_row, current_col)) is not None:
                return False
            current_row += step_row
            current_col += step_col

        return True

    @staticmethod
    def _get_queen_moves(piece: Piece, board) -> List[ConstantSquare]:
        """Get all valid queen moves (rook + bishop combined)."""
        rook_moves = PieceMovers._get_rook_moves(piece, board)
        bishop_moves = PieceMovers._get_bishop_moves(piece, board)
        return rook_moves + bishop_moves

    @staticmethod
    def _get_king_moves(piece: Piece, board) -> List[ConstantSquare]:
        """Get all valid king moves (one square in any direction plus castling)."""
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

            # Check bounds before converting to ConstantSquare
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

        # Add castling moves
        if piece.kind == PieceType.KING:
            color = piece.color
            king_row = int(piece.square.row)

            # Kingside castling (e1 -> g1 for white, e8 -> g8 for black)
            if (color == Color.WHITE and board.white_kingside) or (
                color == Color.BLACK and board.black_kingside
            ):
                # Check if rook is at original position
                rook_at_h1 = board.get_piece(
                    ConstantSquare(
                        row=get_row_constant(king_row),
                        col=get_col_constant(7),  # h file
                    )
                )
                rook_ok = (
                    rook_at_h1 is not None
                    and rook_at_h1.kind == PieceType.ROOK
                    and rook_at_h1.color == color
                )

                # Check path is clear (f file)
                f1_square = ConstantSquare(
                    row=get_row_constant(king_row),
                    col=get_col_constant(5),  # f file
                )
                path_clear = board.is_empty(f1_square)

                # Check king safety
                king_path_safe = True
                enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
                for sq in [
                    ConstantSquare(
                        row=get_row_constant(king_row),
                        col=get_col_constant(4),  # e file
                    ),
                    ConstantSquare(
                        row=get_row_constant(king_row),
                        col=get_col_constant(5),  # f file
                    ),
                    ConstantSquare(
                        row=get_row_constant(king_row),
                        col=get_col_constant(6),  # g file
                    ),
                ]:
                    # Check if attacked by enemy
                    for row in range(8):
                        for col in range(8):
                            attacker = board.get_piece(
                                ConstantSquare(
                                    row=get_row_constant(row), col=get_col_constant(col)
                                )
                            )
                            if (
                                attacker
                                and attacker.color == enemy_color
                                and PieceMovers._piece_attacks_square(
                                    attacker,
                                    ConstantSquare(
                                        row=get_row_constant(row),
                                        col=get_col_constant(col),
                                    ),
                                    sq,
                                )
                            ):
                                king_path_safe = False
                                break
                        if not king_path_safe:
                            break

                if rook_ok and path_clear and king_path_safe:
                    moves.append(
                        ConstantSquare(
                            row=get_row_constant(king_row),
                            col=get_col_constant(6),  # g file
                        )
                    )

            # Queenside castling (e1 -> c1 for white, e8 -> c8 for black)
            if (color == Color.WHITE and board.white_queenside) or (
                color == Color.BLACK and board.black_queenside
            ):
                # Check if rook is at original position
                rook_at_a1 = board.get_piece(
                    ConstantSquare(
                        row=get_row_constant(king_row),
                        col=get_col_constant(0),  # a file
                    )
                )
                rook_ok = (
                    rook_at_a1 is not None
                    and rook_at_a1.kind == PieceType.ROOK
                    and rook_at_a1.color == color
                )

                # Check path is clear (d and c files)
                d1_square = ConstantSquare(
                    row=get_row_constant(king_row),
                    col=get_col_constant(3),  # d file
                )
                c1_square = ConstantSquare(
                    row=get_row_constant(king_row),
                    col=get_col_constant(2),  # c file
                )
                path_clear = board.is_empty(d1_square) and board.is_empty(c1_square)

                # Check king safety
                king_path_safe = True
                enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
                for sq in [
                    ConstantSquare(
                        row=get_row_constant(king_row),
                        col=get_col_constant(4),  # e file
                    ),
                    ConstantSquare(
                        row=get_row_constant(king_row),
                        col=get_col_constant(3),  # d file
                    ),
                    ConstantSquare(
                        row=get_row_constant(king_row),
                        col=get_col_constant(2),  # c file
                    ),
                ]:
                    # Check if attacked by enemy
                    for row in range(8):
                        for col in range(8):
                            attacker = board.get_piece(
                                ConstantSquare(
                                    row=get_row_constant(row), col=get_col_constant(col)
                                )
                            )
                            if (
                                attacker
                                and attacker.color == enemy_color
                                and PieceMovers._piece_attacks_square(
                                    attacker,
                                    ConstantSquare(
                                        row=get_row_constant(row),
                                        col=get_col_constant(col),
                                    ),
                                    sq,
                                )
                            ):
                                king_path_safe = False
                                break
                        if not king_path_safe:
                            break

                if rook_ok and path_clear and king_path_safe:
                    moves.append(
                        ConstantSquare(
                            row=get_row_constant(king_row),
                            col=get_col_constant(2),  # c file
                        )
                    )

        return moves
