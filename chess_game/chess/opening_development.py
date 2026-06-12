"""Opening-phase development helpers shared by evaluation and ordering."""

from chess_game.chess.board import Board
from chess_game.chess.constants import ConstantSquare, get_col_constant, get_row_constant
from chess_game.chess.eval_weights import EvalWeights
from chess_game.chess.evaluation_tables import (
    CENTRAL_SQUARES,
    CENTER_FILES,
    EXTENDED_CENTER_FILES,
    EXTENDED_CENTER_RANKS,
)
from chess_game.chess.strategy_utils import (
    both_queens_on_board,
    iter_color_pieces,
    path_clear_between,
    pawn_supports_square,
    shield_pawn_support_state,
)
from chess_game.chess.types import Color, PieceType
from chess_game.chess.opening_development_helpers import (
    _castling_options_remaining,
    _distant_queen_from_king_penalty,
    _edge_space_grab,
    _flank_pawn_is_overextended,
    _is_castled_king,
    _is_wing_knight_lunge,
    _king_zone_attack_pressure,
    _piece_in_enemy_half,
    _queen_has_nearby_support,
    _queen_in_enemy_half,
    _queen_on_flank_sortie,
    _queens_on_board,
    _uncastled_shell_penalty,
)


def opening_central_control_bonus(
    board: Board, color: Color, weights: EvalWeights | None = None
) -> int:
    """Reward early control of the center by pawns and minor pieces."""

    if weights is None:
        weights = EvalWeights.default()
    bonus = 0
    for piece, row, col in iter_color_pieces(board, color):
        if piece.kind == PieceType.PAWN and (row, col) in CENTRAL_SQUARES:
            bonus += weights.pawns.central_duo_bonus // 2
        if (
            piece.kind in {PieceType.KNIGHT, PieceType.BISHOP}
            and row in EXTENDED_CENTER_RANKS
            and col in EXTENDED_CENTER_FILES
        ):
            bonus += weights.pieces.central_minor_piece_bonus // 2
    return bonus


def opening_piece_coordination_bonus(
    board: Board,
    color: Color,
    undeveloped: int,
    weights: EvalWeights | None = None,
) -> int:
    """Reward coordinated minor-piece development before the opening is finished."""

    if undeveloped > 2:
        return 0
    if weights is None:
        weights = EvalWeights.default()
    developed_minors = [
        (row, col)
        for piece, row, col in iter_color_pieces(board, color)
        if piece.kind in {PieceType.KNIGHT, PieceType.BISHOP}
        and not minor_on_home_square(color, piece.kind, row, col)
    ]
    if coordinated_minor_piece_setup(developed_minors):
        return weights.pieces.minor_coordination_bonus // 2
    return 0


def early_flank_raid_penalty(
    board: Board, color: Color, undeveloped: int, weights: EvalWeights | None = None
) -> int:
    """Penalize early queen/rook flank raids before king safety is secured."""

    king_square = board.find_king(color)
    if undeveloped < 2 or king_square is None or _is_castled_king(color, king_square):
        return 0
    if weights is None:
        weights = EvalWeights.default()
    flank_penalty = weights.development.early_flank_raid_penalty
    penalty = 0
    for piece, row, col in iter_color_pieces(board, color):
        if piece.kind not in {PieceType.QUEEN, PieceType.ROOK}:
            continue
        if col not in {0, 1, 6, 7} or not _piece_in_enemy_half(color, row):
            continue
        penalty += (
            flank_penalty
            if piece.kind == PieceType.QUEEN
            else flank_penalty // 2
        )
    return penalty


def early_flank_pawn_poke_penalty(
    board: Board, color: Color, undeveloped: int, weights: EvalWeights | None = None
) -> int:
    """Penalize premature flank pawn lunges before development and castling."""

    king_square = board.find_king(color)
    if undeveloped < 1 or king_square is None or _is_castled_king(color, king_square):
        return 0
    if weights is None:
        weights = EvalWeights.default()
    flank_penalty = weights.development.early_flank_raid_penalty
    penalty = 0
    for piece, row, col in iter_color_pieces(board, color):
        if piece.kind != PieceType.PAWN or col not in {0, 1, 6, 7}:
            continue
        if _flank_pawn_is_overextended(color, row):
            penalty += flank_penalty
            if col in {0, 7}:
                penalty += flank_penalty // 2
            if col in {6, 7}:
                penalty += flank_penalty // 2
    return penalty


def early_kingside_flank_lunge_penalty(
    board: Board, color: Color, undeveloped: int, weights: EvalWeights | None = None
) -> int:
    """Penalize early g/h-pawn lunges before development and castling are settled."""

    return _opening_drift_penalties(board, color, undeveloped, weights)[0]


def early_home_rank_rook_sidestep_penalty(
    board: Board, color: Color, undeveloped: int, weights: EvalWeights | None = None
) -> int:
    """Penalize rooks drifting along the home rank before king safety is fixed."""

    return _opening_drift_penalties(board, color, undeveloped, weights)[1]


def early_rim_knight_development_penalty(
    board: Board, color: Color, undeveloped: int, weights: EvalWeights | None = None
) -> int:
    """Penalize early knight development to the rim when central squares are available."""

    return _opening_drift_penalties(board, color, undeveloped, weights)[2]


def early_edge_space_grab_penalty(
    board: Board, color: Color, undeveloped: int, weights: EvalWeights | None = None
) -> int:
    """Penalize early a/h-pawn space grabs that do not help development or king safety."""

    return _opening_drift_penalties(board, color, undeveloped, weights)[3]


def _opening_drift_penalties(
    board: Board,
    color: Color,
    undeveloped: int,
    weights: EvalWeights | None = None,
) -> tuple[int, int, int, int]:
    """Return combined opening penalties for drift-heavy late-opening moves."""

    king_square = board.find_king(color)
    if (
        undeveloped > 1
        or king_square is None
        or not _queens_on_board(board)
    ):
        return 0, 0, 0, 0
    if weights is None:
        weights = EvalWeights.default()
    home_row = 7 if color == Color.WHITE else 0
    king_col = int(king_square.col)
    castled_king = _is_castled_king(color, king_square)
    unsettled = king_col in {3, 4, 5}
    dev = weights.development
    # penalties: [kingside_pawn, rook_sidestep, rim_knight, edge_space_grab]
    pens: list[int] = [0, 0, 0, 0]
    for piece, row, col in iter_color_pieces(board, color):
        if (
            piece.kind == PieceType.PAWN
            and col in {6, 7}
            and _flank_pawn_is_overextended(color, row)
            and not castled_king
        ):
            pens[0] += dev.early_flank_raid_penalty + dev.early_queen_move_penalty
            pens[0] += dev.early_rook_move_penalty if col == 7 else 0
        elif (
            piece.kind == PieceType.ROOK
            and row == home_row
            and col not in {0, 7}
            and not castled_king
        ):
            pens[1] += dev.early_rook_move_penalty + dev.early_queen_move_penalty
            pens[1] += dev.early_rook_move_penalty if col not in CENTER_FILES else 0
        elif (
            piece.kind == PieceType.KNIGHT
            and col in {0, 7}
            and not minor_on_home_square(color, PieceType.KNIGHT, row, col)
        ):
            pens[2] += (
                weights.pieces.knight_rim_penalty
                + dev.early_queen_move_penalty
                + dev.early_flank_raid_penalty
            )
            pens[2] += weights.king.castled_king_bonus if unsettled else 0
        elif (
            piece.kind == PieceType.PAWN
            and col in {0, 7}
            and (
                _edge_space_grab(color, row)
                or (col == 0 and _flank_pawn_is_overextended(color, row))
            )
        ):
            pens[3] += dev.early_flank_raid_penalty + dev.early_rook_move_penalty
    return pens[0], pens[1], pens[2], pens[3]


def early_flank_queen_sortie_penalty(
    board: Board, color: Color, undeveloped: int, weights: EvalWeights | None = None
) -> int:
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
    if weights is None:
        weights = EvalWeights.default()
    dev = weights.development
    penalty = dev.early_flank_raid_penalty + dev.early_queen_move_penalty // 2
    king_square = board.find_king(color)
    if king_square is None:
        return penalty
    king_distance = max(
        abs(int(king_square.row) - queen_row),
        abs(int(king_square.col) - queen_col),
    )
    if king_distance >= 4:
        penalty += weights.king.defender_distance_penalty
    return penalty


def early_queen_raid_penalty(
    board: Board, color: Color, undeveloped: int, weights: EvalWeights | None = None
) -> int:
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
    if weights is None:
        weights = EvalWeights.default()
    dev = weights.development
    penalty = dev.early_queen_raid_penalty
    if undeveloped >= 2:
        penalty += dev.early_queen_move_penalty // 2
    return penalty + _distant_queen_from_king_penalty(board, color, queen_row, queen_col, weights)


def unforced_shelter_loosening_penalty(
    board: Board,
    color: Color,
    square: ConstantSquare,
    attack_pressure: int,
    weights: EvalWeights | None = None,
) -> int:
    """Penalize single-step shield pawn pushes when the castled king is not under fire."""

    if not _is_castled_king(color, square) or not _queens_on_board(board) or attack_pressure > 0:
        return 0
    if weights is None:
        weights = EvalWeights.default()
    flank_penalty = weights.development.early_flank_raid_penalty
    king_col = int(square.col)
    penalty = 0
    for file_index in range(max(0, king_col - 1), min(7, king_col + 1) + 1):
        has_home_pawn, has_advanced_pawn = shield_pawn_support_state(board, color, file_index)
        if has_home_pawn:
            continue
        if has_advanced_pawn:
            penalty += flank_penalty
    return penalty


def early_shelter_pawn_push_penalty(
    board: Board, color: Color, undeveloped: int, weights: EvalWeights | None = None
) -> int:
    """Penalize premature castled-king shelter loosening before development finishes."""

    king_square = board.find_king(color)
    if king_square is None or undeveloped < 2:
        return 0
    attack_pressure = _king_zone_attack_pressure(board, color, king_square)
    return (
        unforced_shelter_loosening_penalty(board, color, king_square, attack_pressure, weights)
        * 2
    )


def opening_king_safety_score(
    board: Board, color: Color, undeveloped: int, weights: EvalWeights | None = None
) -> int:
    """Reward castling on time once opening development is underway."""

    king_square = board.find_king(color)
    if king_square is None:
        return 0
    if not _is_castled_king(color, king_square):
        return 0
    if weights is None:
        weights = EvalWeights.default()
    castled_bonus = weights.king.castled_king_bonus
    if undeveloped <= 1:
        return castled_bonus
    if undeveloped == 2:
        return castled_bonus // 2
    return 0


def opening_king_urgency_penalty(
    board: Board, color: Color, undeveloped: int, weights: EvalWeights | None = None
) -> int:
    """Penalize delaying king safety or abandoning castling rights in the opening."""

    king_square = board.find_king(color)
    if king_square is None or _is_castled_king(color, king_square) or not _queens_on_board(board):
        return 0
    home_row = 7 if color == Color.WHITE else 0
    king_row = int(king_square.row)
    king_col = int(king_square.col)
    if king_row != home_row:
        return 0
    if weights is None:
        weights = EvalWeights.default()
    dev = weights.development
    castled_bonus = weights.king.castled_king_bonus

    penalty = 0
    if king_col in {3, 4, 5}:
        penalty += castled_bonus // 2
        penalty += max(undeveloped, 1) * (dev.early_queen_move_penalty // 2)
    if king_col != 4:
        penalty += dev.early_queen_move_penalty

    castling_options = _castling_options_remaining(board, color)
    if castling_options == 0:
        penalty += castled_bonus
    elif castling_options == 1:
        penalty += dev.early_rook_move_penalty

    penalty += _uncastled_shell_penalty(board, color, king_col, weights)
    return penalty


_LATE_CASTLING_BASE_PENALTY = 20
_LATE_CASTLING_MAX_PENALTY = 160
_BISHOP_BLOCKS_CASTLING_PENALTY = 56
_BISHOP_BLOCKS_CASTLING_SCALING = 8  # extra cp per fullmove past move 6


def late_castling_urgency_penalty(board: Board, color: Color) -> int:
    """Scale urgency penalty for every extra move the king stays uncastled past move 10.

    After move 10, a king still on its home square with queens on the board is
    increasingly dangerous.  The penalty grows linearly with move count so the
    engine strongly prefers castling over tactical wing adventures.
    """

    if not _queens_on_board(board):
        return 0
    king_square = board.find_king(color)
    if king_square is None or _is_castled_king(color, king_square):
        return 0
    home_row = 7 if color == Color.WHITE else 0
    if int(king_square.row) != home_row or int(king_square.col) != 4:
        return 0
    if _castling_options_remaining(board, color) == 0:
        return 0
    excess = max(0, board.fullmove_number - 3)
    if excess == 0:
        return 0
    return min(_LATE_CASTLING_BASE_PENALTY * excess, _LATE_CASTLING_MAX_PENALTY)


def castling_path_blocked_penalty(board: Board, color: Color) -> int:
    """Penalise a position where the kingside bishop is still on f1/f8 blocking castling.

    When the king hasn't castled and kingside castling rights exist, the f-square
    bishop sitting on its home square means castling is impossible until the bishop
    moves.  This penalty pushes the engine to prioritise bishop development as a
    prerequisite for castling.
    """

    if not _queens_on_board(board):
        return 0
    king_square = board.find_king(color)
    if king_square is None or _is_castled_king(color, king_square):
        return 0
    home_row = 7 if color == Color.WHITE else 0
    if int(king_square.row) != home_row or int(king_square.col) != 4:
        return 0
    rights = board.castling_rights
    has_kingside = rights.white_kingside if color == Color.WHITE else rights.black_kingside
    if not has_kingside:
        return 0
    piece = board.board[home_row][5]
    if piece is None or piece.color != color or piece.kind != PieceType.BISHOP:
        return 0
    scaling = _BISHOP_BLOCKS_CASTLING_SCALING * max(0, board.fullmove_number - 6)
    return min(_BISHOP_BLOCKS_CASTLING_PENALTY + scaling, 128)


def opening_rook_connection_bonus(
    board: Board, color: Color, undeveloped: int, weights: EvalWeights | None = None
) -> int:
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
    if weights is None:
        weights = EvalWeights.default()
    return weights.pieces.connected_rooks_bonus


def opening_central_rook_bonus(
    board: Board, color: Color, undeveloped: int, weights: EvalWeights | None = None
) -> int:
    """Reward rooks that reach central files after king safety is fixed."""

    king_square = board.find_king(color)
    if undeveloped > 1 or king_square is None or not _is_castled_king(color, king_square):
        return 0
    if weights is None:
        weights = EvalWeights.default()
    rook_bonus = weights.pieces.connected_rooks_bonus
    bonus = 0
    home_row = 7 if color == Color.WHITE else 0
    for piece, row, col in iter_color_pieces(board, color):
        if piece.kind != PieceType.ROOK:
            continue
        if col in CENTER_FILES and (row != home_row or col not in {0, 7}):
            bonus += rook_bonus // 2
    return bonus


def opening_queen_restraint_bonus(
    board: Board, color: Color, undeveloped: int, weights: EvalWeights | None = None
) -> int:
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
    if weights is None:
        weights = EvalWeights.default()
    return weights.development.early_queen_move_penalty // 2


def opening_wing_knight_lunge_penalty(
    board: Board, color: Color, undeveloped: int, weights: EvalWeights | None = None
) -> int:
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
    if weights is None:
        weights = EvalWeights.default()
    rim_penalty = weights.pieces.knight_rim_penalty
    flank_penalty = weights.development.early_flank_raid_penalty
    penalty = 0
    for piece, row, col in iter_color_pieces(board, color):
        if piece.kind != PieceType.KNIGHT or not _is_wing_knight_lunge(color, row, col):
            continue
        if pawn_supports_square(board, color, row, col):
            continue
        penalty += rim_penalty + flank_penalty
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


def middlegame_rim_knight_penalty(
    board: Board, color: Color, weights: EvalWeights | None = None
) -> int:
    """Penalise knights on the rim (a or h file) whenever queens are still on the board.

    The existing early_rim_knight_development_penalty only fires when most pieces are
    already developed (undeveloped <= 1).  This function fires regardless of
    development count so that a knight that wanders to the rim early in the middlegame
    is also penalised in the static evaluation.
    """

    if not _queens_on_board(board):
        return 0
    if weights is None:
        weights = EvalWeights.default()
    rim_penalty = weights.pieces.knight_rim_penalty
    penalty = 0
    home_row = 7 if color == Color.WHITE else 0
    for piece, row, col in iter_color_pieces(board, color):
        if piece.kind != PieceType.KNIGHT:
            continue
        if col not in {0, 7}:
            continue
        if (row, col) in {(home_row, 0), (home_row, 7)}:
            continue
        penalty += rim_penalty * 3
    return penalty
