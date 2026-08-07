# Rust Chess Engine S4 Hyperparameter Matrix Results — 2026-08-07

**Status:** Complete bounded-calibration evidence  
**Date:** 2026-08-07  
**Source SHA:** `fd940a52f2a2cc7472ef8a36c857949ec9792281`  
**Workflow run:** `31200184027`  
**Workflow job:** `92938059565`  
**Artifact ID:** `9002551314`  
**Artifact ZIP SHA-256:** `af86926588c2c3b8c9da7e5b15d2e7a039f128759a5209b8115d041d7b607ea2`  
**Frozen matrix:** `docs/RUST_CHESS_ENGINE_S4_HYPERPARAMETER_MATRIX_2026-08-07.md`  
**Matrix TSV SHA-256:** `021a1f2cc30281b5167e0557fe68d8c3cf5d62b7f6d1789604d9d956920cad8e`

## Result

All 12 predeclared SPSA rows executed exactly once against the admitted stronger S4 corpus. No row hit the explicit optimizer bounds. Every row produced a non-baseline runtime evaluator, strictly improved training loss, strictly improved held-out validation loss, remained `activated=false`, and therefore advanced to the S4-9 reproducibility gate under the frozen matrix rules.

The deterministic selection rule chose **run 11**:

- learning rate: `4096`;
- perturbation size: `8`;
- regularization: `0`;
- iterations: `32`;
- candidate value checksum: `520db5dd58086a8a`;
- candidate artifact checksum: `fe3aca3e78625310`;
- optimizer trace checksum: `cc7a7c0da94b37d3`;
- changed parameters: `645 / 810`;
- maximum absolute integer parameter delta: `8`;
- mean absolute integer parameter delta: `1.41604938271604941`;
- training-loss delta: `-4.83858551862105524e-3`;
- validation-loss delta: `-6.37062441281038838e-3`;
- clipping count: `0`;
- activation: `false`.

Run 11 won because it had the smallest (most improved) held-out validation-loss delta. No tie-breaker was needed.

## Exact corpus used

The workflow regenerated the stronger S4 corpus on the matrix SHA and required the frozen dataset identity before executing any row:

- dataset checksum: `85c0e5949cb329e3`;
- games: `96`;
- positions / eligible rows: `1,530`;
- training occurrences: `8,202`;
- validation occurrences: `2,465`;
- excluded rows: `0`;
- admitted for tuning: `true`.

The source-bound manifest checksum on this matrix SHA was `a1d6f7c148e1f385`. The dataset checksum remained exactly the frozen S4-7 identity.

## All matrix rows

| Run | LR | Perturb | Reg | Train delta | Validation delta | Changed | Max Δ | Mean | Zero-after-quant. | Clip | Value checksum | Artifact checksum | Trace checksum | Disposition |
|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|---|---|---|---|
| 1 | 512 | 2 | 0 | `-3.88641952657989287e-4` | `-5.53403648083428124e-4` | 10 | 1 | `1.23456790123456783e-2` | 25,819 | 0 | `c720471c94c44a4d` | `22eaf5d96a238f8b` | `fc3cee73566c0c04` | advances |
| 2 | 512 | 2 | 0.0001 | `-3.88641952657989287e-4` | `-5.53403648083428124e-4` | 10 | 1 | `1.23456790123456783e-2` | 25,817 | 0 | `c720471c94c44a4d` | `311ca41cfc22fbcb` | `ba335c19024bd8ff` | advances |
| 3 | 512 | 8 | 0 | `-3.81844591256397248e-4` | `-5.56863167160859263e-4` | 15 | 1 | `1.85185185185185175e-2` | 25,833 | 0 | `203fec2ab0fc7f04` | `025e0b350ff78220` | `6f00dbf29ab237b2` | advances |
| 4 | 512 | 8 | 0.0001 | `-3.81074050697746691e-4` | `-5.47431724077049320e-4` | 7 | 1 | `8.64197530864197448e-3` | 25,833 | 0 | `e164317beabc5d0e` | `2822daa88cad0ea0` | `05b190805164dc6c` | advances |
| 5 | 2048 | 2 | 0 | `-2.45709451660872102e-3` | `-3.16333537547988652e-3` | 464 | 4 | `6.60493827160493874e-1` | 22,653 | 0 | `392a956edd6d08d9` | `f6eb5678ef66db05` | `b2d41a083ab9b7f5` | advances |
| 6 | 2048 | 2 | 0.0001 | `-2.45790132284084972e-3` | `-3.16469342553740707e-3` | 461 | 4 | `6.54320987654321007e-1` | 22,702 | 0 | `df2bbdc252fdc4ca` | `51354c08955cb108` | `e259906938e12606` | advances |
| 7 | 2048 | 8 | 0 | `-2.44570718814433874e-3` | `-3.13886902219848163e-3` | 453 | 4 | `6.48148148148148140e-1` | 22,749 | 0 | `4fed1e9bd412dbfb` | `aa449ac79f4b2681` | `f8bd0e71d04bb1f8` | advances |
| 8 | 2048 | 8 | 0.0001 | `-2.44825207889633190e-3` | `-3.14669976353243452e-3` | 454 | 4 | `6.50617283950617242e-1` | 22,761 | 0 | `3ad939e7305de958` | `7b3a6534cc0ea824` | `1f60d6178a36cbaa` | advances |
| 9 | 4096 | 2 | 0 | `-4.79314783113922449e-3` | `-6.31116644395489368e-3` | 643 | 8 | `1.44074074074074066` | 18,509 | 0 | `3a33190b030a2499` | `6b4bb2259247ba8b` | `b87a66ac503fd75d` | advances |
| 10 | 4096 | 2 | 0.0001 | `-4.80150598582070043e-3` | `-6.30860593598016328e-3` | 639 | 8 | `1.43456790123456801` | 18,560 | 0 | `fbf7146e4c818935` | `6a3c80ca1d60a4a1` | `10872f483216d197` | advances |
| 11 | 4096 | 8 | 0 | `-4.83858551862105524e-3` | `-6.37062441281038838e-3` | 645 | 8 | `1.41604938271604941` | 18,628 | 0 | `520db5dd58086a8a` | `fe3aca3e78625310` | `cc7a7c0da94b37d3` | **selected** |
| 12 | 4096 | 8 | 0.0001 | `-4.79305111285940888e-3` | `-6.33025761186402358e-3` | 643 | 8 | `1.39753086419753081` | 18,664 | 0 | `0fde79b4c45f3a4a` | `dcd760c131b42402` | `e8d663fc0a19d88b` | advances |

## Interpretation

S4 has now disproved the hypothesis that integer-valued SPSA is inherently unable to tune the current evaluator. The S3 failure was a calibration failure: its learning-rate regime made effective integer movement practically impossible. Under bounded, predeclared larger gains, the same optimizer/update implementation produced controlled movement with no clipping and simultaneous train/held-out improvement.

This does **not** establish chess playing-strength improvement and does not authorize production activation. S4-9 must reproduce the selected row from identical chess/tuning inputs and validate the candidate through the existing inactive candidate registry. Only then may the optional S4-10 development chess-strength smoke run.
