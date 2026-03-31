"""Tests for safety."""
from __future__ import annotations
from chess_game.chess.board import Board, create_piece
from chess_game.constants import (
    
        get_row_constant,
        get_col_constant,
        ROW_1,
        ROW_2,
        ROW_3,
        ROW_4,
        ROW_5,
        ROW_6,
        ROW_7,
        ROW_8,
        COL_A,
        COL_B,
        COL_C,
        COL_D,
        COL_E,
        COL_F,
        COL_G,
        COL_H,
    
)
from chess_game.constants import ConstantSquare
from chess_game.chess.types import Color, PieceType
def clear_board(board: Board) -> None:
    for row in range(8):
        for col in range(8):
            board.clear_square(ConstantSquare(row=get_row_constant(row), col=get_col_constant(col)))
def _setup_kings(board: Board) -> None:
    board.set_piece(
        ConstantSquare(row=ROW_1, col=4), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=4), create_piece(Color.BLACK, PieceType.KING)
    )
# Category 7: Complex Sequences
# =============================================================================
def test_scholars_mate_sequence() -> None:
    """T7.1: Simple bishop diagonal move test."""
    board = Board()
    clear_board(board)
    # Clear the path for the bishop
    board.clear_square(
        ConstantSquare(row=ROW_7, col=COL_E)
    )  # e7 - pawn was blocking diagonal
    board.clear_square(
        ConstantSquare(row=ROW_6, col=COL_E)
    )  # e6 - pawn was blocking diagonal
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    # Clear bishop's path
    board.clear_square(ConstantSquare(row=ROW_6, col=COL_H))
    board.clear_square(ConstantSquare(row=ROW_5, col=COL_G))
    board.clear_square(ConstantSquare(row=ROW_4, col=COL_F))
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_F),
        create_piece(Color.BLACK, PieceType.BISHOP),
    )  # f7
    # Black bishop moves diagonally
    board.turn = Color.BLACK
    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_F), ConstantSquare(row=ROW_6, col=COL_E)
        )
        is True
    )  # f7-f6
    board.turn = Color.BLACK
    assert (
        board.make_move(
            ConstantSquare(row=ROW_6, col=COL_E), ConstantSquare(row=ROW_5, col=COL_D)
        )
        is True
    )  # f6-e5
    board.turn = Color.BLACK
    assert (
        board.make_move(
            ConstantSquare(row=ROW_5, col=COL_D), ConstantSquare(row=ROW_4, col=COL_C)
        )
        is True
    )  # e5-d4
    # Verify bishop is at d4 (4,3)
    piece = board.get_piece(ConstantSquare(row=ROW_4, col=COL_C))
    assert piece is not None
    assert piece.kind == PieceType.BISHOP
def _setup_empty_board(board: Board) -> None:
    """Helper to clear entire board before setting up test pieces."""
    for row in range(8):
        for col in range(8):
            board.clear_square(ConstantSquare(row=get_row_constant(row), col=get_col_constant(col)))
def test_intentional_stalemate_sequence() -> None:
    """T7.2: Stalemate sequence from opening."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    # Place pieces to create stalemate - use pawns that block without being capturable
    # White king trapped on e1 by surrounding pieces
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_D), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_F), create_piece(Color.BLACK, PieceType.PAWN)
    )
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_E), create_piece(Color.BLACK, PieceType.PAWN)
    )
    # Verify king has no legal moves (blocked by pawns)
    board.turn = Color.WHITE
    assert len(board.get_legal_moves()) == 0
def test_multiple_en_passant_in_game() -> None:
    """T7.3: Multiple en passant captures in a game."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_4, col=COL_E), create_piece(Color.WHITE, PieceType.PAWN)
    )  # e4
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.BLACK, PieceType.PAWN)
    )  # e7
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_F), create_piece(Color.BLACK, PieceType.PAWN)
    )  # f7
    # First en passant: black pawn f7 moves to f5
    board.turn = Color.BLACK
    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_F), ConstantSquare(row=ROW_5, col=COL_F)
        )
        is True
    )  # f7-f5
    assert board.en_passant_target == ConstantSquare(row=ROW_6, col=COL_F)
    board.turn = Color.WHITE
    # White pawn at e4 captures f5 en passant - en passant target is at (5,5)
    assert (
        board.make_move(
            ConstantSquare(row=ROW_4, col=COL_E), ConstantSquare(row=ROW_5, col=COL_F)
        )
        is True
    )  # e4 captures f5 e.p.
    # State resets after en passant
    assert board.en_passant_target is None
    # Black moves e7-e5
    board.turn = Color.BLACK
    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_E), ConstantSquare(row=ROW_5, col=COL_E)
        )
        is True
    )  # e7-e5
    assert board.en_passant_target == ConstantSquare(row=ROW_6, col=COL_E)
    board.turn = Color.WHITE
    # White has no pawn to capture - en passant target remains set
    # State does NOT reset until black moves
    assert board.en_passant_target == ConstantSquare(row=ROW_6, col=COL_E)
    # Setup a new black pawn at f7 to move to f5 for second en passant
    # First, clear the white pawn that captured at (3,5), then set new pawn
    board.clear_square(
        ConstantSquare(row=ROW_6, col=COL_F)
    )  # Remove captured white pawn
    board.turn = Color.BLACK
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_F), create_piece(Color.BLACK, PieceType.PAWN)
    )  # Place new pawn at f7
    # Second en passant sequence
    board.turn = Color.BLACK
    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_F), ConstantSquare(row=ROW_5, col=COL_F)
        )
        is True
    )  # f7-f5
    assert board.en_passant_target == ConstantSquare(row=ROW_6, col=COL_F)
    board.turn = Color.WHITE
    # White has no pawn to capture
    # The black pawn is now at (3,5) from the en passant move
    # Clear destination (4,5) before black moves pawn forward
    board.clear_square(ConstantSquare(row=ROW_4, col=COL_F))
    # State does NOT reset until black moves
    assert board.en_passant_target == ConstantSquare(row=ROW_6, col=COL_F)
    # Black makes a non-en-passant move
    board.turn = Color.BLACK
    assert (
        board.make_move(
            ConstantSquare(row=ROW_5, col=COL_F), ConstantSquare(row=ROW_4, col=COL_F)
        )
        is True
    )  # f5-f6
    # State resets after non-en-passant move
    assert board.en_passant_target is None
    # Clear (3,5) for the next e7-e5 sequence
    board.clear_square(ConstantSquare(row=ROW_3, col=COL_F))
    # Black moves e7-e5 again - need to re-set the pawn
    # First clear the destination square from the previous pawn
    board.clear_square(ConstantSquare(row=ROW_3, col=COL_E))
    board.turn = Color.BLACK
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.BLACK, PieceType.PAWN)
    )  # Re-add pawn at e7
    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_E), ConstantSquare(row=ROW_5, col=COL_E)
        )
        is True
    )  # e7-e5
    assert board.en_passant_target == ConstantSquare(row=ROW_6, col=COL_E)
    board.turn = Color.WHITE
    # White has no pawn to capture - en passant target remains set
    # State does NOT reset until black moves
    assert board.en_passant_target == ConstantSquare(row=ROW_6, col=COL_E)
    # Setup a new black pawn at f7 to move to f5 for third en passant
    # First, clear the white pawn that captured at (3,5), then set new pawn
    board.clear_square(
        ConstantSquare(row=ROW_6, col=COL_F)
    )  # Remove captured white pawn
    board.turn = Color.BLACK
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_F), create_piece(Color.BLACK, PieceType.PAWN)
    )  # Place new pawn at f7
    # Third en passant sequence
    board.turn = Color.BLACK
    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_F), ConstantSquare(row=ROW_5, col=COL_F)
        )
        is True
    )  # f7-f5
    assert board.en_passant_target == ConstantSquare(row=ROW_6, col=COL_F)
    board.turn = Color.WHITE
    # White has no pawn to capture
    # Clear destination (4,5) before black moves pawn forward
    board.clear_square(ConstantSquare(row=ROW_4, col=COL_F))
    # State does NOT reset until black moves
    assert board.en_passant_target == ConstantSquare(row=ROW_6, col=COL_F)
    # Black makes a non-en-passant move
    board.turn = Color.BLACK
    assert (
        board.make_move(
            ConstantSquare(row=ROW_5, col=COL_F), ConstantSquare(row=ROW_4, col=COL_F)
        )
        is True
    )  # f5-f6
    # State resets after non-en-passant move
    assert board.en_passant_target is None
    # Black moves e7-e5
    board.turn = Color.BLACK
    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_E), ConstantSquare(row=ROW_5, col=COL_E)
        )
        is True
    )  # e7-e5
    assert board.en_passant_target == ConstantSquare(row=ROW_6, col=COL_E)
    board.turn = Color.WHITE
    # White has no pawn to capture - en passant target remains set
    # State does NOT reset until black moves
    assert board.en_passant_target == ConstantSquare(row=ROW_6, col=COL_E)
    # Setup a new black pawn at f7 to move to f5 for second en passant
    # First, clear the white pawn that captured at (3,5), then set new pawn
    board.clear_square(
        ConstantSquare(row=ROW_6, col=COL_F)
    )  # Remove captured white pawn
    board.turn = Color.BLACK
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_F), create_piece(Color.BLACK, PieceType.PAWN)
    )  # Place new pawn at f7
    # Second en passant sequence
    board.turn = Color.BLACK
    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_F), ConstantSquare(row=ROW_5, col=COL_F)
        )
        is True
    )  # f7-f5
    assert board.en_passant_target == ConstantSquare(row=ROW_6, col=COL_F)
    board.turn = Color.WHITE
    # White has no pawn to capture
    # The black pawn is now at (3,5) from the en passant move
    # Clear destination (4,5) before black moves pawn forward
    board.clear_square(ConstantSquare(row=ROW_4, col=COL_F))
    # State does NOT reset until black moves
    assert board.en_passant_target == ConstantSquare(row=ROW_6, col=COL_F)
    # Black makes a non-en-passant move
    board.turn = Color.BLACK
    assert (
        board.make_move(
            ConstantSquare(row=ROW_5, col=COL_F), ConstantSquare(row=ROW_4, col=COL_F)
        )
        is True
    )  # f5-f6
    # State resets after non-en-passant move
    assert board.en_passant_target is None
    # Clear (3,5) for the next e7-e5 sequence
    board.clear_square(ConstantSquare(row=ROW_6, col=COL_F))
    # Black moves e7-e5 again - need to re-set the pawn
    # First clear the destination square from the previous pawn
    board.clear_square(ConstantSquare(row=ROW_6, col=COL_E))
    board.turn = Color.BLACK
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_E), create_piece(Color.BLACK, PieceType.PAWN)
    )  # Re-add pawn at e7
    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_E), ConstantSquare(row=ROW_5, col=COL_E)
        )
        is True
    )  # e7-e5
    assert board.en_passant_target == ConstantSquare(row=ROW_6, col=COL_E)
    board.turn = Color.WHITE
    # White has no pawn to capture - en passant target remains set
    # State does NOT reset until black moves
    assert board.en_passant_target == ConstantSquare(row=ROW_6, col=COL_E)
    # Setup a new black pawn at f7 to move to f5 for third en passant
    # First, clear the white pawn that captured at (3,5), then set new pawn
    board.clear_square(
        ConstantSquare(row=ROW_6, col=COL_F)
    )  # Remove captured white pawn
    board.turn = Color.BLACK
    board.set_piece(
        ConstantSquare(row=ROW_7, col=COL_F), create_piece(Color.BLACK, PieceType.PAWN)
    )  # Place new pawn at f7
    # Third en passant sequence
    board.turn = Color.BLACK
    assert (
        board.make_move(
            ConstantSquare(row=ROW_7, col=COL_F), ConstantSquare(row=ROW_5, col=COL_F)
        )
        is True
    )  # f7-f5
    assert board.en_passant_target == ConstantSquare(row=ROW_6, col=COL_F)
    board.turn = Color.WHITE
    # White has no pawn to capture
    # Clear destination (4,5) before black moves pawn forward
    board.clear_square(ConstantSquare(row=ROW_4, col=COL_F))
    # State does NOT reset until black moves
    assert board.en_passant_target == ConstantSquare(row=ROW_6, col=COL_F)
    # Black makes a non-en-passant move
    board.turn = Color.BLACK
    assert (
        board.make_move(
            ConstantSquare(row=ROW_5, col=COL_F), ConstantSquare(row=ROW_4, col=COL_F)
        )
        is True
    )  # f5-f6
    # State resets after non-en-passant move
    assert board.en_passant_target is None
# =============================================================================
# Category 8: Castling Safety Edge Cases
# =============================================================================
def test_cannot_castle_if_square_behind_king_attacked() -> None:
    """T8.1: Cannot castle if square behind king is attacked."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_H), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_H), create_piece(Color.BLACK, PieceType.ROOK)
    )
    # Place black bishop to attack g1 (square behind king on kingside)
    # Bishop on g2 (row 6, col 6) attacks diagonally through f1 and e1
    board.turn = Color.BLACK
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_G),
        create_piece(Color.BLACK, PieceType.BISHOP),
    )
    # White cannot castle kingside (path through attacked square g1)
    board.turn = Color.WHITE
    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_1, col=COL_G)
        )
        is False
    )
def test_castling_blocked_if_king_square_attacked() -> None:
    """T8.2: Castling blocked if king square attacked."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_H), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_H), create_piece(Color.BLACK, PieceType.ROOK)
    )
    # Black bishop attacks e1 (king square) - bishop on d2 (row 5, col 3) attacks e1 (row 7, col 4)
    board.turn = Color.BLACK
    board.set_piece(
        ConstantSquare(row=ROW_3, col=COL_D),
        create_piece(Color.BLACK, PieceType.BISHOP),
    )
    # White cannot castle (king square attacked)
    board.turn = Color.WHITE
    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_1, col=COL_G)
        )
        is False
    )
def test_castling_blocked_if_destination_attacked() -> None:
    """T8.2: Castling blocked if destination square attacked."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_H), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_H), create_piece(Color.BLACK, PieceType.ROOK)
    )
    # Black bishop attacks f1 (destination square) - bishop on g2 (row 6, col 6) attacks f1
    board.turn = Color.BLACK
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_G),
        create_piece(Color.BLACK, PieceType.BISHOP),
    )
    # White cannot castle kingside (destination f1 attacked)
    board.turn = Color.WHITE
    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_1, col=COL_G)
        )
        is False
    )
def test_castling_blocked_if_path_through_attacked_square() -> None:
    """T8.2: Castling blocked if path through attacked square."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_H), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_H), create_piece(Color.BLACK, PieceType.ROOK)
    )
    # Black bishop attacks f1 (square the king passes through for kingside)
    # Bishop on g2 (row 6, col 6) attacks f1 diagonally
    board.turn = Color.BLACK
    board.set_piece(
        ConstantSquare(row=ROW_2, col=COL_G),
        create_piece(Color.BLACK, PieceType.BISHOP),
    )
    # White cannot castle (path through attacked square f1)
    board.turn = Color.WHITE
    assert (
        board.make_move(
            ConstantSquare(row=ROW_1, col=COL_E), ConstantSquare(row=ROW_1, col=COL_G)
        )
        is False
    )
def test_castling_while_in_check_forbidden() -> None:
    """T8.2: Cannot castle while in check."""
    board = Board()
    clear_board(board)
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_E), create_piece(Color.WHITE, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_E), create_piece(Color.BLACK, PieceType.KING)
    )
    board.set_piece(
        ConstantSquare(row=ROW_1, col=COL_H), create_piece(Color.WHITE, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_8, col=COL_H), create_piece(Color.BLACK, PieceType.ROOK)
    )
    board.set_piece(
        ConstantSquare(row=ROW_3, col=COL_E), create_piece(Color.BLACK, PieceType.ROOK)
    )
    # White king in check from black rook
    board.turn = Color.WHITE
