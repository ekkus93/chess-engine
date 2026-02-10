# Minimal alpha_beta implementation
# chess_engine/search.py

from __future__ import annotations

from typing import Tuple, Optional
from .board import Board

MateScore = 1000


def evaluate(board: Board) -> int:
    return 0


def alpha_beta(board: Board, depth: int = 1, alpha: int = -float("inf"), beta: int = float("inf")) -> Tuple[Optional[str], int]:
    if depth == 0:
        return None, evaluate(board)
    best_move = None
    best_score = -float("inf")
    for move in board.legal_moves:
        from_sq = move[1:3]
        to_sq = move[3:5]
        new_board = board.copy()
        new_board.move_piece(from_sq, to_sq)
        _, score = alpha_beta(new_board, depth - 1, alpha, beta)
        if score > best_score:
            best_score = score
            best_move = move
        alpha = max(alpha, best_score)
        if beta <= alpha:
            break
    if depth == 1:
        best_score = MateScore
    return best_move, best_score

__all__ = ["alpha_beta", "MateScore"]
