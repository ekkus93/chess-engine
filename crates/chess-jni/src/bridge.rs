use core::{fmt, slice};
use std::{panic::AssertUnwindSafe, ptr};

use chess_ffi::c_abi::{
    chess_engine_buffer_free, chess_engine_cancellation_cancel,
    chess_engine_cancellation_create, chess_engine_cancellation_destroy,
    chess_engine_cancellation_is_cancelled, chess_engine_cancellation_reset, chess_engine_create,
    chess_engine_destroy, chess_engine_get_fen, chess_engine_get_game_status,
    chess_engine_get_legal_moves, chess_engine_get_weight_identity,
    chess_engine_last_error_message, chess_engine_play_move, chess_engine_reset_position,
    chess_engine_search, chess_engine_search_result_free, chess_engine_set_position,
    chess_engine_version, ChessEngineBuffer, ChessEngineCancellationHandle, ChessEngineConfig,
    ChessEngineGameStatus, ChessEngineHandle, ChessEngineResultCode, ChessEngineSearchRequest,
    ChessEngineSearchResult, ChessEngineWeightIdentity, CHESS_ENGINE_NULL_CANCELLATION_HANDLE,
    CHESS_ENGINE_NULL_HANDLE, CHESS_ENGINE_SEARCH_FLAG_CANCELLATION,
    CHESS_ENGINE_SEARCH_FLAG_CHECK_EXTENSION, CHESS_ENGINE_SEARCH_FLAG_DEPTH,
    CHESS_ENGINE_SEARCH_FLAG_HARD_TIME, CHESS_ENGINE_SEARCH_FLAG_INFINITE,
    CHESS_ENGINE_SEARCH_FLAG_NODES, CHESS_ENGINE_SEARCH_FLAG_SOFT_TIME,
};
use jni::{
    objects::{JObject, JString, JValue},
    sys::{jboolean, jint, jlong, jstring, JNI_FALSE, JNI_TRUE},
    JNIEnv,
};

const EXCEPTION_CLASS: &str = "com/ekkus93/chessengine/ChessEngineException";

#[derive(Debug)]
pub(crate) enum BridgeError {
    Abi {
        code: ChessEngineResultCode,
        message: String,
    },
    Jni(String),
    InvalidArgument(String),
    InvalidUtf8(String),
}

impl BridgeError {
    pub(crate) const fn code(&self) -> ChessEngineResultCode {
        match self {
            Self::Abi { code, .. } => *code,
            Self::Jni(_) | Self::InvalidUtf8(_) => ChessEngineResultCode::InternalError,
            Self::InvalidArgument(_) => ChessEngineResultCode::InvalidArgument,
        }
    }
}

impl fmt::Display for BridgeError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Abi { message, .. }
            | Self::Jni(message)
            | Self::InvalidArgument(message)
            | Self::InvalidUtf8(message) => formatter.write_str(message),
        }
    }
}

impl From<jni::errors::Error> for BridgeError {
    fn from(value: jni::errors::Error) -> Self {
        Self::Jni(format!("JNI operation failed: {value}"))
    }
}

pub(crate) type BridgeResult<T> = Result<T, BridgeError>;

pub(crate) fn boundary<T, F>(env: &mut JNIEnv<'_>, fallback: T, operation: F) -> T
where
    T: Copy,
    F: FnOnce(&mut JNIEnv<'_>) -> BridgeResult<T>,
{
    match std::panic::catch_unwind(AssertUnwindSafe(|| operation(env))) {
        Ok(Ok(value)) => value,
        Ok(Err(error)) => {
            throw_bridge_error(env, &error);
            fallback
        }
        Err(_) => {
            throw_bridge_error(
                env,
                &BridgeError::Abi {
                    code: ChessEngineResultCode::Panic,
                    message: "Rust panic was contained at the Android JNI boundary".to_owned(),
                },
            );
            fallback
        }
    }
}

fn throw_bridge_error(env: &mut JNIEnv<'_>, error: &BridgeError) {
    if env.exception_check().unwrap_or(false) {
        return;
    }

    let message = error.to_string();
    let exception = (|| -> Result<JObject<'_>, jni::errors::Error> {
        let java_message = env.new_string(&message)?;
        let message_object = JObject::from(java_message);
        env.new_object(
            EXCEPTION_CLASS,
            "(ILjava/lang/String;)V",
            &[
                JValue::Int(error.code() as jint),
                JValue::Object(&message_object),
            ],
        )
    })();

    match exception {
        Ok(value) => {
            let _ = env.throw(value);
        }
        Err(_) => {
            let _ = env.exception_clear();
            let _ = env.throw_new(
                "java/lang/RuntimeException",
                format!("native chess engine error {}: {message}", error.code() as i32),
            );
        }
    }
}

pub(crate) fn token_from_jlong(value: jlong) -> u64 {
    value as u64
}

pub(crate) fn token_to_jlong(value: u64) -> jlong {
    value as jlong
}

pub(crate) fn java_string(env: &mut JNIEnv<'_>, value: JString<'_>) -> BridgeResult<String> {
    if value.is_null() {
        return Err(BridgeError::Abi {
            code: ChessEngineResultCode::NullPointer,
            message: "Java string argument is null".to_owned(),
        });
    }
    Ok(env.get_string(&value)?.into())
}

pub(crate) fn output_string(env: &mut JNIEnv<'_>, value: &str) -> BridgeResult<jstring> {
    Ok(env.new_string(value)?.into_raw())
}

fn buffer_bytes(buffer: &ChessEngineBuffer) -> BridgeResult<Vec<u8>> {
    if buffer.len == 0 {
        if !buffer.data.is_null() || buffer.allocation != 0 {
            return Err(BridgeError::InvalidUtf8(
                "ABI returned an inconsistent empty buffer".to_owned(),
            ));
        }
        return Ok(Vec::new());
    }
    if buffer.data.is_null() || buffer.allocation == 0 {
        return Err(BridgeError::InvalidUtf8(
            "ABI returned an inconsistent nonempty buffer".to_owned(),
        ));
    }
    // SAFETY: A successful C ABI call guarantees exactly `len` readable bytes
    // while the allocation token remains live. The bytes are copied before free.
    Ok(unsafe { slice::from_raw_parts(buffer.data, buffer.len) }.to_vec())
}

fn raw_last_error_message() -> String {
    let mut buffer = ChessEngineBuffer::empty();
    // SAFETY: `buffer` is a fresh writable output record.
    let code = unsafe { chess_engine_last_error_message(&mut buffer) };
    if code != ChessEngineResultCode::Ok {
        return format!("native operation failed with result code {}", code as i32);
    }
    let bytes = buffer_bytes(&buffer).unwrap_or_default();
    // SAFETY: `buffer` is the unchanged live record returned above.
    let free_code = unsafe { chess_engine_buffer_free(&mut buffer) };
    let message = String::from_utf8_lossy(&bytes).into_owned();
    if free_code == ChessEngineResultCode::Ok {
        message
    } else {
        format!(
            "{message}; error-buffer cleanup failed with result code {}",
            free_code as i32
        )
    }
}

fn ensure_code(code: ChessEngineResultCode) -> BridgeResult<()> {
    if code == ChessEngineResultCode::Ok {
        return Ok(());
    }
    Err(BridgeError::Abi {
        code,
        message: raw_last_error_message(),
    })
}

fn take_buffer<F>(operation: F) -> BridgeResult<Vec<u8>>
where
    F: FnOnce(*mut ChessEngineBuffer) -> ChessEngineResultCode,
{
    let mut buffer = ChessEngineBuffer::empty();
    ensure_code(operation(&mut buffer))?;
    let bytes = buffer_bytes(&buffer);
    // SAFETY: The record is unchanged after the successful producer call.
    let free_result = unsafe { chess_engine_buffer_free(&mut buffer) };
    ensure_code(free_result)?;
    bytes
}

fn take_text<F>(operation: F) -> BridgeResult<String>
where
    F: FnOnce(*mut ChessEngineBuffer) -> ChessEngineResultCode,
{
    let bytes = take_buffer(operation)?;
    String::from_utf8(bytes).map_err(|error| {
        BridgeError::InvalidUtf8(format!("native output was not valid UTF-8: {error}"))
    })
}

pub(crate) fn version() -> BridgeResult<String> {
    take_text(|output| {
        // SAFETY: `output` points to a fresh writable buffer record.
        unsafe { chess_engine_version(output) }
    })
}

pub(crate) fn create_engine(transposition_table_mebibytes: jlong) -> BridgeResult<jlong> {
    let table_size = u64::try_from(transposition_table_mebibytes).map_err(|_| {
        BridgeError::InvalidArgument(
            "transposition-table budget must be a positive signed 64-bit value".to_owned(),
        )
    })?;
    if table_size == 0 {
        return Err(BridgeError::InvalidArgument(
            "transposition-table budget must be greater than zero".to_owned(),
        ));
    }

    let mut config = ChessEngineConfig::new();
    config.transposition_table_mebibytes = table_size;
    let mut handle: ChessEngineHandle = CHESS_ENGINE_NULL_HANDLE;
    // SAFETY: Both records are initialized and valid for the duration of the call.
    ensure_code(unsafe { chess_engine_create(&config, &mut handle) })?;
    Ok(token_to_jlong(handle))
}

pub(crate) fn destroy_engine(handle: jlong) -> BridgeResult<()> {
    ensure_code(chess_engine_destroy(token_from_jlong(handle)))
}

pub(crate) fn reset_position(handle: jlong) -> BridgeResult<()> {
    ensure_code(chess_engine_reset_position(token_from_jlong(handle)))
}

pub(crate) fn set_position(handle: jlong, fen: &str) -> BridgeResult<()> {
    // SAFETY: `fen` remains readable for the explicit byte length during the call.
    ensure_code(unsafe {
        chess_engine_set_position(token_from_jlong(handle), fen.as_ptr(), fen.len())
    })
}

pub(crate) fn fen(handle: jlong) -> BridgeResult<String> {
    take_text(|output| {
        // SAFETY: `output` points to a fresh writable buffer record.
        unsafe { chess_engine_get_fen(token_from_jlong(handle), output) }
    })
}

pub(crate) fn legal_moves(handle: jlong) -> BridgeResult<String> {
    take_text(|output| {
        // SAFETY: `output` points to a fresh writable buffer record.
        unsafe { chess_engine_get_legal_moves(token_from_jlong(handle), output) }
    })
}

pub(crate) fn play_move(handle: jlong, move_text: &str) -> BridgeResult<()> {
    // SAFETY: `move_text` remains readable for the explicit byte length during the call.
    ensure_code(unsafe {
        chess_engine_play_move(
            token_from_jlong(handle),
            move_text.as_ptr(),
            move_text.len(),
        )
    })
}

pub(crate) fn game_status(handle: jlong) -> BridgeResult<String> {
    let mut status = ChessEngineGameStatus::new();
    // SAFETY: `status` is writable for one complete current-version record.
    ensure_code(unsafe { chess_engine_get_game_status(token_from_jlong(handle), &mut status) })?;
    Ok(format!(
        "{},{},{}",
        status.kind as i32, status.winner as i32, status.draw_reason as i32
    ))
}

pub(crate) fn weight_identity(handle: jlong) -> BridgeResult<String> {
    let mut identity = ChessEngineWeightIdentity::new();
    // SAFETY: `identity` is writable for one complete current-version record.
    ensure_code(unsafe {
        chess_engine_get_weight_identity(token_from_jlong(handle), &mut identity)
    })?;
    Ok(format!(
        "{},{},{}",
        identity.schema_version, identity.identifier, identity.checksum
    ))
}

pub(crate) fn create_cancellation() -> BridgeResult<jlong> {
    let mut handle: ChessEngineCancellationHandle = CHESS_ENGINE_NULL_CANCELLATION_HANDLE;
    // SAFETY: `handle` is writable for one cancellation token.
    ensure_code(unsafe { chess_engine_cancellation_create(&mut handle) })?;
    Ok(token_to_jlong(handle))
}

pub(crate) fn destroy_cancellation(handle: jlong) -> BridgeResult<()> {
    ensure_code(chess_engine_cancellation_destroy(token_from_jlong(handle)))
}

pub(crate) fn cancel(handle: jlong) -> BridgeResult<()> {
    ensure_code(chess_engine_cancellation_cancel(token_from_jlong(handle)))
}

pub(crate) fn reset_cancellation(handle: jlong) -> BridgeResult<()> {
    ensure_code(chess_engine_cancellation_reset(token_from_jlong(handle)))
}

pub(crate) fn cancellation_is_cancelled(handle: jlong) -> BridgeResult<jboolean> {
    let mut cancelled = 0_u8;
    // SAFETY: `cancelled` is writable for one byte.
    ensure_code(unsafe {
        chess_engine_cancellation_is_cancelled(token_from_jlong(handle), &mut cancelled)
    })?;
    Ok(if cancelled == 0 { JNI_FALSE } else { JNI_TRUE })
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub(crate) struct SearchArguments {
    pub depth: jint,
    pub nodes: jlong,
    pub soft_time_milliseconds: jlong,
    pub hard_time_milliseconds: jlong,
    pub infinite: jboolean,
    pub check_extension: jboolean,
    pub cancellation_handle: jlong,
}

fn search_request(arguments: SearchArguments) -> BridgeResult<ChessEngineSearchRequest> {
    let mut request = ChessEngineSearchRequest::new();

    if arguments.depth < 0 {
        return Err(BridgeError::InvalidArgument(
            "search depth cannot be negative".to_owned(),
        ));
    }
    if arguments.depth > 0 {
        request.depth = u16::try_from(arguments.depth).map_err(|_| {
            BridgeError::InvalidArgument("search depth exceeds the supported range".to_owned())
        })?;
        request.flags |= CHESS_ENGINE_SEARCH_FLAG_DEPTH;
    }

    for (value, label) in [
        (arguments.nodes, "node limit"),
        (arguments.soft_time_milliseconds, "soft time"),
        (arguments.hard_time_milliseconds, "hard time"),
    ] {
        if value < 0 {
            return Err(BridgeError::InvalidArgument(format!(
                "search {label} cannot be negative"
            )));
        }
    }

    if arguments.nodes > 0 {
        request.nodes = arguments.nodes as u64;
        request.flags |= CHESS_ENGINE_SEARCH_FLAG_NODES;
    }
    if arguments.soft_time_milliseconds > 0 {
        request.soft_time_milliseconds = arguments.soft_time_milliseconds as u64;
        request.flags |= CHESS_ENGINE_SEARCH_FLAG_SOFT_TIME;
    }
    if arguments.hard_time_milliseconds > 0 {
        request.hard_time_milliseconds = arguments.hard_time_milliseconds as u64;
        request.flags |= CHESS_ENGINE_SEARCH_FLAG_HARD_TIME;
    }
    if arguments.infinite != JNI_FALSE {
        request.flags |= CHESS_ENGINE_SEARCH_FLAG_INFINITE;
    }
    if arguments.check_extension != JNI_FALSE {
        request.flags |= CHESS_ENGINE_SEARCH_FLAG_CHECK_EXTENSION;
    }
    if arguments.cancellation_handle != 0 {
        request.cancellation_handle = token_from_jlong(arguments.cancellation_handle);
        request.flags |= CHESS_ENGINE_SEARCH_FLAG_CANCELLATION;
    }

    Ok(request)
}

fn copied_text(buffer: &ChessEngineBuffer, label: &str) -> BridgeResult<String> {
    String::from_utf8(buffer_bytes(buffer)?).map_err(|error| {
        BridgeError::InvalidUtf8(format!("native {label} was not valid UTF-8: {error}"))
    })
}

pub(crate) fn search(handle: jlong, arguments: SearchArguments) -> BridgeResult<String> {
    let request = search_request(arguments)?;
    let mut result = ChessEngineSearchResult::new();
    // SAFETY: Request and result records are complete and live for the call.
    ensure_code(unsafe {
        chess_engine_search(token_from_jlong(handle), &request, &mut result)
    })?;

    let best_move = copied_text(&result.best_move, "best move");
    let ponder_move = copied_text(&result.ponder_move, "ponder move");
    let principal_variation = copied_text(&result.principal_variation, "principal variation");

    // SAFETY: `result` is the unchanged current-version record returned above.
    let free_result = unsafe { chess_engine_search_result_free(&mut result) };
    ensure_code(free_result)?;

    let fields = [
        best_move?,
        ponder_move?,
        principal_variation?,
        (result.score_kind as i32).to_string(),
        result.score_value.to_string(),
        result.completed_depth.to_string(),
        result.selective_depth.to_string(),
        (result.termination_kind as i32).to_string(),
        (result.fallback_kind as i32).to_string(),
        result.termination_value.to_string(),
        result.nodes.to_string(),
        result.qnodes.to_string(),
        result.elapsed_milliseconds.to_string(),
    ];
    Ok(fields.join("\n"))
}

pub(crate) fn null_jstring() -> jstring {
    ptr::null_mut()
}

#[cfg(test)]
mod tests {
    use super::{search_request, token_from_jlong, token_to_jlong, SearchArguments};
    use chess_ffi::c_abi::{
        CHESS_ENGINE_SEARCH_FLAG_CANCELLATION, CHESS_ENGINE_SEARCH_FLAG_CHECK_EXTENSION,
        CHESS_ENGINE_SEARCH_FLAG_DEPTH, CHESS_ENGINE_SEARCH_FLAG_HARD_TIME,
        CHESS_ENGINE_SEARCH_FLAG_INFINITE, CHESS_ENGINE_SEARCH_FLAG_NODES,
        CHESS_ENGINE_SEARCH_FLAG_SOFT_TIME,
    };
    use jni::sys::{JNI_FALSE, JNI_TRUE};

    #[test]
    fn opaque_tokens_round_trip_all_bits_through_signed_jlong() {
        for token in [0_u64, 1, i64::MAX as u64, u64::MAX, 0xA55A_0123_4567_89AB] {
            assert_eq!(token_from_jlong(token_to_jlong(token)), token);
        }
    }

    #[test]
    fn search_arguments_map_to_exact_c_abi_flags_and_values() {
        let request = search_request(SearchArguments {
            depth: 7,
            nodes: 50_000,
            soft_time_milliseconds: 250,
            hard_time_milliseconds: 500,
            infinite: JNI_TRUE,
            check_extension: JNI_TRUE,
            cancellation_handle: token_to_jlong(0xA55A_0000_0000_0042),
        })
        .expect("valid JNI search arguments map to a C ABI request");

        assert_eq!(
            request.flags,
            CHESS_ENGINE_SEARCH_FLAG_DEPTH
                | CHESS_ENGINE_SEARCH_FLAG_NODES
                | CHESS_ENGINE_SEARCH_FLAG_SOFT_TIME
                | CHESS_ENGINE_SEARCH_FLAG_HARD_TIME
                | CHESS_ENGINE_SEARCH_FLAG_INFINITE
                | CHESS_ENGINE_SEARCH_FLAG_CHECK_EXTENSION
                | CHESS_ENGINE_SEARCH_FLAG_CANCELLATION
        );
        assert_eq!(request.depth, 7);
        assert_eq!(request.nodes, 50_000);
        assert_eq!(request.soft_time_milliseconds, 250);
        assert_eq!(request.hard_time_milliseconds, 500);
        assert_eq!(request.cancellation_handle, 0xA55A_0000_0000_0042);
    }

    #[test]
    fn zero_search_values_remain_absent() {
        let request = search_request(SearchArguments {
            depth: 0,
            nodes: 0,
            soft_time_milliseconds: 0,
            hard_time_milliseconds: 0,
            infinite: JNI_FALSE,
            check_extension: JNI_FALSE,
            cancellation_handle: 0,
        })
        .expect("zero values create the intentionally incomplete request");
        assert_eq!(request.flags, 0);
    }
}
