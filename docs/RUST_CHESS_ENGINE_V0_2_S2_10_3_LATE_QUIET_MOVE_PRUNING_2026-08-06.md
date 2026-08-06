# Rust Chess Engine v0.2 S2-10.3 Late Quiet-Move Pruning Decision

**Status:** Complete — deferred
**Date:** 2026-08-06
**Disposition:** `deferred_insufficient_evidence`
**Activation:** `false`
**Starting master SHA:** `9f0ba7267ceab406a8bb1fa3cb9cc0d0699fe226`
**Decision staging SHA:** `c912bfb4e13895b41b5f54b4ebd6293b355a2d2a`
**Tracker:** `docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md`
**Specification:** `docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_SPEC_2026-08-05.md`
**Prerequisite evidence:** `docs/RUST_CHESS_ENGINE_V0_2_S2_8_LMR_2026-08-05.md`

## Decision

S2-10.3 is complete with `deferred_insufficient_evidence`. No late quiet-move pruning policy, threshold, search branch, diagnostic mutation, test-only activation path, or production behavior is retained.

This is not a claim that late-move pruning can never improve the engine. It records that the available LMR and move-ordering evidence does not justify omitting legal quiet moves under a fail-closed correctness contract.

## Prerequisite evidence reviewed

The ordered prerequisite is satisfied in the documentary sense: S2-8 produced an isolated, typed, fully verified LMR candidate with deterministic x86-64 and native ARM64 evidence. That evidence is negative for a more aggressive pruning layer:

- both fixed-node and clock development protocols returned `rejected_strength`;
- the x86-64 candidate/baseline timing ratio was `1.001488`, approximately `0.149%` slower;
- the ARM64 ratio was `1.000153`, approximately `0.015%` slower;
- the bounded release workload searched `40,000 / 40,000` main nodes and changed qnodes only from `35,620` to `35,665` while executing `98` reductions and `38` mandatory verifications;
- the correctness corpus exercised `29` reductions, including `7` reduced alpha raises followed by `7` full-depth verification searches;
- an early policy missed a sparse forced mate after treating an apparently quiet late move as safely reducible. The permanent repair required additional low-material and mate-window exclusions.

LMR is less destructive than late-move pruning: it keeps a reduced search and verifies every alpha raise. Late-move pruning omits the move entirely. Negative LMR performance/strength evidence and the discovered quiet-resource defect therefore do not support removing the verification path.

## Missing policy proof

The current ordering state contains two killers and a search-local history table. History entries accumulate `depth^2` bonuses and saturate at `1,000,000`, but the repository has no calibrated, versioned threshold that establishes when a history score is weak enough to permit omission.

Choosing a threshold from folklore or convenience would violate the program's one-candidate-at-a-time and evidence-first rules. It would also make “protect strong-history moves” circular: the candidate would define strength by the same unvalidated cutoff used to prune.

## Required future semantics

Any reconsidered candidate must have a new complete policy identity and satisfy all of the following before games:

1. Use explicitly versioned, typed, bounded depth, move-index, legal-move-count, total-piece-count, and history thresholds.
2. Remain shallow and non-root, and exclude in-check nodes, checking moves, captures, promotions, TT moves, killers, mate-score windows, low-mobility positions, and low-material/endgame positions unless separately proven safe.
3. Define how principal-variation or narrow-window status is established; it may not infer non-PV safety from move index alone.
4. Preserve at least one searched quiet move after every protected category and never prune all legal continuations.
5. Treat arithmetic, capacity, ordering-state, and internal errors as visible failures rather than silently disabling or widening the candidate.
6. Never report a pruned subtree as exact or create an exact transposition-table entry without independent proof.
7. Count considered moves, policy-disabled moves, and actual prunes separately with checked overflow behavior.
8. Extend the permanent quiet strategic-resource, quiet defensive-resource, forced-mate, longest-survival, promotion-race, en-passant, zugzwang, low-mobility, low-material, cancellation, limit, legal-PV, and restoration matrix.
9. Run independent fixed-node and clock strength protocols after the correctness gate. A compound LMR-plus-pruning experiment requires its own identity and cannot silently enable the rejected LMR policy.

## Correctness and strength disposition

No behaviorally distinct candidate passed the design gate. Consequently:

- candidate correctness matrix: not run;
- fixed-node strength match: not run;
- clock strength match: not run;
- activation: `false`.

An identical-policy match would only reproduce the frozen `0.5` control and would not constitute late-move-pruning evidence.

## Production impact

None. The authoritative v0.1 policy/checksum, alpha-beta, quiescence, transposition-table semantics, diagnostics values, evaluation weights, UCI, safe Rust API, C ABI, JNI, Android behavior, package version, and defaults remain unchanged. `ExperimentalSearchFeature::LateMovePruning` remains reserved but unsupported by policy validation, and production alpha-beta contains no late-move-pruning branch.

## Reconsideration gate

Reconsider only after fresh profiling or controlled move-value evidence identifies a defensible shallow late-quiet population and a calibrated history threshold. Full correctness, architecture-specific performance, and separate fixed-node and clock strength reports remain mandatory. No rejected candidate may be silently enabled to manufacture eligibility.
