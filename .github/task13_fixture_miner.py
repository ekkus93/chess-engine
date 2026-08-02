#!/usr/bin/env python3
"""Mine deterministic KQK mate-distance fixtures for Task 13.5."""

from __future__ import annotations

from functools import lru_cache

import chess

MATE = 30_000


def terminal_score(board: chess.Board, ply: int) -> int | None:
    if board.is_checkmate():
        return -MATE + ply
    if (
        board.is_stalemate()
        or board.is_insufficient_material()
        or board.is_seventyfive_moves()
        or board.is_fivefold_repetition()
        or board.can_claim_fifty_moves()
        or board.can_claim_threefold_repetition()
    ):
        return 0
    return None


def search_score(board: chess.Board, depth: int, ply: int) -> int:
    @lru_cache(maxsize=None)
    def visit(fen: str, remaining: int, current_ply: int) -> int:
        current = chess.Board(fen)
        resolved = terminal_score(current, current_ply)
        if resolved is not None:
            return resolved
        if remaining == 0:
            return 0

        best = -MATE
        for move in current.legal_moves:
            current.push(move)
            score = -visit(current.fen(en_passant="fen"), remaining - 1, current_ply + 1)
            current.pop()
            if score > best:
                best = score
        return best

    return visit(board.fen(en_passant="fen"), depth, ply)


def root_scores(board: chess.Board, depth: int) -> list[tuple[chess.Move, int]]:
    scores: list[tuple[chess.Move, int]] = []
    for move in board.legal_moves:
        board.push(move)
        score = -search_score(board, depth - 1, 1)
        board.pop()
        scores.append((move, score))
    return scores


def kqk_board(white_king: int, white_queen: int, black_king: int, turn: bool) -> chess.Board:
    board = chess.Board.empty()
    board.set_piece_at(white_king, chess.Piece(chess.KING, chess.WHITE))
    board.set_piece_at(white_queen, chess.Piece(chess.QUEEN, chess.WHITE))
    board.set_piece_at(black_king, chess.Piece(chess.KING, chess.BLACK))
    board.turn = turn
    board.halfmove_clock = 0
    board.fullmove_number = 1
    return board


def find_fixture(turn: bool, depth: int) -> tuple[chess.Board, int, list[tuple[chess.Move, int]]]:
    corner_kings = [chess.A8, chess.H8]
    support_kings = [
        chess.F7,
        chess.G7,
        chess.E6,
        chess.F6,
        chess.G6,
        chess.F5,
        chess.G5,
        chess.C7,
        chess.B7,
        chess.D6,
        chess.C6,
        chess.B6,
    ]

    for black_king in corner_kings:
        for white_king in support_kings:
            if chess.square_distance(white_king, black_king) <= 1:
                continue
            for white_queen in chess.SQUARES:
                if white_queen in (white_king, black_king):
                    continue
                board = kqk_board(white_king, white_queen, black_king, turn)
                if not board.is_valid() or board.is_game_over(claim_draw=False):
                    continue

                scores = root_scores(board, depth)
                if not scores:
                    continue
                root = max(score for _, score in scores)
                distinct = sorted(set(score for _, score in scores))
                best_moves = [move for move, score in scores if score == root]

                if turn == chess.WHITE:
                    positive_mates = sorted(set(score for _, score in scores if score > 20_000))
                    if root > 20_000 and len(positive_mates) >= 2 and len(best_moves) == 1:
                        return board, root, scores
                else:
                    if (
                        root < -20_000
                        and len(distinct) >= 2
                        and all(score < -20_000 for _, score in scores)
                        and len(best_moves) == 1
                    ):
                        return board, root, scores

    raise SystemExit(f"no fixture found for turn={turn} depth={depth}")


def format_scores(scores: list[tuple[chess.Move, int]]) -> str:
    return ",".join(f"{move.uci()}={score}" for move, score in sorted(scores, key=lambda item: item[0].uci()))


def main() -> None:
    shorter_board, shorter_root, shorter_scores = find_fixture(chess.WHITE, 5)
    survival_board, survival_root, survival_scores = find_fixture(chess.BLACK, 6)

    shorter_best = max(shorter_scores, key=lambda item: item[1])[0]
    survival_best = max(survival_scores, key=lambda item: item[1])[0]

    print(
        "MINED_SHORTER "
        f"fen={shorter_board.fen(en_passant='fen')} depth=5 score={shorter_root} "
        f"best={shorter_best.uci()} children=[{format_scores(shorter_scores)}]"
    )
    print(
        "MINED_SURVIVAL "
        f"fen={survival_board.fen(en_passant='fen')} depth=6 score={survival_root} "
        f"best={survival_best.uci()} children=[{format_scores(survival_scores)}]"
    )


if __name__ == "__main__":
    main()
