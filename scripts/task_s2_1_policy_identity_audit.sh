#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

required=(
  crates/chess-search/src/search_policy.rs
  crates/chess-tools/src/policy_io.rs
  crates/chess-tools/src/engine_variant.rs
  crates/chess-search/tests/search_policy_identity.rs
  docs/RUST_CHESS_ENGINE_SEARCH_POLICY_AND_VARIANT_IDENTITY.md
)
for path in "${required[@]}"; do
  test -f "$path" || {
    echo "missing S2-1 asset: $path" >&2
    exit 1
  }
done

grep -Fq 'pub const SEARCH_POLICY_SCHEMA_VERSION: u16 = 1;' \
  crates/chess-search/src/search_policy.rs
grep -Fq 'pub const V0_1_SEARCH_POLICY_CHECKSUM: u64 = 0x0c07_69ef_9d03_4770;' \
  crates/chess-search/src/search_policy.rs
grep -Fq 'UnsupportedExperimentalFeature' crates/chess-search/src/search_policy.rs
grep -Fq 'iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights' \
  crates/chess-search/src/lib.rs
grep -Fq 'pub use policy_io::{deserialize_search_policy, serialize_search_policy};' \
  crates/chess-tools/src/lib.rs
grep -Fq 'pub mod engine_variant;' crates/chess-tools/src/lib.rs
grep -Fq 'policy-export' crates/chess-tools/src/main.rs
grep -Fq 'policy-validate' crates/chess-tools/src/main.rs

if grep -R --line-number --include='*.rs' 'SearchPolicy' \
  crates/chess-uci crates/chess-ffi crates/chess-jni; then
  echo 'experimental search policy must remain unavailable through UCI/FFI/JNI in S2-1' >&2
  exit 1
fi

if grep -E --line-number 'std::env|std::fs|File::|read_to_string|var\(' \
  crates/chess-search/src/search_policy.rs; then
  echo 'search policy core must not use implicit environment or filesystem discovery' >&2
  exit 1
fi

# Match only actual S2-1 staging names. A broad `*s2-1*` glob also matches
# later tasks such as `s2-14-*`, which would incorrectly reject permanent
# workflows for S2-10 through S2-19.
if find .github/workflows -maxdepth 1 -type f \
  \( -name 's2-1.yml' -o -name 's2-1-*' -o -name '*policy-patch*' \) -print | grep -q .; then
  echo 'temporary S2-1 workflow remains in the repository' >&2
  exit 1
fi

echo 'S2-1 search-policy and engine-variant identity audit passed'
