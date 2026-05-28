"""Shared piece-coordination heuristics for quiet move ordering."""

from dataclasses import dataclass

from chess_game.chess.board import Board
from chess_game.chess.board.attack_utils import piece_attacks_square
from chess_game.chess.constants import ConstantSquare
from chess_game.chess.defensive_priorities import (
    DANGEROUS_KING_PRESSURE_THRESHOLD,
    king_danger_index,
)
from chess_game.chess.move import Move
from chess_game.chess.pieces.piece_movers import PieceMovers
from chess_game.chess.strategy_utils import center_distance, path_clear_between
from chess_game.chess.types import Color, PieceType


@dataclass(frozen=True)
class PiecePlacementProfile:
    """Track how misplaced a strategic piece currently is."""

    kind: PieceType
    square: object
    score: int


def improves_worst_piece(board: Board, move: Move) -> bool:
    """Return True when a legal move meaningfully improves the current worst piece."""

    moving_piece = board.get_piece(move.start)
    if moving_piece is None or moving_piece.kind not in _STRATEGIC_PIECES:
        return False
    color = board.turn
    profiles = _piece_placement_profiles(board, color)
    if not profiles:
        return False
    moving_profile = next(
        (profile for profile in profiles if profile.square == move.start),
        None,
    )
    if moving_profile is None:
        return False
    child_board = board.clone()
    if not child_board.apply_legal_move(move.start, move.end, promotion=move.promotion):
        return False
    moved_piece = child_board.get_piece(move.end)
    if moved_piece is None:
        return False
    worst_score = max(profile.score for profile in profiles)
    improved_score = _piece_misplacement_score(
        child_board,
        color,
        moved_piece,
        int(move.end.row),
        int(move.end.col),
    )
    return moving_profile.score >= worst_score and moving_profile.score - improved_score >= 4


def rook_coordination_bonus(board: Board, color: Color, move: Move) -> int:
    """Reward rook moves that reconnect heavy pieces."""

    moving_piece = board.get_piece(move.start)
    if moving_piece is None or moving_piece.kind != PieceType.ROOK:
        return 0
    if _rook_is_connected(board, color, move.start):
        return 0
    child_board = board.clone()
    if not child_board.apply_legal_move(move.start, move.end, promotion=move.promotion):
        return 0
    if _rook_is_connected(child_board, color, move.end):
        return 20
    return 0


def bishop_coordination_bonus(board: Board, move: Move) -> int:
    """Reward bishop reroutes that unlock long-diagonal activity."""

    moving_piece = board.get_piece(move.start)
    if moving_piece is None or moving_piece.kind != PieceType.BISHOP:
        return 0
    child_board = board.clone()
    if not child_board.apply_legal_move(move.start, move.end, promotion=move.promotion):
        return 0
    moved_piece = child_board.get_piece(move.end)
    if moved_piece is None:
        return 0
    before_mobility = len(PieceMovers.get_valid_moves(moving_piece, board))
    after_mobility = len(PieceMovers.get_valid_moves(moved_piece, child_board))
    if (
        not _on_long_diagonal(int(move.start.row), int(move.start.col))
        and _on_long_diagonal(int(move.end.row), int(move.end.col))
        and after_mobility >= before_mobility
    ):
        return 18 + max(0, after_mobility - before_mobility)
    return 0


def queen_coordination_bonus(board: Board, color: Color, move: Move) -> int:
    """Reward queen moves that improve support for the whole position."""

    moving_piece = board.get_piece(move.start)
    if moving_piece is None or moving_piece.kind != PieceType.QUEEN:
        return 0
    child_board = board.clone()
    if not child_board.apply_legal_move(move.start, move.end, promotion=move.promotion):
        return 0
    before_support = _supported_friendly_piece_count(board, color, move.start)
    after_support = _supported_friendly_piece_count(child_board, color, move.end)
    before_rook_links = _connected_rook_count(board, color)
    after_rook_links = _connected_rook_count(child_board, color)
    support_gain = max(0, after_support - before_support)
    rook_link_gain = max(0, after_rook_links - before_rook_links)
    return support_gain * 10 + rook_link_gain * 18


_STRATEGIC_PIECES = {
    PieceType.ROOK,
    PieceType.QUEEN,
    PieceType.BISHOP,
    PieceType.KNIGHT,
}


def _piece_placement_profiles(board: Board, color: Color) -> list[PiecePlacementProfile]:
    profiles: list[PiecePlacementProfile] = []
    for row_index, row in enumerate(board.board):
        for col_index, piece in enumerate(row):
            if piece is None or piece.color != color or piece.kind not in _STRATEGIC_PIECES:
                continue
            profiles.append(
                PiecePlacementProfile(
                    kind=piece.kind,
                    square=piece.square,
                    score=_piece_misplacement_score(
                        board,
                        color,
                        piece,
                        row_index,
                        col_index,
                    ),
                )
            )
    return profiles


def _piece_misplacement_score(
    board: Board,
    color: Color,
    piece,
    row: int,
    col: int,
) -> int:
    mobility = len(PieceMovers.get_valid_moves(piece, board))
    score = max(0, _target_piece_mobility(piece.kind) - mobility) * 3
    score += _theater_distance_penalty(piece.kind, row, col)
    score += _coordination_penalty(board, color, piece.kind, piece.square)
    score += _blocked_line_penalty(piece.kind, row, col, mobility)
    if king_danger_index(board, color) >= DANGEROUS_KING_PRESSURE_THRESHOLD:
        score += _king_distance_penalty(board, color, row, col)
    return score


def _target_piece_mobility(kind: PieceType) -> int:
    targets = {
        PieceType.KNIGHT: 5,
        PieceType.BISHOP: 6,
        PieceType.ROOK: 5,
        PieceType.QUEEN: 8,
    }
    return targets.get(kind, 0)


def _theater_distance_penalty(kind: PieceType, row: int, col: int) -> int:
    distance = center_distance(row, col)
    if kind in {PieceType.BISHOP, PieceType.KNIGHT}:
        return distance * 3
    return distance * 2


def _coordination_penalty(board: Board, color: Color, kind: PieceType, square) -> int:
    penalty = 0
    if not square_has_friendly_support(board, color, square):
        penalty += 4
    if kind == PieceType.ROOK and not _rook_is_connected(board, color, square):
        penalty += 8
    return penalty


def _blocked_line_penalty(kind: PieceType, row: int, col: int, mobility: int) -> int:
    if kind == PieceType.BISHOP:
        penalty = 0 if _on_long_diagonal(row, col) else 4
        return penalty + max(0, 5 - mobility) * 2
    if kind == PieceType.ROOK:
        return max(0, 4 - mobility) * 2
    if kind == PieceType.QUEEN:
        return max(0, 6 - mobility) * 2
    return max(0, 4 - mobility) * 2


def _rook_is_connected(board: Board, color: Color, square) -> bool:
    start = (int(square.row), int(square.col))
    for row_index, row in enumerate(board.board):
        for col_index, piece in enumerate(row):
            if (
                piece is None
                or piece.color != color
                or piece.kind != PieceType.ROOK
                or (row_index, col_index) == start
            ):
                continue
            target = (row_index, col_index)
            if (start[0] == target[0] or start[1] == target[1]) and path_clear_between(
                board,
                start,
                target,
            ):
                return True
    return False


def _king_distance_penalty(board: Board, color: Color, row: int, col: int) -> int:
    king_square = next(
        (
            piece.square
            for board_row in board.board
            for piece in board_row
            if piece is not None and piece.color == color and piece.kind == PieceType.KING
        ),
        None,
    )
    if king_square is None:
        return 0
    return max(
        abs(int(king_square.row) - row),
        abs(int(king_square.col) - col),
    )


def _on_long_diagonal(row: int, col: int) -> bool:
    return row == col or row + col == 7


def square_has_friendly_support(
    board: Board,
    color: Color,
    target_square: ConstantSquare,
) -> bool:
    """Return True when a friendly piece already protects the target square."""

    for row in board.board:
        for piece in row:
            if piece is None or piece.color != color or piece.square == target_square:
                continue
            if piece.square is not None and piece_attacks_square(
                piece,
                piece.square,
                target_square,
                board,
            ):
                return True
    return False


def _supported_friendly_piece_count(
    board: Board,
    color: Color,
    queen_square: ConstantSquare,
) -> int:
    queen = board.get_piece(queen_square)
    if queen is None:
        return 0
    count = 0
    for row in board.board:
        for piece in row:
            if (
                piece is None
                or piece.color != color
                or piece.square == queen_square
                or piece.square is None
                or piece.kind == PieceType.PAWN
            ):
                continue
            if _shares_support_line(queen_square, piece.square) and path_clear_between(
                board,
                (int(queen_square.row), int(queen_square.col)),
                (int(piece.square.row), int(piece.square.col)),
            ):
                count += 1
    return count


def _connected_rook_count(board: Board, color: Color) -> int:
    """Return how many friendly rooks are currently connected to another rook."""

    rooks = [
        piece.square
        for row in board.board
        for piece in row
        if piece is not None and piece.color == color and piece.kind == PieceType.ROOK
    ]
    return sum(1 for square in rooks if _rook_is_connected(board, color, square))


def _shares_support_line(start_square, end_square) -> bool:
    """Return True when two squares lie on the same rook or bishop support line."""

    start_row = int(start_square.row)
    start_col = int(start_square.col)
    end_row = int(end_square.row)
    end_col = int(end_square.col)
    return (
        start_row == end_row
        or start_col == end_col
        or abs(start_row - end_row) == abs(start_col - end_col)
    )
