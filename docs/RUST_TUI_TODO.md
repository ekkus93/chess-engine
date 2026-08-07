# Rust Chess TUI Implementation TODO

Companion specification: `docs/RUST_TUI_SPEC.md`

Status: implementation plan; unchecked items are not complete.

The objective is a native Rust `chess-tui` application based behaviorally on the historical Python Textual TUI while using the authoritative Rust core/search implementation. This work is a frontend/integration milestone. It must not alter engine strength, evaluation weights, search policy, tuning state, or candidate-promotion disposition.

## Phase 0 — Baseline and architecture confirmation

- [ ] Record the starting `master` SHA before implementation.
- [ ] Run the existing fast Rust validation and record the result.
- [ ] Confirm `crates/chess-core`, `crates/chess-search`, `crates/chess-book`, and `crates/chess-uci` public APIs needed by the TUI.
- [ ] Map historical Python behaviors from `chess_game/tui.py` and `chess_game/tui_game.py` to Rust APIs.
- [ ] Explicitly classify Python-only behavior that will not be ported, especially online self-learning/automatic weight mutation.
- [ ] Verify whether UCI worker/search orchestration contains presentation-neutral code worth extracting.
- [ ] Do not make `chess-search` depend on UCI/TUI/filesystem code.
- [ ] Do not use a `chess-uci` subprocess unless a documented blocker makes in-process reuse impossible.

### Phase 0 acceptance

- [ ] A short implementation note identifies the exact state/search APIs to be reused.
- [ ] Any required shared abstraction has a clear owner and does not invert existing dependency direction.
- [ ] No engine algorithm change is included in the TUI plan.

## Phase 1 — Create `chess-tui` crate

- [ ] Add `crates/chess-tui/Cargo.toml`.
- [ ] Add `crates/chess-tui` to workspace members.
- [ ] Add Ratatui and Crossterm dependencies compatible with the repository MSRV.
- [ ] Depend on `chess-core`.
- [ ] Depend on `chess-search`.
- [ ] Add `chess-book` only if explicit book support is implemented in this milestone.
- [ ] Apply workspace lint configuration.
- [ ] Add `#![forbid(unsafe_code)]` unless a documented terminal-library requirement proves otherwise.
- [ ] Add a minimal `main.rs` that initializes and safely restores the terminal.
- [ ] Ensure terminal cleanup is RAII/scoped rather than dependent only on the happy path.

### Phase 1 tests/gates

- [ ] `cargo fmt --all -- --check`
- [ ] `cargo check -p chess-tui`
- [ ] `cargo clippy -p chess-tui --all-targets -- -D warnings`
- [ ] Launch/quit smoke test restores the shell terminal correctly.

## Phase 2 — Presentation-neutral application/session model

Create a controller/state layer that can be tested without a live terminal.

- [ ] Define `AppState`/equivalent top-level state.
- [ ] Define screen/mode state: Main Menu, Game, confirmation modal, Game Over/error state as needed.
- [ ] Define `GameConfig` with Human vs Engine and Self-play variants or an equivalently type-safe representation.
- [ ] Store the authoritative `chess_core::Game` in the game session.
- [ ] Store move history as structured Rust moves rather than authoritative free-form strings.
- [ ] Track game generation/session ID.
- [ ] Track active search request generation.
- [ ] Track thinking/search status explicitly.
- [ ] Track self-play auto/pause state explicitly.
- [ ] Track visible nonfatal user error/status messages explicitly.
- [ ] Make illegal state transitions reject visibly in debug/tests rather than silently doing nothing when that would hide a bug.

### Phase 2 tests

- [ ] Default menu configuration matches the intended defaults.
- [ ] Starting Human/White creates a fresh starting game with human input enabled.
- [ ] Starting Human/Black creates a fresh starting game requiring an engine move first.
- [ ] Starting Self-play schedules White engine search.
- [ ] New game increments/replaces the generation so old search results become stale.
- [ ] Game-over state disables future move/search scheduling.

## Phase 3 — Board and game rendering model

- [ ] Implement a pure board-render/model helper independent of terminal side effects.
- [ ] Render files and ranks.
- [ ] Render White pieces uppercase and Black pieces lowercase.
- [ ] Render knights as `N`/`n`.
- [ ] Support White-at-bottom orientation.
- [ ] Support Black-at-bottom orientation.
- [ ] Human-vs-engine orientation follows human color.
- [ ] Self-play defaults to White at bottom.
- [ ] Add turn/status text.
- [ ] Add check indication using authoritative core state.
- [ ] Add numbered move-history formatting.
- [ ] Add terminal-result formatting.
- [ ] Do not make correctness depend on terminal color support.

### Phase 3 tests

- [ ] Starting position White orientation snapshot/structural test.
- [ ] Starting position Black orientation snapshot/structural test.
- [ ] Piece-case test.
- [ ] Rank/file-label test.
- [ ] Move-list numbering test for odd and even ply counts.
- [ ] Narrow-terminal layout decision does not panic.

## Phase 4 — Ratatui screens and responsive layout

- [ ] Implement main-menu screen.
- [ ] Implement Human vs Engine mode selection.
- [ ] Implement human color selection.
- [ ] Implement initial engine depth selection.
- [ ] Implement Self-play mode selection.
- [ ] Implement separate White/Black depth selection.
- [ ] Implement game screen with board pane.
- [ ] Implement move-history pane.
- [ ] Implement status/input area.
- [ ] Implement engine-information pane.
- [ ] Implement thinking indicator.
- [ ] Implement game-over panel/modal.
- [ ] Implement confirmation UI for resignation and abandoning an active game.
- [ ] Handle terminal resize events.
- [ ] For unusably small terminals, render a minimum-size message instead of panicking or corrupting layout.

### Phase 4 tests

- [ ] Render tests for menu state.
- [ ] Render tests for human game state.
- [ ] Render tests for self-play state.
- [ ] Render tests for thinking state.
- [ ] Render tests for game-over/error state.
- [ ] Small-dimension rendering smoke tests.

## Phase 5 — Human move input

- [ ] Add focused move-entry editing.
- [ ] Accept UCI coordinate notation such as `e2e4`.
- [ ] Accept promotion suffixes such as `e7e8q`.
- [ ] Parse through Rust-core move types/APIs rather than a second TUI chess parser where possible.
- [ ] Validate moves against the authoritative current game.
- [ ] Apply a legal move transactionally.
- [ ] Append move history only after successful application.
- [ ] Reject malformed input visibly.
- [ ] Reject illegal moves visibly.
- [ ] Preserve game state exactly after rejected input.
- [ ] Detect terminal state after a human move before scheduling engine work.
- [ ] Ensure shortcuts do not trigger accidentally while editing move text.

### Phase 5 tests

- [ ] `e2e4` succeeds from the starting position.
- [ ] malformed move is rejected without mutation.
- [ ] well-formed illegal move is rejected without mutation.
- [ ] promotion move preserves explicit promotion identity.
- [ ] move submission when it is not the human's turn is rejected/disabled.
- [ ] terminal human move does not schedule another engine search.

## Phase 6 — Engine worker and cancellation lifecycle

- [ ] Implement a dedicated search worker or equivalent bounded worker abstraction.
- [ ] Keep search off the terminal event thread.
- [ ] Guarantee at most one TUI-owned active search per game session.
- [ ] Use existing `SearchLimits` for fixed-depth search.
- [ ] Use existing transposition/search policy APIs rather than TUI-local search behavior.
- [ ] Pass safely owned/snapshotted state into the worker.
- [ ] Assign every search a request/generation ID.
- [ ] Return typed progress/completion/error events to the UI/controller.
- [ ] Reject a completion whose generation does not match the active game/request.
- [ ] Wire existing cancellation/stop support for menu/new-game/quit/pause transitions where appropriate.
- [ ] Resolve worker ownership cleanly during application shutdown.
- [ ] Catch/report worker failures at the application boundary as appropriate; do not leave `thinking=true` forever.

### Explicit forbidden fallbacks

- [ ] Verify there is no random-legal-move fallback after search failure.
- [ ] Verify there is no first-legal-move fallback after search failure.
- [ ] Verify there is no silent depth reduction/retry.
- [ ] Verify there is no silent search-policy replacement.
- [ ] Verify there is no Python-engine fallback.
- [ ] Verify cancellation cannot later apply an obsolete best move to a new game.

### Phase 6 tests

- [ ] Search runs without blocking synthetic UI event processing.
- [ ] Completed engine move is legal and applied exactly once.
- [ ] Stale generation completion is ignored.
- [ ] Search error clears thinking state and becomes visible.
- [ ] Cancellation does not mutate the game after abandonment.
- [ ] Quit/new-game while searching does not deadlock.

## Phase 7 — Search progress and engine panel

Use existing observer/progress APIs rather than instrumenting the search algorithm specifically for the TUI unless a small presentation-neutral API improvement is required.

- [ ] Display completed/current depth where available.
- [ ] Display score in centipawns.
- [ ] Format mate scores distinctly.
- [ ] Display node count.
- [ ] Display NPS when calculable from authoritative progress/time data.
- [ ] Display elapsed time.
- [ ] Display principal variation.
- [ ] Display hash fullness only if available cleanly.
- [ ] Represent unavailable fields as unavailable/blank, never invented zero values that imply real measurements.
- [ ] Rate-limit redraw/progress delivery if necessary so search progress cannot flood the terminal event loop.

### Phase 7 tests

- [ ] Progress event updates only presentation state.
- [ ] Progress from stale request is ignored.
- [ ] Mate score formatting test.
- [ ] Missing optional metrics do not panic and are not fabricated.

## Phase 8 — Human vs Engine complete workflow

- [ ] Human White game starts awaiting input.
- [ ] Valid human move automatically starts engine search.
- [ ] Engine completion applies the engine move and returns control to the human.
- [ ] Human Black game starts with an engine search.
- [ ] Check status is displayed.
- [ ] Checkmate/stalemate/draw result stops play.
- [ ] Add resignation shortcut/action.
- [ ] Add resignation confirmation.
- [ ] Correctly declare the opponent winner on resignation.
- [ ] Add new-game/menu/quit confirmation when abandoning an active game.

### Phase 8 integration tests

- [ ] Human White: `e2e4` -> engine legal response -> human to move.
- [ ] Human Black: engine legal first move -> human to move.
- [ ] Resignation as White declares Black winner.
- [ ] Resignation as Black declares White winner.
- [ ] Terminal game cannot accept another move.

## Phase 9 — Self-play workflow

- [ ] Start White engine search automatically.
- [ ] Apply White result and schedule Black automatically.
- [ ] Continue until paused or terminal.
- [ ] Space/explicit action pauses auto-play.
- [ ] Resume continues from the current authoritative game.
- [ ] Step while paused schedules exactly one ply.
- [ ] Step remains disabled while a search is active.
- [ ] Game-over stops all auto scheduling.
- [ ] Do not port Python online-learning/background weight mutation.

### Phase 9 tests

- [ ] Self-play alternates sides legally.
- [ ] Pause prevents scheduling the next ply.
- [ ] Step applies exactly one ply and remains paused.
- [ ] Resume restarts automatic scheduling.
- [ ] Terminal state schedules no additional search.
- [ ] No tuning/evaluation files are written by self-play TUI mode.

## Phase 10 — Save game

- [ ] Define a deterministic text serialization function separate from filesystem I/O.
- [ ] Include mode/configuration.
- [ ] Include ordered UCI moves.
- [ ] Include result/reason.
- [ ] Include date/time only through an injectable/testable boundary where needed.
- [ ] Implement explicit save path entry/action.
- [ ] Do not claim PGN unless valid PGN is implemented.
- [ ] Surface path/permission/write errors in the UI.
- [ ] Mark Saved only after the complete write succeeds.
- [ ] Avoid implicit writes or auto-save unless separately specified.

### Phase 10 tests

- [ ] Serialization golden test.
- [ ] Successful write test using temporary directory.
- [ ] Failed write remains visible and does not set Saved state.
- [ ] Saved move order/result matches authoritative session state.

## Phase 11 — Developer workflow and documentation

- [ ] Add `bash scripts/dev.sh tui`.
- [ ] Add `tui` to `scripts/dev.sh help`.
- [ ] Document direct `cargo run -p chess-tui` usage.
- [ ] Update README description to mention native Rust TUI.
- [ ] Add `crates/chess-tui` to README workspace list.
- [ ] Add TUI launch command to README common commands.
- [ ] Document controls and modes.
- [ ] Document that the historical Python TUI is reference-only and is not a runtime dependency.
- [ ] Document architecture relationship among `chess-tui`, `chess-uci`, `chess-search`, and `chess-core`.

## Phase 12 — Validation and regression gates

Run on the exact intended final source SHA.

- [ ] `cargo fmt --all -- --check`
- [ ] workspace `cargo check` through the supported developer workflow.
- [ ] workspace strict Clippy through the supported developer workflow.
- [ ] workspace Rust tests.
- [ ] `cargo test -p chess-tui`.
- [ ] release build of `chess-tui`.
- [ ] existing core perft gate remains unchanged and green.
- [ ] existing differential/core correctness gates remain unchanged and green.
- [ ] existing UCI tests remain green.
- [ ] relevant robustness gates remain green.
- [ ] no Python production/runtime dependency was added.
- [ ] no generated tuning/weight candidate became active.
- [ ] no default evaluation/search policy changed.
- [ ] manually launch the release TUI in a real terminal.
- [ ] manually play at least several legal plies as White.
- [ ] manually play at least several legal plies as Black.
- [ ] manually exercise self-play pause/resume/step.
- [ ] manually exercise resign confirmation.
- [ ] manually exercise menu/quit during engine thinking.
- [ ] manually exercise terminal resize.
- [ ] manually exercise a save success and a save failure.
- [ ] confirm terminal state is restored after every tested exit path.

## Phase 13 — Final evidence and closure

- [ ] Record final implementation SHA.
- [ ] Record exact validation commands and results.
- [ ] Record relevant CI run/job URLs or IDs.
- [ ] Confirm CI ran against the exact final SHA rather than an earlier implementation commit.
- [ ] Confirm the final diff contains only intended TUI/integration/documentation changes.
- [ ] Confirm no silent fallback behavior was introduced.
- [ ] Confirm no search/evaluation/tuning/promotion behavior changed.
- [ ] Mark this TODO complete only after all required gates are green.

## Definition of done

Do not close this TODO merely because the TUI renders. Completion requires a usable Human vs Engine workflow, Self-play controls, safe asynchronous engine integration, stale-result protection, visible error handling, tested save behavior, terminal cleanup, documentation, and exact-SHA validation with the existing correctness-first Rust gates still passing.