#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1])


def replace_once(path: str, old: str, new: str) -> None:
    target = root / path
    text = target.read_text()
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"expected exactly one match in {path}, found {count}: {old[:160]!r}")
    target.write_text(text.replace(old, new, 1))


alpha = "crates/chess-search/src/alpha_beta.rs"
replace_once(
    alpha,
    """use crate::{
    cancellation::NeverCancelled,
    move_ordering::{ordered_legal_moves_with_state, MoveOrdering, QuietOrderingState},
    quiescence::{search_quiescence_node, QuiescenceContext},
    search_common::resolved_node_score,
    Score, SearchCancellationProbe, MAX_MATE_PLY, MAX_QUIESCENCE_PLY,
};
""",
    """use crate::{
    cancellation::NeverCancelled,
    move_ordering::{
        ordered_legal_moves_with_state_and_tt_move, MoveOrdering, QuietOrderingState,
    },
    quiescence::{search_quiescence_node, QuiescenceContext},
    search_common::resolved_node_score,
    Score, SearchCancellationProbe, TranspositionBound, TranspositionEntry,
    TranspositionProbeError, TranspositionProbeRequest, TranspositionProbeScore,
    TranspositionScore, TranspositionScoreConversionError, TranspositionScoreReuse,
    TranspositionTable, TranspositionTableAllocationError, MAX_MATE_PLY, MAX_QUIESCENCE_PLY,
};
""",
)
replace_once(
    alpha,
    """/// Result of one full-window negamax alpha-beta search.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct AlphaBetaSearchResult {
""",
    """/// Fixed table size used by the convenience alpha-beta entry points.
pub const DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES: usize = 1;

/// Result of one full-window negamax alpha-beta search.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct AlphaBetaSearchResult {
""",
)
replace_once(
    alpha,
    """    /// Reversible search-line history processing failed.
    History(SearchHistoryError),
    /// The supplied history is not rooted at the supplied current position.
""",
    """    /// Reversible search-line history processing failed.
    History(SearchHistoryError),
    /// Fixed-capacity transposition-table allocation failed.
    TranspositionTableAllocation(TranspositionTableAllocationError),
    /// A transposition probe could not be evaluated safely.
    TranspositionProbe(TranspositionProbeError),
    /// A searched score could not be normalized for storage.
    TranspositionScoreConversion(TranspositionScoreConversionError),
    /// The supplied history is not rooted at the supplied current position.
""",
)
replace_once(
    alpha,
    """            Self::Rules(error) => error.fmt(formatter),
            Self::History(error) => error.fmt(formatter),
            Self::HistoryPositionMismatch {
""",
    """            Self::Rules(error) => error.fmt(formatter),
            Self::History(error) => error.fmt(formatter),
            Self::TranspositionTableAllocation(error) => error.fmt(formatter),
            Self::TranspositionProbe(error) => error.fmt(formatter),
            Self::TranspositionScoreConversion(error) => error.fmt(formatter),
            Self::HistoryPositionMismatch {
""",
)
replace_once(
    alpha,
    """impl From<SearchHistoryError> for AlphaBetaSearchError {
    fn from(value: SearchHistoryError) -> Self {
        Self::History(value)
    }
}

/// Searches to `depth` with recursive fail-soft negamax alpha-beta pruning.
""",
    """impl From<SearchHistoryError> for AlphaBetaSearchError {
    fn from(value: SearchHistoryError) -> Self {
        Self::History(value)
    }
}

impl From<TranspositionTableAllocationError> for AlphaBetaSearchError {
    fn from(value: TranspositionTableAllocationError) -> Self {
        Self::TranspositionTableAllocation(value)
    }
}

impl From<TranspositionProbeError> for AlphaBetaSearchError {
    fn from(value: TranspositionProbeError) -> Self {
        Self::TranspositionProbe(value)
    }
}

impl From<TranspositionScoreConversionError> for AlphaBetaSearchError {
    fn from(value: TranspositionScoreConversionError) -> Self {
        Self::TranspositionScoreConversion(value)
    }
}

/// Searches to `depth` with recursive fail-soft negamax alpha-beta pruning.
""",
)

start = (root / alpha).read_text().index("pub fn alpha_beta_search(")
end = (root / alpha).read_text().index("#[derive(Clone, Copy, Debug, Eq, PartialEq)]\nstruct AlphaBetaWindow")
text = (root / alpha).read_text()
api_block = r'''pub fn alpha_beta_search(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError> {
    let mut cancellation = NeverCancelled;
    alpha_beta_search_with_cancellation(position, history, depth, &mut cancellation)
}

/// Searches with a fresh bounded default transposition table and cancellation.
pub fn alpha_beta_search_with_cancellation<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    cancellation: &mut Probe,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    validate_search_inputs(position, history, depth)?;
    let mut transposition_table =
        TranspositionTable::new(DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES)?;
    run_validated_search(
        position,
        history,
        depth,
        &mut transposition_table,
        cancellation,
    )
}

/// Searches with a caller-owned fixed-capacity transposition table.
///
/// Existing entries are retained across calls. The table generation advances
/// once and diagnostics reset before the search starts. Position and history
/// validation happens first, so invalid inputs do not mutate table state.
pub fn alpha_beta_search_with_transposition_table(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    transposition_table: &mut TranspositionTable,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError> {
    let mut cancellation = NeverCancelled;
    alpha_beta_search_with_cancellation_and_transposition_table(
        position,
        history,
        depth,
        transposition_table,
        &mut cancellation,
    )
}

/// Searches with a caller-owned table and cooperative cancellation.
pub fn alpha_beta_search_with_cancellation_and_transposition_table<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    transposition_table: &mut TranspositionTable,
    cancellation: &mut Probe,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    validate_search_inputs(position, history, depth)?;
    run_validated_search(
        position,
        history,
        depth,
        transposition_table,
        cancellation,
    )
}

fn validate_search_inputs(
    position: &Position,
    history: &SearchHistory,
    depth: u16,
) -> Result<(), AlphaBetaSearchError> {
    if depth > MAX_MATE_PLY {
        return Err(AlphaBetaSearchError::DepthTooLarge {
            depth,
            maximum: MAX_MATE_PLY,
        });
    }

    let history_zobrist = history.current_zobrist();
    if history_zobrist != Some(position.zobrist()) {
        return Err(AlphaBetaSearchError::HistoryPositionMismatch {
            position_zobrist: position.zobrist(),
            history_zobrist,
        });
    }
    Ok(())
}

fn run_validated_search<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    transposition_table: &mut TranspositionTable,
    cancellation: &mut Probe,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    transposition_table.advance_generation();
    transposition_table.reset_diagnostics();

    let initial_history_len = history.len();
    let initial_line_len = history.line_len();
    let initial_zobrist = position.zobrist();
    let alpha = Score::mated_in(0).expect("zero-ply mate score is supported");
    let beta = Score::mate_in(0).expect("zero-ply mate score is supported");
    let window = AlphaBetaWindow { alpha, beta };
    let mut quiet_ordering = QuietOrderingState::new();
    let mut context = AlphaBetaContext {
        ordering: MoveOrdering::Quiet,
        quiet_ordering: &mut quiet_ordering,
        transposition_table: Some(transposition_table),
        cancellation,
    };
    let result = search_node(position, history, depth, 0, window, &mut context);

    debug_assert_eq!(history.len(), initial_history_len);
    debug_assert_eq!(history.line_len(), initial_line_len);
    debug_assert_eq!(history.current_zobrist(), Some(initial_zobrist));
    debug_assert_eq!(position.zobrist(), initial_zobrist);
    debug_assert_eq!(position.zobrist(), position.recomputed_zobrist());

    result
}

'''
(root / alpha).write_text(text[:start] + api_block + text[end:])

replace_once(
    alpha,
    """    ordering: MoveOrdering,
    quiet_ordering: &'a mut QuietOrderingState,
    cancellation: &'a mut Probe,
""",
    """    ordering: MoveOrdering,
    quiet_ordering: &'a mut QuietOrderingState,
    transposition_table: Option<&'a mut TranspositionTable>,
    cancellation: &'a mut Probe,
""",
)

text = (root / alpha).read_text()
start = text.index("fn search_node<Probe>(")
end = text.index("#[cfg(test)]\nmod ordering_tests")
search_block = r'''fn search_node<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    ply: u16,
    window: AlphaBetaWindow,
    context: &mut AlphaBetaContext<'_, Probe>,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    let mut alpha = window.alpha;
    let original_alpha = window.alpha;
    let beta = window.beta;
    if context.cancellation.should_cancel() {
        return Err(AlphaBetaSearchError::Cancelled);
    }

    if depth == 0 {
        let quiescence_context = QuiescenceContext {
            ply,
            quiescence_ply: 0,
            maximum_quiescence_ply: MAX_QUIESCENCE_PLY,
        };
        return search_quiescence_node(
            position,
            history,
            quiescence_context,
            alpha,
            beta,
            context.ordering,
            &mut *context.cancellation,
        );
    }

    let tokens = position.legal_move_tokens()?;
    if let Some(score) = resolved_node_score(position, history, tokens.is_empty(), depth, ply)
        .map_err(|error| AlphaBetaSearchError::DepthTooLarge {
            depth: error.ply(),
            maximum: MAX_MATE_PLY,
        })?
    {
        return Ok(AlphaBetaSearchResult {
            score,
            best_move: None,
            nodes: 1,
        });
    }

    let score_reuse = transposition_score_reuse(position);
    let mut transposition_table_move = None;
    if let Some(table) = context.transposition_table.as_deref_mut() {
        let request = TranspositionProbeRequest::new(
            position.zobrist(),
            depth,
            ply,
            alpha,
            beta,
            score_reuse,
        );
        if let Some(probe) = table.probe(request)? {
            transposition_table_move = probe.best_move();
            if let Some(probe_score) = probe.score() {
                let root_best_move = transposition_table_move.filter(|candidate| {
                    tokens
                        .iter()
                        .any(|token| token.move_made() == *candidate)
                });
                let can_return = match (ply, probe_score) {
                    (0, TranspositionProbeScore::Exact(_)) => root_best_move.is_some(),
                    (0, TranspositionProbeScore::LowerBoundCutoff(_))
                    | (0, TranspositionProbeScore::UpperBoundCutoff(_)) => false,
                    _ => true,
                };
                if can_return {
                    return Ok(AlphaBetaSearchResult {
                        score: probe_score.score(),
                        best_move: if ply == 0 {
                            root_best_move
                        } else {
                            transposition_table_move
                        },
                        nodes: 1,
                    });
                }
            }
        }
    }

    if ply == 0 {
        transposition_table_move = None;
    }
    let ordered_tokens = ordered_legal_moves_with_state_and_tt_move(
        position,
        &tokens,
        context.ordering,
        ply,
        context.quiet_ordering,
        transposition_table_move,
    );
    let mut nodes = 1_u64;
    let mut best_score = None;
    let mut best_move = None;

    for token in ordered_tokens.iter() {
        if context.cancellation.should_cancel() {
            return Err(AlphaBetaSearchError::Cancelled);
        }

        let current = token.move_made();
        let position_undo = position.make_legal_token(token)?;
        let history_undo = history.push_position(position);
        let child_window = AlphaBetaWindow {
            alpha: -beta,
            beta: -alpha,
        };
        let child = search_node(position, history, depth - 1, ply + 1, child_window, context);
        let history_restore = history.pop_position(history_undo);
        let position_restore = position.unmake_move(position_undo);

        if let Err(error) = position_restore {
            return Err(error.into());
        }
        if let Err(error) = history_restore {
            return Err(error.into());
        }

        let child = child?;
        nodes = nodes
            .checked_add(child.nodes)
            .ok_or(AlphaBetaSearchError::NodeCountOverflow)?;
        let score = -child.score;
        let replace_best = match best_score {
            Some(previous) => score > previous,
            None => true,
        };
        if replace_best {
            best_score = Some(score);
            best_move = Some(current);
        }
        if score > alpha {
            alpha = score;
        }
        if alpha >= beta {
            if context.ordering == MoveOrdering::Quiet {
                context.quiet_ordering.record_quiet_cutoff(
                    position.side_to_move(),
                    current,
                    depth,
                    ply,
                );
            }
            break;
        }
    }

    let result = match (best_score, best_move) {
        (Some(score), Some(current)) => AlphaBetaSearchResult {
            score,
            best_move: Some(current),
            nodes,
        },
        _ => return Err(AlphaBetaSearchError::MissingBestMove),
    };

    if score_reuse == TranspositionScoreReuse::Allowed {
        if let Some(table) = context.transposition_table.as_deref_mut() {
            let bound = if result.score <= original_alpha {
                TranspositionBound::Upper
            } else if result.score >= beta {
                TranspositionBound::Lower
            } else {
                TranspositionBound::Exact
            };
            let stored_best_move = if bound == TranspositionBound::Exact && ply > 0 {
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
        }
    }

    Ok(result)
}

fn transposition_score_reuse(position: &Position) -> TranspositionScoreReuse {
    if position.halfmove_clock().get() == 0 {
        TranspositionScoreReuse::Allowed
    } else {
        TranspositionScoreReuse::SuppressedForRepetition
    }
}

'''
(root / alpha).write_text(text[:start] + search_block + text[end:])

# Existing direct-node test contexts explicitly run without a table.
text = (root / alpha).read_text()
text = text.replace(
    "quiet_ordering: &mut quiet_ordering,\n            cancellation:",
    "quiet_ordering: &mut quiet_ordering,\n            transposition_table: None,\n            cancellation:",
)
(root / alpha).write_text(text)

replace_once(
    alpha,
    """    use crate::{
        cancellation::NeverCancelled,
        move_ordering::{MoveOrdering, QuietOrderingState},
        Score,
    };
""",
    """    use crate::{
        cancellation::NeverCancelled,
        move_ordering::{
            ordered_legal_moves_with_state, MoveOrdering, QuietOrderingState,
        },
        Score, TranspositionBound, TranspositionEntry, TranspositionScore, TranspositionTable,
        TranspositionTableDiagnostics,
    };
""",
)

marker = """    #[test]
    fn quiet_ordering_preserves_full_window_result_deterministically() {
"""
insert = r'''    fn quiet_order_cutoff_witness(root: &Position) -> (Move, Score, usize) {
        let mut position = root.clone();
        let snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);
        let history_snapshot = history.clone();
        let tokens = position
            .legal_move_tokens()
            .expect("benchmark legal tokens generate");
        let quiet_ordering = QuietOrderingState::new();
        let ordered = ordered_legal_moves_with_state(
            &position,
            &tokens,
            MoveOrdering::Quiet,
            1,
            &quiet_ordering,
        );
        let mut best_before = Score::mated_in(0).expect("zero-ply mate score is supported");
        let mut witness = None;

        for (index, token) in ordered.iter().enumerate() {
            let current = token.move_made();
            let score = root_move_score(&mut position, &mut history, token);
            let quiet = !current.kind().is_capture() && current.promotion().is_none();
            if index > 0 && quiet && score > best_before {
                witness = Some((current, score, index));
                break;
            }
            if score > best_before {
                best_before = score;
            }
        }

        assert_eq!(position, snapshot);
        assert_eq!(history, history_snapshot);
        assert_eq!(position.zobrist(), position.recomputed_zobrist());
        witness.expect("fixed benchmark contains a later improving quiet-ordered move")
    }

    fn search_with_transposition_hint(
        root: &Position,
        depth: u16,
        window: AlphaBetaWindow,
        hint: Move,
    ) -> (AlphaBetaSearchResult, TranspositionTableDiagnostics) {
        let mut position = root.clone();
        let snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);
        let history_snapshot = history.clone();
        let mut quiet_ordering = QuietOrderingState::new();
        let mut cancellation = NeverCancelled;
        let mut table = TranspositionTable::new(1).expect("TT benchmark table allocates");
        table.store(TranspositionEntry::new(
            position.zobrist(),
            0,
            TranspositionBound::Exact,
            TranspositionScore::normalize(Score::ZERO, 1)
                .expect("TT benchmark score normalizes"),
            Some(hint),
            table.generation(),
        ));
        table.reset_diagnostics();
        let result = {
            let mut context = AlphaBetaContext {
                ordering: MoveOrdering::Quiet,
                quiet_ordering: &mut quiet_ordering,
                transposition_table: Some(&mut table),
                cancellation: &mut cancellation,
            };
            search_node(&mut position, &mut history, depth, 1, window, &mut context)
                .expect("TT ordering benchmark search succeeds")
        };
        let diagnostics = table.diagnostics();

        assert_eq!(position, snapshot);
        assert_eq!(history, history_snapshot);
        assert_eq!(position.zobrist(), position.recomputed_zobrist());
        (result, diagnostics)
    }

'''
replace_once(alpha, marker, insert + marker)

module_end = """    #[test]
    fn seeded_quiet_cutoff_reduces_a_fixed_narrow_window_tree() {
        let root = Position::starting();
        let (witness, score, generation_index) = quiet_cutoff_witness(&root);
        let alpha = Score::from_raw(score.centipawns() - 1)
            .expect("benchmark cutoff score has a predecessor");
        let window = AlphaBetaWindow { alpha, beta: score };
        let generation = search_with_ordering(&root, 1, window, MoveOrdering::Generation, None);
        let quiet = search_with_ordering(&root, 1, window, MoveOrdering::Quiet, Some(witness));

        assert!(generation_index > 0);
        assert_eq!(generation.score(), score);
        assert_eq!(generation.best_move(), Some(witness));
        assert_eq!(quiet.score(), generation.score());
        assert_eq!(quiet.best_move(), generation.best_move());
        assert!(
            quiet.nodes() < generation.nodes(),
            "quiet ordering visited {} nodes versus generation order {}",
            quiet.nodes(),
            generation.nodes()
        );
    }
}

#[cfg(test)]
mod tests {
"""
module_replacement = r'''    #[test]
    fn seeded_quiet_cutoff_reduces_a_fixed_narrow_window_tree() {
        let root = Position::starting();
        let (witness, score, generation_index) = quiet_cutoff_witness(&root);
        let alpha = Score::from_raw(score.centipawns() - 1)
            .expect("benchmark cutoff score has a predecessor");
        let window = AlphaBetaWindow { alpha, beta: score };
        let generation = search_with_ordering(&root, 1, window, MoveOrdering::Generation, None);
        let quiet = search_with_ordering(&root, 1, window, MoveOrdering::Quiet, Some(witness));

        assert!(generation_index > 0);
        assert_eq!(generation.score(), score);
        assert_eq!(generation.best_move(), Some(witness));
        assert_eq!(quiet.score(), generation.score());
        assert_eq!(quiet.best_move(), generation.best_move());
        assert!(
            quiet.nodes() < generation.nodes(),
            "quiet ordering visited {} nodes versus generation order {}",
            quiet.nodes(),
            generation.nodes()
        );
    }

    #[test]
    fn transposition_move_ordering_reduces_fixed_narrow_window_tree() {
        let root = Position::starting();
        let (witness, score, quiet_index) = quiet_order_cutoff_witness(&root);
        let alpha = Score::from_raw(score.centipawns() - 1)
            .expect("TT cutoff score has a predecessor");
        let window = AlphaBetaWindow { alpha, beta: score };
        let baseline = search_with_ordering(&root, 1, window, MoveOrdering::Quiet, None);
        let (transposition, diagnostics) =
            search_with_transposition_hint(&root, 1, window, witness);

        assert!(quiet_index > 0);
        assert_eq!(transposition.score(), baseline.score());
        assert_eq!(transposition.best_move(), baseline.best_move());
        assert_eq!(transposition.best_move(), Some(witness));
        assert!(
            transposition.nodes() < baseline.nodes(),
            "TT move ordering visited {} nodes versus baseline {}",
            transposition.nodes(),
            baseline.nodes()
        );
        assert_eq!(diagnostics.probes(), 1);
        assert_eq!(diagnostics.hits(), 1);
        assert_eq!(diagnostics.exact_hits(), 0);
    }
}

#[cfg(test)]
mod tests {
'''
replace_once(alpha, module_end, module_replacement)

move_ordering = "crates/chess-search/src/move_ordering.rs"
replace_once(
    move_ordering,
    """pub(crate) fn ordered_legal_moves_with_state(
    position: &Position,
    tokens: &LegalMoveTokenList,
    ordering: MoveOrdering,
    ply: u16,
    quiet_state: &QuietOrderingState,
) -> OrderedLegalMoves {
    let previous_pv_move = match ordering {
        MoveOrdering::Quiet => previous_pv_move_hook(ply),
        MoveOrdering::Generation | MoveOrdering::Tactical => None,
    };
    order_legal_moves_with_hints(
        position,
        tokens,
        ordering,
        ply,
        Some(quiet_state),
        transposition_table_move_hook(position),
        previous_pv_move,
    )
}
""",
    """pub(crate) fn ordered_legal_moves_with_state(
    position: &Position,
    tokens: &LegalMoveTokenList,
    ordering: MoveOrdering,
    ply: u16,
    quiet_state: &QuietOrderingState,
) -> OrderedLegalMoves {
    ordered_legal_moves_with_state_and_tt_move(
        position,
        tokens,
        ordering,
        ply,
        quiet_state,
        transposition_table_move_hook(position),
    )
}

pub(crate) fn ordered_legal_moves_with_state_and_tt_move(
    position: &Position,
    tokens: &LegalMoveTokenList,
    ordering: MoveOrdering,
    ply: u16,
    quiet_state: &QuietOrderingState,
    transposition_table_move: Option<Move>,
) -> OrderedLegalMoves {
    let previous_pv_move = match ordering {
        MoveOrdering::Quiet => previous_pv_move_hook(ply),
        MoveOrdering::Generation | MoveOrdering::Tactical => None,
    };
    order_legal_moves_with_hints(
        position,
        tokens,
        ordering,
        ply,
        Some(quiet_state),
        transposition_table_move,
        previous_pv_move,
    )
}
""",
)
replace_once(
    move_ordering,
    """    use super::{
        ordered_legal_moves_with_state, previous_pv_move_hook, MoveOrdering, QuietOrderingState,
    };
""",
    """    use super::{
        ordered_legal_moves_with_state, ordered_legal_moves_with_state_and_tt_move,
        previous_pv_move_hook, MoveOrdering, QuietOrderingState,
    };
""",
)
replace_once(
    move_ordering,
    """    #[test]
    fn killers_precede_history_and_captures_are_not_recorded() {
""",
    """    #[test]
    fn explicit_tt_move_precedes_quiet_heuristics() {
        let mut position = Position::starting();
        let hint = legal_move(&mut position, \"h2h4\");
        let tokens = position.legal_move_tokens().expect(\"legal tokens generate\");
        let state = QuietOrderingState::new();
        let ordered: Vec<_> = ordered_legal_moves_with_state_and_tt_move(
            &position,
            &tokens,
            MoveOrdering::Quiet,
            0,
            &state,
            Some(hint),
        )
        .iter()
        .map(|token| token.move_made())
        .collect();
        assert_eq!(ordered.first().copied(), Some(hint));
    }

    #[test]
    fn killers_precede_history_and_captures_are_not_recorded() {
""",
)

lib = "crates/chess-search/src/lib.rs"
replace_once(
    lib,
    """pub use alpha_beta::{
    alpha_beta_search, alpha_beta_search_with_cancellation, AlphaBetaSearchError,
    AlphaBetaSearchResult,
};
""",
    """pub use alpha_beta::{
    alpha_beta_search, alpha_beta_search_with_cancellation,
    alpha_beta_search_with_cancellation_and_transposition_table,
    alpha_beta_search_with_transposition_table, AlphaBetaSearchError, AlphaBetaSearchResult,
    DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES,
};
""",
)

(root / "crates/chess-search/tests/search_transposition.rs").write_text(r'''use chess_core::{Move, MoveKind, Position, SearchHistory, Square};
use chess_search::{
    alpha_beta_search, alpha_beta_search_with_transposition_table, Score, TranspositionBound,
    TranspositionEntry, TranspositionScore, TranspositionTable,
    DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES,
};

fn square(text: &str) -> Square {
    text.parse().expect("transposition integration square is valid")
}

fn e2e4() -> Move {
    Move::new(
        square("e2"),
        square("e4"),
        MoveKind::DoublePawnPush,
    )
}

#[test]
fn warm_table_exact_root_hit_reduces_nodes_and_preserves_result() {
    assert_eq!(DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES, 1);
    let mut position = Position::starting();
    let position_snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let mut table = TranspositionTable::new(1).expect("integration table allocates");
    let capacity = table.entry_capacity();
    let allocated = table.allocated_bytes();

    let cold = alpha_beta_search_with_transposition_table(
        &mut position,
        &mut history,
        3,
        &mut table,
    )
    .expect("cold TT search succeeds");
    let cold_diagnostics = table.diagnostics();
    assert!(cold.nodes() > 1);
    assert!(cold_diagnostics.stores() > 0);
    assert_eq!(position, position_snapshot);
    assert_eq!(history, history_snapshot);

    let warm = alpha_beta_search_with_transposition_table(
        &mut position,
        &mut history,
        3,
        &mut table,
    )
    .expect("warm TT search succeeds");
    let warm_diagnostics = table.diagnostics();

    assert_eq!(warm.score(), cold.score());
    assert_eq!(warm.best_move(), cold.best_move());
    assert_eq!(warm.nodes(), 1);
    assert!(warm.nodes() < cold.nodes());
    assert_eq!(warm_diagnostics.probes(), 1);
    assert_eq!(warm_diagnostics.hits(), 1);
    assert_eq!(warm_diagnostics.exact_hits(), 1);
    assert_eq!(table.entry_capacity(), capacity);
    assert_eq!(table.allocated_bytes(), allocated);
    assert_eq!(position, position_snapshot);
    assert_eq!(history, history_snapshot);
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
}

#[test]
fn reversible_history_suppresses_cached_root_score_and_hint() {
    let fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 1 1";
    let mut baseline_position: Position = fen.parse().expect("baseline FEN is valid");
    let mut baseline_history = SearchHistory::from_position(&baseline_position);
    let baseline = alpha_beta_search(&mut baseline_position, &mut baseline_history, 1)
        .expect("baseline search succeeds");

    let mut position: Position = fen.parse().expect("TT FEN is valid");
    let snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let mut table = TranspositionTable::new(1).expect("integration table allocates");
    let bogus = Score::from_evaluation(1_234);
    table.store(TranspositionEntry::new(
        position.zobrist(),
        8,
        TranspositionBound::Exact,
        TranspositionScore::normalize(bogus, 0).expect("bogus fixture score normalizes"),
        Some(e2e4()),
        table.generation(),
    ));

    let result = alpha_beta_search_with_transposition_table(
        &mut position,
        &mut history,
        1,
        &mut table,
    )
    .expect("history-sensitive TT search succeeds");
    let diagnostics = table.diagnostics();

    assert_ne!(result.score(), bogus);
    assert_eq!(result.score(), baseline.score());
    assert_eq!(result.best_move(), baseline.best_move());
    assert_eq!(result.nodes(), baseline.nodes());
    assert_eq!(diagnostics.probes(), 1);
    assert_eq!(diagnostics.hits(), 1);
    assert_eq!(diagnostics.exact_hits(), 0);
    assert_eq!(diagnostics.stores(), 0);
    assert_eq!(position, snapshot);
    assert_eq!(history, history_snapshot);
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
}

#[test]
fn illegal_exact_root_move_does_not_bypass_legal_search() {
    let mut position = Position::starting();
    let snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let mut table = TranspositionTable::new(1).expect("integration table allocates");
    let bogus = Score::from_evaluation(2_345);
    let illegal = Move::new(square("a1"), square("a8"), MoveKind::Quiet);
    table.store(TranspositionEntry::new(
        position.zobrist(),
        8,
        TranspositionBound::Exact,
        TranspositionScore::normalize(bogus, 0).expect("bogus fixture score normalizes"),
        Some(illegal),
        table.generation(),
    ));

    let result = alpha_beta_search_with_transposition_table(
        &mut position,
        &mut history,
        1,
        &mut table,
    )
    .expect("invalid-root-hint search succeeds");

    assert_ne!(result.score(), bogus);
    assert_ne!(result.best_move(), Some(illegal));
    assert!(result.best_move().is_some_and(|current| {
        position
            .legal_moves()
            .expect("root legal moves generate")
            .iter()
            .any(|candidate| candidate == current)
    }));
    assert_eq!(position, snapshot);
    assert_eq!(history, history_snapshot);
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
}
''')

(root / "docs/RUST_TRANSPOSITION_TABLE_SEARCH_INTEGRATION.md").write_text(r'''# Rust Transposition-Table Search Integration

The overall Task 15 gate connects the fixed-capacity transposition table to production negamax alpha-beta without changing legal-move, terminal, draw, mate-distance, cancellation, or restoration semantics.

## Public entry points

The existing `alpha_beta_search` and `alpha_beta_search_with_cancellation` convenience functions allocate one fresh bounded table using `DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES`, currently 1 MiB.

Callers that want reuse across searches provide a fixed table through:

- `alpha_beta_search_with_transposition_table`;
- `alpha_beta_search_with_cancellation_and_transposition_table`.

A caller-owned table retains entries, advances generation once per valid search, and resets only diagnostic counters. It never resizes and has no map fallback.

## Node sequence

For every non-quiescence node, production search:

1. checks cancellation;
2. generates legal moves and resolves checkmate, stalemate, dead position, repetition, and move-count draws before consulting cached scores;
3. probes by the complete position key, required depth, current ply, and alpha-beta window;
4. accepts exact or bound cutoffs only through the verified probe contract;
5. uses a verified TT move as the highest ordering hint at non-root nodes when no score cutoff is available;
6. searches and restores every active child exactly;
7. classifies the completed fail-soft result as exact, lower, or upper against the original window;
8. normalizes the score at the current ply and stores it only when history-independent reuse is safe.

Depth-zero nodes continue through correctness-first quiescence and are not stored as ordinary alpha-beta entries.

## Reversible-history safety

The position Zobrist key intentionally excludes the halfmove clock and prior repetition path. A score is therefore stored or reused only when `halfmove_clock == 0`, immediately after an irreversible pawn move or capture has reset the relevant repetition and fifty-move history boundary.

At nodes with a nonzero halfmove clock, the probe uses `SuppressedForRepetition`. A verified move may still order already-generated legal moves, but the cached score cannot cut off and the newly searched path-dependent score is not stored. Terminal and draw resolution always happens before probing.

## Root determinism

The root ignores ordering-only TT moves. A root shortcut is accepted only for an exact entry whose stored best move is present in the current legal-token list. This preserves the established deterministic best-move contract when equal root scores exist and prevents corrupt or stale move payloads from bypassing legal search.

Exact entries created below the root omit their best move. Their scores remain reusable internally, but a later search rooted at that position must search legal moves to establish the canonical root move. Exact root entries retain the canonical move and support a one-node warm-table return.

## Bounds and restoration

Completed node scores are stored as:

- upper bounds when the result is at or below the original alpha;
- lower bounds when the result is at or above beta;
- exact values otherwise.

No entry is stored for cancellation, rule failure, history failure, score-conversion failure, terminal/draw resolution, or incomplete child restoration.

## Deterministic usefulness witnesses

The gate includes two independent node-reduction witnesses:

- a fixed narrow-window production-node test where an insufficient-depth TT entry contributes only its move and visits fewer nodes without changing score or best move;
- a caller-owned warm-table test where the second identical full-window search returns the same exact score and canonical best move in one node.

Additional regressions prove reversible-history score suppression, root hint suppression, illegal exact-root move rejection, fixed table capacity, and exact position/history/Zobrist restoration.
''')
