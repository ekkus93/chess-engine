#!/usr/bin/env python3

from chess_engine.engine import Engine
from chess_engine.search import Search
from cli.ui import render_board


def main():
    engine = Engine()
    search = Search(engine)
    # Simple loop placeholder
    render_board(engine.board)

if __name__ == "__main__":
    main()
