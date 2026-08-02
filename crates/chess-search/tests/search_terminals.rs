use chess_core::{Game, Move, Position, SearchHistory, UciMove};
use chess_search::{
    alpha_beta_search, reference_search_with_quiescence, AlphaBetaSearchResult,
    ReferenceSearchResult, Score,
};

const SHORTER_MATE_FEN: &str = "7k/5Q2/6K1/8/8/8/8/8 w - - 0 1";
const SHORTER_MATE_DEPTH: u16 = 3;
const LONGER_SURVIVAL_FEN: &str = "4Q2k/8/4K3/8/8/8/8/8 b - - 0 1";
const LONGER_SURVIVAL_DEPTH: u16 = 6;

fn position(fen: &str) -> Position {
    Position::from_fen(fen).expect("terminal fixture FEN is valid")
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

fn search_pair(
    label: &str,
    root: &Position,
    root_history: &SearchHistory,
    depth: u16,
) -> (ReferenceSearchResult, AlphaBetaSearchResult) {
    let mut reference_position = root.clone();
    let reference_snapshot = reference_position.clone();
    let mut reference_history = root_history.clone();
    let reference_history_snapshot = reference_history.clone();
    let reference =
        reference_search_with_quiescence(&mut reference_position, &mut reference_history, depth)
            .expect("reference search succeeds");
    assert_restored(
        &format!("{label} reference"),
        &reference_position,
        &reference_snapshot,
        &reference_history,
        &reference_history_snapshot,
    );

    let mut alpha_beta_position = root.clone();
    let alpha_beta_snapshot = alpha_beta_position.clone();
    let mut alpha_beta_history = root_history.clone();
    let alpha_beta_history_snapshot = alpha_beta_history.clone();
    let alpha_beta = alpha_beta_search(&mut alpha_beta_position, &mut alpha_beta_history, depth)
        .expect("alpha-beta search succeeds");
    assert_restored(
        &format!("{label} alpha-beta"),
        &alpha_beta_position,
        &alpha_beta_snapshot,
        &alpha_beta_history,
        &alpha_beta_history_snapshot,
    );

    assert_eq!(alpha_beta.score(), reference.score(), "score: {label}");
    assert_eq!(
        alpha_beta.best_move(),
        reference.best_move(),
        "best move: {label}"
    );
    assert!(
        alpha_beta.nodes() <= reference.nodes(),
        "alpha-beta visited {} nodes versus reference {}: {label}",
        alpha_beta.nodes(),
        reference.nodes()
    );

    (reference, alpha_beta)
}

fn legal_move(position: &Position, text: &str) -> Move {
    let syntax = text.parse::<UciMove>().expect("fixture UCI is valid");
    let mut scratch = position.clone();
    scratch
        .legal_moves()
        .expect("fixture legal generation succeeds")
        .iter()
        .find(|candidate| syntax.matches(*candidate))
        .expect("fixture move is legal")
}

fn parent_score(child: Score) -> Score {
    if !child.is_mate() {
        return -child;
    }

    let raw = if child.centipawns() > 0 {
        -child.centipawns() + 1
    } else {
        -child.centipawns() - 1
    };
    Score::from_raw(raw).expect("one-ply mate normalization stays in range")
}

fn reference_move_score(
    label: &str,
    root: &Position,
    root_history: &SearchHistory,
    depth: u16,
    text: &str,
) -> Score {
    assert!(depth > 0);
    let expected_move = legal_move(root, text);
    let mut position = root.clone();
    let position_snapshot = position.clone();
    let mut history = root_history.clone();
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
    let child = reference_search_with_quiescence(&mut position, &mut history, depth - 1)
        .expect("reference child search succeeds");
    history
        .pop_position(history_undo)
        .expect("reference child history restores");
    position
        .unmake_move(position_undo)
        .expect("reference child position restores");
    assert_restored(
        &format!("{label} reference move {text}"),
        &position,
        &position_snapshot,
        &history,
        &history_snapshot,
    );
    parent_score(child.score())
}

fn alpha_beta_move_score(
    label: &str,
    root: &Position,
    root_history: &SearchHistory,
    depth: u16,
    text: &str,
) -> Score {
    assert!(depth > 0);
    let expected_move = legal_move(root, text);
    let mut position = root.clone();
    let position_snapshot = position.clone();
    let mut history = root_history.clone();
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
    let child = alpha_beta_search(&mut position, &mut history, depth - 1)
        .expect("alpha-beta child search succeeds");
    history
        .pop_position(history_undo)
        .expect("alpha-beta child history restores");
    position
        .unmake_move(position_undo)
        .expect("alpha-beta child position restores");
    assert_restored(
        &format!("{label} alpha-beta move {text}"),
        &position,
        &position_snapshot,
        &history,
        &history_snapshot,
    );
    parent_score(child.score())
}

fn assert_terminal_root(name: &str, fen: &str, expected: Score) {
    let root = position(fen);
    let history = SearchHistory::from_position(&root);
    let (reference, alpha_beta) = search_pair(name, &root, &history, 3);

    assert_eq!(reference.score(), expected, "score: {name}");
    assert_eq!(reference.best_move(), None, "best move: {name}");
    assert_eq!(alpha_beta.best_move(), None, "alpha best move: {name}");
    assert_eq!(reference.nodes(), 1, "reference nodes: {name}");
    assert_eq!(alpha_beta.nodes(), 1, "alpha-beta nodes: {name}");
}

#[test]
fn terminal_and_rule_draw_roots_have_exact_one_node_scores() {
    let mated = Score::mated_in(0).expect("root mate distance is supported");
    for (name, fen, expected) in [
        (
            "mated-root-checkmate-precedence",
            "7k/6Q1/6K1/8/8/8/8/8 b - - 150 1",
            mated,
        ),
        (
            "stalemate-root",
            "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1",
            Score::ZERO,
        ),
        (
            "dead-position-root",
            "7k/8/8/8/8/8/8/K7 w - - 0 1",
            Score::ZERO,
        ),
        (
            "claimable-fifty-move-root",
            "8/8/8/8/8/8/R3K3/7k w - - 100 1",
            Score::ZERO,
        ),
        (
            "automatic-seventy-five-move-root",
            "8/8/8/8/8/8/R3K3/7k w - - 150 1",
            Score::ZERO,
        ),
    ] {
        assert_terminal_root(name, fen, expected);
    }
}

#[test]
fn claimable_and_automatic_repetition_roots_score_as_one_node_draws() {
    for (cycles, expected_count, label) in [
        (2_usize, 3_usize, "claimable-threefold-root"),
        (4_usize, 5_usize, "automatic-fivefold-root"),
    ] {
        let mut game = Game::starting();
        for _ in 0..cycles {
            play_knight_cycle(&mut game);
        }
        assert_eq!(game.repetition_count(), expected_count, "{label}");

        let root = game.position().clone();
        let history = game.search_history();
        let (reference, alpha_beta) = search_pair(label, &root, &history, 3);
        assert_eq!(reference.score(), Score::ZERO, "{label}");
        assert_eq!(reference.best_move(), None, "{label}");
        assert_eq!(alpha_beta.best_move(), None, "{label}");
        assert_eq!(reference.nodes(), 1, "{label}");
        assert_eq!(alpha_beta.nodes(), 1, "{label}");
    }
}

#[test]
fn shorter_forced_mate_outranks_slower_forced_mate() {
    let root = position(SHORTER_MATE_FEN);
    let history = SearchHistory::from_position(&root);
    let expected_fast = Score::mate_in(1).expect("mate in one is supported");
    let expected_slow = Score::mate_in(3).expect("mate in three is supported");

    let fast_reference =
        reference_move_score("shorter-mate", &root, &history, SHORTER_MATE_DEPTH, "f7e8");
    let fast_alpha_beta =
        alpha_beta_move_score("shorter-mate", &root, &history, SHORTER_MATE_DEPTH, "f7e8");
    let slow_reference =
        reference_move_score("shorter-mate", &root, &history, SHORTER_MATE_DEPTH, "f7a7");
    let slow_alpha_beta =
        alpha_beta_move_score("shorter-mate", &root, &history, SHORTER_MATE_DEPTH, "f7a7");

    assert_eq!(fast_reference, expected_fast);
    assert_eq!(fast_alpha_beta, expected_fast);
    assert_eq!(slow_reference, expected_slow);
    assert_eq!(slow_alpha_beta, expected_slow);
    assert!(expected_fast > expected_slow);

    let (reference, alpha_beta) =
        search_pair("shorter-mate-root", &root, &history, SHORTER_MATE_DEPTH);
    assert_eq!(reference.score(), expected_fast);
    let selected = reference.best_move().expect("winning root has a best move");
    assert!(
        ["f7e8", "f7f8", "f7g7", "f7h7"].contains(&selected.to_uci().as_str()),
        "selected move must deliver immediate mate: {}",
        selected.to_uci()
    );
    assert_eq!(alpha_beta.best_move(), Some(selected));
    assert_eq!(
        reference_move_score(
            "selected-shorter-mate",
            &root,
            &history,
            SHORTER_MATE_DEPTH,
            &selected.to_uci(),
        ),
        expected_fast
    );
}

#[test]
fn forced_loss_selects_the_line_that_delays_mate_longest() {
    let root = position(LONGER_SURVIVAL_FEN);
    let history = SearchHistory::from_position(&root);
    let expected_longer = Score::mated_in(6).expect("mated in six is supported");
    let expected_shorter = Score::mated_in(4).expect("mated in four is supported");

    let longer_reference = reference_move_score(
        "longer-survival",
        &root,
        &history,
        LONGER_SURVIVAL_DEPTH,
        "h8g7",
    );
    let longer_alpha_beta = alpha_beta_move_score(
        "longer-survival",
        &root,
        &history,
        LONGER_SURVIVAL_DEPTH,
        "h8g7",
    );
    let shorter_reference = reference_move_score(
        "longer-survival",
        &root,
        &history,
        LONGER_SURVIVAL_DEPTH,
        "h8h7",
    );
    let shorter_alpha_beta = alpha_beta_move_score(
        "longer-survival",
        &root,
        &history,
        LONGER_SURVIVAL_DEPTH,
        "h8h7",
    );

    assert_eq!(longer_reference, expected_longer);
    assert_eq!(longer_alpha_beta, expected_longer);
    assert_eq!(shorter_reference, expected_shorter);
    assert_eq!(shorter_alpha_beta, expected_shorter);
    assert!(expected_longer > expected_shorter);

    let (reference, alpha_beta) = search_pair(
        "longer-survival-root",
        &root,
        &history,
        LONGER_SURVIVAL_DEPTH,
    );
    let expected_move = legal_move(&root, "h8g7");
    assert_eq!(reference.score(), expected_longer);
    assert_eq!(reference.best_move(), Some(expected_move));
    assert_eq!(alpha_beta.best_move(), Some(expected_move));
}
