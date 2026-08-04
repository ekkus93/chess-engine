# Rust offline self-play and dataset contract

Task 20 adds deterministic, offline self-play orchestration to `chess-tools`. The rules and search crates remain free of filesystem and dataset concerns. Every input and output path is supplied explicitly by the command line or the versioned configuration file.

## Commands

```bash
cargo run --release -p chess-tools -- self-play CONFIG_PATH OUTPUT_PATH
cargo run --release -p chess-tools -- self-play-validate DATASET_PATH
cargo run --release -p chess-tools -- self-play-replay DATASET_PATH GAME_ID
```

`self-play` reads exactly the named configuration and opening files, completes the requested games, validates the complete in-memory result, and only then writes `OUTPUT_PATH`. A zero-game configuration, an empty opening source, or a dataset with zero retained position records fails instead of reporting success.

`self-play-validate` parses the complete dataset, checks its schema and provenance, replays every game move by move, verifies every retained position against its game and ply, checks deterministic splits and opening selection, and rejects unmerged exact duplicates.

`self-play-replay` replays one recorded game from its initial FEN and recorded legal UCI moves. Replay does not rerun search. This makes depth-, node-, and wall-clock-limited game records independently auditable even when a future machine would not reproduce the same timing decisions.

## Configuration schema

The configuration is strict `key=value` text with schema version 1. Blank lines and lines beginning with `#` are ignored. Unknown, duplicate, or missing keys fail.

```text
schema=1
games=4
seed=12345
maximum_plies=256
white_limit=depth:3
white_tt_mib=16
white_check_extension=false
black_limit=nodes:50000
black_tt_mib=16
black_check_extension=false
claimable_draw=accept
opening_positions=exclude
split_train=80
split_validation=10
split_test=10
opening_path=fixtures/self_play_openings.tsv
```

Each side has an independent fixed transposition-table budget, search limit, and check-extension choice. Supported fixed limit forms are:

- `depth:N`
- `nodes:N`
- `time_ms:N`

The three split percentages must each be nonzero and total 100. A stable seed-derived hash assigns each complete game to exactly one of `train`, `validation`, or `test`.

`claimable_draw=accept` ends a game at an available threefold or fifty-move claim. `claimable_draw=continue` continues until checkmate, stalemate, an automatic draw, or the configured maximum ply.

`opening_positions=exclude` omits the initial position and every position reached before the first engine-selected move. `opening_positions=mark` retains those records with `eligible=false` and `filter_reason=opening`.

## Opening diversification source

The opening source is a strict version-1 tab-separated file:

```text
CHESS_SELF_PLAY_OPENINGS	1
king-pawn	rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1	e2e4 e7e5
queen-pawn	rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1	d2d4 d7d5
```

Identifiers may contain ASCII letters, digits, `.`, `_`, and `-`. Every FEN is parsed and canonicalized. Every supplied move is resolved against the exact current legal move set. Empty, duplicate-identifier, illegal, corrupt, or terminal opening lines fail.

The batch seed chooses a stable starting offset, and game IDs rotate through the source order. The complete selected opening is embedded in the generated dataset so replay never depends on the original opening file remaining available.

## Game records

Every `GAME` row records:

- game ID, derived game seed, and explicit split;
- opening identifier, initial FEN, and opening ply count;
- every opening and engine-selected UCI move;
- final FEN, absolute result, and exact termination reason;
- engine version for White and Black;
- evaluator schema, identifier, and checksum for each side;
- fixed search limit, transposition-table size, and check-extension setting for each side;
- a standalone `chess-tools self-play-replay ...` command.

Results are `1-0`, `0-1`, `1/2-1/2`, or `*`. Reaching `maximum_plies` produces `*` with `maximum_ply:N`; it is never silently converted into a valid draw.

## Position dataset records

Every `POSITION` row records:

- first source game ID and ply;
- lossless canonical six-field FEN;
- side to move and absolute final outcome;
- explicit train, validation, or test split;
- active-side engine, evaluator, and search metadata;
- opening marker, training eligibility, and filtering reason;
- exact duplicate occurrence count.

A non-opening position from a completed game is `eligible`. Retained opening positions are marked `opening`. Every position from an unfinished maximum-ply game is marked `unfinished_maximum_ply` and is not eligible.

## Duplicate policy

The generator retains the first occurrence of an exact `(split, FEN, outcome, filter_reason)` record and increments its `occurrences` count for later exact matches. Positions with different outcomes, splits, or filtering classifications remain distinct. Serialization preserves first-occurrence order and never depends on hash-map iteration order.

## Reproducibility and validation

The permanent contract is:

1. The configuration, opening source, and output path are explicit.
2. Opening selection, game-local seeds, and split assignment use fixed version-1 arithmetic.
3. Depth- and node-limited searches are deterministic for a fixed engine build and input.
4. Time-limited records remain completely replayable because replay validates recorded legal moves rather than rerunning wall-clock search.
5. Every game replays to the stored final FEN and termination reason.
6. Every position matches the stored game at the stored ply.
7. Empty output, malformed schemas, illegal moves, inconsistent provenance, and unmerged duplicates fail loudly.

The Task 20 gate requires the strict workspace checks, release perft, differential oracle, Android regressions, and the deterministic small-run integration suite to remain green.
