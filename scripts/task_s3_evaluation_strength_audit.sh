#!/usr/bin/env bash
set -euo pipefail

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$root"

fail() {
  echo "s3-evaluation-strength-audit: $*" >&2
  exit 1
}

require_file() {
  test -f "$1" || fail "missing required file: $1"
}

require_literal() {
  grep -Fq "$1" "$2" || fail "missing witness in $2: $1"
}

spec=docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_SPEC_2026-08-07.md
tracker=docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_TODO_2026-08-07.md
baseline=docs/RUST_CHESS_ENGINE_S3_BASELINE_2026-08-07.md
pipeline=docs/RUST_CHESS_ENGINE_S3_PIPELINE.md
pilot=docs/RUST_CHESS_ENGINE_S3_PILOT_EVALUATION_2026-08-07.md
final_report=docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_IMPLEMENTATION_REPORT.md
legacy=docs/LEGACY_TODO_INDEX.md
editor=crates/chess-core/src/position/editor.rs
position_mod=crates/chess-core/src/position/mod.rs
core_lib=crates/chess-core/src/lib.rs
uci_tests=crates/chess-uci/tests/uci_process.rs
mask=crates/chess-tune/src/mask.rs
optimizer=crates/chess-tune/src/optimizer.rs
s3_tools=crates/chess-tools/src/s3.rs
s3_cli=crates/chess-tools/src/s3_cli.rs
tuning_cli=crates/chess-tools/src/tuning_cli.rs
tuning_report=crates/chess-tools/src/tuning/report.rs
tools_main=crates/chess-tools/src/main.rs

for path in "$spec" "$tracker" "$baseline" "$pipeline" "$pilot" "$final_report" "$legacy" "$editor" "$position_mod" "$core_lib" "$uci_tests" "$mask" "$optimizer" "$s3_tools" "$s3_cli" "$tuning_cli" "$tuning_report" "$tools_main"; do
  require_file "$path"
done

# Preserve the entire signed-off v0.1 and S2 closure foundation.
bash scripts/task_v0_2_strength_audit.sh

# Closed-program authority and no-promotion disposition.
require_literal '`docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_TODO_2026-08-07.md`' "$legacy"
require_literal 'Active S4 evaluation tuning calibration program' "$legacy"
require_literal '`docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_TODO_2026-08-07.md`' "$legacy"
if grep -Fq '| Active S3 evaluation strength program |' "$legacy"; then
  fail 'closed S3 tracker is still classified as active'
fi
require_literal '**Status:** Complete — program closed without promotion' "$tracker"
require_literal '# Task S3-7: Development strength validation — SKIPPED (NO ADVANCING CANDIDATE)' "$tracker"
require_literal '# Task S3-8: Optional new evaluation feature candidates — DEFERRED' "$tracker"
require_literal '# Task S3-9: Combined evaluation candidate — COMPLETE (NO COMBINATION FORMED)' "$tracker"
require_literal '# Task S3-10: Production candidate validation — SKIPPED (NO ELIGIBLE CANDIDATE)' "$tracker"
require_literal '# Task S3-11: Separate activation and release gate — SKIPPED (NO ACCEPTED CANDIDATE)' "$tracker"
require_literal '# Task S3-12: Final report, audit, cleanup, and closure — COMPLETE (NO PROMOTION)' "$tracker"
require_literal '**Status:** Complete — program closed without promotion' "$final_report"
require_literal '**Program outcome:** Completed without promotion; no S3 candidate reached development or production strength validation' "$final_report"
require_literal 'package/UCI version: `0.1.0`' "$final_report"
require_literal 'No S3-10 candidate exists' "$final_report"
require_literal 'No rejected S3 artifact authorizes promotion.' "$final_report"

# Frozen baseline identity.
require_literal '**S3 planning/authority SHA:** `90a015c2cf8b8d45edcd07d705fb6ca58fe336f7`' "$baseline"
require_literal '**Unchanged production/code baseline SHA:** `677cd2a4d2a4f3c376f7bf47fae412171206fb`' "$baseline"
require_literal 'Package/UCI version: `0.1.0`' "$baseline"
require_literal 'Runtime weight-vector length: `816`; named tunable-parameter count: `810`.' "$baseline"
require_literal 'experimental_features=0000000000000000' "$baseline"
require_literal 'Tablebases/Syzygy are disabled' "$baseline"

# PositionEditor must be private to chess-core and explicitly hash-neutral.
if grep -Eq '^[[:space:]]*pub[[:space:]]+use[[:space:]].*PositionEditor' "$position_mod" "$core_lib"; then
  fail 'PositionEditor is publicly re-exported'
fi
require_literal 'use editor::PositionEditor;' "$position_mod"
require_literal 'does **not** update the' "$editor"
require_literal 'editor_mutation_is_hash_neutral_until_the_caller_updates_hash_state' "$editor"
require_literal 'PositionEditor` is intentionally an internal board-representation capability' docs/RUST_MAKE_UNMAKE.md

# No rejected S2 or S3 experimental selector may escape through production adapters.
for path in crates/chess-uci/src crates/chess-ffi/src crates/chess-jni/src crates/chess-jni/kotlin/src/main android-harness; do
  if grep -R --line-number --include='*.rs' --include='*.kt' 'SearchPolicy' "$path"; then
    fail "experimental SearchPolicy escaped through $path"
  fi
done
for token in PrincipalVariationSearch LateMoveReductions NullMovePruning FutilityPruning Razoring LateMovePruning SeeCaptureOrdering SeeQuiescencePruning DeltaPruning Syzygy Tablebase; do
  for path in crates/chess-uci/src crates/chess-ffi/src crates/chess-jni/src crates/chess-jni/kotlin/src/main android-harness; do
    if grep -R --line-number --include='*.rs' --include='*.kt' "$token" "$path"; then
      fail "experimental capability $token escaped through $path"
    fi
  done
done

# UCI stale-worker regressions remain permanent.
require_literal 'fn position_replacement_discards_active_search_without_stale_bestmove()' "$uci_tests"
require_literal 'fn ucinewgame_discards_active_search_without_stale_bestmove()' "$uci_tests"
require_literal 'fn repeated_stop_and_restart_cycles_emit_exactly_one_bestmove_per_search()' "$uci_tests"
require_literal 'fn quit_interrupts_active_search_without_stale_bestmove()' "$uci_tests"
require_literal 'fn stop_interrupts_infinite_search_and_session_remains_ready()' "$uci_tests"

# S3 dataset provenance is a strict sidecar, not a silent Task-20 schema mutation.
require_literal 'pub const S3_DATASET_MANIFEST_SCHEMA_VERSION: u16 = 1;' "$s3_tools"
require_literal 'pub const S3_DATASET_MANIFEST_IDENTIFIER: u64 = 0x5333_4441_5441_3031;' "$s3_tools"
require_literal 'pub const S3_MINIMUM_TUNING_GAMES: u32 = 16;' "$s3_tools"
require_literal 'pub const S3_MINIMUM_COMPLETED_GAMES: u32 = 12;' "$s3_tools"
require_literal 'pub const S3_MAXIMUM_UNFINISHED_PER_MILLE: u32 = 250;' "$s3_tools"
require_literal 'pub const S3_MINIMUM_TRAINING_OCCURRENCES: u64 = 128;' "$s3_tools"
require_literal 'pub const S3_MINIMUM_VALIDATION_OCCURRENCES: u64 = 16;' "$s3_tools"
require_literal 'pub struct S3DatasetManifest' "$s3_tools"
require_literal 'exact_invocation: String,' "$s3_tools"
require_literal 'total_position_rows: u64,' "$s3_tools"
require_literal 'eligible_position_rows: u64,' "$s3_tools"
require_literal 'excluded_position_rows: u64,' "$s3_tools"
require_literal 'writeln!(output, "exact_invocation={}", self.exact_invocation)' "$s3_tools"
require_literal 'writeln!(output, "total_position_rows={}", self.total_position_rows)' "$s3_tools"
require_literal 'const KEYS: [&str; 25]' "$s3_tools"
require_literal 'pub fn validate_dataset(' "$s3_tools"
require_literal 'dataset: &SelfPlayDataset,' "$s3_tools"
require_literal 'pub fn validate_for_tuning(&self) -> Result<(), S3DatasetAdmissionError>' "$s3_tools"
require_literal 'fn manifest_round_trip_binds_exact_dataset_and_source()' "$s3_tools"
require_literal 'fn manifest_checksum_and_dataset_binding_fail_closed()' "$s3_tools"
require_literal 'fn exact_invocation_is_provenance_and_changes_manifest_checksum()' "$s3_tools"
require_literal 'the strict Task 20 dataset image' "$pipeline"
require_literal 'a strict `CHESS_S3_TRAINING_DATASET_MANIFEST` sidecar' "$pipeline"
require_literal 'no Git, environment, filesystem, or process discovery is used by the library contract' "$pipeline"

# Group tuning stays mask-bound and inactive.
require_literal 'pub struct TunableParameterMask' "$mask"
require_literal 'pub enum EvaluationParameterGroup' "$mask"
require_literal 'Self::MaterialAndPieceSquare => "material_and_piece_square"' "$mask"
require_literal 'Self::MobilityAndActivity => "mobility_and_activity"' "$mask"
require_literal 'Self::PawnStructure => "pawn_structure"' "$mask"
require_literal 'Self::KingSafetyAndSpace => "king_safety_and_space"' "$mask"
require_literal 'Self::EndgameKingActivity => "endgame_king_activity"' "$mask"
require_literal 'Self::FullExistingEvaluator => "full_existing_evaluator"' "$mask"
require_literal 'let expected = [778, 16, 8, 6, 2, 810];' "$mask"
require_literal 'pub fn with_parameter_mask(' "$optimizer"
require_literal 'if !self.parameter_mask.is_all() {' "$optimizer"
require_literal 'b"spsa-parameter-mask-v1"' "$optimizer"
require_literal 'if direction == 0 {' "$optimizer"
require_literal 'fn masked_optimizer_never_changes_inactive_parameters()' "$optimizer"
require_literal 'fn mask_identity_binds_checkpoint_configuration()' "$optimizer"
require_literal 'fn masked_optimizer_report_uses_the_same_regularization_domain()' "$tuning_report"
require_literal 'Regularization is normalized over the selected parameter count' "$pipeline"
require_literal 'validation MSE separately after bounded work' "$pipeline"

# Reproducible S3 command surface remains tooling-only and inactive.
require_literal 'pub(crate) fn run_s3_self_play(arguments: &[String])' "$s3_cli"
require_literal 'pub(crate) fn run_s3_self_play_validate(arguments: &[String])' "$s3_cli"
require_literal 'ACTIVATION_DISABLED' "$s3_cli"
require_literal 'std::env::args().collect::<Vec<_>>().join(" ")' "$s3_cli"
require_literal 'fs::rename(&staging, output_dir)' "$s3_cli"
require_literal 'pub(crate) fn run_group_tuning_command(arguments: &[String])' "$tuning_cli"
require_literal '.validate_for_tuning()' "$tuning_cli"
require_literal 'S3 dataset source commit differs from tuning config source_commit' "$tuning_cli"
require_literal 'resume requires the exact previous S3 tuning group' "$tuning_cli"
require_literal 'resume requires the exact previous S3 dataset manifest' "$tuning_cli"
require_literal 's3-summary.tsv' "$tuning_cli"
require_literal '"s3-self-play" =>' "$tools_main"
require_literal '"s3-self-play-validate" =>' "$tools_main"
require_literal '"tune-group" =>' "$tools_main"
require_literal 'chess-tools s3-self-play SOURCE_SHA CONFIG_PATH OUTPUT_DIR' "$pipeline"
require_literal 'chess-tools tune-group GROUP CONFIG_PATH S3_DATASET_DIR OUTPUT_DIR [PREVIOUS_OUTPUT_DIR]' "$pipeline"

# Exact pilot evidence is a rejection, not strength acceptance.
require_literal '**Status:** Complete — no pilot candidate advances' "$pilot"
require_literal '**Successful run/job:** `31184450979` / `92885406054`' "$pilot"
require_literal '**Artifact:** `8996149049`' "$pilot"
require_literal 'dataset checksum: `c691d1928ffda61b`' "$pilot"
require_literal 'S3 manifest checksum: `6aef02a9b375c5a3`' "$pilot"
require_literal 'training delta: `0.0`' "$pilot"
require_literal 'validation delta: `0.0`' "$pilot"
require_literal '689d960bd3a2751604165861116a0bc3d10afa4aea32bbbb82e808a59c777066' "$pilot"
require_literal 'No pilot candidate is eligible for S3 development or production strength matches.' "$pilot"

# Release identities remain v0.1.
require_literal 'version = "0.1.0"' Cargo.toml
require_literal 'pub const V0_1_SEARCH_POLICY_ID: u64 = 0x5630_315f_504f_4c31;' crates/chess-search/src/search_policy.rs
require_literal 'pub const BASELINE_WEIGHT_SET_ID: u64 = 0x4241_5345_4c49_4e45;' crates/chess-search/src/weights.rs
require_literal 'pub const WEIGHT_VALUE_COUNT: usize = 816;' crates/chess-search/src/weights.rs
require_literal 'pub const TUNABLE_PARAMETER_COUNT: usize = 810;' crates/chess-tune/src/lib.rs

# Temporary write-capable staging controls must be absent at closure.
for temporary in \
  .github/s3_phase1.py \
  .github/workflows/s3-phase1-stage.yml \
  .github/s3_phase2.py \
  .github/s3_phase2_fix.py \
  .github/workflows/s3-phase2-stage.yml \
  .github/s3_phase3.py \
  .github/s3_phase3_fix.py \
  .github/workflows/s3-phase3-stage.yml \
  .github/s3_candidate_stage.py \
  .github/workflows/s3-candidate-stage.yml \
  .github/s3_closure_docs.py \
  .github/workflows/s3-closure-docs-stage.yml; do
  if test -e "$temporary"; then
    fail "temporary S3 staging control remains: $temporary"
  fi
done

# Permanent experiment workflows are allowed only as read-only evidence producers.
for workflow in .github/workflows/s3-evaluation-experiment.yml .github/workflows/s3-full-tuning-reviewed.yml .github/workflows/s3-evaluation-strength.yml; do
  require_file "$workflow"
  if grep -Fq 'contents: write' "$workflow"; then
    fail "permanent S3 workflow is write-capable: $workflow"
  fi
done

# No production Python/subprocess fallback may appear.
if grep -R --line-number --include='*.rs' -E 'Command::new\("python(3)?"|Py_Initialize|pyo3' crates; then
  fail 'production Rust gained a Python/subprocess fallback'
fi

echo 'S3 evaluation-strength closure audit passed'
