#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

fail() {
  echo "s4-evaluation-tuning-calibration-audit: $*" >&2
  exit 1
}

require_file() {
  test -f "$1" || fail "missing required file: $1"
}

require_literal() {
  grep -Fq "$1" "$2" || fail "missing witness in $2: $1"
}

spec=docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_SPEC_2026-08-07.md
tracker=docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_TODO_2026-08-07.md
baseline=docs/RUST_CHESS_ENGINE_S4_BASELINE_2026-08-07.md
diagnosis=docs/RUST_CHESS_ENGINE_S4_ZERO_MOVEMENT_DIAGNOSIS_2026-08-07.md
corpus=docs/RUST_CHESS_ENGINE_S4_CALIBRATION_CORPUS_2026-08-07.md
matrix=docs/RUST_CHESS_ENGINE_S4_HYPERPARAMETER_MATRIX_RESULTS_2026-08-07.md
selected=docs/RUST_CHESS_ENGINE_S4_SELECTED_CANDIDATE_REPRODUCTION_2026-08-07.md
smoke=docs/RUST_CHESS_ENGINE_S4_DEVELOPMENT_STRENGTH_SMOKE_2026-08-07.md
method=docs/RUST_CHESS_ENGINE_S4_METHOD_DISPOSITION_AND_S5_READINESS_2026-08-07.md
final_report=docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_IMPLEMENTATION_REPORT.md
legacy=docs/LEGACY_TODO_INDEX.md
s3_tracker=docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_TODO_2026-08-07.md
s3_report=docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_IMPLEMENTATION_REPORT.md
diagnostics=crates/chess-tune/src/diagnostics.rs
trace=crates/chess-tune/src/trace.rs
optimizer=crates/chess-tune/src/optimizer.rs

for path in "$spec" "$tracker" "$baseline" "$diagnosis" "$corpus" "$matrix" "$selected" "$smoke" "$method" "$final_report" "$legacy" "$s3_tracker" "$s3_report" "$diagnostics" "$trace" "$optimizer"; do
  require_file "$path"
done

# Preserve all prior closure/correctness guarantees.
bash scripts/task_s3_evaluation_strength_audit.sh

# S4 is the only active program; S3 remains closed and historical.
require_literal 'Active S4 evaluation tuning calibration program' "$legacy"
require_literal '`docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_TODO_2026-08-07.md`' "$legacy"
require_literal '**Status:** Closure candidate — S4-0 through S4-11 complete; S4-12 exact final validation pending' "$tracker"
require_literal '**Status:** Closure candidate; implementation complete through S4-11, exact final validation pending' "$spec"
require_literal '**Status:** Complete — program closed without promotion' "$s3_tracker"
if grep -Fq '| Active S3 evaluation strength program |' "$legacy"; then
  fail 'closed S3 tracker is active again'
fi

# Baseline identity and explicit correction of the inherited S3 closure gate.
require_literal '**S4 planning baseline SHA:** `543dce22e51e71f821e37754a97ce0f33c3be122`' "$baseline"
require_literal '**S4 clean operational baseline SHA:** `b02623f20417c7f5769b6a16fc94566239e7979a`' "$baseline"
require_literal '**Unchanged production/code baseline SHA:** `677cd2a4d2a4a4f3c376f7bf47fae412171206fb`' "$baseline"
require_literal 'Package/UCI version: `0.1.0`.' "$baseline"
require_literal 'v0.1 search-policy identifier/checksum: `5630315f504f4c31` / `0c0769ef9d034770`.' "$baseline"
require_literal 'Baseline evaluation-weight identifier/checksum: `424153454c494e45` / `d2cca7ae10ec6e34`.' "$baseline"
require_literal 'Runtime evaluation weight-vector length: `816`; named tunable-parameter count: `810`.' "$baseline"
require_literal 'C ABI version: `1`.' "$baseline"
require_literal 'Rust JNI export source blob: `63a3e4e4b7dcbe12106b17a36ce15117daa46cf8`.' "$baseline"
require_literal 'Kotlin public wrapper blob: `67c58b41e86be4d00ffb07a7296f5034f10b198e`.' "$baseline"
require_literal 'S3 Evaluation Strength run `31186888170`, job `92893571662`: **failure**.' "$baseline"
require_literal 'A failed permanent gate is not reclassified as green' "$baseline"
require_literal '**Workflow run:** `31198269449`' "$diagnosis"
require_literal '**Workflow job:** `92931740915`' "$diagnosis"
require_literal '**Artifact ID:** `9001742616`' "$diagnosis"
require_literal 'quantization_limited' "$diagnosis"
require_literal '`6,480`' "$diagnosis"
require_literal '`2.06410316075983228e-04`' "$diagnosis"
require_literal '**Workflow run:** `31199370707`' "$corpus"
require_literal 'dataset checksum: `85c0e5949cb329e3`' "$corpus"
require_literal '**Workflow run:** `31200184027`' "$matrix"
require_literal '**selected**' "$matrix"
require_literal '`520db5dd58086a8a`' "$matrix"
require_literal '**Workflow run:** `31201066297`' "$selected"
require_literal 'registered candidate count `1`' "$selected"
require_literal '**Workflow run:** `31203299756`' "$smoke"
require_literal '**Workflow job:** `92948219087`' "$smoke"
require_literal '**Artifact ID:** `9003757817`' "$smoke"
require_literal '`12 / 4 / 16`' "$smoke"
require_literal '`14 / 2 / 15`' "$smoke"
require_literal 'decision: `rejected_strength`' "$smoke"
require_literal '**Status:** Accepted for future evaluator experimentation; not production activation evidence' "$method"
require_literal '**Status:** Closure candidate — exact final validation pending' "$final_report"
require_literal 'No activation occurred anywhere in S4.' "$final_report"
require_literal '# Task S4-0: Authority registration and baseline freeze — COMPLETE' "$tracker"
require_literal '# Task S4-11: Method disposition and S5 readiness — COMPLETE (METHOD ACCEPTED FOR S5 EXPERIMENTATION)' "$tracker"
require_literal '# Task S4-12: Final report and closure — IN PROGRESS (EXACT FINAL VALIDATION PENDING)' "$tracker"

# Release identities remain frozen.
require_literal 'version = "0.1.0"' Cargo.toml
require_literal 'pub const V0_1_SEARCH_POLICY_ID: u64 = 0x5630_315f_504f_4c31;' crates/chess-search/src/search_policy.rs
require_literal 'pub const BASELINE_WEIGHT_SET_ID: u64 = 0x4241_5345_4c49_4e45;' crates/chess-search/src/weights.rs
require_literal 'pub const WEIGHT_VALUE_COUNT: usize = 816;' crates/chess-search/src/weights.rs
require_literal 'pub const TUNABLE_PARAMETER_COUNT: usize = 810;' crates/chess-tune/src/lib.rs
require_literal 'pub const S3_CANDIDATE_SCHEMA_VERSION: u16 = 1;' crates/chess-tools/src/s3_candidate.rs
require_literal 'pub const S3_CANDIDATE_FORMAT_IDENTIFIER: u64 = 0x5333_4341_4e44_3031;' crates/chess-tools/src/s3_candidate.rs

# S4 optimizer diagnostics and strict trace contract.
require_literal 'pub const S4_OPTIMIZER_DIAGNOSTIC_SCHEMA_VERSION: u16 = 1;' "$diagnostics"
require_literal 'pub const S4_OPTIMIZER_DIAGNOSTIC_IDENTIFIER: u64 = 0x5334_4449_4147_3031;' "$diagnostics"
require_literal 'pub const S4_OPTIMIZER_TRACE_SCHEMA_VERSION: u16 = 1;' "$trace"
require_literal 'pub const S4_OPTIMIZER_TRACE_IDENTIFIER: u64 = 0x5334_5452_4143_3031;' "$trace"
require_literal 'pub fn advance_with_diagnostics(' "$optimizer"
require_literal 'positive_regularization' "$diagnostics"
require_literal 'zero_after_quantization_count' "$diagnostics"
require_literal 'clipped_update_count' "$diagnostics"
require_literal 'initial_checkpoint_checksum' "$trace"
require_literal 'pub fn validate_binding(' "$trace"
require_literal 'if trace.to_text()? != text' "$trace"
require_literal 'trace_round_trip_is_bit_canonical' "$trace"
require_literal 'trace_checksum_corruption_fails_closed' "$trace"
require_literal 'wrong_binding_fails_closed' "$trace"
require_literal 'advance_with_diagnostics(&dataset, iterations)' crates/chess-tools/src/tuning_cli.rs
require_literal 's4-optimizer-trace.txt' crates/chess-tools/src/tuning_cli.rs
require_literal 's4-summary.tsv' crates/chess-tools/src/tuning_cli.rs
require_literal 's3-candidate-envelope.txt' crates/chess-tools/src/tuning_cli.rs
require_literal 's3-candidate-registry.tsv' crates/chess-tools/src/tuning_cli.rs
require_literal 'S3CandidateRegistry::default()' crates/chess-tools/src/tuning_cli.rs
require_literal '.validate_artifact(candidate)' crates/chess-tools/src/tuning_cli.rs
require_literal 'envelope.loss_decision.name()' crates/chess-tools/src/tuning_cli.rs
require_literal 'changed_parameter_count' crates/chess-tools/src/tuning_cli.rs
require_literal 'maximum_absolute_parameter_delta' crates/chess-tools/src/tuning_cli.rs
require_literal 'mean_absolute_parameter_delta' crates/chess-tools/src/tuning_cli.rs
require_literal 'zero_after_quantization_count' crates/chess-tools/src/tuning_cli.rs
require_literal 'clipping_count' crates/chess-tools/src/tuning_cli.rs
require_literal 'candidate_value_checksum' crates/chess-tools/src/tuning_cli.rs
require_literal 'disposition' crates/chess-tools/src/tuning_cli.rs
require_literal 'unassessed' crates/chess-tools/src/tuning_cli.rs
require_literal 'initial_checkpoint_checksum: checkpoint_checksum(&initial_checkpoint)?' crates/chess-tools/src/tuning_cli.rs
require_literal 'fn apply_gradient_step(' "$optimizer"
require_literal 'subinteger_update_is_explicitly_quantization_limited' "$optimizer"
require_literal 'effective_integer_update_changes_runtime_checksum' "$optimizer"
require_literal 'clipping_accounting_is_signed_and_exact' "$optimizer"
require_literal 'regularization_contribution_is_independently_accounted' "$optimizer"
require_literal 'one_parameter_known_answer_moves_toward_optimum_deterministically' "$optimizer"
require_literal 'multi_parameter_known_answer_preserves_inactive_values_and_converges' "$optimizer"
require_literal 'S4_DEGRADED_TEST_WEIGHT_ID' "$optimizer"
require_literal 'degraded_queen_material_recovers_real_chess_loss_signal' "$optimizer"
require_file crates/chess-tools/src/bin/s4_candidate_smoke.rs
require_literal 'NamedWeightArtifact::deserialize' crates/chess-tools/src/bin/s4_candidate_smoke.rs
require_literal 'SearchPolicySet::baseline()' crates/chess-tools/src/bin/s4_candidate_smoke.rs
require_literal 'EvaluationWeightSet::new(artifact.identifier, artifact.weights)' crates/chess-tools/src/bin/s4_candidate_smoke.rs
require_literal 'EngineVariantValidationTier::Development' crates/chess-tools/src/bin/s4_candidate_smoke.rs
require_literal 'activated' crates/chess-tools/src/bin/s4_candidate_smoke.rs
require_literal 'false' crates/chess-tools/src/bin/s4_candidate_smoke.rs
require_literal 'final_validation <= initial_validation + 0.02' "$optimizer"

for path in crates/chess-uci/src crates/chess-ffi/src crates/chess-jni/src crates/chess-jni/kotlin/src/main android-harness; do
  if grep -R --line-number --include='*.rs' --include='*.kt' 'S4_DEGRADED_TEST_WEIGHT_ID' "$path"; then
    fail "test-only degraded S4 evaluator escaped through $path"
  fi
done

# Temporary S4 staging controls must never become permanent evidence.
while IFS= read -r path; do
  case "$path" in
    .github/workflows/s4-evaluation-tuning-calibration.yml)
      ;;
    *)
      fail "temporary S4 control remains: $path"
      ;;
  esac
done < <(find .github -maxdepth 2 -type f \( -name 's4_*stage*.py' -o -name 's4-*-stage.yml' -o -name 's4_*fix*.py' \) -print | sort)

for temporary in .github/s4_closure_stage.py .github/workflows/s4-closure-stage.yml .github/s4_s3_audit_transition.py .github/workflows/s4-s3-audit-transition.yml; do
  test ! -e "$temporary" || fail "temporary S4 closure/transition control remains: $temporary"
done

# Permanent S4 workflow must be read-only.
require_file .github/workflows/s4-evaluation-tuning-calibration.yml
if grep -Fq 'contents: write' .github/workflows/s4-evaluation-tuning-calibration.yml; then
  fail 'permanent S4 workflow is write-capable'
fi
require_literal 'contents: read' .github/workflows/s4-evaluation-tuning-calibration.yml

# Calibration work must not create a production Python/subprocess fallback.
if grep -R --line-number --include='*.rs' -E 'Command::new\("python(3)?"|Py_Initialize|pyo3' crates; then
  fail 'production Rust gained a Python/subprocess fallback'
fi

echo 'S4 evaluation-tuning calibration closure-candidate audit passed'
