# S2-9.3 Conservative Null-Move Pruning Policy

**Status:** Implementation complete; validation pending
**Date:** 2026-08-05
**Branch:** `master`
**Core implementation SHA:** `029c16ed216a0fc84d6772c10ea8678ad202c6cf`
**Staging validation run:** `31080097848`
**Activation:** `false`

## Scope

S2-9.3 integrates the S2-9.2 reversible search-only transition into controlled alpha-beta search under a new isolated, inactive policy identity. It does not activate null-move pruning in default search, expose it through production adapters, run strength matches, or claim the S2-9 gate.

## Frozen policy

- minimum remaining depth: `4`;
- speculative child depth: `depth - 1 - 2`;
- verification depth: `depth - 1`;
- side-to-move minimum non-pawn/non-king pieces: `2`;
- total minimum non-pawn/non-king pieces: `4`;
- static evaluation must meet or exceed beta;
- every speculative fail-high is verified before cutoff;
- root, check, shallow, low-material, nested, verification, and mate-sensitive contexts are disabled.

All depth and one-centipawn window arithmetic is checked before the position transition. Arithmetic failure is typed and cannot silently disable or mutate the position.

## Search-state and TT semantics

Recursive state explicitly distinguishes ordinary, speculative-null, and verification subtrees. The complete speculative subtree disables additional null attempts and uses `TranspositionScoreReuse::SuppressedForNullMove`, which suppresses TT scores and storage while preserving only complete-key, legal-checked move-ordering hints. The verification subtree also disables null recursively but may use ordinary TT score policy because the position is again legal and no speculative subtree entry was stored.

The synthetic position is never pushed into `SearchHistory`. Position undo always runs before cancellation or recursive errors propagate.

## Diagnostics

The candidate records checked counters for:

- null-move eligibility attempts;
- disabled nodes, with stable reason-bearing events;
- speculative fail-highs;
- verification searches;
- confirmed cutoffs.

Every speculative fail-high must have exactly one verification search. Confirmed cutoffs cannot exceed verification searches. Baseline/default search keeps all null counters at zero.

## Permanent tests

Tests cover policy identity/default inactivity, checked depths and windows, root/check/shallow/material/nested guards, explicit TT suppression, midgame diagnostics, pawn-only and low-material exclusion, legal PV replay, deterministic restoration, and node-limited cancellation.

## Remaining S2-9.4 work

S2-9.4 must independently validate zugzwang, stalemate, repetition, fifty/seventy-five-move boundaries, mate distance, longest survival, exact restoration/cancellation, and fixed-node plus clock development strength. It must then record `accept`, `reject`, or `defer`. The candidate remains inactive until that evidence exists.
