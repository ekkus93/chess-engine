use core::fmt;

use chess_core::{Move, Position, SearchHistory};

use crate::{
    alpha_beta::{
        alpha_beta_search_with_transposition_table, AlphaBetaSearchError, AlphaBetaSearchResult,
        DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES,
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
    principal_variation: PrincipalVariation,
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

    /// Returns the exact full-window result completed at this depth.
    #[must_use]
    pub const fn result(&self) -> AlphaBetaSearchResult {
        self.result
    }

    /// Returns the root score from the side-to-move perspective.
    #[must_use]
    pub const fn score(&self) -> Score {
        self.result.score()
    }

    /// Returns the deterministic best move completed at this depth.
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

    /// Returns nodes visited by this iteration only.
    #[must_use]
    pub const fn nodes(&self) -> u64 {
        self.result.nodes()
    }

    /// Returns probe/store counters produced by this iteration only.
    #[must_use]
    pub const fn transposition_diagnostics(&self) -> TranspositionTableDiagnostics {
        self.transposition_diagnostics
    }

    /// Returns bounded current-generation table occupancy after this iteration.
    #[must_use]
    pub const fn hash_full(&self) -> TranspositionHashFull {
        self.hash_full
    }

    /// Returns the table generation assigned to this iteration.
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

    /// Returns the sum of nodes visited by all completed iterations.
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
    /// One fixed-depth iteration failed.
    IterationFailed {
        /// Depth that failed before producing a completed record.
        depth: u16,
        /// Underlying fixed-depth search error.
        error: AlphaBetaSearchError,
    },
    /// Safe principal-variation reconstruction failed after a completed search.
    PrincipalVariationFailed {
        /// Completed depth whose PV could not be reconstructed safely.
        depth: u16,
        /// Underlying bounded reconstruction failure.
        error: PrincipalVariationError,
    },
    /// Summing completed iteration node counts exceeded `u64`.
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

/// Searches every full-window depth from one through `maximum_depth`.
///
/// The convenience entry point allocates one bounded default transposition table
/// and reuses it for every iteration. Every completed depth retains its exact
/// result, legal principal variation, per-iteration table diagnostics, bounded
/// hash-full estimate, and generation identifier.
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

/// Searches every full-window depth using one caller-owned bounded table.
///
/// Entries survive between depths. The fixed-depth search advances generation
/// and resets diagnostic counters once per iteration. PV reconstruction is a
/// read-only complete-key traversal and does not alter those counters.
pub fn iterative_deepening_search_with_transposition_table(
    position: &mut Position,
    history: &mut SearchHistory,
    maximum_depth: u16,
    transposition_table: &mut TranspositionTable,
) -> Result<IterativeDeepeningSearchResult, IterativeDeepeningSearchError> {
    validate_maximum_depth(maximum_depth)?;

    let mut iterations = Vec::new();
    iterations
        .try_reserve_exact(maximum_depth as usize)
        .map_err(|_| IterativeDeepeningSearchError::IterationStorageAllocation { maximum_depth })?;
    let mut total_nodes = 0_u64;

    for depth in 1..=maximum_depth {
        let result = alpha_beta_search_with_transposition_table(
            position,
            history,
            depth,
            transposition_table,
        )
        .map_err(|error| IterativeDeepeningSearchError::IterationFailed { depth, error })?;
        let principal_variation = reconstruct_principal_variation(
            position,
            depth,
            result.best_move(),
            transposition_table,
        )
        .map_err(
            |error| IterativeDeepeningSearchError::PrincipalVariationFailed { depth, error },
        )?;

        total_nodes = total_nodes.checked_add(result.nodes()).ok_or(
            IterativeDeepeningSearchError::NodeCountOverflow {
                completed_depth: depth - 1,
            },
        )?;
        iterations.push(IterativeDeepeningIteration {
            depth,
            result,
            principal_variation,
            transposition_diagnostics: transposition_table.diagnostics(),
            hash_full: transposition_table.hash_full(),
            transposition_generation: transposition_table.generation(),
        });
    }

    Ok(IterativeDeepeningSearchResult {
        iterations,
        total_nodes,
    })
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
