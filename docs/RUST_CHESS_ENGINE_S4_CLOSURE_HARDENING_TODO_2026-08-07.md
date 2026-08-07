# Rust Chess Engine S4 Closure Hardening TODO — 2026-08-07

**Status:** Complete — closure hardening validated; no production promotion
**Date:** 2026-08-07
**Branch:** `master`
**Planning baseline SHA:** `bc406d78d673cc3258e8b522bcec25c4838f5e32`
**Implementation-start SHA:** `9f5c398a70e22228454f0184225a414f1466cdf5`
**Specification:** `docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_SPEC_2026-08-07.md`
**Prior S4 tracker:** `docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_TODO_2026-08-07.md`

---

## Status rules

- `[x]` means implemented, documented, and validated with exact evidence.
- `[ ]` means incomplete.
- `SKIPPED` means a conditional validation step was correctly not run and the reason is recorded.
- `REJECTED` means an attempted implementation failed a predeclared gate and cannot be reused as positive evidence.
- This is an S4 closure-hardening program, not a new tuning or strength program.
- No evaluator candidate may be activated.
- No package/UCI version, ABI, JNI/Kotlin, Android API, opening-default, tablebase, or production search-policy behavior may change.
- First-party failures must be fixed at source unless explicitly classified as external service/reporting behavior.
- No lint suppression, hidden fallback, ignored failure, or weakened gate is acceptable.

---

# Task H0: Authority registration and baseline freeze — COMPLETE

## H0.1 Planning baseline

- [x] Record the current `master` SHA before implementation begins.
- [x] Confirm the planning baseline is `bc406d78d673cc3258e8b522bcec25c4838f5e32` unless `master` has advanced before implementation.
- [x] If `master` has advanced, record both this planning SHA and the actual implementation-start SHA.
- [x] Confirm package/UCI version is still `0.1.0`.
- [x] Confirm v0.1 search-policy identifier/checksum remains `5630315f504f4c31` / `0c0769ef9d034770`.
- [x] Confirm baseline evaluation-weight identifier/checksum remains `424153454c494e45` / `d2cca7ae10ec6e34`.
- [x] Confirm selected S4 candidate checksum `520db5dd58086a8a` remains inactive and rejected as development-strength evidence.

## H0.2 Authority registration

- [x] Register this TODO as the single active implementation tracker in `docs/LEGACY_TODO_INDEX.md` when implementation begins.
- [x] Keep the completed S4 evaluation-tuning calibration TODO historical.
- [x] Keep all prior S2/S3/S4 no-promotion dispositions unchanged.
- [x] Update the permanent TODO-authority audit to reject unclassified active TODO additions.
- [x] Confirm no other active top-level `docs/*TODO*.md` remains.

## H0 gate

- [x] Hardening begins from an exact, documented, non-promoted baseline.

---

# Task H1: Final S4 validation evidence correction — COMPLETE

## H1.1 Evidence inventory

- [x] Locate the final post-closure CI run/job IDs for SHA `bc406d78d673cc3258e8b522bcec25c4838f5e32`.
- [x] Locate the final post-closure Performance run/job IDs for SHA `bc406d78d673cc3258e8b522bcec25c4838f5e32`.
- [x] Locate the final post-closure Robustness run/job IDs for SHA `bc406d78d673cc3258e8b522bcec25c4838f5e32`.
- [x] Locate the final post-closure Android/JNI run/job IDs for SHA `bc406d78d673cc3258e8b522bcec25c4838f5e32`.
- [x] Locate the final post-closure S4 Evaluation Tuning Calibration run/job ID for SHA `bc406d78d673cc3258e8b522bcec25c4838f5e32`.
- [x] Locate the final post-closure report-publication run/job ID for SHA `bc406d78d673cc3258e8b522bcec25c4838f5e32`.
- [x] Record any relevant final post-closure artifact IDs/checksums.

## H1.2 Documentation update

- [x] Create an S4 final-validation addendum or update the existing S4 final report/TODO evidence section.
- [x] Explicitly distinguish pre-closure implementation SHA `b66b256a5b81621ba5310a749b7b93e650cc6067` from final closed SHA `bc406d78d673cc3258e8b522bcec25c4838f5e32`.
- [x] Record the final closed-SHA matrix as completed, not merely triggered.
- [x] Preserve the selected S4 candidate disposition as `rejected_strength` / inactive.
- [x] Preserve the S4 method disposition as accepted only for future controlled evaluator experimentation.
- [x] Confirm no production promotion occurred.

## H1.3 Audit witness

- [x] Update the permanent S4 audit to require the final closed SHA and its run/job evidence.
- [x] Ensure the audit no longer accepts only pre-closure validation evidence as satisfying S4-12.3.

## H1 gate

- [x] The repository evidence fully satisfies S4-12.3 for the final closed SHA.

---

# Task H2: Strict diagnostic-count validation — COMPLETE

## H2.1 Source invariant hardening

- [x] Strengthen `SpsaIterationDiagnostics::validate_counts()` in `crates/chess-tune/src/diagnostics.rs`.
- [x] Require checked arithmetic for gradient-count summation.
- [x] Require `positive_gradient_count + negative_gradient_count + zero_gradient_count == active_parameter_count`.
- [x] Require `zero_after_quantization_count + nonzero_integer_update_count <= active_parameter_count`.
- [x] Require `changed_parameter_count == nonzero_integer_update_count`.
- [x] Require `clipped_update_count <= active_parameter_count`.
- [x] Reject overflow-prone count combinations without wrapping.
- [x] Preserve all currently valid optimizer-emitted diagnostics.

## H2.2 Trace parser regressions

- [x] Add a malformed-trace test where `zero_after_quantization_count + nonzero_integer_update_count > active_parameter_count`.
- [x] Add a malformed-trace test where `changed_parameter_count != nonzero_integer_update_count`.
- [x] Keep the existing impossible gradient-count rejection test.
- [x] Ensure the parser-level canonical trace path rejects the malformed rows.
- [x] Ensure valid trace round-trip tests continue to pass.

## H2.3 Audit witness

- [x] Update the S4 audit to witness the new count invariants in source.
- [x] Update the S4 audit to witness the new malformed-trace tests.

## H2 gate

- [x] Impossible diagnostic count combinations fail closed through the strict trace path.

---

# Task H3: Fail-visible tuning-output staging cleanup — COMPLETE

## H3.1 Source cleanup behavior

- [x] Replace silent `let _ = fs::remove_dir_all(&staging);` behavior in `publish_output_directory()`.
- [x] Preserve the original publication failure as the primary error.
- [x] Add deterministic secondary context or stderr warning when staging cleanup fails.
- [x] Do not retry into a different output directory.
- [x] Do not delete or overwrite an existing output directory.
- [x] Do not hide cleanup failure with `|| true`, ignored result, or equivalent behavior.

## H3.2 Tests

- [x] Add or update tests if the cleanup path can be exercised deterministically.
- [x] SKIPPED — direct OS-level cleanup failure injection is not portable; the pure secondary-context formatter is tested and the production cleanup call is source/audit witnessed.

## H3.3 Audit witness

- [x] Update the S4 audit to reject the silent cleanup-discard pattern.
- [x] Update the S4 audit to witness the replacement fail-visible cleanup behavior.

## H3 gate

- [x] Tuning-output staging cleanup failure cannot disappear silently.

---

# Task H4: Canonical tuning source-commit parsing — COMPLETE

## H4.1 Source parser hardening

- [x] Update `parse_source_commit()` in `crates/chess-tools/src/tuning_cli.rs` to require exactly 40 lowercase hexadecimal characters.
- [x] Continue rejecting all-zero source commits.
- [x] Preserve existing binary commit identity for valid lowercase inputs.
- [x] Preserve tuning-config checksum binding to exact config text.

## H4.2 Tests

- [x] Add a lowercase valid commit test.
- [x] Add an uppercase commit rejection test.
- [x] Add a mixed-case commit rejection test.
- [x] Keep short/invalid/all-zero rejection tests.

## H4.3 Audit witness

- [x] Update the S4 audit to witness lowercase-only parsing.
- [x] Update the S4 audit to witness uppercase/mixed-case rejection tests.

## H4 gate

- [x] Tuning config `source_commit` text is canonical and consistent with S4 trace parsing style.

---

# Task H5: Checkpoint materialization API review — COMPLETE

## H5.1 Caller inventory

Caller inventory result: GitHub code search for `current_weights(` returned only the method definition in `crates/chess-tune/src/optimizer.rs`; there are zero production, workflow, or test callers.

- [x] Search all callers of `SpsaCheckpoint::current_weights`.
- [x] Determine whether any production or S4 workflow relies on the current all-mask projection behavior.
- [x] Record the caller inventory in the implementation report.

## H5.2 API decision

Choose one path and complete it:

- [x] SKIPPED — Path A was unnecessary because repo-wide caller inventory found no caller of `SpsaCheckpoint::current_weights`.
- [x] Path B selected: remove the unused public `SpsaCheckpoint::current_weights` method entirely; no caller depends on it.
- [x] SKIPPED — Path C would preserve the ambiguous all-mask materialization footgun and was not selected.

## H5.3 Safety proof

- [x] Prove resume validation still rejects mismatched dataset/config/objectives.
- [x] Prove inactive parameters cannot escape through S4 candidate publication.
- [x] Prove the selected API decision does not change production evaluator/search behavior.

## H5.4 Audit witness

- [x] Update the S4 audit to witness the API decision.
- [x] Add or update tests for the chosen behavior.

## H5 gate

- [x] Checkpoint materialization semantics are explicit, tested, and safe against inactive-parameter escape.

---

# Task H6: Permanent audit and workflow integration — COMPLETE

## H6.1 S4 audit update

- [x] Update `scripts/task_s4_evaluation_tuning_calibration_audit.sh` to require the H1-H5 hardening evidence.
- [x] Keep all existing no-promotion checks.
- [x] Keep all existing temporary-control rejection checks.
- [x] Keep all existing production identity checks.
- [x] Keep S3/S4 historical closure awareness.

## H6.2 Workflow check

- [x] Confirm `.github/workflows/s4-evaluation-tuning-calibration.yml` remains read-only.
- [x] Confirm no temporary hardening helper/workflow remains after closure.
- [x] Confirm permanent workflow runs strict Clippy and full `chess-tune`/`chess-tools` regressions.

## H6 gate

- [x] Permanent audits fail closed on the new hardening requirements.

---

# Task H7: Final implementation report and authority cleanup — COMPLETE

## H7.1 Implementation report

- [x] Create `docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_IMPLEMENTATION_REPORT.md`.
- [x] Record baseline SHA and final hardening SHA.
- [x] Record every source file changed.
- [x] Record final-SHA evidence correction outcome.
- [x] Record diagnostic-count validation changes.
- [x] Record malformed-trace tests.
- [x] Record staging-cleanup behavior change.
- [x] Record source-commit parser change.
- [x] Record checkpoint materialization API decision.
- [x] Record audit/workflow updates.
- [x] Confirm no production activation or version/API behavior change.

## H7.2 TODO closure

- [x] Mark every completed task/subtask in this TODO.
- [x] Move this TODO from active authority to historical inventory when hardening closes.
- [x] Update `docs/LEGACY_TODO_INDEX.md` counts/classification.
- [x] Confirm no other active implementation TODO remains.

## H7.3 Final validation

Exact validated hardening closure SHA: `040dbfa7d88df71380c9082d224f54b99e17c583`. Evidence: `docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_FINAL_VALIDATION_2026-08-07.md`.


- [x] Run permanent S4 Evaluation Tuning Calibration workflow.
- [x] Run strict workspace CI.
- [x] Run Performance workflow or explicitly justify if unchanged hot-path behavior makes it unnecessary.
- [x] Run Robustness workflow.
- [x] Run Android/JNI workflow or explicitly justify if adapter-facing behavior is unchanged.
- [x] Run report-publication validation.
- [x] Record exact final SHA, run IDs, job IDs, artifact IDs, and checksums.

## H7 gate

- [x] S4 closure hardening is truthfully closed with exact evidence and no production promotion.

---

# Final hardening completion checklist

- [x] H0 authority and baseline freeze complete.
- [x] H1 final S4 validation evidence correction complete.
- [x] H2 strict diagnostic-count validation complete.
- [x] H3 fail-visible tuning-output staging cleanup complete.
- [x] H4 canonical tuning source-commit parsing complete.
- [x] H5 checkpoint materialization API review complete.
- [x] H6 permanent audit/workflow integration complete.
- [x] H7 final report and authority cleanup complete.
