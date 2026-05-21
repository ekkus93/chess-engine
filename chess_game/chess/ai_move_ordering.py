"""Helpers for scoring quiet strategic moves during search ordering."""

from chess_game.chess.board import Board
from chess_game.chess.move import Move
from chess_game.chess.strategy_utils import center_distance, is_capture_move, path_clear_between
from chess_game.chess.types import Color, PieceType

QUIET_CASTLING_BONUS = 160
QUIET_PASSED_PAWN_PUSH_BONUS = 90
QUIET_KING_CENTRALIZATION_BONUS = 18
QUIET_HEAVY_PIECE_PRESSURE_BONUS = 24
QUIET_CENTRALIZATION_BONUS = 12
QUIET_KING_CUTOFF_BONUS = 32
QUIET_ROOK_BEHIND_PASSER_BONUS = 40
QUIET_LUFT_BONUS = 16
QUIET_WORST_PIECE_BONUS = 18
QUIET_BLOCKADE_BONUS = 28
QUIET_MAJOR_TRADE_OFFER_BONUS = 26


def quiet_strategy_order_score(board: Board, move: Move) -> int:
    """Return a bonus for strong quiet strategic moves."""

    if move.promotion is not None or is_capture_move(board, move):
        return 0
    piece = board.get_piece(move.start)
    if piece is None:
        return 0
    score = _centralization_bonus(piece.kind, move)
    if piece.kind == PieceType.KING and _is_castling_move(move):
        score += QUIET_CASTLING_BONUS
    if piece.kind == PieceType.KING and _is_heavy_piece_endgame(board):
        score += _king_centralization_bonus(move)
    if piece.kind == PieceType.PAWN and _is_passed_pawn_push(board, piece.color, move):
        score += QUIET_PASSED_PAWN_PUSH_BONUS + _pawn_push_progress(piece.color, move)
    if piece.kind in (PieceType.ROOK, PieceType.QUEEN) and _lines_up_with_enemy_king(board, move):
        score += QUIET_HEAVY_PIECE_PRESSURE_BONUS
    if piece.kind in (PieceType.ROOK, PieceType.QUEEN) and _improves_king_cutoff(board, move):
        score += QUIET_KING_CUTOFF_BONUS
    if piece.kind in (PieceType.ROOK, PieceType.QUEEN) and _offers_major_piece_trade(board, move):
        score += QUIET_MAJOR_TRADE_OFFER_BONUS
    if piece.kind == PieceType.ROOK and _moves_rook_behind_passer(board, piece.color, move):
        score += QUIET_ROOK_BEHIND_PASSER_BONUS
    if piece.kind in (PieceType.KING, PieceType.ROOK, PieceType.QUEEN) and _blockades_enemy_passer(
        board, piece.color, move
    ):
        score += QUIET_BLOCKADE_BONUS
    if piece.kind == PieceType.PAWN and _creates_luft(piece.color, move):
        score += QUIET_LUFT_BONUS
    if _improves_worst_piece(board, piece.kind, move):
        score += QUIET_WORST_PIECE_BONUS
    return score


def _centralization_bonus(kind: PieceType, move: Move) -> int:
    """Return a bonus for improving piece placement toward useful squares."""

    if kind == PieceType.ROOK:
        return _line_piece_bonus(move)
    if kind == PieceType.QUEEN:
        return _line_piece_bonus(move) // 2
    if kind in (PieceType.KNIGHT, PieceType.BISHOP):
        return _minor_piece_centralization(move)
    return 0


def _line_piece_bonus(move: Move) -> int:
    """Score rook/queen moves by improving central file or rank pressure."""

    start_distance = center_distance(int(move.start.row), int(move.start.col))
    end_distance = center_distance(int(move.end.row), int(move.end.col))
    return max(0, start_distance - end_distance) * QUIET_CENTRALIZATION_BONUS


def _minor_piece_centralization(move: Move) -> int:
    """Score quiet minor-piece moves by centralization gain."""

    start_distance = center_distance(int(move.start.row), int(move.start.col))
    end_distance = center_distance(int(move.end.row), int(move.end.col))
    return max(0, start_distance - end_distance) * QUIET_CENTRALIZATION_BONUS


def _is_castling_move(move: Move) -> bool:
    """Return True for king-side or queen-side castling geometry."""

    return int(move.start.col) == 4 and abs(int(move.start.col) - int(move.end.col)) == 2


def _is_heavy_piece_endgame(board: Board) -> bool:
    """Return True in simple endings where king centralization matters more."""

    non_king_pieces = [
        piece.kind
        for row in board.board
        for piece in row
        if piece is not None and piece.kind != PieceType.KING
    ]
    return len(non_king_pieces) <= 4


def _king_centralization_bonus(move: Move) -> int:
    """Reward king steps toward the center in quiet endgames."""

    start_distance = center_distance(int(move.start.row), int(move.start.col))
    end_distance = center_distance(int(move.end.row), int(move.end.col))
    return max(0, start_distance - end_distance) * QUIET_KING_CENTRALIZATION_BONUS


def _is_passed_pawn_push(board: Board, color: Color, move: Move) -> bool:
    """Return True when a quiet pawn push advances a passed pawn candidate."""

    if int(move.start.col) != int(move.end.col):
        return False
    start_row = int(move.start.row)
    end_row = int(move.end.row)
    if color == Color.WHITE and end_row >= start_row:
        return False
    if color == Color.BLACK and end_row <= start_row:
        return False
    enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
    for row_index, row in enumerate(board.board):
        for col_index, piece in enumerate(row):
            if (
                piece is not None
                and piece.color == enemy_color
                and piece.kind == PieceType.PAWN
                and abs(col_index - int(move.end.col)) <= 1
            ):
                if color == Color.WHITE and row_index < end_row:
                    return False
                if color == Color.BLACK and row_index > end_row:
                    return False
    return True


def _pawn_push_progress(color: Color, move: Move) -> int:
    """Return a bonus scaled by how advanced the pawn push becomes."""

    end_row = int(move.end.row)
    progress = 6 - end_row if color == Color.WHITE else end_row - 1
    return progress * 4


def _lines_up_with_enemy_king(board: Board, move: Move) -> bool:
    """Return True when a heavy piece move increases pressure on the enemy king."""

    enemy_color = Color.BLACK if board.turn == Color.WHITE else Color.WHITE
    enemy_king = next(
        (
            piece.square
            for row in board.board
            for piece in row
            if piece is not None
            and piece.color == enemy_color
            and piece.kind == PieceType.KING
        ),
        None,
    )
    if enemy_king is None:
        return False
    return int(move.end.row) == int(enemy_king.row) or int(move.end.col) == int(enemy_king.col)


def _improves_king_cutoff(board: Board, move: Move) -> bool:
    enemy_color = Color.BLACK if board.turn == Color.WHITE else Color.WHITE
    enemy_king = next(
        (
            piece.square
            for row in board.board
            for piece in row
            if piece is not None
            and piece.color == enemy_color
            and piece.kind == PieceType.KING
        ),
        None,
    )
    if enemy_king is None:
        return False
    start_same_line = (
        int(move.start.row) == int(enemy_king.row)
        or int(move.start.col) == int(enemy_king.col)
    )
    end_same_line = (
        int(move.end.row) == int(enemy_king.row)
        or int(move.end.col) == int(enemy_king.col)
    )
    return not start_same_line and end_same_line


def _moves_rook_behind_passer(board: Board, color: Color, move: Move) -> bool:
    for row_index, row in enumerate(board.board):
        for col_index, piece in enumerate(row):
            if piece is None or piece.color != color or piece.kind != PieceType.PAWN:
                continue
            if not _is_passed_pawn_candidate(board, color, row_index, col_index):
                continue
            if int(move.end.col) != col_index:
                continue
            if color == Color.WHITE and int(move.end.row) > row_index:
                return True
            if color == Color.BLACK and int(move.end.row) < row_index:
                return True
    return False


def _is_passed_pawn_candidate(board: Board, color: Color, row: int, col: int) -> bool:
    enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
    for row_index, board_row in enumerate(board.board):
        for col_index, piece in enumerate(board_row):
            if (
                piece is not None
                and piece.color == enemy_color
                and piece.kind == PieceType.PAWN
                and abs(col_index - col) <= 1
            ):
                if color == Color.WHITE and row_index < row:
                    return False
                if color == Color.BLACK and row_index > row:
                    return False
    return True


def _creates_luft(color: Color, move: Move) -> bool:
    home_row = 6 if color == Color.WHITE else 1
    return (
        int(move.start.row) == home_row
        and int(move.start.col) in {5, 6, 7}
        and abs(int(move.end.row) - int(move.start.row)) == 1
    )


def _improves_worst_piece(board: Board, kind: PieceType, move: Move) -> bool:
    if kind not in (PieceType.ROOK, PieceType.QUEEN, PieceType.BISHOP, PieceType.KNIGHT):
        return False
    moving_piece_distance = center_distance(int(move.start.row), int(move.start.col))
    end_distance = center_distance(int(move.end.row), int(move.end.col))
    if end_distance >= moving_piece_distance:
        return False
    color = board.turn
    worst_distance = max(
        (
            center_distance(row_index, col_index)
            for row_index, row in enumerate(board.board)
            for col_index, piece in enumerate(row)
            if piece is not None
            and piece.color == color
            and piece.kind == kind
        ),
        default=moving_piece_distance,
    )
    return moving_piece_distance >= worst_distance


def _offers_major_piece_trade(board: Board, move: Move) -> bool:
    if not _is_materially_ahead(board, board.turn):
        return False
    enemy_color = Color.BLACK if board.turn == Color.WHITE else Color.WHITE
    enemy_targets = {
        (row_index, col_index)
        for row_index, row in enumerate(board.board)
        for col_index, piece in enumerate(row)
        if (
            piece is not None
            and piece.color == enemy_color
            and piece.kind in (PieceType.ROOK, PieceType.QUEEN)
        )
    }
    if not enemy_targets:
        return False
    return _attacks_any_target(board, move, enemy_targets)


def _blockades_enemy_passer(board: Board, color: Color, move: Move) -> bool:
    enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
    target_square = (int(move.end.row), int(move.end.col))
    for row_index, board_row in enumerate(board.board):
        for col_index, piece in enumerate(board_row):
            if piece is None or piece.color != enemy_color or piece.kind != PieceType.PAWN:
                continue
            if not _is_passed_pawn_candidate(board, enemy_color, row_index, col_index):
                continue
            blockade_row = row_index + (-1 if enemy_color == Color.WHITE else 1)
            if target_square == (blockade_row, col_index):
                return True
    return False


def _is_materially_ahead(board: Board, color: Color) -> bool:
    own_material = 0
    enemy_material = 0
    for row in board.board:
        for piece in row:
            if piece is None or piece.kind == PieceType.KING:
                continue
            value = _piece_value(piece.kind)
            if piece.color == color:
                own_material += value
            else:
                enemy_material += value
    return own_material > enemy_material


def _attacks_any_target(
    board: Board,
    move: Move,
    enemy_targets: set[tuple[int, int]],
) -> bool:
    start_row = int(move.start.row)
    start_col = int(move.start.col)
    end_row = int(move.end.row)
    end_col = int(move.end.col)
    piece = board.board[start_row][start_col]
    if piece is None:
        return False
    for target_row, target_col in enemy_targets:
        row_delta = target_row - end_row
        col_delta = target_col - end_col
        if piece.kind == PieceType.ROOK and _rook_attacks_delta(row_delta, col_delta):
            if not path_clear_between(board, (end_row, end_col), (target_row, target_col)):
                continue
            return True
        if piece.kind == PieceType.QUEEN and _queen_attacks_delta(row_delta, col_delta):
            if not path_clear_between(board, (end_row, end_col), (target_row, target_col)):
                continue
            return True
    return False


def _rook_attacks_delta(row_delta: int, col_delta: int) -> bool:
    return row_delta == 0 or col_delta == 0


def _queen_attacks_delta(row_delta: int, col_delta: int) -> bool:
    return _rook_attacks_delta(row_delta, col_delta) or abs(row_delta) == abs(col_delta)


def _piece_value(kind: PieceType) -> int:
    if kind == PieceType.PAWN:
        return 100
    if kind == PieceType.KNIGHT:
        return 320
    if kind == PieceType.BISHOP:
        return 330
    if kind == PieceType.ROOK:
        return 500
    if kind == PieceType.QUEEN:
        return 900
    return 0
