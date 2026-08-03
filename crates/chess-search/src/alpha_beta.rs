use core::fmt;

use chess_core::{LegalMoveError, Move, Position, SearchHistory, SearchHistoryError};

use crate::{
    aspiration::AspirationWindowOutcome,
    cancellation::NeverCancelled,
    move_ordering::{ordered_legal_moves_with_state_and_tt_move, MoveOrdering, QuietOrderingState},
    quiescence::{search_quiescence_node, QuiescenceContext},
    search_common::resolved_node_score,
    Score, SearchCancellationProbe, TranspositionBound, TranspositionEntry,
    TranspositionProbeError, TranspositionProbeRequest, TranspositionProbeScore,
    TranspositionScore, TranspositionScoreConversionError, TranspositionScoreReuse,
    TranspositionTable, TranspositionTableAllocationError, MAX_MATE_PLY, MAX_QUIESCENCE_PLY,
};

/// Fixed table size used by the convenience alpha-beta entry points.
pub const DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES: usize = 1;

/// Result of one full-window negamax alpha-beta search.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct AlphaBetaSearchResult {
    pub(crate) score: Score,
    pub(crate) best_move: Option<Move>,
    pub(crate) nodes: u64,
    pub(crate) qnodes: u64,
    pub(crate) selective_depth: u16,
}

impl AlphaBetaSearchResult {
    /// Returns the root score from the side-to-move perspective.
    #[must_use]
    pub const fn score(self) -> Score {
        self.score
    }

    /// Returns the first deterministic best move, or `None` when stand-pat or a terminal is best.
    #[must_use]
    pub const fn best_move(self) -> Option<Move> {
        self.best_move
    }

    /// Returns the number of visited nodes, including the root.
    #[must_use]
    pub const fn nodes(self) -> u64 {
        self.nodes
    }

    /// Returns the number of visited quiescence nodes.
    #[must_use]
    pub const fn qnodes(self) -> u64 {
        self.qnodes
    }

    /// Returns the deepest root-relative ply entered by this search.
    #[must_use]
    pub const fn selective_depth(self) -> u16 {
        self.selective_depth
    }
}

/// Typed classification of one root-window search.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct AlphaBetaRootWindowResult {
    result: AlphaBetaSearchResult,
    outcome: AspirationWindowOutcome,
}

impl AlphaBetaRootWindowResult {
    pub(crate) const fn new(
        result: AlphaBetaSearchResult,
        outcome: AspirationWindowOutcome,
    ) -> Self {
        Self { result, outcome }
    }

    pub(crate) const fn result(self) -> AlphaBetaSearchResult {
        self.result
    }

    pub(crate) const fn outcome(self) -> AspirationWindowOutcome {
        self.outcome
    }
}

/// Valid root alpha-beta window.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct AlphaBetaWindow {
    alpha: Score,
    beta: Score,
}

impl AlphaBetaWindow {
    pub(crate) fn full() -> Self {
        let alpha = Score::mated_in(0).expect("zero-ply mate score is supported");
        let beta = Score::mate_in(0).expect("zero-ply mate score is supported");
        Self { alpha, beta }
    }

    pub(crate) fn new(alpha: Score, beta: Score) -> Option<Self> {
        if alpha < beta {
            Some(Self { alpha, beta })
        } else {
            None
        }
    }

    pub(crate) const fn alpha(self) -> Score {
        self.alpha
    }

    pub(crate) const fn beta(self) -> Score {
        self.beta
    }

    pub(crate) fn is_full(self) -> bool {
        self == Self::full()
    }
}

/// A fail-loud alpha-beta search error.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum AlphaBetaSearchError {
    /// Position rule processing failed.
    Rules(LegalMoveError),
    /// Reversible search-line history processing failed.
    History(SearchHistoryError),
    /// Fixed-capacity transposition-table allocation failed.
    TranspositionTableAllocation(TranspositionTableAllocationError),
    /// A transposition probe could not be evaluated safely.
    TranspositionProbe(TranspositionProbeError),
    /// A searched score could not be normalized for storage.
    TranspositionScoreConversion(TranspositionScoreConversionError),
    /// The supplied history is not rooted at the supplied current position.
    HistoryPositionMismatch {
        /// Current position identity.
        position_zobrist: u64,
        /// Latest history identity, if present.
        history_zobrist: Option<u64>,
    },
    /// Requested depth exceeds the supported mate-distance domain.
    DepthTooLarge {
        /// Requested depth in plies.
        depth: u16,
        /// Largest supported depth in plies.
        maximum: u16,
    },
    /// Cooperative cancellation was requested.
    Cancelled,
    /// The quiescence guard was reached while the side to move remained in check.
    QuiescenceDepthLimitReachedInCheck {
        /// Tactical ply at which expansion stopped.
        quiescence_ply: u16,
        /// Selected tactical-ply maximum.
        maximum: u16,
    },
    /// Recursive node accumulation exceeded `u64`.
    NodeCountOverflow,
    /// A non-terminal searched node unexpectedly produced no best move.
    MissingBestMove,
}

impl fmt::Display for AlphaBetaSearchError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Rules(error) => error.fmt(formatter),
            Self::History(error) => error.fmt(formatter),
            Self::TranspositionTableAllocation(error) => error.fmt(formatter),
            Self::TranspositionProbe(error) => error.fmt(formatter),
            Self::TranspositionScoreConversion(error) => error.fmt(formatter),
            Self::HistoryPositionMismatch {
                position_zobrist,
                history_zobrist,
            } => write!(
                formatter,
                "search history {history_zobrist:?} does not match position {position_zobrist:#018x}"
            ),
            Self::DepthTooLarge { depth, maximum } => write!(
                formatter,
                "alpha-beta depth {depth} exceeds supported maximum {maximum}"
            ),
            Self::Cancelled => formatter.write_str("alpha-beta search cancelled"),
            Self::QuiescenceDepthLimitReachedInCheck {
                quiescence_ply,
                maximum,
            } => write!(
                formatter,
                "quiescence depth limit {maximum} reached in check at tactical ply {quiescence_ply}"
            ),
            Self::NodeCountOverflow => formatter.write_str("alpha-beta node count overflow"),
            Self::MissingBestMove => {
                formatter.write_str("non-terminal alpha-beta node has no best move")
            }
        }
    }
}

impl std::error::Error for AlphaBetaSearchError {}

impl From<LegalMoveError> for AlphaBetaSearchError {
    fn from(value: LegalMoveError) -> Self {
        Self::Rules(value)
    }
}

impl From<SearchHistoryError> for AlphaBetaSearchError {
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
///
/// This convenience entry point never requests cancellation. Use
/// [`alpha_beta_search_with_cancellation`] when an external stop probe is
/// required.
pub fn alpha_beta_search(
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
    let mut transposition_table = TranspositionTable::new(DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES)?;
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
    run_validated_search(position, history, depth, transposition_table, cancellation)
}

pub(crate) fn validate_search_inputs(
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
    prepare_alpha_beta_iteration(position, history, depth, transposition_table)?;
    run_search_in_current_generation(
        position,
        history,
        depth,
        AlphaBetaWindow::full(),
        transposition_table,
        cancellation,
    )
}

pub(crate) fn prepare_alpha_beta_iteration(
    position: &Position,
    history: &SearchHistory,
    depth: u16,
    transposition_table: &mut TranspositionTable,
) -> Result<(), AlphaBetaSearchError> {
    validate_search_inputs(position, history, depth)?;
    transposition_table.advance_generation();
    Ok(())
}

pub(crate) fn alpha_beta_search_window_in_current_generation<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    window: AlphaBetaWindow,
    transposition_table: &mut TranspositionTable,
    cancellation: &mut Probe,
) -> Result<AlphaBetaRootWindowResult, AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    validate_search_inputs(position, history, depth)?;
    let result = run_search_in_current_generation(
        position,
        history,
        depth,
        window,
        transposition_table,
        cancellation,
    )?;
    let outcome = if window.is_full() {
        AspirationWindowOutcome::Exact
    } else if result.score() <= window.alpha() {
        AspirationWindowOutcome::FailLow
    } else if result.score() >= window.beta() {
        AspirationWindowOutcome::FailHigh
    } else {
        AspirationWindowOutcome::Exact
    };
    Ok(AlphaBetaRootWindowResult::new(result, outcome))
}

fn run_search_in_current_generation<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    window: AlphaBetaWindow,
    transposition_table: &mut TranspositionTable,
    cancellation: &mut Probe,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    transposition_table.reset_diagnostics();

    let initial_history_len = history.len();
    let initial_line_len = history.line_len();
    let initial_zobrist = position.zobrist();
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

struct AlphaBetaContext<'a, Probe>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    ordering: MoveOrdering,
    quiet_ordering: &'a mut QuietOrderingState,
    transposition_table: Option<&'a mut TranspositionTable>,
    cancellation: &'a mut Probe,
}

fn search_node<Probe>(
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

    if context.cancellation.on_alpha_beta_node(ply) {
        return Err(AlphaBetaSearchError::Cancelled);
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
            qnodes: 0,
            selective_depth: ply,
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
                let root_best_move = transposition_table_move
                    .filter(|candidate| tokens.iter().any(|token| token.move_made() == *candidate));
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
                        qnodes: 0,
                        selective_depth: ply,
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
    let mut qnodes = 0_u64;
    let mut selective_depth = ply;
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
        qnodes = qnodes
            .checked_add(child.qnodes)
            .ok_or(AlphaBetaSearchError::NodeCountOverflow)?;
        selective_depth = selective_depth.max(child.selective_depth);
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
            qnodes,
            selective_depth,
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
            let normalized_score = TranspositionScore::normalize(result.score, ply)?;
            table.store(TranspositionEntry::new(
                position.zobrist(),
                depth,
                bound,
                normalized_score,
                result.best_move,
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

#[cfg(test)]
mod ordering_tests {
    use chess_core::{LegalMoveToken, Move, Position, SearchHistory};

    use super::{search_node, AlphaBetaContext, AlphaBetaSearchResult, AlphaBetaWindow};
    use crate::{
        cancellation::NeverCancelled,
        move_ordering::{ordered_legal_moves_with_state, MoveOrdering, QuietOrderingState},
        Score, TranspositionBound, TranspositionEntry, TranspositionScore, TranspositionTable,
        TranspositionTableDiagnostics,
    };

    fn full_window() -> AlphaBetaWindow {
        AlphaBetaWindow {
            alpha: Score::mated_in(0).expect("zero-ply mate score is supported"),
            beta: Score::mate_in(0).expect("zero-ply mate score is supported"),
        }
    }

    fn search_with_ordering(
        root: &Position,
        depth: u16,
        window: AlphaBetaWindow,
        ordering: MoveOrdering,
        seeded_killer: Option<Move>,
    ) -> AlphaBetaSearchResult {
        let mut position = root.clone();
        let snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);
        let history_snapshot = history.clone();
        let mut quiet_ordering = QuietOrderingState::new();
        if let Some(current) = seeded_killer {
            quiet_ordering.record_quiet_cutoff(position.side_to_move(), current, depth, 0);
        }
        let mut cancellation = NeverCancelled;
        let mut context = AlphaBetaContext {
            ordering,
            quiet_ordering: &mut quiet_ordering,
            transposition_table: None,
            cancellation: &mut cancellation,
        };
        let result = search_node(&mut position, &mut history, depth, 0, window, &mut context)
            .expect("ordering benchmark search succeeds");

        assert_eq!(position, snapshot);
        assert_eq!(history, history_snapshot);
        assert_eq!(position.zobrist(), position.recomputed_zobrist());
        result
    }

    fn root_move_score(
        position: &mut Position,
        history: &mut SearchHistory,
        token: LegalMoveToken,
    ) -> Score {
        let position_undo = position
            .make_legal_token(token)
            .expect("benchmark token applies");
        let history_undo = history.push_position(position);
        let mut quiet_ordering = QuietOrderingState::new();
        let mut cancellation = NeverCancelled;
        let mut context = AlphaBetaContext {
            ordering: MoveOrdering::Generation,
            quiet_ordering: &mut quiet_ordering,
            transposition_table: None,
            cancellation: &mut cancellation,
        };
        let child = search_node(position, history, 0, 1, full_window(), &mut context);
        history
            .pop_position(history_undo)
            .expect("benchmark history restores");
        position
            .unmake_move(position_undo)
            .expect("benchmark position restores");
        -child.expect("benchmark child search succeeds").score()
    }

    fn quiet_cutoff_witness(root: &Position) -> (Move, Score, usize) {
        let mut position = root.clone();
        let snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);
        let history_snapshot = history.clone();
        let tokens = position
            .legal_move_tokens()
            .expect("benchmark legal tokens generate");
        let mut best_before = Score::mated_in(0).expect("zero-ply mate score is supported");
        let mut witness = None;

        for (index, token) in tokens.iter().enumerate() {
            let current = token.move_made();
            let score = root_move_score(&mut position, &mut history, token);
            let quiet = !current.kind().is_capture() && current.promotion().is_none();
            if index > 0 && quiet && score > best_before {
                witness = Some((current, score, index));
            }
            if score > best_before {
                best_before = score;
            }
        }

        assert_eq!(position, snapshot);
        assert_eq!(history, history_snapshot);
        assert_eq!(position.zobrist(), position.recomputed_zobrist());
        witness.expect("fixed benchmark contains a later improving quiet move")
    }

    fn quiet_order_cutoff_witness(root: &Position) -> (Move, Score, usize) {
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
            TranspositionScore::normalize(Score::ZERO, 1).expect("TT benchmark score normalizes"),
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

    #[test]
    fn quiet_ordering_preserves_full_window_result_deterministically() {
        let root: Position = "7k/8/8/1p2q3/2P1Q3/8/K7/8 w - - 0 1"
            .parse()
            .expect("ordering benchmark FEN is valid");
        let tactical = search_with_ordering(&root, 2, full_window(), MoveOrdering::Tactical, None);
        let first_quiet = search_with_ordering(&root, 2, full_window(), MoveOrdering::Quiet, None);
        let second_quiet = search_with_ordering(&root, 2, full_window(), MoveOrdering::Quiet, None);

        assert_eq!(first_quiet.score(), tactical.score());
        assert_eq!(first_quiet.best_move(), tactical.best_move());
        assert_eq!(first_quiet, second_quiet);
    }

    #[test]
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
        let alpha =
            Score::from_raw(score.centipawns() - 1).expect("TT cutoff score has a predecessor");
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
    use chess_core::{Game, Position, SearchHistory, UciMove};

    use super::{alpha_beta_search, AlphaBetaSearchError};
    use crate::{evaluate, Score, MAX_MATE_PLY};

    fn position(fen: &str) -> Position {
        fen.parse().expect("test FEN is valid")
    }

    fn play(game: &mut Game, text: &str) {
        let syntax = text.parse::<UciMove>().expect("test UCI is valid");
        let current = game
            .legal_moves()
            .expect("legal generation succeeds")
            .iter()
            .find(|candidate| syntax.matches(*candidate))
            .expect("test move is legal");
        let _undo = game.make_move(current).expect("test move is playable");
    }

    fn play_knight_cycle(game: &mut Game) {
        play(game, "g1f3");
        play(game, "g8f6");
        play(game, "f3g1");
        play(game, "f6g8");
    }

    #[test]
    fn depth_zero_evaluates_and_counts_only_the_root() {
        let mut position = Position::starting();
        let snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);
        let history_snapshot = history.clone();
        let expected = evaluate(&position);

        let result = alpha_beta_search(&mut position, &mut history, 0).expect("search succeeds");

        assert_eq!(result.score(), expected);
        assert_eq!(result.best_move(), None);
        assert_eq!(result.nodes(), 1);
        assert_eq!(position, snapshot);
        assert_eq!(history, history_snapshot);
    }

    #[test]
    fn starting_depth_three_prunes_and_restores_exactly() {
        const COMPLETE_DEPTH_THREE_TREE: u64 = 1 + 20 + 400 + 8_902;

        let mut position = Position::starting();
        let snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);
        let history_snapshot = history.clone();

        let result = alpha_beta_search(&mut position, &mut history, 3).expect("search succeeds");

        assert!(result.nodes() < COMPLETE_DEPTH_THREE_TREE);
        let best_move = result.best_move().expect("non-terminal root has a move");
        assert!(position
            .legal_moves()
            .expect("legal generation succeeds")
            .iter()
            .any(|current| current == best_move));
        assert_eq!(position, snapshot);
        assert_eq!(history, history_snapshot);
        assert_eq!(position.zobrist(), position.recomputed_zobrist());
    }

    #[test]
    fn equal_scores_keep_deterministic_first_best_move() {
        let mut first_position = Position::starting();
        let mut first_history = SearchHistory::from_position(&first_position);
        let first = alpha_beta_search(&mut first_position, &mut first_history, 2)
            .expect("first search succeeds");

        let mut second_position = Position::starting();
        let mut second_history = SearchHistory::from_position(&second_position);
        let second = alpha_beta_search(&mut second_position, &mut second_history, 2)
            .expect("second search succeeds");

        assert_eq!(first.score(), second.score());
        assert_eq!(first.best_move(), second.best_move());
        assert_eq!(first.nodes(), second.nodes());
    }

    #[test]
    fn mate_in_one_uses_ply_relative_terminal_scoring() {
        let mut position = position("7k/5Q2/6K1/8/8/8/8/8 w - - 0 1");
        let snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);

        let result = alpha_beta_search(&mut position, &mut history, 1).expect("search succeeds");

        assert_eq!(result.score(), Score::mate_in(1).expect("supported ply"));
        let best_move = result.best_move().expect("mate has a root move");
        assert!(position
            .legal_moves()
            .expect("legal generation succeeds")
            .iter()
            .any(|current| current == best_move));
        assert_eq!(position, snapshot);
    }

    #[test]
    fn terminal_and_repetition_draw_roots_resolve_without_a_move() {
        let mut mate = position("7k/6Q1/6K1/8/8/8/8/8 b - - 150 1");
        let mut mate_history = SearchHistory::from_position(&mate);
        let mate_result =
            alpha_beta_search(&mut mate, &mut mate_history, 3).expect("mate search succeeds");
        assert_eq!(
            mate_result.score(),
            Score::mated_in(0).expect("supported ply")
        );
        assert_eq!(mate_result.best_move(), None);
        assert_eq!(mate_result.nodes(), 1);

        let mut game = Game::starting();
        play_knight_cycle(&mut game);
        play_knight_cycle(&mut game);
        let mut repeated = game.position().clone();
        let repeated_snapshot = repeated.clone();
        let mut history = game.search_history();
        let history_snapshot = history.clone();
        let draw =
            alpha_beta_search(&mut repeated, &mut history, 3).expect("repetition search succeeds");
        assert_eq!(history.repetition_count(&repeated), 3);
        assert_eq!(draw.score(), Score::ZERO);
        assert_eq!(draw.best_move(), None);
        assert_eq!(draw.nodes(), 1);
        assert_eq!(repeated, repeated_snapshot);
        assert_eq!(history, history_snapshot);
    }

    #[test]
    fn mismatched_history_and_excessive_depth_fail_without_mutation() {
        let mut root = Position::starting();
        let snapshot = root.clone();
        let other = position("7k/8/8/8/8/8/8/K7 w - - 0 1");
        let mut history = SearchHistory::from_position(&other);
        let history_snapshot = history.clone();

        assert!(matches!(
            alpha_beta_search(&mut root, &mut history, 1),
            Err(AlphaBetaSearchError::HistoryPositionMismatch { .. })
        ));
        assert_eq!(root, snapshot);
        assert_eq!(history, history_snapshot);

        let mut history = SearchHistory::from_position(&root);
        let history_snapshot = history.clone();
        assert_eq!(
            alpha_beta_search(&mut root, &mut history, MAX_MATE_PLY + 1),
            Err(AlphaBetaSearchError::DepthTooLarge {
                depth: MAX_MATE_PLY + 1,
                maximum: MAX_MATE_PLY,
            })
        );
        assert_eq!(root, snapshot);
        assert_eq!(history, history_snapshot);
    }
}
