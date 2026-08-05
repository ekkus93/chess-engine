use chess_core::{Position, SearchHistory};
use chess_search::{
    iterative_deepening_search_with_limits_and_transposition_table,
    iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights,
    EvaluationWeights, IterativeDeepeningSearchError, SearchLimits, SearchPolicy, SearchPolicySet,
    TranspositionTable,
};

#[test]
fn explicit_v0_1_policy_matches_existing_default_search_exactly() {
    let root =
        Position::from_fen("r2q1rk1/ppp2ppp/2npbn2/3Np3/2B1P3/2P2N2/PP3PPP/R1BQR1K1 w - - 0 10")
            .expect("fixture parses");
    let limits = SearchLimits::new().with_depth(4);

    let mut default_position = root.clone();
    let mut default_history = SearchHistory::from_position(&default_position);
    let mut default_table = TranspositionTable::new(4).expect("default table allocates");
    let default = iterative_deepening_search_with_limits_and_transposition_table(
        &mut default_position,
        &mut default_history,
        limits.clone(),
        &mut default_table,
    )
    .expect("default policy search succeeds");

    let mut explicit_position = root.clone();
    let mut explicit_history = SearchHistory::from_position(&explicit_position);
    let mut explicit_table = TranspositionTable::new(4).expect("explicit table allocates");
    let policy = SearchPolicySet::baseline();
    let explicit =
        iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights(
            &mut explicit_position,
            &mut explicit_history,
            limits,
            &mut explicit_table,
            &policy,
            &EvaluationWeights::DEFAULT,
        )
        .expect("explicit v0.1 policy search succeeds");

    assert_eq!(explicit.completed(), default.completed());
    assert_eq!(explicit.termination(), default.termination());
    assert_eq!(explicit.nodes(), default.nodes());
    assert_eq!(explicit.qnodes(), default.qnodes());
    assert_eq!(explicit.selective_depth(), default.selective_depth());
    assert_eq!(
        explicit.check_extension_diagnostics(),
        default.check_extension_diagnostics()
    );
    assert_eq!(explicit.fallback(), default.fallback());
    assert_eq!(default_position, root);
    assert_eq!(explicit_position, root);
    assert_eq!(default_history, SearchHistory::from_position(&root));
    assert_eq!(explicit_history, SearchHistory::from_position(&root));
}

#[test]
fn invalid_policy_fails_before_position_history_or_table_mutation() {
    let root = Position::starting();
    let mut position = root.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let mut table = TranspositionTable::new(1).expect("table allocates");
    let initial_generation = table.generation();
    let limits = SearchLimits::new().with_depth(2);
    let baseline = SearchPolicySet::baseline();
    let corrupt = SearchPolicySet::from_parts(
        baseline.schema_version,
        baseline.identifier,
        baseline.policy,
        baseline.checksum ^ 1,
    );

    let error =
        iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights(
            &mut position,
            &mut history,
            limits,
            &mut table,
            &corrupt,
            &EvaluationWeights::DEFAULT,
        )
        .expect_err("corrupt policy must fail");

    assert!(matches!(
        error,
        IterativeDeepeningSearchError::InvalidSearchPolicy(_)
    ));
    assert_eq!(position, root);
    assert_eq!(history, history_snapshot);
    assert_eq!(table.generation(), initial_generation);
}

#[test]
fn policy_dependent_searches_use_separate_transposition_tables() {
    let baseline = SearchPolicySet::baseline();
    let mut parameters = baseline.policy.parameters();
    parameters.aspiration_half_width_centipawns += 1;
    let candidate = SearchPolicySet::new(0x4341_4e44_504f_4c31, SearchPolicy::new(parameters));

    assert_ne!(candidate.checksum, baseline.checksum);
    let baseline_table = TranspositionTable::new(1).expect("baseline table allocates");
    let candidate_table = TranspositionTable::new(1).expect("candidate table allocates");
    assert_eq!(baseline_table.generation(), candidate_table.generation());
}
