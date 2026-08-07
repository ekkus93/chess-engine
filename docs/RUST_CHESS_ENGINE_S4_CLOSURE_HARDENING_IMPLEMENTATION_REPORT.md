# Rust Chess Engine S4 Closure Hardening Implementation Report

**Status:** Complete — closure hardening validated; no production promotion
**Date:** 2026-08-07
**Planning baseline SHA:** `bc406d78d673cc3258e8b522bcec25c4838f5e32`
**Implementation-start SHA:** `9f5c398a70e22228454f0184225a414f1466cdf5`
**H0-H6 source implementation SHA:** `e5b239e9c182b9f862ab6c603b0f235ee26ac7e8`
**Exact pre-closure validation SHA:** `5d350b86ce924ea2a149312acf9e4b66e1d0251d`
**Production package/UCI version:** `0.1.0`
**Production activation:** unchanged / none

## Executive disposition

The S4 closure-hardening implementation resolves every code-review issue targeted by H0-H6 without reopening evaluator tuning or changing production chess behavior. The implementation is fully validated on exact SHA `5d350b86ce924ea2a149312acf9e4b66e1d0251d`. This report is being published as part of H7 authority closure; the final closed-authority SHA must still pass the permanent matrix before H7.3 and the tracker can be marked complete.

Production identities remain unchanged:

- v0.1 search-policy identifier/checksum: `5630315f504f4c31` / `0c0769ef9d034770`;
- baseline evaluation-weight identifier/checksum: `424153454c494e45` / `d2cca7ae10ec6e34`;
- selected S4 calibration candidate value checksum: `520db5dd58086a8a`, still inactive and `rejected_strength`;
- package/UCI version: `0.1.0`;
- no ABI, JNI, Kotlin, Android, opening-default, tablebase, or production search-policy behavior change.

## H0 authority and baseline

The hardening program began from final S4 closure SHA `bc406d78d673cc3258e8b522bcec25c4838f5e32`. The planning files advanced `master` to implementation-start SHA `9f5c398a70e22228454f0184225a414f1466cdf5`, at which point the hardening TODO became the sole active implementation tracker. Closed S2/S3/S4 tuning and strength programs remained historical and no production candidate was activated.

## H1 final S4 evidence correction

`docs/RUST_CHESS_ENGINE_S4_FINAL_VALIDATION_ADDENDUM_2026-08-07.md` now records the previously missing completed permanent matrix for original final S4 SHA `bc406d78d673cc3258e8b522bcec25c4838f5e32`:

- CI `31208874474`: jobs `92966583551`, `92966583700` success;
- Performance `31208875019`: jobs `92966584891`, `92966585078` success;
- Robustness `31208875521`: jobs `92966586631`, `92966586666`, `92966586684` success;
- Android/JNI `31208874646`: jobs `92966594534`, `92966594629`, `92966594742` success;
- S4 `31208874643`: job `92966583439` success;
- report publication `31209467578`: job `92968530668` success.

Retained original final-S4 artifacts are also recorded with digests: Performance artifacts `9005860229` and `9005851414`, and Android artifact `9005947857`.

## H2 strict diagnostic-count validation

Changed `crates/chess-tune/src/diagnostics.rs` and `crates/chess-tune/src/trace.rs`.

`SpsaIterationDiagnostics::validate_counts()` now uses checked arithmetic and requires:

- positive + negative + zero gradient counts to equal the active count;
- zero-after-quantization + nonzero integer movement to be no greater than the active count;
- `changed_parameter_count == nonzero_integer_update_count`;
- clipped-update count to be no greater than the active count;
- active count to remain within `TUNABLE_PARAMETER_COUNT`.

Parser-level regressions `trace_rejects_impossible_quantization_update_partition` and `trace_rejects_changed_count_mismatch` prove malformed canonical trace rows fail closed. Existing canonical round-trip and corruption/binding tests remain green.

## H3 fail-visible staging cleanup

Changed `crates/chess-tools/src/tuning_cli.rs`.

The old discarded cleanup result was removed. A primary tuning publication failure is preserved, while a secondary failure to remove the staging directory is appended deterministically through `cleanup_staging_after_failure` / `cleanup_failure_message`. No fallback output directory, overwrite, ignored error, or retry path was introduced. `cleanup_failure_context_preserves_primary_error` covers the deterministic error-composition behavior; direct OS-level cleanup failure injection remains intentionally skipped as non-portable.

## H4 canonical source-commit parsing

Changed `crates/chess-tools/src/tuning_cli.rs`.

Tuning-config `source_commit` now requires exactly 40 lowercase hexadecimal characters, consistent with the strict S4 trace representation, and still rejects the all-zero identity. Regressions cover valid lowercase, uppercase rejection, mixed-case rejection, and short/invalid/zero inputs.

## H5 checkpoint materialization API decision

Changed `crates/chess-tune/src/optimizer.rs`.

Repository-wide caller inventory found zero callers of `SpsaCheckpoint::current_weights`; only the public method definition existed. Path B was selected: the unused method was removed rather than preserving ambiguous all-mask raw checkpoint projection. The safe `best_weights()` publication path remains, and `checkpoint_best_weights_preserve_inactive_parameters_after_masked_run` proves inactive values remain baseline-identical after a masked run. Existing resume checks continue to fail closed on config, dataset, objective, bounds, and runtime-weight mismatches.

## H6 audit/workflow integration

Updated:

- `scripts/task_post_port_review_fix_audit.sh`;
- `scripts/task_s3_evaluation_strength_audit.sh`;
- `scripts/task_s4_evaluation_tuning_calibration_audit.sh`;
- `docs/LEGACY_TODO_INDEX.md`;
- S4 hardening spec/TODO and original S4 evidence documents.

The permanent S4 workflow itself was not weakened or made write-capable. It remains `contents: read` and runs the permanent S4 audit, formatting, strict Clippy, complete `chess-tune` regressions, and complete `chess-tools` regressions.

## H0-H6 staging evidence

Temporary staging run `31212409405`, job `92978072080`, passed after the helper and workflow removed themselves from the working tree. It validated formatting, strict tuning/tooling Clippy, both regression suites, authority audit, S4 audit, and `git diff --check` before publishing `e5b239e9c182b9f862ab6c603b0f235ee26ac7e8`.

The first staging attempt `31212279860`, job `92977651725`, failed only on generated Rust formatting and published nothing. The staging workflow was corrected to run `cargo fmt --all` before `--check`; no semantic gate was weakened.

## Exact implementation prevalidation

A normal repository write produced exact implementation-validation SHA `5d350b86ce924ea2a149312acf9e4b66e1d0251d`. All required permanent workflows passed on that same SHA:

- CI run `31212586187`: x86-64 job `92978647071`, ARM64 job `92978647134` — success;
- Performance run `31212586069`: x86-64 job `92978646654`, ARM64 job `92978646729` — success;
- Robustness run `31212586338`: fuzz/corpus `92978647371`, Miri `92978647390`, sanitizers/leak `92978647427` — success;
- Android/JNI run `31212586580`: lint `92978665266`, API-35 JNI `92978665285`, host JVM JNI `92978665319` — success;
- S4 run `31212586025`, guardrails job `92978646315` — success;
- post-CI bounded report publication run `31213948156`, job `92983000347` — success.

Retained prevalidation artifacts:

- x86-64 Performance artifact `9007273737`, digest `sha256:140c626f08128b23504a44ffb331d903f0d573a365fe63814f5200bb464882c0`;
- ARM64 Performance artifact `9007261853`, digest `sha256:083cbdcbc4401db074af6d408a9c55604028af5b048b59a420bef80e0654af02`;
- Android Performance artifact `9007354662`, digest `sha256:f45d290c61b90827de212a5a113b7ea882c4c597f9ba3326ff71ca649d2721e1`.

## Source files changed

Behavioral Rust changes are limited to:

1. `crates/chess-tune/src/diagnostics.rs`;
2. `crates/chess-tune/src/trace.rs`;
3. `crates/chess-tune/src/optimizer.rs`;
4. `crates/chess-tools/src/tuning_cli.rs`.

All other hardening changes are evidence, authority, or audit documentation/scripts. No runtime search/evaluation implementation, public adapter, or Android production code was changed.

## H7 closure state

H7.1 implementation reporting and H7.2 authority cleanup are complete in this closure candidate. The hardening TODO is historical and there is no active implementation TODO. H7.3 remains pending until a normal repository write on this closed-authority state triggers and passes the permanent CI, Performance, Robustness, Android/JNI, S4, and report-publication gates. No final completion claim is made before that evidence exists.

## H7 exact final validation

The exact closed-authority hardening SHA `040dbfa7d88df71380c9082d224f54b99e17c583` passed the complete permanent matrix. `docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_FINAL_VALIDATION_2026-08-07.md` is the authoritative detailed record.

- CI `31214468559`: jobs `92984632692`, `92984632651` success.
- Performance `31214473918`: jobs `92984650575`, `92984650722` success.
- Robustness `31214467831`: jobs `92984630799`, `92984630807`, `92984630842` success.
- Android/JNI `31214467810`: jobs `92984646200`, `92984646272`, `92984646321` success.
- S4 `31214467814`: job `92984630452` success.
- post-CI report publication `31215644023`: job `92988408595` success.

Retained final evidence artifacts are Performance `9007948263` (`sha256:4aa8e1ed737a51728b2a4edd8e98fac671be89307979c2476e45d4ac39aaf63b`), Performance ARM64 `9007944932` (`sha256:a32c74557f09348a4856cc0591c798d2b472d321d958ae84eef967d13a8598cf`), and Android `9008040056` (`sha256:48224d6b5da1d299caa9403a573f8642f4ba2b21d88847d24946f9b737f3a38a`).

H7 is complete. The hardening tracker remains historical, there is no active implementation TODO, and no production promotion occurred.
