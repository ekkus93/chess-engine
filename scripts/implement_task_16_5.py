#!/usr/bin/env python3
from pathlib import Path
import sys

root = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else Path.cwd()


def read(path: str) -> str:
    return (root / path).read_text(encoding="utf-8")


def write(path: str, content: str) -> None:
    target = root / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one match, found {count}")
    return text.replace(old, new, 1)


# Formalize the production cancellation interval.
write(
    "crates/chess-search/src/cancellation.rs",
    '''/// Maximum production-node interval between cooperative cancellation checks.
///
/// The current correctness-first policy checks every alpha-beta and quiescence
/// node. Child boundaries also check before applying the next move, so an
/// observed request cannot require completion of an arbitrary subtree or depth.
pub const CANCELLATION_CHECK_INTERVAL_NODES: u64 = 1;

/// Cooperative cancellation source for recursive search.
///
/// Search calls `on_node` exactly once for each production node and calls
/// `should_cancel` at child boundaries. Returning `true` requests an orderly
/// unwind: active line-history entries are popped and active position moves are
/// unmade before the cancellation error reaches the root.
pub trait SearchCancellationProbe {
    /// Returns whether the current search should stop at a non-node checkpoint.
    fn should_cancel(&mut self) -> bool;

    /// Enters one production search node and returns whether it should stop.
    ///
    /// The default checks the source for every node, which satisfies
    /// [`CANCELLATION_CHECK_INTERVAL_NODES`]. Limit-aware controllers override
    /// this hook to account one node while retaining the same polling bound.
    fn on_node(&mut self) -> bool {
        self.should_cancel()
    }
}

impl<Callback> SearchCancellationProbe for Callback
where
    Callback: FnMut() -> bool,
{
    fn should_cancel(&mut self) -> bool {
        self()
    }
}

#[derive(Default)]
pub(crate) struct NeverCancelled;

impl SearchCancellationProbe for NeverCancelled {
    fn should_cancel(&mut self) -> bool {
        false
    }
}
''',
)

# Reuse the fail-loud root validation before computing an emergency move.
alpha_path = "crates/chess-search/src/alpha_beta.rs"
alpha = read(alpha_path)
alpha = replace_once(
    alpha,
    "fn validate_search_inputs(\n",
    "pub(crate) fn validate_search_inputs(\n",
    "alpha-beta root validation visibility",
)
write(alpha_path, alpha)

# Add typed no-completed-iteration fallback semantics to limited iterative search.
iterative_path = "crates/chess-search/src/iterative_deepening.rs"
iterative = read(iterative_path)
iterative = replace_once(
    iterative,
    """        alpha_beta_search_window_in_current_generation, prepare_alpha_beta_iteration,
        AlphaBetaRootWindowResult, AlphaBetaSearchError, AlphaBetaSearchResult, AlphaBetaWindow,
""",
    """        alpha_beta_search_window_in_current_generation, prepare_alpha_beta_iteration,
        validate_search_inputs, AlphaBetaRootWindowResult, AlphaBetaSearchError,
        AlphaBetaSearchResult, AlphaBetaWindow,
""",
    "iterative alpha-beta imports",
)
fallback_enum = '''/// Deterministic emergency result when cancellation precedes depth one.
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

'''
iterative = replace_once(
    iterative,
    "/// Exact completed iterations plus the limit that stopped the request.\n",
    fallback_enum + "/// Exact completed iterations plus the limit that stopped the request.\n",
    "fallback enum insertion",
)
iterative = replace_once(
    iterative,
    """pub struct LimitedIterativeDeepeningSearchResult {
    completed: IterativeDeepeningSearchResult,
    termination: SearchLimitTermination,
    searched_nodes: u64,
}
""",
    """pub struct LimitedIterativeDeepeningSearchResult {
    completed: IterativeDeepeningSearchResult,
    termination: SearchLimitTermination,
    searched_nodes: u64,
    fallback: Option<SearchCancellationFallback>,
}
""",
    "limited result fields",
)
iterative = replace_once(
    iterative,
    """    pub fn incomplete_nodes(&self) -> u64 {
        self.searched_nodes
            .saturating_sub(self.completed.total_nodes())
    }
}
""",
    """    pub fn incomplete_nodes(&self) -> u64 {
        self.searched_nodes
            .saturating_sub(self.completed.total_nodes())
    }

    /// Returns the deterministic emergency result when no depth completed.
    ///
    /// Once any exact iteration completes, that iteration is authoritative and
    /// this method returns `None`.
    #[must_use]
    pub const fn fallback(&self) -> Option<SearchCancellationFallback> {
        self.fallback
    }
}
""",
    "limited result fallback accessor",
)
iterative = replace_once(
    iterative,
    """    let mut controller = SearchLimitController::new(limits, clock)
        .map_err(IterativeDeepeningSearchError::InvalidLimits)?;
    let mut iterations: Vec<IterativeDeepeningIteration> = Vec::new();
""",
    """    let mut controller = SearchLimitController::new(limits, clock)
        .map_err(IterativeDeepeningSearchError::InvalidLimits)?;
    let fallback = cancellation_fallback(position, history)?;
    let mut iterations: Vec<IterativeDeepeningIteration> = Vec::new();
""",
    "fallback preparation",
)
iterative = iterative.replace(
    """                controller.visited_nodes(),
            ));
""",
    """                controller.visited_nodes(),
                fallback,
            ));
""",
)
if iterative.count("fallback,\n            ));") != 1:
    raise RuntimeError("boundary limited-result fallback insertion failed")
iterative = iterative.replace(
    """                            controller.visited_nodes(),
                        ));
""",
    """                            controller.visited_nodes(),
                            fallback,
                        ));
""",
)
if iterative.count("fallback,\n                        ));") != 1:
    raise RuntimeError("cancelled limited-result fallback insertion failed")
old_limited = '''fn limited_result(
    iterations: Vec<IterativeDeepeningIteration>,
    total_nodes: u64,
    termination: SearchLimitTermination,
    searched_nodes: u64,
) -> LimitedIterativeDeepeningSearchResult {
    LimitedIterativeDeepeningSearchResult {
        completed: IterativeDeepeningSearchResult {
            iterations,
            total_nodes,
        },
        termination,
        searched_nodes,
    }
}
'''
new_limited = '''fn cancellation_fallback(
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
    Ok(tokens.iter().next().map_or(
        SearchCancellationFallback::NoLegalMove,
        |token| SearchCancellationFallback::FirstLegalMove(token.move_made()),
    ))
}

fn limited_result(
    iterations: Vec<IterativeDeepeningIteration>,
    total_nodes: u64,
    termination: SearchLimitTermination,
    searched_nodes: u64,
    root_fallback: SearchCancellationFallback,
) -> LimitedIterativeDeepeningSearchResult {
    let fallback = iterations.is_empty().then_some(root_fallback);
    LimitedIterativeDeepeningSearchResult {
        completed: IterativeDeepeningSearchResult {
            iterations,
            total_nodes,
        },
        termination,
        searched_nodes,
        fallback,
    }
}
'''
iterative = replace_once(iterative, old_limited, new_limited, "limited result constructor")
write(iterative_path, iterative)

# Public exports.
lib_path = "crates/chess-search/src/lib.rs"
lib = read(lib_path)
lib = replace_once(
    lib,
    "pub use cancellation::SearchCancellationProbe;",
    "pub use cancellation::{SearchCancellationProbe, CANCELLATION_CHECK_INTERVAL_NODES};",
    "cancellation exports",
)
lib = replace_once(
    lib,
    """    IterativeDeepeningSearchError, IterativeDeepeningSearchResult,
    LimitedIterativeDeepeningSearchResult,
""",
    """    IterativeDeepeningSearchError, IterativeDeepeningSearchResult,
    LimitedIterativeDeepeningSearchResult, SearchCancellationFallback,
""",
    "fallback export",
)
write(lib_path, lib)

# Expand the limit integration coverage with formal fallback cases.
write(
    "crates/chess-search/tests/search_limits.rs",
    '''use std::time::Duration;

use chess_core::{Move, Position, SearchHistory};
use chess_search::{
    iterative_deepening_search, iterative_deepening_search_with_limits,
    iterative_deepening_search_with_limits_and_transposition_table, IterativeDeepeningSearchError,
    SearchCancellationFallback, SearchLimitError, SearchLimitTermination, SearchLimits,
    SearchStopFlag, TranspositionTable,
};

fn benchmark_position() -> Position {
    "7k/8/8/1p2q3/2P1Q3/8/K7/8 w - - 0 1"
        .parse()
        .expect("search-limit benchmark FEN is valid")
}

fn first_legal_move(root: &Position) -> Move {
    let mut position = root.clone();
    position
        .legal_moves()
        .expect("fallback legal generation succeeds")
        .iter()
        .next()
        .expect("benchmark root has a legal move")
}

fn assert_restored(
    position: &Position,
    position_snapshot: &Position,
    history: &SearchHistory,
    history_snapshot: &SearchHistory,
) {
    assert_eq!(position, position_snapshot);
    assert_eq!(history, history_snapshot);
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
    assert_eq!(history.current_zobrist(), Some(position.zobrist()));
}

#[test]
fn depth_limit_matches_fixed_iterative_deepening_exactly() {
    let root = benchmark_position();
    let mut expected_position = root.clone();
    let mut expected_history = SearchHistory::from_position(&expected_position);
    let expected = iterative_deepening_search(&mut expected_position, &mut expected_history, 3)
        .expect("fixed iterative search succeeds");

    let mut position = root.clone();
    let position_snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let result = iterative_deepening_search_with_limits(
        &mut position,
        &mut history,
        SearchLimits::new().with_depth(3),
    )
    .expect("depth-limited search succeeds");

    assert_eq!(
        result.termination(),
        SearchLimitTermination::Depth { depth: 3 }
    );
    assert_eq!(result.completed(), &expected);
    assert_eq!(result.searched_nodes(), expected.total_nodes());
    assert_eq!(result.incomplete_nodes(), 0);
    assert_eq!(result.fallback(), None);
    assert_restored(&position, &position_snapshot, &history, &history_snapshot);
}

#[test]
fn node_limit_discards_partial_depth_and_preserves_last_exact_iteration() {
    let root = benchmark_position();
    let mut depth_one_position = root.clone();
    let mut depth_one_history = SearchHistory::from_position(&depth_one_position);
    let depth_one = iterative_deepening_search(&mut depth_one_position, &mut depth_one_history, 1)
        .expect("depth-one baseline succeeds");
    let depth_one_nodes = depth_one.total_nodes();
    let node_limit = depth_one_nodes
        .checked_add(1)
        .expect("small test node limit fits");

    let mut position = root.clone();
    let position_snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let mut table = TranspositionTable::new(1).expect("bounded table allocates");
    let result = iterative_deepening_search_with_limits_and_transposition_table(
        &mut position,
        &mut history,
        SearchLimits::new().with_nodes(node_limit),
        &mut table,
    )
    .expect("node-limited search returns completed work");

    assert_eq!(
        result.termination(),
        SearchLimitTermination::Nodes { nodes: node_limit }
    );
    assert_eq!(result.completed().completed_depth(), 1);
    assert_eq!(result.completed(), &depth_one);
    assert_eq!(result.searched_nodes(), node_limit);
    assert_eq!(result.incomplete_nodes(), 1);
    assert_eq!(result.fallback(), None);
    assert_eq!(table.generation(), 2);
    assert_restored(&position, &position_snapshot, &history, &history_snapshot);
}

#[test]
fn node_limit_before_depth_one_returns_the_deterministic_legal_fallback() {
    let root = benchmark_position();
    let expected = first_legal_move(&root);
    let mut position = root.clone();
    let position_snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let mut table = TranspositionTable::new(1).expect("bounded table allocates");

    let result = iterative_deepening_search_with_limits_and_transposition_table(
        &mut position,
        &mut history,
        SearchLimits::new().with_nodes(1),
        &mut table,
    )
    .expect("one-node cancellation returns a fallback");

    assert_eq!(
        result.termination(),
        SearchLimitTermination::Nodes { nodes: 1 }
    );
    assert_eq!(result.completed().completed_depth(), 0);
    assert_eq!(result.searched_nodes(), 1);
    assert_eq!(result.incomplete_nodes(), 1);
    assert_eq!(
        result.fallback(),
        Some(SearchCancellationFallback::FirstLegalMove(expected))
    );
    assert_eq!(result.fallback().and_then(|fallback| fallback.best_move()), Some(expected));
    assert_eq!(table.generation(), 1);
    assert_restored(&position, &position_snapshot, &history, &history_snapshot);
}

#[test]
fn preset_stop_flag_stops_finite_and_infinite_requests_before_mutation() {
    for limits in [
        SearchLimits::new().with_depth(3),
        SearchLimits::new().infinite(),
    ] {
        let stop = SearchStopFlag::new();
        stop.request_stop();
        let mut position = benchmark_position();
        let expected = first_legal_move(&position);
        let position_snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);
        let history_snapshot = history.clone();
        let mut table = TranspositionTable::new(1).expect("bounded table allocates");
        let result = iterative_deepening_search_with_limits_and_transposition_table(
            &mut position,
            &mut history,
            limits.with_stop_flag(stop),
            &mut table,
        )
        .expect("preset stop is a normal limited-search termination");

        assert_eq!(result.termination(), SearchLimitTermination::ExplicitStop);
        assert_eq!(result.completed().completed_depth(), 0);
        assert_eq!(result.searched_nodes(), 0);
        assert_eq!(
            result.fallback(),
            Some(SearchCancellationFallback::FirstLegalMove(expected))
        );
        assert_eq!(table.generation(), 0);
        assert_restored(&position, &position_snapshot, &history, &history_snapshot);
    }
}

#[test]
fn terminal_preset_stop_returns_an_explicit_no_legal_move_fallback() {
    let stop = SearchStopFlag::new();
    stop.request_stop();
    let mut position: Position = "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1"
        .parse()
        .expect("terminal fallback FEN is valid");
    let position_snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let mut table = TranspositionTable::new(1).expect("bounded table allocates");

    let result = iterative_deepening_search_with_limits_and_transposition_table(
        &mut position,
        &mut history,
        SearchLimits::new().with_depth(3).with_stop_flag(stop),
        &mut table,
    )
    .expect("terminal preset stop returns a typed fallback");

    assert_eq!(result.termination(), SearchLimitTermination::ExplicitStop);
    assert_eq!(result.completed().completed_depth(), 0);
    assert_eq!(result.fallback(), Some(SearchCancellationFallback::NoLegalMove));
    assert_eq!(result.fallback().and_then(|fallback| fallback.best_move()), None);
    assert_eq!(table.generation(), 0);
    assert_restored(&position, &position_snapshot, &history, &history_snapshot);
}

#[test]
fn invalid_limit_combinations_fail_before_table_or_root_mutation() {
    let mut position = benchmark_position();
    let position_snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let mut table = TranspositionTable::new(1).expect("bounded table allocates");

    let error = iterative_deepening_search_with_limits_and_transposition_table(
        &mut position,
        &mut history,
        SearchLimits::new()
            .with_soft_time(Duration::from_millis(2))
            .with_hard_time(Duration::from_millis(1)),
        &mut table,
    )
    .expect_err("soft time above hard time is invalid");
    assert_eq!(
        error,
        IterativeDeepeningSearchError::InvalidLimits(SearchLimitError::SoftTimeExceedsHardTime {
            soft: Duration::from_millis(2),
            hard: Duration::from_millis(1),
        })
    );

    let stop = SearchStopFlag::new();
    let error = iterative_deepening_search_with_limits_and_transposition_table(
        &mut position,
        &mut history,
        SearchLimits::new()
            .infinite()
            .with_depth(1)
            .with_stop_flag(stop),
        &mut table,
    )
    .expect_err("infinite mode rejects automatic limits");
    assert_eq!(
        error,
        IterativeDeepeningSearchError::InvalidLimits(
            SearchLimitError::InfiniteConflictsWithAutomaticLimit
        )
    );

    assert_eq!(table.generation(), 0);
    assert_restored(&position, &position_snapshot, &history, &history_snapshot);
}
''',
)

# Deterministic in-tree response and exact unwind witness.
write(
    "crates/chess-search/tests/search_responsive_cancellation.rs",
    '''use chess_core::{Position, SearchHistory};
use chess_search::{
    alpha_beta_search_with_cancellation, AlphaBetaSearchError, SearchCancellationProbe,
    CANCELLATION_CHECK_INTERVAL_NODES,
};

struct BoundaryRequestProbe {
    entered_nodes: u64,
    request_after_nodes: u64,
    requested_at_node: Option<u64>,
    observed_at_node: Option<u64>,
}

impl BoundaryRequestProbe {
    const fn new(request_after_nodes: u64) -> Self {
        Self {
            entered_nodes: 0,
            request_after_nodes,
            requested_at_node: None,
            observed_at_node: None,
        }
    }

    fn observe(&mut self) {
        if self.observed_at_node.is_none() {
            self.observed_at_node = Some(self.entered_nodes);
        }
    }

    fn response_nodes(&self) -> u64 {
        self.observed_at_node
            .expect("request is observed")
            .saturating_sub(self.requested_at_node.expect("request is issued"))
    }
}

impl SearchCancellationProbe for BoundaryRequestProbe {
    fn should_cancel(&mut self) -> bool {
        if self.requested_at_node.is_some() {
            self.observe();
            return true;
        }
        if self.entered_nodes >= self.request_after_nodes {
            self.requested_at_node = Some(self.entered_nodes);
        }
        false
    }

    fn on_node(&mut self) -> bool {
        if self.requested_at_node.is_some() {
            self.observe();
            return true;
        }
        self.entered_nodes = self.entered_nodes.saturating_add(1);
        false
    }
}

#[test]
fn in_tree_request_stops_within_the_node_bound_and_restores_every_root_invariant() {
    let mut position = Position::starting();
    let position_snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let mut probe = BoundaryRequestProbe::new(64);

    let result = alpha_beta_search_with_cancellation(&mut position, &mut history, 5, &mut probe);

    assert_eq!(result, Err(AlphaBetaSearchError::Cancelled));
    assert!(probe.requested_at_node.is_some());
    assert!(probe.observed_at_node.is_some());
    assert!(
        probe.response_nodes() <= CANCELLATION_CHECK_INTERVAL_NODES,
        "request consumed {} additional nodes with a {}-node bound",
        probe.response_nodes(),
        CANCELLATION_CHECK_INTERVAL_NODES
    );
    assert_eq!(position, position_snapshot);
    assert_eq!(history, history_snapshot);
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
    assert_eq!(history.current_zobrist(), Some(position.zobrist()));
}
''',
)

# Add a reproducible cancellation-response benchmark to chess-tools.
tools_lib_path = "crates/chess-tools/src/lib.rs"
tools = read(tools_lib_path)
tools = replace_once(
    tools,
    "use chess_core::{Move, Position, UciMove};",
    "use chess_core::{Move, Position, SearchHistory, UciMove};",
    "chess-tools core imports",
)
tools = replace_once(
    tools,
    """    evaluate_term, evaluate_trace as search_evaluate_trace, EvaluationTerm, EvaluationTrace,
    EvaluationWeightSet, Score, TranspositionBound, TranspositionEntry, TranspositionProbeRequest,
    TranspositionProbeScore, TranspositionScore, TranspositionScoreReuse, TranspositionStoreAction,
    TranspositionTable,
""",
    """    alpha_beta_search_with_cancellation, evaluate_term,
    evaluate_trace as search_evaluate_trace, AlphaBetaSearchError, EvaluationTerm,
    EvaluationTrace, EvaluationWeightSet, Score, SearchCancellationProbe, TranspositionBound,
    TranspositionEntry, TranspositionProbeRequest, TranspositionProbeScore, TranspositionScore,
    TranspositionScoreReuse, TranspositionStoreAction, TranspositionTable,
    CANCELLATION_CHECK_INTERVAL_NODES,
""",
    "chess-tools search imports",
)
benchmark_code = '''
/// One cancellation-response benchmark result.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct CancellationBenchmarkRow {
    /// Stable operation name.
    pub operation: &'static str,
    /// Number of independent cancellation samples.
    pub iterations: u64,
    /// Production nodes entered before the synthetic external request.
    pub request_after_nodes: u64,
    /// Largest observed number of additional node entries after the request.
    pub maximum_response_nodes: u64,
    /// Sum of measured request-to-return latency in nanoseconds.
    pub total_latency_nanos: u128,
    /// Largest measured request-to-return latency in nanoseconds.
    pub maximum_latency_nanos: u128,
    /// Deterministic accumulator over node and restoration evidence.
    pub checksum: u64,
}

const CANCELLATION_BENCHMARK_REQUEST_AFTER_NODES: u64 = 64;
const CANCELLATION_BENCHMARK_DEPTH: u16 = 5;

struct CancellationLatencyProbe {
    entered_nodes: u64,
    request_after_nodes: u64,
    requested_at_node: Option<u64>,
    observed_at_node: Option<u64>,
    requested_at: Option<Instant>,
    observed_latency_nanos: Option<u128>,
}

impl CancellationLatencyProbe {
    const fn new(request_after_nodes: u64) -> Self {
        Self {
            entered_nodes: 0,
            request_after_nodes,
            requested_at_node: None,
            observed_at_node: None,
            requested_at: None,
            observed_latency_nanos: None,
        }
    }

    fn observe(&mut self) {
        if self.observed_at_node.is_none() {
            self.observed_at_node = Some(self.entered_nodes);
            self.observed_latency_nanos = Some(
                self.requested_at
                    .expect("benchmark request timestamp exists")
                    .elapsed()
                    .as_nanos(),
            );
        }
    }
}

impl SearchCancellationProbe for CancellationLatencyProbe {
    fn should_cancel(&mut self) -> bool {
        if self.requested_at_node.is_some() {
            self.observe();
            return true;
        }
        if self.entered_nodes >= self.request_after_nodes {
            self.requested_at_node = Some(self.entered_nodes);
            self.requested_at = Some(Instant::now());
        }
        false
    }

    fn on_node(&mut self) -> bool {
        if self.requested_at_node.is_some() {
            self.observe();
            return true;
        }
        self.entered_nodes = self.entered_nodes.saturating_add(1);
        false
    }
}

/// Benchmarks deterministic mid-tree cancellation detection and unwind latency.
///
/// Wall-clock values are informational. The enforced correctness threshold is
/// the exported node interval: no sample may enter more than
/// `CANCELLATION_CHECK_INTERVAL_NODES` additional nodes after the request.
pub fn benchmark_cancellation(iterations: u64) -> Result<CancellationBenchmarkRow, ToolError> {
    if iterations == 0 {
        return Err(ToolError::new(
            "cancellation benchmark requires at least one iteration",
        ));
    }

    let mut maximum_response_nodes = 0_u64;
    let mut total_latency_nanos = 0_u128;
    let mut maximum_latency_nanos = 0_u128;
    let mut checksum = 0_u64;

    for sample in 0..iterations {
        let mut position = Position::starting();
        let position_snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);
        let history_snapshot = history.clone();
        let mut probe = CancellationLatencyProbe::new(CANCELLATION_BENCHMARK_REQUEST_AFTER_NODES);

        let result = alpha_beta_search_with_cancellation(
            &mut position,
            &mut history,
            CANCELLATION_BENCHMARK_DEPTH,
            &mut probe,
        );
        if result != Err(AlphaBetaSearchError::Cancelled) {
            return Err(ToolError::new(
                "cancellation benchmark search did not terminate through cancellation",
            ));
        }
        if position != position_snapshot
            || history != history_snapshot
            || position.zobrist() != position.recomputed_zobrist()
            || history.current_zobrist() != Some(position.zobrist())
        {
            return Err(ToolError::new(
                "cancellation benchmark failed exact root restoration",
            ));
        }

        let requested_at_node = probe
            .requested_at_node
            .ok_or_else(|| ToolError::new("cancellation benchmark did not issue a request"))?;
        let observed_at_node = probe
            .observed_at_node
            .ok_or_else(|| ToolError::new("cancellation benchmark did not observe the request"))?;
        let response_nodes = observed_at_node.saturating_sub(requested_at_node);
        if response_nodes > CANCELLATION_CHECK_INTERVAL_NODES {
            return Err(ToolError::new(format!(
                "cancellation response used {response_nodes} nodes; bound is {CANCELLATION_CHECK_INTERVAL_NODES}"
            )));
        }
        let latency_nanos = probe
            .observed_latency_nanos
            .ok_or_else(|| ToolError::new("cancellation benchmark did not measure latency"))?;

        maximum_response_nodes = maximum_response_nodes.max(response_nodes);
        total_latency_nanos = total_latency_nanos.saturating_add(latency_nanos);
        maximum_latency_nanos = maximum_latency_nanos.max(latency_nanos);
        checksum = checksum
            .wrapping_mul(0x9e37_79b9_7f4a_7c15)
            .wrapping_add(requested_at_node.rotate_left(7))
            .wrapping_add(observed_at_node.rotate_left(17))
            .wrapping_add(position.zobrist())
            .wrapping_add(sample);
    }

    Ok(CancellationBenchmarkRow {
        operation: "cancel",
        iterations,
        request_after_nodes: CANCELLATION_BENCHMARK_REQUEST_AFTER_NODES,
        maximum_response_nodes,
        total_latency_nanos,
        maximum_latency_nanos,
        checksum,
    })
}

'''
tools = replace_once(
    tools,
    "fn sanitize_error(error: &ToolError) -> String {\n",
    benchmark_code + "fn sanitize_error(error: &ToolError) -> String {\n",
    "cancellation benchmark insertion",
)
tools = replace_once(
    tools,
    """        benchmark_transposition, divide, legal_uci, perft_fixtures, play_uci, run_oracle,
        STARTING_FEN,
""",
    """        benchmark_cancellation, benchmark_transposition, divide, legal_uci, perft_fixtures,
        play_uci, run_oracle, STARTING_FEN,
""",
    "benchmark test import",
)
tools = replace_once(
    tools,
    """    #[test]
    fn transposition_benchmark_fixtures_and_checksums_are_reproducible() {
""",
    """    #[test]
    fn cancellation_benchmark_enforces_the_node_bound_and_repeats_its_checksum() {
        assert!(benchmark_cancellation(0).is_err());
        let first = benchmark_cancellation(4).expect("cancellation benchmark succeeds");
        let second = benchmark_cancellation(4).expect("cancellation benchmark repeats");

        assert_eq!(first.operation, "cancel");
        assert_eq!(first.iterations, 4);
        assert_eq!(first.request_after_nodes, 64);
        assert!(first.maximum_response_nodes <= CANCELLATION_CHECK_INTERVAL_NODES);
        assert!(first.maximum_latency_nanos <= first.total_latency_nanos);
        assert_eq!(first.checksum, second.checksum);
    }

    #[test]
    fn transposition_benchmark_fixtures_and_checksums_are_reproducible() {
""",
    "cancellation benchmark test",
)
# The test module needs the exported interval constant.
tools = replace_once(
    tools,
    "    use std::io::Cursor;\n\n    use super::{",
    "    use std::io::Cursor;\n\n    use chess_search::CANCELLATION_CHECK_INTERVAL_NODES;\n\n    use super::{",
    "benchmark test constant import",
)
write(tools_lib_path, tools)

# CLI command.
tools_main_path = "crates/chess-tools/src/main.rs"
tools_main = read(tools_main_path)
tools_main = replace_once(
    tools_main,
    """    benchmark_evaluation, benchmark_transposition, deserialize_weight_set, divide,
    evaluation_trace, legal_uci, perft, play_uci, run_oracle, serialize_weight_set, suite,
""",
    """    benchmark_cancellation, benchmark_evaluation, benchmark_transposition,
    deserialize_weight_set, divide, evaluation_trace, legal_uci, perft, play_uci, run_oracle,
    serialize_weight_set, suite,
""",
    "CLI benchmark import",
)
tools_main = replace_once(
    tools_main,
    "  chess-tools tt-bench ITERATIONS\\n",
    "  chess-tools tt-bench ITERATIONS\\n  chess-tools cancel-bench ITERATIONS\\n",
    "CLI usage",
)
tools_main = replace_once(
    tools_main,
    """        "weights-export" => {
""",
    """        "cancel-bench" => {
            if arguments.len() != 2 {
                return Err(usage().to_owned());
            }
            let iterations = parse_iterations(&arguments[1])?;
            let row = benchmark_cancellation(iterations).map_err(|error| error.to_string())?;
            println!(
                "{}\\t{}\\t{}\\t{}\\t{}\\t{}\\t{}",
                row.operation,
                row.iterations,
                row.request_after_nodes,
                row.maximum_response_nodes,
                row.total_latency_nanos,
                row.maximum_latency_nanos,
                row.checksum
            );
        }
        "weights-export" => {
""",
    "CLI cancellation command",
)
write(tools_main_path, tools_main)

# Contract documentation.
write(
    "docs/RUST_RESPONSIVE_CANCELLATION.md",
    '''# Rust Responsive Cancellation — Task 16.5

Task 16.5 formalizes the cancellation behavior used by fixed-depth alpha-beta, quiescence, and typed limited iterative deepening. Cancellation is cooperative, bounded in production-node units, and never exposes a partially searched depth as exact work.

## Checkpoint contract

`CANCELLATION_CHECK_INTERVAL_NODES` is currently `1`.

Every production alpha-beta node and every production quiescence node calls `SearchCancellationProbe::on_node` before ordinary node work. Move loops also call `should_cancel` before applying the next child move. The strict response target is therefore no more than one additional production-node entry after a request becomes observable.

The one-node bound is a correctness assertion. It is not replaced by a wall-clock threshold, because hosted runners and target devices have different scheduling and node costs.

## Orderly unwind

A cancellation result propagates only after each active child frame:

1. pops its reversible search-history entry;
2. unmakes its applied legal move;
3. restores the parent Zobrist identity;
4. returns the typed cancellation error.

The root boundary verifies the original position, detached history lengths, current history identity, incremental Zobrist value, and recomputed Zobrist value. Cancellation cannot leave a partially applied line behind.

## Iterative-deepening result policy

A cancelled aspiration attempt or depth is discarded completely. It contributes no exact score, best move, principal variation, ponder move, aspiration record, or completed node total.

Every earlier exact iteration remains in `LimitedIterativeDeepeningSearchResult::completed`. Once at least one iteration exists, the deepest completed iteration is authoritative and `fallback()` returns `None`.

## No-completed-iteration fallback

When cancellation occurs before depth one completes, `fallback()` returns one typed `SearchCancellationFallback`:

- `FirstLegalMove(move)` — the first move in deterministic legal-generation order;
- `NoLegalMove` — the root is terminal.

The fallback is generated and validated at the unchanged root. It is not scored, is not inserted into the transposition table, and is never represented as a completed depth-one result. Task 16.6 may wrap this value in the final unified result API without changing this policy.

## Latency benchmark

Run the release benchmark with:

```text
cargo run --locked -p chess-tools --release -- cancel-bench ITERATIONS
```

Output fields are:

```text
operation<TAB>iterations<TAB>request_after_nodes<TAB>maximum_response_nodes<TAB>total_latency_nanos<TAB>maximum_latency_nanos<TAB>checksum
```

Each sample injects a deterministic request after 64 entered production nodes, requires typed cancellation from an unfinished depth-five search, verifies exact position/history/Zobrist restoration, and rejects any sample exceeding `CANCELLATION_CHECK_INTERVAL_NODES` additional nodes. Nanosecond values are informational; the node bound and checksum are the deterministic evidence.
''',
)

limits_path = "docs/RUST_SEARCH_LIMITS.md"
limits_doc = read(limits_path)
limits_doc = replace_once(
    limits_doc,
    """A cancelled depth cannot contribute a score, best move, PV, ponder move, aspiration record, or completed node total. The caller can inspect the last completed iteration when one exists. Task 16.5 remains responsible for the formal no-completed-iteration fallback and cancellation-latency benchmark. Task 16.6 remains responsible for the final unified engine result API.
""",
    """A cancelled depth cannot contribute a score, best move, PV, ponder move, aspiration record, or completed node total. The caller can inspect the last completed iteration when one exists. When no iteration completed, `fallback()` returns a deterministic first legal move or an explicit terminal `NoLegalMove` value. The one-node polling bound and cancellation benchmark are documented in `docs/RUST_RESPONSIVE_CANCELLATION.md`. Task 16.6 remains responsible for the final unified engine result API.
""",
    "search-limits fallback paragraph",
)
write(limits_path, limits_doc)

iterative_doc_path = "docs/RUST_ITERATIVE_DEEPENING.md"
iterative_doc = read(iterative_doc_path)
iterative_doc = replace_once(
    iterative_doc,
    "# Rust Iterative Deepening — Tasks 16.1–16.4",
    "# Rust Iterative Deepening — Tasks 16.1–16.5",
    "iterative document title",
)
iterative_doc = replace_once(
    iterative_doc,
    "Typed limit semantics are documented in `docs/RUST_SEARCH_LIMITS.md`.",
    "Typed limit semantics are documented in `docs/RUST_SEARCH_LIMITS.md`. The responsive cancellation and fallback contract is documented in `docs/RUST_RESPONSIVE_CANCELLATION.md`.",
    "iterative document references",
)
iterative_doc = replace_once(
    iterative_doc,
    """## Deferred Task 16 work

Tasks 16.1–16.4 do not yet add:

- the Task 16.5 formal cancellation-latency benchmark and no-completed-iteration fallback;
- the final unified Task 16.6 search-result API, including public elapsed time and selective depth;
- check extensions.
""",
    """## Responsive cancellation

Task 16.5 makes the existing production-node cancellation checks an explicit one-node response contract. Interrupted depths are discarded after exact unwind. Earlier completed iterations remain authoritative, while a request that stops before depth one receives a deterministic legal-root fallback or an explicit terminal no-move fallback. A release tooling benchmark measures request-to-return latency and enforces the deterministic node bound.

## Deferred Task 16 work

Tasks 16.1–16.5 do not yet add:

- the final unified Task 16.6 search-result API, including public elapsed time and selective depth;
- check extensions.
""",
    "iterative deferred section",
)
write(iterative_doc_path, iterative_doc)

print("Task 16.5 implementation applied")
