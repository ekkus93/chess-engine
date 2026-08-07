# Rust Chess Engine S4 Hyperparameter Calibration Matrix — 2026-08-07

**Status:** Frozen before execution  
**Program:** S4 evaluation tuning calibration  
**Matrix identifier:** `S4_SPSA_INTEGER_CALIBRATION_V1`  
**Canonical TSV SHA-256:** `021a1f2cc30281b5167e0557fe68d8c3cf5d62b7f6d1789604d9d956920cad8e`  
**Total experiments:** `12`

## Purpose

S3 demonstrated nonzero loss/gradient signal but a maximum proposed floating update of only `2.06410316075983228e-04`, producing zero integer evaluator changes. S4 known-answer and degraded-evaluator gates subsequently proved that the existing SPSA transition can move integer weights when its gain is large enough.

This matrix therefore varies only the dimensions directly implicated by that evidence:

- learning rate;
- perturbation size;
- regularization off/on.

It intentionally does **not** vary decay exponents, stability constant, seed, iteration count, mask, bounds, K calibration, dataset, split, or evaluator structure. This limits confounding and prevents an open-ended search for a favorable result.

## Frozen common settings

- parameter group: `full_existing_evaluator`;
- active parameter count: `810`;
- iterations: `32`;
- step decay: `0.602`;
- perturbation decay: `0.101`;
- stability constant: `10.0`;
- minimum/maximum weight: `-2000` / `2000`;
- random seed: `1395995457` for every run;
- K minimum/maximum: `0.1` / `3.0`;
- K intervals: `20`;
- initial evaluator: authoritative v0.1 baseline;
- activation: forbidden; every result remains `activated=false`.

Using the same seed across matrix rows is intentional: the perturbation stream is held constant so the tested hyperparameters can be compared without adding seed selection as another search dimension.

## Frozen matrix

The following UTF-8 LF-terminated TSV block is the canonical matrix image whose SHA-256 is recorded above.

```text
run	learning_rate	perturbation_size	regularization_strength	iterations	step_decay	perturbation_decay	stability_constant	random_seed	candidate_identifier
1	512	2	0.0000	32	0.602	0.101	10.0	1395995457	5995501946914471937
2	512	2	0.0001	32	0.602	0.101	10.0	1395995457	5995501946914471938
3	512	8	0.0000	32	0.602	0.101	10.0	1395995457	5995501946914471939
4	512	8	0.0001	32	0.602	0.101	10.0	1395995457	5995501946914471940
5	2048	2	0.0000	32	0.602	0.101	10.0	1395995457	5995501946914471941
6	2048	2	0.0001	32	0.602	0.101	10.0	1395995457	5995501946914471942
7	2048	8	0.0000	32	0.602	0.101	10.0	1395995457	5995501946914471943
8	2048	8	0.0001	32	0.602	0.101	10.0	1395995457	5995501946914471944
9	4096	2	0.0000	32	0.602	0.101	10.0	1395995457	5995501946914471945
10	4096	2	0.0001	32	0.602	0.101	10.0	1395995457	5995501946914471946
11	4096	8	0.0000	32	0.602	0.101	10.0	1395995457	5995501946914471947
12	4096	8	0.0001	32	0.602	0.101	10.0	1395995457	5995501946914471948
```

## Execution rules

1. All 12 rows must be executed once against the same admitted stronger S4 dataset and exact split.
2. No failed or unfavorable row may be selectively rerun with a different seed.
3. Infrastructure failures are not chess/tuning results and must be repaired before evidence is accepted.
4. A row that cannot produce a structurally valid evaluator is `rejected_invalid_candidate`, not silently clipped/retried with altered hyperparameters.
5. Advancement requires, at minimum:
   - effective changed-parameter count > 0;
   - candidate value checksum differs from baseline;
   - training loss delta < 0;
   - validation loss delta <= `0.0005`;
   - `clipping_count == 0`; any explicit optimizer-bound clipping rejects the row as `rejected_clipping`;
   - artifact/trace checksums validate;
   - `activated=false`.
6. If multiple rows pass, selection for S4-9 is deterministic in this order:
   - smallest validation-loss delta;
   - then smallest training-loss delta;
   - then smallest maximum absolute parameter delta;
   - then lowest matrix run number.
7. S4-9 must repeat the selected row with identical inputs and require an identical candidate value checksum before any optional chess-strength smoke.

The `0.0005` held-out regression tolerance and zero-clipping requirement are frozen before execution. The held-out tolerance permits a small validation fluctuation during optimizer calibration but prevents material held-out degradation from being hidden by training improvement. The zero-clipping rule prevents a parameter hitting the explicit `[-2000, 2000]` optimizer boundary from being interpreted as healthy calibrated movement.
