use core::fmt;
use std::{
    fmt::Write as _,
    fs::{self, OpenOptions},
    io::Write as _,
    path::Path,
};

use chess_search::{
    EvaluationWeightSet, EvaluationWeights, WeightValidationError, EVALUATION_STRUCTURE,
    EVALUATION_STRUCTURE_SCHEMA_VERSION, EVALUATION_WEIGHT_SCHEMA_VERSION,
};
use chess_tune::{
    tunable_values, LogisticK, LossDataset, LossPartition, LossPipelineError, NamedWeightArtifact,
    NamedWeightArtifactError, OutcomeTarget, SpsaCheckpoint, SpsaConfig, SpsaOptimizer,
    SpsaOptimizerError, TrainingDatasetProvenance, TrainingMetadata, TrainingRunProvenance,
    TunableParameter, SPSA_OPTIMIZER_IDENTIFIER, TUNABLE_PARAMETER_COUNT,
};

/// Current strict tuning-report schema.
pub const TUNING_REPORT_SCHEMA_VERSION: u16 = 1;
/// Stable semantic identity of the Task 21.4 report contract.
pub const TUNING_REPORT_IDENTIFIER: u64 = 0x5455_4e45_5250_5431;

const REPORT_MARKER: &str = "chess-tuning-report-v1";
const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;

/// Caller-supplied engine, source, weight, and invocation identity.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct TuningReportProvenance {
    /// Stable caller-defined engine build identity.
    pub engine_identifier: u64,
    /// Semantic engine version.
    pub engine_version: String,
    /// Exact 20-byte source commit used by the trainer.
    pub source_commit: [u8; 20],
    /// Starting weight-set identifier.
    pub initial_weight_identifier: u64,
    /// Candidate weight-set identifier.
    pub candidate_weight_identifier: u64,
    /// Exact shell command or equivalent invocation.
    pub exact_command: String,
}

impl TuningReportProvenance {
    /// Constructs and validates complete report provenance.
    pub fn new(
        engine_identifier: u64,
        engine_version: String,
        source_commit: [u8; 20],
        initial_weight_identifier: u64,
        candidate_weight_identifier: u64,
        exact_command: String,
    ) -> Result<Self, TuningReportError> {
        let value = Self {
            engine_identifier,
            engine_version,
            source_commit,
            initial_weight_identifier,
            candidate_weight_identifier,
            exact_command,
        };
        value.validate()?;
        Ok(value)
    }

    fn validate(&self) -> Result<(), TuningReportError> {
        if self.engine_identifier == 0
            || self.initial_weight_identifier == 0
            || self.candidate_weight_identifier == 0
        {
            return Err(TuningReportError::InvalidProvenance(
                "engine and weight identifiers must be non-zero",
            ));
        }
        if self.initial_weight_identifier == self.candidate_weight_identifier {
            return Err(TuningReportError::InvalidProvenance(
                "initial and candidate identifiers must differ",
            ));
        }
        if self.engine_version.is_empty() || self.exact_command.is_empty() {
            return Err(TuningReportError::InvalidProvenance(
                "engine version and exact command must not be empty",
            ));
        }
        if self.source_commit.iter().all(|byte| *byte == 0) {
            return Err(TuningReportError::InvalidProvenance(
                "source commit must not be all zeroes",
            ));
        }
        Ok(())
    }
}

/// One canonical named parameter comparison.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TuningParameterDelta {
    /// Stable named parameter identity.
    pub parameter: TunableParameter,
    /// Starting value.
    pub initial: i16,
    /// Candidate value.
    pub candidate: i16,
}

impl TuningParameterDelta {
    /// Signed candidate-minus-initial delta without `i16` overflow.
    #[must_use]
    pub const fn delta(self) -> i32 {
        self.candidate as i32 - self.initial as i32
    }
}

/// Versioned, checksummed Task 21.4 report.
#[derive(Clone, Debug, PartialEq)]
pub struct TuningReport {
    /// Caller-supplied engine and command identity.
    pub provenance: TuningReportProvenance,
    /// Canonical Task 20 source identity and occurrence counts.
    pub dataset: TrainingDatasetProvenance,
    /// Fingerprint of the exact train/validation loss rows.
    pub loss_dataset_fingerprint: u64,
    /// Number of unique training rows.
    pub training_rows: u64,
    /// Number of unique validation rows.
    pub validation_rows: u64,
    /// Complete SPSA configuration.
    pub config: SpsaConfig,
    /// Checksum stored by the exact checkpoint.
    pub checkpoint_checksum: u64,
    /// Original perturbation seed.
    pub random_seed: u64,
    /// Cumulative completed iterations.
    pub completed_iterations: u64,
    /// Exact logistic mapping constant.
    pub logistic_k: LogisticK,
    /// Starting weights.
    pub initial_weights: EvaluationWeights,
    /// Training-selected candidate weights.
    pub candidate_weights: EvaluationWeights,
    /// Initial weight-set checksum.
    pub initial_weight_checksum: u64,
    /// Candidate weight-set checksum.
    pub candidate_weight_checksum: u64,
    /// Initial unregularized training MSE.
    pub initial_training_loss: f64,
    /// Initial unregularized held-out validation MSE.
    pub initial_validation_loss: f64,
    /// Candidate unregularized training MSE.
    pub final_training_loss: f64,
    /// Candidate unregularized held-out validation MSE.
    pub final_validation_loss: f64,
    /// Candidate regularized training objective selected by SPSA.
    pub final_training_objective: f64,
    /// Canonical semantic report checksum.
    pub checksum: u64,
}

impl TuningReport {
    /// Builds a report and binds it to the exact data, config, initial weights, and checkpoint.
    pub fn from_checkpoint(
        provenance: TuningReportProvenance,
        dataset_provenance: TrainingDatasetProvenance,
        config: SpsaConfig,
        dataset: &LossDataset,
        initial_weights: EvaluationWeights,
        checkpoint: &SpsaCheckpoint,
    ) -> Result<Self, TuningReportError> {
        provenance.validate()?;
        validate_dataset_provenance(dataset_provenance, dataset)?;
        SpsaOptimizer::resume(config, dataset, checkpoint.clone())?;
        if checkpoint.completed_iterations() == 0 {
            return Err(TuningReportError::InvalidProvenance(
                "a report requires at least one completed iteration",
            ));
        }
        let fingerprint = loss_dataset_fingerprint(dataset);
        require_u64(
            "loss dataset fingerprint",
            checkpoint.dataset_fingerprint(),
            fingerprint,
        )?;
        require_u64(
            "optimizer config fingerprint",
            checkpoint.config_fingerprint(),
            config.fingerprint(),
        )?;

        let initial_set =
            EvaluationWeightSet::new(provenance.initial_weight_identifier, initial_weights);
        initial_set.validate()?;
        let candidate_weights = checkpoint.best_weights();
        let candidate_set =
            EvaluationWeightSet::new(provenance.candidate_weight_identifier, candidate_weights);
        candidate_set.validate()?;

        let initial_training_loss = dataset.mean_squared_error(
            LossPartition::Training,
            &initial_weights,
            checkpoint.logistic_k(),
        )?;
        let initial_validation_loss = dataset.mean_squared_error(
            LossPartition::Validation,
            &initial_weights,
            checkpoint.logistic_k(),
        )?;
        let final_training_loss = dataset.mean_squared_error(
            LossPartition::Training,
            &candidate_weights,
            checkpoint.logistic_k(),
        )?;
        let final_validation_loss = dataset.mean_squared_error(
            LossPartition::Validation,
            &candidate_weights,
            checkpoint.logistic_k(),
        )?;
        let objective = regularized_training_objective(
            initial_weights,
            candidate_weights,
            final_training_loss,
            config.regularization_strength(),
        );
        require_float(
            "checkpoint initial-weight reference",
            checkpoint.best_training_objective(),
            objective,
        )?;

        let mut report = Self {
            provenance,
            dataset: dataset_provenance,
            loss_dataset_fingerprint: fingerprint,
            training_rows: u64::try_from(dataset.training().len()).map_err(|_| {
                TuningReportError::InvalidProvenance("training row count exceeds u64")
            })?,
            validation_rows: u64::try_from(dataset.validation().len()).map_err(|_| {
                TuningReportError::InvalidProvenance("validation row count exceeds u64")
            })?,
            config,
            checkpoint_checksum: checkpoint_checksum(checkpoint)?,
            random_seed: checkpoint.random_seed(),
            completed_iterations: checkpoint.completed_iterations(),
            logistic_k: checkpoint.logistic_k(),
            initial_weights,
            candidate_weights,
            initial_weight_checksum: initial_set.checksum,
            candidate_weight_checksum: candidate_set.checksum,
            initial_training_loss,
            initial_validation_loss,
            final_training_loss,
            final_validation_loss,
            final_training_objective: checkpoint.best_training_objective(),
            checksum: 0,
        };
        report.checksum = report.computed_checksum();
        report.validate()?;
        Ok(report)
    }

    /// Iterates all 810 deltas in canonical named-schema order.
    pub fn parameter_deltas(&self) -> impl ExactSizeIterator<Item = TuningParameterDelta> + '_ {
        TunableParameter::all().map(|parameter| TuningParameterDelta {
            parameter,
            initial: parameter.value(&self.initial_weights),
            candidate: parameter.value(&self.candidate_weights),
        })
    }

    /// Produces the existing versioned candidate artifact without activating it.
    pub fn candidate_artifact(
        &self,
        generated_at_unix_seconds: u64,
    ) -> Result<NamedWeightArtifact, TuningReportError> {
        self.validate()?;
        let metadata = TrainingMetadata::new(
            TrainingRunProvenance::new(
                SPSA_OPTIMIZER_IDENTIFIER,
                self.provenance.source_commit,
                self.random_seed,
                self.completed_iterations,
                generated_at_unix_seconds,
            ),
            self.dataset,
        );
        Ok(NamedWeightArtifact::new(
            self.provenance.candidate_weight_identifier,
            metadata,
            self.candidate_weights,
        )?)
    }

    /// Recomputes semantic identity, weight validity, and report checksum.
    pub fn validate(&self) -> Result<(), TuningReportError> {
        self.provenance.validate()?;
        if self.training_rows == 0 || self.validation_rows == 0 {
            return Err(TuningReportError::InvalidProvenance(
                "training and validation row counts must be non-zero",
            ));
        }
        if self.completed_iterations == 0
            || self.completed_iterations > self.config.maximum_iterations()
        {
            return Err(TuningReportError::InvalidProvenance(
                "completed iterations are outside the configured range",
            ));
        }
        let initial = EvaluationWeightSet::new(
            self.provenance.initial_weight_identifier,
            self.initial_weights,
        );
        initial.validate()?;
        require_u64(
            "initial weight checksum",
            self.initial_weight_checksum,
            initial.checksum,
        )?;
        let candidate = EvaluationWeightSet::new(
            self.provenance.candidate_weight_identifier,
            self.candidate_weights,
        );
        candidate.validate()?;
        require_u64(
            "candidate weight checksum",
            self.candidate_weight_checksum,
            candidate.checksum,
        )?;
        for (field, value) in [
            ("initial training loss", self.initial_training_loss),
            ("initial validation loss", self.initial_validation_loss),
            ("final training loss", self.final_training_loss),
            ("final validation loss", self.final_validation_loss),
            ("final training objective", self.final_training_objective),
        ] {
            if !value.is_finite() || value < 0.0 {
                return Err(TuningReportError::InvalidLoss { field, value });
            }
        }
        require_u64("report checksum", self.checksum, self.computed_checksum())
    }

    /// Computes the canonical semantic checksum over every report field and named delta.
    #[must_use]
    pub fn computed_checksum(&self) -> u64 {
        let mut hash = FNV_OFFSET;
        for value in [
            u64::from(TUNING_REPORT_SCHEMA_VERSION),
            TUNING_REPORT_IDENTIFIER,
            self.provenance.engine_identifier,
        ] {
            hash = hash_bytes(hash, &value.to_le_bytes());
        }
        hash = hash_text(hash, &self.provenance.engine_version);
        hash = hash_bytes(hash, &self.provenance.source_commit);
        hash = hash_bytes(
            hash,
            &self.provenance.initial_weight_identifier.to_le_bytes(),
        );
        hash = hash_bytes(
            hash,
            &self.provenance.candidate_weight_identifier.to_le_bytes(),
        );
        hash = hash_text(hash, &self.provenance.exact_command);
        hash = hash_bytes(hash, &EVALUATION_WEIGHT_SCHEMA_VERSION.to_le_bytes());
        hash = hash_bytes(hash, &EVALUATION_STRUCTURE_SCHEMA_VERSION.to_le_bytes());
        for value in [
            EVALUATION_STRUCTURE.computed_checksum(),
            u64::from(self.dataset.schema_version),
            self.dataset.checksum,
            self.dataset.training_positions,
            self.dataset.validation_positions,
            self.loss_dataset_fingerprint,
            self.training_rows,
            self.validation_rows,
            SPSA_OPTIMIZER_IDENTIFIER,
            self.config.fingerprint(),
            self.checkpoint_checksum,
            self.config.maximum_iterations(),
            self.config.schedule().learning_rate().to_bits(),
            self.config.schedule().step_decay().to_bits(),
            self.config.schedule().perturbation_size().to_bits(),
            self.config.schedule().perturbation_decay().to_bits(),
            self.config.schedule().stability_constant().to_bits(),
        ] {
            hash = hash_bytes(hash, &value.to_le_bytes());
        }
        hash = hash_bytes(hash, &self.config.bounds().minimum().to_le_bytes());
        hash = hash_bytes(hash, &self.config.bounds().maximum().to_le_bytes());
        for value in [
            self.config.regularization_strength().to_bits(),
            self.random_seed,
            self.completed_iterations,
            self.logistic_k.value().to_bits(),
            self.initial_weight_checksum,
            self.candidate_weight_checksum,
            self.initial_training_loss.to_bits(),
            self.initial_validation_loss.to_bits(),
            self.final_training_loss.to_bits(),
            self.final_validation_loss.to_bits(),
            self.final_training_objective.to_bits(),
            TUNABLE_PARAMETER_COUNT as u64,
        ] {
            hash = hash_bytes(hash, &value.to_le_bytes());
        }
        for delta in self.parameter_deltas() {
            hash = hash_text(hash, &delta.parameter.name());
            hash = hash_bytes(hash, &delta.initial.to_le_bytes());
            hash = hash_bytes(hash, &delta.candidate.to_le_bytes());
            hash = hash_bytes(hash, &delta.delta().to_le_bytes());
        }
        hash
    }

    /// Serializes a deterministic, human-readable report with exact float bits.
    pub fn serialize(&self) -> Result<String, TuningReportError> {
        self.validate()?;
        let mut output = String::new();
        line(&mut output, REPORT_MARKER);
        field(&mut output, "report_schema", TUNING_REPORT_SCHEMA_VERSION);
        hex_field(&mut output, "report_identifier", TUNING_REPORT_IDENTIFIER);
        hex_field(
            &mut output,
            "engine_identifier",
            self.provenance.engine_identifier,
        );
        text_field(
            &mut output,
            "engine_version",
            &self.provenance.engine_version,
        );
        field(
            &mut output,
            "source_commit",
            encode_hex(&self.provenance.source_commit),
        );
        field(
            &mut output,
            "evaluation_schema",
            EVALUATION_WEIGHT_SCHEMA_VERSION,
        );
        field(
            &mut output,
            "structure_schema",
            EVALUATION_STRUCTURE_SCHEMA_VERSION,
        );
        hex_field(
            &mut output,
            "structure_checksum",
            EVALUATION_STRUCTURE.computed_checksum(),
        );
        field(&mut output, "dataset_schema", self.dataset.schema_version);
        hex_field(&mut output, "dataset_checksum", self.dataset.checksum);
        hex_field(
            &mut output,
            "loss_dataset_fingerprint",
            self.loss_dataset_fingerprint,
        );
        field(&mut output, "training_rows", self.training_rows);
        field(&mut output, "validation_rows", self.validation_rows);
        field(
            &mut output,
            "training_occurrences",
            self.dataset.training_positions,
        );
        field(
            &mut output,
            "validation_occurrences",
            self.dataset.validation_positions,
        );
        hex_field(
            &mut output,
            "optimizer_identifier",
            SPSA_OPTIMIZER_IDENTIFIER,
        );
        hex_field(
            &mut output,
            "optimizer_config_fingerprint",
            self.config.fingerprint(),
        );
        hex_field(&mut output, "checkpoint_checksum", self.checkpoint_checksum);
        field(
            &mut output,
            "maximum_iterations",
            self.config.maximum_iterations(),
        );
        float_field(
            &mut output,
            "learning_rate",
            self.config.schedule().learning_rate(),
        );
        float_field(
            &mut output,
            "step_decay",
            self.config.schedule().step_decay(),
        );
        float_field(
            &mut output,
            "perturbation_size",
            self.config.schedule().perturbation_size(),
        );
        float_field(
            &mut output,
            "perturbation_decay",
            self.config.schedule().perturbation_decay(),
        );
        float_field(
            &mut output,
            "stability_constant",
            self.config.schedule().stability_constant(),
        );
        field(
            &mut output,
            "minimum_weight",
            self.config.bounds().minimum(),
        );
        field(
            &mut output,
            "maximum_weight",
            self.config.bounds().maximum(),
        );
        float_field(
            &mut output,
            "regularization_strength",
            self.config.regularization_strength(),
        );
        field(&mut output, "random_seed", self.random_seed);
        field(
            &mut output,
            "completed_iterations",
            self.completed_iterations,
        );
        float_field(&mut output, "logistic_k", self.logistic_k.value());
        text_field(&mut output, "exact_command", &self.provenance.exact_command);
        hex_field(
            &mut output,
            "initial_weight_identifier",
            self.provenance.initial_weight_identifier,
        );
        hex_field(
            &mut output,
            "initial_weight_checksum",
            self.initial_weight_checksum,
        );
        hex_field(
            &mut output,
            "candidate_weight_identifier",
            self.provenance.candidate_weight_identifier,
        );
        hex_field(
            &mut output,
            "candidate_weight_checksum",
            self.candidate_weight_checksum,
        );
        float_field(
            &mut output,
            "initial_training_loss",
            self.initial_training_loss,
        );
        float_field(
            &mut output,
            "initial_validation_loss",
            self.initial_validation_loss,
        );
        float_field(&mut output, "final_training_loss", self.final_training_loss);
        float_field(
            &mut output,
            "final_validation_loss",
            self.final_validation_loss,
        );
        float_field(
            &mut output,
            "final_training_objective",
            self.final_training_objective,
        );
        field(&mut output, "parameter_count", TUNABLE_PARAMETER_COUNT);
        for delta in self.parameter_deltas() {
            writeln!(
                output,
                "parameter.{}={}\t{}\t{}",
                delta.parameter.name(),
                delta.initial,
                delta.candidate,
                delta.delta()
            )
            .expect("writing to String cannot fail");
        }
        hex_field(&mut output, "checksum", self.checksum);
        Ok(output)
    }
}

/// Writes a report through an explicit same-directory temporary path and atomic rename.
pub fn write_tuning_report_atomic(
    destination: &Path,
    temporary: &Path,
    report: &TuningReport,
) -> Result<(), TuningReportError> {
    write_text_atomic(destination, temporary, &report.serialize()?)
}

/// Writes a named candidate artifact without changing runtime defaults.
pub fn write_candidate_artifact_atomic(
    destination: &Path,
    temporary: &Path,
    artifact: &NamedWeightArtifact,
) -> Result<(), TuningReportError> {
    write_text_atomic(destination, temporary, &artifact.serialize()?)
}

/// Invalid report provenance, binding, loss, weight, or persistence.
#[derive(Debug, PartialEq)]
pub enum TuningReportError {
    /// Caller-supplied provenance was absent or contradictory.
    InvalidProvenance(&'static str),
    /// One exact integer/checksum identity differed.
    ValueMismatch {
        field: &'static str,
        expected: u64,
        found: u64,
    },
    /// One exact or recomputed floating-point value differed.
    LossMismatch {
        field: &'static str,
        stored: f64,
        recomputed: f64,
    },
    /// A loss was negative, infinite, or not a number.
    InvalidLoss { field: &'static str, value: f64 },
    /// Optimizer validation failed.
    Optimizer(SpsaOptimizerError),
    /// Loss evaluation failed.
    Loss(LossPipelineError),
    /// Runtime weight validation failed.
    Weight(WeightValidationError),
    /// Named candidate artifact validation failed.
    Artifact(NamedWeightArtifactError),
    /// A filesystem operation failed.
    Io {
        operation: &'static str,
        path: String,
        message: String,
    },
}

impl fmt::Display for TuningReportError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InvalidProvenance(message) => formatter.write_str(message),
            Self::ValueMismatch {
                field,
                expected,
                found,
            } => write!(
                formatter,
                "{field} mismatch: expected {expected:016x}, found {found:016x}"
            ),
            Self::LossMismatch {
                field,
                stored,
                recomputed,
            } => write!(
                formatter,
                "{field} mismatch: stored {stored}, recomputed {recomputed}"
            ),
            Self::InvalidLoss { field, value } => {
                write!(
                    formatter,
                    "{field} must be finite and non-negative, found {value}"
                )
            }
            Self::Optimizer(error) => write!(formatter, "invalid optimizer state: {error}"),
            Self::Loss(error) => write!(formatter, "loss evaluation failed: {error}"),
            Self::Weight(error) => write!(formatter, "invalid report weights: {error}"),
            Self::Artifact(error) => write!(formatter, "invalid candidate artifact: {error}"),
            Self::Io {
                operation,
                path,
                message,
            } => write!(formatter, "failed to {operation} at {path}: {message}"),
        }
    }
}

impl std::error::Error for TuningReportError {}

impl From<SpsaOptimizerError> for TuningReportError {
    fn from(error: SpsaOptimizerError) -> Self {
        Self::Optimizer(error)
    }
}

impl From<LossPipelineError> for TuningReportError {
    fn from(error: LossPipelineError) -> Self {
        Self::Loss(error)
    }
}

impl From<WeightValidationError> for TuningReportError {
    fn from(error: WeightValidationError) -> Self {
        Self::Weight(error)
    }
}

impl From<NamedWeightArtifactError> for TuningReportError {
    fn from(error: NamedWeightArtifactError) -> Self {
        Self::Artifact(error)
    }
}

fn validate_dataset_provenance(
    provenance: TrainingDatasetProvenance,
    dataset: &LossDataset,
) -> Result<(), TuningReportError> {
    if provenance.schema_version == 0 || provenance.checksum == 0 {
        return Err(TuningReportError::InvalidProvenance(
            "dataset schema and checksum must be non-zero",
        ));
    }
    require_u64(
        "training occurrences",
        provenance.training_positions,
        dataset.training_occurrences(),
    )?;
    require_u64(
        "validation occurrences",
        provenance.validation_positions,
        dataset.validation_occurrences(),
    )
}

fn regularized_training_objective(
    initial: EvaluationWeights,
    candidate: EvaluationWeights,
    training_loss: f64,
    regularization_strength: f64,
) -> f64 {
    let initial_values = tunable_values(&initial);
    let candidate_values = tunable_values(&candidate);
    let mean_squared_delta = initial_values
        .iter()
        .zip(candidate_values)
        .map(|(initial_value, candidate_value)| {
            let difference = f64::from(candidate_value) - f64::from(*initial_value);
            difference * difference
        })
        .sum::<f64>()
        / TUNABLE_PARAMETER_COUNT as f64;
    training_loss + regularization_strength * mean_squared_delta
}

fn require_u64(field: &'static str, expected: u64, found: u64) -> Result<(), TuningReportError> {
    if expected != found {
        return Err(TuningReportError::ValueMismatch {
            field,
            expected,
            found,
        });
    }
    Ok(())
}

fn require_float(
    field: &'static str,
    stored: f64,
    recomputed: f64,
) -> Result<(), TuningReportError> {
    let tolerance = 1.0e-12 * stored.abs().max(recomputed.abs()).max(1.0);
    if !stored.is_finite() || !recomputed.is_finite() || (stored - recomputed).abs() > tolerance {
        return Err(TuningReportError::LossMismatch {
            field,
            stored,
            recomputed,
        });
    }
    Ok(())
}

fn loss_dataset_fingerprint(dataset: &LossDataset) -> u64 {
    let mut hash = FNV_OFFSET;
    for (tag, positions) in [(0_u8, dataset.training()), (1_u8, dataset.validation())] {
        hash = hash_bytes(hash, &[tag]);
        hash = hash_bytes(hash, &(positions.len() as u64).to_le_bytes());
        for position in positions {
            let fen = position.position().to_fen();
            hash = hash_text(hash, &fen);
            hash = hash_bytes(
                hash,
                &[match position.outcome() {
                    OutcomeTarget::Loss => 0,
                    OutcomeTarget::Draw => 1,
                    OutcomeTarget::Win => 2,
                }],
            );
            hash = hash_bytes(hash, &position.occurrences().to_le_bytes());
        }
    }
    hash
}

fn checkpoint_checksum(checkpoint: &SpsaCheckpoint) -> Result<u64, TuningReportError> {
    let bytes = checkpoint.to_bytes();
    let tail =
        bytes
            .get(bytes.len().saturating_sub(8)..)
            .ok_or(TuningReportError::InvalidProvenance(
                "checkpoint checksum is missing",
            ))?;
    let checksum: [u8; 8] = tail.try_into().map_err(|_| {
        TuningReportError::InvalidProvenance("checkpoint checksum length is invalid")
    })?;
    Ok(u64::from_le_bytes(checksum))
}

fn write_text_atomic(
    destination: &Path,
    temporary: &Path,
    text: &str,
) -> Result<(), TuningReportError> {
    if destination == temporary
        || destination.parent().unwrap_or_else(|| Path::new("."))
            != temporary.parent().unwrap_or_else(|| Path::new("."))
    {
        return Err(TuningReportError::InvalidProvenance(
            "atomic destination and temporary paths must differ and share one directory",
        ));
    }
    let mut file = OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(temporary)
        .map_err(|error| io_error("create temporary artifact", temporary, error))?;
    if let Err(error) = file
        .write_all(text.as_bytes())
        .and_then(|()| file.flush())
        .and_then(|()| file.sync_all())
    {
        drop(file);
        let _ = fs::remove_file(temporary);
        return Err(io_error("write temporary artifact", temporary, error));
    }
    drop(file);
    if let Err(error) = fs::rename(temporary, destination) {
        let _ = fs::remove_file(temporary);
        return Err(io_error("rename artifact", destination, error));
    }
    Ok(())
}

fn io_error(operation: &'static str, path: &Path, error: std::io::Error) -> TuningReportError {
    TuningReportError::Io {
        operation,
        path: path.display().to_string(),
        message: error.to_string(),
    }
}

fn line(output: &mut String, value: &str) {
    writeln!(output, "{value}").expect("writing to String cannot fail");
}

fn field(output: &mut String, name: &str, value: impl fmt::Display) {
    writeln!(output, "{name}={value}").expect("writing to String cannot fail");
}

fn hex_field(output: &mut String, name: &str, value: u64) {
    writeln!(output, "{name}={value:016x}").expect("writing to String cannot fail");
}

fn float_field(output: &mut String, name: &str, value: f64) {
    writeln!(output, "{name}={value:.17e}\tbits={:016x}", value.to_bits())
        .expect("writing to String cannot fail");
}

fn text_field(output: &mut String, name: &str, value: &str) {
    field(
        output,
        &format!("{name}.utf8_hex"),
        encode_hex(value.as_bytes()),
    );
}

fn encode_hex(bytes: &[u8]) -> String {
    let mut output = String::with_capacity(bytes.len() * 2);
    for byte in bytes {
        write!(output, "{byte:02x}").expect("writing to String cannot fail");
    }
    output
}

fn hash_text(mut hash: u64, text: &str) -> u64 {
    hash = hash_bytes(hash, &(text.len() as u64).to_le_bytes());
    hash_bytes(hash, text.as_bytes())
}

fn hash_bytes(mut hash: u64, bytes: &[u8]) -> u64 {
    for byte in bytes {
        hash ^= u64::from(*byte);
        hash = hash.wrapping_mul(FNV_PRIME);
    }
    hash
}

#[cfg(test)]
mod tests {
    use chess_core::Position;
    use chess_search::{EvaluationWeights, BASELINE_WEIGHT_SET_ID};
    use chess_tune::{
        LogisticK, LossDataset, LossPosition, OutcomeTarget, SpsaConfig, SpsaOptimizer,
        SpsaSchedule, SpsaWeightBounds, TrainingDatasetProvenance, TUNABLE_PARAMETER_COUNT,
    };

    use super::{TuningReport, TuningReportProvenance, FNV_OFFSET};

    fn position(fen: &str, outcome: OutcomeTarget, occurrences: u32) -> LossPosition {
        LossPosition::new(
            Position::from_fen(fen).expect("valid fixture"),
            outcome,
            occurrences,
        )
        .expect("valid loss row")
    }

    #[test]
    fn report_records_required_losses_deltas_identities_and_exact_config() {
        let dataset = LossDataset::new(
            vec![position(
                "7k/8/8/8/8/8/Q6K/8 w - - 0 1",
                OutcomeTarget::Win,
                3,
            )],
            vec![position(
                "7k/q7/8/8/8/8/8/7K b - - 0 1",
                OutcomeTarget::Draw,
                2,
            )],
        )
        .expect("valid dataset");
        let config = SpsaConfig::new(
            4,
            SpsaSchedule::new(1.0, 0.602, 2.0, 0.101, 1.0).expect("valid schedule"),
            SpsaWeightBounds::new(-1_000, 2_000).expect("valid bounds"),
            0.001,
        )
        .expect("valid config");
        let mut optimizer = SpsaOptimizer::new(
            config,
            7,
            EvaluationWeights::DEFAULT,
            &dataset,
            LogisticK::new(1.0).expect("valid K"),
        )
        .expect("optimizer starts");
        optimizer.advance(&dataset, 2).expect("optimizer advances");
        let report = TuningReport::from_checkpoint(
            TuningReportProvenance::new(
                1,
                "0.1.0-test".to_owned(),
                [1; 20],
                BASELINE_WEIGHT_SET_ID,
                2,
                "cargo run --locked -p chess-tools -- tune-report".to_owned(),
            )
            .expect("valid provenance"),
            TrainingDatasetProvenance::new(
                1,
                FNV_OFFSET,
                dataset.training_occurrences(),
                dataset.validation_occurrences(),
            ),
            config,
            &dataset,
            EvaluationWeights::DEFAULT,
            &optimizer.checkpoint(),
        )
        .expect("valid report");
        let text = report.serialize().expect("report serializes");
        for required in [
            "initial_training_loss=",
            "initial_validation_loss=",
            "final_training_loss=",
            "final_validation_loss=",
            "dataset_checksum=",
            "engine_identifier=",
            "exact_command.utf8_hex=",
            "maximum_iterations=",
        ] {
            assert!(text.contains(required));
        }
        assert_eq!(report.parameter_deltas().len(), TUNABLE_PARAMETER_COUNT);
        assert_eq!(report.checksum, report.computed_checksum());
        let artifact = report
            .candidate_artifact(1_800_000_000)
            .expect("candidate artifact is valid");
        assert_eq!(artifact.identifier, 2);
    }
}
