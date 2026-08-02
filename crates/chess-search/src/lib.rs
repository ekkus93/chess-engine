#![forbid(unsafe_code)]
//! Portable classical evaluation and search.
//!
//! This crate may depend on `chess-core` only. It must remain independent of
//! UCI, FFI, JNI, Android, filesystems, and application user interfaces.

mod evaluation;
mod score;
mod weights;

pub use evaluation::{
    evaluate, evaluate_term, evaluate_trace, evaluate_trace_with_weights, evaluate_with_weights,
    EvaluationTerm, EvaluationTrace,
};
pub use score::{Score, MATE_SCORE, MAX_EVALUATION, MAX_MATE_PLY};
pub use weights::{
    EvaluationWeightSet, EvaluationWeights, PhasedWeight, WeightValidationError,
    BASELINE_WEIGHT_SET_ID, EVALUATION_WEIGHT_SCHEMA_VERSION, WEIGHT_VALUE_COUNT,
};
