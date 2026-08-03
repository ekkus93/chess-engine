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
