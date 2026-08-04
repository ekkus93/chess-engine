//! Adapter from validated Task 20 self-play datasets to `chess-tune` loss inputs.

use core::fmt;

use chess_core::{Color, Position};
use chess_tune::{LossDataset, LossPipelineError, LossPosition, OutcomeTarget};

use crate::self_play::{DatasetSplit, SelfPlayDataset, SelfPlayResult};

/// Parses a strict self-play dataset and constructs training and validation loss partitions.
pub fn loss_dataset_from_self_play_text(
    text: &str,
) -> Result<LossDataset, SelfPlayLossDatasetError> {
    let dataset = SelfPlayDataset::from_text(text)
        .map_err(|error| SelfPlayLossDatasetError::SelfPlayDataset(error.to_string()))?;
    loss_dataset_from_self_play_dataset(&dataset)
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
