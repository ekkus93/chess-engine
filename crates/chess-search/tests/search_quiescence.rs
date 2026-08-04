use chess_core::{Game, Move, Position, SearchHistory, UciMove};
use chess_search::{
    alpha_beta_search, evaluate, quiescence_search, quiescence_search_with_cancellation,
    quiescence_search_with_limit, AlphaBetaSearchError, QuiescenceSearchResult, Score,
    MAX_QUIESCENCE_PLY,
};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
struct OracleResult {
    score: Score,
    best_move: Option<Move>,
    nodes: u64,
}

fn position(fen: &str) -> Position {
    fen.parse().expect("quiescence fixture FEN is valid")
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

fn play_knight_cycle(game: &mut Game) {
    play(game, "g1f3");
    play(game, "g8f6");
    play(game, "f3g1");
    play(game, "f6g8");
}

fn reference_quiescence(
    position: &mut Position,
    history: &mut SearchHistory,
    ply: u16,
    quiescence_ply: u16,
) -> OracleResult {
    let tokens = position
        .legal_move_tokens()
        .expect("oracle legal tokens generate");
    if tokens.is_empty() {
        let score = if position.is_in_check(position.side_to_move()) {
            Score::mated_in(ply).expect("fixture mate ply is supported")
        } else {
            Score::ZERO
        };
        return OracleResult {
            score,
            best_move: None,
            nodes: 1,
        };
    }

    if position.is_dead_position()
        || history.repetition_count(position) >= 3
        || position.halfmove_clock().get() >= 100
    {
        return OracleResult {
            score: Score::ZERO,
            best_move: None,
            nodes: 1,
        };
    }

    let in_check = position.is_in_check(position.side_to_move());
    let mut best_score = (!in_check).then(|| evaluate(position));
    let mut best_move = None;
    if quiescence_ply >= MAX_QUIESCENCE_PLY {
        assert!(!in_check, "fixtures must not exhaust the guard in check");
        return OracleResult {
            score: best_score.expect("stand-pat exists outside check"),
            best_move: None,
            nodes: 1,
        };
    }

    let mut nodes = 1_u64;
    for token in tokens.iter() {
        let current = token.move_made();
        if !in_check && !current.kind().is_capture() && current.promotion().is_none() {
            continue;
        }

        let position_undo = position
            .make_legal_token(token)
            .expect("oracle token applies");
        let history_undo = history.push_position(position);
        let child = reference_quiescence(position, history, ply + 1, quiescence_ply + 1);
        history
            .pop_position(history_undo)
            .expect("oracle history restores");
        position
            .unmake_move(position_undo)
            .expect("oracle position restores");

        nodes = nodes
            .checked_add(child.nodes)
            .expect("oracle node count fits");
        let score = -child.score;
        let replace_best = match best_score {
            Some(previous) => score > previous,
            None => true,
        };
        if replace_best {
            best_score = Some(score);
            best_move = Some(current);
        }
    }

    OracleResult {
        score: best_score.expect("checked node has an evasion or stand-pat exists"),
        best_move,
        nodes,
    }
}

fn search_pair(label: &str, root: &Position) -> (OracleResult, QuiescenceSearchResult) {
    let mut oracle_position = root.clone();
    let oracle_snapshot = oracle_position.clone();
    let mut oracle_history = SearchHistory::from_position(&oracle_position);
    let oracle_history_snapshot = oracle_history.clone();
    let oracle = reference_quiescence(&mut oracle_position, &mut oracle_history, 0, 0);
    assert_restored(
        &format!("{label} oracle"),
        &oracle_position,
        &oracle_snapshot,
        &oracle_history,
        &oracle_history_snapshot,
    );

    let mut searched_position = root.clone();
    let searched_snapshot = searched_position.clone();
    let mut searched_history = SearchHistory::from_position(&searched_position);
    let searched_history_snapshot = searched_history.clone();
    let searched = quiescence_search(&mut searched_position, &mut searched_history)
        .expect("quiescence search succeeds");
    assert_restored(
        &format!("{label} alpha-beta"),
        &searched_position,
        &searched_snapshot,
        &searched_history,
        &searched_history_snapshot,
    );

    assert_eq!(searched.score(), oracle.score, "score: {label}");
    assert_eq!(searched.best_move(), oracle.best_move, "best move: {label}");
    assert!(
        searched.nodes() <= oracle.nodes,
        "quiescence visited {} nodes versus oracle {}: {label}",
        searched.nodes(),
        oracle.nodes
    );

    (oracle, searched)
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

fn quiescence_move_score(root: &Position, text: &str) -> Score {
    let expected_move = legal_move(root, text);
    let mut position = root.clone();
    let position_snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let tokens = position
        .legal_move_tokens()
        .expect("root legal tokens generate");
    let token = tokens
        .iter()
        .find(|candidate| candidate.move_made() == expected_move)
        .expect("root legal token is present");
    let position_undo = position
        .make_legal_token(token)
        .expect("root legal token applies");
    let history_undo = history.push_position(&position);
    let child =
        quiescence_search(&mut position, &mut history).expect("quiescence child search succeeds");
    history
        .pop_position(history_undo)
        .expect("quiescence child history restores");
    position
        .unmake_move(position_undo)
        .expect("quiescence child position restores");
    assert_restored(
        &format!("move score {text}"),
        &position,
        &position_snapshot,
        &history,
        &history_snapshot,
    );
    -child.score()
}

#[test]
fn full_window_quiescence_matches_an_unpruned_tactical_oracle() {
    for (label, fen) in [
        ("hanging-rook", "3r3k/8/8/8/8/8/8/K2Q4 w - - 0 1"),
        ("quiet-check-evasions", "4r2k/8/8/8/8/8/8/4K3 w - - 0 1"),
        ("promotion", "7k/P7/8/8/8/8/8/K7 w - - 0 1"),
        ("poisoned-rook", "3rk3/8/8/8/8/8/8/K2Q4 w - - 0 1"),
    ] {
        let root = position(fen);
        let (_oracle, _searched) = search_pair(label, &root);
    }
}

#[test]
fn depth_zero_alpha_beta_resolves_a_hanging_capture() {
    let root = position("3r3k/8/8/8/8/8/8/K2Q4 w - - 0 1");
    let static_score = evaluate(&root);
    let expected_move = legal_move(&root, "d1d8");

    let mut quiescence_position = root.clone();
    let mut quiescence_history = SearchHistory::from_position(&quiescence_position);
    let quiescence = quiescence_search(&mut quiescence_position, &mut quiescence_history)
        .expect("quiescence succeeds");

    let mut alpha_beta_position = root;
    let mut alpha_beta_history = SearchHistory::from_position(&alpha_beta_position);
    let alpha_beta = alpha_beta_search(&mut alpha_beta_position, &mut alpha_beta_history, 0)
        .expect("depth-zero alpha-beta succeeds");

    assert!(quiescence.score() > static_score);
    assert_eq!(quiescence.best_move(), Some(expected_move));
    assert_eq!(alpha_beta, quiescence);
}

#[test]
fn checked_leaf_searches_quiet_evasions_and_promotions_are_tactical() {
    let checked = position("4r2k/8/8/8/8/8/8/4K3 w - - 0 1");
    let (_oracle, searched) = search_pair("checked-leaf", &checked);
    let evasion = searched.best_move().expect("checked root has an evasion");
    assert!(searched.nodes() > 1);
    assert!(!evasion.kind().is_capture());
    assert_eq!(evasion.promotion(), None);

    let promotion = position("7k/P7/8/8/8/8/8/K7 w - - 0 1");
    let static_score = evaluate(&promotion);
    let (_oracle, searched) = search_pair("promotion-scope", &promotion);
    let best_move = searched.best_move().expect("promotion improves stand-pat");
    assert!(searched.score() > static_score);
    assert!(best_move.promotion().is_some());
}

#[test]
fn poisoned_capture_is_rejected_after_the_forced_recapture() {
    let root = position("3rk3/8/8/8/8/8/8/K2Q4 w - - 0 1");
    let poisoned = legal_move(&root, "d1d8");
    let poisoned_score = quiescence_move_score(&root, "d1d8");
    let mut position = root.clone();
    let snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();

    let searched =
        alpha_beta_search(&mut position, &mut history, 1).expect("one-ply alpha-beta succeeds");

    assert_ne!(searched.best_move(), Some(poisoned));
    assert!(searched.score() > poisoned_score);
    assert_restored(
        "poisoned capture",
        &position,
        &snapshot,
        &history,
        &history_snapshot,
    );
}

#[test]
fn guard_draw_and_cancellation_paths_are_fail_loud_and_reversible() {
    let mut checked = position("4r2k/8/8/8/8/8/8/4K3 w - - 0 1");
    let checked_snapshot = checked.clone();
    let mut checked_history = SearchHistory::from_position(&checked);
    let checked_history_snapshot = checked_history.clone();
    assert_eq!(
        quiescence_search_with_limit(&mut checked, &mut checked_history, 0),
        Err(AlphaBetaSearchError::QuiescenceDepthLimitReachedInCheck {
            quiescence_ply: 0,
            maximum: 0,
        })
    );
    assert_restored(
        "in-check guard",
        &checked,
        &checked_snapshot,
        &checked_history,
        &checked_history_snapshot,
    );

    let mut game = Game::starting();
    play_knight_cycle(&mut game);
    play_knight_cycle(&mut game);
    let mut draw_position = game.position().clone();
    let draw_snapshot = draw_position.clone();
    let mut draw_history = game.search_history();
    let draw_history_snapshot = draw_history.clone();
    let draw = quiescence_search(&mut draw_position, &mut draw_history)
        .expect("repetition qsearch succeeds");
    assert_eq!(draw.score(), Score::ZERO);
    assert_eq!(draw.best_move(), None);
    assert_eq!(draw.nodes(), 1);
    assert_restored(
        "repetition draw",
        &draw_position,
        &draw_snapshot,
        &draw_history,
        &draw_history_snapshot,
    );

    let mut position = position("3r3k/8/8/8/8/8/8/K2Q4 w - - 0 1");
    let snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let mut checks = 0_u32;
    let mut cancellation = || {
        checks += 1;
        checks >= 3
    };
    let cancelled = quiescence_search_with_cancellation(
        &mut position,
        &mut history,
        MAX_QUIESCENCE_PLY,
        &mut cancellation,
    );
    assert_eq!(cancelled, Err(AlphaBetaSearchError::Cancelled));
    assert!(checks >= 3);
    assert_restored(
        "cancelled quiescence",
        &position,
        &snapshot,
        &history,
        &history_snapshot,
    );
}
