#!/usr/bin/env python3
from pathlib import Path

path = Path("crates/chess-jni/src/bridge.rs")
text = path.read_text()

replacements = [
    (
        "objects::{JObject, JString, JValue}",
        "objects::{JObject, JString, JThrowable, JValue}",
    ),
    (
        "let _ = env.throw(value);",
        "let _ = env.throw(JThrowable::from(value));",
    ),
    (
        "use chess_ffi::c_abi::{\n        CHESS_ENGINE_SEARCH_FLAG_CANCELLATION,",
        "use chess_ffi::c_abi::{\n        ChessEngineResultCode, CHESS_ENGINE_SEARCH_FLAG_CANCELLATION,",
    ),
]

for old, new in replacements:
    if text.count(old) != 1:
        raise SystemExit(f"expected exactly one occurrence: {old!r}")
    text = text.replace(old, new)

path.write_text(text)
