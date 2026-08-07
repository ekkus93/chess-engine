# Rust Chess Engine S4 Method Disposition and S5 Readiness — 2026-08-07

**Status:** Accepted for future evaluator experimentation; not production activation evidence  
**Date:** 2026-08-07  
**Program:** S4 evaluation tuning calibration  
**Selected calibration row:** `11`  
**Selected runtime value checksum:** `520db5dd58086a8a`

## Method disposition

The current integer-weight SPSA tuning method is **accepted as a validated experimental tuning method for future evaluator work** within the tested S4 operating envelope.

This disposition is narrower than a release or chess-strength claim. It means the project has established that the current optimizer, integer evaluator representation, deterministic data pipeline, loss calculation, artifact registry, and bounded calibration process can produce reproducible non-zero evaluator changes with simultaneous training and held-out loss improvement. It does **not** mean the selected S4 evaluator should become production default, and it does not authorize a version change or activation.

## Why the method is accepted

S4 established all of the following independently:

1. The historical S3 zero-movement result had nonzero objective and gradient signal. Its maximum proposed update was only `2.06410316075983228e-04`, so all `6,480` selected parameter-iterations quantized back to their previous integer runtime values.
2. The exact production update path has regression coverage proving:
   - sub-integer update quantization;
   - effective integer materialization;
   - signed clipping at both bounds;
   - separate regularization accounting;
   - deterministic one-parameter known-answer recovery;
   - deterministic multi-parameter convergence with inactive values frozen.
3. A deliberately degraded but structurally valid chess evaluator recovered on actual `LossDataset` positions when the dataset was first proven to contain baseline-favoring signal.
4. A stronger deterministic 96-game / 1,530-position calibration corpus was generated twice byte-identically, with `8,202` training occurrences, `2,465` held-out validation occurrences, zero excluded rows, and strict provenance.
5. The 12-row predeclared calibration matrix executed without selective reruns. All rows produced nonzero movement, training improvement, held-out improvement, zero clipping, and inactive artifacts.
6. The deterministic selection rule chose row 11, which changed `645 / 810` parameters with maximum absolute integer delta `8`, training-loss delta `-4.83858551862105524e-3`, validation-loss delta `-6.37062441281038838e-3`, and no clipping.
7. S4-9 repeated the selected row twice with identical inputs and reproduced the complete output directory and CLI logs byte-for-byte. The runtime value checksum remained `520db5dd58086a8a` and the strict candidate registry accepted exactly one inactive candidate with decision `advance`.

## Validated operating envelope

The following configuration family is validated for **experimental evaluator tuning**, not release:

- optimizer: existing bounded SPSA implementation;
- runtime representation: current integer `i16` evaluator weights;
- parameter masks: explicit `TunableParameterMask`; inactive parameters must remain frozen;
- current full-evaluator mask: `810` tunables, fingerprint `02c6c0907d4847c3`;
- learning-rate range exercised successfully on real data: `512` through `4096`;
- perturbation sizes exercised successfully on real data: `2` and `8`;
- regularization exercised: `0` and `0.0001`;
- calibration iterations: `32`;
- step decay: `0.602`;
- perturbation decay: `0.101`;
- stability constant: `10.0`;
- explicit optimizer bounds: `[-2000, 2000]`;
- required clipping count for advancement: `0`;
- K search: `0.1` through `3.0`, `20` intervals;
- deterministic seed must be explicit and provenance-bound;
- dataset and split identities must be frozen before tuning;
- candidate must remain `activated=false`;
- training loss must strictly improve;
- held-out validation must satisfy a predeclared tolerance;
- candidate runtime value checksum must differ from baseline;
- candidate artifact/trace/registry checksums must validate;
- an advancing configuration must reproduce under identical inputs before downstream strength work.

The S4 selected configuration is:

- learning rate `4096`;
- perturbation size `8`;
- regularization `0`;
- `32` iterations;
- seed `1395995457`.

It is a useful calibrated starting point for S5, **not** a permanently optimal global tuning configuration. Future datasets or newly introduced evaluator terms may require a newly predeclared bounded calibration rather than blindly reusing row 11.

## Parameter-group signal

Evidence-backed conclusions by group are deliberately conservative:

- **Full existing evaluator:** demonstrated strong measurable real-data tuning signal under the S4 matrix. All 12 bounded configurations moved runtime weights and improved both training and held-out loss.
- **Material parameters:** demonstrated controlled chess-specific recovery in the degraded-queen known-answer test using a 10-parameter material mask.
- **S3 group-specific masks** (piece-square/material, mobility/activity, pawn structure, king safety/space, endgame king activity): the historical S3 pilot cannot be used as evidence of absent signal because its gain regime was quantization-limited. S4 did not rerun an independent calibrated matrix for every one of those masks, so their relative signal strengths remain unproven rather than rejected.

S5 should not infer that an untested individual group is weak merely because S3 produced zero movement.

## Limitations

The accepted method has important limits:

- The S4 loss corpus is deterministic and stronger than S3, but still small relative to production-scale tuning datasets.
- Hyperparameter selection used one frozen perturbation seed across rows to isolate configuration effects. Cross-seed stability remains a separate future concern.
- Held-out loss improvement is not equivalent to Elo improvement.
- The selected candidate changed many weights simultaneously, so its individual parameter deltas do not identify causal chess features.
- Integer materialization remains a discontinuity. Future configurations with smaller gains can still become quantization-limited.
- Larger gains can become unstable; S4 therefore requires explicit clipping accounting and rejects bound hits during calibration.
- The matrix explored a bounded family, not all possible SPSA schedules or alternative optimizers.
- S4 does not establish that SPSA is superior to Texel-style optimization, coordinate methods, higher-precision latent weights, or other explicitly designed future methods.
- No candidate is authorized for production merely because it passes the S4 tuning method gates.

## S5 readiness requirements

A future S5 evaluator-feature program may proceed using the S4 method only if it preserves these rules:

1. **Feature isolation first.** Each new evaluator term must have a precise chess definition, independent unit tests, evaluation-trace visibility, and explicit default-zero/inactive candidate semantics before tuning.
2. **No search-policy smuggling.** S5 evaluation work must not reactivate S2 PVS, LMR, null move, SEE, tablebase, or other rejected/deferred search features through an evaluation experiment.
3. **Explicit parameter registration.** New tunables must have stable names/indexes, masks, bounds, and artifact serialization; no anonymous appended weights.
4. **Known-answer sensitivity.** Before real-data tuning, each new feature must have controlled positions where changing its weight changes evaluation in the expected direction.
5. **Frozen data and protocol.** Dataset identity, opening policy, train/validation/test split, K calibration, seed, iteration budget, and advancement tolerance must be declared before results are inspected.
6. **Quantization visibility.** S4 per-iteration trace/movement metrics remain mandatory. Zero movement must never be mistaken for optimizer convergence.
7. **Bounded calibration.** If S5 changes the feature set materially, predeclare a small hyperparameter matrix or justify reuse of the S4 calibrated family before seeing candidate results.
8. **Held-out gate.** Training improvement alone is insufficient. Held-out loss must satisfy the declared tolerance.
9. **Exact reproducibility.** An advancing candidate must reproduce its runtime value checksum and publication artifacts under identical inputs.
10. **Chess-strength evidence remains separate.** Development smoke may triage candidates, but production activation requires a future dedicated strength/release program with predeclared statistical thresholds and separate activation approval.
11. **Fail closed.** Invalid weights, malformed artifacts, checksum drift, unknown schema, clipping violations, infrastructure failures, or illegal chess behavior reject evidence rather than invoke fallback behavior.
12. **No automatic activation.** S5 evaluator exploration remains candidate-only until a distinct production acceptance and activation program succeeds.

## Recommendation

S4 should close with the tuning method **accepted for S5 evaluator-feature experimentation**. S5 should focus on isolated evaluator terms and causal evaluation improvements rather than reopening S2 search heuristics. The first S5 candidates should be narrow, independently testable evaluation features; each should use the S4 trace/provenance/reproducibility machinery and earn chess-strength testing separately.

The S4 selected full-evaluator candidate is useful as a calibration witness and optional development-smoke subject. It is not itself the production target for S5 and remains inactive.
