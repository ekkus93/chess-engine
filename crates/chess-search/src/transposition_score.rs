use core::fmt;

use crate::{
    transposition::TranspositionScore, Score, MAX_EVALUATION, MAX_MATE_PLY,
};

/// Failure to convert between root-relative search scores and TT storage scores.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum TranspositionScoreConversionError {
    /// The requested search ply exceeds the engine's supported mate-distance domain.
    UnsupportedPly {
        /// Requested root-relative search ply.
        ply: u16,
        /// Largest supported search ply.
        maximum: u16,
    },
    /// Normalizing the supplied search score would leave the supported score domain.
    NormalizationOutOfRange {
        /// Root-relative score supplied by search.
        score: Score,
        /// Ply at which the score would be stored.
        ply: u16,
    },
    /// Denormalizing the stored score would leave the supported score domain.
    DenormalizationOutOfRange {
        /// Position-relative score retained in storage.
        normalized_score: Score,
        /// Ply at which the score would be reused.
        ply: u16,
    },
}

impl fmt::Display for TranspositionScoreConversionError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::UnsupportedPly { ply, maximum } => write!(
                formatter,
                "transposition-score ply {ply} exceeds supported maximum {maximum}"
            ),
            Self::NormalizationOutOfRange { score, ply } => write!(
                formatter,
                "normalizing search score {score} at ply {ply} leaves the supported score domain"
            ),
            Self::DenormalizationOutOfRange {
                normalized_score,
                ply,
            } => write!(
                formatter,
                "denormalizing stored score {normalized_score} at ply {ply} leaves the supported score domain"
            ),
        }
    }
}

impl std::error::Error for TranspositionScoreConversionError {}

impl TranspositionScore {
    /// Converts a root-relative search score into a position-relative TT score.
    ///
    /// Winning mate scores add `ply`; losing mate scores subtract `ply`. This
    /// removes the distance already travelled from the search root. Ordinary
    /// evaluation scores, including both evaluation boundaries, are preserved
    /// exactly.
    pub fn normalize(
        score: Score,
        ply: u16,
    ) -> Result<Self, TranspositionScoreConversionError> {
        validate_ply(ply)?;
        let centipawns = score.centipawns();
        let adjusted = if centipawns > MAX_EVALUATION {
            centipawns + i32::from(ply)
        } else if centipawns < -MAX_EVALUATION {
            centipawns - i32::from(ply)
        } else {
            centipawns
        };
        let normalized = Score::from_raw(adjusted).ok_or(
            TranspositionScoreConversionError::NormalizationOutOfRange { score, ply },
        )?;
        Ok(Self::from_normalized(normalized))
    }

    /// Converts a position-relative TT score into a root-relative search score.
    ///
    /// Winning mate scores subtract `ply`; losing mate scores add `ply`. This
    /// restores the distance from the current search root to the probed node.
    /// Ordinary evaluation scores are preserved exactly.
    pub fn denormalize(
        self,
        ply: u16,
    ) -> Result<Score, TranspositionScoreConversionError> {
        validate_ply(ply)?;
        let normalized_score = self.normalized();
        let centipawns = normalized_score.centipawns();
        let adjusted = if centipawns > MAX_EVALUATION {
            centipawns - i32::from(ply)
        } else if centipawns < -MAX_EVALUATION {
            centipawns + i32::from(ply)
        } else {
            centipawns
        };
        Score::from_raw(adjusted).ok_or(
            TranspositionScoreConversionError::DenormalizationOutOfRange {
                normalized_score,
                ply,
            },
        )
    }
}

fn validate_ply(ply: u16) -> Result<(), TranspositionScoreConversionError> {
    if ply > MAX_MATE_PLY {
        Err(TranspositionScoreConversionError::UnsupportedPly {
            ply,
            maximum: MAX_MATE_PLY,
        })
    } else {
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use super::TranspositionScoreConversionError;
    use crate::{
        Score, TranspositionScore, MATE_SCORE, MAX_EVALUATION, MAX_MATE_PLY,
    };

    #[test]
    fn ordinary_evaluations_are_preserved_exactly_at_every_supported_ply() {
        for centipawns in [
            -MAX_EVALUATION,
            -417,
            0,
            892,
            MAX_EVALUATION,
        ] {
            let score = Score::from_evaluation(centipawns);
            let stored = TranspositionScore::normalize(score, MAX_MATE_PLY)
                .expect("evaluation normalization succeeds");

            assert_eq!(stored.normalized(), score);
            assert_eq!(stored.denormalize(0), Ok(score));
            assert_eq!(stored.denormalize(MAX_MATE_PLY), Ok(score));
        }
    }

    #[test]
    fn winning_mate_entry_round_trips_when_reached_at_different_plies() {
        let first_ply = 7;
        let second_ply = 19;
        let node_distance = 12;
        let first_score = Score::mate_in(first_ply + node_distance).expect("mate score");
        let second_score = Score::mate_in(second_ply + node_distance).expect("mate score");

        let stored = TranspositionScore::normalize(first_score, first_ply)
            .expect("winning mate normalizes");

        assert_eq!(stored.normalized().centipawns(), MATE_SCORE - i32::from(node_distance));
        assert_eq!(
            TranspositionScore::normalize(second_score, second_ply),
            Ok(stored)
        );
        assert_eq!(stored.denormalize(first_ply), Ok(first_score));
        assert_eq!(stored.denormalize(second_ply), Ok(second_score));
    }

    #[test]
    fn losing_mate_entry_round_trips_when_reached_at_different_plies() {
        let first_ply = 5;
        let second_ply = 23;
        let node_distance = 9;
        let first_score = Score::mated_in(first_ply + node_distance).expect("mate score");
        let second_score = Score::mated_in(second_ply + node_distance).expect("mate score");

        let stored = TranspositionScore::normalize(first_score, first_ply)
            .expect("losing mate normalizes");

        assert_eq!(stored.normalized().centipawns(), -MATE_SCORE + i32::from(node_distance));
        assert_eq!(
            TranspositionScore::normalize(second_score, second_ply),
            Ok(stored)
        );
        assert_eq!(stored.denormalize(first_ply), Ok(first_score));
        assert_eq!(stored.denormalize(second_ply), Ok(second_score));
    }

    #[test]
    fn maximum_supported_ply_reaches_both_immediate_mate_boundaries() {
        let winning = Score::mate_in(MAX_MATE_PLY).expect("maximum mate distance");
        let losing = Score::mated_in(MAX_MATE_PLY).expect("maximum mate distance");
        let stored_winning = TranspositionScore::normalize(winning, MAX_MATE_PLY)
            .expect("winning boundary normalizes");
        let stored_losing = TranspositionScore::normalize(losing, MAX_MATE_PLY)
            .expect("losing boundary normalizes");

        assert_eq!(stored_winning.normalized().centipawns(), MATE_SCORE);
        assert_eq!(stored_losing.normalized().centipawns(), -MATE_SCORE);
        assert_eq!(stored_winning.denormalize(MAX_MATE_PLY), Ok(winning));
        assert_eq!(stored_losing.denormalize(MAX_MATE_PLY), Ok(losing));
    }

    #[test]
    fn inconsistent_root_relative_mates_fail_before_storage() {
        let immediate_win = Score::mate_in(0).expect("immediate mate boundary");
        let immediate_loss = Score::mated_in(0).expect("immediate mate boundary");

        assert_eq!(
            TranspositionScore::normalize(immediate_win, 1),
            Err(TranspositionScoreConversionError::NormalizationOutOfRange {
                score: immediate_win,
                ply: 1,
            })
        );
        assert_eq!(
            TranspositionScore::normalize(immediate_loss, 1),
            Err(TranspositionScoreConversionError::NormalizationOutOfRange {
                score: immediate_loss,
                ply: 1,
            })
        );
    }

    #[test]
    fn unsupported_ply_is_rejected_for_both_conversion_directions() {
        let unsupported = MAX_MATE_PLY + 1;
        let score = Score::from_evaluation(17);
        let stored = TranspositionScore::normalize(score, 0).expect("root score normalizes");
        let expected = TranspositionScoreConversionError::UnsupportedPly {
            ply: unsupported,
            maximum: MAX_MATE_PLY,
        };

        assert_eq!(TranspositionScore::normalize(score, unsupported), Err(expected));
        assert_eq!(stored.denormalize(unsupported), Err(expected));
        assert_eq!(
            expected.to_string(),
            format!(
                "transposition-score ply {unsupported} exceeds supported maximum {MAX_MATE_PLY}"
            )
        );
    }
}
