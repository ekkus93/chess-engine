use chess_core::{Move, Position, SearchHistory};
use chess_search::{
    iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights,
    EvaluationWeights, SearchLimits, SearchPolicySet, SearchResult, TranspositionTable,
    LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID, LMR_MINIMUM_DEPTH, LMR_MINIMUM_LEGAL_MOVES,
    LMR_MINIMUM_MOVE_INDEX, LMR_MINIMUM_TOTAL_PIECES, LMR_REDUCTION_TABLE,
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
fn candidate_identity_and_parameters_are_explicit_and_inactive_by_default() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::late_move_reductions_candidate();
    baseline.validate().expect("baseline policy validates");
    candidate.validate().expect("candidate policy validates");
    assert_eq!(candidate.identifier, LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID);
    assert_eq!(LMR_MINIMUM_DEPTH, 4);
    assert_eq!(LMR_MINIMUM_MOVE_INDEX, 4);
    assert_eq!(LMR_MINIMUM_LEGAL_MOVES, 6);
    assert_eq!(LMR_MINIMUM_TOTAL_PIECES, 10);
    assert_eq!(LMR_REDUCTION_TABLE, [(4, 4, 1), (7, 8, 2)]);
    assert!(!baseline.policy.late_move_reductions_enabled());
    assert!(candidate.policy.late_move_reductions_enabled());
    assert_ne!(baseline.checksum, candidate.checksum);
}

#[test]
fn candidate_preserves_tactical_mate_promotion_and_endgame_fixtures() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::late_move_reductions_candidate();
    for (fen, depth) in [
        ("7k/5Q2/6K1/8/8/8/8/8 w - - 0 1", 4),
        ("4Q2k/8/4K3/8/8/8/8/8 b - - 0 1", 6),
        ("7k/P7/6K1/8/8/8/8/8 w - - 0 1", 5),
        ("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1", 5),
        ("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 5),
        ("3rk3/8/8/8/8/8/8/K2Q4 w - - 0 1", 5),
        (
            "r2q1rk1/ppp2ppp/2npbn2/3Np3/2B1P3/2P2N2/PP3PPP/R1BQR1K1 w - - 0 10",
            5,
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
fn candidate_reduces_only_late_moves_and_verifies_every_reduced_alpha_raise() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::late_move_reductions_candidate();
    let fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1";
    let baseline_result = run(fen, SearchLimits::new().with_depth(5), &baseline);
    let candidate_result = run(fen, SearchLimits::new().with_depth(5), &candidate);
    let baseline_diagnostics = baseline_result.search_diagnostics();
    let diagnostics = candidate_result.search_diagnostics();
    assert_eq!(baseline_diagnostics.lmr_reductions(), 0);
    assert_eq!(baseline_diagnostics.lmr_reduced_fail_highs(), 0);
    assert_eq!(baseline_diagnostics.lmr_verification_searches(), 0);
    assert!(diagnostics.lmr_reductions() > 0);
    assert_eq!(
        diagnostics.lmr_reduced_fail_highs(),
        diagnostics.lmr_verification_searches()
    );
    assert!(diagnostics.lmr_verification_searches() <= diagnostics.lmr_reductions());
    assert_eq!(candidate_result.score(), baseline_result.score());
    assert_eq!(candidate_result.best_move(), baseline_result.best_move());
}

#[test]
fn node_limited_cancellation_restores_state_and_keeps_only_completed_iterations() {
    let candidate = SearchPolicySet::late_move_reductions_candidate();
    let fen = "r2q1rk1/ppp2ppp/2npbn2/3Np3/2B1P3/2P2N2/PP3PPP/R1BQR1K1 w - - 0 10";
    let limited = run(
        fen,
        SearchLimits::new().with_depth(9).with_nodes(768),
        &candidate,
    );
    assert!(limited.completed_depth() < 9);
    assert!(limited.nodes() <= 768);
    for iteration in limited.completed().iterations() {
        assert!(iteration.best_move().is_some());
        assert!(!iteration.search_diagnostics().overflowed());
        assert_eq!(
            iteration.search_diagnostics().lmr_reduced_fail_highs(),
            iteration.search_diagnostics().lmr_verification_searches()
        );
    }
}
