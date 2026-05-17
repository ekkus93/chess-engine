"""Self-play mode: AI plays both sides with algebraic notation and board display."""

from __future__ import annotations

from chess_game.chess.ai import get_best_move
from chess_game.chess.board import Board
from chess_game.chess.board.game_state import is_checkmate, is_stalemate
from chess_game.chess.coords import index_to_algebraic
from chess_game.chess.types import Color


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


def run_self_play(depth: int = 3, max_moves: int = 100):
    """Run a self-play game with the AI playing both sides."""
    board = Board()

    print("=" * 40)
    print("Self-play game starting")
    print("=" * 40)
    print()

    for move_number in range(1, max_moves + 1):
        # Check if game is over
        if is_checkmate(board):
            winner = "Black" if board.turn == Color.WHITE else "White"
            print(f"\nCheckmate on move {move_number}. {winner} wins.")
            board.display()
            return
        if is_stalemate(board):
            print(f"\nStalemate on move {move_number}. The game is a draw.")
            board.display()
            return

        # Get best move from AI
        best = get_best_move(board, depth=depth)

        if best is None:
            print(f"\nGame ended on move {move_number} (no legal moves).")
            board.display()
            return

        # Make move on the real board
        board.make_move(best.start, best.end, promotion=best.promotion)

        # Print move in algebraic notation
        algebraic = _move_to_algebraic(best.start, best.end, best.promotion)
        side = "White" if board.turn == Color.WHITE else "Black"

        print(f"Move {move_number}: {side} plays {algebraic}")
        board.display()
        print()

    else:
        print("Reached maximum move limit. Game stopped.")
        board.display()


def main():
    """Entry point for self-play."""
    run_self_play(depth=3)


if __name__ == "__main__":
    main()
