from pathlib import Path

TODO_PATH = Path("docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md")
REPORT_PATH = Path("docs/RUST_CHESS_ENGINE_V0_2_S2_10_1_FUTILITY_2026-08-06.md")
SCRIPT_PATH = Path(".github/s2_10_1_closure.py")
WORKFLOW_PATH = Path(".github/workflows/s2-10-1-closure.yml")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one occurrence, found {count}")
    return text.replace(old, new, 1)


todo = TODO_PATH.read_text(encoding="utf-8")

decision_record = """## S2-10.1 futility-pruning decision record

- Disposition: complete with `defer`; no futility candidate is retained or activated.
- Authoritative production baseline restored: `542509b07bc02f6754de7c1682224fd2aa249a1e` search-policy/source blobs, preserved by cleanup commit `e603d963f3de363406c47be6d8dafa8bfb6bea1d`.
- Initial generated draft SHA: `86004c11da96dad19455619c0fdb98cf8b97b66b`.
- Strict non-PV review staging SHA: `87fb97b7aed342cf79ba5765ed6696411a7677e6`.
- Focused proof run: `31092967077`; job `92588097246`.
- Final decision record: `docs/RUST_CHESS_ENGINE_V0_2_S2_10_1_FUTILITY_2026-08-06.md`.
- The generated draft was rejected because it allowed frontier pruning at wide-window/PV nodes, contrary to the frozen S2-10.1 contract.
- The corrected candidate required a one-centipawn null window, passed check, strict Clippy, 119 unit tests, property tests, and tactical/rule-sensitive tests, then failed its mandatory exercise assertion because it recorded exactly zero futility attempts.
- This is an architectural result rather than a missing fixture: the authoritative v0.1 baseline is full-window alpha-beta, while the only narrow-window main-search implementation is the rejected and inactive S2-7 PVS candidate. A standalone compliant futility policy therefore has no eligible non-PV frontier nodes.
- Widening eligibility would violate the task contract; combining futility with rejected PVS would violate candidate isolation. Retaining a policy flag, margin, counters, or tests for a behavior that cannot execute would create misleading dead configuration.
- No strength match was run because there was no executable behavioral candidate after the correctness pre-gate. A no-op comparison would duplicate the frozen identical-policy control and cannot supply acceptance evidence.
- The unsafe/no-op draft, candidate identity, margin, diagnostics changes, test, generator payloads, and write-capable temporary workflow were removed. Production UCI, safe Rust facade, C ABI, JNI, Android, package version, evaluation weights, authoritative policy, and defaults remain unchanged.
- Exact cleanup validation: CI run `31093244779`; performance run `31093244660`; robustness run `31093244674`; Android/JNI run `31093244043`; all successful.
- Reconsider only after a narrow-window main-search policy is independently accepted, or as an explicitly identified combination candidate with its own policy identity, correctness evidence, and strength disposition.

"""

todo = replace_once(
    todo,
    "## Program guardrails\n",
    decision_record + "## Program guardrails\n",
    "decision record insertion",
)

todo = replace_once(
    todo,
    "| S2-10 | Optional frontier and quiet-move pruning candidates | **Not started** |",
    "| S2-10 | Optional frontier and quiet-move pruning candidates | **In progress — S2-10.1 deferred; S2-10.2 and S2-10.3 not started** |",
    "program summary",
)

old_task = """# Task S2-10: Optional frontier and quiet-move pruning candidates — NOT STARTED

## S2-10.1 Futility pruning

- [ ] Decide based on current profile and accepted prior candidates.
- [ ] Add separate versioned policy if implemented.
- [ ] Limit initial use to shallow non-PV, non-check nodes and quiet non-checking moves.
- [ ] Protect checks, promotions, captures, forced evasions, and mate-score windows.
- [ ] Type and bound margins.
- [ ] Count attempts/prunes.
- [ ] Run independent correctness and strength disposition.
"""
new_task = """# Task S2-10: Optional frontier and quiet-move pruning candidates — IN PROGRESS

## S2-10.1 Futility pruning — COMPLETE (DEFERRED)

- [x] Decide based on current profile and accepted prior candidates. Disposition: `defer`; the accepted full-window baseline has no eligible non-PV frontier nodes, and the narrow-window PVS candidate is rejected/inactive.
- [x] Add separate versioned policy if implemented. Not implemented: the unsafe/no-op draft identity was removed rather than retained as dead configuration.
- [x] Limit initial use to shallow non-PV, non-check nodes and quiet non-checking moves. The strict review required a one-centipawn null window and preserved the remaining guards; the resulting candidate recorded zero attempts.
- [x] Protect checks, promotions, captures, forced evasions, and mate-score windows. The draft protections were reviewed, but the complete candidate was removed because its node-level eligibility could not be satisfied independently.
- [x] Type and bound margins. The draft's checked `150 cp` depth-one margin was not adopted because no compliant node could exercise it.
- [x] Count attempts/prunes. Reserved baseline counters remain zero; the strict proof observed exactly zero candidate attempts and therefore no prunes.
- [x] Run independent correctness and strength disposition. Check, strict Clippy, 119 unit tests, property tests, and tactical/rule-sensitive tests passed; the mandatory exercise test failed closed on zero attempts. No strength match was run for a non-behavioral candidate; final disposition is `defer`, activation `false`.

**S2-10.1 gate:** Complete with `defer`. A wide-window implementation was rejected as contract-violating, the strict non-PV implementation was proven inert under the authoritative baseline, and all experimental code/configuration was removed.
"""

todo = replace_once(todo, old_task, new_task, "S2-10.1 task block")
TODO_PATH.write_text(todo, encoding="utf-8")

report = """# S2-10.1 Futility-Pruning Decision and Disposition

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
"""
REPORT_PATH.write_text(report, encoding="utf-8")

SCRIPT_PATH.unlink()
WORKFLOW_PATH.unlink()
