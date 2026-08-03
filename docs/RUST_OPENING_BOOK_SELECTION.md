# Rust opening-book selection policies

Task 19.3 adds adapter-neutral legality resolution and selection policy to the
`chess-book` crate. It does not integrate opening books into UCI, the safe
engine facade, JNI, or Android; those remain Task 19.4.

## Exact legal resolution

`IndexedBook` now implements `OpeningBook`. A lookup:

1. derives the canonical position key;
2. obtains the contiguous indexed records for that position;
3. generates the exact legal move identities from a cloned `Position`;
4. resolves each stored `UciMove` against those identities; and
5. returns `BookMove<u32>` candidates only when every record resolves exactly
   once.

A syntax-valid record that is illegal in the supplied position returns
`IndexedBookQueryError::IllegalMove`. Legal-move generation and indexed-format
errors remain typed and fail visible. No unchecked internal `Move` is ever
synthesized from coordinate syntax.

`BookSelector` validates all candidates again at the generic `OpeningBook`
boundary. This protects adapters that implement another backend and ensures no
policy can return an illegal or semantically mismatched internal move.

## Deterministic highest weight

`BookSelector::deterministic_highest_weight()` is the default policy.

Candidates are placed in ascending UCI coordinate order before selection. The
candidate with the greatest `u32` weight is returned. Equal greatest weights
therefore resolve to the lexicographically first UCI move, independent of the
order supplied by a backend.

Duplicate exact move identities are rejected rather than counted twice.

## Seeded weighted random

`BookSelector::weighted_random(seed)` opts into weighted selection with one
explicit `u64` seed. The selector owns its random state; it does not use a
process-global generator, operating-system entropy, wall-clock time, files,
environment variables, or platform services.

The stable version-1 policy uses SplitMix64 and unbiased rejection sampling over
the sum of candidate weights. A candidate with weight zero is never selected.
If all candidate weights are zero, selection fails with
`BookSelectionError::ZeroTotalWeight`. Checked `u64` accumulation prevents a
silently wrapped total.

Two selectors created with the same seed and queried through the same sequence
of canonically equivalent candidate sets produce the same move sequence.
Cloning a selector intentionally clones its current local stream state.

## Empty books and failures

An empty candidate list returns `Ok(None)`. Backend errors, legal-move
generation failures, illegal candidates, duplicate candidates, weight overflow,
and zero-total weighted selection remain distinct typed failures. None is
converted into an empty-book result or a search fallback.

## Deferred integration

Task 19.3 does not:

- enable or disable a book through UCI;
- add safe-facade configuration;
- load Android assets;
- define adapter I/O;
- change search behavior when no book is configured; or
- close the overall Task 19 gate.

Those behaviors remain assigned to Tasks 19.4 and 19.5.

## Completion evidence

- Exact merged implementation SHA: `82b5100f501fe4e4a845d5fb3bdbb1c8fe7d34ef`.
- Exact PR head validated before rebase merge: `4bb4e30f457b9b84e09485cf51629ab0b3c6d37d`; the production policy blob is unchanged at the merged SHA.
- Permanent Rust validation: run `30859905206`, job `91839380997`.
- Permanent Android regression validation: run `30859905203`, host JVM job `91839428990`, API-35 emulator job `91839429013`.
- Six focused Task 19.3 policy and legality tests passed; `chess-book` executed 17 tests and the complete workspace executed 323 non-documentation Rust tests with zero failures.
- Committed lockfile verification, workspace metadata, rustfmt, all-target/all-feature compilation, strict Clippy with warnings denied, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and the independent differential oracle passed.
- Differential validation covered 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- The unchanged Android gate rebuilt and verified both JNI ABIs, passed host JVM tests, rebuilt the AAR/test APK, and passed the API-35 emulator lifecycle.
- Task 19.3 is complete. Tasks 19.4–19.5 and the overall Task 19 gate remain open.
