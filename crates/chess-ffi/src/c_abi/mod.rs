//! Stable C ABI over the safe Rust engine facade.
//!
//! The ABI exposes versioned `repr(C)` records, opaque numeric tokens, explicit
//! UTF-8 lengths, structured result codes, registry-owned output buffers, and
//! panic containment. Rust engine and search layouts never cross this boundary.

mod functions;
mod registry;
mod types;

pub use functions::*;
pub use types::*;

#[cfg(test)]
mod tests {
    use super::{registry::force_boundary_panic_for_test, ChessEngineResultCode};

    #[test]
    fn shared_boundary_contains_panics() {
        assert_eq!(
            force_boundary_panic_for_test(),
            ChessEngineResultCode::Panic
        );
    }
}
