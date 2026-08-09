#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT}"

usage() {
  cat <<'EOF'
usage: bash scripts/dev.sh COMMAND [ARGUMENTS]

Commands:
  bootstrap                         Install/check pinned developer prerequisites.
  fast                              Run the standard fast Rust validation gate.
  full                              Run the complete local Rust validation gate.
  perft [DEPTH]                     Run the authoritative perft suite (default: 4).
  uci [--book PATH]                 Run the Linux UCI engine on stdin/stdout.
  tui                               Run the native Rust terminal interface.
  tui-coverage COMMAND              Run focused Rust TUI llvm-cov coverage.
  tui-pty-smoke                     Run additional chess-tui PTY regression coverage.
  android                           Build JNI libraries and the Android harness.
  self-play CONFIG OUTPUT           Generate one versioned offline dataset.
  tune CONFIG DATASET OUTPUT [CKPT] Run/resume offline SPSA; candidate stays inactive.
  fuzz-smoke                        Run stable fuzz entrypoint and corpus regressions.
  strength-audit                    Run the consolidated v0.2 authority audit.
  variant-control OUT TIER PROTOCOL Run one inactive complete-variant control.
  artifact-audit                    Audit tracked filenames and generated artifacts.
EOF
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "developer-workflow: required command not found: $1" >&2
    exit 1
  }
}

bootstrap() {
  require_command rustup
  require_command cargo
  require_command python3
  rustup component add rustfmt clippy
  rustup target add aarch64-unknown-linux-gnu aarch64-linux-android x86_64-linux-android
  cargo fetch --locked
  if [[ ! -x .venv-oracle/bin/python ]]; then
    python3 -m venv .venv-oracle
  fi
  .venv-oracle/bin/python -m pip install --disable-pip-version-check --upgrade pip
  .venv-oracle/bin/python -m pip install --disable-pip-version-check --requirement requirements/oracle.txt
  echo "developer-workflow: bootstrap complete"
}

artifact_audit() {
  require_command python3
  python3 scripts/task_25_artifact_audit.py
  python3 -m unittest discover -s scripts/tests -p 'test_*.py'
  bash -n scripts/dev.sh scripts/build_android_jni.sh scripts/prepare_android_harness_jni.sh
}

strength_audit() {
  bash scripts/task_v0_2_strength_audit.sh
}

variant_control() {
  local output="$1"
  local tier="$2"
  local protocol="$3"
  require_command cargo
  require_command git
  require_command rustc
  if [[ -e "$output" ]]; then
    echo "developer-workflow: output already exists: $output" >&2
    exit 1
  fi
  if [[ -n "$(git status --porcelain --untracked-files=all)" ]]; then
    echo 'developer-workflow: variant control requires a clean committed checkout' >&2
    exit 1
  fi
  export S2_13_SOURCE_SHA="$(git rev-parse HEAD)"
  export S2_13_BUILD_IDENTITY="local;$(rustc -vV | tr '\n' ';')"
  export S2_13_EXACT_INVOCATION="bash scripts/dev.sh variant-control $output $tier $protocol"
  cargo run --locked --release -p chess-tools --bin s2_13_variant_control -- \
    "$output" "$tier" "$protocol"
  local report
  report="$(find "$output" -maxdepth 1 -type f -name '*.report' -print)"
  [[ -n "$report" && "$(printf '%s\n' "$report" | wc -l)" -eq 1 ]] || {
    echo 'developer-workflow: expected exactly one complete-variant report' >&2
    exit 1
  }
  cargo run --locked --release -p chess-tools -- variant-report-validate "$report"
}

fast() {
  require_command cargo
  artifact_audit
  strength_audit
  cargo fmt --all -- --check
  cargo check --locked --workspace --all-targets --all-features
  cargo clippy --locked --workspace --all-targets --all-features -- -D warnings
  cargo test --locked --workspace --all-features
}

full() {
  fast
  cargo test --locked -p chess-core --release authoritative_perft_depth_four -- --ignored --exact
  RUSTDOCFLAGS='-D warnings' cargo doc --locked --workspace --all-features --no-deps
  cargo build --locked --workspace --all-features
  cargo build --locked --workspace --all-features --release
  if [[ ! -x .venv-oracle/bin/python ]]; then
    echo "developer-workflow: run 'bash scripts/dev.sh bootstrap' before full validation" >&2
    exit 1
  fi
  .venv-oracle/bin/python scripts/differential_oracle.py \
    --binary target/release/chess-tools \
    --corpus fixtures/differential_corpus.tsv \
    --games 12 --plies 48 --seed 0xC0FFEE
}

android() {
  require_command cargo
  require_command java
  require_command gradle
  : "${ANDROID_NDK_HOME:?Set ANDROID_NDK_HOME to the Android NDK root.}"
  export ANDROID_API_LEVEL="${ANDROID_API_LEVEL:-24}"
  bash scripts/prepare_android_harness_jni.sh
  gradle -p android-harness \
    :android-smoke:lintDebug \
    :android-smoke:assembleDebug \
    :android-smoke:assembleDebugAndroidTest \
    :host-jvm:test \
    --no-daemon --stacktrace --console=plain
}

command="${1:-}"
if [[ -z "${command}" ]]; then
  usage
  exit 2
fi
shift
case "${command}" in
  bootstrap) [[ $# -eq 0 ]] || { usage; exit 2; }; bootstrap ;;
  fast) [[ $# -eq 0 ]] || { usage; exit 2; }; fast ;;
  full) [[ $# -eq 0 ]] || { usage; exit 2; }; full ;;
  perft)
    [[ $# -le 1 ]] || { usage; exit 2; }
    cargo run --locked --release -p chess-tools -- suite "${1:-4}"
    ;;
  uci)
    cargo run --locked --release -p chess-uci -- "$@"
    ;;
  tui)
    [[ $# -eq 0 ]] || { usage; exit 2; }
    cargo run --locked -p chess-tui
    ;;
  tui-coverage)
    [[ $# -eq 1 ]] || { usage; exit 2; }
    bash scripts/tui_coverage.sh "$1"
    ;;
  tui-pty-smoke)
    [[ $# -eq 0 ]] || { usage; exit 2; }
    # --test-threads=1: each test spawns a real PTY + chess-tui process;
    # single-threaded avoids PTY resource contention between tests.
    cargo test --locked -p chess-tui --test pty_acceptance -- --ignored --test-threads=1
    ;;
  android) [[ $# -eq 0 ]] || { usage; exit 2; }; android ;;
  self-play)
    [[ $# -eq 2 ]] || { usage; exit 2; }
    cargo run --locked --release -p chess-tools -- self-play "$1" "$2"
    ;;
  tune)
    [[ $# -eq 3 || $# -eq 4 ]] || { usage; exit 2; }
    cargo run --locked --release -p chess-tools -- tune "$@"
    ;;
  fuzz-smoke)
    [[ $# -eq 0 ]] || { usage; exit 2; }
    cargo fmt --manifest-path fuzz/Cargo.toml -- --check
    cargo clippy --manifest-path fuzz/Cargo.toml --locked --lib --tests -- -D warnings
    cargo test --manifest-path fuzz/Cargo.toml --locked --lib --tests
    ;;
  strength-audit) [[ $# -eq 0 ]] || { usage; exit 2; }; strength_audit ;;
  variant-control)
    [[ $# -eq 3 ]] || { usage; exit 2; }
    variant_control "$1" "$2" "$3"
    ;;
  artifact-audit) [[ $# -eq 0 ]] || { usage; exit 2; }; artifact_audit ;;
  help|-h|--help) usage ;;
  *) usage; exit 2 ;;
esac
