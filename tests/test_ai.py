"""Tests for AI evaluation symmetry and correctness."""


from chess_game.chess.ai import evaluate
from chess_game.chess.board import Board
from chess_game.chess.constants import Color
from chess_game.chess.types import Piece, PieceType
from tests.helpers import sq


def _create_piece(color: Color, kind: PieceType) -> Piece:
    return Piece(color=color, kind=kind)


class TestEvaluationSymmetry:
    """Tests that the evaluator is symmetric: evaluate(board) == -evaluate(mirrored_board)."""

    def test_starting_position_evaluates_to_zero(self) -> None:
        """The standard starting position should evaluate to 0."""
        board = Board()
        assert evaluate(board) == 0

    def test_mirrored_starting_position_is_zero(self) -> None:
        """Flipping the starting position should also evaluate to 0."""
        board = Board()
        mirrored = _mirror_board(board)
        assert evaluate(mirrored) == 0

    def test_symmetry_single_white_pawn(self) -> None:
        """A single white pawn evaluates positively."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e5"), _create_piece(Color.WHITE, PieceType.PAWN))
        score = evaluate(board)
        assert score > 0

    def test_symmetry_single_black_pawn(self) -> None:
        """A single black pawn evaluates negatively."""
        board = Board()
        board.clear_board()
        board.set_piece(sq("e4"), _create_piece(Color.BLACK, PieceType.PAWN))
        score = evaluate(board)
        assert score < 0

    def test_symmetry_white_pawn_negates_black_pawn(self) -> None:
        """Score of white pawn == -(score of black pawn at mirrored square)."""
        board_w = Board()
        board_w.clear_board()
        board_w.set_piece(sq("e5"), _create_piece(Color.WHITE, PieceType.PAWN))

        board_b = Board()
        board_b.clear_board()
        board_b.set_piece(sq("e4"), _create_piece(Color.BLACK, PieceType.PAWN))

        assert evaluate(board_w) == -evaluate(board_b)

    def test_symmetry_full_mirror(self) -> None:
        """evaluate(board) == -evaluate(mirrored_board) for arbitrary positions."""
        board = Board()
        board.clear_board()
        # White queen on d4, white rook on a1
        board.set_piece(sq("d4"), _create_piece(Color.WHITE, PieceType.QUEEN))
        board.set_piece(sq("a1"), _create_piece(Color.WHITE, PieceType.ROOK))
        # Black knight on f5
        board.set_piece(sq("f5"), _create_piece(Color.BLACK, PieceType.KNIGHT))

        mirrored = _mirror_board(board)
        assert evaluate(board) == -evaluate(mirrored)

    def test_symmetry_complex_position(self) -> None:
        """Symmetry holds for a position with all piece types."""
        board = Board()
        board.clear_board()
        pieces = [
            (Color.WHITE, PieceType.KING, "e1"),
            (Color.WHITE, PieceType.QUEEN, "d2"),
            (Color.WHITE, PieceType.ROOK, "a1"),
            (Color.WHITE, PieceType.BISHOP, "c3"),
            (Color.WHITE, PieceType.KNIGHT, "f4"),
            (Color.WHITE, PieceType.PAWN, "e6"),
            (Color.BLACK, PieceType.KING, "d8"),
            (Color.BLACK, PieceType.QUEEN, "e7"),
            (Color.BLACK, PieceType.ROOK, "h8"),
            (Color.BLACK, PieceType.BISHOP, "f6"),
            (Color.BLACK, PieceType.KNIGHT, "c5"),
            (Color.BLACK, PieceType.PAWN, "d3"),
        ]
        for color, kind, square in pieces:
            board.set_piece(sq(square), _create_piece(color, kind))

        mirrored = _mirror_board(board)
        assert evaluate(board) == -evaluate(mirrored)

    def test_simulations_do_not_mutate_original_board(self) -> None:
        """AI minimax must not mutate the original board."""
        from chess_game.chess.ai import get_best_move

        board = Board()
        original = board.clone()

        get_best_move(board, depth=1)

        for row in range(8):
            for col in range(8):
                orig_piece = original.board[row][col]
                curr_piece = board.board[row][col]
                assert (orig_piece is None) == (curr_piece is None)
                if orig_piece is not None and curr_piece is not None:
                    assert orig_piece.color == curr_piece.color
                    assert orig_piece.kind == curr_piece.kind
        assert board.turn == original.turn
        assert board.castling_rights.white_kingside == original.castling_rights.white_kingside
        assert board.castling_rights.white_queenside == original.castling_rights.white_queenside
        assert board.castling_rights.black_kingside == original.castling_rights.black_kingside
        assert board.castling_rights.black_queenside == original.castling_rights.black_queenside
        assert board.en_passant_target == original.en_passant_target


def _mirror_board(board: Board) -> Board:
    """Create a mirrored board: swap colors, flip rows (row -> 7-row)."""
    mirrored = Board()
    mirrored.clear_board()

    for row in range(8):
        for col in range(8):
            square_name = f"{chr(ord('a') + col)}{8 - row}"
            piece = board.get_piece(sq(square_name))
            if piece is not None:
                mirrored_color = (
                    Color.BLACK if piece.color == Color.WHITE else Color.WHITE
                )
                mirrored_piece = _create_piece(mirrored_color, piece.kind)
                mirrored.set_piece(
                    sq(f"{chr(ord('a') + col)}{1 + row}"),
                    mirrored_piece,
                )

    return mirrored
