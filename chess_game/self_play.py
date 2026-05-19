"""Self-play mode: AI plays both sides with algebraic notation and board display."""

from __future__ import annotations

import argparse
import sys

from chess_game.chess.ai import get_best_move
from chess_game.chess.board import Board
from chess_game.chess.board.game_state import is_checkmate, is_stalemate
from chess_game.chess.coords import index_to_algebraic
from chess_game.chess.types import Color

# Increase recursion limit for deep search
sys.setrecursionlimit(3000)


def _move_to_algebraic(start, end, promotion):
    """Format a move as algebraic notation like e2e4 or e7e8q."""
    base = index_to_algebraic(start) + index_to_algebraic(end)
    if promotion is not None:
        promo_map = {
            "q": "q",
            "r": "r",
            "b": "b",
            "n": "n",
        }
        promo_key = str(promotion).lower()
        base += promo_map.get(promo_key, "q")
    return base


def _position_key(board: Board) -> str:
    """Generate a simple key from board state and side to move."""
    pieces = ""
    for row in board.board:
        for piece in row:
            if piece is None:
                pieces += "."
            else:
                c = "W" if piece.color == Color.WHITE else "B"
                kind = {
                    "KING": "K",
                    "QUEEN": "Q",
                    "ROOK": "R",
                    "BISHOP": "B",
                    "KNIGHT": "N",
                    "PAWN": "P",
                }.get(piece.kind.name, "?")
                pieces += c + kind
    turn = "W" if board.turn == Color.WHITE else "B"
    return pieces + "|" + turn


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
        print("=" * 40)
        print("Self-play game starting")
        print(f"White depth: {depth_white}, Black depth: {depth_black}")
        print("=" * 40)
        print()

    move_number = 1
    position_counts = {}

    while move_number <= max_moves:
        key = _position_key(board)
        position_counts[key] = position_counts.get(key, 0) + 1

        # Threefold repetition draw
        if position_counts[key] >= 3:
            if verbose:
                print(f"\nDraw on move {move_number} (threefold repetition).")
                board.display()
            return

        # Checkmate
        if is_checkmate(board):
            winner = "Black" if board.turn == Color.WHITE else "White"
            if verbose:
                print(f"\nCheckmate on move {move_number}. {winner} wins.")
                board.display()
            return

        # Stalemate
        if is_stalemate(board):
            if verbose:
                print(f"\nStalemate on move {move_number}. The game is a draw.")
                board.display()
            return

        # Use side-specific depth
        current_depth = depth_white if board.turn == Color.WHITE else depth_black

        # Get best move from AI
        best = get_best_move(board, depth=current_depth)

        if best is None:
            if verbose:
                print(f"\nGame ended on move {move_number} (no legal moves).")
                board.display()
            return

        # Record the side that is about to move
        side = "White" if board.turn == Color.WHITE else "Black"

        # Make move on the real board
        board.make_move(best.start, best.end, promotion=best.promotion)

        # Print move in algebraic notation
        algebraic = _move_to_algebraic(best.start, best.end, best.promotion)
        if verbose:
            print(f"Move {move_number}: {side} plays {algebraic}")
            board.display()
            print()

        move_number += 1
    else:
        if verbose:
            print("\nReached maximum move limit. Game stopped.")
            board.display()


def main():
    """Entry point for self-play with optional depth arguments."""
    parser = argparse.ArgumentParser(
        description="Run self-play games with optional separate depths for White and Black.",
    )
    parser.add_argument(
        "--white-depth",
        type=int,
        default=2,
        help="Search depth for White (default: 2, max recommended: 4)",
    )
    parser.add_argument(
        "--black-depth",
        type=int,
        default=2,
        help="Search depth for Black (default: 2, max recommended: 4)",
    )
    parser.add_argument(
        "--max-moves",
        type=int,
        default=1000,
        help="Maximum moves before stopping (default: 1000)",
    )
    args = parser.parse_args()

    # Enforce reasonable limits to avoid freezing
    white_depth = min(args.white_depth, 4)
    black_depth = min(args.black_depth, 4)

    run_self_play(
        depth_white=white_depth,
        depth_black=black_depth,
        max_moves=args.max_moves,
        verbose=True,
    )


if __name__ == "__main__":
    main()
