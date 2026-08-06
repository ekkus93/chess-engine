from __future__ import annotations

import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRACKER = ROOT / "docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md"
REPORT = ROOT / "docs/RUST_CHESS_ENGINE_V0_2_S2_10_3_LATE_QUIET_MOVE_PRUNING_2026-08-06.md"
LMR_REPORT = ROOT / "docs/RUST_CHESS_ENGINE_V0_2_S2_8_LMR_2026-08-05.md"
POLICY = ROOT / "crates/chess-search/src/search_policy.rs"
SEARCH = ROOT / "crates/chess-search/src/alpha_beta.rs"
ORDERING = ROOT / "crates/chess-search/src/move_ordering.rs"
DIAGNOSTICS = ROOT / "crates/chess-search/src/diagnostics.rs"

STARTING_SHA = "9f0ba7267ceab406a8bb1fa3cb9cc0d0699fe226"


def fail(message: str) -> None:
    raise SystemExit(f"S2-10.3 closure failed: {message}")


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        fail(f"expected exactly one {label}, found {count}")
    return text.replace(old, new, 1)


def require(text: str, needle: str, label: str) -> None:
    if needle not in text:
        fail(f"missing {label}: {needle}")


def forbid(text: str, needle: str, label: str) -> None:
    if needle in text:
        fail(f"unexpected {label}: {needle}")


def current_sha() -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
    ).strip()


def main() -> None:
    if REPORT.exists():
        fail(f"report already exists: {REPORT.relative_to(ROOT)}")

    tracker = TRACKER.read_text(encoding="utf-8")
    lmr_report = LMR_REPORT.read_text(encoding="utf-8")
    policy = POLICY.read_text(encoding="utf-8")
    search = SEARCH.read_text(encoding="utf-8")
    ordering = ORDERING.read_text(encoding="utf-8")
    diagnostics = DIAGNOSTICS.read_text(encoding="utf-8")

    # Fail closed unless the exact prerequisite evidence and current inactive
    # architecture are still present.
    require(lmr_report, "**Disposition:** Standalone candidate rejected", "LMR rejection")
    require(lmr_report, "Decision: `rejected_strength`.", "LMR fixed-node disposition")
    if lmr_report.count("Decision: `rejected_strength`.") != 2:
        fail("LMR report no longer records two rejected development protocols")
    require(lmr_report, "Candidate/baseline ratio: `1.001488`", "x86-64 timing ratio")
    require(lmr_report, "Candidate/baseline ratio: `1.000153`", "ARM64 timing ratio")
    require(lmr_report, "Nodes: `40,000 / 40,000`", "unchanged bounded node count")
    require(lmr_report, "Total reductions: `29`", "correctness-corpus LMR exercise")
    require(lmr_report, "Reduced fail-highs: `7`", "LMR verification evidence")
    require(lmr_report, "returned a material score of `-1030` instead of the required mate score `-29994`", "quiet forced-mate defect")
    require(policy, "LateMovePruning", "reserved late-move-pruning feature bit")
    forbid(policy, "LATE_MOVE_PRUNING_SEARCH_POLICY_ID", "implemented LMP policy identity")
    forbid(search, "late_move_pruning", "late-move-pruning search branch")
    require(ordering, "const HISTORY_SCORE_MAXIMUM: u32 = 1_000_000;", "history cap")
    forbid(ordering, "STRONG_HISTORY", "calibrated strong-history threshold")
    require(diagnostics, "LateMovePrunes", "reserved late-move-prune diagnostics")

    old_summary = (
        "| S2-10 | Optional frontier and quiet-move pruning candidates | "
        "**In progress — S2-10.1 and S2-10.2 deferred; S2-10.3 not started** |"
    )
    new_summary = (
        "| S2-10 | Optional frontier and quiet-move pruning candidates | "
        "**Complete — S2-10.1, S2-10.2, and S2-10.3 deferred; inactive** |"
    )
    tracker = replace_once(tracker, old_summary, new_summary, "S2-10 summary row")
    tracker = replace_once(
        tracker,
        "# Task S2-10: Optional frontier and quiet-move pruning candidates — IN PROGRESS",
        "# Task S2-10: Optional frontier and quiet-move pruning candidates — COMPLETE",
        "S2-10 task heading",
    )

    old_section = """## S2-10.3 Late quiet-move pruning

- [ ] Evaluate only after LMR evidence.
- [ ] Protect TT moves, killers, strong-history moves, checks, promotions, and low-mobility nodes.
- [ ] Define move-count/depth thresholds explicitly.
- [ ] Add quiet strategic/defensive regressions.
- [ ] Record independent disposition.

**S2-10 gate:** Every frontier/selectivity candidate is isolated, bounded, and accepted/rejected/deferred independently.
"""
    new_section = """## S2-10.3 Late quiet-move pruning — COMPLETE (DEFERRED)

- [x] Evaluate only after LMR evidence. The corrected LMR candidate passed its correctness matrix but returned `rejected_strength` in both development protocols, was fractionally slower on x86-64 and ARM64, and did not reduce the bounded workload's main-node count. Its discovered sparse forced-mate regression also proves that a late quiet move cannot be omitted safely from move index alone.
- [x] Protect TT moves, killers, strong-history moves, checks, promotions, and low-mobility nodes. No pruning candidate was implemented. TT, killer, check, promotion, and mobility guards exist in the LMR infrastructure, but the search-local history table has no calibrated/versioned strong-history threshold suitable for a pruning proof.
- [x] Define move-count/depth thresholds explicitly. No thresholds were adopted: inventing depth, move-count, or history cutoffs without supporting node/resource evidence would create an unsafe policy. Any future candidate must version and bound every threshold before implementation.
- [x] Add quiet strategic/defensive regressions. No behaviorally distinct candidate reached implementation. The LMR quiet-resource, quiet-defense, mate-distance, low-mobility, low-material, promotion, en-passant, cancellation, and restoration corpus was reviewed as prerequisite evidence and remains mandatory for reconsideration.
- [x] Record independent disposition. `deferred_insufficient_evidence`, activation `false`; no candidate correctness matrix or strength match was run because no defensible pruning policy passed the design gate.

**S2-10 gate:** Complete. Futility, razoring, and late quiet-move pruning are independently deferred and inactive. No frontier/selectivity candidate changed production policy, search semantics, diagnostics, evaluation, adapters, package identity, or defaults.
"""
    tracker = replace_once(tracker, old_section, new_section, "S2-10.3 section")
    TRACKER.write_text(tracker, encoding="utf-8")

    staging_sha = current_sha()
    report = f"""# Rust Chess Engine v0.2 S2-10.3 Late Quiet-Move Pruning Decision

**Status:** Complete — deferred
**Date:** 2026-08-06
**Disposition:** `deferred_insufficient_evidence`
**Activation:** `false`
**Starting master SHA:** `{STARTING_SHA}`
**Decision staging SHA:** `{staging_sha}`
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
"""
    REPORT.write_text(report, encoding="utf-8")

    # Verify the resulting documentary closure before the workflow commits it.
    updated = TRACKER.read_text(encoding="utf-8")
    require(updated, new_summary, "closed S2-10 summary")
    require(updated, "# Task S2-10: Optional frontier and quiet-move pruning candidates — COMPLETE", "closed task heading")
    require(updated, "## S2-10.3 Late quiet-move pruning — COMPLETE (DEFERRED)", "closed subsection heading")
    section = updated.split("## S2-10.3 ", 1)[1].split("# Task S2-11:", 1)[0]
    if section.count("- [x]") != 5 or "- [ ]" in section:
        fail("S2-10.3 requirements are not exactly five completed items")
    require(report, "**Disposition:** `deferred_insufficient_evidence`", "report disposition")
    require(report, "**Activation:** `false`", "report inactive state")


if __name__ == "__main__":
    main()
