# Rust Advanced Classical Evaluation Protocol

Task 22 evaluates proposed classical evaluation concepts without assuming that every familiar chess heuristic deserves a new production term. The protocol is deliberately fail-closed: a proposal is measured in isolation, compared with the compact baseline, and either accepted, revised, or rejected. No experiment mutates the built-in evaluator or activates candidate weights.

## Scope

The protocol covers these eight retained candidate areas:

1. pawn-majority and candidate-passer modeling;
2. king-zone attack units;
3. defender coordination;
4. rook/queen batteries;
5. minor-piece outposts and bad bishops;
6. endgame king and passer races;
7. general simplification incentives;
8. additional endgame phase-specific PST or material scaling.

Every area has a stable machine-readable identity, a concise chess definition, and an explicit inventory of existing baseline terms that may already encode the same information.

## Evidence pipeline

`crates/chess-tools/src/advanced_evaluation.rs` implements a version-1 evidence report and the following deterministic pipeline for every area:

1. Load two isolated legal FEN fixtures.
2. Generate the color-swapped vertical mirror of every fixture.
3. Verify exact evaluator antisymmetry for both the baseline and the proposal probe.
4. Measure baseline and probe evaluation time over a fixed iteration count.
5. Run baseline and probe searches with the same fixed node budget and separate transposition tables.
6. Record move changes, absolute score movement, and exact node totals.
7. Run a fixed-seed, color-balanced candidate-versus-baseline match over independent opening pairs.
8. Compute pair-relative score, sample standard error, and the one-sided 95% lower confidence bound.
9. Record an explicit `accepted`, `revise_dedicated_implementation`, `rejected_overlap`, or `rejected_no_strength_evidence` decision.

The current experiments use an **overlap probe**: a small deterministic perturbation of existing named weights that most closely represent the proposed concept. This is a screening mechanism, not a hidden implementation of the proposed feature. It measures whether existing terms already express the concept and whether perturbing that coverage changes fixed-node search or controlled games enough to justify a dedicated implementation.

## Acceptance boundary

A strength claim requires at least **200 independent color-balanced pairs**. A smaller control run may verify fixtures, symmetry, cost accounting, search accounting, match scheduling, report serialization, and rejection behavior, but it cannot accept a term.

Acceptance additionally requires all of the following:

- exact symmetry passes;
- the proposal is not already adequately represented;
- fixed-node behavior provides measurable signal;
- the controlled match lower confidence bound clears the configured threshold;
- the evidence report validates and its checksum matches;
- activation occurs only in a separate explicit change.

A no-op or duplicate proposal is rejected as overlap. A proposal without sufficient strength evidence is rejected rather than retained speculatively.

## Report and persistence contract

The report records:

- schema version and semantic checksum;
- pair count, seed, maximum plies, search limits, TT size, check-extension policy, benchmark iterations, and fixed-node budget;
- every area definition and overlap statement;
- fixture count and symmetry result;
- baseline and probe evaluation timing;
- fixed-node positions, best-move changes, score deltas, and node totals;
- candidate wins, draws, losses, and explicit unfinished games;
- pair mean, standard error, lower confidence bound, and final decision;
- immutable `activated=false`.

Persistence uses an explicit same-directory temporary path, flush, file synchronization, atomic rename, and parent-directory synchronization. Corrupt, incomplete, reordered, non-finite, or checksum-mismatched evidence fails loudly.

## Controlled evidence run

The Task 22 control used:

- 32 independent opening pairs per area;
- 64 color-swapped games per area;
- fixed seed `570425378`;
- depth 1 search;
- maximum 8 plies;
- 1 MiB evaluator-specific transposition tables;
- 2,000 evaluation iterations per timing sample;
- 512 fixed nodes over four mirrored fixture positions per area;
- minimum acceptance sample of 200 pairs;
- report checksum `0ad7dcc3dda4cdfb`.

All 512 controlled games reached the deliberately short maximum-ply boundary and remained explicitly `unfinished`; they were not relabeled as draws. Consequently, the run is protocol and rejection evidence, not a strength claim.

| Candidate area | Symmetry | Best-move changes | Absolute score delta | Eval-time delta | Decision |
|---|---:|---:|---:|---:|---|
| Pawn majority / candidate passer | pass | 0 / 4 | 56 cp | +4.92% | `rejected_no_strength_evidence` |
| King-zone attack units | pass | 0 / 4 | 0 cp | +0.24% | `rejected_no_strength_evidence` |
| Defender coordination | pass | 0 / 4 | 46 cp | +0.05% | `rejected_overlap` |
| Rook/queen battery | pass | 0 / 4 | 0 cp | +0.01% | `rejected_no_strength_evidence` |
| Minor outposts / bad bishops | pass | 0 / 4 | 16 cp | +0.08% | `rejected_no_strength_evidence` |
| Endgame king/passer races | pass | 0 / 4 | 248 cp | +0.30% | `rejected_no_strength_evidence` |
| Simplification incentive | pass | 0 / 4 | 34 cp | +0.13% | `rejected_no_strength_evidence` |
| Endgame phase-specific scaling | pass | 0 / 4 | 0 cp | +0.45% | `rejected_overlap` |

Every fixed-node comparison searched exactly 2,048 baseline nodes and 2,048 probe nodes. Every pair mean and one-sided lower bound was exactly `0.5`, with zero sample standard error, because all games were unfinished and scored neutrally only for the declared match statistic.

## Explicit exclusions

Task 22 does not port or disguise any of the following Python concepts:

- `review_loop_guidance`;
- `anti_drift_guidance`;
- exact transcript move preferences;
- hard-coded windows for historical self-play positions;
- any term lacking measurable evidence.

No advanced term was added to the production evaluator, no default weight changed, and no candidate was activated by Task 22.
