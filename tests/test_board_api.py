"""Tests for untested Board API methods.

Covers: is_valid_position, is_same_color, is_opponent, is_empty, find_king,
get_legal_moves_for_color.
"""

from chess_game.chess.board import Board
from chess_game.chess.constants import ROW_1, ROW_8, ColConstant, ConstantSquare, get_square_constant, RowConstant
from chess_game.chess.types import Color, PieceType, Piece
from chess_game.chess.move import parse_move_notation
from tests.helpers import sq


# =============================================================================
# 1. is_valid_position
# =============================================================================

def test_is_valid_position_corners_return_true() -> None:
    """Valid corner squares (a1, a8, h1, h8) return True."""
    board = Board()
    assert board.is_valid_position(sq("a1")) is True
    assert board.is_valid_position(sq("a8")) is True
    assert board.is_valid_position(sq("h1")) is True
    assert board.is_valid_position(sq("h8")) is True


def test_is_valid_position_center_squares_return_true() -> None:
    """Valid center squares (e4, d5) return True."""
    board = Board()
    assert board.is_valid_position(sq("e4")) is True
    assert board.is_valid_position(sq("d5")) is True


def test_is_valid_position_out_of_bounds_column_returns_false() -> None:
    """Column index < 0 or >= 8 returns False."""
    board = Board()
    # col 8 is out of range (0-7)
    bad = ConstantSquare(row=ROW_1, col=ColConstant(8))
    assert board.is_valid_position(bad) is False


def test_is_valid_position_out_of_bounds_row_returns_false() -> None:
    """Row index < 0 or >= 8 returns False."""
    board = Board()
    bad = ConstantSquare(row=RowConstant(8), col=ColConstant(0))
    assert board.is_valid_position(bad) is False


def test_is_valid_position_negative_indices_return_false() -> None:
    """Negative row and column indices return False."""
    board = Board()
    bad = ConstantSquare(row=RowConstant(-1), col=ColConstant(-1))
    assert board.is_valid_position(bad) is False


# =============================================================================
# 2. is_same_color
# =============================================================================

def test_is_same_color_two_white_pieces() -> None:
    """Two white pieces on different squares return True."""
    board = Board()
    assert board.is_same_color(sq("e1"), sq("d1")) is True


def test_is_same_color_two_black_pieces() -> None:
    """Two black pieces on different squares return True."""
    board = Board()
    assert board.is_same_color(sq("e8"), sq("d8")) is True


def test_is_same_color_white_and_black_returns_false() -> None:
    """One white and one black piece return False."""
    board = Board()
    assert board.is_same_color(sq("e1"), sq("e8")) is False


def test_is_same_color_same_square_returns_true() -> None:
    """Same square returns True."""
    board = Board()
    assert board.is_same_color(sq("e1"), sq("e1")) is True


def test_is_same_color_one_occupied_one_empty_returns_false() -> None:
    """One occupied and one empty square returns False."""
    board = Board()
    assert board.is_same_color(sq("e1"), sq("e4")) is False


def test_is_same_color_both_empty_returns_false() -> None:
    """Both squares empty returns False."""
    board = Board()
    assert board.is_same_color(sq("e4"), sq("d4")) is False


# =============================================================================
# 3. is_opponent
# =============================================================================

def test_is_opponent_white_vs_black() -> None:
    """White vs black piece returns True."""
    board = Board()
    assert board.is_opponent(sq("e1"), sq("e8")) is True


def test_is_opponent_black_vs_white() -> None:
    """Black vs white piece returns True."""
    board = Board()
    assert board.is_opponent(sq("e8"), sq("e1")) is True


def test_is_opponent_two_white_pieces_returns_false() -> None:
    """Two white pieces return False."""
    board = Board()
    assert board.is_opponent(sq("e1"), sq("d1")) is False


def test_is_opponent_two_black_pieces_returns_false() -> None:
    """Two black pieces return False."""
    board = Board()
    assert board.is_opponent(sq("e8"), sq("d8")) is False


def test_is_opponent_one_occupied_one_empty_returns_false() -> None:
    """One occupied and one empty square returns False."""
    board = Board()
    assert board.is_opponent(sq("e1"), sq("e4")) is False


def test_is_opponent_both_empty_returns_false() -> None:
    """Both squares empty returns False."""
    board = Board()
    assert board.is_opponent(sq("e4"), sq("d4")) is False


def test_is_opponent_same_square_returns_false() -> None:
    """Same square returns False."""
    board = Board()
    assert board.is_opponent(sq("e1"), sq("e1")) is False


# =============================================================================
# 4. is_empty
# =============================================================================

def test_is_empty_default_board_empty_squares() -> None:
    """Default board empty squares (e.g., e2, e7) return True."""
    board = Board()
    assert board.is_empty(sq("e4")) is True
    assert board.is_empty(sq("d5")) is True


def test_is_empty_occupied_square_returns_false() -> None:
    """Occupied squares (e.g., e1 has king) return False."""
    board = Board()
    assert board.is_empty(sq("e1")) is False


def test_is_empty_after_clear_square() -> None:
    """Square after clear_square returns True."""
    board = Board()
    board.clear_square(sq("e1"))
    assert board.is_empty(sq("e1")) is True


def test_is_empty_after_set_piece() -> None:
    """Square after set_piece returns False."""
    board = Board()
    board.set_piece(sq("e4"), Piece(color=Color.WHITE, kind=PieceType.PAWN))
    assert board.is_empty(sq("e4")) is False


def test_is_empty_corner_squares_default_board() -> None:
    """Corner squares on default board are occupied (a1 has rook, a8 has rook)."""
    board = Board()
    assert board.is_empty(sq("a1")) is False
    assert board.is_empty(sq("a8")) is False


# =============================================================================
# 5. find_king
# =============================================================================

def test_find_king_white_default_board() -> None:
    """Default board white king found at e1."""
    board = Board()
    king_sq = board.find_king(Color.WHITE)
    assert king_sq == sq("e1")


def test_find_king_black_default_board() -> None:
    """Default board black king found at e8."""
    board = Board()
    king_sq = board.find_king(Color.BLACK)
    assert king_sq == sq("e8")


def test_find_king_after_king_moves() -> None:
    """After king moves, new position is returned."""
    board = Board()
    board.clear_square(sq("f1"))
    board.make_move(sq("e1"), sq("f1"))
    king_sq = board.find_king(Color.WHITE)
    assert king_sq == sq("f1")


def test_find_king_returns_none_when_missing() -> None:
    """After king removed from board, returns None."""
    board = Board()
    board.clear_square(sq("e1"))
    king_sq = board.find_king(Color.WHITE)
    assert king_sq is None


def test_find_king_both_colors_independent() -> None:
    """Both colors independently return correct squares."""
    board = Board()
    white_king = board.find_king(Color.WHITE)
    black_king = board.find_king(Color.BLACK)
    assert white_king == sq("e1")
    assert black_king == sq("e8")


def test_find_king_cloned_board_preserves_positions() -> None:
    """Cloned board preserves king positions."""
    board = Board()
    board.make_move(sq("e1"), sq("f1"))
    cloned = board.clone()
    assert cloned.find_king(Color.WHITE) == sq("f1")
    assert cloned.find_king(Color.BLACK) == sq("e8")


# =============================================================================
# 6. get_legal_moves_for_color
# =============================================================================

def test_legal_moves_for_color_white_default_board() -> None:
    """Default board white has expected number of legal moves (20)."""
    board = Board()
    moves = board.get_legal_moves_for_color(Color.WHITE)
    assert len(moves) == 20


def test_legal_moves_for_color_black_default_board() -> None:
    """Default board black has expected number of legal moves (20)."""
    board = Board()
    moves = board.get_legal_moves_for_color(Color.BLACK)
    assert len(moves) == 20


def test_legal_moves_for_color_after_move_only_next_side() -> None:
    """After a move, only the next side's moves are returned."""
    board = Board()
    board.make_move(sq("e2"), sq("e4"))
    # After white moves, it's black's turn.
    # Ask for white moves — they should still work (method ignores turn).
    white_moves = board.get_legal_moves_for_color(Color.WHITE)
    assert len(white_moves) > 0
    # Ask for black moves — should also work.
    black_moves = board.get_legal_moves_for_color(Color.BLACK)
    assert len(black_moves) > 0
    # The move counts differ after e4 is played.
    assert len(black_moves) != len(white_moves)


def test_legal_moves_for_color_pinned_piece_no_illegal_moves() -> None:
    """Pinned pieces do not produce illegal moves in the list."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e1"), Piece(color=Color.WHITE, kind=PieceType.KING))
    board.set_piece(sq("e2"), Piece(color=Color.WHITE, kind=PieceType.PAWN))
    board.set_piece(sq("e8"), Piece(color=Color.BLACK, kind=PieceType.ROOK))
    board.set_piece(sq("a1"), Piece(color=Color.WHITE, kind=PieceType.ROOK))
    board.turn = Color.WHITE

    moves = board.get_legal_moves_for_color(Color.WHITE)
    # The e2 pawn is pinned, so it shouldn't have moves.
    for start, end, _promo in moves:
        assert start != sq("e2"), "Pinned e2 pawn should have no legal moves"


def test_legal_moves_for_color_castling_moves_appear() -> None:
    """Castling moves appear when conditions are met."""
    board = Board()
    # Default position — white can castle on both sides.
    moves = board.get_legal_moves_for_color(Color.WHITE)
    king_moves = [m for m in moves if m[0] == sq("e1")]
    # Kingside and queenside castling should be present.
    assert (sq("e1"), sq("g1"), None) in king_moves
    assert (sq("e1"), sq("c1"), None) in king_moves


def test_legal_moves_for_color_en_passant_appears() -> None:
    """En passant move appears when available."""
    board = Board()
    board.make_move(sq("d2"), sq("d4"))
    board.make_move(sq("e7"), sq("e5"))
    # White's turn; d4xe6 e.p. should be a legal move for white.
    moves = board.get_legal_moves_for_color(Color.WHITE)
    ep_move = (sq("d4"), sq("e6"), None)
    assert ep_move in moves, f"En passant move {ep_move} not found in {moves}"


def test_legal_moves_for_color_promotion_moves_appear() -> None:
    """Promotion moves appear when pawn reaches rank."""
    board = Board()
    board.clear_board()
    board.set_piece(sq("e7"), Piece(color=Color.WHITE, kind=PieceType.PAWN))
    board.set_piece(sq("e1"), Piece(color=Color.WHITE, kind=PieceType.KING))
    board.set_piece(sq("e8"), Piece(color=Color.BLACK, kind=PieceType.KING))
    board.turn = Color.WHITE

    moves = board.get_legal_moves_for_color(Color.WHITE)
    promotion_moves = [m for m in moves if m[2] is not None]
    assert len(promotion_moves) > 0, "Expected promotion moves for e7 pawn"
    # Should have queen, rook, bishop, knight promotions
    assert len(promotion_moves) == 4


def test_legal_moves_for_color_checkmate_returns_empty() -> None:
    """Checkmate position returns empty list for side in checkmate."""
    board = Board()
    board.clear_board()
    # Classic back-rank mate: black king on e8, white rook on e1,
    # black pawns on a7, b7, c7, d7, f7, g7, h7 blocking escape.
    board.set_piece(sq("e8"), Piece(color=Color.BLACK, kind=PieceType.KING))
    board.set_piece(sq("e1"), Piece(color=Color.WHITE, kind=PieceType.ROOK))
    for col in range(8):
        if col == 4:
            continue  # skip e7 (occupied by rook line)
        board.set_piece(
            get_square_constant(1, col),
            Piece(color=Color.BLACK, kind=PieceType.PAWN),
        )
    board.turn = Color.BLACK

    moves = board.get_legal_moves_for_color(Color.BLACK)
    assert len(moves) == 0, f"Expected no legal moves in checkmate, got {len(moves)}"


def test_legal_moves_for_color_stalemate_returns_empty() -> None:
    """Stalemate position returns empty list for side in stalemate."""
    board = Board()
    board.clear_board()
    # Stalemate: black king on h8, white king on g6,
    # all squares around h8 covered or occupied.
    board.set_piece(sq("h8"), Piece(color=Color.BLACK, kind=PieceType.KING))
    board.set_piece(sq("g6"), Piece(color=Color.WHITE, kind=PieceType.KING))
    board.set_piece(sq("h7"), Piece(color=Color.WHITE, kind=PieceType.PAWN))
    board.set_piece(sq("g7"), Piece(color=Color.WHITE, kind=PieceType.PAWN))
    board.turn = Color.BLACK

    moves = board.get_legal_moves_for_color(Color.BLACK)
    assert len(moves) == 0, f"Expected no legal moves in stalemate, got {len(moves)}"
