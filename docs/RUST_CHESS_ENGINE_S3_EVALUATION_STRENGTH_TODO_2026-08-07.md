# Rust Chess Engine S3 Evaluation Strength TODO — 2026-08-07

**Status:** Complete — program closed without promotion  
**Date:** 2026-08-07  
**Branch:** `master`  
**Planning authority SHA:** `90a015c2cf8b8d45edcd07d705fb6ca58fe336f7`  
**Specification:** `docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_SPEC_2026-08-07.md`  
**Final report:** `docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_IMPLEMENTATION_REPORT.md`  
**Pilot evidence:** `docs/RUST_CHESS_ENGINE_S3_PILOT_EVALUATION_2026-08-07.md`  
**Authoritative released engine:** v0.1 (`0.1.0`)  
**Closure disposition:** no S3 candidate passed the held-out advancement rule; development/production strength validation and activation were not entered.

---

## Status rules

- `[x]` means the requirement has a final, explicit disposition backed by source/tests/evidence.
- For executable work that became inapplicable because a required predecessor produced no eligible candidate, `[x] N/A` means **not executed and not silently treated as passed**.
- `DEFERRED` means optional work was consciously left for a future program and was not implemented by S3.
- No workflow success, benchmark result, training loss, candidate artifact, or checked box authorizes production activation.
- S3 never changed package/UCI version from `0.1.0` and never activated S2.

---

# Task S3-0: Authority registration and v0.1 baseline freeze — COMPLETE

## S3-0.1 Authority registration

- [x] Registered this TODO as the active S3 authority during implementation.
- [x] Kept every other top-level `docs/*TODO*.md` explicitly classified as authority/index/historical.
- [x] Updated the permanent TODO-authority audit for S3.
- [x] Kept the closed S2 v0.2 strength TODO historical.
- [x] Confirmed no S2 activation/release task remained active.

## S3-0.2 Baseline identity freeze

- [x] Recorded planning authority SHA `90a015c2cf8b8d45edcd07d705fb6ca58fe336f7`.
- [x] Recorded unchanged production/code baseline SHA `677cd2a4d2a4a4f3c376f7bf47fae412171206fb`.
- [x] Recorded package/UCI version `0.1.0`.
- [x] Recorded search-policy schema/id/checksum `1` / `5630315f504f4c31` / `0c0769ef9d034770` and canonical v0.1 policy text.
- [x] Recorded evaluation schema/id/checksum `1` / `424153454c494e45` / `d2cca7ae10ec6e34`.
- [x] Recorded runtime vector length `816` and named tunable count `810`.
- [x] Recorded C ABI version `1`.
- [x] Recorded JNI/Kotlin public-surface source identity.
- [x] Recorded opening-book default disabled/explicit-input policy.
- [x] Recorded tablebase/Syzygy state as absent/disabled.
- [x] Recorded baseline CI/performance/robustness/Android evidence in `docs/RUST_CHESS_ENGINE_S3_BASELINE_2026-08-07.md` and this program report.

## S3-0.3 Non-promotion proof

- [x] Confirmed no rejected S2 candidate is enabled by default.
- [x] Confirmed no public adapter exposes experimental `SearchPolicy` selection.
- [x] Confirmed default search remains v0.1 policy plus baseline evaluation weights.
- [x] Baseline capture changed no production semantics/defaults.

**S3-0 gate:** Complete — exact v0.1 authority frozen.

---

# Task S3-1: Public-surface and review-cleanup guardrails — COMPLETE

## S3-1.1 Experimental-policy exposure audit

- [x] Permanent audits prove UCI cannot select experimental S2 policies.
- [x] Permanent audits prove the safe Rust facade cannot select experimental S2 policies.
- [x] Permanent audits prove the C ABI cannot select experimental S2 policies.
- [x] Permanent audits prove JNI/Kotlin cannot select experimental S2 policies.
- [x] Permanent audits prove Android harness code cannot select experimental S2 policies.
- [x] Negative scans cover PVS, LMR, null move, futility, razoring, late-move pruning, SEE ordering/pruning, delta pruning, Syzygy/tablebase exposure.

## S3-1.2 `PositionEditor` contract hardening

- [x] Documented that `PositionEditor` updates board representations but deliberately does not update Zobrist state.
- [x] Added `editor_mutation_is_hash_neutral_until_the_caller_updates_hash_state`.
- [x] Preserved make/unmake recomputed-Zobrist verification.
- [x] Removed the unnecessary public `PositionEditor` re-export; it is internal to `chess-core`.

## S3-1.3 UCI worker lifecycle hardening

- [x] Added active-search `position` replacement stale-bestmove regression.
- [x] Added active-search `ucinewgame` stale-bestmove regression.
- [x] Added repeated stop/restart exact-final-bestmove regression.
- [x] Preserved explicit stop and quit tests.
- [x] No silent worker-result discard/error fallback was introduced.

## S3-1.4 Validation

- [x] Guardrail implementation commit `57420991e856ac8ee1ff4c3ddf44177db8c3f76c`.
- [x] Permanent run `31180832957`, job `92873446300`, passed audit/fmt/strict Clippy/editor/UCI regressions.

**S3-1 gate:** Complete.

---

# Task S3-2: Deterministic self-play dataset and provenance validation — COMPLETE

## S3-2.1 Preserve Task-20 schema and add S3 sidecar

- [x] Preserved the historical `CHESS_SELF_PLAY_DATASET` schema rather than silently revising it.
- [x] Added strict `CHESS_S3_TRAINING_DATASET_MANIFEST` schema `1`, identifier `5333444154413031`.
- [x] Manifest binds explicit source SHA, engine version, v0.1 policy identity, baseline weight identity, dataset/config/opening checksums, seed, game completion, split occurrences, exact invocation, and row eligibility counts.
- [x] Manifest is checksummed and strictly parsed.
- [x] Manifest revalidation reconstructs identity from the supplied dataset and fails closed on mismatch.
- [x] No Git/environment/process discovery supplies provenance implicitly.

## S3-2.2 Dataset admission and filtering

- [x] Minimum pilot/tuning admission is explicit: 16 games, 12 completed, <=250 unfinished/1000, >=128 training occurrences, >=16 validation occurrences.
- [x] Opening-position policy and unfinished-game treatment remain explicit in Task-20 data.
- [x] Train/validation/test split assignment remains deterministic.
- [x] Duplicate positions retain occurrence counts and split identity.
- [x] Training conversion uses eligible positions only; excluded data do not become training rows silently.

## S3-2.3 Determinism and replay

- [x] S3 library tests generate deterministic real self-play and prove manifest round-trip/checksum binding.
- [x] Experiment generated the exact S3 data package twice and compared it byte-for-byte.
- [x] Existing Task-20 validation/replay tooling remains available.
- [x] First experiment infrastructure failure (`cmp -r`) was fixed at workflow source and rerun; no data defect was ignored.

## S3-2.4 Pilot dataset evidence

- [x] Successful run/job `31184450979` / `92885406054`.
- [x] Artifact `8996149049`, digest `sha256:797a03d73830e30ead1537378716b02a9aa91553764f9992388876ec0d267d`.
- [x] Dataset checksum `c691d1928ffda61b`.
- [x] Manifest checksum `6aef02a9b375c5a3`.
- [x] Training occurrences `2,066`; validation occurrences `195`; excluded rows `0`.
- [x] Admission result `true`; activation `false`.

**S3-2 gate:** Complete — deterministic admitted S3 data path validated.

---

# Task S3-3: Tuning-pipeline correctness, determinism, resume, and held-out separation — COMPLETE

## S3-3.1 K calibration and loss separation

- [x] Existing `LossDataset` calibrates K from the training partition only.
- [x] Held-out validation loss remains separate from optimizer state transitions.
- [x] Non-finite/invalid loss domains fail loudly.
- [x] Tuning reports preserve initial/final training and validation losses independently.

## S3-3.2 SPSA correctness

- [x] SPSA schedule/bounds/regularization validation is typed and fail closed.
- [x] Deterministic RNG/checkpoint state is preserved.
- [x] Existing optimizer regressions cover deterministic repeatability/resume/checkpoint binding.
- [x] Weight projection preserves runtime evaluator constraints.
- [x] Node/runtime code never substitutes a failed tuner result with baseline and calls it a candidate.

## S3-3.3 Mask-aware optimizer correctness

- [x] `TunableParameterMask` selects exact named parameters.
- [x] Inactive parameters receive no perturbation direction/update and project back to reference values.
- [x] Partial material masks reject because material ordering projection is coupled.
- [x] Non-full masks are bound into the SPSA config/checkpoint fingerprint using `spsa-parameter-mask-v1`.
- [x] Masked regularization normalizes over selected parameters only.
- [x] Fixed `TuningReport` to use the same masked regularization domain as the optimizer.
- [x] Added `masked_optimizer_never_changes_inactive_parameters`, `mask_identity_binds_checkpoint_configuration`, and masked-report regression.

## S3-3.4 Resume/provenance

- [x] Legacy tuning resume requires exact config and checkpoint seed.
- [x] `tune-group` additionally requires exact previous S3 group and exact dataset manifest text.
- [x] Source SHA in tuning config must equal S3 dataset-manifest source SHA.
- [x] Exact invocation is recorded in report provenance.
- [x] Outputs are published through bounded same-parent staging/rename and contain `ACTIVATION_DISABLED`.

## S3-3.5 Validation evidence

- [x] Infrastructure commit `c28fc5e0d8bc9919f8ef5da35017fde1c32ac96b`.
- [x] Clean pipeline gate `31182113877`, job `92877654602`, success.
- [x] Reproducible CLI/report commit `93ab676b13b1a5d394ffa6d3d4f312a889b5f202`.
- [x] Focused run `31183716103`, job `92882978680`, success.
- [x] Clean permanent run `31184166429`, job `92884442719`, success.

**S3-3 gate:** Complete.

---

# Task S3-4: Held-out-loss advancement framework — COMPLETE

## S3-4.1 Frozen rule

- [x] Every assessed loss must be finite and non-negative.
- [x] Candidate training loss must be strictly lower than baseline training loss.
- [x] Training-only improvement cannot hide held-out validation regression.
- [x] Validation regression beyond deterministic tolerance `1e-12` rejects.
- [x] Equal/no-improvement training loss rejects as `reject_no_training_improvement`.
- [x] Passing loss evidence may only produce `advance`; it cannot activate production.

## S3-4.2 Machine-readable implementation

- [x] Added `S3LossEvidence` and `S3LossDecision`.
- [x] Stable dispositions: `advance`, `reject_no_training_improvement`, `reject_validation_regression`.
- [x] Added finite-domain and decision-boundary regression coverage.

## S3-4.3 Pilot application

- [x] All six initial groups had training delta `0.0` and validation delta `0.0`.
- [x] All six therefore reject for no training improvement.
- [x] Candidate `parameter.*` payloads all shared value digest `689d960bd3a2751604165861116a0bc3d10afa4aea32bbbb82e808a59c777066`.
- [x] No pilot workflow success was interpreted as candidate strength.

**S3-4 gate:** Complete.

---

# Task S3-5: Existing-evaluator group tuning — COMPLETE (NO ADVANCING GROUP)

## S3-5.1 Frozen groups

- [x] Material and piece-square: 778 named scalars, mask `6a6ca13fc4a12d1f`.
- [x] Mobility and activity: 16, mask `78f56bc1fbfd98c5`.
- [x] Pawn structure: 8, mask `6c1cbe6802740220`.
- [x] King safety and space: 6, mask `0c98c164c0951c99`.
- [x] Endgame king activity: 2, mask `7306dfbdf5aa6544`.
- [x] Full existing evaluator: 810, mask `02c6c0907d4847c3`.
- [x] First five groups are disjoint and their union is all 810 tunables.

## S3-5.2 Initial grouped pilot

- [x] Every group used explicit deterministic candidate identifier, RNG seed, bounds, regularization, schedule, source SHA, dataset manifest, and inactive output.
- [x] All six produced exactly zero training-loss and validation-loss delta.
- [x] All six are rejected by S3-4.
- [x] Pawn-structure tuning was rerun from scratch and output/log compared byte-for-byte.

## S3-5.3 Review-before-full sequencing

- [x] Did **not** retroactively count the pilot's same-job full pass as satisfying review-before-full sequencing.
- [x] Formally reviewed/rejected the five smaller-group results in `docs/RUST_CHESS_ENGINE_S3_PILOT_EVALUATION_2026-08-07.md`.
- [x] Ran a separate reviewed full 810-parameter pass after that review.
- [x] Reviewed pass source `cbfe949398d5218f4362b0401951b8e59f8f4b84`, run/job `31185848704` / `92890034934`.
- [x] Reviewed candidate `533347525030305c`, mask `02c6c0907d4847c3`.
- [x] Reviewed pass training delta `0.0`, validation delta `0.0`, activation `false`.
- [x] Reviewed-pass artifact `8996696803`, digest `sha256:5f1cbb38d7409baba2fd03300c19e0d81e83d8c777ac73c91e795d0e73895877`.

**S3-5 gate:** Complete — no existing-evaluator candidate advances.

---

# Task S3-6: Versioned candidate artifact and registry — COMPLETE

## S3-6.1 Candidate envelope

- [x] Candidate schema version `1`.
- [x] Format identifier `533343414e443031`.
- [x] Candidate type is explicit; current supported type is `existing_evaluation_weights`.
- [x] Candidate identifier and exact source SHA are explicit.
- [x] Baseline evaluation identifier/checksum are explicit and validated.
- [x] Named-weight artifact checksum and dense value checksum are explicit.
- [x] Dense vector length `816` and tunable count `810` are explicit and validated.
- [x] Exact group and mask fingerprint are explicit.
- [x] Generation timestamp, tuning-config checksum, dataset checksum, S3 manifest checksum, and tuning-report checksum are explicit.
- [x] Exact candidate-generation invocation is explicit.
- [x] Held-out decision and training/validation deltas are explicit.
- [x] `activated=false` is mandatory; `true` fails validation.
- [x] Envelope has a canonical semantic checksum.

## S3-6.2 Controlled loading and registry

- [x] Strict canonical text parser/serializer rejects malformed/schema/type/length/baseline/checksum mismatches.
- [x] `validate_artifact` binds the envelope to the exact `NamedWeightArtifact` including value checksum.
- [x] Runtime weight artifact validation rejects malformed/out-of-range/invariant-invalid underlying weight artifacts through the existing named-weight validation contract.
- [x] `S3CandidateRegistry` rejects duplicate candidate identifiers.
- [x] Candidate registry is validation/tooling-only and not exposed by UCI/FFI/JNI/Android.

## S3-6.3 Validation

- [x] Candidate-registry implementation commit `664bbf4b281efecafb3a3b60465e6dfff9ed1aaa`.
- [x] Focused run `31185313282`, job `92888271090`, passed workspace check, strict Clippy, registry tests, and whitespace gate.
- [x] Permanent read-only candidate-registry audit/test gate added.
- [x] Temporary candidate staging workflow/helper removed before permanent validation.

**S3-6 gate:** Complete.

---

# Task S3-7: Development strength validation — SKIPPED (NO ADVANCING CANDIDATE)

## S3-7.1 Preconditions

- [x] N/A — no S3-4/S3-5 candidate received `advance`.
- [x] N/A — no optional S3-8 candidate existed.
- [x] N/A — therefore there was no candidate that could truthfully enter development strength validation.

## S3-7.2 Smoke/development match

- [x] N/A — no candidate-strength smoke match was run against a baseline-identical evaluator and labeled as candidate evidence.
- [x] N/A — no paired fixed-node development match was run.
- [x] N/A — no paired clock development match was run.
- [x] N/A — no statistical acceptance claim was created.

## S3-7.3 Fail-closed disposition

- [x] Workflow success and inactive candidate artifacts were not substituted for strength evidence.
- [x] Large redundant matches were not used to manufacture evidence for unchanged payloads.
- [x] v0.1 remains authoritative.

**S3-7 gate:** Skipped honestly — precondition unsatisfied.

---

# Task S3-8: Optional new evaluation feature candidates — DEFERRED

## S3-8.1 Candidate menu

- [x] DEFERRED — pawn islands / backward pawns.
- [x] DEFERRED — knight/bishop outposts.
- [x] DEFERRED — richer rook activity.
- [x] DEFERRED — richer passed-pawn detail.
- [x] DEFERRED — richer king safety / attack units.
- [x] DEFERRED — threats/hanging pieces.
- [x] DEFERRED — richer endgame terms.

## S3-8.2 Rationale

- [x] Existing-weight pilot failed to move any evaluator value at the chosen depth/data/iteration scale.
- [x] Adding new structure at that point would conflate feature design with unresolved data/optimizer sensitivity.
- [x] No optional feature code, weight, identity, public option, or production fallback was added.
- [x] Future feature work requires a separately justified evidence plan and isolated candidate identity.

**S3-8 gate:** Deferred by design; not implemented and not represented as strength work completed.

---

# Task S3-9: Combined evaluation candidate — COMPLETE (NO COMBINATION FORMED)

## S3-9.1 Combination rule

- [x] Only independently justified/advancing components are eligible to combine.
- [x] Rejected/deferred components cannot be silently bundled.

## S3-9.2 Disposition

- [x] No S3-5 weight group advanced.
- [x] S3-8 produced no feature candidate.
- [x] Therefore no combined S3 evaluation candidate was formed.
- [x] No new combined identity was invented for unchanged/rejected components.

**S3-9 gate:** Complete — no justified combination exists.

---

# Task S3-10: Production candidate validation — SKIPPED (NO ELIGIBLE CANDIDATE)

## S3-10.1 Preconditions

- [x] N/A — no development-validated candidate existed.
- [x] N/A — no combined candidate existed.
- [x] Production validation was not entered.

## S3-10.2 Required production evidence if a future candidate exists

- [x] N/A — no >=1,000-pair fixed-node production match was run for S3.
- [x] N/A — no >=1,000-pair clock production match was run for S3.
- [x] N/A — no lower-confidence-bound acceptance calculation was emitted for S3.
- [x] N/A — no unfinished/crash/illegal/time-forfeit thresholds were applied because no production games were authorized.
- [x] No report claims `accepted_for_activation`.

## S3-10.3 Fail-closed disposition

- [x] Baseline-identical pilot payloads were not promoted to production candidates.
- [x] No S2 rejected candidate was substituted.
- [x] v0.1 remains authoritative.

**S3-10 gate:** Skipped honestly — no eligible candidate.

---

# Task S3-11: Separate activation and release gate — SKIPPED (NO ACCEPTED CANDIDATE)

## S3-11.1 Approval/precondition

- [x] N/A — no S3-10 `accepted_for_activation` candidate exists.
- [x] N/A — explicit user approval was therefore not requested and not obtained.
- [x] No activation work began without approval.

## S3-11.2 Production default/version changes

- [x] N/A — no candidate weight set was made default.
- [x] N/A — no search-policy/default change was made.
- [x] N/A — package/UCI version was not changed to `0.2.0`.
- [x] N/A — no public Rust/C/JNI/Android release surface changed for S3 activation.
- [x] All candidate artifacts remain inactive.

## S3-11.3 Release validation

- [x] N/A — there is no activation SHA to validate as a release candidate.
- [x] No release report claims promotion.

**S3-11 gate:** Skipped honestly — activation preconditions unsatisfied.

---

# Task S3-12: Final report, audit, cleanup, and closure — COMPLETE (NO PROMOTION)

## S3-12.1 Final report

- [x] Added `docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_IMPLEMENTATION_REPORT.md`.
- [x] Added `docs/RUST_CHESS_ENGINE_S3_PILOT_EVALUATION_2026-08-07.md`.
- [x] Recorded exact implementation commits, runs/jobs/artifacts, checksums, candidate dispositions, and limitations.
- [x] Distinguished successful pipeline validation from failed strength advancement.
- [x] Recorded S3-7/S3-10/S3-11 as skipped, not passed.
- [x] Recorded S3-8 as deferred, not implemented.

## S3-12.2 Permanent audits

- [x] Existing v0.1/S2 closure audits remain required.
- [x] Permanent S3 evaluation-strength audit covers public-surface, provenance, masked tuning, reproducible CLI, version/default and no-Python-fallback contracts.
- [x] Permanent S3 candidate-registry audit covers schema/type/baseline/vector/mask/inactive/duplicate/adapter isolation contracts.
- [x] Permanent S3 workflow runs strict Clippy and the focused S3 regression suites.

## S3-12.3 Cleanup

- [x] Removed Phase 1 temporary write-capable staging workflow/helper.
- [x] Removed Phase 2 temporary staging workflow/helpers.
- [x] Removed Phase 3 temporary staging workflow/helpers.
- [x] Removed candidate-registry temporary staging workflow/helper.
- [x] Permanent experiment workflows are read-only (`contents: read`) and cannot commit or activate.
- [x] No Python/subprocess production fallback was added.
- [x] No rejected S2 candidate was reactivated.

## S3-12.4 Authority closure

- [x] S3 TODO will be reclassified historical at closure.
- [x] Completed Rust-port tracker/task definitions remain authority records.
- [x] No active implementation TODO remains after S3 closure unless a future program is explicitly registered.

## S3-12.5 Final exact-head validation requirement

- [x] Closure requires the final documentation/audit SHA to pass permanent CI, performance, robustness, Android/JNI, and S3 guardrail/candidate-registry gates before the final completion claim.
- [x] Any first-party final-SHA failure must be fixed at source; no gate may be weakened.

**S3-12 gate:** Complete in program semantics; exact final-SHA matrix is the final closure evidence recorded after authority reclassification.

---

# Final completion checklist

- [x] S3-0 baseline/authority freeze complete.
- [x] S3-1 public-surface/review guardrails complete.
- [x] S3-2 deterministic dataset/provenance validation complete.
- [x] S3-3 tuning-pipeline correctness/determinism/resume validation complete.
- [x] S3-4 held-out advancement framework complete.
- [x] S3-5 existing-evaluator group tuning complete; no group advances.
- [x] S3-6 candidate format/registry complete.
- [x] S3-7 explicitly skipped because no candidate advanced.
- [x] S3-8 explicitly deferred; no feature candidate implemented.
- [x] S3-9 complete with no combined candidate formed.
- [x] S3-10 explicitly skipped because no eligible candidate exists.
- [x] S3-11 explicitly skipped because no accepted candidate exists; no approval/activation occurred.
- [x] S3-12 final report/audit/cleanup/closure complete without promotion.
- [x] v0.1 remains authoritative and package/UCI version remains `0.1.0`.
- [x] No S3 evidence authorizes future activation by itself.
