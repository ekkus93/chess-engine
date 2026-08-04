# Rust Baseline Evaluator and Trace

This document defines the static-evaluation contract introduced by Task 12. The evaluator lives in `chess-search`, depends only on `chess-core`, and is intentionally independent of UCI, filesystems, FFI, JNI, and application state.

## Score convention

`Score` is a signed centipawn value from the side-to-move perspective. Positive values favor the side to move, which permits direct use by a negamax search.

Static evaluation is clamped to plus or minus 20,000 centipawns. Mate scores occupy a separate band around plus or minus 30,000 and encode distance in plies. Static terms therefore cannot collide with a mate result.

Tests prove:

- the starting position evaluates to exactly zero;
- changing only the side to move negates a score;
- color-swapped, vertically mirrored positions retain the same relative score;
- mate scores negate and preserve distance exactly.

## Tapered evaluation

Every named weight is a middlegame/endgame pair. The phase ranges from zero through 24 and is derived from remaining knights, bishops, rooks, and queens. Each term is accumulated as a white-minus-black pair and blended once at the final phase before conversion to the side-to-move convention.

The baseline evaluator includes:

- material;
- piece-square tables;
- mobility for knights, bishops, rooks, and queens;
- isolated and doubled pawn penalties;
- passed and connected pawn bonuses scaled by advancement;
- bishop-pair bonus;
- rook open-file and semi-open-file bonuses;
- rook seventh-rank activity;
- phase-tapered pawn shield and enemy king-zone pressure;
- controlled enemy-space bonus;
- endgame king centralization.

The baseline values are explicit defaults. They are a deterministic starting point for later tuning, not an assertion that the engine has already reached a final strength configuration.

## Allocation and data-flow contract

Normal `evaluate()` and `evaluate_with_weights()` execution uses fixed structs, fixed arrays, bitboards, stack locals, and existing position attack primitives. It does not construct vectors, strings, maps, trace dictionaries, or filesystem objects.

The opt-in trace is also a fixed `EvaluationTrace` struct. Tool-only benchmark and serialization paths may allocate because they are outside recursive search.

Task 12 does not add incremental evaluation state to `Position`; later measured optimization may do so only after profiling demonstrates a need and restoration tests protect the new state.

## Evaluation trace

The trace exposes the blended contribution of:

- material;
- piece-square tables;
- mobility;
- isolated, doubled, passed, and connected pawns;
- bishop pair;
- rook files and seventh-rank activity;
- king shield and king-zone attack pressure;
- space;
- king activity;
- phase and total.

Every value follows the public side-to-move convention. `component_sum()` must equal `total`, and the trace total must equal normal evaluation exactly. These relationships are enforced by tests.

`chess-tools eval [FEN]` prints the stable tab-delimited trace for diagnostics.

## Named and versioned weights

`EvaluationWeights` is a strongly typed structure containing all named scalar and table values. `EvaluationWeightSet` adds:

- schema version `1`;
- a non-zero 64-bit identifier;
- the named weights;
- a canonical FNV-1a checksum.

The built-in baseline identifier is `424153454c494e45` and its validated checksum is `d2cca7ae10ec6e34`.

Validation rejects unsupported schema versions, zero identifiers, out-of-range values, invalid material ordering, and checksum mismatches. The canonical dense vector contains 816 signed 16-bit values and round-trips exactly to the named structure.

Serialization is implemented in `chess-tools`, not in the search core. The format contains an explicit marker, schema, identifier, checksum, and exact value count. Commands are:

```text
chess-tools weights-export
chess-tools weights-validate PATH
```

No component scans conventional directories or automatically loads a weight file. A caller must select and validate a weight set explicitly.

## Benchmark interface and evidence

`chess-tools eval-bench ITERATIONS [FEN]` benchmarks stable coarse groups and the full evaluator while using `black_box` and a deterministic accumulator.

On GitHub's Ubuntu 24.04 hosted runner, release-mode starting-position measurements for 20,000 iterations were:

| Group | Total nanoseconds | Approximate nanoseconds/evaluation |
|---|---:|---:|
| Material and PSQT | 2,818,742 | 140.9 |
| Pawn structure | 9,214,918 | 460.7 |
| Mobility and activity | 3,769,019 | 188.5 |
| King and space | 3,480,964 | 174.0 |
| Full evaluation | 19,596,825 | 979.8 |

These figures are reproducibility evidence for the implementation environment, not a cross-machine performance guarantee. Task 24 owns formal performance regression policy and measured optimization.

## Exclusion audit

The Rust evaluator contains only general board features listed in the Task 12 contract. Repository search and source inspection found no review-loop, anti-drift, transcript-specific, exact-scenario, or opponent-transcript guidance in the Rust evaluator or weight schema. No Python evaluator patch module was translated wholesale.

## Validation evidence

- Formatted implementation SHA: `d8547cc258ecc2e52b8e4eb7ef287d92d5d0a04f`.
- Permanent implementation CI run/job: `30734451785` / `91460574656`.
- Results: workspace assets, lockfile, metadata, rustfmt, Cargo check, Clippy with warnings denied, 103 executed Rust tests, release depth-four perft, rustdoc with warnings denied, debug build, release build, and the independent differential corpus all passed.
- Benchmark/tooling run/job: `30734335652` / `91460185440`.
- Tooling results: fixed trace, five release benchmark groups, explicit weight export, and validated import passed.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime and dependency `punycode` deprecation notices only.

Task 13 may use this score and evaluator contract while implementing reference minimax and negamax alpha-beta.
