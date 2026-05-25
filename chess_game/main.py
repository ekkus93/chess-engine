"""Interactive chess game entry point."""

from __future__ import annotations

from chess_game.chess.board import Board
from chess_game.chess.board.game_state import (
    is_in_check,
    record_position,
    terminal_message,
)
from chess_game.chess.move import parse_move_notation


def _game_over_message(
    board: Board,
    position_counts: dict[str, int] | None = None,
) -> str | None:
    """Return a end-of-game message if the game is over, else None."""
    return terminal_message(board, position_counts)


def _game_loop(board: Board) -> None:
    """Main game loop."""
    board.display()
    position_counts: dict[str, int] = {}
    record_position(board, position_counts)

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
        record_position(board, position_counts)

        status = _game_over_message(board, position_counts)
        if status:
            print(status)
            break

        if is_in_check(board, board.turn):
            next_side = board.turn.name.capitalize()
            print(f"{next_side} is in check!")


def main() -> None:
    """Entry point for interactive chess play."""
    board = Board()
    _game_loop(board)


if __name__ == "__main__":
    main()
