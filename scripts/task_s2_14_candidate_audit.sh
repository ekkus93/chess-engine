#!/usr/bin/env bash
set -euo pipefail

policy='crates/chess-search/src/search_policy.rs'
pvs='crates/chess-tools/src/bin/s2_7_pvs.rs'
production='crates/chess-tools/src/bin/s2_14_production.rs'
rejection='docs/RUST_CHESS_ENGINE_V0_2_S2_14_SEE_LMR_PREFLIGHT_REJECTION_2026-08-06.md'

test -f "$pvs"
test -f "$production"
test -f "$rejection"
test ! -e crates/chess-tools/src/bin/s2_14_candidate.rs

grep -Fq 'pub const PRINCIPAL_VARIATION_SEARCH_POLICY_ID: u64 = 0x5332_3750_5653_3031;' "$policy"
grep -Fq 'pub fn principal_variation_search_candidate()' "$policy"
grep -Fq 'candidate_policy = SearchPolicySet::principal_variation_search_candidate()' "$production"
grep -Fq 'pair_count: 1_000' "$production"
grep -Fq 'const OPENING_COUNT: usize = 1_200' "$production"
grep -Fq 'opening_provenance\tfirst_party_deterministic_generator_v1' "$production"
grep -Fq 'opening_license\tMIT' "$production"
grep -Fq '0x5332_3134_534d_4f4b' "$production"
grep -Fq '0x5332_3134_4445_5631' "$production"
grep -Fq '0x5332_3134_5052_4f44' "$production"
grep -Fq '**Disposition:** `rejected_performance_preflight`' "$rejection"

if grep -R -E 'S2_14_SEE_LMR|s2_14_see_lmr' crates; then
  echo 'rejected SEE+LMR candidate remains in active source' >&2
  exit 1
fi

python3 - <<'PY2'
from pathlib import Path
text = Path('crates/chess-tools/src/bin/s2_14_production.rs').read_text()
start = text.index('let candidate_policy = SearchPolicySet::principal_variation_search_candidate();')
end = text.index('let openings = control_openings()?;', start)
block = text[start:end]
required = (
    '!candidate_policy.policy.principal_variation_search_enabled()',
    'candidate_policy.policy.see_capture_ordering_enabled()',
    'candidate_policy.policy.see_quiescence_pruning_enabled()',
    'candidate_policy.policy.delta_pruning_enabled()',
    'candidate_policy.policy.late_move_reductions_enabled()',
    'candidate_policy.policy.null_move_pruning_enabled()',
)
for witness in required:
    if witness not in block:
        raise SystemExit(f'missing PVS freeze witness: {witness}')
PY2

! grep -R -E 'principal_variation_search_candidate|PRINCIPAL_VARIATION_SEARCH_POLICY_ID'   crates/chess-uci crates/chess-ffi crates/chess-jni android-harness 2>/dev/null

echo 'S2-14 PVS candidate audit passed'
