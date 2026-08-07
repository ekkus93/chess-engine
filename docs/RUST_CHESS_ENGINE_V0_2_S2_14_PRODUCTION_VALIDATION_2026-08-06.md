# Rust Chess Engine v0.2 — S2-14 Production Candidate Validation

**Status:** Complete — candidate rejected
**Task:** S2-14
**Disposition:** `rejected_strength`
**Activation:** `false`
**Frozen candidate source SHA:** `21406b5e92b6bd42a3a902591dddae22c9b3f16f`
**Selected candidate:** standalone Principal Variation Search (PVS)
**Authoritative production policy after disposition:** v0.1 baseline

## Executive result

S2-14 is complete. The frozen standalone PVS candidate passed the complete exact-SHA correctness, robustness, adapter, allocation, and architecture-specific performance preflight, then failed the project strength rule independently in both required 1,000-pair production protocols. The result is `rejected_strength`; PVS remains inactive and the authoritative v0.1 production policy remains unchanged.

The GitHub Actions workflow itself completed successfully because the reports were generated, strictly validated, checksummed, and preserved. Workflow success does not mean candidate acceptance. Both report decisions are explicitly `rejected_strength`.

No threshold was relaxed, no report was manually reinterpreted, no failed game was converted into a chess result, and no activation/default/package/API/ABI/JNI change was made.

## Frozen identity and protocol

- Source SHA: `21406b5e92b6bd42a3a902591dddae22c9b3f16f`.
- Candidate policy identifier/checksum: `5332375056533031` / `ef730d158002ccfa`.
- Baseline policy identifier/checksum: `5630315f504f4c31` / `0c0769ef9d034770`.
- Evaluation-weight identifier/checksum: `424153454c494e45` / `d2cca7ae10ec6e34`.
- Opening book: disabled.
- Tablebase: disabled.
- TT: 1 MiB independently per side.
- Maximum game length: 256 plies.
- Fixed-node resource: 2,000 nodes per move per engine.
- Clock resource: 10 ms per move per engine.
- Production pair count: 1,000 independent color-swapped opening pairs per protocol / 2,000 games per protocol.
- Minimum score margin: `0.0`; acceptance requires a one-sided 95% lower confidence bound strictly greater than `0.5`.
- Maximum unfinished rate: 50 per mille.
- Reports remain `activated=false` regardless of disposition.

The first S2-14 SEE-ordering + LMR preselection experiment was already rejected at preflight because its x86-64 and ARM64 median ratios (`1.054297` and `1.055081`) exceeded the frozen `1.05` ceiling. Its code was removed and the threshold was not changed. Standalone PVS was then frozen for the production program.

## Exact preflight evidence

Preflight workflow run `31146057113` succeeded on the frozen source SHA.

- x86-64 job `92765623932`; artifact `8981719767`; artifact digest `sha256:8b0e1119611586587aa904a3e9f32a67096b8c96e4b5733da12031b71dd44e24`; seven-sample candidate/baseline median ratio `1.012722`.
- Native ARM64 job `92765623863`; artifact `8981761297`; artifact digest `sha256:71d99e5f753638423421d7b2f4cbb864e7f2f7db90315089d3445a30ec0a73fa`; seven-sample candidate/baseline median ratio `1.013350`.
- Frozen maximum median ratio: `1.05`; both architectures passed.
- Deterministic opening suite: 1,200 unique first-party legal opening lines.
- Opening file SHA-256: `6c3ff4cc9837bc66dd517d4a7c60d56e71a9b3a4e1fb1aabd904de81dad4e9b7`.
- Semantic opening-suite checksum: `36c98c850cff76ba`.
- Formatting, strict Clippy, focused PVS/search tests, deterministic repeated evidence, complete-variant smoke, suite uniqueness, and zero-allocation designated-hot-path checks passed.

## Exact full correctness and platform matrix

The same frozen source SHA passed the permanent project matrix before production disposition:

- CI run `31146057163`: x86-64 workspace-quality job `92765624453` and native ARM64 job `92765624377`; inherited audits, rustfmt, strict Clippy, complete tests, release perft, rustdoc, debug/release builds, UCI smoke, and differential oracle passed.
- Performance run `31146057128`: success.
- Robustness run `31146057142`: Miri, fuzz/corpus replay, ASan/LSan, and TSan gates passed.
- Android/JNI run `31146057103`: host-JVM, Android lint, native ABI, API-35 instrumentation/lifecycle/cancellation gates passed.
- Strength tracker audit run `31146057112`: success.
- Report-master validation run `31146990298`: success.

No correctness, illegal-move, crash, time-forfeit, or infrastructure failure was used to explain away the strength result.

## Production fixed-node result

Workflow run `31146807904`, job `92767800034`, exact invocation `s2-14-production-31146807904-1-fixed-nodes`.

- Protocol: `fixed_nodes:2000`.
- Pairs/games: `1000` / `2000`.
- Candidate wins/draws/losses: `862` / `144` / `977`.
- Unfinished: `17` (`8.5` per mille, below the 50-per-mille ceiling).
- Illegal moves/crashes/time forfeits/infrastructure failures: `0/0/0/0`.
- Mean independent-pair score: `0.47125`.
- Pair-score standard error: `0.008173294332167456`.
- One-sided 95% lower confidence bound: `0.4578061271735924`.
- Required lower bound: strictly greater than `0.5`.
- Decision: `rejected_strength`.
- Report checksum: `bad7aa1f69e9d18e`.
- Baseline variant checksum: `0f0e83e206b88553`.
- Candidate variant checksum: `dc333116073e06e1`.
- Artifact `8982304975`: `s2-14-production-fixed-nodes-21406b5e92b6bd42a3a902591dddae22c9b3f16f`.
- Artifact digest: `sha256:f3997874840a160ece061f77d8a4696379d874e86d706271dfa855ebdb204eb9`.

The unfinished-rate gate passed. The statistical strength gate did not.

## Production clock result

Workflow run `31146807904`, job `92767800098`, exact invocation `s2-14-production-31146807904-1-clock`.

- Protocol: `clock_ms:10`.
- Pairs/games: `1000` / `2000`.
- Candidate wins/draws/losses: `857` / `144` / `972`.
- Unfinished: `27` (`13.5` per mille, below the 50-per-mille ceiling).
- Illegal moves/crashes/time forfeits/infrastructure failures: `0/0/0/0`.
- Mean independent-pair score: `0.47125`.
- Pair-score standard error: `0.008042114965176367`.
- One-sided 95% lower confidence bound: `0.45802189803116894`.
- Required lower bound: strictly greater than `0.5`.
- Decision: `rejected_strength`.
- Report checksum: `d3b883442ec6107b`.
- Baseline variant checksum: `e9869584189d3211`.
- Candidate variant checksum: `ac1e651d3fe824af`.
- Artifact `8982375018`: `s2-14-production-clock-21406b5e92b6bd42a3a902591dddae22c9b3f16f`.
- Artifact digest: `sha256:35189e3e6ff368b7f0eb5cfb004790798d42b516cddde7f1bf33ecccf116551b`.

The unfinished-rate gate passed. The statistical strength gate did not.

## Disposition and activation boundary

Both independent production protocols fail the same predeclared acceptance rule, and both do so with a mean score below `0.5`, not merely a marginally inconclusive confidence interval. S2-14 therefore closes as `rejected_strength`.

The v0.1 baseline policy remains authoritative. PVS remains an inactive controlled candidate. S2-14 does not activate anything, does not update package/UCI version, does not modify public Rust APIs, C ABI, JNI, Kotlin/Android interfaces, or production defaults, and does not authorize S2-15 activation.

S2-15's first precondition (`S2-14 report is accepted_for_activation`) is not satisfied. No activation commit may be made from this evidence. Final program closure may instead use S2-16's explicit no-release disposition path.
