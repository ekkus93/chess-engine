"""Capture-order helpers shared by the main search module."""

from __future__ import annotations

from chess_game.chess.ai_search_helpers import defensive_capture_bonus
from chess_game.chess.board import Board
from chess_game.chess.constants import Color, ConstantSquare
from chess_game.chess.move import Move
from chess_game.chess.strategy_utils import is_capture_move, iter_color_pieces
from chess_game.chess.structure_recognition import structure_capture_bonus
from chess_game.chess.types import Piece, PieceType

_VICTIM_VALUES = {
    PieceType.PAWN: 10,
    PieceType.KNIGHT: 30,
    PieceType.BISHOP: 32,
    PieceType.ROOK: 35,
    PieceType.QUEEN: 90,
}

_ATTACKER_VALUES = {
    PieceType.PAWN: 10,
    PieceType.KNIGHT: 30,
    PieceType.BISHOP: 32,
    PieceType.ROOK: 35,
    PieceType.QUEEN: 90,
}
_LOOSE_SHELTER_PAWN_GRAB_PENALTY = 10_500
_PSEUDO_FORK_PAWN_RECAPTURE_PENALTY = 20_000


def capture_order_score(
    board: Board,
    move: Move,
    make_copy_with_move,
) -> int:
    """Return capture ordering score using MVV/LVA plus structural priorities."""

    captured_piece = board.get_piece(move.end)
    attacker = board.get_piece(move.start)
    if attacker is None or captured_piece is None:
        return 900 if is_capture_move(board, move) else 0
    return (
        _mvv_lva_capture_score(attacker, captured_piece)
        + defensive_capture_bonus(
            board,
            move,
            captured_piece.kind,
            make_copy_with_move,
        )
        + structure_capture_bonus(
            board,
            attacker.color,
            attacker.kind,
            captured_piece.kind,
            move.end,
        )
        - _shelter_loosening_pawn_grab_penalty(board, move, attacker, captured_piece)
        - _pseudo_fork_pawn_recapture_penalty(board, move, attacker, captured_piece)
    )


def _mvv_lva_capture_score(attacker: Piece, victim: Piece) -> int:
    """MVV/LVA score for a capture."""

    return (victim_value(victim.kind) * 1_000) - attacker_value(attacker.kind)


def victim_value(kind: PieceType) -> int:
    """Return the MVV/LVA victim priority value."""

    return _VICTIM_VALUES.get(kind, 0)


def attacker_value(kind: PieceType) -> int:
    """Return the MVV/LVA attacker priority value."""

    return _ATTACKER_VALUES.get(kind, 0)


def _pseudo_fork_pawn_recapture_penalty(
    board: Board,
    move: Move,
    attacker: Piece,
    captured_piece: Piece,
) -> int:
    """Penalise captures where the attacker immediately becomes en-prise to an enemy pawn.

    A 'pseudo-fork' occurs when a knight (or bishop) captures on a square defended by
    an enemy pawn, mistakenly believing the resulting position is favourable.  In game 2
    White played Nxe5 which was immediately answered by dxe5, losing a full piece.
    """

    if attacker.kind not in {PieceType.KNIGHT, PieceType.BISHOP}:
        return 0
    attacker_value_cp = attacker_value(attacker.kind) * 100
    captured_value_cp = victim_value(captured_piece.kind) * 100
    if attacker_value_cp <= captured_value_cp:
        return 0
    end_row = int(move.end.row)
    end_col = int(move.end.col)
    enemy_color = Color.BLACK if attacker.color == Color.WHITE else Color.WHITE
    pawn_attack_row = end_row - 1 if attacker.color == Color.WHITE else end_row + 1
    if pawn_attack_row < 0 or pawn_attack_row > 7:
        return 0
    for piece, row, col in iter_color_pieces(board, enemy_color):
        if piece.kind != PieceType.PAWN:
            continue
        if row != pawn_attack_row:
            continue
        if abs(col - end_col) == 1:
            return _PSEUDO_FORK_PAWN_RECAPTURE_PENALTY
    return 0


def _shelter_loosening_pawn_grab_penalty(
    board: Board,
    move: Move,
    attacker: Piece,
    captured_piece: Piece,
) -> int:
    if attacker.kind != PieceType.PAWN or captured_piece.kind != PieceType.PAWN:
        return 0
    king_square = board.find_king(attacker.color)
    if king_square is None or not _is_castled_king(attacker.color, king_square):
        return 0
    if not _is_shelter_pawn(attacker.color, king_square, move.start):
        return 0
    if int(move.start.col) == int(move.end.col):
        return 0
    if not _enemy_long_range_piece_present(board, attacker.color):
        return 0
    return _LOOSE_SHELTER_PAWN_GRAB_PENALTY


def _is_castled_king(color: Color, square: ConstantSquare) -> bool:
    row = int(square.row)
    col = int(square.col)
    return (color == Color.WHITE and row == 7 and col in {2, 6}) or (
        color == Color.BLACK and row == 0 and col in {2, 6}
    )


def _is_shelter_pawn(
    color: Color,
    king_square: ConstantSquare,
    pawn_square: ConstantSquare,
) -> bool:
    home_row = 6 if color == Color.WHITE else 1
    return int(pawn_square.row) == home_row and abs(
        int(pawn_square.col) - int(king_square.col)
    ) <= 1


def _enemy_long_range_piece_present(board: Board, color: Color) -> bool:
    enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
    return any(
        piece is not None
        and piece.color == enemy_color
        and piece.kind in {PieceType.BISHOP, PieceType.ROOK, PieceType.QUEEN}
        for row in board.board
        for piece in row
    )
