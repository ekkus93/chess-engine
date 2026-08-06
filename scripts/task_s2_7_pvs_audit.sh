#!/usr/bin/env bash
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
