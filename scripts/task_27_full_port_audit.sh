#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

fail() {
  printf 'task27-audit: %s\n' "$1" >&2
  exit 1
}

required_files=(
  Cargo.toml
  Cargo.lock
  README.md
  docs/RUST_CHESS_ENGINE_PORT_SPEC_2026-08-01.md
  docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md
  docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md
  docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md
  docs/RUST_CHESS_ENGINE_V0_1_IMPLEMENTATION_REPORT.md
  docs/RUST_CHESS_ENGINE_PORT_IMPLEMENTATION_REPORT.md
  docs/RUST_WORKSPACE_ARCHITECTURE.md
  docs/RUST_UCI_PROCESS_INTEGRATION.md
  docs/RUST_SAFE_ENGINE_FACADE.md
  docs/RUST_ANDROID_JNI.md
  docs/RUST_SELF_PLAY_DATASET.md
  docs/RUST_TUNING_WORKFLOW.md
  docs/RUST_CANDIDATE_VALIDATION.md
  docs/RUST_ADVANCED_EVALUATION_PROTOCOL.md
  docs/RUST_ROBUSTNESS_GATES.md
  docs/RUST_PERFORMANCE_GATES.md
  docs/RUST_DEVELOPER_WORKFLOWS.md
  docs/RUST_GENERATED_ARTIFACT_POLICY.md
  crates/chess-core/src/lib.rs
  crates/chess-search/src/lib.rs
  crates/chess-book/src/lib.rs
  crates/chess-book/tests/task_19_5.rs
  crates/chess-uci/src/main.rs
  crates/chess-ffi/src/lib.rs
  crates/chess-ffi/tests/c_abi_lifecycle.rs
  crates/chess-jni/src/lib.rs
  crates/chess-jni/tests/jni_contract.rs
  crates/chess-tools/src/main.rs
  crates/chess-tune/src/lib.rs
  scripts/task_26_v0_1_audit.sh
  scripts/task_25_artifact_audit.py
  scripts/task_24_performance_audit.py
  scripts/task_14_5_exclusion_audit.py
)

for path in "${required_files[@]}"; do
  [[ -f "${path}" ]] || fail "missing required final-port witness: ${path}"
done

for temporary in \
  .github/task21-candidate-discovery-harness.rs \
  .github/workflows/task21-candidate-discovery.yml \
  .github/workflows/task27-tracker-closure.yml \
  .github/workflows/task27-tracker-closure-retry.yml; do
  [[ ! -e "${temporary}" ]] || fail "temporary signoff helper remains tracked: ${temporary}"
done

report=docs/RUST_CHESS_ENGINE_PORT_IMPLEMENTATION_REPORT.md
required_report_markers=(
  '# Rust Chess Engine Port Implementation Report'
  '## Executive conclusion'
  '## Evidence boundary'
  '## Final architecture and versions'
  '## Specification traceability'
  '## TODO traceability'
  '## Optional-capability audit'
  '## Python migration decision'
  '## Retained, redesigned, and rejected Python concepts'
  '## Exact functional evidence inherited from Task 26'
  '## Authoritative perft'
  '## Performance baselines'
  '## Known limitations and future roadmap'
  '## Final release gate'
  'Rust is the authoritative implementation'
  'Python is reference-only'
  'rejected_strength'
  'activated=false'
  '30962735433'
  '30962735439'
  '30962735450'
  '30962735451'
  '377 passed'
  '4 ignored'
  '0 failed'
  '272,991 oracle perft nodes'
)

for marker in "${required_report_markers[@]}"; do
  grep -Fq -- "${marker}" "${report}" \
    || fail "final implementation report is missing marker: ${marker}"
done

for section in $(seq 1 37); do
  grep -Eq "^\| ${section} \|" "${report}" \
    || fail "specification traceability is missing section ${section}"
done

grep -Fq 'A correctness-first Rust chess engine' README.md \
  || fail 'README no longer identifies the Rust engine'
grep -Fq 'former Python implementation remains' README.md \
  || fail 'README no longer records the reference-only Python migration'
grep -Fq 'docs/RUST_CHESS_ENGINE_PORT_IMPLEMENTATION_REPORT.md' README.md \
  || fail 'README does not link the final implementation report'

grep -Fq 'version = "0.1.0"' Cargo.toml \
  || fail 'workspace version is not recorded as 0.1.0'
grep -Fq 'rust-version = "1.91"' Cargo.toml \
  || fail 'workspace minimum Rust version is not recorded as 1.91'

grep -Fq 'pub const SELF_PLAY_CONFIG_SCHEMA_VERSION: u16 = 1;' crates/chess-tools/src/self_play.rs \
  || fail 'self-play configuration schema changed'
grep -Fq 'pub const SELF_PLAY_OPENING_SCHEMA_VERSION: u16 = 1;' crates/chess-tools/src/self_play.rs \
  || fail 'self-play opening schema changed'
grep -Fq 'pub const SELF_PLAY_DATASET_SCHEMA_VERSION: u16 = 1;' crates/chess-tools/src/self_play.rs \
  || fail 'self-play dataset schema changed'
grep -Fq 'pub const EVALUATION_WEIGHT_SCHEMA_VERSION: u16 = 1;' crates/chess-search/src/weights.rs \
  || fail 'evaluation weight schema changed'
grep -Fq 'pub const EVALUATION_STRUCTURE_SCHEMA_VERSION: u16 = 1;' crates/chess-search/src/weights.rs \
  || fail 'evaluation structure schema changed'

grep -Fq 'MINIMUM_VALIDATION_PAIRS: u32 = 200' crates/chess-tools/src/candidate_validation.rs \
  || fail 'production candidate-validation sample size changed'
grep -Fq 'lower_bound > 0.5 + config.minimum_score_margin' crates/chess-tools/src/candidate_validation.rs \
  || fail 'candidate strength acceptance rule changed'
grep -Fq 'pub const fn activated(&self) -> bool' crates/chess-tools/src/candidate_validation.rs \
  || fail 'candidate activation boundary is missing'

if grep -RInE --include='*.rs' \
  '(pyo3|PyO3|Python\.h|std::process::Command|Command::new\([^)]*python)' \
  crates/chess-core/src crates/chess-search/src crates/chess-book/src crates/chess-ffi/src; then
  fail 'production engine crates must not embed or launch Python'
fi

bash scripts/task_26_v0_1_audit.sh
python3 scripts/task_25_artifact_audit.py
python3 scripts/task_24_performance_audit.py
python3 scripts/task_14_5_exclusion_audit.py

if awk '
  /^# Task 27: Full port-program signoff$/ { in_task = 1; next }
  in_task && /^\*\*Task 27 gate:.*\*\*COMPLETE\.\*\*$/ { found = 1 }
  in_task && /^---$/ { exit }
  END { exit(found ? 0 : 1) }
' docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md; then
  grep -Fq '**Status:** Task 27 full port-program signoff complete' "${report}" \
    || fail 'Task 27 tracker is complete but the final report is not'
  ! grep -Fq 'PENDING_EXACT_SHA' "${report}" \
    || fail 'Task 27 tracker is complete but the report still has a pending SHA'
  grep -Fq '# Task 27: Full port-program signoff — COMPLETE' docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md \
    || fail 'detailed Task 27 completion is not mirrored in the live tracker'
fi

printf '%s\n' \
  'task27-audit: architecture, specification/TODO traceability, migration, schemas, activation boundary, inherited evidence, and permanent audits passed'
