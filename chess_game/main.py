"""Interactive chess game entry point."""

from __future__ import annotations

from chess_game.chess.board import Board
from chess_game.chess.move import parse_move_notation
from chess_game.chess.types import Color


def _game_over_message(board: Board) -> str | None:
    """Return a end-of-game message if the game is over, else None."""
    if board.is_checkmate():
        winner = "Black" if board.turn == Color.WHITE else "White"
        return f"Checkmate! {winner} wins."
    if board.is_stalemate():
        return "Stalemate! The game is a draw."
    return None


def _game_loop(board: Board) -> None:
    """Main game loop."""
    board.display()

    while True:
        side = board.turn.name.capitalize()
        move_str = input(f"{side} to move (e.g., e2e4, e7e8q — or 'quit'): ").strip()
        if move_str.lower() in ("quit", "exit", "q"):
            break

        try:
            move = parse_move_notation(move_str)
        except ValueError as exc:
            print(f"Invalid input: {exc}")
            continue

        success = board.make_move(move.start, move.end, promotion=move.promotion)
        if not success:
            print(f"Illegal move: {move_str}")
            continue

        board.display()

        status = _game_over_message(board)
        if status:
            print(status)
            break

        if board.is_in_check(board.turn):
            next_side = board.turn.name.capitalize()
            print(f"{next_side} is in check!")


def main() -> None:
    """Entry point for interactive chess play."""
    board = Board()
    _game_loop(board)


if __name__ == "__main__":
    main()
