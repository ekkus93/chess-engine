# S2-10.1 Futility-Pruning Decision and Disposition

**Status:** Complete — deferred
**Date:** 2026-08-06
**Branch:** `master`
**Authoritative baseline source:** `542509b07bc02f6754de7c1682224fd2aa249a1e`
**Initial generated draft SHA:** `86004c11da96dad19455619c0fdb98cf8b97b66b`
**Strict review staging SHA:** `87fb97b7aed342cf79ba5765ed6696411a7677e6`
**Cleanup implementation SHA:** `e603d963f3de363406c47be6d8dafa8bfb6bea1d`
**Focused proof run/job:** `31092967077` / `92588097246`
**Disposition:** `defer`
**Activation:** `false`

## Scope

S2-10.1 asks whether a separately versioned, shallow, non-PV futility-pruning candidate is justified against the accepted search baseline. It explicitly forbids silently combining futility with rejected PVS, LMR, SEE/delta, or null-move candidates and requires an independent correctness and strength disposition.

The authoritative production search remains full-window alpha-beta under the v0.1 search policy. S2-7 implemented a narrow-window PVS candidate, but that candidate was independently rejected and remains inactive.

## Review finding

The initial generated draft added a depth-one `150 cp` frontier margin, candidate policy identity, attempt/prune diagnostics, quiet-move protections, and tactical tests. Its node eligibility did not distinguish PV from non-PV search, so it could prune at wide-window/PV nodes. That violates the frozen S2-10.1 contract and was not accepted as an implementation detail or justified fallback.

The review correction added a strict one-centipawn null-window requirement. It retained shallow-depth, non-check, non-root, non-mate-domain, quiet, non-checking, non-capture, non-promotion, non-TT-move, non-killer, and multi-move protections.

## Fail-closed proof

Focused workflow run `31092967077`, job `92588097246`, executed the corrected candidate with Rust `1.97.1` and LLVM `22.1.6`.

The following passed before the exercise gate:

- formatting and diff checks;
- locked `cargo check` for all `chess-search` targets/features;
- strict Clippy with warnings denied;
- all 119 `chess-search` unit tests;
- search property tests;
- candidate identity/default-inactivity tests;
- tactical and rule-sensitive root parity tests.

The mandatory exercise test then failed because `frontier_futility_attempts()` was exactly zero. Publication was skipped. The failed assertion was intentional evidence that a purported candidate cannot be accepted when it never reaches its advertised behavior.

## Architectural conclusion

The zero-attempt result is not repaired by searching for a more convenient fixture. Under the accepted baseline, recursive main search uses wide alpha-beta windows. The codebase produces eligible one-centipawn non-PV main-search windows only through the rejected and inactive PVS candidate. Therefore:

1. allowing futility at existing wide-window nodes violates S2-10.1;
2. enforcing the non-PV contract makes the standalone candidate inert;
3. enabling PVS solely to exercise futility would combine independently rejected candidates and invalidate isolation;
4. retaining an unexercisable policy bit, margin, diagnostics, or test surface would misrepresent supported behavior.

The correct disposition is `defer`, not `implement`, `accept`, or a quiet no-op fallback.

## Strength disposition

No fixed-node or clock match was run after the correctness pre-gate proved there was no executable behavioral candidate. A baseline-versus-no-op match would duplicate the frozen S2-3 identical-policy control and cannot provide evidence for activation. This is recorded as a deliberate deferred disposition, not as favorable, unfavorable, or missing strength evidence.

Reconsideration requires one of these explicit future conditions:

- a narrow-window main-search policy is independently accepted; or
- an explicitly identified combination candidate is evaluated with a new complete policy identity, isolated correctness proof, and independent fixed-node and clock strength reports.

## Cleanup and permanent validation

Cleanup commit `e603d963f3de363406c47be6d8dafa8bfb6bea1d` restored the authoritative production source blobs and removed:

- the unsafe/no-op futility implementation;
- its candidate policy identity and parameters;
- its diagnostics mutations and integration test;
- both one-time generator payloads; and
- the write-capable temporary generator workflow.

Exact cleanup validation succeeded:

- CI run `31093244779`;
- performance run `31093244660`;
- robustness run `31093244674`;
- Android/JNI run `31093244043`.

Production UCI, safe Rust facade, C ABI, JNI, Android, package version, evaluation weights, authoritative v0.1 policy, and defaults remain unchanged. No lint suppression, ignored failure, downgraded gate, silent fallback, dead candidate configuration, temporary helper, or write-capable permanent workflow remains.
