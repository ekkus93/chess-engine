use core::fmt;

use chess_core::Move;

use super::{TranspositionBound, TranspositionEntry, TranspositionTable};
use crate::{Score, TranspositionScoreConversionError};

/// Whether a verified transposition entry may contribute a cached score.
///
/// Repetition outcomes depend on the path used to reach a position rather than
/// the Zobrist position key alone. Callers must therefore select
/// [`Self::SuppressedForRepetition`] whenever the current node's repetition
/// history can affect its value. A verified best move remains safe as an
/// ordering hint because it does not bypass legal move generation or search.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum TranspositionScoreReuse {
    /// The current node is path-independent for transposition-score reuse.
    Allowed,
    /// Cached scores are suppressed because repetition history may affect value.
    SuppressedForRepetition,
}

/// Complete information required to probe one transposition-table position.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TranspositionProbeRequest {
    verification_key: u64,
    required_depth: u16,
    ply: u16,
    alpha: Score,
    beta: Score,
    score_reuse: TranspositionScoreReuse,
}

impl TranspositionProbeRequest {
    /// Creates a probe request for one alpha-beta node.
    #[must_use]
    pub const fn new(
        verification_key: u64,
        required_depth: u16,
        ply: u16,
        alpha: Score,
        beta: Score,
        score_reuse: TranspositionScoreReuse,
    ) -> Self {
        Self {
            verification_key,
            required_depth,
            ply,
            alpha,
            beta,
            score_reuse,
        }
    }

    /// Returns the complete position-verification key.
    #[must_use]
    pub const fn verification_key(self) -> u64 {
        self.verification_key
    }

    /// Returns the minimum stored depth required for score reuse.
    #[must_use]
    pub const fn required_depth(self) -> u16 {
        self.required_depth
    }

    /// Returns the current root-relative search ply.
    #[must_use]
    pub const fn ply(self) -> u16 {
        self.ply
    }

    /// Returns the current alpha bound.
    #[must_use]
    pub const fn alpha(self) -> Score {
        self.alpha
    }

    /// Returns the current beta bound.
    #[must_use]
    pub const fn beta(self) -> Score {
        self.beta
    }

    /// Returns whether cached score reuse is safe for this node.
    #[must_use]
    pub const fn score_reuse(self) -> TranspositionScoreReuse {
        self.score_reuse
    }
}

/// A score that a verified transposition probe may safely reuse.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum TranspositionProbeScore {
    /// Exact minimax value for at least the requested depth.
    Exact(Score),
    /// Fail-high lower bound meeting or exceeding beta.
    LowerBoundCutoff(Score),
    /// Fail-low upper bound meeting or falling below alpha.
    UpperBoundCutoff(Score),
}

impl TranspositionProbeScore {
    /// Returns the denormalized root-relative score.
    #[must_use]
    pub const fn score(self) -> Score {
        match self {
            Self::Exact(score) | Self::LowerBoundCutoff(score) | Self::UpperBoundCutoff(score) => {
                score
            }
        }
    }
}

/// Result of finding a complete-key match in the selected collision cluster.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct TranspositionProbeResult {
    best_move: Option<Move>,
    score: Option<TranspositionProbeScore>,
}

impl TranspositionProbeResult {
    const fn new(best_move: Option<Move>, score: Option<TranspositionProbeScore>) -> Self {
        Self { best_move, score }
    }

    /// Returns the verified move-ordering hint, even when score reuse is unsafe.
    #[must_use]
    pub const fn best_move(self) -> Option<Move> {
        self.best_move
    }

    /// Returns an exact value or valid alpha-beta cutoff, when available.
    #[must_use]
    pub const fn score(self) -> Option<TranspositionProbeScore> {
        self.score
    }
}

/// Failure to evaluate a transposition probe safely.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum TranspositionProbeError {
    /// Alpha must be strictly less than beta.
    InvalidWindow {
        /// Supplied alpha bound.
        alpha: Score,
        /// Supplied beta bound.
        beta: Score,
    },
    /// The stored normalized score could not be restored at the requested ply.
    ScoreConversion(TranspositionScoreConversionError),
}

impl fmt::Display for TranspositionProbeError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InvalidWindow { alpha, beta } => write!(
                formatter,
                "transposition probe requires alpha below beta, received {alpha} and {beta}"
            ),
            Self::ScoreConversion(error) => fmt::Display::fmt(error, formatter),
        }
    }
}

impl std::error::Error for TranspositionProbeError {}

impl From<TranspositionScoreConversionError> for TranspositionProbeError {
    fn from(error: TranspositionScoreConversionError) -> Self {
        Self::ScoreConversion(error)
    }
}

impl TranspositionTable {
    /// Probes the selected cluster and returns only a complete-key match.
    ///
    /// A verified best move is returned regardless of stored depth. Cached
    /// scores require sufficient depth and [`TranspositionScoreReuse::Allowed`].
    /// Exact values are returned directly; lower bounds cut off only at beta and
    /// upper bounds cut off only at alpha. Stored mate scores are denormalized at
    /// the current probe ply before any comparison or return.
    pub fn probe(
        &mut self,
        request: TranspositionProbeRequest,
    ) -> Result<Option<TranspositionProbeResult>, TranspositionProbeError> {
        if request.alpha() >= request.beta() {
            return Err(TranspositionProbeError::InvalidWindow {
                alpha: request.alpha(),
                beta: request.beta(),
            });
        }

        self.diagnostics.record_probe();
        let cluster = &self.clusters[self.cluster_index(request.verification_key())];
        let Some(entry) = cluster
            .entries
            .iter()
            .flatten()
            .copied()
            .find(|entry| entry.verification_key() == request.verification_key())
        else {
            return Ok(None);
        };

        self.diagnostics.record_hit();
        let score = reusable_score(entry, request)?;
        match score {
            Some(TranspositionProbeScore::Exact(_)) => self.diagnostics.record_exact_hit(),
            Some(TranspositionProbeScore::LowerBoundCutoff(_)) => {
                self.diagnostics.record_lower_bound_cutoff();
            }
            Some(TranspositionProbeScore::UpperBoundCutoff(_)) => {
                self.diagnostics.record_upper_bound_cutoff();
            }
            None => {}
        }
        Ok(Some(TranspositionProbeResult::new(
            entry.best_move(),
            score,
        )))
    }

    #[cfg(test)]
    fn install_probe_fixture(&mut self, slot: usize, entry: TranspositionEntry) {
        let cluster_index = self.cluster_index(entry.verification_key());
        self.clusters[cluster_index].entries[slot] = Some(entry);
    }
}

fn reusable_score(
    entry: TranspositionEntry,
    request: TranspositionProbeRequest,
) -> Result<Option<TranspositionProbeScore>, TranspositionProbeError> {
    if request.score_reuse() == TranspositionScoreReuse::SuppressedForRepetition
        || entry.depth() < request.required_depth()
    {
        return Ok(None);
    }

    let score = entry.normalized_score().denormalize(request.ply())?;
    let reusable = match entry.bound() {
        TranspositionBound::Exact => Some(TranspositionProbeScore::Exact(score)),
        TranspositionBound::Lower if score >= request.beta() => {
            Some(TranspositionProbeScore::LowerBoundCutoff(score))
        }
        TranspositionBound::Upper if score <= request.alpha() => {
            Some(TranspositionProbeScore::UpperBoundCutoff(score))
        }
        TranspositionBound::Lower | TranspositionBound::Upper => None,
    };
    Ok(reusable)
}

#[cfg(test)]
mod tests {
    use chess_core::{Move, MoveKind, Square};

    use super::{
        TranspositionProbeError, TranspositionProbeRequest, TranspositionProbeScore,
        TranspositionScoreReuse,
    };
    use crate::{
        Score, TranspositionBound, TranspositionEntry, TranspositionScore,
        TranspositionScoreConversionError, TranspositionTable, MAX_MATE_PLY,
    };

    const KEY: u64 = 0x1234_5678_9abc_def0;

    fn square(text: &str) -> Square {
        text.parse().expect("probe-test square is valid")
    }

    fn best_move() -> Move {
        Move::new(square("g1"), square("f3"), MoveKind::Quiet)
    }

    fn entry(
        verification_key: u64,
        depth: u16,
        bound: TranspositionBound,
        score: Score,
    ) -> TranspositionEntry {
        TranspositionEntry::new(
            verification_key,
            depth,
            bound,
            TranspositionScore::normalize(score, 0).expect("fixture score normalizes"),
            Some(best_move()),
            0,
        )
    }

    fn request(
        verification_key: u64,
        required_depth: u16,
        alpha: i32,
        beta: i32,
        score_reuse: TranspositionScoreReuse,
    ) -> TranspositionProbeRequest {
        TranspositionProbeRequest::new(
            verification_key,
            required_depth,
            0,
            Score::from_evaluation(alpha),
            Score::from_evaluation(beta),
            score_reuse,
        )
    }

    #[test]
    fn complete_key_verification_rejects_cluster_collisions() {
        let mut table = TranspositionTable::new(1).expect("table allocates");
        let collision = KEY + table.cluster_count() as u64;
        table.install_probe_fixture(
            0,
            entry(
                collision,
                12,
                TranspositionBound::Exact,
                Score::from_evaluation(90),
            ),
        );

        assert_eq!(
            table.probe(request(KEY, 1, -100, 100, TranspositionScoreReuse::Allowed,)),
            Ok(None)
        );

        table.install_probe_fixture(
            1,
            entry(
                KEY,
                12,
                TranspositionBound::Exact,
                Score::from_evaluation(35),
            ),
        );
        assert!(table
            .probe(request(KEY, 1, -100, 100, TranspositionScoreReuse::Allowed,))
            .expect("probe succeeds")
            .is_some());
    }

    #[test]
    fn insufficient_depth_preserves_best_move_without_reusing_score() {
        let mut table = TranspositionTable::new(1).expect("table allocates");
        table.install_probe_fixture(
            0,
            entry(
                KEY,
                5,
                TranspositionBound::Exact,
                Score::from_evaluation(42),
            ),
        );

        let result = table
            .probe(request(KEY, 6, -100, 100, TranspositionScoreReuse::Allowed))
            .expect("probe succeeds")
            .expect("verified entry");

        assert_eq!(result.best_move(), Some(best_move()));
        assert_eq!(result.score(), None);
    }

    #[test]
    fn exact_hit_denormalizes_mate_score_at_the_probe_ply() {
        let mut table = TranspositionTable::new(1).expect("table allocates");
        let storage_ply = 7;
        let probe_ply = 19;
        let node_distance = 11;
        let stored_score = Score::mate_in(storage_ply + node_distance).expect("mate score");
        let expected = Score::mate_in(probe_ply + node_distance).expect("mate score");
        let normalized =
            TranspositionScore::normalize(stored_score, storage_ply).expect("mate normalizes");
        table.install_probe_fixture(
            0,
            TranspositionEntry::new(
                KEY,
                8,
                TranspositionBound::Exact,
                normalized,
                Some(best_move()),
                0,
            ),
        );

        let request = TranspositionProbeRequest::new(
            KEY,
            8,
            probe_ply,
            Score::from_evaluation(-100),
            Score::from_evaluation(100),
            TranspositionScoreReuse::Allowed,
        );
        let result = table
            .probe(request)
            .expect("probe succeeds")
            .expect("verified entry");

        assert_eq!(
            result.score(),
            Some(TranspositionProbeScore::Exact(expected))
        );
    }

    #[test]
    fn lower_bound_cuts_off_only_when_denormalized_score_reaches_beta() {
        let mut table = TranspositionTable::new(1).expect("table allocates");
        table.install_probe_fixture(
            0,
            entry(
                KEY,
                9,
                TranspositionBound::Lower,
                Score::from_evaluation(80),
            ),
        );

        let cutoff = table
            .probe(request(KEY, 9, -50, 50, TranspositionScoreReuse::Allowed))
            .expect("probe succeeds")
            .expect("verified entry");
        assert_eq!(
            cutoff.score(),
            Some(TranspositionProbeScore::LowerBoundCutoff(
                Score::from_evaluation(80)
            ))
        );

        let no_cutoff = table
            .probe(request(KEY, 9, -50, 100, TranspositionScoreReuse::Allowed))
            .expect("probe succeeds")
            .expect("verified entry");
        assert_eq!(no_cutoff.best_move(), Some(best_move()));
        assert_eq!(no_cutoff.score(), None);
    }

    #[test]
    fn upper_bound_cuts_off_only_when_denormalized_score_reaches_alpha() {
        let mut table = TranspositionTable::new(1).expect("table allocates");
        table.install_probe_fixture(
            0,
            entry(
                KEY,
                9,
                TranspositionBound::Upper,
                Score::from_evaluation(-80),
            ),
        );

        let cutoff = table
            .probe(request(KEY, 9, -50, 50, TranspositionScoreReuse::Allowed))
            .expect("probe succeeds")
            .expect("verified entry");
        assert_eq!(
            cutoff.score(),
            Some(TranspositionProbeScore::UpperBoundCutoff(
                Score::from_evaluation(-80)
            ))
        );

        let no_cutoff = table
            .probe(request(KEY, 9, -100, 50, TranspositionScoreReuse::Allowed))
            .expect("probe succeeds")
            .expect("verified entry");
        assert_eq!(no_cutoff.best_move(), Some(best_move()));
        assert_eq!(no_cutoff.score(), None);
    }

    #[test]
    fn repetition_sensitive_nodes_suppress_scores_but_keep_ordering_move() {
        let mut table = TranspositionTable::new(1).expect("table allocates");
        table.install_probe_fixture(
            0,
            entry(
                KEY,
                20,
                TranspositionBound::Exact,
                Score::from_evaluation(63),
            ),
        );

        let result = table
            .probe(request(
                KEY,
                1,
                -100,
                100,
                TranspositionScoreReuse::SuppressedForRepetition,
            ))
            .expect("probe succeeds")
            .expect("verified entry");

        assert_eq!(result.best_move(), Some(best_move()));
        assert_eq!(result.score(), None);
    }

    #[test]
    fn invalid_windows_fail_before_lookup() {
        let mut table = TranspositionTable::new(1).expect("table allocates");
        let alpha = Score::from_evaluation(25);
        let beta = Score::from_evaluation(25);
        let request = TranspositionProbeRequest::new(
            KEY,
            1,
            0,
            alpha,
            beta,
            TranspositionScoreReuse::Allowed,
        );

        assert_eq!(
            table.probe(request),
            Err(TranspositionProbeError::InvalidWindow { alpha, beta })
        );
    }

    #[test]
    fn score_conversion_failures_are_preserved() {
        let mut table = TranspositionTable::new(1).expect("table allocates");
        table.install_probe_fixture(
            0,
            entry(
                KEY,
                4,
                TranspositionBound::Exact,
                Score::from_evaluation(12),
            ),
        );
        let unsupported = MAX_MATE_PLY + 1;
        let request = TranspositionProbeRequest::new(
            KEY,
            1,
            unsupported,
            Score::from_evaluation(-100),
            Score::from_evaluation(100),
            TranspositionScoreReuse::Allowed,
        );

        assert_eq!(
            table.probe(request),
            Err(TranspositionProbeError::ScoreConversion(
                TranspositionScoreConversionError::UnsupportedPly {
                    ply: unsupported,
                    maximum: MAX_MATE_PLY,
                }
            ))
        );
    }
}
