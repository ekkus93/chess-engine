use chess_core::{Move, Position, SearchHistory};
use chess_search::{
    iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights,
    EvaluationWeights, SearchLimits, SearchPolicySet, SearchResult, TranspositionTable,
    FUTILITY_PRUNING_MARGIN_CENTIPAWNS, FUTILITY_PRUNING_MAXIMUM_DEPTH,
    FUTILITY_PRUNING_SEARCH_POLICY_ID,
};

const TT_MEBIBYTES: usize = 1;

fn run(fen: &str, depth: u16, policy: &SearchPolicySet) -> SearchResult {
    let mut position = Position::from_fen(fen).expect("fixture parses");
    let root = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let root_history = history.clone();
    let mut table = TranspositionTable::new(TT_MEBIBYTES).expect("small TT allocates");
    let result =
        iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights(
            &mut position,
            &mut history,
            SearchLimits::new().with_depth(depth),
            &mut table,
            policy,
            &EvaluationWeights::DEFAULT,
        )
        .expect("controlled search succeeds");
    assert_eq!(position, root);
    assert_eq!(history, root_history);
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
    replay_pv(
        &root,
        result.principal_variation().map_or(&[], |pv| pv.moves()),
    );
    result
}

fn replay_pv(root: &Position, moves: &[Move]) {
    let mut position = root.clone();
    for current in moves {
        let token = position
            .legal_move_tokens()
            .expect("PV moves generate")
            .iter()
            .find(|token| token.move_made() == *current)
            .expect("PV move remains legal");
        position.make_legal_token(token).expect("PV move applies");
    }
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
}

#[test]
fn candidate_identity_parameters_and_default_inactivity_are_explicit() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::futility_pruning_candidate();
    baseline.validate().expect("baseline validates");
    candidate.validate().expect("candidate validates");
    assert_eq!(candidate.identifier, FUTILITY_PRUNING_SEARCH_POLICY_ID);
    assert_eq!(FUTILITY_PRUNING_MAXIMUM_DEPTH, 1);
    assert_eq!(FUTILITY_PRUNING_MARGIN_CENTIPAWNS, 150);
    assert!(!baseline.policy.futility_pruning_enabled());
    assert!(candidate.policy.futility_pruning_enabled());
    assert_ne!(baseline.checksum, candidate.checksum);
}

#[test]
fn baseline_counters_stay_zero_and_candidate_attempts_are_bounded() {
    let fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1";
    let baseline = run(fen, 4, &SearchPolicySet::baseline());
    let candidate = run(fen, 4, &SearchPolicySet::futility_pruning_candidate());
    let base = baseline.search_diagnostics();
    let experimental = candidate.search_diagnostics();
    assert_eq!(base.frontier_futility_attempts(), 0);
    assert_eq!(base.frontier_futility_prunes(), 0);
    assert!(experimental.frontier_futility_attempts() > 0);
    assert!(experimental.frontier_futility_prunes() <= experimental.frontier_futility_attempts());
    assert!(!experimental.overflowed());
}

#[test]
fn tactical_and_rule_sensitive_roots_preserve_exact_semantics() {
    let baseline_policy = SearchPolicySet::baseline();
    let candidate_policy = SearchPolicySet::futility_pruning_candidate();
    for (fen, depth) in [
        ("4k3/8/8/8/8/8/4R3/4K3 b - - 0 1", 3),
        ("7k/P7/8/8/8/8/8/K7 w - - 0 1", 4),
        ("7k/8/8/8/8/8/6q1/7K w - - 0 1", 3),
        ("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1", 3),
        ("6k1/5ppp/8/8/8/8/5PPP/6K1 w - - 99 1", 3),
    ] {
        let baseline = run(fen, depth, &baseline_policy);
        let candidate = run(fen, depth, &candidate_policy);
        assert_eq!(candidate.score(), baseline.score(), "{fen}");
        assert_eq!(candidate.best_move(), baseline.best_move(), "{fen}");
        assert_eq!(
            candidate.completed_depth(),
            baseline.completed_depth(),
            "{fen}"
        );
    }
}
