"""Opening-phase development helpers shared by evaluation and ordering."""

from chess_game.chess.board import Board
from chess_game.chess.constants import ConstantSquare, get_col_constant, get_row_constant
from chess_game.chess.evaluation_tables import (
    CASTLED_KING_BONUS,
    CENTRAL_DUO_BONUS,
    CENTRAL_MINOR_PIECE_BONUS,
    CENTRAL_SQUARES,
    CENTER_FILES,
    EARLY_QUEEN_MOVE_PENALTY,
    EARLY_ROOK_MOVE_PENALTY,
    CONNECTED_ROOKS_BONUS,
    DEFENDER_DISTANCE_PENALTY,
    EARLY_FLANK_RAID_PENALTY,
    EARLY_QUEEN_RAID_PENALTY,
    EXTENDED_CENTER_FILES,
    EXTENDED_CENTER_RANKS,
    KNIGHT_RIM_PENALTY,
    MINOR_COORDINATION_BONUS,
)
from chess_game.chess.strategy_utils import (
    both_queens_on_board,
    iter_color_pieces,
    path_clear_between,
    pawn_supports_square,
    shield_pawn_support_state,
)
from chess_game.chess.types import Color, PieceType


def opening_central_control_bonus(board: Board, color: Color) -> int:
    """Reward early control of the center by pawns and minor pieces."""

    bonus = 0
    for piece, row, col in iter_color_pieces(board, color):
        if piece.kind == PieceType.PAWN and (row, col) in CENTRAL_SQUARES:
            bonus += CENTRAL_DUO_BONUS // 2
        if (
            piece.kind in {PieceType.KNIGHT, PieceType.BISHOP}
            and row in EXTENDED_CENTER_RANKS
            and col in EXTENDED_CENTER_FILES
        ):
            bonus += CENTRAL_MINOR_PIECE_BONUS // 2
    return bonus


def opening_piece_coordination_bonus(
    board: Board,
    color: Color,
    undeveloped: int,
) -> int:
    """Reward coordinated minor-piece development before the opening is finished."""

    if undeveloped > 2:
        return 0
    developed_minors = [
        (row, col)
        for piece, row, col in iter_color_pieces(board, color)
        if piece.kind in {PieceType.KNIGHT, PieceType.BISHOP}
        and not minor_on_home_square(color, piece.kind, row, col)
    ]
    if coordinated_minor_piece_setup(developed_minors):
        return MINOR_COORDINATION_BONUS // 2
    return 0


def early_flank_raid_penalty(board: Board, color: Color, undeveloped: int) -> int:
    """Penalize early queen/rook flank raids before king safety is secured."""

    king_square = board.find_king(color)
    if undeveloped < 2 or king_square is None or _is_castled_king(color, king_square):
        return 0
    penalty = 0
    for piece, row, col in iter_color_pieces(board, color):
        if piece.kind not in {PieceType.QUEEN, PieceType.ROOK}:
            continue
        if col not in {0, 1, 6, 7} or not _piece_in_enemy_half(color, row):
            continue
        penalty += (
            EARLY_FLANK_RAID_PENALTY
            if piece.kind == PieceType.QUEEN
            else EARLY_FLANK_RAID_PENALTY // 2
        )
    return penalty


def early_flank_pawn_poke_penalty(board: Board, color: Color, undeveloped: int) -> int:
    """Penalize premature flank pawn lunges before development and castling."""

    king_square = board.find_king(color)
    if undeveloped < 1 or king_square is None or _is_castled_king(color, king_square):
        return 0
    penalty = 0
    for piece, row, col in iter_color_pieces(board, color):
        if piece.kind != PieceType.PAWN or col not in {0, 1, 6, 7}:
            continue
        if _flank_pawn_is_overextended(color, row):
            penalty += EARLY_FLANK_RAID_PENALTY
            if col in {0, 7}:
                penalty += EARLY_FLANK_RAID_PENALTY // 2
            if col in {6, 7}:
                penalty += EARLY_FLANK_RAID_PENALTY // 2
    return penalty


def early_kingside_flank_lunge_penalty(board: Board, color: Color, undeveloped: int) -> int:
    """Penalize early g/h-pawn lunges before development and castling are settled."""

    return _opening_drift_penalties(board, color, undeveloped)[0]


def early_home_rank_rook_sidestep_penalty(board: Board, color: Color, undeveloped: int) -> int:
    """Penalize rooks drifting along the home rank before king safety is fixed."""

    return _opening_drift_penalties(board, color, undeveloped)[1]


def early_rim_knight_development_penalty(board: Board, color: Color, undeveloped: int) -> int:
    """Penalize early knight development to the rim when central squares are available."""

    return _opening_drift_penalties(board, color, undeveloped)[2]


def early_edge_space_grab_penalty(board: Board, color: Color, undeveloped: int) -> int:
    """Penalize early a/h-pawn space grabs that do not help development or king safety."""

    return _opening_drift_penalties(board, color, undeveloped)[3]


def _opening_drift_penalties(
    board: Board,
    color: Color,
    undeveloped: int,
) -> tuple[int, int, int, int]:
    """Return combined opening penalties for drift-heavy late-opening moves."""

    king_square = board.find_king(color)
    if (
        undeveloped > 1
        or king_square is None
        or not _queens_on_board(board)
    ):
        return 0, 0, 0, 0
    kingside_pawn_penalty = 0
    rook_sidestep_penalty = 0
    rim_knight_penalty = 0
    edge_space_grab_penalty = 0
    home_row = 7 if color == Color.WHITE else 0
    king_col = int(king_square.col)
    castled_king = _is_castled_king(color, king_square)
    unsettled_central_king = king_col in {3, 4, 5}
    for piece, row, col in iter_color_pieces(board, color):
        if (
            piece.kind == PieceType.PAWN
            and col in {6, 7}
            and _flank_pawn_is_overextended(color, row)
            and not castled_king
        ):
            kingside_pawn_penalty += EARLY_FLANK_RAID_PENALTY + EARLY_QUEEN_MOVE_PENALTY
            if col == 7:
                kingside_pawn_penalty += EARLY_ROOK_MOVE_PENALTY
        elif (
            piece.kind == PieceType.ROOK
            and row == home_row
            and col not in {0, 7}
            and not castled_king
        ):
            rook_sidestep_penalty += EARLY_ROOK_MOVE_PENALTY + EARLY_QUEEN_MOVE_PENALTY
            if col not in CENTER_FILES:
                rook_sidestep_penalty += EARLY_ROOK_MOVE_PENALTY
        elif (
            piece.kind == PieceType.KNIGHT
            and col in {0, 7}
            and not minor_on_home_square(color, PieceType.KNIGHT, row, col)
        ):
            rim_knight_penalty += (
                KNIGHT_RIM_PENALTY + EARLY_QUEEN_MOVE_PENALTY + EARLY_FLANK_RAID_PENALTY
            )
            if unsettled_central_king:
                rim_knight_penalty += CASTLED_KING_BONUS
        elif (
            piece.kind == PieceType.PAWN
            and col in {0, 7}
            and (
                _edge_space_grab(color, row)
                or (col == 0 and _flank_pawn_is_overextended(color, row))
            )
        ):
            edge_space_grab_penalty += EARLY_FLANK_RAID_PENALTY + EARLY_ROOK_MOVE_PENALTY
    return (
        kingside_pawn_penalty,
        rook_sidestep_penalty,
        rim_knight_penalty,
        edge_space_grab_penalty,
    )


def early_flank_queen_sortie_penalty(board: Board, color: Color, undeveloped: int) -> int:
    """Penalize early unsupported queen swings to the board edge."""

    queens = [
        (row, col)
        for piece, row, col in iter_color_pieces(board, color)
        if piece.kind == PieceType.QUEEN
    ]
    if undeveloped < 2 or len(queens) != 1:
        return 0
    queen_row, queen_col = queens[0]
    if queen_col not in {0, 1, 6, 7} or not _queen_on_flank_sortie(color, queen_row):
        return 0
    if _queen_has_nearby_support(board, color, queen_row, queen_col):
        return 0

    penalty = EARLY_FLANK_RAID_PENALTY + EARLY_QUEEN_MOVE_PENALTY // 2
    king_square = board.find_king(color)
    if king_square is None:
        return penalty
    king_distance = max(
        abs(int(king_square.row) - queen_row),
        abs(int(king_square.col) - queen_col),
    )
    if king_distance >= 4:
        penalty += DEFENDER_DISTANCE_PENALTY
    return penalty


def early_queen_raid_penalty(board: Board, color: Color, undeveloped: int) -> int:
    """Penalize unsupported early queen raids into the enemy half."""

    queens = [
        (row, col)
        for piece, row, col in iter_color_pieces(board, color)
        if piece.kind == PieceType.QUEEN
    ]
    if len(queens) != 1:
        return 0
    queen_row, queen_col = queens[0]
    if not _queen_in_enemy_half(color, queen_row):
        return 0
    if _queen_has_nearby_support(board, color, queen_row, queen_col):
        return 0
    penalty = EARLY_QUEEN_RAID_PENALTY
    if undeveloped >= 2:
        penalty += EARLY_QUEEN_MOVE_PENALTY // 2
    return penalty + _distant_queen_from_king_penalty(board, color, queen_row, queen_col)


def unforced_shelter_loosening_penalty(
    board: Board,
    color: Color,
    square: ConstantSquare,
    attack_pressure: int,
) -> int:
    """Penalize single-step shield pawn pushes when the castled king is not under fire."""

    if not _is_castled_king(color, square) or not _queens_on_board(board) or attack_pressure > 0:
        return 0
    king_col = int(square.col)
    penalty = 0
    for file_index in range(max(0, king_col - 1), min(7, king_col + 1) + 1):
        has_home_pawn, has_advanced_pawn = shield_pawn_support_state(board, color, file_index)
        if has_home_pawn:
            continue
        if has_advanced_pawn:
            penalty += EARLY_FLANK_RAID_PENALTY
    return penalty


def early_shelter_pawn_push_penalty(board: Board, color: Color, undeveloped: int) -> int:
    """Penalize premature castled-king shelter loosening before development finishes."""

    king_square = board.find_king(color)
    if king_square is None or undeveloped < 2:
        return 0
    attack_pressure = _king_zone_attack_pressure(board, color, king_square)
    return unforced_shelter_loosening_penalty(board, color, king_square, attack_pressure) * 2


def opening_king_safety_score(board: Board, color: Color, undeveloped: int) -> int:
    """Reward castling on time once opening development is underway."""

    king_square = board.find_king(color)
    if king_square is None:
        return 0
    if not _is_castled_king(color, king_square):
        return 0
    if undeveloped <= 1:
        return CASTLED_KING_BONUS
    if undeveloped == 2:
        return CASTLED_KING_BONUS // 2
    return 0


def opening_king_urgency_penalty(board: Board, color: Color, undeveloped: int) -> int:
    """Penalize delaying king safety or abandoning castling rights in the opening."""

    king_square = board.find_king(color)
    if king_square is None or _is_castled_king(color, king_square) or not _queens_on_board(board):
        return 0
    home_row = 7 if color == Color.WHITE else 0
    king_row = int(king_square.row)
    king_col = int(king_square.col)
    if king_row != home_row:
        return 0

    penalty = 0
    if king_col in {3, 4, 5}:
        penalty += CASTLED_KING_BONUS // 2
        penalty += max(undeveloped, 1) * (EARLY_QUEEN_MOVE_PENALTY // 2)
    if king_col != 4:
        penalty += EARLY_QUEEN_MOVE_PENALTY

    castling_options = _castling_options_remaining(board, color)
    if castling_options == 0:
        penalty += CASTLED_KING_BONUS
    elif castling_options == 1:
        penalty += EARLY_ROOK_MOVE_PENALTY

    penalty += _uncastled_shell_penalty(board, color, king_col)
    return penalty


def opening_rook_connection_bonus(board: Board, color: Color, undeveloped: int) -> int:
    """Reward connected rooks once the opening phase is nearly complete."""

    if undeveloped > 1:
        return 0
    rooks = [
        (row, col)
        for piece, row, col in iter_color_pieces(board, color)
        if piece.kind == PieceType.ROOK
    ]
    if len(rooks) != 2:
        return 0
    first, second = rooks
    same_line = first[0] == second[0] or first[1] == second[1]
    if not same_line or not path_clear_between(board, first, second):
        return 0
    return CONNECTED_ROOKS_BONUS


def opening_central_rook_bonus(board: Board, color: Color, undeveloped: int) -> int:
    """Reward rooks that reach central files after king safety is fixed."""

    king_square = board.find_king(color)
    if undeveloped > 1 or king_square is None or not _is_castled_king(color, king_square):
        return 0
    bonus = 0
    home_row = 7 if color == Color.WHITE else 0
    for piece, row, col in iter_color_pieces(board, color):
        if piece.kind != PieceType.ROOK:
            continue
        if col in CENTER_FILES and (row != home_row or col not in {0, 7}):
            bonus += CONNECTED_ROOKS_BONUS // 2
    return bonus


def opening_queen_restraint_bonus(board: Board, color: Color, undeveloped: int) -> int:
    """Reward keeping the queen home while development and king safety lag."""

    if undeveloped < 2:
        return 0
    home_square = ConstantSquare(
        row=get_row_constant(7 if color == Color.WHITE else 0),
        col=get_col_constant(3),
    )
    queen = board.get_piece(home_square)
    if queen is None or queen.color != color or queen.kind != PieceType.QUEEN:
        return 0
    return EARLY_QUEEN_MOVE_PENALTY // 2


def opening_wing_knight_lunge_penalty(board: Board, color: Color, undeveloped: int) -> int:
    """Penalize unsupported early knight lunges toward the enemy wing."""

    king_square = board.find_king(color)
    if (
        undeveloped < 1
        or king_square is None
        or int(king_square.row) != (7 if color == Color.WHITE else 0)
        or int(king_square.col) != 4
        or not both_queens_on_board(board)
    ):
        return 0
    penalty = 0
    for piece, row, col in iter_color_pieces(board, color):
        if piece.kind != PieceType.KNIGHT or not _is_wing_knight_lunge(color, row, col):
            continue
        if pawn_supports_square(board, color, row, col):
            continue
        penalty += KNIGHT_RIM_PENALTY + EARLY_FLANK_RAID_PENALTY
    return penalty


def minor_on_home_square(color: Color, kind: PieceType, row: int, col: int) -> bool:
    """Return True when a minor piece still sits on its original square."""

    starting_squares = {
        Color.WHITE: {
            PieceType.KNIGHT: {(7, 1), (7, 6)},
            PieceType.BISHOP: {(7, 2), (7, 5)},
        },
        Color.BLACK: {
            PieceType.KNIGHT: {(0, 1), (0, 6)},
            PieceType.BISHOP: {(0, 2), (0, 5)},
        },
    }
    return (row, col) in starting_squares[color].get(kind, set())


def coordinated_minor_piece_setup(minor_squares: list[tuple[int, int]]) -> bool:
    """Return True when two developed minor pieces work near the center together."""

    central_squares = [
        square
        for square in minor_squares
        if square[1] in EXTENDED_CENTER_FILES and square[0] in EXTENDED_CENTER_RANKS
    ]
    if len(central_squares) < 2:
        return False
    first_row, first_col = central_squares[0]
    for second_row, second_col in central_squares[1:]:
        if abs(first_row - second_row) <= 2 and abs(first_col - second_col) <= 2:
            return True
    return False


def undeveloped_minor_piece_count(board: Board, color: Color) -> int:
    """Return how many knights and bishops still sit on their home squares."""

    undeveloped = 0
    for piece, row, col in iter_color_pieces(board, color):
        if piece.kind in {PieceType.KNIGHT, PieceType.BISHOP} and minor_on_home_square(
            color,
            piece.kind,
            row,
            col,
        ):
            undeveloped += 1
    return undeveloped


def _is_wing_knight_lunge(color: Color, row: int, col: int) -> bool:
    return col in {1, 6} and (row <= 3 if color == Color.WHITE else row >= 4)


def _is_castled_king(color: Color, square: ConstantSquare) -> bool:
    """Return True when the king already sits on a castled home-rank square."""

    home_row = 7 if color == Color.WHITE else 0
    return int(square.row) == home_row and int(square.col) in {2, 6}


def _piece_in_enemy_half(color: Color, row: int) -> bool:
    """Return True when the piece has advanced far enough to count as a raid."""

    return row <= 3 if color == Color.WHITE else row >= 4


def _queen_on_flank_sortie(color: Color, row: int) -> bool:
    return row <= 4 if color == Color.WHITE else row >= 3


def _flank_pawn_is_overextended(color: Color, row: int) -> bool:
    return row <= 4 if color == Color.WHITE else row >= 3


def _edge_space_grab(color: Color, row: int) -> bool:
    return row == 5 if color == Color.WHITE else row == 2


def _queen_in_enemy_half(color: Color, queen_row: int) -> bool:
    return queen_row <= 2 if color == Color.WHITE else queen_row >= 5




def _queens_on_board(board: Board) -> bool:
    white_has_queen = any(
        piece.kind == PieceType.QUEEN
        for piece, _, _ in iter_color_pieces(board, Color.WHITE)
    )
    black_has_queen = any(
        piece.kind == PieceType.QUEEN
        for piece, _, _ in iter_color_pieces(board, Color.BLACK)
    )
    return white_has_queen or black_has_queen


def _queen_has_nearby_support(
    board: Board,
    color: Color,
    queen_row: int,
    queen_col: int,
) -> bool:
    for piece, row, col in iter_color_pieces(board, color):
        if piece.kind == PieceType.QUEEN:
            continue
        if max(abs(row - queen_row), abs(col - queen_col)) <= 1:
            return True
    return False


def _distant_queen_from_king_penalty(
    board: Board,
    color: Color,
    queen_row: int,
    queen_col: int,
) -> int:
    king_square = board.find_king(color)
    if king_square is None:
        return 0
    king_distance = max(
        abs(int(king_square.row) - queen_row),
        abs(int(king_square.col) - queen_col),
    )
    return DEFENDER_DISTANCE_PENALTY if king_distance >= 4 else 0


def _king_zone_attack_pressure(
    board: Board,
    color: Color,
    square: ConstantSquare,
) -> int:
    enemy_color = Color.BLACK if color == Color.WHITE else Color.WHITE
    king_row = int(square.row)
    king_col = int(square.col)
    penalty = 0
    for piece, row, col in iter_color_pieces(board, enemy_color):
        distance = max(abs(row - king_row), abs(col - king_col))
        if distance > 2:
            continue
        if piece.kind == PieceType.QUEEN:
            penalty += 15
        elif piece.kind == PieceType.ROOK:
            penalty += 10
        elif piece.kind in (PieceType.BISHOP, PieceType.KNIGHT):
            penalty += 5
    return penalty


def _castling_options_remaining(board: Board, color: Color) -> int:
    rights = board.castling_rights
    if color == Color.WHITE:
        return int(rights.white_kingside) + int(rights.white_queenside)
    return int(rights.black_kingside) + int(rights.black_queenside)


def _uncastled_shell_penalty(board: Board, color: Color, king_col: int) -> int:
    shield_row = 6 if color == Color.WHITE else 1
    penalty = 0
    for file_index in range(max(0, king_col - 1), min(7, king_col + 1) + 1):
        square = ConstantSquare(
            row=get_row_constant(shield_row),
            col=get_col_constant(file_index),
        )
        pawn = board.get_piece(square)
        if pawn is None or pawn.color != color or pawn.kind != PieceType.PAWN:
            penalty += EARLY_FLANK_RAID_PENALTY
    return penalty
