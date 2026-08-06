#!/usr/bin/env bash
set -euo pipefail

policy=crates/chess-search/src/search_policy.rs
search=crates/chess-search/src/alpha_beta.rs
diagnostics=crates/chess-search/src/diagnostics.rs
probe=crates/chess-search/src/transposition/probe.rs
tracker=docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md
doc=docs/RUST_CHESS_ENGINE_V0_2_S2_9_NULL_MOVE_POLICY_2026-08-05.md
workflow=.github/workflows/s2-9-null-policy.yml

grep -Fq 'pub const NULL_MOVE_PRUNING_SEARCH_POLICY_ID' "$policy"
grep -Fq 'pub const NULL_MOVE_MINIMUM_DEPTH: u16 = 4;' "$policy"
grep -Fq 'pub const NULL_MOVE_REDUCTION: u16 = 2;' "$policy"
grep -Fq 'pub const NULL_MOVE_VERIFICATION_REDUCTION: u16 = 1;' "$policy"
grep -Fq 'pub const NULL_MOVE_MINIMUM_SIDE_NON_PAWN_PIECES: u16 = 2;' "$policy"
grep -Fq 'pub const NULL_MOVE_MINIMUM_TOTAL_NON_PAWN_PIECES: u16 = 4;' "$policy"
grep -Fq 'pub const NULL_MOVE_VERIFY_ALL_CUTOFFS: bool = true;' "$policy"
grep -Fq 'pub const NULL_MOVE_PRUNING: Self' "$policy"
grep -Fq 'pub const fn null_move_pruning_enabled' "$policy"
grep -Fq 'pub fn null_move_pruning_candidate' "$policy"
grep -Fq 'NullMovePruningMustBeIsolated' "$policy"

grep -Fq 'enum NullMoveState' "$search"
grep -Fq 'SpeculativeSubtree' "$search"
grep -Fq 'VerificationSubtree' "$search"
grep -Fq 'fn decide_null_move' "$search"
grep -Fq 'position.make_search_null()' "$search"
grep -Fq 'position.unmake_search_null(undo)' "$search"
grep -Fq 'NullMoveVerificationSearch' "$search"
grep -Fq 'NullMoveSpeculativeFailHigh' "$search"
grep -Fq 'NullMoveDisabledReason::LowNonPawnMaterial' "$search"
grep -Fq 'TranspositionScoreReuse::SuppressedForNullMove' "$search"

grep -Fq 'SuppressedForNullMove' "$probe"
grep -Fq 'NullMoveDisabledReason' "$diagnostics"
grep -Fq 'NullMoveDisabledNodes' "$diagnostics"
grep -Fq 'NullMoveSpeculativeFailHighs' "$diagnostics"
grep -Fq 'NullMoveVerificationSearches' "$diagnostics"
grep -Fq 'pub const fn null_move_disabled_nodes' "$diagnostics"
grep -Fq 'pub const fn null_move_verification_searches' "$diagnostics"

test -f crates/chess-search/tests/s2_9_null_move.rs
test -f "$doc"
test -f "$workflow"
grep -Fq '**Activation:** `false`' "$doc"
grep -Fq '## S2-9.3 conservative policy record' "$tracker"
grep -Fq 'Begin with **S2-10.1 only**:' "$tracker"

s2_9_3="$(sed -n '/## S2-9.3 Conservative policy if implemented/,/## S2-9.4 Validation if implemented/p' "$tracker")"
test "$(grep -Fc -- '- [x]' <<<"$s2_9_3")" -eq 7
test "$(grep -Fc -- '- [ ]' <<<"$s2_9_3")" -eq 0

grep -q '^permissions:' "$workflow"
grep -q '^  contents: read$' "$workflow"
if grep -q 'contents: write' "$workflow"; then
  echo 'permanent S2-9.3 workflow can write repository contents' >&2
  exit 1
fi

# Default production entry points remain bound to V0_1.
grep -Fq '&SearchPolicy::V0_1' "$search"
# The synthetic transition remains absent from adapter and protocol crates.
if grep -R -n -E 'make_search_null|NULL_MOVE_PRUNING' crates/chess-uci crates/chess-api crates/chess-ffi crates/chess-jni 2>/dev/null; then
  echo 'S2-9 null move leaked into a production adapter' >&2
  exit 1
fi

test ! -e .github/s2_9_3_policy.py
test ! -e .github/workflows/s2-9-3-stage.yml
test ! -e .github/s2_9_3_finalize.py
