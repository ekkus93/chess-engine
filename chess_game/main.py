# chess_game/main.py
# Entry point for the chess program
from chess_game.chess.board import Board


def parse_move(move):
    # Convert algebraic notation (e2e4) to board indices
    from_pos = move[2:4]
    to_pos = move[4:6]

    # Convert columns a-h to 0-7
    col_from = ord(from_pos[0]) - ord("a")
    row_from = 7 - int(from_pos[1])  # Reverse for display

    col_to = ord(to_pos[0]) - ord("a")
    row_to = 7 - int(to_pos[1])

    return (row_from, col_from), (row_to, col_to)


if __name__ == "__main__":
    board = Board()
    board.display()

    while True:
        move = input(f"{board.turn}'s move (e.g., e2e4): ")
        if move.lower() == "quit":
            break

        try:
            from_pos, to_pos = parse_move(move)
            # Use proper move validation API instead of direct board mutation
            success = board.make_move(from_pos, to_pos)
            if success:
                print(f"Move {move} accepted")
            else:
                print(f"Move {move} rejected")

            board.display()
        except Exception as e:
            print(f"Error: {e}")
            board.display()
