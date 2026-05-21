"""Self-play mode: AI plays both sides with algebraic notation and board display."""

from __future__ import annotations

import argparse
import signal
import sys
from typing import Optional

from chess_game.chess.ai import get_best_move, position_key
from chess_game.chess.board import Board
from chess_game.chess.board.game_state import is_checkmate, is_stalemate
from chess_game.chess.constants import ConstantSquare
from chess_game.chess.coords import index_to_algebraic
from chess_game.chess.types import Color, PieceType

# Increase recursion limit for deep search
sys.setrecursionlimit(5000)


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


def _get_best_move_with_timeout(
    board: Board,
    depth: int,
    timeout: Optional[float],
    position_counts: Optional[dict[str, int]] = None,
) -> object:
    """Run get_best_move with a POSIX alarm-based timeout.

    If timeout is None, search runs to completion at the requested depth.
    Otherwise, if it exceeds 'timeout' seconds, returns None.
    """
    if timeout is None:
        return get_best_move(board, depth=depth, position_counts=position_counts)

    class _SearchTimeout(Exception):
        """Raised when move search exceeds allowed time."""

    def _handler(signum: int, frame: object) -> None:
        raise _SearchTimeout("Search timed out")

    old_handler = signal.signal(signal.SIGALRM, _handler)
    signal.alarm(int(timeout) or 1)

    try:
        best = get_best_move(board, depth=depth, position_counts=position_counts)
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


def _terminal_message(
    board: Board,
    move_number: int,
    position_counts: dict[str, int],
) -> Optional[str]:
    """Return a terminal message if the game is already over."""

    key = position_key(board)
    position_counts[key] = position_counts.get(key, 0) + 1
    if position_counts[key] >= 3:
        return f"Draw on move {move_number} (threefold repetition)."
    if is_checkmate(board):
        winner = "Black" if board.turn == Color.WHITE else "White"
        return f"Checkmate on move {move_number}. {winner} wins."
    if is_stalemate(board):
        return f"Stalemate on move {move_number}. The game is a draw."
    return None


def _pick_self_play_move(
    board: Board,
    base_depth: int,
    timeout: Optional[int],
    position_counts: Optional[dict[str, int]] = None,
):
    """Choose a move at the exact requested depth."""
    return _get_best_move_with_timeout(board, base_depth, timeout, position_counts)


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


def run_self_play(
    depth_white: int = 2,
    depth_black: int = 2,
    max_moves: int = 1000,
    verbose: bool = True,
):
    """Run a self-play game with the AI playing both sides.

    Args:
        depth_white: Search depth for White.
        depth_black: Search depth for Black.
        max_moves: Maximum moves before stopping.
        verbose: If True, print moves and board; else silent.
    """
    board = Board()
    if verbose:
        _print_game_header(depth_white, depth_black)

    move_number = 1
    position_counts: dict[str, int] = {}
    per_move_timeout: Optional[int] = None

    while move_number <= max_moves:
        terminal_message = _terminal_message(board, move_number, position_counts)
        if terminal_message is not None:
            if verbose:
                _print_terminal_position(terminal_message, board)
            return

        base_depth = depth_white if board.turn == Color.WHITE else depth_black
        best = _pick_self_play_move(
            board,
            base_depth,
            per_move_timeout,
            position_counts,
        )
        if best is None:
            if verbose:
                _print_terminal_position(
                    f"Game ended on move {move_number} (no legal moves).",
                    board,
                )
            return

        side = "White" if board.turn == Color.WHITE else "Black"
        board.make_move(best.start, best.end, promotion=best.promotion)
        if verbose:
            _print_played_move(board, move_number, side, best)
        move_number += 1

    if verbose:
        _print_terminal_position("Reached maximum move limit. Game stopped.", board)


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
    args = parser.parse_args()

    # Validate depths >= 1
    if args.white_depth < 1:
        print("Error: --white-depth must be >= 1", file=sys.stderr)
        sys.exit(1)
    if args.black_depth < 1:
        print("Error: --black-depth must be >= 1", file=sys.stderr)
        sys.exit(1)

    run_self_play(
        depth_white=args.white_depth,
        depth_black=args.black_depth,
        max_moves=args.max_moves,
        verbose=True,
    )


if __name__ == "__main__":
    main()
