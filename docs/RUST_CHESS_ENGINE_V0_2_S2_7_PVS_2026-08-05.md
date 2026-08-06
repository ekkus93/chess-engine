# Rust Chess Engine v0.2 — S2-7 Principal Variation Search

**Status:** Implementation validation in progress
**Date:** 2026-08-05
**Activation:** false

## Scope

S2-7 adds an inactive, identity-bound Principal Variation Search candidate to the controlled Rust search path. The authoritative v0.1 production policy, public convenience entry points, UCI, safe Rust facade, C ABI, JNI, Android integration, package version, evaluation weights, and defaults remain unchanged.

## Search contract

- The first ordered move is searched with the node's full alpha-beta window.
- Every later move is first searched with the one-centipawn child window `[-alpha - 1, -alpha]`.
- A null-window result that strictly improves alpha without reaching beta is re-searched with the full child window before it can become an exact principal value.
- Null-window fail-low results cannot replace an equal earlier best move; fail-high results retain normal beta-cutoff semantics.
- Both attempts contribute to node, quiescence-node, selective-depth, diagnostic, cancellation, and limit accounting.
- TT probing, fail-soft score propagation, mate normalization, bound classification, and deterministic strict-greater best-move replacement remain shared with the baseline search.
- Window construction is fail-loud; there is no neutral-score, baseline-search, or disabled-feature fallback.

## Identity and activation boundary

The candidate is available only through `SearchPolicySet::principal_variation_search_candidate()`. `SearchPolicy::V0_1` remains the policy used by every production convenience path. Candidate and baseline validation must use separate caller-owned transposition tables.

## Validation plan

The permanent `S2-7 Principal Variation Search validation` workflow runs the source audit, formatting, strict Clippy, focused parity/restoration tests, and the complete `chess-search` test suite on x86-64 and native ARM64. Deterministic corpus, fixed-node development, optional clock development, and benchmark evidence are added only after this correctness slice passes.
