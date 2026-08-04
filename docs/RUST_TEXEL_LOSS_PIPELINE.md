# Rust Texel-style loss pipeline

## Scope

Task 21.2 defines the deterministic objective boundary used by future optimizer work. It does not implement an optimizer, checkpointing, reporting, candidate activation, or playing-strength validation.

The reusable mathematics live in `chess-tune`. The `chess-tools` adapter consumes the strict Task 20 self-play dataset and converts eligible position rows into the loss API without creating a dependency from `chess-tune` back to the command-line tooling crate.

## Result targets

Every static evaluation is already expressed from the side-to-move perspective. Completed game results are therefore converted to side-to-move targets:

- eventual loss: `0.0`;
- draw: `0.5`;
- eventual win: `1.0`.

White and Black wins are mapped relative to the side to move in each retained FEN. An unfinished maximum-ply result has no supervised target and may not enter the loss dataset.

## Logistic mapping

For a side-to-move evaluation `e` in centipawns and a finite positive calibration constant `K`, the expected result is:

```text
p(e, K) = 1 / (1 + 10 ^ (-K * e / 400))
```

The implementation evaluates the equivalent natural-exponential form with separate positive and negative branches to avoid overflow. Zero evaluation maps exactly to `0.5`; positive and negative evaluations are symmetric around `0.5`.

## Objective

The documented objective is occurrence-weighted mean-squared error:

```text
MSE = sum(occurrences * (predicted - target)^2) / sum(occurrences)
```

Task 20 deterministically merges exact duplicate position rows and records their occurrence count. Task 21.2 preserves that multiplicity as an objective weight rather than treating every deduplicated row as one observation.

## Train, validation, and test isolation

The Task 20 split is consumed as follows:

- `train`: used by optimizer loss and `K` calibration;
- `validation`: held out from calibration and optimization and evaluated separately;
- `test`: excluded from Task 21.2 entirely and reserved for later final candidate assessment.

Both training and validation partitions must contain at least one eligible row. Opening-source rows and unfinished maximum-ply rows are already marked ineligible by Task 20 and are omitted. Missing partitions, zero occurrence counts, or occurrence-count overflow fail loudly.

## Explicit K calibration

`KCalibrationConfig` defines an inclusive deterministic grid using an explicit minimum, maximum, and interval count. The interval count is bounded from one through 1,000,000; the number of evaluated candidates is `intervals + 1`.

Calibration evaluates every grid candidate against the training partition only. The candidate with the smallest training MSE is selected. Exact ties retain the smaller `K`, making the result deterministic. Validation rows never influence calibration.

The caller must record the chosen grid and calibrated value in later Task 21 reports. Task 21.2 provides the result but does not choose hidden defaults.

## Dataset adapter and failure policy

`chess_tools::tuning::loss_dataset_from_self_play_text` first invokes the complete strict Task 20 parser and validator. Malformed headers, records, FENs, provenance, splits, filtering metadata, duplicate accounting, or replay data therefore fail before loss construction.

The adapter then:

1. skips ineligible records;
2. excludes the held-out test split;
3. reconstructs every retained canonical FEN;
4. maps the final game result relative to the side to move;
5. preserves duplicate occurrence counts;
6. constructs nonempty training and validation partitions.

There is no fallback parser, implicit split reassignment, unfinished-game draw conversion, automatic candidate activation, or silent omission of malformed eligible rows.

## Public boundaries

`chess-tune` exposes:

- `OutcomeTarget`;
- `LogisticK`;
- `KCalibrationConfig` and `KCalibrationResult`;
- `LossPosition`, `LossPartition`, and `LossDataset`;
- `logistic_result_probability`;
- typed `LossPipelineError` failures.

`chess-tools` exposes:

- `loss_dataset_from_self_play_text`;
- `loss_dataset_from_self_play_dataset`;
- typed `SelfPlayLossDatasetError` failures.

Task 21.3 may repeatedly evaluate candidate `EvaluationWeights` against the same parsed `LossDataset`. Task 21.4 owns persistent reports, and Task 21.5 owns final held-out and playing-strength validation.
