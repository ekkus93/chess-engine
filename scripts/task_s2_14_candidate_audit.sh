#!/usr/bin/env bash
set -euo pipefail

policy='crates/chess-search/src/search_policy.rs'
candidate='crates/chess-tools/src/bin/s2_14_candidate.rs'
production='crates/chess-tools/src/bin/s2_14_production.rs'

grep -Fq 'S2_14_SEE_LMR_SEARCH_POLICY_ID' "$policy"
grep -Fq 'pub fn s2_14_see_lmr_candidate()' "$policy"
grep -Fq 'ExperimentalSearchFeatures::S2_14_SEE_LMR' "$policy"
grep -Fq 'candidate_policy = SearchPolicySet::s2_14_see_lmr_candidate()' "$production"
grep -Fq 'pair_count: 1_000' "$production"
grep -Fq 'const OPENING_COUNT: usize = 1_200' "$production"
grep -Fq 'opening_provenance\tfirst_party_deterministic_generator_v1' "$production"
grep -Fq 'opening_license\tMIT' "$production"

python3 - <<'PY2'
from pathlib import Path
text = Path('crates/chess-search/src/search_policy.rs').read_text()
start = text.index('/// Frozen inactive S2-14 candidate: SEE capture ordering plus bounded verified LMR.')
end = text.index('/// Inactive S2-9 candidate:', start)
block = text[start:end]
for forbidden in ('PRINCIPAL_VARIATION_SEARCH', 'NULL_MOVE_PRUNING', 'SEE_QUIESCENCE_PRUNING', 'DELTA_PRUNING'):
    if forbidden in block:
        raise SystemExit(f'forbidden S2-14 feature in frozen policy: {forbidden}')
PY2

! grep -R -E 'S2_14_SEE_LMR|s2_14_see_lmr' crates/chess-uci crates/chess-ffi android 2>/dev/null

echo 'S2-14 candidate audit passed'
