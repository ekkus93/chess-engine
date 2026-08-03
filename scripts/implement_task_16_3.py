#!/usr/bin/env python3
from pathlib import Path
import sys

ROOT = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.cwd()


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected one match in {path}, found {count}: {old[:120]!r}")
    path.write_text(text.replace(old, new, 1), encoding="utf-8")


transposition = ROOT / "crates/chess-search/src/transposition.rs"
replace_once(
    transposition,
    "mod diagnostics;\nmod probe;\nmod store;",
    "mod diagnostics;\nmod principal_variation;\nmod probe;\nmod store;",
)

alpha_beta = ROOT / "crates/chess-search/src/alpha_beta.rs"
replace_once(
    alpha_beta,
    """            let stored_best_move = if bound == TranspositionBound::Exact && ply > 0 {
                None
            } else {
                result.best_move
            };
            let normalized_score = TranspositionScore::normalize(result.score, ply)?;
            table.store(TranspositionEntry::new(
                position.zobrist(),
                depth,
                bound,
                normalized_score,
                stored_best_move,
                table.generation(),
            ));
""",
    """            let normalized_score = TranspositionScore::normalize(result.score, ply)?;
            table.store(TranspositionEntry::new(
                position.zobrist(),
                depth,
                bound,
                normalized_score,
                result.best_move,
                table.generation(),
            ));
""",
)

(ROOT / "crates/chess-search/src/transposition/principal_variation.rs").write_text(
    r'''use chess_core::Move;

use super::{TranspositionBound, TranspositionTable};

impl TranspositionTable {
    /// Returns a complete-key, exact-bound move with sufficient remaining depth.
    ///
    /// Principal-variation reconstruction is observational: it does not mutate
    /// table diagnostics, generation, allocation, or replacement state.
    pub(crate) fn principal_variation_move(
        &self,
        verification_key: u64,
        required_depth: u16,
    ) -> Option<Move> {
        let cluster = &self.clusters[self.cluster_index(verification_key)];
        cluster
            .entries
            .iter()
            .flatten()
            .copied()
            .find(|entry| {
                entry.verification_key() == verification_key
                    && entry.bound() == TranspositionBound::Exact
                    && entry.depth() >= required_depth
            })
            .and_then(|entry| entry.best_move())
    }
}

#[cfg(test)]
mod tests {
    use chess_core::{Move, MoveKind, Square};

    use crate::{
        Score, TranspositionBound, TranspositionEntry, TranspositionScore, TranspositionTable,
        TranspositionTableDiagnostics,
    };

    fn square(text: &str) -> Square {
        text.parse().expect("PV lookup square is valid")
    }

    fn best_move() -> Move {
        Move::new(square("e2"), square("e4"), MoveKind::DoublePawnPush)
    }

    fn entry(
        key: u64,
        depth: u16,
        bound: TranspositionBound,
        current: Option<Move>,
    ) -> TranspositionEntry {
        TranspositionEntry::new(
            key,
            depth,
            bound,
            TranspositionScore::normalize(Score::ZERO, 0).expect("zero score normalizes"),
            current,
            0,
        )
    }

    #[test]
    fn lookup_requires_complete_key_exact_bound_depth_and_move() {
        let mut table = TranspositionTable::new(1).expect("table allocates");
        let key = 0x1234_5678_9abc_def0;
        let collision = key.wrapping_add(table.cluster_count() as u64);
        table.store(entry(
            collision,
            12,
            TranspositionBound::Exact,
            Some(best_move()),
        ));
        table.store(entry(
            key,
            11,
            TranspositionBound::Lower,
            Some(best_move()),
        ));

        assert_eq!(table.principal_variation_move(key, 1), None);

        table.store(entry(
            key,
            5,
            TranspositionBound::Exact,
            Some(best_move()),
        ));
        assert_eq!(table.principal_variation_move(key, 6), None);
        assert_eq!(table.principal_variation_move(key, 5), Some(best_move()));

        table.store(entry(key, 7, TranspositionBound::Exact, None));
        assert_eq!(table.principal_variation_move(key, 1), None);
    }

    #[test]
    fn lookup_does_not_change_search_diagnostics() {
        let mut table = TranspositionTable::new(1).expect("table allocates");
        let key = 9;
        table.store(entry(
            key,
            3,
            TranspositionBound::Exact,
            Some(best_move()),
        ));
        table.reset_diagnostics();
        let before = table.diagnostics();

        assert_eq!(table.principal_variation_move(key, 3), Some(best_move()));
        assert_eq!(table.diagnostics(), before);
        assert_eq!(before, TranspositionTableDiagnostics::default());
    }
}
''',
    encoding="utf-8",
)

(ROOT / "crates/chess-search/src/principal_variation.rs").write_text(
    r'''use core::fmt;

use chess_core::{LegalMoveError, Move, Position};

use crate::TranspositionTable;

/// Why safe principal-variation reconstruction stopped.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PrincipalVariationTermination {
    /// The line contains exactly the requested number of plies.
    ReachedRequestedDepth,
    /// The current position has no legal moves before the requested depth.
    TerminalPosition {
        /// Root-relative ply at which the terminal was observed.
        ply: u16,
    },
    /// The exact root result did not contain a move, such as a resolved draw.
    RootResultWithoutMove,
    /// No complete-key exact entry with sufficient depth and a move was available.
    MissingExactEntry {
        /// Root-relative ply that could not be extended.
        ply: u16,
        /// Depth still required from the current position.
        remaining_depth: u16,
    },
    /// A verified table entry contained a move that is not currently legal.
    IllegalTableMove {
        /// Root-relative ply at which the move was rejected.
        ply: u16,
        /// Rejected candidate.
        candidate: Move,
    },
    /// Following legal verified moves returned to a previously visited identity.
    RepeatedPosition {
        /// Number of legal PV moves already retained.
        ply: u16,
        /// Repeated complete position identity.
        verification_key: u64,
    },
}

/// A bounded legal principal variation reconstructed after one completed search.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PrincipalVariation {
    moves: Vec<Move>,
    termination: PrincipalVariationTermination,
}

impl PrincipalVariation {
    /// Returns the legal move sequence in root-to-leaf order.
    #[must_use]
    pub fn moves(&self) -> &[Move] {
        &self.moves
    }

    /// Returns the number of retained legal plies.
    #[must_use]
    pub fn len(&self) -> usize {
        self.moves.len()
    }

    /// Returns whether the reconstructed line contains no move.
    #[must_use]
    pub fn is_empty(&self) -> bool {
        self.moves.is_empty()
    }

    /// Returns the opponent reply after the root best move, when available.
    #[must_use]
    pub fn ponder_move(&self) -> Option<Move> {
        self.moves.get(1).copied()
    }

    /// Returns the explicit reason reconstruction stopped.
    #[must_use]
    pub const fn termination(&self) -> PrincipalVariationTermination {
        self.termination
    }
}

/// Failure to allocate or legally validate a principal variation.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum PrincipalVariationError {
    /// The allocator rejected bounded move or cycle-detection storage.
    AllocationFailed {
        /// Requested maximum PV depth.
        requested_depth: u16,
    },
    /// Legal move generation or application failed unexpectedly.
    Rules {
        /// Root-relative ply being reconstructed.
        ply: u16,
        /// Underlying rule error.
        error: LegalMoveError,
    },
}

impl fmt::Display for PrincipalVariationError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::AllocationFailed { requested_depth } => write!(
                formatter,
                "failed to reserve bounded principal-variation storage for depth {requested_depth}"
            ),
            Self::Rules { ply, error } => {
                write!(formatter, "principal-variation rules failed at ply {ply}: {error}")
            }
        }
    }
}

impl std::error::Error for PrincipalVariationError {}

pub(crate) fn reconstruct_principal_variation(
    root: &Position,
    requested_depth: u16,
    root_best_move: Option<Move>,
    transposition_table: &TranspositionTable,
) -> Result<PrincipalVariation, PrincipalVariationError> {
    let mut moves = Vec::new();
    moves
        .try_reserve_exact(usize::from(requested_depth))
        .map_err(|_| PrincipalVariationError::AllocationFailed { requested_depth })?;
    let mut visited_keys = Vec::new();
    visited_keys
        .try_reserve_exact(usize::from(requested_depth) + 1)
        .map_err(|_| PrincipalVariationError::AllocationFailed { requested_depth })?;

    let mut position = root.clone();
    visited_keys.push(position.zobrist());
    let mut remaining_depth = requested_depth;
    let mut ply = 0_u16;

    while remaining_depth > 0 {
        let tokens = position
            .legal_move_tokens()
            .map_err(|error| PrincipalVariationError::Rules { ply, error })?;
        if tokens.is_empty() {
            return Ok(PrincipalVariation {
                moves,
                termination: PrincipalVariationTermination::TerminalPosition { ply },
            });
        }

        let candidate = if ply == 0 {
            root_best_move
        } else {
            transposition_table.principal_variation_move(position.zobrist(), remaining_depth)
        };
        let Some(candidate) = candidate else {
            let termination = if ply == 0 {
                PrincipalVariationTermination::RootResultWithoutMove
            } else {
                PrincipalVariationTermination::MissingExactEntry {
                    ply,
                    remaining_depth,
                }
            };
            return Ok(PrincipalVariation { moves, termination });
        };

        let Some(token) = tokens
            .iter()
            .find(|token| token.move_made() == candidate)
        else {
            return Ok(PrincipalVariation {
                moves,
                termination: PrincipalVariationTermination::IllegalTableMove { ply, candidate },
            });
        };

        position
            .make_legal_token(token)
            .map_err(|error| PrincipalVariationError::Rules { ply, error })?;
        moves.push(candidate);
        ply += 1;
        remaining_depth -= 1;

        if remaining_depth == 0 {
            return Ok(PrincipalVariation {
                moves,
                termination: PrincipalVariationTermination::ReachedRequestedDepth,
            });
        }

        let verification_key = position.zobrist();
        if visited_keys.contains(&verification_key) {
            return Ok(PrincipalVariation {
                moves,
                termination: PrincipalVariationTermination::RepeatedPosition {
                    ply,
                    verification_key,
                },
            });
        }
        visited_keys.push(verification_key);
    }

    Ok(PrincipalVariation {
        moves,
        termination: PrincipalVariationTermination::ReachedRequestedDepth,
    })
}

#[cfg(test)]
mod tests {
    use chess_core::{Move, MoveKind, Position, Square, UciMove};

    use super::{
        reconstruct_principal_variation, PrincipalVariationTermination,
    };
    use crate::{
        Score, TranspositionBound, TranspositionEntry, TranspositionScore, TranspositionTable,
        TranspositionTableDiagnostics,
    };

    fn resolve(position: &mut Position, text: &str) -> Move {
        let syntax = text.parse::<UciMove>().expect("PV UCI syntax is valid");
        position
            .legal_move_tokens()
            .expect("PV legal tokens generate")
            .iter()
            .find(|token| syntax.matches(token.move_made()))
            .expect("PV fixture move is legal")
            .move_made()
    }

    fn play(position: &mut Position, text: &str) -> Move {
        let current = resolve(position, text);
        let token = position
            .legal_move_tokens()
            .expect("PV legal tokens generate")
            .iter()
            .find(|token| token.move_made() == current)
            .expect("PV token is present");
        position
            .make_legal_token(token)
            .expect("PV fixture move applies");
        current
    }

    fn store_exact(
        table: &mut TranspositionTable,
        position: &Position,
        depth: u16,
        current: Move,
    ) {
        table.store(TranspositionEntry::new(
            position.zobrist(),
            depth,
            TranspositionBound::Exact,
            TranspositionScore::normalize(Score::ZERO, 0).expect("PV score normalizes"),
            Some(current),
            table.generation(),
        ));
    }

    #[test]
    fn complete_exact_chain_is_legal_bounded_and_returns_ponder_move() {
        let root = Position::starting();
        let mut cursor = root.clone();
        let root_move = play(&mut cursor, "e2e4");
        let reply = resolve(&mut cursor, "e7e5");
        let mut table = TranspositionTable::new(1).expect("PV table allocates");
        store_exact(&mut table, &cursor, 2, reply);
        let _reply = play(&mut cursor, "e7e5");
        let third = resolve(&mut cursor, "g1f3");
        store_exact(&mut table, &cursor, 1, third);
        table.reset_diagnostics();

        let pv = reconstruct_principal_variation(&root, 3, Some(root_move), &table)
            .expect("PV reconstruction succeeds");

        assert_eq!(pv.moves(), &[root_move, reply, third]);
        assert_eq!(pv.ponder_move(), Some(reply));
        assert_eq!(
            pv.termination(),
            PrincipalVariationTermination::ReachedRequestedDepth
        );
        assert_eq!(table.diagnostics(), TranspositionTableDiagnostics::default());
    }

    #[test]
    fn complete_key_collision_cannot_extend_the_line() {
        let root = Position::starting();
        let mut cursor = root.clone();
        let root_move = play(&mut cursor, "e2e4");
        let reply = resolve(&mut cursor, "e7e5");
        let mut table = TranspositionTable::new(1).expect("PV table allocates");
        let collision_key = cursor
            .zobrist()
            .wrapping_add(table.cluster_count() as u64);
        table.store(TranspositionEntry::new(
            collision_key,
            2,
            TranspositionBound::Exact,
            TranspositionScore::normalize(Score::ZERO, 0).expect("PV score normalizes"),
            Some(reply),
            table.generation(),
        ));

        let pv = reconstruct_principal_variation(&root, 3, Some(root_move), &table)
            .expect("PV reconstruction succeeds");

        assert_eq!(pv.moves(), &[root_move]);
        assert_eq!(
            pv.termination(),
            PrincipalVariationTermination::MissingExactEntry {
                ply: 1,
                remaining_depth: 2,
            }
        );
    }

    #[test]
    fn illegal_table_move_is_rejected_before_it_enters_the_pv() {
        let root = Position::starting();
        let mut cursor = root.clone();
        let root_move = play(&mut cursor, "e2e4");
        let illegal = Move::new(
            "a1".parse::<Square>().expect("a1 is valid"),
            "a8".parse::<Square>().expect("a8 is valid"),
            MoveKind::Quiet,
        );
        let mut table = TranspositionTable::new(1).expect("PV table allocates");
        store_exact(&mut table, &cursor, 2, illegal);

        let pv = reconstruct_principal_variation(&root, 3, Some(root_move), &table)
            .expect("PV reconstruction succeeds");

        assert_eq!(pv.moves(), &[root_move]);
        assert_eq!(
            pv.termination(),
            PrincipalVariationTermination::IllegalTableMove {
                ply: 1,
                candidate: illegal,
            }
        );
    }

    #[test]
    fn repeated_position_terminates_a_legal_tt_cycle() {
        let root = Position::starting();
        let root_key = root.zobrist();
        let mut cursor = root.clone();
        let first = play(&mut cursor, "g1f3");
        let second = resolve(&mut cursor, "g8f6");
        let mut table = TranspositionTable::new(1).expect("PV table allocates");
        store_exact(&mut table, &cursor, 7, second);
        let _second = play(&mut cursor, "g8f6");
        let third = resolve(&mut cursor, "f3g1");
        store_exact(&mut table, &cursor, 6, third);
        let _third = play(&mut cursor, "f3g1");
        let fourth = resolve(&mut cursor, "f6g8");
        store_exact(&mut table, &cursor, 5, fourth);

        let pv = reconstruct_principal_variation(&root, 8, Some(first), &table)
            .expect("PV reconstruction succeeds");

        assert_eq!(pv.moves(), &[first, second, third, fourth]);
        assert_eq!(
            pv.termination(),
            PrincipalVariationTermination::RepeatedPosition {
                ply: 4,
                verification_key: root_key,
            }
        );
    }
}
''',
    encoding="utf-8",
)

(ROOT / "crates/chess-search/src/iterative_deepening.rs").write_text(
    r'''use core::fmt;

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
        .map_err(|error| IterativeDeepeningSearchError::PrincipalVariationFailed {
            depth,
            error,
        })?;

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
''',
    encoding="utf-8",
)

lib = ROOT / "crates/chess-search/src/lib.rs"
replace_once(
    lib,
    "mod move_ordering;\nmod quiescence;",
    "mod move_ordering;\nmod principal_variation;\nmod quiescence;",
)
replace_once(
    lib,
    """pub use iterative_deepening::{
    iterative_deepening_search, iterative_deepening_search_with_transposition_table,
    IterativeDeepeningIteration, IterativeDeepeningSearchError, IterativeDeepeningSearchResult,
};
pub use quiescence::{
""",
    """pub use iterative_deepening::{
    iterative_deepening_search, iterative_deepening_search_with_transposition_table,
    IterativeDeepeningIteration, IterativeDeepeningSearchError, IterativeDeepeningSearchResult,
};
pub use principal_variation::{
    PrincipalVariation, PrincipalVariationError, PrincipalVariationTermination,
};
pub use quiescence::{
""",
)

(ROOT / "crates/chess-search/tests/search_iterative_deepening.rs").write_text(
    r'''use chess_core::{Move, Position, SearchHistory};
use chess_search::{
    alpha_beta_search, iterative_deepening_search,
    iterative_deepening_search_with_transposition_table, AlphaBetaSearchError,
    IterativeDeepeningSearchError, PrincipalVariationTermination, TranspositionTable,
    TranspositionTableDiagnostics, MAX_MATE_PLY,
};

fn benchmark_position() -> Position {
    "7k/8/8/1p2q3/2P1Q3/8/K7/8 w - - 0 1"
        .parse()
        .expect("iterative-deepening benchmark FEN is valid")
}

fn assert_legal_line(root: &Position, line: &[Move]) {
    let mut cursor = root.clone();
    for current in line {
        let tokens = cursor
            .legal_move_tokens()
            .expect("PV legal tokens generate");
        let token = tokens
            .iter()
            .find(|token| token.move_made() == *current)
            .expect("every returned PV move is legal in sequence");
        cursor
            .make_legal_token(token)
            .expect("returned PV move applies");
    }
}

#[test]
fn every_depth_is_preserved_and_matches_independent_full_window_search() {
    let root = benchmark_position();
    let mut position = root.clone();
    let position_snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let mut table = TranspositionTable::new(1).expect("bounded table allocates");

    let result = iterative_deepening_search_with_transposition_table(
        &mut position,
        &mut history,
        3,
        &mut table,
    )
    .expect("iterative deepening succeeds");

    assert_eq!(result.completed_depth(), 3);
    assert_eq!(result.iterations().len(), 3);
    assert_eq!(
        result
            .iterations()
            .iter()
            .map(|iteration| iteration.depth())
            .collect::<Vec<_>>(),
        vec![1, 2, 3]
    );
    assert_eq!(
        result.total_nodes(),
        result
            .iterations()
            .iter()
            .map(|iteration| iteration.nodes())
            .sum()
    );

    for iteration in result.iterations() {
        let mut independent_position = benchmark_position();
        let mut independent_history = SearchHistory::from_position(&independent_position);
        let independent = alpha_beta_search(
            &mut independent_position,
            &mut independent_history,
            iteration.depth(),
        )
        .expect("independent fixed-depth search succeeds");

        assert_eq!(iteration.score(), independent.score());
        assert_eq!(iteration.best_move(), independent.best_move());
        assert_eq!(
            iteration.principal_variation().moves().first().copied(),
            iteration.best_move()
        );
        assert!(iteration.principal_variation().len() <= usize::from(iteration.depth()));
        assert_legal_line(&root, iteration.principal_variation().moves());
        assert_eq!(independent_position, benchmark_position());
        assert_eq!(
            independent_position.zobrist(),
            independent_position.recomputed_zobrist()
        );
    }

    assert_eq!(
        result
            .iterations()
            .iter()
            .map(|iteration| iteration.transposition_generation())
            .collect::<Vec<_>>(),
        vec![1, 2, 3]
    );
    assert_eq!(table.generation(), 3);
    assert!(result.iterations()[0].transposition_diagnostics().probes() > 0);
    assert!(result.iterations()[1].transposition_diagnostics().hits() > 0);
    assert!(result.iterations()[2].transposition_diagnostics().hits() > 0);
    for iteration in result.iterations() {
        assert!(iteration.transposition_diagnostics().stores() > 0);
        assert!(iteration.hash_full().sampled_slots() > 0);
        assert!(iteration.hash_full().per_mille() <= 1_000);
    }

    assert_eq!(position, position_snapshot);
    assert_eq!(history, history_snapshot);
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
}

#[test]
fn convenience_search_reuses_one_bounded_table_and_returns_the_final_iteration() {
    let root = Position::starting();
    let mut position = root.clone();
    let position_snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();

    let result = iterative_deepening_search(&mut position, &mut history, 3)
        .expect("convenience iterative deepening succeeds");
    let final_iteration = result
        .final_iteration()
        .expect("positive maximum depth always completes a final iteration");

    assert_eq!(final_iteration.depth(), 3);
    assert_eq!(final_iteration.transposition_generation(), 3);
    assert_eq!(final_iteration.result().nodes(), final_iteration.nodes());
    assert!(final_iteration.transposition_diagnostics().hits() > 0);
    assert!(!final_iteration.principal_variation().is_empty());
    assert_eq!(
        final_iteration.ponder_move(),
        final_iteration.principal_variation().moves().get(1).copied()
    );
    assert_eq!(result.ponder_move(), final_iteration.ponder_move());
    assert_eq!(
        result.principal_variation(),
        Some(final_iteration.principal_variation())
    );
    assert_legal_line(&root, final_iteration.principal_variation().moves());
    assert_eq!(position, position_snapshot);
    assert_eq!(history, history_snapshot);
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
}

#[test]
fn terminal_roots_produce_empty_terminal_principal_variations() {
    let mut position: Position = "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1"
        .parse()
        .expect("checkmate FEN is valid");
    let position_snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let mut table = TranspositionTable::new(1).expect("bounded table allocates");

    let result = iterative_deepening_search_with_transposition_table(
        &mut position,
        &mut history,
        3,
        &mut table,
    )
    .expect("terminal iterative deepening succeeds");

    assert_eq!(result.iterations().len(), 3);
    for iteration in result.iterations() {
        assert_eq!(iteration.nodes(), 1);
        assert_eq!(iteration.best_move(), None);
        assert!(iteration.score().is_mate());
        assert!(iteration.principal_variation().is_empty());
        assert_eq!(
            iteration.principal_variation().termination(),
            PrincipalVariationTermination::TerminalPosition { ply: 0 }
        );
        assert_eq!(iteration.ponder_move(), None);
        assert_eq!(
            iteration.transposition_diagnostics(),
            TranspositionTableDiagnostics::default()
        );
        assert_eq!(iteration.hash_full().occupied_current_generation(), 0);
    }
    assert_eq!(result.total_nodes(), 3);
    assert_eq!(table.generation(), 3);
    assert_eq!(position, position_snapshot);
    assert_eq!(history, history_snapshot);
}

#[test]
fn invalid_maximum_depths_fail_before_mutating_a_caller_owned_table() {
    let mut position = benchmark_position();
    let mut history = SearchHistory::from_position(&position);
    let mut table = TranspositionTable::new(1).expect("bounded table allocates");
    let generation = table.generation();
    let diagnostics = table.diagnostics();
    let capacity = table.entry_capacity();

    assert_eq!(
        iterative_deepening_search_with_transposition_table(
            &mut position,
            &mut history,
            0,
            &mut table,
        ),
        Err(IterativeDeepeningSearchError::ZeroMaximumDepth)
    );
    assert_eq!(
        iterative_deepening_search_with_transposition_table(
            &mut position,
            &mut history,
            MAX_MATE_PLY + 1,
            &mut table,
        ),
        Err(IterativeDeepeningSearchError::MaximumDepthTooLarge {
            maximum_depth: MAX_MATE_PLY + 1,
            supported: MAX_MATE_PLY,
        })
    );

    assert_eq!(table.generation(), generation);
    assert_eq!(table.diagnostics(), diagnostics);
    assert_eq!(table.entry_capacity(), capacity);
}

#[test]
fn mismatched_history_fails_on_depth_one_without_mutating_table_or_position() {
    let mut position = benchmark_position();
    let position_snapshot = position.clone();
    let other_position: Position = "8/8/8/8/8/8/4K3/6k1 w - - 0 1"
        .parse()
        .expect("alternate history root is valid");
    let mut history = SearchHistory::from_position(&other_position);
    let history_snapshot = history.clone();
    let mut table = TranspositionTable::new(1).expect("bounded table allocates");

    let error = iterative_deepening_search_with_transposition_table(
        &mut position,
        &mut history,
        2,
        &mut table,
    )
    .expect_err("mismatched history must fail");

    assert!(matches!(
        error,
        IterativeDeepeningSearchError::IterationFailed {
            depth: 1,
            error: AlphaBetaSearchError::HistoryPositionMismatch { .. },
        }
    ));
    assert_eq!(table.generation(), 0);
    assert_eq!(
        table.diagnostics(),
        TranspositionTableDiagnostics::default()
    );
    assert_eq!(position, position_snapshot);
    assert_eq!(history, history_snapshot);
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
}
''',
    encoding="utf-8",
)

(ROOT / "docs/RUST_PRINCIPAL_VARIATION.md").write_text(
    '''# Rust Principal Variation — Task 16.3

Task 16.3 adds bounded, collision-safe principal-variation reconstruction to every completed iterative-deepening result. Task 16.2 aspiration windows remains open and is not implemented by this change.

## Reconstruction contract

The first PV move comes from the completed exact root `AlphaBetaSearchResult`. Later moves come only from transposition entries that satisfy all of these conditions:

- the complete 64-bit verification key matches the current position;
- the entry bound is `Exact`;
- the stored depth is at least the remaining PV depth;
- the entry contains a best move.

Lookup is read-only and does not increment TT probes, hits, cutoffs, stores, or replacement counters.

Every candidate is matched against freshly generated legal move tokens for the current position before it is appended. An illegal stored move terminates reconstruction and is never returned. Search now retains best moves in internal exact entries so complete exact chains can be followed after the search has restored the root.

## Bounded termination

`PrincipalVariation` reserves at most the completed search depth in moves and at most depth plus one complete position identities. Reconstruction stops explicitly when it:

- reaches the requested depth;
- reaches a position with no legal moves;
- lacks an exact entry with sufficient depth;
- encounters a root result without a move;
- rejects an illegal stored move; or
- reaches a previously visited Zobrist identity.

The repeated-identity guard prevents a legal cyclic TT chain from looping, while the completed-depth bound provides an independent hard maximum.

## Ponder move

The ponder move is the second validated PV move. It is returned only when at least two legal moves were reconstructed. Terminal, truncated, collision-rejected, and one-ply lines return no ponder move.

## Public API

- `PrincipalVariation`
- `PrincipalVariationTermination`
- `PrincipalVariationError`
- `IterativeDeepeningIteration::principal_variation`
- `IterativeDeepeningIteration::ponder_move`
- `IterativeDeepeningSearchResult::principal_variation`
- `IterativeDeepeningSearchResult::ponder_move`

## Validation

Focused tests cover complete exact chains, ponder extraction, full-key collision rejection, exact-bound/depth requirements, illegal stored moves, repeated-position termination, diagnostic non-mutation, legal replay of every returned move, terminal roots, and exact root/history/Zobrist restoration.
''',
    encoding="utf-8",
)

iterative_doc = ROOT / "docs/RUST_ITERATIVE_DEEPENING.md"
replace_once(
    iterative_doc,
    """- principal-variation reconstruction or ponder moves;
- node, time, infinite, or stop limits;
""",
    """- node, time, infinite, or stop limits;
""",
)
replace_once(
    iterative_doc,
    """Those remain Tasks 16.2 through 16.7. This separation keeps the initial iteration loop exact, deterministic, and independently testable.
""",
    """Task 16.3 now adds safe legal PV reconstruction and ponder extraction as documented in `docs/RUST_PRINCIPAL_VARIATION.md`. Aspiration windows, limits, cancellation recovery, the final result API, and check extensions remain in Tasks 16.2 and 16.4 through 16.7.
""",
)

print("Task 16.3 implementation applied")
