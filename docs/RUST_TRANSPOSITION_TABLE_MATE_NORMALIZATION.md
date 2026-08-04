# Rust Transposition-Table Mate-Score Normalization

## Scope

This document defines Task 15.3 only: converting root-relative search mate scores into position-relative transposition-table scores and converting them back at a later search ply.

It does not define table probing, depth or bound cutoffs, repetition-sensitive reuse, replacement, diagnostics, or production search integration. Those remain Tasks 15.4 through 15.6.

## Why normalization is required

Search scores encode mate distance from the current search root. The same chess position can be reached at different plies in different searches, so storing that root-relative value directly would make the entry incorrect when reused from another root.

The table instead stores mate distance relative to the indexed position. Let `p` be the ply from the current root to that position.

For a winning mate score:

- storage adds `p`;
- retrieval subtracts the new probe ply.

For a losing mate score:

- storage subtracts `p`;
- retrieval adds the new probe ply.

This removes the already-travelled root distance when storing and restores the appropriate root distance when retrieving.

## Non-mate scores

Every score in the static-evaluation domain from `-MAX_EVALUATION` through `MAX_EVALUATION` is preserved exactly. Normalization and denormalization do not round, clamp, or otherwise alter ordinary evaluations.

## Public API

- `TranspositionScore::normalize(score, ply)` converts a root-relative `Score` into the storage domain.
- `TranspositionScore::denormalize(ply)` converts the stored value back into a root-relative `Score`.
- `TranspositionScoreConversionError` reports unsupported plies and any conversion that would leave the supported score domain.

The unchecked constructor used by entry-layout tests is crate-private, so external callers cannot place an arbitrary search score into the storage domain.

## Failure behavior

Both directions reject plies greater than `MAX_MATE_PLY`.

Normalization also rejects an inconsistent mate score whose adjustment would exceed `MATE_SCORE` or go below `-MATE_SCORE`. There is no saturation, clamping, or fallback score.

## Validation requirements

Task 15.3 tests prove:

- ordinary evaluations remain exact at root and maximum supported ply;
- one winning-mate entry normalizes identically when the same position is reached at different plies;
- one losing-mate entry normalizes identically when the same position is reached at different plies;
- maximum supported ply reaches and reverses both immediate-mate storage boundaries;
- inconsistent root-relative mate values fail before storage;
- unsupported plies fail in both conversion directions.
