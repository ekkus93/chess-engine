#!/usr/bin/env bash
set -euo pipefail

fail() {
  echo "S2-9.1 null-move feasibility audit failed: $*" >&2
  exit 1
}

tracker="docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md"
decision="docs/RUST_CHESS_ENGINE_V0_2_S2_9_NULL_MOVE_FEASIBILITY_2026-08-05.md"
position="crates/chess-core/src/position/mod.rs"
make_unmake="crates/chess-core/src/position/make_unmake.rs"
zobrist="crates/chess-core/src/position/zobrist.rs"
counters="crates/chess-core/src/counters.rs"
game="crates/chess-core/src/game.rs"
search="crates/chess-search/src/alpha_beta.rs"
search_common="crates/chess-search/src/search_common.rs"
tt_probe="crates/chess-search/src/transposition/probe.rs"
policy="crates/chess-search/src/search_policy.rs"
diagnostics="crates/chess-search/src/diagnostics.rs"

for path in \
  "$tracker" "$decision" "$position" "$make_unmake" "$zobrist" "$counters" \
  "$game" "$search" "$search_common" "$tt_probe" "$policy" "$diagnostics"; do
  [[ -f "$path" ]] || fail "missing $path"
done

grep -Fq '**Status:** Feasibility complete' "$decision" || fail "decision status is missing"
grep -Fq '**Inspected source SHA:** `76862f5730a518957bf0fbd3daf15af99f37ce6c`' "$decision" || fail "baseline SHA is missing"
grep -Fq '**Disposition:** `implement`' "$decision" || fail "implement disposition is missing"
grep -Fq '**Activation:** `false`' "$decision" || fail "inactive state is missing"
grep -Fq 'must **not** be pushed into `SearchHistory`' "$decision" || fail "synthetic-history exclusion is missing"
grep -Fq 'leave `halfmove_clock` unchanged' "$decision" || fail "halfmove semantics are missing"
grep -Fq 'leave `fullmove_number` unchanged' "$decision" || fail "fullmove semantics are missing"
grep -Fq 'suppress TT score reuse throughout the speculative null subtree' "$decision" || fail "TT reuse suppression is missing"
grep -Fq 'suppress TT score storage throughout that subtree' "$decision" || fail "TT store suppression is missing"
grep -Fq 'No second null transition may occur anywhere inside that speculative subtree.' "$decision" || fail "consecutive-null contract is missing"
grep -Fq 'S2-9.2 may now add only the dedicated reversible search-null transition' "$decision" || fail "next implementation boundary is missing"
grep -Fq 'Production behavior, package/UCI version, adapters, authoritative policy, and defaults remain unchanged.' "$decision" || fail "production non-change is missing"

grep -Fq '| S2-9 | Optional null-move pruning decision/candidate | **Complete — standalone rejected; inactive** |' "$tracker" || fail "summary status is not advanced through S2-9.3"
grep -Fq '## S2-9 feasibility record' "$tracker" || fail "tracker feasibility record is missing"
grep -Fq '# Task S2-9: Optional null-move pruning decision/candidate — COMPLETE' "$tracker" || fail "S2-9 heading is not in progress"
grep -Fq 'Begin with **S2-10.1 only**:' "$tracker" || fail "next action does not point to S2-9.4"

s2_9_1="$(sed -n '/## S2-9.1 Feasibility decision/,/## S2-9.2 Search-only transition if implemented/p' "$tracker")"
[[ "$(grep -Fc -- '- [x]' <<<"$s2_9_1")" -eq 4 ]] || fail "S2-9.1 does not have exactly four completed requirements"
[[ "$(grep -Fc -- '- [ ]' <<<"$s2_9_1")" -eq 0 ]] || fail "S2-9.1 still has incomplete requirements"

s2_9_remaining="$(sed -n '/## S2-9.2 Search-only transition if implemented/,/# Task S2-10:/p' "$tracker")"
[[ "$(grep -Fc -- '- [x]' <<<"$s2_9_remaining")" -eq 19 ]] || fail "later S2-9 work is not fully completed"
[[ "$(grep -Fc -- '- [ ]' <<<"$s2_9_remaining")" -eq 0 ]] || fail "later S2-9 work still has incomplete requirements"

grep -Fq 'pub struct Position {' "$position" || fail "private position state inventory is missing"
grep -Fq 'previous_zobrist: u64' "$make_unmake" || fail "legal undo no longer retains exact prior hash"
grep -Fq 'Halfmove and fullmove counters are intentionally excluded.' "$zobrist" || fail "canonical hash clock policy changed"
grep -Fq 'pub fn checked_increment' "$counters" || fail "checked clock arithmetic is missing"
grep -Fq 'The position remains history-free.' "$game" || fail "position/history separation changed"
grep -Fq 'pub fn search_history(&self) -> SearchHistory' "$game" || fail "detached search history is missing"
grep -Fq 'pub fn push_position(&mut self, position: &Position)' "$game" || fail "search history push contract is missing"
grep -Fq 'HistoryPositionMismatch' "$search" || fail "root history-position validation is missing"
grep -Fq 'history.pop_position(history_undo)' "$search" || fail "recursive history restoration is missing"
grep -Fq 'position.unmake_move(position_undo)' "$search" || fail "recursive position restoration is missing"
grep -Fq 'position.halfmove_clock().get() >= CLAIMABLE_HALFMOVE_COUNT' "$search_common" || fail "search fifty-move boundary changed"
grep -Fq 'SuppressedForRepetition' "$tt_probe" || fail "path-dependent TT suppression is missing"
grep -Fq 'ExperimentalSearchFeature::NullMovePruning' "$policy" || fail "reserved null-move identity bit is missing"
grep -Fq 'NullMoveAttempts' "$diagnostics" || fail "reserved null-move attempt counter is missing"
grep -Fq 'NullMoveCutoffs' "$diagnostics" || fail "reserved null-move cutoff counter is missing"

grep -Fq 'position.make_search_null()' "$search" || fail "S2-9.3 search-null integration is missing"
grep -Fq 'position.unmake_search_null(undo)' "$search" || fail "S2-9.3 search-null restoration is missing"
grep -Fq 'null_move_pruning_enabled' "$search" || fail "S2-9.3 policy gate is missing"

echo "S2-9.1 null-move feasibility audit passed"
