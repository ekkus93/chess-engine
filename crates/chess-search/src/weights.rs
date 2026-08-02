use core::fmt;

use chess_core::PieceKind;

/// Current serialized evaluation-weight schema.
pub const EVALUATION_WEIGHT_SCHEMA_VERSION: u16 = 1;
/// Stable identifier for the built-in baseline weight set.
pub const BASELINE_WEIGHT_SET_ID: u64 = 0x4241_5345_4c49_4e45;
/// Number of signed scalar values in the canonical serialized weight vector.
pub const WEIGHT_VALUE_COUNT: usize = 816;

const MAX_WEIGHT_MAGNITUDE: i32 = 10_000;
const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;

/// A middlegame/endgame pair used by tapered evaluation.
#[derive(Clone, Copy, Debug, Default, Eq, PartialEq)]
pub struct PhasedWeight {
    /// Middlegame value.
    pub middlegame: i16,
    /// Endgame value.
    pub endgame: i16,
}

impl PhasedWeight {
    /// Zero in both phases.
    pub const ZERO: Self = Self::new(0, 0);

    /// Creates a phased value.
    #[must_use]
    pub const fn new(middlegame: i16, endgame: i16) -> Self {
        Self {
            middlegame,
            endgame,
        }
    }
}

/// Complete named static-evaluation configuration.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct EvaluationWeights {
    /// Material value by [`PieceKind`].
    pub material: [PhasedWeight; 6],
    /// White-oriented piece-square value by piece kind and square.
    pub piece_square: [[PhasedWeight; 64]; 6],
    /// Mobility value per reachable square by piece kind.
    pub mobility: [PhasedWeight; 6],
    /// Penalty per isolated pawn.
    pub isolated_pawn: PhasedWeight,
    /// Penalty per pawn beyond the first on a file.
    pub doubled_pawn: PhasedWeight,
    /// Passed-pawn bonus multiplied by advancement.
    pub passed_pawn: PhasedWeight,
    /// Connected-pawn bonus multiplied by advancement.
    pub connected_pawn: PhasedWeight,
    /// Bonus for retaining both bishops.
    pub bishop_pair: PhasedWeight,
    /// Bonus for a rook on a file without pawns.
    pub rook_open_file: PhasedWeight,
    /// Bonus for a rook on a file without a friendly pawn.
    pub rook_semi_open_file: PhasedWeight,
    /// Bonus for a rook on the seventh rank.
    pub rook_seventh_rank: PhasedWeight,
    /// Bonus per friendly pawn shielding the king.
    pub king_shield: PhasedWeight,
    /// Penalty per enemy-attacked square in the king zone.
    pub king_zone_attack: PhasedWeight,
    /// Bonus per controlled square in enemy space.
    pub space: PhasedWeight,
    /// Bonus for central king placement, tapered toward the endgame.
    pub king_activity: PhasedWeight,
}

impl EvaluationWeights {
    /// Explicit built-in baseline defaults.
    pub const DEFAULT: Self = Self {
        material: [
            PhasedWeight::new(100, 120),
            PhasedWeight::new(320, 300),
            PhasedWeight::new(330, 320),
            PhasedWeight::new(500, 520),
            PhasedWeight::new(900, 900),
            PhasedWeight::ZERO,
        ],
        piece_square: baseline_piece_square_tables(),
        mobility: [
            PhasedWeight::ZERO,
            PhasedWeight::new(4, 4),
            PhasedWeight::new(5, 5),
            PhasedWeight::new(2, 4),
            PhasedWeight::new(1, 2),
            PhasedWeight::ZERO,
        ],
        isolated_pawn: PhasedWeight::new(-12, -10),
        doubled_pawn: PhasedWeight::new(-10, -12),
        passed_pawn: PhasedWeight::new(12, 28),
        connected_pawn: PhasedWeight::new(5, 10),
        bishop_pair: PhasedWeight::new(28, 40),
        rook_open_file: PhasedWeight::new(18, 10),
        rook_semi_open_file: PhasedWeight::new(10, 6),
        rook_seventh_rank: PhasedWeight::new(20, 28),
        king_shield: PhasedWeight::new(12, 2),
        king_zone_attack: PhasedWeight::new(-8, -2),
        space: PhasedWeight::new(3, 1),
        king_activity: PhasedWeight::new(0, 10),
    };

    /// Returns the canonical dense value vector used for checksums and tools.
    #[must_use]
    pub fn values(&self) -> [i16; WEIGHT_VALUE_COUNT] {
        let mut values = [0_i16; WEIGHT_VALUE_COUNT];
        let mut index = 0;
        for weight in self.material {
            write_phased(&mut values, &mut index, weight);
        }
        for table in self.piece_square {
            for weight in table {
                write_phased(&mut values, &mut index, weight);
            }
        }
        for weight in self.mobility {
            write_phased(&mut values, &mut index, weight);
        }
        for weight in [
            self.isolated_pawn,
            self.doubled_pawn,
            self.passed_pawn,
            self.connected_pawn,
            self.bishop_pair,
            self.rook_open_file,
            self.rook_semi_open_file,
            self.rook_seventh_rank,
            self.king_shield,
            self.king_zone_attack,
            self.space,
            self.king_activity,
        ] {
            write_phased(&mut values, &mut index, weight);
        }
        debug_assert_eq!(index, WEIGHT_VALUE_COUNT);
        values
    }

    /// Reconstructs weights from the canonical dense value vector.
    #[must_use]
    pub fn from_values(values: [i16; WEIGHT_VALUE_COUNT]) -> Self {
        let mut index = 0;
        let mut material = [PhasedWeight::ZERO; 6];
        for weight in &mut material {
            *weight = read_phased(&values, &mut index);
        }
        let mut piece_square = [[PhasedWeight::ZERO; 64]; 6];
        for table in &mut piece_square {
            for weight in table {
                *weight = read_phased(&values, &mut index);
            }
        }
        let mut mobility = [PhasedWeight::ZERO; 6];
        for weight in &mut mobility {
            *weight = read_phased(&values, &mut index);
        }
        let isolated_pawn = read_phased(&values, &mut index);
        let doubled_pawn = read_phased(&values, &mut index);
        let passed_pawn = read_phased(&values, &mut index);
        let connected_pawn = read_phased(&values, &mut index);
        let bishop_pair = read_phased(&values, &mut index);
        let rook_open_file = read_phased(&values, &mut index);
        let rook_semi_open_file = read_phased(&values, &mut index);
        let rook_seventh_rank = read_phased(&values, &mut index);
        let king_shield = read_phased(&values, &mut index);
        let king_zone_attack = read_phased(&values, &mut index);
        let space = read_phased(&values, &mut index);
        let king_activity = read_phased(&values, &mut index);
        debug_assert_eq!(index, WEIGHT_VALUE_COUNT);
        Self {
            material,
            piece_square,
            mobility,
            isolated_pawn,
            doubled_pawn,
            passed_pawn,
            connected_pawn,
            bishop_pair,
            rook_open_file,
            rook_semi_open_file,
            rook_seventh_rank,
            king_shield,
            king_zone_attack,
            space,
            king_activity,
        }
    }
}

/// A versioned, identified, checksummed evaluation-weight set.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct EvaluationWeightSet {
    /// Serialized schema version.
    pub schema_version: u16,
    /// Stable caller-selected weight-set identifier.
    pub identifier: u64,
    /// Named evaluator weights.
    pub weights: EvaluationWeights,
    /// Canonical FNV-1a checksum over schema, identifier, and values.
    pub checksum: u64,
}

impl EvaluationWeightSet {
    /// Constructs a valid weight set and computes its checksum.
    #[must_use]
    pub fn new(identifier: u64, weights: EvaluationWeights) -> Self {
        let mut set = Self {
            schema_version: EVALUATION_WEIGHT_SCHEMA_VERSION,
            identifier,
            weights,
            checksum: 0,
        };
        set.checksum = set.computed_checksum();
        set
    }

    /// Constructs a weight set from serialized parts for subsequent validation.
    #[must_use]
    pub const fn from_parts(
        schema_version: u16,
        identifier: u64,
        weights: EvaluationWeights,
        checksum: u64,
    ) -> Self {
        Self {
            schema_version,
            identifier,
            weights,
            checksum,
        }
    }

    /// Returns the explicit built-in baseline set.
    #[must_use]
    pub fn baseline() -> Self {
        Self::new(BASELINE_WEIGHT_SET_ID, EvaluationWeights::DEFAULT)
    }

    /// Computes the canonical checksum for the current fields.
    #[must_use]
    pub fn computed_checksum(&self) -> u64 {
        let mut hash = FNV_OFFSET;
        hash = hash_bytes(hash, &self.schema_version.to_le_bytes());
        hash = hash_bytes(hash, &self.identifier.to_le_bytes());
        for value in self.weights.values() {
            hash = hash_bytes(hash, &value.to_le_bytes());
        }
        hash
    }

    /// Validates schema, identifier, value ranges, material ordering, and checksum.
    pub fn validate(&self) -> Result<(), WeightValidationError> {
        if self.schema_version != EVALUATION_WEIGHT_SCHEMA_VERSION {
            return Err(WeightValidationError::SchemaVersion {
                expected: EVALUATION_WEIGHT_SCHEMA_VERSION,
                found: self.schema_version,
            });
        }
        if self.identifier == 0 {
            return Err(WeightValidationError::EmptyIdentifier);
        }
        for (index, value) in self.weights.values().into_iter().enumerate() {
            if i32::from(value).abs() > MAX_WEIGHT_MAGNITUDE {
                return Err(WeightValidationError::WeightOutOfRange { index, value });
            }
        }
        validate_material(self.weights.material)?;
        let expected = self.computed_checksum();
        if self.checksum != expected {
            return Err(WeightValidationError::ChecksumMismatch {
                expected,
                found: self.checksum,
            });
        }
        Ok(())
    }
}

/// Validation failure for a serialized evaluation weight set.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum WeightValidationError {
    /// Unsupported schema version.
    SchemaVersion { expected: u16, found: u16 },
    /// Zero is not a valid weight-set identifier.
    EmptyIdentifier,
    /// One scalar exceeded the supported magnitude.
    WeightOutOfRange { index: usize, value: i16 },
    /// Material values do not retain the required ordering.
    InvalidMaterialOrdering,
    /// Serialized checksum did not match the canonical value.
    ChecksumMismatch { expected: u64, found: u64 },
}

impl fmt::Display for WeightValidationError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match *self {
            Self::SchemaVersion { expected, found } => {
                write!(formatter, "expected weight schema {expected}, found {found}")
            }
            Self::EmptyIdentifier => formatter.write_str("weight-set identifier must be non-zero"),
            Self::WeightOutOfRange { index, value } => {
                write!(formatter, "weight value {index} is out of range: {value}")
            }
            Self::InvalidMaterialOrdering => formatter.write_str(
                "material values must be positive, ordered pawn < minor < rook < queen, and king = 0",
            ),
            Self::ChecksumMismatch { expected, found } => {
                write!(
                    formatter,
                    "weight checksum mismatch: expected {expected:016x}, found {found:016x}"
                )
            }
        }
    }
}

impl std::error::Error for WeightValidationError {}

fn write_phased(
    values: &mut [i16; WEIGHT_VALUE_COUNT],
    index: &mut usize,
    weight: PhasedWeight,
) {
    values[*index] = weight.middlegame;
    values[*index + 1] = weight.endgame;
    *index += 2;
}

fn read_phased(values: &[i16; WEIGHT_VALUE_COUNT], index: &mut usize) -> PhasedWeight {
    let weight = PhasedWeight::new(values[*index], values[*index + 1]);
    *index += 2;
    weight
}

fn hash_bytes(mut hash: u64, bytes: &[u8]) -> u64 {
    for byte in bytes {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    hash
}

fn validate_material(material: [PhasedWeight; 6]) -> Result<(), WeightValidationError> {
    for phase in [
        material.map(|weight| weight.middlegame),
        material.map(|weight| weight.endgame),
    ] {
        let pawn = phase[PieceKind::Pawn.index()];
        let knight = phase[PieceKind::Knight.index()];
        let bishop = phase[PieceKind::Bishop.index()];
        let rook = phase[PieceKind::Rook.index()];
        let queen = phase[PieceKind::Queen.index()];
        let king = phase[PieceKind::King.index()];
        if pawn <= 0
            || knight <= pawn
            || bishop <= pawn
            || rook <= knight.max(bishop)
            || queen <= rook
            || king != 0
        {
            return Err(WeightValidationError::InvalidMaterialOrdering);
        }
    }
    Ok(())
}

const fn baseline_piece_square_tables() -> [[PhasedWeight; 64]; 6] {
    let mut tables = [[PhasedWeight::ZERO; 64]; 6];
    let mut index = 0;
    while index < 64 {
        let row = (index / 8) as i16;
        let file = (index % 8) as i16;
        let advancement = 7 - row;
        let center = center_bonus(row) + center_bonus(file);
        tables[PieceKind::Pawn as usize][index] =
            PhasedWeight::new(advancement * 6 + center * 2, advancement * 10 + center);
        tables[PieceKind::Knight as usize][index] =
            PhasedWeight::new(center * 8 - 24, center * 6 - 18);
        tables[PieceKind::Bishop as usize][index] =
            PhasedWeight::new(center * 4 + advancement - 12, center * 4 - 10);
        let seventh = if advancement == 6 { 12 } else { 0 };
        tables[PieceKind::Rook as usize][index] =
            PhasedWeight::new(advancement * 2 + seventh, advancement * 3);
        tables[PieceKind::Queen as usize][index] =
            PhasedWeight::new(center * 2 - 8, center * 3 - 10);
        tables[PieceKind::King as usize][index] =
            PhasedWeight::new(-(advancement * 5) - center * 2, center * 8 - 24);
        index += 1;
    }
    tables
}

const fn center_bonus(coordinate: i16) -> i16 {
    let distance_to_three = absolute_difference(coordinate, 3);
    let distance_to_four = absolute_difference(coordinate, 4);
    let distance = if distance_to_three < distance_to_four {
        distance_to_three
    } else {
        distance_to_four
    };
    3 - distance
}

const fn absolute_difference(left: i16, right: i16) -> i16 {
    if left >= right {
        left - right
    } else {
        right - left
    }
}

#[cfg(test)]
mod tests {
    use super::{
        EvaluationWeightSet, EvaluationWeights, WeightValidationError, BASELINE_WEIGHT_SET_ID,
        EVALUATION_WEIGHT_SCHEMA_VERSION, WEIGHT_VALUE_COUNT,
    };

    #[test]
    fn baseline_weights_round_trip_through_the_canonical_vector() {
        let weights = EvaluationWeights::DEFAULT;
        let values = weights.values();
        assert_eq!(values.len(), WEIGHT_VALUE_COUNT);
        assert_eq!(EvaluationWeights::from_values(values), weights);
    }

    #[test]
    fn baseline_set_is_explicit_valid_and_stable() {
        let set = EvaluationWeightSet::baseline();
        assert_eq!(set.schema_version, EVALUATION_WEIGHT_SCHEMA_VERSION);
        assert_eq!(set.identifier, BASELINE_WEIGHT_SET_ID);
        assert_ne!(set.checksum, 0);
        assert_eq!(set.validate(), Ok(()));
        assert_eq!(set.computed_checksum(), set.checksum);
    }

    #[test]
    fn validation_rejects_schema_identifier_checksum_and_material_corruption() {
        let baseline = EvaluationWeightSet::baseline();
        let wrong_schema = EvaluationWeightSet::from_parts(
            baseline.schema_version + 1,
            baseline.identifier,
            baseline.weights,
            baseline.checksum,
        );
        assert!(matches!(
            wrong_schema.validate(),
            Err(WeightValidationError::SchemaVersion { .. })
        ));

        let empty_identifier = EvaluationWeightSet::new(0, baseline.weights);
        assert_eq!(
            empty_identifier.validate(),
            Err(WeightValidationError::EmptyIdentifier)
        );

        let mut wrong_checksum = baseline;
        wrong_checksum.checksum ^= 1;
        assert!(matches!(
            wrong_checksum.validate(),
            Err(WeightValidationError::ChecksumMismatch { .. })
        ));

        let mut invalid_weights = baseline.weights;
        invalid_weights.material[0].middlegame = 1_000;
        let invalid_material = EvaluationWeightSet::new(1, invalid_weights);
        assert_eq!(
            invalid_material.validate(),
            Err(WeightValidationError::InvalidMaterialOrdering)
        );
    }
}
