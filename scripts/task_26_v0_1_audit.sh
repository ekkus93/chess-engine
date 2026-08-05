#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

fail() {
  printf 'task26-audit: %s\n' "$1" >&2
  exit 1
}

required_files=(
  Cargo.toml
  Cargo.lock
  fixtures/perft.tsv
  fixtures/differential_corpus.tsv
  requirements/oracle.txt
  docs/RUST_CHESS_ENGINE_PORT_SPEC_2026-08-01.md
  docs/RUST_CHESS_ENGINE_V0_1_IMPLEMENTATION_REPORT.md
  crates/chess-core/tests/authoritative_perft.rs
  crates/chess-core/tests/property_invariants.rs
  crates/chess-search/tests/property_search.rs
  crates/chess-uci/tests/uci_process.rs
  crates/chess-ffi/tests/c_abi_lifecycle.rs
  crates/chess-jni/tests/jni_contract.rs
  scripts/differential_oracle.py
  scripts/task_14_5_exclusion_audit.py
  scripts/task_24_performance_audit.py
)

for path in "${required_files[@]}"; do
  [[ -f "${path}" ]] || fail "missing required witness: ${path}"
done

report=docs/RUST_CHESS_ENGINE_V0_1_IMPLEMENTATION_REPORT.md
required_report_markers=(
  '# Rust Chess Engine v0.1 Implementation Report'
  '## Evidence identity'
  '## Exact validation commands and outputs'
  '## Rules signoff'
  '## Search signoff'
  '## Adapter signoff'
  '## Quality signoff'
  '## Authoritative perft table'
  '## Differential-validation statistics'
  '## Benchmark environment and results'
  '## UCI transcript'
  '## C ABI and Android JNI evidence'
  '## Known limitations and deferred features'
  '## Signoff conclusion'
  '332967613098f30348489a73249e822c9eb70bc3'
  '377 passed; 4 ignored; 0 failed'
  '15 corpus positions'
  '272,991 oracle perft nodes'
  '576 seeded plies'
  'Task 21'
)

for marker in "${required_report_markers[@]}"; do
  grep -Fq -- "${marker}" "${report}" || fail "implementation report is missing marker: ${marker}"
done

[[ "$(wc -l < fixtures/perft.tsv)" -eq 7 ]] || fail 'authoritative perft fixture must contain one header and six positions'
head -n 1 fixtures/perft.tsv | grep -Fqx $'name\tfen\td1\td2\td3\td4\td5' \
  || fail 'authoritative perft fixture header changed'

grep -Fq 'handshake_transcript_is_exact_and_quit_exits_cleanly' crates/chess-uci/tests/uci_process.rs \
  || fail 'exact UCI handshake witness is missing'
grep -Fq 'start_position_and_fen_searches_return_legal_fixed_depth_moves' crates/chess-uci/tests/uci_process.rs \
  || fail 'playable UCI search witness is missing'
grep -Fq 'active_infinite_search_cancels_from_another_thread' crates/chess-ffi/tests/c_abi_lifecycle.rs \
  || fail 'C ABI active-cancellation witness is missing'
grep -Fq 'kotlin_native_declarations_match_exact_rust_export_names' crates/chess-jni/tests/jni_contract.rs \
  || fail 'JNI export/declaration witness is missing'

if grep -RInE --include='*.rs' \
  '(pyo3|PyO3|Python\.h|std::process::Command|Command::new\([^)]*python)' \
  crates/chess-core/src crates/chess-search/src crates/chess-book/src crates/chess-ffi/src; then
  fail 'production engine crates must not depend on or launch a Python runtime'
fi

python3 scripts/task_14_5_exclusion_audit.py
python3 scripts/task_24_performance_audit.py

printf '%s\n' \
  'task26-audit: report completeness, permanent witnesses, Python-runtime exclusion, and search architecture passed'
