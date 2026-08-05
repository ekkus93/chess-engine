#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  printf 'usage: %s PATH_TO_CHESS_UCI\n' "$0" >&2
  exit 2
fi

binary=$1
[[ -x "${binary}" ]] || {
  printf 'task26-uci-smoke: binary is not executable: %s\n' "${binary}" >&2
  exit 1
}

transcript=$(mktemp)
trap 'rm -f "${transcript}"' EXIT

{
  printf 'uci\n'
  printf 'isready\n'
  printf 'position startpos\n'
  printf 'go depth 1\n'
  sleep 1
  printf 'quit\n'
} | timeout 15s "${binary}" | tee "${transcript}"

grep -Fqx 'uciok' "${transcript}"
grep -Fqx 'readyok' "${transcript}"
grep -Eq '^info depth 1 .* pv [a-h][1-8][a-h][1-8][qrbn]?( |$)' "${transcript}"
grep -Eq '^bestmove [a-h][1-8][a-h][1-8][qrbn]?( ponder [a-h][1-8][a-h][1-8][qrbn]?)?$' "${transcript}"

printf '%s\n' 'task26-uci-smoke: exact handshake and playable fixed-depth search passed'
