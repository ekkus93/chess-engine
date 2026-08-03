use chess_core::{Move, Position, SearchHistory};
use chess_search::{
    alpha_beta_search, iterative_deepening_search,
    iterative_deepening_search_with_transposition_table, AlphaBetaSearchError,
    AspirationWindowOutcome, IterativeDeepeningSearchError, PrincipalVariationTermination,
    TranspositionTable, TranspositionTableDiagnostics, DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS,
    MAX_MATE_PLY,
};

fn benchmark_position() -> Position {
    "7k/8/8/1p2q3/2P1Q3/8/K7/8 w - - 0 1"
        .parse()
        .expect("iterative-deepening benchmark FEN is valid")
}

fn assert_legal_line(root: &Position, line: &[Move]) {
    let mut cursor = root.clone();
    for current in line {
        let tokens = cursor
            .legal_move_tokens()
            .expect("PV legal tokens generate");
        let token = tokens
            .iter()
            .find(|token| token.move_made() == *current)
            .expect("every returned PV move is legal in sequence");
        cursor
            .make_legal_token(token)
            .expect("returned PV move applies");
    }
}

#[test]
fn every_depth_is_preserved_and_matches_independent_full_window_search() {
    let root = benchmark_position();
    let mut position = root.clone();
    let position_snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let mut table = TranspositionTable::new(1).expect("bounded table allocates");

    let result = iterative_deepening_search_with_transposition_table(
        &mut position,
        &mut history,
        3,
        &mut table,
    )
    .expect("iterative deepening succeeds");

    assert_eq!(result.completed_depth(), 3);
    assert_eq!(result.iterations().len(), 3);
    assert_eq!(
        result
            .iterations()
            .iter()
            .map(|iteration| iteration.depth())
            .collect::<Vec<_>>(),
        vec![1, 2, 3]
    );
    assert_eq!(
        result.total_nodes(),
        result
            .iterations()
            .iter()
            .map(|iteration| iteration.nodes())
            .sum()
    );

    for (index, iteration) in result.iterations().iter().enumerate() {
        let mut independent_position = benchmark_position();
        let mut independent_history = SearchHistory::from_position(&independent_position);
        let independent = alpha_beta_search(
            &mut independent_position,
            &mut independent_history,
            iteration.depth(),
        )
        .expect("independent fixed-depth search succeeds");

        assert_eq!(iteration.score(), independent.score());
        assert_eq!(iteration.best_move(), independent.best_move());
        assert_eq!(
            iteration.principal_variation().moves().first().copied(),
            iteration.best_move()
        );
        assert!(iteration.principal_variation().len() <= usize::from(iteration.depth()));
        assert_legal_line(&root, iteration.principal_variation().moves());

        let aspiration = iteration.aspiration_diagnostics();
        if index == 0 {
            assert_eq!(aspiration.center(), None);
            assert!(aspiration.initial_attempt().is_full_window());
        } else {
            let prior = result.iterations()[index - 1].score();
            assert_eq!(aspiration.center(), Some(prior));
            let initial = aspiration.initial_attempt();
            if !initial.is_full_window() {
                assert_eq!(
                    initial.alpha().centipawns(),
                    prior.centipawns() - DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS
                );
                assert_eq!(
                    initial.beta().centipawns(),
                    prior.centipawns() + DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS
                );
            }
        }
        assert_eq!(
            aspiration.final_attempt().outcome(),
            AspirationWindowOutcome::Exact
        );
        assert_eq!(
            aspiration.final_attempt().exact_score(),
            Some(iteration.score())
        );
        assert!(aspiration.retry_count() <= 1);

        let initial = aspiration.initial_attempt();
        let expected_nodes = aspiration
            .full_window_retry()
            .map_or(initial.nodes(), |retry| {
                initial
                    .nodes()
                    .checked_add(retry.nodes())
                    .expect("small iteration node total fits")
            });
        let expected_diagnostics =
            aspiration
                .full_window_retry()
                .map_or(initial.transposition_diagnostics(), |retry| {
                    initial
                        .transposition_diagnostics()
                        .saturating_add(retry.transposition_diagnostics())
                });
        assert_eq!(iteration.nodes(), expected_nodes);
        assert_eq!(iteration.transposition_diagnostics(), expected_diagnostics);
        assert!(iteration.result().nodes() <= iteration.nodes());

        assert_eq!(independent_position, benchmark_position());
        assert_eq!(
            independent_position.zobrist(),
            independent_position.recomputed_zobrist()
        );
    }

    assert_eq!(
        result
            .iterations()
            .iter()
            .map(|iteration| iteration.transposition_generation())
            .collect::<Vec<_>>(),
        vec![1, 2, 3]
    );
    assert_eq!(table.generation(), 3);
    assert!(result.iterations()[0].transposition_diagnostics().probes() > 0);
    assert!(result.iterations()[1].transposition_diagnostics().hits() > 0);
    assert!(result.iterations()[2].transposition_diagnostics().hits() > 0);
    for iteration in result.iterations() {
        assert!(iteration.transposition_diagnostics().stores() > 0);
        assert!(iteration.hash_full().sampled_slots() > 0);
        assert!(iteration.hash_full().per_mille() <= 1_000);
    }

    assert_eq!(position, position_snapshot);
    assert_eq!(history, history_snapshot);
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
}

#[test]
fn convenience_search_reuses_one_bounded_table_and_returns_the_final_iteration() {
    let root = Position::starting();
    let mut position = root.clone();
    let position_snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();

    let result = iterative_deepening_search(&mut position, &mut history, 3)
        .expect("convenience iterative deepening succeeds");
    let final_iteration = result
        .final_iteration()
        .expect("positive maximum depth always completes a final iteration");

    assert_eq!(final_iteration.depth(), 3);
    assert_eq!(final_iteration.transposition_generation(), 3);
    assert!(final_iteration.result().nodes() <= final_iteration.nodes());
    assert!(final_iteration.transposition_diagnostics().hits() > 0);
    assert_eq!(
        final_iteration
            .aspiration_diagnostics()
            .final_attempt()
            .outcome(),
        AspirationWindowOutcome::Exact
    );
    assert!(!final_iteration.principal_variation().is_empty());
    assert_eq!(
        final_iteration.ponder_move(),
        final_iteration
            .principal_variation()
            .moves()
            .get(1)
            .copied()
    );
    assert_eq!(result.ponder_move(), final_iteration.ponder_move());
    assert_eq!(
        result.principal_variation(),
        Some(final_iteration.principal_variation())
    );
    assert_legal_line(&root, final_iteration.principal_variation().moves());
    assert_eq!(position, position_snapshot);
    assert_eq!(history, history_snapshot);
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
}

#[test]
fn terminal_roots_use_safe_full_windows_and_empty_terminal_principal_variations() {
    let mut position: Position = "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1"
        .parse()
        .expect("checkmate FEN is valid");
    let position_snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let mut table = TranspositionTable::new(1).expect("bounded table allocates");

    let result = iterative_deepening_search_with_transposition_table(
        &mut position,
        &mut history,
        3,
        &mut table,
    )
    .expect("terminal iterative deepening succeeds");

    assert_eq!(result.iterations().len(), 3);
    for iteration in result.iterations() {
        assert_eq!(iteration.nodes(), 1);
        assert_eq!(iteration.best_move(), None);
        assert!(iteration.score().is_mate());
        assert!(iteration.principal_variation().is_empty());
        assert_eq!(
            iteration.principal_variation().termination(),
            PrincipalVariationTermination::TerminalPosition { ply: 0 }
        );
        assert_eq!(iteration.ponder_move(), None);
        assert!(iteration
            .aspiration_diagnostics()
            .initial_attempt()
            .is_full_window());
        assert_eq!(iteration.aspiration_diagnostics().retry_count(), 0);
        assert_eq!(
            iteration.transposition_diagnostics(),
            TranspositionTableDiagnostics::default()
        );
        assert_eq!(iteration.hash_full().occupied_current_generation(), 0);
    }
    assert_eq!(result.total_nodes(), 3);
    assert_eq!(table.generation(), 3);
    assert_eq!(position, position_snapshot);
    assert_eq!(history, history_snapshot);
}

#[test]
fn invalid_maximum_depths_fail_before_mutating_a_caller_owned_table() {
    let mut position = benchmark_position();
    let mut history = SearchHistory::from_position(&position);
    let mut table = TranspositionTable::new(1).expect("bounded table allocates");
    let generation = table.generation();
    let diagnostics = table.diagnostics();
    let capacity = table.entry_capacity();

    assert_eq!(
        iterative_deepening_search_with_transposition_table(
            &mut position,
            &mut history,
            0,
            &mut table,
        ),
        Err(IterativeDeepeningSearchError::ZeroMaximumDepth)
    );
    assert_eq!(
        iterative_deepening_search_with_transposition_table(
            &mut position,
            &mut history,
            MAX_MATE_PLY + 1,
            &mut table,
        ),
        Err(IterativeDeepeningSearchError::MaximumDepthTooLarge {
            maximum_depth: MAX_MATE_PLY + 1,
            supported: MAX_MATE_PLY,
        })
    );

    assert_eq!(table.generation(), generation);
    assert_eq!(table.diagnostics(), diagnostics);
    assert_eq!(table.entry_capacity(), capacity);
}

#[test]
fn mismatched_history_fails_on_depth_one_without_mutating_table_or_position() {
    let mut position = benchmark_position();
    let position_snapshot = position.clone();
    let other_position: Position = "8/8/8/8/8/8/4K3/6k1 w - - 0 1"
        .parse()
        .expect("alternate history root is valid");
    let mut history = SearchHistory::from_position(&other_position);
    let history_snapshot = history.clone();
    let mut table = TranspositionTable::new(1).expect("bounded table allocates");

    let error = iterative_deepening_search_with_transposition_table(
        &mut position,
        &mut history,
        2,
        &mut table,
    )
    .expect_err("mismatched history must fail");

    assert!(matches!(
        error,
        IterativeDeepeningSearchError::IterationFailed {
            depth: 1,
            error: AlphaBetaSearchError::HistoryPositionMismatch { .. },
        }
    ));
    assert_eq!(table.generation(), 0);
    assert_eq!(
        table.diagnostics(),
        TranspositionTableDiagnostics::default()
    );
    assert_eq!(position, position_snapshot);
    assert_eq!(history, history_snapshot);
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
}
