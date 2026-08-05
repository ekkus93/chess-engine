#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
policy="$root/crates/chess-search/src/search_policy.rs"
quiescence="$root/crates/chess-search/src/quiescence.rs"
diagnostics="$root/crates/chess-search/src/diagnostics.rs"
evidence="$root/crates/chess-tools/src/bin/s2_6_quiescence.rs"
doc="$root/docs/RUST_CHESS_ENGINE_V0_2_S2_6_QUIESCENCE_2026-08-05.md"
workflow="$root/.github/workflows/s2-6-quiescence.yml"
ci="$root/.github/workflows/ci.yml"

require_file() {
  test -f "$1" || { echo "missing S2-6 asset: ${1#$root/}" >&2; exit 1; }
}

require_literal() {
  grep -Fq "$1" "$2" || {
    echo "missing S2-6 witness in ${2#$root/}: $1" >&2
    exit 1
  }
}

for path in "$policy" "$quiescence" "$diagnostics" "$evidence" "$doc" "$workflow" "$ci"; do
  require_file "$path"
done

for witness in \
  'SEE_QUIESCENCE_PRUNING_SEARCH_POLICY_ID' \
  'SEE_AND_DELTA_QUIESCENCE_PRUNING_SEARCH_POLICY_ID' \
  'DeltaPruningRequiresSeePruning' \
  'see_quiescence_pruning_candidate' \
  'see_and_delta_quiescence_pruning_candidate'; do
  require_literal "$witness" "$policy"
done

for witness in \
  'SEE_QUIESCENCE_PRUNE_THRESHOLD_CENTIPAWNS: i32 = -100' \
  'DELTA_PRUNING_MARGIN_CENTIPAWNS: i32 = 200' \
  'QuiescenceDepthLimitReachedInCheck' \
  'tactical_move_count > 1' \
  'current.kind() != MoveKind::EnPassant' \
  'let gives_check = position.is_in_check(position.side_to_move())' \
  'StaticExchangeMoveStateError::InvalidTargetState' \
  'delta_pruning_is_exercised_only_after_see_under_a_narrow_window'; do
  require_literal "$witness" "$quiescence"
done

for witness in \
  'QuiescenceDeltaAttempt' \
  'quiescence_delta_attempts' \
  'QuiescenceSeePrune' \
  'QuiescenceDeltaPrune'; do
  require_literal "$witness" "$diagnostics"
done

for witness in \
  'reference_search_with_quiescence' \
  'run_engine_variant_validation' \
  'EngineVariantResourceProtocol::FixedNodes' \
  'EngineVariantResourceProtocol::ClockMilliseconds' \
  'baseline_maximum_allocations' \
  'activated=false'; do
  require_literal "$witness" "$evidence"
done

require_literal 'contents: read' "$workflow"
require_literal 'task_s2_6_quiescence_audit.sh' "$ci"

if grep -Eq 'contents: write|git push|git commit|s2_6_.*apply.py' "$workflow"; then
  echo 'permanent S2-6 workflow retains write or staging behavior' >&2
  exit 1
fi

if grep -R --line-number 'see_quiescence_pruning_candidate\|see_and_delta_quiescence_pruning_candidate' \
  "$root/crates/chess-uci" "$root/crates/chess-ffi" "$root/android" 2>/dev/null; then
  echo 'S2-6 candidate leaked into a production adapter/default' >&2
  exit 1
fi

for temporary in \
  "$root/scripts/s2_6_see_apply.py" \
  "$root/scripts/s2_6_see_driver.py" \
  "$root/scripts/s2_6_evidence_apply.py" \
  "$root/.github/workflows/s2-6-see-apply-temp.yml" \
  "$root/.github/workflows/s2-6-evidence-apply-temp.yml"; do
  test ! -e "$temporary" || { echo "temporary S2-6 asset remains: ${temporary#$root/}" >&2; exit 1; }
done

echo 'S2-6 quiescence audit passed'
