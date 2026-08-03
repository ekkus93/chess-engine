use core::fmt;

use chess_core::{Move, Position, SearchHistory};

use crate::{
    alpha_beta::{
        alpha_beta_search_window_in_current_generation, prepare_alpha_beta_iteration,
        AlphaBetaRootWindowResult, AlphaBetaSearchError, AlphaBetaSearchResult, AlphaBetaWindow,
        DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES,
    },
    aspiration::{
        AspirationWindowAttempt, AspirationWindowDiagnostics, AspirationWindowOutcome,
        DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS,
    },
    principal_variation::{reconstruct_principal_variation, PrincipalVariationError},
    PrincipalVariation, Score, TranspositionHashFull, TranspositionTable,
    TranspositionTableAllocationError, TranspositionTableDiagnostics, MAX_MATE_PLY,
};

/// One fully completed fixed-depth iteration.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct IterativeDeepeningIteration {
    depth: u16,
    result: AlphaBetaSearchResult,
    nodes: u64,
    principal_variation: PrincipalVariation,
    aspiration_diagnostics: AspirationWindowDiagnostics,
    transposition_diagnostics: TranspositionTableDiagnostics,
    hash_full: TranspositionHashFull,
    transposition_generation: u8,
}

impl IterativeDeepeningIteration {
    /// Returns the completed depth in plies.
    #[must_use]
    pub const fn depth(&self) -> u16 {
        self.depth
    }

    /// Returns the exact result completed at this depth.
    ///
    /// When an aspiration attempt fails, this is the complete-window retry
    /// result. Its node count covers that exact attempt only; [`Self::nodes`]
    /// covers every attempt made for this depth.
    #[must_use]
    pub const fn result(&self) -> AlphaBetaSearchResult {
        self.result
    }

    /// Returns the exact root score from the side-to-move perspective.
    #[must_use]
    pub const fn score(&self) -> Score {
        self.result.score()
    }

    /// Returns the deterministic best move from the exact completed result.
    #[must_use]
    pub const fn best_move(&self) -> Option<Move> {
        self.result.best_move()
    }

    /// Returns the safely reconstructed legal principal variation.
    #[must_use]
    pub const fn principal_variation(&self) -> &PrincipalVariation {
        &self.principal_variation
    }

    /// Returns the opponent reply after the best move, when reconstructed.
    #[must_use]
    pub fn ponder_move(&self) -> Option<Move> {
        self.principal_variation.ponder_move()
    }

    /// Returns nodes visited by all attempts for this depth.
    #[must_use]
    pub const fn nodes(&self) -> u64 {
        self.nodes
    }

    /// Returns aspiration-window and retry diagnostics for this depth.
    #[must_use]
    pub const fn aspiration_diagnostics(&self) -> AspirationWindowDiagnostics {
        self.aspiration_diagnostics
    }

    /// Returns aggregate probe/store counters from every attempt at this depth.
    #[must_use]
    pub const fn transposition_diagnostics(&self) -> TranspositionTableDiagnostics {
        self.transposition_diagnostics
    }

    /// Returns bounded current-generation table occupancy after the final attempt.
    #[must_use]
    pub const fn hash_full(&self) -> TranspositionHashFull {
        self.hash_full
    }

    /// Returns the table generation shared by every attempt at this depth.
    #[must_use]
    pub const fn transposition_generation(&self) -> u8 {
        self.transposition_generation
    }
}

/// Completed depth-by-depth results from one iterative-deepening search.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct IterativeDeepeningSearchResult {
    iterations: Vec<IterativeDeepeningIteration>,
    total_nodes: u64,
}

impl IterativeDeepeningSearchResult {
    /// Returns every completed iteration in ascending depth order.
    #[must_use]
    pub fn iterations(&self) -> &[IterativeDeepeningIteration] {
        &self.iterations
    }

    /// Returns the final completed iteration.
    #[must_use]
    pub fn final_iteration(&self) -> Option<&IterativeDeepeningIteration> {
        self.iterations.last()
    }

    /// Returns the final completed legal principal variation.
    #[must_use]
    pub fn principal_variation(&self) -> Option<&PrincipalVariation> {
        self.final_iteration()
            .map(IterativeDeepeningIteration::principal_variation)
    }

    /// Returns the final completed ponder move, when available.
    #[must_use]
    pub fn ponder_move(&self) -> Option<Move> {
        self.final_iteration()
            .and_then(IterativeDeepeningIteration::ponder_move)
    }

    /// Returns the deepest completed depth, or zero for an internally empty result.
    #[must_use]
    pub fn completed_depth(&self) -> u16 {
        self.final_iteration()
            .map_or(0, IterativeDeepeningIteration::depth)
    }

    /// Returns the checked sum of every attempt at every completed depth.
    #[must_use]
    pub const fn total_nodes(&self) -> u64 {
        self.total_nodes
    }
}

/// A fail-loud iterative-deepening error.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum IterativeDeepeningSearchError {
    /// Iterative deepening requires at least one completed depth.
    ZeroMaximumDepth,
    /// The requested maximum exceeds the supported mate-distance domain.
    MaximumDepthTooLarge {
        /// Requested maximum depth.
        maximum_depth: u16,
        /// Largest supported depth.
        supported: u16,
    },
    /// The default fixed-capacity transposition table could not be allocated.
    TranspositionTableAllocation(TranspositionTableAllocationError),
    /// The bounded iteration-record reservation failed.
    IterationStorageAllocation {
        /// Number of records requested.
        maximum_depth: u16,
    },
    /// One root-window attempt failed.
    IterationFailed {
        /// Depth that failed before producing a completed record.
        depth: u16,
        /// Underlying fixed-depth search error.
        error: AlphaBetaSearchError,
    },
    /// An allegedly complete-window retry did not classify as exact.
    FullWindowDidNotResolveExactly {
        /// Depth whose retry violated the complete-window invariant.
        depth: u16,
        /// Unexpected classification.
        outcome: AspirationWindowOutcome,
    },
    /// Safe principal-variation reconstruction failed after a completed search.
    PrincipalVariationFailed {
        /// Completed depth whose PV could not be reconstructed safely.
        depth: u16,
        /// Underlying bounded reconstruction failure.
        error: PrincipalVariationError,
    },
    /// Summing attempt or iteration node counts exceeded `u64`.
    NodeCountOverflow {
        /// Last depth completed before overflow was detected.
        completed_depth: u16,
    },
}

impl fmt::Display for IterativeDeepeningSearchError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::ZeroMaximumDepth => {
                formatter.write_str("iterative-deepening maximum depth must be at least one")
            }
            Self::MaximumDepthTooLarge {
                maximum_depth,
                supported,
            } => write!(
                formatter,
                "iterative-deepening maximum depth {maximum_depth} exceeds supported maximum {supported}"
            ),
            Self::TranspositionTableAllocation(error) => error.fmt(formatter),
            Self::IterationStorageAllocation { maximum_depth } => write!(
                formatter,
                "failed to reserve {maximum_depth} bounded iterative-deepening records"
            ),
            Self::IterationFailed { depth, error } => {
                write!(formatter, "iterative-deepening depth {depth} failed: {error}")
            }
            Self::FullWindowDidNotResolveExactly { depth, outcome } => write!(
                formatter,
                "iterative-deepening depth {depth} complete-window retry returned {outcome:?}"
            ),
            Self::PrincipalVariationFailed { depth, error } => write!(
                formatter,
                "iterative-deepening depth {depth} principal variation failed: {error}"
            ),
            Self::NodeCountOverflow { completed_depth } => write!(
                formatter,
                "iterative-deepening node total overflowed after completing depth {completed_depth}"
            ),
        }
    }
}

impl std::error::Error for IterativeDeepeningSearchError {}

/// Searches every depth from one through `maximum_depth`.
///
/// Depth one uses the complete score domain. Later depths begin with a bounded
/// aspiration window centered on the prior exact score. Fail-low or fail-high
/// triggers one complete-window retry. Only an exact attempt becomes the
/// completed result.
pub fn iterative_deepening_search(
    position: &mut Position,
    history: &mut SearchHistory,
    maximum_depth: u16,
) -> Result<IterativeDeepeningSearchResult, IterativeDeepeningSearchError> {
    validate_maximum_depth(maximum_depth)?;
    let mut transposition_table = TranspositionTable::new(DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES)
        .map_err(IterativeDeepeningSearchError::TranspositionTableAllocation)?;
    iterative_deepening_search_with_transposition_table(
        position,
        history,
        maximum_depth,
        &mut transposition_table,
    )
}

/// Searches every depth using one caller-owned bounded table.
///
/// The generation advances once per depth, not once per retry. Diagnostic
/// counters reset for each attempt and are retained both per-attempt and as a
/// saturating aggregate for the completed iteration.
pub fn iterative_deepening_search_with_transposition_table(
    position: &mut Position,
    history: &mut SearchHistory,
    maximum_depth: u16,
    transposition_table: &mut TranspositionTable,
) -> Result<IterativeDeepeningSearchResult, IterativeDeepeningSearchError> {
    validate_maximum_depth(maximum_depth)?;

    let mut iterations: Vec<IterativeDeepeningIteration> = Vec::new();
    iterations
        .try_reserve_exact(maximum_depth as usize)
        .map_err(|_| IterativeDeepeningSearchError::IterationStorageAllocation { maximum_depth })?;
    let mut total_nodes = 0_u64;

    for depth in 1..=maximum_depth {
        let center = iterations.last().map(IterativeDeepeningIteration::score);
        let iteration = search_completed_iteration(
            position,
            history,
            depth,
            center,
            DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS,
            transposition_table,
        )?;

        total_nodes = total_nodes.checked_add(iteration.nodes()).ok_or(
            IterativeDeepeningSearchError::NodeCountOverflow {
                completed_depth: depth - 1,
            },
        )?;
        iterations.push(iteration);
    }

    Ok(IterativeDeepeningSearchResult {
        iterations,
        total_nodes,
    })
}

fn search_completed_iteration(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    center: Option<Score>,
    half_width_centipawns: i32,
    transposition_table: &mut TranspositionTable,
) -> Result<IterativeDeepeningIteration, IterativeDeepeningSearchError> {
    prepare_alpha_beta_iteration(position, history, depth, transposition_table)
        .map_err(|error| IterativeDeepeningSearchError::IterationFailed { depth, error })?;

    let initial_window = center.map_or_else(AlphaBetaWindow::full, |score| {
        aspiration_window(score, half_width_centipawns)
    });
    let (initial_result, initial_attempt) = run_attempt(
        position,
        history,
        depth,
        initial_window,
        transposition_table,
    )?;

    let mut nodes = initial_attempt.nodes();
    let mut transposition_diagnostics = initial_attempt.transposition_diagnostics();

    let (result, full_window_retry) = match initial_result.outcome() {
        AspirationWindowOutcome::Exact => (initial_result.result(), None),
        AspirationWindowOutcome::FailLow | AspirationWindowOutcome::FailHigh => {
            let (retry_result, retry_attempt) = run_attempt(
                position,
                history,
                depth,
                AlphaBetaWindow::full(),
                transposition_table,
            )?;
            nodes = nodes.checked_add(retry_attempt.nodes()).ok_or(
                IterativeDeepeningSearchError::NodeCountOverflow {
                    completed_depth: depth - 1,
                },
            )?;
            transposition_diagnostics =
                transposition_diagnostics.saturating_add(retry_attempt.transposition_diagnostics());
            if retry_result.outcome() != AspirationWindowOutcome::Exact {
                return Err(
                    IterativeDeepeningSearchError::FullWindowDidNotResolveExactly {
                        depth,
                        outcome: retry_result.outcome(),
                    },
                );
            }
            (retry_result.result(), Some(retry_attempt))
        }
    };

    let aspiration_diagnostics =
        AspirationWindowDiagnostics::new(center, initial_attempt, full_window_retry);
    let principal_variation =
        reconstruct_principal_variation(position, depth, result.best_move(), transposition_table)
            .map_err(
            |error| IterativeDeepeningSearchError::PrincipalVariationFailed { depth, error },
        )?;
    let final_attempt = aspiration_diagnostics.final_attempt();

    Ok(IterativeDeepeningIteration {
        depth,
        result,
        nodes,
        principal_variation,
        aspiration_diagnostics,
        transposition_diagnostics,
        hash_full: final_attempt.hash_full(),
        transposition_generation: final_attempt.transposition_generation(),
    })
}

fn run_attempt(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    window: AlphaBetaWindow,
    transposition_table: &mut TranspositionTable,
) -> Result<(AlphaBetaRootWindowResult, AspirationWindowAttempt), IterativeDeepeningSearchError> {
    let result = alpha_beta_search_window_in_current_generation(
        position,
        history,
        depth,
        window,
        transposition_table,
    )
    .map_err(|error| IterativeDeepeningSearchError::IterationFailed { depth, error })?;
    let search_result = result.result();
    let attempt = AspirationWindowAttempt {
        alpha: window.alpha(),
        beta: window.beta(),
        outcome: result.outcome(),
        reported_score: search_result.score(),
        nodes: search_result.nodes(),
        transposition_diagnostics: transposition_table.diagnostics(),
        hash_full: transposition_table.hash_full(),
        transposition_generation: transposition_table.generation(),
    };
    Ok((result, attempt))
}

fn aspiration_window(center: Score, half_width_centipawns: i32) -> AlphaBetaWindow {
    let full = AlphaBetaWindow::full();
    let half_width = half_width_centipawns.max(1);
    let minimum = full.alpha().centipawns();
    let maximum = full.beta().centipawns();
    let center_value = center.centipawns();

    if center_value <= minimum.saturating_add(half_width)
        || center_value >= maximum.saturating_sub(half_width)
    {
        return full;
    }

    let alpha_value = center_value.saturating_sub(half_width).max(minimum);
    let beta_value = center_value.saturating_add(half_width).min(maximum);
    let alpha = Score::from_raw(alpha_value).expect("clamped aspiration alpha is supported");
    let beta = Score::from_raw(beta_value).expect("clamped aspiration beta is supported");
    AlphaBetaWindow::new(alpha, beta).expect("positive aspiration width is valid")
}

fn validate_maximum_depth(maximum_depth: u16) -> Result<(), IterativeDeepeningSearchError> {
    if maximum_depth == 0 {
        return Err(IterativeDeepeningSearchError::ZeroMaximumDepth);
    }
    if maximum_depth > MAX_MATE_PLY {
        return Err(IterativeDeepeningSearchError::MaximumDepthTooLarge {
            maximum_depth,
            supported: MAX_MATE_PLY,
        });
    }
    Ok(())
}

#[cfg(test)]
mod aspiration_tests {
    use chess_core::{Position, SearchHistory};

    use super::search_completed_iteration;
    use crate::{
        alpha_beta_search, AspirationWindowOutcome, Score, TranspositionTable,
        TranspositionTableDiagnostics,
    };

    fn assert_forced_retry(center: i32, expected: AspirationWindowOutcome) {
        let root = Position::starting();
        let mut position = root.clone();
        let position_snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);
        let history_snapshot = history.clone();
        let mut table = TranspositionTable::new(1).expect("bounded table allocates");

        let iteration = search_completed_iteration(
            &mut position,
            &mut history,
            2,
            Some(Score::from_evaluation(center)),
            1,
            &mut table,
        )
        .expect("forced aspiration retry succeeds");
        let diagnostics = iteration.aspiration_diagnostics();
        let initial = diagnostics.initial_attempt();
        let retry = diagnostics
            .full_window_retry()
            .expect("failed aspiration receives a complete-window retry");

        assert_eq!(initial.outcome(), expected);
        assert_eq!(initial.exact_score(), None);
        assert!(!initial.is_full_window());
        assert_eq!(retry.outcome(), AspirationWindowOutcome::Exact);
        assert!(retry.is_full_window());
        assert_eq!(retry.exact_score(), Some(iteration.score()));
        assert_eq!(diagnostics.retry_count(), 1);
        assert_eq!(
            iteration.nodes(),
            initial
                .nodes()
                .checked_add(retry.nodes())
                .expect("small test node total fits")
        );
        assert_eq!(
            iteration.transposition_diagnostics(),
            initial
                .transposition_diagnostics()
                .saturating_add(retry.transposition_diagnostics())
        );
        assert_eq!(
            initial.transposition_generation(),
            retry.transposition_generation()
        );
        assert_eq!(iteration.transposition_generation(), table.generation());

        let mut independent_position = root.clone();
        let mut independent_history = SearchHistory::from_position(&independent_position);
        let independent = alpha_beta_search(
            &mut independent_position,
            &mut independent_history,
            iteration.depth(),
        )
        .expect("independent full-window search succeeds");
        assert_eq!(iteration.score(), independent.score());
        assert_eq!(iteration.best_move(), independent.best_move());
        assert_ne!(
            iteration.transposition_diagnostics(),
            TranspositionTableDiagnostics::default()
        );
        assert_eq!(position, position_snapshot);
        assert_eq!(history, history_snapshot);
        assert_eq!(position.zobrist(), position.recomputed_zobrist());
    }

    #[test]
    fn fail_low_bound_is_not_promoted_and_full_window_retry_recovers_exactly() {
        assert_forced_retry(1_000, AspirationWindowOutcome::FailLow);
    }

    #[test]
    fn fail_high_bound_is_not_promoted_and_full_window_retry_recovers_exactly() {
        assert_forced_retry(-1_000, AspirationWindowOutcome::FailHigh);
    }
}
