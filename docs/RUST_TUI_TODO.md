# Rust Chess TUI Implementation TODO

Companion specification: `docs/RUST_TUI_SPEC.md`

Status: implementation complete through Phase 11; permanent regression gates and manual real-terminal acceptance remain open.

The objective is a native Rust `chess-tui` application based behaviorally on the historical Python Textual TUI while using the authoritative Rust core/search implementation. This work is a frontend/integration milestone. It must not alter engine strength, evaluation weights, search policy, tuning state, or candidate-promotion disposition.

## Phase 0 — Baseline and architecture confirmation

- [x] Record the starting `master` SHA before implementation.
- [ ] Run the existing fast Rust validation and record the result.
- [x] Confirm `crates/chess-core`, `crates/chess-search`, `crates/chess-book`, and `crates/chess-uci` public APIs needed by the TUI.
- [x] Map historical Python behaviors from `chess_game/tui.py` and `chess_game/tui_game.py` to Rust APIs.
- [x] Explicitly classify Python-only behavior that will not be ported, especially online self-learning/automatic weight mutation.
- [x] Verify whether UCI worker/search orchestration contains presentation-neutral code worth extracting.
- [x] Do not make `chess-search` depend on UCI/TUI/filesystem code.
- [x] Do not use a `chess-uci` subprocess unless a documented blocker makes in-process reuse impossible.

### Phase 0 acceptance

- [x] A short implementation note identifies the exact state/search APIs to be reused.
- [x] Any required shared abstraction has a clear owner and does not invert existing dependency direction.
- [x] No engine algorithm change is included in the TUI plan.

## Phase 1 — Create `chess-tui` crate

- [x] Add `crates/chess-tui/Cargo.toml`.
- [x] Add `crates/chess-tui` to workspace members.
- [x] Add Ratatui and Crossterm dependencies compatible with the repository MSRV.
- [x] Depend on `chess-core`.
- [x] Depend on `chess-search`.
- [x] Add `chess-book` only if explicit book support is implemented in this milestone.
- [x] Apply workspace lint configuration.
- [x] Add `#![forbid(unsafe_code)]` unless a documented terminal-library requirement proves otherwise.
- [x] Add a minimal `main.rs` that initializes and safely restores the terminal.
- [x] Ensure terminal cleanup is RAII/scoped rather than dependent only on the happy path.

### Phase 1 tests/gates

- [x] `cargo fmt --all -- --check`
- [x] `cargo check -p chess-tui`
- [x] `cargo clippy -p chess-tui --all-targets -- -D warnings`
- [x] Launch/quit smoke test restores the shell terminal correctly.

## Phase 2 — Presentation-neutral application/session model

Create a controller/state layer that can be tested without a live terminal.

- [x] Define `AppState`/equivalent top-level state.
- [x] Define screen/mode state: Main Menu, Game, confirmation modal, Game Over/error state as needed.
- [x] Define `GameConfig` with Human vs Engine and Self-play variants or an equivalently type-safe representation.
- [x] Store the authoritative `chess_core::Game` in the game session.
- [x] Store move history as structured Rust moves rather than authoritative free-form strings.
- [x] Track game generation/session ID.
- [x] Track active search request generation.
- [x] Track thinking/search status explicitly.
- [x] Track self-play auto/pause state explicitly.
- [x] Track visible nonfatal user error/status messages explicitly.
- [x] Make illegal state transitions reject visibly in debug/tests rather than silently doing nothing when that would hide a bug.

### Phase 2 tests

- [x] Default menu configuration matches the intended defaults.
- [x] Starting Human/White creates a fresh starting game with human input enabled.
- [x] Starting Human/Black creates a fresh starting game requiring an engine move first.
- [x] Starting Self-play schedules White engine search.
- [x] New game increments/replaces the generation so old search results become stale.
- [x] Game-over state disables future move/search scheduling.

## Phase 3 — Board and game rendering model

- [x] Implement a pure board-render/model helper independent of terminal side effects.
- [x] Render files and ranks.
- [x] Render White pieces uppercase and Black pieces lowercase.
- [x] Render knights as `N`/`n`.
- [x] Support White-at-bottom orientation.
- [x] Support Black-at-bottom orientation.
- [x] Human-vs-engine orientation follows human color.
- [x] Self-play defaults to White at bottom.
- [x] Add turn/status text.
- [x] Add check indication using authoritative core state.
- [x] Add numbered move-history formatting.
- [x] Add terminal-result formatting.
- [x] Do not make correctness depend on terminal color support.

### Phase 3 tests

- [x] Starting position White orientation snapshot/structural test.
- [x] Starting position Black orientation snapshot/structural test.
- [x] Piece-case test.
- [x] Rank/file-label test.
- [x] Move-list numbering test for odd and even ply counts.
- [x] Narrow-terminal layout decision does not panic.

## Phase 4 — Ratatui screens and responsive layout

- [x] Implement main-menu screen.
- [x] Implement Human vs Engine mode selection.
- [x] Implement human color selection.
- [x] Implement initial engine depth selection.
- [x] Implement Self-play mode selection.
- [x] Implement separate White/Black depth selection.
- [x] Implement game screen with board pane.
- [x] Implement move-history pane.
- [x] Implement status/input area.
- [x] Implement engine-information pane.
- [x] Implement thinking indicator.
- [x] Implement game-over panel/modal.
- [x] Implement confirmation UI for resignation and abandoning an active game.
- [x] Handle terminal resize events.
- [x] For unusably small terminals, render a minimum-size message instead of panicking or corrupting layout.

### Phase 4 tests

- [x] Render tests for menu state.
- [x] Render tests for human game state.
- [x] Render tests for self-play state.
- [x] Render tests for thinking state.
- [x] Render tests for game-over/error state.
- [x] Small-dimension rendering smoke tests.

## Phase 5 — Human move input

- [x] Add focused move-entry editing.
- [x] Accept UCI coordinate notation such as `e2e4`.
- [x] Accept promotion suffixes such as `e7e8q`.
- [x] Parse through Rust-core move types/APIs rather than a second TUI chess parser where possible.
- [x] Validate moves against the authoritative current game.
- [x] Apply a legal move transactionally.
- [x] Append move history only after successful application.
- [x] Reject malformed input visibly.
- [x] Reject illegal moves visibly.
- [x] Preserve game state exactly after rejected input.
- [x] Detect terminal state after a human move before scheduling engine work.
- [x] Ensure shortcuts do not trigger accidentally while editing move text.

### Phase 5 tests

- [x] `e2e4` succeeds from the starting position.
- [x] malformed move is rejected without mutation.
- [x] well-formed illegal move is rejected without mutation.
- [x] promotion move preserves explicit promotion identity.
- [x] move submission when it is not the human's turn is rejected/disabled.
- [x] terminal human move does not schedule another engine search.

## Phase 6 — Engine worker and cancellation lifecycle

- [x] Implement a dedicated search worker or equivalent bounded worker abstraction.
- [x] Keep search off the terminal event thread.
- [x] Guarantee at most one TUI-owned active search per game session.
- [x] Use existing `SearchLimits` for fixed-depth search.
- [x] Use existing transposition/search policy APIs rather than TUI-local search behavior.
- [x] Pass safely owned/snapshotted state into the worker.
- [x] Assign every search a request/generation ID.
- [x] Return typed progress/completion/error events to the UI/controller.
- [x] Reject a completion whose generation does not match the active game/request.
- [x] Wire existing cancellation/stop support for menu/new-game/quit/pause transitions where appropriate.
- [x] Resolve worker ownership cleanly during application shutdown.
- [x] Catch/report worker failures at the application boundary as appropriate; do not leave `thinking=true` forever.

### Explicit forbidden fallbacks

- [x] Verify there is no random-legal-move fallback after search failure.
- [x] Verify there is no first-legal-move fallback after search failure.
- [x] Verify there is no silent depth reduction/retry.
- [x] Verify there is no silent search-policy replacement.
- [x] Verify there is no Python-engine fallback.
- [x] Verify cancellation cannot later apply an obsolete best move to a new game.

### Phase 6 tests

- [x] Search runs without blocking synthetic UI event processing.
- [x] Completed engine move is legal and applied exactly once.
- [x] Stale generation completion is ignored.
- [x] Search error clears thinking state and becomes visible.
- [x] Cancellation does not mutate the game after abandonment.
- [x] Quit/new-game while searching does not deadlock.

## Phase 7 — Search progress and engine panel

Use existing observer/progress APIs rather than instrumenting the search algorithm specifically for the TUI unless a small presentation-neutral API improvement is required.

- [x] Display completed/current depth where available.
- [x] Display score in centipawns.
- [x] Format mate scores distinctly.
- [x] Display node count.
- [x] Display NPS when calculable from authoritative progress/time data.
- [x] Display elapsed time.
- [x] Display principal variation.
- [x] Display hash fullness only if available cleanly.
- [x] Represent unavailable fields as unavailable/blank, never invented zero values that imply real measurements.
- [x] Rate-limit redraw/progress delivery if necessary so search progress cannot flood the terminal event loop.

### Phase 7 tests

- [x] Progress event updates only presentation state.
- [x] Progress from stale request is ignored.
- [x] Mate score formatting test.
- [x] Missing optional metrics do not panic and are not fabricated.

## Phase 8 — Human vs Engine complete workflow

- [x] Human White game starts awaiting input.
- [x] Valid human move automatically starts engine search.
- [x] Engine completion applies the engine move and returns control to the human.
- [x] Human Black game starts with an engine search.
- [x] Check status is displayed.
- [x] Checkmate/stalemate/draw result stops play.
- [x] Add resignation shortcut/action.
- [x] Add resignation confirmation.
- [x] Correctly declare the opponent winner on resignation.
- [x] Add new-game/menu/quit confirmation when abandoning an active game.

### Phase 8 integration tests

- [x] Human White: `e2e4` -> engine legal response -> human to move.
- [x] Human Black: engine legal first move -> human to move.
- [x] Resignation as White declares Black winner.
- [x] Resignation as Black declares White winner.
- [x] Terminal game cannot accept another move.

## Phase 9 — Self-play workflow

- [x] Start White engine search automatically.
- [x] Apply White result and schedule Black automatically.
- [x] Continue until paused or terminal.
- [x] Space/explicit action pauses auto-play.
- [x] Resume continues from the current authoritative game.
- [x] Step while paused schedules exactly one ply.
- [x] Step remains disabled while a search is active.
- [x] Game-over stops all auto scheduling.
- [x] Do not port Python online-learning/background weight mutation.

### Phase 9 tests

- [x] Self-play alternates sides legally.
- [x] Pause prevents scheduling the next ply.
- [x] Step applies exactly one ply and remains paused.
- [x] Resume restarts automatic scheduling.
- [x] Terminal state schedules no additional search.
- [x] No tuning/evaluation files are written by self-play TUI mode.

## Phase 10 — Save game

- [x] Define a deterministic text serialization function separate from filesystem I/O.
- [x] Include mode/configuration.
- [x] Include ordered UCI moves.
- [x] Include result/reason.
- [x] Include date/time only through an injectable/testable boundary where needed.
- [x] Implement explicit save path entry/action.
- [x] Do not claim PGN unless valid PGN is implemented.
- [x] Surface path/permission/write errors in the UI.
- [x] Mark Saved only after the complete write succeeds.
- [x] Avoid implicit writes or auto-save unless separately specified.

### Phase 10 tests

- [x] Serialization golden test.
- [x] Successful write test using temporary directory.
- [x] Failed write remains visible and does not set Saved state.
- [x] Saved move order/result matches authoritative session state.

## Phase 11 — Developer workflow and documentation

- [x] Add `bash scripts/dev.sh tui`.
- [x] Add `tui` to `scripts/dev.sh help`.
- [x] Document direct `cargo run -p chess-tui` usage.
- [x] Update README description to mention native Rust TUI.
- [x] Add `crates/chess-tui` to README workspace list.
- [x] Add TUI launch command to README common commands.
- [x] Document controls and modes.
- [x] Document that the historical Python TUI is reference-only and is not a runtime dependency.
- [x] Document architecture relationship among `chess-tui`, `chess-uci`, `chess-search`, and `chess-core`.

## Focused Ralph evidence

- Focused run `31227985266` / job `93025997708`: locked metadata, TUI check, strict Clippy, TUI tests, release build, PTY launch/quit cleanup smoke, and Rust 1.75 MSRV check all succeeded.
- Earlier focused runs `31227684896`, `31227799491`, `31227882334`, and `31227931565` established workflow, integration, responsive-layout, terminal-lifecycle, and state-machine regressions before source freeze.
- The TUI rejects `SearchResult` emergency cancellation fallback moves and accepts only an exact `completed().best_move()` from a completed iterative-deepening depth.

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