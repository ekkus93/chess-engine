# S3 evaluation-strength pipeline contract

S3 preserves the Task 20 `CHESS_SELF_PLAY_DATASET` schema instead of silently changing a completed historical format. An S3 training package is therefore two explicit artifacts:

1. the strict Task 20 dataset image; and
2. a strict `CHESS_S3_TRAINING_DATASET_MANIFEST` sidecar.

The sidecar binds the dataset checksum to an explicit 40-hex source commit, package version, exact v0.1 search-policy schema/identifier/checksum, baseline evaluation schema/identifier/checksum, deterministic self-play configuration checksum, opening-suite checksum, seed, game completion counts, and train/validation/test occurrence counts. The sidecar is itself checksummed and fail-closed. A caller must explicitly supply the source commit; no Git, environment, filesystem, or process discovery is used by the library contract.

## Dataset admission

A structurally valid pilot dataset is not automatically large enough for tuning. S3 initially requires:

- at least 16 self-play games;
- at least 12 completed games;
- at most 250 unfinished games per 1000 games;
- at least 128 occurrence-weighted eligible training positions; and
- at least 16 occurrence-weighted eligible validation positions.

These are minimum correctness/admission thresholds, not claims of statistical sufficiency for production strength. Larger S3 tasks must record their actual scale before candidate promotion.

## Existing-evaluator parameter groups

The runtime evaluator has 816 serialized scalar slots. Six structural zero slots are not tunable, leaving 810 named optimizer parameters. S3 partitions those 810 named parameters into five disjoint pre-full groups, followed by an all-parameter pass:

| Group | Named scalars |
|---|---:|
| material and piece-square | 778 |
| mobility and activity | 16 |
| pawn structure | 8 |
| king safety and space | 6 |
| endgame king activity | 2 |
| full existing evaluator | 810 |

Each group is a deterministic fixed-size bit mask with a stable FNV-1a fingerprint.

## Mask-aware SPSA

`SpsaConfig` defaults to the historical all-810-parameter mask, preserving the historical configuration fingerprint for full-mask runs. A non-full mask is explicitly bound into the configuration fingerprint and therefore into checkpoint resume validation.

Only selected parameters receive perturbation directions or optimizer updates. Inactive parameters are restored to their reference values during projection. The coupled ten material parameters may be selected as a complete group or not at all, preventing ordering projection from changing nominally inactive material values. Regularization is normalized over the selected parameter count, not diluted over all 810 values.

Validation loss remains held out from optimizer state transitions. Existing `LossDataset::calibrate_k` calibrates `K` on training data only, and SPSA reports validation MSE separately after bounded work.

No artifact described here is a production activation mechanism. v0.1 defaults remain authoritative until the distinct S3 activation gate is explicitly approved and passes.
