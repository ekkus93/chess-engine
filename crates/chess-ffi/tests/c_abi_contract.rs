use std::{ptr, slice, str};

use chess_ffi::c_abi::*;

const STARTING_FEN: &str = "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1";
const MATE_FEN: &str = "7k/6Q1/6K1/8/8/8/8/8 b - - 0 1";

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

fn buffer_bytes(buffer: &ChessEngineBuffer) -> Vec<u8> {
    if buffer.len == 0 {
        assert!(buffer.data.is_null());
        return Vec::new();
    }
    assert!(!buffer.data.is_null());
    // SAFETY: Live ABI buffer records guarantee exactly `len` readable bytes.
    unsafe { slice::from_raw_parts(buffer.data, buffer.len).to_vec() }
}

fn buffer_text(buffer: &ChessEngineBuffer) -> String {
    str::from_utf8(&buffer_bytes(buffer))
        .expect("ABI text outputs are UTF-8")
        .to_owned()
}

fn free_buffer(buffer: &mut ChessEngineBuffer) {
    // SAFETY: The record is either empty or an unchanged live ABI allocation.
    assert_eq!(
        unsafe { chess_engine_buffer_free(buffer) },
        ChessEngineResultCode::Ok
    );
}

#[test]
fn versioned_construction_identity_and_destroy_are_exact() {
    assert_eq!(chess_engine_abi_version(), CHESS_ENGINE_ABI_VERSION);

    let mut config = ChessEngineConfig {
        struct_size: 0,
        abi_version: 0,
        transposition_table_mebibytes: 0,
    };
    // SAFETY: `config` is writable for one complete record.
    assert_eq!(
        unsafe { chess_engine_config_init(&mut config) },
        ChessEngineResultCode::Ok
    );
    config.transposition_table_mebibytes = 1;

    let mut handle = CHESS_ENGINE_NULL_HANDLE;
    // SAFETY: Input and output pointers reference valid records.
    assert_eq!(
        unsafe { chess_engine_create(&config, &mut handle) },
        ChessEngineResultCode::Ok
    );

    let mut version = ChessEngineBuffer::empty();
    // SAFETY: `version` is a fresh writable output record.
    assert_eq!(
        unsafe { chess_engine_version(&mut version) },
        ChessEngineResultCode::Ok
    );
    assert_eq!(buffer_text(&version), env!("CARGO_PKG_VERSION"));
    free_buffer(&mut version);

    let mut identity = ChessEngineWeightIdentity::new();
    // SAFETY: `identity` is writable for one complete record.
    assert_eq!(
        unsafe { chess_engine_get_weight_identity(handle, &mut identity) },
        ChessEngineResultCode::Ok
    );
    assert_eq!(identity.abi_version, CHESS_ENGINE_ABI_VERSION);
    assert_ne!(identity.identifier, 0);
    assert_ne!(identity.checksum, 0);

    assert_eq!(chess_engine_destroy(handle), ChessEngineResultCode::Ok);
    assert_eq!(
        chess_engine_destroy(handle),
        ChessEngineResultCode::InvalidHandle
    );
}

#[test]
fn explicit_utf8_position_moves_and_status_round_trip() {
    let handle = create_engine();

    let mut legal_moves = ChessEngineBuffer::empty();
    // SAFETY: `legal_moves` is a fresh writable output record.
    assert_eq!(
        unsafe { chess_engine_get_legal_moves(handle, &mut legal_moves) },
        ChessEngineResultCode::Ok
    );
    let legal_text = buffer_text(&legal_moves);
    assert_eq!(legal_text.lines().count(), 20);
    assert!(legal_text.lines().any(|current| current == "e2e4"));
    free_buffer(&mut legal_moves);

    let move_text = b"e2e4";
    // SAFETY: The input range is readable for exactly its explicit length.
    assert_eq!(
        unsafe { chess_engine_play_move(handle, move_text.as_ptr(), move_text.len()) },
        ChessEngineResultCode::Ok
    );

    let mut fen = ChessEngineBuffer::empty();
    // SAFETY: `fen` is a fresh writable output record.
    assert_eq!(
        unsafe { chess_engine_get_fen(handle, &mut fen) },
        ChessEngineResultCode::Ok
    );
    assert_eq!(
        buffer_text(&fen),
        "rnbqkbnr/pppppppp/8/8/4P3/8/PPPP1PPP/RNBQKBNR b KQkq e3 0 1"
    );
    free_buffer(&mut fen);

    // SAFETY: The FEN byte range is readable for exactly its explicit length.
    assert_eq!(
        unsafe { chess_engine_set_position(handle, MATE_FEN.as_ptr(), MATE_FEN.len()) },
        ChessEngineResultCode::Ok
    );
    let mut status = ChessEngineGameStatus::new();
    // SAFETY: `status` is writable for one complete record.
    assert_eq!(
        unsafe { chess_engine_get_game_status(handle, &mut status) },
        ChessEngineResultCode::Ok
    );
    assert_eq!(status.kind, ChessEngineGameStatusKind::Checkmate);
    assert_eq!(status.winner, ChessEngineColor::White);

    assert_eq!(
        chess_engine_reset_position(handle),
        ChessEngineResultCode::Ok
    );
    let mut reset_fen = ChessEngineBuffer::empty();
    // SAFETY: `reset_fen` is a fresh writable output record.
    assert_eq!(
        unsafe { chess_engine_get_fen(handle, &mut reset_fen) },
        ChessEngineResultCode::Ok
    );
    assert_eq!(buffer_text(&reset_fen), STARTING_FEN);
    free_buffer(&mut reset_fen);

    let invalid_utf8 = [0xff_u8];
    // SAFETY: The byte range is readable, but intentionally invalid UTF-8.
    assert_eq!(
        unsafe { chess_engine_set_position(handle, invalid_utf8.as_ptr(), invalid_utf8.len()) },
        ChessEngineResultCode::InvalidUtf8
    );
    let mut error = ChessEngineBuffer::empty();
    // SAFETY: `error` is a fresh writable output record.
    assert_eq!(
        unsafe { chess_engine_last_error_message(&mut error) },
        ChessEngineResultCode::Ok
    );
    assert!(buffer_text(&error).contains("not valid UTF-8"));
    free_buffer(&mut error);

    assert_eq!(chess_engine_destroy(handle), ChessEngineResultCode::Ok);
}

#[test]
fn opaque_types_and_buffer_tokens_reject_stale_or_wrong_values() {
    let engine = create_engine();
    let mut cancellation = CHESS_ENGINE_NULL_CANCELLATION_HANDLE;
    // SAFETY: `cancellation` is writable for one complete token.
    assert_eq!(
        unsafe { chess_engine_cancellation_create(&mut cancellation) },
        ChessEngineResultCode::Ok
    );

    assert_eq!(
        chess_engine_destroy(cancellation),
        ChessEngineResultCode::InvalidHandle
    );
    assert_eq!(
        chess_engine_cancellation_cancel(engine),
        ChessEngineResultCode::InvalidHandle
    );

    let mut fen = ChessEngineBuffer::empty();
    // SAFETY: `fen` is a fresh writable output record.
    assert_eq!(
        unsafe { chess_engine_get_fen(engine, &mut fen) },
        ChessEngineResultCode::Ok
    );
    let mut stale = fen;
    free_buffer(&mut fen);
    // SAFETY: `stale` intentionally repeats an already-freed allocation token.
    assert_eq!(
        unsafe { chess_engine_buffer_free(&mut stale) },
        ChessEngineResultCode::InvalidBuffer
    );

    // SAFETY: A null output pointer is intentionally supplied for validation.
    assert_eq!(
        unsafe { chess_engine_get_fen(engine, ptr::null_mut()) },
        ChessEngineResultCode::NullPointer
    );

    assert_eq!(
        chess_engine_cancellation_destroy(cancellation),
        ChessEngineResultCode::Ok
    );
    assert_eq!(chess_engine_destroy(engine), ChessEngineResultCode::Ok);
}

#[test]
fn search_result_is_typed_owned_and_cancellable_before_depth_one() {
    let engine = create_engine();
    let mut request = ChessEngineSearchRequest::new();
    request.flags = CHESS_ENGINE_SEARCH_FLAG_DEPTH;
    request.depth = 2;
    let mut result = ChessEngineSearchResult::new();

    // SAFETY: Request and output pointers reference complete live records.
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
    assert_eq!(buffer_text(&result.best_move).len(), 4);
    assert!(!buffer_text(&result.principal_variation).is_empty());
    // SAFETY: `result` is an unchanged live ABI search result.
    assert_eq!(
        unsafe { chess_engine_search_result_free(&mut result) },
        ChessEngineResultCode::Ok
    );

    let mut cancellation = CHESS_ENGINE_NULL_CANCELLATION_HANDLE;
    // SAFETY: `cancellation` is writable for one complete token.
    assert_eq!(
        unsafe { chess_engine_cancellation_create(&mut cancellation) },
        ChessEngineResultCode::Ok
    );
    assert_eq!(
        chess_engine_cancellation_cancel(cancellation),
        ChessEngineResultCode::Ok
    );

    request = ChessEngineSearchRequest::new();
    request.flags = CHESS_ENGINE_SEARCH_FLAG_DEPTH | CHESS_ENGINE_SEARCH_FLAG_CANCELLATION;
    request.depth = 8;
    request.cancellation_handle = cancellation;
    result = ChessEngineSearchResult::new();
    // SAFETY: Request and output pointers reference complete live records.
    assert_eq!(
        unsafe { chess_engine_search(engine, &request, &mut result) },
        ChessEngineResultCode::Ok
    );
    assert_eq!(result.completed_depth, 0);
    assert_eq!(
        result.termination_kind,
        ChessEngineSearchTerminationKind::ExplicitStop
    );
    assert_eq!(
        result.fallback_kind,
        ChessEngineSearchFallbackKind::FirstLegalMove
    );
    assert_eq!(buffer_text(&result.best_move).len(), 4);
    // SAFETY: `result` is an unchanged live ABI search result.
    assert_eq!(
        unsafe { chess_engine_search_result_free(&mut result) },
        ChessEngineResultCode::Ok
    );

    assert_eq!(
        chess_engine_cancellation_reset(cancellation),
        ChessEngineResultCode::Ok
    );
    let mut cancelled = 1_u8;
    // SAFETY: `cancelled` points to one writable byte.
    assert_eq!(
        unsafe { chess_engine_cancellation_is_cancelled(cancellation, &mut cancelled) },
        ChessEngineResultCode::Ok
    );
    assert_eq!(cancelled, 0);

    assert_eq!(
        chess_engine_cancellation_destroy(cancellation),
        ChessEngineResultCode::Ok
    );
    assert_eq!(chess_engine_destroy(engine), ChessEngineResultCode::Ok);
}

#[test]
fn versioned_input_records_fail_closed() {
    let mut config = ChessEngineConfig::new();
    config.abi_version = CHESS_ENGINE_ABI_VERSION + 1;
    let mut handle = CHESS_ENGINE_NULL_HANDLE;
    // SAFETY: Input and output pointers reference complete records.
    assert_eq!(
        unsafe { chess_engine_create(&config, &mut handle) },
        ChessEngineResultCode::AbiMismatch
    );
    assert_eq!(handle, CHESS_ENGINE_NULL_HANDLE);

    let engine = create_engine();
    let mut request = ChessEngineSearchRequest::new();
    request.struct_size = 0;
    let mut result = ChessEngineSearchResult::new();
    // SAFETY: Request and output pointers reference complete records.
    assert_eq!(
        unsafe { chess_engine_search(engine, &request, &mut result) },
        ChessEngineResultCode::AbiMismatch
    );
    assert_eq!(result, ChessEngineSearchResult::new());
    assert_eq!(chess_engine_destroy(engine), ChessEngineResultCode::Ok);
}
