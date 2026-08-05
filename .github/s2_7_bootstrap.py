from pathlib import Path


def replace_once(path: str, old: str, new: str) -> None:
    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected exactly one replacement, found {count}: {old[:120]!r}")
    file_path.write_text(text.replace(old, new, 1), encoding="utf-8")


def write_new(path: str, content: str) -> None:
    file_path = Path(path)
    if file_path.exists():
        raise SystemExit(f"refusing to overwrite existing file: {path}")
    file_path.parent.mkdir(parents=True, exist_ok=True)
    file_path.write_text(content, encoding="utf-8")


# Search-policy identity and activation boundary.
replace_once(
    "crates/chess-search/src/search_policy.rs",
    "/// Stable identifier for the inactive S2-6 SEE-plus-delta candidate.\n"
    "pub const SEE_AND_DELTA_QUIESCENCE_PRUNING_SEARCH_POLICY_ID: u64 = 0x5332_3644_454c_5031;\n",
    "/// Stable identifier for the inactive S2-6 SEE-plus-delta candidate.\n"
    "pub const SEE_AND_DELTA_QUIESCENCE_PRUNING_SEARCH_POLICY_ID: u64 = 0x5332_3644_454c_5031;\n"
    "/// Stable identifier for the inactive S2-7 Principal Variation Search candidate.\n"
    "pub const PRINCIPAL_VARIATION_SEARCH_POLICY_ID: u64 = 0x5332_3750_5653_3031;\n",
)
replace_once(
    "crates/chess-search/src/search_policy.rs",
    "    /// Inactive S2-6 SEE pruning followed by delta pruning.\n"
    "    pub const SEE_AND_DELTA_QUIESCENCE_PRUNING: Self = Self {\n"
    "        bits: ExperimentalSearchFeature::SeeQuiescencePruning.bit()\n"
    "            | ExperimentalSearchFeature::DeltaPruning.bit(),\n"
    "    };\n",
    "    /// Inactive S2-6 SEE pruning followed by delta pruning.\n"
    "    pub const SEE_AND_DELTA_QUIESCENCE_PRUNING: Self = Self {\n"
    "        bits: ExperimentalSearchFeature::SeeQuiescencePruning.bit()\n"
    "            | ExperimentalSearchFeature::DeltaPruning.bit(),\n"
    "    };\n"
    "    /// Inactive S2-7 Principal Variation Search candidate.\n"
    "    pub const PRINCIPAL_VARIATION_SEARCH: Self = Self {\n"
    "        bits: ExperimentalSearchFeature::PrincipalVariationSearch.bit(),\n"
    "    };\n",
)
replace_once(
    "crates/chess-search/src/search_policy.rs",
    "                ExperimentalSearchFeature::SeeCaptureOrdering\n"
    "                    | ExperimentalSearchFeature::SeeQuiescencePruning\n"
    "                    | ExperimentalSearchFeature::DeltaPruning\n",
    "                ExperimentalSearchFeature::SeeCaptureOrdering\n"
    "                    | ExperimentalSearchFeature::SeeQuiescencePruning\n"
    "                    | ExperimentalSearchFeature::DeltaPruning\n"
    "                    | ExperimentalSearchFeature::PrincipalVariationSearch\n",
)
replace_once(
    "crates/chess-search/src/search_policy.rs",
    "    /// Constructs explicit typed parameters for subsequent validation.\n",
    "    /// Inactive S2-7 candidate: baseline semantics plus Principal Variation Search.\n"
    "    pub const PRINCIPAL_VARIATION_SEARCH: Self = Self::new(SearchPolicyParameters {\n"
    "        alpha_beta: AlphaBetaMode::FullWindowFailSoft,\n"
    "        transposition: TranspositionPolicy::ClusteredFullKey,\n"
    "        move_ordering: MoveOrderingPolicy::V0_1MvvLvaKillersHistory,\n"
    "        quiescence: QuiescencePolicy::CapturesPromotionsAndEvasions,\n"
    "        aspiration_windows: true,\n"
    "        aspiration_half_width_centipawns: DEFAULT_ASPIRATION_HALF_WIDTH_CENTIPAWNS as u16,\n"
    "        maximum_quiescence_ply: MAX_QUIESCENCE_PLY,\n"
    "        maximum_check_extensions_per_line: MAX_CHECK_EXTENSIONS_PER_LINE,\n"
    "        experimental_features: ExperimentalSearchFeatures::PRINCIPAL_VARIATION_SEARCH,\n"
    "    });\n\n"
    "    /// Constructs explicit typed parameters for subsequent validation.\n",
)
replace_once(
    "crates/chess-search/src/search_policy.rs",
    "    /// Validates supported ranges and rejects not-yet-implemented features.\n",
    "    /// Returns whether the inactive S2-7 PVS candidate is selected.\n"
    "    #[must_use]\n"
    "    pub const fn principal_variation_search_enabled(self) -> bool {\n"
    "        self.parameters\n"
    "            .experimental_features\n"
    "            .contains(ExperimentalSearchFeature::PrincipalVariationSearch)\n"
    "    }\n\n"
    "    /// Validates supported ranges and rejects not-yet-implemented features.\n",
)
replace_once(
    "crates/chess-search/src/search_policy.rs",
    "    /// Computes the canonical checksum.\n",
    "    /// Returns the inactive S2-7 Principal Variation Search candidate.\n"
    "    #[must_use]\n"
    "    pub fn principal_variation_search_candidate() -> Self {\n"
    "        Self::new(\n"
    "            PRINCIPAL_VARIATION_SEARCH_POLICY_ID,\n"
    "            SearchPolicy::PRINCIPAL_VARIATION_SEARCH,\n"
    "        )\n"
    "    }\n\n"
    "    /// Computes the canonical checksum.\n",
)

# Public identity export.
replace_once(
    "crates/chess-search/src/lib.rs",
    "    SEE_AND_DELTA_QUIESCENCE_PRUNING_SEARCH_POLICY_ID, SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID,\n"
    "    SEE_QUIESCENCE_PRUNING_SEARCH_POLICY_ID, V0_1_SEARCH_POLICY_CHECKSUM, V0_1_SEARCH_POLICY_ID,\n",
    "    PRINCIPAL_VARIATION_SEARCH_POLICY_ID,\n"
    "    SEE_AND_DELTA_QUIESCENCE_PRUNING_SEARCH_POLICY_ID, SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID,\n"
    "    SEE_QUIESCENCE_PRUNING_SEARCH_POLICY_ID, V0_1_SEARCH_POLICY_CHECKSUM, V0_1_SEARCH_POLICY_ID,\n",
)

# PVS window construction and fail-loud invariant.
replace_once(
    "crates/chess-search/src/alpha_beta.rs",
    "    pub(crate) fn is_full(self) -> bool {\n"
    "        self == Self::full()\n"
    "    }\n",
    "    pub(crate) fn is_full(self) -> bool {\n"
    "        self == Self::full()\n"
    "    }\n\n"
    "    fn pvs_child(parent_alpha: Score) -> Result<Self, AlphaBetaSearchError> {\n"
    "        let child_beta = -parent_alpha;\n"
    "        let child_alpha_raw = child_beta.centipawns() - 1;\n"
    "        let child_alpha = Score::from_raw(child_alpha_raw).ok_or(\n"
    "            AlphaBetaSearchError::PvsWindowOutOfRange {\n"
    "                parent_alpha: parent_alpha.centipawns(),\n"
    "            },\n"
    "        )?;\n"
    "        Self::new(child_alpha, child_beta).ok_or(\n"
    "            AlphaBetaSearchError::PvsWindowOutOfRange {\n"
    "                parent_alpha: parent_alpha.centipawns(),\n"
    "            },\n"
    "        )\n"
    "    }\n",
)
replace_once(
    "crates/chess-search/src/alpha_beta.rs",
    "    /// Fixed-capacity transposition-table allocation failed.\n",
    "    /// A one-centipawn PVS child window could not be represented.\n"
    "    PvsWindowOutOfRange {\n"
    "        /// Parent alpha whose negated successor was outside the score domain.\n"
    "        parent_alpha: i32,\n"
    "    },\n"
    "    /// Fixed-capacity transposition-table allocation failed.\n",
)
replace_once(
    "crates/chess-search/src/alpha_beta.rs",
    "            Self::StaticExchange(error) => error.fmt(formatter),\n"
    "            Self::TranspositionTableAllocation(error) => error.fmt(formatter),\n",
    "            Self::StaticExchange(error) => error.fmt(formatter),\n"
    "            Self::PvsWindowOutOfRange { parent_alpha } => write!(\n"
    "                formatter,\n"
    "                \"cannot construct PVS null window from parent alpha {parent_alpha}\"\n"
    "            ),\n"
    "            Self::TranspositionTableAllocation(error) => error.fmt(formatter),\n",
)

# Thread the inactive policy flag into the search context.
replace_once(
    "crates/chess-search/src/alpha_beta.rs",
    "        delta_pruning: policy.search_policy.delta_pruning_enabled(),\n"
    "        weights: policy.weights,\n",
    "        delta_pruning: policy.search_policy.delta_pruning_enabled(),\n"
    "        principal_variation_search: policy\n"
    "            .search_policy\n"
    "            .principal_variation_search_enabled(),\n"
    "        weights: policy.weights,\n",
)
replace_once(
    "crates/chess-search/src/alpha_beta.rs",
    "    delta_pruning: bool,\n"
    "    weights: &'a EvaluationWeights,\n",
    "    delta_pruning: bool,\n"
    "    principal_variation_search: bool,\n"
    "    weights: &'a EvaluationWeights,\n",
)
alpha_path = Path("crates/chess-search/src/alpha_beta.rs")
alpha_text = alpha_path.read_text(encoding="utf-8")
needle = "            delta_pruning: false,\n            weights:"
count = alpha_text.count(needle)
if count == 0:
    raise SystemExit("alpha_beta.rs: no test contexts found for PVS inactivity insertion")
alpha_text = alpha_text.replace(
    needle,
    "            delta_pruning: false,\n            principal_variation_search: false,\n            weights:",
)
alpha_path.write_text(alpha_text, encoding="utf-8")

# Replace the one-shot child search with PVS-aware bounded search and exact re-search.
replace_once(
    "crates/chess-search/src/alpha_beta.rs",
    "        let child_window = AlphaBetaWindow {\n"
    "            alpha: -beta,\n"
    "            beta: -alpha,\n"
    "        };\n"
    "        let child_in_check = position.is_in_check(position.side_to_move());\n"
    "        let extension = decide_check_extension(\n"
    "            depth,\n"
    "            ply,\n"
    "            child_in_check,\n"
    "            context.check_extension_enabled,\n"
    "            extension_budget,\n"
    "        );\n"
    "        if let Some(event) = extension.event() {\n"
    "            context.cancellation.on_check_extension(event);\n"
    "        }\n"
    "        let child = search_node_with_extensions(\n"
    "            position,\n"
    "            history,\n"
    "            extension.child_depth(),\n"
    "            ply + 1,\n"
    "            extension.remaining_budget(),\n"
    "            child_window,\n"
    "            context,\n"
    "        );\n",
    "        let child_in_check = position.is_in_check(position.side_to_move());\n"
    "        let extension = decide_check_extension(\n"
    "            depth,\n"
    "            ply,\n"
    "            child_in_check,\n"
    "            context.check_extension_enabled,\n"
    "            extension_budget,\n"
    "        );\n"
    "        if let Some(event) = extension.event() {\n"
    "            context.cancellation.on_check_extension(event);\n"
    "        }\n"
    "        let child = search_child_with_optional_pvs(\n"
    "            position,\n"
    "            history,\n"
    "            extension.child_depth(),\n"
    "            ply + 1,\n"
    "            extension.remaining_budget(),\n"
    "            move_index,\n"
    "            alpha,\n"
    "            beta,\n"
    "            context,\n"
    "            &mut diagnostics,\n"
    "        );\n",
)
replace_once(
    "crates/chess-search/src/alpha_beta.rs",
    "fn transposition_score_reuse(\n",
    "fn search_child_with_optional_pvs<Probe>(\n"
    "    position: &mut Position,\n"
    "    history: &mut SearchHistory,\n"
    "    depth: u16,\n"
    "    ply: u16,\n"
    "    extension_budget: u16,\n"
    "    move_index: usize,\n"
    "    alpha: Score,\n"
    "    beta: Score,\n"
    "    context: &mut AlphaBetaContext<'_, Probe>,\n"
    "    diagnostics: &mut SearchDiagnostics,\n"
    ") -> Result<AlphaBetaSearchResult, AlphaBetaSearchError>\n"
    "where\n"
    "    Probe: SearchCancellationProbe + ?Sized,\n"
    "{\n"
    "    let full_window = AlphaBetaWindow {\n"
    "        alpha: -beta,\n"
    "        beta: -alpha,\n"
    "    };\n"
    "    if !context.principal_variation_search || move_index == 0 {\n"
    "        return search_node_with_extensions(\n"
    "            position,\n"
    "            history,\n"
    "            depth,\n"
    "            ply,\n"
    "            extension_budget,\n"
    "            full_window,\n"
    "            context,\n"
    "        );\n"
    "    }\n\n"
    "    let zero_window_event = SearchDiagnosticEvent::PvsZeroWindowSearch;\n"
    "    diagnostics.record_checked(zero_window_event)?;\n"
    "    context\n"
    "        .cancellation\n"
    "        .on_search_diagnostic(zero_window_event);\n"
    "    let zero_window = AlphaBetaWindow::pvs_child(alpha)?;\n"
    "    let narrow = search_node_with_extensions(\n"
    "        position,\n"
    "        history,\n"
    "        depth,\n"
    "        ply,\n"
    "        extension_budget,\n"
    "        zero_window,\n"
    "        context,\n"
    "    )?;\n"
    "    let narrow_parent_score = -narrow.score;\n"
    "    if narrow_parent_score <= alpha || narrow_parent_score >= beta {\n"
    "        return Ok(narrow);\n"
    "    }\n\n"
    "    let research_event = SearchDiagnosticEvent::PvsResearch;\n"
    "    diagnostics.record_checked(research_event)?;\n"
    "    context.cancellation.on_search_diagnostic(research_event);\n"
    "    let exact = search_node_with_extensions(\n"
    "        position,\n"
    "        history,\n"
    "        depth,\n"
    "        ply,\n"
    "        extension_budget,\n"
    "        full_window,\n"
    "        context,\n"
    "    )?;\n"
    "    combine_pvs_attempts(narrow, exact)\n"
    "}\n\n"
    "fn combine_pvs_attempts(\n"
    "    narrow: AlphaBetaSearchResult,\n"
    "    exact: AlphaBetaSearchResult,\n"
    ") -> Result<AlphaBetaSearchResult, AlphaBetaSearchError> {\n"
    "    Ok(AlphaBetaSearchResult {\n"
    "        score: exact.score,\n"
    "        best_move: exact.best_move,\n"
    "        nodes: narrow\n"
    "            .nodes\n"
    "            .checked_add(exact.nodes)\n"
    "            .ok_or(AlphaBetaSearchError::NodeCountOverflow)?,\n"
    "        qnodes: narrow\n"
    "            .qnodes\n"
    "            .checked_add(exact.qnodes)\n"
    "            .ok_or(AlphaBetaSearchError::NodeCountOverflow)?,\n"
    "        selective_depth: narrow.selective_depth.max(exact.selective_depth),\n"
    "        diagnostics: narrow.diagnostics.checked_add(exact.diagnostics)?,\n"
    "    })\n"
    "}\n\n"
    "fn transposition_score_reuse(\n",
)

# Focused integration tests.
write_new(
    "crates/chess-search/tests/s2_7_pvs.rs",
    r'''use chess_core::{Move, Position, SearchHistory};
use chess_search::{
    iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights,
    EvaluationWeights, SearchLimits, SearchPolicySet, SearchResult, TranspositionTable,
    PRINCIPAL_VARIATION_SEARCH_POLICY_ID,
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
fn candidate_identity_is_explicit_valid_and_inactive_by_default() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::principal_variation_search_candidate();
    baseline.validate().expect("baseline policy validates");
    candidate.validate().expect("candidate policy validates");
    assert_eq!(candidate.identifier, PRINCIPAL_VARIATION_SEARCH_POLICY_ID);
    assert!(!baseline.policy.principal_variation_search_enabled());
    assert!(candidate.policy.principal_variation_search_enabled());
    assert_ne!(baseline.checksum, candidate.checksum);
}

#[test]
fn candidate_preserves_exact_scores_best_moves_and_legal_pvs() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::principal_variation_search_candidate();
    for (fen, depth) in [
        ("7k/5Q2/6K1/8/8/8/8/8 w - - 0 1", 3),
        ("4Q2k/8/4K3/8/8/8/8/8 b - - 0 1", 6),
        ("7k/P7/6K1/8/8/8/8/8 w - - 0 1", 4),
        ("4k3/8/8/3pP3/8/8/8/4K3 w - d6 0 1", 4),
        ("3rk3/8/8/8/8/8/8/K2Q4 w - - 0 1", 4),
        (
            "r1bq1rk1/ppp2ppp/2np1n2/4p3/2B1P3/2N2N2/PPPP1PPP/R1BQ1RK1 w - - 4 7",
            4,
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
        assert_eq!(
            candidate_result.best_move(),
            baseline_result.best_move(),
            "{fen}"
        );
    }
}

#[test]
fn candidate_uses_zero_windows_and_only_researches_improving_moves() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::principal_variation_search_candidate();
    let fen = "r3k2r/p1ppqpb1/bn2pnp1/3PN3/1p2P3/2N2Q1p/PPPBBPPP/R3K2R w KQkq - 0 1";
    let baseline_result = run(fen, SearchLimits::new().with_depth(4), &baseline);
    let candidate_result = run(fen, SearchLimits::new().with_depth(4), &candidate);
    let baseline_diagnostics = baseline_result.search_diagnostics();
    let diagnostics = candidate_result.search_diagnostics();
    assert_eq!(baseline_diagnostics.pvs_zero_window_searches(), 0);
    assert_eq!(baseline_diagnostics.pvs_researches(), 0);
    assert!(diagnostics.pvs_zero_window_searches() > 0);
    assert!(diagnostics.pvs_researches() <= diagnostics.pvs_zero_window_searches());
    assert_eq!(candidate_result.score(), baseline_result.score());
    assert_eq!(candidate_result.best_move(), baseline_result.best_move());
}

#[test]
fn aspiration_recovery_and_node_limited_cancellation_keep_only_exact_iterations() {
    let baseline = SearchPolicySet::baseline();
    let candidate = SearchPolicySet::principal_variation_search_candidate();
    let fen = "r2q1rk1/ppp2ppp/2npbn2/3Np3/2B1P3/2P2N2/PP3PPP/R1BQR1K1 w - - 0 10";

    let baseline_exact = run(fen, SearchLimits::new().with_depth(5), &baseline);
    let candidate_exact = run(fen, SearchLimits::new().with_depth(5), &candidate);
    assert_eq!(candidate_exact.score(), baseline_exact.score());
    assert_eq!(candidate_exact.best_move(), baseline_exact.best_move());

    let limited = run(
        fen,
        SearchLimits::new().with_depth(8).with_nodes(512),
        &candidate,
    );
    assert!(limited.completed_depth() < 8);
    assert!(limited.nodes() <= 512);
    for iteration in limited.completed().iterations() {
        assert!(iteration.best_move().is_some());
        assert!(!iteration.search_diagnostics().overflowed());
    }
}
''',
)

# Fail-closed source audit.
write_new(
    "scripts/task_s2_7_pvs_audit.sh",
    r'''#!/usr/bin/env bash
set -euo pipefail

fail() {
  echo "S2-7 PVS audit failed: $*" >&2
  exit 1
}

policy="crates/chess-search/src/search_policy.rs"
search="crates/chess-search/src/alpha_beta.rs"
lib="crates/chess-search/src/lib.rs"
tests="crates/chess-search/tests/s2_7_pvs.rs"

for path in "$policy" "$search" "$lib" "$tests"; do
  [[ -f "$path" ]] || fail "missing $path"
done

grep -q 'pub const PRINCIPAL_VARIATION_SEARCH_POLICY_ID' "$policy" || fail "missing PVS identity"
grep -q 'pub const PRINCIPAL_VARIATION_SEARCH: Self' "$policy" || fail "missing PVS policy"
grep -q 'principal_variation_search_enabled' "$policy" || fail "missing PVS accessor"
grep -q 'SearchPolicy::V0_1' "$search" || fail "baseline convenience path no longer explicit"
grep -q 'SearchDiagnosticEvent::PvsZeroWindowSearch' "$search" || fail "missing zero-window diagnostic"
grep -q 'SearchDiagnosticEvent::PvsResearch' "$search" || fail "missing re-search diagnostic"
grep -q 'narrow_parent_score <= alpha || narrow_parent_score >= beta' "$search" || fail "missing exact re-search boundary"
grep -q 'combine_pvs_attempts' "$search" || fail "missing attempt accounting"
grep -q 'PRINCIPAL_VARIATION_SEARCH_POLICY_ID' "$lib" || fail "missing public identity export"

if grep -R --line-number --fixed-strings 'principal_variation_search: true' crates/chess-search/src; then
  fail "PVS is hard-coded active"
fi
if grep -R --line-number -E 'unwrap_or\(|unwrap_or_default\(|\.ok\(\)' crates/chess-search/src/alpha_beta.rs | grep -i pvs; then
  fail "PVS contains a silent fallback"
fi

echo "S2-7 PVS audit passed"
''',
)
Path("scripts/task_s2_7_pvs_audit.sh").chmod(0o755)

# Permanent focused CI.
write_new(
    ".github/workflows/s2-7-pvs.yml",
    r'''name: S2-7 Principal Variation Search validation

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
  group: s2-7-pvs-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  linux-x86-64:
    name: Linux x86-64 PVS correctness
    runs-on: ubuntu-24.04
    timeout-minutes: 45
    steps:
      - uses: actions/checkout@v4
      - name: Install stable Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt, clippy
      - name: Cache Cargo data
        uses: Swatinem/rust-cache@v2
        with:
          shared-key: rust-engine-s2-7-pvs-x86-64
      - name: Audit S2-7 architecture
        run: bash scripts/task_s2_7_pvs_audit.sh
      - name: Check formatting and strict Clippy
        run: |
          cargo fmt --all -- --check
          cargo clippy --locked -p chess-search --all-targets --all-features -- -D warnings
      - name: Run focused and complete search tests
        run: |
          cargo test --locked -p chess-search --test s2_7_pvs
          cargo test --locked -p chess-search --all-targets --all-features

  linux-arm64:
    name: Linux ARM64 PVS correctness
    runs-on: ubuntu-24.04-arm
    timeout-minutes: 45
    steps:
      - uses: actions/checkout@v4
      - name: Install stable Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          components: rustfmt, clippy
      - name: Cache Cargo data
        uses: Swatinem/rust-cache@v2
        with:
          shared-key: rust-engine-s2-7-pvs-arm64
      - name: Audit, lint, and test on native ARM64
        run: |
          bash scripts/task_s2_7_pvs_audit.sh
          cargo fmt --all -- --check
          cargo clippy --locked -p chess-search --all-targets --all-features -- -D warnings
          cargo test --locked -p chess-search --test s2_7_pvs
          cargo test --locked -p chess-search --all-targets --all-features
''',
)

write_new(
    "docs/RUST_CHESS_ENGINE_V0_2_S2_7_PVS_2026-08-05.md",
    r'''# Rust Chess Engine v0.2 — S2-7 Principal Variation Search

**Status:** Implementation validation in progress  
**Date:** 2026-08-05  
**Activation:** false

## Scope

S2-7 adds an inactive, identity-bound Principal Variation Search candidate to the controlled Rust search path. The authoritative v0.1 production policy, public convenience entry points, UCI, safe Rust facade, C ABI, JNI, Android integration, package version, evaluation weights, and defaults remain unchanged.

## Search contract

- The first ordered move is searched with the node's full alpha-beta window.
- Every later move is first searched with the one-centipawn child window `[-alpha - 1, -alpha]`.
- A null-window result that strictly improves alpha without reaching beta is re-searched with the full child window before it can become an exact principal value.
- Null-window fail-low results cannot replace an equal earlier best move; fail-high results retain normal beta-cutoff semantics.
- Both attempts contribute to node, quiescence-node, selective-depth, diagnostic, cancellation, and limit accounting.
- TT probing, fail-soft score propagation, mate normalization, bound classification, and deterministic strict-greater best-move replacement remain shared with the baseline search.
- Window construction is fail-loud; there is no neutral-score, baseline-search, or disabled-feature fallback.

## Identity and activation boundary

The candidate is available only through `SearchPolicySet::principal_variation_search_candidate()`. `SearchPolicy::V0_1` remains the policy used by every production convenience path. Candidate and baseline validation must use separate caller-owned transposition tables.

## Validation plan

The permanent `S2-7 Principal Variation Search validation` workflow runs the source audit, formatting, strict Clippy, focused parity/restoration tests, and the complete `chess-search` test suite on x86-64 and native ARM64. Deterministic corpus, fixed-node development, optional clock development, and benchmark evidence are added only after this correctness slice passes.
''',
)

# The bootstrap mechanism must not survive in the implementation tree.
Path(".github/s2_7_bootstrap.py").unlink()
Path(".github/workflows/s2-7-bootstrap.yml").unlink()
