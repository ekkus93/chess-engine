//! Adapter from validated Task 20 self-play datasets to `chess-tune` loss inputs.

mod report;

use core::fmt;

use chess_core::{Color, Position};
use chess_tune::{
    LossDataset, LossPipelineError, LossPosition, OutcomeTarget, TrainingDatasetProvenance,
};

use crate::self_play::{
    DatasetSplit, SelfPlayDataset, SelfPlayResult, SELF_PLAY_DATASET_SCHEMA_VERSION,
};

pub use report::{
    write_candidate_artifact_atomic, write_tuning_report_atomic, TuningParameterDelta,
    TuningReport, TuningReportError, TuningReportProvenance, TUNING_REPORT_IDENTIFIER,
    TUNING_REPORT_SCHEMA_VERSION,
};

const FNV_OFFSET: u64 = 0xcbf2_9ce4_8422_2325;
const FNV_PRIME: u64 = 0x0000_0100_0000_01b3;

/// Parses a strict self-play dataset and constructs training and validation loss partitions.
pub fn loss_dataset_from_self_play_text(
    text: &str,
) -> Result<LossDataset, SelfPlayLossDatasetError> {
    let dataset = SelfPlayDataset::from_text(text)
        .map_err(|error| SelfPlayLossDatasetError::SelfPlayDataset(error.to_string()))?;
    loss_dataset_from_self_play_dataset(&dataset)
}

/// Parses a strict Task 20 dataset and returns both loss rows and canonical source provenance.
pub fn loss_dataset_and_provenance_from_self_play_text(
    text: &str,
) -> Result<(LossDataset, TrainingDatasetProvenance), SelfPlayLossDatasetError> {
    let dataset = SelfPlayDataset::from_text(text)
        .map_err(|error| SelfPlayLossDatasetError::SelfPlayDataset(error.to_string()))?;
    let loss_dataset = loss_dataset_from_self_play_dataset(&dataset)?;
    let provenance = training_dataset_provenance(&dataset, &loss_dataset)?;
    Ok((loss_dataset, provenance))
}

/// Constructs loss inputs from an already validated self-play dataset.
///
/// Ineligible opening and unfinished-game rows are omitted. The held-out test
/// split is not exposed to calibration or optimizer loss. Exact duplicate
/// occurrence counts remain weights in the mean-squared objective.
pub fn loss_dataset_from_self_play_dataset(
    dataset: &SelfPlayDataset,
) -> Result<LossDataset, SelfPlayLossDatasetError> {
    dataset
        .validate()
        .map_err(|error| SelfPlayLossDatasetError::SelfPlayDataset(error.to_string()))?;

    let mut training = Vec::new();
    let mut validation = Vec::new();
    for record in dataset.positions() {
        if !record.eligible() || record.split() == DatasetSplit::Test {
            continue;
        }
        let outcome = outcome_for_side(record.outcome(), record.side_to_move()).ok_or(
            SelfPlayLossDatasetError::UnfinishedEligiblePosition {
                game_id: record.game_id(),
                ply: record.ply(),
            },
        )?;
        let position = Position::from_fen(record.fen()).map_err(|error| {
            SelfPlayLossDatasetError::Position {
                game_id: record.game_id(),
                ply: record.ply(),
                message: error.to_string(),
            }
        })?;
        let loss_position = LossPosition::new(position, outcome, record.occurrences())
            .map_err(SelfPlayLossDatasetError::LossPipeline)?;
        match record.split() {
            DatasetSplit::Train => training.push(loss_position),
            DatasetSplit::Validation => validation.push(loss_position),
            DatasetSplit::Test => unreachable!("test rows were excluded before conversion"),
        }
    }
    LossDataset::new(training, validation).map_err(SelfPlayLossDatasetError::LossPipeline)
}

/// Computes canonical Task 20 provenance for a validated tuning loss dataset.
pub fn training_dataset_provenance(
    dataset: &SelfPlayDataset,
    loss_dataset: &LossDataset,
) -> Result<TrainingDatasetProvenance, SelfPlayLossDatasetError> {
    dataset
        .validate()
        .map_err(|error| SelfPlayLossDatasetError::SelfPlayDataset(error.to_string()))?;
    let checksum = hash_bytes(FNV_OFFSET, dataset.to_text().as_bytes());
    if checksum == 0 {
        return Err(SelfPlayLossDatasetError::SelfPlayDataset(
            "canonical self-play dataset checksum must be non-zero".to_owned(),
        ));
    }
    Ok(TrainingDatasetProvenance::new(
        SELF_PLAY_DATASET_SCHEMA_VERSION,
        checksum,
        loss_dataset.training_occurrences(),
        loss_dataset.validation_occurrences(),
    ))
}

/// Failure while parsing or adapting a self-play dataset for tuning loss.
#[derive(Clone, Debug, PartialEq)]
pub enum SelfPlayLossDatasetError {
    /// The strict Task 20 dataset parser or validator rejected the input.
    SelfPlayDataset(String),
    /// A retained canonical FEN could not be reconstructed.
    Position {
        /// Source game identifier.
        game_id: u32,
        /// Source ply.
        ply: u32,
        /// Position parser diagnostic.
        message: String,
    },
    /// An unfinished result was incorrectly marked eligible upstream.
    UnfinishedEligiblePosition {
        /// Source game identifier.
        game_id: u32,
        /// Source ply.
        ply: u32,
    },
    /// Core loss-dataset validation failed.
    LossPipeline(LossPipelineError),
}

impl fmt::Display for SelfPlayLossDatasetError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::SelfPlayDataset(message) => {
                write!(formatter, "invalid self-play loss dataset: {message}")
            }
            Self::Position {
                game_id,
                ply,
                message,
            } => write!(
                formatter,
                "invalid loss position for game {game_id} ply {ply}: {message}"
            ),
            Self::UnfinishedEligiblePosition { game_id, ply } => write!(
                formatter,
                "unfinished game {game_id} ply {ply} was marked eligible for loss"
            ),
            Self::LossPipeline(error) => write!(formatter, "invalid loss partitions: {error}"),
        }
    }
}

impl std::error::Error for SelfPlayLossDatasetError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            Self::LossPipeline(error) => Some(error),
            _ => None,
        }
    }
}

fn outcome_for_side(outcome: SelfPlayResult, side_to_move: Color) -> Option<OutcomeTarget> {
    match outcome {
        SelfPlayResult::WhiteWin => Some(if side_to_move == Color::White {
            OutcomeTarget::Win
        } else {
            OutcomeTarget::Loss
        }),
        SelfPlayResult::BlackWin => Some(if side_to_move == Color::Black {
            OutcomeTarget::Win
        } else {
            OutcomeTarget::Loss
        }),
        SelfPlayResult::Draw => Some(OutcomeTarget::Draw),
        SelfPlayResult::Unfinished => None,
    }
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
    use chess_core::Color;
    use chess_tune::OutcomeTarget;

    use super::{loss_dataset_from_self_play_text, outcome_for_side, SelfPlayLossDatasetError};
    use crate::self_play::SelfPlayResult;

    #[test]
    fn completed_results_map_to_the_side_to_move() {
        assert_eq!(
            outcome_for_side(SelfPlayResult::WhiteWin, Color::White),
            Some(OutcomeTarget::Win)
        );
        assert_eq!(
            outcome_for_side(SelfPlayResult::WhiteWin, Color::Black),
            Some(OutcomeTarget::Loss)
        );
        assert_eq!(
            outcome_for_side(SelfPlayResult::BlackWin, Color::Black),
            Some(OutcomeTarget::Win)
        );
        assert_eq!(
            outcome_for_side(SelfPlayResult::BlackWin, Color::White),
            Some(OutcomeTarget::Loss)
        );
        assert_eq!(
            outcome_for_side(SelfPlayResult::Draw, Color::White),
            Some(OutcomeTarget::Draw)
        );
        assert_eq!(
            outcome_for_side(SelfPlayResult::Unfinished, Color::White),
            None
        );
    }

    #[test]
    fn malformed_self_play_text_fails_before_loss_construction() {
        assert!(matches!(
            loss_dataset_from_self_play_text("not a self-play dataset"),
            Err(SelfPlayLossDatasetError::SelfPlayDataset(_))
        ));
    }
}
