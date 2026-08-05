use core::fmt;
use std::time::Duration;

use chess_core::{Move, Position, SearchHistory};

use crate::{
    alpha_beta::{
        alpha_beta_search_window_in_current_generation_with_weights, prepare_alpha_beta_iteration,
        validate_search_inputs, AlphaBetaRootWindowResult, AlphaBetaSearchError,
        AlphaBetaSearchPolicy, AlphaBetaSearchResult, AlphaBetaWindow,
        DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES,
    },
    aspiration::{
        AspirationWindowAttempt, AspirationWindowDiagnostics, AspirationWindowOutcome,
        DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS,
    },
    cancellation::NeverCancelled,
    check_extension::CheckExtensionDiagnostics,
    limits::{
        SearchClock, SearchLimitController, SearchLimitError, SearchLimitTermination, SearchLimits,
        WallClock,
    },
    principal_variation::{
        reconstruct_principal_variation_with_table_policy, PrincipalVariationError,
    },
    EvaluationWeights, PrincipalVariation, Score, SearchCancellationProbe,
    SearchDiagnosticOverflow, SearchDiagnostics, SearchPolicy, SearchPolicySet,
    SearchPolicyValidationError, TranspositionHashFull, TranspositionTable,
    TranspositionTableAllocationError, TranspositionTableDiagnostics, MAX_MATE_PLY,
};

/// One fully completed fixed-depth iteration.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct IterativeDeepeningIteration {
    depth: u16,
    result: AlphaBetaSearchResult,
    nodes: u64,
    qnodes: u64,
    selective_depth: u16,
    search_diagnostics: SearchDiagnostics,
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

    /// Returns quiescence nodes visited by all attempts for this depth.
    #[must_use]
    pub const fn qnodes(&self) -> u64 {
        self.qnodes
    }

    /// Returns the deepest root-relative ply entered at this depth.
    #[must_use]
    pub const fn selective_depth(&self) -> u16 {
        self.selective_depth
    }

    /// Returns deterministic diagnostics aggregated across all attempts.
    #[must_use]
    pub const fn search_diagnostics(&self) -> SearchDiagnostics {
        self.search_diagnostics
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

/// Protocol-neutral snapshot emitted after one exact iteration completes.
#[derive(Clone, Copy, Debug)]
pub struct SearchProgress<'a> {
    iteration: &'a IterativeDeepeningIteration,
    nodes: u64,
    qnodes: u64,
    selective_depth: u16,
    search_diagnostics: SearchDiagnostics,
}

impl<'a> SearchProgress<'a> {
    /// Returns the exact completed iteration represented by this snapshot.
    #[must_use]
    pub const fn iteration(self) -> &'a IterativeDeepeningIteration {
        self.iteration
    }

    /// Returns every production node entered through this completed depth.
    #[must_use]
    pub const fn nodes(self) -> u64 {
        self.nodes
    }

    /// Returns every quiescence node entered through this completed depth.
    #[must_use]
    pub const fn qnodes(self) -> u64 {
        self.qnodes
    }

    /// Returns the deepest root-relative ply entered through this completed depth.
    #[must_use]
    pub const fn selective_depth(self) -> u16 {
        self.selective_depth
    }

    /// Returns request-wide diagnostics through this exact completed depth.
    #[must_use]
    pub const fn search_diagnostics(self) -> SearchDiagnostics {
        self.search_diagnostics
    }
}

/// Completed depth-by-depth results from one iterative-deepening search.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct IterativeDeepeningSearchResult {
    iterations: Vec<IterativeDeepeningIteration>,
    total_nodes: u64,
    total_qnodes: u64,
    selective_depth: u16,
    search_diagnostics: SearchDiagnostics,
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

    /// Returns the exact score from the deepest completed iteration.
    #[must_use]
    pub fn score(&self) -> Option<Score> {
        self.final_iteration()
            .map(IterativeDeepeningIteration::score)
    }

    /// Returns the deterministic best move from the deepest completed iteration.
    #[must_use]
    pub fn best_move(&self) -> Option<Move> {
        self.final_iteration()
            .and_then(IterativeDeepeningIteration::best_move)
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

    /// Returns the checked sum of quiescence nodes from completed depths.
    #[must_use]
    pub const fn total_qnodes(&self) -> u64 {
        self.total_qnodes
    }

    /// Returns the deepest root-relative ply entered by completed work.
    #[must_use]
    pub const fn selective_depth(&self) -> u16 {
        self.selective_depth
    }

    /// Returns checked diagnostics from every completed attempt and depth.
    #[must_use]
    pub const fn search_diagnostics(&self) -> SearchDiagnostics {
        self.search_diagnostics
    }
}

/// Deterministic emergency result when cancellation precedes depth one.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SearchCancellationFallback {
    /// The first move in deterministic legal-generation order.
    FirstLegalMove(Move),
    /// The root is terminal and has no legal move.
    NoLegalMove,
}

impl SearchCancellationFallback {
    /// Returns the emergency legal move, or `None` for a terminal root.
    #[must_use]
    pub const fn best_move(self) -> Option<Move> {
        match self {
            Self::FirstLegalMove(current) => Some(current),
            Self::NoLegalMove => None,
        }
    }
}

/// Authoritative final snapshot for one limit-controlled search request.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SearchResult {
    completed: IterativeDeepeningSearchResult,
    termination: SearchLimitTermination,
    nodes: u64,
    qnodes: u64,
    selective_depth: u16,
    elapsed: Duration,
    check_extension_diagnostics: CheckExtensionDiagnostics,
    search_diagnostics: SearchDiagnostics,
    fallback: Option<SearchCancellationFallback>,
}

impl SearchResult {
    /// Returns only fully exact completed iterations.
    #[must_use]
    pub const fn completed(&self) -> &IterativeDeepeningSearchResult {
        &self.completed
    }

    /// Consumes the snapshot and returns the exact completed iterations.
    #[must_use]
    pub fn into_completed(self) -> IterativeDeepeningSearchResult {
        self.completed
    }

    /// Returns the deterministic move to play.
    ///
    /// A deepest exact iteration is authoritative. When no iteration completed,
    /// this falls back to the unscored deterministic emergency move from Task 16.5.
    #[must_use]
    pub fn best_move(&self) -> Option<Move> {
        match self.completed.best_move() {
            Some(current) => Some(current),
            None => self
                .fallback
                .and_then(SearchCancellationFallback::best_move),
        }
    }

    /// Returns the exact side-to-move score from the deepest completed iteration.
    #[must_use]
    pub fn score(&self) -> Option<Score> {
        self.completed.score()
    }

    /// Returns the opponent reply from the deepest completed legal PV.
    #[must_use]
    pub fn ponder_move(&self) -> Option<Move> {
        self.completed.ponder_move()
    }

    /// Returns the deepest fully completed exact depth.
    #[must_use]
    pub fn completed_depth(&self) -> u16 {
        self.completed.completed_depth()
    }

    /// Returns the deepest root-relative ply entered, including partial work.
    #[must_use]
    pub const fn selective_depth(&self) -> u16 {
        self.selective_depth
    }

    /// Returns every production node entered, including quiescence and partial work.
    #[must_use]
    pub const fn nodes(&self) -> u64 {
        self.nodes
    }

    /// Returns every quiescence node entered, including partial work.
    #[must_use]
    pub const fn qnodes(&self) -> u64 {
        self.qnodes
    }

    /// Returns elapsed request time measured by the configured search clock.
    #[must_use]
    pub const fn elapsed(&self) -> Duration {
        self.elapsed
    }

    /// Returns request-wide bounded check-extension decisions, including partial work.
    #[must_use]
    pub const fn check_extension_diagnostics(&self) -> CheckExtensionDiagnostics {
        self.check_extension_diagnostics
    }

    /// Returns request-wide deterministic diagnostics, including partial work.
    #[must_use]
    pub const fn search_diagnostics(&self) -> SearchDiagnostics {
        self.search_diagnostics
    }

    /// Returns the deepest completed legal principal variation.
    #[must_use]
    pub fn principal_variation(&self) -> Option<&PrincipalVariation> {
        self.completed.principal_variation()
    }

    /// Returns the winning deterministic termination reason.
    #[must_use]
    pub const fn termination(&self) -> SearchLimitTermination {
        self.termination
    }

    /// Compatibility accessor for the pre-Task-16.6 name.
    #[must_use]
    pub const fn searched_nodes(&self) -> u64 {
        self.nodes()
    }

    /// Returns nodes entered by the interrupted, non-completed depth.
    #[must_use]
    pub fn incomplete_nodes(&self) -> u64 {
        self.nodes.saturating_sub(self.completed.total_nodes())
    }

    /// Returns qnodes entered by the interrupted, non-completed depth.
    #[must_use]
    pub fn incomplete_qnodes(&self) -> u64 {
        self.qnodes.saturating_sub(self.completed.total_qnodes())
    }

    /// Returns the deterministic emergency result when no depth completed.
    #[must_use]
    pub const fn fallback(&self) -> Option<SearchCancellationFallback> {
        self.fallback
    }
}

/// Compatibility alias for the Task 16.4/16.5 wrapper name.
pub type LimitedIterativeDeepeningSearchResult = SearchResult;

/// A fail-loud iterative-deepening error.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum IterativeDeepeningSearchError {
    /// A typed limit request was invalid.
    InvalidLimits(SearchLimitError),
    /// An explicit search policy failed before search mutation.
    InvalidSearchPolicy(SearchPolicyValidationError),
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
    /// Checked deterministic diagnostic aggregation overflowed.
    DiagnosticCountOverflow(SearchDiagnosticOverflow),
}

impl fmt::Display for IterativeDeepeningSearchError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InvalidLimits(error) => error.fmt(formatter),
            Self::InvalidSearchPolicy(error) => error.fmt(formatter),
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
            Self::DiagnosticCountOverflow(error) => error.fmt(formatter),
        }
    }
}

impl std::error::Error for IterativeDeepeningSearchError {}

impl From<SearchDiagnosticOverflow> for IterativeDeepeningSearchError {
    fn from(value: SearchDiagnosticOverflow) -> Self {
        Self::DiagnosticCountOverflow(value)
    }
}

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
    let mut total_qnodes = 0_u64;
    let mut selective_depth = 0_u16;
    let mut search_diagnostics = SearchDiagnostics::default();

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
        total_qnodes = total_qnodes.checked_add(iteration.qnodes()).ok_or(
            IterativeDeepeningSearchError::NodeCountOverflow {
                completed_depth: depth - 1,
            },
        )?;
        selective_depth = selective_depth.max(iteration.selective_depth());
        search_diagnostics = search_diagnostics.checked_add(iteration.search_diagnostics())?;
        iterations.push(iteration);
    }

    Ok(completed_result(
        iterations,
        total_nodes,
        total_qnodes,
        selective_depth,
        search_diagnostics,
    ))
}

/// Searches under a validated combination of depth, node, time, infinite, and stop limits.
pub fn iterative_deepening_search_with_limits(
    position: &mut Position,
    history: &mut SearchHistory,
    limits: SearchLimits,
) -> Result<SearchResult, IterativeDeepeningSearchError> {
    limits
        .validate()
        .map_err(IterativeDeepeningSearchError::InvalidLimits)?;
    let mut transposition_table = TranspositionTable::new(DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES)
        .map_err(IterativeDeepeningSearchError::TranspositionTableAllocation)?;
    iterative_deepening_search_with_limits_and_transposition_table(
        position,
        history,
        limits,
        &mut transposition_table,
    )
}

/// Searches under typed limits using one caller-owned bounded table.
pub fn iterative_deepening_search_with_limits_and_transposition_table(
    position: &mut Position,
    history: &mut SearchHistory,
    limits: SearchLimits,
    transposition_table: &mut TranspositionTable,
) -> Result<SearchResult, IterativeDeepeningSearchError> {
    iterative_deepening_search_with_limits_and_transposition_table_and_weights(
        position,
        history,
        limits,
        transposition_table,
        &EvaluationWeights::DEFAULT,
    )
}

/// Searches under typed limits using explicit evaluation weights.
///
/// The caller must not reuse one transposition table across different weight
/// sets without clearing it because stored scores are evaluator-dependent.
pub fn iterative_deepening_search_with_limits_and_transposition_table_and_weights(
    position: &mut Position,
    history: &mut SearchHistory,
    limits: SearchLimits,
    transposition_table: &mut TranspositionTable,
    weights: &EvaluationWeights,
) -> Result<SearchResult, IterativeDeepeningSearchError> {
    let search_policy = SearchPolicySet::baseline();
    iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights(
        position,
        history,
        limits,
        transposition_table,
        &search_policy,
        weights,
    )
}

/// Searches with explicit policy and evaluation identities in controlled Rust tooling/tests.
///
/// Validation happens before position, history, controller, or table mutation. A caller must
/// use a separate transposition table whenever policy or evaluator identity differs.
pub fn iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights(
    position: &mut Position,
    history: &mut SearchHistory,
    limits: SearchLimits,
    transposition_table: &mut TranspositionTable,
    search_policy: &SearchPolicySet,
    weights: &EvaluationWeights,
) -> Result<SearchResult, IterativeDeepeningSearchError> {
    search_policy
        .validate()
        .map_err(IterativeDeepeningSearchError::InvalidSearchPolicy)?;
    iterative_deepening_search_with_limits_and_clock_and_observer_and_weights(
        position,
        history,
        limits,
        transposition_table,
        WallClock::start(),
        IterativeDeepeningExecutionPolicy {
            search_policy: &search_policy.policy,
            weights,
        },
        |_| {},
    )
}

/// Searches under typed limits while observing every exact completed iteration.
///
/// The observer is called synchronously on the search thread after cumulative
/// counters have been updated and before the next depth begins. It receives no
/// protocol or I/O capability and cannot alter search decisions.
pub fn iterative_deepening_search_with_limits_and_transposition_table_and_observer<Observer>(
    position: &mut Position,
    history: &mut SearchHistory,
    limits: SearchLimits,
    transposition_table: &mut TranspositionTable,
    observer: Observer,
) -> Result<SearchResult, IterativeDeepeningSearchError>
where
    Observer: for<'a> FnMut(SearchProgress<'a>),
{
    iterative_deepening_search_with_limits_and_clock_and_observer(
        position,
        history,
        limits,
        transposition_table,
        WallClock::start(),
        observer,
    )
}

#[cfg(test)]
fn iterative_deepening_search_with_limits_and_clock<Clock>(
    position: &mut Position,
    history: &mut SearchHistory,
    limits: SearchLimits,
    transposition_table: &mut TranspositionTable,
    clock: Clock,
) -> Result<SearchResult, IterativeDeepeningSearchError>
where
    Clock: SearchClock,
{
    iterative_deepening_search_with_limits_and_clock_and_observer(
        position,
        history,
        limits,
        transposition_table,
        clock,
        |_| {},
    )
}

fn iterative_deepening_search_with_limits_and_clock_and_observer<Clock, Observer>(
    position: &mut Position,
    history: &mut SearchHistory,
    limits: SearchLimits,
    transposition_table: &mut TranspositionTable,
    clock: Clock,
    observer: Observer,
) -> Result<SearchResult, IterativeDeepeningSearchError>
where
    Clock: SearchClock,
    Observer: for<'a> FnMut(SearchProgress<'a>),
{
    iterative_deepening_search_with_limits_and_clock_and_observer_and_weights(
        position,
        history,
        limits,
        transposition_table,
        clock,
        IterativeDeepeningExecutionPolicy {
            search_policy: &SearchPolicy::V0_1,
            weights: &EvaluationWeights::DEFAULT,
        },
        observer,
    )
}

#[derive(Clone, Copy)]
struct IterativeDeepeningExecutionPolicy<'a> {
    search_policy: &'a SearchPolicy,
    weights: &'a EvaluationWeights,
}

fn iterative_deepening_search_with_limits_and_clock_and_observer_and_weights<Clock, Observer>(
    position: &mut Position,
    history: &mut SearchHistory,
    limits: SearchLimits,
    transposition_table: &mut TranspositionTable,
    clock: Clock,
    execution_policy: IterativeDeepeningExecutionPolicy<'_>,
    mut observer: Observer,
) -> Result<SearchResult, IterativeDeepeningSearchError>
where
    Clock: SearchClock,
    Observer: for<'a> FnMut(SearchProgress<'a>),
{
    let IterativeDeepeningExecutionPolicy {
        search_policy,
        weights,
    } = execution_policy;
    let check_extension_enabled =
        limits.check_extension_enabled() && search_policy.maximum_check_extensions_per_line() > 0;
    let mut controller = SearchLimitController::new(limits, clock)
        .map_err(IterativeDeepeningSearchError::InvalidLimits)?;
    let fallback = cancellation_fallback(position, history)?;
    let mut iterations: Vec<IterativeDeepeningIteration> = Vec::new();
    let mut total_nodes = 0_u64;
    let mut total_qnodes = 0_u64;
    let mut selective_depth = 0_u16;
    let mut search_diagnostics = SearchDiagnostics::default();

    loop {
        let completed_depth = iterations
            .last()
            .map_or(0, IterativeDeepeningIteration::depth);
        if let Some(termination) = controller.boundary_termination(completed_depth) {
            return Ok(limited_result(
                completed_result(
                    iterations,
                    total_nodes,
                    total_qnodes,
                    selective_depth,
                    search_diagnostics,
                ),
                termination,
                &controller,
                fallback,
            ));
        }

        iterations.try_reserve(1).map_err(|_| {
            IterativeDeepeningSearchError::IterationStorageAllocation {
                maximum_depth: controller.iteration_ceiling(),
            }
        })?;
        let depth = completed_depth.saturating_add(1);
        let center = iterations.last().map(IterativeDeepeningIteration::score);
        let iteration = match search_completed_iteration_with_cancellation(
            position,
            history,
            depth,
            center,
            IterationSearchPolicy {
                half_width_centipawns: i32::from(search_policy.aspiration_half_width_centipawns()),
                check_extension_enabled,
                search_policy,
                weights,
            },
            transposition_table,
            &mut controller,
        ) {
            Ok(iteration) => iteration,
            Err(error) => {
                if matches!(
                    error,
                    IterativeDeepeningSearchError::IterationFailed {
                        error: AlphaBetaSearchError::Cancelled,
                        ..
                    }
                ) {
                    if let Some(termination) = controller.termination() {
                        return Ok(limited_result(
                            completed_result(
                                iterations,
                                total_nodes,
                                total_qnodes,
                                selective_depth,
                                search_diagnostics,
                            ),
                            termination,
                            &controller,
                            fallback,
                        ));
                    }
                }
                return Err(error);
            }
        };

        total_nodes = total_nodes.checked_add(iteration.nodes()).ok_or(
            IterativeDeepeningSearchError::NodeCountOverflow {
                completed_depth: depth - 1,
            },
        )?;
        total_qnodes = total_qnodes.checked_add(iteration.qnodes()).ok_or(
            IterativeDeepeningSearchError::NodeCountOverflow {
                completed_depth: depth - 1,
            },
        )?;
        selective_depth = selective_depth.max(iteration.selective_depth());
        search_diagnostics = search_diagnostics.checked_add(iteration.search_diagnostics())?;
        observer(SearchProgress {
            iteration: &iteration,
            nodes: controller.visited_nodes(),
            qnodes: controller.visited_qnodes(),
            selective_depth: controller.selective_depth(),
            search_diagnostics: controller.search_diagnostics(),
        });
        iterations.push(iteration);
    }
}

fn cancellation_fallback(
    position: &mut Position,
    history: &SearchHistory,
) -> Result<SearchCancellationFallback, IterativeDeepeningSearchError> {
    validate_search_inputs(position, history, 1)
        .map_err(|error| IterativeDeepeningSearchError::IterationFailed { depth: 1, error })?;
    let tokens = position.legal_move_tokens().map_err(|error| {
        IterativeDeepeningSearchError::IterationFailed {
            depth: 1,
            error: AlphaBetaSearchError::from(error),
        }
    })?;
    let fallback = tokens
        .iter()
        .next()
        .map_or(SearchCancellationFallback::NoLegalMove, |token| {
            SearchCancellationFallback::FirstLegalMove(token.move_made())
        });
    Ok(fallback)
}

fn completed_result(
    iterations: Vec<IterativeDeepeningIteration>,
    total_nodes: u64,
    total_qnodes: u64,
    selective_depth: u16,
    search_diagnostics: SearchDiagnostics,
) -> IterativeDeepeningSearchResult {
    IterativeDeepeningSearchResult {
        iterations,
        total_nodes,
        total_qnodes,
        selective_depth,
        search_diagnostics,
    }
}

fn limited_result<Clock>(
    completed: IterativeDeepeningSearchResult,
    termination: SearchLimitTermination,
    controller: &SearchLimitController<Clock>,
    root_fallback: SearchCancellationFallback,
) -> SearchResult
where
    Clock: SearchClock,
{
    let fallback = completed.iterations().is_empty().then_some(root_fallback);
    SearchResult {
        completed,
        termination,
        nodes: controller.visited_nodes(),
        qnodes: controller.visited_qnodes(),
        selective_depth: controller.selective_depth(),
        elapsed: controller.elapsed(),
        check_extension_diagnostics: controller.check_extension_diagnostics(),
        search_diagnostics: controller.search_diagnostics(),
        fallback,
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct IterationSearchPolicy<'a> {
    half_width_centipawns: i32,
    check_extension_enabled: bool,
    search_policy: &'a SearchPolicy,
    weights: &'a EvaluationWeights,
}

fn search_completed_iteration(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    center: Option<Score>,
    half_width_centipawns: i32,
    transposition_table: &mut TranspositionTable,
) -> Result<IterativeDeepeningIteration, IterativeDeepeningSearchError> {
    let mut cancellation = NeverCancelled;
    search_completed_iteration_with_cancellation(
        position,
        history,
        depth,
        center,
        IterationSearchPolicy {
            half_width_centipawns,
            check_extension_enabled: false,
            search_policy: &SearchPolicy::V0_1,
            weights: &EvaluationWeights::DEFAULT,
        },
        transposition_table,
        &mut cancellation,
    )
}

fn search_completed_iteration_with_cancellation<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    center: Option<Score>,
    policy: IterationSearchPolicy<'_>,
    transposition_table: &mut TranspositionTable,
    cancellation: &mut Probe,
) -> Result<IterativeDeepeningIteration, IterativeDeepeningSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    prepare_alpha_beta_iteration(position, history, depth, transposition_table)
        .map_err(|error| IterativeDeepeningSearchError::IterationFailed { depth, error })?;

    let initial_window = if policy.search_policy.aspiration_windows_enabled() {
        center.map_or_else(AlphaBetaWindow::full, |score| {
            aspiration_window(score, policy.half_width_centipawns)
        })
    } else {
        AlphaBetaWindow::full()
    };
    let (initial_result, initial_attempt) = run_attempt(
        position,
        history,
        depth,
        AlphaBetaSearchPolicy::new(
            initial_window,
            policy.check_extension_enabled,
            policy.search_policy,
            policy.weights,
        ),
        transposition_table,
        cancellation,
    )?;

    let mut nodes = initial_attempt.nodes();
    let mut qnodes = initial_attempt.qnodes();
    let mut selective_depth = initial_attempt.selective_depth();
    let mut transposition_diagnostics = initial_attempt.transposition_diagnostics();
    let mut search_diagnostics = initial_result.result().diagnostics();

    let (result, full_window_retry) = match initial_result.outcome() {
        AspirationWindowOutcome::Exact => (initial_result.result(), None),
        AspirationWindowOutcome::FailLow | AspirationWindowOutcome::FailHigh => {
            let (retry_result, retry_attempt) = run_attempt(
                position,
                history,
                depth,
                AlphaBetaSearchPolicy::new(
                    AlphaBetaWindow::full(),
                    policy.check_extension_enabled,
                    policy.search_policy,
                    policy.weights,
                ),
                transposition_table,
                cancellation,
            )?;
            nodes = nodes.checked_add(retry_attempt.nodes()).ok_or(
                IterativeDeepeningSearchError::NodeCountOverflow {
                    completed_depth: depth - 1,
                },
            )?;
            qnodes = qnodes.checked_add(retry_attempt.qnodes()).ok_or(
                IterativeDeepeningSearchError::NodeCountOverflow {
                    completed_depth: depth - 1,
                },
            )?;
            selective_depth = selective_depth.max(retry_attempt.selective_depth());
            transposition_diagnostics =
                transposition_diagnostics.saturating_add(retry_attempt.transposition_diagnostics());
            search_diagnostics =
                search_diagnostics.checked_add(retry_result.result().diagnostics())?;
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
    let principal_variation = reconstruct_principal_variation_with_table_policy(
        position,
        depth,
        result.best_move(),
        transposition_table,
        !policy.check_extension_enabled,
    )
    .map_err(|error| IterativeDeepeningSearchError::PrincipalVariationFailed { depth, error })?;
    let final_attempt = aspiration_diagnostics.final_attempt();

    Ok(IterativeDeepeningIteration {
        depth,
        result,
        nodes,
        qnodes,
        selective_depth,
        search_diagnostics,
        principal_variation,
        aspiration_diagnostics,
        transposition_diagnostics,
        hash_full: final_attempt.hash_full(),
        transposition_generation: final_attempt.transposition_generation(),
    })
}

fn run_attempt<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    policy: AlphaBetaSearchPolicy<'_>,
    transposition_table: &mut TranspositionTable,
    cancellation: &mut Probe,
) -> Result<(AlphaBetaRootWindowResult, AspirationWindowAttempt), IterativeDeepeningSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    let result = alpha_beta_search_window_in_current_generation_with_weights(
        position,
        history,
        depth,
        policy,
        transposition_table,
        cancellation,
    )
    .map_err(|error| IterativeDeepeningSearchError::IterationFailed { depth, error })?;
    let search_result = result.result();
    let attempt = AspirationWindowAttempt {
        alpha: policy.window().alpha(),
        beta: policy.window().beta(),
        outcome: result.outcome(),
        reported_score: search_result.score(),
        nodes: search_result.nodes(),
        qnodes: search_result.qnodes(),
        selective_depth: search_result.selective_depth(),
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

#[cfg(test)]
mod limit_tests {
    use std::{cell::Cell, time::Duration};

    use chess_core::{Position, SearchHistory};

    use super::{
        iterative_deepening_search_with_limits_and_clock,
        iterative_deepening_search_with_limits_and_clock_and_observer,
    };
    use crate::{limits::SearchClock, SearchLimitTermination, SearchLimits, TranspositionTable};

    struct ScriptedClock {
        values: Vec<Duration>,
        index: Cell<usize>,
    }

    impl ScriptedClock {
        fn new(values: Vec<Duration>) -> Self {
            assert!(!values.is_empty());
            Self {
                values,
                index: Cell::new(0),
            }
        }
    }

    impl SearchClock for ScriptedClock {
        fn elapsed(&self) -> Duration {
            let index = self.index.get();
            self.index.set(index.saturating_add(1));
            self.values
                .get(index)
                .copied()
                .unwrap_or_else(|| *self.values.last().expect("clock has a terminal value"))
        }
    }

    fn terminal_root() -> Position {
        "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1"
            .parse()
            .expect("terminal limit-test FEN is valid")
    }

    #[test]
    fn soft_time_is_checked_after_one_exact_completed_iteration() {
        let mut position = terminal_root();
        let snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);
        let history_snapshot = history.clone();
        let mut table = TranspositionTable::new(1).expect("bounded table allocates");
        let limit = Duration::from_millis(1);

        let result = iterative_deepening_search_with_limits_and_clock(
            &mut position,
            &mut history,
            SearchLimits::new().with_depth(3).with_soft_time(limit),
            &mut table,
            ScriptedClock::new(vec![limit]),
        )
        .expect("soft-time search returns exact completed work");

        assert_eq!(
            result.termination(),
            SearchLimitTermination::SoftTime { limit }
        );
        assert_eq!(result.completed().completed_depth(), 1);
        assert_eq!(result.completed().total_nodes(), 1);
        assert_eq!(result.searched_nodes(), 1);
        assert_eq!(result.elapsed(), limit);
        assert_eq!(table.generation(), 1);
        assert_eq!(position, snapshot);
        assert_eq!(history, history_snapshot);
        assert_eq!(position.zobrist(), position.recomputed_zobrist());
    }

    #[test]
    fn hard_time_wins_before_starting_the_next_depth() {
        let mut position = terminal_root();
        let snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);
        let history_snapshot = history.clone();
        let mut table = TranspositionTable::new(1).expect("bounded table allocates");
        let limit = Duration::from_millis(1);

        let result = iterative_deepening_search_with_limits_and_clock(
            &mut position,
            &mut history,
            SearchLimits::new().with_depth(3).with_hard_time(limit),
            &mut table,
            ScriptedClock::new(vec![Duration::ZERO, Duration::ZERO, limit]),
        )
        .expect("hard-time search returns prior exact work");

        assert_eq!(
            result.termination(),
            SearchLimitTermination::HardTime { limit }
        );
        assert_eq!(result.completed().completed_depth(), 1);
        assert_eq!(result.searched_nodes(), 1);
        assert_eq!(result.elapsed(), limit);
        assert_eq!(table.generation(), 1);
        assert_eq!(position, snapshot);
        assert_eq!(history, history_snapshot);
        assert_eq!(position.zobrist(), position.recomputed_zobrist());
    }

    #[test]
    fn observer_receives_every_completed_depth_in_order() {
        let mut position = terminal_root();
        let snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);
        let history_snapshot = history.clone();
        let mut table = TranspositionTable::new(1).expect("bounded table allocates");
        let mut observed = Vec::new();

        let result = iterative_deepening_search_with_limits_and_clock_and_observer(
            &mut position,
            &mut history,
            SearchLimits::new().with_depth(3),
            &mut table,
            ScriptedClock::new(vec![Duration::ZERO]),
            |progress| {
                observed.push((
                    progress.iteration().depth(),
                    progress.nodes(),
                    progress.qnodes(),
                    progress.selective_depth(),
                ));
            },
        )
        .expect("observed depth search succeeds");

        assert_eq!(result.completed_depth(), 3);
        assert_eq!(
            result.nodes(),
            result.search_diagnostics().main_nodes()
                + result.search_diagnostics().quiescence_nodes()
        );
        assert_eq!(
            result.qnodes(),
            result.search_diagnostics().quiescence_nodes()
        );
        assert!(result.search_diagnostics().reserved_counters_are_zero());
        assert_eq!(
            observed.iter().map(|entry| entry.0).collect::<Vec<_>>(),
            vec![1, 2, 3]
        );
        assert!(observed.windows(2).all(|window| window[0].1 <= window[1].1));
        assert_eq!(
            observed.last().map(|entry| entry.1),
            Some(result.completed().total_nodes())
        );
        assert_eq!(position, snapshot);
        assert_eq!(history, history_snapshot);
        assert_eq!(position.zobrist(), position.recomputed_zobrist());
    }
}
