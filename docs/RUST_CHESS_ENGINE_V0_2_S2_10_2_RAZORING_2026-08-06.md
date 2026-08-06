# Rust Chess Engine v0.2 S2-10.2 Razoring Decision

**Status:** Complete — deferred
**Date:** 2026-08-06
**Disposition:** `defer`
**Activation:** `false`
**Starting master SHA:** `90c5c1ef0afa615b1d63a0b7857c0809133ef4e4`
**Decision staging SHA:** `a3b7bca8f538f2e154a6690939ba37ad14b82798`
**Tracker:** `docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md`
**Specification:** `docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_SPEC_2026-08-05.md`
**Prerequisite:** `docs/RUST_CHESS_ENGINE_V0_2_S2_10_1_FUTILITY_2026-08-06.md`

## Decision

S2-10.2 is complete with `defer`. No razoring policy, margin, diagnostics mutation, search branch, test-only activation path, or production behavior is retained. This does not establish that razoring is intrinsically weak; it records that the ordered prerequisite evidence does not exist.

## Prerequisite finding

The tracker permits razoring only after futility evidence. The specification permits it only when profiling and node evidence justify it after futility work. S2-10.1 produced no executable evidence:

- the accepted engine remains full-window fail-soft alpha-beta;
- the strict futility candidate recorded exactly zero attempts;
- the wide-window draft violated the non-PV contract;
- PVS, which provides systematic null-window contexts, was independently rejected and remains inactive;
- all futility implementation, policy, margin, diagnostics mutation, and candidate tests were removed rather than retained as dead configuration.

Implementing razoring now would therefore bypass the evidence order, create an inert candidate, or silently combine it with rejected/inactive search behavior.

## Required future verification semantics

Any reconsidered candidate must satisfy all of these conditions:

1. Eligibility is shallow, explicitly bounded, outside check, forced-evasion, mate-score, promotion, tactically unstable, and unproven low-material contexts.
2. Static evaluation plus a typed versioned margin requests only a razor probe; it is not an exact result.
3. The probe uses legal quiescence verification against the original alpha bound.
4. Only a verified fail-low may return early, and that return is an upper bound.
5. A probe that raises alpha, is ambiguous, or encounters any arithmetic/capacity/internal failure falls through to the unchanged full search.
6. The probe never creates an exact transposition-table entry. Any upper-bound storage must be separately specified and depth-safe.
7. Dedicated regressions cover checks, evasions, mate distance, promotions, quiet defenses, tactical instability, and low-material/endgame positions.
8. Attempts, verified fail-lows, fall-throughs, and prunes are independently counted without allocation or silent exact-aggregation overflow.

## Correctness and strength disposition

No behaviorally distinct candidate passed the prerequisite gate. Consequently:

- candidate correctness matrix: not run;
- fixed-node strength match: not run;
- clock strength match: not run;
- activation: `false`.

An identical-policy match would only reproduce the frozen 0.5 control and would not constitute razoring evidence.

## Production impact

None. The authoritative policy/checksum, alpha-beta, quiescence, TT semantics, diagnostics, evaluation weights, UCI, Rust API, C ABI, JNI, Android behavior, package version, and defaults remain unchanged. `ExperimentalSearchFeature::Razoring` remains unsupported by policy validation, and production alpha-beta contains no razoring branch.

## Reconsideration gate

Reconsider only after independently accepted futility evidence, or as an explicitly approved combination with a new complete policy identity and independent combined-semantics proof. Full correctness plus separate fixed-node and clock strength reports remain mandatory. No rejected candidate may be silently enabled merely to exercise razoring.
