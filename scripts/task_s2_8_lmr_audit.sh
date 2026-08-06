#!/usr/bin/env bash
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
evidence="crates/chess-tools/src/bin/s2_8_lmr.rs"
workflow=".github/workflows/s2-8-lmr.yml"

for path in "$policy" "$search" "$diagnostics" "$ordering" "$lib" "$tests" "$evidence" "$workflow"; do
  [[ -f "$path" ]] || fail "missing $path"
done

grep -q 'pub const LATE_MOVE_REDUCTIONS_SEARCH_POLICY_ID' "$policy" || fail "missing LMR identity"
grep -q 'pub const LMR_MINIMUM_DEPTH: u16 = 4' "$policy" || fail "missing minimum depth"
grep -q 'pub const LMR_MINIMUM_MOVE_INDEX: u16 = 4' "$policy" || fail "missing minimum move index"
grep -q 'pub const LMR_MINIMUM_LEGAL_MOVES: u16 = 6' "$policy" || fail "missing low-mobility guard"
grep -q 'pub const LMR_MINIMUM_TOTAL_PIECES: u16 = 10' "$policy" || fail "missing low-material guard"
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
grep -q 'total_piece_count' "$search" || fail "low-material nodes are not protected"
grep -q 'request.alpha.is_mate()' "$search" || fail "mate alpha windows are not protected"
grep -q 'request.beta.is_mate()' "$search" || fail "mate beta windows are not protected"
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

grep -q 'late_move_reductions_candidate' "$evidence" || fail "evidence harness does not select LMR"
grep -q 'lmr_reduced_fail_highs' "$evidence" || fail "evidence omits reduced fail-highs"
grep -q 'selective_depth' "$evidence" || fail "evidence omits selective depth"
grep -q 'activated=false' "$evidence" || fail "evidence omits inactive disposition"
grep -q '^permissions:' "$workflow" || fail "workflow permissions are missing"
grep -q '^  contents: read$' "$workflow" || fail "permanent workflow is not read-only"
if grep -q 'contents: write' "$workflow"; then
  fail "permanent workflow can write repository contents"
fi
