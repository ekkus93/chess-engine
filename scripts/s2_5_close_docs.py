#!/usr/bin/env python3
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
TRACKER = ROOT / "docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md"
REPORT = ROOT / "docs/RUST_CHESS_ENGINE_V0_2_S2_5_SEE_ORDERING_2026-08-05.md"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one exact match, found {count}")
    return text.replace(old, new, 1)


tracker = TRACKER.read_text()
tracker = replace_once(
    tracker,
    "| S2-5 | SEE capture-ordering candidate | **Not started** |",
    "| S2-5 | SEE capture-ordering candidate | **Complete — standalone rejected; inactive for combinations** |",
    "program summary",
)

record = r'''## S2-5 implementation record

- Disposition: complete; the standalone SEE capture-ordering candidate is **rejected for activation** because both development comparisons returned `rejected_strength` and the measured fixed-node search path was slower on x86-64 and ARM64. The implementation remains inactive and may be reused only as an explicitly identified component in later combination experiments.
- Starting `master` SHA: `5ccf5704ec1e1c94e03918b079be4abc4f37b038`.
- Core implementation SHA: `95d1917d986bc3f9ec808ba0f5f5a1a63619e5aa`.
- Permanent evidence implementation SHA: `c17791c4a8e4ddfdd150cd0b77720fa48dc53cb4`.
- Exact validated candidate SHA: `f5e4b1e1e630e5708444f9192a1436faac84090c`.
- Candidate policy identifier/checksum: `5332355345454f31` / `96fd6e0c744e326a`; authoritative v0.1 policy remains `5630315f504f4c31` / `0c0769ef9d034770`.
- Ordering contract: TT move first; previous-PV and promotion precedence preserved; captures ordered `winning > equal > losing`, then signed SEE, existing MVV-LVA, and packed move identity; quiet killer/history ordering unchanged; no legal move is removed.
- SEE is computed once per capture in a fixed-capacity construction pass. Temporary sort keys are discarded before recursive search retains the ordered legal-token list, permanently fixing the stack-overflow defect discovered by the first parity run.
- Contradictory internal SEE state propagates as typed `StaticExchangeError` / `AlphaBetaSearchError::StaticExchange`; there is no neutral score, MVV-LVA substitution, ignored error, or silent fallback.
- Exact diagnostics count SEE calls and winning/equal/losing classifications. Calls equal the sum of classes; `see_prunes` and `quiescence_see_prunes` remain zero.
- Frozen 13-case tactical parity: every exact score, mate distance, completed depth, best move, legal PV replay, root position, history, and Zobrist invariant matched; `differing_best_moves=0`, total SEE calls `48186`, aggregate checksum `950f8cb49057540f`, `activated=false`.
- Fixed-node development comparison: 8 pairs / 16 games at 2,000 nodes; candidate wins `2`, losses `2`, unfinished `12`; mean/lower bound `0.5`; zero illegal moves, crashes, time forfeits, or infrastructure failures; `rejected_strength`; checksum `1750c9ee353388aa`; `activated=false`.
- Clock development comparison: 8 pairs / 16 games at 10 ms; candidate wins `1`, losses `1`, unfinished `14`; mean `0.5`; zero illegal moves, crashes, time forfeits, or infrastructure failures; `rejected_strength`; checksum `6a5bdb753e670799`; `activated=false`.
- Seven-sample x86-64 distribution: baseline median `213586975 ns`, candidate `225341022 ns`, ratio `1.055032`; nodes `40000/40000`, qnodes `35620/35496`, beta cutoffs `3265/3386`, first-move cutoffs `2715/2894`.
- Seven-sample ARM64 distribution: baseline median `173970839 ns`, candidate `183633660 ns`, ratio `1.055543`; the same deterministic node, qnode, cutoff, and SEE-class counts were reproduced.
- End-to-end iterative-deepening allocation evidence is reported honestly: baseline/candidate maxima `42/44` calls and `27888/27906` bytes, a delta of `+2` calls / `+18` bytes. The separate permanent designated-hot-path audit remained zero-allocation on both architectures.
- Exact focused run `31038429453`: x86-64 job `92416527069`, artifact `8943661186`, digest `cea5bc9b09e24251ba2ff1d06028e853d1ddc9060d9f0b2f38f801c036050d64`; ARM64 job `92416526991`, artifact `8943638318`, digest `2e6392e08481b014c246070f6911cc8b64e9f4e6e29edda9b9a2f30b135dfbb7`; all focused correctness, deterministic evidence, strength, performance, allocation, and audit gates passed.
- Exact Rust CI run `31038429514`: x86-64 workspace-quality job `92416444304` and native ARM64 job `92416444199`; all audits, lockfile/metadata checks, formatting, strict Clippy, all-target/all-feature tests, release perft, rustdoc, debug/release builds, UCI smoke, and differential oracle passed.
- Exact robustness run `31038429455`, performance run `31038429707`, and Android/JNI run `31038429765` all passed on the same validation SHA.
- The Task 14.5 exclusion audit was repaired at source so it recognizes interleaved test-only helpers and the explicit SEE ordering fields while ignoring comments/string literals during lexical strategic-evaluator checks. No exclusion was weakened.
- Production UCI, safe Rust, C ABI, JNI, Android, package version, weights, v0.1 policy, and defaults remain unchanged. No first-party lint suppression, ignored failure, downgraded gate, implicit discovery, temporary helper, or write-capable permanent workflow remains in the validated candidate tree.

'''
tracker = replace_once(
    tracker,
    "## Program guardrails\n",
    record + "## Program guardrails\n",
    "S2-5 implementation record insertion",
)

complete_block = r'''# Task S2-5: SEE capture-ordering candidate — COMPLETE

## S2-5.1 Define the candidate

- [x] Add an explicit inactive policy flag and parameter set.
- [x] Keep TT-move priority first.
- [x] Preserve promotion ordering.
- [x] Define exact capture classes, such as winning/equal/losing, using SEE.
- [x] Define deterministic tie-breaks inside each class.
- [x] Keep the candidate ordering-only; do not prune moves here.

## S2-5.2 Integrate safely

- [x] Compute SEE once per capture per ordering pass where practical.
- [x] Avoid heap allocation and repeated board reconstruction.
- [x] Integrate in both main-search tactical ordering and quiescence ordering where specified.
- [x] Preserve legal move sets exactly.
- [x] Propagate SEE failure explicitly; do not silently substitute MVV-LVA.

## S2-5.3 Add diagnostics

- [x] Count SEE calls.
- [x] Count winning/equal/losing classifications.
- [x] Count ordering cutoffs and first-move cutoffs.
- [x] Record deterministic diagnostics checksum.
- [x] Keep pruning counters zero.

## S2-5.4 Correctness validation

- [x] Exact root-score parity versus baseline on the frozen corpus.
- [x] Mate-distance parity.
- [x] Legal-PV replay.
- [x] Position/history/Zobrist restoration.
- [x] Deterministic repeated-run parity.
- [x] Baseline behavior remains unchanged when the flag is off.

## S2-5.5 Performance and allocation validation

- [x] Compare nodes and qnodes at fixed depth/nodes.
- [x] Compare first-move cutoffs and cutoff distribution.
- [x] Measure x86-64 and ARM64 timing distributions.
- [x] Audit allocation behavior in the measured search path.
- [x] Reject the candidate if SEE cost dominates ordering gain without strength benefit.

## S2-5.6 Strength validation

- [x] Run deterministic fixed-node development comparison.
- [x] Run clock-based development comparison where release relevance warrants it.
- [x] Record unfinished games and all failure categories separately.
- [x] Record one disposition: accept independently, reject, or retain only for later combination experiments.

**S2-5 gate:** Complete. The ordering implementation is exact, typed, deterministic, no-prune, and inactive. Standalone activation is rejected; the controlled candidate is retained only for later combination experiments.

---

# Task S2-6'''
pattern = re.compile(
    r"# Task S2-5: SEE capture-ordering candidate — NOT STARTED\n.*?\n---\n\n# Task S2-6",
    flags=re.DOTALL,
)
tracker, count = pattern.subn(complete_block, tracker, count=1)
if count != 1:
    raise SystemExit(f"S2-5 task block: expected one replacement, found {count}")

if tracker.count("## S2-5 implementation record") != 1:
    raise SystemExit("S2-5 implementation record count is not one")
if "# Task S2-5: SEE capture-ordering candidate — NOT STARTED" in tracker:
    raise SystemExit("stale S2-5 NOT STARTED heading remains")
section = tracker.split("# Task S2-5:", 1)[1].split("# Task S2-6", 1)[0]
if "- [ ]" in section:
    raise SystemExit("unchecked S2-5 item remains")
TRACKER.write_text(tracker)

REPORT.write_text(r'''# Rust Chess Engine v0.2 S2-5 SEE Capture Ordering

**Status:** Complete; standalone candidate rejected for activation and retained inactive for later combination experiments  
**Task:** S2-5  
**Starting master:** `5ccf5704ec1e1c94e03918b079be4abc4f37b038`  
**Core implementation:** `95d1917d986bc3f9ec808ba0f5f5a1a63619e5aa`  
**Permanent evidence implementation:** `c17791c4a8e4ddfdd150cd0b77720fa48dc53cb4`  
**Exact validated candidate:** `f5e4b1e1e630e5708444f9192a1436faac84090c`

## Final disposition

The standalone S2-5 candidate is **rejected for activation**. It preserved correctness and improved several ordering diagnostics, but both development match protocols returned `rejected_strength`, while seven-sample fixed-node timing was approximately 5.5% slower on both x86-64 and ARM64. The implementation remains available only through the explicit controlled policy identity for possible later combination experiments. Production defaults remain unchanged and `activated=false` in every report.

## Candidate boundary

S2-5 integrates the S2-4 Static Exchange Evaluation primitive into main-search and quiescence capture ordering only. It does not prune, reduce, extend, or omit a move. The production v0.1 policy remains the default for UCI, safe Rust, C ABI, JNI, and Android entry points.

The candidate is available only through `SearchPolicySet::see_capture_ordering_candidate()`. Its policy identifier/checksum is `5332355345454f31` / `96fd6e0c744e326a`; the authoritative v0.1 policy remains `5630315f504f4c31` / `0c0769ef9d034770`.

## Ordering contract

1. A valid transposition-table move remains first.
2. Previous-PV and promotion precedence remains unchanged.
3. Non-promotion captures are classified `winning > equal > losing`.
4. Captures in one class use signed SEE value, then existing MVV-LVA terms, then packed move identity as deterministic ties.
5. Quiet killer/history ordering is unchanged.
6. Every legal move remains in the ordered list.

SEE is calculated once per capture in the fixed-capacity ordering pass. The recursively retained move list contains only legal tokens and a bounded diagnostic summary; temporary sort keys are dropped before recursive search begins. This design is permanently guarded after the initial implementation exposed and fixed a recursive test-stack overflow.

## Failure model and diagnostics

The ordering pass returns the existing typed `StaticExchangeError`. Alpha-beta exposes it as `AlphaBetaSearchError::StaticExchange`, and quiescence propagates the same error. Contradictory internal move state is never converted to MVV-LVA, a neutral SEE value, or an unvalidated fallback.

The candidate records SEE calls plus winning, equal, and losing classifications. Calls must equal the sum of the three classes. `see_prunes` and `quiescence_see_prunes` remain zero.

## Exact correctness evidence

The frozen 13-case tactical corpus produced exact baseline/candidate score, mate-distance, completed-depth, best-move, legal-PV, root-position, history, and Zobrist parity. All 13 best moves matched; total SEE calls were `48186`; aggregate checksum was `950f8cb49057540f`; no move was pruned; `activated=false`.

## Strength evidence

The 8-pair fixed-node development comparison at 2,000 nodes recorded 2 wins, 2 losses, and 12 unfinished games. Mean and lower confidence bound were `0.5`; decision `rejected_strength`; checksum `1750c9ee353388aa`.

The 8-pair clock comparison at 10 ms recorded 1 win, 1 loss, and 14 unfinished games. Mean was `0.5`; decision `rejected_strength`; checksum `6a5bdb753e670799`.

Both reports recorded zero illegal moves, crashes, time forfeits, and infrastructure failures, and both retained `activated=false`.

## Performance and allocation evidence

On x86-64, seven samples measured baseline/candidate medians of `213586975 ns` / `225341022 ns`, ratio `1.055032`. On ARM64, medians were `173970839 ns` / `183633660 ns`, ratio `1.055543`.

The deterministic 40,000-node aggregate changed qnodes from `35620` to `35496`, beta cutoffs from `3265` to `3386`, and first-move cutoffs from `2715` to `2894`. Candidate SEE classifications were `21138` winning, `1648` equal, and `13727` losing.

The broad iterative-deepening measurement reported baseline/candidate maxima of `42/44` allocation calls and `27888/27906` bytes. Those are recorded as an explicit `+2` call / `+18` byte delta rather than mislabeled as zero-allocation. The repository's separate permanent designated-hot-path allocation audit passed with zero allocations on both architectures.

## Validation record

Focused run `31038429453` passed on the exact validated candidate SHA:

- x86-64 job `92416527069`; artifact `8943661186`; digest `cea5bc9b09e24251ba2ff1d06028e853d1ddc9060d9f0b2f38f801c036050d64`;
- ARM64 job `92416526991`; artifact `8943638318`; digest `2e6392e08481b014c246070f6911cc8b64e9f4e6e29edda9b9a2f30b135dfbb7`.

Rust CI run `31038429514`, robustness run `31038429455`, performance run `31038429707`, and Android/JNI run `31038429765` all passed on the same SHA. No lint suppression, ignored failure, downgraded gate, silent fallback, temporary helper, or write-capable permanent workflow remains in the validated candidate tree.
''')

print("S2-5 tracker and report reconciled")
