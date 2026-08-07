#![forbid(unsafe_code)]
//! Named evaluation-weight schemas and reproducible offline tuning artifacts.
//!
//! The crate deliberately keeps tuning metadata and artifact serialization
//! outside the runtime search crate. Loading or activating an artifact is an
//! explicit caller action.

mod diagnostics;
mod loss;
mod mask;
mod optimizer;

pub use loss::{
    logistic_result_probability, KCalibrationConfig, KCalibrationResult, LogisticK, LossDataset,
    LossPartition, LossPipelineError, LossPosition, OutcomeTarget, MAX_K_CALIBRATION_INTERVALS,
    TEXEL_EVALUATION_SCALE_CENTIPAWNS,
};

pub use diagnostics::{
    SpsaIterationDiagnostics, S4_OPTIMIZER_DIAGNOSTIC_IDENTIFIER,
    S4_OPTIMIZER_DIAGNOSTIC_SCHEMA_VERSION,
};
pub use mask::{EvaluationParameterGroup, TunableParameterMask, TUNABLE_PARAMETER_MASK_WORD_COUNT};
pub use optimizer::{
    SpsaCheckpoint, SpsaConfig, SpsaOptimizer, SpsaOptimizerError, SpsaRunSummary, SpsaSchedule,
    SpsaWeightBounds, MAX_SPSA_ITERATIONS, MAX_SPSA_WEIGHT_MAGNITUDE,
    SPSA_CHECKPOINT_SCHEMA_VERSION, SPSA_OPTIMIZER_IDENTIFIER,
};

use core::{fmt, fmt::Write as _, iter::FusedIterator};

use chess_core::{PieceKind, Square};
use chess_search::{
    EvaluationWeightSet, EvaluationWeights, PhasedWeight, WeightValidationError,
    EVALUATION_STRUCTURE, EVALUATION_STRUCTURE_SCHEMA_VERSION, EVALUATION_WEIGHT_SCHEMA_VERSION,
};

/// Current named tuning-artifact serialization schema.
pub const NAMED_WEIGHT_ARTIFACT_SCHEMA_VERSION: u16 = 1;
/// Current training-provenance metadata schema.
pub const TRAINING_METADATA_SCHEMA_VERSION: u16 = 1;
/// Number of tunable named scalar parameters.
pub const TUNABLE_PARAMETER_COUNT: usize = 810;

const FORMAT_MARKER: &str = "chess-named-eval-weights-v1";
const MATERIAL_PARAMETER_COUNT: usize = 5 * 2;
const PIECE_SQUARE_PARAMETER_COUNT: usize = 6 * 64 * 2;
const MOBILITY_PARAMETER_COUNT: usize = 4 * 2;
const FEATURE_PARAMETER_COUNT: usize = 12 * 2;
const HEADER_LINE_COUNT: usize = 17;
const SERIALIZED_LINE_COUNT: usize = HEADER_LINE_COUNT + TUNABLE_PARAMETER_COUNT + 1;
const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;

const MATERIAL_PIECES: [PieceKind; 5] = [
    PieceKind::Pawn,
    PieceKind::Knight,
    PieceKind::Bishop,
    PieceKind::Rook,
    PieceKind::Queen,
];
const MOBILITY_PIECES: [PieceKind; 4] = [
    PieceKind::Knight,
    PieceKind::Bishop,
    PieceKind::Rook,
    PieceKind::Queen,
];

/// One phase of a tapered evaluation weight.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[repr(u8)]
pub enum EvaluationPhase {
    /// Middlegame component.
    Middlegame = 0,
    /// Endgame component.
    Endgame = 1,
}

impl EvaluationPhase {
    const fn from_index(index: usize) -> Self {
        match index {
            0 => Self::Middlegame,
            1 => Self::Endgame,
            _ => unreachable!(),
        }
    }

    const fn suffix(self) -> &'static str {
        match self {
            Self::Middlegame => "mg",
            Self::Endgame => "eg",
        }
    }

    const fn value(self, weight: PhasedWeight) -> i16 {
        match self {
            Self::Middlegame => weight.middlegame,
            Self::Endgame => weight.endgame,
        }
    }

    fn set(self, weight: &mut PhasedWeight, value: i16) {
        match self {
            Self::Middlegame => weight.middlegame = value,
            Self::Endgame => weight.endgame = value,
        }
    }
}

/// Scalar evaluator terms that are not arrays indexed by piece or square.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[repr(u8)]
pub enum EvaluationFeature {
    /// Isolated-pawn penalty.
    IsolatedPawn = 0,
    /// Doubled-pawn penalty.
    DoubledPawn = 1,
    /// Passed-pawn bonus.
    PassedPawn = 2,
    /// Connected-pawn bonus.
    ConnectedPawn = 3,
    /// Bishop-pair bonus.
    BishopPair = 4,
    /// Open-file rook bonus.
    RookOpenFile = 5,
    /// Semi-open-file rook bonus.
    RookSemiOpenFile = 6,
    /// Seventh-rank rook bonus.
    RookSeventhRank = 7,
    /// King-shield bonus.
    KingShield = 8,
    /// King-zone attack penalty.
    KingZoneAttack = 9,
    /// Space bonus.
    Space = 10,
    /// Endgame king-activity bonus.
    KingActivity = 11,
}

impl EvaluationFeature {
    /// Stable feature order used by the named schema.
    pub const ALL: [Self; 12] = [
        Self::IsolatedPawn,
        Self::DoubledPawn,
        Self::PassedPawn,
        Self::ConnectedPawn,
        Self::BishopPair,
        Self::RookOpenFile,
        Self::RookSemiOpenFile,
        Self::RookSeventhRank,
        Self::KingShield,
        Self::KingZoneAttack,
        Self::Space,
        Self::KingActivity,
    ];

    /// Stable machine-readable feature name.
    #[must_use]
    pub const fn name(self) -> &'static str {
        match self {
            Self::IsolatedPawn => "isolated_pawn",
            Self::DoubledPawn => "doubled_pawn",
            Self::PassedPawn => "passed_pawn",
            Self::ConnectedPawn => "connected_pawn",
            Self::BishopPair => "bishop_pair",
            Self::RookOpenFile => "rook_open_file",
            Self::RookSemiOpenFile => "rook_semi_open_file",
            Self::RookSeventhRank => "rook_seventh_rank",
            Self::KingShield => "king_shield",
            Self::KingZoneAttack => "king_zone_attack",
            Self::Space => "space",
            Self::KingActivity => "king_activity",
        }
    }
}

/// Semantic location of one tunable scalar parameter.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum TunableParameterDescriptor {
    /// Material value for a non-king piece.
    Material {
        /// Piece kind.
        piece: PieceKind,
        /// Tapered phase.
        phase: EvaluationPhase,
    },
    /// Piece-square value.
    PieceSquare {
        /// Piece kind.
        piece: PieceKind,
        /// White-oriented square.
        square: Square,
        /// Tapered phase.
        phase: EvaluationPhase,
    },
    /// Mobility value for a sliding piece or knight.
    Mobility {
        /// Piece kind.
        piece: PieceKind,
        /// Tapered phase.
        phase: EvaluationPhase,
    },
    /// Scalar evaluator feature.
    Feature {
        /// Feature identity.
        feature: EvaluationFeature,
        /// Tapered phase.
        phase: EvaluationPhase,
    },
}

/// Stable index into the complete named tuning schema.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct TunableParameter(u16);

impl TunableParameter {
    /// Returns a parameter for a valid stable schema index.
    #[must_use]
    pub const fn from_index(index: usize) -> Option<Self> {
        if index < TUNABLE_PARAMETER_COUNT {
            Some(Self(index as u16))
        } else {
            None
        }
    }

    /// Returns this parameter's stable zero-based schema index.
    #[must_use]
    pub const fn index(self) -> usize {
        self.0 as usize
    }

    /// Iterates every tunable parameter in canonical serialization order.
    #[must_use]
    pub const fn all() -> TunableParameters {
        TunableParameters { next: 0 }
    }

    /// Returns the semantic descriptor for this parameter.
    #[must_use]
    pub fn descriptor(self) -> TunableParameterDescriptor {
        let mut index = self.index();
        if index < MATERIAL_PARAMETER_COUNT {
            return TunableParameterDescriptor::Material {
                piece: MATERIAL_PIECES[index / 2],
                phase: EvaluationPhase::from_index(index % 2),
            };
        }
        index -= MATERIAL_PARAMETER_COUNT;
        if index < PIECE_SQUARE_PARAMETER_COUNT {
            let piece = PieceKind::ALL[index / (64 * 2)];
            let within_piece = index % (64 * 2);
            let square_index = u8::try_from(within_piece / 2).expect("piece-square index fits u8");
            let square = Square::new(square_index).expect("piece-square index is on board");
            return TunableParameterDescriptor::PieceSquare {
                piece,
                square,
                phase: EvaluationPhase::from_index(within_piece % 2),
            };
        }
        index -= PIECE_SQUARE_PARAMETER_COUNT;
        if index < MOBILITY_PARAMETER_COUNT {
            return TunableParameterDescriptor::Mobility {
                piece: MOBILITY_PIECES[index / 2],
                phase: EvaluationPhase::from_index(index % 2),
            };
        }
        index -= MOBILITY_PARAMETER_COUNT;
        debug_assert!(index < FEATURE_PARAMETER_COUNT);
        TunableParameterDescriptor::Feature {
            feature: EvaluationFeature::ALL[index / 2],
            phase: EvaluationPhase::from_index(index % 2),
        }
    }

    /// Returns the stable machine-readable parameter name.
    #[must_use]
    pub fn name(self) -> String {
        match self.descriptor() {
            TunableParameterDescriptor::Material { piece, phase } => {
                format!("material.{piece}.{}", phase.suffix())
            }
            TunableParameterDescriptor::PieceSquare {
                piece,
                square,
                phase,
            } => format!("piece_square.{piece}.{square}.{}", phase.suffix()),
            TunableParameterDescriptor::Mobility { piece, phase } => {
                format!("mobility.{piece}.{}", phase.suffix())
            }
            TunableParameterDescriptor::Feature { feature, phase } => {
                format!("feature.{}.{}", feature.name(), phase.suffix())
            }
        }
    }

    /// Reads this scalar from a complete runtime weight set.
    #[must_use]
    pub fn value(self, weights: &EvaluationWeights) -> i16 {
        let (weight, phase) = match self.descriptor() {
            TunableParameterDescriptor::Material { piece, phase } => {
                (weights.material[piece.index()], phase)
            }
            TunableParameterDescriptor::PieceSquare {
                piece,
                square,
                phase,
            } => (
                weights.piece_square[piece.index()][usize::from(square.index())],
                phase,
            ),
            TunableParameterDescriptor::Mobility { piece, phase } => {
                (weights.mobility[piece.index()], phase)
            }
            TunableParameterDescriptor::Feature { feature, phase } => {
                (feature_weight(weights, feature), phase)
            }
        };
        phase.value(weight)
    }

    /// Writes this scalar without exposing non-tunable structural slots.
    pub fn set_value(self, weights: &mut EvaluationWeights, value: i16) {
        let (weight, phase) = match self.descriptor() {
            TunableParameterDescriptor::Material { piece, phase } => {
                (&mut weights.material[piece.index()], phase)
            }
            TunableParameterDescriptor::PieceSquare {
                piece,
                square,
                phase,
            } => (
                &mut weights.piece_square[piece.index()][usize::from(square.index())],
                phase,
            ),
            TunableParameterDescriptor::Mobility { piece, phase } => {
                (&mut weights.mobility[piece.index()], phase)
            }
            TunableParameterDescriptor::Feature { feature, phase } => {
                (feature_weight_mut(weights, feature), phase)
            }
        };
        phase.set(weight, value);
    }
}

impl fmt::Display for TunableParameter {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(&self.name())
    }
}

/// Canonical iterator over all named tunable parameters.
#[derive(Clone, Debug)]
pub struct TunableParameters {
    next: usize,
}

impl Iterator for TunableParameters {
    type Item = TunableParameter;

    fn next(&mut self) -> Option<Self::Item> {
        let parameter = TunableParameter::from_index(self.next)?;
        self.next += 1;
        Some(parameter)
    }

    fn size_hint(&self) -> (usize, Option<usize>) {
        let remaining = TUNABLE_PARAMETER_COUNT.saturating_sub(self.next);
        (remaining, Some(remaining))
    }
}

impl ExactSizeIterator for TunableParameters {
    fn len(&self) -> usize {
        TUNABLE_PARAMETER_COUNT.saturating_sub(self.next)
    }
}

impl FusedIterator for TunableParameters {}

/// Returns the complete canonical named tuning vector.
#[must_use]
pub fn tunable_values(weights: &EvaluationWeights) -> [i16; TUNABLE_PARAMETER_COUNT] {
    let mut values = [0_i16; TUNABLE_PARAMETER_COUNT];
    for parameter in TunableParameter::all() {
        values[parameter.index()] = parameter.value(weights);
    }
    values
}

/// Reconstructs runtime weights while restoring all structural fields explicitly.
#[must_use]
pub fn weights_from_tunable_values(values: [i16; TUNABLE_PARAMETER_COUNT]) -> EvaluationWeights {
    let mut weights = EvaluationWeights::DEFAULT;
    for parameter in TunableParameter::all() {
        parameter.set_value(&mut weights, values[parameter.index()]);
    }
    weights
}

/// Provenance for the optimizer invocation that produced a candidate.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TrainingRunProvenance {
    /// Stable identifier for the trainer implementation/configuration.
    pub trainer_identifier: u64,
    /// Exact 20-byte source commit used by the trainer.
    pub source_commit: [u8; 20],
    /// Explicit deterministic training seed.
    pub random_seed: u64,
    /// Number of completed optimizer iterations.
    pub completed_iterations: u64,
    /// Artifact creation time as Unix seconds, supplied explicitly by the caller.
    pub generated_at_unix_seconds: u64,
}

impl TrainingRunProvenance {
    /// Constructs explicit optimizer provenance.
    #[must_use]
    pub const fn new(
        trainer_identifier: u64,
        source_commit: [u8; 20],
        random_seed: u64,
        completed_iterations: u64,
        generated_at_unix_seconds: u64,
    ) -> Self {
        Self {
            trainer_identifier,
            source_commit,
            random_seed,
            completed_iterations,
            generated_at_unix_seconds,
        }
    }
}

/// Provenance and split sizes for the source dataset.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TrainingDatasetProvenance {
    /// Source dataset schema version.
    pub schema_version: u16,
    /// Canonical source dataset checksum.
    pub checksum: u64,
    /// Number of training positions.
    pub training_positions: u64,
    /// Number of separately held-out validation positions.
    pub validation_positions: u64,
}

impl TrainingDatasetProvenance {
    /// Constructs explicit source-dataset provenance.
    #[must_use]
    pub const fn new(
        schema_version: u16,
        checksum: u64,
        training_positions: u64,
        validation_positions: u64,
    ) -> Self {
        Self {
            schema_version,
            checksum,
            training_positions,
            validation_positions,
        }
    }
}

/// Complete reproducibility metadata for a tuned weight artifact.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TrainingMetadata {
    /// Metadata schema version.
    pub schema_version: u16,
    /// Stable identifier for the trainer implementation/configuration.
    pub trainer_identifier: u64,
    /// Exact 20-byte source commit used by the trainer.
    pub source_commit: [u8; 20],
    /// Source dataset schema version.
    pub dataset_schema_version: u16,
    /// Canonical source dataset checksum.
    pub dataset_checksum: u64,
    /// Number of training positions.
    pub training_positions: u64,
    /// Number of separately held-out validation positions.
    pub validation_positions: u64,
    /// Explicit deterministic training seed.
    pub random_seed: u64,
    /// Number of completed optimizer iterations.
    pub completed_iterations: u64,
    /// Artifact creation time as Unix seconds, supplied explicitly by the caller.
    pub generated_at_unix_seconds: u64,
}

impl TrainingMetadata {
    /// Constructs current-schema metadata from grouped explicit provenance.
    #[must_use]
    pub const fn new(run: TrainingRunProvenance, dataset: TrainingDatasetProvenance) -> Self {
        Self {
            schema_version: TRAINING_METADATA_SCHEMA_VERSION,
            trainer_identifier: run.trainer_identifier,
            source_commit: run.source_commit,
            dataset_schema_version: dataset.schema_version,
            dataset_checksum: dataset.checksum,
            training_positions: dataset.training_positions,
            validation_positions: dataset.validation_positions,
            random_seed: run.random_seed,
            completed_iterations: run.completed_iterations,
            generated_at_unix_seconds: run.generated_at_unix_seconds,
        }
    }

    /// Validates that every required provenance field is present.
    pub fn validate(self) -> Result<(), TrainingMetadataError> {
        if self.schema_version != TRAINING_METADATA_SCHEMA_VERSION {
            return Err(TrainingMetadataError::SchemaVersion {
                expected: TRAINING_METADATA_SCHEMA_VERSION,
                found: self.schema_version,
            });
        }
        if self.trainer_identifier == 0 {
            return Err(TrainingMetadataError::EmptyTrainerIdentifier);
        }
        if self.source_commit.iter().all(|byte| *byte == 0) {
            return Err(TrainingMetadataError::EmptySourceCommit);
        }
        if self.dataset_schema_version == 0 {
            return Err(TrainingMetadataError::EmptyDatasetSchemaVersion);
        }
        if self.dataset_checksum == 0 {
            return Err(TrainingMetadataError::EmptyDatasetChecksum);
        }
        if self.training_positions == 0 {
            return Err(TrainingMetadataError::EmptyTrainingSet);
        }
        if self.validation_positions == 0 {
            return Err(TrainingMetadataError::EmptyValidationSet);
        }
        if self.completed_iterations == 0 {
            return Err(TrainingMetadataError::EmptyIterationCount);
        }
        if self.generated_at_unix_seconds == 0 {
            return Err(TrainingMetadataError::EmptyGenerationTimestamp);
        }
        Ok(())
    }
}

/// Invalid or incomplete training provenance.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum TrainingMetadataError {
    /// Unsupported metadata schema.
    SchemaVersion { expected: u16, found: u16 },
    /// Trainer identity is missing.
    EmptyTrainerIdentifier,
    /// Source commit is all zeroes.
    EmptySourceCommit,
    /// Dataset schema is missing.
    EmptyDatasetSchemaVersion,
    /// Dataset checksum is missing.
    EmptyDatasetChecksum,
    /// Training split is empty.
    EmptyTrainingSet,
    /// Validation split is empty.
    EmptyValidationSet,
    /// Optimizer iteration count is empty.
    EmptyIterationCount,
    /// Generation timestamp is empty.
    EmptyGenerationTimestamp,
}

impl fmt::Display for TrainingMetadataError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match *self {
            Self::SchemaVersion { expected, found } => write!(
                formatter,
                "expected training metadata schema {expected}, found {found}"
            ),
            Self::EmptyTrainerIdentifier => {
                formatter.write_str("trainer identifier must be non-zero")
            }
            Self::EmptySourceCommit => formatter.write_str("source commit must be recorded"),
            Self::EmptyDatasetSchemaVersion => {
                formatter.write_str("dataset schema version must be non-zero")
            }
            Self::EmptyDatasetChecksum => formatter.write_str("dataset checksum must be non-zero"),
            Self::EmptyTrainingSet => formatter.write_str("training split must not be empty"),
            Self::EmptyValidationSet => formatter.write_str("validation split must not be empty"),
            Self::EmptyIterationCount => {
                formatter.write_str("completed iteration count must be non-zero")
            }
            Self::EmptyGenerationTimestamp => {
                formatter.write_str("generation timestamp must be non-zero")
            }
        }
    }
}

impl std::error::Error for TrainingMetadataError {}

/// Versioned named weight artifact with complete training provenance.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct NamedWeightArtifact {
    /// Named artifact schema version.
    pub artifact_schema_version: u16,
    /// Runtime evaluation-weight schema version.
    pub evaluation_schema_version: u16,
    /// Non-tunable evaluator-structure schema version.
    pub structure_schema_version: u16,
    /// Checksum of the non-tunable evaluator structure.
    pub structure_checksum: u64,
    /// Stable caller-selected weight-set identifier.
    pub identifier: u64,
    /// Complete training provenance.
    pub metadata: TrainingMetadata,
    /// Runtime evaluator weights.
    pub weights: EvaluationWeights,
    /// Canonical checksum over schemas, metadata, names, and values.
    pub checksum: u64,
}

impl NamedWeightArtifact {
    /// Constructs and validates a current-schema named artifact.
    pub fn new(
        identifier: u64,
        metadata: TrainingMetadata,
        weights: EvaluationWeights,
    ) -> Result<Self, NamedWeightArtifactError> {
        let mut artifact = Self {
            artifact_schema_version: NAMED_WEIGHT_ARTIFACT_SCHEMA_VERSION,
            evaluation_schema_version: EVALUATION_WEIGHT_SCHEMA_VERSION,
            structure_schema_version: EVALUATION_STRUCTURE_SCHEMA_VERSION,
            structure_checksum: EVALUATION_STRUCTURE.computed_checksum(),
            identifier,
            metadata,
            weights,
            checksum: 0,
        };
        artifact.checksum = artifact.computed_checksum();
        artifact.validate()?;
        Ok(artifact)
    }

    /// Computes the canonical checksum for all serialized semantic fields.
    #[must_use]
    pub fn computed_checksum(&self) -> u64 {
        let mut hash = FNV_OFFSET;
        hash = hash_bytes(hash, &self.artifact_schema_version.to_le_bytes());
        hash = hash_bytes(hash, &self.evaluation_schema_version.to_le_bytes());
        hash = hash_bytes(hash, &self.structure_schema_version.to_le_bytes());
        hash = hash_bytes(hash, &self.structure_checksum.to_le_bytes());
        hash = hash_bytes(hash, &self.identifier.to_le_bytes());
        hash = hash_bytes(hash, &self.metadata.schema_version.to_le_bytes());
        hash = hash_bytes(hash, &self.metadata.trainer_identifier.to_le_bytes());
        hash = hash_bytes(hash, &self.metadata.source_commit);
        hash = hash_bytes(hash, &self.metadata.dataset_schema_version.to_le_bytes());
        hash = hash_bytes(hash, &self.metadata.dataset_checksum.to_le_bytes());
        hash = hash_bytes(hash, &self.metadata.training_positions.to_le_bytes());
        hash = hash_bytes(hash, &self.metadata.validation_positions.to_le_bytes());
        hash = hash_bytes(hash, &self.metadata.random_seed.to_le_bytes());
        hash = hash_bytes(hash, &self.metadata.completed_iterations.to_le_bytes());
        hash = hash_bytes(hash, &self.metadata.generated_at_unix_seconds.to_le_bytes());
        hash = hash_bytes(hash, &(TUNABLE_PARAMETER_COUNT as u64).to_le_bytes());
        for parameter in TunableParameter::all() {
            let name = parameter.name();
            let name_length = u16::try_from(name.len()).expect("parameter name length fits u16");
            hash = hash_bytes(hash, &name_length.to_le_bytes());
            hash = hash_bytes(hash, name.as_bytes());
            hash = hash_bytes(hash, &parameter.value(&self.weights).to_le_bytes());
        }
        hash
    }

    /// Validates schemas, structure, provenance, runtime weights, and checksum.
    pub fn validate(&self) -> Result<(), NamedWeightArtifactError> {
        if self.artifact_schema_version != NAMED_WEIGHT_ARTIFACT_SCHEMA_VERSION {
            return Err(NamedWeightArtifactError::ArtifactSchemaVersion {
                expected: NAMED_WEIGHT_ARTIFACT_SCHEMA_VERSION,
                found: self.artifact_schema_version,
            });
        }
        if self.evaluation_schema_version != EVALUATION_WEIGHT_SCHEMA_VERSION {
            return Err(NamedWeightArtifactError::EvaluationSchemaVersion {
                expected: EVALUATION_WEIGHT_SCHEMA_VERSION,
                found: self.evaluation_schema_version,
            });
        }
        if self.structure_schema_version != EVALUATION_STRUCTURE_SCHEMA_VERSION {
            return Err(NamedWeightArtifactError::StructureSchemaVersion {
                expected: EVALUATION_STRUCTURE_SCHEMA_VERSION,
                found: self.structure_schema_version,
            });
        }
        let expected_structure_checksum = EVALUATION_STRUCTURE.computed_checksum();
        if self.structure_checksum != expected_structure_checksum {
            return Err(NamedWeightArtifactError::StructureChecksumMismatch {
                expected: expected_structure_checksum,
                found: self.structure_checksum,
            });
        }
        self.metadata
            .validate()
            .map_err(NamedWeightArtifactError::TrainingMetadata)?;
        EvaluationWeightSet::new(self.identifier, self.weights)
            .validate()
            .map_err(NamedWeightArtifactError::WeightValidation)?;
        let expected = self.computed_checksum();
        if self.checksum != expected {
            return Err(NamedWeightArtifactError::ChecksumMismatch {
                expected,
                found: self.checksum,
            });
        }
        Ok(())
    }

    /// Serializes the artifact into the canonical line-oriented named format.
    pub fn serialize(&self) -> Result<String, NamedWeightArtifactError> {
        self.validate()?;
        let mut output = String::new();
        writeln!(output, "{FORMAT_MARKER}").expect("writing to String cannot fail");
        writeln!(output, "artifact_schema={}", self.artifact_schema_version)
            .expect("writing to String cannot fail");
        writeln!(
            output,
            "evaluation_schema={}",
            self.evaluation_schema_version
        )
        .expect("writing to String cannot fail");
        writeln!(output, "structure_schema={}", self.structure_schema_version)
            .expect("writing to String cannot fail");
        writeln!(
            output,
            "structure_checksum={:016x}",
            self.structure_checksum
        )
        .expect("writing to String cannot fail");
        writeln!(output, "identifier={:016x}", self.identifier)
            .expect("writing to String cannot fail");
        writeln!(output, "metadata_schema={}", self.metadata.schema_version)
            .expect("writing to String cannot fail");
        writeln!(
            output,
            "trainer_identifier={:016x}",
            self.metadata.trainer_identifier
        )
        .expect("writing to String cannot fail");
        writeln!(
            output,
            "source_commit={}",
            encode_commit(self.metadata.source_commit)
        )
        .expect("writing to String cannot fail");
        writeln!(
            output,
            "dataset_schema={}",
            self.metadata.dataset_schema_version
        )
        .expect("writing to String cannot fail");
        writeln!(
            output,
            "dataset_checksum={:016x}",
            self.metadata.dataset_checksum
        )
        .expect("writing to String cannot fail");
        writeln!(
            output,
            "training_positions={}",
            self.metadata.training_positions
        )
        .expect("writing to String cannot fail");
        writeln!(
            output,
            "validation_positions={}",
            self.metadata.validation_positions
        )
        .expect("writing to String cannot fail");
        writeln!(output, "random_seed={}", self.metadata.random_seed)
            .expect("writing to String cannot fail");
        writeln!(
            output,
            "completed_iterations={}",
            self.metadata.completed_iterations
        )
        .expect("writing to String cannot fail");
        writeln!(
            output,
            "generated_at_unix_seconds={}",
            self.metadata.generated_at_unix_seconds
        )
        .expect("writing to String cannot fail");
        writeln!(output, "parameter_count={TUNABLE_PARAMETER_COUNT}")
            .expect("writing to String cannot fail");
        for parameter in TunableParameter::all() {
            writeln!(
                output,
                "parameter.{}={}",
                parameter.name(),
                parameter.value(&self.weights)
            )
            .expect("writing to String cannot fail");
        }
        writeln!(output, "checksum={:016x}", self.checksum).expect("writing to String cannot fail");
        Ok(output)
    }

    /// Parses and validates the canonical named artifact format.
    pub fn deserialize(input: &str) -> Result<Self, NamedWeightArtifactError> {
        let lines: Vec<_> = input.lines().collect();
        if lines.len() != SERIALIZED_LINE_COUNT {
            return Err(NamedWeightArtifactError::Format(format!(
                "expected {SERIALIZED_LINE_COUNT} lines, found {}",
                lines.len()
            )));
        }
        if lines[0] != FORMAT_MARKER {
            return Err(NamedWeightArtifactError::Format(format!(
                "expected format marker {FORMAT_MARKER:?}, found {:?}",
                lines[0]
            )));
        }
        let artifact_schema_version = parse_u16_field(lines[1], "artifact_schema")?;
        let evaluation_schema_version = parse_u16_field(lines[2], "evaluation_schema")?;
        let structure_schema_version = parse_u16_field(lines[3], "structure_schema")?;
        let structure_checksum = parse_hex_u64_field(lines[4], "structure_checksum")?;
        let identifier = parse_hex_u64_field(lines[5], "identifier")?;
        let metadata = TrainingMetadata {
            schema_version: parse_u16_field(lines[6], "metadata_schema")?,
            trainer_identifier: parse_hex_u64_field(lines[7], "trainer_identifier")?,
            source_commit: parse_commit_field(lines[8], "source_commit")?,
            dataset_schema_version: parse_u16_field(lines[9], "dataset_schema")?,
            dataset_checksum: parse_hex_u64_field(lines[10], "dataset_checksum")?,
            training_positions: parse_u64_field(lines[11], "training_positions")?,
            validation_positions: parse_u64_field(lines[12], "validation_positions")?,
            random_seed: parse_u64_field(lines[13], "random_seed")?,
            completed_iterations: parse_u64_field(lines[14], "completed_iterations")?,
            generated_at_unix_seconds: parse_u64_field(lines[15], "generated_at_unix_seconds")?,
        };
        let parameter_count = parse_u64_field(lines[16], "parameter_count")?;
        if parameter_count != TUNABLE_PARAMETER_COUNT as u64 {
            return Err(NamedWeightArtifactError::ParameterCount {
                expected: TUNABLE_PARAMETER_COUNT,
                found: parameter_count,
            });
        }
        let mut weights = EvaluationWeights::DEFAULT;
        for parameter in TunableParameter::all() {
            let line = lines[HEADER_LINE_COUNT + parameter.index()];
            let name = parameter.name();
            let prefix = format!("parameter.{name}=");
            let value_text = line.strip_prefix(&prefix).ok_or_else(|| {
                NamedWeightArtifactError::Format(format!(
                    "expected parameter line beginning {prefix:?}, found {line:?}"
                ))
            })?;
            let value = value_text.parse::<i16>().map_err(|error| {
                NamedWeightArtifactError::Format(format!(
                    "invalid value for parameter {name}: {error}"
                ))
            })?;
            parameter.set_value(&mut weights, value);
        }
        let checksum = parse_hex_u64_field(lines[SERIALIZED_LINE_COUNT - 1], "checksum")?;
        let artifact = Self {
            artifact_schema_version,
            evaluation_schema_version,
            structure_schema_version,
            structure_checksum,
            identifier,
            metadata,
            weights,
            checksum,
        };
        artifact.validate()?;
        Ok(artifact)
    }
}

/// Validation or parsing failure for a named tuning artifact.
#[derive(Debug, Eq, PartialEq)]
pub enum NamedWeightArtifactError {
    /// Unsupported named artifact schema.
    ArtifactSchemaVersion { expected: u16, found: u16 },
    /// Unsupported runtime evaluation schema.
    EvaluationSchemaVersion { expected: u16, found: u16 },
    /// Unsupported evaluator-structure schema.
    StructureSchemaVersion { expected: u16, found: u16 },
    /// Evaluator structural constants do not match this runtime.
    StructureChecksumMismatch { expected: u64, found: u64 },
    /// Training provenance is incomplete or incompatible.
    TrainingMetadata(TrainingMetadataError),
    /// Runtime evaluation weights are invalid.
    WeightValidation(WeightValidationError),
    /// Serialized parameter count is incompatible.
    ParameterCount { expected: usize, found: u64 },
    /// Artifact checksum did not match the canonical semantic content.
    ChecksumMismatch { expected: u64, found: u64 },
    /// Canonical text format was malformed.
    Format(String),
}

impl fmt::Display for NamedWeightArtifactError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::ArtifactSchemaVersion { expected, found } => write!(
                formatter,
                "expected named artifact schema {expected}, found {found}"
            ),
            Self::EvaluationSchemaVersion { expected, found } => write!(
                formatter,
                "expected evaluation schema {expected}, found {found}"
            ),
            Self::StructureSchemaVersion { expected, found } => write!(
                formatter,
                "expected evaluator structure schema {expected}, found {found}"
            ),
            Self::StructureChecksumMismatch { expected, found } => write!(
                formatter,
                "evaluator structure checksum mismatch: expected {expected:016x}, found {found:016x}"
            ),
            Self::TrainingMetadata(error) => write!(formatter, "invalid training metadata: {error}"),
            Self::WeightValidation(error) => write!(formatter, "invalid evaluation weights: {error}"),
            Self::ParameterCount { expected, found } => {
                write!(formatter, "expected {expected} named parameters, found {found}")
            }
            Self::ChecksumMismatch { expected, found } => write!(
                formatter,
                "named artifact checksum mismatch: expected {expected:016x}, found {found:016x}"
            ),
            Self::Format(message) => formatter.write_str(message),
        }
    }
}

impl std::error::Error for NamedWeightArtifactError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            Self::TrainingMetadata(error) => Some(error),
            Self::WeightValidation(error) => Some(error),
            _ => None,
        }
    }
}

fn feature_weight(weights: &EvaluationWeights, feature: EvaluationFeature) -> PhasedWeight {
    match feature {
        EvaluationFeature::IsolatedPawn => weights.isolated_pawn,
        EvaluationFeature::DoubledPawn => weights.doubled_pawn,
        EvaluationFeature::PassedPawn => weights.passed_pawn,
        EvaluationFeature::ConnectedPawn => weights.connected_pawn,
        EvaluationFeature::BishopPair => weights.bishop_pair,
        EvaluationFeature::RookOpenFile => weights.rook_open_file,
        EvaluationFeature::RookSemiOpenFile => weights.rook_semi_open_file,
        EvaluationFeature::RookSeventhRank => weights.rook_seventh_rank,
        EvaluationFeature::KingShield => weights.king_shield,
        EvaluationFeature::KingZoneAttack => weights.king_zone_attack,
        EvaluationFeature::Space => weights.space,
        EvaluationFeature::KingActivity => weights.king_activity,
    }
}

fn feature_weight_mut(
    weights: &mut EvaluationWeights,
    feature: EvaluationFeature,
) -> &mut PhasedWeight {
    match feature {
        EvaluationFeature::IsolatedPawn => &mut weights.isolated_pawn,
        EvaluationFeature::DoubledPawn => &mut weights.doubled_pawn,
        EvaluationFeature::PassedPawn => &mut weights.passed_pawn,
        EvaluationFeature::ConnectedPawn => &mut weights.connected_pawn,
        EvaluationFeature::BishopPair => &mut weights.bishop_pair,
        EvaluationFeature::RookOpenFile => &mut weights.rook_open_file,
        EvaluationFeature::RookSemiOpenFile => &mut weights.rook_semi_open_file,
        EvaluationFeature::RookSeventhRank => &mut weights.rook_seventh_rank,
        EvaluationFeature::KingShield => &mut weights.king_shield,
        EvaluationFeature::KingZoneAttack => &mut weights.king_zone_attack,
        EvaluationFeature::Space => &mut weights.space,
        EvaluationFeature::KingActivity => &mut weights.king_activity,
    }
}

fn hash_bytes(mut hash: u64, bytes: &[u8]) -> u64 {
    for byte in bytes {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    hash
}

fn encode_commit(commit: [u8; 20]) -> String {
    let mut output = String::with_capacity(40);
    for byte in commit {
        write!(output, "{byte:02x}").expect("writing to String cannot fail");
    }
    output
}

fn field_value<'a>(line: &'a str, name: &str) -> Result<&'a str, NamedWeightArtifactError> {
    line.strip_prefix(name)
        .and_then(|suffix| suffix.strip_prefix('='))
        .ok_or_else(|| {
            NamedWeightArtifactError::Format(format!("expected {name}= field, found {line:?}"))
        })
}

fn parse_u16_field(line: &str, name: &str) -> Result<u16, NamedWeightArtifactError> {
    let value = field_value(line, name)?;
    value.parse::<u16>().map_err(|error| {
        NamedWeightArtifactError::Format(format!("invalid {name} value {value:?}: {error}"))
    })
}

fn parse_u64_field(line: &str, name: &str) -> Result<u64, NamedWeightArtifactError> {
    let value = field_value(line, name)?;
    value.parse::<u64>().map_err(|error| {
        NamedWeightArtifactError::Format(format!("invalid {name} value {value:?}: {error}"))
    })
}

fn parse_hex_u64_field(line: &str, name: &str) -> Result<u64, NamedWeightArtifactError> {
    let value = field_value(line, name)?;
    if value.len() != 16 || !value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(NamedWeightArtifactError::Format(format!(
            "{name} must contain exactly sixteen hexadecimal digits"
        )));
    }
    u64::from_str_radix(value, 16).map_err(|error| {
        NamedWeightArtifactError::Format(format!("invalid {name} value {value:?}: {error}"))
    })
}

fn parse_commit_field(line: &str, name: &str) -> Result<[u8; 20], NamedWeightArtifactError> {
    let value = field_value(line, name)?;
    if value.len() != 40 || !value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(NamedWeightArtifactError::Format(format!(
            "{name} must contain exactly forty hexadecimal digits"
        )));
    }
    let mut commit = [0_u8; 20];
    for (index, byte) in commit.iter_mut().enumerate() {
        let offset = index * 2;
        *byte = u8::from_str_radix(&value[offset..offset + 2], 16).map_err(|error| {
            NamedWeightArtifactError::Format(format!("invalid {name} byte {index}: {error}"))
        })?;
    }
    Ok(commit)
}

#[cfg(test)]
mod tests {
    use std::collections::BTreeSet;

    use chess_core::PieceKind;
    use chess_search::{EvaluationWeights, PhasedWeight, EVALUATION_STRUCTURE};

    use super::{
        tunable_values, weights_from_tunable_values, NamedWeightArtifact, NamedWeightArtifactError,
        TrainingDatasetProvenance, TrainingMetadata, TrainingMetadataError, TrainingRunProvenance,
        TunableParameter, TUNABLE_PARAMETER_COUNT,
    };

    fn metadata() -> TrainingMetadata {
        TrainingMetadata::new(
            TrainingRunProvenance::new(
                0x5452_4149_4e45_5231,
                [0x11; 20],
                0x00C0_FFEE,
                64,
                1_785_820_000,
            ),
            TrainingDatasetProvenance::new(1, 0x1122_3344_5566_7788, 8_000, 2_000),
        )
    }

    #[test]
    fn named_schema_is_complete_unique_and_stable() {
        let parameters: Vec<_> = TunableParameter::all().collect();
        assert_eq!(parameters.len(), TUNABLE_PARAMETER_COUNT);
        assert_eq!(parameters[0].name(), "material.pawn.mg");
        assert_eq!(parameters[9].name(), "material.queen.eg");
        assert_eq!(parameters[10].name(), "piece_square.pawn.a8.mg");
        assert_eq!(parameters[777].name(), "piece_square.king.h1.eg");
        assert_eq!(parameters[778].name(), "mobility.knight.mg");
        assert_eq!(parameters[809].name(), "feature.king_activity.eg");
        let names: BTreeSet<_> = parameters
            .iter()
            .map(|parameter| parameter.name())
            .collect();
        assert_eq!(names.len(), TUNABLE_PARAMETER_COUNT);
        assert_eq!(TunableParameter::from_index(TUNABLE_PARAMETER_COUNT), None);
    }

    #[test]
    fn named_vector_round_trip_preserves_tunable_values_and_restores_structure() {
        let baseline = EvaluationWeights::DEFAULT;
        let values = tunable_values(&baseline);
        assert_eq!(weights_from_tunable_values(values), baseline);

        let mut structurally_invalid = baseline;
        structurally_invalid.material[PieceKind::King.index()] = PhasedWeight::new(1, 1);
        structurally_invalid.mobility[PieceKind::Pawn.index()] = PhasedWeight::new(2, 2);
        structurally_invalid.mobility[PieceKind::King.index()] = PhasedWeight::new(3, 3);
        let restored = weights_from_tunable_values(tunable_values(&structurally_invalid));
        assert_eq!(
            restored.material[PieceKind::King.index()],
            EVALUATION_STRUCTURE.fixed_king_material
        );
        assert_eq!(
            restored.mobility[PieceKind::Pawn.index()],
            EVALUATION_STRUCTURE.fixed_pawn_mobility
        );
        assert_eq!(
            restored.mobility[PieceKind::King.index()],
            EVALUATION_STRUCTURE.fixed_king_mobility
        );
    }

    #[test]
    fn artifact_round_trips_with_named_parameters_and_complete_metadata() {
        let artifact =
            NamedWeightArtifact::new(0xCAFE_BABE, metadata(), EvaluationWeights::DEFAULT)
                .expect("artifact is valid");
        let serialized = artifact.serialize().expect("artifact serializes");
        assert!(serialized.contains("parameter.material.pawn.mg=100\n"));
        assert!(serialized.contains("parameter.piece_square.king.h1.eg="));
        assert!(!serialized.contains("values="));
        assert_eq!(
            NamedWeightArtifact::deserialize(&serialized).expect("artifact parses"),
            artifact
        );
    }

    #[test]
    fn checksum_covers_metadata_parameter_names_and_values() {
        let artifact = NamedWeightArtifact::new(7, metadata(), EvaluationWeights::DEFAULT)
            .expect("artifact is valid");
        let mut metadata_changed = artifact.clone();
        metadata_changed.metadata.random_seed ^= 1;
        assert_ne!(metadata_changed.computed_checksum(), artifact.checksum);

        let serialized = artifact.serialize().expect("artifact serializes");
        let renamed = serialized.replacen(
            "parameter.material.pawn.mg=",
            "parameter.material.pawn.middle=",
            1,
        );
        assert!(matches!(
            NamedWeightArtifact::deserialize(&renamed),
            Err(NamedWeightArtifactError::Format(_))
        ));

        let corrupt_checksum = serialized.replacen(
            &format!("checksum={:016x}", artifact.checksum),
            "checksum=0000000000000000",
            1,
        );
        assert!(matches!(
            NamedWeightArtifact::deserialize(&corrupt_checksum),
            Err(NamedWeightArtifactError::ChecksumMismatch { .. })
        ));
    }

    #[test]
    fn incomplete_training_metadata_fails_loudly() {
        let mut incomplete = metadata();
        incomplete.validation_positions = 0;
        assert_eq!(
            NamedWeightArtifact::new(1, incomplete, EvaluationWeights::DEFAULT),
            Err(NamedWeightArtifactError::TrainingMetadata(
                TrainingMetadataError::EmptyValidationSet
            ))
        );
    }
}
