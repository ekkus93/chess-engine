"""Recognize recurring pawn structures and reward matching strategic plans."""

from __future__ import annotations

from dataclasses import dataclass

from chess_game.chess.board import Board
from chess_game.chess.board.attack_utils import piece_attacks_square
from chess_game.chess.constants import (
    ConstantSquare,
    get_col_constant,
    get_row_constant,
)
from chess_game.chess.move import Move
from chess_game.chess.strategy_utils import (
    center_distance,
    file_pawn_state,
    is_passed_pawn,
    iter_board_pieces,
    iter_color_pieces,
    king_coordinates,
)
from chess_game.chess.types import Color, PieceType

_QUEENSIDE_FILES = {0, 1, 2}
_LONG_DIAGONAL_SQUARES = {(1, 1), (1, 6), (6, 1), (6, 6)}
_OPEN_CENTER_LINE_BONUS = 24
_OPEN_CENTER_SEMI_OPEN_BONUS = 16
_CLOSED_CENTER_MANEUVER_BONUS = 24
_CLOSED_CENTER_BREAK_BONUS = 18
_STRUCTURAL_BLOCKADE_BONUS = 36
_MINORITY_ATTACK_BONUS = 64
_FAVORABLE_MINOR_EXCHANGE_BONUS = 1_200
_WRONG_MINOR_EXCHANGE_PENALTY = 1_200
_STRUCTURAL_DEFENDER_EXCHANGE_BONUS = 450


@dataclass(frozen=True)
class StructuralTarget:
    """A pawn whose structure suggests a durable plan against it."""

    row: int
    col: int
    blockade_row: int


@dataclass(frozen=True)
class SideStructureProfile:
    """Structure features for one side."""

    isolated_queen_pawns: tuple[StructuralTarget, ...]
    hanging_pawns: tuple[StructuralTarget, ...]
    minority_attack_file: int | None
    outside_passed_files: tuple[int, ...]
    protected_passed_files: tuple[int, ...]


@dataclass(frozen=True)
class StructureProfile:
    """Lightweight structure grouping used by evaluation and move ordering."""

    open_center: bool
    closed_center: bool
    opposite_side_castling: bool
    rook_endgame_with_passer_plan: bool
    white: SideStructureProfile
    black: SideStructureProfile

    def side(self, color: Color) -> SideStructureProfile:
        """Return the structure profile for the given color."""

        return self.white if color == Color.WHITE else self.black

    def enemy(self, color: Color) -> SideStructureProfile:
        """Return the structure profile for the opposing color."""

        return self.black if color == Color.WHITE else self.white


def structure_profile(board: Board) -> StructureProfile:
    """Return the recognized structure family for the current position."""

    white_pawns = _pawn_positions(board, Color.WHITE)
    black_pawns = _pawn_positions(board, Color.BLACK)
    white_files = {col for _, col in white_pawns}
    black_files = {col for _, col in black_pawns}
    white_central = _central_pawns(white_pawns)
    black_central = _central_pawns(black_pawns)
    locked_pairs = _locked_central_pairs(white_central, black_central)
    white_profile = _side_structure_profile(
        Color.WHITE,
        white_pawns,
        white_files,
        black_pawns,
        black_files,
    )
    black_profile = _side_structure_profile(
        Color.BLACK,
        black_pawns,
        black_files,
        white_pawns,
        white_files,
    )
    return StructureProfile(
        open_center=locked_pairs == 0 and len(white_central) + len(black_central) <= 2,
        closed_center=locked_pairs >= 1 and len(white_central) + len(black_central) >= 3,
        opposite_side_castling=_opposite_side_castling(board),
        rook_endgame_with_passer_plan=_rook_endgame_with_passer_plan(
            board,
            white_profile,
            black_profile,
        ),
        white=white_profile,
        black=black_profile,
    )


def structure_plan_bonus(board: Board, color: Color, kind: PieceType, move: Move) -> int:
    """Return a quiet-order bonus when a move matches the current structure."""

    profile = structure_profile(board)
    score = 0
    if profile.open_center:
        score += _open_center_bonus(board, color, kind, move)
    if profile.closed_center:
        score += _closed_center_bonus(kind, color, move)
    score += _structural_target_bonus(profile.enemy(color), kind, move)
    if _is_minority_attack_push(profile.side(color).minority_attack_file, color, kind, move):
        score += _MINORITY_ATTACK_BONUS
    return score


def structure_capture_bonus(
    board: Board,
    color: Color,
    attacker_kind: PieceType,
    captured_kind: PieceType,
    captured_square: ConstantSquare,
) -> int:
    """Return capture-order adjustments from structure-specific plans."""

    profile = structure_profile(board)
    score = _minor_piece_exchange_bonus(profile, attacker_kind, captured_kind)
    score += _structural_defender_capture_bonus(
        board,
        profile.enemy(color),
        captured_square,
    )
    return score


def _pawn_positions(board: Board, color: Color) -> list[tuple[int, int]]:
    return [
        (row, col)
        for piece, row, col in iter_color_pieces(board, color)
        if piece.kind == PieceType.PAWN
    ]


def _central_pawns(pawn_positions: list[tuple[int, int]]) -> list[tuple[int, int]]:
    return [(row, col) for row, col in pawn_positions if col in {3, 4}]


def _locked_central_pairs(
    white_central: list[tuple[int, int]],
    black_central: list[tuple[int, int]],
) -> int:
    black_lookup = set(black_central)
    return sum(1 for row, col in white_central if (row - 1, col) in black_lookup)


def _side_structure_profile(
    color: Color,
    pawn_positions: list[tuple[int, int]],
    pawn_files: set[int],
    enemy_pawns: list[tuple[int, int]],
    enemy_files: set[int],
) -> SideStructureProfile:
    isolated_queen_pawns = _isolated_queen_pawn_targets(pawn_positions, pawn_files)
    hanging_pawns = _hanging_pawn_targets(pawn_positions, pawn_files)
    minority_attack_file = _minority_attack_file(pawn_files, enemy_files)
    outside_passed_files, protected_passed_files = _passed_pawn_files(
        color,
        pawn_positions,
        enemy_pawns,
    )
    return SideStructureProfile(
        isolated_queen_pawns=isolated_queen_pawns,
        hanging_pawns=hanging_pawns,
        minority_attack_file=minority_attack_file,
        outside_passed_files=outside_passed_files,
        protected_passed_files=protected_passed_files,
    )


def _isolated_queen_pawn_targets(
    pawn_positions: list[tuple[int, int]],
    pawn_files: set[int],
) -> tuple[StructuralTarget, ...]:
    return tuple(
        StructuralTarget(row=row, col=col, blockade_row=_blockade_row(row))
        for row, col in pawn_positions
        if col == 3 and 2 not in pawn_files and 4 not in pawn_files
    )


def _hanging_pawn_targets(
    pawn_positions: list[tuple[int, int]],
    pawn_files: set[int],
) -> tuple[StructuralTarget, ...]:
    central_lookup = {(row, col) for row, col in pawn_positions if col in {2, 3, 4}}
    targets: list[StructuralTarget] = []
    for left_file, right_file in ((2, 3), (3, 4)):
        if left_file not in pawn_files or right_file not in pawn_files:
            continue
        if left_file - 1 in pawn_files or right_file + 1 in pawn_files:
            continue
        for row, col in central_lookup:
            if col in {left_file, right_file}:
                targets.append(
                    StructuralTarget(row=row, col=col, blockade_row=_blockade_row(row))
                )
    return tuple(sorted(targets, key=lambda target: (target.row, target.col)))


def _minority_attack_file(pawn_files: set[int], enemy_files: set[int]) -> int | None:
    own_queenside = len(pawn_files & _QUEENSIDE_FILES)
    enemy_queenside = len(enemy_files & _QUEENSIDE_FILES)
    if own_queenside == 2 and enemy_queenside >= 3 and 1 in pawn_files:
        return 1
    return None


def _passed_pawn_files(
    color: Color,
    pawn_positions: list[tuple[int, int]],
    enemy_pawns: list[tuple[int, int]],
) -> tuple[tuple[int, ...], tuple[int, ...]]:
    outside: list[int] = []
    protected: list[int] = []
    for row, col in pawn_positions:
        if not is_passed_pawn(color, row, col, enemy_pawns):
            continue
        if _is_outside_passer(col):
            outside.append(col)
        if _is_protected_passer(color, row, col, pawn_positions):
            protected.append(col)
    return tuple(sorted(set(outside))), tuple(sorted(set(protected)))


def _is_outside_passer(col: int) -> bool:
    return col in {0, 7}


def _is_protected_passer(
    color: Color,
    row: int,
    col: int,
    pawn_positions: list[tuple[int, int]],
) -> bool:
    support_row = row + (1 if color == Color.WHITE else -1)
    return any(
        ally_row == support_row and abs(ally_col - col) == 1
        for ally_row, ally_col in pawn_positions
    )


def _blockade_row(row: int) -> int:
    return row + 1 if row <= 3 else row - 1


def _opposite_side_castling(board: Board) -> bool:
    white_king = king_coordinates(board, Color.WHITE)
    black_king = king_coordinates(board, Color.BLACK)
    if white_king is None or black_king is None:
        return False
    if white_king[0] != 7 or black_king[0] != 0:
        return False
    if white_king[1] not in {2, 6} or black_king[1] not in {2, 6}:
        return False
    return white_king[1] != black_king[1]


def _rook_endgame_with_passer_plan(
    board: Board,
    white: SideStructureProfile,
    black: SideStructureProfile,
) -> bool:
    if any(
        piece.kind not in {PieceType.KING, PieceType.ROOK, PieceType.PAWN}
        for piece, _, _ in iter_board_pieces(board)
    ):
        return False
    return bool(
        white.outside_passed_files
        or white.protected_passed_files
        or black.outside_passed_files
        or black.protected_passed_files
    )


def _open_center_bonus(board: Board, color: Color, kind: PieceType, move: Move) -> int:
    if kind not in {PieceType.ROOK, PieceType.QUEEN}:
        return 0
    file_state = file_pawn_state(board, color, int(move.end.col))
    if int(move.end.col) not in {3, 4}:
        return 0
    if file_state == "open":
        return _OPEN_CENTER_LINE_BONUS
    if file_state == "semi-open":
        return _OPEN_CENTER_SEMI_OPEN_BONUS
    return 0


def _closed_center_bonus(kind: PieceType, color: Color, move: Move) -> int:
    if kind in {PieceType.KNIGHT, PieceType.BISHOP} and _is_closed_center_maneuver(kind, move):
        return _CLOSED_CENTER_MANEUVER_BONUS
    if kind == PieceType.PAWN and _is_closed_center_break(color, move):
        return _CLOSED_CENTER_BREAK_BONUS
    return 0


def _is_closed_center_maneuver(kind: PieceType, move: Move) -> bool:
    start = (int(move.start.row), int(move.start.col))
    end = (int(move.end.row), int(move.end.col))
    if kind == PieceType.BISHOP and end in _LONG_DIAGONAL_SQUARES:
        return True
    return center_distance(*end) < center_distance(*start)


def _is_closed_center_break(color: Color, move: Move) -> bool:
    if int(move.start.col) != int(move.end.col):
        return False
    if int(move.start.col) not in {2, 5}:
        return False
    if color == Color.WHITE:
        return int(move.end.row) < int(move.start.row)
    return int(move.end.row) > int(move.start.row)


def _structural_target_bonus(
    enemy_profile: SideStructureProfile,
    kind: PieceType,
    move: Move,
) -> int:
    if kind == PieceType.PAWN:
        return 0
    target_square = (int(move.end.row), int(move.end.col))
    for target in enemy_profile.isolated_queen_pawns + enemy_profile.hanging_pawns:
        if target_square == (target.blockade_row, target.col):
            return _STRUCTURAL_BLOCKADE_BONUS
    return 0


def _minor_piece_exchange_bonus(
    profile: StructureProfile,
    attacker_kind: PieceType,
    captured_kind: PieceType,
) -> int:
    is_minor_exchange = (
        attacker_kind in {PieceType.BISHOP, PieceType.KNIGHT}
        and captured_kind in {PieceType.BISHOP, PieceType.KNIGHT}
    )
    if not is_minor_exchange:
        return 0
    if profile.open_center:
        return _open_center_exchange_bonus(attacker_kind, captured_kind)
    if profile.closed_center:
        return _closed_center_exchange_bonus(attacker_kind, captured_kind)
    return 0


def _open_center_exchange_bonus(
    attacker_kind: PieceType,
    captured_kind: PieceType,
) -> int:
    if attacker_kind == PieceType.BISHOP and captured_kind == PieceType.KNIGHT:
        return _FAVORABLE_MINOR_EXCHANGE_BONUS
    if attacker_kind == PieceType.KNIGHT and captured_kind == PieceType.BISHOP:
        return -_WRONG_MINOR_EXCHANGE_PENALTY
    return 0


def _closed_center_exchange_bonus(
    attacker_kind: PieceType,
    captured_kind: PieceType,
) -> int:
    if attacker_kind == PieceType.KNIGHT and captured_kind == PieceType.BISHOP:
        return _FAVORABLE_MINOR_EXCHANGE_BONUS
    if attacker_kind == PieceType.BISHOP and captured_kind == PieceType.KNIGHT:
        return -_WRONG_MINOR_EXCHANGE_PENALTY
    return 0


def _structural_defender_capture_bonus(
    board: Board,
    enemy_profile: SideStructureProfile,
    captured_square: ConstantSquare,
) -> int:
    captured_piece = board.get_piece(captured_square)
    if captured_piece is None:
        return 0
    for target in enemy_profile.isolated_queen_pawns + enemy_profile.hanging_pawns:
        if _piece_defends_structural_target(board, captured_piece, captured_square, target):
            return _STRUCTURAL_DEFENDER_EXCHANGE_BONUS
    return 0


def _piece_defends_structural_target(
    board: Board,
    piece,
    piece_square: ConstantSquare,
    target: StructuralTarget,
) -> bool:
    return piece_attacks_square(
        piece,
        piece_square,
        _target_square(target.row, target.col),
        board,
    ) or piece_attacks_square(
        piece,
        piece_square,
        _target_square(target.blockade_row, target.col),
        board,
    )


def _target_square(row: int, col: int) -> ConstantSquare:
    return ConstantSquare(row=get_row_constant(row), col=get_col_constant(col))


def _is_minority_attack_push(
    minority_attack_file: int | None,
    color: Color,
    kind: PieceType,
    move: Move,
) -> bool:
    if kind != PieceType.PAWN or minority_attack_file is None:
        return False
    if (
        int(move.start.col) != minority_attack_file
        or int(move.end.col) != minority_attack_file
    ):
        return False
    if color == Color.WHITE:
        return int(move.end.row) < int(move.start.row)
    return int(move.end.row) > int(move.start.row)
