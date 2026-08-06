# S2-9.1 Null-Move Pruning Feasibility Decision

**Status:** Feasibility complete
**Date:** 2026-08-05
**Branch:** `master`
**Inspected source SHA:** `76862f5730a518957bf0fbd3daf15af99f37ce6c`
**Disposition:** `implement`
**Activation:** `false`

## Decision

Null-move pruning fits the current Rust core and search architecture, provided it is implemented as a dedicated reversible **search-only transition** and never represented as a legal chess move.

This decision authorizes S2-9.2 to implement and test the transition primitive. It does not authorize null-move pruning in production search, change the authoritative v0.1 policy, expose a new adapter option, or mark S2-9 complete.

## Inspected architecture

The feasibility review covered:

- `crates/chess-core/src/position/mod.rs`;
- `crates/chess-core/src/position/make_unmake.rs`;
- `crates/chess-core/src/position/zobrist.rs`;
- `crates/chess-core/src/counters.rs`;
- `crates/chess-core/src/game.rs`;
- `crates/chess-search/src/alpha_beta.rs`;
- `crates/chess-search/src/search_common.rs`;
- `crates/chess-search/src/transposition.rs`;
- `crates/chess-search/src/transposition/probe.rs`;
- `crates/chess-search/src/search_policy.rs`;
- `crates/chess-search/src/diagnostics.rs`.

The current architecture is suitable because position state is private and centralized, legal make/unmake already uses opaque exact-state undo tokens, the repetition hash has explicit canonical semantics, played-game history and search-line history are separate, recursive search restores position and history before propagating child errors, and null-move policy identity plus initial diagnostics slots are already reserved.

## Required search-only transition contract

### Type and API boundary

- Add a dedicated opaque undo type such as `SearchNullUndo`.
- Add a Rust-only position transition API with an explicit search-only name.
- Do not encode the transition as `Move`, add a `MoveKind`, create a legal-move token, or let legal move generation return it.
- Do not add it to `Game`, UCI move history, C ABI, JNI, Android, opening-book data, PV output, or user-visible notation.
- Reject invalid use with a typed error before changing any position field.

### Position state

A successful search-null transition must:

- leave the board, mailbox, piece bitboards, occupancies, cached king squares, and castling rights unchanged;
- toggle `side_to_move`;
- clear `en_passant`;
- leave `halfmove_clock` unchanged;
- leave `fullmove_number` unchanged.

The clocks remain unchanged because a search-null transition is not a legal chess halfmove. Artificially incrementing either clock would create false fifty/seventy-five-move outcomes and would break the relationship between legal history entries and the reversible-move boundary.

### Zobrist identity

The incremental transition must:

1. remove the old canonical en-passant contribution;
2. toggle the side-to-move key;
3. add no new en-passant contribution because the target is cleared;
4. leave all piece and castling contributions untouched.

The resulting key must match full recomputation. Undo must restore the exact prior key rather than trying to reconstruct it from partially trusted state.

### Undo and failure atomicity

The opaque undo token must retain enough information to prove exact LIFO use, including the prior side, en-passant state, clocks, and Zobrist key, plus the expected post-transition identity.

- Counter, depth, window, diagnostic, and eligibility checks must complete before mutation.
- A mismatched undo token must fail before mutation.
- Successful undo must restore every position field exactly.
- Tests must cover normal completion, cancellation, recursive errors, mismatched tokens, and repeated transition/untransition sequences.

## History and repetition semantics

The synthetic null position must **not** be pushed into `SearchHistory`.

`SearchHistory` represents legally reached game and search-line positions. Adding a synthetic pass would let an illegal position count toward threefold repetition and would misalign the history length with the legal halfmove clock.

At the direct synthetic node, the latest history hash intentionally remains the legal parent hash. Repetition lookup therefore cannot treat the synthetic node as a legal occurrence. After the null subtree makes an actual legal move, that resulting legal position is pushed normally.

The real `Game` object and its move/hash vectors must never be involved.

## Transposition-table semantics

A null-search subtree is path-dependent and synthetic. Its position keys can collide semantically with normally reached positions even though their legal histories differ.

The initial candidate must therefore:

- suppress TT score reuse throughout the speculative null subtree;
- suppress TT score storage throughout that subtree;
- permit a verified TT move only as a legal-move-checked ordering hint;
- use a distinct explicit suppression reason rather than silently treating the subtree as ordinary repetition;
- return to ordinary TT policy only after leaving the speculative subtree or entering an explicit verification search.

Baseline and candidate searches continue to require separate caller-owned transposition tables through the existing engine-variant identity contract.

## Search recursion and consecutive-null behavior

Null eligibility must be explicit recursive state, not inferred from move history.

- Root calls start outside a null subtree.
- Entering the speculative null subtree marks the complete subtree as null-disabled for the initial conservative implementation.
- No second null transition may occur anywhere inside that speculative subtree.
- Any verification search must also disable null at the verifying node so it cannot confirm itself recursively.
- The state must be restored by ordinary stack unwinding and covered by cancellation/error tests.

The null attempt belongs only in main alpha-beta search after legal-move generation and terminal/draw resolution. It must not run:

- at quiescence nodes;
- in check;
- at a checkmate or stalemate node;
- after a rule draw has already resolved;
- when depth/window arithmetic cannot be represented safely.

A dedicated checked null-window constructor and checked reduced-depth calculation are required before mutation.

## Zugzwang, stalemate, and material risk

Null-move pruning assumes that passing is not beneficial. That assumption fails in zugzwang and is particularly dangerous in pawn-only and low-material endings.

Before pruning integration, S2-9.3 must freeze a conservative policy that initially excludes:

- pawn-only endings;
- low non-pawn material;
- in-check nodes;
- shallow depths;
- mate-sensitive windows and contexts;
- consecutive or nested null attempts.

Permanent fixtures must include classical zugzwang, mutual zugzwang, synthetic-stalemate-after-pass, quiet only-move defenses, mate distance, and longest-survival cases. A speculative null fail-high must not become a cutoff unless the frozen policy's explicit verification rule permits it.

## Fifty- and seventy-five-move behavior

The parent node resolves existing rule draws before attempting null.

Because null does not increment the halfmove clock:

- a position at 100 or 150 halfmoves is resolved before null;
- a position at 99 remains at 99 during the synthetic pass;
- the opponent's subsequent legal quiet move advances it to 100 normally;
- a legal pawn move or capture resets it normally;
- no synthetic history key is counted as a reversible legal position.

This preserves legal draw semantics without a hidden exception or fallback.

## Diagnostics required before pruning integration

The existing reserved attempt and cutoff counters are not sufficient for the tracker contract. S2-9.3 must define and implement explicit checked diagnostics for at least:

- eligibility attempts;
- disabled nodes, preferably with stable reason classes;
- speculative null fail-highs;
- verification searches;
- confirmed cutoffs.

Overflow must remain typed for completed exact results and explicit/saturating only where the existing request-wide observation interface requires it.

## Feasibility gate result

**Disposition: `implement`.**

S2-9.2 may now add only the dedicated reversible search-null transition and its focused correctness tests. Null pruning, reduction parameters, material thresholds, verification policy, strength testing, and activation remain blocked until their later S2-9 gates pass.

Production behavior, package/UCI version, adapters, authoritative policy, and defaults remain unchanged.
