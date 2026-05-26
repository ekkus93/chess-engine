"""Opening-specific quiet move-order heuristics."""

from chess_game.chess.board import Board
from chess_game.chess.defensive_priorities import king_needs_shelter
from chess_game.chess.move import Move
from chess_game.chess.opening_guidance import opening_guidance_bonus
from chess_game.chess.strategy_utils import center_distance
from chess_game.chess.types import Color, PieceType

QUIET_DEVELOPING_MINOR_BONUS = 30
QUIET_EARLY_QUEEN_SORTIE_PENALTY = 32
QUIET_FLANK_RAID_PENALTY = 28
QUIET_REPEAT_HEAVY_PIECE_PENALTY = 24
QUIET_FLANK_PAWN_POKE_PENALTY = 18
QUIET_EARLY_ROOK_WANDER_PENALTY = 18
QUIET_UNCASTLED_HOME_RANK_ROOK_PENALTY = 24
QUIET_RIM_KNIGHT_DEVELOPMENT_PENALTY = 24
QUIET_KINGSIDE_FLANK_LUNGE_PENALTY = 24
QUIET_OPENING_CASTLING_URGENCY_BONUS = 40
QUIET_PREMATURE_KING_WALK_PENALTY = 20
QUIET_FINISH_DEVELOPMENT_BONUS = 18
QUIET_OPENING_CENTRAL_ROOK_BONUS = 18
QUIET_EARLY_QUEEN_DRIFT_PENALTY = 16
QUIET_UNSETTLED_RIM_KNIGHT_PENALTY = 18


def opening_discipline_order_score(board: Board, kind: PieceType, move: Move) -> int:
    """Return opening-phase bonuses and penalties for a quiet move."""

    score = opening_guidance_bonus(board, board.turn, kind, move)
    if kind in (PieceType.KNIGHT, PieceType.BISHOP):
        score += _minor_opening_discipline_score(board, kind, move)
    elif kind == PieceType.KING:
        score += _king_opening_discipline_score(board, move)
    elif kind in {PieceType.QUEEN, PieceType.ROOK, PieceType.PAWN}:
        score += _heavy_or_pawn_opening_discipline_score(board, kind, move)
    return score


def _minor_opening_discipline_score(board: Board, kind: PieceType, move: Move) -> int:
    undeveloped = undeveloped_minor_count(board)
    unsettled_king = _opening_king_unsettled(board)
    score = 0
    if _develops_minor_piece(move):
        score += QUIET_DEVELOPING_MINOR_BONUS
        if undeveloped <= 2:
            score += QUIET_FINISH_DEVELOPMENT_BONUS
    if kind == PieceType.KNIGHT and _is_early_rim_knight_development(
        board,
        move,
        undeveloped,
        king_needs_shelter(board, board.turn) or unsettled_king,
    ):
        score -= QUIET_RIM_KNIGHT_DEVELOPMENT_PENALTY
        if unsettled_king:
            score -= QUIET_UNSETTLED_RIM_KNIGHT_PENALTY
    return score


def _king_opening_discipline_score(board: Board, move: Move) -> int:
    if _is_castling_move(move) and _opening_king_unsettled(board):
        return QUIET_OPENING_CASTLING_URGENCY_BONUS
    if _is_premature_king_walk(board, move, king_needs_shelter(board, board.turn)):
        return -QUIET_PREMATURE_KING_WALK_PENALTY
    return 0


def _heavy_or_pawn_opening_discipline_score(board: Board, kind: PieceType, move: Move) -> int:
    if kind == PieceType.PAWN and int(move.end.col) not in {0, 1, 6, 7}:
        return 0
    undeveloped = undeveloped_minor_count(board)
    needs_shelter = king_needs_shelter(board, board.turn) or _opening_king_unsettled(board)
    score = 0
    if kind == PieceType.QUEEN and _is_early_queen_sortie(board, move, undeveloped):
        score -= QUIET_EARLY_QUEEN_SORTIE_PENALTY
    if kind == PieceType.QUEEN and _is_early_queen_drift(
        board,
        move,
        undeveloped,
        needs_shelter,
    ):
        score -= QUIET_EARLY_QUEEN_DRIFT_PENALTY
    if kind in {PieceType.QUEEN, PieceType.ROOK} and _is_flank_raid(
        board,
        move,
        undeveloped,
        needs_shelter,
    ):
        score -= QUIET_FLANK_RAID_PENALTY
    if kind in {PieceType.QUEEN, PieceType.ROOK} and is_repeat_heavy_piece_move(
        board,
        kind,
        move,
        undeveloped,
        needs_shelter,
    ):
        score -= QUIET_REPEAT_HEAVY_PIECE_PENALTY
    if kind == PieceType.PAWN and _is_early_flank_pawn_poke(
        board,
        move,
        undeveloped,
        needs_shelter,
    ):
        score -= QUIET_FLANK_PAWN_POKE_PENALTY
    if kind == PieceType.PAWN and _is_kingside_flank_lunge(
        board,
        move,
        undeveloped,
        needs_shelter,
    ):
        score -= QUIET_KINGSIDE_FLANK_LUNGE_PENALTY
    if kind == PieceType.ROOK and _is_early_rook_wander(
        board,
        move,
        undeveloped,
        needs_shelter,
    ):
        score -= QUIET_EARLY_ROOK_WANDER_PENALTY
    if kind == PieceType.ROOK and _is_uncastled_home_rank_rook_sidestep(
        board,
        move,
        undeveloped,
        needs_shelter,
    ):
        score -= QUIET_UNCASTLED_HOME_RANK_ROOK_PENALTY
    if kind == PieceType.ROOK and _is_opening_central_rook_move(
        board,
        move,
        undeveloped,
        needs_shelter,
    ):
        score += QUIET_OPENING_CENTRAL_ROOK_BONUS
    return score


def _develops_minor_piece(move: Move) -> bool:
    start_row = int(move.start.row)
    end_row = int(move.end.row)
    start_col = int(move.start.col)
    end_col = int(move.end.col)
    return start_row in {0, 7} and end_row not in {0, 7} and center_distance(
        end_row, end_col
    ) < center_distance(start_row, start_col)


def _is_early_queen_sortie(
    board: Board,
    move: Move,
    undeveloped: int,
) -> bool:
    end_row = int(move.end.row)
    if board.turn == Color.WHITE:
        return undeveloped >= 2 and end_row <= 4
    return undeveloped >= 2 and end_row >= 3


def undeveloped_minor_count(board: Board) -> int:
    """Return how many friendly minor pieces still sit on their home squares."""

    undeveloped = 0
    for row_index, row in enumerate(board.board):
        for col_index, piece in enumerate(row):
            if piece is None or piece.color != board.turn:
                continue
            if piece.kind == PieceType.KNIGHT and row_index in {0, 7} and col_index in {1, 6}:
                undeveloped += 1
            if piece.kind == PieceType.BISHOP and row_index in {0, 7} and col_index in {2, 5}:
                undeveloped += 1
    return undeveloped


def _is_flank_raid(
    board: Board,
    move: Move,
    undeveloped: int,
    needs_shelter: bool,
) -> bool:
    if undeveloped < 2 or not needs_shelter:
        return False
    end_col = int(move.end.col)
    end_row = int(move.end.row)
    if end_col not in {0, 1, 6, 7}:
        return False
    return end_row <= 3 if board.turn == Color.WHITE else end_row >= 4


def is_repeat_heavy_piece_move(
    board: Board,
    kind: PieceType,
    move: Move,
    undeveloped: int,
    needs_shelter: bool,
) -> bool:
    """Return True for early quiet queen/rook repeats before development is finished."""

    return (
        undeveloped >= 2
        and needs_shelter
        and not heavy_piece_on_home_square(board.turn, kind, move.start)
        and not heavy_piece_on_home_square(board.turn, kind, move.end)
    )


def _is_early_flank_pawn_poke(
    board: Board,
    move: Move,
    undeveloped: int,
    needs_shelter: bool,
) -> bool:
    if undeveloped < 2 or not needs_shelter:
        return False
    end_col = int(move.end.col)
    if end_col not in {0, 1, 6, 7}:
        return False
    end_row = int(move.end.row)
    return end_row <= 4 if board.turn == Color.WHITE else end_row >= 3


def _is_kingside_flank_lunge(
    board: Board,
    move: Move,
    undeveloped: int,
    needs_shelter: bool,
) -> bool:
    if undeveloped > 1 or not needs_shelter or not _queens_on_board(board):
        return False
    end_col = int(move.end.col)
    if end_col not in {6, 7}:
        return False
    end_row = int(move.end.row)
    return end_row <= 4 if board.turn == Color.WHITE else end_row >= 3


def _is_early_rook_wander(
    board: Board,
    move: Move,
    undeveloped: int,
    needs_shelter: bool,
) -> bool:
    if undeveloped < 1 or not needs_shelter:
        return False
    return heavy_piece_on_home_square(board.turn, PieceType.ROOK, move.start) and not (
        heavy_piece_on_home_square(board.turn, PieceType.ROOK, move.end)
    )


def _is_uncastled_home_rank_rook_sidestep(
    board: Board,
    move: Move,
    undeveloped: int,
    needs_shelter: bool,
) -> bool:
    if undeveloped > 1 or not needs_shelter or not _queens_on_board(board):
        return False
    home_row = 7 if board.turn == Color.WHITE else 0
    end_col = int(move.end.col)
    return (
        int(move.start.row) == home_row
        and int(move.end.row) == home_row
        and heavy_piece_on_home_square(board.turn, PieceType.ROOK, move.start)
        and end_col not in {0, 7}
    )


def _is_early_queen_drift(
    board: Board,
    move: Move,
    undeveloped: int,
    needs_shelter: bool,
) -> bool:
    if undeveloped < 2 or not needs_shelter:
        return False
    end_row = int(move.end.row)
    end_col = int(move.end.col)
    if board.turn == Color.WHITE:
        return end_row < 6 or end_col not in {3, 4}
    return end_row > 1 or end_col not in {3, 4}


def _is_early_rim_knight_development(
    board: Board,
    move: Move,
    undeveloped: int,
    needs_shelter: bool,
) -> bool:
    if undeveloped < 1 or not needs_shelter:
        return False
    return (
        _home_knight_square(board.turn, move.start)
        and int(move.end.col) in {0, 7}
        and int(move.end.row) not in {0, 7}
    )


def _is_opening_central_rook_move(
    board: Board,
    move: Move,
    undeveloped: int,
    needs_shelter: bool,
) -> bool:
    if undeveloped > 1 or needs_shelter:
        return False
    return int(move.end.col) in {3, 4} and not heavy_piece_on_home_square(
        board.turn,
        PieceType.ROOK,
        move.end,
    )


def _is_castling_move(move: Move) -> bool:
    """Return True for king-side or queen-side castling geometry."""

    return int(move.start.col) == 4 and abs(int(move.start.col) - int(move.end.col)) == 2


def _is_premature_king_walk(board: Board, move: Move, needs_shelter: bool) -> bool:
    if (
        not needs_shelter
        or int(move.start.col) != 4
        or abs(int(move.end.col) - int(move.start.col)) != 1
    ):
        return False
    return _both_queens_on_board(board)


def heavy_piece_on_home_square(color: Color, kind: PieceType, square) -> bool:
    """Return True when a queen or rook still occupies its starting square."""

    row = int(square.row)
    col = int(square.col)
    if kind == PieceType.QUEEN:
        return (row, col) == ((7, 3) if color == Color.WHITE else (0, 3))
    if kind == PieceType.ROOK:
        home_row = 7 if color == Color.WHITE else 0
        return (row, col) in {(home_row, 0), (home_row, 7)}
    return False


def _home_knight_square(color: Color, square) -> bool:
    row = int(square.row)
    col = int(square.col)
    home_row = 7 if color == Color.WHITE else 0
    return (row, col) in {(home_row, 1), (home_row, 6)}


def _both_queens_on_board(board: Board) -> bool:
    white_queen = False
    black_queen = False
    for row in board.board:
        for piece in row:
            if piece is None or piece.kind != PieceType.QUEEN:
                continue
            if piece.color == Color.WHITE:
                white_queen = True
            else:
                black_queen = True
            if white_queen and black_queen:
                return True
    return False


def _queens_on_board(board: Board) -> bool:
    return any(
        piece is not None and piece.kind == PieceType.QUEEN
        for row in board.board
        for piece in row
    )


def _opening_king_unsettled(board: Board) -> bool:
    king_square = board.find_king(board.turn)
    if king_square is None or not _both_queens_on_board(board):
        return False
    home_row = 7 if board.turn == Color.WHITE else 0
    return int(king_square.row) == home_row and int(king_square.col) == 4
