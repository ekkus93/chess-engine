use core::{fmt, ops::Neg};

/// Centipawn value reserved for an immediate checkmate score.
pub const MATE_SCORE: i32 = 30_000;
/// Largest magnitude produced by the static evaluator.
pub const MAX_EVALUATION: i32 = 20_000;
/// Largest supported mate distance in plies.
pub const MAX_MATE_PLY: u16 = 1_024;

/// A signed engine score measured in centipawns.
///
/// Positive values favor the side to move. Static evaluation is clamped to
/// [`MAX_EVALUATION`], leaving a distinct band for mate-distance scores.
#[derive(Clone, Copy, Debug, Default, Eq, Hash, Ord, PartialEq, PartialOrd)]
#[repr(transparent)]
pub struct Score(i32);

impl Score {
    /// A neutral score.
    pub const ZERO: Self = Self(0);

    /// Creates a static-evaluation score and clamps it outside the mate band.
    #[must_use]
    pub const fn from_evaluation(centipawns: i32) -> Self {
        if centipawns > MAX_EVALUATION {
            Self(MAX_EVALUATION)
        } else if centipawns < -MAX_EVALUATION {
            Self(-MAX_EVALUATION)
        } else {
            Self(centipawns)
        }
    }

    /// Creates a score from a raw engine value inside the supported range.
    #[must_use]
    pub const fn from_raw(centipawns: i32) -> Option<Self> {
        if centipawns < -MATE_SCORE || centipawns > MATE_SCORE {
            None
        } else {
            Some(Self(centipawns))
        }
    }

    /// Returns a winning mate score at `plies` from the current node.
    #[must_use]
    pub const fn mate_in(plies: u16) -> Option<Self> {
        if plies > MAX_MATE_PLY {
            None
        } else {
            Some(Self(MATE_SCORE - plies as i32))
        }
    }

    /// Returns a losing mate score at `plies` from the current node.
    #[must_use]
    pub const fn mated_in(plies: u16) -> Option<Self> {
        if plies > MAX_MATE_PLY {
            None
        } else {
            Some(Self(-MATE_SCORE + plies as i32))
        }
    }

    /// Returns the underlying centipawn value.
    #[must_use]
    pub const fn centipawns(self) -> i32 {
        self.0
    }

    /// Returns whether the score occupies the reserved mate band.
    #[must_use]
    pub const fn is_mate(self) -> bool {
        self.0 > MAX_EVALUATION || self.0 < -MAX_EVALUATION
    }
}

impl Neg for Score {
    type Output = Self;

    fn neg(self) -> Self::Output {
        Self(-self.0)
    }
}

impl fmt::Display for Score {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        write!(formatter, "{} cp", self.0)
    }
}

#[cfg(test)]
mod tests {
    use super::{Score, MATE_SCORE, MAX_EVALUATION, MAX_MATE_PLY};

    #[test]
    fn evaluation_scores_stay_outside_the_mate_band() {
        assert_eq!(Score::from_evaluation(123).centipawns(), 123);
        assert_eq!(
            Score::from_evaluation(i32::MAX).centipawns(),
            MAX_EVALUATION
        );
        assert_eq!(
            Score::from_evaluation(i32::MIN).centipawns(),
            -MAX_EVALUATION
        );
        assert!(!Score::from_evaluation(MAX_EVALUATION).is_mate());
    }

    #[test]
    fn mate_scores_encode_distance_and_negate_exactly() {
        let winning = Score::mate_in(7).expect("supported mate distance");
        let losing = Score::mated_in(7).expect("supported mate distance");
        assert_eq!(winning.centipawns(), MATE_SCORE - 7);
        assert_eq!(losing, -winning);
        assert!(winning.is_mate());
        assert_eq!(Score::mate_in(MAX_MATE_PLY + 1), None);
    }

    #[test]
    fn raw_scores_validate_the_supported_domain() {
        assert_eq!(
            Score::from_raw(MATE_SCORE).expect("boundary").centipawns(),
            MATE_SCORE
        );
        assert_eq!(
            Score::from_raw(-MATE_SCORE).expect("boundary").centipawns(),
            -MATE_SCORE
        );
        assert_eq!(Score::from_raw(MATE_SCORE + 1), None);
        assert_eq!(Score::from_raw(-MATE_SCORE - 1), None);
        assert_eq!(Score::ZERO.to_string(), "0 cp");
    }
}
