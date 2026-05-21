"""Helper functions for tests."""

from chess_game.chess.ai import MinimaxParams, SearchContext
from chess_game.chess.board import Board, ConstantSquare
from chess_game.chess.board import create_piece
from chess_game.chess.coords import algebraic_to_index
from chess_game.chess.types import Color, PieceType


def sq(name: str) -> ConstantSquare:
    """Convert algebraic notation (e.g. 'e4') to a ConstantSquare."""
    return algebraic_to_index(name)


def assert_piece(
    board: Board,
    square_name: str,
    color: Color,
    kind: PieceType,
) -> None:
    """Assert that the given square contains a piece of the given color and type."""
    square = algebraic_to_index(square_name)
    piece = board.get_piece(square)
    assert piece is not None, f"Expected piece at {square_name}, found empty square"
    assert piece.color == color, (
        f"Expected {color.name} piece at {square_name}, "
        f"got {piece.color.name}"
    )
    assert piece.kind == kind, (
        f"Expected {kind.name} at {square_name}, got {piece.kind.name}"
    )


def assert_empty(board: Board, square_name: str) -> None:
    """Assert that the given square is empty."""
    square = algebraic_to_index(square_name)
    piece = board.get_piece(square)
    assert piece is None, (
        f"Expected empty square at {square_name}, "
        f"found {piece.color.name} {piece.kind.name}"
    )


def make_mate_in_one_white_position() -> Board:
    """Create a simple mate-in-one position for White."""

    board = Board()
    board.clear_board()
    board.set_piece(sq("g6"), create_piece(Color.WHITE, PieceType.KING))
    board.set_piece(sq("f7"), create_piece(Color.WHITE, PieceType.QUEEN))
    board.set_piece(sq("h8"), create_piece(Color.BLACK, PieceType.KING))
    board.turn = Color.WHITE
    return board


def make_search_context(*, tt=None, nodes=None, stats=None) -> SearchContext:
    """Create a SearchContext for search-related tests."""

    return SearchContext(
        transposition_table=tt,
        nodes_searched=nodes,
        stats=stats,
    )


def make_search_params(
    depth: int,
    alpha: int,
    beta: int,
    is_maximizing: bool,
    *,
    context: SearchContext | None = None,
) -> MinimaxParams:
    """Create MinimaxParams with an optional shared SearchContext."""

    return MinimaxParams(
        depth=depth,
        alpha=alpha,
        beta=beta,
        is_maximizing=is_maximizing,
        context=context,
    )
