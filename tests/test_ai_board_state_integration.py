"""Integration tests for board state transitions: castling rights and en-passant targets."""

from chess_game.chess.ai import get_best_move
from chess_game.chess.board import Board
from chess_game.chess.board.board import create_piece
from chess_game.chess.constants import Color, PieceType
from chess_game.chess.coords import algebraic_to_index


def _clear_board(board: Board) -> None:
    for row in range(8):
        for col in range(8):
            board.clear_square((row, col))


def _place_minimal_kings(board: Board) -> None:
    _clear_board(board)
    board.set_piece(algebraic_to_index("e1"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(algebraic_to_index("e8"), create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.WHITE
    board.castling_rights.white_kingside = True
    board.castling_rights.white_queenside = True
    board.castling_rights.black_kingside = True
    board.castling_rights.black_queenside = True
    board.en_passant_target = None


class TestCastlingRightsSensitiveAIChoice:
    """Test that AI-selected moves leave castling metadata consistent."""

    def test_ai_move_keeps_castling_rights_valid(self):
        """Verify AI-selected move updates state with valid castling rights."""
        board = Board()
        best_move = get_best_move(board, depth=1)
        assert best_move is not None

        assert board.make_move(best_move.start, best_move.end, best_move.promotion)
        assert board.turn == Color.BLACK
        assert isinstance(board.castling_rights.white_kingside, bool)
        assert isinstance(board.castling_rights.white_queenside, bool)
        assert isinstance(board.castling_rights.black_kingside, bool)
        assert isinstance(board.castling_rights.black_queenside, bool)

    def test_king_move_clears_both_white_castling_rights(self):
        """Verify that moving the king revokes both white castling rights."""
        board = Board()
        _place_minimal_kings(board)

        assert board.make_move(
            algebraic_to_index("e1"),
            algebraic_to_index("e2"),
        )

        assert board.turn == Color.BLACK
        assert board.castling_rights.white_kingside is False
        assert board.castling_rights.white_queenside is False

    def test_rook_move_clears_kingside_right_only(self):
        """Verify that moving the rook revokes only the relevant side."""
        board = Board()
        _place_minimal_kings(board)
        board.set_piece(algebraic_to_index("h1"), create_piece(Color.WHITE, PieceType.ROOK))

        assert board.make_move(
            algebraic_to_index("h1"),
            algebraic_to_index("h2"),
        )

        assert board.turn == Color.BLACK
        assert board.castling_rights.white_kingside is False
        assert board.castling_rights.white_queenside is True


class TestEnPassantSensitiveAIChoice:
    """Test that AI and board state respect en-passant metadata."""

    def test_pawn_double_push_sets_en_passant_target(self):
        """Verify that double-pushing a pawn sets the en-passant target."""
        board = Board()

        assert board.make_move(algebraic_to_index("e2"), algebraic_to_index("e4"))
        assert board.en_passant_target == algebraic_to_index("e3")
        assert board.turn == Color.BLACK

    def test_en_passant_target_clears_after_reply(self):
        """Verify that the en-passant target clears after the next move."""
        board = Board()

        assert board.make_move(algebraic_to_index("e2"), algebraic_to_index("e4"))
        assert board.en_passant_target == algebraic_to_index("e3")

        assert board.make_move(algebraic_to_index("a7"), algebraic_to_index("a6"))
        assert board.turn == Color.WHITE
        assert board.en_passant_target is None


class TestBoardMetadataIntegrityAfterAIMove:
    """Test that board metadata remains consistent after AI-selected moves."""

    def test_side_to_move_alternates(self):
        """Verify that side to move changes after an AI move."""
        board = Board()
        initial_turn = board.turn

        best_move = get_best_move(board, depth=2)
        assert best_move is not None
        assert board.make_move(best_move.start, best_move.end, best_move.promotion)
        assert board.turn != initial_turn

    def test_castling_rights_remain_valid_bool_fields(self):
        """Verify castling rights stay as boolean metadata."""
        board = Board()
        best_move = get_best_move(board, depth=2)
        assert best_move is not None

        assert board.make_move(best_move.start, best_move.end, best_move.promotion)
        assert isinstance(board.castling_rights.white_kingside, bool)
        assert isinstance(board.castling_rights.white_queenside, bool)
        assert isinstance(board.castling_rights.black_kingside, bool)
        assert isinstance(board.castling_rights.black_queenside, bool)

    def test_en_passant_target_valid_or_none(self):
        """Verify en-passant target is either None or a valid square."""
        board = Board()
        best_move = get_best_move(board, depth=2)
        assert best_move is not None

        assert board.make_move(best_move.start, best_move.end, best_move.promotion)
        ep = board.en_passant_target
        assert ep is None or (0 <= int(ep.row) < 8 and 0 <= int(ep.col) < 8)


class TestMultipleMovesPreserveIntegrity:
    """Test that board state remains consistent over multiple moves."""

    def test_three_move_sequence_preserves_board_state(self):
        """Verify board integrity across three AI moves."""
        board = Board()

        for _ in range(3):
            best_move = get_best_move(board, depth=1)
            if best_move is None:
                break
            assert board.make_move(best_move.start, best_move.end, best_move.promotion)
            assert board.turn in (Color.WHITE, Color.BLACK)
            assert isinstance(board.castling_rights.white_kingside, bool)
            assert isinstance(board.castling_rights.white_queenside, bool)
            assert isinstance(board.castling_rights.black_kingside, bool)
            assert isinstance(board.castling_rights.black_queenside, bool)
            ep = board.en_passant_target
            assert ep is None or (0 <= int(ep.row) < 8 and 0 <= int(ep.col) < 8)

    def test_move_sequence_obeys_turn_order(self):
        """Verify alternating turn order across moves."""
        board = Board()

        for expected_turn in (Color.WHITE, Color.BLACK, Color.WHITE, Color.BLACK):
            assert board.turn == expected_turn
            best_move = get_best_move(board, depth=1)
            if best_move is None:
                break
            assert board.make_move(best_move.start, best_move.end, best_move.promotion)
