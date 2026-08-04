"""FEN parsing helpers for the Board class.

Extracted from ``board.py`` (module-level helpers kept out of the Board class to
keep its public method count low). ``Board.from_fen`` imports these. ``Board`` is
referenced only in type annotations, so it is imported under ``TYPE_CHECKING`` to
avoid a runtime import cycle with ``board.py``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from chess_game.chess.board.board_setup import create_piece
from chess_game.chess.constants import Color, ConstantSquare, get_square_constant
from chess_game.chess.coords import algebraic_to_index
from chess_game.chess.types import CastlingRights, GameMetadata, MoveCounters

if TYPE_CHECKING:
    from chess_game.chess.board.board import Board


def _fen_parse_fields(
    parts: list[str],
) -> tuple[str, str, str, str, int, int]:
    """Extract the six FEN fields from the already-split token list."""
    placement, turn_str = parts[0], parts[1]
    castling_str = parts[2] if len(parts) > 2 else "KQkq"
    ep_str = parts[3] if len(parts) > 3 else "-"
    halfmove = int(parts[4]) if len(parts) > 4 else 0
    fullmove = int(parts[5]) if len(parts) > 5 else 1
    return placement, turn_str, castling_str, ep_str, halfmove, fullmove


def _fen_init_state(
    board: Board,
    fields: tuple[str, str, str, str, int, int],
) -> None:
    """Populate a bare Board's __dict__ with the meta-state from FEN fields tuple."""
    _, turn_str, castling_str, ep_str, halfmove, fullmove = fields
    board.__dict__["turn"] = Color.WHITE if turn_str == "w" else Color.BLACK
    castling_rights = CastlingRights(
        white_kingside="K" in castling_str,
        white_queenside="Q" in castling_str,
        black_kingside="k" in castling_str,
        black_queenside="q" in castling_str,
    )
    ep_target: ConstantSquare | None = None
    if ep_str != "-":
        ep_target = algebraic_to_index(ep_str)
    board.__dict__["_state"] = GameMetadata(
        en_passant_target=ep_target,
        castling_rights=castling_rights,
        move_counters=MoveCounters(
            halfmove_clock=halfmove,
            fullmove_number=fullmove,
        ),
    )


def _fen_parse_placement(
    board: Board,
    fen_to_piece: dict,
    placement: str,
) -> None:
    """Parse the FEN piece-placement string onto *board*."""
    rank_strs = placement.split("/")
    if len(rank_strs) != 8:
        raise ValueError(f"FEN placement must have 8 ranks: {placement!r}")
    for row_idx, rank_str in enumerate(rank_strs):
        col_idx = 0
        for ch in rank_str:
            if ch.isdigit():
                col_idx += int(ch)
            else:
                color, kind = fen_to_piece[ch]
                sq = get_square_constant(row_idx, col_idx)
                board.__dict__["board"][row_idx][col_idx] = create_piece(
                    color, kind, sq
                )
                col_idx += 1
        if col_idx != 8:
            raise ValueError(
                f"FEN rank {row_idx} has wrong number of squares: {rank_str!r}"
            )
