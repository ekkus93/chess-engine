# Rust Chess Engine S4 Zero-Movement Diagnosis — 2026-08-07

**Status:** Complete diagnostic evidence  
**Date:** 2026-08-07  
**S4 source SHA:** `17fa3dd22b2c3606ede7303186cbe1c11259c5b9`  
**Workflow run:** `31198269449`  
**Workflow job:** `92931740915`  
**Artifact ID:** `9001742616`  
**Artifact ZIP SHA-256:** `63e957572b1a872a6cc1c109332c7e09aef2c29b73449eb9887470dfdff5e39d`

## Result

S4 reproduced the S3 reviewed full-evaluator pilot with the same chess-data image and the same tuning configuration, while adding strict per-iteration optimizer diagnostics. The zero-movement result is **quantization-limited**.

The optimizer had a measurable nonzero objective difference and a measurable nonzero gradient. It did not hit configured weight bounds. The proposed floating-point updates were simply far too small to change any integer runtime evaluation weight.

This rules out the following as the primary cause of the S3 pilot result:

- zero gradient;
- zero objective signal;
- min/max clipping;
- hidden optimizer early exit;
- inactive-mask behavior;
- silent replacement of the tuning candidate;
- absence of an optimizer state transition.

The S3 pilot's effective failure mode was the interaction between its gain schedule and integer evaluator materialization.

## Exact reproduction contract

The successful S4 reproduction retained the S3 pilot's self-play configuration:

- games: `32`;
- self-play seed: `1395864373`;
- maximum plies: `256`;
- White/Black search limit: `depth:1`;
- White/Black TT budget: `1 MiB`;
- check extension: disabled;
- claimable draws: accepted;
- opening positions: excluded;
- split: `70/20/10` train/validation/test;
- opening source: `fixtures/self_play_openings.tsv`;
- canonical output path: `/tmp/s3-data`.

The output path is part of self-play replay provenance, so preserving `/tmp/s3-data` is required for byte-identical S3 dataset reproduction.

The reproduced dataset matched S3 exactly:

- dataset checksum: `c691d1928ffda61b`;
- games: `32`;
- positions: `760`;
- training occurrences: `2,066`;
- validation occurrences: `195`;
- excluded rows: `0`;
- admitted for tuning: `true`.

The S4 manifest checksum is `baf99d1663f52886`. It correctly differs from the historical S3 manifest because the strict manifest also binds current source/invocation provenance.

## Frozen S3 tuning configuration

- group: `full_existing_evaluator`;
- active parameters: `810`;
- group mask fingerprint: `02c6c0907d4847c3`;
- maximum iterations: `8`;
- advance iterations: `8`;
- learning rate: `0.5`;
- step decay: `0.602`;
- perturbation size: `2.0`;
- perturbation decay: `0.101`;
- stability constant: `10.0`;
- minimum/maximum weight: `-2000` / `2000`;
- regularization strength: `0.0001`;
- random seed: `1395864499`;
- K range: `0.1` to `3.0` over `20` intervals.

The reproduced final candidate remained `533347525030305c`, with training-loss delta `0`, validation-loss delta `0`, and `activated=false`.

## Per-iteration arithmetic diagnosis

Across all eight iterations:

| Measurement | Result |
|---|---:|
| Maximum absolute objective difference | `7.03043834947084112e-03` |
| Maximum absolute gradient estimate | `2.02176406002437924e-03` |
| Maximum absolute proposed floating update | `2.06410316075983228e-04` |
| Zero-after-quantization parameter-iterations | `6,480` |
| Effective integer updates | `0` |
| Clipped updates | `0` |
| Changed runtime parameters | `0` |
| Classification | `quantization_limited` |

`6,480 = 810 × 8`: every selected parameter in every S3 pilot iteration received an effective runtime value identical to its pre-iteration integer value.

The maximum proposed floating update, approximately `0.0002064`, was over three orders of magnitude below a half-centipawn integer-rounding boundary. Therefore the S3 learning-rate/schedule regime could not plausibly move an integer evaluator weight in this pilot even though the loss function supplied nonzero directional signal.

## Consequence for S4

S4 must not solve this by silently changing numeric representation or by blindly multiplying the learning rate until something moves. The next gates are controlled known-answer tests and bounded calibration:

1. prove sub-integer updates are correctly diagnosed as quantization-limited;
2. prove sufficiently large controlled updates survive integer materialization;
3. prove clipping and regularization accounting independently;
4. prove the same production SPSA transition can recover known synthetic objectives;
5. only then predeclare a bounded hyperparameter matrix for chess data.

No production evaluator, public adapter, version, search policy, opening behavior, or activation state changed as a result of this diagnosis.
