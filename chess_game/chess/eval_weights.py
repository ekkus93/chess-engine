"""Tunable evaluation weights for Texel tuning.

All weights that can be optimised by SPSA are bundled into the ``EvalWeights``
dataclass.  Non-tunable structural constants (``CENTER_FILES``,
``CENTRAL_SQUARES``, threshold integers) remain in ``evaluation_tables.py``.
"""

from __future__ import annotations

import copy
from dataclasses import dataclass, field, fields

from chess_game.chess.evaluation_tables import (
    BISHOP_TABLE,
    KING_TABLE,
    KNIGHT_TABLE,
    MATERIAL_VALUES,
    PAWN_TABLE,
    QUEEN_TABLE,
    ROOK_TABLE,
)
from chess_game.chess.types import PieceType


def _copy_table(table: list[list[int]]) -> list[list[int]]:
    """Return a deep copy of a piece-square table."""
    return [list(row) for row in table]


# ---------------------------------------------------------------------------
# Sub-group dataclasses
# ---------------------------------------------------------------------------


@dataclass
class MaterialWeights:
    """Centipawn values for each non-king piece type."""

    pawn: int = MATERIAL_VALUES[PieceType.PAWN]
    knight: int = MATERIAL_VALUES[PieceType.KNIGHT]
    bishop: int = MATERIAL_VALUES[PieceType.BISHOP]
    rook: int = MATERIAL_VALUES[PieceType.ROOK]
    queen: int = MATERIAL_VALUES[PieceType.QUEEN]

    def as_dict(self) -> dict[PieceType, int]:
        """Return material values keyed by ``PieceType``."""
        return {
            PieceType.PAWN: self.pawn,
            PieceType.KNIGHT: self.knight,
            PieceType.BISHOP: self.bishop,
            PieceType.ROOK: self.rook,
            PieceType.QUEEN: self.queen,
        }


@dataclass
class TableWeights:
    """Piece-square tables (8×8 lists, row 0 = rank 8 from White's perspective).

    Default values are sourced from ``evaluation_tables`` to avoid duplication.
    """

    pawn_table: list[list[int]] = field(
        default_factory=lambda: _copy_table(PAWN_TABLE)
    )
    knight_table: list[list[int]] = field(
        default_factory=lambda: _copy_table(KNIGHT_TABLE)
    )
    bishop_table: list[list[int]] = field(
        default_factory=lambda: _copy_table(BISHOP_TABLE)
    )
    rook_table: list[list[int]] = field(
        default_factory=lambda: _copy_table(ROOK_TABLE)
    )
    queen_table: list[list[int]] = field(
        default_factory=lambda: _copy_table(QUEEN_TABLE)
    )
    king_table: list[list[int]] = field(
        default_factory=lambda: _copy_table(KING_TABLE)
    )


@dataclass
class PawnWeights:
    """Pawn-structure penalty / bonus weights."""

    isolated_pawn_penalty: int = 12
    doubled_pawn_penalty: int = 10
    backward_pawn_penalty: int = 8
    pawn_island_penalty: int = 7
    weak_chain_pawn_penalty: int = 6
    connected_passed_pawn_bonus: int = 10
    candidate_passed_pawn_bonus: int = 8
    central_duo_bonus: int = 12
    pawn_majority_endgame_bonus: int = 10
    blocked_central_pawn_penalty: int = 8
    king_shelter_loosening_penalty: int = 10
    # 7-entry dict stored as a flat list (index = progress rank 0–6)
    _passed_pawn_bonuses: list[int] = field(
        default_factory=lambda: [0, 6, 12, 20, 32, 50, 80]
    )

    def passed_pawn_bonus_by_progress(self) -> dict[int, int]:
        """Return ``{progress: bonus}`` for ranks 0–6."""
        return dict(enumerate(self._passed_pawn_bonuses))


@dataclass
class PieceActivityWeights:
    """Piece-activity bonuses and penalties."""

    bishop_pair_bonus: int = 28
    rook_open_file_bonus: int = 18
    rook_semi_open_file_bonus: int = 10
    rook_seventh_rank_bonus: int = 12
    rook_trapped_penalty: int = 18
    connected_rooks_bonus: int = 14
    queen_rook_battery_bonus: int = 10
    knight_outpost_bonus: int = 18
    knight_strong_square_bonus: int = 16
    knight_rim_penalty: int = 14
    bad_bishop_pawn_penalty: int = 4
    long_diagonal_bishop_bonus: int = 8
    central_minor_piece_bonus: int = 6
    minor_coordination_bonus: int = 10
    space_advantage_bonus: int = 4
    cramped_piece_penalty: int = 3
    # Mobility weights stored as a flat list [knight_weight, bishop_weight]
    _mobility: list[int] = field(default_factory=lambda: [4, 4])

    def mobility_weights(self) -> dict[PieceType, int]:
        """Return ``{PieceType: weight}`` for KNIGHT and BISHOP."""
        return {
            PieceType.KNIGHT: self._mobility[0],
            PieceType.BISHOP: self._mobility[1],
        }


@dataclass
class KingSafetyWeights:
    """King-safety bonus/penalty weights."""

    castled_king_bonus: int = 22
    pawn_shield_bonus: int = 7
    open_king_file_penalty: int = 9
    exposed_central_king_penalty: int = 16
    king_zone_attack_penalty: int = 5
    back_rank_tension_penalty: int = 10
    central_king_with_queens_penalty: int = 14
    heavy_file_pressure_penalty: int = 10
    defender_distance_penalty: int = 6


@dataclass
class DevelopmentWeights:
    """Opening / development penalty and bonus weights."""

    early_queen_move_penalty: int = 10
    early_rook_move_penalty: int = 7
    early_flank_raid_penalty: int = 10
    early_queen_raid_penalty: int = 16
    undeveloped_minor_piece_penalty: int = 5


@dataclass
class EndgameWeights:
    """Endgame-specific bonus and penalty weights."""

    space_advantage_bonus: int = 4  # alias kept for cross-reference
    voluntary_repetition_penalty: int = 32
    repetition_progress_threshold: int = 120
    repetition_progress_only_threshold: int = 24
    active_king_endgame_bonus: int = 24
    blockaded_passed_pawn_bonus: int = 10
    simplification_bonus_scale: int = 14
    queens_off_when_ahead_bonus: int = 18
    rooks_off_when_ahead_bonus: int = 10
    luft_progress_bonus: int = 8


@dataclass
class MatingWeights:
    """Mating-material scoring weights."""

    mating_edge_bonus: int = 24
    mating_king_distance_bonus: int = 8
    heavy_piece_coordination_bonus: int = 12
    king_cutoff_bonus: int = 14
    rook_behind_passed_pawn_bonus: int = 18
    king_escort_passed_pawn_bonus: int = 12
    promotion_square_control_bonus: int = 10
    enemy_king_box_bonus: int = 6
    counterplay_reduction_bonus: int = 8
    heavy_piece_activity_bonus: int = 8
    # Mating material bases stored as a flat list [KQK, KRK, KRRK, KQRK]
    _mating_bases: list[int] = field(default_factory=lambda: [250, 180, 260, 320])

    def mating_material_base(self) -> dict[str, int]:
        """Return ``{endgame_type: base_score}``."""
        keys = ["KQK", "KRK", "KRRK", "KQRK"]
        return dict(zip(keys, self._mating_bases))


# ---------------------------------------------------------------------------
# Top-level EvalWeights container
# ---------------------------------------------------------------------------

# The total number of scalar parameters exposed by EvalWeights.to_flat_list().
# Update this constant whenever the dataclass structure changes.
# Breakdown:
#   MaterialWeights: 5 scalars
#   TableWeights: 6 tables × 64 cells = 384
#   PawnWeights: 12 scalars + 7 passed-pawn bonuses = 19
#   PieceActivityWeights: 13 scalars + 2 mobility = 15
#   KingSafetyWeights: 9 scalars
#   DevelopmentWeights: 5 scalars
#   EndgameWeights: 10 scalars
#   MatingWeights: 10 scalars + 4 mating bases = 14
#   Total: 5 + 384 + 19 + 15 + 9 + 5 + 10 + 14 = 461 + 2 (space_advantage re-counted) = 463
EVAL_WEIGHTS_FLAT_LENGTH = 463


@dataclass
class EvalWeights:
    """Container for all tunable evaluation weights.

    Usage::

        weights = EvalWeights.default()          # identical to current hardcoded values
        score = evaluate(board, weights)         # use custom weights
        flat = weights.to_flat_list()            # for SPSA
        w2 = EvalWeights.from_flat_list(flat)    # reconstruct from flat list
    """

    material: MaterialWeights = field(default_factory=MaterialWeights)
    tables: TableWeights = field(default_factory=TableWeights)
    pawns: PawnWeights = field(default_factory=PawnWeights)
    pieces: PieceActivityWeights = field(default_factory=PieceActivityWeights)
    king: KingSafetyWeights = field(default_factory=KingSafetyWeights)
    development: DevelopmentWeights = field(default_factory=DevelopmentWeights)
    endgame: EndgameWeights = field(default_factory=EndgameWeights)
    mating: MatingWeights = field(default_factory=MatingWeights)

    # ------------------------------------------------------------------
    # Factory methods
    # ------------------------------------------------------------------

    @classmethod
    def default(cls) -> "EvalWeights":
        """Return an instance with the current hardcoded baseline values."""
        return cls()

    # ------------------------------------------------------------------
    # Serialisation helpers
    # ------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Return a JSON-serialisable dictionary representation."""
        result: dict = {}
        for grp_field in fields(self):
            grp = getattr(self, grp_field.name)
            grp_dict: dict = {}
            for f in fields(grp):
                val = getattr(grp, f.name)
                grp_dict[f.name] = val
            result[grp_field.name] = grp_dict
        return result

    @classmethod
    def from_dict(cls, data: dict) -> "EvalWeights":
        """Reconstruct an ``EvalWeights`` from a dictionary (e.g. loaded from JSON)."""
        w = cls()
        sub_classes = {
            "material": MaterialWeights,
            "tables": TableWeights,
            "pawns": PawnWeights,
            "pieces": PieceActivityWeights,
            "king": KingSafetyWeights,
            "development": DevelopmentWeights,
            "endgame": EndgameWeights,
            "mating": MatingWeights,
        }
        for grp_name, grp_cls in sub_classes.items():
            if grp_name not in data:
                continue
            grp_data = data[grp_name]
            grp_obj = getattr(w, grp_name)
            for f in fields(grp_cls):
                if f.name in grp_data:
                    object.__setattr__(grp_obj, f.name, grp_data[f.name])
        return w

    # ------------------------------------------------------------------
    # Flat-list helpers (for SPSA)
    # ------------------------------------------------------------------

    def to_flat_list(self) -> list[float]:
        """Flatten all tunable values into a single list of floats."""
        result: list[float] = []
        for grp_field in fields(self):
            grp = getattr(self, grp_field.name)
            for f in fields(grp):
                val = getattr(grp, f.name)
                if isinstance(val, list):
                    for row in val:
                        if isinstance(row, list):
                            result.extend(float(x) for x in row)
                        else:
                            result.append(float(row))
                else:
                    result.append(float(val))
        return result

    @classmethod
    def from_flat_list(
        cls,
        values: list[float],
        reference: "EvalWeights | None" = None,
    ) -> "EvalWeights":
        """Reconstruct an ``EvalWeights`` from a flat list of floats.

        ``reference`` is only used to infer list shapes; if ``None`` a
        default instance is used.
        """
        ref = reference if reference is not None else cls.default()
        if len(values) != len(ref.to_flat_list()):
            raise ValueError(
                f"flat list length {len(values)} does not match expected "
                f"{len(ref.to_flat_list())}"
            )
        w = copy.deepcopy(ref)
        idx = 0
        for grp_field in fields(w):
            grp = getattr(w, grp_field.name)
            for f in fields(grp):
                val = getattr(grp, f.name)
                if isinstance(val, list):
                    new_val: list = []
                    for row in val:
                        if isinstance(row, list):
                            new_row = [int(round(values[idx + i])) for i in range(len(row))]
                            idx += len(row)
                            new_val.append(new_row)
                        else:
                            new_val.append(int(round(values[idx])))
                            idx += 1
                    object.__setattr__(grp, f.name, new_val)
                else:
                    object.__setattr__(grp, f.name, int(round(values[idx])))
                    idx += 1
        return w
