# Rust Chess Engine Port Baseline and Decision Record

**Status:** Source inventory complete; runtime capture pending  
**Date:** 2026-08-01  
**Target branch:** `rust-engine`  
**Baseline commit before Rust source changes:** `f743013a84173b551eac5488c638cb48098ec6d0`  
**Authoritative specification:** `docs/RUST_CHESS_ENGINE_PORT_SPEC_2026-08-01.md`  
**Authoritative tracker:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`

---

## 1. Purpose

This document freezes the Python implementation as a migration reference before Rust source work begins. It identifies:

- the exact source snapshot being used as the historical baseline;
- the commands needed to reproduce tests, perft, and UCI behavior;
- the Python modules and concepts that may inform the Rust implementation;
- the Python architecture and behavior that must not be translated;
- historical engine-strength and tuning artifacts that may be used only as comparison evidence;
- the remaining runtime evidence required before Task 0 can be declared complete.

This is a decision record, not a compatibility promise. The Rust engine will preserve useful chess behavior and engineering lessons while replacing the Python architecture.

---

## 2. Frozen source snapshot

The `rust-engine` ref was compared against commit:

```text
f743013a84173b551eac5488c638cb48098ec6d0
```

The comparison reported `identical`, with zero commits ahead or behind. This SHA is therefore the authoritative pre-Rust-source baseline.

At this snapshot:

- no root `Cargo.toml` exists;
- no Rust workspace or Rust crate exists;
- the branch CI workflow is Rust-only and intentionally fails at `Verify Cargo workspace` until Task 1 creates the workspace;
- the Python implementation remains under `chess_game/` as reference material;
- the Python tests remain under `tests/` as reference and differential-test material;
- no Python internals were modified to establish this baseline.

---

## 3. Runtime evidence status

The repository source and commit history can be inspected through the GitHub connector in the current execution environment, but the repository cannot be cloned or executed locally because outbound GitHub DNS is unavailable and the GitHub CLI is not installed. Connector-authored commits also do not start normal push-triggered GitHub Actions runs.

Accordingly, this document does **not** claim that the current Python suites, perft timings, or UCI smoke test were executed at the baseline SHA during this Ralph Loop iteration.

The following items remain open and must be populated from an environment that can execute the repository:

- fast Python test result;
- slow Python test result;
- current perft result and timings;
- current UCI smoke transcript;
- current lint result, if retained as supplementary historical evidence.

A reproducible capture script is added separately so these results can be collected without changing Python engine behavior.

Historical commit messages and documentation are recorded below, but they are not substituted for a fresh baseline run.

---

## 4. Reproduction contract for the Python baseline

The project declares Python 3.11 or newer and uses `uv` for environment management.

### 4.1 Environment

```bash
uv sync --extra dev
```

### 4.2 Fast suite

```bash
uv run python -m pytest tests/ -q -m "not slow"
```

The README describes this as the unit, smoke, and shallow-search suite.

### 4.3 Slow suite

```bash
uv run python -m pytest tests/ -q -m "slow"
```

The README describes this as the expensive depth-3-or-greater engine-strength regression suite.

### 4.4 Full suite

```bash
uv run python -m pytest tests/ -q
```

### 4.5 Historical Python lint commands

These commands are retained only to characterize the reference implementation. They are not part of `rust-engine` CI.

```bash
uv run python -m ruff check chess_game tests
uv run python -m mypy chess_game
uv run python -m pylint chess_game
```

### 4.6 Perft oracle

`tests/test_perft.py` defines these exact starting-position node counts:

| Depth | Nodes | Current classification |
|---:|---:|---|
| 1 | 20 | fast |
| 2 | 400 | fast |
| 3 | 8,902 | fast |
| 4 | 197,281 | slow |

The Python helper recursively clones the board for every child. The counts are useful; the implementation strategy is not.

The same test module contains smoke-only positions for:

- castling;
- en passant;
- promotion;
- check evasion.

Those special positions do not currently assert authoritative exact node counts, so the Rust project must replace or supplement them with known-count suites before claiming move-generation completeness.

### 4.7 UCI smoke contract

The Python UCI entry point is:

```bash
uv run python -m chess_game.uci
```

The minimum smoke sequence to capture is:

```text
uci
isready
position startpos moves e2e4 e7e5
go depth 1
quit
```

Expected protocol properties:

- `uci` emits engine identification followed by `uciok`;
- `isready` emits `readyok`;
- `go depth 1` emits at least one `info` line and one legal `bestmove` line;
- malformed state must not produce a fabricated legal move;
- the process must terminate cleanly on `quit`.

The exact transcript must be recorded when runtime capture is available.

---

## 5. Historical strength, self-play, and tuning evidence

These records are historical comparison points only. They are not Rust acceptance thresholds and are not proof of the current baseline SHA.

### 5.1 Fast-suite scale

Commit `f7e8649647e72b6a7028c043b5259216547260e4` reported:

- 1,203 fast tests passing;
- Stockfish annotation and Stockfish-targeted tuning infrastructure added.

The exact current test count must be measured rather than inferred from that commit.

### 5.2 Self-play and Stockfish corpus

Commit `19754e9281268a3fbaf7c12516b2efc1df1099e8` reported:

- 300 Stockfish depth-8 self-play games;
- 13,007 unique FENs;
- 12,990 positions annotated at depth 10;
- a 100-game depth-2 validation match ending 50 wins and 50 losses, with the candidate weights not promoted.

The corpus may be useful as a future versioned Rust tuning input only after its provenance, format, licensing, and integrity are documented.

### 5.3 Earlier tuning result

Commit `bbe50133008f40331f6ee07bc34aac322d8010c4` reported:

- ridge-regression PST tuning on 2,561 depth-3 self-play positions;
- validation RMSE improvement of 21 centipawns;
- a 20-game depth-3 result of 10.5/20;
- 1,140 fast tests passing at that historical point.

This is useful as evidence that tuning pipelines can overfit or be underpowered. Rust tuning must use explicit promotion gates and versioned datasets.

### 5.4 Known tuning failure mode

Commit `4142d875790da5ca77eda44a10056f298748a046` records removal of a bad automatically promoted weight file whose material values were nonsensical. The Rust implementation must never silently change engine behavior because a conventional-path file exists.

---

## 6. Python reference inventory

### 6.1 Rules and board state

Primary modules:

- `chess_game/chess/board/board.py`
- `chess_game/chess/board/board_setup.py`
- `chess_game/chess/board/move_execution.py`
- `chess_game/chess/board/move_validation.py`
- `chess_game/chess/board/game_state.py`
- `chess_game/chess/board/castling.py`
- `chess_game/chess/board/en_passant.py`
- `chess_game/chess/board/promotion.py`
- `chess_game/chess/board/attack_utils.py`
- `chess_game/chess/board/path_validator.py`
- `chess_game/chess/board/piece_validation.py`
- `chess_game/chess/pieces/piece_movers.py`
- `chess_game/chess/types.py`
- `chess_game/chess/color.py`
- `chess_game/chess/constants.py`
- `chess_game/chess/coords.py`

Useful concepts to retain:

- row 0 maps to rank 8 and row 7 maps to rank 1;
- complete legal-move coverage for ordinary moves, castling, en passant, and all promotions;
- explicit game-state queries for check, checkmate, stalemate, repetition, and move-count rules;
- test-driven edge-case development.

Do not translate:

- the mutable nested `Board` object graph;
- `Piece.square` as a second location source of truth;
- compatibility constant classes for rows, columns, and squares;
- raw tuple moves;
- clone-per-child recursion;
- draw shortcuts described in Section 8.

Rust destination milestones:

- Tasks 2 through 10;
- Task 11 for perft and differential validation;
- Task 23 for adversarial and property testing.

### 6.2 FEN and notation

Primary modules:

- `chess_game/chess/board/board_fen.py`
- `chess_game/chess/move.py`
- `chess_game/chess/coords.py`
- UCI conversion helpers in `chess_game/uci.py`

Useful concepts to retain:

- six-field FEN serialization and parsing;
- algebraic square conversion;
- UCI long-algebraic move strings;
- explicit promotion suffixes `q`, `r`, `b`, and `n`.

Do not translate:

- defaulting omitted FEN fields;
- interpreting any active-color token other than `w` as Black;
- substring-based castling-right acceptance;
- accepting structurally invalid playable positions;
- implicit queen promotion in core move execution.

Rust destination milestones:

- Task 2 for squares and move identity;
- Task 4 for strict FEN and notation;
- Task 17 for UCI protocol behavior.

### 6.3 Search

Primary modules include:

- `chess_game/chess/ai.py`
- `chess_game/chess/ai_search_types.py`
- `chess_game/chess/ai_search_helpers.py`
- `chess_game/chess/ai_search_eval.py`
- `chess_game/chess/ai_transposition.py`
- `chess_game/chess/ai_quiescence_search.py`
- `chess_game/chess/ai_quiescence_helpers.py`
- `chess_game/chess/ai_move_ordering.py`
- `chess_game/chess/ai_capture_ordering.py`
- `chess_game/chess/ai_board_utils.py`
- root-search and iterative-deepening helpers imported by `ai.py`.

Useful concepts to retain:

- reference minimax/negamax behavior;
- alpha-beta bounds;
- iterative deepening;
- aspiration-window recovery;
- quiescence search;
- transposition-table flags;
- deterministic mode;
- principal-move and diagnostic reporting.

Do not translate:

- cloned positions at every recursive child;
- string keys;
- an unbounded Python dictionary TT;
- skipped mate entries instead of normalized mate scores;
- heuristic root tie-break cascades;
- cancellation that is observed only between completed depths;
- shared mutable protocol control state.

Rust destination milestones:

- Tasks 13 through 16;
- Task 24 for performance gates.

### 6.4 Evaluation

Primary baseline modules:

- `chess_game/chess/evaluation.py`
- `chess_game/chess/eval_weights.py`
- `chess_game/chess/evaluation_tables.py`
- `chess_game/chess/pawn_structure_evaluation.py`
- `chess_game/chess/piece_coordination.py`
- `chess_game/chess/endgame_evaluation.py`

Useful concepts to retain initially:

- material values;
- piece-square tables;
- compact pawn-structure terms;
- mobility and king-safety terms that can be traced independently;
- explicit evaluation weights;
- evaluation tracing and versioning.

Do not translate wholesale:

- the full 463-parameter Python weight surface;
- overlapping aliases and duplicated concepts;
- transcript-specific scoring terms;
- automatic discovery or loading of weight files;
- narrowly tuned bonuses without independent suites.

Rust destination milestones:

- Task 12 for a compact baseline evaluator and trace;
- Task 22 for justified advanced classical terms;
- Task 21 for versioned tuning.

### 6.5 Opening book

Primary modules:

- `chess_game/chess/opening_book.py`
- `chess_game/chess/opening_development.py`
- `chess_game/chess/opening_move_ordering.py`
- `chess_game/chess/opening_guidance.py`
- bundled book data under `chess_game/chess/data/`.

Useful concepts to retain:

- optional book lookup;
- deterministic or explicitly seeded selection;
- separation between book policy and core legal-move validation.

Do not translate:

- implicit global or bundled book activation inside the search core;
- opening-specific heuristics that duplicate evaluator or ordering responsibilities;
- filesystem discovery in portable core crates.

Rust destination milestone:

- Task 19.

### 6.6 Self-play and tuning

Primary modules:

- `chess_game/self_play.py`
- `chess_game/texel/collect.py`
- `chess_game/texel/position_db.py`
- `chess_game/texel/annotated_position_db.py`
- `chess_game/texel/features.py`
- `chess_game/texel/loss.py`
- `chess_game/texel/spsa.py`
- `chess_game/texel/tune.py`
- `chess_game/texel/eval_tune.py`
- `chess_game/texel/eval_tune_sf.py`
- `chess_game/texel/validate.py`
- `chess_game/texel/weights_io.py`
- `chess_game/texel/stockfish_annotate.py`
- `chess_game/texel/online_learning.py`

Useful concepts to retain:

- explicit dataset collection;
- deterministic seeds;
- independent training and validation partitions;
- candidate-versus-baseline validation;
- Stockfish annotation as an offline tool;
- fail-loud file handling.

Do not translate:

- Python object serialization assumptions;
- automatic runtime learning;
- automatic promotion based only on loss improvement;
- loading a candidate because a path happens to exist;
- unversioned dataset or weight formats.

Rust destination milestones:

- Tasks 20 and 21.

### 6.7 UCI

Primary module:

- `chess_game/uci.py`

Useful concepts to retain:

- `uci`, `isready`, `ucinewgame`, `position`, `go`, `stop`, `debug`, and `quit` coverage;
- iterative `info` output;
- legal `bestmove` conversion;
- support for depth, movetime, clocks, increments, and infinite search.

Do not translate:

- module-level `_ctrl` search state;
- temporary reassignment of global `sys.stdout`;
- `sys.exit()` in reusable protocol/core code;
- stop handling that cannot interrupt recursive nodes promptly;
- implicit bundled-book use in the protocol adapter.

Rust destination milestones:

- Task 16 for cancellation and limits;
- Task 17 for the UCI executable.

### 6.8 CLI and TUI

Primary modules:

- `chess_game/main.py`
- `chess_game/tui.py`
- `chess_game/tui_game.py`
- related Textual screens and widgets.

These modules may be used to understand user workflows, but compatibility is explicitly out of scope for the initial Rust port. They must not influence core crate dependencies.

Rust destination:

- no initial compatibility milestone;
- future applications consume the safe Rust API, C ABI, or JNI layer.

### 6.9 Transcript-specific guidance

Modules identified by repository structure and naming include:

- `review_loop_guidance.py`
- `middlegame_practicality_guidance.py`
- `anti_drift_guidance.py`
- `tactical_transition_guidance.py`
- `conversion_guidance.py`
- `defensive_containment_guidance.py`
- `defensive_endgame_guidance.py`
- `defensive_priorities.py`
- `endgame_choice_guidance.py`
- `endgame_emergency_defense.py`
- `low_material_race_guidance.py`
- `low_material_coordination_guidance.py`
- `passer_race_guidance.py`
- `heavy_piece_endgame_guidance.py`
- `rook_endgame_guidance.py`
- `forced_win_guidance.py`
- `pawn_race_move_ordering.py`
- `opponent_plans.py`
- `structure_recognition.py`

Decision:

- these files are **excluded from direct translation**;
- an underlying chess concept may be reintroduced only through a general, traceable evaluation or ordering term;
- every reintroduced term requires objective tests, independent positions, and measurable benefit;
- no Rust module may encode preferences for a particular reviewed transcript or named move sequence.

Rust destination:

- none by default;
- Task 22 only after the baseline engine is correct and measured.

---

## 7. Retained concept-to-milestone matrix

| Python concept | Rust treatment | Milestone |
|---|---|---|
| Coordinate convention | Preserve `a8 = 0` mapping with a validated `Square` | Task 2 |
| Typed color/piece model | Rebuild as compact enums/value types without square ownership | Task 2 |
| Legal move coverage | Reimplement with attacks, pseudo-legal generation, and legality filtering | Tasks 5–7 |
| FEN | Strict parser and serializer | Task 4 |
| UCI move notation | Canonical move parse/format around one packed move | Tasks 2, 4, 17 |
| State transitions | In-place make/unmake with complete `Undo` | Task 8 |
| Repetition tracking | Incremental Zobrist plus canonical repetition semantics | Task 9 |
| Draw rules | Separate claimable and automatic outcomes | Task 10 |
| Perft | Known-count release oracle, not clone-based architecture | Task 11 |
| Alpha-beta | Reference search first, then negamax alpha-beta | Task 13 |
| Quiescence | Bounded tactical search with explicit policy | Task 14 |
| TT flags | Retain bounds; replace storage and score semantics | Task 15 |
| Iterative deepening | Retain with PV, aspiration recovery, and responsive limits | Task 16 |
| Diagnostics | Typed search/evaluation reports | Tasks 12, 16 |
| Classical evaluation | Start compact; add terms only with traces and suites | Tasks 12, 22 |
| Opening book | Optional injected adapter | Task 19 |
| Self-play | Versioned deterministic tooling | Task 20 |
| Tuning | Versioned datasets, weights, and promotion gates | Task 21 |
| UCI protocol | Standalone adapter over safe engine API | Task 17 |
| Mobile integration | C ABI and JNI over opaque handles | Task 18 |

---

## 8. Fixed defect and non-copy decision log

### D-001: Incorrect dead-position and insufficient-material shortcuts

**Evidence:** `chess_game/chess/board/game_state.py` treats all king-plus-two-knight positions with no bishops as dead when there are at most two knights. That includes positions such as king and two knights versus king, where mate cannot be forced but a legal mating sequence and checkmate position can exist. The same module conflates inability to force mate with impossibility of mate and applies broad two-minor-piece shortcuts.

**Rust decision:**

- do not expose the Python predicate as an oracle;
- distinguish automatic dead position from heuristic material classification;
- implement only proven automatic cases initially;
- add explicit regression positions for every accepted case;
- do not call a position dead merely because mate cannot be forced against perfect defense.

Destination: Task 10 and Task 23.

### D-002: Castling transit and destination evaluated against the wrong position

**Evidence:** `CastlingValidator._king_square_safe_during_castle()` asks whether source, intermediate, and destination squares are attacked while the king remains on its original square in the board representation. For sliding attacks, the original king can block a line that becomes open after it leaves the source square.

**Rust decision:**

- test the source square in the original position;
- test transit and destination with the king moved through the relevant transient state, or use an attack implementation whose occupancy argument is explicitly adjusted;
- add x-ray regression positions for both sides and both castling directions.

Destination: Tasks 5, 7, and 11.

### D-003: Clone-per-child recursion

**Evidence:** `tests/test_perft.py` clones the board for every child. The Python search architecture also relies on child-board cloning.

**Rust decision:**

- production perft and search use make/unmake;
- cloning remains allowed for test or reference comparisons only;
- benchmark make/unmake throughput and verify exact restoration.

Destination: Tasks 8, 11, 13, and 24.

### D-004: String position keys

**Evidence:** `chess_game/chess/position_utils.py` builds a variable-length string by appending piece tokens and metadata.

**Rust decision:**

- use incremental fixed-width Zobrist keys;
- retain an independently recomputed debug hash for assertions and tests;
- never allocate strings in the recursive search key path.

Destination: Task 9.

### D-005: Raw en-passant target included in every repetition key

**Evidence:** `position_key()` includes `board.en_passant_target` whenever the field is non-null, regardless of whether an en-passant capture is actually legal.

**Rust decision:**

- canonical repetition identity includes en-passant state only when it changes legal-move availability under the adopted rules contract;
- add regression pairs whose FEN en-passant field differs but whose legal positions are repetition-equivalent.

Destination: Task 9.

### D-006: Permissive FEN parsing

**Evidence:** `board_fen._fen_parse_fields()` supplies defaults when castling, en-passant, halfmove, or fullmove fields are omitted. `_fen_init_state()` maps any active-color token other than `w` to Black and derives castling rights using substring membership.

**Rust decision:**

- require exactly six fields for the strict public parser;
- reject invalid active-color, castling, en-passant, and numeric tokens;
- reject malformed rank digits, unknown pieces, overflow, impossible kings, and contradictory state according to the parser mode;
- keep any deliberately relaxed fixture builder private and explicitly named.

Destination: Task 4.

### D-007: Implicit queen promotion in core execution

**Evidence:** `MoveExecutor._handle_promotion()` replaces a missing promotion piece with `get_default_promotion_piece()`, effectively allowing core move execution to choose a queen.

**Rust decision:**

- every promotion move has an explicit promotion identity;
- core execution rejects a promotion move without a promotion kind;
- user-interface adapters may offer a queen default before constructing the canonical move, but the core never guesses.

Destination: Tasks 2, 4, 7, and 8.

### D-008: Multiple internal move representations

**Evidence:** the Python repository uses a `Move` model, a `LegalMove` model, and raw `(start, end, promotion)` tuples; `tests/test_perft.py` iterates tuple moves.

**Rust decision:**

- one canonical packed move type is used by move generation, search, TT, PV, perft, and adapters;
- external ABIs serialize fields rather than exposing the packed layout.

Destination: Task 2.

### D-009: Unbounded dictionary transposition table

**Evidence:** `SearchContext.transposition_table` is an optional `dict[str, TTEntry]`; no fixed memory budget or replacement policy is encoded in the type.

**Rust decision:**

- use a fixed-capacity clustered TT sized explicitly by configuration;
- use deterministic replacement rules;
- report occupancy/replacement diagnostics;
- never allow recursive search to grow memory without a configured bound.

Destination: Task 15.

### D-010: Missing TT mate-score normalization

**Evidence:** `ai_transposition.py` contains explicit TODO comments and avoids storing mate-like scores because ply-relative normalization is not implemented.

**Rust decision:**

- implement score-to-TT and score-from-TT normalization before mate entries are accepted;
- test storing at one ply and probing at another;
- use typed score helpers so centipawn and mate semantics cannot be confused casually.

Destination: Tasks 13 and 15.

### D-011: Root heuristic and tie-break interaction with alpha-beta results

**Evidence:** commit `f801bd9d696ad3b142edcd1073d71fc2ba625020` documents a cascade in which later tie-break comparisons used a previous tie-break winner rather than the alpha-beta best score, allowing progressively weaker moves to replace the true search winner.

**Rust decision:**

- alpha-beta score is authoritative;
- deterministic tie-breaking applies only to exactly equal scores unless a separately specified bounded policy is proven safe;
- ordering heuristics may change search order, not the mathematical result of a completed fixed-depth reference search;
- compare optimized and reference searches at shallow depths.

Destination: Tasks 13, 14, and 16.

### D-012: Automatic tuned-weight discovery

**Evidence:** the README states that the engine automatically loads `chess_game/chess/data/tuned_weights.json` when the file exists. Historical commits document a bad promoted weight file and subsequent removal.

**Rust decision:**

- defaults are compiled/versioned and deterministic;
- non-default weights require an explicit API/configuration argument;
- loaded weights include schema, evaluator version, checksum, and provenance;
- missing or invalid explicitly requested weights fail visibly;
- an unrelated file appearing on disk cannot change engine behavior.

Destination: Tasks 12 and 21.

### D-013: Global UCI control and output state

**Evidence:** `chess_game/uci.py` has module-level `_ctrl`, rewrites global `sys.stdout` inside `uci_loop()`, and uses `sys.exit()` from a command handler.

**Rust decision:**

- each UCI session owns its engine, cancellation token, input, and output;
- reusable protocol code returns control outcomes rather than exiting the process;
- no mutable process-global search state;
- cancellation is checked inside search nodes.

Destination: Tasks 16 and 17.

### D-014: Narrow transcript-driven evaluator and ordering patches

**Evidence:** the repository contains numerous modules named for review-loop guidance, anti-drift behavior, defensive containment, emergency defense, low-material races, forced-win guidance, and other narrow scenarios. Historical root-search fixes also document named move sequences.

**Rust decision:**

- none of these modules are translated directly;
- a general chess term may be introduced only after a traceable definition, independent test suite, and objective measurement;
- disliked self-play output alone is not a specification;
- search correctness must not depend on subjective tie-break cascades.

Destination: Task 22 only after earlier gates pass.

---

## 9. Task 0 completion state

### Completed source-grounded work

- baseline SHA identified and verified against `rust-engine`;
- Python modules inventoried by required category;
- retained concepts mapped to Rust milestones;
- excluded modules and architectural patterns recorded;
- every known non-copy defect in Task 0.3 converted into an explicit Rust decision;
- no Python engine internals modified.

### Runtime evidence still required

- fast Python suite at the baseline SHA;
- slow Python suite at the baseline SHA, or a documented practical deferral with reason;
- perft counts and timings at the baseline SHA;
- UCI smoke transcript at the baseline SHA.

### Gate decision

Task 0 is **not yet declared complete** because fresh runtime evidence has not been captured. Source analysis is complete, and Task 1 must not be marked complete until the remaining Task 0 evidence is recorded or the tracker is explicitly amended by the user.

---

## 10. Required runtime result block

Append or update this block after executing the capture script:

```text
BASELINE_SHA=f743013a84173b551eac5488c638cb48098ec6d0
PYTHON_VERSION=<value>
UV_VERSION=<value>
OS=<value>
CPU=<value>

FAST_TEST_COMMAND=uv run python -m pytest tests/ -q -m "not slow"
FAST_TEST_RESULT=<exit code and summary>
FAST_TEST_DURATION_SECONDS=<value>

SLOW_TEST_COMMAND=uv run python -m pytest tests/ -q -m "slow"
SLOW_TEST_RESULT=<exit code and summary, or explicit practical deferral>
SLOW_TEST_DURATION_SECONDS=<value>

PERFT_D1=20
PERFT_D2=400
PERFT_D3=8902
PERFT_D4=197281
PERFT_TIMINGS=<values>

UCI_SMOKE_RESULT=<pass/fail>
UCI_TRANSCRIPT_PATH=<path>

RUNTIME_EVIDENCE_COMMIT=<sha>
```
