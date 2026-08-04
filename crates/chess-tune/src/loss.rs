use core::fmt;

use chess_core::Position;
use chess_search::{evaluate_with_weights, EvaluationWeights};

/// Evaluation divisor used by the base-10 Texel logistic mapping.
pub const TEXEL_EVALUATION_SCALE_CENTIPAWNS: f64 = 400.0;
/// Upper bound on deterministic calibration intervals.
pub const MAX_K_CALIBRATION_INTERVALS: u32 = 1_000_000;

/// Side-to-move-relative result target used by the loss objective.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum OutcomeTarget {
    /// The side to move eventually lost.
    Loss,
    /// The game was drawn.
    Draw,
    /// The side to move eventually won.
    Win,
}

impl OutcomeTarget {
    /// Returns the exact numerical target used by mean-squared error.
    #[must_use]
    pub const fn probability(self) -> f64 {
        match self {
            Self::Loss => 0.0,
            Self::Draw => 0.5,
            Self::Win => 1.0,
        }
    }
}

/// Valid positive logistic calibration constant.
#[derive(Clone, Copy, Debug, PartialEq, PartialOrd)]
pub struct LogisticK(f64);

impl LogisticK {
    /// Validates a finite strictly positive calibration constant.
    pub fn new(value: f64) -> Result<Self, LossPipelineError> {
        if !value.is_finite() || value <= 0.0 {
            return Err(LossPipelineError::InvalidLogisticK { value });
        }
        Ok(Self(value))
    }

    /// Returns the calibrated constant.
    #[must_use]
    pub const fn value(self) -> f64 {
        self.0
    }
}

/// Deterministic inclusive grid used to calibrate `K` on training data.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct KCalibrationConfig {
    minimum: LogisticK,
    maximum: LogisticK,
    intervals: u32,
}

impl KCalibrationConfig {
    /// Creates an inclusive calibration grid with `intervals + 1` candidates.
    pub fn new(minimum: f64, maximum: f64, intervals: u32) -> Result<Self, LossPipelineError> {
        let minimum = LogisticK::new(minimum)?;
        let maximum = LogisticK::new(maximum)?;
        if minimum.value() >= maximum.value() {
            return Err(LossPipelineError::InvalidCalibrationRange {
                minimum: minimum.value(),
                maximum: maximum.value(),
            });
        }
        if intervals == 0 || intervals > MAX_K_CALIBRATION_INTERVALS {
            return Err(LossPipelineError::InvalidCalibrationIntervals {
                found: intervals,
                maximum: MAX_K_CALIBRATION_INTERVALS,
            });
        }
        Ok(Self {
            minimum,
            maximum,
            intervals,
        })
    }

    /// Returns the smallest candidate value.
    #[must_use]
    pub const fn minimum(self) -> LogisticK {
        self.minimum
    }

    /// Returns the largest candidate value.
    #[must_use]
    pub const fn maximum(self) -> LogisticK {
        self.maximum
    }

    /// Returns the number of equal intervals in the inclusive grid.
    #[must_use]
    pub const fn intervals(self) -> u32 {
        self.intervals
    }

    /// Returns the number of evaluated candidates.
    #[must_use]
    pub const fn candidate_count(self) -> u32 {
        self.intervals + 1
    }

    fn candidate(self, index: u32) -> LogisticK {
        debug_assert!(index <= self.intervals);
        let fraction = f64::from(index) / f64::from(self.intervals);
        LogisticK(self.minimum.value() + (self.maximum.value() - self.minimum.value()) * fraction)
    }
}

/// One position and completed-game target retained for loss evaluation.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct LossPosition {
    position: Position,
    outcome: OutcomeTarget,
    occurrences: u32,
}

impl LossPosition {
    /// Creates one loss row, rejecting zero occurrence counts.
    pub fn new(
        position: Position,
        outcome: OutcomeTarget,
        occurrences: u32,
    ) -> Result<Self, LossPipelineError> {
        if occurrences == 0 {
            return Err(LossPipelineError::ZeroOccurrences);
        }
        Ok(Self {
            position,
            outcome,
            occurrences,
        })
    }

    /// Returns the exact parsed position.
    #[must_use]
    pub const fn position(&self) -> &Position {
        &self.position
    }

    /// Returns the side-to-move-relative game target.
    #[must_use]
    pub const fn outcome(&self) -> OutcomeTarget {
        self.outcome
    }

    /// Returns the number of exact duplicate occurrences represented by this row.
    #[must_use]
    pub const fn occurrences(&self) -> u32 {
        self.occurrences
    }
}

/// Explicit objective partition.
#[derive(Clone, Copy, Debug, Eq, Hash, PartialEq)]
pub enum LossPartition {
    /// Optimizer and `K`-calibration partition.
    Training,
    /// Separately held-out model-selection partition.
    Validation,
}

impl fmt::Display for LossPartition {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str(match self {
            Self::Training => "training",
            Self::Validation => "validation",
        })
    }
}

/// Parsed positions separated into optimizer and held-out partitions.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct LossDataset {
    training: Vec<LossPosition>,
    validation: Vec<LossPosition>,
    training_occurrences: u64,
    validation_occurrences: u64,
}

impl LossDataset {
    /// Constructs a dataset and rejects either empty partition or count overflow.
    pub fn new(
        training: Vec<LossPosition>,
        validation: Vec<LossPosition>,
    ) -> Result<Self, LossPipelineError> {
        let training_occurrences = validate_partition(&training, LossPartition::Training)?;
        let validation_occurrences = validate_partition(&validation, LossPartition::Validation)?;
        Ok(Self {
            training,
            validation,
            training_occurrences,
            validation_occurrences,
        })
    }

    /// Returns unique deduplicated training rows.
    #[must_use]
    pub fn training(&self) -> &[LossPosition] {
        &self.training
    }

    /// Returns unique deduplicated validation rows.
    #[must_use]
    pub fn validation(&self) -> &[LossPosition] {
        &self.validation
    }

    /// Returns occurrence-weighted training position count.
    #[must_use]
    pub const fn training_occurrences(&self) -> u64 {
        self.training_occurrences
    }

    /// Returns occurrence-weighted validation position count.
    #[must_use]
    pub const fn validation_occurrences(&self) -> u64 {
        self.validation_occurrences
    }

    /// Evaluates occurrence-weighted mean-squared error for one explicit partition.
    pub fn mean_squared_error(
        &self,
        partition: LossPartition,
        weights: &EvaluationWeights,
        k: LogisticK,
    ) -> Result<f64, LossPipelineError> {
        let samples = match partition {
            LossPartition::Training => &self.training,
            LossPartition::Validation => &self.validation,
        };
        let evaluated = evaluate_positions(samples, weights);
        mean_squared_error_for_evaluated(&evaluated, k)
    }

    /// Calibrates `K` exclusively on the training partition.
    pub fn calibrate_k(
        &self,
        weights: &EvaluationWeights,
        config: KCalibrationConfig,
    ) -> Result<KCalibrationResult, LossPipelineError> {
        let evaluated = evaluate_positions(&self.training, weights);
        calibrate_evaluated_k(&evaluated, config)
    }
}

/// Deterministic result of training-only `K` calibration.
#[derive(Clone, Copy, Debug, PartialEq)]
pub struct KCalibrationResult {
    k: LogisticK,
    training_mean_squared_error: f64,
    evaluated_candidates: u32,
}

impl KCalibrationResult {
    /// Returns the selected constant.
    #[must_use]
    pub const fn k(self) -> LogisticK {
        self.k
    }

    /// Returns the minimum training objective found on the grid.
    #[must_use]
    pub const fn training_mean_squared_error(self) -> f64 {
        self.training_mean_squared_error
    }

    /// Returns the exact number of inclusive grid candidates evaluated.
    #[must_use]
    pub const fn evaluated_candidates(self) -> u32 {
        self.evaluated_candidates
    }
}

/// Maps a side-to-move centipawn score to an expected game result.
#[must_use]
pub fn logistic_result_probability(evaluation_centipawns: i32, k: LogisticK) -> f64 {
    let exponent = std::f64::consts::LN_10 * k.value() * f64::from(evaluation_centipawns)
        / TEXEL_EVALUATION_SCALE_CENTIPAWNS;
    if exponent >= 0.0 {
        1.0 / (1.0 + (-exponent).exp())
    } else {
        let scaled = exponent.exp();
        scaled / (1.0 + scaled)
    }
}

/// Invalid loss input, split, calibration, or numerical result.
#[derive(Clone, Debug, PartialEq)]
pub enum LossPipelineError {
    /// `K` was zero, negative, infinite, or not a number.
    InvalidLogisticK { value: f64 },
    /// Inclusive grid endpoints were reversed or equal.
    InvalidCalibrationRange { minimum: f64, maximum: f64 },
    /// Grid interval count was zero or unbounded.
    InvalidCalibrationIntervals { found: u32, maximum: u32 },
    /// One retained row represented no occurrences.
    ZeroOccurrences,
    /// The selected required partition had no rows.
    EmptyPartition { partition: LossPartition },
    /// Summed duplicate occurrences exceeded `u64`.
    OccurrenceCountOverflow { partition: LossPartition },
    /// The objective produced a non-finite value.
    NonFiniteObjective,
}

impl fmt::Display for LossPipelineError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match *self {
            Self::InvalidLogisticK { value } => {
                write!(
                    formatter,
                    "logistic K must be finite and positive, found {value}"
                )
            }
            Self::InvalidCalibrationRange { minimum, maximum } => write!(
                formatter,
                "calibration minimum must be smaller than maximum, found {minimum}..={maximum}"
            ),
            Self::InvalidCalibrationIntervals { found, maximum } => write!(
                formatter,
                "calibration intervals must be between 1 and {maximum}, found {found}"
            ),
            Self::ZeroOccurrences => formatter.write_str("loss row occurrences must be nonzero"),
            Self::EmptyPartition { partition } => {
                write!(formatter, "{partition} loss partition must not be empty")
            }
            Self::OccurrenceCountOverflow { partition } => {
                write!(formatter, "{partition} occurrence count overflow")
            }
            Self::NonFiniteObjective => formatter.write_str("loss objective is not finite"),
        }
    }
}

impl std::error::Error for LossPipelineError {}

#[derive(Clone, Copy, Debug)]
struct EvaluatedLossPosition {
    evaluation_centipawns: i32,
    outcome: OutcomeTarget,
    occurrences: u32,
}

fn validate_partition(
    positions: &[LossPosition],
    partition: LossPartition,
) -> Result<u64, LossPipelineError> {
    if positions.is_empty() {
        return Err(LossPipelineError::EmptyPartition { partition });
    }
    positions.iter().try_fold(0_u64, |total, position| {
        total
            .checked_add(u64::from(position.occurrences))
            .ok_or(LossPipelineError::OccurrenceCountOverflow { partition })
    })
}

fn evaluate_positions(
    positions: &[LossPosition],
    weights: &EvaluationWeights,
) -> Vec<EvaluatedLossPosition> {
    positions
        .iter()
        .map(|position| EvaluatedLossPosition {
            evaluation_centipawns: evaluate_with_weights(&position.position, weights).centipawns(),
            outcome: position.outcome,
            occurrences: position.occurrences,
        })
        .collect()
}

fn mean_squared_error_for_evaluated(
    positions: &[EvaluatedLossPosition],
    k: LogisticK,
) -> Result<f64, LossPipelineError> {
    let mut weighted_squared_error = 0.0;
    let mut total_occurrences = 0_u64;
    for position in positions {
        let predicted = logistic_result_probability(position.evaluation_centipawns, k);
        let difference = predicted - position.outcome.probability();
        weighted_squared_error += difference * difference * f64::from(position.occurrences);
        total_occurrences = total_occurrences
            .checked_add(u64::from(position.occurrences))
            .ok_or(LossPipelineError::OccurrenceCountOverflow {
                partition: LossPartition::Training,
            })?;
    }
    if total_occurrences == 0 {
        return Err(LossPipelineError::EmptyPartition {
            partition: LossPartition::Training,
        });
    }
    let objective = weighted_squared_error / total_occurrences as f64;
    if !objective.is_finite() {
        return Err(LossPipelineError::NonFiniteObjective);
    }
    Ok(objective)
}

fn calibrate_evaluated_k(
    positions: &[EvaluatedLossPosition],
    config: KCalibrationConfig,
) -> Result<KCalibrationResult, LossPipelineError> {
    let mut best_k = config.candidate(0);
    let mut best_loss = mean_squared_error_for_evaluated(positions, best_k)?;
    for index in 1..=config.intervals() {
        let candidate = config.candidate(index);
        let loss = mean_squared_error_for_evaluated(positions, candidate)?;
        if loss < best_loss {
            best_k = candidate;
            best_loss = loss;
        }
    }
    Ok(KCalibrationResult {
        k: best_k,
        training_mean_squared_error: best_loss,
        evaluated_candidates: config.candidate_count(),
    })
}

#[cfg(test)]
mod tests {
    use chess_core::Position;
    use chess_search::{evaluate_with_weights, EvaluationWeights};

    use super::{
        calibrate_evaluated_k, logistic_result_probability, mean_squared_error_for_evaluated,
        EvaluatedLossPosition, KCalibrationConfig, LogisticK, LossDataset, LossPartition,
        LossPipelineError, LossPosition, OutcomeTarget, MAX_K_CALIBRATION_INTERVALS,
    };

    const WHITE_ADVANTAGE_FEN: &str = "7k/8/8/8/8/8/Q6K/8 w - - 0 1";

    fn white_advantage_position() -> Position {
        Position::from_fen(WHITE_ADVANTAGE_FEN).expect("fixture FEN is valid")
    }

    fn loss_position(outcome: OutcomeTarget, occurrences: u32) -> LossPosition {
        LossPosition::new(white_advantage_position(), outcome, occurrences)
            .expect("loss position is valid")
    }

    #[test]
    fn logistic_mapping_is_centered_monotonic_and_symmetric() {
        let k = LogisticK::new(1.2).expect("K is valid");
        let center = logistic_result_probability(0, k);
        let positive = logistic_result_probability(250, k);
        let negative = logistic_result_probability(-250, k);
        assert!((center - 0.5).abs() < f64::EPSILON);
        assert!(positive > center);
        assert!(negative < center);
        assert!((positive + negative - 1.0).abs() < 1.0e-12);
    }

    #[test]
    fn invalid_k_and_calibration_grids_fail_loudly() {
        assert!(matches!(
            LogisticK::new(0.0),
            Err(LossPipelineError::InvalidLogisticK { .. })
        ));
        assert!(matches!(
            KCalibrationConfig::new(2.0, 1.0, 10),
            Err(LossPipelineError::InvalidCalibrationRange { .. })
        ));
        assert!(matches!(
            KCalibrationConfig::new(0.1, 2.0, 0),
            Err(LossPipelineError::InvalidCalibrationIntervals { .. })
        ));
        assert!(matches!(
            KCalibrationConfig::new(0.1, 2.0, MAX_K_CALIBRATION_INTERVALS + 1),
            Err(LossPipelineError::InvalidCalibrationIntervals { .. })
        ));
    }

    #[test]
    fn occurrence_weighting_is_exact() {
        let k = LogisticK::new(1.0).expect("K is valid");
        let positions = [
            EvaluatedLossPosition {
                evaluation_centipawns: 400,
                outcome: OutcomeTarget::Win,
                occurrences: 3,
            },
            EvaluatedLossPosition {
                evaluation_centipawns: 400,
                outcome: OutcomeTarget::Draw,
                occurrences: 1,
            },
        ];
        let predicted = logistic_result_probability(400, k);
        let expected = (3.0 * (predicted - 1.0).powi(2) + (predicted - 0.5).powi(2)) / 4.0;
        let actual = mean_squared_error_for_evaluated(&positions, k).expect("loss is valid");
        assert!((actual - expected).abs() < 1.0e-15);
    }

    #[test]
    fn calibration_recovers_an_interior_training_optimum() {
        let positions = [
            EvaluatedLossPosition {
                evaluation_centipawns: 400,
                outcome: OutcomeTarget::Win,
                occurrences: 1,
            },
            EvaluatedLossPosition {
                evaluation_centipawns: 400,
                outcome: OutcomeTarget::Draw,
                occurrences: 1,
            },
        ];
        let config = KCalibrationConfig::new(0.001, 1.001, 1_000).expect("grid is valid");
        let result = calibrate_evaluated_k(&positions, config).expect("calibration succeeds");
        let expected = 3.0_f64.log10();
        assert!((result.k().value() - expected).abs() < 0.001);
        assert_eq!(result.evaluated_candidates(), 1_001);
    }

    #[test]
    fn calibration_and_objectives_keep_validation_held_out() {
        let position = white_advantage_position();
        assert!(
            evaluate_with_weights(&position, &EvaluationWeights::DEFAULT).centipawns() > 0,
            "fixture must be favorable to the side to move"
        );
        let dataset = LossDataset::new(
            vec![loss_position(OutcomeTarget::Win, 1)],
            vec![loss_position(OutcomeTarget::Loss, 1)],
        )
        .expect("dataset is valid");
        let config = KCalibrationConfig::new(0.1, 2.0, 19).expect("grid is valid");
        let result = dataset
            .calibrate_k(&EvaluationWeights::DEFAULT, config)
            .expect("calibration succeeds");
        assert_eq!(result.k(), config.maximum());

        let training = dataset
            .mean_squared_error(
                LossPartition::Training,
                &EvaluationWeights::DEFAULT,
                result.k(),
            )
            .expect("training loss");
        let validation = dataset
            .mean_squared_error(
                LossPartition::Validation,
                &EvaluationWeights::DEFAULT,
                result.k(),
            )
            .expect("validation loss");
        assert!(training < validation);
    }

    #[test]
    fn empty_partitions_and_zero_occurrences_are_rejected() {
        assert_eq!(
            LossPosition::new(white_advantage_position(), OutcomeTarget::Draw, 0),
            Err(LossPipelineError::ZeroOccurrences)
        );
        assert_eq!(
            LossDataset::new(Vec::new(), vec![loss_position(OutcomeTarget::Draw, 1)]),
            Err(LossPipelineError::EmptyPartition {
                partition: LossPartition::Training,
            })
        );
        assert_eq!(
            LossDataset::new(vec![loss_position(OutcomeTarget::Draw, 1)], Vec::new()),
            Err(LossPipelineError::EmptyPartition {
                partition: LossPartition::Validation,
            })
        );
    }
}
