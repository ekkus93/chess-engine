# UI rendering and input handling

from ..chess_engine.board import Board
from ..chess_engine.engine import Engine
from ..chess_engine.move import Move

import sys


def render_board(board: Board, turn: str):
    """Render the board and game status."""
    print("\n" + board.__str__() + "\n")
    if board.is_checkmate():
        print(f"Checkmate! {turn} wins.")
    elif board.is_stalemate():
        print("Stalemate! Draw.")
    elif board.is_check():
        print(f"{turn} is in check.")


def get_player_color() -> str:
    """Ask the user to choose a color."""
    while True:
        choice = input("Choose your color (w for White, b for Black): ").strip().lower()
        if choice in {"w", "b"}:
            return "white" if choice == "w" else "black"
        print("Invalid choice. Please enter 'w' or 'b'.")


def get_depth() -> int:
    """Ask the user for the search depth."""
    while True:
        depth_str = input("Enter depth for engine search (e.g., 3): ").strip()
        if depth_str.isdigit() and int(depth_str) > 0:
            return int(depth_str)
        print("Please enter a positive integer.")


def parse_san(san: str, board: Board) -> Move:
    try:
        return Move.from_san(san, board)
    except Exception as e:
        print(f"Invalid move: {e}")
        return None


def main():
    board = Board()
    engine = Engine()
    player_color = get_player_color()
    depth = get_depth()
    turn = "white"

    while not (board.is_checkmate() or board.is_stalemate()):
        render_board(board, turn)
        if turn == player_color:
            # Player turn
            san = input(f"{turn.capitalize()} move (SAN): ")
            move = parse_san(san, board)
            if move:
                board.apply(move)
                turn = board.opponent_color(turn)
        else:
            # AI turn
            print(f"Engine ({turn}) is thinking...\n")
            best_move = engine.search(board, depth, turn)
            if best_move is None:
                print("No legal moves found. Game over.")
                break
            board.apply(best_move)
            turn = board.opponent_color(turn)

    render_board(board, turn)
    if board.is_checkmate():
        print(f"Game over: {turn} wins by checkmate.")
    elif board.is_stalemate():
        print("Game over: stalemate.")


if __name__ == "__main__":
    main()
