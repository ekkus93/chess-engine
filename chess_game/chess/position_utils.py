"""Helpers for generating repetition-safe position identifiers."""

from __future__ import annotations

from typing import TYPE_CHECKING

from chess_game.chess.coords import index_to_algebraic
from chess_game.chess.types import Color, PieceType

if TYPE_CHECKING:
    from chess_game.chess.board import Board


def position_key(board: "Board") -> str:
    """Generate a position key using board state relevant to repetition."""

    pieces: list[str] = []
    for row in board.board:
        for piece in row:
            if piece is None:
                pieces.append(".")
                continue
            color_char = "w" if piece.color == Color.WHITE else "b"
            kind_char = {
                PieceType.PAWN: "p",
                PieceType.KNIGHT: "n",
                PieceType.BISHOP: "b",
                PieceType.ROOK: "r",
                PieceType.QUEEN: "q",
                PieceType.KING: "k",
            }[piece.kind]
            pieces.append(f"{color_char}{kind_char}")

    turn_char = "w" if board.turn == Color.WHITE else "b"
    castling = ""
    if board.castling_rights.white_kingside:
        castling += "K"
    if board.castling_rights.white_queenside:
        castling += "Q"
    if board.castling_rights.black_kingside:
        castling += "k"
    if board.castling_rights.black_queenside:
        castling += "q"
    ep_target = (
        "-"
        if board.en_passant_target is None
        else index_to_algebraic(board.en_passant_target)
    )
    return "".join(pieces) + "|" + turn_char + "|" + (castling or "-") + "|" + ep_target
