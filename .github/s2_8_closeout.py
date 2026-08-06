from pathlib import Path
import re


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one occurrence, found {count}")
    return text.replace(old, new, 1)


def replace_block(text: str, pattern: str, replacement: str, label: str) -> str:
    updated, count = re.subn(pattern, replacement, text, count=1, flags=re.DOTALL)
    if count != 1:
        raise SystemExit(f"{label}: expected exactly one block, found {count}")
    return updated


closeout = '''# Rust Chess Engine v0.2 — S2-8 Late Move Reductions

**Status:** Complete
**Date:** 2026-08-05
**Disposition:** Standalone candidate rejected
**Activation:** false
**Core implementation SHA:** `6ecc8cce609a11d26dde81a03db38b9284a801f1`
**Evidence-harness SHA:** `12a959756864c01cc82e18d71f109c0eb0938786`
**Selective-depth evidence SHA:** `ba565dea4afc2dcf074520d9cf5b7c55e60c9e6f`
**Exact validation SHA:** `c8d4e835f0946ccd385b32e9a03b62cba6112d4b`
**Permanent validation run:** `31065063892`

## Outcome

S2-8 implemented an isolated, typed, identity-bound Late Move Reductions candidate and evaluated it independently against the authoritative v0.1 full-depth search. The corrected candidate passed the complete correctness, restoration, reproducibility, allocation, x86-64, and native ARM64 gates. It did not satisfy either development strength gate and was fractionally slower in the measured release workload, so standalone activation is rejected.

The implementation remains inactive for possible explicitly identified combination experiments. Production UCI, safe Rust, C ABI, JNI, Android, package version, evaluation weights, authoritative v0.1 policy, and all default entry points remain unchanged.

## Candidate identity and parameters

- Candidate policy identifier: `5332384c4d523031`.
- Candidate policy checksum: `250607d2af491286`.
- Baseline policy identifier/checksum: `5630315f504f4c31` / `0c0769ef9d034770`.
- Baseline evaluation-weight identifier/checksum: `424153454c494e45` / `d2cca7ae10ec6e34`.
- Minimum parent depth: `4`.
- First eligible zero-based move index: `4`, the fifth ordered move.
- Minimum legal-move count: `6`.
- Minimum total piece count: `10`.
- Reduction table: `(depth >= 4, move index >= 4) -> 1 ply`; `(depth >= 7, move index >= 8) -> 2 plies`.
- The selected reduction is bounded so the child retains at least one full search ply.
- The candidate must be selected explicitly through `SearchPolicySet::late_move_reductions_candidate()` and cannot be combined with another unevaluated experimental feature.

## Reduction and verification contract

A move is eligible only when all initial safety conditions hold. LMR does not reduce:

- the first/PV move;
- a transposition-table move;
- a configured killer move;
- captures or promotions;
- moves from an in-check node;
- checking moves;
- low-mobility nodes;
- low-material positions;
- mate-score windows; or
- depths where the reduction would underflow the full search domain.

Every eligible late move is searched at the reduced depth first. A reduced result that does not raise alpha may remain a fail-low result. Every reduced result that raises alpha receives exactly one full-depth verification search before it can affect the exact score, best move, PV, TT bound, or reported result. Reduced fail-highs and full-depth verifications are counted separately, and their totals must match.

There is no baseline-search fallback, neutral-score substitution, swallowed error, or conversion of an unverified speculative result into an exact result. Node, qnode, selective-depth, diagnostic, cancellation, and limit accounting include all reduced and verification attempts.

## Discovered forced-mate defect and permanent repair

The first candidate failed the permanent tactical/endgame parity matrix on:

`4Q2k/8/4K3/8/8/8/8/8 b - - 0 1`

It returned a material score of `-1030` instead of the required mate score `-29994`. This demonstrated that an apparently quiet late move could not safely receive a reduced fail-low in sparse or mate-sensitive search space.

The defect was fixed at the reduction-policy boundary by excluding low-material positions and mate-score windows. The original forced-mate fixture remained unchanged and now passes as a permanent regression. The complete mate-distance, longest-survival, promotion, en-passant, quiet tactical-resource, quiet defensive-resource, low-mobility, zugzwang-sensitive, cancellation, and restoration matrix passed after the repair.

## Correctness and reproducibility evidence

- Deterministic corpus cases: `13`.
- Differing best moves: `0`.
- Total reductions: `29`.
- Reduced fail-highs: `7`.
- Full-depth verification searches: `7`.
- Aggregate checksum: `60faa8a799565fc7`.
- x86-64 evidence generated twice byte-for-byte identically.
- Native ARM64 reproduced the same semantic results and checksums.
- Exact score, mate distance, longest survival, legal PV replay, aspiration recovery, TT behavior, cancellation, node/time limits, and position/history/Zobrist restoration passed.
- Strict Clippy, complete `chess-search` all-target/all-feature tests, evidence-tool tests, release builds, and designated zero-allocation hot-path audit passed.

## Strength disposition

### Fixed-node development

- Protocol: `8` color-swapped opening pairs / `16` games.
- Resource limit: `2,000` nodes per move; maximum `48` plies.
- Candidate wins/draws/losses: `2 / 0 / 2`.
- Unfinished games: `12`.
- Illegal moves, crashes, time forfeits, and infrastructure failures: `0`.
- Mean pair score and lower confidence bound: `0.5`.
- Decision: `rejected_strength`.
- Report checksum: `b0f204ec892fb99d`.

### Clock development

- Protocol: `8` color-swapped opening pairs / `16` games at `10 ms` per move.
- Candidate wins/draws/losses: `2 / 0 / 2`.
- Unfinished games: `12`.
- Illegal moves, crashes, time forfeits, and infrastructure failures: `0`.
- Decision: `rejected_strength`.
- Report checksum: `e837571ccedb820d`.

The symmetric completed-game score and high unfinished-game count do not meet the predeclared fail-closed promotion rule. No production match or activation was run.

## Performance and allocation evidence

### Linux x86-64, seven release samples

- Baseline median: `213,986,824 ns`.
- Candidate median: `214,305,307 ns`.
- Candidate/baseline ratio: `1.001488`, approximately `0.149%` slower.
- Nodes: `40,000 / 40,000`.
- Qnodes: `35,620 / 35,665`.
- Selective depth: `22 / 22`.
- Beta cutoffs: `3,265 / 3,428`.
- First-move beta cutoffs: `2,715 / 2,841`.
- Candidate reductions / reduced fail-highs / verifications: `98 / 38 / 38`.
- Allocation maxima: `42 / 42` calls and `28,912 / 28,912` bytes.
- Baseline/candidate semantic checksums: `38fad5029ca42607` / `18b8988288ea5c8a`.

### Linux ARM64, seven release samples

- Baseline median: `149,653,978 ns`.
- Candidate median: `149,794,342 ns`.
- Candidate/baseline ratio: `1.000938`, approximately `0.094%` slower.
- Nodes, qnodes, selective depth, cutoff counts, LMR diagnostics, allocation maxima, and semantic checksums matched the x86-64 workload.

The candidate increased cutoff counts but did not reduce nodes or elapsed time in the bounded workload. It also introduced no measured allocation regression.

## Permanent validation and artifacts

- Workflow: `.github/workflows/s2-8-lmr.yml`.
- Exact run: `31065063892`.
- x86-64 job: `92501001970`; success.
- Native ARM64 job: `92501001923`; success.
- x86-64 artifact: `8953737384`, `s2-8-lmr-linux-x86-64-c8d4e835f0946ccd385b32e9a03b62cba6112d4b`, ZIP SHA-256 `22844449c56536ae94957726ff5a378511bec99fffbdf2f839a9164e6b0818c0`.
- ARM64 artifact: `8953716636`, `s2-8-lmr-linux-arm64-c8d4e835f0946ccd385b32e9a03b62cba6112d4b`, ZIP SHA-256 `d89efe92c3382b0f291be0dce958ea7aca1ded7b6ac98b3e2024879ab6910224`.
- Toolchain: Rust `1.97.1`, commit `8bab26f4f68e0e26f0bb7960be334d5b520ea452`, LLVM `22.1.6`.

The permanent workflow has read-only repository permission. Generated evidence paths are ignored and no temporary bootstrap, repair, or closure workflow remains in the completed tree.

## Final disposition

S2-8 is complete. The corrected LMR implementation is bounded, verified, tactically protected, deterministic, reproducible, and retained only as inactive controlled infrastructure. Standalone activation is rejected because both development protocols returned `rejected_strength` and measured release performance was fractionally slower on both architectures. The strength program advances to the S2-9 null-move feasibility decision without changing production behavior.
'''
Path("docs/RUST_CHESS_ENGINE_V0_2_S2_8_LMR_2026-08-05.md").write_text(closeout, encoding="utf-8")

tracker_path = Path("docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md")
tracker = tracker_path.read_text(encoding="utf-8")

record = '''## S2-8 implementation record

- Disposition: complete; standalone LMR activation rejected; the corrected typed candidate remains inactive for possible explicitly identified combination experiments.
- Core implementation SHA: `6ecc8cce609a11d26dde81a03db38b9284a801f1`.
- Evidence-harness SHA: `12a959756864c01cc82e18d71f109c0eb0938786`.
- Explicit selective-depth evidence SHA: `ba565dea4afc2dcf074520d9cf5b7c55e60c9e6f`.
- Exact validation SHA: `c8d4e835f0946ccd385b32e9a03b62cba6112d4b`.
- Candidate policy identifier/checksum: `5332384c4d523031` / `250607d2af491286`; baseline remains `5630315f504f4c31` / `0c0769ef9d034770`.
- Parameters: minimum depth `4`; fifth ordered move; at least `6` legal moves and `10` total pieces; reduction table `[(4, 4, 1), (7, 8, 2)]`; reductions retain at least one full child ply.
- Protected: first/PV move, TT move, killers, captures, promotions, in-check nodes, checking moves, low-mobility nodes, low-material positions, mate windows, and underflowing depths.
- Every reduced alpha raise receives exactly one full-depth verification. Deterministic evidence recorded `29` reductions, `7` reduced fail-highs, and `7` verifications across 13 parity cases; zero differing best moves; checksum `60faa8a799565fc7`; repeated x86-64 output was byte-identical and ARM64 semantics matched.
- The first candidate exposed a forced-mate defect on `4Q2k/8/4K3/8/8/8/8/8 b - - 0 1`, returning `-1030` instead of `-29994`. Low-material and mate-window exclusions fixed it; the unchanged fixture is a permanent regression.
- Fixed-node development: 8 pairs / 16 games at 2,000 nodes; candidate W/D/L `2/0/2`, unfinished `12`, all failure categories zero, `rejected_strength`, checksum `b0f204ec892fb99d`.
- Clock development: 8 pairs / 16 games at 10 ms; candidate W/D/L `2/0/2`, unfinished `12`, all failure categories zero, `rejected_strength`, checksum `e837571ccedb820d`.
- Seven-sample x86-64 median ratio `1.001488`; ARM64 ratio `1.000938`; candidate was fractionally slower on both. Nodes remained `40,000`; qnodes `35,620/35,665`; selective depth `22/22`; allocations and bytes were unchanged.
- Exact permanent run `31065063892`: x86-64 job `92501001970`, artifact `8953737384`, digest `22844449c56536ae94957726ff5a378511bec99fffbdf2f839a9164e6b0818c0`; ARM64 job `92501001923`, artifact `8953716636`, digest `d89efe92c3382b0f291be0dce958ea7aca1ded7b6ac98b3e2024879ab6910224`; all gates passed.
- Production UCI, safe Rust facade, C ABI, JNI, Android, package version, evaluation weights, authoritative v0.1 policy, and defaults remain unchanged. No silent fallback, implicit discovery, committed generated evidence, or write-capable permanent workflow remains.

'''
if "## S2-8 implementation record" in tracker:
    raise SystemExit("S2-8 implementation record already exists")
tracker = replace_once(
    tracker,
    "## Program guardrails\n",
    record + "## Program guardrails\n",
    "implementation record insertion",
)
tracker = replace_once(
    tracker,
    "| S2-8 | Late Move Reductions candidate | **Not started** |",
    "| S2-8 | Late Move Reductions candidate | **Complete — standalone rejected; inactive for combinations** |",
    "program summary row",
)

completed_task = '''# Task S2-8: Late Move Reductions candidate — COMPLETE

## S2-8.1 Reduction policy

- [x] Add a versioned inactive LMR policy.
- [x] Define minimum depth `4`, first eligible move index `4`, low-mobility/material guards, and reduction table `[(4, 4, 1), (7, 8, 2)]`.
- [x] Apply initial reductions only to quiet, non-checking, non-promotion late moves.
- [x] Protect TT move, first/PV move, captures, promotions, checks, killers, low-mobility nodes, low-material positions, and mate windows.
- [x] Bound reductions so effective depth retains at least one full child ply and cannot escape the mate domain.

## S2-8.2 Verification

- [x] A reduced search that raises alpha receives the required full-depth verification search.
- [x] Count reductions, reduced fail-highs, and full-depth verification searches independently.
- [x] Require reduced fail-high and verification totals to match exactly.
- [x] Never report or store a reduced speculative result as exact without verification.
- [x] Preserve TT bound/store, fail-soft score, mate normalization, and deterministic equal-score correctness across reduced searches.

## S2-8.3 Targeted correctness

- [x] Quiet tactical-resource fixtures.
- [x] Quiet defensive-resource fixtures.
- [x] Forced-mate and longest-survival fixtures, including the permanent sparse forced-mate regression discovered during implementation.
- [x] Promotion races and en-passant tactics.
- [x] Low-mobility, low-material, and zugzwang-sensitive endings.
- [x] Check-extension and mate-window interaction.
- [x] Cancellation, node/time limits, legal PV replay, and position/history/Zobrist restoration paths.

## S2-8.4 Evidence

- [x] Record nodes, qnodes, elapsed time, selective depth, cutoffs, reductions, reduced fail-highs, verification searches, allocations, and semantic checksums.
- [x] Run deterministic fixed-node development match; result `rejected_strength`.
- [x] Run clock-based development match; result `rejected_strength`.
- [x] Record independent standalone rejection and exact parameters in `docs/RUST_CHESS_ENGINE_V0_2_S2_8_LMR_2026-08-05.md`.
- [x] Keep default inactive and preserve all production adapters/defaults unchanged.

**S2-8 gate:** Complete. LMR is isolated, bounded, fully verified after reduced alpha raises, tactically protected, reproducible on x86-64 and native ARM64, and independently evaluated. Standalone activation is rejected and the candidate remains inactive.

---

# Task S2-9:'''
tracker = replace_block(
    tracker,
    r"# Task S2-8: Late Move Reductions candidate — NOT STARTED\n.*?\n# Task S2-9:",
    completed_task,
    "S2-8 task block",
)
tracker = replace_block(
    tracker,
    r"## Initial next action\n\n.*\Z",
    "## Initial next action\n\nBegin with **S2-9 only**: make the optional null-move pruning feasibility decision before coding. Do not add futility pruning, razoring, late quiet-move pruning, tablebases, or combine rejected candidates until S2-9 has an explicit implement/reject/defer architectural disposition.\n",
    "initial next action",
)
tracker_path.write_text(tracker, encoding="utf-8")

tracker_workflow = '''name: Strength tracker audit

on:
  push:
    branches:
      - master
  pull_request:
    branches:
      - master
  workflow_dispatch:

permissions:
  contents: read

concurrency:
  group: strength-tracker-${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

jobs:
  tracker-audit:
    name: Strength tracker authority and evidence
    runs-on: ubuntu-24.04
    timeout-minutes: 10
    steps:
      - uses: actions/checkout@v4

      - name: Audit TODO authority and inherited closure
        run: bash scripts/task_post_port_review_fix_audit.sh

      - name: Audit search policy and variant identity
        run: bash scripts/task_s2_1_policy_identity_audit.sh

      - name: Audit complete engine-variant validation
        run: bash scripts/task_s2_2_variant_validation_audit.sh

      - name: Audit S2-3 diagnostics and baselines
        run: bash scripts/task_s2_3_baseline_audit.sh

      - name: Audit standalone S2-4 SEE
        run: bash scripts/task_s2_4_see_audit.sh

      - name: Audit S2-5 SEE capture ordering
        run: bash scripts/task_s2_5_see_ordering_audit.sh

      - name: Audit S2-6 quiescence redesign
        run: bash scripts/task_s2_6_quiescence_audit.sh

      - name: Audit S2-7 Principal Variation Search
        run: bash scripts/task_s2_7_pvs_audit.sh

      - name: Audit S2-8 Late Move Reductions
        run: bash scripts/task_s2_8_lmr_audit.sh

      - name: Verify active program progression
        shell: bash
        run: |
          set -euo pipefail
          tracker=docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md
          s2_7_closeout=docs/RUST_CHESS_ENGINE_V0_2_S2_7_PVS_2026-08-05.md
          s2_8_closeout=docs/RUST_CHESS_ENGINE_V0_2_S2_8_LMR_2026-08-05.md
          grep -Fq '| S2-0 | Authority cleanup and exact baseline inspection | **Complete** |' "$tracker"
          grep -Fq '| S2-1 | Versioned search-policy and engine-variant identity | **Complete** |' "$tracker"
          grep -Fq '| S2-2 | Generalized strength-validation infrastructure | **Complete** |' "$tracker"
          grep -Fq '| S2-3 | Baseline strength, diagnostics, and performance capture | **Complete** |' "$tracker"
          grep -Fq '| S2-4 | Correct allocation-free Static Exchange Evaluation | **Complete** |' "$tracker"
          grep -Fq '| S2-5 | SEE capture-ordering candidate | **Complete — standalone rejected; inactive for combinations** |' "$tracker"
          grep -Fq '| S2-6 | Quiescence redesign candidates | **Complete — SEE and delta rejected; inactive** |' "$tracker"
          grep -Fq '| S2-7 | Principal Variation Search candidate | **Complete — standalone rejected; inactive** |' "$tracker"
          grep -Fq '| S2-8 | Late Move Reductions candidate | **Complete — standalone rejected; inactive for combinations** |' "$tracker"
          grep -Fq '| S2-9 | Optional null-move pruning decision/candidate | **Not started** |' "$tracker"
          grep -Fq '## S2-8 implementation record' "$tracker"
          grep -Fq '# Task S2-8: Late Move Reductions candidate — COMPLETE' "$tracker"
          grep -Fq '# Task S2-9: Optional null-move pruning decision/candidate — NOT STARTED' "$tracker"
          grep -Fq 'Begin with **S2-9 only**:' "$tracker"
          grep -Fq '**Status:** Complete' "$s2_7_closeout"
          grep -Fq '**Activation:** false' "$s2_7_closeout"
          grep -Fq '**Status:** Complete' "$s2_8_closeout"
          grep -Fq '**Disposition:** Standalone candidate rejected' "$s2_8_closeout"
          grep -Fq '**Activation:** false' "$s2_8_closeout"
          grep -Fq '31065063892' "$s2_8_closeout"
          grep -Fq 'c8d4e835f0946ccd385b32e9a03b62cba6112d4b' "$s2_8_closeout"
          test "$(sed -n '/# Task S2-8:/,/# Task S2-9:/p' "$tracker" | grep -Fc -- '- [ ]')" -eq 0
          test "$(sed -n '/# Task S2-9:/,/# Task S2-10:/p' "$tracker" | grep -Fc -- '- [ ]')" -gt 0
          if find .github -maxdepth 2 -type f \( -name 's2_8_closeout*.py' -o -name 's2-8-closeout.yml' -o -name 's2_8_*bootstrap*.py' -o -name 's2-8-*bootstrap.yml' -o -name 's2_8_*repair*.py' -o -name 's2-8-*patch.yml' \) -print | grep -q .; then
            echo 'temporary S2-8 helper remains' >&2
            exit 1
          fi
          if find .github -maxdepth 1 -type f -name 's2_7_closure*.py' -print | grep -q .; then
            echo 'temporary S2-7 closure script remains' >&2
            exit 1
          fi
          if find scripts -maxdepth 1 -type f \( -name 'tracker_close.py' -o -name 's2_6_closure.py' \) -print | grep -q .; then
            echo 'temporary tracker closure script remains' >&2
            exit 1
          fi
'''
Path(".github/workflows/tracker-close.yml").write_text(tracker_workflow, encoding="utf-8")

Path(".github/s2_8_closeout.py").unlink()
Path(".github/workflows/s2-8-closeout.yml").unlink()
