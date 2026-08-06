from __future__ import annotations

import os
from pathlib import Path

BASELINE_SHA = "152b8a52b90989b113411a9dffc33cb520e45e6b"
RUN_ID = os.environ.get("GITHUB_RUN_ID", "S2_9_VALIDATION_RUN_ID")
CORE_SHA_TOKEN = "CORE_IMPLEMENTATION_SHA"


def read(path: str) -> str:
    return Path(path).read_text(encoding="utf-8")


def write(path: str, content: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def replace_once(path: str, old: str, new: str) -> None:
    content = read(path)
    count = content.count(old)
    if count != 1:
        raise SystemExit(f"{path}: expected one occurrence of {old!r}, found {count}")
    write(path, content.replace(old, new, 1))


search_null = r'''use core::fmt;

use crate::{Color, FullmoveNumber, HalfmoveClock, Square};

use super::{zobrist::side_to_move_key, Position};

/// A fail-loud search-only null-transition error.
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SearchNullError {
    /// The side to move is checked and therefore cannot pass synthetically.
    InCheck {
        /// Checked side that would otherwise have been toggled.
        side_to_move: Color,
    },
    /// The supplied opaque undo token does not match the current synthetic state.
    UndoStateMismatch,
}

impl fmt::Display for SearchNullError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InCheck { side_to_move } => write!(
                formatter,
                "cannot apply a search-only null transition while {side_to_move} is in check"
            ),
            Self::UndoStateMismatch => formatter.write_str(
                "search-only null undo token does not match the current position state",
            ),
        }
    }
}

impl std::error::Error for SearchNullError {}

/// Opaque state required to reverse one search-only null transition.
///
/// This token is deliberately separate from legal-move undo state. It cannot
/// be constructed or altered by callers and must be consumed in LIFO order
/// against the exact synthetic position that produced it.
#[derive(Debug, Eq, PartialEq)]
pub struct SearchNullUndo {
    previous_side_to_move: Color,
    previous_en_passant: Option<Square>,
    previous_halfmove_clock: HalfmoveClock,
    previous_fullmove_number: FullmoveNumber,
    previous_zobrist: u64,
    resulting_zobrist: u64,
}

impl Position {
    /// Applies one reversible search-only null transition.
    ///
    /// The board, castling rights, and legal clocks remain unchanged. The side
    /// to move toggles, en-passant is cleared, and the canonical incremental
    /// hash removes the prior en-passant contribution before toggling its side
    /// key. Checked positions fail before any field is changed.
    pub fn make_search_null(&mut self) -> Result<SearchNullUndo, SearchNullError> {
        let side_to_move = self.side_to_move();
        if self.is_in_check(side_to_move) {
            return Err(SearchNullError::InCheck { side_to_move });
        }

        let undo = SearchNullUndo {
            previous_side_to_move: side_to_move,
            previous_en_passant: self.en_passant(),
            previous_halfmove_clock: self.halfmove_clock(),
            previous_fullmove_number: self.fullmove_number(),
            previous_zobrist: self.zobrist(),
            resulting_zobrist: self.zobrist()
                ^ self.canonical_en_passant_key()
                ^ side_to_move_key(),
        };

        self.en_passant = None;
        self.side_to_move = side_to_move.opposite();
        self.zobrist = undo.resulting_zobrist;
        debug_assert_eq!(self.zobrist(), self.recomputed_zobrist());
        Ok(undo)
    }

    /// Reverses one search-only null transition exactly.
    ///
    /// A token from another position or a non-LIFO restoration attempt fails
    /// before any field is changed.
    pub fn unmake_search_null(&mut self, undo: SearchNullUndo) -> Result<(), SearchNullError> {
        if self.side_to_move() != undo.previous_side_to_move.opposite()
            || self.en_passant().is_some()
            || self.halfmove_clock() != undo.previous_halfmove_clock
            || self.fullmove_number() != undo.previous_fullmove_number
            || self.zobrist() != undo.resulting_zobrist
        {
            return Err(SearchNullError::UndoStateMismatch);
        }

        self.side_to_move = undo.previous_side_to_move;
        self.en_passant = undo.previous_en_passant;
        self.halfmove_clock = undo.previous_halfmove_clock;
        self.fullmove_number = undo.previous_fullmove_number;
        self.zobrist = undo.previous_zobrist;
        debug_assert_eq!(self.zobrist(), self.recomputed_zobrist());
        Ok(())
    }
}

#[cfg(test)]
mod tests {
    use crate::{Color, Position, SearchHistory};

    use super::SearchNullError;

    fn position(fen: &str) -> Position {
        Position::from_fen(fen).expect("search-null fixture FEN is valid")
    }

    fn assert_board_and_rule_state_unchanged(actual: &Position, expected: &Position) {
        for index in 0..crate::Square::COUNT {
            let square = crate::Square::new(index).expect("board index is valid");
            assert_eq!(actual.piece_at(square), expected.piece_at(square));
        }
        for color in [Color::White, Color::Black] {
            assert_eq!(actual.occupancy(color), expected.occupancy(color));
            assert_eq!(actual.king_square(color), expected.king_square(color));
            for kind in crate::PieceKind::ALL {
                assert_eq!(
                    actual.piece_bitboard(color, kind),
                    expected.piece_bitboard(color, kind)
                );
            }
        }
        assert_eq!(actual.all_occupancy(), expected.all_occupancy());
        assert_eq!(actual.castling_rights(), expected.castling_rights());
        assert_eq!(actual.halfmove_clock(), expected.halfmove_clock());
        assert_eq!(actual.fullmove_number(), expected.fullmove_number());
    }

    #[test]
    fn search_null_round_trip_clears_en_passant_and_restores_exactly() {
        let mut current = position("r3k2r/8/8/3pP3/8/8/8/R3K2R w KQkq d6 99 42");
        let snapshot = current.clone();
        let previous_zobrist = current.zobrist();

        let undo = current
            .make_search_null()
            .expect("eligible position accepts a search-only null transition");

        assert_eq!(current.side_to_move(), Color::Black);
        assert_eq!(current.en_passant(), None);
        assert_board_and_rule_state_unchanged(&current, &snapshot);
        assert_ne!(current.zobrist(), previous_zobrist);
        assert_eq!(current.zobrist(), current.recomputed_zobrist());

        current
            .unmake_search_null(undo)
            .expect("matching search-null token restores exactly");
        assert_eq!(current, snapshot);
        assert_eq!(current.zobrist(), previous_zobrist);
        assert_eq!(current.zobrist(), current.recomputed_zobrist());
    }

    #[test]
    fn search_null_preserves_maximum_clocks_without_arithmetic() {
        let mut current = position("7k/8/8/8/8/8/8/K7 b - - 65535 65535");
        let snapshot = current.clone();

        let undo = current
            .make_search_null()
            .expect("maximum counters do not overflow because null does not advance them");
        assert_eq!(current.halfmove_clock(), snapshot.halfmove_clock());
        assert_eq!(current.fullmove_number(), snapshot.fullmove_number());
        assert_eq!(current.zobrist(), current.recomputed_zobrist());

        current
            .unmake_search_null(undo)
            .expect("maximum-counter position restores");
        assert_eq!(current, snapshot);
    }

    #[test]
    fn search_null_rejects_checked_side_before_mutation() {
        let mut current = position("4k3/8/8/8/8/8/4R3/4K3 b - - 17 9");
        let snapshot = current.clone();

        assert_eq!(
            current.make_search_null(),
            Err(SearchNullError::InCheck {
                side_to_move: Color::Black
            })
        );
        assert_eq!(current, snapshot);
        assert_eq!(current.zobrist(), current.recomputed_zobrist());
    }

    #[test]
    fn search_null_rejects_mismatched_undo_before_mutation() {
        let mut source = Position::starting();
        let source_undo = source
            .make_search_null()
            .expect("source transition succeeds");

        let mut target = position("7k/8/8/8/8/8/8/K7 w - - 0 1");
        let _target_undo = target
            .make_search_null()
            .expect("target transition succeeds");
        let target_snapshot = target.clone();

        assert_eq!(
            target.unmake_search_null(source_undo),
            Err(SearchNullError::UndoStateMismatch)
        );
        assert_eq!(target, target_snapshot);
        assert_eq!(target.zobrist(), target.recomputed_zobrist());
    }

    #[test]
    fn search_null_keeps_search_history_on_the_legal_parent() {
        let mut current = position("7k/8/8/3pP3/8/8/8/7K w - d6 73 20");
        let history = SearchHistory::from_position(&current);
        let history_snapshot = history.clone();
        let legal_parent_zobrist = current.zobrist();

        let undo = current
            .make_search_null()
            .expect("search-only null transition succeeds");

        assert_eq!(history, history_snapshot);
        assert_eq!(history.current_zobrist(), Some(legal_parent_zobrist));
        assert_ne!(history.current_zobrist(), Some(current.zobrist()));
        assert_eq!(history.line_len(), 0);

        current
            .unmake_search_null(undo)
            .expect("history-independent transition restores");
        assert_eq!(history.current_zobrist(), Some(current.zobrist()));
    }

    #[test]
    fn search_null_repeated_round_trips_remain_exact() {
        let mut current = position("r3k2r/8/8/3pP3/8/8/8/R3K2R w KQkq d6 12 34");
        let snapshot = current.clone();

        for _ in 0..32 {
            let undo = current
                .make_search_null()
                .expect("repeated transition succeeds");
            assert_eq!(current.zobrist(), current.recomputed_zobrist());
            current
                .unmake_search_null(undo)
                .expect("repeated restoration succeeds");
            assert_eq!(current, snapshot);
            assert_eq!(current.zobrist(), current.recomputed_zobrist());
        }
    }
}
'''

transition_doc = f'''# S2-9.2 Reversible Search-Null Transition

**Status:** Complete
**Date:** 2026-08-05
**Branch:** `master`
**Starting master SHA:** `{BASELINE_SHA}`
**Core implementation SHA:** `{CORE_SHA_TOKEN}`
**Focused validation run:** `{RUN_ID}`
**Activation:** `false`

## Scope

S2-9.2 adds only a dedicated reversible search-only null transition to `chess-core`. It does not add null-move pruning to alpha-beta search, does not enable the reserved policy bit, and does not expose new behavior through UCI, the safe facade, C ABI, JNI, or Android.

## API and type boundary

- `SearchNullUndo` is an opaque token distinct from `PositionUndo`.
- `SearchNullError` reports checked-position misuse and mismatched restoration.
- `Position::make_search_null` and `Position::unmake_search_null` are explicitly named Rust-only position operations.
- No legal-move identity, move kind, legal token, notation, principal variation, or played-game history representation was added.

## State transition

A successful transition:

- leaves every piece, mailbox entry, bitboard, occupancy, cached king square, and castling right unchanged;
- toggles the side to move;
- clears en-passant;
- leaves the halfmove clock unchanged;
- leaves the fullmove number unchanged;
- removes the prior canonical en-passant hash contribution and toggles the side key.

Undo verifies the synthetic side, cleared en-passant state, unchanged clocks, and exact resulting Zobrist identity before mutation. It then restores the prior side, en-passant target, counters, and exact stored hash.

## Failure and counter behavior

Checked positions return `SearchNullError::InCheck` before mutation. A token from another position or a non-LIFO state returns `SearchNullError::UndoStateMismatch` before mutation.

The transition performs no halfmove or fullmove arithmetic. Maximum `u16` counter fixtures therefore remain valid and unchanged rather than encountering an artificial overflow path.

## History boundary

The transition API accepts only `&mut Position`; it has no `Game` or `SearchHistory` argument. Focused tests prove that a detached search history remains rooted at the legal parent while the position temporarily carries the synthetic hash.

## Focused tests

Permanent tests cover:

- legal en-passant identity removal and exact restoration;
- maximum halfmove/fullmove values without arithmetic;
- checked-position failure atomicity;
- mismatched-token failure atomicity;
- detached search-history non-mutation;
- repeated exact round trips;
- incremental/full Zobrist parity after every successful transition and restoration.

## Remaining S2-9 boundary

S2-9.3 must separately define and implement the conservative pruning policy, recursive null-disabled state, TT score suppression, reduced-depth/null-window arithmetic, verification behavior, and complete diagnostics. S2-9.4 remains responsible for zugzwang, draw-boundary, mate, cancellation, performance, and strength disposition evidence.

Production policy, defaults, package/UCI version, adapters, and activation remain unchanged.
'''

transition_audit = r'''#!/usr/bin/env bash
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

for path in "$source_file" "$position_mod" "$core_lib" "$tracker" "$record" "$feasibility"; do
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
grep -Fq '^            previous_halfmove_clock: self.halfmove_clock(),' "$source_file" || fail "halfmove clock is not retained"
grep -Fq '^            previous_fullmove_number: self.fullmove_number(),' "$source_file" || fail "fullmove number is not retained"
grep -Fq '^            previous_zobrist: self.zobrist(),' "$source_file" || fail "prior hash is not retained"
grep -Fq '^                ^ self.canonical_en_passant_key()' "$source_file" || fail "prior canonical en-passant key is not removed"
grep -Fq '^                ^ side_to_move_key(),' "$source_file" || fail "side key is not toggled"
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
  | grep -v '^crates/chess-core/src/position/search_null.rs:' || true)"
[[ -z "$unexpected" ]] || fail "search-null transition escaped its core module: $unexpected"

if grep -R --line-number -E 'make_search_null|unmake_search_null|null_move_pruning_enabled' \
  crates/chess-search/src crates/chess-uci crates/chess-ffi crates/chess-jni 2>/dev/null; then
  fail "search pruning or adapter integration landed during S2-9.2"
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

grep -Fq '| S2-9 | Optional null-move pruning decision/candidate | **In progress — search-null transition complete; pruning policy not started** |' "$tracker" \
  || fail "tracker summary was not advanced"
grep -Fq '## S2-9.2 transition record' "$tracker" || fail "tracker transition record is missing"
grep -Fq 'Begin with **S2-9.3 only**:' "$tracker" || fail "next action does not point to S2-9.3"

s2_9_2="$(sed -n '/## S2-9.2 Search-only transition if implemented/,/## S2-9.3 Conservative policy if implemented/p' "$tracker")"
[[ "$(grep -Fc -- '- [x]' <<<"$s2_9_2")" -eq 5 ]] || fail "S2-9.2 does not have exactly five completed requirements"
[[ "$(grep -Fc -- '- [ ]' <<<"$s2_9_2")" -eq 0 ]] || fail "S2-9.2 still has incomplete requirements"

s2_9_3="$(sed -n '/## S2-9.3 Conservative policy if implemented/,/## S2-9.4 Validation if implemented/p' "$tracker")"
[[ "$(grep -Fc -- '- [ ]' <<<"$s2_9_3")" -gt 0 ]] || fail "S2-9.3 was advanced without policy evidence"

echo "S2-9.2 search-null transition audit passed"
'''

source_path = Path("crates/chess-core/src/position/search_null.rs")
if source_path.exists():
    raise SystemExit(f"{source_path} already exists")
write(str(source_path), search_null)

replace_once(
    "crates/chess-core/src/position/mod.rs",
    "mod make_unmake;\n#[cfg(test)]\nmod tests;",
    "mod make_unmake;\nmod search_null;\n#[cfg(test)]\nmod tests;",
)
replace_once(
    "crates/chess-core/src/position/mod.rs",
    "pub use make_unmake::PositionUndo;\n",
    "pub use make_unmake::PositionUndo;\npub use search_null::{SearchNullError, SearchNullUndo};\n",
)
replace_once(
    "crates/chess-core/src/lib.rs",
    "    PositionInvariantError, PositionUndo,\n",
    "    PositionInvariantError, PositionUndo, SearchNullError, SearchNullUndo,\n",
)

write(
    "docs/RUST_CHESS_ENGINE_V0_2_S2_9_SEARCH_NULL_TRANSITION_2026-08-05.md",
    transition_doc,
)
write("scripts/task_s2_9_search_null_transition_audit.sh", transition_audit)

feasibility_audit = read("scripts/task_s2_9_null_move_feasibility_audit.sh")
feasibility_audit = feasibility_audit.replace(
    "| S2-9 | Optional null-move pruning decision/candidate | **In progress — feasibility complete; implementation approved** |",
    "| S2-9 | Optional null-move pruning decision/candidate | **In progress — search-null transition complete; pruning policy not started** |",
)
feasibility_audit = feasibility_audit.replace(
    "Begin with **S2-9.2 only**:",
    "Begin with **S2-9.3 only**:",
)
old_guard = '''if grep -R --line-number -E 'make_(search_)?null|unmake_(search_)?null|null_move_pruning_enabled' \\
  crates/chess-core/src crates/chess-search/src; then
  fail "null transition or pruning landed before S2-9.2"
fi
'''
new_guard = '''if grep -R --line-number -E 'make_search_null|unmake_search_null|null_move_pruning_enabled' \\
  crates/chess-search/src; then
  fail "null pruning integration landed before S2-9.3"
fi
'''
if old_guard not in feasibility_audit:
    raise SystemExit("feasibility audit transition guard was not found")
feasibility_audit = feasibility_audit.replace(old_guard, new_guard, 1)
write("scripts/task_s2_9_null_move_feasibility_audit.sh", feasibility_audit)

tracker_path = "docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md"
tracker = read(tracker_path)
tracker = tracker.replace(
    "| S2-9 | Optional null-move pruning decision/candidate | **In progress — feasibility complete; implementation approved** |",
    "| S2-9 | Optional null-move pruning decision/candidate | **In progress — search-null transition complete; pruning policy not started** |",
    1,
)
transition_record = f'''## S2-9.2 transition record

- Disposition: complete; the reversible search-only position transition is accepted as infrastructure for S2-9.3, while null pruning remains unimplemented and inactive.
- Starting master SHA: `{BASELINE_SHA}`.
- Core implementation SHA: `{CORE_SHA_TOKEN}`.
- Focused validation run: `{RUN_ID}`.
- Added `SearchNullUndo`, `SearchNullError`, `Position::make_search_null`, and `Position::unmake_search_null` in a dedicated `chess-core` position module.
- State contract: board representations and castling remain unchanged; side toggles; en-passant clears; legal clocks remain unchanged; incremental hash removes the prior canonical en-passant key and toggles the side key.
- Failure contract: checked positions and mismatched undo tokens fail before mutation; maximum counter values are preserved because the transition performs no clock arithmetic.
- History contract: the API accepts only a mutable position and cannot append to `Game` or `SearchHistory`; focused tests retain the legal parent hash while the synthetic state is active.
- Legal/API boundary: no `Move`, `MoveKind`, legal token, UCI history, PV, C ABI, JNI, or Android representation was added.
- Permanent tests cover en-passant identity, both sides, maximum counters, checked-position atomicity, mismatched-token atomicity, detached history, repeated restoration, and incremental/full-hash parity.
- S2-9.3 remains blocked from silently reusing/storing TT scores, nesting null attempts, or cutting off without its separately frozen conservative policy and diagnostics.
- Production search policy, defaults, package/UCI version, adapters, and activation remain unchanged.

'''
marker = "## Program guardrails\n"
if tracker.count(marker) != 1:
    raise SystemExit("tracker program guardrails marker is not unique")
tracker = tracker.replace(marker, transition_record + marker, 1)
old_checklist = '''## S2-9.2 Search-only transition if implemented

- [ ] Add dedicated reversible search-only null transition.
- [ ] It cannot be encoded or accepted as a legal `Move`.
- [ ] It cannot enter UCI/game move history.
- [ ] Exact make/unmake and incremental/full-hash parity.
- [ ] Counter overflow and invalid state fail before mutation.
'''
new_checklist = '''## S2-9.2 Search-only transition if implemented

- [x] Add dedicated reversible search-only null transition.
- [x] It cannot be encoded or accepted as a legal `Move`.
- [x] It cannot enter UCI/game move history.
- [x] Exact make/unmake and incremental/full-hash parity.
- [x] Counter overflow and invalid state fail before mutation.
'''
if tracker.count(old_checklist) != 1:
    raise SystemExit("tracker S2-9.2 checklist was not found exactly once")
tracker = tracker.replace(old_checklist, new_checklist, 1)
if tracker.count("Begin with **S2-9.2 only**:") != 1:
    raise SystemExit("tracker next-action marker was not found exactly once")
tracker = tracker.replace("Begin with **S2-9.2 only**:", "Begin with **S2-9.3 only**:", 1)
write(tracker_path, tracker)

Path(__file__).unlink()
