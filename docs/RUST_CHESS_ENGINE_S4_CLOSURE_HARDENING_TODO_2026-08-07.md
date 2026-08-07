# Rust Chess Engine S4 Closure Hardening TODO — 2026-08-07

**Status:** Proposed — not yet implemented
**Date:** 2026-08-07
**Branch:** `master`
**Planning baseline SHA:** `bc406d78d673cc3258e8b522bcec25c4838f5e32`
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

# Task H0: Authority registration and baseline freeze — NOT STARTED

## H0.1 Planning baseline

- [ ] Record the current `master` SHA before implementation begins.
- [ ] Confirm the planning baseline is `bc406d78d673cc3258e8b522bcec25c4838f5e32` unless `master` has advanced before implementation.
- [ ] If `master` has advanced, record both this planning SHA and the actual implementation-start SHA.
- [ ] Confirm package/UCI version is still `0.1.0`.
- [ ] Confirm v0.1 search-policy identifier/checksum remains `5630315f504f4c31` / `0c0769ef9d034770`.
- [ ] Confirm baseline evaluation-weight identifier/checksum remains `424153454c494e45` / `d2cca7ae10ec6e34`.
- [ ] Confirm selected S4 candidate checksum `520db5dd58086a8a` remains inactive and rejected as development-strength evidence.

## H0.2 Authority registration

- [ ] Register this TODO as the single active implementation tracker in `docs/LEGACY_TODO_INDEX.md` when implementation begins.
- [ ] Keep the completed S4 evaluation-tuning calibration TODO historical.
- [ ] Keep all prior S2/S3/S4 no-promotion dispositions unchanged.
- [ ] Update the permanent TODO-authority audit to reject unclassified active TODO additions.
- [ ] Confirm no other active top-level `docs/*TODO*.md` remains.

## H0 gate

- [ ] Hardening begins from an exact, documented, non-promoted baseline.

---

# Task H1: Final S4 validation evidence correction — NOT STARTED

## H1.1 Evidence inventory

- [ ] Locate the final post-closure CI run/job IDs for SHA `bc406d78d673cc3258e8b522bcec25c4838f5e32`.
- [ ] Locate the final post-closure Performance run/job IDs for SHA `bc406d78d673cc3258e8b522bcec25c4838f5e32`.
- [ ] Locate the final post-closure Robustness run/job IDs for SHA `bc406d78d673cc3258e8b522bcec25c4838f5e32`.
- [ ] Locate the final post-closure Android/JNI run/job IDs for SHA `bc406d78d673cc3258e8b522bcec25c4838f5e32`.
- [ ] Locate the final post-closure S4 Evaluation Tuning Calibration run/job ID for SHA `bc406d78d673cc3258e8b522bcec25c4838f5e32`.
- [ ] Locate the final post-closure report-publication run/job ID for SHA `bc406d78d673cc3258e8b522bcec25c4838f5e32`.
- [ ] Record any relevant final post-closure artifact IDs/checksums.

## H1.2 Documentation update

- [ ] Create an S4 final-validation addendum or update the existing S4 final report/TODO evidence section.
- [ ] Explicitly distinguish pre-closure implementation SHA `b66b256a5b81621ba5310a749b7b93e650cc6067` from final closed SHA `bc406d78d673cc3258e8b522bcec25c4838f5e32`.
- [ ] Record the final closed-SHA matrix as completed, not merely triggered.
- [ ] Preserve the selected S4 candidate disposition as `rejected_strength` / inactive.
- [ ] Preserve the S4 method disposition as accepted only for future controlled evaluator experimentation.
- [ ] Confirm no production promotion occurred.

## H1.3 Audit witness

- [ ] Update the permanent S4 audit to require the final closed SHA and its run/job evidence.
- [ ] Ensure the audit no longer accepts only pre-closure validation evidence as satisfying S4-12.3.

## H1 gate

- [ ] The repository evidence fully satisfies S4-12.3 for the final closed SHA.

---

# Task H2: Strict diagnostic-count validation — NOT STARTED

## H2.1 Source invariant hardening

- [ ] Strengthen `SpsaIterationDiagnostics::validate_counts()` in `crates/chess-tune/src/diagnostics.rs`.
- [ ] Require checked arithmetic for gradient-count summation.
- [ ] Require `positive_gradient_count + negative_gradient_count + zero_gradient_count == active_parameter_count`.
- [ ] Require `zero_after_quantization_count + nonzero_integer_update_count <= active_parameter_count`.
- [ ] Require `changed_parameter_count == nonzero_integer_update_count`.
- [ ] Require `clipped_update_count <= active_parameter_count`.
- [ ] Reject overflow-prone count combinations without wrapping.
- [ ] Preserve all currently valid optimizer-emitted diagnostics.

## H2.2 Trace parser regressions

- [ ] Add a malformed-trace test where `zero_after_quantization_count + nonzero_integer_update_count > active_parameter_count`.
- [ ] Add a malformed-trace test where `changed_parameter_count != nonzero_integer_update_count`.
- [ ] Keep the existing impossible gradient-count rejection test.
- [ ] Ensure the parser-level canonical trace path rejects the malformed rows.
- [ ] Ensure valid trace round-trip tests continue to pass.

## H2.3 Audit witness

- [ ] Update the S4 audit to witness the new count invariants in source.
- [ ] Update the S4 audit to witness the new malformed-trace tests.

## H2 gate

- [ ] Impossible diagnostic count combinations fail closed through the strict trace path.

---

# Task H3: Fail-visible tuning-output staging cleanup — NOT STARTED

## H3.1 Source cleanup behavior

- [ ] Replace silent `let _ = fs::remove_dir_all(&staging);` behavior in `publish_output_directory()`.
- [ ] Preserve the original publication failure as the primary error.
- [ ] Add deterministic secondary context or stderr warning when staging cleanup fails.
- [ ] Do not retry into a different output directory.
- [ ] Do not delete or overwrite an existing output directory.
- [ ] Do not hide cleanup failure with `|| true`, ignored result, or equivalent behavior.

## H3.2 Tests

- [ ] Add or update tests if the cleanup path can be exercised deterministically.
- [ ] If direct filesystem cleanup failure is impractical to test portably, document why and rely on source/audit witness for the no-silent-discard invariant.

## H3.3 Audit witness

- [ ] Update the S4 audit to reject the silent cleanup-discard pattern.
- [ ] Update the S4 audit to witness the replacement fail-visible cleanup behavior.

## H3 gate

- [ ] Tuning-output staging cleanup failure cannot disappear silently.

---

# Task H4: Canonical tuning source-commit parsing — NOT STARTED

## H4.1 Source parser hardening

- [ ] Update `parse_source_commit()` in `crates/chess-tools/src/tuning_cli.rs` to require exactly 40 lowercase hexadecimal characters.
- [ ] Continue rejecting all-zero source commits.
- [ ] Preserve existing binary commit identity for valid lowercase inputs.
- [ ] Preserve tuning-config checksum binding to exact config text.

## H4.2 Tests

- [ ] Add a lowercase valid commit test.
- [ ] Add an uppercase commit rejection test.
- [ ] Add a mixed-case commit rejection test.
- [ ] Keep short/invalid/all-zero rejection tests.

## H4.3 Audit witness

- [ ] Update the S4 audit to witness lowercase-only parsing.
- [ ] Update the S4 audit to witness uppercase/mixed-case rejection tests.

## H4 gate

- [ ] Tuning config `source_commit` text is canonical and consistent with S4 trace parsing style.

---

# Task H5: Checkpoint materialization API review — NOT STARTED

## H5.1 Caller inventory

- [ ] Search all callers of `SpsaCheckpoint::current_weights`.
- [ ] Determine whether any production or S4 workflow relies on the current all-mask projection behavior.
- [ ] Record the caller inventory in the implementation report.

## H5.2 API decision

Choose one path and complete it:

- [ ] Path A: add or change an API to require explicit projection mask/reference values for checkpoint materialization.
- [ ] Path B: make `current_weights` private or test-only if no public caller needs it.
- [ ] Path C: document and test the current method as intentional raw full-vector projection.

## H5.3 Safety proof

- [ ] Prove resume validation still rejects mismatched dataset/config/objectives.
- [ ] Prove inactive parameters cannot escape through S4 candidate publication.
- [ ] Prove the selected API decision does not change production evaluator/search behavior.

## H5.4 Audit witness

- [ ] Update the S4 audit to witness the API decision.
- [ ] Add or update tests for the chosen behavior.

## H5 gate

- [ ] Checkpoint materialization semantics are explicit, tested, and safe against inactive-parameter escape.

---

# Task H6: Permanent audit and workflow integration — NOT STARTED

## H6.1 S4 audit update

- [ ] Update `scripts/task_s4_evaluation_tuning_calibration_audit.sh` to require the H1-H5 hardening evidence.
- [ ] Keep all existing no-promotion checks.
- [ ] Keep all existing temporary-control rejection checks.
- [ ] Keep all existing production identity checks.
- [ ] Keep S3/S4 historical closure awareness.

## H6.2 Workflow check

- [ ] Confirm `.github/workflows/s4-evaluation-tuning-calibration.yml` remains read-only.
- [ ] Confirm no temporary hardening helper/workflow remains after closure.
- [ ] Confirm permanent workflow runs strict Clippy and full `chess-tune`/`chess-tools` regressions.

## H6 gate

- [ ] Permanent audits fail closed on the new hardening requirements.

---

# Task H7: Final implementation report and authority cleanup — NOT STARTED

## H7.1 Implementation report

- [ ] Create `docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_IMPLEMENTATION_REPORT.md`.
- [ ] Record baseline SHA and final hardening SHA.
- [ ] Record every source file changed.
- [ ] Record final-SHA evidence correction outcome.
- [ ] Record diagnostic-count validation changes.
- [ ] Record malformed-trace tests.
- [ ] Record staging-cleanup behavior change.
- [ ] Record source-commit parser change.
- [ ] Record checkpoint materialization API decision.
- [ ] Record audit/workflow updates.
- [ ] Confirm no production activation or version/API behavior change.

## H7.2 TODO closure

- [ ] Mark every completed task/subtask in this TODO.
- [ ] Move this TODO from active authority to historical inventory when hardening closes.
- [ ] Update `docs/LEGACY_TODO_INDEX.md` counts/classification.
- [ ] Confirm no other active implementation TODO remains.

## H7.3 Final validation

- [ ] Run permanent S4 Evaluation Tuning Calibration workflow.
- [ ] Run strict workspace CI.
- [ ] Run Performance workflow or explicitly justify if unchanged hot-path behavior makes it unnecessary.
- [ ] Run Robustness workflow.
- [ ] Run Android/JNI workflow or explicitly justify if adapter-facing behavior is unchanged.
- [ ] Run report-publication validation.
- [ ] Record exact final SHA, run IDs, job IDs, artifact IDs, and checksums.

## H7 gate

- [ ] S4 closure hardening is truthfully closed with exact evidence and no production promotion.

---

# Final hardening completion checklist

- [ ] H0 authority and baseline freeze complete.
- [ ] H1 final S4 validation evidence correction complete.
- [ ] H2 strict diagnostic-count validation complete.
- [ ] H3 fail-visible tuning-output staging cleanup complete.
- [ ] H4 canonical tuning source-commit parsing complete.
- [ ] H5 checkpoint materialization API review complete.
- [ ] H6 permanent audit/workflow integration complete.
- [ ] H7 final report and authority cleanup complete.
