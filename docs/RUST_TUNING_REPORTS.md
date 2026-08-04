# Rust tuning reports

**Schema:** `chess-tuning-report-v1`  
**Implementation:** `crates/chess-tools/src/tuning/report.rs`  
**Status:** Task 21.4 report contract

## Purpose

Task 21.4 turns one validated SPSA checkpoint into two separate, explicit artifacts:

1. a human-readable, deterministic tuning report; and
2. an optional named candidate-weight artifact.

Neither artifact is loaded automatically. Producing a candidate does not change the built-in evaluator, UCI defaults, safe API defaults, C ABI behavior, or Android behavior. Candidate activation remains an explicit later decision after Task 21.5 validation.

## Required report contents

Every report contains:

- initial occurrence-weighted training MSE;
- initial occurrence-weighted held-out validation MSE;
- final occurrence-weighted training MSE for the training-selected checkpoint best;
- final occurrence-weighted held-out validation MSE for that same candidate;
- the final regularized training objective used by SPSA selection;
- all 810 named parameters in canonical schema order, each with initial value, candidate value, and signed delta;
- canonical Task 20 dataset schema, checksum, split occurrence counts, and the derived train/validation loss fingerprint;
- engine identifier, semantic version, and exact 20-byte source commit;
- initial and candidate weight-set identifiers and checksums;
- SPSA implementation identifier, configuration fingerprint, checkpoint checksum, random seed, completed iteration count, and logistic `K`;
- every explicit SPSA schedule, bound, and regularization value;
- the exact caller-supplied command or equivalent invocation;
- a semantic checksum over the complete report.

Validation loss is reported but never used to choose or mutate the optimizer candidate.

## Construction contract

Use `TuningReport::from_checkpoint` with:

- `TuningReportProvenance`;
- canonical `TrainingDatasetProvenance`;
- the exact `SpsaConfig`;
- the exact `LossDataset`;
- the initial runtime weights; and
- the final `SpsaCheckpoint`.

Construction fails when:

- the checkpoint cannot resume against the supplied configuration and dataset;
- the Task 20 provenance counts do not match the loss partitions;
- the supplied initial weights do not reproduce the checkpoint's regularized objective reference;
- the checkpoint has completed zero iterations;
- any initial or candidate weight set is invalid;
- a loss is non-finite;
- any configuration, dataset, seed, iteration, `K`, candidate, objective, or checkpoint identity differs;
- any required identifier or command is empty.

## Dataset identity

`loss_dataset_and_provenance_from_self_play_text` parses and validates the strict Task 20 dataset, constructs the train/validation loss partitions, excludes the held-out test split, and returns provenance containing:

- `SELF_PLAY_DATASET_SCHEMA_VERSION`;
- FNV-1a over the canonical validated `SelfPlayDataset::to_text()` output;
- occurrence-weighted training count; and
- occurrence-weighted validation count.

The report separately records the deterministic loss-dataset fingerprint used by the optimizer checkpoint. This prevents a report from being rebound to another source dataset that happens to have the same row counts.

## Parameter deltas

`parameter_deltas()` iterates `TunableParameter::all()` and therefore uses the same stable 810-scalar ordering as the named weight schema. Every serialized row has:

```text
parameter.<stable-name>=<initial>    <candidate>    <candidate-minus-initial>
```

Deltas use `i32` so subtraction cannot overflow the `i16` runtime weight range.

## Exact configuration encoding

The report prints readable decimal values and exact IEEE-754 bit patterns for all floating-point configuration and loss fields. The semantic checksum hashes the exact bits, not decimal formatting.

Recorded configuration includes:

- maximum cumulative iterations;
- learning rate;
- step-decay exponent;
- perturbation size;
- perturbation-decay exponent;
- stability constant;
- inclusive minimum and maximum weight bounds;
- L2 regularization strength;
- random seed;
- completed iterations; and
- logistic `K`.

The engine version and exact command are serialized as UTF-8 hexadecimal so spaces, quotes, and shell punctuation remain unambiguous.

## Persistence

The filesystem is adapter-owned. There is no default path and no conventional-path discovery.

Use:

- `write_tuning_report_atomic(destination, temporary, report)`; and
- `write_candidate_artifact_atomic(destination, temporary, artifact)`.

The destination and temporary paths must be distinct and in the same directory. The temporary file is created with `create_new`, fully written, flushed, synchronized, and renamed. Callers must choose both paths explicitly.

## Candidate artifact

`TuningReport::candidate_artifact(generated_at_unix_seconds)` creates the existing versioned `NamedWeightArtifact` using:

- the report's candidate identifier and candidate weights;
- the exact source commit;
- the SPSA implementation identifier;
- the original random seed;
- completed iterations;
- Task 20 dataset provenance; and
- the caller-supplied creation timestamp.

This method only constructs data. It does not activate or install the candidate.

## Example integration

```rust
let (loss_dataset, dataset_provenance) =
    chess_tools::tuning::loss_dataset_and_provenance_from_self_play_text(&dataset_text)?;

let report_provenance = TuningReportProvenance::new(
    engine_identifier,
    env!("CARGO_PKG_VERSION").to_owned(),
    source_commit,
    initial_weight_identifier,
    candidate_weight_identifier,
    exact_command,
)?;

let report = TuningReport::from_checkpoint(
    report_provenance,
    dataset_provenance,
    config,
    &loss_dataset,
    initial_weights,
    &checkpoint,
)?;

write_tuning_report_atomic(&report_path, &report_temp_path, &report)?;

let candidate = report.candidate_artifact(generated_at_unix_seconds)?;
write_candidate_artifact_atomic(
    &candidate_path,
    &candidate_temp_path,
    &candidate,
)?;
```

The caller should retain the report, candidate artifact, checkpoint, source dataset, and exact source commit together. Task 21.5 must validate the candidate before any explicit activation decision.
