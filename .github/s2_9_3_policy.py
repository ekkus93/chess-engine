#!/usr/bin/env python3
from __future__ import annotations

import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise RuntimeError(f"{label}: expected one occurrence, found {count}")
    return text.replace(old, new, 1)


def phase1() -> None:
    diagnostics_path = "crates/chess-search/src/diagnostics.rs"
    diagnostics = read(diagnostics_path)
    diagnostics = replace_once(
        diagnostics,
        "/// One bounded deterministic search counter.\n",
        """/// Stable reason why an S2-9 null-move attempt was disabled.\n#[derive(Clone, Copy, Debug, Eq, PartialEq)]\npub enum NullMoveDisabledReason {\n    /// Root nodes never prune by a synthetic pass.\n    Root,\n    /// The side to move is checked.\n    InCheck,\n    /// Remaining depth is below the frozen minimum.\n    ShallowDepth,\n    /// The position has too little non-pawn material for the pass assumption.\n    LowNonPawnMaterial,\n    /// The node is already inside a speculative or verification subtree.\n    NestedOrVerification,\n    /// Mate-score bounds or mate-domain proximity make pruning unsafe.\n    MateSensitive,\n    /// Static evaluation does not already meet beta.\n    StaticEvaluationBelowBeta,\n}\n\nimpl NullMoveDisabledReason {\n    /// Stable machine-readable reason name.\n    #[must_use]\n    pub const fn name(self) -> &'static str {\n        match self {\n            Self::Root => \"root\",\n            Self::InCheck => \"in_check\",\n            Self::ShallowDepth => \"shallow_depth\",\n            Self::LowNonPawnMaterial => \"low_non_pawn_material\",\n            Self::NestedOrVerification => \"nested_or_verification\",\n            Self::MateSensitive => \"mate_sensitive\",\n            Self::StaticEvaluationBelowBeta => \"static_evaluation_below_beta\",\n        }\n    }\n}\n\n/// One bounded deterministic search counter.\n""",
        "insert null disabled reason",
    )
    diagnostics = replace_once(
        diagnostics,
        "    NullMoveAttempts,\n    NullMoveCutoffs,\n",
        "    NullMoveAttempts,\n    NullMoveDisabledNodes,\n    NullMoveSpeculativeFailHighs,\n    NullMoveVerificationSearches,\n    NullMoveCutoffs,\n",
        "diagnostic counter variants",
    )
    diagnostics = replace_once(
        diagnostics,
        "            Self::NullMoveAttempts => \"null_move_attempts\",\n            Self::NullMoveCutoffs => \"null_move_cutoffs\",\n",
        "            Self::NullMoveAttempts => \"null_move_attempts\",\n            Self::NullMoveDisabledNodes => \"null_move_disabled_nodes\",\n            Self::NullMoveSpeculativeFailHighs => \"null_move_speculative_fail_highs\",\n            Self::NullMoveVerificationSearches => \"null_move_verification_searches\",\n            Self::NullMoveCutoffs => \"null_move_cutoffs\",\n",
        "diagnostic counter names",
    )
    diagnostics = replace_once(
        diagnostics,
        "    NullMoveAttempt,\n    NullMoveCutoff,\n",
        "    NullMoveAttempt,\n    NullMoveDisabled { reason: NullMoveDisabledReason },\n    NullMoveSpeculativeFailHigh,\n    NullMoveVerificationSearch,\n    NullMoveCutoff,\n",
        "diagnostic event variants",
    )
    diagnostics = replace_once(
        diagnostics,
        "    null_move_attempts: u64,\n    null_move_cutoffs: u64,\n",
        "    null_move_attempts: u64,\n    null_move_disabled_nodes: u64,\n    null_move_speculative_fail_highs: u64,\n    null_move_verification_searches: u64,\n    null_move_cutoffs: u64,\n",
        "diagnostic fields",
    )
    diagnostics = replace_once(
        diagnostics,
        "        null_move_attempts: 0,\n        null_move_cutoffs: 0,\n",
        "        null_move_attempts: 0,\n        null_move_disabled_nodes: 0,\n        null_move_speculative_fail_highs: 0,\n        null_move_verification_searches: 0,\n        null_move_cutoffs: 0,\n",
        "diagnostic empty fields",
    )
    diagnostics = replace_once(
        diagnostics,
        "            SearchDiagnosticEvent::NullMoveAttempt => increment_checked(\n                &mut self.null_move_attempts,\n                SearchDiagnosticCounter::NullMoveAttempts,\n            ),\n            SearchDiagnosticEvent::NullMoveCutoff => increment_checked(\n",
        "            SearchDiagnosticEvent::NullMoveAttempt => increment_checked(\n                &mut self.null_move_attempts,\n                SearchDiagnosticCounter::NullMoveAttempts,\n            ),\n            SearchDiagnosticEvent::NullMoveDisabled { reason: _ } => increment_checked(\n                &mut self.null_move_disabled_nodes,\n                SearchDiagnosticCounter::NullMoveDisabledNodes,\n            ),\n            SearchDiagnosticEvent::NullMoveSpeculativeFailHigh => increment_checked(\n                &mut self.null_move_speculative_fail_highs,\n                SearchDiagnosticCounter::NullMoveSpeculativeFailHighs,\n            ),\n            SearchDiagnosticEvent::NullMoveVerificationSearch => increment_checked(\n                &mut self.null_move_verification_searches,\n                SearchDiagnosticCounter::NullMoveVerificationSearches,\n            ),\n            SearchDiagnosticEvent::NullMoveCutoff => increment_checked(\n",
        "diagnostic event recording",
    )
    diagnostics = replace_once(
        diagnostics,
        "            null_move_attempts: sum!(null_move_attempts, NullMoveAttempts),\n            null_move_cutoffs: sum!(null_move_cutoffs, NullMoveCutoffs),\n",
        "            null_move_attempts: sum!(null_move_attempts, NullMoveAttempts),\n            null_move_disabled_nodes: sum!(null_move_disabled_nodes, NullMoveDisabledNodes),\n            null_move_speculative_fail_highs: sum!(\n                null_move_speculative_fail_highs,\n                NullMoveSpeculativeFailHighs\n            ),\n            null_move_verification_searches: sum!(\n                null_move_verification_searches,\n                NullMoveVerificationSearches\n            ),\n            null_move_cutoffs: sum!(null_move_cutoffs, NullMoveCutoffs),\n",
        "diagnostic checked add",
    )
    diagnostics = replace_once(
        diagnostics,
        "    pub const fn null_move_attempts(self) -> u64 {\n        self.null_move_attempts\n    }\n    #[must_use]\n    pub const fn null_move_cutoffs(self) -> u64 {\n",
        "    pub const fn null_move_attempts(self) -> u64 {\n        self.null_move_attempts\n    }\n    #[must_use]\n    pub const fn null_move_disabled_nodes(self) -> u64 {\n        self.null_move_disabled_nodes\n    }\n    #[must_use]\n    pub const fn null_move_speculative_fail_highs(self) -> u64 {\n        self.null_move_speculative_fail_highs\n    }\n    #[must_use]\n    pub const fn null_move_verification_searches(self) -> u64 {\n        self.null_move_verification_searches\n    }\n    #[must_use]\n    pub const fn null_move_cutoffs(self) -> u64 {\n",
        "diagnostic getters",
    )
    diagnostics = replace_once(
        diagnostics,
        "            && self.null_move_attempts == 0\n            && self.null_move_cutoffs == 0\n",
        "            && self.null_move_attempts == 0\n            && self.null_move_disabled_nodes == 0\n            && self.null_move_speculative_fail_highs == 0\n            && self.null_move_verification_searches == 0\n            && self.null_move_cutoffs == 0\n",
        "reserved diagnostics",
    )
    diagnostics = replace_once(
        diagnostics,
        "            self.null_move_attempts,\n            self.null_move_cutoffs,\n",
        "            self.null_move_attempts,\n            self.null_move_disabled_nodes,\n            self.null_move_speculative_fail_highs,\n            self.null_move_verification_searches,\n            self.null_move_cutoffs,\n",
        "diagnostic checksum",
    )
    write(diagnostics_path, diagnostics)

    probe_path = "crates/chess-search/src/transposition/probe.rs"
    probe = read(probe_path)
    probe = replace_once(
        probe,
        "    /// Cached scores are suppressed because selective-extension budget is path-dependent.\n    SuppressedForSelectiveExtension,\n",
        "    /// Cached scores are suppressed because selective-extension budget is path-dependent.\n    SuppressedForSelectiveExtension,\n    /// Cached scores are suppressed throughout a synthetic null-move subtree.\n    SuppressedForNullMove,\n",
        "TT null suppression reason",
    )
    write(probe_path, probe)

    policy_path = "crates/chess-search/src/search_policy.rs"
    policy = read(policy_path)
    policy = replace_once(
        policy,
        "/// Stable identifier for the inactive S2-8 Late Move Reductions candidate.\npub const LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID: u64 = 0x5332_384c_4d52_3031;\n",
        "/// Stable identifier for the inactive S2-8 Late Move Reductions candidate.\npub const LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID: u64 = 0x5332_384c_4d52_3031;\n/// Stable identifier for the inactive S2-9 null-move pruning candidate.\npub const NULL_MOVE_PRUNING_SEARCH_POLICY_ID: u64 = 0x5332_394e_4d50_3031;\n/// Smallest remaining depth at which null move may be considered.\npub const NULL_MOVE_MINIMUM_DEPTH: u16 = 4;\n/// Fixed speculative depth reduction after the synthetic pass ply.\npub const NULL_MOVE_REDUCTION: u16 = 2;\n/// Verification search depth reduction from the current legal node.\npub const NULL_MOVE_VERIFICATION_REDUCTION: u16 = 1;\n/// Minimum non-pawn, non-king pieces required for the side to move.\npub const NULL_MOVE_MINIMUM_SIDE_NON_PAWN_PIECES: u16 = 2;\n/// Minimum total non-pawn, non-king pieces required on the board.\npub const NULL_MOVE_MINIMUM_TOTAL_NON_PAWN_PIECES: u16 = 4;\n/// Every speculative fail-high is verified before it may cut off.\npub const NULL_MOVE_VERIFY_ALL_CUTOFFS: bool = true;\n",
        "null policy constants",
    )
    policy = replace_once(
        policy,
        "    /// Inactive S2-8 Late Move Reductions candidate.\n    pub const LATE_MOVE_REDUCTIONS: Self = Self {\n        bits: ExperimentalSearchFeature::LateMoveReductions.bit(),\n    };\n",
        "    /// Inactive S2-8 Late Move Reductions candidate.\n    pub const LATE_MOVE_REDUCTIONS: Self = Self {\n        bits: ExperimentalSearchFeature::LateMoveReductions.bit(),\n    };\n    /// Inactive S2-9 conservative null-move pruning candidate.\n    pub const NULL_MOVE_PRUNING: Self = Self {\n        bits: ExperimentalSearchFeature::NullMovePruning.bit(),\n    };\n",
        "null feature bitset",
    )
    policy = replace_once(
        policy,
        "                    | ExperimentalSearchFeature::LateMoveReductions\n",
        "                    | ExperimentalSearchFeature::LateMoveReductions\n                    | ExperimentalSearchFeature::NullMovePruning\n",
        "mark null implemented",
    )
    policy = replace_once(
        policy,
        "    /// Constructs explicit typed parameters for subsequent validation.\n",
        "    /// Inactive S2-9 candidate: baseline semantics plus conservative verified null move.\n    pub const NULL_MOVE_PRUNING: Self = Self::new(SearchPolicyParameters {\n        alpha_beta: AlphaBetaMode::FullWindowFailSoft,\n        transposition: TranspositionPolicy::ClusteredFullKey,\n        move_ordering: MoveOrderingPolicy::V0_1MvvLvaKillersHistory,\n        quiescence: QuiescencePolicy::CapturesPromotionsAndEvasions,\n        aspiration_windows: true,\n        aspiration_half_width_centipawns: DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS as u16,\n        maximum_quiescence_ply: MAX_QUIESCENCE_PLY,\n        maximum_check_extensions_per_line: MAX_CHECK_EXTENSIONS_PER_LINE,\n        experimental_features: ExperimentalSearchFeatures::NULL_MOVE_PRUNING,\n    });\n\n    /// Constructs explicit typed parameters for subsequent validation.\n",
        "null policy constant",
    )
    policy = replace_once(
        policy,
        "    /// Validates supported ranges and rejects not-yet-implemented features.\n",
        "    /// Returns whether the inactive S2-9 null-move candidate is selected.\n    #[must_use]\n    pub const fn null_move_pruning_enabled(self) -> bool {\n        self.parameters\n            .experimental_features\n            .contains(ExperimentalSearchFeature::NullMovePruning)\n    }\n\n    /// Validates supported ranges and rejects not-yet-implemented features.\n",
        "null policy getter",
    )
    policy = replace_once(
        policy,
        "        if let Some(feature) = self\n",
        "        if self.null_move_pruning_enabled()\n            && self.parameters.experimental_features.bits()\n                != ExperimentalSearchFeatures::NULL_MOVE_PRUNING.bits()\n        {\n            return Err(SearchPolicyValidationError::NullMovePruningMustBeIsolated);\n        }\n        if let Some(feature) = self\n",
        "null policy isolation validation",
    )
    policy = replace_once(
        policy,
        "    /// Returns the inactive S2-8 Late Move Reductions candidate.\n    #[must_use]\n    pub fn late_move_reductions_candidate() -> Self {\n        Self::new(\n            LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID,\n            SearchPolicy::LATE_MOVE_REDUCTIONS,\n        )\n    }\n",
        "    /// Returns the inactive S2-8 Late Move Reductions candidate.\n    #[must_use]\n    pub fn late_move_reductions_candidate() -> Self {\n        Self::new(\n            LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID,\n            SearchPolicy::LATE_MOVE_REDUCTIONS,\n        )\n    }\n\n    /// Returns the inactive S2-9 conservative null-move candidate.\n    #[must_use]\n    pub fn null_move_pruning_candidate() -> Self {\n        Self::new(\n            NULL_MOVE_PRUNING_SEARCH_POLICY_ID,\n            SearchPolicy::NULL_MOVE_PRUNING,\n        )\n    }\n",
        "null policy set constructor",
    )
    policy = replace_once(
        policy,
        "        if self.policy.late_move_reductions_enabled() {\n",
        "        if self.policy.null_move_pruning_enabled() {\n            hash = hash_bytes(hash, b\"s2-9-null-move-policy-v1\");\n            hash = hash_bytes(hash, &NULL_MOVE_MINIMUM_DEPTH.to_le_bytes());\n            hash = hash_bytes(hash, &NULL_MOVE_REDUCTION.to_le_bytes());\n            hash = hash_bytes(hash, &NULL_MOVE_VERIFICATION_REDUCTION.to_le_bytes());\n            hash = hash_bytes(\n                hash,\n                &NULL_MOVE_MINIMUM_SIDE_NON_PAWN_PIECES.to_le_bytes(),\n            );\n            hash = hash_bytes(\n                hash,\n                &NULL_MOVE_MINIMUM_TOTAL_NON_PAWN_PIECES.to_le_bytes(),\n            );\n            hash = hash_bytes(hash, &[u8::from(NULL_MOVE_VERIFY_ALL_CUTOFFS)]);\n        }\n        if self.policy.late_move_reductions_enabled() {\n",
        "null policy checksum parameters",
    )
    policy = replace_once(
        policy,
        "    /// A known future feature was enabled before its implementation task.\n    UnsupportedExperimentalFeature { feature: ExperimentalSearchFeature },\n",
        "    /// Null move was combined with another unevaluated feature.\n    NullMovePruningMustBeIsolated,\n    /// A known future feature was enabled before its implementation task.\n    UnsupportedExperimentalFeature { feature: ExperimentalSearchFeature },\n",
        "null policy validation error",
    )
    policy = replace_once(
        policy,
        "            Self::LateMoveReductionsMustBeIsolated => formatter.write_str(\n                \"late move reductions must be evaluated as an isolated policy candidate\",\n            ),\n",
        "            Self::LateMoveReductionsMustBeIsolated => formatter.write_str(\n                \"late move reductions must be evaluated as an isolated policy candidate\",\n            ),\n            Self::NullMovePruningMustBeIsolated => formatter.write_str(\n                \"null-move pruning must be evaluated as an isolated policy candidate\",\n            ),\n",
        "null policy validation display",
    )
    policy = replace_once(
        policy,
        "        SearchPolicyValidationError, LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID,\n",
        "        SearchPolicyValidationError, LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID,\n        NULL_MOVE_PRUNING_SEARCH_POLICY_ID,\n",
        "policy test imports",
    )
    policy = replace_once(
        policy,
        "    #[test]\n    fn delta_pruning_without_see_pruning_fails_loudly() {\n",
        "    #[test]\n    fn s2_9_null_move_candidate_is_distinct_valid_and_inactive_by_default() {\n        let baseline = SearchPolicySet::baseline();\n        let candidate = SearchPolicySet::null_move_pruning_candidate();\n        assert_eq!(candidate.identifier, NULL_MOVE_PRUNING_SEARCH_POLICY_ID);\n        assert_eq!(candidate.validate(), Ok(()));\n        assert!(!baseline.policy.null_move_pruning_enabled());\n        assert!(candidate.policy.null_move_pruning_enabled());\n        assert_ne!(candidate.checksum, baseline.checksum);\n    }\n\n    #[test]\n    fn delta_pruning_without_see_pruning_fails_loudly() {\n",
        "null policy unit test",
    )
    policy = replace_once(
        policy,
        "        parameters.experimental_features = ExperimentalSearchFeatures::from_bits(1 << 5)\n",
        "        parameters.experimental_features = ExperimentalSearchFeatures::from_bits(1 << 6)\n",
        "unsupported feature test advances to futility",
    )
    write(policy_path, policy)

    lib_path = "crates/chess-search/src/lib.rs"
    lib = read(lib_path)
    lib = replace_once(
        lib,
        "pub use diagnostics::{\n    SearchDiagnosticCounter, SearchDiagnosticEvent, SearchDiagnosticOverflow, SearchDiagnostics,\n};\n",
        "pub use diagnostics::{\n    NullMoveDisabledReason, SearchDiagnosticCounter, SearchDiagnosticEvent,\n    SearchDiagnosticOverflow, SearchDiagnostics,\n};\n",
        "diagnostic exports",
    )
    lib = replace_once(
        lib,
        "    LMR_REDUCTION_TABLE, MAXIMUM_ASPIRATION_HALF_WIDTH_CENTIPAWNS,\n",
        "    LMR_REDUCTION_TABLE, MAXIMUM_ASPIRATION_HALF_WIDTH_CENTIPAWNS,\n    NULL_MOVE_MINIMUM_DEPTH, NULL_MOVE_MINIMUM_SIDE_NON_PAWN_PIECES,\n    NULL_MOVE_MINIMUM_TOTAL_NON_PAWN_PIECES, NULL_MOVE_PRUNING_SEARCH_POLICY_ID,\n    NULL_MOVE_REDUCTION, NULL_MOVE_VERIFICATION_REDUCTION, NULL_MOVE_VERIFY_ALL_CUTOFFS,\n",
        "null policy exports",
    )
    write(lib_path, lib)

    alpha_path = "crates/chess-search/src/alpha_beta.rs"
    alpha = read(alpha_path)
    alpha = replace_once(
        alpha,
        "    LegalMoveError, Move, Position, SearchHistory, SearchHistoryError, StaticExchangeError,\n",
        "    LegalMoveError, Move, PieceKind, Position, SearchHistory, SearchHistoryError,\n    SearchNullError, StaticExchangeError,\n",
        "alpha core imports",
    )
    alpha = replace_once(
        alpha,
        "    EvaluationWeights, Score, SearchCancellationProbe, SearchDiagnosticEvent,\n",
        "    evaluate_with_weights, EvaluationWeights, NullMoveDisabledReason, Score,\n    SearchCancellationProbe, SearchDiagnosticEvent,\n",
        "alpha crate imports",
    )
    alpha = replace_once(
        alpha,
        "        LMR_MINIMUM_TOTAL_PIECES, LMR_REDUCTION_TABLE,\n",
        "        LMR_MINIMUM_TOTAL_PIECES, LMR_REDUCTION_TABLE, NULL_MOVE_MINIMUM_DEPTH,\n        NULL_MOVE_MINIMUM_SIDE_NON_PAWN_PIECES, NULL_MOVE_MINIMUM_TOTAL_NON_PAWN_PIECES,\n        NULL_MOVE_REDUCTION, NULL_MOVE_VERIFICATION_REDUCTION, NULL_MOVE_VERIFY_ALL_CUTOFFS,\n",
        "alpha null constants",
    )
    alpha = replace_once(
        alpha,
        "    fn pvs_child(parent_alpha: Score) -> Result<Self, AlphaBetaSearchError> {\n",
        "    fn null_child(parent_beta: Score) -> Result<Self, AlphaBetaSearchError> {\n        let child_alpha = -parent_beta;\n        let child_beta_raw = child_alpha.centipawns().checked_add(1).ok_or(\n            AlphaBetaSearchError::NullMoveWindowOutOfRange {\n                parent_beta: parent_beta.centipawns(),\n            },\n        )?;\n        let child_beta = Score::from_raw(child_beta_raw).ok_or(\n            AlphaBetaSearchError::NullMoveWindowOutOfRange {\n                parent_beta: parent_beta.centipawns(),\n            },\n        )?;\n        Self::new(child_alpha, child_beta).ok_or(\n            AlphaBetaSearchError::NullMoveWindowOutOfRange {\n                parent_beta: parent_beta.centipawns(),\n            },\n        )\n    }\n\n    fn null_verification(parent_beta: Score) -> Result<Self, AlphaBetaSearchError> {\n        let alpha_raw = parent_beta.centipawns().checked_sub(1).ok_or(\n            AlphaBetaSearchError::NullMoveWindowOutOfRange {\n                parent_beta: parent_beta.centipawns(),\n            },\n        )?;\n        let alpha = Score::from_raw(alpha_raw).ok_or(\n            AlphaBetaSearchError::NullMoveWindowOutOfRange {\n                parent_beta: parent_beta.centipawns(),\n            },\n        )?;\n        Self::new(alpha, parent_beta).ok_or(\n            AlphaBetaSearchError::NullMoveWindowOutOfRange {\n                parent_beta: parent_beta.centipawns(),\n            },\n        )\n    }\n\n    fn pvs_child(parent_alpha: Score) -> Result<Self, AlphaBetaSearchError> {\n",
        "null windows",
    )
    alpha = replace_once(
        alpha,
        "    /// Position rule processing failed.\n    Rules(LegalMoveError),\n",
        "    /// Position rule processing failed.\n    Rules(LegalMoveError),\n    /// Search-only null transition processing failed.\n    SearchNull(SearchNullError),\n",
        "alpha null error",
    )
    alpha = replace_once(
        alpha,
        "    /// A one-centipawn PVS child window could not be represented.\n",
        "    /// Null-move depth arithmetic could not be represented.\n    NullMoveDepthOutOfRange {\n        /// Current legal-node depth.\n        depth: u16,\n        /// Requested reduction.\n        reduction: u16,\n    },\n    /// A one-centipawn null or verification window could not be represented.\n    NullMoveWindowOutOfRange {\n        /// Parent beta used to derive the narrow window.\n        parent_beta: i32,\n    },\n    /// A one-centipawn PVS child window could not be represented.\n",
        "alpha null arithmetic errors",
    )
    alpha = replace_once(
        alpha,
        "            Self::Rules(error) => error.fmt(formatter),\n",
        "            Self::Rules(error) => error.fmt(formatter),\n            Self::SearchNull(error) => error.fmt(formatter),\n",
        "alpha null display",
    )
    alpha = replace_once(
        alpha,
        "            Self::PvsWindowOutOfRange { parent_alpha } => write!(\n",
        "            Self::NullMoveDepthOutOfRange { depth, reduction } => write!(\n                formatter,\n                \"cannot reduce null-move depth {depth} by {reduction}\"\n            ),\n            Self::NullMoveWindowOutOfRange { parent_beta } => write!(\n                formatter,\n                \"cannot construct null-move window from parent beta {parent_beta}\"\n            ),\n            Self::PvsWindowOutOfRange { parent_alpha } => write!(\n",
        "alpha null display arms",
    )
    alpha = replace_once(
        alpha,
        "impl From<SearchHistoryError> for AlphaBetaSearchError {\n",
        "impl From<SearchNullError> for AlphaBetaSearchError {\n    fn from(value: SearchNullError) -> Self {\n        Self::SearchNull(value)\n    }\n}\n\nimpl From<SearchHistoryError> for AlphaBetaSearchError {\n",
        "alpha null From",
    )
    alpha = replace_once(
        alpha,
        "        late_move_reductions: policy.search_policy.late_move_reductions_enabled(),\n",
        "        late_move_reductions: policy.search_policy.late_move_reductions_enabled(),\n        null_move_pruning: policy.search_policy.null_move_pruning_enabled(),\n",
        "context null enablement",
    )
    alpha = replace_once(
        alpha,
        "    late_move_reductions: bool,\n    weights: &'a EvaluationWeights,\n",
        "    late_move_reductions: bool,\n    null_move_pruning: bool,\n    weights: &'a EvaluationWeights,\n",
        "context null field",
    )
    alpha = replace_once(
        alpha,
        "        window,\n        context,\n    )\n}\n\nfn search_node_with_extensions<Probe>(\n",
        "        window,\n        NullMoveState::Allowed,\n        context,\n    )\n}\n\n#[derive(Clone, Copy, Debug, Eq, PartialEq)]\nenum NullMoveState {\n    Allowed,\n    SpeculativeSubtree,\n    VerificationSubtree,\n}\n\n#[derive(Clone, Copy, Debug, Eq, PartialEq)]\nstruct NullMoveSearch {\n    speculative_depth: u16,\n    speculative_window: AlphaBetaWindow,\n    verification_depth: u16,\n    verification_window: AlphaBetaWindow,\n}\n\n#[derive(Clone, Copy, Debug, Eq, PartialEq)]\nenum NullMoveDecision {\n    Disabled(NullMoveDisabledReason),\n    Search(NullMoveSearch),\n}\n\nfn search_node_with_extensions<Probe>(\n",
        "null state types",
    )
    alpha = replace_once(
        alpha,
        "    extension_budget: u16,\n    window: AlphaBetaWindow,\n    context: &mut AlphaBetaContext<'_, Probe>,\n",
        "    extension_budget: u16,\n    window: AlphaBetaWindow,\n    null_move_state: NullMoveState,\n    context: &mut AlphaBetaContext<'_, Probe>,\n",
        "null state search signature",
    )
    alpha = replace_once(
        alpha,
        "    let score_reuse = transposition_score_reuse(position, context.check_extension_enabled);\n",
        "    let score_reuse = transposition_score_reuse(\n        position,\n        context.check_extension_enabled,\n        null_move_state,\n    );\n",
        "TT null state call",
    )
    old_node_setup = """    if ply == 0 {\n        transposition_table_move = None;\n    }\n    let ordered_tokens = ordered_legal_moves_with_state_and_tt_move_and_see(\n        position,\n        &tokens,\n        context.ordering,\n        ply,\n        context.quiet_ordering,\n        transposition_table_move,\n        context.see_capture_ordering,\n    )?;\n    let mut nodes = 1_u64;\n    let mut qnodes = 0_u64;\n    let mut selective_depth = ply;\n    let mut diagnostics = SearchDiagnostics::main_node();\n    ordered_tokens\n"""
    new_node_setup = """    if ply == 0 {\n        transposition_table_move = None;\n    }\n\n    let mut nodes = 1_u64;\n    let mut qnodes = 0_u64;\n    let mut selective_depth = ply;\n    let mut diagnostics = SearchDiagnostics::main_node();\n\n    if context.null_move_pruning {\n        let attempt_event = SearchDiagnosticEvent::NullMoveAttempt;\n        diagnostics.record_checked(attempt_event)?;\n        context.cancellation.on_search_diagnostic(attempt_event);\n        match decide_null_move(\n            position,\n            depth,\n            ply,\n            window,\n            null_move_state,\n            context.weights,\n        )? {\n            NullMoveDecision::Disabled(reason) => {\n                let disabled_event = SearchDiagnosticEvent::NullMoveDisabled { reason };\n                diagnostics.record_checked(disabled_event)?;\n                context.cancellation.on_search_diagnostic(disabled_event);\n            }\n            NullMoveDecision::Search(request) => {\n                let undo = position.make_search_null()?;\n                let speculative = search_node_with_extensions(\n                    position,\n                    history,\n                    request.speculative_depth,\n                    ply + 1,\n                    extension_budget,\n                    request.speculative_window,\n                    NullMoveState::SpeculativeSubtree,\n                    context,\n                );\n                let restore = position.unmake_search_null(undo);\n                if let Err(error) = restore {\n                    return Err(error.into());\n                }\n                let speculative = speculative?;\n                nodes = nodes\n                    .checked_add(speculative.nodes)\n                    .ok_or(AlphaBetaSearchError::NodeCountOverflow)?;\n                qnodes = qnodes\n                    .checked_add(speculative.qnodes)\n                    .ok_or(AlphaBetaSearchError::NodeCountOverflow)?;\n                selective_depth = selective_depth.max(speculative.selective_depth);\n                diagnostics = diagnostics.checked_add(speculative.diagnostics)?;\n                let speculative_parent_score = -speculative.score;\n                if speculative_parent_score >= beta {\n                    let fail_high_event = SearchDiagnosticEvent::NullMoveSpeculativeFailHigh;\n                    diagnostics.record_checked(fail_high_event)?;\n                    context.cancellation.on_search_diagnostic(fail_high_event);\n                    debug_assert!(NULL_MOVE_VERIFY_ALL_CUTOFFS);\n                    let verification_event = SearchDiagnosticEvent::NullMoveVerificationSearch;\n                    diagnostics.record_checked(verification_event)?;\n                    context.cancellation.on_search_diagnostic(verification_event);\n                    let verification = search_node_with_extensions(\n                        position,\n                        history,\n                        request.verification_depth,\n                        ply,\n                        extension_budget,\n                        request.verification_window,\n                        NullMoveState::VerificationSubtree,\n                        context,\n                    )?;\n                    nodes = nodes\n                        .checked_add(verification.nodes)\n                        .ok_or(AlphaBetaSearchError::NodeCountOverflow)?;\n                    qnodes = qnodes\n                        .checked_add(verification.qnodes)\n                        .ok_or(AlphaBetaSearchError::NodeCountOverflow)?;\n                    selective_depth = selective_depth.max(verification.selective_depth);\n                    diagnostics = diagnostics.checked_add(verification.diagnostics)?;\n                    if verification.score >= beta {\n                        let cutoff_event = SearchDiagnosticEvent::NullMoveCutoff;\n                        diagnostics.record_checked(cutoff_event)?;\n                        context.cancellation.on_search_diagnostic(cutoff_event);\n                        return Ok(AlphaBetaSearchResult {\n                            score: verification.score,\n                            best_move: verification.best_move,\n                            nodes,\n                            qnodes,\n                            selective_depth,\n                            diagnostics,\n                        });\n                    }\n                }\n            }\n        }\n    }\n\n    let ordered_tokens = ordered_legal_moves_with_state_and_tt_move_and_see(\n        position,\n        &tokens,\n        context.ordering,\n        ply,\n        context.quiet_ordering,\n        transposition_table_move,\n        context.see_capture_ordering,\n    )?;\n    ordered_tokens\n"""
    alpha = replace_once(alpha, old_node_setup, new_node_setup, "null node integration")
    alpha = replace_once(
        alpha,
        "                alpha,\n                beta,\n            },\n",
        "                alpha,\n                beta,\n                null_move_state,\n            },\n",
        "child null state",
    )
    alpha = replace_once(
        alpha,
        "    beta: Score,\n}\n\nfn search_child_with_optional_lmr",
        "    beta: Score,\n    null_move_state: NullMoveState,\n}\n\nfn search_child_with_optional_lmr",
        "ChildSearch null state field",
    )
    alpha = replace_once(
        alpha,
        "        beta,\n        ..\n    } = request;\n",
        "        beta,\n        null_move_state,\n        ..\n    } = request;\n",
        "PVS null state destructure",
    )
    alpha = alpha.replace(
        "            full_window,\n            context,\n",
        "            full_window,\n            null_move_state,\n            context,\n",
    )
    alpha = alpha.replace(
        "        zero_window,\n        context,\n",
        "        zero_window,\n        null_move_state,\n        context,\n",
    )
    alpha = replace_once(
        alpha,
        "fn transposition_score_reuse(\n    position: &Position,\n    check_extension_enabled: bool,\n) -> TranspositionScoreReuse {\n    if check_extension_enabled {\n",
        "fn transposition_score_reuse(\n    position: &Position,\n    check_extension_enabled: bool,\n    null_move_state: NullMoveState,\n) -> TranspositionScoreReuse {\n    if null_move_state == NullMoveState::SpeculativeSubtree {\n        TranspositionScoreReuse::SuppressedForNullMove\n    } else if check_extension_enabled {\n",
        "TT null suppression implementation",
    )
    helper = r'''
fn decide_null_move(
    position: &Position,
    depth: u16,
    ply: u16,
    window: AlphaBetaWindow,
    state: NullMoveState,
    weights: &EvaluationWeights,
) -> Result<NullMoveDecision, AlphaBetaSearchError> {
    if state != NullMoveState::Allowed {
        return Ok(NullMoveDecision::Disabled(
            NullMoveDisabledReason::NestedOrVerification,
        ));
    }
    if ply == 0 {
        return Ok(NullMoveDecision::Disabled(NullMoveDisabledReason::Root));
    }
    if position.is_in_check(position.side_to_move()) {
        return Ok(NullMoveDecision::Disabled(
            NullMoveDisabledReason::InCheck,
        ));
    }
    if depth < NULL_MOVE_MINIMUM_DEPTH {
        return Ok(NullMoveDecision::Disabled(
            NullMoveDisabledReason::ShallowDepth,
        ));
    }
    if window.alpha().is_mate()
        || window.beta().is_mate()
        || ply >= MAX_MATE_PLY.saturating_sub(depth)
    {
        return Ok(NullMoveDecision::Disabled(
            NullMoveDisabledReason::MateSensitive,
        ));
    }

    let side = position.side_to_move();
    let side_non_pawn = non_pawn_non_king_count(position, side);
    let total_non_pawn = side_non_pawn + non_pawn_non_king_count(position, side.opposite());
    if side_non_pawn < u32::from(NULL_MOVE_MINIMUM_SIDE_NON_PAWN_PIECES)
        || total_non_pawn < u32::from(NULL_MOVE_MINIMUM_TOTAL_NON_PAWN_PIECES)
    {
        return Ok(NullMoveDecision::Disabled(
            NullMoveDisabledReason::LowNonPawnMaterial,
        ));
    }

    if evaluate_with_weights(position, weights) < window.beta() {
        return Ok(NullMoveDecision::Disabled(
            NullMoveDisabledReason::StaticEvaluationBelowBeta,
        ));
    }

    let speculative_reduction = NULL_MOVE_REDUCTION.checked_add(1).ok_or(
        AlphaBetaSearchError::NullMoveDepthOutOfRange {
            depth,
            reduction: NULL_MOVE_REDUCTION,
        },
    )?;
    let speculative_depth = depth.checked_sub(speculative_reduction).ok_or(
        AlphaBetaSearchError::NullMoveDepthOutOfRange {
            depth,
            reduction: speculative_reduction,
        },
    )?;
    let verification_depth = depth.checked_sub(NULL_MOVE_VERIFICATION_REDUCTION).ok_or(
        AlphaBetaSearchError::NullMoveDepthOutOfRange {
            depth,
            reduction: NULL_MOVE_VERIFICATION_REDUCTION,
        },
    )?;
    Ok(NullMoveDecision::Search(NullMoveSearch {
        speculative_depth,
        speculative_window: AlphaBetaWindow::null_child(window.beta())?,
        verification_depth,
        verification_window: AlphaBetaWindow::null_verification(window.beta())?,
    }))
}

fn non_pawn_non_king_count(position: &Position, color: chess_core::Color) -> u32 {
    [
        PieceKind::Knight,
        PieceKind::Bishop,
        PieceKind::Rook,
        PieceKind::Queen,
    ]
    .into_iter()
    .map(|kind| position.piece_bitboard(color, kind).count())
    .sum()
}

'''
    alpha = replace_once(
        alpha,
        "#[derive(Clone, Copy)]\nstruct ChildSearch {\n",
        helper + "#[derive(Clone, Copy)]\nstruct ChildSearch {\n",
        "null decision helpers",
    )
    alpha = alpha.replace(
        "        late_move_reductions: false,\n",
        "        late_move_reductions: false,\n        null_move_pruning: false,\n",
    )
    alpha = replace_once(
        alpha,
        "mod lmr_policy_tests {\n",
        r'''mod null_move_policy_tests {
    use chess_core::Position;

    use super::{
        decide_null_move, transposition_score_reuse, AlphaBetaWindow, NullMoveDecision,
        NullMoveState,
    };
    use crate::{
        EvaluationWeights, NullMoveDisabledReason, Score, TranspositionScoreReuse,
        NULL_MOVE_MINIMUM_DEPTH, NULL_MOVE_REDUCTION, NULL_MOVE_VERIFICATION_REDUCTION,
    };

    fn position(fen: &str) -> Position {
        Position::from_fen(fen).expect("fixture parses")
    }

    fn window(alpha: i32, beta: i32) -> AlphaBetaWindow {
        AlphaBetaWindow::new(
            Score::from_raw(alpha).expect("alpha fits"),
            Score::from_raw(beta).expect("beta fits"),
        )
        .expect("window is valid")
    }

    #[test]
    fn eligible_policy_uses_checked_frozen_depths_and_windows() {
        let current = Position::starting();
        let decision = decide_null_move(
            &current,
            6,
            1,
            window(-200, -100),
            NullMoveState::Allowed,
            &EvaluationWeights::DEFAULT,
        )
        .expect("decision succeeds");
        let NullMoveDecision::Search(request) = decision else {
            panic!("midgame fixture should be eligible: {decision:?}");
        };
        assert_eq!(NULL_MOVE_MINIMUM_DEPTH, 4);
        assert_eq!(NULL_MOVE_REDUCTION, 2);
        assert_eq!(NULL_MOVE_VERIFICATION_REDUCTION, 1);
        assert_eq!(request.speculative_depth, 3);
        assert_eq!(request.verification_depth, 5);
        assert_eq!(request.speculative_window.alpha().centipawns(), 100);
        assert_eq!(request.speculative_window.beta().centipawns(), 101);
        assert_eq!(request.verification_window.alpha().centipawns(), -101);
        assert_eq!(request.verification_window.beta().centipawns(), -100);
    }

    #[test]
    fn conservative_guards_disable_unsafe_contexts() {
        let starting = Position::starting();
        assert_eq!(
            decide_null_move(
                &starting,
                6,
                0,
                window(-200, -100),
                NullMoveState::Allowed,
                &EvaluationWeights::DEFAULT,
            ),
            Ok(NullMoveDecision::Disabled(NullMoveDisabledReason::Root))
        );
        assert_eq!(
            decide_null_move(
                &starting,
                3,
                1,
                window(-200, -100),
                NullMoveState::Allowed,
                &EvaluationWeights::DEFAULT,
            ),
            Ok(NullMoveDecision::Disabled(
                NullMoveDisabledReason::ShallowDepth
            ))
        );
        assert_eq!(
            decide_null_move(
                &starting,
                6,
                1,
                window(-200, -100),
                NullMoveState::SpeculativeSubtree,
                &EvaluationWeights::DEFAULT,
            ),
            Ok(NullMoveDecision::Disabled(
                NullMoveDisabledReason::NestedOrVerification
            ))
        );
        let checked = position("4k3/8/8/8/8/8/4R3/4K3 b - - 0 1");
        assert_eq!(
            decide_null_move(
                &checked,
                6,
                1,
                window(-200, -100),
                NullMoveState::Allowed,
                &EvaluationWeights::DEFAULT,
            ),
            Ok(NullMoveDecision::Disabled(NullMoveDisabledReason::InCheck))
        );
        let pawn_only = position("7k/6pp/8/8/8/8/PP6/K7 w - - 0 1");
        assert_eq!(
            decide_null_move(
                &pawn_only,
                6,
                1,
                window(-200, -100),
                NullMoveState::Allowed,
                &EvaluationWeights::DEFAULT,
            ),
            Ok(NullMoveDecision::Disabled(
                NullMoveDisabledReason::LowNonPawnMaterial
            ))
        );
    }

    #[test]
    fn synthetic_subtree_has_distinct_tt_suppression_and_verification_does_not() {
        let current = Position::starting();
        assert_eq!(
            transposition_score_reuse(&current, false, NullMoveState::SpeculativeSubtree),
            TranspositionScoreReuse::SuppressedForNullMove
        );
        assert_eq!(
            transposition_score_reuse(&current, false, NullMoveState::VerificationSubtree),
            TranspositionScoreReuse::Allowed
        );
    }
}

#[cfg(test)]
mod lmr_policy_tests {
''',
        "null policy unit module",
    )
    alpha = replace_once(
        alpha,
        "    use super::{late_move_reduction, ChildSearch};\n",
        "    use super::{late_move_reduction, ChildSearch, NullMoveState};\n",
        "lmr test null state import",
    )
    alpha = replace_once(
        alpha,
        "            beta: Score::from_raw(20).expect(\"score fits\"),\n        }\n",
        "            beta: Score::from_raw(20).expect(\"score fits\"),\n            null_move_state: NullMoveState::Allowed,\n        }\n",
        "lmr request null state",
    )
    write(alpha_path, alpha)

    test_path = "crates/chess-search/tests/s2_9_null_move.rs"
    write(
        test_path,
        r'''use chess_core::{Move, Position, SearchHistory};
use chess_search::{
    iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights,
    EvaluationWeights, SearchLimits, SearchPolicySet, SearchResult, TranspositionTable,
    NULL_MOVE_MINIMUM_DEPTH, NULL_MOVE_MINIMUM_SIDE_NON_PAWN_PIECES,
    NULL_MOVE_MINIMUM_TOTAL_NON_PAWN_PIECES, NULL_MOVE_PRUNING_SEARCH_POLICY_ID,
    NULL_MOVE_REDUCTION, NULL_MOVE_VERIFICATION_REDUCTION, NULL_MOVE_VERIFY_ALL_CUTOFFS,
};

const TT_MEBIBYTES: usize = 1;

fn run(fen: &str, limits: SearchLimits, policy: &SearchPolicySet) -> SearchResult {
    let mut position = Position::from_fen(fen).expect("fixture FEN parses");
    let root = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let root_history = history.clone();
    let mut table = TranspositionTable::new(TT_MEBIBYTES).expect("small TT allocates");
    let result =
        iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights(
            &mut position,
            &mut history,
            limits,
            &mut table,
            policy,
            &EvaluationWeights::DEFAULT,
        )
        .expect("controlled search succeeds");
    assert_eq!(position, root);
    assert_eq!(history, root_history);
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
    replay_pv(
        &root,
        result
            .principal_variation()
            .map(|pv| pv.moves())
            .unwrap_or(&[]),
    );
    result
}

fn replay_pv(root: &Position, moves: &[Move]) {
    let mut position = root.clone();
    for current in moves {
        let token = position
            .legal_move_tokens()
            .expect("PV legal tokens generate")
            .iter()
            .find(|token| token.move_made() == *current)
            .expect("PV move is legal");
        position
            .make_legal_token(token)
            .expect("PV legal token applies");
    }
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
}

#[test]
fn candidate_identity_parameters_and_default_inactivity_are_explicit() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::null_move_pruning_candidate();
    baseline.validate().expect("baseline validates");
    candidate.validate().expect("candidate validates");
    assert_eq!(candidate.identifier, NULL_MOVE_PRUNING_SEARCH_POLICY_ID);
    assert_eq!(NULL_MOVE_MINIMUM_DEPTH, 4);
    assert_eq!(NULL_MOVE_REDUCTION, 2);
    assert_eq!(NULL_MOVE_VERIFICATION_REDUCTION, 1);
    assert_eq!(NULL_MOVE_MINIMUM_SIDE_NON_PAWN_PIECES, 2);
    assert_eq!(NULL_MOVE_MINIMUM_TOTAL_NON_PAWN_PIECES, 4);
    assert!(NULL_MOVE_VERIFY_ALL_CUTOFFS);
    assert!(!baseline.policy.null_move_pruning_enabled());
    assert!(candidate.policy.null_move_pruning_enabled());
    assert_ne!(baseline.checksum, candidate.checksum);
}

#[test]
fn midgame_candidate_records_attempts_guards_and_verified_cutoffs_only() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::null_move_pruning_candidate();
    let fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1";
    let baseline_result = run(fen, SearchLimits::new().with_depth(5), &baseline);
    let candidate_result = run(fen, SearchLimits::new().with_depth(5), &candidate);
    let baseline_diagnostics = baseline_result.search_diagnostics();
    let diagnostics = candidate_result.search_diagnostics();
    assert_eq!(baseline_diagnostics.null_move_attempts(), 0);
    assert_eq!(baseline_diagnostics.null_move_disabled_nodes(), 0);
    assert_eq!(baseline_diagnostics.null_move_speculative_fail_highs(), 0);
    assert_eq!(baseline_diagnostics.null_move_verification_searches(), 0);
    assert_eq!(baseline_diagnostics.null_move_cutoffs(), 0);
    assert!(diagnostics.null_move_attempts() > 0);
    assert!(diagnostics.null_move_disabled_nodes() > 0);
    assert_eq!(
        diagnostics.null_move_speculative_fail_highs(),
        diagnostics.null_move_verification_searches()
    );
    assert!(diagnostics.null_move_cutoffs() <= diagnostics.null_move_verification_searches());
    assert!(!diagnostics.overflowed());
    assert_eq!(candidate_result.completed_depth(), baseline_result.completed_depth());
}

#[test]
fn pawn_only_and_low_material_positions_never_enter_speculative_search() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::null_move_pruning_candidate();
    for fen in [
        "7k/6pp/8/8/8/8/PP6/K7 w - - 0 1",
        "7k/8/8/8/8/8/6N1/K7 w - - 0 1",
    ] {
        let baseline_result = run(fen, SearchLimits::new().with_depth(5), &baseline);
        let candidate_result = run(fen, SearchLimits::new().with_depth(5), &candidate);
        let diagnostics = candidate_result.search_diagnostics();
        assert!(diagnostics.null_move_attempts() > 0, "{fen}");
        assert_eq!(diagnostics.null_move_speculative_fail_highs(), 0, "{fen}");
        assert_eq!(diagnostics.null_move_verification_searches(), 0, "{fen}");
        assert_eq!(diagnostics.null_move_cutoffs(), 0, "{fen}");
        assert_eq!(candidate_result.score(), baseline_result.score(), "{fen}");
        assert_eq!(candidate_result.best_move(), baseline_result.best_move(), "{fen}");
    }
}

#[test]
fn node_limited_cancellation_restores_position_history_and_hash() {
    let candidate = SearchPolicySet::null_move_pruning_candidate();
    let fen = "r2q1rk1/ppp2ppp/2npbn2/3Np3/2B1P3/2P2N2/PP3PPP/R1BQR1K1 w - - 0 10";
    let limited = run(
        fen,
        SearchLimits::new().with_depth(9).with_nodes(768),
        &candidate,
    );
    assert!(limited.completed_depth() < 9);
    assert!(limited.nodes() <= 768);
    for iteration in limited.completed().iterations() {
        let diagnostics = iteration.search_diagnostics();
        assert_eq!(
            diagnostics.null_move_speculative_fail_highs(),
            diagnostics.null_move_verification_searches()
        );
        assert!(diagnostics.null_move_cutoffs() <= diagnostics.null_move_verification_searches());
        assert!(!diagnostics.overflowed());
    }
}
''',
    )


def phase2() -> None:
    core_sha = os.environ["CORE_SHA"]
    run_id = os.environ.get("GITHUB_RUN_ID", "unknown")

    tracker_path = "docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md"
    tracker = read(tracker_path)
    tracker = tracker.replace(
        "| S2-9 | Optional null-move pruning decision/candidate | **In progress — search-null transition complete; pruning policy not started** |",
        "| S2-9 | Optional null-move pruning decision/candidate | **In progress — conservative policy complete; validation/disposition not started** |",
    )
    for item in [
        "Disable in check.",
        "Disable at shallow depth.",
        "Disable in low non-pawn material and pawn-only endings.",
        "Disable consecutive null moves.",
        "Disable in mate-sensitive windows/contexts as specified.",
        "Add optional verification search policy.",
        "Count attempts, disabled nodes, cutoffs, and verifications.",
    ]:
        tracker = tracker.replace(f"- [ ] {item}", f"- [x] {item}")
    tracker = tracker.replace(
        "Begin with **S2-9.3 only**: implement the dedicated reversible search-only null transition and focused core correctness tests described in `docs/RUST_CHESS_ENGINE_V0_2_S2_9_NULL_MOVE_FEASIBILITY_2026-08-05.md`. Do not integrate null pruning into alpha-beta, enable the policy bit, add strength evidence, begin S2-10, or combine rejected candidates until the transition's exact restoration, hash parity, failure atomicity, and permanent audit pass.",
        "Begin with **S2-9.4 only**: validate the inactive conservative null-move candidate against zugzwang, stalemate, repetition, fifty/seventy-five-move, mate-distance, longest-survival, restoration, cancellation, fixed-node, and clock protocols. Do not activate the candidate, begin S2-10, or combine it with rejected candidates until S2-9.4 records an explicit evidence-backed disposition.",
    )
    marker = "## S2-9.2 transition record\n"
    index = tracker.find(marker)
    if index < 0:
        raise RuntimeError("tracker S2-9.2 record marker missing")
    next_record = tracker.find("\n## ", index + len(marker))
    if next_record < 0:
        raise RuntimeError("tracker record boundary missing")
    record = f'''\n## S2-9.3 conservative policy record\n\n- Disposition: implementation complete; validation and strength disposition remain pending; activation remains false.\n- Core implementation SHA: `{core_sha}`.\n- Staging validation workflow run: `{run_id}`.\n- Candidate policy identifier: `5332394e4d503031`; isolated null-move feature bit only.\n- Frozen policy: minimum depth `4`; speculative reduction `2` after the synthetic pass ply; verification reduction `1`; side-to-move non-pawn minimum `2`; total non-pawn minimum `4`; every speculative fail-high requires verification.\n- Disabled contexts: root, check, shallow depth, pawn-only/low non-pawn material, nested/speculative/verification subtrees, mate-sensitive bounds/domain, and static evaluation below beta.\n- Synthetic subtrees suppress TT score reuse and storage through the explicit `SuppressedForNullMove` reason while retaining legal-checked TT move ordering hints. Verification searches return to ordinary TT score policy but keep null disabled for the complete verification subtree.\n- Diagnostics now count eligibility attempts, disabled nodes with stable reason events, speculative fail-highs, verification searches, and confirmed cutoffs using checked exact-result accumulation.\n- The authoritative v0.1 policy, production adapters, UCI, C ABI, JNI, Android, package version, and defaults remain unchanged.\n- S2-9.4 correctness, development strength, and final disposition are not claimed.\n'''
    tracker = tracker[:next_record] + record + tracker[next_record:]
    write(tracker_path, tracker)

    doc_path = "docs/RUST_CHESS_ENGINE_V0_2_S2_9_NULL_MOVE_POLICY_2026-08-05.md"
    write(
        doc_path,
        f'''# S2-9.3 Conservative Null-Move Pruning Policy\n\n**Status:** Implementation complete; validation pending\n**Date:** 2026-08-05\n**Branch:** `master`\n**Core implementation SHA:** `{core_sha}`\n**Staging validation run:** `{run_id}`\n**Activation:** `false`\n\n## Scope\n\nS2-9.3 integrates the S2-9.2 reversible search-only transition into controlled alpha-beta search under a new isolated, inactive policy identity. It does not activate null-move pruning in default search, expose it through production adapters, run strength matches, or claim the S2-9 gate.\n\n## Frozen policy\n\n- minimum remaining depth: `4`;\n- speculative child depth: `depth - 1 - 2`;\n- verification depth: `depth - 1`;\n- side-to-move minimum non-pawn/non-king pieces: `2`;\n- total minimum non-pawn/non-king pieces: `4`;\n- static evaluation must meet or exceed beta;\n- every speculative fail-high is verified before cutoff;\n- root, check, shallow, low-material, nested, verification, and mate-sensitive contexts are disabled.\n\nAll depth and one-centipawn window arithmetic is checked before the position transition. Arithmetic failure is typed and cannot silently disable or mutate the position.\n\n## Search-state and TT semantics\n\nRecursive state explicitly distinguishes ordinary, speculative-null, and verification subtrees. The complete speculative subtree disables additional null attempts and uses `TranspositionScoreReuse::SuppressedForNullMove`, which suppresses TT scores and storage while preserving only complete-key, legal-checked move-ordering hints. The verification subtree also disables null recursively but may use ordinary TT score policy because the position is again legal and no speculative subtree entry was stored.\n\nThe synthetic position is never pushed into `SearchHistory`. Position undo always runs before cancellation or recursive errors propagate.\n\n## Diagnostics\n\nThe candidate records checked counters for:\n\n- null-move eligibility attempts;\n- disabled nodes, with stable reason-bearing events;\n- speculative fail-highs;\n- verification searches;\n- confirmed cutoffs.\n\nEvery speculative fail-high must have exactly one verification search. Confirmed cutoffs cannot exceed verification searches. Baseline/default search keeps all null counters at zero.\n\n## Permanent tests\n\nTests cover policy identity/default inactivity, checked depths and windows, root/check/shallow/material/nested guards, explicit TT suppression, midgame diagnostics, pawn-only and low-material exclusion, legal PV replay, deterministic restoration, and node-limited cancellation.\n\n## Remaining S2-9.4 work\n\nS2-9.4 must independently validate zugzwang, stalemate, repetition, fifty/seventy-five-move boundaries, mate distance, longest survival, exact restoration/cancellation, and fixed-node plus clock development strength. It must then record `accept`, `reject`, or `defer`. The candidate remains inactive until that evidence exists.\n''',
    )

    audit_path = "scripts/task_s2_9_null_move_policy_audit.sh"
    write(
        audit_path,
        r'''#!/usr/bin/env bash
set -euo pipefail

policy=crates/chess-search/src/search_policy.rs
search=crates/chess-search/src/alpha_beta.rs
diagnostics=crates/chess-search/src/diagnostics.rs
probe=crates/chess-search/src/transposition/probe.rs
tracker=docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md
doc=docs/RUST_CHESS_ENGINE_V0_2_S2_9_NULL_MOVE_POLICY_2026-08-05.md
workflow=.github/workflows/s2-9-null-policy.yml

grep -Fq 'pub const NULL_MOVE_PRUNING_SEARCH_POLICY_ID' "$policy"
grep -Fq 'pub const NULL_MOVE_MINIMUM_DEPTH: u16 = 4;' "$policy"
grep -Fq 'pub const NULL_MOVE_REDUCTION: u16 = 2;' "$policy"
grep -Fq 'pub const NULL_MOVE_VERIFICATION_REDUCTION: u16 = 1;' "$policy"
grep -Fq 'pub const NULL_MOVE_MINIMUM_SIDE_NON_PAWN_PIECES: u16 = 2;' "$policy"
grep -Fq 'pub const NULL_MOVE_MINIMUM_TOTAL_NON_PAWN_PIECES: u16 = 4;' "$policy"
grep -Fq 'pub const NULL_MOVE_VERIFY_ALL_CUTOFFS: bool = true;' "$policy"
grep -Fq 'pub const NULL_MOVE_PRUNING: Self' "$policy"
grep -Fq 'pub const fn null_move_pruning_enabled' "$policy"
grep -Fq 'pub fn null_move_pruning_candidate' "$policy"
grep -Fq 'NullMovePruningMustBeIsolated' "$policy"

grep -Fq 'enum NullMoveState' "$search"
grep -Fq 'SpeculativeSubtree' "$search"
grep -Fq 'VerificationSubtree' "$search"
grep -Fq 'fn decide_null_move' "$search"
grep -Fq 'position.make_search_null()' "$search"
grep -Fq 'position.unmake_search_null(undo)' "$search"
grep -Fq 'NullMoveVerificationSearch' "$search"
grep -Fq 'NullMoveSpeculativeFailHigh' "$search"
grep -Fq 'NullMoveDisabledReason::LowNonPawnMaterial' "$search"
grep -Fq 'TranspositionScoreReuse::SuppressedForNullMove' "$search"

grep -Fq 'SuppressedForNullMove' "$probe"
grep -Fq 'NullMoveDisabledReason' "$diagnostics"
grep -Fq 'NullMoveDisabledNodes' "$diagnostics"
grep -Fq 'NullMoveSpeculativeFailHighs' "$diagnostics"
grep -Fq 'NullMoveVerificationSearches' "$diagnostics"
grep -Fq 'pub const fn null_move_disabled_nodes' "$diagnostics"
grep -Fq 'pub const fn null_move_verification_searches' "$diagnostics"

test -f crates/chess-search/tests/s2_9_null_move.rs
test -f "$doc"
test -f "$workflow"
grep -Fq '**Activation:** `false`' "$doc"
grep -Fq '## S2-9.3 conservative policy record' "$tracker"
grep -Fq 'Begin with **S2-9.4 only**:' "$tracker"

s2_9_3="$(sed -n '/## S2-9.3 Conservative policy if implemented/,/## S2-9.4 Validation if implemented/p' "$tracker")"
test "$(grep -Fc -- '- [x]' <<<"$s2_9_3")" -eq 7
test "$(grep -Fc -- '- [ ]' <<<"$s2_9_3")" -eq 0

grep -q '^permissions:' "$workflow"
grep -q '^  contents: read$' "$workflow"
if grep -q 'contents: write' "$workflow"; then
  echo 'permanent S2-9.3 workflow can write repository contents' >&2
  exit 1
fi

# Default production entry points remain bound to V0_1.
grep -Fq '&SearchPolicy::V0_1' "$search"
# The synthetic transition remains absent from adapter and protocol crates.
if grep -R -n -E 'make_search_null|NULL_MOVE_PRUNING' crates/chess-uci crates/chess-api crates/chess-ffi crates/chess-jni 2>/dev/null; then
  echo 'S2-9 null move leaked into a production adapter' >&2
  exit 1
fi

test ! -e .github/s2_9_3_policy.py
test ! -e .github/workflows/s2-9-3-stage.yml
''',
    )
    os.chmod(ROOT / audit_path, 0o755)

    workflow_path = ".github/workflows/s2-9-null-policy.yml"
    write(
        workflow_path,
        r'''name: S2-9.3 null-move policy validation

on:
  push:
    branches:
      - master
  pull_request:
    branches:
      - master
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: s2-9-null-policy-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  linux-x86-64:
    name: Linux x86-64 conservative policy
    runs-on: ubuntu-24.04
    timeout-minutes: 40
    steps:
      - uses: actions/checkout@v4
      - name: Install stable Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt, clippy
      - name: Cache Cargo data
        uses: Swatinem/rust-cache@v2
        with:
          shared-key: rust-engine-s2-9-null-policy-x86-64
      - name: Audit S2-9 boundaries
        run: |
          bash scripts/task_s2_9_null_move_feasibility_audit.sh
          bash scripts/task_s2_9_search_null_transition_audit.sh
          bash scripts/task_s2_9_null_move_policy_audit.sh
      - name: Check formatting and strict Clippy
        run: |
          cargo fmt --all -- --check
          cargo clippy --locked -p chess-core -p chess-search --all-targets --all-features -- -D warnings
      - name: Run complete core and search tests
        run: |
          cargo test --locked -p chess-core --all-targets --all-features
          cargo test --locked -p chess-search --all-targets --all-features

  linux-arm64:
    name: Linux ARM64 conservative policy
    runs-on: ubuntu-24.04-arm
    timeout-minutes: 40
    steps:
      - uses: actions/checkout@v4
      - name: Install stable Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt, clippy
      - name: Cache Cargo data
        uses: Swatinem/rust-cache@v2
        with:
          shared-key: rust-engine-s2-9-null-policy-arm64
      - name: Audit, lint, and test on native ARM64
        run: |
          bash scripts/task_s2_9_null_move_feasibility_audit.sh
          bash scripts/task_s2_9_search_null_transition_audit.sh
          bash scripts/task_s2_9_null_move_policy_audit.sh
          cargo fmt --all -- --check
          cargo clippy --locked -p chess-core -p chess-search --all-targets --all-features -- -D warnings
          cargo test --locked -p chess-core --all-targets --all-features
          cargo test --locked -p chess-search --all-targets --all-features
''',
    )

    tracker_close_path = ".github/workflows/tracker-close.yml"
    tracker_close = read(tracker_close_path)
    tracker_close = tracker_close.replace(
        "          bash scripts/task_s2_9_search_null_transition_audit.sh\n",
        "          bash scripts/task_s2_9_search_null_transition_audit.sh\n          bash scripts/task_s2_9_null_move_policy_audit.sh\n",
    )
    tracker_close = tracker_close.replace(
        "      - name: Verify S2-9 transition progression\n",
        "      - name: Verify S2-9 conservative-policy progression\n",
    )
    start = tracker_close.find("      - name: Verify S2-9 conservative-policy progression\n")
    if start < 0:
        raise RuntimeError("tracker-close S2-9 step missing")
    replacement = r'''      - name: Verify S2-9 conservative-policy progression
        shell: bash
        run: |
          set -euo pipefail
          tracker=docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md
          decision=docs/RUST_CHESS_ENGINE_V0_2_S2_9_NULL_MOVE_FEASIBILITY_2026-08-05.md
          transition=docs/RUST_CHESS_ENGINE_V0_2_S2_9_SEARCH_NULL_TRANSITION_2026-08-05.md
          policy=docs/RUST_CHESS_ENGINE_V0_2_S2_9_NULL_MOVE_POLICY_2026-08-05.md
          transition_workflow=.github/workflows/s2-9-search-null.yml
          policy_workflow=.github/workflows/s2-9-null-policy.yml

          grep -Fq '| S2-8 | Late Move Reductions candidate | **Complete — standalone rejected; inactive for combinations** |' "$tracker"
          grep -Fq '| S2-9 | Optional null-move pruning decision/candidate | **In progress — conservative policy complete; validation/disposition not started** |' "$tracker"
          grep -Fq '| S2-10 | Optional frontier and quiet-move pruning candidates | **Not started** |' "$tracker"
          grep -Fq '## S2-9 feasibility record' "$tracker"
          grep -Fq '## S2-9.2 transition record' "$tracker"
          grep -Fq '## S2-9.3 conservative policy record' "$tracker"
          grep -Fq '# Task S2-9: Optional null-move pruning decision/candidate — IN PROGRESS' "$tracker"
          grep -Fq '# Task S2-10: Optional frontier and quiet-move pruning candidates — NOT STARTED' "$tracker"
          grep -Fq 'Begin with **S2-9.4 only**:' "$tracker"

          grep -Fq '**Status:** Feasibility complete' "$decision"
          grep -Fq '**Disposition:** `implement`' "$decision"
          grep -Fq '**Activation:** `false`' "$decision"
          grep -Fq '**Status:** Complete' "$transition"
          grep -Fq '**Activation:** `false`' "$transition"
          grep -Fq '**Status:** Implementation complete; validation pending' "$policy"
          grep -Fq '**Activation:** `false`' "$policy"

          s2_9_1="$(sed -n '/## S2-9.1 Feasibility decision/,/## S2-9.2 Search-only transition if implemented/p' "$tracker")"
          test "$(grep -Fc -- '- [x]' <<<"$s2_9_1")" -eq 4
          test "$(grep -Fc -- '- [ ]' <<<"$s2_9_1")" -eq 0
          s2_9_2="$(sed -n '/## S2-9.2 Search-only transition if implemented/,/## S2-9.3 Conservative policy if implemented/p' "$tracker")"
          test "$(grep -Fc -- '- [x]' <<<"$s2_9_2")" -eq 5
          test "$(grep -Fc -- '- [ ]' <<<"$s2_9_2")" -eq 0
          s2_9_3="$(sed -n '/## S2-9.3 Conservative policy if implemented/,/## S2-9.4 Validation if implemented/p' "$tracker")"
          test "$(grep -Fc -- '- [x]' <<<"$s2_9_3")" -eq 7
          test "$(grep -Fc -- '- [ ]' <<<"$s2_9_3")" -eq 0
          s2_9_4="$(sed -n '/## S2-9.4 Validation if implemented/,/# Task S2-10:/p' "$tracker")"
          test "$(grep -Fc -- '- [ ]' <<<"$s2_9_4")" -eq 7

          for workflow in "$transition_workflow" "$policy_workflow"; do
            test -f "$workflow"
            grep -q '^permissions:' "$workflow"
            grep -q '^  contents: read$' "$workflow"
            if grep -q 'contents: write' "$workflow"; then
              echo "permanent S2-9 workflow can write repository contents: $workflow" >&2
              exit 1
            fi
          done

          test ! -e .github/s2_9_feasibility.py
          test ! -e .github/workflows/s2-9-feasibility.yml
          test ! -e .github/s2_9_2_transition.py
          test ! -e .github/s2_9_2_audit_fix.py
          test ! -e .github/workflows/s2-9-2-transition.yml
          test ! -e .github/s2_9_3_policy.py
          test ! -e .github/workflows/s2-9-3-stage.yml
'''
    tracker_close = tracker_close[:start] + replacement
    write(tracker_close_path, tracker_close)

    for path in [
        ROOT / ".github/s2_9_3_policy.py",
        ROOT / ".github/workflows/s2-9-3-stage.yml",
    ]:
        if path.exists():
            path.unlink()


def main() -> None:
    if len(sys.argv) != 2 or sys.argv[1] not in {"phase1", "phase2"}:
        raise SystemExit("usage: s2_9_3_policy.py phase1|phase2")
    if sys.argv[1] == "phase1":
        phase1()
    else:
        phase2()


if __name__ == "__main__":
    main()
