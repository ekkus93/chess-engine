#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

fail() {
  echo "v0.2-strength-audit: $*" >&2
  exit 1
}

require_file() {
  test -f "$1" || fail "missing required file: $1"
}

require_literal() {
  local literal="$1"
  local path="$2"
  grep -Fq "$literal" "$path" || fail "missing witness in $path: $literal"
}

# Preserve the complete signed-off foundation and every accepted/rejected/deferred
# v0.2 search decision before checking the integrated authority layer.
bash scripts/task_26_v0_1_audit.sh
bash scripts/task_27_full_port_audit.sh
bash scripts/task_post_port_review_fix_audit.sh
bash scripts/task_s2_1_policy_identity_audit.sh
bash scripts/task_s2_2_variant_validation_audit.sh
bash scripts/task_s2_3_baseline_audit.sh
bash scripts/task_s2_4_see_audit.sh
bash scripts/task_s2_5_see_ordering_audit.sh
bash scripts/task_s2_6_quiescence_audit.sh
bash scripts/task_s2_7_pvs_audit.sh
bash scripts/task_s2_8_lmr_audit.sh
bash scripts/task_s2_9_null_move_feasibility_audit.sh
bash scripts/task_s2_9_search_null_transition_audit.sh
bash scripts/task_s2_9_null_move_policy_audit.sh
bash scripts/task_s2_9_null_move_validation_audit.sh

required_paths=(
  docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_SPEC_2026-08-05.md
  docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md
  docs/RUST_CHESS_ENGINE_SEARCH_POLICY_AND_VARIANT_IDENTITY.md
  docs/RUST_CHESS_ENGINE_VARIANT_VALIDATION.md
  docs/RUST_CHESS_ENGINE_V0_2_BASELINE_2026-08-05.md
  docs/RUST_CHESS_ENGINE_V0_2_S2_3_BASELINE_2026-08-05.md
  docs/RUST_CHESS_ENGINE_V0_2_S2_4_SEE_2026-08-05.md
  docs/RUST_CHESS_ENGINE_V0_2_S2_5_SEE_ORDERING_2026-08-05.md
  docs/RUST_CHESS_ENGINE_V0_2_S2_6_QUIESCENCE_2026-08-05.md
  docs/RUST_CHESS_ENGINE_V0_2_S2_7_PVS_2026-08-05.md
  docs/RUST_CHESS_ENGINE_V0_2_S2_8_LMR_2026-08-05.md
  docs/RUST_CHESS_ENGINE_V0_2_S2_9_NULL_MOVE_2026-08-06.md
  docs/RUST_CHESS_ENGINE_V0_2_S2_10_1_FUTILITY_2026-08-06.md
  docs/RUST_CHESS_ENGINE_V0_2_S2_10_2_RAZORING_2026-08-06.md
  docs/RUST_CHESS_ENGINE_V0_2_S2_10_3_LATE_QUIET_MOVE_PRUNING_2026-08-06.md
  docs/RUST_CHESS_ENGINE_V0_2_S2_11_PROFILING_2026-08-06.md
  docs/RUST_CHESS_ENGINE_V0_2_S2_12_SYZYGY_DECISION_2026-08-06.md
  docs/RUST_CHESS_ENGINE_V0_2_S2_13_INTEGRATION_2026-08-06.md
  docs/RUST_CHESS_ENGINE_V0_2_S2_14_CANDIDATE_SELECTION_2026-08-06.md
  docs/RUST_CHESS_ENGINE_V0_2_S2_14_SEE_LMR_PREFLIGHT_REJECTION_2026-08-06.md
  docs/RUST_CHESS_ENGINE_V0_2_S2_14_PRODUCTION_VALIDATION_2026-08-06.md
  docs/RUST_DEVELOPER_WORKFLOWS.md
  docs/RUST_GENERATED_ARTIFACT_POLICY.md
  crates/chess-tools/src/bin/s2_13_variant_control.rs
  crates/chess-tools/src/bin/s2_14_production.rs
  scripts/task_s2_14_candidate_audit.sh
  scripts/task_v0_2_strength_audit.sh
  .github/workflows/variant-validation.yml
  .github/workflows/s2-14-candidate-preflight.yml
  .github/workflows/s2-14-production.yml
)
for path in "${required_paths[@]}"; do
  require_file "$path"
done

tracker=docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md
report=docs/RUST_CHESS_ENGINE_V0_2_S2_13_INTEGRATION_2026-08-06.md
policy=crates/chess-search/src/search_policy.rs
weights=crates/chess-search/src/weights.rs
variant=crates/chess-tools/src/engine_variant.rs
validation=crates/chess-tools/src/engine_variant_validation.rs
legacy=crates/chess-tools/src/candidate_validation.rs
control=crates/chess-tools/src/bin/s2_13_variant_control.rs
workflow=.github/workflows/variant-validation.yml
s2_14_report=docs/RUST_CHESS_ENGINE_V0_2_S2_14_PRODUCTION_VALIDATION_2026-08-06.md

require_literal '| S2-13 | API, UCI, ABI/JNI, Android, CI, and documentation integration | **Complete — internal candidate infrastructure integrated; public adapters unchanged; inactive** |' "$tracker"
require_literal '| S2-14 | Production candidate selection and validation | **Complete — PVS rejected_strength; v0.1 remains authoritative; inactive** |' "$tracker"
require_literal '# Task S2-13: API, UCI, ABI/JNI, Android, CI, and documentation integration — COMPLETE' "$tracker"
require_literal '# Task S2-14: Production candidate selection and validation — COMPLETE (REJECTED)' "$tracker"
s2_13="$(sed -n '/^# Task S2-13:/,/^# Task S2-14:/p' "$tracker")"
test "$(grep -Fc -- '- [x]' <<<"$s2_13")" -eq 33 || fail 'S2-13 must contain exactly 33 completed requirements'
test "$(grep -Fc -- '- [ ]' <<<"$s2_13")" -eq 0 || fail 'S2-13 retains incomplete requirements'
s2_14="$(sed -n '/^# Task S2-14:/,/^# Task S2-15:/p' "$tracker")"
test "$(grep -Fc -- '- [x]' <<<"$s2_14")" -eq 31 || fail 'S2-14 must contain exactly 31 completed requirements'
test "$(grep -Fc -- '- [ ]' <<<"$s2_14")" -eq 0 || fail 'S2-14 retains incomplete requirements'

# S2-14 is an evidence-backed rejection, not an activation. Pin the immutable
# candidate SHA and both independent production decisions so documentation
# cannot silently turn workflow success into candidate acceptance.
require_literal '**Status:** Complete — candidate rejected' "$s2_14_report"
require_literal '**Disposition:** `rejected_strength`' "$s2_14_report"
require_literal '**Activation:** `false`' "$s2_14_report"
require_literal '**Frozen candidate source SHA:** `21406b5e92b6bd42a3a902591dddae22c9b3f16f`' "$s2_14_report"
require_literal 'run `31146807904`, job `92767800034`' "$s2_14_report"
require_literal 'run `31146807904`, job `92767800098`' "$s2_14_report"
require_literal 'Report checksum: `bad7aa1f69e9d18e`.' "$s2_14_report"
require_literal 'Report checksum: `d3b883442ec6107b`.' "$s2_14_report"
require_literal 'Artifact `8982304975`' "$s2_14_report"
require_literal 'Artifact `8982375018`' "$s2_14_report"
require_literal '0.4578061271735924' "$s2_14_report"
require_literal '0.45802189803116894' "$s2_14_report"
require_literal 'does not authorize S2-15 activation' "$s2_14_report"

# Exact schema and identity boundaries.
require_literal 'pub const SEARCH_POLICY_SCHEMA_VERSION: u16 = 1;' "$policy"
require_literal 'pub const V0_1_SEARCH_POLICY_ID: u64 = 0x5630_315f_504f_4c31;' "$policy"
require_literal 'pub const V0_1_SEARCH_POLICY_CHECKSUM: u64 = 0x0c07_69ef_9d03_4770;' "$policy"
require_literal 'pub const EVALUATION_WEIGHT_SCHEMA_VERSION: u16 = 1;' "$weights"
require_literal 'pub const ENGINE_VARIANT_SCHEMA_VERSION: u16 = 1;' "$variant"
require_literal 'pub const ENGINE_VARIANT_VALIDATION_SCHEMA_VERSION: u16 = 1;' "$validation"
require_literal 'pub const ENGINE_VARIANT_VALIDATION_IDENTIFIER: u64 = 0x5641_5249_5641_4c31;' "$validation"
require_literal 'pub const CANDIDATE_VALIDATION_SCHEMA_VERSION: u16 = 1;' "$legacy"
require_literal 'pub const CANDIDATE_VALIDATION_IDENTIFIER: u64 = 0x4341_4e44_5641_4c31;' "$legacy"
require_literal 'pub const fn activated(&self) -> bool {' "$validation"
require_literal 'engine-variant validation reports must remain inactive' "$validation"
require_literal 'version = "0.1.0"' Cargo.toml

# No candidate is accepted for public configuration in S2-13. The exact v0.1
# production surface therefore remains authoritative and unsupported options
# remain absent rather than being accepted and silently ignored.
for path in crates/chess-uci crates/chess-ffi crates/chess-jni; do
  if grep -R --line-number --include='*.rs' 'SearchPolicy' "$path"; then
    fail "experimental SearchPolicy escaped through $path"
  fi
done
for name in PVS LMR NullMove Futility Razoring LateMovePruning Syzygy Tablebase; do
  if grep -R --line-number --ignore-case "$name" crates/chess-uci; then
    fail "unsupported experimental UCI option or behavior is advertised: $name"
  fi
done
require_literal 'option name Hash type spin default 1 min 1 max 65536' crates/chess-uci/tests/uci_process.rs
require_literal 'option name CheckExtension type check default false' crates/chess-uci/tests/uci_process.rs
require_literal 'option name OwnBook type check default false' crates/chess-uci/tests/uci_process.rs
require_literal 'stop_interrupts_infinite_search_and_session_remains_ready' crates/chess-uci/tests/uci_process.rs
require_literal 'quit_interrupts_active_search_without_stale_bestmove' crates/chess-uci/tests/uci_process.rs

# Stable additive adapter boundary: no ABI/JNI/Kotlin policy record was required.
require_literal '#define CHESS_ENGINE_ABI_VERSION UINT32_C(1)' crates/chess-ffi/include/chess_engine.h
require_literal 'pub const CHESS_ENGINE_ABI_VERSION: u32 = 1;' crates/chess-ffi/src/c_abi/types.rs
require_literal 'ChessEngineHandle' crates/chess-ffi/include/chess_engine.h
require_literal 'ChessEngineCancellationHandle' crates/chess-ffi/include/chess_engine.h
require_literal 'CHESS_ENGINE_RESULT_PANIC = 101' crates/chess-ffi/include/chess_engine.h
require_literal 'all-or-nothing validation' crates/chess-ffi/tests/c_abi_lifecycle.rs
require_literal 'Java_com_ekkus93_chessengine_NativeChessEngineBindings_nativeSearch' crates/chess-jni/src/lib.rs
require_literal 'boundary(&mut env' crates/chess-jni/src/lib.rs
require_file android-harness/host-jvm/src/test/kotlin/com/ekkus93/chessengine/ChessEngineHostJvmTest.kt
require_file android-harness/android-smoke/src/androidTest/kotlin/com/ekkus93/chessengine/harness/ChessEngineInstrumentedTest.kt
require_literal 'sampleMainThreadEntryRunsTheNativeCallOnTheWorker' android-harness/android-smoke/src/androidTest/kotlin/com/ekkus93/chessengine/harness/ChessEngineInstrumentedTest.kt
require_literal 'repeatedCreateSearchStopDestroyIsStableOnAndroid' android-harness/android-smoke/src/androidTest/kotlin/com/ekkus93/chessengine/harness/ChessEngineInstrumentedTest.kt
require_literal 'cancellationElapsedNanos' android-harness/android-smoke/src/androidTest/kotlin/com/ekkus93/chessengine/harness/ChessEngineInstrumentedTest.kt

# Internal control/report tooling is explicit, versioned, checksummed, and
# incapable of changing defaults.
require_literal 'S2_13_SOURCE_SHA' "$control"
require_literal 'S2_13_BUILD_IDENTITY' "$control"
require_literal 'S2_13_EXACT_INVOCATION' "$control"
require_literal 'OptionalCapabilityIdentity::Disabled' "$control"
require_literal 'EngineVariantValidationTier::Production' "$control"
require_literal 'EngineVariantResourceProtocol::ClockMilliseconds' "$control"
require_literal 'write_engine_variant_validation_report_atomic' "$control"
require_literal 'EngineVariantValidationReport::deserialize' "$control"
require_literal 'activated\tfalse' "$control"
require_literal 'variant-report-validate' crates/chess-tools/src/main.rs

# Read-only bounded control workflow with exact source/artifact identity.
require_literal 'name: Variant validation' "$workflow"
require_literal 'contents: read' "$workflow"
require_literal 'tier=development' "$workflow"
require_literal 'tier=production' "$workflow"
require_literal 'protocol=clock_ms' "$workflow"
require_literal 'S2_13_SOURCE_SHA: ${{ github.sha }}' "$workflow"
require_literal 'git diff --exit-code' "$workflow"
require_literal 'variant-validation-control-${{ steps.configuration.outputs.tier }}-${{ steps.configuration.outputs.protocol }}-${{ matrix.architecture }}-${{ github.sha }}' "$workflow"
if grep -Eq 'contents: write|git push|git commit|update-ref|checkout.*token:' "$workflow"; then
  fail 'variant-validation workflow can edit source or repository refs'
fi

# Every permanent workflow remains unable to modify repository contents. The
# reporting bridge may write issue comments, but never contents.
while IFS= read -r path; do
  if grep -Eq '^  contents: write$|git push|git commit' "$path"; then
    fail "permanent workflow can modify source: $path"
  fi
done < <(find .github/workflows -maxdepth 1 -type f -name '*.yml' -print | sort)

# CI must execute this exact audit, and all independent architecture/platform
# gates remain present.
require_literal 'bash scripts/task_v0_2_strength_audit.sh' .github/workflows/ci.yml
for path in \
  .github/workflows/ci.yml \
  .github/workflows/android.yml \
  .github/workflows/robustness.yml \
  .github/workflows/performance.yml \
  .github/workflows/slow-perft.yml \
  .github/workflows/strength.yml \
  .github/workflows/variant-validation.yml; do
  require_file "$path"
done
require_literal 'Variant validation' .github/workflows/report-master-validation.yml
require_literal '/variant-evidence-*/' .gitignore

# No staging helper or hidden runtime-language fallback may survive. Python is
# permitted only in explicit offline validation/oracle tooling, never engine,
# search, UCI, FFI, JNI, book, or Android runtime sources.
temporary_paths=(
  .github/workflows/s2-13-source-snapshot.yml
  .github/workflows/s2-13-closure.yml
  .github/workflows/strength-integration-apply.yml
  .github/s2_13_close.py
  .github/s2_13_payload.py
  .github/s2_13_payload_00
  .github/s2_13_payload_01
  .github/s2_13_payload_02
  .github/s2_13_payload_03
  .github/s2_14_close_once.py
  .github/workflows/s2-14-close-once.yml
)
for path in "${temporary_paths[@]}"; do
  test ! -e "$path" || fail "temporary S2-13 asset remains: $path"
done
if find crates -type f -name '*.py' -print | grep -q .; then
  fail 'Python source exists inside the Rust production/tool crate tree'
fi
if grep -R --line-number --include='*.rs' -E 'Command::new\("python|python3|Py_Initialize|pyo3' \
  crates/chess-core crates/chess-search crates/chess-book crates/chess-uci crates/chess-ffi crates/chess-jni; then
  fail 'production runtime contains a hidden Python/subprocess fallback'
fi

require_literal '**Status:** Complete' "$report"
require_literal '**Activation:** `false`' "$report"
require_literal '**Public adapter change:** none' "$report"
require_literal '**Next task:** S2-14' "$report"

echo 'v0.2 strength integration audit passed'
