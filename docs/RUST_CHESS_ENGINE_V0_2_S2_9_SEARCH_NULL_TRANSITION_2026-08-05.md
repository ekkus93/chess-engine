# S2-9.2 Reversible Search-Null Transition

**Status:** Complete
**Date:** 2026-08-05
**Branch:** `master`
**Starting master SHA:** `152b8a52b90989b113411a9dffc33cb520e45e6b`
**Core implementation SHA:** `CORE_IMPLEMENTATION_SHA`
**Focused validation run:** `31074949590`
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
