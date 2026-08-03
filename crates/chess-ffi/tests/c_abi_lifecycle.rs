use std::{
    collections::HashSet,
    ptr, slice, str,
    sync::mpsc,
    thread,
    time::Duration,
};

use chess_ffi::c_abi::*;

const STARTING_FEN: &str = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";

fn create_engine() -> ChessEngineHandle {
    let mut config = ChessEngineConfig::new();
    config.transposition_table_mebibytes = 1;
    let mut handle = CHESS_ENGINE_NULL_HANDLE;
    // SAFETY: Both pointers reference initialized records with valid lifetimes.
    let code = unsafe { chess_engine_create(&config, &mut handle) };
    assert_eq!(code, ChessEngineResultCode::Ok);
    assert_ne!(handle, CHESS_ENGINE_NULL_HANDLE);
    handle
}

fn create_cancellation() -> ChessEngineCancellationHandle {
    let mut handle = CHESS_ENGINE_NULL_CANCELLATION_HANDLE;
    // SAFETY: `handle` points to one writable cancellation token.
    let code = unsafe { chess_engine_cancellation_create(&mut handle) };
    assert_eq!(code, ChessEngineResultCode::Ok);
    assert_ne!(handle, CHESS_ENGINE_NULL_CANCELLATION_HANDLE);
    handle
}

fn buffer_bytes(buffer: &ChessEngineBuffer) -> Vec<u8> {
    if buffer.len == 0 {
        assert!(buffer.data.is_null());
        return Vec::new();
    }
    assert!(!buffer.data.is_null());
    // SAFETY: A live ABI buffer guarantees exactly `len` readable bytes.
    unsafe { slice::from_raw_parts(buffer.data, buffer.len).to_vec() }
}

fn buffer_text(buffer: &ChessEngineBuffer) -> String {
    str::from_utf8(&buffer_bytes(buffer))
        .expect("ABI text output is valid UTF-8")
        .to_owned()
}

fn free_buffer(buffer: &mut ChessEngineBuffer) {
    // SAFETY: The record is empty or an unchanged live ABI allocation.
    assert_eq!(
        unsafe { chess_engine_buffer_free(buffer) },
        ChessEngineResultCode::Ok
    );
}

fn get_fen(handle: ChessEngineHandle) -> String {
    let mut buffer = ChessEngineBuffer::empty();
    // SAFETY: `buffer` is a fresh writable output record.
    assert_eq!(
        unsafe { chess_engine_get_fen(handle, &mut buffer) },
        ChessEngineResultCode::Ok
    );
    let fen = buffer_text(&buffer);
    free_buffer(&mut buffer);
    fen
}

fn last_error_text() -> String {
    let mut buffer = ChessEngineBuffer::empty();
    // SAFETY: `buffer` is a fresh writable output record.
    assert_eq!(
        unsafe { chess_engine_last_error_message(&mut buffer) },
        ChessEngineResultCode::Ok
    );
    let message = buffer_text(&buffer);
    free_buffer(&mut buffer);
    message
}

#[test]
fn rust_through_abi_smoke_covers_complete_lifecycle() {
    let engine = create_engine();

    // SAFETY: The FEN byte range is readable for its explicit length.
    assert_eq!(
        unsafe {
            chess_engine_set_position(engine, STARTING_FEN.as_ptr(), STARTING_FEN.len())
        },
        ChessEngineResultCode::Ok
    );

    let mut legal_moves = ChessEngineBuffer::empty();
    // SAFETY: `legal_moves` is a fresh writable output record.
    assert_eq!(
        unsafe { chess_engine_get_legal_moves(engine, &mut legal_moves) },
        ChessEngineResultCode::Ok
    );
    let starting_moves = buffer_text(&legal_moves);
    assert_eq!(starting_moves.lines().count(), 20);
    assert!(starting_moves.lines().any(|current| current == "e2e4"));
    free_buffer(&mut legal_moves);

    let opening = b"e2e4";
    // SAFETY: The move byte range is readable for its explicit length.
    assert_eq!(
        unsafe { chess_engine_play_move(engine, opening.as_ptr(), opening.len()) },
        ChessEngineResultCode::Ok
    );

    let mut status = ChessEngineGameStatus::new();
    // SAFETY: `status` is writable for one complete record.
    assert_eq!(
        unsafe { chess_engine_get_game_status(engine, &mut status) },
        ChessEngineResultCode::Ok
    );
    assert_eq!(status.kind, ChessEngineGameStatusKind::Ongoing);

    let mut reply_buffer = ChessEngineBuffer::empty();
    // SAFETY: `reply_buffer` is a fresh writable output record.
    assert_eq!(
        unsafe { chess_engine_get_legal_moves(engine, &mut reply_buffer) },
        ChessEngineResultCode::Ok
    );
    let legal_replies = buffer_text(&reply_buffer)
        .lines()
        .map(str::to_owned)
        .collect::<HashSet<_>>();
    free_buffer(&mut reply_buffer);

    let mut request = ChessEngineSearchRequest::new();
    request.flags = CHESS_ENGINE_SEARCH_FLAG_DEPTH;
    request.depth = 2;
    let mut result = ChessEngineSearchResult::new();
    // SAFETY: Request and result pointers reference complete live records.
    assert_eq!(
        unsafe { chess_engine_search(engine, &request, &mut result) },
        ChessEngineResultCode::Ok
    );
    assert_eq!(result.completed_depth, 2);
    assert_eq!(
        result.termination_kind,
        ChessEngineSearchTerminationKind::Depth
    );
    assert_eq!(result.termination_value, 2);
    let best_move = buffer_text(&result.best_move);
    assert!(legal_replies.contains(&best_move));
    assert!(!buffer_text(&result.principal_variation).is_empty());
    // SAFETY: `result` is an unchanged live ABI search result.
    assert_eq!(
        unsafe { chess_engine_search_result_free(&mut result) },
        ChessEngineResultCode::Ok
    );

    assert_eq!(
        chess_engine_reset_position(engine),
        ChessEngineResultCode::Ok
    );
    assert_eq!(get_fen(engine), STARTING_FEN);
    assert_eq!(chess_engine_destroy(engine), ChessEngineResultCode::Ok);
}

#[test]
fn repeated_create_destroy_is_unique_and_stale_safe() {
    let mut engine_tokens = HashSet::new();
    for _ in 0..128 {
        let handle = create_engine();
        assert!(engine_tokens.insert(handle));
        assert_eq!(get_fen(handle), STARTING_FEN);
        assert_eq!(chess_engine_destroy(handle), ChessEngineResultCode::Ok);

        let mut stale_output = ChessEngineBuffer::empty();
        // SAFETY: The output record is writable; the engine token is intentionally stale.
        assert_eq!(
            unsafe { chess_engine_get_fen(handle, &mut stale_output) },
            ChessEngineResultCode::InvalidHandle
        );
        assert_eq!(stale_output, ChessEngineBuffer::empty());
        assert_eq!(
            chess_engine_destroy(handle),
            ChessEngineResultCode::InvalidHandle
        );
    }

    let mut cancellation_tokens = HashSet::new();
    for _ in 0..128 {
        let handle = create_cancellation();
        assert!(cancellation_tokens.insert(handle));
        assert_eq!(
            chess_engine_cancellation_destroy(handle),
            ChessEngineResultCode::Ok
        );
        assert_eq!(
            chess_engine_cancellation_cancel(handle),
            ChessEngineResultCode::InvalidHandle
        );
        assert_eq!(
            chess_engine_cancellation_destroy(handle),
            ChessEngineResultCode::InvalidHandle
        );
    }
}

#[test]
fn invalid_inputs_fail_loudly_without_mutation() {
    let engine = create_engine();
    let before = get_fen(engine);

    // SAFETY: A null input pointer with a nonzero length is intentional validation input.
    assert_eq!(
        unsafe { chess_engine_set_position(engine, ptr::null(), 1) },
        ChessEngineResultCode::NullPointer
    );
    assert!(last_error_text().contains("FEN input is null"));

    let invalid_utf8 = [0xff_u8];
    // SAFETY: The byte range is readable but intentionally invalid UTF-8.
    assert_eq!(
        unsafe {
            chess_engine_set_position(engine, invalid_utf8.as_ptr(), invalid_utf8.len())
        },
        ChessEngineResultCode::InvalidUtf8
    );

    let malformed_fen = b"not a fen";
    // SAFETY: The byte range is readable for its explicit length.
    assert_eq!(
        unsafe {
            chess_engine_set_position(engine, malformed_fen.as_ptr(), malformed_fen.len())
        },
        ChessEngineResultCode::InvalidFen
    );

    let malformed_move = b"e2e9";
    // SAFETY: The byte range is readable for its explicit length.
    assert_eq!(
        unsafe {
            chess_engine_play_move(engine, malformed_move.as_ptr(), malformed_move.len())
        },
        ChessEngineResultCode::InvalidMoveSyntax
    );

    let illegal_move = b"e2e5";
    // SAFETY: The byte range is readable for its explicit length.
    assert_eq!(
        unsafe { chess_engine_play_move(engine, illegal_move.as_ptr(), illegal_move.len()) },
        ChessEngineResultCode::IllegalMove
    );

    let mut request = ChessEngineSearchRequest::new();
    request.flags = 1 << 31;
    let mut result = ChessEngineSearchResult::new();
    // SAFETY: Request and result pointers reference complete records.
    assert_eq!(
        unsafe { chess_engine_search(engine, &request, &mut result) },
        ChessEngineResultCode::InvalidArgument
    );
    assert_eq!(result, ChessEngineSearchResult::new());
    assert!(last_error_text().contains("unknown flag bits"));

    request = ChessEngineSearchRequest::new();
    request.struct_size = 0;
    // SAFETY: Request and result pointers reference complete records.
    assert_eq!(
        unsafe { chess_engine_search(engine, &request, &mut result) },
        ChessEngineResultCode::AbiMismatch
    );
    assert_eq!(result, ChessEngineSearchResult::new());

    // SAFETY: A null output pointer is intentional validation input.
    assert_eq!(
        unsafe { chess_engine_get_fen(engine, ptr::null_mut()) },
        ChessEngineResultCode::NullPointer
    );
    assert!(last_error_text().contains("output FEN buffer is null"));

    assert_eq!(get_fen(engine), before);
    assert_eq!(chess_engine_destroy(engine), ChessEngineResultCode::Ok);
}

#[derive(Debug)]
struct SearchSnapshot {
    code: ChessEngineResultCode,
    free_code: ChessEngineResultCode,
    termination_kind: ChessEngineSearchTerminationKind,
    best_move: String,
    completed_depth: u16,
    selective_depth: u16,
    nodes: u64,
}

#[test]
fn active_infinite_search_cancels_from_another_thread() {
    let engine = create_engine();
    let cancellation = create_cancellation();

    let mut legal_buffer = ChessEngineBuffer::empty();
    // SAFETY: `legal_buffer` is a fresh writable output record.
    assert_eq!(
        unsafe { chess_engine_get_legal_moves(engine, &mut legal_buffer) },
        ChessEngineResultCode::Ok
    );
    let legal_moves = buffer_text(&legal_buffer)
        .lines()
        .map(str::to_owned)
        .collect::<HashSet<_>>();
    free_buffer(&mut legal_buffer);

    let (started_sender, started_receiver) = mpsc::sync_channel(0);
    let (result_sender, result_receiver) = mpsc::channel();
    let worker = thread::spawn(move || {
        let mut request = ChessEngineSearchRequest::new();
        request.flags = CHESS_ENGINE_SEARCH_FLAG_INFINITE
            | CHESS_ENGINE_SEARCH_FLAG_CANCELLATION;
        request.cancellation_handle = cancellation;
        let mut result = ChessEngineSearchResult::new();
        started_sender
            .send(())
            .expect("cancellation test receiver remains connected");

        // SAFETY: Request and result pointers reference complete records for the call.
        let code = unsafe { chess_engine_search(engine, &request, &mut result) };
        let snapshot = SearchSnapshot {
            code,
            termination_kind: result.termination_kind,
            best_move: buffer_text(&result.best_move),
            completed_depth: result.completed_depth,
            selective_depth: result.selective_depth,
            nodes: result.nodes,
            // SAFETY: `result` is initialized and remains unchanged after search.
            free_code: unsafe { chess_engine_search_result_free(&mut result) },
        };
        result_sender
            .send(snapshot)
            .expect("search result receiver remains connected");
    });

    started_receiver
        .recv_timeout(Duration::from_secs(1))
        .expect("search worker reaches the ABI call boundary");
    thread::sleep(Duration::from_millis(20));
    assert_eq!(
        chess_engine_cancellation_cancel(cancellation),
        ChessEngineResultCode::Ok
    );
    assert_eq!(
        chess_engine_cancellation_destroy(cancellation),
        ChessEngineResultCode::Ok
    );

    let snapshot = result_receiver
        .recv_timeout(Duration::from_secs(5))
        .expect("infinite ABI search stops within the cancellation deadline");
    worker.join().expect("ABI search worker does not panic");

    assert_eq!(snapshot.code, ChessEngineResultCode::Ok);
    assert_eq!(snapshot.free_code, ChessEngineResultCode::Ok);
    assert_eq!(
        snapshot.termination_kind,
        ChessEngineSearchTerminationKind::ExplicitStop
    );
    assert!(legal_moves.contains(&snapshot.best_move));
    assert!(snapshot.completed_depth > 0 || snapshot.selective_depth > 0 || snapshot.nodes > 0);
    assert_eq!(
        chess_engine_cancellation_destroy(cancellation),
        ChessEngineResultCode::InvalidHandle
    );
    assert_eq!(chess_engine_destroy(engine), ChessEngineResultCode::Ok);
}

#[test]
fn buffer_and_search_result_lifecycles_are_exact() {
    let engine = create_engine();

    let mut fen = ChessEngineBuffer::empty();
    // SAFETY: `fen` is a fresh writable output record.
    assert_eq!(
        unsafe { chess_engine_get_fen(engine, &mut fen) },
        ChessEngineResultCode::Ok
    );
    let mut stale_fen = fen;
    let mut wrong_length = fen;
    wrong_length.len = wrong_length.len.saturating_add(1);
    // SAFETY: The record is intentionally tampered to validate fail-closed freeing.
    assert_eq!(
        unsafe { chess_engine_buffer_free(&mut wrong_length) },
        ChessEngineResultCode::InvalidBuffer
    );
    assert_eq!(buffer_text(&fen), STARTING_FEN);
    free_buffer(&mut fen);
    // SAFETY: `stale_fen` repeats an allocation token that has already been freed.
    assert_eq!(
        unsafe { chess_engine_buffer_free(&mut stale_fen) },
        ChessEngineResultCode::InvalidBuffer
    );

    let mut empty = ChessEngineBuffer::empty();
    free_buffer(&mut empty);
    free_buffer(&mut empty);

    let mut request = ChessEngineSearchRequest::new();
    request.flags = CHESS_ENGINE_SEARCH_FLAG_DEPTH;
    request.depth = 2;
    let mut result = ChessEngineSearchResult::new();
    // SAFETY: Request and result pointers reference complete live records.
    assert_eq!(
        unsafe { chess_engine_search(engine, &request, &mut result) },
        ChessEngineResultCode::Ok
    );
    let mut stale_result = result;
    let mut tampered_result = result;
    tampered_result.principal_variation.len = tampered_result
        .principal_variation
        .len
        .saturating_add(1);
    // SAFETY: One field is intentionally tampered to verify all-or-nothing validation.
    assert_eq!(
        unsafe { chess_engine_search_result_free(&mut tampered_result) },
        ChessEngineResultCode::InvalidBuffer
    );
    assert!(!buffer_text(&result.best_move).is_empty());
    assert!(!buffer_text(&result.principal_variation).is_empty());
    // SAFETY: The original result remains unchanged and live after failed validation.
    assert_eq!(
        unsafe { chess_engine_search_result_free(&mut result) },
        ChessEngineResultCode::Ok
    );
    // SAFETY: `stale_result` repeats allocations already released by the prior call.
    assert_eq!(
        unsafe { chess_engine_search_result_free(&mut stale_result) },
        ChessEngineResultCode::InvalidBuffer
    );

    let mut empty_result = ChessEngineSearchResult::new();
    // SAFETY: Empty current-version result records own no allocations.
    assert_eq!(
        unsafe { chess_engine_search_result_free(&mut empty_result) },
        ChessEngineResultCode::Ok
    );
    // SAFETY: The previous call reset the record to the same valid empty state.
    assert_eq!(
        unsafe { chess_engine_search_result_free(&mut empty_result) },
        ChessEngineResultCode::Ok
    );

    assert_eq!(chess_engine_destroy(engine), ChessEngineResultCode::Ok);
}

#[cfg(feature = "ffi-test-faults")]
#[test]
fn exported_test_fault_is_contained_and_process_remains_usable() {
    assert_eq!(
        chess_engine_test_inject_panic(),
        ChessEngineResultCode::Panic
    );
    assert!(last_error_text().contains("panic contained"));

    let engine = create_engine();
    assert_eq!(get_fen(engine), STARTING_FEN);
    assert_eq!(chess_engine_destroy(engine), ChessEngineResultCode::Ok);
}
