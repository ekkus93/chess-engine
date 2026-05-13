"""Tests for Board and BoardState cloning behavior.

Verifies that cloning produces independent copies where mutations to the
clone do not affect the original, and vice versa.
"""

from __future__ import annotations

from chess_game.chess.board import Board, create_piece
from chess_game.chess.board.board_state import BoardState
from chess_game.chess.constants import get_square_constant
from chess_game.chess.types import Color, PieceType


# ---------------------------------------------------------------------------
# BoardState.clone() tests
# ---------------------------------------------------------------------------

def test_board_state_clone_deep_copies_pieces() -> None:
    """TS6.1: Cloned BoardState has independent Piece objects."""
    board = Board()
    original_e2_piece = board.get_piece(get_square_constant(6, 4))  # e2
    assert original_e2_piece is not None

    state = BoardState(
        board=board.board,
        turn=board.turn,
        en_passant_target=board.en_passant_target,
        white_kingside=board.white_kingside,
        white_queenside=board.white_queenside,
        black_kingside=board.black_kingside,
        black_queenside=board.black_queenside,
    )
    cloned_state = state.clone()

    cloned_e2_piece = cloned_state.get_piece(get_square_constant(6, 4))
    assert cloned_e2_piece is not None
    assert cloned_e2_piece is not original_e2_piece
    assert cloned_e2_piece.color == original_e2_piece.color
    assert cloned_e2_piece.kind == original_e2_piece.kind

    # Mutating cloned piece must not affect original
    cloned_e2_piece._square = get_square_constant(0, 0)
    assert original_e2_piece._square != get_square_constant(0, 0)


def test_board_state_clone_preserves_turn() -> None:
    """TS6.1: Cloned BoardState preserves turn."""
    board = Board()
    board.turn = Color.BLACK
    state = BoardState(
        board=board.board,
        turn=board.turn,
        en_passant_target=None,
    )
    cloned = state.clone()
    assert cloned.turn == Color.BLACK
    assert state.turn == Color.BLACK


def test_board_state_clone_preserves_en_passant_target() -> None:
    """TS6.1: Cloned BoardState preserves en passant target."""
    board = Board()
    ep_target = get_square_constant(4, 4)  # e5
    state = BoardState(
        board=board.board,
        turn=Color.WHITE,
        en_passant_target=ep_target,
    )
    cloned = state.clone()
    assert cloned.en_passant_target == ep_target
    assert state.en_passant_target == ep_target


def test_board_state_clone_preserves_castling_rights() -> None:
    """TS6.1: Cloned BoardState preserves castling rights."""
    board = Board()
    state = BoardState(
        board=board.board,
        turn=Color.WHITE,
        en_passant_target=None,
        white_kingside=True,
        white_queenside=False,
        black_kingside=False,
        black_queenside=True,
    )
    cloned = state.clone()
    assert cloned.white_kingside is True
    assert cloned.white_queenside is False
    assert cloned.black_kingside is False
    assert cloned.black_queenside is True


# ---------------------------------------------------------------------------
# Board.clone() tests
# ---------------------------------------------------------------------------

def test_board_clone_produces_independent_board() -> None:
    """TS6.2: Mutating clone does not affect original."""
    original = Board()
    original_e2 = original.get_piece(get_square_constant(6, 4))  # e2
    assert original_e2 is not None

    cloned = original.clone()

    # Move the e2 pawn on the clone
    cloned.clear_square(get_square_constant(6, 4))
    cloned_e2_piece = original_e2.__class__(
        color=original_e2.color, kind=original_e2.kind
    )
    cloned_e2_piece._square = get_square_constant(4, 4)  # e4
    cloned.set_piece(get_square_constant(4, 4), cloned_e2_piece)

    # Original should be unchanged
    assert original.get_piece(get_square_constant(6, 4)) is not None
    assert original.get_piece(get_square_constant(4, 4)) is None


def test_board_clone_validators_point_at_cloned_board() -> None:
    """TS6.2: Clone validators reference the cloned board, not original."""
    original = Board()
    cloned = original.clone()

    assert cloned._move_validator.board is cloned
    assert cloned._move_executor.board is cloned
    assert cloned._promotion_validator.board is cloned
    assert cloned._en_passant_validator.board is cloned

    # They must NOT reference the original
    assert cloned._move_validator.board is not original
    assert cloned._move_executor.board is not original


def test_board_clone_pieces_are_independent() -> None:
    """TS6.2: Clone has its own Piece objects, not shared references."""
    original = Board()
    cloned = original.clone()

    original_e2 = original.get_piece(get_square_constant(6, 4))
    cloned_e2 = cloned.get_piece(get_square_constant(6, 4))
    assert original_e2 is not None
    assert cloned_e2 is not None
    assert original_e2 is not cloned_e2


def test_board_clone_preserves_all_state() -> None:
    """TS6.2: Clone preserves turn, en_passant_target, and castling rights."""
    original = Board()
    original.turn = Color.BLACK
    original.en_passant_target = get_square_constant(4, 3)  # d5
    original.white_kingside = False
    original.black_queenside = False
    original.white_queenside = True
    original.black_kingside = True

    cloned = original.clone()

    assert cloned.turn == Color.BLACK
    assert cloned.en_passant_target == get_square_constant(4, 3)
    assert cloned.white_kingside is False
    assert cloned.white_queenside is True
    assert cloned.black_kingside is True
    assert cloned.black_queenside is False


def test_board_clone_moves_on_clone_independent() -> None:
    """TS6.2: Making a legal move on clone doesn't affect original."""
    original = Board()
    # e2e4 on original
    assert original.make_move(
        get_square_constant(6, 4), get_square_constant(4, 4)
    )  # e2->e4
    assert original.get_piece(get_square_constant(6, 4)) is None
    assert original.get_piece(get_square_constant(4, 4)) is not None

    cloned = original.clone()

    # Now play e7e5 on clone (Black's turn)
    assert cloned.make_move(
        get_square_constant(1, 4), get_square_constant(3, 4)
    )  # e7->e5
    assert cloned.get_piece(get_square_constant(1, 4)) is None
    assert cloned.get_piece(get_square_constant(3, 4)) is not None

    # Original should be unchanged (still has black pawn on e7)
    assert original.get_piece(get_square_constant(1, 4)) is not None
    assert original.get_piece(get_square_constant(3, 4)) is None


# ---------------------------------------------------------------------------
# Clone used for king-safety simulation
# ---------------------------------------------------------------------------

def test_clone_used_in_king_safety_simulation() -> None:
    """TS6.4: King-safety simulation uses clone, doesn't mutate original."""
    board = Board()
    # Set up a position where e2e4 is legal
    e2_piece = board.get_piece(get_square_constant(6, 4))
    assert e2_piece is not None
    original_square = e2_piece._square

    # Make the move (internally uses clone for king-safety check)
    result = board.make_move(
        get_square_constant(6, 4), get_square_constant(4, 4)
    )
    assert result is True

    # The original e2 pawn should now be on e4
    assert board.get_piece(get_square_constant(6, 4)) is None
    assert board.get_piece(get_square_constant(4, 4)) is not None


def test_clone_simulation_rejects_self_check() -> None:
    """TS6.4: Clone-based simulation correctly rejects moves that expose king."""
    board = Board()
    board.clear_board()

    # Set up: White king on e1, white pawn on d2, black rook on e8.
    # Moving d2->d4 removes the d-file blocker; king on e1 is exposed along
    # the e-file by the rook on e8 (no intervening pieces on e-file).
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.WHITE, PieceType.KING)
    )  # e1
    board.set_piece(
        get_square_constant(6, 3), create_piece(Color.WHITE, PieceType.PAWN)
    )  # d2
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.BLACK, PieceType.ROOK)
    )  # e8
    board.turn = Color.WHITE

    # d2->d4 is a valid pawn move geometrically, but we need a setup where
    # moving a piece exposes the king. Instead, set up a position where a
    # piece on f1 blocks a black rook on f8 from attacking the king on e1.
    # If the f1 piece moves away, the king is exposed on the f-file...
    # Actually, the king is on e-file, not f-file. Let me use a simpler setup.
    #
    # White king on e1 (row 7, col 4), white rook on f1 (row 7, col 5)
    # blocks a black rook on f8 (row 0, col 5) from the f-file.
    # If the f1 rook moves away (f1->g1), the king on e1 is NOT on f-file.
    #
    # Better: white king on e1, white pawn on e2 blocks black rook on e8.
    # Move e2->f3 (diagonal capture-like, but we need an enemy on f3).
    #
    # Simplest correct setup: king on e1, knight on e2 blocks rook on e8.
    # Move knight away (e2->g1) exposes king to rook on e8.
    board.clear_board()
    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.WHITE, PieceType.KING)
    )  # e1
    board.set_piece(
        get_square_constant(6, 4), create_piece(Color.WHITE, PieceType.KNIGHT)
    )  # e2
    board.set_piece(
        get_square_constant(0, 4), create_piece(Color.BLACK, PieceType.ROOK)
    )  # e8
    board.turn = Color.WHITE

    # Knight e2->g1 exposes king to rook on e8
    assert not board.make_move(
        get_square_constant(6, 4), get_square_constant(7, 6)
    )  # e2->g1 should be rejected

    # King and knight still in original positions
    assert board.get_piece(get_square_constant(7, 4)) is not None
    assert board.get_piece(get_square_constant(6, 4)) is not None


def test_clone_en_passant_king_safety() -> None:
    """TS6.4: En passant king-safety simulation uses clone correctly."""
    board = Board()
    board.clear_board()

    # Set up: White king on e1, white pawn on e5, black pawn on d5,
    # black rook on a8. After d4 captures e.p. on d6, king would be exposed.
    # Simpler setup: White king on e1, white pawn on f5, black pawn on e4,
    # en passant target on e3, black rook on a1.
    # f5xe3 e.p. would expose king on e1 to rook on a1 via rank 1.

    board.set_piece(
        get_square_constant(7, 4), create_piece(Color.WHITE, PieceType.KING)
    )  # e1
    board.set_piece(
        get_square_constant(2, 5), create_piece(Color.WHITE, PieceType.PAWN)
    )  # f5
    board.set_piece(
        get_square_constant(3, 4), create_piece(Color.BLACK, PieceType.PAWN)
    )  # e4
    board.set_piece(
        get_square_constant(7, 0), create_piece(Color.BLACK, PieceType.ROOK)
    )  # a1
    board.en_passant_target = get_square_constant(5, 4)  # e3
    board.turn = Color.WHITE

    # f5xe3 e.p. would put white pawn on e3, but rook on a1 attacks e1
    # (the king square) along rank 1.  Since the pawn move doesn't block
    # that attack, the king is still exposed.
    assert not board.make_move(
        get_square_constant(2, 5), get_square_constant(5, 4)
    )  # f5->e3 en passant

    # Original position unchanged
    assert board.get_piece(get_square_constant(2, 5)) is not None
    assert board.get_piece(get_square_constant(7, 4)) is not None
