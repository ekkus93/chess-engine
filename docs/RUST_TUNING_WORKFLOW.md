# Reproducible Rust tuning workflow

Tuning is an offline evidence-producing workflow. It never changes `EvaluationWeights::DEFAULT`, loads a candidate implicitly, or activates a candidate.

## Inputs

The command requires:

1. a strict Task 25 tuning configuration beginning with `CHESS_TUNING_CONFIG<TAB>1`;
2. a validated Task 20 self-play dataset;
3. a new output directory;
4. optionally, a complete output directory from a previous run.

Use `fixtures/tuning_config.example` as the schema example. Every field is mandatory, duplicates and unknown fields fail, and source provenance is explicit.

The configuration records the engine/candidate identities, exact 20-byte source commit, explicit creation timestamp, cumulative and per-invocation iteration limits, the complete SPSA schedule and bounds, regularization, random seed, and deterministic logistic-`K` calibration grid.

## Command

Fresh run:

```bash
bash scripts/dev.sh tune CONFIG DATASET OUTPUT_DIR
```

Resume:

```bash
bash scripts/dev.sh tune CONFIG DATASET NEW_OUTPUT_DIR PREVIOUS_OUTPUT_DIR
```

Resume requires the exact previous configuration, loss-dataset fingerprint, baseline reference weights, and objective. A mismatch fails before optimization.

## Publication contract

The adapter writes into a sibling staging directory and renames that directory only after all outputs are complete. It refuses to overwrite either an output directory or stale staging directory.

The output contains the exact `tuning-config.txt`, a checksummed checkpoint, complete report, named candidate artifact, compact summary, and `ACTIVATION_DISABLED`. Generated output belongs under `tuning-output/` or another ignored explicit path unless an individual artifact is deliberately promoted for review.

## Activation boundary

A tuning run may improve training or held-out loss and still remain unsuitable for play. No result in this workflow bypasses the Task 21 correctness-first, 200-pair color-balanced candidate-validation protocol. An accepted validation report also remains inactive until a separate reviewed source/configuration change explicitly activates it.
