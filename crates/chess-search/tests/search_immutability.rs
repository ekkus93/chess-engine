use std::cell::Cell;

use chess_core::{Game, Position, SearchHistory, UciMove};
use chess_search::{
    alpha_beta_search, alpha_beta_search_with_cancellation, reference_search,
    reference_search_with_cancellation, AlphaBetaSearchError, ReferenceSearchError, MAX_MATE_PLY,
};

fn position(fen: &str) -> Position {
    fen.parse().expect("immutability fixture FEN is valid")
}

fn play(game: &mut Game, text: &str) {
    let syntax = text.parse::<UciMove>().expect("test UCI is valid");
    let current = game
        .legal_moves()
        .expect("legal generation succeeds")
        .iter()
        .find(|candidate| syntax.matches(*candidate))
        .expect("test move is legal");
    let _undo = game.make_move(current).expect("test move is playable");
}

fn opening_game() -> Game {
    let mut game = Game::starting();
    for current in ["e2e4", "e7e5", "g1f3", "b8c6"] {
        play(&mut game, current);
    }
    game
}

fn assert_position_valid(label: &str, position: &Position) {
    position
        .validate_invariants()
        .unwrap_or_else(|error| panic!("position invariant failed after {label}: {error}"));
    assert_eq!(
        position.zobrist(),
        position.recomputed_zobrist(),
        "incremental hash diverged after {label}"
    );
}

fn assert_state_restored(
    label: &str,
    position: &Position,
    position_snapshot: &Position,
    history: &SearchHistory,
    history_snapshot: &SearchHistory,
) {
    assert_eq!(
        position, position_snapshot,
        "position changed after {label}"
    );
    assert_eq!(history, history_snapshot, "history changed after {label}");
    assert_position_valid(label, position);
    assert_eq!(
        history.current_zobrist(),
        Some(position.zobrist()),
        "history root diverged after {label}"
    );
}

#[test]
fn repeated_successful_searches_do_not_accumulate_state_or_history_drift() {
    let game = opening_game();
    let mut position = game.position().clone();
    let position_snapshot = position.clone();
    let mut history = game.search_history();
    let history_snapshot = history.clone();
    let mut first_reference = None;
    let mut first_alpha_beta = None;

    for iteration in 0..4 {
        let reference =
            reference_search(&mut position, &mut history, 2).expect("reference search succeeds");
        assert_state_restored(
            &format!("reference iteration {iteration}"),
            &position,
            &position_snapshot,
            &history,
            &history_snapshot,
        );
        match first_reference {
            Some(expected) => assert_eq!(reference, expected),
            None => first_reference = Some(reference),
        }

        let alpha_beta =
            alpha_beta_search(&mut position, &mut history, 3).expect("alpha-beta search succeeds");
        assert_state_restored(
            &format!("alpha-beta iteration {iteration}"),
            &position,
            &position_snapshot,
            &history,
            &history_snapshot,
        );
        match first_alpha_beta {
            Some(expected) => assert_eq!(alpha_beta, expected),
            None => first_alpha_beta = Some(alpha_beta),
        }
    }
}

#[test]
fn reference_cancellation_from_inside_the_tree_restores_every_active_state() {
    let game = opening_game();
    let mut position = game.position().clone();
    let position_snapshot = position.clone();
    let mut history = game.search_history();
    let history_snapshot = history.clone();
    let checks = Cell::new(0_usize);
    let mut cancellation = || {
        let next = checks.get() + 1;
        checks.set(next);
        next >= 64
    };

    let result =
        reference_search_with_cancellation(&mut position, &mut history, 4, &mut cancellation);

    assert_eq!(result, Err(ReferenceSearchError::Cancelled));
    assert!(
        checks.get() >= 64,
        "cancellation must occur inside the tree"
    );
    assert_state_restored(
        "mid-tree reference cancellation",
        &position,
        &position_snapshot,
        &history,
        &history_snapshot,
    );
}

#[test]
fn alpha_beta_cancellation_from_inside_the_tree_restores_every_active_state() {
    let game = opening_game();
    let mut position = game.position().clone();
    let position_snapshot = position.clone();
    let mut history = game.search_history();
    let history_snapshot = history.clone();
    let checks = Cell::new(0_usize);
    let mut cancellation = || {
        let next = checks.get() + 1;
        checks.set(next);
        next >= 64
    };

    let result =
        alpha_beta_search_with_cancellation(&mut position, &mut history, 5, &mut cancellation);

    assert_eq!(result, Err(AlphaBetaSearchError::Cancelled));
    assert!(
        checks.get() >= 64,
        "cancellation must occur inside the tree"
    );
    assert_state_restored(
        "mid-tree alpha-beta cancellation",
        &position,
        &position_snapshot,
        &history,
        &history_snapshot,
    );
}

#[test]
fn terminal_and_validation_error_paths_are_non_mutating_and_invariant_clean() {
    for fen in [
        "7k/6Q1/6K1/8/8/8/8/8 b - - 150 1",
        "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1",
        "8/8/8/8/8/8/R3K3/7k w - - 100 1",
    ] {
        let mut root = position(fen);
        let root_snapshot = root.clone();
        let mut history = SearchHistory::from_position(&root);
        let history_snapshot = history.clone();

        reference_search(&mut root, &mut history, 3).expect("terminal reference search succeeds");
        assert_state_restored(
            "terminal reference completion",
            &root,
            &root_snapshot,
            &history,
            &history_snapshot,
        );

        alpha_beta_search(&mut root, &mut history, 3).expect("terminal alpha-beta search succeeds");
        assert_state_restored(
            "terminal alpha-beta completion",
            &root,
            &root_snapshot,
            &history,
            &history_snapshot,
        );
    }

    let mut root = Position::starting();
    let root_snapshot = root.clone();
    let other = position("7k/8/8/8/8/8/8/K7 w - - 0 1");
    let mut mismatched_history = SearchHistory::from_position(&other);
    let mismatched_snapshot = mismatched_history.clone();

    assert!(matches!(
        reference_search(&mut root, &mut mismatched_history, 1),
        Err(ReferenceSearchError::HistoryPositionMismatch { .. })
    ));
    assert_eq!(root, root_snapshot);
    assert_eq!(mismatched_history, mismatched_snapshot);
    assert_position_valid("reference history validation failure", &root);

    assert!(matches!(
        alpha_beta_search(&mut root, &mut mismatched_history, 1),
        Err(AlphaBetaSearchError::HistoryPositionMismatch { .. })
    ));
    assert_eq!(root, root_snapshot);
    assert_eq!(mismatched_history, mismatched_snapshot);
    assert_position_valid("alpha-beta history validation failure", &root);

    let mut history = SearchHistory::from_position(&root);
    let history_snapshot = history.clone();
    assert!(matches!(
        reference_search(&mut root, &mut history, MAX_MATE_PLY + 1),
        Err(ReferenceSearchError::DepthTooLarge { .. })
    ));
    assert_state_restored(
        "reference depth validation failure",
        &root,
        &root_snapshot,
        &history,
        &history_snapshot,
    );

    assert!(matches!(
        alpha_beta_search(&mut root, &mut history, MAX_MATE_PLY + 1),
        Err(AlphaBetaSearchError::DepthTooLarge { .. })
    ));
    assert_state_restored(
        "alpha-beta depth validation failure",
        &root,
        &root_snapshot,
        &history,
        &history_snapshot,
    );
}
