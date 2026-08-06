from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    target = Path(path)
    text = target.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one occurrence, found {count}: {old[:80]!r}")
    target.write_text(text.replace(old, new, 1), encoding="utf-8")


# Search policy: isolated candidate identity and frozen parameters.
policy = "crates/chess-search/src/search_policy.rs"
replace_once(
    policy,
    "/// Stable identifier for the inactive S2-9 null-move pruning candidate.\npub const NULL_MOVE_PRUNING_SEARCH_POLICY_ID: u64 = 0x5332_394e_4d50_3031;\n",
    "/// Stable identifier for the inactive S2-9 null-move pruning candidate.\npub const NULL_MOVE_PRUNING_SEARCH_POLICY_ID: u64 = 0x5332_394e_4d50_3031;\n/// Stable identifier for the inactive S2-10.1 frontier-futility candidate.\npub const FUTILITY_PRUNING_SEARCH_POLICY_ID: u64 = 0x5332_3130_4655_5431;\n/// Largest remaining depth at which frontier futility may be considered.\npub const FUTILITY_PRUNING_MAXIMUM_DEPTH: u16 = 1;\n/// Frozen optimistic material margin for the isolated frontier-futility candidate.\npub const FUTILITY_PRUNING_MARGIN_CENTIPAWNS: u16 = 150;\n",
)
replace_once(
    policy,
    "    /// Inactive S2-9 conservative null-move pruning candidate.\n    pub const NULL_MOVE_PRUNING: Self = Self {\n        bits: ExperimentalSearchFeature::NullMovePruning.bit(),\n    };\n",
    "    /// Inactive S2-9 conservative null-move pruning candidate.\n    pub const NULL_MOVE_PRUNING: Self = Self {\n        bits: ExperimentalSearchFeature::NullMovePruning.bit(),\n    };\n    /// Inactive S2-10.1 conservative frontier-futility candidate.\n    pub const FUTILITY_PRUNING: Self = Self {\n        bits: ExperimentalSearchFeature::FutilityPruning.bit(),\n    };\n",
)
replace_once(
    policy,
    "                    | ExperimentalSearchFeature::LateMoveReductions\n                    | ExperimentalSearchFeature::NullMovePruning\n",
    "                    | ExperimentalSearchFeature::LateMoveReductions\n                    | ExperimentalSearchFeature::NullMovePruning\n                    | ExperimentalSearchFeature::FutilityPruning\n",
)
replace_once(
    policy,
    "    /// Constructs explicit typed parameters for subsequent validation.\n",
    "    /// Inactive S2-10.1 candidate: baseline semantics plus frontier futility.\n    pub const FUTILITY_PRUNING: Self = Self::new(SearchPolicyParameters {\n        alpha_beta: AlphaBetaMode::FullWindowFailSoft,\n        transposition: TranspositionPolicy::ClusteredFullKey,\n        move_ordering: MoveOrderingPolicy::V0_1MvvLvaKillersHistory,\n        quiescence: QuiescencePolicy::CapturesPromotionsAndEvasions,\n        aspiration_windows: true,\n        aspiration_half_width_centipawns: DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS as u16,\n        maximum_quiescence_ply: MAX_QUIESCENCE_PLY,\n        maximum_check_extensions_per_line: MAX_CHECK_EXTENSIONS_PER_LINE,\n        experimental_features: ExperimentalSearchFeatures::FUTILITY_PRUNING,\n    });\n\n    /// Constructs explicit typed parameters for subsequent validation.\n",
)
replace_once(
    policy,
    "    /// Validates supported ranges and rejects not-yet-implemented features.\n",
    "    /// Returns whether the inactive S2-10.1 frontier-futility candidate is selected.\n    #[must_use]\n    pub const fn futility_pruning_enabled(self) -> bool {\n        self.parameters\n            .experimental_features\n            .contains(ExperimentalSearchFeature::FutilityPruning)\n    }\n\n    /// Validates supported ranges and rejects not-yet-implemented features.\n",
)
replace_once(
    policy,
    "        if let Some(feature) = self\n",
    "        if self.futility_pruning_enabled()\n            && self.parameters.experimental_features.bits()\n                != ExperimentalSearchFeatures::FUTILITY_PRUNING.bits()\n        {\n            return Err(SearchPolicyValidationError::FutilityPruningMustBeIsolated);\n        }\n        if let Some(feature) = self\n",
)
replace_once(
    policy,
    "    /// Computes the canonical checksum.\n",
    "    /// Returns the inactive S2-10.1 frontier-futility candidate.\n    #[must_use]\n    pub fn futility_pruning_candidate() -> Self {\n        Self::new(\n            FUTILITY_PRUNING_SEARCH_POLICY_ID,\n            SearchPolicy::FUTILITY_PRUNING,\n        )\n    }\n\n    /// Computes the canonical checksum.\n",
)
replace_once(
    policy,
    "        if self.policy.null_move_pruning_enabled() {\n",
    "        if self.policy.futility_pruning_enabled() {\n            hash = hash_bytes(hash, b\"s2-10-frontier-futility-policy-v1\");\n            hash = hash_bytes(hash, &FUTILITY_PRUNING_MAXIMUM_DEPTH.to_le_bytes());\n            hash = hash_bytes(hash, &FUTILITY_PRUNING_MARGIN_CENTIPAWNS.to_le_bytes());\n        }\n        if self.policy.null_move_pruning_enabled() {\n",
)
replace_once(
    policy,
    "    /// Null move was combined with another unevaluated feature.\n    NullMovePruningMustBeIsolated,\n",
    "    /// Null move was combined with another unevaluated feature.\n    NullMovePruningMustBeIsolated,\n    /// Frontier futility was combined with another unevaluated feature.\n    FutilityPruningMustBeIsolated,\n",
)
replace_once(
    policy,
    "            Self::NullMovePruningMustBeIsolated => formatter.write_str(\n                \"null-move pruning must be evaluated as an isolated policy candidate\",\n            ),\n",
    "            Self::NullMovePruningMustBeIsolated => formatter.write_str(\n                \"null-move pruning must be evaluated as an isolated policy candidate\",\n            ),\n            Self::FutilityPruningMustBeIsolated => formatter.write_str(\n                \"frontier futility pruning must be evaluated as an isolated policy candidate\",\n            ),\n",
)
replace_once(
    policy,
    "        SearchPolicyValidationError, LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID,\n",
    "        SearchPolicyValidationError, FUTILITY_PRUNING_SEARCH_POLICY_ID,\n        LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID,\n",
)
replace_once(
    policy,
    "    #[test]\n    fn delta_pruning_without_see_pruning_fails_loudly() {\n",
    "    #[test]\n    fn s2_10_futility_candidate_is_distinct_valid_and_inactive_by_default() {\n        let baseline = SearchPolicySet::baseline();\n        let candidate = SearchPolicySet::futility_pruning_candidate();\n        assert_eq!(candidate.identifier, FUTILITY_PRUNING_SEARCH_POLICY_ID);\n        assert_eq!(candidate.validate(), Ok(()));\n        assert!(!baseline.policy.futility_pruning_enabled());\n        assert!(candidate.policy.futility_pruning_enabled());\n        assert_ne!(candidate.checksum, baseline.checksum);\n    }\n\n    #[test]\n    fn delta_pruning_without_see_pruning_fails_loudly() {\n",
)
replace_once(
    policy,
    "        parameters.experimental_features = ExperimentalSearchFeatures::from_bits(1 << 6)\n            .expect(\"assigned feature bit is recognized\");\n",
    "        parameters.experimental_features = ExperimentalSearchFeatures::from_bits(1 << 7)\n            .expect(\"assigned feature bit is recognized\");\n",
)

# Diagnostics: add a distinct attempt counter without perturbing the all-zero baseline checksum.
diag = "crates/chess-search/src/diagnostics.rs"
replace_once(diag, "    FrontierFutilityPrunes,\n", "    FrontierFutilityAttempts,\n    FrontierFutilityPrunes,\n")
replace_once(
    diag,
    "            Self::FrontierFutilityPrunes => \"frontier_futility_prunes\",\n",
    "            Self::FrontierFutilityAttempts => \"frontier_futility_attempts\",\n            Self::FrontierFutilityPrunes => \"frontier_futility_prunes\",\n",
)
replace_once(diag, "    FrontierFutilityPrune,\n", "    FrontierFutilityAttempt,\n    FrontierFutilityPrune,\n")
replace_once(diag, "    frontier_futility_prunes: u64,\n", "    frontier_futility_attempts: u64,\n    frontier_futility_prunes: u64,\n")
replace_once(diag, "        frontier_futility_prunes: 0,\n", "        frontier_futility_attempts: 0,\n        frontier_futility_prunes: 0,\n")
replace_once(
    diag,
    "            SearchDiagnosticEvent::FrontierFutilityPrune => increment_checked(\n",
    "            SearchDiagnosticEvent::FrontierFutilityAttempt => increment_checked(\n                &mut self.frontier_futility_attempts,\n                SearchDiagnosticCounter::FrontierFutilityAttempts,\n            ),\n            SearchDiagnosticEvent::FrontierFutilityPrune => increment_checked(\n",
)
replace_once(
    diag,
    "            frontier_futility_prunes: sum!(frontier_futility_prunes, FrontierFutilityPrunes),\n",
    "            frontier_futility_attempts: sum!(\n                frontier_futility_attempts,\n                FrontierFutilityAttempts\n            ),\n            frontier_futility_prunes: sum!(frontier_futility_prunes, FrontierFutilityPrunes),\n",
)
replace_once(
    diag,
    "    #[must_use]\n    pub const fn frontier_futility_prunes(self) -> u64 {\n",
    "    #[must_use]\n    pub const fn frontier_futility_attempts(self) -> u64 {\n        self.frontier_futility_attempts\n    }\n    #[must_use]\n    pub const fn frontier_futility_prunes(self) -> u64 {\n",
)
replace_once(
    diag,
    "            && self.frontier_futility_prunes == 0\n",
    "            && self.frontier_futility_attempts == 0\n            && self.frontier_futility_prunes == 0\n",
)
replace_once(
    diag,
    "        if self.quiescence_delta_attempts != 0 {\n",
    "        if self.frontier_futility_attempts != 0 {\n            hash = hash_bytes(hash, b\"frontier-futility-attempts-v1\");\n            hash = hash_bytes(hash, &self.frontier_futility_attempts.to_le_bytes());\n        }\n        if self.quiescence_delta_attempts != 0 {\n",
)
replace_once(
    diag,
    "    #[test]\n    fn cutoff_events_are_deterministic_and_future_counters_stay_zero() {\n",
    "    #[test]\n    fn futility_events_distinguish_attempts_from_prunes() {\n        let mut diagnostics = SearchDiagnostics::default();\n        diagnostics\n            .record_checked(SearchDiagnosticEvent::FrontierFutilityAttempt)\n            .expect(\"small count fits\");\n        diagnostics\n            .record_checked(SearchDiagnosticEvent::FrontierFutilityPrune)\n            .expect(\"small count fits\");\n        assert_eq!(diagnostics.frontier_futility_attempts(), 1);\n        assert_eq!(diagnostics.frontier_futility_prunes(), 1);\n        assert!(!diagnostics.reserved_counters_are_zero());\n    }\n\n    #[test]\n    fn cutoff_events_are_deterministic_and_future_counters_stay_zero() {\n",
)

# Public exports.
lib = "crates/chess-search/src/lib.rs"
replace_once(
    lib,
    "    SearchPolicyValidationError, TranspositionPolicy, LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID,\n",
    "    SearchPolicyValidationError, TranspositionPolicy, FUTILITY_PRUNING_MARGIN_CENTIPAWNS,\n    FUTILITY_PRUNING_MAXIMUM_DEPTH, FUTILITY_PRUNING_SEARCH_POLICY_ID,\n    LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID,\n",
)

# Alpha-beta integration: conservative depth-one, later quiet moves only.
alpha = "crates/chess-search/src/alpha_beta.rs"
replace_once(
    alpha,
    "        LMR_MINIMUM_DEPTH, LMR_MINIMUM_LEGAL_MOVES, LMR_MINIMUM_MOVE_INDEX,\n",
    "        FUTILITY_PRUNING_MARGIN_CENTIPAWNS, FUTILITY_PRUNING_MAXIMUM_DEPTH,\n        LMR_MINIMUM_DEPTH, LMR_MINIMUM_LEGAL_MOVES, LMR_MINIMUM_MOVE_INDEX,\n",
)
replace_once(
    alpha,
    "    /// Fixed-capacity transposition-table allocation failed.\n",
    "    /// Frontier-futility margin arithmetic left the supported score domain.\n    FutilityMarginOutOfRange {\n        /// Static evaluation before the optimistic margin.\n        static_evaluation: i32,\n        /// Frozen optimistic margin.\n        margin: u16,\n    },\n    /// Fixed-capacity transposition-table allocation failed.\n",
)
replace_once(
    alpha,
    "            Self::PvsWindowOutOfRange { parent_alpha } => write!(\n                formatter,\n                \"cannot construct PVS null window from parent alpha {parent_alpha}\"\n            ),\n",
    "            Self::PvsWindowOutOfRange { parent_alpha } => write!(\n                formatter,\n                \"cannot construct PVS null window from parent alpha {parent_alpha}\"\n            ),\n            Self::FutilityMarginOutOfRange {\n                static_evaluation,\n                margin,\n            } => write!(\n                formatter,\n                \"cannot add frontier-futility margin {margin} to static evaluation {static_evaluation}\"\n            ),\n",
)
replace_once(
    alpha,
    "        null_move_pruning: policy.search_policy.null_move_pruning_enabled(),\n",
    "        null_move_pruning: policy.search_policy.null_move_pruning_enabled(),\n        futility_pruning: policy.search_policy.futility_pruning_enabled(),\n",
)
replace_once(alpha, "    null_move_pruning: bool,\n", "    null_move_pruning: bool,\n    futility_pruning: bool,\n")
replace_once(
    alpha,
    "    let total_piece_count = u16::try_from(position.all_occupancy().count())\n        .expect(\"a chess position contains at most 64 pieces\");\n\n    for (move_index, token) in ordered_tokens.iter().enumerate() {\n",
    "    let total_piece_count = u16::try_from(position.all_occupancy().count())\n        .expect(\"a chess position contains at most 64 pieces\");\n    let frontier_futility_upper_bound = decide_frontier_futility(\n        position,\n        depth,\n        ply,\n        parent_in_check,\n        window,\n        context.futility_pruning,\n        context.weights,\n    )?;\n\n    for (move_index, token) in ordered_tokens.iter().enumerate() {\n",
)
replace_once(
    alpha,
    "        let position_undo = position.make_legal_token(token)?;\n        let history_undo = history.push_position(position);\n        let child_in_check = position.is_in_check(position.side_to_move());\n",
    "        let position_undo = position.make_legal_token(token)?;\n        let child_in_check = position.is_in_check(position.side_to_move());\n        let futility_candidate = frontier_futility_upper_bound.is_some()\n            && move_index > 0\n            && legal_move_count > 1\n            && !child_in_check\n            && !current.kind().is_capture()\n            && current.promotion().is_none()\n            && !is_transposition_table_move\n            && !protected_quiet_candidate;\n        if futility_candidate {\n            let attempt = SearchDiagnosticEvent::FrontierFutilityAttempt;\n            diagnostics.record_checked(attempt)?;\n            context.cancellation.on_search_diagnostic(attempt);\n            if frontier_futility_upper_bound.is_some_and(|upper_bound| upper_bound <= alpha) {\n                position.unmake_move(position_undo)?;\n                let prune = SearchDiagnosticEvent::FrontierFutilityPrune;\n                diagnostics.record_checked(prune)?;\n                context.cancellation.on_search_diagnostic(prune);\n                continue;\n            }\n        }\n        let history_undo = history.push_position(position);\n",
)
replace_once(
    alpha,
    "fn decide_null_move(\n",
    "fn decide_frontier_futility(\n    position: &Position,\n    depth: u16,\n    ply: u16,\n    parent_in_check: bool,\n    window: AlphaBetaWindow,\n    enabled: bool,\n    weights: &EvaluationWeights,\n) -> Result<Option<Score>, AlphaBetaSearchError> {\n    if !enabled\n        || depth == 0\n        || depth > FUTILITY_PRUNING_MAXIMUM_DEPTH\n        || ply == 0\n        || parent_in_check\n        || window.alpha().is_mate()\n        || window.beta().is_mate()\n        || ply >= MAX_MATE_PLY.saturating_sub(depth)\n    {\n        return Ok(None);\n    }\n    let static_evaluation = evaluate_with_weights(position, weights);\n    let raw = static_evaluation\n        .centipawns()\n        .checked_add(i32::from(FUTILITY_PRUNING_MARGIN_CENTIPAWNS))\n        .ok_or(AlphaBetaSearchError::FutilityMarginOutOfRange {\n            static_evaluation: static_evaluation.centipawns(),\n            margin: FUTILITY_PRUNING_MARGIN_CENTIPAWNS,\n        })?;\n    Score::from_raw(raw)\n        .map(Some)\n        .ok_or(AlphaBetaSearchError::FutilityMarginOutOfRange {\n            static_evaluation: static_evaluation.centipawns(),\n            margin: FUTILITY_PRUNING_MARGIN_CENTIPAWNS,\n        })\n}\n\nfn decide_null_move(\n",
)
replace_once(
    alpha,
    "#[cfg(test)]\nmod null_move_policy_tests {\n",
    "#[cfg(test)]\nmod futility_policy_tests {\n    use chess_core::Position;\n\n    use super::{decide_frontier_futility, AlphaBetaWindow};\n    use crate::{\n        EvaluationWeights, Score, FUTILITY_PRUNING_MARGIN_CENTIPAWNS,\n        FUTILITY_PRUNING_MAXIMUM_DEPTH,\n    };\n\n    fn window(alpha: i32, beta: i32) -> AlphaBetaWindow {\n        AlphaBetaWindow::new(\n            Score::from_raw(alpha).expect(\"alpha fits\"),\n            Score::from_raw(beta).expect(\"beta fits\"),\n        )\n        .expect(\"valid window\")\n    }\n\n    #[test]\n    fn frozen_frontier_margin_is_typed_and_checked() {\n        let position = Position::starting();\n        let upper = decide_frontier_futility(\n            &position,\n            1,\n            1,\n            false,\n            window(-200, 200),\n            true,\n            &EvaluationWeights::DEFAULT,\n        )\n        .expect(\"decision succeeds\")\n        .expect(\"frontier is eligible\");\n        assert_eq!(FUTILITY_PRUNING_MAXIMUM_DEPTH, 1);\n        assert_eq!(FUTILITY_PRUNING_MARGIN_CENTIPAWNS, 150);\n        assert_eq!(upper.centipawns(), 150);\n    }\n\n    #[test]\n    fn root_check_deeper_and_mate_sensitive_nodes_are_protected() {\n        let position = Position::starting();\n        for (depth, ply, parent_in_check, current_window) in [\n            (1, 0, false, window(-200, 200)),\n            (1, 1, true, window(-200, 200)),\n            (2, 1, false, window(-200, 200)),\n            (1, 1, false, AlphaBetaWindow::full()),\n        ] {\n            assert_eq!(\n                decide_frontier_futility(\n                    &position,\n                    depth,\n                    ply,\n                    parent_in_check,\n                    current_window,\n                    true,\n                    &EvaluationWeights::DEFAULT,\n                ),\n                Ok(None)\n            );\n        }\n    }\n}\n\n#[cfg(test)]\nmod null_move_policy_tests {\n",
)

# Integration tests for policy identity, diagnostics, restoration, and tactical protections.
Path("crates/chess-search/tests/s2_10_futility.rs").write_text(
    r'''use chess_core::{Move, Position, SearchHistory};
use chess_search::{
    iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights,
    EvaluationWeights, SearchLimits, SearchPolicySet, SearchResult, TranspositionTable,
    FUTILITY_PRUNING_MARGIN_CENTIPAWNS, FUTILITY_PRUNING_MAXIMUM_DEPTH,
    FUTILITY_PRUNING_SEARCH_POLICY_ID,
};

const TT_MEBIBYTES: usize = 1;

fn run(fen: &str, depth: u16, policy: &SearchPolicySet) -> SearchResult {
    let mut position = Position::from_fen(fen).expect("fixture parses");
    let root = position.clone();
    let mut history = SearchHistory::from_position(&position);
    let root_history = history.clone();
    let mut table = TranspositionTable::new(TT_MEBIBYTES).expect("small TT allocates");
    let result =
        iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights(
            &mut position,
            &mut history,
            SearchLimits::new().with_depth(depth),
            &mut table,
            policy,
            &EvaluationWeights::DEFAULT,
        )
        .expect("controlled search succeeds");
    assert_eq!(position, root);
    assert_eq!(history, root_history);
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
    replay_pv(&root, result.principal_variation().map_or(&[], |pv| pv.moves()));
    result
}

fn replay_pv(root: &Position, moves: &[Move]) {
    let mut position = root.clone();
    for current in moves {
        let token = position
            .legal_move_tokens()
            .expect("PV moves generate")
            .iter()
            .find(|token| token.move_made() == *current)
            .expect("PV move remains legal");
        position.make_legal_token(token).expect("PV move applies");
    }
    assert_eq!(position.zobrist(), position.recomputed_zobrist());
}

#[test]
fn candidate_identity_parameters_and_default_inactivity_are_explicit() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::futility_pruning_candidate();
    baseline.validate().expect("baseline validates");
    candidate.validate().expect("candidate validates");
    assert_eq!(candidate.identifier, FUTILITY_PRUNING_SEARCH_POLICY_ID);
    assert_eq!(FUTILITY_PRUNING_MAXIMUM_DEPTH, 1);
    assert_eq!(FUTILITY_PRUNING_MARGIN_CENTIPAWNS, 150);
    assert!(!baseline.policy.futility_pruning_enabled());
    assert!(candidate.policy.futility_pruning_enabled());
    assert_ne!(baseline.checksum, candidate.checksum);
}

#[test]
fn baseline_counters_stay_zero_and_candidate_attempts_are_bounded() {
    let fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1";
    let baseline = run(fen, 4, &SearchPolicySet::baseline());
    let candidate = run(fen, 4, &SearchPolicySet::futility_pruning_candidate());
    let base = baseline.search_diagnostics();
    let experimental = candidate.search_diagnostics();
    assert_eq!(base.frontier_futility_attempts(), 0);
    assert_eq!(base.frontier_futility_prunes(), 0);
    assert!(experimental.frontier_futility_attempts() > 0);
    assert!(experimental.frontier_futility_prunes() <= experimental.frontier_futility_attempts());
    assert!(!experimental.overflowed());
}

#[test]
fn tactical_and_rule_sensitive_roots_preserve_exact_semantics() {
    let baseline_policy = SearchPolicySet::baseline();
    let candidate_policy = SearchPolicySet::futility_pruning_candidate();
    for (fen, depth) in [
        ("4k3/8/8/8/8/8/4R3/4K3 b - - 0 1", 3),
        ("7k/P7/8/8/8/8/8/K7 w - - 0 1", 4),
        ("7k/8/8/8/8/8/6q1/7K w - - 0 1", 3),
        ("7k/5Q2/6K1/8/8/8/8/8 b - - 0 1", 3),
        ("6k1/5ppp/8/8/8/8/5PPP/6K1 w - - 99 1", 3),
    ] {
        let baseline = run(fen, depth, &baseline_policy);
        let candidate = run(fen, depth, &candidate_policy);
        assert_eq!(candidate.score(), baseline.score(), "{fen}");
        assert_eq!(candidate.best_move(), baseline.best_move(), "{fen}");
        assert_eq!(candidate.completed_depth(), baseline.completed_depth(), "{fen}");
    }
}
''',
    encoding="utf-8",
)

Path(__file__).unlink()
