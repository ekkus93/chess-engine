# Rust Chess Engine S4 Closure Hardening Spec — 2026-08-07

**Status:** Complete — closure hardening validated; no production promotion
**Date:** 2026-08-07
**Branch:** `master`
**Planning baseline SHA:** `bc406d78d673cc3258e8b522bcec25c4838f5e32`
**Implementation-start SHA:** `9f5c398a70e22228454f0184225a414f1466cdf5`
**Companion TODO:** `docs/RUST_CHESS_ENGINE_S4_CLOSURE_HARDENING_TODO_2026-08-07.md`
**Source review:** Post-S4 code review of final `master` closure state

---

## 1. Purpose

S4 successfully closed the evaluation-tuning calibration program without promoting an evaluator candidate. The post-closure review found that the implementation is broadly sound, but two archive-hardening issues and several smaller cleanup items should be addressed before the S4 evidence set is treated as fully clean:

1. the repository records a complete pre-closure validation matrix, but does not yet record the completed final post-closure validation matrix for SHA `bc406d78d673cc3258e8b522bcec25c4838f5e32` in the S4 evidence documents;
2. the S4 optimizer trace parser validates many invariants, but its diagnostic count validation does not reject every impossible quantization/update-count combination;
3. a staging-cleanup error in `publish_output_directory()` can be silently discarded after a primary publication failure;
4. tuning-config `source_commit` parsing is less canonical than the strict trace parser;
5. `SpsaCheckpoint::current_weights(bounds)` can be misleading because it projects raw checkpoint parameters with `TunableParameterMask::all()` instead of making the intended projection mask explicit.

This hardening pass is deliberately small and archival. It should improve evidence fidelity, strict trace validation, and API clarity. It must not reopen S4 tuning, alter production evaluator behavior, or promote any experimental candidate.

---

## 2. Scope

This program covers only S4 closure/evidence hardening and first-party correctness cleanup around the reviewed issues.

In scope:

- final-SHA evidence documentation for the already-validated final S4 closure head;
- stronger impossible-count rejection in `SpsaIterationDiagnostics::validate_counts()` and trace parser regressions;
- fail-visible staging cleanup behavior in `crates/chess-tools/src/tuning_cli.rs`;
- canonical lowercase `source_commit` parsing for tuning config text;
- API review and fix or documentation for checkpoint materialization/projection;
- permanent audit updates that lock the corrected evidence and invariants;
- exact final validation after the hardening commit.

Out of scope:

- no new tuning experiment;
- no new self-play corpus;
- no hyperparameter changes;
- no candidate activation;
- no evaluator weight promotion;
- no chess-strength claim;
- no package/UCI version bump;
- no public search-policy selector;
- no ABI, JNI, Kotlin, Android, opening-default, or tablebase behavior change.

---

## 3. Baseline state

The planning baseline is final S4 closure SHA:

`bc406d78d673cc3258e8b522bcec25c4838f5e32`

At this baseline:

- S4 is closed and historical;
- there is no active implementation TODO;
- package/UCI version remains `0.1.0`;
- production v0.1 evaluator/search authority remains unchanged;
- selected S4 candidate value checksum `520db5dd58086a8a` remains rejected by development strength evidence;
- no S2, S3, or S4 experimental candidate is activated;
- permanent CI, Performance, Robustness, Android/JNI, S4, and report-publication gates passed on the final closure head during the Ralph loop, but those final run/job IDs are not fully captured in the repository evidence files.

The hardening pass must treat this baseline as production-stable. Any behavior-changing Rust code edit must be justified as validation/error-reporting/API-safety work, not strength work.

---

## 4. Required outcomes

### 4.1 Final validation evidence addendum

The repository must contain a clear S4 final-validation addendum or equivalent updates to the S4 final report/TODO that record:

- final validated SHA `bc406d78d673cc3258e8b522bcec25c4838f5e32`;
- final exact-SHA CI run/job IDs;
- final exact-SHA Performance run/job IDs;
- final exact-SHA Robustness run/job IDs;
- final exact-SHA Android/JNI run/job IDs;
- final exact-SHA S4 Evaluation Tuning Calibration run/job IDs;
- final exact-SHA report-publication run/job ID;
- any final artifact IDs/checksums relevant to S4 closure evidence;
- a distinction between pre-closure implementation SHA `b66b256a5b81621ba5310a749b7b93e650cc6067` and final closed SHA `bc406d78d673cc3258e8b522bcec25c4838f5e32`.

The addendum must not reinterpret the selected S4 candidate as accepted strength evidence. It must preserve the disposition: method accepted for future controlled evaluator experimentation; selected candidate rejected; no production promotion.

### 4.2 Strict S4 diagnostic count invariants

`SpsaIterationDiagnostics::validate_counts()` must reject impossible diagnostic count combinations. At minimum, it must enforce:

- `active_parameter_count <= TUNABLE_PARAMETER_COUNT`;
- `positive_gradient_count + negative_gradient_count + zero_gradient_count == active_parameter_count` using checked arithmetic;
- `zero_after_quantization_count + nonzero_integer_update_count <= active_parameter_count` using checked arithmetic;
- `changed_parameter_count == nonzero_integer_update_count`;
- `clipped_update_count <= active_parameter_count`;
- no count combination can overflow or silently wrap;
- existing valid S4 traces still parse.

The implementation must not weaken trace schema, checksum, canonical text, provenance binding, non-finite rejection, or iteration sequencing.

### 4.3 Malformed-trace regression coverage

Add focused tests that prove the strict trace parser rejects:

- quantization/update counts whose sum exceeds `active_parameter_count`;
- `changed_parameter_count` that differs from `nonzero_integer_update_count`;
- any overflow-prone count combination if representable through the diagnostic structure;
- the existing impossible gradient-count case must continue to fail.

These tests should exercise the canonical trace validation path, not only a private helper, unless a private helper test is paired with at least one parser-level rejection test.

### 4.4 Fail-visible staging cleanup

`publish_output_directory()` currently attempts to delete its staging directory after an error, but discards cleanup failure. Replace that behavior with fail-visible cleanup reporting.

Acceptable implementations:

- include cleanup failure as secondary context in the returned error;
- or print a deterministic warning to stderr while preserving the original failure;
- or explicitly return a structured combined error string.

Unacceptable implementations:

- `let _ = ...` on cleanup failure;
- `|| true`-style hiding;
- silently retrying into a different output path;
- deleting or overwriting existing output directories.

### 4.5 Canonical tuning source commit parsing

`TuningFileConfig::parse` should reject non-canonical `source_commit` text. The parser should require exactly 40 lowercase hexadecimal characters and reject all-zero commits.

The implementation must preserve the existing binary identity semantics while making the text format align with the stricter S4 trace parser.

### 4.6 Checkpoint materialization API clarity

Review `SpsaCheckpoint::current_weights(bounds)`. The current method projects with `TunableParameterMask::all()`, which can be misleading for raw checkpoints because optimizer masks are not part of the method signature.

One of the following outcomes is required:

- change or add an API that takes an explicit `TunableParameterMask` and reference values before materializing raw checkpoint parameters;
- make `current_weights` private or test-only if no public caller needs it;
- or document and test the current behavior as intentional raw full-vector projection, while ensuring no S4/public workflow depends on it incorrectly.

The chosen outcome must preserve resume validation and must not allow inactive parameters to escape into production artifacts.

### 4.7 Permanent audit updates

The permanent S4 audit must be updated to witness:

- final-SHA evidence addendum or updated final report content;
- stronger diagnostic-count invariants;
- malformed-trace tests for impossible quantization/update counts;
- absence of silent staging cleanup discard;
- canonical lowercase source commit parsing;
- the checkpoint materialization decision;
- continued no-promotion state;
- absence of temporary S4 staging controls.

The audit must remain fail-closed and must not rely solely on prose if a source-level invariant can be witnessed directly.

---

## 5. Validation requirements

Before closure, run and record the exact SHA for:

- permanent S4 Evaluation Tuning Calibration workflow;
- strict workspace CI;
- Performance workflow if any hot-path or workspace-significant Rust code changed;
- Robustness workflow;
- Android/JNI workflow if any adapter-facing identity might have changed, or explicitly record why it is unchanged;
- report-publication validation.

The final report must explicitly state whether any validation was skipped and why. Because this pass touches shared Rust crates and evidence/audit infrastructure, the expected default is to run the full permanent matrix.

---

## 6. Safety and non-promotion constraints

This hardening pass must preserve all of the following:

- package/UCI version remains `0.1.0`;
- production evaluator remains v0.1 baseline;
- production search policy remains v0.1 baseline;
- S4 candidate `520db5dd58086a8a` remains inactive and rejected as strength evidence;
- no new candidate is activated;
- no adapter accepts experimental candidate selection;
- no ABI/JNI/Kotlin/Android behavior changes;
- opening-book default remains disabled/explicit-only;
- tablebases remain disabled/absent by default;
- no Python/subprocess fallback is added to production Rust;
- no lint suppression or weakened gate is introduced;
- no temporary write-capable workflow remains after closure.

---

## 7. Completion definition

This program is complete only when:

1. the evidence gap is closed with final-SHA validation records;
2. impossible S4 trace count combinations fail closed;
3. staging cleanup failure is visible;
4. tuning `source_commit` parsing is canonical or explicitly justified by tests and docs;
5. checkpoint materialization semantics are safe and documented/tested;
6. permanent audits enforce the corrections;
7. all permanent validation gates pass on the final exact SHA;
8. the TODO is moved from active to historical, if it is registered as active during implementation;
9. no production promotion or version/API behavior change occurred.
