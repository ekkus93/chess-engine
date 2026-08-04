# Rust deterministic SPSA optimizer

## Scope

Task 21.3 adds a reusable optimizer to `chess-tune`. It consumes the named 810-parameter schema from Task 21.1 and the train/validation loss boundary from Task 21.2. It does not write final tuning reports, activate candidate weights, evaluate the held-out test split, or claim playing-strength improvement; those remain Tasks 21.4 and 21.5.

## Algorithm

The implementation uses simultaneous perturbation stochastic approximation (SPSA). For cumulative one-based iteration `k`, the explicit schedule is:

```text
a_k = learning_rate / (stability_constant + k) ^ step_decay
c_k = perturbation_size / k ^ perturbation_decay
```

A deterministic SplitMix64 stream generates one `-1` or `+1` perturbation direction for each named parameter. The optimizer evaluates the training objective at the projected `theta + c_k * delta` and `theta - c_k * delta` candidates, estimates the simultaneous gradient, and applies one bounded update.

Every hyperparameter is caller-supplied through `SpsaSchedule`, `SpsaWeightBounds`, and `SpsaConfig`. There is no entropy-derived seed, hidden learning-rate default, implicit iteration count, or automatic dataset sampling.

## Objective isolation

Only the Task 21.2 training partition participates in:

- positive and negative perturbation loss;
- gradient estimation;
- current-candidate objective;
- best-candidate selection.

The validation partition is evaluated only after a requested group of iterations completes. Validation loss is returned for observation and later reporting, but it cannot alter RNG state, gradients, current parameters, or the training-selected best candidate. The Task 20 test split remains absent from `LossDataset` and therefore cannot enter Task 21.3.

## Bounds and regularization

All 810 named scalar parameters are projected into explicit inclusive bounds that must remain within the runtime evaluator's supported `-10,000..=10,000` range. Material values receive an additional deterministic projection that preserves the runtime invariant:

```text
0 < pawn < knight and bishop < rook < queen
```

The training objective is:

```text
training MSE + regularization_strength * mean((weight - initial_weight)^2)
```

The initial named weight vector is the fixed L2 reference for the entire run and is retained in every checkpoint. A zero regularization coefficient is allowed only when selected explicitly. Candidate and resumed weights are revalidated through `EvaluationWeightSet` before use.

## Determinism

A run is reproducible from:

- the exact `SpsaConfig`;
- the explicit `u64` random seed;
- the exact Task 21.2 dataset;
- the explicit logistic `K`;
- the initial named weight vector;
- the number and grouping of completed iterations.

The checkpoint stores the live SplitMix64 state and continuous SPSA parameters, so running 12 iterations continuously is required to produce the same state as running 5 iterations, serializing, resuming, and running 7 more.

Exact training ties retain the lexicographically smaller named integer vector. The best objective is initialized to the starting candidate, so a run never discards a better initial solution merely because later stochastic steps are worse.

## Checkpoint contract

`SpsaCheckpoint` uses a fixed-length, little-endian binary version-1 envelope with:

- magic and schema version;
- optimizer implementation identifier;
- exact-bit configuration fingerprint;
- canonical train/validation dataset fingerprint;
- exact logistic `K` bits;
- original seed and current RNG state;
- completed iteration count;
- continuous current parameters;
- initial regularization reference values;
- best named values;
- current and best training objectives;
- an FNV-1a checksum over the complete payload.

Parsing rejects incorrect length, magic, schema, optimizer identity, checksum, non-finite fields, or impossible objective ordering. Resume additionally rejects configuration changes, dataset changes, iteration-limit violations, invalid weights, out-of-bound values, and stored objectives that do not reproduce against the bound dataset.

The checkpoint API returns bytes but performs no filesystem access. The caller owns atomic file creation, replacement, retention, and naming. Task 21.4 owns persistent report and artifact workflows.

## Failure policy

The optimizer fails loudly for:

- zero or excessive iteration limits;
- zero-iteration advance requests;
- non-finite or invalid schedule values;
- perturbations smaller than half a centipawn;
- reversed, unsupported, or material-incompatible bounds;
- negative or non-finite regularization;
- invalid initial or resumed runtime weights;
- cumulative iteration overflow or cap violations;
- loss-pipeline failures;
- non-finite gradients or state;
- corrupt or incompatible checkpoints;
- resuming or advancing against a different dataset.

There is no silent clipping outside the documented projection, implicit checkpoint fallback, validation-driven model selection, or automatic activation of optimized weights.

## Public boundary

`chess-tune` exposes:

- `SpsaSchedule`;
- `SpsaWeightBounds`;
- `SpsaConfig`;
- `SpsaOptimizer`;
- `SpsaCheckpoint`;
- `SpsaRunSummary`;
- `SpsaOptimizerError`;
- version, identity, iteration, and runtime-bound constants.

Task 21.4 may serialize tuning reports and named candidate artifacts from `SpsaRunSummary` and `SpsaCheckpoint`. Task 21.5 must independently evaluate the held-out test split and playing strength before any candidate may be approved or activated.
