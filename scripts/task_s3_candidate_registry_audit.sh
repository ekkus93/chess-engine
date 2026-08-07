#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

fail() {
  echo "s3-candidate-registry-audit: $*" >&2
  exit 1
}

require_file() {
  test -f "$1" || fail "missing required file: $1"
}

require_literal() {
  grep -Fq "$1" "$2" || fail "missing witness in $2: $1"
}

candidate=crates/chess-tools/src/s3_candidate.rs
lib=crates/chess-tools/src/lib.rs
require_file "$candidate"
require_file "$lib"

require_literal 'pub mod s3_candidate;' "$lib"
require_literal 'pub const S3_CANDIDATE_SCHEMA_VERSION: u16 = 1;' "$candidate"
require_literal 'pub const S3_CANDIDATE_FORMAT_IDENTIFIER: u64 = 0x5333_4341_4e44_3031;' "$candidate"
require_literal 'pub const S3_VALIDATION_LOSS_TOLERANCE: f64 = 1.0e-12;' "$candidate"
require_literal 'RejectNoTrainingImprovement' "$candidate"
require_literal 'RejectValidationRegression' "$candidate"
require_literal 'pub struct S3CandidateEnvelope' "$candidate"
require_literal 'pub struct S3CandidateRegistry' "$candidate"
require_literal 'if self.activated {' "$candidate"
require_literal 'return Err(S3CandidateError::ActivationForbidden);' "$candidate"
require_literal 'DuplicateCandidateIdentifier' "$candidate"
require_literal 'fn held_out_rule_requires_strict_training_improvement()' "$candidate"
require_literal 'fn candidate_round_trip_binds_artifact_and_remains_inactive()' "$candidate"
require_literal 'fn schema_checksum_baseline_type_and_length_fail_closed()' "$candidate"
require_literal 'fn artifact_corruption_and_duplicate_ids_fail_closed()' "$candidate"

for temporary in \
  .github/s3_candidate_stage.py \
  .github/workflows/s3-candidate-stage.yml; do
  if test -e "$temporary"; then
    fail "temporary candidate-registry staging control remains: $temporary"
  fi
done

# Candidate metadata is validation-only and must not escape into production adapters.
for path in crates/chess-uci crates/chess-ffi crates/chess-jni android-harness; do
  if grep -R --line-number --include='*.rs' --include='*.kt' 'S3Candidate' "$path"; then
    fail "S3 candidate registry escaped through production adapter path $path"
  fi
done

# No candidate work can silently change the current release identity.
grep -Fq 'version = "0.1.0"' Cargo.toml || fail 'package version drifted from v0.1'
grep -Fq 'pub const V0_1_SEARCH_POLICY_ID: u64 = 0x5630_315f_504f_4c31;' crates/chess-search/src/search_policy.rs || fail 'v0.1 search policy identity drifted'
grep -Fq 'pub const BASELINE_WEIGHT_SET_ID: u64 = 0x4241_5345_4c49_4e45;' crates/chess-search/src/weights.rs || fail 'baseline evaluation identity drifted'

echo 'S3 candidate registry audit passed'
