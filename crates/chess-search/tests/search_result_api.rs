use chess_core::{Position, SearchHistory};
use chess_search::{
    iterative_deepening_search_with_limits,
    iterative_deepening_search_with_limits_and_transposition_table, SearchCancellationFallback,
    SearchLimitTermination, SearchLimits, SearchStopFlag, TranspositionTable,
};

fn assert_restored(
    position: &Position,
    position_snapshot: &Position,
    history: &SearchHistory,
    history_snapshot: &SearchHistory,
) {
    assert_eq!(position, position_snapshot);
    assert_eq!(history, history_snapshot);
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
}

#[test]
fn completed_request_exposes_one_consistent_authoritative_snapshot() {
    let mut position = Position::starting();
    let position_snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();

    let result = iterative_deepening_search_with_limits(
        &mut position,
        &mut history,
        SearchLimits::new().with_depth(2),
    )
    .expect("depth-limited search succeeds");
    let completed = result.completed();
    let final_iteration = completed.final_iteration().expect("depth two completed");

    assert_eq!(
        result.termination(),
        SearchLimitTermination::Depth { depth: 2 }
    );
    assert_eq!(result.completed_depth(), 2);
    assert_eq!(result.score(), Some(final_iteration.score()));
    assert_eq!(result.best_move(), final_iteration.best_move());
    assert_eq!(result.ponder_move(), final_iteration.ponder_move());
    assert_eq!(
        result.principal_variation(),
        Some(final_iteration.principal_variation())
    );
    assert_eq!(result.nodes(), completed.total_nodes());
    assert_eq!(result.qnodes(), completed.total_qnodes());
    assert_eq!(result.selective_depth(), completed.selective_depth());
    assert!(result.nodes() >= result.qnodes());
    assert!(result.qnodes() > 0);
    assert!(result.selective_depth() >= result.completed_depth());
    assert_eq!(result.fallback(), None);
    assert_eq!(result.incomplete_nodes(), 0);
    assert_eq!(result.incomplete_qnodes(), 0);
    let _elapsed = result.elapsed();
    assert_restored(&position, &position_snapshot, &history, &history_snapshot);
}

#[test]
fn interrupted_request_preserves_headline_fields_from_the_last_exact_iteration() {
    let mut baseline_position = Position::starting();
    let mut baseline_history = SearchHistory::from_position(&baseline_position);
    let baseline = iterative_deepening_search_with_limits(
        &mut baseline_position,
        &mut baseline_history,
        SearchLimits::new().with_depth(1),
    )
    .expect("depth one baseline succeeds");
    let node_limit = baseline
        .nodes()
        .checked_add(1)
        .expect("small test node limit fits");

    let mut position = Position::starting();
    let position_snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let result = iterative_deepening_search_with_limits(
        &mut position,
        &mut history,
        SearchLimits::new().with_depth(4).with_nodes(node_limit),
    )
    .expect("node-limited search returns completed work");

    assert_eq!(
        result.termination(),
        SearchLimitTermination::Nodes { nodes: node_limit }
    );
    assert_eq!(result.completed_depth(), 1);
    assert_eq!(result.score(), baseline.score());
    assert_eq!(result.best_move(), baseline.best_move());
    assert_eq!(result.ponder_move(), baseline.ponder_move());
    assert_eq!(result.principal_variation(), baseline.principal_variation());
    assert_eq!(result.nodes(), node_limit);
    assert_eq!(result.incomplete_nodes(), 1);
    assert!(result.qnodes() >= result.completed().total_qnodes());
    assert!(result.selective_depth() >= result.completed().selective_depth());
    assert_eq!(result.fallback(), None);
    assert_restored(&position, &position_snapshot, &history, &history_snapshot);
}

#[test]
fn pre_depth_one_stop_returns_a_move_without_inventing_search_data() {
    let mut position = Position::starting();
    let position_snapshot = position.clone();
    let expected = position
        .legal_moves()
        .expect("root legal generation succeeds")
        .iter()
        .next()
        .expect("starting position has a move");
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let mut table = TranspositionTable::new(1).expect("bounded table allocates");

    let result = iterative_deepening_search_with_limits_and_transposition_table(
        &mut position,
        &mut history,
        SearchLimits::new().with_nodes(1),
        &mut table,
    )
    .expect("one-node request returns a typed snapshot");

    assert_eq!(
        result.termination(),
        SearchLimitTermination::Nodes { nodes: 1 }
    );
    assert_eq!(result.completed_depth(), 0);
    assert_eq!(result.best_move(), Some(expected));
    assert_eq!(result.score(), None);
    assert_eq!(result.ponder_move(), None);
    assert_eq!(result.principal_variation(), None);
    assert_eq!(result.nodes(), 1);
    assert_eq!(result.qnodes(), 0);
    assert_eq!(result.selective_depth(), 0);
    assert_eq!(result.incomplete_nodes(), 1);
    assert_eq!(result.incomplete_qnodes(), 0);
    assert_eq!(
        result.fallback(),
        Some(SearchCancellationFallback::FirstLegalMove(expected))
    );
    assert_restored(&position, &position_snapshot, &history, &history_snapshot);
}

#[test]
fn terminal_pre_depth_one_stop_has_no_move_score_or_pv() {
    let stop = SearchStopFlag::new();
    stop.request_stop();
    let mut position: Position = "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1"
        .parse()
        .expect("terminal FEN is valid");
    let position_snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();

    let result = iterative_deepening_search_with_limits(
        &mut position,
        &mut history,
        SearchLimits::new().with_depth(3).with_stop_flag(stop),
    )
    .expect("terminal preset stop returns a typed snapshot");

    assert_eq!(result.termination(), SearchLimitTermination::ExplicitStop);
    assert_eq!(result.completed_depth(), 0);
    assert_eq!(result.best_move(), None);
    assert_eq!(result.score(), None);
    assert_eq!(result.ponder_move(), None);
    assert_eq!(result.principal_variation(), None);
    assert_eq!(result.nodes(), 0);
    assert_eq!(result.qnodes(), 0);
    assert_eq!(result.selective_depth(), 0);
    assert_eq!(
        result.fallback(),
        Some(SearchCancellationFallback::NoLegalMove)
    );
    assert_restored(&position, &position_snapshot, &history, &history_snapshot);
}
