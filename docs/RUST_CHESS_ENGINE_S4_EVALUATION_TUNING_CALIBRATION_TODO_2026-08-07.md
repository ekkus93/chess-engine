# Rust Chess Engine S4 Evaluation Tuning Calibration TODO — 2026-08-07

**Status:** Active — not yet implemented  
**Date:** 2026-08-07  
**Branch:** `master`  
**Planning baseline SHA:** `543dce22e51e71f821e37754a97ce0f33c3be122`  
**Specification:** `docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_SPEC_2026-08-07.md`  
**S3 closure report:** `docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_IMPLEMENTATION_REPORT.md`

---

## Status rules

- `[x]` means implemented, documented, tested, and supported by exact validation evidence.
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

# Task S4-0: Authority registration and baseline freeze — NOT STARTED

## S4-0.1 Authority registration

- [ ] Register this TODO as the single active implementation tracker in `docs/LEGACY_TODO_INDEX.md`.
- [ ] Classify the closed S3 TODO as historical.
- [ ] Confirm the completed Rust-port tracker and task definitions remain completion authority.
- [ ] Update the permanent TODO-authority audit to reject unclassified active TODO additions.
- [ ] Confirm no other active top-level `docs/*TODO*.md` remains.

## S4-0.2 Exact baseline identity

- [ ] Record exact current `master` SHA.
- [ ] Record S3 final/closure SHA `543dce22e51e71f821e37754a97ce0f33c3be122`.
- [ ] Record package/UCI version.
- [ ] Record v0.1 search-policy identifier/checksum.
- [ ] Record baseline evaluation-weight identifier/checksum/value count.
- [ ] Record C ABI version.
- [ ] Record public JNI/Kotlin surface identity.
- [ ] Record opening-book default state.
- [ ] Record tablebase/Syzygy default state.
- [ ] Record S3 candidate-registry and provenance identities.
- [ ] Record exact CI/performance/robustness/Android/S3 validation evidence inherited from closure.

## S4-0.3 Non-promotion proof

- [ ] Confirm all S2 experimental search policies remain inactive.
- [ ] Confirm all S3 tuning candidates remain `activated=false`.
- [ ] Confirm production evaluator weights are still the v0.1 baseline.
- [ ] Confirm no public adapter accepts experimental search-policy or S3 candidate selection.

## S4-0 gate

- [ ] S4 begins from an exact, documented, non-promoted v0.1 baseline.

---

# Task S4-1: Reproduce and classify the S3 zero-movement result — NOT STARTED

## S4-1.1 Controlled reproduction

- [ ] Re-run one representative S3 masked tuning group with exact S3-equivalent inputs.
- [ ] Re-run the full-existing-evaluator group with exact S3-equivalent inputs.
- [ ] Confirm whether final candidate values remain identical to baseline.
- [ ] Confirm whether training and validation loss deltas remain exactly zero.
- [ ] Record exact source/config/dataset/mask identities.

## S4-1.2 Root-cause classification framework

For each reproduced run, distinguish and report:

- [ ] Zero positive/negative perturbation loss difference.
- [ ] Non-zero loss difference but zero estimated gradient after arithmetic.
- [ ] Non-zero gradient but sub-integer proposed update.
- [ ] Integer update cancelled by regularization.
- [ ] Integer update clipped by configured bounds.
- [ ] Candidate materialization/reporting defect.
- [ ] Parameter-mask defect.
- [ ] Dataset/loss insensitivity.
- [ ] Other explicitly identified cause.

## S4-1.3 Evidence

- [ ] Record per-iteration movement counts.
- [ ] Record final changed-parameter count.
- [ ] Record baseline/candidate value checksums.
- [ ] Record exact run/job/artifact IDs.

## S4-1 gate

- [ ] The S3 zero-movement behavior is reproducible and classified using direct evidence.

---

# Task S4-2: Versioned optimizer iteration trace — NOT STARTED

## S4-2.1 Trace schema

- [ ] Define a versioned S4 optimizer-trace schema.
- [ ] Bind trace to source SHA.
- [ ] Bind trace to tuning config checksum.
- [ ] Bind trace to dataset manifest checksum.
- [ ] Bind trace to parameter-mask fingerprint.
- [ ] Bind trace to initial weight identity/checksum.
- [ ] Bind trace to random seed.
- [ ] Bind trace to iteration number and checkpoint identity.
- [ ] Add canonical semantic checksum.

## S4-2.2 Per-iteration fields

- [ ] Record perturbation-vector identity.
- [ ] Record positive candidate identity and loss.
- [ ] Record negative candidate identity and loss.
- [ ] Record loss difference.
- [ ] Record learning-rate schedule value.
- [ ] Record perturbation-size schedule value.
- [ ] Record regularization contribution.
- [ ] Record active parameter count.
- [ ] Record positive/negative/zero gradient-estimate counts.
- [ ] Record min/max/mean absolute gradient estimate.
- [ ] Record min/max/mean proposed floating-point update magnitude.
- [ ] Record zero-after-quantization count.
- [ ] Record non-zero integer update count.
- [ ] Record clipped-update count.
- [ ] Record resulting candidate value checksum.
- [ ] Record resulting training and validation losses when available.

## S4-2.3 Strictness

- [ ] Reject unknown trace schema.
- [ ] Reject malformed/noncanonical trace text.
- [ ] Reject duplicate or missing fields.
- [ ] Reject checksum mismatch.
- [ ] Reject config/dataset/mask/source mismatch.
- [ ] Reject impossible counts or non-finite numeric values.
- [ ] Use canonical locale-independent numeric serialization.

## S4-2.4 Tests

- [ ] Add trace round-trip test.
- [ ] Add checksum corruption test.
- [ ] Add wrong-source/config/dataset/mask tests.
- [ ] Add deterministic repeated-run trace test.
- [ ] Add quantization-accounting known-answer test.

## S4-2 gate

- [ ] Every optimizer update decision can be reconstructed from strict provenance-bound evidence.

---

# Task S4-3: Quantization and update-path diagnostics — NOT STARTED

## S4-3.1 Floating-point versus integer movement

- [ ] Expose proposed floating-point deltas before integer materialization.
- [ ] Measure which proposed updates round to zero.
- [ ] Measure which updates survive integer materialization.
- [ ] Measure which updates are clipped by min/max bounds.
- [ ] Measure regularization's contribution independently.

## S4-3.2 Invariants

- [ ] Inactive parameters remain exactly unchanged.
- [ ] Fixed structural slots remain exactly unchanged.
- [ ] Active integer weights never exceed configured bounds.
- [ ] Candidate value checksum changes iff effective runtime values change.
- [ ] Reported changed-parameter count matches the dense runtime vector diff.

## S4-3.3 Tests

- [ ] Add sub-integer update test that intentionally rounds to zero.
- [ ] Add update test that survives quantization.
- [ ] Add positive and negative clipping tests.
- [ ] Add regularization-dominance test.
- [ ] Add candidate-checksum movement test.

## S4-3 gate

- [ ] Zero movement can no longer hide whether the cause was gradient, quantization, clipping, or regularization.

---

# Task S4-4: Single-parameter known-answer optimizer test — NOT STARTED

## S4-4.1 Objective

- [ ] Define a deterministic one-parameter synthetic objective with known optimum.
- [ ] Start from a deliberately offset value.
- [ ] Predeclare expected movement direction.
- [ ] Predeclare acceptable convergence tolerance.

## S4-4.2 Validation

- [ ] Prove first effective update moves toward the optimum.
- [ ] Prove final value is closer to the optimum than initial value.
- [ ] Prove result is deterministic for fixed seed/config.
- [ ] Prove changed seed changes stochastic provenance identity.
- [ ] Prove bounds remain enforced.

## S4-4 gate

- [ ] SPSA can demonstrably solve a one-dimensional known-answer objective.

---

# Task S4-5: Multi-parameter known-answer optimizer test — NOT STARTED

## S4-5.1 Objective

- [ ] Define a deterministic bounded multi-parameter objective with a known optimum.
- [ ] Include mixed positive and negative expected update directions.
- [ ] Include inactive parameters in the surrounding vector.

## S4-5.2 Validation

- [ ] Active parameters move in expected directions.
- [ ] Inactive parameters never move.
- [ ] Bounds are respected.
- [ ] Regularization behavior matches the declared objective.
- [ ] Resume result equals uninterrupted result exactly.
- [ ] Checkpoint/config/mask identity mismatches fail closed.

## S4-5 gate

- [ ] SPSA can solve a controlled multi-parameter problem without violating masks, bounds, or resume determinism.

---

# Task S4-6: Deliberately degraded chess-evaluator recovery — NOT STARTED

## S4-6.1 Test-only degraded variants

- [ ] Define at least one test-only degraded evaluator with materially incorrect piece values.
- [ ] Define at least one test-only degraded evaluator with a distorted PST/activity term if useful.
- [ ] Assign explicit inactive/test-only identities.
- [ ] Prevent production UCI/safe Rust/C ABI/JNI/Android selection.

## S4-6.2 Recovery dataset

- [ ] Define deterministic chess positions/results suitable for detecting the degradation.
- [ ] Bind dataset to exact provenance.
- [ ] Keep train/validation split explicit.

## S4-6.3 Recovery test

- [ ] Predeclare target direction or target baseline values.
- [ ] Run bounded tuning from the degraded evaluator.
- [ ] Prove at least one degraded parameter moves toward the target.
- [ ] Prove training loss improves.
- [ ] Prove held-out behavior does not violate the predeclared tolerance.
- [ ] Prove candidate remains inactive/test-only.

## S4-6 gate

- [ ] The tuning stack can recover measurable chess-evaluation signal from a deliberately worse starting point.

---

# Task S4-7: Stronger deterministic calibration corpus — NOT STARTED

## S4-7.1 Corpus specification

- [ ] Define opening suite identity.
- [ ] Define deterministic random seed.
- [ ] Define game count.
- [ ] Define maximum plies.
- [ ] Define claimable-draw policy.
- [ ] Define opening-row eligibility policy.
- [ ] Define train/validation/test split.
- [ ] Define unfinished-game ceiling.
- [ ] Define minimum training and validation occurrences.

## S4-7.2 Search-resource policy

- [ ] Prefer fixed-node limits for deterministic calibration.
- [ ] Define white/black node budgets.
- [ ] Define TT budgets.
- [ ] Define check-extension policy.
- [ ] Reject implicit clock/default resource selection.

## S4-7.3 Corpus scales

- [ ] Generate a medium bounded calibration corpus.
- [ ] Generate a larger/stronger bounded calibration corpus.
- [ ] Prove repeated generation with identical inputs is byte-identical.
- [ ] Compare position diversity and occurrence counts between scales.
- [ ] Keep generated datasets out of Git unless artifact policy explicitly permits them.

## S4-7.4 Admission

- [ ] Reject malformed games/rows/results.
- [ ] Reject excessive unfinished games.
- [ ] Reject insufficient training/validation occurrences.
- [ ] Record exact dataset and manifest checksums.
- [ ] Record exact invocation and source SHA.

## S4-7 gate

- [ ] S4 has a stronger deterministic, admitted, provenance-bound corpus suitable for tuning-signal experiments.

---

# Task S4-8: Predeclared hyperparameter calibration matrix — NOT STARTED

## S4-8.1 Matrix definition

- [ ] Predeclare bounded learning-rate choices.
- [ ] Predeclare bounded perturbation-size choices.
- [ ] Predeclare decay choices if varied.
- [ ] Predeclare stability-constant choices if varied.
- [ ] Predeclare regularization choices.
- [ ] Predeclare iteration counts.
- [ ] Bound total experiment count before execution.
- [ ] Record matrix checksum/identity.

## S4-8.2 Execution policy

- [ ] Use identical admitted dataset and split for comparable runs.
- [ ] Use explicit parameter group/mask.
- [ ] Use deterministic seeds declared before results are inspected.
- [ ] Do not rerun selectively to cherry-pick favorable stochastic outcomes.

## S4-8.3 Required report fields

For every run:

- [ ] Config identity.
- [ ] Dataset identity.
- [ ] Mask identity.
- [ ] Initial/final training loss.
- [ ] Initial/final held-out loss.
- [ ] Effective changed-parameter count.
- [ ] Maximum absolute parameter delta.
- [ ] Mean absolute parameter delta.
- [ ] Zero-after-quantization count.
- [ ] Clipping count.
- [ ] Candidate value checksum.
- [ ] `activated=false`.
- [ ] Advancement/rejection disposition.

## S4-8 gate

- [ ] Hyperparameter calibration is bounded, predeclared, reproducible, and not cherry-picked.

---

# Task S4-9: Real-data tuning-signal experiment — NOT STARTED

## S4-9.1 Preflight

- [ ] Select configuration only from S4-8 evidence.
- [ ] Freeze source SHA.
- [ ] Freeze admitted dataset identity.
- [ ] Freeze mask/group identity.
- [ ] Freeze random seed and iteration count.
- [ ] Freeze held-out regression tolerance.
- [ ] Keep baseline evaluator untouched.

## S4-9.2 Required advancement evidence

- [ ] Effective changed-parameter count is greater than zero.
- [ ] Candidate value checksum differs from baseline.
- [ ] Training loss improves by more than zero.
- [ ] Held-out loss does not regress beyond the frozen tolerance.
- [ ] Repeated run with identical inputs yields identical candidate checksum.
- [ ] Candidate registry accepts the artifact.
- [ ] Candidate remains `activated=false`.
- [ ] Production defaults remain baseline.

## S4-9.3 Failure path

If no bounded configuration passes:

- [ ] Record `method_rejected` or `deferred` explicitly.
- [ ] Identify whether failure is optimizer, quantization, loss, or data related.
- [ ] Recommend the next tuning method or representation to evaluate.
- [ ] Do not proceed to evaluator-feature work under the current method.

## S4-9 gate

- [ ] A reproducible non-zero real-data tuning signal exists, or the current method is truthfully rejected/deferred.

---

# Task S4-10: Optional development chess-strength smoke — CONDITIONAL / NOT STARTED

## S4-10.1 Preconditions

- [ ] S4-9 produced a non-zero candidate satisfying all advancement evidence.
- [ ] Candidate source/artifact identities are frozen.
- [ ] Correctness pre-gates pass.

## S4-10.2 Match

- [ ] Run a small paired fixed-resource match versus untouched v0.1.
- [ ] Use color-swapped openings.
- [ ] Use equal node/time resources.
- [ ] Use independent TTs.
- [ ] Record W/D/L, unfinished games, illegal moves, crashes, and infrastructure failures separately.
- [ ] Keep report `activated=false` regardless of score.

## S4-10 gate

- [ ] Development smoke is completed for a genuinely changed candidate, or correctly marked `SKIPPED` because S4-9 did not advance one.

---

# Task S4-11: Method disposition and S5 readiness — NOT STARTED

## S4-11.1 Accept-current-method path

If S4-9 passes:

- [ ] Record the optimizer/tuning configuration family as validated for future evaluator experimentation.
- [ ] Record limitations and safe operating bounds.
- [ ] Identify which parameter groups showed measurable signal.
- [ ] Define requirements for a future S5 evaluator-feature program.

## S4-11.2 Reject-current-method path

If S4-9 fails:

- [ ] Record the current SPSA/integer-weight method as rejected or insufficient for real-data tuning under tested bounds.
- [ ] Preserve known-answer evidence separately from real-data failure.
- [ ] Recommend next method candidates, such as higher-precision latent parameters with quantized export, coordinate/gradient-free alternatives, Texel-style optimization, or another explicitly specified approach.
- [ ] Do not claim S5 evaluator-feature readiness under an unvalidated optimizer.

## S4-11 gate

- [ ] The project has an explicit, evidence-backed tuning-method disposition and next-step recommendation.

---

# Task S4-12: Final report and closure — NOT STARTED

## S4-12.1 Final implementation report

- [ ] Create `docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_IMPLEMENTATION_REPORT.md`.
- [ ] Record exact baseline and final SHAs.
- [ ] Record root cause(s) of S3 zero movement.
- [ ] Record optimizer-trace schema/identity.
- [ ] Record single-parameter known-answer result.
- [ ] Record multi-parameter known-answer result.
- [ ] Record degraded-evaluator recovery result.
- [ ] Record corpus identities/statistics.
- [ ] Record hyperparameter matrix and all dispositions.
- [ ] Record S4-9 real-data result.
- [ ] Record S4-10 development smoke or explicit skip.
- [ ] Record final tuning-method disposition.
- [ ] Confirm no activation occurred.

## S4-12.2 Authority cleanup

- [ ] Move this TODO from active authority to historical inventory when S4 closes.
- [ ] Update `docs/LEGACY_TODO_INDEX.md` counts/classification.
- [ ] Update permanent TODO-authority audit.
- [ ] Confirm no temporary S4 staging helper remains.
- [ ] Confirm generated artifacts follow repository policy.

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

- [ ] S4-0 authority and baseline freeze complete.
- [ ] S4-1 S3 zero-movement reproduction/classification complete.
- [ ] S4-2 optimizer iteration trace complete.
- [ ] S4-3 quantization/update diagnostics complete.
- [ ] S4-4 single-parameter known-answer test complete.
- [ ] S4-5 multi-parameter known-answer test complete.
- [ ] S4-6 degraded chess-evaluator recovery complete.
- [ ] S4-7 stronger deterministic corpus complete.
- [ ] S4-8 bounded hyperparameter calibration complete.
- [ ] S4-9 real-data tuning-signal gate complete or method rejected/deferred.
- [ ] S4-10 development strength smoke complete or explicitly skipped.
- [ ] S4-11 method disposition and next-step recommendation complete.
- [ ] S4-12 final report and closure complete.
