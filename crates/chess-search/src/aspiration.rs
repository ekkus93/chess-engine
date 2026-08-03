use crate::{Score, TranspositionHashFull, TranspositionTableDiagnostics};

/// Default half-width used for score-centered aspiration searches.
pub const DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS: i32 = 50;

/// Classification of one root-window search attempt.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum AspirationWindowOutcome {
    /// The reported score lies strictly inside the requested window, or the
    /// request used the complete supported score domain.
    Exact,
    /// The reported score is an upper bound at or below alpha.
    FailLow,
    /// The reported score is a lower bound at or above beta.
    FailHigh,
}

/// Immutable diagnostics for one root-window attempt.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct AspirationWindowAttempt {
    pub(crate) alpha: Score,
    pub(crate) beta: Score,
    pub(crate) outcome: AspirationWindowOutcome,
    pub(crate) reported_score: Score,
    pub(crate) nodes: u64,
    pub(crate) transposition_diagnostics: TranspositionTableDiagnostics,
    pub(crate) hash_full: TranspositionHashFull,
    pub(crate) transposition_generation: u8,
}

impl AspirationWindowAttempt {
    /// Returns the alpha edge supplied to this attempt.
    #[must_use]
    pub const fn alpha(self) -> Score {
        self.alpha
    }

    /// Returns the beta edge supplied to this attempt.
    #[must_use]
    pub const fn beta(self) -> Score {
        self.beta
    }

    /// Returns whether the attempt was exact, fail-low, or fail-high.
    #[must_use]
    pub const fn outcome(self) -> AspirationWindowOutcome {
        self.outcome
    }

    /// Returns the fail-soft score reported by the attempt.
    ///
    /// This value is a bound unless [`Self::outcome`] is
    /// [`AspirationWindowOutcome::Exact`].
    #[must_use]
    pub const fn reported_score(self) -> Score {
        self.reported_score
    }

    /// Returns an exact score only when the attempt completed in-window.
    #[must_use]
    pub const fn exact_score(self) -> Option<Score> {
        match self.outcome {
            AspirationWindowOutcome::Exact => Some(self.reported_score),
            AspirationWindowOutcome::FailLow | AspirationWindowOutcome::FailHigh => None,
        }
    }

    /// Returns nodes visited by this attempt only.
    #[must_use]
    pub const fn nodes(self) -> u64 {
        self.nodes
    }

    /// Returns transposition counters produced by this attempt only.
    #[must_use]
    pub const fn transposition_diagnostics(self) -> TranspositionTableDiagnostics {
        self.transposition_diagnostics
    }

    /// Returns the bounded hash-full sample after this attempt.
    #[must_use]
    pub const fn hash_full(self) -> TranspositionHashFull {
        self.hash_full
    }

    /// Returns the generation shared by every attempt in the iteration.
    #[must_use]
    pub const fn transposition_generation(self) -> u8 {
        self.transposition_generation
    }

    /// Returns whether this attempt used the complete supported score domain.
    #[must_use]
    pub fn is_full_window(self) -> bool {
        self.alpha == Score::mated_in(0).expect("zero-ply mate score is supported")
            && self.beta == Score::mate_in(0).expect("zero-ply mate score is supported")
    }
}

/// Bounded aspiration diagnostics for one completed depth.
///
/// An iteration always has one initial attempt and at most one complete-window
/// retry. The optional center is the exact score from the prior completed
/// depth. Depth one has no prior center and therefore starts full-window.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct AspirationWindowDiagnostics {
    center: Option<Score>,
    initial_attempt: AspirationWindowAttempt,
    full_window_retry: Option<AspirationWindowAttempt>,
}

impl AspirationWindowDiagnostics {
    pub(crate) const fn new(
        center: Option<Score>,
        initial_attempt: AspirationWindowAttempt,
        full_window_retry: Option<AspirationWindowAttempt>,
    ) -> Self {
        Self {
            center,
            initial_attempt,
            full_window_retry,
        }
    }

    /// Returns the prior exact score used as the initial center.
    #[must_use]
    pub const fn center(self) -> Option<Score> {
        self.center
    }

    /// Returns the first attempt for this depth.
    #[must_use]
    pub const fn initial_attempt(self) -> AspirationWindowAttempt {
        self.initial_attempt
    }

    /// Returns the complete-window retry after fail-low or fail-high.
    #[must_use]
    pub const fn full_window_retry(self) -> Option<AspirationWindowAttempt> {
        self.full_window_retry
    }

    /// Returns zero or one.
    #[must_use]
    pub const fn retry_count(self) -> u8 {
        if self.full_window_retry.is_some() {
            1
        } else {
            0
        }
    }

    /// Returns the final exact attempt.
    #[must_use]
    pub const fn final_attempt(self) -> AspirationWindowAttempt {
        match self.full_window_retry {
            Some(retry) => retry,
            None => self.initial_attempt,
        }
    }
}
