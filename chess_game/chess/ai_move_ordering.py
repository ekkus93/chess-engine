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
QUIET_DEVELOPING_MINOR_BONUS = 26
QUIET_USEFUL_CHECK_BONUS = 34
QUIET_URGENT_LUFT_BONUS = 24
QUIET_EARLY_QUEEN_SORTIE_PENALTY = 32
QUIET_CONTEST_ATTACK_FILE_BONUS = 44


def quiet_strategy_order_score(board: Board, move: Move) -> int:
    """Return a bonus for strong quiet strategic moves."""

    if move.promotion is not None or is_capture_move(board, move):
        return 0
    piece = board.get_piece(move.start)
    if piece is None:
        return 0
    score = _centralization_bonus(piece.kind, move)
    score += _opening_discipline_bonus(board, piece.kind, move)
    score += _king_move_bonus(board, piece.kind, move)
    score += _heavy_piece_bonus(board, piece.kind, piece.color, move)
    score += _pawn_bonus(board, piece.color, piece.kind, move)
    if _improves_worst_piece(board, piece.kind, move):
        score += QUIET_WORST_PIECE_BONUS
    score += _check_quality_bonus(board, piece.kind, move)
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


def _opening_discipline_bonus(board: Board, kind: PieceType, move: Move) -> int:
    score = 0
    if kind in (PieceType.KNIGHT, PieceType.BISHOP) and _develops_minor_piece(move):
        score += QUIET_DEVELOPING_MINOR_BONUS
    if kind == PieceType.QUEEN and _is_early_queen_sortie(board, move):
        score -= QUIET_EARLY_QUEEN_SORTIE_PENALTY
    return score


def _king_move_bonus(board: Board, kind: PieceType, move: Move) -> int:
    score = 0
    if kind == PieceType.KING and _is_castling_move(move):
        score += QUIET_CASTLING_BONUS
    if kind == PieceType.KING and _is_heavy_piece_endgame(board):
        score += _king_centralization_bonus(move)
    return score


def _heavy_piece_bonus(board: Board, kind: PieceType, color: Color, move: Move) -> int:
    score = 0
    if _contests_attack_line(board, color, move):
        score += QUIET_CONTEST_ATTACK_FILE_BONUS
    if kind in (PieceType.ROOK, PieceType.QUEEN) and _lines_up_with_enemy_king(board, move):
        score += QUIET_HEAVY_PIECE_PRESSURE_BONUS
    if kind in (PieceType.ROOK, PieceType.QUEEN) and _improves_king_cutoff(board, move):
        score += QUIET_KING_CUTOFF_BONUS
    if kind in (PieceType.ROOK, PieceType.QUEEN) and _offers_major_piece_trade(board, move):
        score += QUIET_MAJOR_TRADE_OFFER_BONUS
    if kind == PieceType.ROOK and _moves_rook_behind_passer(board, color, move):
        score += QUIET_ROOK_BEHIND_PASSER_BONUS
    if kind in (PieceType.KING, PieceType.ROOK, PieceType.QUEEN) and _blockades_enemy_passer(
        board, color, move
    ):
        score += QUIET_BLOCKADE_BONUS
    return score


def _pawn_bonus(board: Board, color: Color, kind: PieceType, move: Move) -> int:
    score = 0
    if kind == PieceType.PAWN and _is_passed_pawn_push(board, color, move):
        score += QUIET_PASSED_PAWN_PUSH_BONUS + _pawn_push_progress(color, move)
    if kind == PieceType.PAWN and _creates_luft(color, move):
        score += QUIET_LUFT_BONUS
        if _is_urgent_luft(board, color):
            score += QUIET_URGENT_LUFT_BONUS
    return score


def _develops_minor_piece(move: Move) -> bool:
    start_row = int(move.start.row)
    end_row = int(move.end.row)
    start_col = int(move.start.col)
    end_col = int(move.end.col)
    return start_row in {0, 7} and end_row not in {0, 7} and center_distance(
        end_row, end_col
    ) < center_distance(start_row, start_col)


def _is_early_queen_sortie(board: Board, move: Move) -> bool:
    undeveloped = 0
    for row_index, row in enumerate(board.board):
        for col_index, piece in enumerate(row):
            if piece is None or piece.color != board.turn:
                continue
            if piece.kind == PieceType.KNIGHT and row_index in {0, 7} and col_index in {1, 6}:
                undeveloped += 1
            if piece.kind == PieceType.BISHOP and row_index in {0, 7} and col_index in {2, 5}:
                undeveloped += 1
    end_row = int(move.end.row)
    if board.turn == Color.WHITE:
        return undeveloped >= 2 and end_row <= 3
    return undeveloped >= 2 and end_row >= 4


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


def _is_urgent_luft(board: Board, color: Color) -> bool:
    king_square = next(
        (
            piece.square
            for row in board.board
            for piece in row
            if piece is not None and piece.color == color and piece.kind == PieceType.KING
        ),
        None,
    )
    if king_square is None or int(king_square.row) not in {0, 7}:
        return False
    enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
    return any(
        piece is not None
        and piece.color == enemy_color
        and piece.kind in (PieceType.QUEEN, PieceType.ROOK)
        for row in board.board
        for piece in row
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


def _contests_attack_line(board: Board, color: Color, move: Move) -> bool:
    king_square = next(
        (
            piece.square
            for row in board.board
            for piece in row
            if piece is not None and piece.color == color and piece.kind == PieceType.KING
        ),
        None,
    )
    if king_square is None:
        return False
    end_square = (int(move.end.row), int(move.end.col))
    king_row = int(king_square.row)
    king_col = int(king_square.col)
    enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
    for row_index, row in enumerate(board.board):
        for col_index, piece in enumerate(row):
            if (
                piece is None
                or piece.color != enemy_color
                or piece.kind not in (PieceType.ROOK, PieceType.QUEEN)
            ):
                continue
            attacker_square = (row_index, col_index)
            if not _attacks_king_line(attacker_square, (king_row, king_col)):
                continue
            if not path_clear_between(board, attacker_square, (king_row, king_col)):
                continue
            if _lies_between(attacker_square, (king_row, king_col), end_square):
                return True
    return False


def _attacks_king_line(
    attacker_square: tuple[int, int],
    king_square: tuple[int, int],
) -> bool:
    return (
        attacker_square[0] == king_square[0]
        or attacker_square[1] == king_square[1]
    )


def _lies_between(
    attacker_square: tuple[int, int],
    king_square: tuple[int, int],
    target_square: tuple[int, int],
) -> bool:
    if target_square in {attacker_square, king_square}:
        return False
    if attacker_square[0] == king_square[0] == target_square[0]:
        start_col = min(attacker_square[1], king_square[1])
        end_col = max(attacker_square[1], king_square[1])
        return start_col < target_square[1] < end_col
    if attacker_square[1] == king_square[1] == target_square[1]:
        start_row = min(attacker_square[0], king_square[0])
        end_row = max(attacker_square[0], king_square[0])
        return start_row < target_square[0] < end_row
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


def _check_quality_bonus(board: Board, kind: PieceType, move: Move) -> int:
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
        return 0
    if not _move_gives_check(board, kind, move, (int(enemy_king.row), int(enemy_king.col))):
        return 0
    return QUIET_USEFUL_CHECK_BONUS


def _move_gives_check(
    board: Board,
    kind: PieceType,
    move: Move,
    enemy_king: tuple[int, int],
) -> bool:
    end_row = int(move.end.row)
    end_col = int(move.end.col)
    row_delta = enemy_king[0] - end_row
    col_delta = enemy_king[1] - end_col
    delta = (row_delta, col_delta)
    gives_check = False
    if kind == PieceType.QUEEN:
        gives_check = _slider_gives_check(board, move, enemy_king, delta, queen=True)
    elif kind == PieceType.ROOK:
        gives_check = _slider_gives_check(board, move, enemy_king, delta, queen=False)
    elif kind == PieceType.BISHOP:
        gives_check = abs(row_delta) == abs(col_delta) and _path_clear_after_move(
            board, move, enemy_king
        )
    elif kind == PieceType.KNIGHT:
        gives_check = sorted((abs(row_delta), abs(col_delta))) == [1, 2]
    elif kind == PieceType.PAWN:
        direction = -1 if board.turn == Color.WHITE else 1
        gives_check = row_delta == direction and abs(col_delta) == 1
    elif kind == PieceType.KING:
        gives_check = max(abs(row_delta), abs(col_delta)) == 1
    return gives_check


def _slider_gives_check(
    board: Board,
    move: Move,
    enemy_king: tuple[int, int],
    delta: tuple[int, int],
    queen: bool,
) -> bool:
    row_delta, col_delta = delta
    if row_delta == 0 or col_delta == 0:
        return _path_clear_after_move(board, move, enemy_king)
    if queen and abs(row_delta) == abs(col_delta):
        return _path_clear_after_move(board, move, enemy_king)
    return False


def _path_clear_after_move(
    board: Board,
    move: Move,
    enemy_king: tuple[int, int],
) -> bool:
    start = (int(move.start.row), int(move.start.col))
    end = (int(move.end.row), int(move.end.col))
    row_step = 0 if end[0] == enemy_king[0] else (1 if enemy_king[0] > end[0] else -1)
    col_step = 0 if end[1] == enemy_king[1] else (1 if enemy_king[1] > end[1] else -1)
    current_row = end[0] + row_step
    current_col = end[1] + col_step
    while (current_row, current_col) != enemy_king:
        if (
            (current_row, current_col) != start
            and board.board[current_row][current_col] is not None
        ):
            return False
        current_row += row_step
        current_col += col_step
    return True
