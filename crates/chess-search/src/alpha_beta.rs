use core::fmt;

use chess_core::{
    LegalMoveError, Move, PieceKind, Position, SearchHistory, SearchHistoryError, SearchNullError,
    StaticExchangeError,
};

use crate::{
    aspiration::AspirationWindowOutcome,
    cancellation::NeverCancelled,
    check_extension::decide_check_extension,
    evaluate_with_weights,
    move_ordering::{
        ordered_legal_moves_with_state_and_tt_move_and_see, MoveOrdering, QuietOrderingState,
    },
    quiescence::{search_quiescence_node_with_weights, QuiescenceContext, QuiescenceSearchPolicy},
    search_common::resolved_node_score,
    search_policy::{
        FUTILITY_PRUNING_MARGIN_CENTIPAWNS, FUTILITY_PRUNING_MAXIMUM_DEPTH, LMR_MINIMUM_DEPTH,
        LMR_MINIMUM_LEGAL_MOVES, LMR_MINIMUM_MOVE_INDEX, LMR_MINIMUM_TOTAL_PIECES,
        LMR_REDUCTION_TABLE, NULL_MOVE_MINIMUM_DEPTH, NULL_MOVE_MINIMUM_SIDE_NON_PAWN_PIECES,
        NULL_MOVE_MINIMUM_TOTAL_NON_PAWN_PIECES, NULL_MOVE_REDUCTION,
        NULL_MOVE_VERIFICATION_REDUCTION,
    },
    EvaluationWeights, NullMoveDisabledReason, Score, SearchCancellationProbe,
    SearchDiagnosticEvent, SearchDiagnosticOverflow, SearchDiagnostics, SearchPolicy,
    TranspositionBound, TranspositionEntry, TranspositionProbeError, TranspositionProbeRequest,
    TranspositionProbeScore, TranspositionScore, TranspositionScoreConversionError,
    TranspositionScoreReuse, TranspositionTable, TranspositionTableAllocationError, MAX_MATE_PLY,
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
    pub(crate) diagnostics: SearchDiagnostics,
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

    /// Returns deterministic allocation-free search diagnostics.
    #[must_use]
    pub const fn diagnostics(self) -> SearchDiagnostics {
        self.diagnostics
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

    fn null_child(parent_beta: Score) -> Result<Self, AlphaBetaSearchError> {
        let child_alpha = -parent_beta;
        let child_beta_raw = child_alpha.centipawns().checked_add(1).ok_or(
            AlphaBetaSearchError::NullMoveWindowOutOfRange {
                parent_beta: parent_beta.centipawns(),
            },
        )?;
        let child_beta = Score::from_raw(child_beta_raw).ok_or(
            AlphaBetaSearchError::NullMoveWindowOutOfRange {
                parent_beta: parent_beta.centipawns(),
            },
        )?;
        Self::new(child_alpha, child_beta).ok_or(AlphaBetaSearchError::NullMoveWindowOutOfRange {
            parent_beta: parent_beta.centipawns(),
        })
    }

    fn null_verification(parent_beta: Score) -> Result<Self, AlphaBetaSearchError> {
        let alpha_raw = parent_beta.centipawns().checked_sub(1).ok_or(
            AlphaBetaSearchError::NullMoveWindowOutOfRange {
                parent_beta: parent_beta.centipawns(),
            },
        )?;
        let alpha =
            Score::from_raw(alpha_raw).ok_or(AlphaBetaSearchError::NullMoveWindowOutOfRange {
                parent_beta: parent_beta.centipawns(),
            })?;
        Self::new(alpha, parent_beta).ok_or(AlphaBetaSearchError::NullMoveWindowOutOfRange {
            parent_beta: parent_beta.centipawns(),
        })
    }

    fn pvs_child(parent_alpha: Score) -> Result<Self, AlphaBetaSearchError> {
        let child_beta = -parent_alpha;
        let child_alpha_raw = child_beta.centipawns() - 1;
        let child_alpha =
            Score::from_raw(child_alpha_raw).ok_or(AlphaBetaSearchError::PvsWindowOutOfRange {
                parent_alpha: parent_alpha.centipawns(),
            })?;
        Self::new(child_alpha, child_beta).ok_or(AlphaBetaSearchError::PvsWindowOutOfRange {
            parent_alpha: parent_alpha.centipawns(),
        })
    }
}

/// A fail-loud alpha-beta search error.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum AlphaBetaSearchError {
    /// Position rule processing failed.
    Rules(LegalMoveError),
    /// Search-only null transition processing failed.
    SearchNull(SearchNullError),
    /// Reversible search-line history processing failed.
    History(SearchHistoryError),
    /// SEE capture ordering found contradictory internal move state.
    StaticExchange(StaticExchangeError),
    /// Null-move depth arithmetic could not be represented.
    NullMoveDepthOutOfRange {
        /// Current legal-node depth.
        depth: u16,
        /// Requested reduction.
        reduction: u16,
    },
    /// A one-centipawn null or verification window could not be represented.
    NullMoveWindowOutOfRange {
        /// Parent beta used to derive the narrow window.
        parent_beta: i32,
    },
    /// A one-centipawn PVS child window could not be represented.
    PvsWindowOutOfRange {
        /// Parent alpha whose negated successor was outside the score domain.
        parent_alpha: i32,
    },
    /// Frontier-futility margin arithmetic left the supported score domain.
    FutilityMarginOutOfRange {
        /// Static evaluation before the optimistic margin.
        static_evaluation: i32,
        /// Frozen optimistic margin.
        margin: u16,
    },
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
    /// Deterministic search diagnostic accumulation exceeded `u64`.
    DiagnosticCountOverflow(SearchDiagnosticOverflow),
    /// A non-terminal searched node unexpectedly produced no best move.
    MissingBestMove,
}

impl fmt::Display for AlphaBetaSearchError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Rules(error) => error.fmt(formatter),
            Self::SearchNull(error) => error.fmt(formatter),
            Self::History(error) => error.fmt(formatter),
            Self::StaticExchange(error) => error.fmt(formatter),
            Self::NullMoveDepthOutOfRange { depth, reduction } => write!(
                formatter,
                "cannot reduce null-move depth {depth} by {reduction}"
            ),
            Self::NullMoveWindowOutOfRange { parent_beta } => write!(
                formatter,
                "cannot construct null-move window from parent beta {parent_beta}"
            ),
            Self::PvsWindowOutOfRange { parent_alpha } => write!(
                formatter,
                "cannot construct PVS null window from parent alpha {parent_alpha}"
            ),
            Self::FutilityMarginOutOfRange {
                static_evaluation,
                margin,
            } => write!(
                formatter,
                "cannot add frontier-futility margin {margin} to static evaluation {static_evaluation}"
            ),
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
            Self::DiagnosticCountOverflow(error) => error.fmt(formatter),
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

impl From<SearchNullError> for AlphaBetaSearchError {
    fn from(value: SearchNullError) -> Self {
        Self::SearchNull(value)
    }
}

impl From<SearchHistoryError> for AlphaBetaSearchError {
    fn from(value: SearchHistoryError) -> Self {
        Self::History(value)
    }
}

impl From<StaticExchangeError> for AlphaBetaSearchError {
    fn from(value: StaticExchangeError) -> Self {
        Self::StaticExchange(value)
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

impl From<SearchDiagnosticOverflow> for AlphaBetaSearchError {
    fn from(value: SearchDiagnosticOverflow) -> Self {
        Self::DiagnosticCountOverflow(value)
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
        false,
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

#[derive(Clone, Copy)]
pub(crate) struct AlphaBetaSearchPolicy<'a> {
    window: AlphaBetaWindow,
    check_extension_enabled: bool,
    search_policy: &'a SearchPolicy,
    weights: &'a EvaluationWeights,
}

impl<'a> AlphaBetaSearchPolicy<'a> {
    pub(crate) const fn new(
        window: AlphaBetaWindow,
        check_extension_enabled: bool,
        search_policy: &'a SearchPolicy,
        weights: &'a EvaluationWeights,
    ) -> Self {
        Self {
            window,
            check_extension_enabled,
            search_policy,
            weights,
        }
    }

    pub(crate) const fn window(self) -> AlphaBetaWindow {
        self.window
    }
}

pub(crate) fn alpha_beta_search_window_in_current_generation_with_weights<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    policy: AlphaBetaSearchPolicy<'_>,
    transposition_table: &mut TranspositionTable,
    cancellation: &mut Probe,
) -> Result<AlphaBetaRootWindowResult, AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    validate_search_inputs(position, history, depth)?;
    let result = run_search_in_current_generation_with_weights(
        position,
        history,
        depth,
        policy,
        transposition_table,
        cancellation,
    )?;
    let outcome = if policy.window.is_full() {
        AspirationWindowOutcome::Exact
    } else if result.score() <= policy.window.alpha() {
        AspirationWindowOutcome::FailLow
    } else if result.score() >= policy.window.beta() {
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
    check_extension_enabled: bool,
    transposition_table: &mut TranspositionTable,
    cancellation: &mut Probe,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    run_search_in_current_generation_with_weights(
        position,
        history,
        depth,
        AlphaBetaSearchPolicy::new(
            window,
            check_extension_enabled,
            &SearchPolicy::V0_1,
            &EvaluationWeights::DEFAULT,
        ),
        transposition_table,
        cancellation,
    )
}

fn run_search_in_current_generation_with_weights<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    policy: AlphaBetaSearchPolicy<'_>,
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
        check_extension_enabled: policy.check_extension_enabled,
        maximum_check_extensions_per_line: policy.search_policy.maximum_check_extensions_per_line(),
        maximum_quiescence_ply: policy.search_policy.maximum_quiescence_ply(),
        see_capture_ordering: policy.search_policy.see_capture_ordering_enabled(),
        see_quiescence_pruning: policy.search_policy.see_quiescence_pruning_enabled(),
        delta_pruning: policy.search_policy.delta_pruning_enabled(),
        principal_variation_search: policy.search_policy.principal_variation_search_enabled(),
        late_move_reductions: policy.search_policy.late_move_reductions_enabled(),
        null_move_pruning: policy.search_policy.null_move_pruning_enabled(),
        futility_pruning: policy.search_policy.futility_pruning_enabled(),
        weights: policy.weights,
        cancellation,
    };
    let result = search_node(position, history, depth, 0, policy.window, &mut context);

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
    check_extension_enabled: bool,
    maximum_check_extensions_per_line: u16,
    maximum_quiescence_ply: u16,
    see_capture_ordering: bool,
    see_quiescence_pruning: bool,
    delta_pruning: bool,
    principal_variation_search: bool,
    late_move_reductions: bool,
    null_move_pruning: bool,
    futility_pruning: bool,
    weights: &'a EvaluationWeights,
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
    let extension_budget = if context.check_extension_enabled {
        context.maximum_check_extensions_per_line
    } else {
        0
    };
    search_node_with_extensions(
        position,
        history,
        depth,
        ply,
        SearchPathState::new(extension_budget, NullMoveState::Allowed),
        window,
        context,
    )
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum NullMoveState {
    Allowed,
    SpeculativeSubtree,
    VerificationSubtree,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct SearchPathState {
    extension_budget: u16,
    null_move_state: NullMoveState,
}

impl SearchPathState {
    const fn new(extension_budget: u16, null_move_state: NullMoveState) -> Self {
        Self {
            extension_budget,
            null_move_state,
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct NullMoveSearch {
    speculative_depth: u16,
    speculative_window: AlphaBetaWindow,
    verification_depth: u16,
    verification_window: AlphaBetaWindow,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum NullMoveDecision {
    Disabled(NullMoveDisabledReason),
    Search(NullMoveSearch),
}

fn search_node_with_extensions<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    ply: u16,
    path_state: SearchPathState,
    window: AlphaBetaWindow,
    context: &mut AlphaBetaContext<'_, Probe>,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    let extension_budget = path_state.extension_budget;
    let null_move_state = path_state.null_move_state;

    let mut alpha = window.alpha;
    let original_alpha = window.alpha;
    let beta = window.beta;

    if depth == 0 {
        let quiescence_context = QuiescenceContext {
            ply,
            quiescence_ply: 0,
            maximum_quiescence_ply: context.maximum_quiescence_ply,
        };
        return search_quiescence_node_with_weights(
            position,
            history,
            quiescence_context,
            QuiescenceSearchPolicy::new(
                alpha,
                beta,
                context.ordering,
                context.see_capture_ordering,
                context.see_quiescence_pruning,
                context.delta_pruning,
                context.weights,
            ),
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
            diagnostics: SearchDiagnostics::main_node(),
        });
    }

    let score_reuse =
        transposition_score_reuse(position, context.check_extension_enabled, null_move_state);
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
                        diagnostics: SearchDiagnostics::main_node(),
                    });
                }
            }
        }
    }

    if ply == 0 {
        transposition_table_move = None;
    }

    let mut nodes = 1_u64;
    let mut qnodes = 0_u64;
    let mut selective_depth = ply;
    let mut diagnostics = SearchDiagnostics::main_node();

    if context.null_move_pruning {
        let attempt_event = SearchDiagnosticEvent::NullMoveAttempt;
        diagnostics.record_checked(attempt_event)?;
        context.cancellation.on_search_diagnostic(attempt_event);
        match decide_null_move(
            position,
            depth,
            ply,
            window,
            null_move_state,
            context.weights,
        )? {
            NullMoveDecision::Disabled(reason) => {
                let disabled_event = SearchDiagnosticEvent::NullMoveDisabled { reason };
                diagnostics.record_checked(disabled_event)?;
                context.cancellation.on_search_diagnostic(disabled_event);
            }
            NullMoveDecision::Search(request) => {
                let undo = position.make_search_null()?;
                let speculative = search_node_with_extensions(
                    position,
                    history,
                    request.speculative_depth,
                    ply + 1,
                    SearchPathState::new(extension_budget, NullMoveState::SpeculativeSubtree),
                    request.speculative_window,
                    context,
                );
                let restore = position.unmake_search_null(undo);
                if let Err(error) = restore {
                    return Err(error.into());
                }
                let speculative = speculative?;
                nodes = nodes
                    .checked_add(speculative.nodes)
                    .ok_or(AlphaBetaSearchError::NodeCountOverflow)?;
                qnodes = qnodes
                    .checked_add(speculative.qnodes)
                    .ok_or(AlphaBetaSearchError::NodeCountOverflow)?;
                selective_depth = selective_depth.max(speculative.selective_depth);
                diagnostics = diagnostics.checked_add(speculative.diagnostics)?;
                let speculative_parent_score = -speculative.score;
                if speculative_parent_score >= beta {
                    let fail_high_event = SearchDiagnosticEvent::NullMoveSpeculativeFailHigh;
                    diagnostics.record_checked(fail_high_event)?;
                    context.cancellation.on_search_diagnostic(fail_high_event);
                    let verification_event = SearchDiagnosticEvent::NullMoveVerificationSearch;
                    diagnostics.record_checked(verification_event)?;
                    context
                        .cancellation
                        .on_search_diagnostic(verification_event);
                    let verification = search_node_with_extensions(
                        position,
                        history,
                        request.verification_depth,
                        ply,
                        SearchPathState::new(extension_budget, NullMoveState::VerificationSubtree),
                        request.verification_window,
                        context,
                    )?;
                    nodes = nodes
                        .checked_add(verification.nodes)
                        .ok_or(AlphaBetaSearchError::NodeCountOverflow)?;
                    qnodes = qnodes
                        .checked_add(verification.qnodes)
                        .ok_or(AlphaBetaSearchError::NodeCountOverflow)?;
                    selective_depth = selective_depth.max(verification.selective_depth);
                    diagnostics = diagnostics.checked_add(verification.diagnostics)?;
                    if verification.score >= beta {
                        let cutoff_event = SearchDiagnosticEvent::NullMoveCutoff;
                        diagnostics.record_checked(cutoff_event)?;
                        context.cancellation.on_search_diagnostic(cutoff_event);
                        return Ok(AlphaBetaSearchResult {
                            score: verification.score,
                            best_move: verification.best_move,
                            nodes,
                            qnodes,
                            selective_depth,
                            diagnostics,
                        });
                    }
                }
            }
        }
    }

    let ordered_tokens = ordered_legal_moves_with_state_and_tt_move_and_see(
        position,
        &tokens,
        context.ordering,
        ply,
        context.quiet_ordering,
        transposition_table_move,
        context.see_capture_ordering,
    )?;
    ordered_tokens
        .diagnostics()
        .record_into(&mut diagnostics, &mut *context.cancellation)?;
    let mut best_score = None;
    let mut best_move = None;
    let parent_in_check = position.is_in_check(position.side_to_move());
    let legal_move_count = ordered_tokens.iter().len();
    let total_piece_count = u16::try_from(position.all_occupancy().count())
        .expect("a chess position contains at most 64 pieces");
    let frontier_futility_upper_bound = decide_frontier_futility(
        position,
        depth,
        ply,
        parent_in_check,
        window,
        context.futility_pruning,
        context.weights,
    )?;

    for (move_index, token) in ordered_tokens.iter().enumerate() {
        if context.cancellation.should_cancel() {
            return Err(AlphaBetaSearchError::Cancelled);
        }

        let current = token.move_made();
        let protected_quiet_candidate = context.quiet_ordering.is_killer(ply, current);
        let is_transposition_table_move = transposition_table_move == Some(current);
        let position_undo = position.make_legal_token(token)?;
        let child_in_check = position.is_in_check(position.side_to_move());
        let futility_candidate = frontier_futility_upper_bound.is_some()
            && move_index > 0
            && legal_move_count > 1
            && !child_in_check
            && !current.kind().is_capture()
            && current.promotion().is_none()
            && !is_transposition_table_move
            && !protected_quiet_candidate;
        if futility_candidate {
            let attempt = SearchDiagnosticEvent::FrontierFutilityAttempt;
            diagnostics.record_checked(attempt)?;
            context.cancellation.on_search_diagnostic(attempt);
            if frontier_futility_upper_bound.is_some_and(|upper_bound| upper_bound <= alpha) {
                position.unmake_move(position_undo)?;
                let prune = SearchDiagnosticEvent::FrontierFutilityPrune;
                diagnostics.record_checked(prune)?;
                context.cancellation.on_search_diagnostic(prune);
                continue;
            }
        }
        let history_undo = history.push_position(position);
        let extension = decide_check_extension(
            depth,
            ply,
            child_in_check,
            context.check_extension_enabled,
            extension_budget,
        );
        if let Some(event) = extension.event() {
            context.cancellation.on_check_extension(event);
        }
        let child = search_child_with_optional_lmr(
            position,
            history,
            ChildSearch {
                parent_depth: depth,
                depth: extension.child_depth(),
                ply: ply + 1,
                extension_budget: extension.remaining_budget(),
                move_index,
                legal_move_count,
                total_piece_count,
                current,
                parent_in_check,
                child_in_check,
                is_transposition_table_move,
                protected_quiet_candidate,
                alpha,
                beta,
                null_move_state,
            },
            context,
            &mut diagnostics,
        );
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
        diagnostics = diagnostics.checked_add(child.diagnostics)?;
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
            let event = SearchDiagnosticEvent::BetaCutoff {
                first_move: move_index == 0,
            };
            diagnostics.record_checked(event)?;
            context.cancellation.on_search_diagnostic(event);
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
            diagnostics,
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

fn decide_frontier_futility(
    position: &Position,
    depth: u16,
    ply: u16,
    parent_in_check: bool,
    window: AlphaBetaWindow,
    enabled: bool,
    weights: &EvaluationWeights,
) -> Result<Option<Score>, AlphaBetaSearchError> {
    if !enabled
        || depth == 0
        || depth > FUTILITY_PRUNING_MAXIMUM_DEPTH
        || ply == 0
        || parent_in_check
        || window.alpha().is_mate()
        || window.beta().is_mate()
        || ply >= MAX_MATE_PLY.saturating_sub(depth)
    {
        return Ok(None);
    }
    let static_evaluation = evaluate_with_weights(position, weights);
    let raw = static_evaluation
        .centipawns()
        .checked_add(i32::from(FUTILITY_PRUNING_MARGIN_CENTIPAWNS))
        .ok_or(AlphaBetaSearchError::FutilityMarginOutOfRange {
            static_evaluation: static_evaluation.centipawns(),
            margin: FUTILITY_PRUNING_MARGIN_CENTIPAWNS,
        })?;
    Score::from_raw(raw)
        .map(Some)
        .ok_or(AlphaBetaSearchError::FutilityMarginOutOfRange {
            static_evaluation: static_evaluation.centipawns(),
            margin: FUTILITY_PRUNING_MARGIN_CENTIPAWNS,
        })
}

fn decide_null_move(
    position: &Position,
    depth: u16,
    ply: u16,
    window: AlphaBetaWindow,
    state: NullMoveState,
    weights: &EvaluationWeights,
) -> Result<NullMoveDecision, AlphaBetaSearchError> {
    if state != NullMoveState::Allowed {
        return Ok(NullMoveDecision::Disabled(
            NullMoveDisabledReason::NestedOrVerification,
        ));
    }
    if ply == 0 {
        return Ok(NullMoveDecision::Disabled(NullMoveDisabledReason::Root));
    }
    if position.is_in_check(position.side_to_move()) {
        return Ok(NullMoveDecision::Disabled(NullMoveDisabledReason::InCheck));
    }
    if depth < NULL_MOVE_MINIMUM_DEPTH {
        return Ok(NullMoveDecision::Disabled(
            NullMoveDisabledReason::ShallowDepth,
        ));
    }
    if window.alpha().is_mate()
        || window.beta().is_mate()
        || ply >= MAX_MATE_PLY.saturating_sub(depth)
    {
        return Ok(NullMoveDecision::Disabled(
            NullMoveDisabledReason::MateSensitive,
        ));
    }

    let side = position.side_to_move();
    let side_non_pawn = non_pawn_non_king_count(position, side);
    let total_non_pawn = side_non_pawn + non_pawn_non_king_count(position, side.opposite());
    if side_non_pawn < u32::from(NULL_MOVE_MINIMUM_SIDE_NON_PAWN_PIECES)
        || total_non_pawn < u32::from(NULL_MOVE_MINIMUM_TOTAL_NON_PAWN_PIECES)
    {
        return Ok(NullMoveDecision::Disabled(
            NullMoveDisabledReason::LowNonPawnMaterial,
        ));
    }

    if evaluate_with_weights(position, weights) < window.beta() {
        return Ok(NullMoveDecision::Disabled(
            NullMoveDisabledReason::StaticEvaluationBelowBeta,
        ));
    }

    let speculative_reduction = NULL_MOVE_REDUCTION.checked_add(1).ok_or(
        AlphaBetaSearchError::NullMoveDepthOutOfRange {
            depth,
            reduction: NULL_MOVE_REDUCTION,
        },
    )?;
    let speculative_depth = depth.checked_sub(speculative_reduction).ok_or(
        AlphaBetaSearchError::NullMoveDepthOutOfRange {
            depth,
            reduction: speculative_reduction,
        },
    )?;
    let verification_depth = depth.checked_sub(NULL_MOVE_VERIFICATION_REDUCTION).ok_or(
        AlphaBetaSearchError::NullMoveDepthOutOfRange {
            depth,
            reduction: NULL_MOVE_VERIFICATION_REDUCTION,
        },
    )?;
    Ok(NullMoveDecision::Search(NullMoveSearch {
        speculative_depth,
        speculative_window: AlphaBetaWindow::null_child(window.beta())?,
        verification_depth,
        verification_window: AlphaBetaWindow::null_verification(window.beta())?,
    }))
}

fn non_pawn_non_king_count(position: &Position, color: chess_core::Color) -> u32 {
    [
        PieceKind::Knight,
        PieceKind::Bishop,
        PieceKind::Rook,
        PieceKind::Queen,
    ]
    .into_iter()
    .map(|kind| position.piece_bitboard(color, kind).count())
    .sum()
}

#[derive(Clone, Copy)]
struct ChildSearch {
    parent_depth: u16,
    depth: u16,
    ply: u16,
    extension_budget: u16,
    move_index: usize,
    legal_move_count: usize,
    total_piece_count: u16,
    current: Move,
    parent_in_check: bool,
    child_in_check: bool,
    is_transposition_table_move: bool,
    protected_quiet_candidate: bool,
    alpha: Score,
    beta: Score,
    null_move_state: NullMoveState,
}

fn search_child_with_optional_lmr<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    request: ChildSearch,
    context: &mut AlphaBetaContext<'_, Probe>,
    diagnostics: &mut SearchDiagnostics,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    let Some(reduction) = late_move_reduction(request, context.late_move_reductions) else {
        return search_child_with_optional_pvs(position, history, request, context, diagnostics);
    };

    let reduction_event = SearchDiagnosticEvent::LmrReduction;
    diagnostics.record_checked(reduction_event)?;
    context.cancellation.on_search_diagnostic(reduction_event);

    let mut reduced_request = request;
    reduced_request.depth -= reduction;
    let reduced =
        search_child_with_optional_pvs(position, history, reduced_request, context, diagnostics)?;
    let reduced_parent_score = -reduced.score;
    if reduced_parent_score <= request.alpha {
        return Ok(reduced);
    }

    let fail_high_event = SearchDiagnosticEvent::LmrReducedFailHigh;
    diagnostics.record_checked(fail_high_event)?;
    context.cancellation.on_search_diagnostic(fail_high_event);
    let verification_event = SearchDiagnosticEvent::LmrResearch;
    diagnostics.record_checked(verification_event)?;
    context
        .cancellation
        .on_search_diagnostic(verification_event);
    let exact = search_child_with_optional_pvs(position, history, request, context, diagnostics)?;
    combine_lmr_attempts(reduced, exact)
}

fn late_move_reduction(request: ChildSearch, enabled: bool) -> Option<u16> {
    if !enabled
        || request.parent_depth < LMR_MINIMUM_DEPTH
        || request.move_index == 0
        || request.parent_in_check
        || request.child_in_check
        || request.is_transposition_table_move
        || request.protected_quiet_candidate
        || request.total_piece_count < LMR_MINIMUM_TOTAL_PIECES
        || request.alpha.is_mate()
        || request.beta.is_mate()
        || request.current.kind().is_capture()
        || request.current.promotion().is_some()
    {
        return None;
    }
    let Ok(move_index) = u16::try_from(request.move_index) else {
        return None;
    };
    let Ok(legal_move_count) = u16::try_from(request.legal_move_count) else {
        return None;
    };
    if move_index < LMR_MINIMUM_MOVE_INDEX || legal_move_count < LMR_MINIMUM_LEGAL_MOVES {
        return None;
    }

    let mut selected = 0_u16;
    for (minimum_depth, minimum_move_index, reduction) in LMR_REDUCTION_TABLE {
        if request.parent_depth >= minimum_depth && move_index >= minimum_move_index {
            selected = reduction;
        }
    }
    let maximum = request.depth.saturating_sub(1);
    let bounded = selected.min(maximum);
    (bounded > 0).then_some(bounded)
}

fn search_child_with_optional_pvs<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    request: ChildSearch,
    context: &mut AlphaBetaContext<'_, Probe>,
    diagnostics: &mut SearchDiagnostics,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    let ChildSearch {
        depth,
        ply,
        extension_budget,
        move_index,
        alpha,
        beta,
        null_move_state,
        ..
    } = request;
    let full_window = AlphaBetaWindow {
        alpha: -beta,
        beta: -alpha,
    };
    if !context.principal_variation_search || move_index == 0 {
        return search_node_with_extensions(
            position,
            history,
            depth,
            ply,
            SearchPathState::new(extension_budget, null_move_state),
            full_window,
            context,
        );
    }

    let zero_window_event = SearchDiagnosticEvent::PvsZeroWindowSearch;
    diagnostics.record_checked(zero_window_event)?;
    context.cancellation.on_search_diagnostic(zero_window_event);
    let zero_window = AlphaBetaWindow::pvs_child(alpha)?;
    let narrow = search_node_with_extensions(
        position,
        history,
        depth,
        ply,
        SearchPathState::new(extension_budget, null_move_state),
        zero_window,
        context,
    )?;
    let narrow_parent_score = -narrow.score;
    if narrow_parent_score <= alpha || narrow_parent_score >= beta {
        return Ok(narrow);
    }

    let research_event = SearchDiagnosticEvent::PvsResearch;
    diagnostics.record_checked(research_event)?;
    context.cancellation.on_search_diagnostic(research_event);
    let exact = search_node_with_extensions(
        position,
        history,
        depth,
        ply,
        SearchPathState::new(extension_budget, null_move_state),
        full_window,
        context,
    )?;
    combine_pvs_attempts(narrow, exact)
}

fn combine_pvs_attempts(
    narrow: AlphaBetaSearchResult,
    exact: AlphaBetaSearchResult,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError> {
    combine_search_attempts(narrow, exact)
}

fn combine_lmr_attempts(
    reduced: AlphaBetaSearchResult,
    exact: AlphaBetaSearchResult,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError> {
    combine_search_attempts(reduced, exact)
}

fn combine_search_attempts(
    first: AlphaBetaSearchResult,
    exact: AlphaBetaSearchResult,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError> {
    Ok(AlphaBetaSearchResult {
        score: exact.score,
        best_move: exact.best_move,
        nodes: first
            .nodes
            .checked_add(exact.nodes)
            .ok_or(AlphaBetaSearchError::NodeCountOverflow)?,
        qnodes: first
            .qnodes
            .checked_add(exact.qnodes)
            .ok_or(AlphaBetaSearchError::NodeCountOverflow)?,
        selective_depth: first.selective_depth.max(exact.selective_depth),
        diagnostics: first.diagnostics.checked_add(exact.diagnostics)?,
    })
}

fn transposition_score_reuse(
    position: &Position,
    check_extension_enabled: bool,
    null_move_state: NullMoveState,
) -> TranspositionScoreReuse {
    if null_move_state == NullMoveState::SpeculativeSubtree {
        TranspositionScoreReuse::SuppressedForNullMove
    } else if check_extension_enabled {
        TranspositionScoreReuse::SuppressedForSelectiveExtension
    } else if position.halfmove_clock().get() == 0 {
        TranspositionScoreReuse::Allowed
    } else {
        TranspositionScoreReuse::SuppressedForRepetition
    }
}

#[cfg(test)]
mod futility_policy_tests {
    use chess_core::Position;

    use super::{decide_frontier_futility, AlphaBetaWindow};
    use crate::{
        EvaluationWeights, Score, FUTILITY_PRUNING_MARGIN_CENTIPAWNS,
        FUTILITY_PRUNING_MAXIMUM_DEPTH,
    };

    fn window(alpha: i32, beta: i32) -> AlphaBetaWindow {
        AlphaBetaWindow::new(
            Score::from_raw(alpha).expect("alpha fits"),
            Score::from_raw(beta).expect("beta fits"),
        )
        .expect("valid window")
    }

    #[test]
    fn frozen_frontier_margin_is_typed_and_checked() {
        let position = Position::starting();
        let upper = decide_frontier_futility(
            &position,
            1,
            1,
            false,
            window(-200, 200),
            true,
            &EvaluationWeights::DEFAULT,
        )
        .expect("decision succeeds")
        .expect("frontier is eligible");
        assert_eq!(FUTILITY_PRUNING_MAXIMUM_DEPTH, 1);
        assert_eq!(FUTILITY_PRUNING_MARGIN_CENTIPAWNS, 150);
        assert_eq!(upper.centipawns(), 150);
    }

    #[test]
    fn root_check_deeper_and_mate_sensitive_nodes_are_protected() {
        let position = Position::starting();
        for (depth, ply, parent_in_check, current_window) in [
            (1, 0, false, window(-200, 200)),
            (1, 1, true, window(-200, 200)),
            (2, 1, false, window(-200, 200)),
            (1, 1, false, AlphaBetaWindow::full()),
        ] {
            assert_eq!(
                decide_frontier_futility(
                    &position,
                    depth,
                    ply,
                    parent_in_check,
                    current_window,
                    true,
                    &EvaluationWeights::DEFAULT,
                ),
                Ok(None)
            );
        }
    }
}

#[cfg(test)]
mod null_move_policy_tests {
    use chess_core::Position;

    use super::{
        decide_null_move, transposition_score_reuse, AlphaBetaWindow, NullMoveDecision,
        NullMoveState,
    };
    use crate::{
        EvaluationWeights, NullMoveDisabledReason, Score, TranspositionScoreReuse,
        NULL_MOVE_MINIMUM_DEPTH, NULL_MOVE_REDUCTION, NULL_MOVE_VERIFICATION_REDUCTION,
    };

    fn position(fen: &str) -> Position {
        Position::from_fen(fen).expect("fixture parses")
    }

    fn window(alpha: i32, beta: i32) -> AlphaBetaWindow {
        AlphaBetaWindow::new(
            Score::from_raw(alpha).expect("alpha fits"),
            Score::from_raw(beta).expect("beta fits"),
        )
        .expect("window is valid")
    }

    #[test]
    fn eligible_policy_uses_checked_frozen_depths_and_windows() {
        let current = Position::starting();
        let decision = decide_null_move(
            &current,
            6,
            1,
            window(-200, -100),
            NullMoveState::Allowed,
            &EvaluationWeights::DEFAULT,
        )
        .expect("decision succeeds");
        let NullMoveDecision::Search(request) = decision else {
            panic!("midgame fixture should be eligible: {decision:?}");
        };
        assert_eq!(NULL_MOVE_MINIMUM_DEPTH, 4);
        assert_eq!(NULL_MOVE_REDUCTION, 2);
        assert_eq!(NULL_MOVE_VERIFICATION_REDUCTION, 1);
        assert_eq!(request.speculative_depth, 3);
        assert_eq!(request.verification_depth, 5);
        assert_eq!(request.speculative_window.alpha().centipawns(), 100);
        assert_eq!(request.speculative_window.beta().centipawns(), 101);
        assert_eq!(request.verification_window.alpha().centipawns(), -101);
        assert_eq!(request.verification_window.beta().centipawns(), -100);
    }

    #[test]
    fn conservative_guards_disable_unsafe_contexts() {
        let starting = Position::starting();
        assert_eq!(
            decide_null_move(
                &starting,
                6,
                0,
                window(-200, -100),
                NullMoveState::Allowed,
                &EvaluationWeights::DEFAULT,
            ),
            Ok(NullMoveDecision::Disabled(NullMoveDisabledReason::Root))
        );
        assert_eq!(
            decide_null_move(
                &starting,
                3,
                1,
                window(-200, -100),
                NullMoveState::Allowed,
                &EvaluationWeights::DEFAULT,
            ),
            Ok(NullMoveDecision::Disabled(
                NullMoveDisabledReason::ShallowDepth
            ))
        );
        assert_eq!(
            decide_null_move(
                &starting,
                6,
                1,
                window(-200, -100),
                NullMoveState::SpeculativeSubtree,
                &EvaluationWeights::DEFAULT,
            ),
            Ok(NullMoveDecision::Disabled(
                NullMoveDisabledReason::NestedOrVerification
            ))
        );
        let checked = position("4k3/8/8/8/8/8/4R3/4K3 b - - 0 1");
        assert_eq!(
            decide_null_move(
                &checked,
                6,
                1,
                window(-200, -100),
                NullMoveState::Allowed,
                &EvaluationWeights::DEFAULT,
            ),
            Ok(NullMoveDecision::Disabled(NullMoveDisabledReason::InCheck))
        );
        let pawn_only = position("7k/6pp/8/8/8/8/PP6/K7 w - - 0 1");
        assert_eq!(
            decide_null_move(
                &pawn_only,
                6,
                1,
                window(-200, -100),
                NullMoveState::Allowed,
                &EvaluationWeights::DEFAULT,
            ),
            Ok(NullMoveDecision::Disabled(
                NullMoveDisabledReason::LowNonPawnMaterial
            ))
        );
    }

    #[test]
    fn synthetic_subtree_has_distinct_tt_suppression_and_verification_does_not() {
        let current = Position::starting();
        assert_eq!(
            transposition_score_reuse(&current, false, NullMoveState::SpeculativeSubtree),
            TranspositionScoreReuse::SuppressedForNullMove
        );
        assert_eq!(
            transposition_score_reuse(&current, false, NullMoveState::VerificationSubtree),
            TranspositionScoreReuse::Allowed
        );
    }
}

#[cfg(test)]
mod lmr_policy_tests {
    use chess_core::Position;

    use super::{late_move_reduction, ChildSearch, NullMoveState};
    use crate::Score;

    fn quiet_move(fen: &str, uci: &str) -> chess_core::Move {
        let mut position = Position::from_fen(fen).expect("fixture parses");
        position
            .legal_moves()
            .expect("legal moves generate")
            .iter()
            .find(|current| current.to_uci() == uci)
            .expect("fixture move exists")
    }

    fn request(current: chess_core::Move) -> ChildSearch {
        ChildSearch {
            parent_depth: 4,
            depth: 3,
            ply: 1,
            extension_budget: 0,
            move_index: 4,
            legal_move_count: 20,
            total_piece_count: 32,
            current,
            parent_in_check: false,
            child_in_check: false,
            is_transposition_table_move: false,
            protected_quiet_candidate: false,
            alpha: Score::from_raw(-20).expect("score fits"),
            beta: Score::from_raw(20).expect("score fits"),
            null_move_state: NullMoveState::Allowed,
        }
    }

    #[test]
    fn reduction_table_is_bounded_and_deterministic() {
        let current = quiet_move(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "e2e4",
        );
        assert_eq!(late_move_reduction(request(current), true), Some(1));
        let mut deep = request(current);
        deep.parent_depth = 7;
        deep.depth = 6;
        deep.move_index = 8;
        assert_eq!(late_move_reduction(deep, true), Some(2));
        deep.depth = 1;
        assert_eq!(late_move_reduction(deep, true), None);
        assert_eq!(late_move_reduction(request(current), false), None);
    }

    #[test]
    fn tactical_and_low_mobility_moves_are_never_reduced() {
        let quiet = quiet_move(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "e2e4",
        );
        let mut protected = request(quiet);
        protected.parent_in_check = true;
        assert_eq!(late_move_reduction(protected, true), None);
        protected = request(quiet);
        protected.child_in_check = true;
        assert_eq!(late_move_reduction(protected, true), None);
        protected = request(quiet);
        protected.is_transposition_table_move = true;
        assert_eq!(late_move_reduction(protected, true), None);
        protected = request(quiet);
        protected.protected_quiet_candidate = true;
        assert_eq!(late_move_reduction(protected, true), None);
        protected = request(quiet);
        protected.legal_move_count = 5;
        assert_eq!(late_move_reduction(protected, true), None);
        protected = request(quiet);
        protected.total_piece_count = 3;
        assert_eq!(late_move_reduction(protected, true), None);
        protected = request(quiet);
        protected.alpha = Score::mate_in(4).expect("mate score fits");
        assert_eq!(late_move_reduction(protected, true), None);
        protected = request(quiet);
        protected.beta = Score::mated_in(4).expect("mate score fits");
        assert_eq!(late_move_reduction(protected, true), None);

        let capture = quiet_move("4k3/8/2p5/3p4/4P3/8/8/4K3 w - - 0 1", "e4d5");
        assert_eq!(late_move_reduction(request(capture), true), None);
        let promotion = quiet_move("7k/P7/8/8/8/8/8/K7 w - - 0 1", "a7a8q");
        assert_eq!(late_move_reduction(request(promotion), true), None);
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
            check_extension_enabled: false,
            maximum_check_extensions_per_line: crate::MAX_CHECK_EXTENSIONS_PER_LINE,
            maximum_quiescence_ply: crate::MAX_QUIESCENCE_PLY,
            see_capture_ordering: false,
            see_quiescence_pruning: false,
            delta_pruning: false,
            principal_variation_search: false,
            late_move_reductions: false,
            null_move_pruning: false,
            futility_pruning: false,
            weights: &crate::EvaluationWeights::DEFAULT,
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
            check_extension_enabled: false,
            maximum_check_extensions_per_line: crate::MAX_CHECK_EXTENSIONS_PER_LINE,
            maximum_quiescence_ply: crate::MAX_QUIESCENCE_PLY,
            see_capture_ordering: false,
            see_quiescence_pruning: false,
            delta_pruning: false,
            principal_variation_search: false,
            late_move_reductions: false,
            null_move_pruning: false,
            futility_pruning: false,
            weights: &crate::EvaluationWeights::DEFAULT,
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
                check_extension_enabled: false,
                maximum_check_extensions_per_line: crate::MAX_CHECK_EXTENSIONS_PER_LINE,
                maximum_quiescence_ply: crate::MAX_QUIESCENCE_PLY,
                see_capture_ordering: false,
                see_quiescence_pruning: false,
                delta_pruning: false,
                principal_variation_search: false,
                late_move_reductions: false,
                null_move_pruning: false,
                futility_pruning: false,
                weights: &crate::EvaluationWeights::DEFAULT,
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
    fn diagnostics_are_consistent_and_observationally_inert() {
        let mut first_position = Position::starting();
        let mut first_history = SearchHistory::from_position(&first_position);
        let first = alpha_beta_search(&mut first_position, &mut first_history, 3)
            .expect("diagnostic search succeeds");

        let mut second_position = Position::starting();
        let mut second_history = SearchHistory::from_position(&second_position);
        let second = alpha_beta_search(&mut second_position, &mut second_history, 3)
            .expect("repeated diagnostic search succeeds");

        let diagnostics = first.diagnostics();
        assert_eq!(first.score(), second.score());
        assert_eq!(first.best_move(), second.best_move());
        assert_eq!(
            first.nodes(),
            diagnostics.main_nodes() + diagnostics.quiescence_nodes()
        );
        assert_eq!(first.qnodes(), diagnostics.quiescence_nodes());
        assert!(diagnostics.beta_cutoffs() > 0);
        assert!(diagnostics.first_move_beta_cutoffs() <= diagnostics.beta_cutoffs());
        assert!(diagnostics.reserved_counters_are_zero());
        assert!(!diagnostics.overflowed());
        assert_eq!(diagnostics, second.diagnostics());
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
