# Rust Chess Engine v0.2 — S2-7 Principal Variation Search

**Status:** Complete
**Date:** 2026-08-05
**Disposition:** Standalone candidate rejected
**Activation:** false
**Core implementation SHA:** `c5ee43810355deaef062c1f7903bc410df2d883e`
**Evidence-harness SHA:** `06c20e219ad54227ee9c9ff4b7e43df2ee6d560d`
**Exact validation SHA:** `a6bd183065e77605c55459e750ac0ea2ffbd9dd3`
**Permanent validation run:** `31059515279`

## Outcome

S2-7 implemented a typed, identity-bound Principal Variation Search candidate and evaluated it independently against the authoritative full-window v0.1 search. Correctness, reproducibility, restoration, limit behavior, and both architecture jobs passed. The candidate did not satisfy the standalone strength gate and was slightly slower in the bounded release benchmark, so it remains inactive and is rejected for standalone activation.

No production default, public convenience search path, UCI option, safe Rust facade, C ABI, JNI surface, Android behavior, package version, evaluation weight, or authoritative v0.1 policy changed.

## Search contract

- The first ordered move is searched with the node's full alpha-beta window.
- Every later move is first searched with the one-centipawn child window `[-alpha - 1, -alpha]`.
- A null-window result that strictly improves alpha without reaching beta is re-searched with the full child window before it may establish an exact value.
- Null-window fail-low results cannot replace an equal earlier best move; fail-high results retain ordinary beta-cutoff semantics.
- The narrow and full-window attempts both contribute to nodes, qnodes, selective depth, diagnostics, cancellation, and limit accounting.
- TT probing, mate-score normalization, fail-soft propagation, bound classification, deterministic strict-greater replacement, and legal PV extraction remain shared with the baseline search.
- An unrepresentable null window returns the typed `PvsWindowOutOfRange` error. There is no baseline-search, neutral-score, disabled-feature, or swallowed-error fallback.

## Identity and activation boundary

- Candidate policy identifier: `5332375056533031`.
- Candidate policy checksum: `ef730d158002ccfa`.
- Baseline policy identifier: `5630315f504f4c31`.
- Baseline policy checksum: `0c0769ef9d034770`.
- Baseline evaluation-weight identifier/checksum: `424153454c494e45` / `d2cca7ae10ec6e34`.
- Controlled callers select the candidate only through `SearchPolicySet::principal_variation_search_candidate()`.
- Existing production entry points continue to select `SearchPolicy::V0_1`.
- Candidate and baseline validation use separate caller-owned transposition tables.
- Every emitted report records `activated=false`.

## Correctness and reproducibility evidence

The deterministic parity corpus ran twice byte-for-byte identically on x86-64 and once natively on ARM64.

- Corpus cases: `13`.
- Differing best moves: `0`.
- PVS zero-window searches: `62,133`.
- PVS full-window re-searches: `310`.
- Re-search rate: approximately `0.499%` of zero-window searches.
- Parity aggregate checksum: `aeee18b6a927f146`.
- Exact score, completed depth, best move, mate distance, longest survival, legal PV replay, aspiration recovery, node-limited cancellation, position/history/Zobrist restoration, and diagnostic overflow behavior passed.
- The complete `chess-search` all-target/all-feature suite passed on x86-64 and native ARM64.
- Formatting, strict Clippy, the fail-closed S2-7 source audit, evidence-tool tests, release builds, and zero-allocation hot-path audit passed.

## Strength disposition

### Fixed-node development

- Protocol: `8` color-swapped opening pairs, `16` games, `2,000` nodes per move, maximum `48` plies.
- Candidate wins/draws/losses: `2 / 0 / 0`.
- Unfinished games: `14`.
- Illegal moves, crashes, time forfeits, and infrastructure failures: `0`.
- Report checksum: `b05aa8e4b464ee2f`.
- Decision: `rejected_strength`.

### Clock development

- Protocol: `8` pairs at `10 ms` per move.
- Candidate wins/draws/losses: `1 / 0 / 0`.
- Unfinished games: `15`.
- Illegal moves, crashes, time forfeits, and infrastructure failures: `0`.
- Report checksum: `84bb4b1a050370f3`.
- Decision: `rejected_strength`.

The favorable completed-game counts do not override the predeclared fail-closed decision rule or the high unfinished-game fraction. No production match or activation was run.

## Performance evidence

### Linux x86-64, seven release samples

- Baseline median: `215,076,241 ns`.
- Candidate median: `217,238,165 ns`.
- Candidate/baseline median ratio: `1.010052` — approximately `1.005%` slower.
- Nodes: `40,000 / 40,000` baseline/candidate.
- Qnodes: `35,620 / 35,176` — approximately `1.246%` fewer candidate qnodes.
- Beta cutoffs: `3,265 / 3,533`.
- First-move beta cutoffs: `2,715 / 2,967`.
- Candidate zero-window searches/re-searches: `12,833 / 60`.

### Linux ARM64, seven release samples

- Baseline median: `150,237,915 ns`.
- Candidate median: `152,367,207 ns`.
- Candidate/baseline median ratio: `1.014173` — approximately `1.417%` slower.
- Node, qnode, cutoff, PVS-counter, and semantic-checksum results matched the x86-64 workload.

The candidate reduced qnodes and increased cutoffs but did not convert that work reduction into elapsed-time improvement on either architecture.

## Permanent validation and artifacts

- Workflow: `.github/workflows/s2-7-pvs.yml`.
- Exact run: `31059515279`.
- x86-64 job: `92484209606`; success.
- Native ARM64 job: `92484209677`; success.
- x86-64 artifact: `8951692759`, `s2-7-pvs-linux-x86-64-a6bd183065e77605c55459e750ac0ea2ffbd9dd3`, ZIP SHA-256 `cbef3feb8816de99899b66fa29d68c047e94e22b9015607a7a7c0553993d08f4`.
- ARM64 artifact: `8951682899`, `s2-7-pvs-linux-arm64-a6bd183065e77605c55459e750ac0ea2ffbd9dd3`, ZIP SHA-256 `2295ec2fe5a024d48b336f00dc2b39b6216f7be8fd05cacbcc4c99de1df369cb`.
- Exact-head master-validation report run: `31059979127`; success.

Generated evidence directories are ignored and are not committed. The permanent workflow has read-only repository permissions and cannot activate or rewrite the candidate.

## Final disposition

S2-7 is complete. The implementation is exact, fail-loud, deterministic, reproducible, independently measurable, and retained as inactive controlled infrastructure. Standalone activation is rejected because the development strength protocol returned `rejected_strength` and the release benchmark was slower on both measured architectures. The program advances to S2-8 without changing production behavior.
