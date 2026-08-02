use chess_core::{Game, Move, Position, SearchHistory, UciMove};
use chess_search::{alpha_beta_search, reference_search, Score};

#[derive(Clone, Copy)]
struct Fixture {
    name: &'static str,
    fen: &'static str,
    depth: u16,
}

const CURATED_FIXTURES: &[Fixture] = &[
    Fixture {
        name: "quiet-starting-position",
        fen: "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        depth: 3,
    },
    Fixture {
        name: "tactical-hanging-rook",
        fen: "3r3k/8/8/8/8/8/8/K2Q4 w - - 0 1",
        depth: 2,
    },
    Fixture {
        name: "mate-in-one-adjacent",
        fen: "7k/5Q2/6K1/8/8/8/8/8 w - - 0 1",
        depth: 2,
    },
    Fixture {
        name: "mated-root",
        fen: "7k/6Q1/6K1/8/8/8/8/8 b - - 150 1",
        depth: 3,
    },
    Fixture {
        name: "stalemate-root",
        fen: "7k/5Q2/6K1/8/8/8/8/8 b - - 0 1",
        depth: 3,
    },
    Fixture {
        name: "claimable-fifty-move-root",
        fen: "8/8/8/8/8/8/R3K3/7k w - - 100 1",
        depth: 3,
    },
];

fn position(fen: &str) -> Position {
    fen.parse().expect("equivalence fixture FEN is valid")
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

fn assert_root_restored(
    name: &str,
    position: &Position,
    position_snapshot: &Position,
    history: &SearchHistory,
    history_snapshot: &SearchHistory,
) {
    assert_eq!(position, position_snapshot, "position changed: {name}");
    assert_eq!(history, history_snapshot, "history changed: {name}");
    assert_eq!(
        position.zobrist(),
        position.recomputed_zobrist(),
        "incremental hash diverged: {name}"
    );
}

fn reference_root_scores(
    position: &mut Position,
    history: &mut SearchHistory,
    depth: u16,
) -> Vec<(Move, Score)> {
    assert!(depth > 0, "root move scoring requires positive depth");
    let position_snapshot = position.clone();
    let history_snapshot = history.clone();
    let tokens = position
        .legal_move_tokens()
        .expect("root legal tokens generate");
    let mut scores = Vec::with_capacity(tokens.len());

    for token in tokens.iter() {
        let current = token.move_made();
        let position_undo = position
            .make_legal_token(token)
            .expect("root token applies");
        let history_undo = history.push_position(position);
        let child = reference_search(position, history, depth - 1);
        let history_restore = history.pop_position(history_undo);
        let position_restore = position.unmake_move(position_undo);

        history_restore.expect("root-score history restores");
        position_restore.expect("root-score position restores");
        let child = child.expect("root child reference search succeeds");
        scores.push((current, -child.score()));
    }

    assert_root_restored(
        "reference-root-score-oracle",
        position,
        &position_snapshot,
        history,
        &history_snapshot,
    );
    scores
}

#[test]
fn curated_shallow_scores_match_and_alpha_beta_never_visits_more_nodes() {
    let mut observed_strict_pruning = false;

    for fixture in CURATED_FIXTURES {
        let root = position(fixture.fen);

        let mut reference_position = root.clone();
        let reference_snapshot = reference_position.clone();
        let mut reference_history = SearchHistory::from_position(&reference_position);
        let reference_history_snapshot = reference_history.clone();
        let reference = reference_search(
            &mut reference_position,
            &mut reference_history,
            fixture.depth,
        )
        .expect("reference search succeeds");
        assert_root_restored(
            fixture.name,
            &reference_position,
            &reference_snapshot,
            &reference_history,
            &reference_history_snapshot,
        );

        let mut alpha_beta_position = root;
        let alpha_beta_snapshot = alpha_beta_position.clone();
        let mut alpha_beta_history = SearchHistory::from_position(&alpha_beta_position);
        let alpha_beta_history_snapshot = alpha_beta_history.clone();
        let alpha_beta = alpha_beta_search(
            &mut alpha_beta_position,
            &mut alpha_beta_history,
            fixture.depth,
        )
        .expect("alpha-beta search succeeds");
        assert_root_restored(
            fixture.name,
            &alpha_beta_position,
            &alpha_beta_snapshot,
            &alpha_beta_history,
            &alpha_beta_history_snapshot,
        );

        assert_eq!(
            alpha_beta.score(),
            reference.score(),
            "score mismatch: {}",
            fixture.name
        );
        assert!(
            alpha_beta.nodes() <= reference.nodes(),
            "alpha-beta visited {} nodes versus reference {}: {}",
            alpha_beta.nodes(),
            reference.nodes(),
            fixture.name
        );
        observed_strict_pruning |= alpha_beta.nodes() < reference.nodes();
    }

    assert!(
        observed_strict_pruning,
        "the curated fixture set must demonstrate at least one real cutoff"
    );
}

#[test]
fn uniquely_best_tactical_move_matches_the_independent_root_score_oracle() {
    let mut oracle_position = position("3r3k/8/8/8/8/8/8/K2Q4 w - - 0 1");
    let mut oracle_history = SearchHistory::from_position(&oracle_position);
    let root_scores = reference_root_scores(&mut oracle_position, &mut oracle_history, 1);
    let best_score = root_scores
        .iter()
        .map(|(_, score)| *score)
        .max()
        .expect("non-terminal root has legal moves");
    let best_moves: Vec<Move> = root_scores
        .iter()
        .filter_map(|(current, score)| (*score == best_score).then_some(*current))
        .collect();

    assert_eq!(best_moves.len(), 1, "fixture must have one exact best move");
    let expected = best_moves[0];
    assert_eq!(expected.to_uci(), "d1d8");

    let mut reference_position = oracle_position.clone();
    let mut reference_history = SearchHistory::from_position(&reference_position);
    let reference = reference_search(&mut reference_position, &mut reference_history, 1)
        .expect("reference search succeeds");

    let mut alpha_beta_position = oracle_position;
    let mut alpha_beta_history = SearchHistory::from_position(&alpha_beta_position);
    let alpha_beta = alpha_beta_search(&mut alpha_beta_position, &mut alpha_beta_history, 1)
        .expect("alpha-beta search succeeds");

    assert_eq!(reference.score(), best_score);
    assert_eq!(alpha_beta.score(), best_score);
    assert_eq!(reference.best_move(), Some(expected));
    assert_eq!(alpha_beta.best_move(), Some(expected));
    assert!(alpha_beta.nodes() <= reference.nodes());
}

#[test]
fn repetition_aware_searches_are_equivalent_and_restore_game_history() {
    let mut game = Game::starting();
    play_knight_cycle(&mut game);
    play_knight_cycle(&mut game);
    assert_eq!(game.repetition_count(), 3);

    let root = game.position().clone();
    let root_history = game.search_history();

    let mut reference_position = root.clone();
    let reference_snapshot = reference_position.clone();
    let mut reference_history = root_history.clone();
    let reference_history_snapshot = reference_history.clone();
    let reference = reference_search(&mut reference_position, &mut reference_history, 3)
        .expect("reference repetition search succeeds");
    assert_root_restored(
        "repetition-reference",
        &reference_position,
        &reference_snapshot,
        &reference_history,
        &reference_history_snapshot,
    );

    let mut alpha_beta_position = root;
    let alpha_beta_snapshot = alpha_beta_position.clone();
    let mut alpha_beta_history = root_history;
    let alpha_beta_history_snapshot = alpha_beta_history.clone();
    let alpha_beta = alpha_beta_search(&mut alpha_beta_position, &mut alpha_beta_history, 3)
        .expect("alpha-beta repetition search succeeds");
    assert_root_restored(
        "repetition-alpha-beta",
        &alpha_beta_position,
        &alpha_beta_snapshot,
        &alpha_beta_history,
        &alpha_beta_history_snapshot,
    );

    assert_eq!(reference.score(), Score::ZERO);
    assert_eq!(alpha_beta.score(), reference.score());
    assert_eq!(reference.best_move(), None);
    assert_eq!(alpha_beta.best_move(), None);
    assert_eq!(reference.nodes(), 1);
    assert_eq!(alpha_beta.nodes(), 1);
}
