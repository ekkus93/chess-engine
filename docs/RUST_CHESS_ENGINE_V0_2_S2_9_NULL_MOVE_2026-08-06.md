# S2-9 Null-Move Pruning Validation and Disposition

**Status:** Complete — standalone activation rejected
**Date:** 2026-08-06
**Branch:** `master`
**Validated candidate source SHA:** `8638611e38c712009e7f98bd4881fb266034df13`
**Staging validation run:** `31085412059`
**Evidence artifact:** `8961204541`
**Artifact digest:** `sha256:1c7ed56774119f9d771453e045b03345d4aae31d840eec30a7c03b96a28d8a19`
**Disposition:** `rejected_strength`
**Activation:** `false`

## Scope

S2-9.4 validates the isolated conservative null-move candidate implemented in S2-9.3. It does not alter the authoritative v0.1 policy, expose an experimental option through UCI or adapters, combine null move with rejected candidates, or activate the candidate.

## Candidate identity and frozen policy

- baseline policy identifier/checksum: `5630315f504f4c31` / `0c0769ef9d034770`;
- candidate policy identifier/checksum: `5332394e4d503031` / `4364aad2ac2abc2a`;
- evaluation identity/checksum: `424153454c494e45` / `d2cca7ae10ec6e34`;
- minimum remaining depth: `4`;
- speculative child depth: `depth - 1 - 2`;
- verification depth: `depth - 1`;
- side-to-move minimum non-pawn/non-king pieces: `2`;
- total minimum non-pawn/non-king pieces: `4`;
- every speculative fail-high requires verification;
- root, check, shallow, low-material, nested-null, verification, and mate-sensitive contexts remain disabled.

The synthetic transition still leaves legal clocks and `SearchHistory` unchanged, suppresses TT score reuse/storage throughout speculative subtrees, and restores the exact legal position before errors or cancellation propagate.

## Correctness evidence

The versioned 14-case corpus covers:

- classical and mutual zugzwang-sensitive endings;
- root stalemate and a high-material position that becomes stalemate after a synthetic pass;
- threefold and fivefold repetition roots;
- halfmove-clock values `99`, `100`, `149`, and `150`;
- mate distance and longest-survival behavior;
- a sparse position that actually enters the speculative null path;
- repeated successful searches and bounded node-cancellation restoration.

Every case matched the baseline score and completed depth. All best moves were identical, every reported PV replayed legally, position/history restoration was exact, and incremental/full Zobrist parity held.

Deterministic aggregate:

- case count: `14`;
- differing best moves: `0`;
- null attempts: `11071`;
- disabled nodes: `11066`;
- speculative fail-highs: `0`;
- verification searches: `0`;
- confirmed cutoffs: `0`;
- aggregate checksum: `75da625a5ae9c6d7`;
- activated: `false`.

The sparse exercise produced `946` attempts and `941` disabled nodes, proving that five speculative null searches executed while retaining exact baseline semantics. The absence of fail-highs means no verification or cutoff occurred in this corpus; the permanent invariants still require fail-high and verification totals to match and cutoffs not to exceed verifications.

## Fixed-node development protocol

- pairs/games: `8` / `16` color-swapped games;
- resource limit: `2000` nodes per move;
- maximum plies: `48`;
- candidate W/D/L: `0/0/0`;
- unfinished: `16`;
- illegal moves/crashes/time forfeits/infrastructure failures: `0/0/0/0`;
- decision: `rejected_strength`;
- report checksum: `81a8a72c9242da64`;
- activated: `false`.

Two independent deterministic generations were byte-identical. Because every game reached the bounded maximum-ply limit, this protocol supplied no positive standalone strength evidence. It does not prove the candidate is weaker; it fails the project acceptance gate.

## Clock development protocol

- pairs/games: `8` / `16` color-swapped games;
- resource limit: `10` milliseconds per move;
- maximum plies: `48`;
- candidate W/D/L: `0/0/0`;
- unfinished: `16`;
- illegal moves/crashes/time forfeits/infrastructure failures: `0/0/0/0`;
- decision: `rejected_strength`;
- report checksum: `9054382ea9b188c5`;
- activated: `false`.

This independent protocol likewise supplied no positive strength evidence and therefore rejects standalone activation under the existing fail-closed development rules.

## Disposition

The explicit S2-9 disposition is **`rejected_strength`**. Correctness and restoration requirements passed, but neither independent development protocol produced evidence sufficient for activation. The null-move candidate remains isolated and inactive. Production UCI, safe Rust APIs, C ABI, JNI, Android, package version, evaluation weights, authoritative v0.1 policy, and defaults remain unchanged.

## Fail-closed findings during validation

Validation corrected fixture and harness assumptions rather than weakening gates:

- rustfmt-only layout differences were applied verbatim;
- the opening generator now uses a mutable legal-move scratch position;
- terminal iterative-deepening accounting correctly records one root node per completed depth;
- a halfmove-`99` position may still evaluate as a forced claimable draw after the next legal move;
- the restoration stress position was changed from an unnecessarily expensive middlegame to a sparse position that still executes speculative null searches;
- synthetic-pass stalemate is tested directly with exact undo.

No lint suppression, ignored result, silent fallback, downgraded gate, or production activation was introduced.
