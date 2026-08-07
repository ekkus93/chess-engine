# Rust Chess Engine S4 Baseline — 2026-08-07

**Status:** Frozen S4 operational baseline; v0.1 remains authoritative  
**S4 planning baseline SHA:** `543dce22e51e71f821e37754a97ce0f33c3be122`  
**S4 clean operational baseline SHA:** `b02623f20417c7f5769b6a16fc94566239e7979a`  
**Unchanged production/code baseline SHA:** `677cd2a4d2a4a4f3c376f7bf47fae412171206fb`  
**Specification:** `docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_SPEC_2026-08-07.md`  
**Tracker:** `docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_TODO_2026-08-07.md`

## Authority and release identity

- Package/UCI version: `0.1.0`.
- v0.1 search-policy identifier/checksum: `5630315f504f4c31` / `0c0769ef9d034770`.
- Baseline evaluation-weight identifier/checksum: `424153454c494e45` / `d2cca7ae10ec6e34`.
- Runtime evaluation weight-vector length: `816`; named tunable-parameter count: `810`.
- C ABI version: `1`.
- Rust JNI export source blob: `63a3e4e4b7dcbe12106b17a36ce15117daa46cf8`.
- Kotlin public wrapper blob: `67c58b41e86be4d00ffb07a7296f5034f10b198e`.
- Opening-book behavior remains explicit-only; no implicit book discovery is enabled and UCI `OwnBook` defaults false.
- Tablebases/Syzygy remain absent and disabled.
- S3 candidate-envelope schema/format identifier: `1` / `533343414e443031`.
- S3 candidate artifacts are inactive by contract and serialize `activated=false`.

## S3 closure evidence correction

The S3 program outcome remains **closed without promotion**, but the exact S3 closure SHA `543dce22e51e71f821e37754a97ce0f33c3be122` was not a fully green repository state.

- Performance run `31186888341`: success.
- S3 Evaluation Strength run `31186888170`, job `92893571662`: **failure**.
- CI run `31186888214`: **failure**.
- The S3 guardrail failure was repository hygiene, not a chess-strength or engine-correctness failure: the permanent v0.2 audit rejected the leftover write-capable `.github/workflows/s3-closure-docs-stage.yml` staging workflow.
- S4 removed that stale S3 workflow and its helper before establishing the operational baseline.
- The closed S3 strength disposition is unchanged: the six pilot groups and the reviewed full 810-parameter run produced zero training-loss delta, zero validation-loss delta, and no effective evaluator-value movement.

This correction is intentionally explicit. A failed permanent gate is not reclassified as green merely because its root cause was staging residue.

## S4 operational-baseline cleanup

Before S4 optimizer work:

1. Removed stale `.github/workflows/s3-closure-docs-stage.yml`.
2. Removed stale `.github/s3_closure_docs.py`.
3. Updated the closed S3 audit so it requires S3 to remain historical while allowing the intentionally active S4 tracker.
4. Extended the S3 temporary-control audit so the stale closure helper/workflow cannot silently reappear.
5. Removed the temporary S4 authority-transition workflow/helper after its targeted staging gate succeeded.

No production Rust engine, search, evaluation, ABI, JNI, Kotlin, Android, opening, tablebase, or default configuration changed during this cleanup.

## Non-promotion proof

- S2 experimental search-policy feature mask remains `0000000000000000` in v0.1.
- No public UCI, safe-Rust facade, C ABI, JNI/Kotlin, or Android API accepts an experimental search policy.
- No public adapter accepts S3 candidate selection.
- Production evaluation remains `EvaluationWeights::DEFAULT` / baseline weight set `424153454c494e45`.
- S4 is calibration-only and cannot activate a candidate.

## Validation rule

`b02623f20417c7f5769b6a16fc94566239e7979a` is the clean operational baseline identity. S4-0 is complete only after the permanent CI, performance, robustness, Android/JNI, S3-closure, and S4-baseline audits on a clean descendant preserve these identities without hidden fallbacks or write-capable staging controls.
