use chess_core::{Move, Position, SearchHistory};
use chess_search::{
    iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights,
    EvaluationWeights, SearchLimits, SearchPolicySet, TranspositionTable,
    SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID,
};

const TT_MEBIBYTES: usize = 1;

fn run(fen: &str, depth: u16, policy: &SearchPolicySet) -> chess_search::SearchResult {
    let mut position = Position::from_fen(fen).expect("fixture FEN parses");
    let root = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_root = history.clone();
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
    assert_eq!(history, history_root);
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
fn candidate_identity_is_explicit_valid_and_default_remains_inactive() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::see_capture_ordering_candidate();
    baseline.validate().expect("baseline policy validates");
    candidate.validate().expect("candidate policy validates");
    assert_eq!(candidate.identifier, SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID);
    assert!(!baseline.policy.see_capture_ordering_enabled());
    assert!(candidate.policy.see_capture_ordering_enabled());
    assert_ne!(baseline.checksum, candidate.checksum);
}

#[test]
fn candidate_preserves_exact_scores_mate_distance_and_legal_pvs() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::see_capture_ordering_candidate();
    for (fen, depth) in [
        ("7k/5Q2/6K1/8/8/8/8/8 w - - 0 1", 3),
        ("4Q2k/8/4K3/8/8/8/8/8 b - - 0 1", 6),
        ("7k/P7/6K1/8/8/8/8/8 w - - 0 1", 3),
        ("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1", 3),
        ("3rk3/8/8/8/8/8/8/K2Q4 w - - 0 1", 3),
        (
            "r1bq1rk1/ppp2ppp/2np1n2/4p3/2B1P3/2N2N2/PPPP1PPP/R1BQ1RK1 w - - 4 7",
            4,
        ),
    ] {
        let baseline_result = run(fen, depth, &baseline);
        let candidate_result = run(fen, depth, &candidate);
        assert_eq!(candidate_result.score(), baseline_result.score(), "{fen}");
        assert_eq!(
            candidate_result.completed_depth(),
            baseline_result.completed_depth(),
            "{fen}"
        );
    }
}

#[test]
fn candidate_records_exact_capture_classes_without_pruning() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::see_capture_ordering_candidate();
    let fen = "7k/8/8/1p2q3/2P1Q3/8/K7/8 w - - 0 1";
    let baseline_result = run(fen, 3, &baseline);
    let candidate_result = run(fen, 3, &candidate);
    let baseline_diagnostics = baseline_result.search_diagnostics();
    let diagnostics = candidate_result.search_diagnostics();
    assert_eq!(baseline_diagnostics.see_calls(), 0);
    assert!(diagnostics.see_calls() > 0);
    assert_eq!(
        diagnostics.see_calls(),
        diagnostics.see_winning_captures()
            + diagnostics.see_equal_captures()
            + diagnostics.see_losing_captures()
    );
    assert_eq!(diagnostics.see_prunes(), 0);
    assert_eq!(diagnostics.quiescence_see_prunes(), 0);
    assert_eq!(candidate_result.score(), baseline_result.score());
}
