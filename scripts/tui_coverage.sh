#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$repo_root"

require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "tui-coverage: required command not found: $1" >&2
    exit 1
  }
}

require_llvm_cov() {
  require_command cargo
  if ! cargo llvm-cov --version >/dev/null 2>&1; then
    echo "tui-coverage: cargo-llvm-cov is required; install the pinned CI version or another compatible local release" >&2
    exit 1
  fi
}

usage() {
  cat <<'EOF'
usage: bash scripts/tui_coverage.sh COMMAND

Commands:
  clean    Remove stale cargo-llvm-cov workspace artifacts.
  summary  Run all chess-tui tests and print the focused coverage summary.
  json     Run all chess-tui tests and write target/chess-tui-coverage-summary.json.
  lcov     Run all chess-tui tests and write target/chess-tui-lcov.info.
  html     Run all chess-tui tests and write HTML under target/llvm-cov/html/.

Coverage is diagnostic evidence. These commands do not enforce a percentage threshold.
EOF
}

command="${1:-}"
[[ $# -eq 1 ]] || {
  usage
  exit 2
}

require_llvm_cov

case "$command" in
  clean)
    cargo llvm-cov clean --workspace
    ;;
  summary)
    cargo llvm-cov --locked -p chess-tui --all-features
    ;;
  json)
    cargo llvm-cov --locked -p chess-tui --all-features \
      --json --summary-only \
      --output-path target/chess-tui-coverage-summary.json
    ;;
  lcov)
    cargo llvm-cov --locked -p chess-tui --all-features \
      --lcov --output-path target/chess-tui-lcov.info
    ;;
  html)
    cargo llvm-cov --locked -p chess-tui --all-features --html
    ;;
  *)
    usage
    exit 2
    ;;
esac
