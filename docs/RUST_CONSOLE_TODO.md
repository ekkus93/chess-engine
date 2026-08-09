# Rust Chess Console Application Implementation TODO

Companion specification: `docs/RUST_CONSOLE_SPEC.md`

Status: proposed / not started

Planning baseline before these documents: `0964371d93b5a54c340769acf2909b86b47da7a6`

Specification commit: `a6880532a43d6cc1f85ae33049b5257b1750aa6f`

## Ralph-loop operating rules

This checklist is intended to be implemented directly on `master` under the repository workflow.

- Work directly on `master`; do not create a branch or PR unless the user explicitly changes that instruction.
- Use `bash scripts/dev.sh ...` as the supported local development/validation entry point.
- Do not mark a checkbox complete merely because code compiles.
- Record exact source SHA, commands, CI run URL/ID, job ID, and relevant artifact/evidence identifiers for major gates.
- Keep the Rust workspace authoritative; Python is historical/reference-only.
- Do not change engine strength, evaluation weights, tuning activation, search policy, opening-book policy, or candidate-promotion disposition as part of this frontend work.
- Preserve the completed TUI behavior while extracting shared code.
- Add focused regression tests for every behavior moved or changed.
- Do not weaken/delete tests to obtain green validation.
- Never add first-party lint suppression to bypass warnings.
- Treat the anti-fallback requirements in this TODO as correctness requirements, not optional cleanup.

## Phase 0 — Establish exact baseline and implementation map

- [ ] Record the exact starting `master` SHA at the beginning of implementation.
- [ ] Confirm the planning baseline/history documented above and note any intervening commits that landed after this TODO was authored.
- [ ] Run `bash scripts/dev.sh fast` on the exact implementation starting SHA.
- [ ] Record whether the existing workspace is green before code changes.
- [ ] Run the existing focused TUI tests through supported `scripts/dev.sh` commands.
- [ ] Run the real TUI PTY acceptance suite through its supported developer command.
- [ ] Record the baseline TUI test/PTY results before extraction.
- [ ] Re-read `AGENTS.md`, `CLAUDE.md`, `docs/RUST_WORKSPACE_ARCHITECTURE.md`, `docs/RUST_DEVELOPER_WORKFLOWS.md`, and `docs/RUST_TUI_TODO.md` before editing architecture/workflow files.
- [ ] Map the current `chess-tui` code into two categories: shared application behavior vs. TUI-only presentation behavior.
- [ ] Confirm the exact current public APIs from `chess-core` and `chess-search` used by the TUI controller/worker.
- [ ] Confirm that `chess-console` can remain in-process and does not require a UCI subprocess.
- [ ] Confirm no opening-book behavior is implicitly added by this milestone.

### Phase 0 extraction inventory

Record the current owner and intended owner for at least:

- [ ] `GameConfig` -> `chess-app`.
- [ ] `GameOutcome` -> `chess-app`.
- [ ] shared `GameSession` fields -> `chess-app`.
- [ ] game/search generation and pending-search scheduling -> `chess-app`.
- [ ] `SearchTicket` -> `chess-app`.
- [ ] `SearchRequest` -> `chess-app`.
- [ ] `SearchMetrics` -> `chess-app`.
- [ ] `EngineEvent` -> `chess-app`.
- [ ] `SearchWorker`/`SearchWorkerError` -> `chess-app`.
- [ ] pure board/history/outcome/search text formatting -> `chess-app::text` or equivalent.
- [ ] atomic save primitive / neutral save record -> `chess-app` where reuse is real.
- [ ] `MenuState` -> remain `chess-tui`.
- [ ] `AppScreen` -> remain `chess-tui`.
- [ ] `Overlay` / confirmation UI state -> remain `chess-tui`.
- [ ] move-input editing buffer -> remain `chess-tui`.
- [ ] TUI save-path/overwrite UI state -> remain `chess-tui`.
- [ ] Ratatui layout decisions/constants/widgets/styles -> remain `chess-tui`.
- [ ] terminal raw/alternate-screen lifecycle -> remain `chess-tui`.

### Phase 0 acceptance

- [ ] Baseline source SHA is recorded.
- [ ] Baseline `fast` result is recorded.
- [ ] Baseline TUI PTY result is recorded.
- [ ] Extraction ownership map is explicit enough that implementation will not simply move all of `AppState` into a generic crate.
- [ ] No engine/search algorithm change is included in the plan.

## Phase 1 — Create the `chess-app` shared library crate

- [ ] Add `crates/chess-app/Cargo.toml`.
- [ ] Add `crates/chess-app/src/lib.rs`.
- [ ] Add `crates/chess-app` to root workspace members.
- [ ] Use workspace version/edition/MSRV/author/repository/license/publish metadata.
- [ ] Use workspace lint configuration.
- [ ] Add `#![forbid(unsafe_code)]`.
- [ ] Depend only on the workspace crates actually required, expected initially to be `chess-core` and `chess-search`.
- [ ] Do not add Ratatui, Crossterm, JNI, FFI, UCI, Android, Python, or tuning dependencies to `chess-app`.
- [ ] Add crate-level documentation defining `chess-app` as an outward interactive-frontend application/session layer, not an engine layer.
- [ ] Document that UCI remains an independent external protocol adapter.

### Phase 1 tests/gates

- [ ] New crate participates in supported workspace formatting/check/Clippy/test commands.
- [ ] No dependency cycle or inverted dependency direction is introduced.
- [ ] `chess-core` and `chess-search` manifests remain free of frontend dependencies.

## Phase 2 — Extract the interactive search worker exactly

Move the current TUI worker semantics into `chess-app` before modifying console behavior.

- [ ] Move/port `SearchTicket` into `chess-app`.
- [ ] Move/port `SearchRequest` into `chess-app`.
- [ ] Move/port `SearchMetrics` into `chess-app`.
- [ ] Move/port `EngineEvent` into `chess-app`.
- [ ] Move/port `SearchWorkerError` into `chess-app`.
- [ ] Move/port `SearchWorker` into `chess-app`.
- [ ] Preserve use of existing `SearchLimits`.
- [ ] Preserve use of existing `SearchStopFlag` cancellation.
- [ ] Preserve typed progress events.
- [ ] Preserve exact completion event semantics.
- [ ] Preserve cancellation vs. failure distinction.
- [ ] Preserve owned game/search snapshot behavior.
- [ ] Preserve transposition-table construction policy unless a separately justified application-neutral refactor is required.
- [ ] Rename thread names from TUI-specific wording to neutral shared wording.
- [ ] Rename error strings from TUI-specific wording to neutral shared wording without changing behavior.
- [ ] Ensure channel closure still requests search stop where appropriate.
- [ ] Ensure `Drop`/explicit cancellation does not leave a detached engine search worker.
- [ ] Ensure worker join errors remain visible to the owning frontend.

### Phase 2 explicit fallback rejection

- [ ] Preserve rejection of `SearchResult` emergency/fallback moves.
- [ ] A result with an exact best move but no exact completed iteration is a failure.
- [ ] A result that ended before completing depth one is a failure/cancellation outcome, never a playable fallback.
- [ ] A result with no exact best move is a failure.
- [ ] No random legal move fallback exists.
- [ ] No first legal move fallback exists.
- [ ] No silent depth reduction/retry exists.
- [ ] No Python fallback exists.
- [ ] No UCI subprocess fallback exists.

### Phase 2 tests

- [ ] Exact fixed-depth worker returns an exact legal move.
- [ ] Explicit cancellation emits no playable `Completed` event.
- [ ] Worker joins after successful completion.
- [ ] Worker joins after cancellation.
- [ ] Worker panic maps to visible `SearchWorkerError`.
- [ ] Channel closure behavior is tested.
- [ ] Search fallback classification is tested directly.
- [ ] Missing exact iteration is tested.
- [ ] No fallback test depends on timing luck.

## Phase 3 — Extract the shared game/session controller

Create `chess_app::GameController` or an equivalently explicit type from the presentation-neutral portions of current TUI `AppState`.

### Phase 3.1 Shared value/state types

- [ ] Move/port `GameConfig` to `chess-app`.
- [ ] Preserve Human vs Engine configuration with human color and engine depth.
- [ ] Preserve Self-play configuration with independent White/Black depths.
- [ ] Preserve validated supported depth range.
- [ ] Move/port `GameOutcome` to `chess-app`.
- [ ] Create/refactor shared `GameSession`.
- [ ] Keep authoritative `chess_core::Game` in shared session state.
- [ ] Keep generation ID in shared session state.
- [ ] Keep active search ticket/thinking state in shared session state.
- [ ] Keep self-play automatic-play state in shared session state.
- [ ] Keep terminal outcome in shared session state.
- [ ] Keep engine metrics in shared session state.
- [ ] Keep shared status/error text only if it is useful to both frontends.
- [ ] Remove TUI move-entry editing state from shared session state.
- [ ] Remove TUI screen/menu/overlay state from shared session state.
- [ ] Remove TUI save-dialog state from shared session state.
- [ ] Decide explicitly whether `saved_path` is shared state or TUI presentation state; do not retain it accidentally.

### Phase 3.2 Controller lifecycle

- [ ] Implement shared `start_game`.
- [ ] Validate configuration before mutating/replacing current game state.
- [ ] Increment/replace game generation on restart/new game.
- [ ] Initialize authoritative starting `Game`.
- [ ] Refresh terminal/game outcome through `chess-core::Game::status()`.
- [ ] Schedule engine first move for Human/Black.
- [ ] Schedule White first move for Self-play.
- [ ] Add explicit abandon/reset method if both frontends need it.
- [ ] Do not put `should_quit` or frontend screen state in the shared controller.

### Phase 3.3 Human move handling

- [ ] Parse syntax through `chess_core::UciMove`.
- [ ] Reject malformed move visibly.
- [ ] Reject human move when no game is active.
- [ ] Reject human move after terminal outcome.
- [ ] Reject human move in Self-play.
- [ ] Reject human move while engine search is active.
- [ ] Reject human move when it is not the human side's turn.
- [ ] Resolve syntax against the current legal move set.
- [ ] Reject zero matches.
- [ ] Reject ambiguous/multiple matches if ever possible.
- [ ] Apply legal move transactionally.
- [ ] Preserve promotion identity.
- [ ] Refresh terminal state before scheduling another search.
- [ ] Schedule engine response only when the game remains ongoing.

### Phase 3.4 Engine event handling

- [ ] Ignore event when there is no current session.
- [ ] Ignore stale ticket that does not match active search.
- [ ] Progress updates presentation-neutral engine metrics only.
- [ ] Exact completion clears active-search/thinking state together.
- [ ] Revalidate returned engine move against current legal moves before applying.
- [ ] Reject engine move that is no longer legal.
- [ ] Apply exact current engine move once.
- [ ] Refresh terminal state after engine move.
- [ ] Schedule next move only when current mode/state requires it.
- [ ] Cancellation clears active-search/thinking state visibly.
- [ ] Failure clears active-search/thinking state visibly.
- [ ] Failure does not schedule a replacement move.

### Phase 3.5 Resignation and Self-play control

- [ ] Human resignation produces opponent winner.
- [ ] Resignation cancels shared search state correctly.
- [ ] Self-play pause is rejected outside Self-play.
- [ ] Self-play pause stops auto scheduling safely.
- [ ] Self-play resume is rejected outside Self-play.
- [ ] Resume is rejected after terminal outcome.
- [ ] Resume schedules the next engine search when appropriate.
- [ ] Step is available only while Self-play is paused.
- [ ] Step is rejected while a search/pending search exists.
- [ ] Step schedules exactly one ply.
- [ ] After step completion, Self-play remains paused.
- [ ] Game-over disables all further scheduling.

### Phase 3 tests

- [ ] Human White starts waiting for input.
- [ ] Human Black schedules first engine search.
- [ ] Self-play schedules first White search.
- [ ] New/restarted game gets a new generation.
- [ ] Malformed human move preserves exact game state.
- [ ] Well-formed illegal human move preserves exact game state.
- [ ] `e2e4` applies and schedules engine response.
- [ ] Promotion preserves explicit promotion piece.
- [ ] Stale completion preserves exact game state and active current search.
- [ ] Current exact completion applies once.
- [ ] Engine-returned illegal move is visible and not applied.
- [ ] Search failure clears thinking and is visible.
- [ ] Cancellation does not mutate game position.
- [ ] Resignation declares correct winner for both human colors.
- [ ] Self-play pause/resume/step transitions are correct.
- [ ] Terminal position schedules no additional search.

## Phase 4 — Extract shared pure text and save primitives

### Phase 4.1 Text formatting

Split current TUI rendering helpers so pure text logic can be reused without Ratatui.

- [ ] Move/port board orientation type to shared text module.
- [ ] Move/port orientation-from-config helper.
- [ ] Move/port ASCII board-line generation.
- [ ] Move/port piece-symbol formatting.
- [ ] Move/port numbered move-history formatting.
- [ ] Move/port turn/check/draw-claim status formatting.
- [ ] Move/port outcome formatting.
- [ ] Move/port score/mate formatting.
- [ ] Move/port search-metrics formatting or provide reusable field formatting suitable for both frontends.
- [ ] Move/port color/draw-reason names where useful.
- [ ] Keep terminal width/height/layout decisions inside `chess-tui`.
- [ ] Keep Ratatui-specific rendering inside `chess-tui`.
- [ ] Keep Crossterm-specific behavior inside `chess-tui`.

### Phase 4.2 Save primitives

- [ ] Define a neutral structured save record/snapshot if it removes real duplication.
- [ ] Derive ordered moves from authoritative `Game` history.
- [ ] Reuse atomic same-directory temp-write + rename implementation where appropriate.
- [ ] Preserve cleanup of temporary file after failed write/rename.
- [ ] Preserve explicit write errors.
- [ ] Keep TUI `v1` save serialization byte-compatible unless an explicit version migration is separately documented.
- [ ] Add console-specific deterministic serialization without calling it PGN.
- [ ] Do not introduce implicit save directories or auto-save.

### Phase 4 tests

- [ ] White board orientation golden/structural test.
- [ ] Black board orientation golden/structural test.
- [ ] Piece case and knight `N`/`n` test.
- [ ] Odd/even ply move numbering test.
- [ ] Check/draw-claim/status tests.
- [ ] Centipawn score formatting test.
- [ ] Mate score formatting test.
- [ ] Missing search metrics are not fabricated.
- [ ] Atomic write success test.
- [ ] Atomic overwrite replacement test.
- [ ] Failed write test.
- [ ] Successful write leaves no temp file.

## Phase 5 — Refactor `chess-tui` onto `chess-app`

This phase must finish and prove regression safety before substantive console features are considered complete.

### Phase 5.1 TUI state boundary

- [ ] Make `chess-tui` depend on `chess-app`.
- [ ] Replace duplicated shared controller types with `chess-app` types.
- [ ] Keep `MenuState` in `chess-tui`.
- [ ] Keep `AppScreen` in `chess-tui`.
- [ ] Keep confirmation/save overlays in `chess-tui`.
- [ ] Keep move input editing buffer in `chess-tui`.
- [ ] Keep `should_quit` in `chess-tui`.
- [ ] Keep terminal lifecycle in `chess-tui`.
- [ ] Keep Ratatui layout/widget code in `chess-tui`.
- [ ] Wrap shared `GameController` cleanly rather than exposing shared internals throughout every UI module.

### Phase 5.2 Worker/runtime wiring

- [ ] Replace TUI-local `SearchWorker` with shared worker.
- [ ] Preserve at-most-one active TUI-owned worker.
- [ ] Preserve cancellation/join on pause/menu/new/quit paths.
- [ ] Preserve stale-event rejection.
- [ ] Preserve engine progress display.
- [ ] Preserve visible worker errors.
- [ ] Preserve rejection of search fallback moves.

### Phase 5.3 Rendering/save wiring

- [ ] Reuse shared board/history/outcome/score/metric text helpers where extracted.
- [ ] Keep responsive layout logic unchanged unless a focused regression justifies a change.
- [ ] Preserve TUI save `v1` serialization bytes.
- [ ] Preserve overwrite confirmation semantics.
- [ ] Preserve mark-saved only-after-success behavior.

### Phase 5 regression gates

- [ ] TUI unit tests green.
- [ ] TUI hardening tests green.
- [ ] TUI integration tests green.
- [ ] TUI real PTY launch/quit green.
- [ ] PTY Human White move + real engine response green.
- [ ] PTY Self-play pause/step/resume green.
- [ ] PTY resignation confirmation green.
- [ ] PTY quit-while-thinking/cancellation green.
- [ ] PTY live resize green.
- [ ] PTY save success green.
- [ ] PTY save failure green.
- [ ] Alternate-screen enter/leave evidence still correct.
- [ ] TUI no longer contains an independent duplicate search worker/controller implementation.

### Phase 5 acceptance

- [ ] TUI behavior is green before proceeding to final console acceptance.
- [ ] Shared extraction did not change core/search behavior.
- [ ] Shared extraction did not add a `chess-tui -> chess-uci` dependency.

## Phase 6 — Create the `chess-console` binary crate

- [ ] Add `crates/chess-console/Cargo.toml`.
- [ ] Add `crates/chess-console/src/main.rs`.
- [ ] Add supporting library modules if needed for testability (`lib.rs`, command parser, runtime, rendering wrapper, input abstraction).
- [ ] Add `crates/chess-console` to workspace members.
- [ ] Use workspace package metadata/lints.
- [ ] Add `#![forbid(unsafe_code)]`.
- [ ] Depend on `chess-app`.
- [ ] Add direct `chess-core`/`chess-search` dependencies only if required for non-reexported value types.
- [ ] Do not depend on `chess-uci`.
- [ ] Do not depend on Python.
- [ ] Do not depend on Ratatui.
- [ ] Avoid Crossterm/raw-terminal dependencies unless the input/event-loop prototype proves they are needed.
- [ ] Keep ordinary stdout scrollback; do not use alternate screen or clear prior game output.

### Phase 6 basic smoke tests

- [ ] Binary starts and prints banner/menu.
- [ ] `Quit` from startup menu exits successfully.
- [ ] No terminal state restoration is required when no raw mode was entered.
- [ ] Captured stdout is readable/deterministic enough for integration assertions.

## Phase 7 — Implement console menu/configuration workflow

### Human vs Engine menu

- [ ] Startup menu offers Human vs Engine.
- [ ] Startup menu offers Self-play.
- [ ] Startup menu offers Quit.
- [ ] Empty startup selection chooses documented default.
- [ ] Invalid menu selection reports error and reprompts.
- [ ] Human mode asks White vs Black.
- [ ] Empty color selection chooses documented default.
- [ ] Invalid color selection reports error and reprompts.
- [ ] Human mode asks engine depth.
- [ ] Empty engine depth chooses documented default.
- [ ] Invalid/non-numeric depth reports error.
- [ ] Out-of-range depth reports accepted range and reprompts.
- [ ] Do not silently clamp invalid user depth.

### Self-play menu

- [ ] Ask White depth.
- [ ] Ask Black depth.
- [ ] Support documented defaults.
- [ ] Reject invalid/out-of-range values visibly.
- [ ] Construct shared `GameConfig::SelfPlay` only after both values validate.

### Phase 7 tests

- [ ] Default selections produce expected config.
- [ ] Human White config test.
- [ ] Human Black config test.
- [ ] Self-play independent depths test.
- [ ] Invalid menu input does not start game.
- [ ] Invalid depth does not silently alter config.

## Phase 8 — Implement console board/status/command parser

### Phase 8.1 Board/status output

- [ ] Print board at game start.
- [ ] Print board after every successfully applied human move.
- [ ] Print board after every successfully applied engine move.
- [ ] Human White orientation has White at bottom.
- [ ] Human Black orientation has Black at bottom.
- [ ] Self-play orientation defaults White at bottom.
- [ ] Print turn/check/result status.
- [ ] Print available draw-claim status consistently with shared logic.

### Phase 8.2 Command grammar

Implement at least:

- [ ] bare `<uci>` human move.
- [ ] `move <uci>` explicit human move.
- [ ] `board`.
- [ ] `moves`.
- [ ] `status`.
- [ ] `engine`.
- [ ] `help`.
- [ ] `resign`.
- [ ] `save <path>`.
- [ ] `new`.
- [ ] `menu`.
- [ ] `quit`.
- [ ] Self-play `pause`.
- [ ] Self-play `resume`.
- [ ] Self-play `step`.

### Parser requirements

- [ ] Command words are case-insensitive.
- [ ] Leading/trailing/repeated whitespace is handled deterministically.
- [ ] UCI move parsing remains core-owned.
- [ ] Unknown command produces visible error.
- [ ] Empty command at a game prompt is defined explicitly and does not accidentally repeat/destructively invoke a command.
- [ ] Mode-invalid command produces visible reason.
- [ ] No command silently does nothing when that would hide an invalid state.

### Phase 8 tests

- [ ] Bare move parse.
- [ ] Explicit move parse.
- [ ] Command case normalization.
- [ ] Whitespace normalization.
- [ ] Unknown command error.
- [ ] `resign` rejected in Self-play.
- [ ] `pause/resume/step` rejected in Human mode.
- [ ] Missing `save` path is visible error/prompt according to chosen grammar.

## Phase 9 — Complete Human vs Engine console workflow

### Human as White

- [ ] Start fresh shared controller game.
- [ ] Print board/status before first prompt.
- [ ] Accept `e2e4`.
- [ ] Apply move transactionally through shared controller.
- [ ] Print human move confirmation.
- [ ] Start shared engine worker only from pending search request.
- [ ] Process typed search progress events.
- [ ] Print progress without fabricating unavailable fields.
- [ ] Apply exact current engine completion through shared controller.
- [ ] Print `Engine plays: <uci>` only after actual application.
- [ ] Print resulting board/status.
- [ ] Return to human prompt only when human is actually to move.

### Human as Black

- [ ] Schedule engine first move immediately.
- [ ] Print engine progress/result.
- [ ] Apply exact engine White move.
- [ ] Print updated board/status.
- [ ] Prompt Black human only after current engine completion is applied.

### Move correctness

- [ ] Malformed move leaves exact game unchanged.
- [ ] Illegal move leaves exact game unchanged.
- [ ] Promotion suffix works.
- [ ] Human input while engine thinking is rejected/queued according to explicit runtime design, never applied out of turn.
- [ ] Terminal human move schedules no engine search.
- [ ] Terminal engine move returns to game-over commands rather than human move prompt.

### Phase 9 integration tests

- [ ] Human White `e2e4 -> exact legal engine response -> human turn`.
- [ ] Human Black `engine exact legal first move -> human turn`.
- [ ] Illegal human move board/history unchanged.
- [ ] Promotion fixture.
- [ ] Check status appears.
- [ ] Game-over status stops further search.

## Phase 10 — Engine progress and failure presentation

- [ ] Print a clear engine-thinking start line.
- [ ] Print completed/current depth when available.
- [ ] Print score in shared centipawn/mate format.
- [ ] Print node count when available.
- [ ] Print NPS when available.
- [ ] Print elapsed time when available.
- [ ] Print PV when available.
- [ ] Print hash fullness when available/desired.
- [ ] Represent unavailable fields as `-` or omit them consistently.
- [ ] Rate-limit or naturally bound progress output so the console is not flooded.
- [ ] Do not write fake `0` metrics for unavailable data.
- [ ] Search failure prints prominent error.
- [ ] Search failure leaves board/game unchanged from last valid move.
- [ ] Search failure clears thinking state.
- [ ] Search failure does not automatically retry.
- [ ] Search failure does not choose another move source.

### Phase 10 tests

- [ ] Progress line formatting test.
- [ ] Mate score output test.
- [ ] Missing optional metrics test.
- [ ] Failed search state/output test.
- [ ] No fallback output test.

## Phase 11 — Console input/event-loop and shutdown lifecycle

This is a correctness-sensitive phase. Do not hide blocking-input limitations.

### Phase 11.1 Choose/test input architecture

- [ ] Define an input event abstraction separate from command semantics.
- [ ] Determine how console input and `EngineEvent` values are multiplexed.
- [ ] Prototype/test receiving a pause or quit intent while a Self-play search is active.
- [ ] Keep `GameController` owned/mutated by exactly one application thread.
- [ ] Background input code, if used, sends typed input events only.
- [ ] Background input code does not own/mutate game state.
- [ ] Document whether the input reader is joinable/interruptible.
- [ ] Do not claim a blocked stdin thread was cleanly joined if it cannot actually be joined.
- [ ] If a process-lifetime input reader is chosen, document the lifecycle explicitly and prove it owns no engine/game state or cleanup-sensitive resources.
- [ ] Prefer no raw terminal mode; if raw mode is required, add scoped restoration and tests.
- [ ] Any new input dependency is MSRV-compatible and justified.

### Phase 11.2 Search worker ownership

- [ ] At most one console-owned active search worker.
- [ ] Spawn only for the current pending `SearchRequest`.
- [ ] Join on exact completion.
- [ ] Cancel/join after confirmed `new`.
- [ ] Cancel/join after confirmed `menu`.
- [ ] Cancel/join after confirmed `quit`.
- [ ] Cancel/join on EOF.
- [ ] Resolve worker panic/channel failure without leaving stale thinking state.
- [ ] Never detach engine worker.

### Phase 11.3 EOF behavior

- [ ] EOF is distinct from empty input.
- [ ] EOF prints a concise reason where possible.
- [ ] EOF cancels active engine search.
- [ ] EOF joins active engine worker.
- [ ] EOF exits deterministically without waiting for impossible confirmation.

### Phase 11 lifecycle tests

- [ ] EOF at startup exits cleanly.
- [ ] EOF during Human game exits cleanly.
- [ ] EOF during active engine search cancels/joins.
- [ ] Confirmed quit during active engine search cancels/joins.
- [ ] Declined quit does not cancel current game/search incorrectly.
- [ ] Restart/new game cannot receive stale old completion.
- [ ] Menu return cannot receive/apply stale old completion.
- [ ] No deadlock on worker completion + input arrival race.

## Phase 12 — Implement confirmations and save workflow

### Phase 12.1 Confirmations

- [ ] `resign` requires confirmation while game active.
- [ ] `new` requires confirmation while game active.
- [ ] `menu` requires confirmation while game active.
- [ ] `quit` requires confirmation while game active.
- [ ] Existing save destination requires overwrite confirmation.
- [ ] Empty confirmation defaults to No.
- [ ] Only explicit affirmative response performs destructive action.
- [ ] Invalid confirmation input is handled explicitly.
- [ ] Search cancellation happens after confirmation, not before.

### Phase 12.2 Save

- [ ] `save <path>` accepts explicit path.
- [ ] Missing/invalid path is visible.
- [ ] Serialize mode/configuration.
- [ ] Serialize ordered UCI moves from authoritative game.
- [ ] Serialize result/reason.
- [ ] Timestamp, if included, enters through a testable boundary.
- [ ] Console header/version is explicit and deterministic.
- [ ] Do not call the format PGN.
- [ ] Existing destination requires confirmation.
- [ ] Reuse shared atomic write primitive.
- [ ] Print success only after final rename/write succeeds.
- [ ] Print write/permission/path error visibly.
- [ ] Failed save does not mark/report Saved.
- [ ] No implicit save directory.
- [ ] No auto-save.

### Phase 12 tests

- [ ] Confirmation yes/no parser tests.
- [ ] Resignation declined leaves game active.
- [ ] Resignation confirmed declares opponent winner.
- [ ] New/menu/quit declined preserves game.
- [ ] Save serialization golden test.
- [ ] Save success exact-byte test.
- [ ] Save failure visibility test.
- [ ] Existing file decline preserves original file.
- [ ] Existing file confirm atomically replaces content.

## Phase 13 — Complete Self-play console workflow

- [ ] Starting Self-play schedules White search.
- [ ] Exact White completion applies one legal move.
- [ ] Automatic Black search follows.
- [ ] Automatic play alternates legally.
- [ ] `pause` safely stops automatic scheduling.
- [ ] If pause cancels the current search under shared semantics, cancellation is explicit and no obsolete result is applied.
- [ ] Paused mode accepts `step`.
- [ ] `step` schedules exactly one engine move.
- [ ] Step completion leaves `auto_play=false`.
- [ ] `resume` restarts automatic scheduling.
- [ ] `step` is disabled while a search is already active.
- [ ] Terminal game stops all scheduling.
- [ ] Console remains able to run `board`, `moves`, `status`, `engine`, `save`, `menu`, `quit`, and `help` where meaningful.
- [ ] Self-play writes no tuning/evaluation/weight-candidate files.

### Phase 13 tests

- [ ] Alternating legal Self-play plies.
- [ ] Pause prevents next automatic ply.
- [ ] Step applies exactly one ply.
- [ ] Step remains paused afterward.
- [ ] Resume restarts automatic play.
- [ ] Pause/resume during/around search does not apply stale result.
- [ ] Terminal Self-play schedules nothing further.
- [ ] No tuning artifact writes.

## Phase 14 — Console real-process acceptance coverage

Because the console does not use a full-screen terminal, real-process tests should be simpler than the TUI PTY suite. Still exercise the actual binary, not only unit abstractions.

- [ ] Add real-process launch/quit smoke test.
- [ ] Drive startup menu through stdin and capture stdout.
- [ ] Real binary Human White flow reaches a real engine response.
- [ ] Real binary Human Black flow receives engine first move.
- [ ] Real binary illegal move is visible and non-mutating.
- [ ] Real binary `board` output contains expected orientation/coordinates.
- [ ] Real binary resignation confirmation works.
- [ ] Real binary save success works using temporary path.
- [ ] Real binary save failure is visible.
- [ ] Real binary Self-play pause/step/resume is exercised through chosen input architecture.
- [ ] Real binary quit/EOF while searching exits without hanging.
- [ ] Test timeouts are bounded and failures provide useful captured stdout/stderr.
- [ ] Tests do not depend on fixed sleeps when a persistent state/output condition can be awaited instead.

## Phase 15 — Developer workflow and documentation

### `scripts/dev.sh`

- [ ] Add `bash scripts/dev.sh console`.
- [ ] Add `console` to `bash scripts/dev.sh help`.
- [ ] Add a focused console test command only if it provides real value.
- [ ] Keep `scripts/dev.sh` as the documented validation entry point.

### Root/workspace docs

- [ ] Update `README.md` to mention the Rust console application.
- [ ] Add `chess-app` to workspace crate list.
- [ ] Add `chess-console` to workspace crate list.
- [ ] Document the distinction among UCI, TUI, and console applications.
- [ ] Document console launch command.
- [ ] Document console commands.
- [ ] Document Human White/Black flow.
- [ ] Document Self-play pause/resume/step.
- [ ] Document save format as non-PGN.
- [ ] Document no Python runtime dependency.
- [ ] Update `docs/RUST_WORKSPACE_ARCHITECTURE.md` dependency table/graph/boundaries.
- [ ] Update `docs/RUST_DEVELOPER_WORKFLOWS.md`.
- [ ] Update `AGENTS.md` developer command list if it would otherwise be stale.
- [ ] Update `CLAUDE.md` architecture/command list if it would otherwise be stale.

## Phase 16 — Explicit dangerous-fallback and silent-failure audit

Before final validation, search the new/refactored code specifically for unsafe convenience behavior.

- [ ] Verify no `random` legal-move fallback in `chess-app`, `chess-console`, or refactored TUI.
- [ ] Verify no `first()`/`get(0)` legal move is used as a production fallback after search failure.
- [ ] Verify no `SearchResult::fallback()` becomes a playable interactive move.
- [ ] Verify no silent depth reduction.
- [ ] Verify no silent search retry with different limits/policy.
- [ ] Verify no Python process/import/runtime fallback.
- [ ] Verify no `chess-uci` subprocess fallback.
- [ ] Verify no implicit book/config discovery.
- [ ] Verify no implicit save destination.
- [ ] Verify no swallowed search worker panic.
- [ ] Verify no swallowed search channel closure.
- [ ] Verify no path where worker failure leaves `thinking=true` indefinitely.
- [ ] Verify no stale completion can apply after restart/new/menu/quit.
- [ ] Verify no detached engine worker.
- [ ] Verify unknown console commands are not silently ignored.
- [ ] Verify invalid mode commands are not silently ignored.
- [ ] Verify destructive confirmations default to No.
- [ ] Verify failed save cannot print/mark success.
- [ ] Verify no broad `unwrap()`/`expect()` was added on user input/filesystem/channel/search response paths.
- [ ] Verify no first-party lint `allow`/`expect` suppression was added.
- [ ] Verify no TUI regression test was removed/weakened merely because code moved.
- [ ] Record audit findings and justified exceptions, if any, explicitly in this TODO or a companion evidence note.

## Phase 17 — Final local validation on exact intended source SHA

Freeze the intended implementation source before claiming completion.

- [ ] Record exact intended final source SHA.
- [ ] Run `bash scripts/dev.sh fast` on that exact SHA.
- [ ] Run the repository's full supported validation workflow on that exact SHA where required.
- [ ] Run focused `chess-app` tests.
- [ ] Run focused `chess-console` tests.
- [ ] Run real-process console acceptance tests.
- [ ] Run focused `chess-tui` tests.
- [ ] Run TUI PTY acceptance suite.
- [ ] Run existing UCI tests.
- [ ] Confirm core perft gate remains unchanged/green.
- [ ] Confirm differential/core correctness gates remain green.
- [ ] Confirm relevant robustness gates remain green.
- [ ] Confirm FFI/JNI/Android boundaries remain unaffected/green through normal workspace gates.
- [ ] Confirm artifact audit remains green.
- [ ] Confirm strength audit remains green/no candidate activation change.
- [ ] Confirm no Python production/runtime dependency was added.
- [ ] Confirm supported MSRV policy for new dependencies/crates.
- [ ] Confirm lockfile is intentional and locked checks pass.

### Phase 17 evidence record

- Final source SHA:
- `fast` command/result:
- full command/result:
- `chess-app` focused command/result:
- `chess-console` focused command/result:
- console real-process command/result:
- TUI focused command/result:
- TUI PTY command/result:
- UCI command/result:
- other relevant gate results:

## Phase 18 — Permanent CI and exact-SHA closure

- [ ] Push the intended final source SHA to `master`.
- [ ] Identify the permanent CI run associated with that exact SHA.
- [ ] Record CI run URL/ID.
- [ ] Record relevant job IDs.
- [ ] Verify the workflow completed successfully; do not infer green from local tests.
- [ ] Verify the CI run tested the exact intended final SHA, not an earlier/later commit.
- [ ] If CI exposes a defect, fix it in a new commit and restart exact-SHA validation rather than marking the prior SHA complete.
- [ ] Record final exact green source SHA.
- [ ] Update this TODO checkboxes only from real evidence.
- [ ] Update any required Ralph status/evidence file if this project uses one for this milestone.
- [ ] Update `memory.md` only with an exact UTC timestamp/commit evidence according to repository policy.

### Permanent CI evidence record

- Final green source SHA:
- Workflow run ID:
- Workflow URL:
- Job ID(s):
- Artifact/evidence ID(s), if applicable:
- Final result:

## Phase 19 — Manual console acceptance

Automated process tests are required, but a short human-operated smoke pass should also verify the intended UX.

- [ ] Launch `bash scripts/dev.sh console` in a real terminal.
- [ ] Human White game: enter at least one legal move and observe engine reply.
- [ ] Human Black game: observe engine first move and enter a legal Black move.
- [ ] Verify board orientation for both human colors.
- [ ] Verify malformed move error is understandable.
- [ ] Verify illegal move error is understandable.
- [ ] Verify `board`.
- [ ] Verify `moves`.
- [ ] Verify `status`.
- [ ] Verify `engine`.
- [ ] Verify `help`.
- [ ] Verify resignation confirmation.
- [ ] Verify save to a writable path.
- [ ] Verify a save failure is visible.
- [ ] Verify overwrite confirmation.
- [ ] Verify Self-play starts automatically.
- [ ] Verify Self-play pause.
- [ ] Verify Self-play step exactly once.
- [ ] Verify Self-play resume.
- [ ] Verify confirmed quit during/after engine activity exits without hanging.
- [ ] Verify normal console scrollback remains readable and no alternate-screen behavior is used.

### Manual acceptance evidence

- Terminal/OS:
- Command:
- Source SHA:
- Result/notes:

## Final acceptance checklist

Do not mark the milestone complete until every applicable item below is backed by exact evidence.

- [ ] `chess-app` exists as a shared safe Rust application layer.
- [ ] `chess-console` exists as a safe Rust binary.
- [ ] Workspace architecture/dependency docs are accurate.
- [ ] TUI consumes shared controller/worker code instead of retaining an independent duplicate implementation.
- [ ] Existing TUI behavior remains green, including PTY acceptance.
- [ ] Human White console flow works end-to-end.
- [ ] Human Black console flow works end-to-end.
- [ ] Human move validation comes from `chess-core`.
- [ ] Engine search comes from `chess-search` through shared application worker.
- [ ] Exact completed engine move is revalidated/applied exactly once.
- [ ] Search fallback/emergency move is never played interactively.
- [ ] Search failure is visible and preserves last valid game.
- [ ] Self-play auto/pause/resume/step works.
- [ ] Stale search results cannot mutate a restarted/new/abandoned game.
- [ ] Board/moves/status/engine/help commands work.
- [ ] Resign/new/menu/quit confirmations work and default safely.
- [ ] Save is explicit, deterministic, and fail-visible.
- [ ] Existing save overwrite requires confirmation.
- [ ] EOF/shutdown resolves active engine worker safely.
- [ ] No random legal move fallback.
- [ ] No first legal move fallback.
- [ ] No silent depth reduction/retry.
- [ ] No Python fallback.
- [ ] No UCI subprocess fallback.
- [ ] No implicit book/config/save discovery.
- [ ] No silent worker failures.
- [ ] No detached engine search worker.
- [ ] No engine/evaluation/tuning activation change bundled into the milestone.
- [ ] `bash scripts/dev.sh fast` is green on exact final source SHA.
- [ ] Required full/focused/PTY/real-process validations are green on exact final source SHA.
- [ ] Permanent CI is green on exact final source SHA.
- [ ] Exact CI run/job/evidence identifiers are recorded.
- [ ] Manual console acceptance is recorded.

## Closure note

The console milestone is a frontend/application-sharing milestone. It is not complete if the console merely appears to work while duplicating the TUI controller, bypassing exact-search-result policy, hiding failures, or regressing the already-completed TUI. The intended end state is one authoritative Rust engine, one shared interactive application/session layer, and separate UCI, TUI, and scrolling-console adapters with explicit responsibilities.