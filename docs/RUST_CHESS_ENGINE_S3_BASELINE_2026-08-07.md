# Rust Chess Engine S3 Baseline — 2026-08-07

**Status:** Frozen S3 planning baseline; v0.1 remains authoritative  
**S3 planning/authority SHA:** `90a015c2cf8b8d45edcd07d705fb6ca58fe336f7`  
**Unchanged production/code baseline SHA:** `677cd2a4d2a4f3c376f7bf47fae412171206fb`  
**S3 specification:** `docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_SPEC_2026-08-07.md`  
**S3 tracker:** `docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_TODO_2026-08-07.md`

Machine witness: `production_baseline_sha=677cd2a4d2a4f3c376f7bf47fae412171206fb`

## Authority and release state

- Package/UCI version: `0.1.0`.
- S2 remains closed without promotion; S2-15 was skipped and no S2 candidate is release authority.
- Search-policy schema: `1`.
- v0.1 search-policy identifier/checksum: `5630315f504f4c31` / `0c0769ef9d034770`.
- Evaluation-weight schema: `1`.
- Baseline evaluation-weight identifier/checksum: `424153454c494e45` / `d2cca7ae10ec6e34`.
- Runtime weight-vector length: `816`; named tunable-parameter count: `810`.
- C ABI version: `1`.
- Opening book is disabled by default; UCI accepts book data only through the explicit `--book <path>` adapter argument and `OwnBook` defaults to false.
- Tablebases/Syzygy are disabled and absent from the production adapter surface.
- No public UCI, safe-Rust facade, C ABI, JNI/Kotlin, or Android API exposes experimental S2 `SearchPolicy` selection.

## Canonical v0.1 policy text

```text
chess-search-policy-v1
schema=1
identifier=5630315f504f4c31
checksum=0c0769ef9d034770
alpha_beta=full_window_fail_soft
transposition=clustered_full_key
move_ordering=v0_1_mvv_lva_killers_history
quiescence=captures_promotions_and_evasions
aspiration_windows=true
aspiration_half_width_centipawns=50
maximum_quiescence_ply=64
maximum_check_extensions_per_line=1
experimental_features=0000000000000000
```

## JNI/Kotlin public-surface identity at the planning baseline

- Rust JNI export source blob: `63a3e4e4b7dcbe12106b17a36ce15117daa46cf8` (`crates/chess-jni/src/lib.rs`).
- Kotlin public wrapper blob: `67c58b41e86be4d00ffb07a7296f5034f10b198e` (`crates/chess-jni/kotlin/src/main/kotlin/com/ekkus93/chessengine/ChessEngine.kt`).
- The public JNI/Kotlin method set remains the v0.1 surface; no experimental search-policy selector is present.

## Exact planning-baseline validation evidence

The S3 planning commit changes documentation and TODO-authority audit state only; it does not change engine/search/adapter semantics relative to the validated production code baseline.

- Performance run `31179459890`: success.
  - Linux ARM64 job `92868991862`: success.
  - Linux x86-64 job `92868991953`: success.
- Robustness run `31179459861`: success.
  - Native sanitizers/leak job `92868992382`: success.
  - Miri core subset job `92868992584`: success.
  - Fuzz/corpus job `92868992629`: success.
- Android/JNI run `31179459876`: success.
  - Android/Kotlin lint job `92868991789`: success.
  - Android API 35 JNI smoke job `92868991806`: success.
  - Host JVM JNI contract job `92868991817`: success.
- Report-master validation run `31179755209`: success.
- CI run `31179459907`: ARM64 job `92868992078` succeeded. The x86-64 workspace-quality job `92868991929` was later cancelled by workflow concurrency after subsequent S3 pushes; it did not fail a test. The later clean permanent S3 gates run the complete x86-64 workspace checks and therefore provide the implementation signoff rather than retroactively relabeling this cancelled planning-baseline job as successful.

## Non-promotion rule

This document is evidence capture only. It authorizes no weight, search-policy, version, opening, tablebase, ABI, JNI, Android, or production-default change. The completed S3 tracker and final report record the later implementation evidence and no-promotion disposition.
