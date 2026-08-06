use chess_core::{Game, Move, Position, SearchHistory, UciMove};
use chess_search::{
    iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights,
    EvaluationWeights, Score, SearchLimits, SearchPolicySet, SearchResult, TranspositionTable,
};

const TT_MEBIBYTES: usize = 1;
const SHORTER_MATE_FEN: &str = "7k/5Q2/6K1/8/8/8/8/8 w - - 0 1";
const LONGEST_SURVIVAL_FEN: &str = "4Q2k/8/4K3/8/8/8/8/8 b - - 0 1";
const MIDGAME_FEN: &str =
    "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1";

fn search(
    root: &Position,
    root_history: &SearchHistory,
    limits: SearchLimits,
    policy: &SearchPolicySet,
) -> SearchResult {
    let mut position = root.clone();
    let mut history = root_history.clone();
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
    assert_eq!(position, *root);
    assert_eq!(history, *root_history);
    position
        .validate_invariants()
        .expect("root invariants remain valid");
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
    assert_eq!(history.current_zobrist(), Some(position.zobrist()));
    replay_pv(
        root,
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

fn compare_exact(fen: &str, depth: u16) -> (SearchResult, SearchResult) {
    let root = Position::from_fen(fen).expect("fixture FEN parses");
    let history = SearchHistory::from_position(&root);
    compare_exact_with_history(&root, &history, depth)
}

fn compare_exact_with_history(
    root: &Position,
    history: &SearchHistory,
    depth: u16,
) -> (SearchResult, SearchResult) {
    let baseline = search(
        root,
        history,
        SearchLimits::new().with_depth(depth),
        &SearchPolicySet::baseline(),
    );
    let candidate = search(
        root,
        history,
        SearchLimits::new().with_depth(depth),
        &SearchPolicySet::null_move_pruning_candidate(),
    );
    assert_eq!(candidate.completed_depth(), baseline.completed_depth());
    assert_eq!(candidate.score(), baseline.score());
    let diagnostics = candidate.search_diagnostics();
    assert_eq!(
        diagnostics.null_move_speculative_fail_highs(),
        diagnostics.null_move_verification_searches()
    );
    assert!(diagnostics.null_move_cutoffs() <= diagnostics.null_move_verification_searches());
    assert!(!diagnostics.overflowed());
    (baseline, candidate)
}

fn play(game: &mut Game, text: &str) {
    let syntax = text.parse::<UciMove>().expect("fixture UCI parses");
    let current = game
        .legal_moves()
        .expect("legal moves generate")
        .iter()
        .find(|candidate| syntax.matches(*candidate))
        .expect("fixture move is legal");
    game.make_move(current).expect("fixture move applies");
}

fn repetition_root(cycles: usize) -> (Position, SearchHistory) {
    let mut game = Game::starting();
    for _ in 0..cycles {
        for current in ["g1f3", "g8f6", "f3g1", "f6g8"] {
            play(&mut game, current);
        }
    }
    (game.position().clone(), game.search_history())
}

#[test]
fn zugzwang_corpus_matches_baseline_and_stays_guarded() {
    for fen in [
        "8/8/8/8/4k3/8/4P3/4K3 w - - 0 1",
        "8/8/8/8/4k3/8/4P3/4K3 b - - 0 1",
        "8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1",
    ] {
        let (baseline, candidate) = compare_exact(fen, 6);
        assert_eq!(candidate.best_move(), baseline.best_move(), "{fen}");
        let diagnostics = candidate.search_diagnostics();
        assert!(diagnostics.null_move_attempts() > 0, "{fen}");
        assert!(diagnostics.null_move_disabled_nodes() > 0, "{fen}");
        assert_eq!(diagnostics.null_move_speculative_fail_highs(), 0, "{fen}");
        assert_eq!(diagnostics.null_move_verification_searches(), 0, "{fen}");
        assert_eq!(diagnostics.null_move_cutoffs(), 0, "{fen}");
    }
}

#[test]
fn stalemate_and_repetition_roots_are_resolved_before_null_search() {
    let (_, stalemate) = compare_exact("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1", 4);
    assert_eq!(stalemate.score(), Some(Score::ZERO));
    assert_eq!(stalemate.best_move(), None);
    assert_eq!(stalemate.nodes(), 1);
    assert_eq!(stalemate.search_diagnostics().null_move_attempts(), 0);

    let (baseline, after_pass) =
        compare_exact("7k/5K2/6Q1/8/8/8/8/8 w - - 0 1", 5);
    assert_eq!(after_pass.best_move(), baseline.best_move());
    assert_eq!(after_pass.search_diagnostics().null_move_cutoffs(), 0);

    for cycles in [2_usize, 4_usize] {
        let (root, history) = repetition_root(cycles);
        let (_, candidate) = compare_exact_with_history(&root, &history, 4);
        assert_eq!(candidate.score(), Some(Score::ZERO));
        assert_eq!(candidate.best_move(), None);
        assert_eq!(candidate.nodes(), 1);
        assert_eq!(candidate.search_diagnostics().null_move_attempts(), 0);
    }
}

#[test]
fn fifty_and_seventy_five_move_boundaries_are_exact() {
    let (_, before) = compare_exact("8/8/8/8/8/8/R3K3/7k w - - 99 1", 4);
    assert_ne!(before.score(), Some(Score::ZERO));
    assert!(before.best_move().is_some());

    for halfmove in [100_u16, 149_u16, 150_u16] {
        let fen = format!("8/8/8/8/8/8/R3K3/7k w - - {halfmove} 1");
        let (_, draw) = compare_exact(&fen, 4);
        assert_eq!(draw.score(), Some(Score::ZERO), "{fen}");
        assert_eq!(draw.best_move(), None, "{fen}");
        assert_eq!(draw.nodes(), 1, "{fen}");
        assert_eq!(draw.search_diagnostics().null_move_attempts(), 0, "{fen}");
    }
}

#[test]
fn mate_distance_and_longest_survival_match_baseline() {
    let (baseline_fast, candidate_fast) = compare_exact(SHORTER_MATE_FEN, 3);
    assert_eq!(
        candidate_fast.score(),
        Some(Score::mate_in(1).expect("mate-in-one score exists"))
    );
    assert_eq!(candidate_fast.best_move(), baseline_fast.best_move());

    let (baseline_slow, candidate_slow) = compare_exact(LONGEST_SURVIVAL_FEN, 6);
    assert_eq!(
        candidate_slow.score(),
        Some(Score::mated_in(6).expect("mated-in-six score exists"))
    );
    assert_eq!(candidate_slow.best_move(), baseline_slow.best_move());
    assert_eq!(
        candidate_slow
            .best_move()
            .expect("forced loss has a survival move")
            .to_uci(),
        "h8g7"
    );
}

#[test]
fn repeated_success_and_bounded_cancellation_restore_exactly() {
    let root = Position::from_fen(MIDGAME_FEN).expect("midgame FEN parses");
    let history = SearchHistory::from_position(&root);
    let policy = SearchPolicySet::null_move_pruning_candidate();

    let first = search(
        &root,
        &history,
        SearchLimits::new().with_depth(5),
        &policy,
    );
    for _ in 0..3 {
        let repeated = search(
            &root,
            &history,
            SearchLimits::new().with_depth(5),
            &policy,
        );
        assert_eq!(repeated.score(), first.score());
        assert_eq!(repeated.best_move(), first.best_move());
        assert_eq!(repeated.nodes(), first.nodes());
        assert_eq!(
            repeated.search_diagnostics().semantic_checksum(),
            first.search_diagnostics().semantic_checksum()
        );
    }

    for nodes in [64_u64, 128, 256, 512, 768] {
        let limited = search(
            &root,
            &history,
            SearchLimits::new().with_depth(9).with_nodes(nodes),
            &policy,
        );
        assert!(limited.nodes() <= nodes);
        assert!(limited.completed_depth() < 9);
        for iteration in limited.completed().iterations() {
            let diagnostics = iteration.search_diagnostics();
            assert_eq!(
                diagnostics.null_move_speculative_fail_highs(),
                diagnostics.null_move_verification_searches()
            );
            assert!(
                diagnostics.null_move_cutoffs() <= diagnostics.null_move_verification_searches()
            );
            assert!(!diagnostics.overflowed());
        }
    }
}
