#!/usr/bin/env bash
# Run the complete Task 0 and Task 1 evidence gate for the Rust port.
#
# This script is intentionally local/manual. The rust-engine CI workflow remains
# Rust-only; the Python baseline is captured once as historical reference evidence.
#
# Usage:
#   bash scripts/validate-rust-port-task0-task1.sh
#
# Optional controls:
#   RUN_SLOW=0          Skip the expensive Python slow suite (Task 0 stays open).
#   RUN_PYTHON_LINT=1   Capture historical Python lint evidence (not required by Rust CI).

set -Eeuo pipefail

EXPECTED_BRANCH="rust-engine"
RUN_SLOW="${RUN_SLOW:-1}"
RUN_PYTHON_LINT="${RUN_PYTHON_LINT:-0}"

repo_root="$(git rev-parse --show-toplevel)"
cd "${repo_root}"

candidate_sha="$(git rev-parse HEAD)"
current_branch="$(git branch --show-current)"

if [[ "${current_branch}" != "${EXPECTED_BRANCH}" ]]; then
  printf 'Expected branch %s, found %s.\n' \
    "${EXPECTED_BRANCH}" "${current_branch:-<detached>}" >&2
  exit 2
fi

if [[ -n "$(git status --porcelain --untracked-files=all)" ]]; then
  printf 'Refusing to validate a dirty worktree.\n' >&2
  git status --short >&2
  exit 2
fi

for required_command in git uv cargo rustc; do
  if ! command -v "${required_command}" >/dev/null 2>&1; then
    printf '%s is required but was not found in PATH.\n' \
      "${required_command}" >&2
    exit 2
  fi
done

temporary_dir="$(mktemp -d)"
baseline_wrapper_log="${temporary_dir}/python-baseline-wrapper.log"

# Run the baseline capture before creating wrapper artifacts inside the repository;
# the baseline script correctly refuses to start from a dirty worktree.
baseline_started="$(date +%s)"
set +e
RUN_SLOW="${RUN_SLOW}" RUN_PYTHON_LINT="${RUN_PYTHON_LINT}" \
  bash scripts/capture-rust-port-python-baseline.sh \
  >"${baseline_wrapper_log}" 2>&1
baseline_status=$?
set -e
baseline_finished="$(date +%s)"

output_dir="${repo_root}/artifacts/rust-port-task0-task1/${candidate_sha}"
mkdir -p "${output_dir}"
mv "${baseline_wrapper_log}" "${output_dir}/python-baseline-wrapper.log"
rmdir "${temporary_dir}"

status_file="${output_dir}/status.tsv"
environment_file="${output_dir}/environment.txt"
summary_file="${output_dir}/RESULTS.md"
: >"${status_file}"

record_status() {
  local label="$1"
  local result="$2"
  local seconds="$3"
  local log_path="$4"
  printf '%s\t%s\t%s\t%s\n' \
    "${label}" "${result}" "${seconds}" "${log_path}" >>"${status_file}"
}

run_timed() {
  local label="$1"
  local log_name="$2"
  shift 2

  local log_path="${output_dir}/${log_name}"
  local started finished duration exit_code
  started="$(date +%s)"

  printf 'Running %s...\n' "${label}"
  set +e
  "$@" >"${log_path}" 2>&1
  exit_code=$?
  set -e

  finished="$(date +%s)"
  duration=$((finished - started))
  record_status "${label}" "${exit_code}" "${duration}" "${log_name}"

  if [[ "${exit_code}" -ne 0 ]]; then
    printf '%s failed with exit %s; tail of %s follows.\n' \
      "${label}" "${exit_code}" "${log_path}" >&2
    tail -n 200 "${log_path}" >&2 || true
  else
    printf '%s passed in %ss.\n' "${label}" "${duration}"
  fi

  return "${exit_code}"
}

write_summary() {
  local overall_status="$1"
  local generated_at
  generated_at="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"

  {
    printf '# Rust Port Task 0 and Task 1 Validation\n\n'
    printf '**Candidate SHA:** `%s`  \n' "${candidate_sha}"
    printf '**Branch:** `%s`  \n' "${current_branch}"
    printf '**Generated:** `%s`  \n' "${generated_at}"
    printf '**Overall exit:** `%s`\n\n' "${overall_status}"
    printf '## Results\n\n'
    printf '| Gate | Exit/result | Seconds | Log |\n'
    printf '|---|---:|---:|---|\n'
    while IFS=$'\t' read -r label result seconds log_path; do
      printf '| `%s` | `%s` | `%s` | `%s` |\n' \
        "${label}" "${result}" "${seconds}" "${log_path}"
    done <"${status_file}"
    printf '\n## Policy\n\n'
    printf -- '- Every first-party compiler, Clippy, rustdoc, formatting, and test finding is a defect.\n'
    printf -- '- No first-party lint finding may be hidden, suppressed, downgraded, or filtered.\n'
    printf -- '- Third-party or vendored warnings are outside this first-party rule.\n'
    printf -- '- All Rust commands after lockfile generation use `--locked`.\n'
    printf -- '- Review `git-status.txt`, `Cargo.lock`, and every log before committing evidence.\n'
  } >"${summary_file}"
}

final_status=0
trap 'trap_status=$?; write_summary "${trap_status}"; exit "${trap_status}"' EXIT

{
  printf 'captured_at_utc=%s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  printf 'candidate_sha=%s\n' "${candidate_sha}"
  printf 'branch=%s\n' "${current_branch}"
  printf 'os=%s\n' "$(uname -a)"
  printf 'uv=%s\n' "$(uv --version 2>&1)"
  printf 'python=%s\n' "$(uv run python --version 2>&1)"
  printf 'rustc=%s\n' "$(rustc --version 2>&1)"
  printf 'cargo=%s\n' "$(cargo --version 2>&1)"
  if command -v lscpu >/dev/null 2>&1; then
    printf '\n[lscpu]\n'
    lscpu
  fi
} >"${environment_file}"

record_status \
  "python-reference-baseline" \
  "${baseline_status}" \
  "$((baseline_finished - baseline_started))" \
  "python-baseline-wrapper.log"
if [[ "${baseline_status}" -ne 0 ]]; then
  final_status=1
  printf 'Python reference baseline failed; continuing to collect Rust evidence.\n' >&2
  tail -n 200 "${output_dir}/python-baseline-wrapper.log" >&2 || true
fi

suppression_log="${output_dir}/first-party-lint-suppression-scan.log"
set +e
{
  suppression_found=0
  if grep -RInE \
    --include='*.rs' \
    '#!?\[[^]]*(allow|expect)[[:space:]]*\(' \
    crates; then
    suppression_found=1
  fi
  if grep -RInE \
    --include='Cargo.toml' \
    '^[[:space:]]*[A-Za-z0-9_-]+[[:space:]]*=[[:space:]]*"allow"' \
    Cargo.toml crates; then
    suppression_found=1
  fi
  if [[ "${suppression_found}" -ne 0 ]]; then
    printf 'First-party lint suppression is prohibited.\n' >&2
    exit 1
  fi
  printf 'No first-party allow/expect lint suppression found.\n'
} >"${suppression_log}" 2>&1
suppression_status=$?
set -e
record_status \
  "first-party-lint-suppression-scan" \
  "${suppression_status}" \
  "0" \
  "first-party-lint-suppression-scan.log"
if [[ "${suppression_status}" -ne 0 ]]; then
  final_status=1
  cat "${suppression_log}" >&2
fi

export CARGO_TERM_COLOR=never
export RUSTFLAGS="-Dwarnings"
export RUSTDOCFLAGS="-Dwarnings"

run_timed "cargo-generate-lockfile" "cargo-generate-lockfile.log" \
  cargo generate-lockfile || final_status=1

if [[ ! -f Cargo.lock ]]; then
  printf 'Cargo.lock was not generated.\n' >&2
  record_status "cargo-lockfile-present" "1" "0" "Cargo.lock"
  final_status=1
else
  record_status "cargo-lockfile-present" "0" "0" "Cargo.lock"
fi

run_timed "cargo-metadata" "cargo-metadata.log" \
  cargo metadata --locked --format-version 1 --no-deps || final_status=1
run_timed "cargo-fmt" "cargo-fmt.log" \
  cargo fmt --all -- --check || final_status=1
run_timed "cargo-check" "cargo-check.log" \
  cargo check --locked --workspace --all-targets --all-features || final_status=1
run_timed "cargo-clippy" "cargo-clippy.log" \
  cargo clippy --locked --workspace --all-targets --all-features -- -D warnings \
  || final_status=1
run_timed "cargo-test" "cargo-test.log" \
  cargo test --locked --workspace --all-features || final_status=1
run_timed "cargo-doc" "cargo-doc.log" \
  cargo doc --locked --workspace --all-features --no-deps || final_status=1
run_timed "cargo-build-debug" "cargo-build-debug.log" \
  cargo build --locked --workspace --all-features || final_status=1
run_timed "cargo-build-release" "cargo-build-release.log" \
  cargo build --locked --workspace --all-features --release || final_status=1

if [[ "$(git rev-parse HEAD)" != "${candidate_sha}" ]]; then
  printf 'HEAD changed during validation.\n' >&2
  record_status "candidate-sha-stable" "1" "0" "git-status.txt"
  final_status=1
else
  record_status "candidate-sha-stable" "0" "0" "git-status.txt"
fi

git status --short --untracked-files=all >"${output_dir}/git-status.txt"

if ! git diff --quiet -- . ':(exclude)Cargo.lock'; then
  printf 'Tracked files other than Cargo.lock changed during validation.\n' >&2
  git diff --stat -- . ':(exclude)Cargo.lock' >&2
  record_status "tracked-source-tree-stable" "1" "0" "git-status.txt"
  final_status=1
else
  record_status "tracked-source-tree-stable" "0" "0" "git-status.txt"
fi

if [[ "${RUN_SLOW}" != "1" ]]; then
  printf 'RUN_SLOW was not 1; Task 0 cannot close.\n' >&2
  record_status "task0-slow-suite-required" "1" "0" "python-baseline-wrapper.log"
  final_status=1
else
  record_status "task0-slow-suite-required" "0" "0" "python-baseline-wrapper.log"
fi

if [[ "${final_status}" -ne 0 ]]; then
  printf 'Task 0/1 validation failed. Fix every first-party finding and rerun the full script.\n' >&2
else
  printf 'Task 0/1 local validation passed for exact SHA %s.\n' "${candidate_sha}"
  printf 'Review and commit Cargo.lock plus the evidence directories, then run CI for the same SHA.\n'
fi

exit "${final_status}"
