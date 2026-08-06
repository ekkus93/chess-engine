#!/usr/bin/env bash
set -euo pipefail

fail() {
  echo "S2-9.4 null-move validation audit failed: $*" >&2
  exit 1
}

tracker=docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md
record=docs/RUST_CHESS_ENGINE_V0_2_S2_9_NULL_MOVE_2026-08-06.md
policy_record=docs/RUST_CHESS_ENGINE_V0_2_S2_9_NULL_MOVE_POLICY_2026-08-05.md
corpus=fixtures/s2_9_null_move_validation_v1.tsv
tests=crates/chess-search/tests/s2_9_null_move_validation.rs
harness=crates/chess-tools/src/bin/s2_9_null_move.rs
policy=crates/chess-search/src/search_policy.rs
search=crates/chess-search/src/alpha_beta.rs
workflow=.github/workflows/s2-9-null-policy.yml

for path in "$tracker" "$record" "$policy_record" "$corpus" "$tests" "$harness" "$policy" "$search" "$workflow"; do
  [[ -f "$path" ]] || fail "missing $path"
done

[[ "$(head -n 1 "$corpus")" == $'S2_9_NULL_MOVE_VALIDATION\t1' ]] || fail "corpus header changed"
rows="$(grep -Ev '^(#|$)' "$corpus" | tail -n +2 | wc -l | tr -d ' ')"
[[ "$rows" -eq 14 ]] || fail "expected 14 corpus rows, found $rows"
for category in zugzwang stalemate repetition fifty-move seventy-five-move mate-distance longest-survival midgame; do
  grep -Fq $'\t'"$category"$'\t' "$corpus" || fail "missing corpus category $category"
done

grep -Fq 'make_search_null()' "$tests" || fail "synthetic-pass stalemate transition is missing"
grep -Fq 'unmake_search_null(undo)' "$tests" || fail "synthetic-pass restoration is missing"
grep -Fq 'repetition_root' "$tests" || fail "repetition regression is missing"
grep -Fq '99_u16' "$tests" && fail "unexpected generated halfmove loop shape"
grep -Fq '[100_u16, 149_u16, 150_u16]' "$tests" || fail "rule-boundary roots are missing"
grep -Fq 'mate_distance_and_longest_survival_match_baseline' "$tests" || fail "mate corpus is missing"
grep -Fq 'repeated_success_and_bounded_cancellation_restore_exactly' "$tests" || fail "restoration/cancellation regression is missing"
grep -Fq 'null_move_speculative_fail_highs()' "$tests" || fail "verification invariant is missing"

grep -Fq 'const FIXED_NODE_PAIRS: u32 = 8;' "$harness" || fail "fixed-node pair count changed"
grep -Fq 'const FIXED_NODE_LIMIT: u64 = 2_000;' "$harness" || fail "fixed-node limit changed"
grep -Fq 'const CLOCK_PAIRS: u32 = 8;' "$harness" || fail "clock pair count changed"
grep -Fq 'const CLOCK_MILLISECONDS: u64 = 10;' "$harness" || fail "clock limit changed"
grep -Fq 'const MAXIMUM_MATCH_PLIES: u32 = 48;' "$harness" || fail "maximum match plies changed"
grep -Fq 'diff' "$workflow" || fail "deterministic reproducibility gate is missing"

grep -Fq '**Validated candidate source SHA:** `8638611e38c712009e7f98bd4881fb266034df13`' "$record" || fail "validated source SHA is missing"
grep -Fq '**Staging validation run:** `31085412059`' "$record" || fail "staging run is missing"
grep -Fq '**Evidence artifact:** `8961204541`' "$record" || fail "artifact ID is missing"
grep -Fq '**Artifact digest:** `sha256:1c7ed56774119f9d771453e045b03345d4aae31d840eec30a7c03b96a28d8a19`' "$record" || fail "artifact digest is missing"
grep -Fq '**Disposition:** `rejected_strength`' "$record" || fail "final disposition is missing"
grep -Fq '**Activation:** `false`' "$record" || fail "inactive disposition is missing"
grep -Fq 'aggregate checksum: `75da625a5ae9c6d7`' "$record" || fail "parity checksum is missing"
grep -Fq 'report checksum: `81a8a72c9242da64`' "$record" || fail "fixed-node checksum is missing"
grep -Fq 'report checksum: `9054382ea9b188c5`' "$record" || fail "clock checksum is missing"
grep -Fq '**Status:** Complete — standalone activation rejected; candidate inactive' "$policy_record" || fail "policy record was not closed"

grep -Fq '| S2-9 | Optional null-move pruning decision/candidate | **Complete — standalone rejected; inactive** |' "$tracker" || fail "summary is not complete"
grep -Fq '# Task S2-9: Optional null-move pruning decision/candidate — COMPLETE' "$tracker" || fail "task heading is not complete"
grep -Fq '## S2-9.4 validation record' "$tracker" || fail "validation record is missing"
if grep -Fq -- '- S2-9.4 correctness, development strength, and final disposition are not claimed.' "$tracker"; then
  fail "stale pre-validation disclaimer remains"
fi
s2_9="$(sed -n '/# Task S2-9:/,/# Task S2-10:/p' "$tracker")"
[[ "$(grep -Fc -- '- [x]' <<<"$s2_9")" -eq 23 ]] || fail "S2-9 does not have exactly 23 completed requirements"
[[ "$(grep -Fc -- '- [ ]' <<<"$s2_9")" -eq 0 ]] || fail "S2-9 still has incomplete requirements"

grep -Fq '# Task S2-10: Optional frontier and quiet-move pruning candidates' "$tracker" || fail "successor S2-10 task is missing"
s2_10="$(sed -n '/# Task S2-10:/,/# Task S2-11:/p' "$tracker")"
[[ "$(grep -Foc -- '- [' <<<"$s2_10")" -gt 0 ]] || fail "S2-10 has no tracked requirements"

grep -Fq '&SearchPolicy::V0_1' "$search" || fail "default production search is not V0_1"
grep -Fq 'pub fn null_move_pruning_candidate' "$policy" || fail "isolated candidate identity is missing"
if grep -R -n -E 'make_search_null|NULL_MOVE_PRUNING' crates/chess-uci crates/chess-api crates/chess-ffi crates/chess-jni 2>/dev/null; then
  fail "null move leaked into a production adapter"
fi

for path in .github/s2_9_4_finalize.py .github/workflows/s2-9-4-stage.yml .github/workflows/s2-9-4-finalize.yml; do
  [[ ! -e "$path" ]] || fail "temporary helper remains: $path"
done

grep -q '^permissions:' "$workflow" || fail "permanent workflow permissions are missing"
grep -q '^  contents: read$' "$workflow" || fail "permanent workflow is not read-only"
if grep -q 'contents: write' "$workflow"; then
  fail "permanent workflow can write repository contents"
fi

echo "S2-9.4 null-move validation audit passed"
