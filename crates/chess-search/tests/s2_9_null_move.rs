use chess_core::{Move, Position, SearchHistory};
use chess_search::{
    iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights,
    EvaluationWeights, SearchLimits, SearchPolicySet, SearchResult, TranspositionTable,
    NULL_MOVE_MINIMUM_DEPTH, NULL_MOVE_MINIMUM_SIDE_NON_PAWN_PIECES,
    NULL_MOVE_MINIMUM_TOTAL_NON_PAWN_PIECES, NULL_MOVE_PRUNING_SEARCH_POLICY_ID,
    NULL_MOVE_REDUCTION, NULL_MOVE_VERIFICATION_REDUCTION,
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
fn candidate_identity_parameters_and_default_inactivity_are_explicit() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::null_move_pruning_candidate();
    baseline.validate().expect("baseline validates");
    candidate.validate().expect("candidate validates");
    assert_eq!(candidate.identifier, NULL_MOVE_PRUNING_SEARCH_POLICY_ID);
    assert_eq!(NULL_MOVE_MINIMUM_DEPTH, 4);
    assert_eq!(NULL_MOVE_REDUCTION, 2);
    assert_eq!(NULL_MOVE_VERIFICATION_REDUCTION, 1);
    assert_eq!(NULL_MOVE_MINIMUM_SIDE_NON_PAWN_PIECES, 2);
    assert_eq!(NULL_MOVE_MINIMUM_TOTAL_NON_PAWN_PIECES, 4);
    assert!(!baseline.policy.null_move_pruning_enabled());
    assert!(candidate.policy.null_move_pruning_enabled());
    assert_ne!(baseline.checksum, candidate.checksum);
}

#[test]
fn midgame_candidate_records_attempts_guards_and_verified_cutoffs_only() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::null_move_pruning_candidate();
    let fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1";
    let baseline_result = run(fen, SearchLimits::new().with_depth(5), &baseline);
    let candidate_result = run(fen, SearchLimits::new().with_depth(5), &candidate);
    let baseline_diagnostics = baseline_result.search_diagnostics();
    let diagnostics = candidate_result.search_diagnostics();
    assert_eq!(baseline_diagnostics.null_move_attempts(), 0);
    assert_eq!(baseline_diagnostics.null_move_disabled_nodes(), 0);
    assert_eq!(baseline_diagnostics.null_move_speculative_fail_highs(), 0);
    assert_eq!(baseline_diagnostics.null_move_verification_searches(), 0);
    assert_eq!(baseline_diagnostics.null_move_cutoffs(), 0);
    assert!(diagnostics.null_move_attempts() > 0);
    assert!(diagnostics.null_move_disabled_nodes() > 0);
    assert_eq!(
        diagnostics.null_move_speculative_fail_highs(),
        diagnostics.null_move_verification_searches()
    );
    assert!(diagnostics.null_move_cutoffs() <= diagnostics.null_move_verification_searches());
    assert!(!diagnostics.overflowed());
    assert_eq!(
        candidate_result.completed_depth(),
        baseline_result.completed_depth()
    );
}

#[test]
fn pawn_only_and_low_material_positions_never_enter_speculative_search() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::null_move_pruning_candidate();
    for fen in [
        "7k/6pp/8/8/8/8/PP6/K7 w - - 0 1",
        "7k/7r/8/8/8/8/6N1/K7 w - - 0 1",
    ] {
        let baseline_result = run(fen, SearchLimits::new().with_depth(5), &baseline);
        let candidate_result = run(fen, SearchLimits::new().with_depth(5), &candidate);
        let diagnostics = candidate_result.search_diagnostics();
        assert!(diagnostics.null_move_attempts() > 0, "{fen}");
        assert_eq!(diagnostics.null_move_speculative_fail_highs(), 0, "{fen}");
        assert_eq!(diagnostics.null_move_verification_searches(), 0, "{fen}");
        assert_eq!(diagnostics.null_move_cutoffs(), 0, "{fen}");
        assert_eq!(candidate_result.score(), baseline_result.score(), "{fen}");
        assert_eq!(
            candidate_result.best_move(),
            baseline_result.best_move(),
            "{fen}"
        );
    }
}

#[test]
fn node_limited_cancellation_restores_position_history_and_hash() {
    let candidate = SearchPolicySet::null_move_pruning_candidate();
    let fen = "r2q1rk1/ppp2ppp/2npbn2/3Np3/2B1P3/2P2N2/PP3PPP/R1BQR1K1 w - - 0 10";
    let limited = run(
        fen,
        SearchLimits::new().with_depth(9).with_nodes(768),
        &candidate,
    );
    assert!(limited.completed_depth() < 9);
    assert!(limited.nodes() <= 768);
    for iteration in limited.completed().iterations() {
        let diagnostics = iteration.search_diagnostics();
        assert_eq!(
            diagnostics.null_move_speculative_fail_highs(),
            diagnostics.null_move_verification_searches()
        );
        assert!(diagnostics.null_move_cutoffs() <= diagnostics.null_move_verification_searches());
        assert!(!diagnostics.overflowed());
    }
}
