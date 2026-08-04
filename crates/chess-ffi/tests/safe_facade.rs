use std::{sync::mpsc, thread, time::Duration};

use chess_book::{IndexedBook, IndexedBookRecord};
use chess_core::{Color, GameStatus, Move, Position};
use chess_ffi::{
    Engine, EngineConfig, EngineError, SearchCancellationHandle, SearchLimitTermination,
    SearchRequest, ENGINE_VERSION,
};
use chess_search::{
    EvaluationWeightSet, IterativeDeepeningSearchError, SearchLimitError,
    TranspositionTableAllocationError,
};

const STARTING_FEN: &str = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
const MATE_FEN: &str = "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1";

fn small_engine() -> Engine {
    Engine::new(EngineConfig::new().with_transposition_table_mebibytes(1))
        .expect("one-MiB engine allocation succeeds")
}

fn starting_book_bytes() -> Vec<u8> {
    let position = Position::starting();
    let record = IndexedBookRecord::new(
        &position,
        "e2e4".parse().expect("test move syntax is valid"),
        100,
    )
    .expect("starting record is valid");
    IndexedBook::from_records(vec![record])
        .expect("test book is valid")
        .to_bytes()
}

fn assert_send<T: Send>() {}
fn assert_send_sync<T: Send + Sync>() {}

#[test]
fn construction_configuration_and_identities_are_exact() {
    assert_send::<Engine>();
    assert_send_sync::<SearchCancellationHandle>();

    let config = EngineConfig::new().with_transposition_table_mebibytes(1);
    let engine = Engine::new(config).expect("configured engine constructs");
    let expected_weights = EvaluationWeightSet::baseline();
    let identity = engine.weight_identity();

    assert_eq!(engine.config(), config);
    assert_eq!(Engine::version(), ENGINE_VERSION);
    assert_eq!(identity.schema_version(), expected_weights.schema_version);
    assert_eq!(identity.identifier(), expected_weights.identifier);
    assert_eq!(identity.checksum(), expected_weights.checksum);
    assert_eq!(engine.fen(), STARTING_FEN);
}

#[test]
fn invalid_table_configuration_is_typed() {
    assert!(matches!(
        Engine::new(EngineConfig::new().with_transposition_table_mebibytes(0)),
        Err(EngineError::TranspositionTableAllocation(
            TranspositionTableAllocationError::ZeroMebibytes
        ))
    ));
}

#[test]
fn position_replacement_is_canonical_transactional_and_resettable() {
    let mut engine = small_engine();
    engine.play_move("e2e4").expect("opening move is legal");
    let played_fen = engine.fen();

    assert!(matches!(
        engine.set_position("not a fen"),
        Err(EngineError::InvalidFen(_))
    ));
    assert_eq!(engine.fen(), played_fen);

    engine.set_position(MATE_FEN).expect("mate FEN is valid");
    assert_eq!(engine.fen(), MATE_FEN);
    assert_eq!(
        engine.game_status(),
        Ok(GameStatus::Checkmate {
            winner: Color::White
        })
    );

    engine.reset_position();
    assert_eq!(engine.fen(), STARTING_FEN);
    assert_eq!(engine.game_status(), Ok(GameStatus::Ongoing));
}

#[test]
fn legal_moves_and_play_move_use_canonical_uci_and_reject_without_mutation() {
    let mut engine = small_engine();
    let legal = engine.legal_moves().expect("starting legal moves generate");

    assert_eq!(legal.len(), 20);
    assert!(legal.contains(&"e2e4".to_owned()));
    assert!(legal.contains(&"g1f3".to_owned()));

    let before = engine.fen();
    assert!(matches!(
        engine.play_move("e2e9"),
        Err(EngineError::InvalidMoveSyntax(_))
    ));
    assert_eq!(engine.fen(), before);

    assert_eq!(
        engine.play_move("e2e5"),
        Err(EngineError::IllegalMove {
            value: "e2e5".to_owned()
        })
    );
    assert_eq!(engine.fen(), before);

    engine.play_move("e2e4").expect("e2e4 is legal");
    assert_eq!(
        engine.fen(),
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    );
}

#[test]
fn terminal_game_rejects_further_moves_explicitly() {
    let mut engine = small_engine();
    engine.set_position(MATE_FEN).expect("mate FEN is valid");

    assert!(matches!(
        engine.play_move("h8h7"),
        Err(EngineError::Game(chess_core::GameError::GameOver {
            status: GameStatus::Checkmate {
                winner: Color::White
            }
        }))
    ));
    assert_eq!(engine.fen(), MATE_FEN);
}

#[test]
fn fixed_depth_search_returns_a_legal_move_without_mutating_played_state() {
    let mut engine = small_engine();
    engine.play_move("e2e4").expect("root move is legal");
    engine.play_move("e7e5").expect("reply is legal");
    let before = engine.fen();
    let legal = engine.legal_moves().expect("root legal moves generate");

    let result = engine
        .search(SearchRequest::new().with_depth(2))
        .expect("fixed-depth facade search succeeds");
    let best_move = result
        .best_move()
        .map(Move::to_uci)
        .expect("nonterminal root has a best move");

    assert!(legal.contains(&best_move));
    assert_eq!(result.completed_depth(), 2);
    assert_eq!(
        result.termination(),
        SearchLimitTermination::Depth { depth: 2 }
    );
    assert_eq!(engine.fen(), before);
}

#[test]
fn invalid_search_request_is_typed_and_non_mutating() {
    let mut engine = small_engine();
    let before = engine.fen();

    assert!(matches!(
        engine.search(SearchRequest::new()),
        Err(EngineError::Search(
            IterativeDeepeningSearchError::InvalidLimits(SearchLimitError::NoAutomaticLimit)
        ))
    ));
    assert_eq!(engine.fen(), before);
}

#[test]
fn preset_cancellation_returns_deterministic_legal_fallback() {
    let mut engine = small_engine();
    let legal = engine.legal_moves().expect("starting legal moves generate");
    let cancellation = SearchCancellationHandle::new();
    cancellation.cancel();

    let result = engine
        .search(
            SearchRequest::new()
                .with_depth(8)
                .with_cancellation(&cancellation),
        )
        .expect("preset cancellation is a successful stopped search");
    let fallback = result
        .best_move()
        .map(Move::to_uci)
        .expect("starting root has deterministic fallback");

    assert_eq!(result.completed_depth(), 0);
    assert_eq!(result.termination(), SearchLimitTermination::ExplicitStop);
    assert!(legal.contains(&fallback));
    assert!(cancellation.is_cancelled());

    cancellation.reset();
    assert!(!cancellation.is_cancelled());
}

#[test]
fn cancellation_handle_stops_infinite_search_from_another_thread() {
    let mut engine = small_engine();
    let cancellation = SearchCancellationHandle::new();
    let request = SearchRequest::infinite(&cancellation);
    let (sender, receiver) = mpsc::channel();

    let worker = thread::spawn(move || {
        sender
            .send(engine.search(request))
            .expect("test receiver remains connected");
    });

    thread::sleep(Duration::from_millis(20));
    cancellation.cancel();
    let result = receiver
        .recv_timeout(Duration::from_secs(5))
        .expect("infinite search stops within the facade deadline")
        .expect("cancelled infinite search returns a result");
    worker.join().expect("search worker does not panic");

    assert_eq!(result.termination(), SearchLimitTermination::ExplicitStop);
    assert!(result.best_move().is_some());
}

#[test]
fn opening_book_configuration_is_explicit_and_absence_is_normal() {
    let enabled = EngineConfig::new()
        .with_transposition_table_mebibytes(1)
        .with_opening_book_enabled(true);
    let mut without_data = Engine::new(enabled).expect("engine without book constructs");
    assert_eq!(without_data.opening_book_move(), Ok(None));
    let result = without_data
        .search(SearchRequest::new().with_depth(1))
        .expect("normal search remains available without a book");
    assert!(result.best_move().is_some());

    let bytes = starting_book_bytes();
    let mut disabled =
        Engine::new_with_indexed_book_bytes(enabled.with_opening_book_enabled(false), &bytes)
            .expect("valid disabled book constructs");
    assert_eq!(disabled.opening_book_move(), Ok(None));
}

#[test]
fn injected_indexed_book_returns_legal_move_and_no_entry_falls_through() {
    let bytes = starting_book_bytes();
    let config = EngineConfig::new()
        .with_transposition_table_mebibytes(1)
        .with_opening_book_enabled(true);
    let mut engine =
        Engine::new_with_indexed_book_bytes(config, &bytes).expect("valid indexed book constructs");
    assert_eq!(engine.opening_book_move(), Ok(Some("e2e4".to_owned())));
    engine.play_move("e2e4").expect("book move is legal");
    assert_eq!(engine.opening_book_move(), Ok(None));
}

#[test]
fn corrupt_explicit_book_is_rejected_before_engine_construction() {
    let config = EngineConfig::new().with_opening_book_enabled(true);
    assert!(matches!(
        Engine::new_with_indexed_book_bytes(config, b"not a book"),
        Err(EngineError::InvalidOpeningBook(_))
    ));
}
