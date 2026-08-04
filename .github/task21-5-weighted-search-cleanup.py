from pathlib import Path


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


# Keep quiescence below the strict seven-argument boundary by grouping the
# alpha-beta window, ordering, and evaluator into one typed policy.
quiescence = Path("crates/chess-search/src/quiescence.rs")
text = quiescence.read_text()
context_block = '''#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct QuiescenceContext {
    pub(crate) ply: u16,
    pub(crate) quiescence_ply: u16,
    pub(crate) maximum_quiescence_ply: u16,
}
'''
policy_block = context_block + '''
#[derive(Clone, Copy)]
pub(crate) struct QuiescenceSearchPolicy<'a> {
    alpha: Score,
    beta: Score,
    ordering: MoveOrdering,
    weights: &'a EvaluationWeights,
}

impl<'a> QuiescenceSearchPolicy<'a> {
    pub(crate) const fn new(
        alpha: Score,
        beta: Score,
        ordering: MoveOrdering,
        weights: &'a EvaluationWeights,
    ) -> Self {
        Self {
            alpha,
            beta,
            ordering,
            weights,
        }
    }
}
'''
text = replace_once(text, context_block, policy_block, "quiescence policy insertion")
text = replace_once(
    text,
    '''    search_quiescence_node_with_weights(
        position,
        history,
        context,
        alpha,
        beta,
        ordering,
        &EvaluationWeights::DEFAULT,
        cancellation,
    )
''',
    '''    search_quiescence_node_with_weights(
        position,
        history,
        context,
        QuiescenceSearchPolicy::new(
            alpha,
            beta,
            ordering,
            &EvaluationWeights::DEFAULT,
        ),
        cancellation,
    )
''',
    "default quiescence policy",
)
text = replace_once(
    text,
    '''pub(crate) fn search_quiescence_node_with_weights<Probe>(
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
''',
    '''pub(crate) fn search_quiescence_node_with_weights<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    context: QuiescenceContext,
    policy: QuiescenceSearchPolicy<'_>,
    cancellation: &mut Probe,
) -> Result<QuiescenceSearchResult, AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    let QuiescenceSearchPolicy {
        mut alpha,
        beta,
        ordering,
        weights,
    } = policy;
''',
    "weighted quiescence signature",
)
text = replace_once(
    text,
    '''        let child = search_quiescence_node_with_weights(
            position,
            history,
            child_context,
            -beta,
            -alpha,
            ordering,
            weights,
            cancellation,
        );
''',
    '''        let child = search_quiescence_node_with_weights(
            position,
            history,
            child_context,
            QuiescenceSearchPolicy::new(-beta, -alpha, ordering, weights),
            cancellation,
        );
''',
    "recursive quiescence policy",
)
quiescence.write_text(text)


# Remove the redundant internal default wrapper and group window, extension,
# and evaluator into one alpha-beta policy passed through iterative deepening.
alpha_beta = Path("crates/chess-search/src/alpha_beta.rs")
text = alpha_beta.read_text()
start_marker = "pub(crate) fn alpha_beta_search_window_in_current_generation<Probe>("
end_marker = "pub(crate) fn alpha_beta_search_window_in_current_generation_with_weights<Probe>("
if text.count(start_marker) != 1 or text.count(end_marker) != 1:
    raise SystemExit("unexpected alpha-beta weighted-window functions")
start = text.index(start_marker)
end = text.index(end_marker)
if end <= start:
    raise SystemExit("weighted alpha-beta function precedes compatibility wrapper")
text = text[:start] + text[end:]
policy_block = '''#[derive(Clone, Copy)]
pub(crate) struct AlphaBetaSearchPolicy<'a> {
    window: AlphaBetaWindow,
    check_extension_enabled: bool,
    weights: &'a EvaluationWeights,
}

impl<'a> AlphaBetaSearchPolicy<'a> {
    pub(crate) const fn new(
        window: AlphaBetaWindow,
        check_extension_enabled: bool,
        weights: &'a EvaluationWeights,
    ) -> Self {
        Self {
            window,
            check_extension_enabled,
            weights,
        }
    }
}

'''
text = replace_once(text, end_marker, policy_block + end_marker, "alpha-beta policy insertion")
text = replace_once(
    text,
    '''pub(crate) fn alpha_beta_search_window_in_current_generation_with_weights<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    window: AlphaBetaWindow,
    check_extension_enabled: bool,
    transposition_table: &mut TranspositionTable,
    weights: &EvaluationWeights,
    cancellation: &mut Probe,
) -> Result<AlphaBetaRootWindowResult, AlphaBetaSearchError>
''',
    '''pub(crate) fn alpha_beta_search_window_in_current_generation_with_weights<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    policy: AlphaBetaSearchPolicy<'_>,
    transposition_table: &mut TranspositionTable,
    cancellation: &mut Probe,
) -> Result<AlphaBetaRootWindowResult, AlphaBetaSearchError>
''',
    "alpha-beta weighted signature",
)
text = replace_once(
    text,
    '''    let result = run_search_in_current_generation_with_weights(
        position,
        history,
        depth,
        window,
        check_extension_enabled,
        transposition_table,
        weights,
        cancellation,
    )?;
    let outcome = if window.is_full() {
''',
    '''    let result = run_search_in_current_generation_with_weights(
        position,
        history,
        depth,
        policy,
        transposition_table,
        cancellation,
    )?;
    let outcome = if policy.window.is_full() {
''',
    "alpha-beta policy call",
)
text = replace_once(text, "result.score() <= window.alpha()", "result.score() <= policy.window.alpha()", "alpha fail-low")
text = replace_once(text, "result.score() >= window.beta()", "result.score() >= policy.window.beta()", "alpha fail-high")
text = replace_once(
    text,
    '''    run_search_in_current_generation_with_weights(
        position,
        history,
        depth,
        window,
        check_extension_enabled,
        transposition_table,
        &EvaluationWeights::DEFAULT,
        cancellation,
    )
''',
    '''    run_search_in_current_generation_with_weights(
        position,
        history,
        depth,
        AlphaBetaSearchPolicy::new(
            window,
            check_extension_enabled,
            &EvaluationWeights::DEFAULT,
        ),
        transposition_table,
        cancellation,
    )
''',
    "default alpha-beta policy",
)
text = replace_once(
    text,
    '''fn run_search_in_current_generation_with_weights<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    window: AlphaBetaWindow,
    check_extension_enabled: bool,
    transposition_table: &mut TranspositionTable,
    weights: &EvaluationWeights,
    cancellation: &mut Probe,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>
''',
    '''fn run_search_in_current_generation_with_weights<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
    policy: AlphaBetaSearchPolicy<'_>,
    transposition_table: &mut TranspositionTable,
    cancellation: &mut Probe,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>
''',
    "alpha-beta run signature",
)
text = replace_once(
    text,
    '''        check_extension_enabled,
        weights,
        cancellation,
    };
    let result = search_node(position, history, depth, 0, window, &mut context);
''',
    '''        check_extension_enabled: policy.check_extension_enabled,
        weights: policy.weights,
        cancellation,
    };
    let result = search_node(position, history, depth, 0, policy.window, &mut context);
''',
    "alpha-beta context policy",
)
text = replace_once(
    text,
    "    quiescence::{search_quiescence_node_with_weights, QuiescenceContext},",
    "    quiescence::{\n        search_quiescence_node_with_weights, QuiescenceContext, QuiescenceSearchPolicy,\n    },",
    "quiescence policy import",
)
text = replace_once(
    text,
    '''        return search_quiescence_node_with_weights(
            position,
            history,
            quiescence_context,
            alpha,
            beta,
            context.ordering,
            context.weights,
            &mut *context.cancellation,
        );
''',
    '''        return search_quiescence_node_with_weights(
            position,
            history,
            quiescence_context,
            QuiescenceSearchPolicy::new(
                alpha,
                beta,
                context.ordering,
                context.weights,
            ),
            &mut *context.cancellation,
        );
''',
    "alpha-beta quiescence policy",
)
alpha_beta.write_text(text)


# Put the evaluator reference inside the existing iteration policy and pass one
# alpha-beta policy into each aspiration attempt.
iterative = Path("crates/chess-search/src/iterative_deepening.rs")
text = iterative.read_text()
text = replace_once(
    text,
    "        alpha_beta_search_window_in_current_generation,\n",
    "",
    "default alpha-beta import",
)
text = replace_once(
    text,
    "        alpha_beta_search_window_in_current_generation_with_weights, prepare_alpha_beta_iteration,",
    "        alpha_beta_search_window_in_current_generation_with_weights,\n        prepare_alpha_beta_iteration, AlphaBetaSearchPolicy,",
    "alpha-beta policy import",
)
text = replace_once(
    text,
    '''struct IterationSearchPolicy {
    half_width_centipawns: i32,
    check_extension_enabled: bool,
}
''',
    '''struct IterationSearchPolicy<'a> {
    half_width_centipawns: i32,
    check_extension_enabled: bool,
    weights: &'a EvaluationWeights,
}
''',
    "iteration policy definition",
)
text = replace_once(
    text,
    '''            IterationSearchPolicy {
                half_width_centipawns: DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS,
                check_extension_enabled,
            },
            transposition_table,
            weights,
            &mut controller,
''',
    '''            IterationSearchPolicy {
                half_width_centipawns: DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS,
                check_extension_enabled,
                weights,
            },
            transposition_table,
            &mut controller,
''',
    "limited iteration policy",
)
text = replace_once(
    text,
    '''        IterationSearchPolicy {
            half_width_centipawns,
            check_extension_enabled: false,
        },
        transposition_table,
        &EvaluationWeights::DEFAULT,
        &mut cancellation,
''',
    '''        IterationSearchPolicy {
            half_width_centipawns,
            check_extension_enabled: false,
            weights: &EvaluationWeights::DEFAULT,
        },
        transposition_table,
        &mut cancellation,
''',
    "default iteration policy",
)
text = replace_once(
    text,
    '''    policy: IterationSearchPolicy,
    transposition_table: &mut TranspositionTable,
    weights: &EvaluationWeights,
    cancellation: &mut Probe,
''',
    '''    policy: IterationSearchPolicy<'_>,
    transposition_table: &mut TranspositionTable,
    cancellation: &mut Probe,
''',
    "iteration search signature",
)
text = replace_once(
    text,
    '''        initial_window,
        policy.check_extension_enabled,
        transposition_table,
        weights,
        cancellation,
''',
    '''        AlphaBetaSearchPolicy::new(
            initial_window,
            policy.check_extension_enabled,
            policy.weights,
        ),
        transposition_table,
        cancellation,
''',
    "initial aspiration policy",
)
text = replace_once(
    text,
    '''                AlphaBetaWindow::full(),
                policy.check_extension_enabled,
                transposition_table,
                weights,
                cancellation,
''',
    '''                AlphaBetaSearchPolicy::new(
                    AlphaBetaWindow::full(),
                    policy.check_extension_enabled,
                    policy.weights,
                ),
                transposition_table,
                cancellation,
''',
    "retry aspiration policy",
)
text = replace_once(
    text,
    '''    window: AlphaBetaWindow,
    check_extension_enabled: bool,
    transposition_table: &mut TranspositionTable,
    weights: &EvaluationWeights,
    cancellation: &mut Probe,
''',
    '''    policy: AlphaBetaSearchPolicy<'_>,
    transposition_table: &mut TranspositionTable,
    cancellation: &mut Probe,
''',
    "attempt signature",
)
text = replace_once(
    text,
    '''        depth,
        window,
        check_extension_enabled,
        transposition_table,
        weights,
        cancellation,
''',
    '''        depth,
        policy,
        transposition_table,
        cancellation,
''',
    "weighted alpha-beta attempt",
)
iterative.write_text(text)
