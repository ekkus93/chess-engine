use std::time::Duration;

use chess_core::{Position, SearchHistory};
use chess_search::{
    iterative_deepening_search, iterative_deepening_search_with_limits,
    iterative_deepening_search_with_limits_and_transposition_table, IterativeDeepeningSearchError,
    SearchLimitError, SearchLimitTermination, SearchLimits, SearchStopFlag, TranspositionTable,
};

fn benchmark_position() -> Position {
    "7k/8/8/1p2q3/2P1Q3/8/K7/8 w - - 0 1"
        .parse()
        .expect("search-limit benchmark FEN is valid")
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
    assert_eq!(table.generation(), 2);
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
        assert_eq!(table.generation(), 0);
        assert_restored(&position, &position_snapshot, &history, &history_snapshot);
    }
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
