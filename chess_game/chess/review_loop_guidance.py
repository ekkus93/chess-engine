"""Narrow guidance for recurring practical misses from review transcripts."""

from chess_game.chess.board import Board
from chess_game.chess.strategy_utils import (
    both_queens_on_board,
    non_king_piece_kinds,
    opposite_color,
    pawn_supports_square,
)
from chess_game.chess.types import Color, PieceType

_MIN_REVIEW_PIECES = 22
_MAX_REVIEW_PIECES = 28
_WING_KNIGHT_LUNGE_PENALTY = 28
_BLOCKED_ROOK_SIDESTEP_PENALTY = 24
_CASTLED_FLANK_MARCH_PENALTY = 18
_BROKEN_SHELTER_PENALTY = 12
_ROOT_REVIEW_SCALE = 6


def review_loop_evaluation_score(board: Board) -> int:
    """Return transcript-driven practical penalties for live review-loop themes."""

    if not _is_relevant_review_loop_board(board):
        return 0
    white_penalty = _review_penalty_for_color(board, Color.WHITE)
    black_penalty = _review_penalty_for_color(board, Color.BLACK)
    return black_penalty - white_penalty


def review_loop_root_bonus(board: Board, child_board: Board, color: Color) -> int:
    """Return a root-only bonus for reducing transcript-style practical drift."""

    if not (
        _is_relevant_review_loop_board(board)
        or _is_relevant_review_loop_board(child_board)
    ):
        return 0
    before = _review_penalty_for_color(board, color)
    after = _review_penalty_for_color(child_board, color)
    enemy = opposite_color(color)
    before_enemy = _review_penalty_for_color(board, enemy)
    after_enemy = _review_penalty_for_color(child_board, enemy)
    return (before - after + after_enemy - before_enemy) * _ROOT_REVIEW_SCALE


def _is_relevant_review_loop_board(board: Board) -> bool:
    piece_count = len(non_king_piece_kinds(board))
    return (
        both_queens_on_board(board)
        and _MIN_REVIEW_PIECES <= piece_count <= _MAX_REVIEW_PIECES
    )


def _review_penalty_for_color(board: Board, color: Color) -> int:
    return (
        _wing_knight_lunge_penalty(board, color)
        + _blocked_rook_sidestep_penalty(board, color)
        + _castled_flank_march_penalty(board, color)
    )


def _wing_knight_lunge_penalty(board: Board, color: Color) -> int:
    penalty = 0
    enemy = opposite_color(color)
    for row_index, row in enumerate(board.board):
        for col_index, piece in enumerate(row):
            if piece is None or piece.color != color or piece.kind != PieceType.KNIGHT:
                continue
            if not _is_advanced_wing_knight(color, row_index, col_index):
                continue
            if _supported_by_pawn(board, color, row_index, col_index):
                continue
            if _edge_pawn_can_chase(board, enemy, col_index):
                penalty += _WING_KNIGHT_LUNGE_PENALTY
    return penalty


def _blocked_rook_sidestep_penalty(board: Board, color: Color) -> int:
    sidestep_squares = {(7, 1), (7, 6)} if color == Color.WHITE else {(0, 1), (0, 6)}
    pawn_row = 6 if color == Color.WHITE else 1
    penalty = 0
    for row_index, col_index in sidestep_squares:
        piece = board.board[row_index][col_index]
        if piece is None or piece.color != color or piece.kind != PieceType.ROOK:
            continue
        blocker = board.board[pawn_row][col_index]
        if blocker is not None and blocker.color == color and blocker.kind == PieceType.PAWN:
            penalty += _BLOCKED_ROOK_SIDESTEP_PENALTY
    return penalty


def _castled_flank_march_penalty(board: Board, color: Color) -> int:
    king_square = board.find_king(color)
    if king_square is None:
        return 0
    king_row = int(king_square.row)
    king_col = int(king_square.col)
    if (color == Color.WHITE and (king_row, king_col) != (7, 6)) or (
        color == Color.BLACK and (king_row, king_col) != (0, 6)
    ):
        return 0
    kingside_pawn_row = _most_advanced_pawn_row(board, color, {6, 7})
    h_pawn_row = _pawn_row(board, color, 7)
    penalty = 0
    if kingside_pawn_row is not None and _pawn_is_overextended(color, kingside_pawn_row):
        penalty += _CASTLED_FLANK_MARCH_PENALTY
    if h_pawn_row is None or _pawn_is_overextended(color, h_pawn_row):
        penalty += _BROKEN_SHELTER_PENALTY
    return penalty


def _is_advanced_wing_knight(color: Color, row: int, col: int) -> bool:
    if col not in {1, 6}:
        return False
    if color == Color.WHITE:
        return row <= 3
    return row >= 4


def _supported_by_pawn(board: Board, color: Color, row: int, col: int) -> bool:
    return pawn_supports_square(board, color, row, col)


def _edge_pawn_can_chase(board: Board, color: Color, col: int) -> bool:
    file_col = 0 if col == 1 else 7
    home_row = 6 if color == Color.WHITE else 1
    candidate_rows = (home_row, home_row - 1) if color == Color.WHITE else (home_row, home_row + 1)
    for candidate_row in candidate_rows:
        if not 0 <= candidate_row < 8:
            continue
        piece = board.board[candidate_row][file_col]
        if piece is not None and piece.color == color and piece.kind == PieceType.PAWN:
            return True
    return False


def _pawn_row(board: Board, color: Color, col: int) -> int | None:
    for row in range(8):
        piece = board.board[row][col]
        if piece is not None and piece.color == color and piece.kind == PieceType.PAWN:
            return row
    return None


def _most_advanced_pawn_row(board: Board, color: Color, cols: set[int]) -> int | None:
    rows: list[int] = []
    for row in range(8):
        for col in cols:
            piece = board.board[row][col]
            if piece is not None and piece.color == color and piece.kind == PieceType.PAWN:
                rows.append(row)
    if not rows:
        return None
    return min(rows) if color == Color.WHITE else max(rows)


def _pawn_is_overextended(color: Color, row: int) -> bool:
    return row <= 3 if color == Color.WHITE else row >= 4
