"""Static tables and weights used by the evaluator."""

from chess_game.chess.types import PieceType

MATERIAL_VALUES: dict[PieceType, int] = {
    PieceType.PAWN: 100,
    PieceType.KNIGHT: 320,
    PieceType.BISHOP: 330,
    PieceType.ROOK: 500,
    PieceType.QUEEN: 900,
    PieceType.KING: 20_000,
}

PAWN_TABLE: list[list[int]] = [
    [-8, -8, -8, -8, -8, -8, -8, -8],
    [-1, -1, -1, -1, -1, -1, -1, -1],
    [1, 2, 1, 3, 2, 3, 1, 2],
    [2, 3, 1, 2, 2, 2, 1, 2],
    [2, 3, 1, 2, 3, 1, 2, 2],
    [1, 1, 2, 1, 2, 1, 1, 0],
    [-1, 0, 0, 0, 0, 0, 0, -1],
    [-8, -8, -8, -8, -8, -8, -8, -8],
]

KNIGHT_TABLE: list[list[int]] = [
    [-3, -2, -1, 0, 0, -1, -2, -3],
    [-2, 0, 1, 1, 1, 1, 0, -2],
    [-1, 1, 3, 3, 3, 3, 1, -1],
    [0, 1, 4, 4, 4, 4, 1, 0],
    [0, 2, 4, 4, 4, 4, 2, 0],
    [0, 1, 3, 4, 4, 3, 1, 0],
    [-2, 0, 2, 3, 3, 2, 0, -2],
    [-3, -2, -1, 0, 0, -1, -2, -3],
]

BISHOP_TABLE: list[list[int]] = [
    [-5, -4, -3, -2, -2, -3, -4, -5],
    [-3, -2, 1, 2, 2, 1, -2, -3],
    [2, 2, 1, 1, 1, 1, 2, 2],
    [2, 3, 1, 5, 5, 1, 3, 2],
    [0, 1, 2, 2, 2, 2, 1, 0],
    [-2, 2, 3, 4, 4, 3, 2, -2],
    [-3, 2, 3, 4, 4, 3, 2, -3],
    [-5, -4, -3, -2, -2, -3, -4, -5],
]

ROOK_TABLE: list[list[int]] = [
    [-3, -3, -3, -3, -3, -3, -3, -3],
    [-2, -2, -1, -1, -1, -1, -2, -2],
    [-1, -1, 1, 3, 4, 3, -1, -1],
    [-2, 1, 3, 7, 7, 3, 1, -2],
    [-1, 2, 5, 8, 8, 5, 2, -1],
    [2, 3, 6, 9, 9, 6, 3, 2],
    [4, 1, 4, 2, 2, 4, 1, 5],
    [-3, -3, -3, -3, -3, -3, -3, -3],
]

QUEEN_TABLE: list[list[int]] = [
    [-2, 1, 2, 2, 2, 2, 1, -2],
    [-3, -2, 2, 4, 4, 2, -2, -3],
    [0, 0, 2, 3, 6, 3, 2, 0],
    [-5, 1, 3, 5, 8, 8, 3, 1],
    [1, 4, 7, 9, 10, 9, 7, 4],
    [-2, 5, 8, 8, 8, 8, 5, -2],
    [-2, 1, 3, 5, 6, 5, 3, -2],
    [-3, -4, -2, -2, -2, -2, -4, -3],
]

KING_TABLE: list[list[int]] = [
    [-8, -7, -6, -4, -2, 0, 1, 3],
    [-7, -6, -4, -2, -1, 1, 2, 3],
    [-7, -5, 0, 2, 5, 5, 2, 5],
    [2, 2, 3, 4, 4, 4, 2, 2],
    [2, 3, 3, 5, 6, 5, 3, 2],
    [-4, -3, -1, 0, 0, 0, -1, -3],
    [-6, -5, -3, -2, -1, 0, -2, -4],
    [-9, -8, -6, -5, -4, -3, -4, -7],
]

STARTING_NON_PAWN_MATERIAL = 6_400
ISOLATED_PAWN_PENALTY = 12
DOUBLED_PAWN_PENALTY = 10
BACKWARD_PAWN_PENALTY = 8
PAWN_ISLAND_PENALTY = 7
WEAK_CHAIN_PAWN_PENALTY = 6
CONNECTED_PASSED_PAWN_BONUS = 10
CANDIDATE_PASSED_PAWN_BONUS = 8
CENTRAL_DUO_BONUS = 12
PAWN_MAJORITY_ENDGAME_BONUS = 10
BLOCKED_CENTRAL_PAWN_PENALTY = 8
BISHOP_PAIR_BONUS = 28
ROOK_OPEN_FILE_BONUS = 18
ROOK_SEMI_OPEN_FILE_BONUS = 10
ROOK_SEVENTH_RANK_BONUS = 12
ROOK_TRAPPED_PENALTY = 18
CONNECTED_ROOKS_BONUS = 14
QUEEN_ROOK_BATTERY_BONUS = 10
CASTLED_KING_BONUS = 22
PAWN_SHIELD_BONUS = 7
OPEN_KING_FILE_PENALTY = 9
EXPOSED_CENTRAL_KING_PENALTY = 16
KING_ZONE_ATTACK_PENALTY = 5
BACK_RANK_TENSION_PENALTY = 10
EARLY_QUEEN_MOVE_PENALTY = 10
EARLY_ROOK_MOVE_PENALTY = 7
UNDEVELOPED_MINOR_PIECE_PENALTY = 5
KNIGHT_OUTPOST_BONUS = 18
KNIGHT_RIM_PENALTY = 14
BAD_BISHOP_PAWN_PENALTY = 4
LONG_DIAGONAL_BISHOP_BONUS = 8
CENTRAL_MINOR_PIECE_BONUS = 6
MINOR_COORDINATION_BONUS = 10
SPACE_ADVANTAGE_BONUS = 4
CRAMPED_PIECE_PENALTY = 3
ACTIVE_KING_ENDGAME_BONUS = 24
BLOCKADED_PASSED_PAWN_BONUS = 10
SIMPLIFICATION_BONUS_SCALE = 14
QUEENS_OFF_WHEN_AHEAD_BONUS = 18
ROOKS_OFF_WHEN_AHEAD_BONUS = 10
MATING_MATERIAL_BASE = {
    "KQK": 250,
    "KRK": 180,
    "KRRK": 260,
    "KQRK": 320,
}
MATING_EDGE_BONUS = 24
MATING_KING_DISTANCE_BONUS = 8
HEAVY_PIECE_COORDINATION_BONUS = 12
KING_CUTOFF_BONUS = 14
ROOK_BEHIND_PASSED_PAWN_BONUS = 18
KING_ESCORT_PASSED_PAWN_BONUS = 12
PROMOTION_SQUARE_CONTROL_BONUS = 10
ENEMY_KING_BOX_BONUS = 6
COUNTERPLAY_REDUCTION_BONUS = 8
HEAVY_PIECE_ACTIVITY_BONUS = 8
LUFT_PROGRESS_BONUS = 8
VOLUNTARY_REPETITION_PENALTY = 32
REPETITION_PROGRESS_THRESHOLD = 120
REPETITION_PROGRESS_ONLY_THRESHOLD = 24

PASSED_PAWN_BONUS_BY_PROGRESS = {
    0: 0,
    1: 6,
    2: 12,
    3: 20,
    4: 32,
    5: 50,
    6: 80,
}

MOBILITY_WEIGHTS = {
    PieceType.KNIGHT: 4,
    PieceType.BISHOP: 4,
}

CENTER_FILES = {3, 4}
EXTENDED_CENTER_FILES = {2, 3, 4, 5}
EXTENDED_CENTER_RANKS = {2, 3, 4, 5}
CENTRAL_SQUARES = {
    (3, 3),
    (3, 4),
    (4, 3),
    (4, 4),
}
