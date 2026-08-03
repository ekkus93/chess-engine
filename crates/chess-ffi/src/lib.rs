//! Safe engine facade and future stable C ABI boundary.
//!
//! Task 18.1 exposes a process-independent, ownership-explicit Rust API over
//! `chess-core` and `chess-search`. Task 18.2 will add opaque C handles and
//! serialization helpers around this facade without exposing Rust layouts.

mod safe;

pub use safe::{
    Engine, EngineConfig, EngineError, EvaluationWeightIdentity, SearchCancellationHandle,
    SearchRequest, ENGINE_VERSION,
};

pub use chess_core::{Color, DrawReason, GameStatus};
pub use chess_search::{Score, SearchCancellationFallback, SearchLimitTermination, SearchResult};
