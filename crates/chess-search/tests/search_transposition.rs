use chess_core::{Move, MoveKind, Position, SearchHistory, Square};
use chess_search::{
    alpha_beta_search, alpha_beta_search_with_transposition_table, Score, TranspositionBound,
    TranspositionEntry, TranspositionScore, TranspositionTable,
    DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES,
};

fn square(text: &str) -> Square {
    text.parse()
        .expect("transposition integration square is valid")
}

fn e2e4() -> Move {
    Move::new(square("e2"), square("e4"), MoveKind::DoublePawnPush)
}

#[test]
fn warm_table_exact_root_hit_reduces_nodes_and_preserves_result() {
    assert_eq!(DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES, 1);
    let mut position = Position::starting();
    let position_snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let mut table = TranspositionTable::new(1).expect("integration table allocates");
    let capacity = table.entry_capacity();
    let allocated = table.allocated_bytes();

    let cold =
        alpha_beta_search_with_transposition_table(&mut position, &mut history, 3, &mut table)
            .expect("cold TT search succeeds");
    let cold_diagnostics = table.diagnostics();
    assert!(cold.nodes() > 1);
    assert!(cold_diagnostics.stores() > 0);
    assert_eq!(position, position_snapshot);
    assert_eq!(history, history_snapshot);

    let warm =
        alpha_beta_search_with_transposition_table(&mut position, &mut history, 3, &mut table)
            .expect("warm TT search succeeds");
    let warm_diagnostics = table.diagnostics();

    assert_eq!(warm.score(), cold.score());
    assert_eq!(warm.best_move(), cold.best_move());
    assert_eq!(warm.nodes(), 1);
    assert!(warm.nodes() < cold.nodes());
    assert_eq!(warm_diagnostics.probes(), 1);
    assert_eq!(warm_diagnostics.hits(), 1);
    assert_eq!(warm_diagnostics.exact_hits(), 1);
    assert_eq!(table.entry_capacity(), capacity);
    assert_eq!(table.allocated_bytes(), allocated);
    assert_eq!(position, position_snapshot);
    assert_eq!(history, history_snapshot);
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
}

#[test]
fn reversible_history_suppresses_cached_root_score_and_hint() {
    let fen = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 1 1";
    let mut baseline_position: Position = fen.parse().expect("baseline FEN is valid");
    let mut baseline_history = SearchHistory::from_position(&baseline_position);
    let baseline = alpha_beta_search(&mut baseline_position, &mut baseline_history, 1)
        .expect("baseline search succeeds");

    let mut position: Position = fen.parse().expect("TT FEN is valid");
    let snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let mut table = TranspositionTable::new(1).expect("integration table allocates");
    let bogus = Score::from_evaluation(1_234);
    table.store(TranspositionEntry::new(
        position.zobrist(),
        8,
        TranspositionBound::Exact,
        TranspositionScore::normalize(bogus, 0).expect("bogus fixture score normalizes"),
        Some(e2e4()),
        table.generation(),
    ));

    let result =
        alpha_beta_search_with_transposition_table(&mut position, &mut history, 1, &mut table)
            .expect("history-sensitive TT search succeeds");
    let diagnostics = table.diagnostics();

    assert_ne!(result.score(), bogus);
    assert_eq!(result.score(), baseline.score());
    assert_eq!(result.best_move(), baseline.best_move());
    assert_eq!(result.nodes(), baseline.nodes());
    assert_eq!(diagnostics.probes(), 1);
    assert_eq!(diagnostics.hits(), 1);
    assert_eq!(diagnostics.exact_hits(), 0);
    assert_eq!(diagnostics.stores(), 0);
    assert_eq!(position, snapshot);
    assert_eq!(history, history_snapshot);
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
}

#[test]
fn illegal_exact_root_move_does_not_bypass_legal_search() {
    let mut position = Position::starting();
    let snapshot = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let history_snapshot = history.clone();
    let mut table = TranspositionTable::new(1).expect("integration table allocates");
    let bogus = Score::from_evaluation(2_345);
    let illegal = Move::new(square("a1"), square("a8"), MoveKind::Quiet);
    table.store(TranspositionEntry::new(
        position.zobrist(),
        8,
        TranspositionBound::Exact,
        TranspositionScore::normalize(bogus, 0).expect("bogus fixture score normalizes"),
        Some(illegal),
        table.generation(),
    ));

    let result =
        alpha_beta_search_with_transposition_table(&mut position, &mut history, 1, &mut table)
            .expect("invalid-root-hint search succeeds");

    assert_ne!(result.score(), bogus);
    assert_ne!(result.best_move(), Some(illegal));
    assert!(result.best_move().is_some_and(|current| {
        position
            .legal_moves()
            .expect("root legal moves generate")
            .iter()
            .any(|candidate| candidate == current)
    }));
    assert_eq!(position, snapshot);
    assert_eq!(history, history_snapshot);
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
}
