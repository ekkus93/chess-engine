use chess_core::{Move, Position, SearchHistory};
use chess_search::{
    iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights,
    EvaluationWeights, SearchLimits, SearchPolicySet, SearchResult, TranspositionTable,
    PRINCIPAL_VARIATION_SEARCH_POLICY_ID,
};

const TT_MEBIBYTES: usize = 1;

fn run(fen: &str, limits: SearchLimits, policy: &SearchPolicySet) -> SearchResult {
    let mut position = Position::from_fen(fen).expect("fixture FEN parses");
    let root = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let root_history = history.clone();
    let mut table = TranspositionTable::new(TT_MEBIBYTES).expect("small TT allocates");
    let result =
        iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights(
            &mut position,
            &mut history,
            limits,
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
        result
            .principal_variation()
            .map(|pv| pv.moves())
            .unwrap_or(&[]),
    );
    result
}

fn replay_pv(root: &Position, moves: &[Move]) {
    let mut position = root.clone();
    for current in moves {
        let token = position
            .legal_move_tokens()
            .expect("PV legal tokens generate")
            .iter()
            .find(|token| token.move_made() == *current)
            .expect("PV move is legal");
        position
            .make_legal_token(token)
            .expect("PV legal token applies");
    }
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
}

#[test]
fn candidate_identity_is_explicit_valid_and_inactive_by_default() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::principal_variation_search_candidate();
    baseline.validate().expect("baseline policy validates");
    candidate.validate().expect("candidate policy validates");
    assert_eq!(candidate.identifier, PRINCIPAL_VARIATION_SEARCH_POLICY_ID);
    assert!(!baseline.policy.principal_variation_search_enabled());
    assert!(candidate.policy.principal_variation_search_enabled());
    assert_ne!(baseline.checksum, candidate.checksum);
}

#[test]
fn candidate_preserves_exact_scores_best_moves_and_legal_pvs() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::principal_variation_search_candidate();
    for (fen, depth) in [
        ("7k/5Q2/6K1/8/8/8/8/8 w - - 0 1", 3),
        ("4Q2k/8/4K3/8/8/8/8/8 b - - 0 1", 6),
        ("7k/P7/6K1/8/8/8/8/8 w - - 0 1", 4),
        ("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1", 4),
        ("3rk3/8/8/8/8/8/8/K2Q4 w - - 0 1", 4),
        (
            "r1bq1rk1/ppp2ppp/2np1n2/4p3/2B1P3/2N2N2/PPPP1PPP/R1BQ1RK1 w - - 4 7",
            4,
        ),
    ] {
        let baseline_result = run(fen, SearchLimits::new().with_depth(depth), &baseline);
        let candidate_result = run(fen, SearchLimits::new().with_depth(depth), &candidate);
        assert_eq!(candidate_result.score(), baseline_result.score(), "{fen}");
        assert_eq!(
            candidate_result.completed_depth(),
            baseline_result.completed_depth(),
            "{fen}"
        );
        assert_eq!(
            candidate_result.best_move(),
            baseline_result.best_move(),
            "{fen}"
        );
    }
}

#[test]
fn candidate_uses_zero_windows_and_only_researches_improving_moves() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::principal_variation_search_candidate();
    let fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1";
    let baseline_result = run(fen, SearchLimits::new().with_depth(4), &baseline);
    let candidate_result = run(fen, SearchLimits::new().with_depth(4), &candidate);
    let baseline_diagnostics = baseline_result.search_diagnostics();
    let diagnostics = candidate_result.search_diagnostics();
    assert_eq!(baseline_diagnostics.pvs_zero_window_searches(), 0);
    assert_eq!(baseline_diagnostics.pvs_researches(), 0);
    assert!(diagnostics.pvs_zero_window_searches() > 0);
    assert!(diagnostics.pvs_researches() <= diagnostics.pvs_zero_window_searches());
    assert_eq!(candidate_result.score(), baseline_result.score());
    assert_eq!(candidate_result.best_move(), baseline_result.best_move());
}

#[test]
fn aspiration_recovery_and_node_limited_cancellation_keep_only_exact_iterations() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::principal_variation_search_candidate();
    let fen = "r2q1rk1/ppp2ppp/2npbn2/3Np3/2B1P3/2P2N2/PP3PPP/R1BQR1K1 w - - 0 10";

    let baseline_exact = run(fen, SearchLimits::new().with_depth(5), &baseline);
    let candidate_exact = run(fen, SearchLimits::new().with_depth(5), &candidate);
    assert_eq!(candidate_exact.score(), baseline_exact.score());
    assert_eq!(candidate_exact.best_move(), baseline_exact.best_move());

    let limited = run(
        fen,
        SearchLimits::new().with_depth(8).with_nodes(512),
        &candidate,
    );
    assert!(limited.completed_depth() < 8);
    assert!(limited.nodes() <= 512);
    for iteration in limited.completed().iterations() {
        assert!(iteration.best_move().is_some());
        assert!(!iteration.search_diagnostics().overflowed());
    }
}
