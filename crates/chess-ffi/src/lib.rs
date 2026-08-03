//! Safe engine facade and stable C ABI boundary.
//!
//! Task 18.1 exposes a process-independent, ownership-explicit Rust API over
//! `chess-core` and `chess-search`. Task 18.2 adds a narrow C adapter with opaque
//! handles, versioned records, length-delimited UTF-8, owned output buffers,
//! structured result codes, and panic containment without exposing Rust layouts.

pub mod c_abi;
mod safe;

pub use safe::{
    Engine, EngineConfig, EngineError, EvaluationWeightIdentity, SearchCancellationHandle,
    SearchRequest, ENGINE_VERSION,
};

pub use chess_core::{Color, DrawReason, GameStatus};
pub use chess_search::{Score, SearchCancellationFallback, SearchLimitTermination, SearchResult};
