from pathlib import Path
import re


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one occurrence, found {count}")
    return text.replace(old, new, 1)


def replace_regex(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one block, found {count}")
    return updated


# Search policy identity and exact versioned parameters.
policy_path = Path("crates/chess-search/src/search_policy.rs")
policy = policy_path.read_text(encoding="utf-8")
policy = replace_once(
    policy,
    "/// Stable identifier for the inactive S2-7 Principal Variation Search candidate.\n"
    "pub const PRINCIPAL_VARIATION_SEARCH_POLICY_ID: u64 = 0x5332_3750_5653_3031;\n",
    "/// Stable identifier for the inactive S2-7 Principal Variation Search candidate.\n"
    "pub const PRINCIPAL_VARIATION_SEARCH_POLICY_ID: u64 = 0x5332_3750_5653_3031;\n"
    "/// Stable identifier for the inactive S2-8 Late Move Reductions candidate.\n"
    "pub const LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID: u64 = 0x5332_384c_4d52_3031;\n"
    "/// Smallest parent depth at which S2-8 may reduce a move.\n"
    "pub const LMR_MINIMUM_DEPTH: u16 = 4;\n"
    "/// Zero-based first move index eligible for S2-8 reduction.\n"
    "pub const LMR_MINIMUM_MOVE_INDEX: u16 = 4;\n"
    "/// Smallest legal move count at which S2-8 may reduce a move.\n"
    "pub const LMR_MINIMUM_LEGAL_MOVES: u16 = 6;\n"
    "/// Ordered `(minimum depth, minimum zero-based move index, reduction)` rules.\n"
    "pub const LMR_REDUCTION_TABLE: [(u16, u16, u16); 2] = [(4, 4, 1), (7, 8, 2)];\n",
    "LMR policy constants",
)
policy = replace_once(
    policy,
    "    /// Inactive S2-7 Principal Variation Search candidate.\n"
    "    pub const PRINCIPAL_VARIATION_SEARCH: Self = Self {\n"
    "        bits: ExperimentalSearchFeature::PrincipalVariationSearch.bit(),\n"
    "    };\n",
    "    /// Inactive S2-7 Principal Variation Search candidate.\n"
    "    pub const PRINCIPAL_VARIATION_SEARCH: Self = Self {\n"
    "        bits: ExperimentalSearchFeature::PrincipalVariationSearch.bit(),\n"
    "    };\n"
    "    /// Inactive S2-8 Late Move Reductions candidate.\n"
    "    pub const LATE_MOVE_REDUCTIONS: Self = Self {\n"
    "        bits: ExperimentalSearchFeature::LateMoveReductions.bit(),\n"
    "    };\n",
    "LMR feature set",
)
policy = replace_once(
    policy,
    "                    | ExperimentalSearchFeature::PrincipalVariationSearch\n",
    "                    | ExperimentalSearchFeature::PrincipalVariationSearch\n"
    "                    | ExperimentalSearchFeature::LateMoveReductions\n",
    "implemented LMR feature",
)
policy = replace_once(
    policy,
    "    /// Constructs explicit typed parameters for subsequent validation.\n",
    "    /// Inactive S2-8 candidate: baseline semantics plus bounded verified LMR.\n"
    "    pub const LATE_MOVE_REDUCTIONS: Self = Self::new(SearchPolicyParameters {\n"
    "        alpha_beta: AlphaBetaMode::FullWindowFailSoft,\n"
    "        transposition: TranspositionPolicy::ClusteredFullKey,\n"
    "        move_ordering: MoveOrderingPolicy::V0_1MvvLvaKillersHistory,\n"
    "        quiescence: QuiescencePolicy::CapturesPromotionsAndEvasions,\n"
    "        aspiration_windows: true,\n"
    "        aspiration_half_width_centipawns: DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS as u16,\n"
    "        maximum_quiescence_ply: MAX_QUIESCENCE_PLY,\n"
    "        maximum_check_extensions_per_line: MAX_CHECK_EXTENSIONS_PER_LINE,\n"
    "        experimental_features: ExperimentalSearchFeatures::LATE_MOVE_REDUCTIONS,\n"
    "    });\n\n"
    "    /// Constructs explicit typed parameters for subsequent validation.\n",
    "LMR SearchPolicy constant",
)
policy = replace_once(
    policy,
    "    /// Validates supported ranges and rejects not-yet-implemented features.\n",
    "    /// Returns whether the inactive S2-8 LMR candidate is selected.\n"
    "    #[must_use]\n"
    "    pub const fn late_move_reductions_enabled(self) -> bool {\n"
    "        self.parameters\n"
    "            .experimental_features\n"
    "            .contains(ExperimentalSearchFeature::LateMoveReductions)\n"
    "    }\n\n"
    "    /// Validates supported ranges and rejects not-yet-implemented features.\n",
    "LMR accessor",
)
policy = replace_once(
    policy,
    "        if let Some(feature) = self\n"
    "            .parameters\n"
    "            .experimental_features\n"
    "            .first_unsupported_enabled()\n"
    "        {\n",
    "        if self.late_move_reductions_enabled()\n"
    "            && self.parameters.experimental_features.bits()\n"
    "                != ExperimentalSearchFeatures::LATE_MOVE_REDUCTIONS.bits()\n"
    "        {\n"
    "            return Err(SearchPolicyValidationError::LateMoveReductionsMustBeIsolated);\n"
    "        }\n"
    "        if let Some(feature) = self\n"
    "            .parameters\n"
    "            .experimental_features\n"
    "            .first_unsupported_enabled()\n"
    "        {\n",
    "LMR isolation validation",
)
policy = replace_once(
    policy,
    "    /// Computes the canonical checksum.\n",
    "    /// Returns the inactive S2-8 Late Move Reductions candidate.\n"
    "    #[must_use]\n"
    "    pub fn late_move_reductions_candidate() -> Self {\n"
    "        Self::new(\n"
    "            LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID,\n"
    "            SearchPolicy::LATE_MOVE_REDUCTIONS,\n"
    "        )\n"
    "    }\n\n"
    "    /// Computes the canonical checksum.\n",
    "LMR candidate constructor",
)
policy = replace_once(
    policy,
    "        hash_bytes(hash, &parameters.experimental_features.bits().to_le_bytes())\n"
    "    }\n",
    "        hash = hash_bytes(hash, &parameters.experimental_features.bits().to_le_bytes());\n"
    "        if self.policy.late_move_reductions_enabled() {\n"
    "            hash = hash_bytes(hash, b\"s2-8-lmr-policy-v1\");\n"
    "            hash = hash_bytes(hash, &LMR_MINIMUM_DEPTH.to_le_bytes());\n"
    "            hash = hash_bytes(hash, &LMR_MINIMUM_MOVE_INDEX.to_le_bytes());\n"
    "            hash = hash_bytes(hash, &LMR_MINIMUM_LEGAL_MOVES.to_le_bytes());\n"
    "            for (minimum_depth, minimum_move_index, reduction) in LMR_REDUCTION_TABLE {\n"
    "                hash = hash_bytes(hash, &minimum_depth.to_le_bytes());\n"
    "                hash = hash_bytes(hash, &minimum_move_index.to_le_bytes());\n"
    "                hash = hash_bytes(hash, &reduction.to_le_bytes());\n"
    "            }\n"
    "        }\n"
    "        hash\n"
    "    }\n",
    "LMR checksum binding",
)
policy = replace_once(
    policy,
    "    /// A known future feature was enabled before its implementation task.\n"
    "    UnsupportedExperimentalFeature { feature: ExperimentalSearchFeature },\n",
    "    /// LMR was combined with another unevaluated experimental feature.\n"
    "    LateMoveReductionsMustBeIsolated,\n"
    "    /// A known future feature was enabled before its implementation task.\n"
    "    UnsupportedExperimentalFeature { feature: ExperimentalSearchFeature },\n",
    "LMR validation error",
)
policy = replace_once(
    policy,
    "            Self::UnsupportedExperimentalFeature { feature } => write!(\n",
    "            Self::LateMoveReductionsMustBeIsolated => formatter.write_str(\n"
    "                \"late move reductions must be evaluated as an isolated policy candidate\",\n"
    "            ),\n"
    "            Self::UnsupportedExperimentalFeature { feature } => write!(\n",
    "LMR validation display",
)
policy = replace_once(
    policy,
    "        SearchPolicyValidationError, SEE_AND_DELTA_QUIESCENCE_PRUNING_SEARCH_POLICY_ID,\n"
    "        SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID, SEE_QUIESCENCE_PRUNING_SEARCH_POLICY_ID,\n"
    "        V0_1_SEARCH_POLICY_CHECKSUM,\n",
    "        SearchPolicyValidationError, LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID,\n"
    "        SEE_AND_DELTA_QUIESCENCE_PRUNING_SEARCH_POLICY_ID,\n"
    "        SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID, SEE_QUIESCENCE_PRUNING_SEARCH_POLICY_ID,\n"
    "        V0_1_SEARCH_POLICY_CHECKSUM,\n",
    "LMR test imports",
)
policy = replace_once(
    policy,
    "    #[test]\n    fn delta_pruning_without_see_pruning_fails_loudly() {\n",
    "    #[test]\n"
    "    fn s2_8_lmr_candidate_is_distinct_valid_and_inactive_by_default() {\n"
    "        let baseline = SearchPolicySet::baseline();\n"
    "        let candidate = SearchPolicySet::late_move_reductions_candidate();\n"
    "        assert_eq!(candidate.identifier, LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID);\n"
    "        assert_eq!(candidate.validate(), Ok(()));\n"
    "        assert!(!baseline.policy.late_move_reductions_enabled());\n"
    "        assert!(candidate.policy.late_move_reductions_enabled());\n"
    "        assert_ne!(candidate.checksum, baseline.checksum);\n"
    "    }\n\n"
    "    #[test]\n    fn delta_pruning_without_see_pruning_fails_loudly() {\n",
    "LMR policy test",
)
policy = replace_once(
    policy,
    "        parameters.experimental_features = ExperimentalSearchFeatures::from_bits(1 << 4)\n",
    "        parameters.experimental_features = ExperimentalSearchFeatures::from_bits(1 << 5)\n",
    "unsupported feature witness",
)
policy_path.write_text(policy, encoding="utf-8")

# Diagnostics: preserve existing LMR counters, add explicit reduced fail-highs.
diagnostics_path = Path("crates/chess-search/src/diagnostics.rs")
diagnostics = diagnostics_path.read_text(encoding="utf-8")
diagnostics = replace_once(
    diagnostics,
    "    LmrReductions,\n    LmrResearches,\n",
    "    LmrReductions,\n    LmrReducedFailHighs,\n    LmrResearches,\n",
    "LMR counter enum",
)
diagnostics = replace_once(
    diagnostics,
    "            Self::LmrReductions => \"lmr_reductions\",\n"
    "            Self::LmrResearches => \"lmr_researches\",\n",
    "            Self::LmrReductions => \"lmr_reductions\",\n"
    "            Self::LmrReducedFailHighs => \"lmr_reduced_fail_highs\",\n"
    "            Self::LmrResearches => \"lmr_researches\",\n",
    "LMR counter display",
)
diagnostics = replace_once(
    diagnostics,
    "    LmrReduction,\n    LmrResearch,\n",
    "    LmrReduction,\n    LmrReducedFailHigh,\n    LmrResearch,\n",
    "LMR events",
)
diagnostics = replace_once(
    diagnostics,
    "    lmr_reductions: u64,\n    lmr_researches: u64,\n",
    "    lmr_reductions: u64,\n    lmr_reduced_fail_highs: u64,\n    lmr_researches: u64,\n",
    "LMR diagnostics field",
)
diagnostics = replace_once(
    diagnostics,
    "        lmr_reductions: 0,\n        lmr_researches: 0,\n",
    "        lmr_reductions: 0,\n        lmr_reduced_fail_highs: 0,\n        lmr_researches: 0,\n",
    "LMR diagnostics zero",
)
diagnostics = replace_once(
    diagnostics,
    "            SearchDiagnosticEvent::LmrReduction => increment_checked(\n"
    "                &mut self.lmr_reductions,\n"
    "                SearchDiagnosticCounter::LmrReductions,\n"
    "            ),\n"
    "            SearchDiagnosticEvent::LmrResearch => increment_checked(\n",
    "            SearchDiagnosticEvent::LmrReduction => increment_checked(\n"
    "                &mut self.lmr_reductions,\n"
    "                SearchDiagnosticCounter::LmrReductions,\n"
    "            ),\n"
    "            SearchDiagnosticEvent::LmrReducedFailHigh => increment_checked(\n"
    "                &mut self.lmr_reduced_fail_highs,\n"
    "                SearchDiagnosticCounter::LmrReducedFailHighs,\n"
    "            ),\n"
    "            SearchDiagnosticEvent::LmrResearch => increment_checked(\n",
    "LMR event recording",
)
diagnostics = replace_once(
    diagnostics,
    "            lmr_reductions: sum!(lmr_reductions, LmrReductions),\n"
    "            lmr_researches: sum!(lmr_researches, LmrResearches),\n",
    "            lmr_reductions: sum!(lmr_reductions, LmrReductions),\n"
    "            lmr_reduced_fail_highs: sum!(lmr_reduced_fail_highs, LmrReducedFailHighs),\n"
    "            lmr_researches: sum!(lmr_researches, LmrResearches),\n",
    "LMR checked addition",
)
diagnostics = replace_once(
    diagnostics,
    "    pub const fn lmr_reductions(self) -> u64 {\n"
    "        self.lmr_reductions\n"
    "    }\n"
    "    #[must_use]\n"
    "    pub const fn lmr_researches(self) -> u64 {\n",
    "    pub const fn lmr_reductions(self) -> u64 {\n"
    "        self.lmr_reductions\n"
    "    }\n"
    "    #[must_use]\n"
    "    pub const fn lmr_reduced_fail_highs(self) -> u64 {\n"
    "        self.lmr_reduced_fail_highs\n"
    "    }\n"
    "    #[must_use]\n"
    "    pub const fn lmr_researches(self) -> u64 {\n",
    "LMR getter",
)
diagnostics = replace_once(
    diagnostics,
    "    pub const fn lmr_researches(self) -> u64 {\n"
    "        self.lmr_researches\n"
    "    }\n",
    "    pub const fn lmr_researches(self) -> u64 {\n"
    "        self.lmr_researches\n"
    "    }\n"
    "    /// Alias naming the exact full-depth LMR verification count.\n"
    "    #[must_use]\n"
    "    pub const fn lmr_verification_searches(self) -> u64 {\n"
    "        self.lmr_researches\n"
    "    }\n",
    "LMR verification alias",
)
diagnostics = replace_once(
    diagnostics,
    "            && self.lmr_reductions == 0\n"
    "            && self.lmr_researches == 0\n",
    "            && self.lmr_reductions == 0\n"
    "            && self.lmr_reduced_fail_highs == 0\n"
    "            && self.lmr_researches == 0\n",
    "LMR reserved counters",
)
diagnostics = replace_once(
    diagnostics,
    "        if self.see_winning_captures != 0\n",
    "        if self.lmr_reduced_fail_highs != 0 {\n"
    "            hash = hash_bytes(hash, b\"lmr-reduced-fail-highs-v1\");\n"
    "            hash = hash_bytes(hash, &self.lmr_reduced_fail_highs.to_le_bytes());\n"
    "        }\n"
    "        if self.see_winning_captures != 0\n",
    "LMR checksum extension",
)
diagnostics = replace_once(
    diagnostics,
    "    #[test]\n    fn cutoff_events_are_deterministic_and_future_counters_stay_zero() {\n",
    "    #[test]\n"
    "    fn lmr_events_distinguish_reduction_fail_high_and_verification() {\n"
    "        let mut diagnostics = SearchDiagnostics::default();\n"
    "        for event in [\n"
    "            SearchDiagnosticEvent::LmrReduction,\n"
    "            SearchDiagnosticEvent::LmrReducedFailHigh,\n"
    "            SearchDiagnosticEvent::LmrResearch,\n"
    "        ] {\n"
    "            diagnostics.record_checked(event).expect(\"small counts fit\");\n"
    "        }\n"
    "        assert_eq!(diagnostics.lmr_reductions(), 1);\n"
    "        assert_eq!(diagnostics.lmr_reduced_fail_highs(), 1);\n"
    "        assert_eq!(diagnostics.lmr_verification_searches(), 1);\n"
    "    }\n\n"
    "    #[test]\n    fn cutoff_events_are_deterministic_and_future_counters_stay_zero() {\n",
    "LMR diagnostics test",
)
diagnostics_path.write_text(diagnostics, encoding="utf-8")

# Killer protection is explicit and allocation-free.
ordering_path = Path("crates/chess-search/src/move_ordering.rs")
ordering = ordering_path.read_text(encoding="utf-8")
ordering = replace_once(
    ordering,
    "    fn history_score(&self, color: Color, current: Move) -> u32 {\n",
    "    pub(crate) fn is_killer(&self, ply: u16, current: Move) -> bool {\n"
    "        let killers = self.killers(ply);\n"
    "        killers.primary == Some(current) || killers.secondary == Some(current)\n"
    "    }\n\n"
    "    fn history_score(&self, color: Color, current: Move) -> u32 {\n",
    "killer protection accessor",
)
ordering_path.write_text(ordering, encoding="utf-8")

# Main-search LMR integration.
search_path = Path("crates/chess-search/src/alpha_beta.rs")
search = search_path.read_text(encoding="utf-8")
search = replace_once(
    search,
    "    search_common::resolved_node_score,\n",
    "    search_common::resolved_node_score,\n"
    "    search_policy::{\n"
    "        LMR_MINIMUM_DEPTH, LMR_MINIMUM_LEGAL_MOVES, LMR_MINIMUM_MOVE_INDEX,\n"
    "        LMR_REDUCTION_TABLE,\n"
    "    },\n",
    "LMR constant imports",
)
search = replace_once(
    search,
    "        principal_variation_search: policy.search_policy.principal_variation_search_enabled(),\n",
    "        principal_variation_search: policy.search_policy.principal_variation_search_enabled(),\n"
    "        late_move_reductions: policy.search_policy.late_move_reductions_enabled(),\n",
    "LMR context activation",
)
search = replace_once(
    search,
    "    principal_variation_search: bool,\n",
    "    principal_variation_search: bool,\n    late_move_reductions: bool,\n",
    "LMR context field",
)
search = search.replace(
    "            principal_variation_search: false,\n",
    "            principal_variation_search: false,\n            late_move_reductions: false,\n",
)
search = replace_once(
    search,
    "    let mut best_score = None;\n    let mut best_move = None;\n\n"
    "    for (move_index, token) in ordered_tokens.iter().enumerate() {\n",
    "    let mut best_score = None;\n"
    "    let mut best_move = None;\n"
    "    let parent_in_check = position.is_in_check(position.side_to_move());\n"
    "    let legal_move_count = ordered_tokens.iter().len();\n\n"
    "    for (move_index, token) in ordered_tokens.iter().enumerate() {\n",
    "LMR node metadata",
)
search = replace_once(
    search,
    "        let current = token.move_made();\n"
    "        let position_undo = position.make_legal_token(token)?;\n",
    "        let current = token.move_made();\n"
    "        let protected_quiet_candidate = context.quiet_ordering.is_killer(ply, current);\n"
    "        let is_transposition_table_move = transposition_table_move == Some(current);\n"
    "        let position_undo = position.make_legal_token(token)?;\n",
    "LMR move protections",
)
search = replace_once(
    search,
    "        let child = search_child_with_optional_pvs(\n"
    "            position,\n"
    "            history,\n"
    "            PvsChildSearch {\n"
    "                depth: extension.child_depth(),\n"
    "                ply: ply + 1,\n"
    "                extension_budget: extension.remaining_budget(),\n"
    "                move_index,\n"
    "                alpha,\n"
    "                beta,\n"
    "            },\n"
    "            context,\n"
    "            &mut diagnostics,\n"
    "        );\n",
    "        let child = search_child_with_optional_lmr(\n"
    "            position,\n"
    "            history,\n"
    "            ChildSearch {\n"
    "                parent_depth: depth,\n"
    "                depth: extension.child_depth(),\n"
    "                ply: ply + 1,\n"
    "                extension_budget: extension.remaining_budget(),\n"
    "                move_index,\n"
    "                legal_move_count,\n"
    "                current,\n"
    "                parent_in_check,\n"
    "                child_in_check,\n"
    "                is_transposition_table_move,\n"
    "                protected_quiet_candidate,\n"
    "                alpha,\n"
    "                beta,\n"
    "            },\n"
    "            context,\n"
    "            &mut diagnostics,\n"
    "        );\n",
    "LMR child search call",
)
new_child_block = r'''#[derive(Clone, Copy)]
struct ChildSearch {
    parent_depth: u16,
    depth: u16,
    ply: u16,
    extension_budget: u16,
    move_index: usize,
    legal_move_count: usize,
    current: Move,
    parent_in_check: bool,
    child_in_check: bool,
    is_transposition_table_move: bool,
    protected_quiet_candidate: bool,
    alpha: Score,
    beta: Score,
}

fn search_child_with_optional_lmr<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    request: ChildSearch,
    context: &mut AlphaBetaContext<'_, Probe>,
    diagnostics: &mut SearchDiagnostics,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    let Some(reduction) = late_move_reduction(request, context.late_move_reductions) else {
        return search_child_with_optional_pvs(position, history, request, context, diagnostics);
    };

    let reduction_event = SearchDiagnosticEvent::LmrReduction;
    diagnostics.record_checked(reduction_event)?;
    context.cancellation.on_search_diagnostic(reduction_event);

    let mut reduced_request = request;
    reduced_request.depth -= reduction;
    let reduced = search_child_with_optional_pvs(
        position,
        history,
        reduced_request,
        context,
        diagnostics,
    )?;
    let reduced_parent_score = -reduced.score;
    if reduced_parent_score <= request.alpha {
        return Ok(reduced);
    }

    let fail_high_event = SearchDiagnosticEvent::LmrReducedFailHigh;
    diagnostics.record_checked(fail_high_event)?;
    context.cancellation.on_search_diagnostic(fail_high_event);
    let verification_event = SearchDiagnosticEvent::LmrResearch;
    diagnostics.record_checked(verification_event)?;
    context.cancellation.on_search_diagnostic(verification_event);
    let exact = search_child_with_optional_pvs(position, history, request, context, diagnostics)?;
    combine_lmr_attempts(reduced, exact)
}

fn late_move_reduction(request: ChildSearch, enabled: bool) -> Option<u16> {
    if !enabled
        || request.parent_depth < LMR_MINIMUM_DEPTH
        || request.move_index == 0
        || request.parent_in_check
        || request.child_in_check
        || request.is_transposition_table_move
        || request.protected_quiet_candidate
        || request.current.kind().is_capture()
        || request.current.promotion().is_some()
    {
        return None;
    }
    let Ok(move_index) = u16::try_from(request.move_index) else {
        return None;
    };
    let Ok(legal_move_count) = u16::try_from(request.legal_move_count) else {
        return None;
    };
    if move_index < LMR_MINIMUM_MOVE_INDEX || legal_move_count < LMR_MINIMUM_LEGAL_MOVES {
        return None;
    }

    let mut selected = 0_u16;
    for (minimum_depth, minimum_move_index, reduction) in LMR_REDUCTION_TABLE {
        if request.parent_depth >= minimum_depth && move_index >= minimum_move_index {
            selected = reduction;
        }
    }
    let maximum = request.depth.saturating_sub(1);
    let bounded = selected.min(maximum);
    (bounded > 0).then_some(bounded)
}

fn search_child_with_optional_pvs<Probe>(
    position: &mut Position,
    history: &mut SearchHistory,
    request: ChildSearch,
    context: &mut AlphaBetaContext<'_, Probe>,
    diagnostics: &mut SearchDiagnostics,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>
where
    Probe: SearchCancellationProbe + ?Sized,
{
    let ChildSearch {
        depth,
        ply,
        extension_budget,
        move_index,
        alpha,
        beta,
        ..
    } = request;
    let full_window = AlphaBetaWindow {
        alpha: -beta,
        beta: -alpha,
    };
    if !context.principal_variation_search || move_index == 0 {
        return search_node_with_extensions(
            position,
            history,
            depth,
            ply,
            extension_budget,
            full_window,
            context,
        );
    }

    let zero_window_event = SearchDiagnosticEvent::PvsZeroWindowSearch;
    diagnostics.record_checked(zero_window_event)?;
    context.cancellation.on_search_diagnostic(zero_window_event);
    let zero_window = AlphaBetaWindow::pvs_child(alpha)?;
    let narrow = search_node_with_extensions(
        position,
        history,
        depth,
        ply,
        extension_budget,
        zero_window,
        context,
    )?;
    let narrow_parent_score = -narrow.score;
    if narrow_parent_score <= alpha || narrow_parent_score >= beta {
        return Ok(narrow);
    }

    let research_event = SearchDiagnosticEvent::PvsResearch;
    diagnostics.record_checked(research_event)?;
    context.cancellation.on_search_diagnostic(research_event);
    let exact = search_node_with_extensions(
        position,
        history,
        depth,
        ply,
        extension_budget,
        full_window,
        context,
    )?;
    combine_pvs_attempts(narrow, exact)
}

fn combine_pvs_attempts(
    narrow: AlphaBetaSearchResult,
    exact: AlphaBetaSearchResult,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError> {
    combine_search_attempts(narrow, exact)
}

fn combine_lmr_attempts(
    reduced: AlphaBetaSearchResult,
    exact: AlphaBetaSearchResult,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError> {
    combine_search_attempts(reduced, exact)
}

fn combine_search_attempts(
    first: AlphaBetaSearchResult,
    exact: AlphaBetaSearchResult,
) -> Result<AlphaBetaSearchResult, AlphaBetaSearchError> {
    Ok(AlphaBetaSearchResult {
        score: exact.score,
        best_move: exact.best_move,
        nodes: first
            .nodes
            .checked_add(exact.nodes)
            .ok_or(AlphaBetaSearchError::NodeCountOverflow)?,
        qnodes: first
            .qnodes
            .checked_add(exact.qnodes)
            .ok_or(AlphaBetaSearchError::NodeCountOverflow)?,
        selective_depth: first.selective_depth.max(exact.selective_depth),
        diagnostics: first.diagnostics.checked_add(exact.diagnostics)?,
    })
}

'''
search = replace_regex(
    search,
    r"#\[derive\(Clone, Copy\)\]\nstruct PvsChildSearch \{.*?\nfn transposition_score_reuse\(",
    new_child_block + "fn transposition_score_reuse(",
    "child search implementation",
)
# Add pure reduction-policy tests before existing ordering tests.
lmr_tests = r'''#[cfg(test)]
mod lmr_policy_tests {
    use chess_core::Position;

    use super::{late_move_reduction, ChildSearch};
    use crate::Score;

    fn quiet_move(fen: &str, uci: &str) -> chess_core::Move {
        let mut position = Position::from_fen(fen).expect("fixture parses");
        position
            .legal_moves()
            .expect("legal moves generate")
            .iter()
            .find(|current| current.to_uci() == uci)
            .expect("fixture move exists")
    }

    fn request(current: chess_core::Move) -> ChildSearch {
        ChildSearch {
            parent_depth: 4,
            depth: 3,
            ply: 1,
            extension_budget: 0,
            move_index: 4,
            legal_move_count: 20,
            current,
            parent_in_check: false,
            child_in_check: false,
            is_transposition_table_move: false,
            protected_quiet_candidate: false,
            alpha: Score::from_raw(-20).expect("score fits"),
            beta: Score::from_raw(20).expect("score fits"),
        }
    }

    #[test]
    fn reduction_table_is_bounded_and_deterministic() {
        let current = quiet_move(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "e2e4",
        );
        assert_eq!(late_move_reduction(request(current), true), Some(1));
        let mut deep = request(current);
        deep.parent_depth = 7;
        deep.depth = 6;
        deep.move_index = 8;
        assert_eq!(late_move_reduction(deep, true), Some(2));
        deep.depth = 1;
        assert_eq!(late_move_reduction(deep, true), None);
        assert_eq!(late_move_reduction(request(current), false), None);
    }

    #[test]
    fn tactical_and_low_mobility_moves_are_never_reduced() {
        let quiet = quiet_move(
            "rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            "e2e4",
        );
        let mut protected = request(quiet);
        protected.parent_in_check = true;
        assert_eq!(late_move_reduction(protected, true), None);
        protected = request(quiet);
        protected.child_in_check = true;
        assert_eq!(late_move_reduction(protected, true), None);
        protected = request(quiet);
        protected.is_transposition_table_move = true;
        assert_eq!(late_move_reduction(protected, true), None);
        protected = request(quiet);
        protected.protected_quiet_candidate = true;
        assert_eq!(late_move_reduction(protected, true), None);
        protected = request(quiet);
        protected.legal_move_count = 5;
        assert_eq!(late_move_reduction(protected, true), None);

        let capture = quiet_move("4k3/8/2p5/3p4/4P3/8/8/4K3 w - - 0 1", "e4d5");
        assert_eq!(late_move_reduction(request(capture), true), None);
        let promotion = quiet_move("7k/P7/8/8/8/8/8/K7 w - - 0 1", "a7a8q");
        assert_eq!(late_move_reduction(request(promotion), true), None);
    }
}

'''
search = replace_once(
    search,
    "#[cfg(test)]\nmod ordering_tests {\n",
    lmr_tests + "#[cfg(test)]\nmod ordering_tests {\n",
    "LMR policy unit tests",
)
search_path.write_text(search, encoding="utf-8")

# Public candidate identity and parameter exports.
lib_path = Path("crates/chess-search/src/lib.rs")
lib = lib_path.read_text(encoding="utf-8")
lib = replace_once(
    lib,
    "    MAXIMUM_CHECK_EXTENSIONS_PER_LINE, PRINCIPAL_VARIATION_SEARCH_POLICY_ID,\n"
    "    SEARCH_POLICY_SCHEMA_VERSION, SEE_AND_DELTA_QUIESCENCE_PRUNING_SEARCH_POLICY_ID,\n",
    "    LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID, LMR_MINIMUM_DEPTH,\n"
    "    LMR_MINIMUM_LEGAL_MOVES, LMR_MINIMUM_MOVE_INDEX, LMR_REDUCTION_TABLE,\n"
    "    MAXIMUM_CHECK_EXTENSIONS_PER_LINE, PRINCIPAL_VARIATION_SEARCH_POLICY_ID,\n"
    "    SEARCH_POLICY_SCHEMA_VERSION, SEE_AND_DELTA_QUIESCENCE_PRUNING_SEARCH_POLICY_ID,\n",
    "LMR public exports",
)
lib_path.write_text(lib, encoding="utf-8")

# Focused integration coverage.
test_content = r'''use chess_core::{Move, Position, SearchHistory};
use chess_search::{
    iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights,
    EvaluationWeights, SearchLimits, SearchPolicySet, SearchResult, TranspositionTable,
    LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID, LMR_MINIMUM_DEPTH, LMR_MINIMUM_LEGAL_MOVES,
    LMR_MINIMUM_MOVE_INDEX, LMR_REDUCTION_TABLE,
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
fn candidate_identity_and_parameters_are_explicit_and_inactive_by_default() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::late_move_reductions_candidate();
    baseline.validate().expect("baseline policy validates");
    candidate.validate().expect("candidate policy validates");
    assert_eq!(candidate.identifier, LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID);
    assert_eq!(LMR_MINIMUM_DEPTH, 4);
    assert_eq!(LMR_MINIMUM_MOVE_INDEX, 4);
    assert_eq!(LMR_MINIMUM_LEGAL_MOVES, 6);
    assert_eq!(LMR_REDUCTION_TABLE, [(4, 4, 1), (7, 8, 2)]);
    assert!(!baseline.policy.late_move_reductions_enabled());
    assert!(candidate.policy.late_move_reductions_enabled());
    assert_ne!(baseline.checksum, candidate.checksum);
}

#[test]
fn candidate_preserves_tactical_mate_promotion_and_endgame_fixtures() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::late_move_reductions_candidate();
    for (fen, depth) in [
        ("7k/5Q2/6K1/8/8/8/8/8 w - - 0 1", 4),
        ("4Q2k/8/4K3/8/8/8/8/8 b - - 0 1", 6),
        ("7k/P7/6K1/8/8/8/8/8 w - - 0 1", 5),
        ("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1", 5),
        ("8/2p5/3p4/KP5r/1R3p1k/8/4P1P1/8 w - - 0 1", 5),
        ("3rk3/8/8/8/8/8/8/K2Q4 w - - 0 1", 5),
        (
            "r2q1rk1/ppp2ppp/2npbn2/3Np3/2B1P3/2P2N2/PP3PPP/R1BQR1K1 w - - 0 10",
            5,
        ),
    ] {
        let baseline_result = run(fen, SearchLimits::new().with_depth(depth), &baseline);
        let candidate_result = run(fen, SearchLimits::new().with_depth(depth), &candidate);
        assert_eq!(candidate_result.score(), baseline_result.score(), "{fen}");
        assert_eq!(
            candidate_result.completed_depth(),
            baseline_result.completed_depth(),
            "{fen}"
        );
        assert_eq!(candidate_result.best_move(), baseline_result.best_move(), "{fen}");
    }
}

#[test]
fn candidate_reduces_only_late_moves_and_verifies_every_reduced_alpha_raise() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::late_move_reductions_candidate();
    let fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1";
    let baseline_result = run(fen, SearchLimits::new().with_depth(5), &baseline);
    let candidate_result = run(fen, SearchLimits::new().with_depth(5), &candidate);
    let baseline_diagnostics = baseline_result.search_diagnostics();
    let diagnostics = candidate_result.search_diagnostics();
    assert_eq!(baseline_diagnostics.lmr_reductions(), 0);
    assert_eq!(baseline_diagnostics.lmr_reduced_fail_highs(), 0);
    assert_eq!(baseline_diagnostics.lmr_verification_searches(), 0);
    assert!(diagnostics.lmr_reductions() > 0);
    assert_eq!(
        diagnostics.lmr_reduced_fail_highs(),
        diagnostics.lmr_verification_searches()
    );
    assert!(diagnostics.lmr_verification_searches() <= diagnostics.lmr_reductions());
    assert_eq!(candidate_result.score(), baseline_result.score());
    assert_eq!(candidate_result.best_move(), baseline_result.best_move());
}

#[test]
fn node_limited_cancellation_restores_state_and_keeps_only_completed_iterations() {
    let candidate = SearchPolicySet::late_move_reductions_candidate();
    let fen = "r2q1rk1/ppp2ppp/2npbn2/3Np3/2B1P3/2P2N2/PP3PPP/R1BQR1K1 w - - 0 10";
    let limited = run(
        fen,
        SearchLimits::new().with_depth(9).with_nodes(768),
        &candidate,
    );
    assert!(limited.completed_depth() < 9);
    assert!(limited.nodes() <= 768);
    for iteration in limited.completed().iterations() {
        assert!(iteration.best_move().is_some());
        assert!(!iteration.search_diagnostics().overflowed());
        assert_eq!(
            iteration.search_diagnostics().lmr_reduced_fail_highs(),
            iteration.search_diagnostics().lmr_verification_searches()
        );
    }
}
'''
Path("crates/chess-search/tests/s2_8_lmr.rs").write_text(test_content, encoding="utf-8")

# Permanent fail-closed source audit.
audit = r'''#!/usr/bin/env bash
set -euo pipefail

fail() {
  echo "S2-8 LMR audit failed: $*" >&2
  exit 1
}

policy="crates/chess-search/src/search_policy.rs"
search="crates/chess-search/src/alpha_beta.rs"
diagnostics="crates/chess-search/src/diagnostics.rs"
ordering="crates/chess-search/src/move_ordering.rs"
lib="crates/chess-search/src/lib.rs"
tests="crates/chess-search/tests/s2_8_lmr.rs"

for path in "$policy" "$search" "$diagnostics" "$ordering" "$lib" "$tests"; do
  [[ -f "$path" ]] || fail "missing $path"
done

grep -q 'pub const LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID' "$policy" || fail "missing LMR identity"
grep -q 'pub const LMR_MINIMUM_DEPTH: u16 = 4' "$policy" || fail "missing minimum depth"
grep -q 'pub const LMR_MINIMUM_MOVE_INDEX: u16 = 4' "$policy" || fail "missing minimum move index"
grep -q 'pub const LMR_MINIMUM_LEGAL_MOVES: u16 = 6' "$policy" || fail "missing low-mobility guard"
grep -q 'pub const LMR_REDUCTION_TABLE.*(4, 4, 1).*(7, 8, 2)' "$policy" || fail "missing bounded reduction table"
grep -q 'late_move_reductions_enabled' "$policy" || fail "missing LMR accessor"
grep -q 'LateMoveReductionsMustBeIsolated' "$policy" || fail "missing isolated-candidate validation"
grep -q 'SearchPolicy::V0_1' "$search" || fail "baseline convenience path no longer explicit"
grep -q 'current.kind().is_capture()' "$search" || fail "captures are not protected"
grep -q 'current.promotion().is_some()' "$search" || fail "promotions are not protected"
grep -q 'parent_in_check' "$search" || fail "in-check nodes are not protected"
grep -q 'child_in_check' "$search" || fail "checking moves are not protected"
grep -q 'is_transposition_table_move' "$search" || fail "TT moves are not protected"
grep -q 'protected_quiet_candidate' "$search" || fail "killer candidates are not protected"
grep -q 'legal_move_count' "$search" || fail "low-mobility nodes are not protected"
grep -q 'SearchDiagnosticEvent::LmrReduction' "$search" || fail "missing reduction diagnostic"
grep -q 'SearchDiagnosticEvent::LmrReducedFailHigh' "$search" || fail "missing reduced fail-high diagnostic"
grep -q 'SearchDiagnosticEvent::LmrResearch' "$search" || fail "missing verification diagnostic"
grep -q 'reduced_parent_score <= request.alpha' "$search" || fail "missing alpha-raise verification boundary"
grep -q 'combine_lmr_attempts' "$search" || fail "missing exact attempt accounting"
grep -q 'LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID' "$lib" || fail "missing public LMR identity export"
grep -q 'lmr_reduced_fail_highs' "$diagnostics" || fail "missing reduced fail-high counter"
grep -q 'lmr_verification_searches' "$diagnostics" || fail "missing verification counter alias"

if grep -R --line-number --fixed-strings 'late_move_reductions: true' crates/chess-search/src; then
  fail "LMR is hard-coded active"
fi
if grep -R --line-number -E 'unwrap_or\(|unwrap_or_default\(|\.ok\(\)' crates/chess-search/src/alpha_beta.rs | grep -i lmr; then
  fail "LMR contains a silent fallback"
fi

echo "S2-8 LMR audit passed"
'''
Path("scripts/task_s2_8_lmr_audit.sh").write_text(audit, encoding="utf-8")

# Do not retain the bootstrap payload in the implementation commit.
Path(".github/s2_8_core_bootstrap.py").unlink()
Path(".github/workflows/s2-8-core-bootstrap.yml").unlink()
