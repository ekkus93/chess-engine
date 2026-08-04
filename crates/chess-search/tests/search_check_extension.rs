use chess_core::{Position, SearchHistory};
use chess_search::{
    iterative_deepening_search_with_limits,
    iterative_deepening_search_with_limits_and_transposition_table, CheckExtensionDiagnostics,
    Score, SearchLimitTermination, SearchLimits, TranspositionBound, TranspositionEntry,
    TranspositionScore, TranspositionTable,
};

fn forcing_check_root() -> Position {
    "6k1/6pp/8/8/8/8/8/3Q2K1 w - - 0 1"
        .parse()
        .expect("forcing-check FEN is valid")
}

#[test]
fn check_extension_is_explicit_opt_in_and_records_applied_work() {
    let root = forcing_check_root();

    let mut baseline_position = root.clone();
    let baseline_snapshot = baseline_position.clone();
    let mut baseline_history = SearchHistory::from_position(&baseline_position);
    let baseline_history_snapshot = baseline_history.clone();
    let baseline = iterative_deepening_search_with_limits(
        &mut baseline_position,
        &mut baseline_history,
        SearchLimits::new().with_depth(1),
    )
    .expect("baseline search succeeds");
    assert_eq!(
        baseline.check_extension_diagnostics(),
        CheckExtensionDiagnostics::default()
    );
    assert_eq!(baseline_position, baseline_snapshot);
    assert_eq!(baseline_history, baseline_history_snapshot);

    let mut extended_position = root.clone();
    let extended_snapshot = extended_position.clone();
    let mut extended_history = SearchHistory::from_position(&extended_position);
    let extended_history_snapshot = extended_history.clone();
    let extended = iterative_deepening_search_with_limits(
        &mut extended_position,
        &mut extended_history,
        SearchLimits::new().with_depth(1).with_check_extension(),
    )
    .expect("extended search succeeds");
    let diagnostics = extended.check_extension_diagnostics();

    assert_eq!(
        extended.termination(),
        SearchLimitTermination::Depth { depth: 1 }
    );
    assert!(diagnostics.eligible_nodes() > 0);
    assert!(diagnostics.applied_extensions() > 0);
    assert_eq!(
        diagnostics.eligible_nodes(),
        diagnostics
            .applied_extensions()
            .saturating_add(diagnostics.budget_exhausted_nodes())
            .saturating_add(diagnostics.mate_domain_blocked_nodes())
    );
    assert_eq!(extended_position, extended_snapshot);
    assert_eq!(extended_history, extended_history_snapshot);
    assert_eq!(
        extended_position.zobrist(),
        extended_position.recomputed_zobrist()
    );
}

#[test]
fn extension_search_is_deterministic_and_keeps_a_legal_root_pv() {
    let root = forcing_check_root();
    let mut first_position = root.clone();
    let mut first_history = SearchHistory::from_position(&first_position);
    let first = iterative_deepening_search_with_limits(
        &mut first_position,
        &mut first_history,
        SearchLimits::new().with_depth(2).with_check_extension(),
    )
    .expect("first extension search succeeds");

    let mut second_position = root.clone();
    let mut second_history = SearchHistory::from_position(&second_position);
    let second = iterative_deepening_search_with_limits(
        &mut second_position,
        &mut second_history,
        SearchLimits::new().with_depth(2).with_check_extension(),
    )
    .expect("second extension search succeeds");

    assert_eq!(first.best_move(), second.best_move());
    assert_eq!(first.score(), second.score());
    assert_eq!(first.nodes(), second.nodes());
    assert_eq!(
        first.check_extension_diagnostics(),
        second.check_extension_diagnostics()
    );
    assert_eq!(first.completed_depth(), 2);
    let pv = first
        .principal_variation()
        .expect("completed extension search retains a root PV");
    assert_eq!(pv.moves().first().copied(), first.best_move());
    assert!(pv.len() <= usize::from(first.completed_depth()));
    assert_eq!(first_position, root);
    assert_eq!(second_position, root);
}

#[test]
fn extension_enabled_search_cannot_reuse_a_baseline_tt_score() {
    let root = Position::starting();
    let mut position = root.clone();
    let snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let first_move = position
        .legal_move_tokens()
        .expect("starting legal moves generate")
        .iter()
        .next()
        .expect("starting position has a move")
        .move_made();
    let bogus = Score::from_evaluation(12_345);
    let mut table = TranspositionTable::new(1).expect("bounded table allocates");
    table.store(TranspositionEntry::new(
        position.zobrist(),
        8,
        TranspositionBound::Exact,
        TranspositionScore::normalize(bogus, 0).expect("bogus score normalizes"),
        Some(first_move),
        table.generation(),
    ));

    let result = iterative_deepening_search_with_limits_and_transposition_table(
        &mut position,
        &mut history,
        SearchLimits::new().with_depth(1).with_check_extension(),
        &mut table,
    )
    .expect("extension search ignores path-incompatible TT score");

    assert_ne!(result.score(), Some(bogus));
    assert_eq!(position, snapshot);
    assert_eq!(history, history_snapshot);
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
}

#[test]
fn tight_node_limit_preserves_partial_extension_diagnostics_and_root_state() {
    let root = forcing_check_root();
    let mut position = root.clone();
    let snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();

    let result = iterative_deepening_search_with_limits(
        &mut position,
        &mut history,
        SearchLimits::new().with_nodes(64).with_check_extension(),
    )
    .expect("node-limited extension search returns a snapshot");

    assert_eq!(
        result.termination(),
        SearchLimitTermination::Nodes { nodes: 64 }
    );
    assert_eq!(result.nodes(), 64);
    assert!(result.check_extension_diagnostics().eligible_nodes() > 0);
    assert_eq!(position, snapshot);
    assert_eq!(history, history_snapshot);
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
}
