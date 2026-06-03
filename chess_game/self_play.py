"""Self-play mode: AI plays both sides with algebraic notation and board display."""

from __future__ import annotations

import argparse
import signal
import sys
from dataclasses import dataclass
from typing import Optional

from chess_game.chess.ai import BestMoveOptions, get_best_move
from chess_game.chess.board import Board
from chess_game.chess.board.game_state import record_position, terminal_message
from chess_game.chess.constants import ConstantSquare
from chess_game.chess.coords import index_to_algebraic
from chess_game.chess.opening_book import OpeningBook, OpeningBookError, get_bundled_opening_book
from chess_game.chess.types import Color, LegalMove, PieceType

@dataclass
class _MoveSelectionParams:
    """Parameters for move selection during self-play."""

    board: Board
    depth: int
    timeout: Optional[float]
    position_counts: Optional[dict[str, int]] = None
    use_opening_book: bool = True
    opening_book: Optional[OpeningBook] = None


@dataclass
class _SelfPlayOptions:
    """Configuration options for self-play game."""

    max_moves: int = 1000
    verbose: bool = True
    use_opening_book: bool = True
    opening_book: Optional[OpeningBook] = None


PROMOTION_SUFFIXES = {
    PieceType.QUEEN: "q",
    PieceType.ROOK: "r",
    PieceType.BISHOP: "b",
    PieceType.KNIGHT: "n",
}


def _move_to_algebraic(
    start: ConstantSquare,
    end: ConstantSquare,
    promotion: Optional[PieceType],
) -> str:
    """Format a move as algebraic notation like e2e4 or e7e8q."""
    base = index_to_algebraic(start) + index_to_algebraic(end)
    if promotion is not None:
        base += PROMOTION_SUFFIXES[promotion]
    return base


def _get_best_move_with_timeout(params: _MoveSelectionParams) -> Optional[LegalMove]:
    """Run get_best_move with a POSIX alarm-based timeout.

    If timeout is None, search runs to completion at the requested depth.
    Otherwise, if it exceeds 'timeout' seconds, returns None.
    """
    if params.timeout is None:
        return get_best_move(
            params.board,
            depth=params.depth,
            position_counts=params.position_counts,
            book_options=BestMoveOptions(
                use_opening_book=params.use_opening_book,
                opening_book=params.opening_book,
            ),
        )

    class _SearchTimeout(Exception):
        """Raised when move search exceeds allowed time."""

    def _handler(signum: int, frame: object) -> None:
        raise _SearchTimeout("Search timed out")

    old_handler = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(int(params.timeout) or 1)

    try:
        best = get_best_move(
            params.board,
            depth=params.depth,
            position_counts=params.position_counts,
            book_options=BestMoveOptions(
                use_opening_book=params.use_opening_book,
                opening_book=params.opening_book,
            ),
        )
    except _SearchTimeout:
        best = None
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, old_handler)

    return best


def _print_game_header(depth_white: int, depth_black: int) -> None:
    """Print the self-play header."""

    print("=" * 40)
    print("Self-play game starting")
    print(f"White depth: {depth_white}, Black depth: {depth_black}")
    print("=" * 40)
    print()


def _print_terminal_position(message: str, board: Board) -> None:
    """Print a final message and the terminal board."""

    print(f"\n{message}")
    board.display()


def _print_played_move(board: Board, move_number: int, side: str, best_move) -> None:
    """Print the chosen move and resulting position."""

    algebraic = _move_to_algebraic(
        best_move.start,
        best_move.end,
        best_move.promotion,
    )
    print(f"Move {move_number}: {side} plays {algebraic}")
    board.display()
    print()


def _run_self_play_internal(
    depth_white: int,
    depth_black: int,
    options: _SelfPlayOptions,
) -> None:
    """Internal implementation of self-play game.

    Args:
        depth_white: Search depth for White.
        depth_black: Search depth for Black.
        options: Configuration options for the game.
    """

    def _pick_move(board: Board, base_depth: int) -> Optional[LegalMove]:
        """Helper to pick a move with current game context."""
        if options.use_opening_book:
            book = options.opening_book or get_bundled_opening_book()
            book_move = book.find_book_move_random(board)
            if book_move is not None:
                return book_move
        params = _MoveSelectionParams(
            board=board,
            depth=base_depth,
            timeout=None,
            position_counts=position_counts,
            use_opening_book=False,
            opening_book=options.opening_book,
        )
        return _get_best_move_with_timeout(params)

    board = Board()
    if options.verbose:
        _print_game_header(depth_white, depth_black)

    move_number = 1
    position_counts: dict[str, int] = {}
    record_position(board, position_counts)

    while move_number <= options.max_moves:
        game_over = terminal_message(board, position_counts)
        if game_over is not None:
            if options.verbose:
                _print_terminal_position(f"{game_over} On move {move_number}.", board)
            return

        base_depth = depth_white if board.turn == Color.WHITE else depth_black
        best = _pick_move(board, base_depth)
        if best is None:
            if options.verbose:
                _print_terminal_position(
                    f"Game ended on move {move_number} (no legal moves).",
                    board,
                )
            return

        side = "White" if board.turn == Color.WHITE else "Black"
        board.make_move(best.start, best.end, promotion=best.promotion)
        record_position(board, position_counts)
        if options.verbose:
            _print_played_move(board, move_number, side, best)
        move_number += 1

    if options.verbose:
        _print_terminal_position("Reached maximum move limit. Game stopped.", board)


def run_self_play(
    depth_white: int = 2,
    depth_black: int = 2,
    options: Optional[_SelfPlayOptions] = None,
) -> None:
    """Run a self-play game with the AI playing both sides.

    Args:
        depth_white: Search depth for White.
        depth_black: Search depth for Black.
        options: Optional self-play configuration. If omitted, default options are used.
    """
    effective_options = options or _SelfPlayOptions()
    _run_self_play_internal(depth_white, depth_black, effective_options)


def main():
    """Entry point for self-play with optional depth arguments."""
    parser = argparse.ArgumentParser(
        description="Run self-play games with optional separate depths for White and Black.",
    )
    parser.add_argument(
        "--white-depth",
        type=int,
        default=2,
        help="Search depth for White (default: 2)",
    )
    parser.add_argument(
        "--black-depth",
        type=int,
        default=2,
        help="Search depth for Black (default: 2)",
    )
    parser.add_argument(
        "--max-moves",
        type=int,
        default=1000,
        help="Maximum moves before stopping (default: 1000)",
    )
    parser.add_argument(
        "--no-opening-book",
        action="store_true",
        help="Disable the opening book (default: enabled)",
    )
    parser.add_argument(
        "--opening-book",
        type=str,
        default=None,
        help="Path to custom opening book JSON file (default: use bundled book)",
    )
    args = parser.parse_args()

    # Validate depths >= 1
    if args.white_depth < 1:
        print("Error: --white-depth must be >= 1", file=sys.stderr)
        sys.exit(1)
    if args.black_depth < 1:
        print("Error: --black-depth must be >= 1", file=sys.stderr)
        sys.exit(1)

    # Handle opening book loading
    opening_book: Optional[OpeningBook] = None
    if not args.no_opening_book and args.opening_book:
        try:
            opening_book = OpeningBook.from_file(args.opening_book)
        except OpeningBookError as exc:
            print(f"Error loading opening book from {args.opening_book}: {exc}", file=sys.stderr)
            sys.exit(1)

    options = _SelfPlayOptions(
        max_moves=args.max_moves,
        verbose=True,
        use_opening_book=not args.no_opening_book,
        opening_book=opening_book,
    )
    run_self_play(
        depth_white=args.white_depth,
        depth_black=args.black_depth,
        options=options,
    )


if __name__ == "__main__":
    main()
