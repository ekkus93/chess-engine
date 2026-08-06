from pathlib import Path
import re

TRACKER = Path('docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md')
AUDIT = Path('.github/workflows/tracker-close.yml')
REPORT = Path('docs/RUST_CHESS_ENGINE_V0_2_S2_11_PROFILING_2026-08-06.md')
BENCH = Path('benchmarks/s2-11')


def one(text, old, new, label):
    count = text.count(old)
    if count != 1:
        raise SystemExit(f'{label}: expected one match, found {count}')
    return text.replace(old, new, 1)

section = '''# Task S2-11: Fresh profiling and measured hot-path decisions — COMPLETE

## S2-11.1 Reprofile — COMPLETE

- [x] Run Callgrind/profile-perft after current candidate set. Exact Kiwipete depth-four workload completed at `4,085,603` nodes on x86-64 and native ARM64.
- [x] Run profile-search after current candidate set. Exact fixed-node workload completed at `250,000` main nodes, `242,711` qnodes, and depth `4` on both architectures.
- [x] Capture x86-64 and native ARM64 performance distributions. Seven-sample matched baseline/candidate distributions were preserved for both architectures.
- [x] Capture Android/JNI metrics if integration code or hot paths changed. The exact-head Android/JNI artifact was preserved; the accepted change is inside the shared Rust attack primitive and does not alter JNI integration semantics.
- [x] Preserve old artifacts and exact provenance. Baseline, Callgrind, rejected portable-candidate, accepted final-dispatch, and Android artifact identifiers/digests are recorded in `benchmarks/s2-11/artifact-manifest.tsv`.

## S2-11.2 Decision: direct legal generation — COMPLETE (DEFERRED)

- [x] Compare current legal-generation cost and search share. Move generation is material, but the profile does not isolate avoidable legality probes from mandatory make/unmake and attack work strongly enough to justify a rewrite.
- [x] Decide `implement`, `reject`, or `defer`. Disposition: `defer_pending_legality_probe_instrumentation`.
- [x] If implemented, retain old legal generation as a test oracle. No implementation was started; the existing generator remains authoritative and is required as the future oracle.
- [x] Require exhaustive move-set equivalence, perft, differential, property, fuzz, and restoration evidence before activation. These remain mandatory reconsideration gates.
- [x] Keep fail-loud internal contradiction coverage. No behavior or error contract changed.

## S2-11.3 Decision: sliding attacks — COMPLETE (ACCEPTED ARCHITECTURE DISPATCH)

- [x] Re-evaluate measured cost. Baseline Callgrind showed sliding attacks at approximately `24.54%` of x86-64 perft instructions and `16.64%` of x86-64 search instructions, versus approximately `12.09%` and `8.38%` on ARM64.
- [x] Decide `implement`, `reject`, or `defer`. The portable ray-table candidate was `rejected_cross_architecture`; the explicit x86-64 ray-table/non-x86 step-walk dispatch was accepted.
- [x] Reject speculative magic/PEXT/table rewrites without architecture evidence. No magic bitboards, PEXT dependency, runtime CPU probing, or silent fallback was added.
- [x] Preserve exhaustive attack-oracle tests for any change. Every source square and relevant blocker subset is compared with the independent step-walk oracle; exact perft/search diagnostics, allocations, and semantic checksums remain unchanged.

## S2-11.4 Decision: incremental evaluation — COMPLETE (DEFERRED)

- [x] Re-evaluate evaluation share after search changes. Evaluation accounted for approximately `4.79%` of x86-64 search instructions and `3.27%` on ARM64.
- [x] Decide whether incremental evaluation is justified. Disposition: `defer_low_profile_share`; updating state on every make/unmake is not justified by the measured share.
- [x] If implemented, keep full recomputation as a test oracle and require exact parity after every make/unmake path. No implementation was started; these remain mandatory reconsideration gates.

## S2-11.5 Decision: TT/layout/allocation work — COMPLETE

- [x] Reprofile TT replacement/packing, move-list behavior, and allocation. TT probe/store was negligible, hot-path allocation remained zero, while move ordering and copy/layout costs remained measurable.
- [x] Decide separately on TT replacement, custom allocation, and layout changes. TT replacement/packing: `reject_not_hot`; custom allocation: `reject_zero_allocation_path`; move-list/layout: `defer_requires_isolated_candidate`.
- [x] Preserve zero-allocation hot-path guarantees and exact semantics. Allocation audit rows and semantic checksums are identical between baseline and accepted candidate on both architectures.

## S2-11.6 Reference discipline — COMPLETE

- [x] Do not overwrite old references. Existing benchmark references were left unchanged.
- [x] Do not update budgets automatically. No performance budget or threshold was rewritten.
- [x] Update semantic checksums only for intentional semantic changes. Attack sets, perft, search diagnostics, and committed semantic checksums were unchanged because the candidate is behaviorally equivalent.
- [x] Preserve last-known-green and candidate evidence separately. Baseline, rejected portable candidate, and accepted architecture-dispatch evidence have distinct commits, runs, artifact IDs, and digests.

**S2-11 gate:** Complete. Fresh cross-architecture profiling produced independent decisions. Direct legal generation, incremental evaluation, and move-list/layout work are deferred; TT replacement and custom allocation are rejected under the current profile. The portable ray-table candidate was rejected after ARM64 representative-workload regressions. The accepted implementation uses a compile-time x86-64 ray-table path and preserves the original step-walk path on non-x86 architectures, with exhaustive oracle equivalence, exact deterministic workloads, zero-allocation parity, strong x86-64 gains, and ARM64 parity.

---

'''
assert section.count('- [x]') == 24 and '- [ ]' not in section

tracker = TRACKER.read_text()
tracker = one(tracker,
    '| S2-11 | Fresh profiling and measured hot-path decisions | **Not started** |',
    '| S2-11 | Fresh profiling and measured hot-path decisions | **Complete — x86-64 sliding dispatch accepted; non-x86 baseline preserved** |',
    'program summary')
updated, count = re.subn(r'(?ms)^# Task S2-11:.*?(?=^# Task S2-12:)', section, tracker)
if count != 1:
    raise SystemExit(f'S2-11 section: expected one match, found {count}')
TRACKER.write_text(updated)

