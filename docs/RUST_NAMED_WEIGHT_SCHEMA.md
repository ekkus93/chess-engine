# Rust named evaluation-weight schema

## Scope

Task 21.1 defines the stable, machine-readable boundary between the Rust evaluator and future offline tuning work. It does not implement an optimizer, automatically load candidate weights, or change the active built-in evaluation weights.

The runtime evaluator continues to use `chess_search::EvaluationWeights`. The `chess-tune` crate owns the named tuning schema, training provenance, artifact serialization, and candidate validation.

## Tunable parameter schema

The canonical tuning vector contains exactly **810 signed scalar parameters** in this order:

1. Material values for pawn, knight, bishop, rook, and queen, with middlegame and endgame components: 10 scalars.
2. Piece-square values for all six piece kinds, all 64 white-oriented squares, and both phases: 768 scalars.
3. Mobility values for knight, bishop, rook, and queen, with both phases: 8 scalars.
4. Twelve scalar evaluation features, with both phases: 24 scalars.

The schema exposes every scalar through a stable zero-based index, semantic descriptor, and canonical name. Representative names are:

- `material.pawn.mg`
- `material.queen.eg`
- `piece_square.pawn.a8.mg`
- `piece_square.king.h1.eg`
- `mobility.knight.mg`
- `feature.king_activity.eg`

Names and ordering are part of the serialized contract. Renaming or reordering a parameter requires a named-artifact schema version change.

## Structural constants

The following evaluator fields are structural and are not tunable parameters:

- maximum tapered-evaluation phase;
- phase units contributed by each piece kind;
- king material value, fixed at zero;
- pawn mobility value, fixed at zero;
- king mobility value, fixed at zero.

They are represented by `chess_search::EVALUATION_STRUCTURE`, with their own schema version and checksum. Runtime tapered evaluation consumes this structure directly. A tuning artifact records the expected structure version and checksum and is rejected if either differs from the running engine.

Reconstructing `EvaluationWeights` from the 810-value tuning vector explicitly restores the fixed structural weight fields. The named tuning API cannot address those fields.

## Versioned named artifacts

`NamedWeightArtifact` records:

- named-artifact schema version;
- runtime evaluation-weight schema version;
- evaluator-structure schema version and checksum;
- nonzero weight-set identifier;
- complete training metadata;
- all 810 canonical parameter names and values;
- canonical artifact checksum.

The line-oriented serialization is deterministic and strict. Parsing requires the exact format marker, header order, parameter count, canonical parameter order, names, numeric forms, and final checksum. Unknown, missing, duplicated, renamed, reordered, or malformed fields fail loudly.

The artifact checksum covers all schema versions, the evaluator-structure checksum, identifier, every training-metadata field, parameter count, every parameter name, and every parameter value.

## Training provenance

Training metadata is divided into two explicit records.

`TrainingRunProvenance` records:

- trainer implementation/configuration identifier;
- exact 20-byte source commit;
- deterministic random seed;
- completed optimizer iteration count;
- caller-supplied Unix generation timestamp.

`TrainingDatasetProvenance` records:

- dataset schema version;
- canonical dataset checksum;
- training-position count;
- separately held-out validation-position count.

The artifact rejects empty identifiers, an all-zero source commit, missing dataset schema/checksum, empty training or validation splits, zero completed iterations, and a zero generation timestamp.

## Activation boundary

Creating, parsing, or validating a named weight artifact does **not** activate it. The built-in baseline remains the default. A future task must define an explicit caller-controlled candidate-loading and promotion path, including regression and playing-strength gates, before tuned weights can replace the baseline.

There is no implicit filesystem lookup, environment-variable override, automatic fallback, or silent candidate activation in Task 21.1.

## Validation expectations

The permanent Rust CI gate must continue to enforce:

- `cargo fmt --check`;
- workspace compilation for all targets and features;
- Clippy with warnings denied;
- complete Rust tests;
- authoritative perft;
- warning-free documentation;
- debug and release builds;
- differential-oracle validation.

Task-specific tests verify schema size and stable names, uniqueness, tunable-vector round trips, structural restoration, complete artifact round trips, checksum coverage, malformed-name rejection, checksum corruption rejection, and incomplete-provenance rejection.

## Task 21.1 validation evidence

The exact validated implementation head is `8410beb6dc22684052ded86a6f2fe71cf9d1e444`.

- Rust workflow run `30889939723`, job `91929495312`: formatting, workspace check, Clippy with warnings denied, complete Rust tests, authoritative release perft, warning-free rustdoc, debug/release builds, and the differential oracle passed.
- Android workflow run `30889939726`: host JVM JNI job `91929459955`, API-35 instrumentation job `91929459977`, and Android/Kotlin lint job `91929460081` all passed.

Task 21.1 is complete. Task 21.2 owns the loss pipeline.
