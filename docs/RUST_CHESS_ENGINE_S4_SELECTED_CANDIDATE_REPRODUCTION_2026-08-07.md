# Rust Chess Engine S4 Selected Candidate Reproduction — 2026-08-07

**Status:** Complete reproducibility and registry evidence  
**Date:** 2026-08-07  
**Source SHA:** `21fa2704b1e99b04d5d6b0231eb33bc232ce26ec`  
**Workflow run:** `31201066297`  
**Workflow job:** `92940904715`  
**Artifact ID:** `9002851591`  
**Artifact ZIP SHA-256:** `21eea3234afe7fd00ee69681536bad8e6fa21186f05ed1816888a40f02923242`  
**Matrix source SHA:** `fd940a52f2a2cc7472ef8a36c857949ec9792281`  
**Selected matrix row:** `11`

## Result

S4-9 reproduced the selected S4-8 tuning result exactly under a fresh source-bound provenance image. Two consecutive invocations used the same admitted stronger corpus, exact tuning configuration, exact output path, exact seed, and exact source SHA. The complete output directories recursively diffed equal and the CLI logs compared byte-for-byte.

The reproduced candidate retained the matrix-selected runtime evaluation value checksum:

`520db5dd58086a8a`

The existing strict S3 candidate-envelope/registry contract accepted exactly one inactive candidate with loss decision `advance`. No new candidate-registry format was created for S4.

## Exact dataset identity

The stronger calibration corpus was regenerated on the S4-9 source SHA and required before tuning:

- dataset checksum: `85c0e5949cb329e3`;
- source-bound manifest checksum: `8a2ecb9725e52017`;
- games: `96`;
- positions / eligible rows: `1,530`;
- training occurrences: `8,202`;
- validation occurrences: `2,465`;
- excluded rows: `0`;
- admitted for tuning: `true`.

The source-bound manifest checksum differs from prior S4 runs by design because the strict manifest binds source/invocation provenance. The chess dataset checksum remains the frozen S4-7 identity.

## Exact selected tuning configuration

- parameter group: `full_existing_evaluator`;
- candidate identifier: decimal `5995501946914471947`, canonical hex `53344d415400000b`;
- generated timestamp: `1786112011`;
- iterations: `32`;
- learning rate: `4096`;
- step decay: `0.602`;
- perturbation size: `8`;
- perturbation decay: `0.101`;
- stability constant: `10.0`;
- minimum/maximum weight: `-2000` / `2000`;
- regularization strength: `0`;
- random seed: `1395995457`;
- K range: `0.1` through `3.0`, `20` intervals;
- activation: forbidden.

## Reproduced movement and loss evidence

The fresh run reproduced the matrix-selected semantic result:

- candidate value checksum: `520db5dd58086a8a`;
- changed parameters: `645 / 810`;
- maximum absolute integer parameter delta: `8`;
- training-loss delta: `-4.83858551862105524e-3`;
- held-out validation-loss delta: `-6.37062441281038838e-3`;
- clipping count: `0`;
- `activated=false`.

Both train and held-out loss strictly improved relative to the authoritative v0.1 baseline evaluator on the same frozen split.

## Registry evidence

The provenance-bound `tune-group` publication produced and validated:

- `candidate-weights.txt`;
- `tuning-report.txt`;
- `checkpoint.bin`;
- `s4-optimizer-trace.txt`;
- `s4-summary.tsv`;
- `s3-candidate-envelope.txt`;
- `s3-candidate-registry.tsv`;
- `ACTIVATION_DISABLED`.

The registry evidence required:

- candidate value checksum `520db5dd58086a8a`;
- loss decision `advance`;
- registered candidate count `1`;
- activation `false`.

The second exact invocation reproduced the entire publication directory and CLI output byte-for-byte. Therefore the tuning signal is not a one-off stochastic artifact of a single run.

## S4 method disposition from S4-9

The S4 tuning method has passed its calibration objective:

1. S3 zero movement was diagnosed as quantization-limited rather than signal-free.
2. Known-answer tests proved the same update path can cross integer materialization boundaries and converge.
3. A deliberately degraded real chess evaluator recovered under controlled tuning.
4. A stronger deterministic chess corpus was established.
5. A predeclared bounded matrix found controlled, non-clipped real-data movement with both training and held-out improvement.
6. The selected row reproduced exactly and registered fail-closed as one inactive `advance` candidate.

This is sufficient for S4-9 method acceptance. It is **not** production strength evidence and does not authorize activation. The optional S4-10 development chess-strength smoke may now compare the candidate against the authoritative v0.1 evaluator under equal-resource paired protocols.
