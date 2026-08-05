#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
diagnostics="$root/crates/chess-search/src/diagnostics.rs"
alpha_beta="$root/crates/chess-search/src/alpha_beta.rs"
quiescence="$root/crates/chess-search/src/quiescence.rs"
iterative="$root/crates/chess-search/src/iterative_deepening.rs"
limits="$root/crates/chess-search/src/limits.rs"
baseline="$root/crates/chess-tools/src/bin/s2_3_baseline.rs"
corpus="$root/fixtures/search_baseline_v1.tsv"
workflow="$root/.github/workflows/s2-3-stage.yml"
performance="$root/.github/workflows/performance.yml"
doc="$root/docs/RUST_CHESS_ENGINE_V0_2_S2_3_BASELINE_2026-08-05.md"

require_file() {
  local path="$1"
  test -f "$path" || { echo "missing S2-3 asset: $path" >&2; exit 1; }
}

require_literal() {
  local literal="$1"
  local path="$2"
  grep -Fq "$literal" "$path" || {
    echo "missing S2-3 witness in ${path#$root/}: $literal" >&2
    exit 1
  }
}

for path in \
  "$diagnostics" "$alpha_beta" "$quiescence" "$iterative" "$limits" \
  "$baseline" "$corpus" "$workflow" "$performance" "$doc"; do
  require_file "$path"
done

# Allocation-free deterministic diagnostic schema and explicit overflow policy.
require_literal 'pub enum SearchDiagnosticCounter' "$diagnostics"
require_literal 'pub enum SearchDiagnosticEvent' "$diagnostics"
require_literal 'pub struct SearchDiagnostics' "$diagnostics"
require_literal 'pub struct SearchDiagnosticOverflow' "$diagnostics"
require_literal 'pub fn record_checked' "$diagnostics"
require_literal 'pub fn saturating_record' "$diagnostics"
require_literal 'pub fn checked_add' "$diagnostics"
require_literal 'pub const fn reserved_counters_are_zero' "$diagnostics"
require_literal 'pub fn semantic_checksum' "$diagnostics"
for marker in \
  MainNodes QuiescenceNodes BetaCutoffs FirstMoveBetaCutoffs \
  QuiescenceBetaCutoffs QuiescenceFirstMoveBetaCutoffs \
  QuiescenceStandPatCutoffs PvsZeroWindowSearches PvsResearches \
  SeeCalls SeePrunes QuiescenceSeePrunes QuiescenceDeltaPrunes \
  LmrReductions LmrResearches NullMoveAttempts NullMoveCutoffs \
  FrontierFutilityPrunes FrontierRazorAttempts LateMovePrunes; do
  require_literal "$marker" "$diagnostics"
done
if grep -Eq 'Vec<|HashMap|BTreeMap|Box<|String' "$diagnostics"; then
  echo 'S2-3 diagnostics module introduced heap-backed per-search storage' >&2
  exit 1
fi

require_literal 'SearchDiagnosticEvent::BetaCutoff' "$alpha_beta"
require_literal 'SearchDiagnosticEvent::QuiescenceBetaCutoff' "$quiescence"
require_literal 'SearchDiagnosticEvent::QuiescenceStandPatCutoff' "$quiescence"
require_literal 'pub const fn search_diagnostics' "$iterative"
require_literal 'search_diagnostics: controller.search_diagnostics()' "$iterative"
require_literal 'SearchDiagnosticEvent::MainNode' "$limits"
require_literal 'SearchDiagnosticEvent::QuiescenceNode' "$limits"
require_literal 'diagnostics_are_consistent_and_observationally_inert' "$alpha_beta"

# Frozen versioned tactical corpus covers every required S2-3 category.
require_literal $'CHESS_SEARCH_BASELINE\t1' "$corpus"
for category in \
  mate_in_1 mate_in_2_plus longest_survival stalemate repetition \
  fifty_move seventy_five_move promotion_race en_passant_tactic \
  quiet_defense zugzwang_sensitive poisoned_capture legal_pv_replay; do
  require_literal "$category" "$corpus"
done

# The harness requires explicit provenance, replays legal PVs, preserves roots,
# generates exactly 200 semantic openings, and exercises all three S2-2 tiers.
require_literal 'S2_3_SOURCE_SHA' "$baseline"
require_literal 'S2_3_BUILD_IDENTITY' "$baseline"
require_literal 'position != position_snapshot || history != history_snapshot' "$baseline"
require_literal 'replay_pv(&position_snapshot' "$baseline"
require_literal 'if index != 200' "$baseline"
require_literal 'EngineVariantValidationTier::Smoke' "$baseline"
require_literal 'EngineVariantValidationTier::Development' "$baseline"
require_literal 'EngineVariantValidationTier::Production' "$baseline"
require_literal '"production",' "$baseline"
require_literal '200_u32' "$baseline"
require_literal 'rejected_strength' "$baseline"
require_literal 'required(&fields, "activated")? != "false"' "$baseline"
require_literal 'mean_pair_score_bits' "$baseline"
require_literal 'pair_score_standard_error_bits' "$baseline"
require_literal 'lower_confidence_bound_bits' "$baseline"
require_literal 'write_engine_variant_validation_report_atomic' "$baseline"

# Existing benchmark semantics and references remain authoritative. Both
# architectures retain seven-sample distributions and allocation audits.
if [[ $(grep -Fc 'performance baseline 7 1' "$performance") -ne 2 ]]; then
  echo 'performance workflow must retain seven-sample x86-64 and ARM64 baselines' >&2
  exit 1
fi
if [[ $(grep -Fc 'performance allocation-audit' "$performance") -ne 2 ]]; then
  echo 'performance workflow must retain x86-64 and ARM64 allocation audits' >&2
  exit 1
fi
require_file "$root/benchmarks/task24/performance-linux-x86-64.tsv"
require_file "$root/benchmarks/task24/performance-linux-arm64.tsv"
require_file "$root/fixtures/performance_reference.tsv"
require_file "$root/fixtures/performance_reference_arm64.tsv"

# One-shot staging machinery must not survive; the permanent workflow is read-only.
for path in \
  "$root/scripts/s2_3_stage.py" \
  "$root/scripts/s2_3_stage_runner.py" \
  "$root/scripts/s2_3_baseline_stage.py" \
  "$root/scripts/s2_3_baseline_stage_runner.py"; do
  test ! -e "$path" || { echo "temporary S2-3 staging asset remains: $path" >&2; exit 1; }
done
require_literal 'contents: read' "$workflow"
if grep -Eq 'contents: write|git push|git commit|s2_3_.*stage' "$workflow"; then
  echo 'S2-3 workflow retains write or temporary staging behavior' >&2
  exit 1
fi
require_literal 'target/release/s2_3_baseline s2-3-evidence-a' "$workflow"
require_literal 'target/release/s2_3_baseline s2-3-evidence-b' "$workflow"
require_literal 'diff -ru s2-3-evidence-a s2-3-evidence-b' "$workflow"
require_literal 's2-3-baseline-${{ github.sha }}' "$workflow"

echo 'S2-3 diagnostics, tactical corpus, and baseline control audit passed'
