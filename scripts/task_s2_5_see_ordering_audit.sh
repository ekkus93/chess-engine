#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
policy="$root/crates/chess-search/src/search_policy.rs"
ordering="$root/crates/chess-search/src/move_ordering.rs"
diagnostics="$root/crates/chess-search/src/diagnostics.rs"
alpha_beta="$root/crates/chess-search/src/alpha_beta.rs"
quiescence="$root/crates/chess-search/src/quiescence.rs"
tests="$root/crates/chess-search/tests/s2_5_see_ordering.rs"
evidence="$root/crates/chess-tools/src/bin/s2_5_see_ordering.rs"
workflow="$root/.github/workflows/s2-5-see-ordering.yml"
doc="$root/docs/RUST_CHESS_ENGINE_V0_2_S2_5_SEE_ORDERING_2026-08-05.md"
ci="$root/.github/workflows/ci.yml"

require_file() {
  test -f "$1" || { echo "missing S2-5 asset: ${1#$root/}" >&2; exit 1; }
}

require_literal() {
  grep -Fq "$1" "$2" || {
    echo "missing S2-5 witness in ${2#$root/}: $1" >&2
    exit 1
  }
}

for path in "$policy" "$ordering" "$diagnostics" "$alpha_beta" "$quiescence" \
  "$tests" "$evidence" "$workflow" "$doc" "$ci"; do
  require_file "$path"
done

for witness in \
  'pub const SEE_CAPTURE_ORDERING_SEARCH_POLICY_ID: u64 = 0x5332_3553_4545_4f31;' \
  'pub const SEE_CAPTURE_ORDERING: Self = Self::new' \
  'pub const fn see_capture_ordering_enabled' \
  'pub fn see_capture_ordering_candidate() -> Self'; do
  require_literal "$witness" "$policy"
done

for witness in \
  'static_exchange_evaluation(position, current)?' \
  'StaticExchangeClass::Winning => 3' \
  'StaticExchangeClass::Equal => 2' \
  'StaticExchangeClass::Losing => 1' \
  'ordered_legal_moves_with_state_and_tt_move_and_see' \
  'recursively_retained_ordering_excludes_temporary_sort_keys'; do
  require_literal "$witness" "$ordering"
done

for witness in \
  'SeeWinningCapture' \
  'SeeEqualCapture' \
  'SeeLosingCapture' \
  'see_winning_captures' \
  'see_equal_captures' \
  'see_losing_captures'; do
  require_literal "$witness" "$diagnostics"
done

require_literal 'StaticExchange(StaticExchangeError)' "$alpha_beta"
require_literal 'see_capture_ordering: policy.search_policy.see_capture_ordering_enabled()' "$alpha_beta"
require_literal 'ordered_legal_moves_with_see(position, &tokens, ordering, see_capture_ordering)?' "$quiescence"
require_literal 'candidate_preserves_exact_scores_mate_distance_and_legal_pvs' "$tests"
require_literal 'candidate_records_exact_capture_classes_without_pruning' "$tests"
require_literal 'diagnostics.see_prunes(), 0' "$tests"
require_literal 'run_engine_variant_validation' "$evidence"
require_literal 'EngineVariantResourceProtocol::FixedNodes' "$evidence"
require_literal 'EngineVariantResourceProtocol::ClockMilliseconds' "$evidence"
require_literal 'baseline_maximum_allocations' "$evidence"
require_literal 'candidate_maximum_allocations' "$evidence"
require_literal 'allocation_delta' "$evidence"
require_literal 'contents: read' "$workflow"
require_literal 'task_s2_5_see_ordering_audit.sh' "$ci"

if grep -Eq 'contents: write|git push|git commit|s2_5_.*apply.py' "$workflow"; then
  echo 'permanent S2-5 workflow retains write or staging behavior' >&2
  exit 1
fi

if grep -R --line-number 'see_capture_ordering_candidate' \
  "$root/crates/chess-uci" "$root/crates/chess-ffi" "$root/android" 2>/dev/null; then
  echo 'S2-5 candidate leaked into a production adapter/default' >&2
  exit 1
fi

for temporary in \
  "$root/scripts/s2_5_apply.py" \
  "$root/scripts/s2_5_refine.py" \
  "$root/scripts/s2_5_fix_compile.py" \
  "$root/scripts/s2_5_reduce_stack.py" \
  "$root/scripts/s2_5_evidence_apply.py" \
  "$root/scripts/s2_5_evidence_refine.py" \
  "$root/scripts/s2_5_evidence_allocation_refine.py" \
  "$root/.github/workflows/s2-5-apply-temp.yml" \
  "$root/.github/workflows/s2-5-evidence-apply-temp.yml"; do
  test ! -e "$temporary" || { echo "temporary S2-5 asset remains: ${temporary#$root/}" >&2; exit 1; }
done

echo 'S2-5 SEE capture-ordering audit passed'
