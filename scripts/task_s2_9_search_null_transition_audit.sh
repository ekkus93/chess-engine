#!/usr/bin/env bash
set -euo pipefail

fail() {
  echo "S2-9.2 search-null transition audit failed: $*" >&2
  exit 1
}

source_file="crates/chess-core/src/position/search_null.rs"
position_mod="crates/chess-core/src/position/mod.rs"
core_lib="crates/chess-core/src/lib.rs"
tracker="docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md"
record="docs/RUST_CHESS_ENGINE_V0_2_S2_9_SEARCH_NULL_TRANSITION_2026-08-05.md"
feasibility="docs/RUST_CHESS_ENGINE_V0_2_S2_9_NULL_MOVE_FEASIBILITY_2026-08-05.md"
validation_test="crates/chess-search/tests/s2_9_null_move_validation.rs"

for path in "$source_file" "$position_mod" "$core_lib" "$tracker" "$record" "$feasibility" "$validation_test"; do
  [[ -f "$path" ]] || fail "missing $path"
done

grep -Fq 'mod search_null;' "$position_mod" || fail "position module is not wired"
grep -Fq 'pub use search_null::{SearchNullError, SearchNullUndo};' "$position_mod" || fail "position exports are missing"
grep -Fq 'SearchNullError, SearchNullUndo' "$core_lib" || fail "crate exports are missing"
grep -Fq 'pub enum SearchNullError' "$source_file" || fail "typed error is missing"
grep -Fq 'pub struct SearchNullUndo' "$source_file" || fail "opaque undo token is missing"
grep -Fq 'pub fn make_search_null' "$source_file" || fail "make transition is missing"
grep -Fq 'pub fn unmake_search_null' "$source_file" || fail "unmake transition is missing"
grep -Fq 'if self.is_in_check(side_to_move)' "$source_file" || fail "checked-position precondition is missing"
grep -Fq 'self.en_passant = None;' "$source_file" || fail "en-passant is not cleared"
grep -Fq 'self.side_to_move = side_to_move.opposite();' "$source_file" || fail "side is not toggled"
grep -Fq 'previous_halfmove_clock: self.halfmove_clock(),' "$source_file" || fail "halfmove clock is not retained"
grep -Fq 'previous_fullmove_number: self.fullmove_number(),' "$source_file" || fail "fullmove number is not retained"
grep -Fq 'previous_zobrist: self.zobrist(),' "$source_file" || fail "prior hash is not retained"
grep -Fq '^ self.canonical_en_passant_key()' "$source_file" || fail "prior canonical en-passant key is not removed"
grep -Fq '^ side_to_move_key(),' "$source_file" || fail "side key is not toggled"
grep -Fq 'debug_assert_eq!(self.zobrist(), self.recomputed_zobrist());' "$source_file" || fail "hash parity assertion is missing"

if grep -Eq '(^|[^[:alnum:]_])Move(Kind)?([^[:alnum:]_]|$)' "$source_file"; then
  fail "search-null source depends on a legal Move identity"
fi
if grep -Eq 'checked_increment|\.reset\(' "$source_file"; then
  fail "search-null source mutates legal clocks"
fi
if grep -Eq '#!\[(allow|expect)|#\[(allow|expect)' "$source_file"; then
  fail "search-null source contains lint suppression"
fi

unexpected="$(grep -R --line-number -E 'make_search_null|unmake_search_null' crates \
  | grep -v '^crates/chess-core/src/position/search_null.rs:' \
  | grep -v '^crates/chess-search/src/alpha_beta.rs:' \
  | grep -v '^crates/chess-search/tests/s2_9_null_move_validation.rs:' || true)"
[[ -z "$unexpected" ]] || fail "search-null transition escaped approved core/search/test modules: $unexpected"
grep -Fq 'position.make_search_null()' crates/chess-search/src/alpha_beta.rs \
  || fail "S2-9.3 search integration is missing make_search_null"
grep -Fq 'position.unmake_search_null(undo)' crates/chess-search/src/alpha_beta.rs \
  || fail "S2-9.3 search integration is missing unmake_search_null"
grep -Fq '.make_search_null()' "$validation_test" \
  || fail "S2-9.4 synthetic-pass validation is missing make_search_null"
grep -Fq '.unmake_search_null(undo)' "$validation_test" \
  || fail "S2-9.4 synthetic-pass validation is missing unmake_search_null"
if grep -R --line-number -E 'make_search_null|unmake_search_null|null_move_pruning_enabled' \
  crates/chess-uci crates/chess-ffi crates/chess-jni 2>/dev/null; then
  fail "search-null transition leaked into a production adapter"
fi

grep -Fq 'search_null_round_trip_clears_en_passant_and_restores_exactly' "$source_file" || fail "round-trip regression is missing"
grep -Fq 'search_null_preserves_maximum_clocks_without_arithmetic' "$source_file" || fail "maximum-counter regression is missing"
grep -Fq 'search_null_rejects_checked_side_before_mutation' "$source_file" || fail "checked-position atomicity regression is missing"
grep -Fq 'search_null_rejects_mismatched_undo_before_mutation' "$source_file" || fail "mismatched-token regression is missing"
grep -Fq 'search_null_keeps_search_history_on_the_legal_parent' "$source_file" || fail "history-boundary regression is missing"
grep -Fq 'search_null_repeated_round_trips_remain_exact' "$source_file" || fail "repeated restoration regression is missing"

grep -Fq '**Status:** Complete' "$record" || fail "transition record is not complete"
grep -Fq '**Activation:** `false`' "$record" || fail "transition record does not remain inactive"
grep -Fq '**Core implementation SHA:** `CORE_IMPLEMENTATION_SHA`' "$record" \
  && fail "transition record still contains the implementation placeholder"
grep -Fq '**Focused validation run:** `S2_9_VALIDATION_RUN_ID`' "$record" \
  && fail "transition record still contains the run placeholder"
grep -Fq 'Production policy, defaults, package/UCI version, adapters, and activation remain unchanged.' "$record" \
  || fail "production non-change is missing"

grep -Fq '| S2-9 | Optional null-move pruning decision/candidate | **Complete — standalone rejected; inactive** |' "$tracker" \
  || fail "tracker summary was not advanced through S2-9.3"
grep -Fq '## S2-9.2 transition record' "$tracker" || fail "tracker transition record is missing"
grep -Fq 'Begin with **S2-10.1 only**:' "$tracker" || fail "next action does not point to S2-9.4"

s2_9_2="$(sed -n '/## S2-9.2 Search-only transition if implemented/,/## S2-9.3 Conservative policy if implemented/p' "$tracker")"
[[ "$(grep -Fc -- '- [x]' <<<"$s2_9_2")" -eq 5 ]] || fail "S2-9.2 does not have exactly five completed requirements"
[[ "$(grep -Fc -- '- [ ]' <<<"$s2_9_2")" -eq 0 ]] || fail "S2-9.2 still has incomplete requirements"

s2_9_3="$(sed -n '/## S2-9.3 Conservative policy if implemented/,/## S2-9.4 Validation if implemented/p' "$tracker")"
[[ "$(grep -Fc -- '- [x]' <<<"$s2_9_3")" -eq 7 ]] || fail "S2-9.3 does not have exactly seven completed requirements"
[[ "$(grep -Fc -- '- [ ]' <<<"$s2_9_3")" -eq 0 ]] || fail "S2-9.3 still has incomplete requirements"

echo "S2-9.2 search-null transition audit passed"
