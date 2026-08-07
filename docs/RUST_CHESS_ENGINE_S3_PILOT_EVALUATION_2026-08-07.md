# Rust Chess Engine S3 Pilot Evaluation Evidence — 2026-08-07

**Status:** Complete — no pilot candidate advances  
**Program:** S3 evaluation strength  
**Experiment source SHA:** `9ba680dbec8b6ec8d5aebf55f06ff4b3db71e70d`  
**Workflow:** `.github/workflows/s3-evaluation-experiment.yml`  
**Successful run/job:** `31184450979` / `92885406054`  
**Artifact:** `8996149049` (`s3-evaluation-experiment-9ba680dbec8b6ec8d5aebf55f06ff4b3db71e70d`)  
**Artifact digest:** `sha256:797a03d73830e30ead1537378716b02a9aa91553764f9992388876ec0d267d`  
**Activation:** `false`

## Purpose

This was an intentionally bounded pipeline-and-sensitivity pilot, not production strength validation. It exercised deterministic S3 self-play packaging, strict dataset admission, all six predeclared existing-evaluator tuning groups, held-out loss reporting, inactive candidate artifacts, and byte-reproducibility. It was not authorized to change production weights, search policy, package version, adapters, or activation state.

## Self-play dataset

Frozen configuration:

- games: `32`
- seed: `1395864373`
- maximum plies: `256`
- white/black search: depth `1`
- white/black transposition table: `1 MiB`
- claimable-draw policy: `accept`
- opening-position policy: `exclude`
- train/validation/test split: `70/20/10`
- openings: `fixtures/self_play_openings.tsv`

The exact S3 package was generated twice on the same source SHA and compared recursively byte-for-byte. Both generations matched.

Dataset evidence:

- dataset checksum: `c691d1928ffda61b`
- S3 manifest checksum: `6aef02a9b375c5a3`
- training occurrences: `2,066`
- validation occurrences: `195`
- excluded rows: `0`
- admission result: `true`
- activation: `false`

The failed predecessor run `31184300662` is infrastructure history only. It reached two matching dataset generations but stopped because the workflow used nonexistent command `cmp -r`. No dataset/source defect was hidden; the workflow was corrected to recursive `diff` and rerun from a new exact SHA.

## Tuning configuration

Each group used:

- maximum/advance iterations: `8` / `8`
- learning rate: `0.5`
- step decay: `0.602`
- perturbation size: `2.0`
- perturbation decay: `0.101`
- stability constant: `10.0`
- bounds: `[-2000, 2000]`
- regularization: `0.0001`
- K calibration range: `[0.1, 3.0]`, `20` intervals
- distinct deterministic candidate identifiers and seeds
- S3 dataset manifest/source-SHA admission required
- candidate outputs explicitly inactive

The pawn-structure group was rerun from scratch and compared byte-for-byte with its first output and log.

## Held-out loss results

All groups started and finished at exactly the same recorded losses:

- initial/final training loss: `1.25882801415297285e-1`
- initial/final held-out validation loss: `6.05660231663427279e-2`
- training delta: `0.0`
- validation delta: `0.0`

| Group | Mask fingerprint | Candidate ID | Candidate artifact checksum | Tuning report checksum | Disposition |
|---|---|---|---|---|---|
| material and piece-square | `6a6ca13fc4a12d1f` | `5333475250303031` | `dd9aeab9c3678ab9` | `893feceb8bde8e93` | reject — no training improvement |
| mobility and activity | `78f56bc1fbfd98c5` | `5333475250303032` | `aa3989574aa36b99` | `dd6b7e31d231224b` | reject — no training improvement |
| pawn structure | `6c1cbe6802740220` | `5333475250303033` | `587cfec136eb6cb1` | `e94dbec1cc0752ff` | reject — no training improvement |
| king safety and space | `0c98c164c0951c99` | `5333475250303034` | `c8c68ae9d2a93099` | `40dba148d3ccf141` | reject — no training improvement |
| endgame king activity | `7306dfbdf5aa6544` | `5333475250303035` | `2353b90deb3f3321` | `8da683cc3fa9e7f7` | reject — no training improvement |
| full existing evaluator | `02c6c0907d4847c3` | `5333475250303036` | `84e3024344cc77a1` | `ac5677186c1599df` | reject — no training improvement |

## Candidate-value identity check

The `parameter.*` value lines from all six generated candidate-weight artifacts were independently normalized and SHA-256 hashed. Every group produced the identical parameter-value digest:

`689d960bd3a2751604165861116a0bc3d10afa4aea32bbbb82e808a59c777066`

Therefore the pilot did not merely fail to improve the reported objective: all six candidate payloads retained the same evaluator parameter values. Candidate/report identifiers differ because their provenance and group configurations differ, but the evaluator values do not.

## Advancement disposition

The S3 held-out advancement policy requires strict training-loss improvement; a training improvement may advance only when held-out validation does not regress beyond the frozen deterministic tolerance. The pilot candidates have zero training improvement, so every group receives `reject_no_training_improvement`.

No pilot candidate is eligible for S3 development or production strength matches. Running large paired matches between baseline-identical evaluator payloads would consume resources without testing a real candidate. S3-7 and S3-10 therefore use the explicit no-eligible-candidate path rather than manufacturing redundant match evidence.

This result does not prove that evaluation tuning is generally ineffective. It proves only that this bounded depth-one, 32-game, eight-iteration pilot did not move the evaluator. A future tuning program may use larger/deeper data or different optimizer schedules under a new explicit evidence plan.
