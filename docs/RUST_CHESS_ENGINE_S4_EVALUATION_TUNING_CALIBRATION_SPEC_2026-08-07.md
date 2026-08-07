# Rust Chess Engine S4 Evaluation Tuning Calibration Specification — 2026-08-07

**Status:** Closure candidate; implementation complete through S4-11, exact final validation pending
**Date:** 2026-08-07  
**Branch:** `master`  
**Planning baseline SHA:** `543dce22e51e71f821e37754a97ce0f33c3be122`  
**Companion TODO:** `docs/RUST_CHESS_ENGINE_S4_EVALUATION_TUNING_CALIBRATION_TODO_2026-08-07.md`  
**S3 closure report:** `docs/RUST_CHESS_ENGINE_S3_EVALUATION_STRENGTH_IMPLEMENTATION_REPORT.md`  
**S3 pilot evidence:** `docs/RUST_CHESS_ENGINE_S3_PILOT_EVALUATION_2026-08-07.md`

---

## 1. Executive summary

S4 is a focused calibration and diagnosis program for the Rust chess engine's
evaluation-tuning stack. S3 proved that the deterministic self-play, provenance,
mask-aware SPSA, candidate-artifact, and closure machinery works, but every S3
pilot tuning group—including the reviewed full 810-parameter pass—finished with
zero training-loss improvement, zero held-out validation-loss improvement, and
no effective evaluator-value change.

S4 must determine **why the optimizer produced no parameter movement** before the
project spends additional compute on large strength matches or adds new evaluator
features. The program must distinguish among at least these possibilities:

- perturbation loss differences are zero or too small to produce useful gradients;
- integer quantization/rounding erases valid floating-point updates;
- learning-rate or perturbation schedules are too conservative;
- regularization dominates candidate movement;
- the dataset is too small, shallow, repetitive, or weakly informative;
- the loss formulation is locally insensitive to the selected parameters;
- the implementation has a defect in SPSA, parameter masking, projection,
  candidate materialization, reporting, or resume logic;
- the current baseline happens to be locally stable under the tested objective.

S4 is successful if it either produces a reproducible tuning configuration that
moves weights in the correct direction on controlled tests and yields credible
held-out improvement on real data, or conclusively identifies and documents why
the current tuning method should be replaced or redesigned. S4 does **not**
authorize a release or production-default change.

---

## 2. Authority and inherited constraints

S4 starts from closed S3 authority at planning baseline
`543dce22e51e71f821e37754a97ce0f33c3be122`.

The following remain authoritative until a later explicit activation program:

- package/UCI version `0.1.0`;
- v0.1 production search policy;
- baseline evaluation-weight set;
- C ABI version `1`;
- existing JNI/Kotlin/Android public surfaces;
- opening book disabled by default unless explicitly configured;
- Syzygy/tablebases disabled and absent from the production adapter surface;
- rejected S2 search candidates remain inactive;
- S3 candidate artifacts remain inactive and cannot change production defaults.

S4 must preserve the S3 fail-closed policies:

- no hidden Python/subprocess production fallback;
- no silent parsing fallback;
- no ignored checksum/provenance mismatch;
- no lint suppression to pass gates;
- no unbounded or implicitly discovered training inputs;
- no activation from loss improvement alone;
- no promotion of unchanged or statistically unsupported candidates.

---

## 3. Primary question

S4 must answer:

> Why did the S3 SPSA pilot complete successfully while producing no effective
> evaluator-value movement?

The answer must be supported by iteration-level evidence rather than inference
from final reports alone.

At minimum, S4 must be able to reconstruct for every optimizer iteration:

- selected parameter mask;
- random perturbation vector identity;
- positive and negative perturbation candidate identities;
- positive loss;
- negative loss;
- loss difference;
- gradient estimate magnitude and sign statistics;
- learning-rate value;
- perturbation-size value;
- regularization contribution;
- proposed floating-point parameter deltas;
- integer/quantized parameter deltas;
- count of parameters whose proposed updates rounded to zero;
- count of parameters clamped by bounds;
- resulting candidate-value checksum;
- resulting train and held-out losses.

---

## 4. Goals

S4 must:

1. Instrument the optimizer sufficiently to explain zero-movement runs.
2. Add known-answer optimizer tests where the expected correction direction is
   known before the test runs.
3. Prove the optimizer can recover deliberately degraded evaluator weights.
4. Measure the effect of quantization, clipping, regularization, and SPSA
   hyperparameters independently.
5. Build a stronger deterministic training corpus suitable for tuning signal
   calibration, without confusing that corpus with production-strength evidence.
6. Predeclare bounded hyperparameter experiments and compare them using exact
   train/validation metrics.
7. Produce at least one reproducible real-data run with non-zero parameter
   movement before any candidate is eligible for downstream strength testing.
8. Keep all tuning results inactive and provenance-bound.
9. Close truthfully if the existing optimizer proves unsuitable.

---

## 5. Non-goals

S4 must not:

- reopen PVS, LMR, null-move pruning, SEE/delta pruning, futility, razoring, or
  other rejected S2 search experiments;
- add new evaluator feature families before the tuning signal is demonstrated;
- treat a synthetic recovery test as production strength evidence;
- treat a training-loss decrease as sufficient proof of chess strength;
- run large production matches on a candidate that is value-identical to
  baseline;
- activate any candidate;
- change package/UCI version from `0.1.0`;
- weaken S3 candidate registry, provenance, or public-surface guardrails;
- silently coerce invalid optimizer configuration into defaults.

---

## 6. Optimizer instrumentation requirements

### 6.1 Iteration trace

Introduce a versioned, checksummed S4 optimizer-trace artifact or equivalent
strict report extension. It must bind to source SHA, tuning-config checksum,
dataset-manifest checksum, parameter-mask fingerprint, initial weight identity,
random seed, optimizer iteration, and checkpoint identity.

The trace must contain enough information to reproduce every update decision.
Critical numeric values must be serialized canonically and must not depend on
locale or debug formatting.

### 6.2 Quantization accounting

Because runtime evaluator weights are integer-valued, S4 must explicitly measure
where floating-point optimizer movement is lost when materialized as integer
weights. Reports must distinguish zero estimated gradient, sub-integer proposed
updates, non-zero integer updates, bound clipping, and regularization effects.

### 6.3 Gradient diagnostics

Each run must report active-parameter count, gradient-sign counts, absolute
gradient statistics, proposed-update statistics, zero-after-quantization count,
and clipped-update count. Raw per-parameter traces may be generated as artifacts
but must follow repository artifact policy.

---

## 7. Known-answer recovery experiments

S4 must add controlled tests that do not rely on the production baseline being
suboptimal.

### 7.1 Single-parameter synthetic objective

Construct a deterministic loss surface over one tunable scalar where the known
optimum is deliberately offset from the starting value. Prove that SPSA moves the
parameter toward the optimum and converges within a declared tolerance.

### 7.2 Multi-parameter synthetic objective

Construct a bounded deterministic objective over multiple parameters with a known
optimum and mixed gradient signs. Prove inactive parameters never move, active
parameters move correctly, bounds are respected, resume equals uninterrupted
execution, and provenance changes when seed/config changes.

### 7.3 Deliberately degraded chess evaluator

Create test-only/inactive evaluator variants with known degraded weights, such as
materially wrong piece values or a deliberately distorted PST term. Use a
deterministic chess-position dataset to prove the tuner can recover toward the
authoritative baseline or another predeclared target. These variants must never
be exposed through production adapters.

---

## 8. Training-corpus calibration

S3's 32-game depth-1 corpus was appropriate for pipeline validation, not for
strong tuning conclusions. S4 must define and generate a stronger deterministic
corpus with explicit opening identity, game count, resource limits, TT budget,
draw policy, maximum plies, seed, train/validation/test split, row eligibility,
unfinished-game ceiling, occurrence minimums, source SHA, and invocation.

Prefer fixed-node limits for cross-run reproducibility. S4 should evaluate at
least two bounded corpus scales to determine whether optimizer signal materially
improves with more or stronger positions.

---

## 9. Hyperparameter calibration

S4 must predeclare a bounded hyperparameter matrix before experiments. Candidate
dimensions may include learning rate, perturbation size, decay schedules,
stability constant, regularization strength, and iteration count.

Each run must report exact config/dataset/mask identities, train/held-out loss,
changed-parameter count, maximum/mean absolute parameter delta,
zero-after-quantization count, clipping count, candidate checksum, and
`activated=false`.

A configuration cannot advance merely because it changes more parameters. It
must satisfy the predeclared held-out rule and all correctness/provenance gates.

---

## 10. Real-data tuning-signal gate

Before future evaluator-feature work, at least one existing-weight run must show:

- deterministic source/config/dataset identities;
- non-zero effective parameter movement;
- training loss improves by more than zero;
- held-out loss does not regress beyond the predeclared tolerance;
- same inputs reproduce the same candidate checksum;
- candidate remains `activated=false`;
- candidate registry accepts the artifact;
- production defaults remain unchanged.

If no bounded configuration meets this gate, S4 must stop and recommend redesign
or replacement of the tuning method rather than continue into evaluator-feature
experimentation.

---

## 11. Optional development strength check

A small development match is permitted only after the real-data tuning-signal
gate passes. It may detect catastrophic chess regressions and validate candidate
plumbing, but it cannot authorize release. It must compare against untouched
v0.1 under paired/color-swapped equal-resource conditions and keep independent
TTs and explicit failure accounting.

---

## 12. Acceptance criteria

S4 succeeds in the preferred path when optimizer traces explain movement,
synthetic known-answer tests move correctly, degraded evaluator tests recover,
stronger deterministic corpora are reproducible, and at least one bounded
real-data configuration yields non-zero effective movement with improved
training loss and acceptable held-out behavior.

S4 may also close successfully with a **method rejected** outcome if rigorous
evidence shows that the current SPSA/integer-weight approach cannot provide a
credible tuning signal under reasonable bounded configurations. That closure
must recommend the next method to evaluate.

---

## 13. Validation requirements

Permanent S4 validation must preserve or extend formatting, workspace check,
strict Clippy, all workspace tests, S3 provenance and candidate-registry tests,
public-surface audits, tuning resume/checkpoint regressions, optimizer
known-answer tests, deterministic trace tests, TODO-authority audit, and any
performance/robustness/Android/JNI gates required by touched code.

First-party failures must be fixed at source or explicitly recorded as real
program blockers. No gate may be weakened merely to obtain a green run.

---

## 14. Documentation and closure

S4 must produce a final implementation report with exact baseline/final SHAs,
root cause of S3 zero movement, optimizer-trace identity, known-answer and
recovery results, corpus identities, hyperparameter matrix, real-data tuning
results, optional development match, exact run/job/artifact evidence, final
method disposition, and explicit confirmation that activation did not occur.

When S4 closes, its TODO must move from active authority to historical inventory
and the permanent authority audit must be updated accordingly.

---

## 15. Completion rule

S4 is complete only when the project can explain the S3 zero-movement outcome
with exact evidence and can either demonstrate a reproducible non-zero tuning
signal or formally reject the current tuning method. Merely running more SPSA
iterations, increasing dataset size, or obtaining workflow success is not
sufficient.
