#!/usr/bin/env python3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path: str) -> str:
    return (ROOT / path).read_text()


def write(path: str, content: str) -> None:
    target = ROOT / path
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content)


def replace_once(path: str, old: str, new: str, expected: int = 1) -> None:
    content = read(path)
    count = content.count(old)
    if count != expected:
        raise SystemExit(
            f"{path}: expected {expected} replacement(s), found {count}: {old[:160]!r}"
        )
    write(path, content.replace(old, new))


POLICY = "crates/chess-search/src/search_policy.rs"
ALPHA_BETA = "crates/chess-search/src/alpha_beta.rs"
QUIESCENCE = "crates/chess-search/src/quiescence.rs"
LIB = "crates/chess-search/src/lib.rs"

# Search-policy identities and fail-closed dependencies.
replace_once(
    POLICY,
    "/// Stable identifier for the inactive S2-5 SEE capture-ordering candidate.\n"
    "pub const SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID: u64 = 0x5332_3553_4545_4f31;\n",
    "/// Stable identifier for the inactive S2-5 SEE capture-ordering candidate.\n"
    "pub const SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID: u64 = 0x5332_3553_4545_4f31;\n"
    "/// Stable identifier for the inactive S2-6 SEE quiescence-pruning candidate.\n"
    "pub const SEE_QUIESCENCE_PRUNING_SEARCH_POLICY_ID: u64 = 0x5332_3653_4545_5031;\n"
    "/// Stable identifier for the inactive S2-6 SEE-plus-delta candidate.\n"
    "pub const SEE_AND_DELTA_QUIESCENCE_PRUNING_SEARCH_POLICY_ID: u64 =\n"
    "    0x5332_3644_454c_5031;\n",
)
replace_once(
    POLICY,
    "    /// Inactive S2-5 SEE capture-ordering candidate.\n"
    "    pub const SEE_CAPTURE_ORDERING: Self = Self {\n"
    "        bits: ExperimentalSearchFeature::SeeCaptureOrdering.bit(),\n"
    "    };\n",
    "    /// Inactive S2-5 SEE capture-ordering candidate.\n"
    "    pub const SEE_CAPTURE_ORDERING: Self = Self {\n"
    "        bits: ExperimentalSearchFeature::SeeCaptureOrdering.bit(),\n"
    "    };\n"
    "    /// Inactive S2-6 SEE quiescence-pruning candidate.\n"
    "    pub const SEE_QUIESCENCE_PRUNING: Self = Self {\n"
    "        bits: ExperimentalSearchFeature::SeeQuiescencePruning.bit(),\n"
    "    };\n"
    "    /// Inactive S2-6 SEE pruning followed by delta pruning.\n"
    "    pub const SEE_AND_DELTA_QUIESCENCE_PRUNING: Self = Self {\n"
    "        bits: ExperimentalSearchFeature::SeeQuiescencePruning.bit()\n"
    "            | ExperimentalSearchFeature::DeltaPruning.bit(),\n"
    "    };\n",
)
replace_once(
    POLICY,
    "        FEATURES.into_iter().find_map(|(bit, feature)| {\n"
    "            (self.bits & bit != 0 && feature != ExperimentalSearchFeature::SeeCaptureOrdering)\n"
    "                .then_some(feature)\n"
    "        })\n",
    "        FEATURES.into_iter().find_map(|(bit, feature)| {\n"
    "            let implemented = matches!(\n"
    "                feature,\n"
    "                ExperimentalSearchFeature::SeeCaptureOrdering\n"
    "                    | ExperimentalSearchFeature::SeeQuiescencePruning\n"
    "                    | ExperimentalSearchFeature::DeltaPruning\n"
    "            );\n"
    "            (self.bits & bit != 0 && !implemented).then_some(feature)\n"
    "        })\n",
)
replace_once(
    POLICY,
    "    /// Inactive S2-5 candidate: v0.1 semantics plus SEE capture ordering.\n"
    "    pub const SEE_CAPTURE_ORDERING: Self = Self::new(SearchPolicyParameters {\n"
    "        alpha_beta: AlphaBetaMode::FullWindowFailSoft,\n"
    "        transposition: TranspositionPolicy::ClusteredFullKey,\n"
    "        move_ordering: MoveOrderingPolicy::V0_1MvvLvaKillersHistory,\n"
    "        quiescence: QuiescencePolicy::CapturesPromotionsAndEvasions,\n"
    "        aspiration_windows: true,\n"
    "        aspiration_half_width_centipawns: DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS as u16,\n"
    "        maximum_quiescence_ply: MAX_QUIESCENCE_PLY,\n"
    "        maximum_check_extensions_per_line: MAX_CHECK_EXTENSIONS_PER_LINE,\n"
    "        experimental_features: ExperimentalSearchFeatures::SEE_CAPTURE_ORDERING,\n"
    "    });\n",
    "    /// Inactive S2-5 candidate: v0.1 semantics plus SEE capture ordering.\n"
    "    pub const SEE_CAPTURE_ORDERING: Self = Self::new(SearchPolicyParameters {\n"
    "        alpha_beta: AlphaBetaMode::FullWindowFailSoft,\n"
    "        transposition: TranspositionPolicy::ClusteredFullKey,\n"
    "        move_ordering: MoveOrderingPolicy::V0_1MvvLvaKillersHistory,\n"
    "        quiescence: QuiescencePolicy::CapturesPromotionsAndEvasions,\n"
    "        aspiration_windows: true,\n"
    "        aspiration_half_width_centipawns: DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS as u16,\n"
    "        maximum_quiescence_ply: MAX_QUIESCENCE_PLY,\n"
    "        maximum_check_extensions_per_line: MAX_CHECK_EXTENSIONS_PER_LINE,\n"
    "        experimental_features: ExperimentalSearchFeatures::SEE_CAPTURE_ORDERING,\n"
    "    });\n\n"
    "    /// Inactive S2-6 candidate: baseline ordering plus conservative SEE pruning.\n"
    "    pub const SEE_QUIESCENCE_PRUNING: Self = Self::new(SearchPolicyParameters {\n"
    "        alpha_beta: AlphaBetaMode::FullWindowFailSoft,\n"
    "        transposition: TranspositionPolicy::ClusteredFullKey,\n"
    "        move_ordering: MoveOrderingPolicy::V0_1MvvLvaKillersHistory,\n"
    "        quiescence: QuiescencePolicy::CapturesPromotionsAndEvasions,\n"
    "        aspiration_windows: true,\n"
    "        aspiration_half_width_centipawns: DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS as u16,\n"
    "        maximum_quiescence_ply: MAX_QUIESCENCE_PLY,\n"
    "        maximum_check_extensions_per_line: MAX_CHECK_EXTENSIONS_PER_LINE,\n"
    "        experimental_features: ExperimentalSearchFeatures::SEE_QUIESCENCE_PRUNING,\n"
    "    });\n\n"
    "    /// Inactive S2-6 candidate: SEE pruning followed by bounded delta pruning.\n"
    "    pub const SEE_AND_DELTA_QUIESCENCE_PRUNING: Self =\n"
    "        Self::new(SearchPolicyParameters {\n"
    "            alpha_beta: AlphaBetaMode::FullWindowFailSoft,\n"
    "            transposition: TranspositionPolicy::ClusteredFullKey,\n"
    "            move_ordering: MoveOrderingPolicy::V0_1MvvLvaKillersHistory,\n"
    "            quiescence: QuiescencePolicy::CapturesPromotionsAndEvasions,\n"
    "            aspiration_windows: true,\n"
    "            aspiration_half_width_centipawns:\n"
    "                DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS as u16,\n"
    "            maximum_quiescence_ply: MAX_QUIESCENCE_PLY,\n"
    "            maximum_check_extensions_per_line: MAX_CHECK_EXTENSIONS_PER_LINE,\n"
    "            experimental_features:\n"
    "                ExperimentalSearchFeatures::SEE_AND_DELTA_QUIESCENCE_PRUNING,\n"
    "        });\n",
)
replace_once(
    POLICY,
    "    /// Returns whether the inactive S2-5 SEE ordering candidate is selected.\n"
    "    #[must_use]\n"
    "    pub const fn see_capture_ordering_enabled(self) -> bool {\n"
    "        self.parameters\n"
    "            .experimental_features\n"
    "            .contains(ExperimentalSearchFeature::SeeCaptureOrdering)\n"
    "    }\n",
    "    /// Returns whether the inactive S2-5 SEE ordering candidate is selected.\n"
    "    #[must_use]\n"
    "    pub const fn see_capture_ordering_enabled(self) -> bool {\n"
    "        self.parameters\n"
    "            .experimental_features\n"
    "            .contains(ExperimentalSearchFeature::SeeCaptureOrdering)\n"
    "    }\n\n"
    "    /// Returns whether conservative SEE pruning is selected in quiescence.\n"
    "    #[must_use]\n"
    "    pub const fn see_quiescence_pruning_enabled(self) -> bool {\n"
    "        self.parameters\n"
    "            .experimental_features\n"
    "            .contains(ExperimentalSearchFeature::SeeQuiescencePruning)\n"
    "    }\n\n"
    "    /// Returns whether bounded delta pruning is selected in quiescence.\n"
    "    #[must_use]\n"
    "    pub const fn delta_pruning_enabled(self) -> bool {\n"
    "        self.parameters\n"
    "            .experimental_features\n"
    "            .contains(ExperimentalSearchFeature::DeltaPruning)\n"
    "    }\n",
)
replace_once(
    POLICY,
    "        if let Some(feature) = self\n"
    "            .parameters\n"
    "            .experimental_features\n"
    "            .first_unsupported_enabled()\n"
    "        {\n"
    "            return Err(SearchPolicyValidationError::UnsupportedExperimentalFeature { feature });\n"
    "        }\n"
    "        Ok(())\n",
    "        if self.delta_pruning_enabled() && !self.see_quiescence_pruning_enabled() {\n"
    "            return Err(SearchPolicyValidationError::DeltaPruningRequiresSeePruning);\n"
    "        }\n"
    "        if let Some(feature) = self\n"
    "            .parameters\n"
    "            .experimental_features\n"
    "            .first_unsupported_enabled()\n"
    "        {\n"
    "            return Err(SearchPolicyValidationError::UnsupportedExperimentalFeature { feature });\n"
    "        }\n"
    "        Ok(())\n",
)
replace_once(
    POLICY,
    "    /// Returns the inactive S2-5 SEE capture-ordering candidate.\n"
    "    #[must_use]\n"
    "    pub fn see_capture_ordering_candidate() -> Self {\n"
    "        Self::new(\n"
    "            SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID,\n"
    "            SearchPolicy::SEE_CAPTURE_ORDERING,\n"
    "        )\n"
    "    }\n",
    "    /// Returns the inactive S2-5 SEE capture-ordering candidate.\n"
    "    #[must_use]\n"
    "    pub fn see_capture_ordering_candidate() -> Self {\n"
    "        Self::new(\n"
    "            SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID,\n"
    "            SearchPolicy::SEE_CAPTURE_ORDERING,\n"
    "        )\n"
    "    }\n\n"
    "    /// Returns the inactive S2-6 SEE quiescence-pruning candidate.\n"
    "    #[must_use]\n"
    "    pub fn see_quiescence_pruning_candidate() -> Self {\n"
    "        Self::new(\n"
    "            SEE_QUIESCENCE_PRUNING_SEARCH_POLICY_ID,\n"
    "            SearchPolicy::SEE_QUIESCENCE_PRUNING,\n"
    "        )\n"
    "    }\n\n"
    "    /// Returns the inactive S2-6 SEE-plus-delta quiescence candidate.\n"
    "    #[must_use]\n"
    "    pub fn see_and_delta_quiescence_pruning_candidate() -> Self {\n"
    "        Self::new(\n"
    "            SEE_AND_DELTA_QUIESCENCE_PRUNING_SEARCH_POLICY_ID,\n"
    "            SearchPolicy::SEE_AND_DELTA_QUIESCENCE_PRUNING,\n"
    "        )\n"
    "    }\n",
)
replace_once(
    POLICY,
    "    /// A known future feature was enabled before its implementation task.\n"
    "    UnsupportedExperimentalFeature { feature: ExperimentalSearchFeature },\n",
    "    /// Delta pruning was enabled without its required SEE-pruning predecessor.\n"
    "    DeltaPruningRequiresSeePruning,\n"
    "    /// A known future feature was enabled before its implementation task.\n"
    "    UnsupportedExperimentalFeature { feature: ExperimentalSearchFeature },\n",
)
replace_once(
    POLICY,
    "            Self::UnsupportedExperimentalFeature { feature } => write!(\n",
    "            Self::DeltaPruningRequiresSeePruning => formatter.write_str(\n"
    "                \"delta pruning requires SEE quiescence pruning in the same policy\",\n"
    "            ),\n"
    "            Self::UnsupportedExperimentalFeature { feature } => write!(\n",
)
replace_once(
    POLICY,
    "        SearchPolicyValidationError, SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID,\n"
    "        V0_1_SEARCH_POLICY_CHECKSUM,\n",
    "        SearchPolicyValidationError, SEE_AND_DELTA_QUIESCENCE_PRUNING_SEARCH_POLICY_ID,\n"
    "        SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID, SEE_QUIESCENCE_PRUNING_SEARCH_POLICY_ID,\n"
    "        V0_1_SEARCH_POLICY_CHECKSUM,\n",
)
replace_once(
    POLICY,
    "    #[test]\n"
    "    fn semantic_parameter_changes_change_the_checksum() {\n",
    "    #[test]\n"
    "    fn s2_6_quiescence_candidates_are_distinct_valid_and_inactive_by_default() {\n"
    "        let baseline = SearchPolicySet::baseline();\n"
    "        let see = SearchPolicySet::see_quiescence_pruning_candidate();\n"
    "        let delta = SearchPolicySet::see_and_delta_quiescence_pruning_candidate();\n"
    "        assert_eq!(see.identifier, SEE_QUIESCENCE_PRUNING_SEARCH_POLICY_ID);\n"
    "        assert_eq!(\n"
    "            delta.identifier,\n"
    "            SEE_AND_DELTA_QUIESCENCE_PRUNING_SEARCH_POLICY_ID\n"
    "        );\n"
    "        assert_eq!(see.validate(), Ok(()));\n"
    "        assert_eq!(delta.validate(), Ok(()));\n"
    "        assert!(!baseline.policy.see_quiescence_pruning_enabled());\n"
    "        assert!(see.policy.see_quiescence_pruning_enabled());\n"
    "        assert!(!see.policy.delta_pruning_enabled());\n"
    "        assert!(delta.policy.see_quiescence_pruning_enabled());\n"
    "        assert!(delta.policy.delta_pruning_enabled());\n"
    "        assert_ne!(baseline.checksum, see.checksum);\n"
    "        assert_ne!(see.checksum, delta.checksum);\n"
    "    }\n\n"
    "    #[test]\n"
    "    fn delta_pruning_without_see_pruning_fails_loudly() {\n"
    "        let mut parameters = SearchPolicy::V0_1.parameters();\n"
    "        parameters.experimental_features = ExperimentalSearchFeatures::from_bits(1 << 2)\n"
    "            .expect(\"delta feature bit is assigned\");\n"
    "        let invalid = SearchPolicySet::new(0x5332_3644_454c_5441, SearchPolicy::new(parameters));\n"
    "        assert_eq!(\n"
    "            invalid.validate(),\n"
    "            Err(SearchPolicyValidationError::DeltaPruningRequiresSeePruning)\n"
    "        );\n"
    "    }\n\n"
    "    #[test]\n"
    "    fn semantic_parameter_changes_change_the_checksum() {\n",
)
replace_once(
    POLICY,
    "        parameters.experimental_features = ExperimentalSearchFeatures::from_bits(1 << 1)\n"
    "            .expect(\"assigned feature bit is recognized\");\n",
    "        parameters.experimental_features = ExperimentalSearchFeatures::from_bits(1 << 3)\n"
    "            .expect(\"assigned feature bit is recognized\");\n",
)

# Alpha-beta passes the isolated quiescence policy into leaves.
replace_once(
    ALPHA_BETA,
    "        see_capture_ordering: policy.search_policy.see_capture_ordering_enabled(),\n"
    "        weights: policy.weights,\n",
    "        see_capture_ordering: policy.search_policy.see_capture_ordering_enabled(),\n"
    "        see_quiescence_pruning: policy.search_policy.see_quiescence_pruning_enabled(),\n"
    "        delta_pruning: policy.search_policy.delta_pruning_enabled(),\n"
    "        weights: policy.weights,\n",
)
replace_once(
    ALPHA_BETA,
    "    see_capture_ordering: bool,\n"
    "    weights: &'a EvaluationWeights,\n",
    "    see_capture_ordering: bool,\n"
    "    see_quiescence_pruning: bool,\n"
    "    delta_pruning: bool,\n"
    "    weights: &'a EvaluationWeights,\n",
)
replace_once(
    ALPHA_BETA,
    "                context.see_capture_ordering,\n"
    "                context.weights,\n",
    "                context.see_capture_ordering,\n"
    "                context.see_quiescence_pruning,\n"
    "                context.delta_pruning,\n"
    "                context.weights,\n",
)
replace_once(
    ALPHA_BETA,
    "            see_capture_ordering: false,\n"
    "            weights:",
    "            see_capture_ordering: false,\n"
    "            see_quiescence_pruning: false,\n"
    "            delta_pruning: false,\n"
    "            weights:",
    expected=3,
)

# Quiescence policy and conservative SEE pruning implementation.
replace_once(
    QUIESCENCE,
    "use chess_core::{Move, Position, SearchHistory};\n",
    "use chess_core::{\n"
    "    static_exchange_evaluation, Move, MoveKind, PieceKind, Position, SearchHistory,\n"
    "    StaticExchangeClass, StaticExchangeValue,\n"
    "};\n",
)
replace_once(
    QUIESCENCE,
    "/// Quiescence uses the normal alpha-beta result shape.\n"
    "pub type QuiescenceSearchResult = AlphaBetaSearchResult;\n",
    "/// Quiescence uses the normal alpha-beta result shape.\n"
    "pub type QuiescenceSearchResult = AlphaBetaSearchResult;\n\n"
    "/// S2-6 SEE pruning removes only captures below this strict threshold.\n"
    "pub const SEE_QUIESCENCE_PRUNE_THRESHOLD_CENTIPAWNS: i32 = -100;\n"
    "/// S2-6 delta-pruning margin used by the separately identified candidate.\n"
    "pub const DELTA_PRUNING_MARGIN_CENTIPAWNS: i32 = 200;\n",
)
replace_once(
    QUIESCENCE,
    "    see_capture_ordering: bool,\n"
    "    weights: &'a EvaluationWeights,\n",
    "    see_capture_ordering: bool,\n"
    "    see_quiescence_pruning: bool,\n"
    "    delta_pruning: bool,\n"
    "    weights: &'a EvaluationWeights,\n",
)
replace_once(
    QUIESCENCE,
    "        see_capture_ordering: bool,\n"
    "        weights: &'a EvaluationWeights,\n"
    "    ) -> Self {\n"
    "        Self {\n"
    "            alpha,\n"
    "            beta,\n"
    "            ordering,\n"
    "            see_capture_ordering,\n"
    "            weights,\n"
    "        }\n",
    "        see_capture_ordering: bool,\n"
    "        see_quiescence_pruning: bool,\n"
    "        delta_pruning: bool,\n"
    "        weights: &'a EvaluationWeights,\n"
    "    ) -> Self {\n"
    "        Self {\n"
    "            alpha,\n"
    "            beta,\n"
    "            ordering,\n"
    "            see_capture_ordering,\n"
    "            see_quiescence_pruning,\n"
    "            delta_pruning,\n"
    "            weights,\n"
    "        }\n",
)
replace_once(
    QUIESCENCE,
    "        QuiescenceSearchPolicy::new(alpha, beta, ordering, false, &EvaluationWeights::DEFAULT),\n",
    "        QuiescenceSearchPolicy::new(\n"
    "            alpha,\n"
    "            beta,\n"
    "            ordering,\n"
    "            false,\n"
    "            false,\n"
    "            false,\n"
    "            &EvaluationWeights::DEFAULT,\n"
    "        ),\n",
)
replace_once(
    QUIESCENCE,
    "        see_capture_ordering,\n"
    "        weights,\n"
    "    } = policy;\n",
    "        see_capture_ordering,\n"
    "        see_quiescence_pruning,\n"
    "        delta_pruning,\n"
    "        weights,\n"
    "    } = policy;\n",
)
replace_once(
    QUIESCENCE,
    "    let in_check = position.is_in_check(position.side_to_move());\n"
    "    let mut best_score = None;\n"
    "    let mut best_move = None;\n\n"
    "    if in_check {\n",
    "    let in_check = position.is_in_check(position.side_to_move());\n"
    "    let mut best_score = None;\n"
    "    let mut best_move = None;\n"
    "    let mut stand_pat = None;\n\n"
    "    if in_check {\n",
)
replace_once(
    QUIESCENCE,
    "        let stand_pat = evaluate_with_weights(position, weights);\n"
    "        best_score = Some(stand_pat);\n",
    "        let evaluated = evaluate_with_weights(position, weights);\n"
    "        stand_pat = Some(evaluated);\n"
    "        best_score = Some(evaluated);\n",
)
replace_once(QUIESCENCE, "        if stand_pat >= beta {\n", "        if evaluated >= beta {\n")
replace_once(QUIESCENCE, "                score: stand_pat,\n", "                score: evaluated,\n", expected=2)
replace_once(QUIESCENCE, "        if stand_pat > alpha {\n            alpha = stand_pat;\n", "        if evaluated > alpha {\n            alpha = evaluated;\n")
replace_once(
    QUIESCENCE,
    "    let mut searched_moves = 0_usize;\n"
    "    for token in ordered_tokens.iter() {\n",
    "    let tactical_move_count = if in_check {\n"
    "        0\n"
    "    } else {\n"
    "        tokens\n"
    "            .iter()\n"
    "            .filter(|token| is_tactical(token.move_made()))\n"
    "            .count()\n"
    "    };\n"
    "    let mate_sensitive = mate_sensitive_window(alpha, beta);\n"
    "    let mut searched_moves = 0_usize;\n"
    "    for token in ordered_tokens.iter() {\n",
)
replace_once(
    QUIESCENCE,
    "        let child_ply = context\n"
    "            .ply\n"
    "            .checked_add(1)\n"
    "            .filter(|next| *next <= MAX_MATE_PLY)\n"
    "            .ok_or(AlphaBetaSearchError::DepthTooLarge {\n"
    "                depth: context.ply.saturating_add(1),\n"
    "                maximum: MAX_MATE_PLY,\n"
    "            })?;\n"
    "        let child_context = QuiescenceContext {\n"
    "            ply: child_ply,\n"
    "            quiescence_ply: context.quiescence_ply + 1,\n"
    "            maximum_quiescence_ply: context.maximum_quiescence_ply,\n"
    "        };\n"
    "        let position_undo = position.make_legal_token(token)?;\n"
    "        let history_undo = history.push_position(position);\n",
    "        let see_value = if see_pruning_preconditions(\n"
    "            current,\n"
    "            in_check,\n"
    "            tactical_move_count,\n"
    "            mate_sensitive,\n"
    "            see_quiescence_pruning,\n"
    "        ) {\n"
    "            let value = static_exchange_evaluation(position, current)?;\n"
    "            record_see_value(value, &mut diagnostics, cancellation)?;\n"
    "            Some(value)\n"
    "        } else {\n"
    "            None\n"
    "        };\n"
    "        let delta_gain = delta_pruning_preconditions(\n"
    "            current,\n"
    "            in_check,\n"
    "            tactical_move_count,\n"
    "            mate_sensitive,\n"
    "            delta_pruning,\n"
    "        )\n"
    "        .then(|| maximum_material_gain(position, current))\n"
    "        .transpose()?;\n\n"
    "        let child_ply = context\n"
    "            .ply\n"
    "            .checked_add(1)\n"
    "            .filter(|next| *next <= MAX_MATE_PLY)\n"
    "            .ok_or(AlphaBetaSearchError::DepthTooLarge {\n"
    "                depth: context.ply.saturating_add(1),\n"
    "                maximum: MAX_MATE_PLY,\n"
    "            })?;\n"
    "        let child_context = QuiescenceContext {\n"
    "            ply: child_ply,\n"
    "            quiescence_ply: context.quiescence_ply + 1,\n"
    "            maximum_quiescence_ply: context.maximum_quiescence_ply,\n"
    "        };\n"
    "        let position_undo = position.make_legal_token(token)?;\n"
    "        let gives_check = position.is_in_check(position.side_to_move());\n"
    "        if !gives_check\n"
    "            && see_value.is_some_and(|value| {\n"
    "                value.centipawns() < SEE_QUIESCENCE_PRUNE_THRESHOLD_CENTIPAWNS\n"
    "            })\n"
    "        {\n"
    "            position.unmake_move(position_undo)?;\n"
    "            record_prune(\n"
    "                SearchDiagnosticEvent::QuiescenceSeePrune,\n"
    "                &mut diagnostics,\n"
    "                cancellation,\n"
    "            )?;\n"
    "            continue;\n"
    "        }\n"
    "        if !gives_check {\n"
    "            if let (Some(evaluated), Some(gain)) = (stand_pat, delta_gain) {\n"
    "                let attempt = SearchDiagnosticEvent::QuiescenceDeltaAttempt;\n"
    "                diagnostics.record_checked(attempt)?;\n"
    "                cancellation.on_search_diagnostic(attempt);\n"
    "                if delta_bound_cannot_raise_alpha(evaluated, gain, alpha) {\n"
    "                    position.unmake_move(position_undo)?;\n"
    "                    record_prune(\n"
    "                        SearchDiagnosticEvent::QuiescenceDeltaPrune,\n"
    "                        &mut diagnostics,\n"
    "                        cancellation,\n"
    "                    )?;\n"
    "                    continue;\n"
    "                }\n"
    "            }\n"
    "        }\n"
    "        let history_undo = history.push_position(position);\n",
)
replace_once(
    QUIESCENCE,
    "            QuiescenceSearchPolicy::new(\n"
    "                -beta,\n"
    "                -alpha,\n"
    "                ordering,\n"
    "                see_capture_ordering,\n"
    "                weights,\n"
    "            ),\n",
    "            QuiescenceSearchPolicy::new(\n"
    "                -beta,\n"
    "                -alpha,\n"
    "                ordering,\n"
    "                see_capture_ordering,\n"
    "                see_quiescence_pruning,\n"
    "                delta_pruning,\n"
    "                weights,\n"
    "            ),\n",
)
replace_once(
    QUIESCENCE,
    "const fn is_tactical(current: Move) -> bool {\n"
    "    current.kind().is_capture() || current.promotion().is_some()\n"
    "}\n",
    "fn record_see_value<Probe>(\n"
    "    value: StaticExchangeValue,\n"
    "    diagnostics: &mut SearchDiagnostics,\n"
    "    cancellation: &mut Probe,\n"
    ") -> Result<(), AlphaBetaSearchError>\n"
    "where\n"
    "    Probe: SearchCancellationProbe + ?Sized,\n"
    "{\n"
    "    for event in [\n"
    "        SearchDiagnosticEvent::SeeCall,\n"
    "        match value.class() {\n"
    "            StaticExchangeClass::Winning => SearchDiagnosticEvent::SeeWinningCapture,\n"
    "            StaticExchangeClass::Equal => SearchDiagnosticEvent::SeeEqualCapture,\n"
    "            StaticExchangeClass::Losing => SearchDiagnosticEvent::SeeLosingCapture,\n"
    "        },\n"
    "    ] {\n"
    "        diagnostics.record_checked(event)?;\n"
    "        cancellation.on_search_diagnostic(event);\n"
    "    }\n"
    "    Ok(())\n"
    "}\n\n"
    "fn record_prune<Probe>(\n"
    "    event: SearchDiagnosticEvent,\n"
    "    diagnostics: &mut SearchDiagnostics,\n"
    "    cancellation: &mut Probe,\n"
    ") -> Result<(), AlphaBetaSearchError>\n"
    "where\n"
    "    Probe: SearchCancellationProbe + ?Sized,\n"
    "{\n"
    "    diagnostics.record_checked(event)?;\n"
    "    cancellation.on_search_diagnostic(event);\n"
    "    Ok(())\n"
    "}\n\n"
    "fn see_pruning_preconditions(\n"
    "    current: Move,\n"
    "    in_check: bool,\n"
    "    tactical_move_count: usize,\n"
    "    mate_sensitive: bool,\n"
    "    enabled: bool,\n"
    ") -> bool {\n"
    "    enabled\n"
    "        && !in_check\n"
    "        && tactical_move_count > 1\n"
    "        && !mate_sensitive\n"
    "        && current.kind().is_capture()\n"
    "        && current.kind() != MoveKind::EnPassant\n"
    "        && current.promotion().is_none()\n"
    "}\n\n"
    "fn delta_pruning_preconditions(\n"
    "    current: Move,\n"
    "    in_check: bool,\n"
    "    tactical_move_count: usize,\n"
    "    mate_sensitive: bool,\n"
    "    enabled: bool,\n"
    ") -> bool {\n"
    "    enabled\n"
    "        && !in_check\n"
    "        && tactical_move_count > 1\n"
    "        && !mate_sensitive\n"
    "        && current.kind().is_capture()\n"
    "        && current.kind() != MoveKind::EnPassant\n"
    "        && current.promotion().is_none()\n"
    "}\n\n"
    "fn mate_sensitive_window(alpha: Score, beta: Score) -> bool {\n"
    "    let full_alpha = Score::mated_in(0).expect(\"zero-ply mate score exists\");\n"
    "    let full_beta = Score::mate_in(0).expect(\"zero-ply mate score exists\");\n"
    "    (alpha.is_mate() && alpha != full_alpha) || (beta.is_mate() && beta != full_beta)\n"
    "}\n\n"
    "fn maximum_material_gain(\n"
    "    position: &Position,\n"
    "    current: Move,\n"
    ") -> Result<i32, AlphaBetaSearchError> {\n"
    "    let captured = position\n"
    "        .piece_at(current.destination())\n"
    "        .ok_or_else(|| chess_core::StaticExchangeError::MoveStateContradiction(\n"
    "            chess_core::StaticExchangeMoveStateError::MissingCapturedPiece {\n"
    "                destination: current.destination(),\n"
    "            },\n"
    "        ))?;\n"
    "    Ok(delta_piece_value(captured.kind))\n"
    "}\n\n"
    "const fn delta_piece_value(kind: PieceKind) -> i32 {\n"
    "    match kind {\n"
    "        PieceKind::Pawn => 100,\n"
    "        PieceKind::Knight => 320,\n"
    "        PieceKind::Bishop => 330,\n"
    "        PieceKind::Rook => 500,\n"
    "        PieceKind::Queen => 900,\n"
    "        PieceKind::King => 20_000,\n"
    "    }\n"
    "}\n\n"
    "fn delta_bound_cannot_raise_alpha(stand_pat: Score, gain: i32, alpha: Score) -> bool {\n"
    "    i64::from(stand_pat.centipawns())\n"
    "        + i64::from(gain)\n"
    "        + i64::from(DELTA_PRUNING_MARGIN_CENTIPAWNS)\n"
    "        <= i64::from(alpha.centipawns())\n"
    "}\n\n"
    "const fn is_tactical(current: Move) -> bool {\n"
    "    current.kind().is_capture() || current.promotion().is_some()\n"
    "}\n",
)

# Add focused unit tests with direct policy control.
replace_once(
    QUIESCENCE,
    "#[cfg(test)]\nmod ordering_tests {\n",
    r'''#[cfg(test)]
mod s2_6_tests {
    use chess_core::{Position, SearchHistory};

    use super::{
        search_quiescence_node_with_weights, QuiescenceContext, QuiescenceSearchPolicy,
        MAX_QUIESCENCE_PLY,
    };
    use crate::{
        cancellation::NeverCancelled, move_ordering::MoveOrdering, AlphaBetaSearchError,
        EvaluationWeights, Score,
    };

    fn run(root: &Position, see_pruning: bool, delta_pruning: bool) -> super::QuiescenceSearchResult {
        let mut position = root.clone();
        let snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);
        let history_snapshot = history.clone();
        let mut cancellation = NeverCancelled;
        let result = search_quiescence_node_with_weights(
            &mut position,
            &mut history,
            QuiescenceContext {
                ply: 0,
                quiescence_ply: 0,
                maximum_quiescence_ply: MAX_QUIESCENCE_PLY,
            },
            QuiescenceSearchPolicy::new(
                Score::mated_in(0).expect("full alpha"),
                Score::mate_in(0).expect("full beta"),
                MoveOrdering::Tactical,
                false,
                see_pruning,
                delta_pruning,
                &EvaluationWeights::DEFAULT,
            ),
            &mut cancellation,
        )
        .expect("controlled quiescence search succeeds");
        assert_eq!(position, snapshot);
        assert_eq!(history, history_snapshot);
        assert_eq!(position.zobrist(), position.recomputed_zobrist());
        result
    }

    #[test]
    fn see_pruning_removes_a_losing_nonchecking_capture_without_changing_score() {
        let root: Position = "3r3k/8/8/3p3p/8/8/8/K2Q4 w - - 0 1"
            .parse()
            .expect("SEE-pruning fixture parses");
        let baseline = run(&root, false, false);
        let candidate = run(&root, true, false);
        assert_eq!(candidate.score(), baseline.score());
        assert!(candidate.qnodes() < baseline.qnodes());
        assert!(candidate.search_diagnostics().quiescence_see_prunes() > 0);
        assert_eq!(candidate.search_diagnostics().quiescence_delta_attempts(), 0);
        assert_eq!(candidate.search_diagnostics().quiescence_delta_prunes(), 0);
    }

    #[test]
    fn see_pruning_exclusions_preserve_sensitive_tactical_moves() {
        for (label, fen) in [
            ("in-check-evasion", "4r2k/8/8/8/8/8/8/4K3 w - - 0 1"),
            ("promotion", "7k/P7/8/8/8/8/8/K7 w - - 0 1"),
            ("en-passant", "4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1"),
            ("single-tactical-response", "3r3k/8/8/3p4/8/8/8/K2Q4 w - - 0 1"),
            ("checking-capture", "3r3k/8/8/8/8/8/8/K2Q4 w - - 0 1"),
        ] {
            let root: Position = fen.parse().unwrap_or_else(|error| panic!("{label}: {error}"));
            let baseline = run(&root, false, false);
            let candidate = run(&root, true, false);
            assert_eq!(candidate.score(), baseline.score(), "{label}");
            assert_eq!(
                candidate.search_diagnostics().quiescence_see_prunes(),
                0,
                "{label}"
            );
        }
    }

    #[test]
    fn guard_exhaustion_in_check_remains_fail_loud_with_pruning_enabled() {
        let mut position: Position = "4r2k/8/8/8/8/8/8/4K3 w - - 0 1"
            .parse()
            .expect("checked fixture parses");
        let snapshot = position.clone();
        let mut history = SearchHistory::from_position(&position);
        let history_snapshot = history.clone();
        let mut cancellation = NeverCancelled;
        let result = search_quiescence_node_with_weights(
            &mut position,
            &mut history,
            QuiescenceContext {
                ply: 0,
                quiescence_ply: 0,
                maximum_quiescence_ply: 0,
            },
            QuiescenceSearchPolicy::new(
                Score::mated_in(0).expect("full alpha"),
                Score::mate_in(0).expect("full beta"),
                MoveOrdering::Tactical,
                false,
                true,
                false,
                &EvaluationWeights::DEFAULT,
            ),
            &mut cancellation,
        );
        assert_eq!(
            result,
            Err(AlphaBetaSearchError::QuiescenceDepthLimitReachedInCheck {
                quiescence_ply: 0,
                maximum: 0,
            })
        );
        assert_eq!(position, snapshot);
        assert_eq!(history, history_snapshot);
    }
}

#[cfg(test)]
mod ordering_tests {
''',
)

# Diagnostics gain explicit delta attempts while preserving old zero-valued checksums.
DIAGNOSTICS = "crates/chess-search/src/diagnostics.rs"
for old, new in [
    ("    QuiescenceSeePrunes,\n    QuiescenceDeltaPrunes,\n", "    QuiescenceSeePrunes,\n    QuiescenceDeltaAttempts,\n    QuiescenceDeltaPrunes,\n"),
    ("            Self::QuiescenceSeePrunes => \"quiescence_see_prunes\",\n            Self::QuiescenceDeltaPrunes => \"quiescence_delta_prunes\",\n", "            Self::QuiescenceSeePrunes => \"quiescence_see_prunes\",\n            Self::QuiescenceDeltaAttempts => \"quiescence_delta_attempts\",\n            Self::QuiescenceDeltaPrunes => \"quiescence_delta_prunes\",\n"),
    ("    QuiescenceSeePrune,\n    QuiescenceDeltaPrune,\n", "    QuiescenceSeePrune,\n    QuiescenceDeltaAttempt,\n    QuiescenceDeltaPrune,\n"),
    ("    quiescence_see_prunes: u64,\n    quiescence_delta_prunes: u64,\n", "    quiescence_see_prunes: u64,\n    quiescence_delta_attempts: u64,\n    quiescence_delta_prunes: u64,\n"),
    ("        quiescence_see_prunes: 0,\n        quiescence_delta_prunes: 0,\n", "        quiescence_see_prunes: 0,\n        quiescence_delta_attempts: 0,\n        quiescence_delta_prunes: 0,\n"),
    ("            SearchDiagnosticEvent::QuiescenceSeePrune => increment_checked(\n                &mut self.quiescence_see_prunes,\n                SearchDiagnosticCounter::QuiescenceSeePrunes,\n            ),\n            SearchDiagnosticEvent::QuiescenceDeltaPrune => increment_checked(\n", "            SearchDiagnosticEvent::QuiescenceSeePrune => increment_checked(\n                &mut self.quiescence_see_prunes,\n                SearchDiagnosticCounter::QuiescenceSeePrunes,\n            ),\n            SearchDiagnosticEvent::QuiescenceDeltaAttempt => increment_checked(\n                &mut self.quiescence_delta_attempts,\n                SearchDiagnosticCounter::QuiescenceDeltaAttempts,\n            ),\n            SearchDiagnosticEvent::QuiescenceDeltaPrune => increment_checked(\n"),
    ("            quiescence_see_prunes: sum!(quiescence_see_prunes, QuiescenceSeePrunes),\n            quiescence_delta_prunes: sum!(quiescence_delta_prunes, QuiescenceDeltaPrunes),\n", "            quiescence_see_prunes: sum!(quiescence_see_prunes, QuiescenceSeePrunes),\n            quiescence_delta_attempts: sum!(\n                quiescence_delta_attempts,\n                QuiescenceDeltaAttempts\n            ),\n            quiescence_delta_prunes: sum!(quiescence_delta_prunes, QuiescenceDeltaPrunes),\n"),
    ("    pub const fn quiescence_see_prunes(self) -> u64 {\n        self.quiescence_see_prunes\n    }\n    #[must_use]\n    pub const fn quiescence_delta_prunes(self) -> u64 {\n", "    pub const fn quiescence_see_prunes(self) -> u64 {\n        self.quiescence_see_prunes\n    }\n    #[must_use]\n    pub const fn quiescence_delta_attempts(self) -> u64 {\n        self.quiescence_delta_attempts\n    }\n    #[must_use]\n    pub const fn quiescence_delta_prunes(self) -> u64 {\n"),
    ("            && self.quiescence_see_prunes == 0\n            && self.quiescence_delta_prunes == 0\n", "            && self.quiescence_see_prunes == 0\n            && self.quiescence_delta_attempts == 0\n            && self.quiescence_delta_prunes == 0\n"),
]:
    replace_once(DIAGNOSTICS, old, new)
replace_once(
    DIAGNOSTICS,
    "        if self.see_winning_captures != 0\n",
    "        if self.quiescence_delta_attempts != 0 {\n"
    "            hash = hash_bytes(hash, b\"quiescence-delta-attempts-v1\");\n"
    "            hash = hash_bytes(hash, &self.quiescence_delta_attempts.to_le_bytes());\n"
    "        }\n"
    "        if self.see_winning_captures != 0\n",
)

# Public exports.
replace_once(
    LIB,
    "    QuiescenceSearchResult, MAX_QUIESCENCE_PLY,\n",
    "    QuiescenceSearchResult, DELTA_PRUNING_MARGIN_CENTIPAWNS, MAX_QUIESCENCE_PLY,\n"
    "    SEE_QUIESCENCE_PRUNE_THRESHOLD_CENTIPAWNS,\n",
)
replace_once(
    LIB,
    "    MAXIMUM_CHECK_EXTENSIONS_PER_LINE, SEARCH_POLICY_SCHEMA_VERSION,\n"
    "    SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID, V0_1_SEARCH_POLICY_CHECKSUM, V0_1_SEARCH_POLICY_ID,\n",
    "    MAXIMUM_CHECK_EXTENSIONS_PER_LINE, SEARCH_POLICY_SCHEMA_VERSION,\n"
    "    SEE_AND_DELTA_QUIESCENCE_PRUNING_SEARCH_POLICY_ID,\n"
    "    SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID, SEE_QUIESCENCE_PRUNING_SEARCH_POLICY_ID,\n"
    "    V0_1_SEARCH_POLICY_CHECKSUM, V0_1_SEARCH_POLICY_ID,\n",
)

# Baseline contract and phase document.
write(
    "docs/RUST_CHESS_ENGINE_V0_2_S2_6_QUIESCENCE_2026-08-05.md",
    """# Rust Chess Engine v0.2 S2-6 Quiescence Redesign\n\n"
    "**Status:** In progress; baseline contract frozen and isolated candidates inactive\n"
    "**Task:** S2-6\n"
    "**Starting master:** `4174c2bf69f4e30b49b669960c33ec506197d425`\n\n"
    "## Frozen v0.1 contract\n\n"
    "The current quiescence implementation resolves terminal and rule-draw states before tactical expansion. Outside check, it evaluates stand-pat, permits a fail-soft stand-pat beta cutoff, raises alpha when appropriate, and searches legal captures plus every legal promotion. In check, stand-pat is forbidden and every legal evasion is searched, including quiet evasions.\n\n"
    "The tactical-ply guard returns stand-pat outside check. Reaching the same guard in check returns `QuiescenceDepthLimitReachedInCheck`; it never returns zero, static evaluation, or a partially searched score. Search cancellation and every error path must restore position, history, line length, and incremental Zobrist identity.\n\n"
    "## SEE-pruning candidate\n\n"
    "The first inactive S2-6 candidate preserves baseline MVV-LVA ordering and prunes only a non-promotion, non-en-passant capture whose SEE value is strictly less than `-100 cp`. It is disabled in check, in narrowed mate-score windows, when the node has only one legal tactical response, and when the move gives check. SEE failures propagate through the existing typed search error. Every evaluated SEE value is classified, and every omitted move increments `quiescence_see_prunes`.\n\n"
    "## Delta-pruning candidate boundary\n\n"
    "Delta pruning is represented by a separate identity that requires SEE pruning in the same policy. Its fixed margin is `200 cp`; it is evaluated only after a move survives SEE pruning. Initial exclusions match the SEE candidate and additionally require a typed captured-piece maximum gain. Delta attempts and prunes are counted separately. The candidate remains blocked from disposition until SEE pruning has stable correctness, performance, and strength evidence.\n\n"
    "Neither candidate is reachable from UCI, the default Rust facade, C ABI, JNI, or Android. All reports must retain `activated=false`.\n"
    """,
)

for path in [POLICY, ALPHA_BETA, QUIESCENCE, DIAGNOSTICS, LIB]:
    text = read(path)
    if "#[allow(" in text or "#[expect(" in text:
        raise SystemExit(f"{path}: first-party lint suppression detected")

print("S2-6 SEE quiescence patch applied")
