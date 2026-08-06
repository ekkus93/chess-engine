#![forbid(unsafe_code)]
//! Portable classical evaluation and search.
//!
//! This crate may depend on `chess-core` only. It must remain independent of
//! UCI, FFI, JNI, Android, filesystems, and application user interfaces.

mod alpha_beta;
mod aspiration;
mod cancellation;
mod check_extension;
mod diagnostics;
mod evaluation;
mod iterative_deepening;
mod limits;
mod move_ordering;
mod principal_variation;
mod quiescence;
mod reference;
mod score;
mod search_common;
mod search_policy;
mod transposition;
mod transposition_score;
mod weights;

pub use alpha_beta::{
    alpha_beta_search, alpha_beta_search_with_cancellation,
    alpha_beta_search_with_cancellation_and_transposition_table,
    alpha_beta_search_with_transposition_table, AlphaBetaSearchError, AlphaBetaSearchResult,
    DEFAULT_TRANSPOSITION_TABLE_MEBIBYTES,
};
pub use aspiration::{
    AspirationWindowAttempt, AspirationWindowDiagnostics, AspirationWindowOutcome,
    DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS,
};
pub use cancellation::{SearchCancellationProbe, CANCELLATION_CHECK_INTERVAL_NODES};
pub use check_extension::{
    CheckExtensionDiagnostics, CheckExtensionEvent, MAX_CHECK_EXTENSIONS_PER_LINE,
};
pub use diagnostics::{
    NullMoveDisabledReason, SearchDiagnosticCounter, SearchDiagnosticEvent,
    SearchDiagnosticOverflow, SearchDiagnostics,
};
pub use evaluation::{
    evaluate, evaluate_term, evaluate_trace, evaluate_trace_with_weights, evaluate_with_weights,
    EvaluationTerm, EvaluationTrace,
};
pub use iterative_deepening::{
    iterative_deepening_search, iterative_deepening_search_with_limits,
    iterative_deepening_search_with_limits_and_transposition_table,
    iterative_deepening_search_with_limits_and_transposition_table_and_observer,
    iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights,
    iterative_deepening_search_with_limits_and_transposition_table_and_weights,
    iterative_deepening_search_with_transposition_table, IterativeDeepeningIteration,
    IterativeDeepeningSearchError, IterativeDeepeningSearchResult,
    LimitedIterativeDeepeningSearchResult, SearchCancellationFallback, SearchProgress,
    SearchResult,
};
pub use limits::{SearchLimitError, SearchLimitTermination, SearchLimits, SearchStopFlag};
pub use principal_variation::{
    PrincipalVariation, PrincipalVariationError, PrincipalVariationTermination,
};
pub use quiescence::{
    quiescence_search, quiescence_search_with_cancellation, quiescence_search_with_limit,
    QuiescenceSearchResult, DELTA_PRUNING_MARGIN_CENTIPAWNS, MAX_QUIESCENCE_PLY,
    SEE_QUIESCENCE_PRUNE_THRESHOLD_CENTIPAWNS,
};
pub use reference::{
    reference_search, reference_search_with_cancellation, reference_search_with_quiescence,
    reference_search_with_quiescence_and_cancellation, ReferenceSearchError, ReferenceSearchResult,
};
pub use score::{Score, MATE_SCORE, MAX_EVALUATION, MAX_MATE_PLY};
pub use search_policy::{
    AlphaBetaMode, ExperimentalSearchFeature, ExperimentalSearchFeatures, MoveOrderingPolicy,
    QuiescencePolicy, SearchPolicy, SearchPolicyParameters, SearchPolicySet,
    SearchPolicyValidationError, TranspositionPolicy, FUTILITY_PRUNING_MARGIN_CENTIPAWNS,
    FUTILITY_PRUNING_MAXIMUM_DEPTH, FUTILITY_PRUNING_SEARCH_POLICY_ID,
    LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID, LMR_MINIMUM_DEPTH, LMR_MINIMUM_LEGAL_MOVES,
    LMR_MINIMUM_MOVE_INDEX, LMR_MINIMUM_TOTAL_PIECES, LMR_REDUCTION_TABLE,
    MAXIMUM_ASPIRATION_HALF_WIDTH_CENTIPAWNS, MAXIMUM_CHECK_EXTENSIONS_PER_LINE,
    NULL_MOVE_MINIMUM_DEPTH, NULL_MOVE_MINIMUM_SIDE_NON_PAWN_PIECES,
    NULL_MOVE_MINIMUM_TOTAL_NON_PAWN_PIECES, NULL_MOVE_PRUNING_SEARCH_POLICY_ID,
    NULL_MOVE_REDUCTION, NULL_MOVE_VERIFICATION_REDUCTION, NULL_MOVE_VERIFY_ALL_CUTOFFS,
    PRINCIPAL_VARIATION_SEARCH_POLICY_ID, SEARCH_POLICY_SCHEMA_VERSION,
    SEE_AND_DELTA_QUIESCENCE_PRUNING_SEARCH_POLICY_ID, SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID,
    SEE_QUIESCENCE_PRUNING_SEARCH_POLICY_ID, V0_1_SEARCH_POLICY_CHECKSUM, V0_1_SEARCH_POLICY_ID,
};
pub use transposition::{
    TranspositionBound, TranspositionEntry, TranspositionHashFull, TranspositionProbeError,
    TranspositionProbeRequest, TranspositionProbeResult, TranspositionProbeScore,
    TranspositionScore, TranspositionScoreReuse, TranspositionStoreAction,
    TranspositionStoreResult, TranspositionTable, TranspositionTableAllocationError,
    TranspositionTableDiagnostics, TRANSPOSITION_CLUSTER_SIZE,
    TRANSPOSITION_HASH_FULL_SAMPLE_LIMIT,
};
pub use transposition_score::TranspositionScoreConversionError;
pub use weights::{
    EvaluationStructure, EvaluationWeightSet, EvaluationWeights, PhasedWeight,
    StructuralWeightField, WeightValidationError, BASELINE_WEIGHT_SET_ID, EVALUATION_STRUCTURE,
    EVALUATION_STRUCTURE_SCHEMA_VERSION, EVALUATION_WEIGHT_SCHEMA_VERSION, WEIGHT_VALUE_COUNT,
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
