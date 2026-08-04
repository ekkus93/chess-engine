from pathlib import Path
from textwrap import dedent


def replace_once(path: Path, old: str, new: str) -> None:
    text = path.read_text()
    old = dedent(old)
    new = dedent(new)
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one match, found {count}: {old[:160]!r}")
    path.write_text(text.replace(old, new, 1))


q = Path("crates/chess-search/src/quiescence.rs")
replace_once(
    q,
    """
    use crate::{
        alpha_beta::{AlphaBetaSearchError, AlphaBetaSearchResult},
        cancellation::NeverCancelled,
        evaluate,
        move_ordering::{ordered_legal_moves, MoveOrdering},
        search_common::resolved_terminal_or_draw_score,
        Score, SearchCancellationProbe, MAX_MATE_PLY,
    };
    """,
    """
    use crate::{
        alpha_beta::{AlphaBetaSearchError, AlphaBetaSearchResult},
        cancellation::NeverCancelled,
        evaluate_with_weights,
        move_ordering::{ordered_legal_moves, MoveOrdering},
        search_common::resolved_terminal_or_draw_score,
        EvaluationWeights, Score, SearchCancellationProbe, MAX_MATE_PLY,
    };
    """,
)
replace_once(
    q,
    """
    pub(crate) fn search_quiescence_node<Probe>(
        position: &mut Position,
        history: &mut SearchHistory,
        context: QuiescenceContext,
        mut alpha: Score,
        beta: Score,
        ordering: MoveOrdering,
        cancellation: &mut Probe,
    ) -> Result<QuiescenceSearchResult, AlphaBetaSearchError>
    where
        Probe: SearchCancellationProbe + ?Sized,
    {
    """,
    """
    pub(crate) fn search_quiescence_node<Probe>(
        position: &mut Position,
        history: &mut SearchHistory,
        context: QuiescenceContext,
        alpha: Score,
        beta: Score,
        ordering: MoveOrdering,
        cancellation: &mut Probe,
    ) -> Result<QuiescenceSearchResult, AlphaBetaSearchError>
    where
        Probe: SearchCancellationProbe + ?Sized,
    {
        search_quiescence_node_with_weights(
            position,
            history,
            context,
            alpha,
            beta,
            ordering,
            &EvaluationWeights::DEFAULT,
            cancellation,
        )
    }

    pub(crate) fn search_quiescence_node_with_weights<Probe>(
        position: &mut Position,
        history: &mut SearchHistory,
        context: QuiescenceContext,
        mut alpha: Score,
        beta: Score,
        ordering: MoveOrdering,
        weights: &EvaluationWeights,
        cancellation: &mut Probe,
    ) -> Result<QuiescenceSearchResult, AlphaBetaSearchError>
    where
        Probe: SearchCancellationProbe + ?Sized,
    {
    """,
)
replace_once(q, "let stand_pat = evaluate(position);", "let stand_pat = evaluate_with_weights(position, weights);")
replace_once(
    q,
    """
    let child = search_quiescence_node(
        position,
        history,
        child_context,
        -beta,
        -alpha,
        ordering,
        cancellation,
    );
    """,
    """
    let child = search_quiescence_node_with_weights(
        position,
        history,
        child_context,
        -beta,
        -alpha,
        ordering,
        weights,
        cancellation,
    );
    """,
)


a = Path("crates/chess-search/src/alpha_beta.rs")
replace_once(
    a,
    "quiescence::{search_quiescence_node, QuiescenceContext},",
    "quiescence::{search_quiescence_node_with_weights, QuiescenceContext},",
)
replace_once(
    a,
    """
    Score, SearchCancellationProbe, TranspositionBound, TranspositionEntry,
    TranspositionProbeError, TranspositionProbeRequest, TranspositionProbeScore,
    """,
    """
    EvaluationWeights, Score, SearchCancellationProbe, TranspositionBound, TranspositionEntry,
    TranspositionProbeError, TranspositionProbeRequest, TranspositionProbeScore,
    """,
)
replace_once(
    a,
    """
    pub(crate) fn alpha_beta_search_window_in_current_generation<Probe>(
        position: &mut Position,
        history: &mut SearchHistory,
        depth: u16,
        window: AlphaBetaWindow,
        check_extension_enabled: bool,
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
            check_extension_enabled,
            transposition_table,
            cancellation,
        )?;
    """,
    """
    pub(crate) fn alpha_beta_search_window_in_current_generation<Probe>(
        position: &mut Position,
        history: &mut SearchHistory,
        depth: u16,
        window: AlphaBetaWindow,
        check_extension_enabled: bool,
        transposition_table: &mut TranspositionTable,
        cancellation: &mut Probe,
    ) -> Result<AlphaBetaRootWindowResult, AlphaBetaSearchError>
    where
        Probe: SearchCancellationProbe + ?Sized,
    {
        alpha_beta_search_window_in_current_generation_with_weights(
            position,
            history,
            depth,
            window,
            check_extension_enabled,
            transposition_table,
            &EvaluationWeights::DEFAULT,
            cancellation,
        )
    }

    pub(crate) fn alpha_beta_search_window_in_current_generation_with_weights<Probe>(
        position: &mut Position,
        history: &mut SearchHistory,
        depth: u16,
        window: AlphaBetaWindow,
        check_extension_enabled: bool,
        transposition_table: &mut TranspositionTable,
        weights: &EvaluationWeights,
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
            window,
            check_extension_enabled,
            transposition_table,
            weights,
            cancellation,
        )?;
    """,
)
replace_once(
    a,
    """
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
        transposition_table.reset_diagnostics();
    """,
    """
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
            window,
            check_extension_enabled,
            transposition_table,
            &EvaluationWeights::DEFAULT,
            cancellation,
        )
    }

    fn run_search_in_current_generation_with_weights<Probe>(
        position: &mut Position,
        history: &mut SearchHistory,
        depth: u16,
        window: AlphaBetaWindow,
        check_extension_enabled: bool,
        transposition_table: &mut TranspositionTable,
        weights: &EvaluationWeights,
        cancellation: &mut Probe,
    ) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>
    where
        Probe: SearchCancellationProbe + ?Sized,
    {
        transposition_table.reset_diagnostics();
    """,
)
replace_once(
    a,
    """
    transposition_table: Some(transposition_table),
    check_extension_enabled,
    cancellation,
    """,
    """
    transposition_table: Some(transposition_table),
    check_extension_enabled,
    weights,
    cancellation,
    """,
)
replace_once(
    a,
    """
    transposition_table: Option<&'a mut TranspositionTable>,
    check_extension_enabled: bool,
    cancellation: &'a mut Probe,
    """,
    """
    transposition_table: Option<&'a mut TranspositionTable>,
    check_extension_enabled: bool,
    weights: &'a EvaluationWeights,
    cancellation: &'a mut Probe,
    """,
)
replace_once(
    a,
    """
    return search_quiescence_node(
        position,
        history,
        quiescence_context,
        alpha,
        beta,
        context.ordering,
        &mut *context.cancellation,
    );
    """,
    """
    return search_quiescence_node_with_weights(
        position,
        history,
        quiescence_context,
        alpha,
        beta,
        context.ordering,
        context.weights,
        &mut *context.cancellation,
    );
    """,
)
text = a.read_text()
for needle in (
    "check_extension_enabled: false,\n            cancellation:",
    "check_extension_enabled: false,\n                cancellation:",
):
    replacement = needle.replace("cancellation:", "weights: &crate::EvaluationWeights::DEFAULT,\n" + needle.split("\n")[-1].split("cancellation:")[0] + "cancellation:")
    text = text.replace(needle, replacement)
a.write_text(text)


i = Path("crates/chess-search/src/iterative_deepening.rs")
replace_once(
    i,
    "alpha_beta_search_window_in_current_generation, prepare_alpha_beta_iteration,",
    "alpha_beta_search_window_in_current_generation,\n        alpha_beta_search_window_in_current_generation_with_weights, prepare_alpha_beta_iteration,",
)
replace_once(
    i,
    "PrincipalVariation, Score, SearchCancellationProbe, TranspositionHashFull, TranspositionTable,",
    "EvaluationWeights, PrincipalVariation, Score, SearchCancellationProbe, TranspositionHashFull,\n    TranspositionTable,",
)
replace_once(
    i,
    """
    pub fn iterative_deepening_search_with_limits_and_transposition_table(
        position: &mut Position,
        history: &mut SearchHistory,
        limits: SearchLimits,
        transposition_table: &mut TranspositionTable,
    ) -> Result<SearchResult, IterativeDeepeningSearchError> {
        iterative_deepening_search_with_limits_and_transposition_table_and_observer(
            position,
            history,
            limits,
            transposition_table,
            |_| {},
        )
    }
    """,
    """
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
        iterative_deepening_search_with_limits_and_clock_and_observer_and_weights(
            position,
            history,
            limits,
            transposition_table,
            WallClock::start(),
            weights,
            |_| {},
        )
    }
    """,
)
replace_once(
    i,
    """
    fn iterative_deepening_search_with_limits_and_clock_and_observer<Clock, Observer>(
        position: &mut Position,
        history: &mut SearchHistory,
        limits: SearchLimits,
        transposition_table: &mut TranspositionTable,
        clock: Clock,
        mut observer: Observer,
    ) -> Result<SearchResult, IterativeDeepeningSearchError>
    where
        Clock: SearchClock,
        Observer: for<'a> FnMut(SearchProgress<'a>),
    {
    """,
    """
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
            &EvaluationWeights::DEFAULT,
            observer,
        )
    }

    fn iterative_deepening_search_with_limits_and_clock_and_observer_and_weights<Clock, Observer>(
        position: &mut Position,
        history: &mut SearchHistory,
        limits: SearchLimits,
        transposition_table: &mut TranspositionTable,
        clock: Clock,
        weights: &EvaluationWeights,
        mut observer: Observer,
    ) -> Result<SearchResult, IterativeDeepeningSearchError>
    where
        Clock: SearchClock,
        Observer: for<'a> FnMut(SearchProgress<'a>),
    {
    """,
)
replace_once(
    i,
    """
    policy,
    transposition_table,
    &mut controller,
    """,
    """
    policy,
    transposition_table,
    weights,
    &mut controller,
    """,
)
replace_once(
    i,
    """
    policy: IterationSearchPolicy,
    transposition_table: &mut TranspositionTable,
    cancellation: &mut Probe,
    """,
    """
    policy: IterationSearchPolicy,
    transposition_table: &mut TranspositionTable,
    weights: &EvaluationWeights,
    cancellation: &mut Probe,
    """,
)
replace_once(
    i,
    """
    },
    transposition_table,
    &mut cancellation,
    """,
    """
    },
    transposition_table,
    &EvaluationWeights::DEFAULT,
    &mut cancellation,
    """,
)
replace_once(
    i,
    """
    check_extension_enabled: bool,
    transposition_table: &mut TranspositionTable,
    cancellation: &mut Probe,
    """,
    """
    check_extension_enabled: bool,
    transposition_table: &mut TranspositionTable,
    weights: &EvaluationWeights,
    cancellation: &mut Probe,
    """,
)
text = i.read_text()
old = dedent(
    """
    policy.check_extension_enabled,
    transposition_table,
    cancellation,
    )?;
    """
)
new = dedent(
    """
    policy.check_extension_enabled,
    transposition_table,
    weights,
    cancellation,
    )?;
    """
)
if text.count(old) != 2:
    raise SystemExit(f"{i}: expected two run_attempt calls, found {text.count(old)}")
text = text.replace(old, new)
i.write_text(text)
replace_once(
    i,
    """
    let result = alpha_beta_search_window_in_current_generation(
        position,
        history,
        depth,
        window,
        check_extension_enabled,
        transposition_table,
        cancellation,
    )
    """,
    """
    let result = alpha_beta_search_window_in_current_generation_with_weights(
        position,
        history,
        depth,
        window,
        check_extension_enabled,
        transposition_table,
        weights,
        cancellation,
    )
    """,
)


lib = Path("crates/chess-search/src/lib.rs")
replace_once(
    lib,
    """
    iterative_deepening_search_with_limits_and_transposition_table,
    iterative_deepening_search_with_limits_and_transposition_table_and_observer,
    """,
    """
    iterative_deepening_search_with_limits_and_transposition_table,
    iterative_deepening_search_with_limits_and_transposition_table_and_observer,
    iterative_deepening_search_with_limits_and_transposition_table_and_weights,
    """,
)
