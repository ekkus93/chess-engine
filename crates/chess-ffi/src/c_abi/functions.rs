use core::{mem::size_of, ptr, slice, str};
use std::time::Duration;

use chess_core::{Color, DrawReason, GameError, GameStatus};
use chess_search::{SearchCancellationFallback, SearchLimitTermination, SearchResult, MATE_SCORE};

use crate::{
    Engine, EngineConfig, EngineError, SearchCancellationHandle, SearchRequest, ENGINE_VERSION,
};

use super::{
    registry::{
        allocate_buffer, boundary, boundary_preserving_error, insert_cancellation, insert_engine,
        last_error_bytes, lock_engine, release_buffers, remove_cancellation, remove_engine,
        resolve_cancellation, resolve_engine, scalar_boundary, AbiFailure, AbiResult,
    },
    types::{
        ChessEngineBuffer, ChessEngineCancellationHandle, ChessEngineColor, ChessEngineConfig,
        ChessEngineDrawReason, ChessEngineGameStatus, ChessEngineGameStatusKind, ChessEngineHandle,
        ChessEngineResultCode, ChessEngineScoreKind, ChessEngineSearchFallbackKind,
        ChessEngineSearchRequest, ChessEngineSearchResult, ChessEngineSearchTerminationKind,
        ChessEngineWeightIdentity, CHESS_ENGINE_ABI_VERSION, CHESS_ENGINE_NULL_CANCELLATION_HANDLE,
        CHESS_ENGINE_NULL_HANDLE, CHESS_ENGINE_SEARCH_FLAG_CANCELLATION,
        CHESS_ENGINE_SEARCH_FLAG_CHECK_EXTENSION, CHESS_ENGINE_SEARCH_FLAG_DEPTH,
        CHESS_ENGINE_SEARCH_FLAG_HARD_TIME, CHESS_ENGINE_SEARCH_FLAG_INFINITE,
        CHESS_ENGINE_SEARCH_FLAG_NODES, CHESS_ENGINE_SEARCH_FLAG_SOFT_TIME,
        CHESS_ENGINE_SEARCH_KNOWN_FLAGS,
    },
};

fn null_pointer(label: &str) -> AbiFailure {
    AbiFailure::new(
        ChessEngineResultCode::NullPointer,
        format!("{label} is null"),
    )
}

fn invalid_argument(message: impl Into<String>) -> AbiFailure {
    AbiFailure::new(ChessEngineResultCode::InvalidArgument, message)
}

fn validate_record_header<T>(struct_size: u32, abi_version: u32, label: &str) -> AbiResult<()> {
    if abi_version != CHESS_ENGINE_ABI_VERSION {
        return Err(AbiFailure::new(
            ChessEngineResultCode::AbiMismatch,
            format!(
                "{label} ABI version {abi_version} is unsupported; expected {CHESS_ENGINE_ABI_VERSION}"
            ),
        ));
    }
    let expected = size_of::<T>() as u32;
    if struct_size != expected {
        return Err(AbiFailure::new(
            ChessEngineResultCode::AbiMismatch,
            format!("{label} size {struct_size} is unsupported; expected {expected}"),
        ));
    }
    Ok(())
}

unsafe fn read_copy<T: Copy>(source: *const T) -> T {
    // SAFETY: The caller guarantees that `source` points to a readable `T`.
    unsafe { ptr::read_unaligned(source) }
}

unsafe fn write_copy<T>(destination: *mut T, value: T) {
    // SAFETY: The caller guarantees that `destination` points to writable storage for `T`.
    unsafe { ptr::write_unaligned(destination, value) };
}

unsafe fn read_utf8<'a>(data: *const u8, len: usize, label: &str) -> AbiResult<&'a str> {
    if len == 0 {
        return Ok("");
    }
    if data.is_null() {
        return Err(null_pointer(label));
    }
    // SAFETY: The C caller guarantees a readable byte range of exactly `len` bytes.
    let bytes = unsafe { slice::from_raw_parts(data, len) };
    str::from_utf8(bytes).map_err(|error| {
        AbiFailure::new(
            ChessEngineResultCode::InvalidUtf8,
            format!("{label} is not valid UTF-8: {error}"),
        )
    })
}

fn engine_failure(error: EngineError) -> AbiFailure {
    let code = match &error {
        EngineError::InvalidFen(_) => ChessEngineResultCode::InvalidFen,
        EngineError::InvalidMoveSyntax(_) => ChessEngineResultCode::InvalidMoveSyntax,
        EngineError::IllegalMove { .. } => ChessEngineResultCode::IllegalMove,
        EngineError::Game(GameError::GameOver { .. }) => ChessEngineResultCode::GameOver,
        EngineError::Game(_) => ChessEngineResultCode::GameError,
        EngineError::Search(_) => ChessEngineResultCode::SearchError,
        EngineError::TranspositionTableAllocation(_)
        | EngineError::LegalMoveStorageAllocation { .. } => {
            ChessEngineResultCode::AllocationFailure
        }
        EngineError::InvalidWeightSet(_) => ChessEngineResultCode::InvalidWeightSet,
    };
    AbiFailure::new(code, error.to_string())
}

fn color_code(color: Color) -> ChessEngineColor {
    match color {
        Color::White => ChessEngineColor::White,
        Color::Black => ChessEngineColor::Black,
    }
}

fn draw_reason_code(reason: DrawReason) -> ChessEngineDrawReason {
    match reason {
        DrawReason::ThreefoldRepetition => ChessEngineDrawReason::ThreefoldRepetition,
        DrawReason::FivefoldRepetition => ChessEngineDrawReason::FivefoldRepetition,
        DrawReason::FiftyMoveRule => ChessEngineDrawReason::FiftyMoveRule,
        DrawReason::SeventyFiveMoveRule => ChessEngineDrawReason::SeventyFiveMoveRule,
        DrawReason::DeadPosition => ChessEngineDrawReason::DeadPosition,
    }
}

fn status_record(status: GameStatus) -> ChessEngineGameStatus {
    let mut output = ChessEngineGameStatus::new();
    match status {
        GameStatus::Ongoing => {}
        GameStatus::Checkmate { winner } => {
            output.kind = ChessEngineGameStatusKind::Checkmate;
            output.winner = color_code(winner);
        }
        GameStatus::Stalemate => {
            output.kind = ChessEngineGameStatusKind::Stalemate;
        }
        GameStatus::AutomaticDraw(reason) => {
            output.kind = ChessEngineGameStatusKind::AutomaticDraw;
            output.draw_reason = draw_reason_code(reason);
        }
        GameStatus::ClaimableDraw(reason) => {
            output.kind = ChessEngineGameStatusKind::ClaimableDraw;
            output.draw_reason = draw_reason_code(reason);
        }
    }
    output
}

fn validate_config(config: ChessEngineConfig) -> AbiResult<EngineConfig> {
    validate_record_header::<ChessEngineConfig>(
        config.struct_size,
        config.abi_version,
        "engine config",
    )?;
    let mebibytes = usize::try_from(config.transposition_table_mebibytes).map_err(|_| {
        invalid_argument("transposition-table budget does not fit the current platform")
    })?;
    Ok(EngineConfig::new().with_transposition_table_mebibytes(mebibytes))
}

fn validate_absent_search_values(request: ChessEngineSearchRequest) -> AbiResult<()> {
    let fields = [
        (
            CHESS_ENGINE_SEARCH_FLAG_DEPTH,
            u64::from(request.depth),
            "depth",
        ),
        (CHESS_ENGINE_SEARCH_FLAG_NODES, request.nodes, "nodes"),
        (
            CHESS_ENGINE_SEARCH_FLAG_SOFT_TIME,
            request.soft_time_milliseconds,
            "soft time",
        ),
        (
            CHESS_ENGINE_SEARCH_FLAG_HARD_TIME,
            request.hard_time_milliseconds,
            "hard time",
        ),
        (
            CHESS_ENGINE_SEARCH_FLAG_CANCELLATION,
            request.cancellation_handle,
            "cancellation handle",
        ),
    ];
    for (flag, value, label) in fields {
        if request.flags & flag == 0 && value != 0 {
            return Err(invalid_argument(format!(
                "search {label} value is nonzero without its presence flag"
            )));
        }
    }
    Ok(())
}

fn build_search_request(request: ChessEngineSearchRequest) -> AbiResult<SearchRequest> {
    validate_record_header::<ChessEngineSearchRequest>(
        request.struct_size,
        request.abi_version,
        "search request",
    )?;
    if request.reserved != 0 || request.reserved_depth != 0 {
        return Err(invalid_argument(
            "search request reserved fields must be zero",
        ));
    }
    if request.flags & !CHESS_ENGINE_SEARCH_KNOWN_FLAGS != 0 {
        return Err(invalid_argument(
            "search request contains unknown flag bits",
        ));
    }
    validate_absent_search_values(request)?;

    let cancellation = if request.flags & CHESS_ENGINE_SEARCH_FLAG_CANCELLATION != 0 {
        Some(resolve_cancellation(request.cancellation_handle)?)
    } else {
        None
    };

    let infinite = request.flags & CHESS_ENGINE_SEARCH_FLAG_INFINITE != 0;
    let mut output = if infinite {
        let cancellation = cancellation.as_deref().ok_or_else(|| {
            invalid_argument("infinite search requires the cancellation presence flag")
        })?;
        SearchRequest::infinite(cancellation)
    } else {
        SearchRequest::new()
    };

    if request.flags & CHESS_ENGINE_SEARCH_FLAG_DEPTH != 0 {
        output = output.with_depth(request.depth);
    }
    if request.flags & CHESS_ENGINE_SEARCH_FLAG_NODES != 0 {
        output = output.with_nodes(request.nodes);
    }
    if request.flags & CHESS_ENGINE_SEARCH_FLAG_SOFT_TIME != 0 {
        output = output.with_soft_time(Duration::from_millis(request.soft_time_milliseconds));
    }
    if request.flags & CHESS_ENGINE_SEARCH_FLAG_HARD_TIME != 0 {
        output = output.with_hard_time(Duration::from_millis(request.hard_time_milliseconds));
    }
    if !infinite {
        if let Some(cancellation) = cancellation.as_deref() {
            output = output.with_cancellation(cancellation);
        }
    }
    if request.flags & CHESS_ENGINE_SEARCH_FLAG_CHECK_EXTENSION != 0 {
        output = output.with_check_extension();
    }
    Ok(output)
}

fn elapsed_milliseconds(duration: Duration) -> u64 {
    u64::try_from(duration.as_millis()).unwrap_or(u64::MAX)
}

fn score_fields(result: &SearchResult) -> (ChessEngineScoreKind, i32) {
    let Some(score) = result.score() else {
        return (ChessEngineScoreKind::None, 0);
    };
    if !score.is_mate() {
        return (ChessEngineScoreKind::Centipawns, score.centipawns());
    }

    let raw = score.centipawns();
    let plies = MATE_SCORE.saturating_sub(raw.abs());
    let moves = plies.saturating_add(1) / 2;
    let signed_moves = if raw < 0 { -moves } else { moves };
    (ChessEngineScoreKind::Mate, signed_moves)
}

fn termination_fields(
    termination: SearchLimitTermination,
) -> (ChessEngineSearchTerminationKind, u64) {
    match termination {
        SearchLimitTermination::Depth { depth } => {
            (ChessEngineSearchTerminationKind::Depth, u64::from(depth))
        }
        SearchLimitTermination::Nodes { nodes } => (ChessEngineSearchTerminationKind::Nodes, nodes),
        SearchLimitTermination::SoftTime { limit } => (
            ChessEngineSearchTerminationKind::SoftTime,
            elapsed_milliseconds(limit),
        ),
        SearchLimitTermination::HardTime { limit } => (
            ChessEngineSearchTerminationKind::HardTime,
            elapsed_milliseconds(limit),
        ),
        SearchLimitTermination::ExplicitStop => (ChessEngineSearchTerminationKind::ExplicitStop, 0),
        SearchLimitTermination::MaximumSupportedDepth { depth } => (
            ChessEngineSearchTerminationKind::MaximumSupportedDepth,
            u64::from(depth),
        ),
    }
}

fn fallback_kind(result: &SearchResult) -> ChessEngineSearchFallbackKind {
    match result.fallback() {
        None => ChessEngineSearchFallbackKind::None,
        Some(SearchCancellationFallback::FirstLegalMove(_)) => {
            ChessEngineSearchFallbackKind::FirstLegalMove
        }
        Some(SearchCancellationFallback::NoLegalMove) => ChessEngineSearchFallbackKind::NoLegalMove,
    }
}

fn principal_variation_text(result: &SearchResult) -> String {
    result
        .principal_variation()
        .map_or_else(String::new, |line| {
            line.moves()
                .iter()
                .map(|current| current.to_uci())
                .collect::<Vec<_>>()
                .join(" ")
        })
}

fn allocate_search_buffers(
    best_move: Vec<u8>,
    ponder_move: Vec<u8>,
    principal_variation: Vec<u8>,
) -> AbiResult<[ChessEngineBuffer; 3]> {
    let best = allocate_buffer(best_move)?;
    let ponder = match allocate_buffer(ponder_move) {
        Ok(buffer) => buffer,
        Err(error) => {
            let _ = release_buffers(&[best]);
            return Err(error);
        }
    };
    let principal_variation = match allocate_buffer(principal_variation) {
        Ok(buffer) => buffer,
        Err(error) => {
            let _ = release_buffers(&[best, ponder]);
            return Err(error);
        }
    };
    Ok([best, ponder, principal_variation])
}

fn search_result_record(result: &SearchResult) -> AbiResult<ChessEngineSearchResult> {
    let best_move = result
        .best_move()
        .map_or_else(Vec::new, |current| current.to_uci().into_bytes());
    let ponder_move = result
        .ponder_move()
        .map_or_else(Vec::new, |current| current.to_uci().into_bytes());
    let principal_variation = principal_variation_text(result).into_bytes();
    let [best_move, ponder_move, principal_variation] =
        allocate_search_buffers(best_move, ponder_move, principal_variation)?;
    let (score_kind, score_value) = score_fields(result);
    let (termination_kind, termination_value) = termination_fields(result.termination());

    Ok(ChessEngineSearchResult {
        struct_size: size_of::<ChessEngineSearchResult>() as u32,
        abi_version: CHESS_ENGINE_ABI_VERSION,
        best_move,
        ponder_move,
        principal_variation,
        score_kind,
        score_value,
        completed_depth: result.completed_depth(),
        selective_depth: result.selective_depth(),
        termination_kind,
        fallback_kind: fallback_kind(result),
        termination_value,
        nodes: result.nodes(),
        qnodes: result.qnodes(),
        elapsed_milliseconds: elapsed_milliseconds(result.elapsed()),
    })
}

/// Returns the stable ABI version, or zero if a panic is contained.
#[no_mangle]
pub extern "C" fn chess_engine_abi_version() -> u32 {
    scalar_boundary(|| CHESS_ENGINE_ABI_VERSION)
}

/// Writes the current default construction record.
///
/// # Safety
///
/// `out_config` must point to writable storage for one [`ChessEngineConfig`].
#[no_mangle]
pub unsafe extern "C" fn chess_engine_config_init(
    out_config: *mut ChessEngineConfig,
) -> ChessEngineResultCode {
    boundary(|| {
        if out_config.is_null() {
            return Err(null_pointer("output config"));
        }
        // SAFETY: Required by this function's C contract and checked for null above.
        unsafe { write_copy(out_config, ChessEngineConfig::new()) };
        Ok(())
    })
}

/// Writes an empty current-version output buffer record.
///
/// # Safety
///
/// `out_buffer` must point to writable storage for one [`ChessEngineBuffer`].
#[no_mangle]
pub unsafe extern "C" fn chess_engine_buffer_init(
    out_buffer: *mut ChessEngineBuffer,
) -> ChessEngineResultCode {
    boundary(|| {
        if out_buffer.is_null() {
            return Err(null_pointer("output buffer"));
        }
        // SAFETY: Required by this function's C contract and checked for null above.
        unsafe { write_copy(out_buffer, ChessEngineBuffer::empty()) };
        Ok(())
    })
}

/// Writes an empty current-version search request.
///
/// # Safety
///
/// `out_request` must point to writable storage for one [`ChessEngineSearchRequest`].
#[no_mangle]
pub unsafe extern "C" fn chess_engine_search_request_init(
    out_request: *mut ChessEngineSearchRequest,
) -> ChessEngineResultCode {
    boundary(|| {
        if out_request.is_null() {
            return Err(null_pointer("output search request"));
        }
        // SAFETY: Required by this function's C contract and checked for null above.
        unsafe { write_copy(out_request, ChessEngineSearchRequest::new()) };
        Ok(())
    })
}

/// Writes an empty current-version search result.
///
/// # Safety
///
/// `out_result` must point to writable storage for one [`ChessEngineSearchResult`].
#[no_mangle]
pub unsafe extern "C" fn chess_engine_search_result_init(
    out_result: *mut ChessEngineSearchResult,
) -> ChessEngineResultCode {
    boundary(|| {
        if out_result.is_null() {
            return Err(null_pointer("output search result"));
        }
        // SAFETY: Required by this function's C contract and checked for null above.
        unsafe { write_copy(out_result, ChessEngineSearchResult::new()) };
        Ok(())
    })
}

/// Copies the calling thread's last error into a registry-owned byte buffer.
///
/// Successful retrieval does not clear the stored error.
///
/// # Safety
///
/// `out_buffer` must point to a fresh writable [`ChessEngineBuffer`] record.
#[no_mangle]
pub unsafe extern "C" fn chess_engine_last_error_message(
    out_buffer: *mut ChessEngineBuffer,
) -> ChessEngineResultCode {
    boundary_preserving_error(|| {
        if out_buffer.is_null() {
            return Err(null_pointer("output error buffer"));
        }
        // SAFETY: Required by this function's C contract and checked for null above.
        unsafe { write_copy(out_buffer, ChessEngineBuffer::empty()) };
        let buffer = allocate_buffer(last_error_bytes())?;
        // SAFETY: Required by this function's C contract and checked for null above.
        unsafe { write_copy(out_buffer, buffer) };
        Ok(())
    })
}

/// Frees one unchanged registry-owned output buffer.
///
/// # Safety
///
/// `buffer` must point to a record returned by this ABI or initialized empty.
#[no_mangle]
pub unsafe extern "C" fn chess_engine_buffer_free(
    buffer: *mut ChessEngineBuffer,
) -> ChessEngineResultCode {
    boundary(|| {
        if buffer.is_null() {
            return Err(null_pointer("buffer record"));
        }
        // SAFETY: Required by this function's C contract and checked for null above.
        let current = unsafe { read_copy(buffer) };
        release_buffers(&[current])?;
        // SAFETY: Required by this function's C contract and checked for null above.
        unsafe { write_copy(buffer, ChessEngineBuffer::empty()) };
        Ok(())
    })
}

/// Frees all owned buffers in one unchanged search result.
///
/// # Safety
///
/// `result` must point to a current-version record returned by this ABI or
/// initialized by `chess_engine_search_result_init`.
#[no_mangle]
pub unsafe extern "C" fn chess_engine_search_result_free(
    result: *mut ChessEngineSearchResult,
) -> ChessEngineResultCode {
    boundary(|| {
        if result.is_null() {
            return Err(null_pointer("search result"));
        }
        // SAFETY: Required by this function's C contract and checked for null above.
        let current = unsafe { read_copy(result) };
        validate_record_header::<ChessEngineSearchResult>(
            current.struct_size,
            current.abi_version,
            "search result",
        )?;
        release_buffers(&[
            current.best_move,
            current.ponder_move,
            current.principal_variation,
        ])?;
        // SAFETY: Required by this function's C contract and checked for null above.
        unsafe { write_copy(result, ChessEngineSearchResult::new()) };
        Ok(())
    })
}

/// Copies the semantic engine version into a registry-owned UTF-8 buffer.
///
/// # Safety
///
/// `out_buffer` must point to a fresh writable [`ChessEngineBuffer`] record.
#[no_mangle]
pub unsafe extern "C" fn chess_engine_version(
    out_buffer: *mut ChessEngineBuffer,
) -> ChessEngineResultCode {
    boundary(|| {
        if out_buffer.is_null() {
            return Err(null_pointer("output version buffer"));
        }
        // SAFETY: Required by this function's C contract and checked for null above.
        unsafe { write_copy(out_buffer, ChessEngineBuffer::empty()) };
        let buffer = allocate_buffer(ENGINE_VERSION.as_bytes().to_vec())?;
        // SAFETY: Required by this function's C contract and checked for null above.
        unsafe { write_copy(out_buffer, buffer) };
        Ok(())
    })
}

/// Creates one opaque engine token. A null config selects defaults.
///
/// # Safety
///
/// A non-null `config` must point to a readable [`ChessEngineConfig`].
/// `out_handle` must point to writable storage for one [`ChessEngineHandle`].
#[no_mangle]
pub unsafe extern "C" fn chess_engine_create(
    config: *const ChessEngineConfig,
    out_handle: *mut ChessEngineHandle,
) -> ChessEngineResultCode {
    boundary(|| {
        if out_handle.is_null() {
            return Err(null_pointer("output engine handle"));
        }
        // SAFETY: Required by this function's C contract and checked for null above.
        unsafe { write_copy(out_handle, CHESS_ENGINE_NULL_HANDLE) };
        let config = if config.is_null() {
            EngineConfig::new()
        } else {
            // SAFETY: Required by this function's C contract.
            validate_config(unsafe { read_copy(config) })?
        };
        let engine = Engine::new(config).map_err(engine_failure)?;
        let handle = insert_engine(engine)?;
        // SAFETY: Required by this function's C contract and checked for null above.
        unsafe { write_copy(out_handle, handle) };
        Ok(())
    })
}

/// Invalidates one opaque engine token.
#[no_mangle]
pub extern "C" fn chess_engine_destroy(handle: ChessEngineHandle) -> ChessEngineResultCode {
    boundary(|| remove_engine(handle))
}

/// Resets one engine to the standard starting position.
#[no_mangle]
pub extern "C" fn chess_engine_reset_position(handle: ChessEngineHandle) -> ChessEngineResultCode {
    boundary(|| {
        let entry = resolve_engine(handle)?;
        let mut engine = lock_engine(&entry)?;
        engine.reset_position();
        Ok(())
    })
}

/// Replaces the current position from explicit-length UTF-8 FEN.
///
/// # Safety
///
/// `fen` must be null only when `fen_len` is zero; otherwise it must reference
/// exactly `fen_len` readable bytes.
#[no_mangle]
pub unsafe extern "C" fn chess_engine_set_position(
    handle: ChessEngineHandle,
    fen: *const u8,
    fen_len: usize,
) -> ChessEngineResultCode {
    boundary(|| {
        // SAFETY: Required by this function's C contract.
        let fen = unsafe { read_utf8(fen, fen_len, "FEN input") }?;
        let entry = resolve_engine(handle)?;
        let mut engine = lock_engine(&entry)?;
        engine.set_position(fen).map_err(engine_failure)
    })
}

/// Returns canonical six-field FEN in a registry-owned UTF-8 buffer.
///
/// # Safety
///
/// `out_buffer` must point to a fresh writable [`ChessEngineBuffer`] record.
#[no_mangle]
pub unsafe extern "C" fn chess_engine_get_fen(
    handle: ChessEngineHandle,
    out_buffer: *mut ChessEngineBuffer,
) -> ChessEngineResultCode {
    boundary(|| {
        if out_buffer.is_null() {
            return Err(null_pointer("output FEN buffer"));
        }
        // SAFETY: Required by this function's C contract and checked for null above.
        unsafe { write_copy(out_buffer, ChessEngineBuffer::empty()) };
        let entry = resolve_engine(handle)?;
        let fen = {
            let engine = lock_engine(&entry)?;
            engine.fen()
        };
        let buffer = allocate_buffer(fen.into_bytes())?;
        // SAFETY: Required by this function's C contract and checked for null above.
        unsafe { write_copy(out_buffer, buffer) };
        Ok(())
    })
}

/// Returns deterministic legal UCI moves separated by `\n` bytes.
///
/// # Safety
///
/// `out_buffer` must point to a fresh writable [`ChessEngineBuffer`] record.
#[no_mangle]
pub unsafe extern "C" fn chess_engine_get_legal_moves(
    handle: ChessEngineHandle,
    out_buffer: *mut ChessEngineBuffer,
) -> ChessEngineResultCode {
    boundary(|| {
        if out_buffer.is_null() {
            return Err(null_pointer("output legal-move buffer"));
        }
        // SAFETY: Required by this function's C contract and checked for null above.
        unsafe { write_copy(out_buffer, ChessEngineBuffer::empty()) };
        let entry = resolve_engine(handle)?;
        let moves = {
            let mut engine = lock_engine(&entry)?;
            engine.legal_moves().map_err(engine_failure)?
        };
        let buffer = allocate_buffer(moves.join("\n").into_bytes())?;
        // SAFETY: Required by this function's C contract and checked for null above.
        unsafe { write_copy(out_buffer, buffer) };
        Ok(())
    })
}

/// Applies one explicit-length UTF-8 UCI move.
///
/// # Safety
///
/// `move_text` must be null only when `move_len` is zero; otherwise it must
/// reference exactly `move_len` readable bytes.
#[no_mangle]
pub unsafe extern "C" fn chess_engine_play_move(
    handle: ChessEngineHandle,
    move_text: *const u8,
    move_len: usize,
) -> ChessEngineResultCode {
    boundary(|| {
        // SAFETY: Required by this function's C contract.
        let move_text = unsafe { read_utf8(move_text, move_len, "move input") }?;
        let entry = resolve_engine(handle)?;
        let mut engine = lock_engine(&entry)?;
        engine.play_move(move_text).map_err(engine_failure)
    })
}

/// Returns the current rule-level game status.
///
/// # Safety
///
/// `out_status` must point to writable storage for one [`ChessEngineGameStatus`].
#[no_mangle]
pub unsafe extern "C" fn chess_engine_get_game_status(
    handle: ChessEngineHandle,
    out_status: *mut ChessEngineGameStatus,
) -> ChessEngineResultCode {
    boundary(|| {
        if out_status.is_null() {
            return Err(null_pointer("output game status"));
        }
        // SAFETY: Required by this function's C contract and checked for null above.
        unsafe { write_copy(out_status, ChessEngineGameStatus::new()) };
        let entry = resolve_engine(handle)?;
        let status = {
            let mut engine = lock_engine(&entry)?;
            engine.game_status().map_err(engine_failure)?
        };
        // SAFETY: Required by this function's C contract and checked for null above.
        unsafe { write_copy(out_status, status_record(status)) };
        Ok(())
    })
}

/// Returns the exact built-in evaluation-weight identity.
///
/// # Safety
///
/// `out_identity` must point to writable storage for one [`ChessEngineWeightIdentity`].
#[no_mangle]
pub unsafe extern "C" fn chess_engine_get_weight_identity(
    handle: ChessEngineHandle,
    out_identity: *mut ChessEngineWeightIdentity,
) -> ChessEngineResultCode {
    boundary(|| {
        if out_identity.is_null() {
            return Err(null_pointer("output weight identity"));
        }
        // SAFETY: Required by this function's C contract and checked for null above.
        unsafe { write_copy(out_identity, ChessEngineWeightIdentity::new()) };
        let entry = resolve_engine(handle)?;
        let identity = {
            let engine = lock_engine(&entry)?;
            engine.weight_identity()
        };
        let output = ChessEngineWeightIdentity {
            struct_size: size_of::<ChessEngineWeightIdentity>() as u32,
            abi_version: CHESS_ENGINE_ABI_VERSION,
            schema_version: identity.schema_version(),
            reserved: 0,
            identifier: identity.identifier(),
            checksum: identity.checksum(),
        };
        // SAFETY: Required by this function's C contract and checked for null above.
        unsafe { write_copy(out_identity, output) };
        Ok(())
    })
}

/// Creates one request-local cancellation token.
///
/// # Safety
///
/// `out_handle` must point to writable storage for one cancellation token.
#[no_mangle]
pub unsafe extern "C" fn chess_engine_cancellation_create(
    out_handle: *mut ChessEngineCancellationHandle,
) -> ChessEngineResultCode {
    boundary(|| {
        if out_handle.is_null() {
            return Err(null_pointer("output cancellation handle"));
        }
        // SAFETY: Required by this function's C contract and checked for null above.
        unsafe { write_copy(out_handle, CHESS_ENGINE_NULL_CANCELLATION_HANDLE) };
        let handle = insert_cancellation(SearchCancellationHandle::new())?;
        // SAFETY: Required by this function's C contract and checked for null above.
        unsafe { write_copy(out_handle, handle) };
        Ok(())
    })
}

/// Invalidates one cancellation token. In-flight searches retain their clone.
#[no_mangle]
pub extern "C" fn chess_engine_cancellation_destroy(
    handle: ChessEngineCancellationHandle,
) -> ChessEngineResultCode {
    boundary(|| remove_cancellation(handle))
}

/// Requests cancellation through one live cancellation token.
#[no_mangle]
pub extern "C" fn chess_engine_cancellation_cancel(
    handle: ChessEngineCancellationHandle,
) -> ChessEngineResultCode {
    boundary(|| {
        let cancellation = resolve_cancellation(handle)?;
        cancellation.cancel();
        Ok(())
    })
}

/// Clears one live cancellation token before intentional reuse.
#[no_mangle]
pub extern "C" fn chess_engine_cancellation_reset(
    handle: ChessEngineCancellationHandle,
) -> ChessEngineResultCode {
    boundary(|| {
        let cancellation = resolve_cancellation(handle)?;
        cancellation.reset();
        Ok(())
    })
}

/// Returns one byte equal to zero or one for cancellation state.
///
/// # Safety
///
/// `out_cancelled` must point to one writable byte.
#[no_mangle]
pub unsafe extern "C" fn chess_engine_cancellation_is_cancelled(
    handle: ChessEngineCancellationHandle,
    out_cancelled: *mut u8,
) -> ChessEngineResultCode {
    boundary(|| {
        if out_cancelled.is_null() {
            return Err(null_pointer("output cancellation state"));
        }
        // SAFETY: Required by this function's C contract and checked for null above.
        unsafe { write_copy(out_cancelled, 0) };
        let cancellation = resolve_cancellation(handle)?;
        // SAFETY: Required by this function's C contract and checked for null above.
        unsafe { write_copy(out_cancelled, u8::from(cancellation.is_cancelled())) };
        Ok(())
    })
}

/// Runs one synchronous search and returns a typed current-version snapshot.
///
/// The engine token remains valid after search. A cancellation token referenced
/// by the request may be used concurrently from another thread.
///
/// # Safety
///
/// `request` must point to a readable [`ChessEngineSearchRequest`].
/// `out_result` must point to a fresh writable [`ChessEngineSearchResult`].
#[no_mangle]
pub unsafe extern "C" fn chess_engine_search(
    handle: ChessEngineHandle,
    request: *const ChessEngineSearchRequest,
    out_result: *mut ChessEngineSearchResult,
) -> ChessEngineResultCode {
    boundary(|| {
        if request.is_null() {
            return Err(null_pointer("search request"));
        }
        if out_result.is_null() {
            return Err(null_pointer("output search result"));
        }
        // SAFETY: Required by this function's C contract and checked for null above.
        unsafe { write_copy(out_result, ChessEngineSearchResult::new()) };
        // SAFETY: Required by this function's C contract and checked for null above.
        let request = build_search_request(unsafe { read_copy(request) })?;
        let entry = resolve_engine(handle)?;
        let result = {
            let mut engine = lock_engine(&entry)?;
            engine.search(request).map_err(engine_failure)?
        };
        let output = search_result_record(&result)?;
        // SAFETY: Required by this function's C contract and checked for null above.
        unsafe { write_copy(out_result, output) };
        Ok(())
    })
}
