#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
see="$root/crates/chess-core/src/see.rs"
tests="$root/crates/chess-core/src/see_tests.rs"
lib="$root/crates/chess-core/src/lib.rs"
benchmark="$root/crates/chess-tools/src/bin/s2_4_see_benchmark.rs"
fuzz_lib="$root/fuzz/src/lib.rs"
fuzz_target="$root/fuzz/fuzz_targets/static_exchange.rs"
fuzz_manifest="$root/fuzz/Cargo.toml"
robustness="$root/.github/workflows/robustness.yml"
miri="$root/crates/chess-core/tests/miri_core.rs"
workflow="$root/.github/workflows/s2-4-stage.yml"
doc="$root/docs/RUST_CHESS_ENGINE_V0_2_S2_4_SEE_2026-08-05.md"

require_file() {
  test -f "$1" || { echo "missing S2-4 asset: ${1#$root/}" >&2; exit 1; }
}

require_literal() {
  grep -Fq "$1" "$2" || {
    echo "missing S2-4 witness in ${2#$root/}: $1" >&2
    exit 1
  }
}

for path in "$see" "$tests" "$lib" "$benchmark" "$fuzz_lib" "$fuzz_target" \
  "$fuzz_manifest" "$robustness" "$miri" "$workflow" "$doc"; do
  require_file "$path"
done

for witness in \
  'pub const STATIC_EXCHANGE_SCHEMA_VERSION: u16 = 1;' \
  'pub const STATIC_EXCHANGE_POLICY_ID: u64 = 0x5345_4556_414c_3031;' \
  'pub const MAX_STATIC_EXCHANGE_PLIES: u8 = 64;' \
  'pub enum StaticExchangeClass' \
  'pub struct StaticExchangeValue' \
  'pub enum StaticExchangeMoveStateError' \
  'pub enum StaticExchangeError' \
  'pub const fn static_exchange_piece_value' \
  'pub fn static_exchange_semantic_checksum' \
  'pub fn static_exchange_evaluation' \
  'least_valuable_legal_attacker' \
  'king_is_attacked' \
  'validated_en_passant_capture_square'; do
  require_literal "$witness" "$see"
done

if grep -Eq 'Vec<|HashMap|BTreeMap|Box<|String' "$see"; then
  echo 'SEE production module contains heap-backed storage' >&2
  exit 1
fi
require_literal 'static_exchange_evaluation' "$lib"
require_literal 'curated_and_deterministic_generated_positions_match_legal_oracle' "$tests"
require_literal 'rook_and_bishop_xray_sequences_match_the_independent_legal_oracle' "$tests"
require_literal 'malformed_exchange_inputs_fail_loudly_without_mutation' "$tests"
require_literal 'maximum_allocations != 0' "$benchmark"
require_literal '"see.exchange' "$benchmark"
require_literal 'fuzz_static_exchange' "$fuzz_lib"
require_literal 'name = "static_exchange"' "$fuzz_manifest"
require_literal 'static_exchange' "$robustness"
require_literal 'miri_static_exchange_is_deterministic_non_mutating_and_bounded' "$miri"
require_literal 'contents: read' "$workflow"
if grep -Eq 'contents: write|git push|git commit|s2_4_.*stage.py' "$workflow"; then
  echo 'permanent S2-4 workflow retains write or staging behavior' >&2
  exit 1
fi
for temporary in "$root/scripts/s2_4_core_stage.py" "$root/scripts/s2_4_evidence_stage.py"; do
  test ! -e "$temporary" || { echo "temporary S2-4 helper remains: ${temporary#$root/}" >&2; exit 1; }
done

echo 'S2-4 standalone SEE audit passed'
