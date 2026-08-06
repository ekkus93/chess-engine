# Rust Chess Engine v0.2 — S2-8 Late Move Reductions

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

- Baseline median: `173,435,085 ns`.
- Candidate median: `173,461,706 ns`.
- Candidate/baseline ratio: `1.000153`, approximately `0.015%` slower.
- Nodes, qnodes, selective depth, cutoff counts, LMR diagnostics, allocation maxima, and semantic checksums matched the x86-64 workload.

The candidate increased cutoff counts but did not reduce nodes or elapsed time in the bounded workload. It also introduced no measured allocation regression.

## Permanent validation and artifacts

- Workflow: `.github/workflows/s2-8-lmr.yml`.
- Exact run: `31065063892`.
- x86-64 job: `92501001970`; success.
- Native ARM64 job: `92501001923`; success.
- x86-64 artifact: `8953737384`, `s2-8-lmr-linux-x86-64-c8d4e835f0946ccd385b32e9a03b62cba6112d4b`, ZIP SHA-256 `22844449c56536ae94957726ff5a378511bec99fffbdf2f839a9164e6b0818c0`.
- ARM64 artifact: `8953681761`, `s2-8-lmr-linux-arm64-c8d4e835f0946ccd385b32e9a03b62cba6112d4b`, ZIP SHA-256 `01c0563109c18ec0cb7a3204452f454cac66e897ee05646c592edfd1dee5be85`.
- Toolchain: Rust `1.97.1`, commit `8bab26f4f68e0e26f0bb7960be334d5b520ea452`, LLVM `22.1.6`.

The permanent workflow has read-only repository permission. Generated evidence paths are ignored and no temporary bootstrap, repair, or closure workflow remains in the completed tree.

## Final disposition

S2-8 is complete. The corrected LMR implementation is bounded, verified, tactically protected, deterministic, reproducible, and retained only as inactive controlled infrastructure. Standalone activation is rejected because both development protocols returned `rejected_strength` and measured release performance was fractionally slower on both architectures. The strength program advances to the S2-9 null-move feasibility decision without changing production behavior.
