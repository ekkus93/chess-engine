//! Test-only exported faults for ABI panic-containment validation.

use super::{
    registry::{boundary, AbiResult},
    ChessEngineResultCode,
};

/// Injects a panic inside the shared C ABI boundary.
///
/// This symbol is compiled only with the non-default `ffi-test-faults` Cargo
/// feature. It exists solely for Task 18.3 smoke testing and is not part of the
/// production ABI surface.
#[no_mangle]
pub extern "C" fn chess_engine_test_inject_panic() -> ChessEngineResultCode {
    boundary(|| -> AbiResult<()> { panic!("injected test-only C ABI panic") })
}
