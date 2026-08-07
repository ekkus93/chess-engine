from pathlib import Path

path = Path("crates/chess-jni/src/bridge.rs")
text = path.read_text()


def replace_once(old: str, new: str, label: str) -> None:
    global text
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one match, found {count}")
    text = text.replace(old, new, 1)


replace_once(
'''fn throw_bridge_error(env: &mut JNIEnv<'_>, error: &BridgeError) {
    if env.exception_check().unwrap_or(false) {
        return;
    }

    let message = error.to_string();
''',
'''fn throw_bridge_error(env: &mut JNIEnv<'_>, error: &BridgeError) {
    match env.exception_check() {
        Ok(true) => return,
        Ok(false) => {}
        Err(check_error) => {
            let message = format!(
                "failed to inspect pending JNI exception while reporting native chess engine error {}: {error}; JNI exception check failed: {check_error}",
                error.code() as i32
            );
            let _ = env.throw_new("java/lang/RuntimeException", message);
            return;
        }
    }

    let message = error.to_string();
''',
"JNI exception check",
)

replace_once(
'''fn raw_last_error_message() -> String {
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
''',
'''fn decode_last_error_bytes(operation_code: ChessEngineResultCode, bytes: Vec<u8>) -> String {
    match String::from_utf8(bytes) {
        Ok(message) if !message.is_empty() => message,
        Ok(_) => format!(
            "native operation failed with result code {}; last-error lookup returned an empty message",
            operation_code as i32
        ),
        Err(error) => format!(
            "native operation failed with result code {}; last-error message was not valid UTF-8: {error}",
            operation_code as i32
        ),
    }
}

fn raw_last_error_message(operation_code: ChessEngineResultCode) -> String {
    let mut buffer = ChessEngineBuffer::empty();
    // SAFETY: `buffer` is a fresh writable output record.
    let lookup_code = unsafe { chess_engine_last_error_message(&mut buffer) };
    if lookup_code != ChessEngineResultCode::Ok {
        return format!(
            "native operation failed with result code {}; last-error lookup failed with result code {}",
            operation_code as i32, lookup_code as i32
        );
    }

    let bytes = buffer_bytes(&buffer);
    // SAFETY: `buffer` is the unchanged record returned by the last-error lookup.
    // The C ABI validates the allocation token before releasing registry storage.
    let free_code = unsafe { chess_engine_buffer_free(&mut buffer) };
    let message = match bytes {
        Ok(bytes) => decode_last_error_bytes(operation_code, bytes),
        Err(error) => format!(
            "native operation failed with result code {}; last-error buffer was invalid: {error}",
            operation_code as i32
        ),
    };

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
        message: raw_last_error_message(code),
    })
}
''',
"strict last-error retrieval",
)

replace_once(
'''mod tests {
    use super::{search_request, token_from_jlong, token_to_jlong, SearchArguments};
    use chess_ffi::c_abi::{
        ChessEngineResultCode, CHESS_ENGINE_SEARCH_FLAG_CANCELLATION,
''',
'''mod tests {
    use core::ptr::NonNull;

    use super::{
        buffer_bytes, decode_last_error_bytes, search_request, token_from_jlong, token_to_jlong,
        SearchArguments,
    };
    use chess_ffi::c_abi::{
        ChessEngineBuffer, ChessEngineResultCode, CHESS_ENGINE_SEARCH_FLAG_CANCELLATION,
''',
"test imports",
)

replace_once(
'''    #[test]
    fn opaque_tokens_round_trip_all_bits_through_signed_jlong() {
''',
'''    #[test]
    fn last_error_diagnostics_reject_empty_and_invalid_utf8() {
        assert_eq!(
            decode_last_error_bytes(ChessEngineResultCode::InvalidFen, b"invalid FEN".to_vec()),
            "invalid FEN"
        );

        let empty = decode_last_error_bytes(ChessEngineResultCode::InvalidFen, Vec::new());
        assert!(empty.contains("result code 10"));
        assert!(empty.contains("empty message"));

        let invalid =
            decode_last_error_bytes(ChessEngineResultCode::InvalidFen, vec![0x66, 0x80, 0x6f]);
        assert!(invalid.contains("result code 10"));
        assert!(invalid.contains("last-error message was not valid UTF-8"));
    }

    #[test]
    fn malformed_native_buffers_are_rejected_without_dereference() {
        let inconsistent_empty = ChessEngineBuffer {
            data: NonNull::<u8>::dangling().as_ptr(),
            len: 0,
            allocation: 1,
        };
        let error = buffer_bytes(&inconsistent_empty)
            .expect_err("non-null empty buffers must be rejected explicitly");
        assert_eq!(error.code(), ChessEngineResultCode::InternalError);
        assert!(error.to_string().contains("inconsistent empty buffer"));

        let inconsistent_nonempty = ChessEngineBuffer {
            data: core::ptr::null(),
            len: 1,
            allocation: 1,
        };
        let error = buffer_bytes(&inconsistent_nonempty)
            .expect_err("null nonempty buffers must be rejected explicitly");
        assert_eq!(error.code(), ChessEngineResultCode::InternalError);
        assert!(error.to_string().contains("inconsistent nonempty buffer"));
    }

    #[test]
    fn opaque_tokens_round_trip_all_bits_through_signed_jlong() {
''',
"JNI diagnostic regression tests",
)

for forbidden in ["exception_check().unwrap_or(false)", "buffer_bytes(&buffer).unwrap_or_default()", "String::from_utf8_lossy(&bytes)"]:
    if forbidden in text:
        raise SystemExit(f"silent JNI fallback remains: {forbidden}")

path.write_text(text)
