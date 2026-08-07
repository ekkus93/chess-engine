# Rust Chess Engine S3 Evaluation Strength Implementation Report

**Status:** Complete — program closed without promotion  
**Date:** 2026-08-07  
**Specification:** `docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_SPEC_2026-08-07.md`  
**Tracker:** `docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_TODO_2026-08-07.md`  
**Pilot evidence:** `docs/RUST_CHESS_ENGINE_S3_PILOT_EVALUATION_2026-08-07.md`  
**Authoritative released engine:** v0.1 (`0.1.0`)  
**Program outcome:** Completed without promotion; no S3 candidate reached development or production strength validation

## Executive disposition

S3 implemented and validated a strict evaluation-strength pipeline, but it did not produce an evaluator candidate eligible for promotion.

The program added:

- public-surface guardrails preventing rejected S2 search policies from escaping into production adapters;
- a private/hash-neutral `PositionEditor` contract and UCI stale-worker regressions;
- strict S3 self-play dataset manifests with explicit source/policy/weight/config/opening identity;
- deterministic dataset admission and byte-reproducibility controls;
- mask-aware SPSA with six named evaluator groups and checkpoint-bound mask identity;
- additive reproducible S3 dataset and `tune-group` CLI adapters;
- masked tuning-report regularization consistency;
- a strict held-out-loss advancement rule;
- a versioned, checksummed, inactive S3 candidate envelope and duplicate-rejecting registry.

The first bounded pilot then generated an admitted deterministic dataset and tuned all six predeclared existing-evaluator groups. Every group had exactly zero training-loss change and exactly zero held-out validation-loss change. Independently normalized candidate parameter payloads were identical across all six groups. A separately sequenced full 810-parameter pass was run after the group review and again produced zero training and validation loss change.

The frozen S3 advancement rule requires strict training-loss improvement before a candidate can advance. Therefore no candidate reached S3-7 development matches. With no surviving individual candidate, S3-8 optional new evaluation features were deferred and S3-9 formed no combined candidate. S3-10 production validation and S3-11 activation/release were consequently skipped. No release approval was requested because the required accepted candidate did not exist.

This is a successful engineering-program closure, not a strength-success claim. v0.1 remains authoritative.

## Release identities preserved

- package/UCI version: `0.1.0`
- authoritative production/code baseline before S3: `677cd2a4d2a4a4f3c376f7bf47fae412171206fb`
- v0.1 search-policy schema/id/checksum: `1` / `5630315f504f4c31` / `0c0769ef9d034770`
- baseline evaluation schema/id/checksum: `1` / `424153454c494e45` / `d2cca7ae10ec6e34`
- runtime evaluation vector: `816` scalar slots
- named tunable parameters: `810`
- C ABI version: `1`
- default opening book: disabled unless explicitly supplied/enabled
- tablebases/Syzygy: absent and disabled
- experimental S2 search policies: not exposed by UCI, safe Rust facade, C ABI, JNI/Kotlin, or Android
- activation: `false`

## Implementation ledger

### S3-0 / S3-1 — baseline and guardrails

Planning authority commit: `90a015c2cf8b8d45edcd07d705fb6ca58fe336f7`.

Planning-baseline matrix:

- Performance `31179459890`: ARM64 `92868991862`, x86-64 `92868991953`, success.
- Robustness `31179459861`: sanitizer/leak `92868992382`, Miri `92868992584`, fuzz/corpus `92868992629`, success.
- Android/JNI `31179459876`: lint `92868991789`, API-35 JNI `92868991806`, host JVM `92868991817`, success.
- Report validation `31179755209`: success.
- CI `31179459907`: ARM64 `92868992078` succeeded; x86 workspace job `92868991929` was cancelled by later push concurrency, not by a test failure. Later exact S3 clean-tree gates provide complete x86 validation.

Guardrail implementation commit: `57420991e856ac8ee1ff4c3ddf44177db8c3f76c`.

Important defect corrected at source: `PositionEditor` had been publicly re-exported. It is now internal to `chess-core`; documentation and tests make explicit that it mutates board representations but not Zobrist state. Reversible callers own incremental hash changes and verify against authoritative recomputation.

UCI process regressions permanently cover active-search replacement by `position`, `ucinewgame`, repeated stop/restart, and quit/stale-bestmove suppression.

Permanent S3 guardrail run `31180832957`, job `92873446300`: success.

### S3-2 / S3-3 / S3-5 — provenance and masked tuning infrastructure

Implementation commit: `c28fc5e0d8bc9919f8ef5da35017fde1c32ac96b`.

S3 dataset sidecar:

- schema `1`
- identifier `5333444154413031`
- explicit source SHA; no Git/environment discovery
- exact baseline search-policy and evaluation identities
- dataset/config/opening checksums
- game completion and split occurrence counts
- strict checksum and dataset rebinding
- tuning admission thresholds: 16 games, 12 completed, unfinished <= 250/1000, 128 training occurrences, 16 validation occurrences

Named tuning groups:

- material and piece-square: 778 scalars
- mobility and activity: 16
- pawn structure: 8
- king safety and space: 6
- endgame king activity: 2
- full existing evaluator: 810

The first five groups are disjoint and cover all 810 named parameters. Non-full masks are bound into `SpsaConfig` fingerprints; inactive parameters are neither perturbed nor updated and are projected to their reference values. Partial material masks fail closed because material-ordering projection is coupled.

Clean permanent pipeline gate `31182113877`, job `92877654602`: success.

### S3-2 / S3-3 / S3-5 reproducible command surface

Implementation commit: `93ab676b13b1a5d394ffa6d3d4f312a889b5f202`.

Added additive commands:

```text
chess-tools s3-self-play SOURCE_SHA CONFIG_PATH OUTPUT_DIR
chess-tools s3-self-play-validate DATASET_DIR
chess-tools tune-group GROUP CONFIG_PATH S3_DATASET_DIR OUTPUT_DIR [PREVIOUS_OUTPUT_DIR]
```

`S3DatasetManifest` was extended to bind the exact invocation and total/eligible/excluded position-row counts. Dataset packages publish atomically through a same-parent staging rename and include exact config/opening text plus `ACTIVATION_DISABLED`.

`tune-group` validates the dataset/manifest admission contract, source-SHA equality, group mask, exact resume config/group/manifest, and writes inactive S3 summaries.

A real integration defect was fixed: `TuningReport` originally normalized regularization over all 810 parameters even for masked optimizer runs. It now uses the same selected mask domain as the optimizer, with a dedicated regression.

Focused validated run `31183716103`, job `92882978680`: success.
Clean permanent S3 gate `31184166429`, job `92884442719`: success.

### S3-4 / S3-5 — pilot loss evidence

Experiment source SHA: `9ba680dbec8b6ec8d5aebf55f06ff4b3db71e70d`.

Successful read-only experiment:

- run `31184450979`
- job `92885406054`
- artifact `8996149049`
- artifact digest `sha256:797a03d73830e30ead1537378716b02a9aa91553764f9992388876ec0d267d`
- dataset checksum `c691d1928ffda61b`
- manifest checksum `6aef02a9b375c5a3`
- training occurrences `2,066`
- validation occurrences `195`
- excluded rows `0`
- dataset admitted for tuning
- activation `false`

The exact self-play package was generated twice and compared byte-for-byte. The pawn-structure tuning run was also regenerated from scratch and compared byte-for-byte.

All six groups reported:

- initial/final training loss `1.25882801415297285e-1`
- initial/final validation loss `6.05660231663427279e-2`
- training delta `0.0`
- validation delta `0.0`

Every candidate's normalized `parameter.*` payload had SHA-256:

`689d960bd3a2751604165861116a0bc3d10afa4aea32bbbb82e808a59c777066`

Therefore no pilot evaluator value changed.

The predecessor run `31184300662` failed only because the workflow attempted nonexistent `cmp -r`; it had already generated matching datasets. The workflow was fixed to recursive `diff`, not weakened.

### Reviewed full-evaluator sequencing pass

The original tracker required the full evaluator pass to occur only after group review. The pilot had exercised all six groups in one pipeline job, so that first full pass was not retroactively counted as satisfying that sequence.

After `docs/RUST_CHESS_ENGINE_S3_PILOT_EVALUATION_2026-08-07.md` formally reviewed/rejected the group results, a separate full pass ran:

- source SHA `cbfe949398d5218f4362b0401951b8e59f8f4b84`
- run `31185848704`
- job `92890034934`
- candidate `533347525030305c`
- full mask `02c6c0907d4847c3`
- dataset checksum `c691d1928ffda61b`
- manifest checksum `5687949bd583f1dc`
- training occurrences `2,066`
- validation occurrences `195`
- eligible position rows `760`
- excluded rows `0`
- training delta `0.0`
- validation delta `0.0`
- activation `false`
- artifact `8996696803`
- artifact digest `sha256:5f1cbb38d7409baba2fd03300c19e0d81e83d8c777ac73c91e795d0e73895877`

This satisfies the review-before-full-pass sequencing requirement and independently confirms the no-improvement disposition.

### S3-4 / S3-6 — held-out policy and candidate registry

The S3 loss rule is fail closed:

1. every loss must be finite and non-negative;
2. final training loss must be strictly lower than initial training loss;
3. if training improves, validation may not regress by more than deterministic tolerance `1e-12`;
4. only `advance` may reach later strength validation;
5. loss evidence alone never activates a candidate.

The candidate registry implementation commit is `664bbf4b281efecafb3a3b60465e6dfff9ed1aaa`.

Candidate envelope:

- schema `1`
- format identifier `533343414e443031`
- current candidate type `existing_evaluation_weights`
- exact candidate/source/baseline/artifact/value/vector/tunable/group/mask/time/config/dataset/manifest/report/invocation identities
- exact held-out loss decision and loss deltas
- canonical checksum
- `activated=false` required

Registry tests reject schema/type/length/baseline/checksum mismatch, corrupt artifact values, duplicate candidate identifiers, and activation. Focused registry gate `31185313282`, job `92888271090`: success.

## Candidate dispositions

The six original pilot candidates plus the reviewed full pass all have `reject_no_training_improvement`. None is an advancing S3 candidate.

This distinction matters: successful tooling workflows and valid candidate artifacts are evidence that the pipeline works, not evidence that the evaluator is stronger.

## S3-7 — development strength validation

**Skipped — no advancing candidate.**

No candidate satisfied the held-out loss rule. A development paired match would therefore compare the authoritative evaluator with an evaluator payload that did not change. Running such games as strength evidence would be misleading and wasteful. No S3 candidate report claims development strength acceptance.

## S3-8 — optional new evaluation features

**Deferred.**

Pawn islands, backward pawns, outposts, rook activity, richer passed-pawn detail, king safety, threats, and endgame terms remain reasonable future experiments, but S3 did not introduce them. Adding structural terms after a depth-one/32-game pilot failed to move existing weights would conflate feature design with unresolved training-scale/optimizer-sensitivity questions. These experiments require a future explicit program with suitable data and isolated feature evidence.

## S3-9 — combined candidate

**Complete — no combined candidate formed.**

No existing-evaluator tuning candidate independently advanced, and no optional feature candidate was implemented. Therefore there were no justified components to combine. Rejected pilot identities were not quietly combined or reactivated.

## S3-10 — production strength validation

**Skipped — no eligible candidate.**

The production gate was not entered. No 1,000-pair fixed-node or clock match was run because no S3 candidate passed the preceding held-out/development prerequisites. No production-strength report claims acceptance.

## S3-11 — activation and release

**Skipped — activation preconditions unsatisfied.**

No S3-10 candidate exists, so explicit user approval was neither requested nor obtained. No activation commit was created; package/UCI version remains `0.1.0`; default search policy and weights remain v0.1; public adapter surfaces remain unchanged.

## S3-12 — closure

S3 is closed through the explicit no-promotion path. Permanent audits preserve:

- v0.1 release identity;
- S2 no-promotion state;
- S3 public-surface guardrails;
- strict dataset provenance and tuning-mask behavior;
- inactive candidate registry semantics;
- no Python/subprocess production fallback;
- no temporary write-capable S3 staging helpers.

At final closure, the S3 TODO is historical and there is no active implementation TODO unless a future program is explicitly registered.

## Limitations and future roadmap

The pilot was deliberately small: 32 games, depth-one search, and eight SPSA iterations. Its zero movement should not be generalized into a conclusion that evaluation tuning cannot improve the engine. It shows that this pilot did not provide a useful gradient at the chosen scale/schedule.

A future strength program should first change the evidence quality, not simply repeat S3 with more checkboxes. Reasonable next experiments include:

- substantially larger/deeper deterministic self-play or externally labelled positions;
- more SPSA iterations and schedule sensitivity studies;
- independent supervised/Texel-style evaluation fitting using held-out partitions;
- then isolated new evaluation features;
- only after a real evaluation candidate exists, renewed search-heuristic experiments.

Any future release candidate must repeat held-out validation, development strength, production strength, explicit approval, activation, and exact-SHA release validation. No rejected S3 artifact authorizes promotion.
