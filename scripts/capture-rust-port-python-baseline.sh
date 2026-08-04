#!/usr/bin/env bash
# Capture the one-time Python reference baseline required by Task 0 of the Rust port.
#
# This script is intentionally local/manual. It is not part of master CI.
# Run from any directory inside a clean checkout:
#
#   bash scripts/capture-rust-port-python-baseline.sh
#
# Optional expensive evidence:
#
#   RUN_SLOW=1 bash scripts/capture-rust-port-python-baseline.sh
#
# Optional historical Python lint evidence:
#
#   RUN_PYTHON_LINT=1 bash scripts/capture-rust-port-python-baseline.sh

set -Eeuo pipefail

EXPECTED_BRANCH="master"
FROZEN_BASELINE_SHA="f743013a84173b551eac5488c638cb48098ec6d0"
RUN_SLOW="${RUN_SLOW:-0}"
RUN_PYTHON_LINT="${RUN_PYTHON_LINT:-0}"

repo_root="$(git rev-parse --show-toplevel)"
cd "${repo_root}"

capture_sha="$(git rev-parse HEAD)"
current_branch="$(git branch --show-current)"

if [[ -n "$(git status --porcelain)" ]]; then
  printf 'Refusing to capture a baseline from a dirty worktree.\n' >&2
  git status --short >&2
  exit 2
fi

if [[ "${current_branch}" != "${EXPECTED_BRANCH}" ]]; then
  printf 'Expected branch %s, found %s.\n' \
    "${EXPECTED_BRANCH}" "${current_branch:-<detached>}" >&2
  exit 2
fi

if ! git cat-file -e "${FROZEN_BASELINE_SHA}^{commit}"; then
  printf 'Frozen baseline commit %s is not available locally.\n' \
    "${FROZEN_BASELINE_SHA}" >&2
  exit 2
fi

if ! git merge-base --is-ancestor "${FROZEN_BASELINE_SHA}" "${capture_sha}"; then
  cat >&2 <<EOF
The current master checkout is not descended from the frozen baseline.
Frozen baseline: ${FROZEN_BASELINE_SHA}
Capture SHA:     ${capture_sha}
EOF
  exit 2
fi

# Later Rust-port documentation, scripts, and workflow commits are allowed. The
# executable Python baseline is valid only while its source, tests, dependency
# declaration, and lockfile remain identical to the frozen SHA.
python_baseline_paths=(
  chess_game
  tests
  pyproject.toml
  uv.lock
)

if ! git diff --quiet \
  "${FROZEN_BASELINE_SHA}" "${capture_sha}" -- "${python_baseline_paths[@]}"; then
  cat >&2 <<EOF
Python baseline inputs have changed since the frozen baseline.
Frozen baseline: ${FROZEN_BASELINE_SHA}
Capture SHA:     ${capture_sha}

Review this diff and either restore the Python reference tree or explicitly
revise the baseline decision record before collecting evidence:
EOF
  git diff --stat \
    "${FROZEN_BASELINE_SHA}" "${capture_sha}" -- "${python_baseline_paths[@]}" >&2
  exit 2
fi

if ! command -v uv >/dev/null 2>&1; then
  printf 'uv is required but was not found in PATH.\n' >&2
  exit 2
fi

output_dir="${repo_root}/artifacts/rust-port-python-baseline/${capture_sha}"
mkdir -p "${output_dir}"

summary_file="${output_dir}/RESULTS.md"
environment_file="${output_dir}/environment.txt"
status_file="${output_dir}/status.env"
: >"${status_file}"

record_status() {
  local key="$1"
  local value="$2"
  printf '%s=%q\n' "${key}" "${value}" >>"${status_file}"
}

run_timed() {
  local label="$1"
  local log_file="$2"
  shift 2

  local started finished duration status
  started="$(date +%s)"
  set +e
  "$@" >"${log_file}" 2>&1
  status=$?
  set -e
  finished="$(date +%s)"
  duration=$((finished - started))

  record_status "${label}_EXIT" "${status}"
  record_status "${label}_SECONDS" "${duration}"
  printf '%s: exit=%s duration=%ss log=%s\n' \
    "${label}" "${status}" "${duration}" "${log_file}"
  return "${status}"
}

{
  printf 'captured_at_utc=%s\n' "$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
  printf 'frozen_baseline_sha=%s\n' "${FROZEN_BASELINE_SHA}"
  printf 'capture_sha=%s\n' "${capture_sha}"
  printf 'python_tree_matches_frozen_baseline=yes\n'
  printf 'branch=%s\n' "${current_branch}"
  printf 'os=%s\n' "$(uname -a)"
  printf 'cpu=%s\n' "$(uname -m)"
  printf 'uv=%s\n' "$(uv --version)"
  printf 'python=%s\n' "$(uv run python --version 2>&1)"
  if command -v lscpu >/dev/null 2>&1; then
    printf '\n[lscpu]\n'
    lscpu
  fi
} >"${environment_file}"

record_status FROZEN_BASELINE_SHA "${FROZEN_BASELINE_SHA}"
record_status CAPTURE_SHA "${capture_sha}"
record_status PYTHON_TREE_MATCHES_FROZEN_BASELINE "yes"
record_status BRANCH "${current_branch}"
record_status RUN_SLOW "${RUN_SLOW}"
record_status RUN_PYTHON_LINT "${RUN_PYTHON_LINT}"

sync_log="${output_dir}/uv-sync.log"
if ! run_timed UV_SYNC "${sync_log}" uv sync --extra dev; then
  printf 'Dependency synchronization failed; see %s.\n' "${sync_log}" >&2
  exit 1
fi

fast_log="${output_dir}/pytest-fast.log"
fast_status=0
run_timed PYTEST_FAST "${fast_log}" \
  uv run python -m pytest tests/ -q -m "not slow" || fast_status=$?

slow_log="${output_dir}/pytest-slow.log"
slow_status=0
if [[ "${RUN_SLOW}" == "1" ]]; then
  run_timed PYTEST_SLOW "${slow_log}" \
    uv run python -m pytest tests/ -q -m "slow" || slow_status=$?
else
  printf 'Not run. Set RUN_SLOW=1 to capture the expensive suite.\n' >"${slow_log}"
  record_status PYTEST_SLOW_EXIT "NOT_RUN"
  record_status PYTEST_SLOW_SECONDS "NOT_RUN"
fi

perft_log="${output_dir}/perft.log"
perft_status=0
run_timed PERFT "${perft_log}" uv run python - <<'PY' || perft_status=$?
from __future__ import annotations

import time

from chess_game.chess import Board
from chess_game.chess.board.board import Board as BoardImpl

EXPECTED = {
    1: 20,
    2: 400,
    3: 8_902,
    4: 197_281,
}


def perft(board: BoardImpl, depth: int) -> int:
    if depth == 0:
        return 1
    legal = board.get_legal_moves()
    if depth == 1:
        return len(legal)
    total = 0
    for start, end, promotion in legal:
        child = board.clone()
        if not child.make_move(start, end, promotion):
            raise RuntimeError(f"generated move was rejected: {start} {end} {promotion}")
        total += perft(child, depth - 1)
    return total


for depth in range(1, 5):
    started = time.perf_counter()
    nodes = perft(Board(), depth)
    elapsed = time.perf_counter() - started
    expected = EXPECTED[depth]
    print(
        f"depth={depth} nodes={nodes} expected={expected} "
        f"seconds={elapsed:.6f}"
    )
    if nodes != expected:
        raise SystemExit(
            f"perft mismatch at depth {depth}: expected {expected}, got {nodes}"
        )
PY

uci_input="${output_dir}/uci-smoke-input.txt"
uci_log="${output_dir}/uci-smoke.log"
cat >"${uci_input}" <<'EOF'
uci
isready
position startpos moves e2e4 e7e5
go depth 1
quit
EOF

uci_status=0
started="$(date +%s)"
set +e
uv run python -m chess_game.uci <"${uci_input}" >"${uci_log}" 2>&1
uci_process_status=$?
set -e
finished="$(date +%s)"
uci_duration=$((finished - started))

if [[ "${uci_process_status}" -ne 0 ]]; then
  uci_status="${uci_process_status}"
elif ! grep -Fxq 'uciok' "${uci_log}"; then
  printf 'UCI smoke output did not contain uciok.\n' >>"${uci_log}"
  uci_status=1
elif ! grep -Fxq 'readyok' "${uci_log}"; then
  printf 'UCI smoke output did not contain readyok.\n' >>"${uci_log}"
  uci_status=1
elif ! grep -Eq '^info depth 1 ' "${uci_log}"; then
  printf 'UCI smoke output did not contain a depth-1 info line.\n' >>"${uci_log}"
  uci_status=1
elif ! grep -Eq '^bestmove [a-h][1-8][a-h][1-8][qrbn]?$' "${uci_log}"; then
  printf 'UCI smoke output did not contain a legal-looking bestmove.\n' >>"${uci_log}"
  uci_status=1
fi
record_status UCI_SMOKE_EXIT "${uci_status}"
record_status UCI_SMOKE_SECONDS "${uci_duration}"

lint_status=0
if [[ "${RUN_PYTHON_LINT}" == "1" ]]; then
  run_timed RUFF "${output_dir}/ruff.log" \
    uv run python -m ruff check chess_game tests || lint_status=$?
  run_timed MYPY "${output_dir}/mypy.log" \
    uv run python -m mypy chess_game || lint_status=$?
  run_timed PYLINT "${output_dir}/pylint.log" \
    uv run python -m pylint chess_game || lint_status=$?
else
  printf 'Not run. Set RUN_PYTHON_LINT=1 for historical lint evidence.\n' \
    >"${output_dir}/python-lint-NOT-RUN.txt"
fi

# shellcheck disable=SC1090
source "${status_file}"

cat >"${summary_file}" <<EOF
# Python Reference Baseline Results

**Frozen Python source baseline:** \`${FROZEN_BASELINE_SHA}\`  
**Evidence capture SHA:** \`${capture_sha}\`  
**Python tree matches frozen baseline:** \`yes\`  
**Branch:** \`${current_branch}\`  
**Captured:** \`$(date -u +'%Y-%m-%dT%H:%M:%SZ')\`

## Environment

See \`environment.txt\`.

## Results

| Gate | Exit/result | Duration |
|---|---:|---:|
| \`uv sync --extra dev\` | \`${UV_SYNC_EXIT}\` | \`${UV_SYNC_SECONDS}s\` |
| Fast pytest | \`${PYTEST_FAST_EXIT}\` | \`${PYTEST_FAST_SECONDS}s\` |
| Slow pytest | \`${PYTEST_SLOW_EXIT}\` | \`${PYTEST_SLOW_SECONDS}\` |
| Starting-position perft depths 1-4 | \`${PERFT_EXIT}\` | \`${PERFT_SECONDS}s\` |
| UCI smoke | \`${UCI_SMOKE_EXIT}\` | \`${UCI_SMOKE_SECONDS}s\` |

## Commands

\`\`\`bash
uv sync --extra dev
uv run python -m pytest tests/ -q -m "not slow"
uv run python -m pytest tests/ -q -m "slow"
uv run python <embedded perft capture>
uv run python -m chess_game.uci < uci-smoke-input.txt
\`\`\`

## Evidence files

- \`environment.txt\`
- \`uv-sync.log\`
- \`pytest-fast.log\`
- \`pytest-slow.log\`
- \`perft.log\`
- \`uci-smoke-input.txt\`
- \`uci-smoke.log\`
- \`status.env\`

The generated directory must be reviewed before it is committed. Do not commit
virtual environments, caches, secrets, or unrelated generated data.
EOF

printf 'Baseline evidence written to %s\n' "${output_dir}"

required_status=0
if [[ "${fast_status}" -ne 0 || "${perft_status}" -ne 0 || "${uci_status}" -ne 0 ]]; then
  required_status=1
fi
if [[ "${RUN_SLOW}" == "1" && "${slow_status}" -ne 0 ]]; then
  required_status=1
fi
if [[ "${RUN_PYTHON_LINT}" == "1" && "${lint_status}" -ne 0 ]]; then
  required_status=1
fi

exit "${required_status}"
