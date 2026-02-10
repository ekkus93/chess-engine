from .board import Board

class Engine:
    def __init__(self, board=None):
        self.board = board if board is not None else Board()
        self.turn = "white"
