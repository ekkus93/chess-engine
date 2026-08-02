use chess_core::{Move, Position, SearchHistory, UciMove};
use chess_search::{
    alpha_beta_search, evaluate, quiescence_search, quiescence_search_with_limit,
    AlphaBetaSearchError, QuiescenceSearchResult, Score,
};

fn position(fen: &str) -> Position {
    fen.parse().expect("Task 14.4 fixture FEN is valid")
}

fn assert_restored(
    label: &str,
    position: &Position,
    position_snapshot: &Position,
    history: &SearchHistory,
    history_snapshot: &SearchHistory,
) {
    assert_eq!(position, position_snapshot, "position changed: {label}");
    assert_eq!(history, history_snapshot, "history changed: {label}");
    position
        .validate_invariants()
        .unwrap_or_else(|error| panic!("position invariant failed after {label}: {error}"));
    assert_eq!(
        position.zobrist(),
        position.recomputed_zobrist(),
        "incremental hash diverged: {label}"
    );
    assert_eq!(
        history.current_zobrist(),
        Some(position.zobrist()),
        "history root diverged: {label}"
    );
}

fn legal_move(position: &Position, text: &str) -> Move {
    let syntax = text.parse::<UciMove>().expect("fixture UCI is valid");
    let mut copy = position.clone();
    copy.legal_moves()
        .expect("fixture legal generation succeeds")
        .iter()
        .find(|candidate| syntax.matches(*candidate))
        .expect("fixture move is legal")
}

fn search(root: &Position, label: &str) -> QuiescenceSearchResult {
    let mut position = root.clone();
    let position_snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let result = quiescence_search(&mut position, &mut history)
        .unwrap_or_else(|error| panic!("Task 14.4 search failed for {label}: {error}"));
    assert_restored(
        label,
        &position,
        &position_snapshot,
        &history,
        &history_snapshot,
    );
    result
}

fn static_move_score(root: &Position, text: &str) -> Score {
    let expected_move = legal_move(root, text);
    let mut position = root.clone();
    let position_snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let tokens = position
        .legal_move_tokens()
        .expect("fixture legal tokens generate");
    let token = tokens
        .iter()
        .find(|candidate| candidate.move_made() == expected_move)
        .expect("fixture legal token is present");
    let position_undo = position
        .make_legal_token(token)
        .expect("fixture legal token applies");
    let history_undo = history.push_position(&position);
    let score = -evaluate(&position);
    history
        .pop_position(history_undo)
        .expect("static-score history restores");
    position
        .unmake_move(position_undo)
        .expect("static-score position restores");
    assert_restored(
        &format!("static move score {text}"),
        &position,
        &position_snapshot,
        &history,
        &history_snapshot,
    );
    score
}

fn quiescence_move_score(root: &Position, text: &str) -> Score {
    let expected_move = legal_move(root, text);
    let mut position = root.clone();
    let position_snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let tokens = position
        .legal_move_tokens()
        .expect("fixture legal tokens generate");
    let token = tokens
        .iter()
        .find(|candidate| candidate.move_made() == expected_move)
        .expect("fixture legal token is present");
    let position_undo = position
        .make_legal_token(token)
        .expect("fixture legal token applies");
    let history_undo = history.push_position(&position);
    let child = quiescence_search(&mut position, &mut history)
        .expect("quiescence move-score search succeeds");
    history
        .pop_position(history_undo)
        .expect("quiescence move-score history restores");
    position
        .unmake_move(position_undo)
        .expect("quiescence move-score position restores");
    assert_restored(
        &format!("quiescence move score {text}"),
        &position,
        &position_snapshot,
        &history,
        &history_snapshot,
    );
    -child.score()
}

#[test]
fn horizon_capture_sequence_is_searched_to_a_quiet_position() {
    let root = position("4r2k/8/8/4q3/4Q3/8/8/1K2R3 w - - 0 1");
    let expected = legal_move(&root, "e4e5");
    let stand_pat = evaluate(&root);
    let searched = search(&root, "horizon capture sequence");

    assert_eq!(searched.best_move(), Some(expected));
    assert!(searched.score() > stand_pat);
    assert!(
        searched.nodes() >= 4,
        "the Qxe5 Rxe5 Rxe5 sequence must reach beyond the nominal leaf"
    );
}

#[test]
fn in_check_leaf_must_search_a_quiet_evasion_instead_of_standing_pat() {
    let root = position("4r2k/8/8/8/8/8/8/4K3 w - - 0 1");
    assert!(root.is_in_check(root.side_to_move()));

    let searched = search(&root, "in-check leaf");
    let evasion = searched
        .best_move()
        .expect("an in-check non-terminal node must return a searched evasion");

    assert!(searched.nodes() > 1);
    assert!(!evasion.kind().is_capture());
    assert_eq!(evasion.promotion(), None);
}

#[test]
fn promotion_sequence_is_searched_through_the_forced_recapture() {
    let root = position("r6k/4P3/8/8/8/8/8/1K2R3 w - - 0 1");
    let stand_pat = evaluate(&root);
    let searched = search(&root, "promotion sequence");
    let promotion = searched
        .best_move()
        .expect("promotion sequence has a best tactical move");

    assert!(promotion.promotion().is_some());
    assert_eq!(promotion.source().to_string(), "e7");
    assert_eq!(promotion.destination().to_string(), "e8");
    assert!(searched.score() > stand_pat);
    assert!(
        searched.nodes() >= 4,
        "promotion, recapture, and counter-recapture must all be searched"
    );
}

#[test]
fn poisoned_capture_is_revalued_by_quiescence_before_root_selection() {
    let root = position("3rk3/8/8/8/8/8/8/K2Q4 w - - 0 1");
    let poisoned = legal_move(&root, "d1d8");
    let static_leaf_score = static_move_score(&root, "d1d8");
    let quiescent_leaf_score = quiescence_move_score(&root, "d1d8");

    assert!(
        static_leaf_score > quiescent_leaf_score,
        "the forced Kxd8 recapture must lower the apparent static-leaf score"
    );

    let mut position = root.clone();
    let position_snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let searched =
        alpha_beta_search(&mut position, &mut history, 1).expect("one-ply search succeeds");

    assert_ne!(searched.best_move(), Some(poisoned));
    assert!(searched.score() > quiescent_leaf_score);
    assert_restored(
        "poisoned capture root search",
        &position,
        &position_snapshot,
        &history,
        &history_snapshot,
    );
}

#[test]
fn quiescence_guard_is_finite_outside_check_and_fail_loud_in_check() {
    let quiet_root = position("3r3k/8/8/8/8/8/8/K2Q4 w - - 0 1");
    let quiet_stand_pat = evaluate(&quiet_root);
    let mut quiet_position = quiet_root.clone();
    let quiet_snapshot = quiet_position.clone();
    let mut quiet_history = SearchHistory::from_position(&quiet_position);
    let quiet_history_snapshot = quiet_history.clone();
    let limited = quiescence_search_with_limit(&mut quiet_position, &mut quiet_history, 0)
        .expect("an unchecked node may stop at stand-pat when the guard is reached");

    assert_eq!(limited.score(), quiet_stand_pat);
    assert_eq!(limited.best_move(), None);
    assert_eq!(limited.nodes(), 1);
    assert_restored(
        "unchecked quiescence guard",
        &quiet_position,
        &quiet_snapshot,
        &quiet_history,
        &quiet_history_snapshot,
    );

    let checked_root = position("4r2k/8/8/8/8/8/8/4K3 w - - 0 1");
    let mut checked_position = checked_root.clone();
    let checked_snapshot = checked_position.clone();
    let mut checked_history = SearchHistory::from_position(&checked_position);
    let checked_history_snapshot = checked_history.clone();
    let error = quiescence_search_with_limit(&mut checked_position, &mut checked_history, 0);

    assert_eq!(
        error,
        Err(AlphaBetaSearchError::QuiescenceDepthLimitReachedInCheck {
            quiescence_ply: 0,
            maximum: 0,
        })
    );
    assert_restored(
        "checked quiescence guard",
        &checked_position,
        &checked_snapshot,
        &checked_history,
        &checked_history_snapshot,
    );
}
