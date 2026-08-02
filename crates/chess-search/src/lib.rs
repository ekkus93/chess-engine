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

#[cfg(test)]
mod core_api_tests {
    use chess_core::Position;

    use crate::evaluate;

    #[test]
    fn public_legal_token_api_supports_search_crate_make_unmake() {
        let mut position = Position::starting();
        let snapshot = position.clone();
        let token = position
            .legal_move_tokens()
            .expect("legal tokens")
            .iter()
            .find(|token| token.move_made().to_uci() == "e2e4")
            .expect("e2e4 token");

        let undo = position.make_legal_token(token).expect("token applies");
        let _child_score = evaluate(&position);
        position.unmake_move(undo).expect("token move unmakes");

        assert_eq!(position, snapshot);
        assert_eq!(position.zobrist(), position.recomputed_zobrist());
    }
}
