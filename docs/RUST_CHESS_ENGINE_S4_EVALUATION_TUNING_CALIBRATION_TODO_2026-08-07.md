# Rust Chess Engine S4 Evaluation Tuning Calibration TODO — 2026-08-07

**Status:** Closure candidate — S4-0 through S4-11 complete; S4-12 exact final validation pending
**Date:** 2026-08-07  
**Branch:** `master`  
**Planning baseline SHA:** `543dce22e51e71f821e37754a97ce0f33c3be122`  
**Specification:** `docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_SPEC_2026-08-07.md`  
**S3 closure report:** `docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_IMPLEMENTATION_REPORT.md`

---

## Status rules

- `[x]` means the item is resolved: implemented/tested with evidence, or explicitly dispositioned as not applicable inside a conditional branch.
- `[ ]` means incomplete.
- `SKIPPED` means a conditional task was correctly not run because its stated precondition was not met.
- `REJECTED` means the evaluated method/candidate failed a predeclared gate and cannot be reused as positive evidence.
- `DEFERRED` means intentionally not executed and carrying no production claim.
- S4 is active authority for optimizer/tuning-signal calibration.
- S4 cannot activate an evaluator candidate or change package/UCI version.
- Workflow success, training-loss improvement, or parameter movement alone cannot authorize release.
- First-party failures must be fixed at source unless explicitly classified as an external notice.
- No lint suppression, hidden fallback, output filtering, ignored failure, or weakened gate is acceptable.

---

# Task S4-0: Authority registration and baseline freeze — COMPLETE

## S4-0.1 Authority registration

- [x] Register this TODO as the single active implementation tracker in `docs/LEGACY_TODO_INDEX.md`.
- [x] Classify the closed S3 TODO as historical.
- [x] Confirm the completed Rust-port tracker and task definitions remain completion authority.
- [x] Update the permanent TODO-authority audit to reject unclassified active TODO additions.
- [x] Confirm no other active top-level `docs/*TODO*.md` remains.

## S4-0.2 Exact baseline identity

- [x] Record exact current `master` SHA.
- [x] Record S3 final/closure SHA `543dce22e51e71f821e37754a97ce0f33c3be122`.
- [x] Record package/UCI version.
- [x] Record v0.1 search-policy identifier/checksum.
- [x] Record baseline evaluation-weight identifier/checksum/value count.
- [x] Record C ABI version.
- [x] Record public JNI/Kotlin surface identity.
- [x] Record opening-book default state.
- [x] Record tablebase/Syzygy default state.
- [x] Record S3 candidate-registry and provenance identities.
- [x] Record exact CI/performance/robustness/Android/S3 validation evidence inherited from closure.

## S4-0.3 Non-promotion proof

- [x] Confirm all S2 experimental search policies remain inactive.
- [x] Confirm all S3 tuning candidates remain `activated=false`.
- [x] Confirm production evaluator weights are still the v0.1 baseline.
- [x] Confirm no public adapter accepts experimental search-policy or S3 candidate selection.

## S4-0 gate

- [x] S4 begins from an exact, documented, non-promoted v0.1 baseline.

---

# Task S4-1: Reproduce and classify the S3 zero-movement result — COMPLETE

## S4-1.1 Controlled reproduction

- [x] Re-run one representative S3 masked tuning group with exact S3-equivalent inputs.
- [x] Re-run the full-existing-evaluator group with exact S3-equivalent inputs.
- [x] Confirm whether final candidate values remain identical to baseline.
- [x] Confirm whether training and validation loss deltas remain exactly zero.
- [x] Record exact source/config/dataset/mask identities.

## S4-1.2 Root-cause classification framework

For each reproduced run, distinguish and report:

- [x] Zero positive/negative perturbation loss difference.
- [x] Non-zero loss difference but zero estimated gradient after arithmetic.
- [x] Non-zero gradient but sub-integer proposed update.
- [x] Integer update cancelled by regularization.
- [x] Integer update clipped by configured bounds.
- [x] Candidate materialization/reporting defect.
- [x] Parameter-mask defect.
- [x] Dataset/loss insensitivity.
- [x] Other explicitly identified cause.

## S4-1.3 Evidence

- [x] Record per-iteration movement counts.
- [x] Record final changed-parameter count.
- [x] Record baseline/candidate value checksums.
- [x] Record exact run/job/artifact IDs.

## S4-1 gate

- [x] The S3 zero-movement behavior is reproducible and classified using direct evidence.

---

# Task S4-2: Versioned optimizer iteration trace — COMPLETE

## S4-2.1 Trace schema

- [x] Define a versioned S4 optimizer-trace schema.
- [x] Bind trace to source SHA.
- [x] Bind trace to tuning config checksum.
- [x] Bind trace to dataset manifest checksum.
- [x] Bind trace to parameter-mask fingerprint.
- [x] Bind trace to initial weight identity/checksum.
- [x] Bind trace to random seed.
- [x] Bind trace to iteration number and checkpoint identity.
- [x] Add canonical semantic checksum.

## S4-2.2 Per-iteration fields

- [x] Record perturbation-vector identity.
- [x] Record positive candidate identity and loss.
- [x] Record negative candidate identity and loss.
- [x] Record loss difference.
- [x] Record learning-rate schedule value.
- [x] Record perturbation-size schedule value.
- [x] Record regularization contribution.
- [x] Record active parameter count.
- [x] Record positive/negative/zero gradient-estimate counts.
- [x] Record min/max/mean absolute gradient estimate.
- [x] Record min/max/mean proposed floating-point update magnitude.
- [x] Record zero-after-quantization count.
- [x] Record non-zero integer update count.
- [x] Record clipped-update count.
- [x] Record resulting candidate value checksum.
- [x] Record resulting training and validation losses when available.

## S4-2.3 Strictness

- [x] Reject unknown trace schema.
- [x] Reject malformed/noncanonical trace text.
- [x] Reject duplicate or missing fields.
- [x] Reject checksum mismatch.
- [x] Reject config/dataset/mask/source mismatch.
- [x] Reject impossible counts or non-finite numeric values.
- [x] Use canonical locale-independent numeric serialization.

## S4-2.4 Tests

- [x] Add trace round-trip test.
- [x] Add checksum corruption test.
- [x] Add wrong-source/config/dataset/mask tests.
- [x] Add deterministic repeated-run trace test.
- [x] Add quantization-accounting known-answer test.

## S4-2 gate

- [x] Every optimizer update decision can be reconstructed from strict provenance-bound evidence.

---

# Task S4-3: Quantization and update-path diagnostics — COMPLETE

## S4-3.1 Floating-point versus integer movement

- [x] Expose proposed floating-point deltas before integer materialization.
- [x] Measure which proposed updates round to zero.
- [x] Measure which updates survive integer materialization.
- [x] Measure which updates are clipped by min/max bounds.
- [x] Measure regularization's contribution independently.

## S4-3.2 Invariants

- [x] Inactive parameters remain exactly unchanged.
- [x] Fixed structural slots remain exactly unchanged.
- [x] Active integer weights never exceed configured bounds.
- [x] Candidate value checksum changes iff effective runtime values change.
- [x] Reported changed-parameter count matches the dense runtime vector diff.

## S4-3.3 Tests

- [x] Add sub-integer update test that intentionally rounds to zero.
- [x] Add update test that survives quantization.
- [x] Add positive and negative clipping tests.
- [x] Add regularization-dominance test.
- [x] Add candidate-checksum movement test.

## S4-3 gate

- [x] Zero movement can no longer hide whether the cause was gradient, quantization, clipping, or regularization.

---

# Task S4-4: Single-parameter known-answer optimizer test — COMPLETE

## S4-4.1 Objective

- [x] Define a deterministic one-parameter synthetic objective with known optimum.
- [x] Start from a deliberately offset value.
- [x] Predeclare expected movement direction.
- [x] Predeclare acceptable convergence tolerance.

## S4-4.2 Validation

- [x] Prove first effective update moves toward the optimum.
- [x] Prove final value is closer to the optimum than initial value.
- [x] Prove result is deterministic for fixed seed/config.
- [x] Prove changed seed changes stochastic provenance identity.
- [x] Prove bounds remain enforced.

## S4-4 gate

- [x] SPSA can demonstrably solve a one-dimensional known-answer objective.

---

# Task S4-5: Multi-parameter known-answer optimizer test — COMPLETE

## S4-5.1 Objective

- [x] Define a deterministic bounded multi-parameter objective with a known optimum.
- [x] Include mixed positive and negative expected update directions.
- [x] Include inactive parameters in the surrounding vector.

## S4-5.2 Validation

- [x] Active parameters move in expected directions.
- [x] Inactive parameters never move.
- [x] Bounds are respected.
- [x] Regularization behavior matches the declared objective.
- [x] Resume result equals uninterrupted result exactly.
- [x] Checkpoint/config/mask identity mismatches fail closed.

## S4-5 gate

- [x] SPSA can solve a controlled multi-parameter problem without violating masks, bounds, or resume determinism.

---

# Task S4-6: Deliberately degraded chess-evaluator recovery — COMPLETE

## S4-6.1 Test-only degraded variants

- [x] Define at least one test-only degraded evaluator with materially incorrect piece values.
- [x] PST/activity degraded variant reviewed and not required after material recovery proved the intended chess-loss path.
- [x] Assign explicit inactive/test-only identities.
- [x] Prevent production UCI/safe Rust/C ABI/JNI/Android selection.

## S4-6.2 Recovery dataset

- [x] Define deterministic chess positions/results suitable for detecting the degradation.
- [x] Bind dataset to exact provenance.
- [x] Keep train/validation split explicit.

## S4-6.3 Recovery test

- [x] Predeclare target direction or target baseline values.
- [x] Run bounded tuning from the degraded evaluator.
- [x] Prove at least one degraded parameter moves toward the target.
- [x] Prove training loss improves.
- [x] Prove held-out behavior does not violate the predeclared tolerance.
- [x] Prove candidate remains inactive/test-only.

## S4-6 gate

- [x] The tuning stack can recover measurable chess-evaluation signal from a deliberately worse starting point.

---

# Task S4-7: Stronger deterministic calibration corpus — COMPLETE

## S4-7.1 Corpus specification

- [x] Define opening suite identity.
- [x] Define deterministic random seed.
- [x] Define game count.
- [x] Define maximum plies.
- [x] Define claimable-draw policy.
- [x] Define opening-row eligibility policy.
- [x] Define train/validation/test split.
- [x] Define unfinished-game ceiling.
- [x] Define minimum training and validation occurrences.

## S4-7.2 Search-resource policy

- [x] Prefer fixed-node limits for deterministic calibration.
- [x] Define white/black node budgets.
- [x] Define TT budgets.
- [x] Define check-extension policy.
- [x] Reject implicit clock/default resource selection.

## S4-7.3 Corpus scales

- [x] Generate a medium bounded calibration corpus.
- [x] Generate a larger/stronger bounded calibration corpus.
- [x] Prove repeated generation with identical inputs is byte-identical.
- [x] Compare position diversity and occurrence counts between scales.
- [x] Keep generated datasets out of Git unless artifact policy explicitly permits them.

## S4-7.4 Admission

- [x] Reject malformed games/rows/results.
- [x] Reject excessive unfinished games.
- [x] Reject insufficient training/validation occurrences.
- [x] Record exact dataset and manifest checksums.
- [x] Record exact invocation and source SHA.

## S4-7 gate

- [x] S4 has a stronger deterministic, admitted, provenance-bound corpus suitable for tuning-signal experiments.

---

# Task S4-8: Predeclared hyperparameter calibration matrix — COMPLETE

## S4-8.1 Matrix definition

- [x] Predeclare bounded learning-rate choices.
- [x] Predeclare bounded perturbation-size choices.
- [x] Predeclare decay choices if varied.
- [x] Predeclare stability-constant choices if varied.
- [x] Predeclare regularization choices.
- [x] Predeclare iteration counts.
- [x] Bound total experiment count before execution.
- [x] Record matrix checksum/identity.

## S4-8.2 Execution policy

- [x] Use identical admitted dataset and split for comparable runs.
- [x] Use explicit parameter group/mask.
- [x] Use deterministic seeds declared before results are inspected.
- [x] Do not rerun selectively to cherry-pick favorable stochastic outcomes.

## S4-8.3 Required report fields

For every run:

- [x] Config identity.
- [x] Dataset identity.
- [x] Mask identity.
- [x] Initial/final training loss.
- [x] Initial/final held-out loss.
- [x] Effective changed-parameter count.
- [x] Maximum absolute parameter delta.
- [x] Mean absolute parameter delta.
- [x] Zero-after-quantization count.
- [x] Clipping count.
- [x] Candidate value checksum.
- [x] `activated=false`.
- [x] Advancement/rejection disposition.

## S4-8 gate

- [x] Hyperparameter calibration is bounded, predeclared, reproducible, and not cherry-picked.

---

# Task S4-9: Real-data tuning-signal experiment — COMPLETE (METHOD ADVANCED)

## S4-9.1 Preflight

- [x] Select configuration only from S4-8 evidence.
- [x] Freeze source SHA.
- [x] Freeze admitted dataset identity.
- [x] Freeze mask/group identity.
- [x] Freeze random seed and iteration count.
- [x] Freeze held-out regression tolerance.
- [x] Keep baseline evaluator untouched.

## S4-9.2 Required advancement evidence

- [x] Effective changed-parameter count is greater than zero.
- [x] Candidate value checksum differs from baseline.
- [x] Training loss improves by more than zero.
- [x] Held-out loss does not regress beyond the frozen tolerance.
- [x] Repeated run with identical inputs yields identical candidate checksum.
- [x] Candidate registry accepts the artifact.
- [x] Candidate remains `activated=false`.
- [x] Production defaults remain baseline.

## S4-9.3 Failure path — NOT APPLICABLE (S4-9 PASSED)

If no bounded configuration passes:

- [x] Record `method_rejected` or `deferred` explicitly.
- [x] Identify whether failure is optimizer, quantization, loss, or data related.
- [x] Recommend the next tuning method or representation to evaluate.
- [x] Do not proceed to evaluator-feature work under the current method.

## S4-9 gate

- [x] A reproducible non-zero real-data tuning signal exists, or the current method is truthfully rejected/deferred.

---

# Task S4-10: Optional development chess-strength smoke — COMPLETE (DEVELOPMENT STRENGTH REJECTED; NO PROMOTION)

## S4-10.1 Preconditions

- [x] S4-9 produced a non-zero candidate satisfying all advancement evidence.
- [x] Candidate source/artifact identities are frozen.
- [x] Correctness pre-gates pass.

## S4-10.2 Match

- [x] Run a small paired fixed-resource match versus untouched v0.1.
- [x] Use color-swapped openings.
- [x] Use equal node/time resources.
- [x] Use independent TTs.
- [x] Record W/D/L, unfinished games, illegal moves, crashes, and infrastructure failures separately.
- [x] Keep report `activated=false` regardless of score.

## S4-10 gate

- [x] Development smoke is completed for a genuinely changed candidate, or correctly marked `SKIPPED` because S4-9 did not advance one.

---

# Task S4-11: Method disposition and S5 readiness — COMPLETE (METHOD ACCEPTED FOR S5 EXPERIMENTATION)

## S4-11.1 Accept-current-method path

If S4-9 passes:

- [x] Record the optimizer/tuning configuration family as validated for future evaluator experimentation.
- [x] Record limitations and safe operating bounds.
- [x] Identify which parameter groups showed measurable signal.
- [x] Define requirements for a future S5 evaluator-feature program.

## S4-11.2 Reject-current-method path — NOT APPLICABLE (S4-9 PASSED)

If S4-9 fails:

- [x] Record the current SPSA/integer-weight method as rejected or insufficient for real-data tuning under tested bounds.
- [x] Preserve known-answer evidence separately from real-data failure.
- [x] Recommend next method candidates, such as higher-precision latent parameters with quantized export, coordinate/gradient-free alternatives, Texel-style optimization, or another explicitly specified approach.
- [x] Do not claim S5 evaluator-feature readiness under an unvalidated optimizer.

## S4-11 gate

- [x] The project has an explicit, evidence-backed tuning-method disposition and next-step recommendation.

---

# Task S4-12: Final report and closure — IN PROGRESS (EXACT FINAL VALIDATION PENDING)

## S4-12.1 Final implementation report

- [x] Create `docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_IMPLEMENTATION_REPORT.md`.
- [ ] Record exact baseline and final SHAs.
- [x] Record root cause(s) of S3 zero movement.
- [x] Record optimizer-trace schema/identity.
- [x] Record single-parameter known-answer result.
- [x] Record multi-parameter known-answer result.
- [x] Record degraded-evaluator recovery result.
- [x] Record corpus identities/statistics.
- [x] Record hyperparameter matrix and all dispositions.
- [x] Record S4-9 real-data result.
- [x] Record S4-10 development smoke or explicit skip.
- [x] Record final tuning-method disposition.
- [x] Confirm no activation occurred.

## S4-12.2 Authority cleanup

- [ ] Move this TODO from active authority to historical inventory when S4 closes.
- [ ] Update `docs/LEGACY_TODO_INDEX.md` counts/classification.
- [ ] Update permanent TODO-authority audit.
- [x] Confirm no temporary S4 staging helper remains.
- [x] Confirm generated artifacts follow repository policy.

## S4-12.3 Exact final validation

- [ ] Run permanent S4 audit.
- [ ] Run strict workspace CI.
- [ ] Run performance validation if hot-path code changed.
- [ ] Run robustness validation.
- [ ] Run Android/JNI validation if adapter-facing code changed.
- [ ] Run report validation.
- [ ] Record exact final SHA, run IDs, job IDs, artifact IDs, and checksums.

## S4-12 gate

- [ ] S4 is truthfully closed with exact evidence and no production activation.

---

# Final S4 completion checklist

- [x] S4-0 authority and baseline freeze complete.
- [x] S4-1 S3 zero-movement reproduction/classification complete.
- [x] S4-2 optimizer iteration trace complete.
- [x] S4-3 quantization/update diagnostics complete.
- [x] S4-4 single-parameter known-answer test complete.
- [x] S4-5 multi-parameter known-answer test complete.
- [x] S4-6 degraded chess-evaluator recovery complete.
- [x] S4-7 stronger deterministic corpus complete.
- [x] S4-8 bounded hyperparameter calibration complete.
- [x] S4-9 real-data tuning-signal gate complete or method rejected/deferred.
- [x] S4-10 development strength smoke complete or explicitly skipped.
- [x] S4-11 method disposition and next-step recommendation complete.
- [ ] S4-12 final report and closure complete.
