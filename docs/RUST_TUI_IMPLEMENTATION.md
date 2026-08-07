# Rust TUI Implementation Notes

Status: implementation in progress under `docs/RUST_TUI_TODO.md`.

## Baseline

- Starting authoritative Rust source SHA before the TUI documentation/implementation work: `925f2e33271cd7657757f4428544a698268b6a7d`.
- The previously prepared TUI specification and TODO were fast-forwarded onto `master` through `e22a23f320198b67d73079fd80b60e29b9b36969` before implementation began.
- The pre-TUI source baseline had successful permanent master-validation reporting, including run `31217162019` for SHA `925f2e33271cd7657757f4428544a698268b6a7d`.

## Reused authoritative APIs

The TUI is an outward presentation adapter. It uses these existing APIs directly:

- `chess_core::Game` for the current position, played-move history, repetition history, legal move generation, move application, and rule-level game status;
- `chess_core::UciMove` to parse human coordinate input and match it against generated legal `Move` values;
- `chess_core::Position`/`Piece`/`Square` only for presentation reads such as board cells, side to move, and check indication;
- `chess_search::SearchLimits` and `SearchStopFlag` for fixed-depth limits and explicit cancellation;
- `chess_search::iterative_deepening_search_with_limits_and_transposition_table_and_observer` for the production iterative-deepening implementation and presentation-neutral progress observer;
- `chess_search::TranspositionTable` with the existing default table size and production search policy/weights selected by the existing public search entry point.

No dependency direction is inverted: `chess-tui` depends on `chess-core` and `chess-search`; neither engine crate depends on terminal, filesystem, UCI, or TUI code.

## UCI worker comparison

`crates/chess-uci/src/worker.rs` was used as an orchestration reference because it already demonstrates the intended ownership model: clone one game snapshot, create a request-local stop flag and transposition table, run search off the adapter thread, and join/discard owned work explicitly.

The UCI worker itself is not reused as a dependency because it owns UCI-specific request/time/output behavior. `chess-tui` therefore implements the smaller adapter-local worker it needs instead of making the TUI depend on the UCI protocol adapter or moving UI concerns into `chess-search`.

## Historical Python mapping and exclusions

The historical `chess_game/tui.py` and `chess_game/tui_game.py` remain reference-only for the menu/game interaction model: Human vs Engine, Self-play, board display, move entry, move history, thinking state, resign confirmation, pause/resume/step, and explicit save actions.

The Rust TUI deliberately does **not** port:

- Python engine execution or Python fallback;
- tuned-weight filesystem discovery;
- Python opening-book discovery/randomization;
- online self-learning, post-game automatic weight mutation, or background tuning;
- Textual widget/CSS implementation details.

The first Rust TUI milestone also does not enable `chess-book`; search therefore uses the existing no-implicit-book behavior rather than discovering a book from the filesystem.

## Search failure and cancellation policy

The TUI has an additional adapter-level fail-closed rule around cancellation. `chess-search::SearchResult::best_move()` can expose the engine's deterministic emergency first-legal result when cancellation occurs before depth one. That behavior is valid for the generic search layer but is explicitly forbidden as a TUI fallback by `docs/RUST_TUI_TODO.md`.

Accordingly, the TUI worker never uses `SearchResult::best_move()`. It accepts a playable engine move only from `result.completed().best_move()`, meaning at least one exact iterative-deepening depth completed. If the generic search result contains only `result.fallback()`, the TUI reports that the fallback was rejected and applies no move. Discard/cancel transitions suppress final move delivery entirely.

There is no random-legal fallback, first-legal TUI fallback, silent depth reduction, silent retry at another policy, search-policy replacement, or Python fallback.

## Session ownership and stale-result protection

Each game receives a monotonically increasing generation ID and each search receives a request ID. Completion/progress/error events carry both values. The controller accepts events only when the event ticket exactly matches the active search ticket for the still-current game.

Search receives a cloned `Game` and a detached `SearchHistory`; the worker never mutates UI-owned game state. The controller re-validates an exact completed engine move against the current authoritative `Game` immediately before applying it.

## Save format

The TUI save format is deliberately not PGN. `serialize_game` is deterministic and independent of filesystem I/O. The caller may inject a timestamp string; the interactive boundary supplies a current Unix-seconds label. The format records mode/configuration, ordered UCI moves, and current/final result. `write_game` reports filesystem errors and the controller marks a path saved only after the write succeeds.

## Validation

Focused and permanent validation evidence is recorded here only after it exists on the exact relevant SHA. The temporary `.github/workflows/rust-tui-ralph.yml` workflow is used solely because the current execution environment cannot fetch crates locally; it generates the committed lockfile/formatting on a GitHub runner and runs focused TUI gates. It must be removed before final closure.
