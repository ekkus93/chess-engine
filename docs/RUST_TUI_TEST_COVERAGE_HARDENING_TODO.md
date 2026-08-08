# Rust TUI Test Coverage Hardening TODO

Companion specification: `docs/RUST_TUI_TEST_COVERAGE_HARDENING_SPEC.md`

Status: active implementation plan; not yet implemented.

Starting baseline SHA: `1c83c40ff33fb77e9f19f6873b33561af64c9199`

Objective: add reproducible `cargo llvm-cov` coverage reporting and close the highest-value Rust TUI test gaps without changing engine/search/evaluation/tuning behavior or weakening the TUI's fail-closed search-result policy.

This TODO is intended to be Ralph-loop executable. Check an item only when its implementation and evidence exist on the repository SHA being validated. Do not infer completion from nearby tests with similar names.

## Hard constraints

- [ ] Do not change chess rules, legal-move semantics, search strength, evaluation, move ordering, pruning, extensions, transposition policy, opening-book policy, tuning state, or promotion disposition.
- [ ] Do not add a first-legal-move fallback.
- [ ] Do not add a random-legal-move fallback.
- [ ] Do not silently retry at lower depth.
- [ ] Do not silently swap search policy/engine implementation.
- [ ] Do not add a Python runtime/engine fallback.
- [ ] Do not weaken existing tests or warning/lint gates to obtain higher coverage.
- [ ] Do not broadly exclude low-coverage production code from `cargo llvm-cov` reports.
- [ ] Treat coverage percentage as diagnostic evidence, not a correctness proof.
- [ ] Keep the existing Rust TUI manual real-terminal acceptance TODO independent; do not retroactively mark those manual items complete here.

## Phase 0 — Authority registration and baseline freeze

- [ ] Record the exact `master` SHA at implementation start.
- [ ] Confirm `docs/RUST_TUI_TEST_COVERAGE_HARDENING_SPEC.md` and this TODO are registered as an active follow-up program in the TODO authority index/audit.
- [ ] Re-read `docs/RUST_TUI_SPEC.md` and `docs/RUST_TUI_TODO.md` before editing production code.
- [ ] Confirm current `crates/chess-tui` source files and tests.
- [ ] Confirm no unrelated engine/search/evaluation/tuning changes are already mixed into the working diff.
- [ ] Run the existing fast/permanent-supported Rust validation appropriate for the environment and record the result.
- [ ] Record the current Rust toolchain/MSRV policy.
- [ ] Record the exact current `cargo-llvm-cov` version chosen for implementation/CI.
- [ ] Record whether coverage uses the repository MSRV toolchain or a separate coverage host toolchain.

### Phase 0 baseline coverage

Before adding hardening tests:

- [ ] Install/enable the LLVM tools component required by the chosen coverage toolchain.
- [ ] Run `cargo llvm-cov clean --workspace`.
- [ ] Run focused baseline coverage for `chess-tui`.
- [ ] Record baseline line coverage.
- [ ] Record baseline function coverage where reported.
- [ ] Record baseline region coverage where reported.
- [ ] Record major uncovered `chess-tui` functions/branches.
- [ ] Save the exact command and tool versions used so final coverage is comparable.

### Phase 0 acceptance

- [ ] Baseline source SHA and coverage summary are recorded before hardening tests materially change the numbers.
- [ ] No arbitrary minimum coverage percentage has been adopted.
- [ ] High-risk uncovered branches are identified explicitly rather than hidden by aggregate percentage.

## Phase 1 — Add canonical `cargo llvm-cov` developer workflow

- [ ] Add a documented supported command for focused terminal coverage summary.
- [ ] Add a documented supported command for LCOV output.
- [ ] Add a documented supported command for optional HTML output.
- [ ] Prefer a repository script/helper if that makes the invocation stable and discoverable.
- [ ] Ensure the focused command runs all relevant `chess-tui` test targets.
- [ ] Use `--all-features` unless the crate has a documented reason not to.
- [ ] Keep coverage artifacts under `target/` or another ignored generated-artifact path.
- [ ] Ensure generated LCOV/HTML files are not accidentally committed.
- [ ] Document `cargo llvm-cov clean --workspace` for clean baseline/reproduction when needed.
- [ ] Add a secondary workspace-wide informational coverage command only if it remains cheap and does not expand task scope.
- [ ] Document that coverage tooling is development infrastructure, not a `chess-tui` runtime dependency.
- [ ] Do not raise the product MSRV solely to satisfy coverage tooling.

### Canonical command acceptance

The repository must have supported equivalents of:

```bash
cargo llvm-cov clean --workspace
cargo llvm-cov -p chess-tui --all-features --summary-only
cargo llvm-cov -p chess-tui --all-features --lcov --output-path target/chess-tui-lcov.info
cargo llvm-cov -p chess-tui --all-features --html
```

- [ ] Summary command succeeds.
- [ ] LCOV command succeeds and produces a nonempty report.
- [ ] HTML command succeeds locally/CI where requested.
- [ ] No production source file is silently excluded merely because it is difficult to test.

## Phase 2 — Deterministic search-result fallback rejection coverage (P0)

Current risk: the existing `explicit_discard_never_emits_a_playable_fallback` test proves cancellation/discard behavior, but does not directly prove the non-discarded `result.fallback().is_some()` rejection branch.

### Refactor/test seam

- [ ] Identify the smallest deterministic boundary around `finish_request` result classification.
- [ ] If needed, extract a pure/internal classifier that does not alter production semantics.
- [ ] Keep channel delivery/worker ownership separate from result classification where practical.
- [ ] Do not expose a generic fallback move to `AppState` or UI code.
- [ ] Do not modify `chess-search` fallback semantics globally merely to satisfy TUI tests.

### Required tests

- [ ] `fallback_only_result_is_rejected_by_tui` or equivalent.
- [ ] Assert fallback-only result produces `Failed`, never `Completed`.
- [ ] Assert failure message explicitly identifies TUI fallback rejection.
- [ ] Assert no playable move is returned with fallback-only disposition.
- [ ] Assert discard state wins over an otherwise completed/fallback result and yields cancellation.
- [ ] Assert exact completed best move still yields `Completed`.
- [ ] Assert search error yields `Failed` with visible message.
- [ ] Assert exact move with missing required exact-iteration metrics fails closed if that state is constructible/testable.
- [ ] Assert result with neither exact move nor fallback fails closed.

### Phase 2 acceptance

- [ ] Coverage report proves the fallback-only rejection branch executed.
- [ ] No first-legal fallback path exists in TUI code after the change.
- [ ] Existing worker exact-depth and explicit-cancellation tests remain green.

## Phase 3 — `EngineRuntime` lifecycle/error coverage (P0/P1)

Directly test `EngineRuntime::drive()` and `EngineRuntime::cancel()` behavior.

### Testability seam

- [ ] Determine whether current private runtime types can be tested directly inside `ui.rs`.
- [ ] Prefer same-module unit tests and synthetic channels over production abstraction changes.
- [ ] If deterministic spawn/join/failure injection is impossible, add the smallest internal worker seam necessary.
- [ ] Production selection must still unconditionally use the real `SearchWorker`.
- [ ] Do not add a runtime-configurable alternate search engine/factory.

### Required lifecycle tests

- [ ] pending `SearchRequest` -> exactly one active worker starts.
- [ ] Progress event updates presentation state and retains active worker ownership.
- [ ] Completed final event clears/joins active worker.
- [ ] Failed final event clears/joins active worker and leaves visible failure state.
- [ ] Cancelled final event clears/joins active worker.
- [ ] finished worker with no final event becomes explicit `Failed` state.
- [ ] event-channel disconnect after worker end is not silently treated as successful completion.
- [ ] `cancel()` with no active worker succeeds harmlessly.
- [ ] `cancel()` with active worker requests stop/discard and joins.
- [ ] cancelled worker cannot later deliver/apply a playable completion.
- [ ] spawn failure clears thinking state and becomes visible.
- [ ] worker panic/join failure propagates to runtime boundary.
- [ ] runtime application-error handling clears thinking rather than leaving a wedged UI.
- [ ] next pending search does not start while previous worker ownership remains active.
- [ ] after final worker cleanup, a legitimate next search can start.

### Race/invariant tests

- [ ] stale final event after game generation change is ignored.
- [ ] stale progress after game generation change is ignored.
- [ ] stale Failed event does not overwrite current-game status.
- [ ] stale Cancelled event does not clear a current search.
- [ ] at most one TUI-owned worker/search is active at a time.

### Phase 3 acceptance

- [ ] Worker ownership transitions are deterministic in tests; no sleep-based luck is required for unit-level behavior.
- [ ] Runtime disconnect/failure branches are visible in coverage.
- [ ] No lifecycle error path silently returns success while leaving `thinking=true`.

## Phase 4 — Keyboard and overlay state-machine coverage (P1)

Add direct synthetic-key tests around `handle_key`, menu/game handlers, overlays, and confirmation execution.

### Main-menu navigation

- [ ] Up at row 0 does not underflow.
- [ ] Down at last row does not overflow.
- [ ] Up/Down move through expected rows.
- [ ] Left/Right on mode toggles Human-vs-Engine/Self-play as intended.
- [ ] Enter on adjustable menu rows performs the intended adjustment.
- [ ] Human color toggles White/Black.
- [ ] Human engine depth decrements/increments.
- [ ] Human engine depth clamps at minimum.
- [ ] Human engine depth clamps at maximum.
- [ ] Self-play White depth adjusts independently.
- [ ] Self-play Black depth adjusts independently.
- [ ] Self-play depths clamp at minimum/maximum.
- [ ] Enter on Start starts exactly the selected configuration.
- [ ] q from menu requests quit.
- [ ] Esc from menu requests quit.

### Human move-entry editing

- [ ] legal move characters append to `move_input`.
- [ ] uppercase input is normalized to lowercase.
- [ ] input is capped at five characters.
- [ ] Backspace removes one character.
- [ ] Backspace on empty input is harmless.
- [ ] Esc with nonempty move input clears input and does not open MainMenu confirmation.
- [ ] Enter with a legal move submits it.
- [ ] Enter with malformed input leaves game state unchanged and visible error set.
- [ ] Enter with well-formed illegal input leaves game state unchanged and visible error set.
- [ ] shortcut-looking letters inside nonempty move input are treated as input, not shortcuts.
- [ ] move characters are ignored when engine owns the turn.
- [ ] move characters are ignored in Self-play mode.

### Active-game shortcuts

- [ ] r opens resignation confirmation only for active Human-vs-Engine game.
- [ ] r does not create resignation action in Self-play.
- [ ] n opens NewGame confirmation while active.
- [ ] m opens MainMenu confirmation while active.
- [ ] Esc opens MainMenu confirmation when not editing move text and game is active.
- [ ] q opens Quit confirmation while active.
- [ ] v opens SavePath overlay.

### Confirmation overlay

- [ ] y executes confirmation.
- [ ] Enter executes confirmation.
- [ ] n dismisses confirmation without action.
- [ ] Esc dismisses confirmation without action.
- [ ] unrelated keys do nothing.
- [ ] Resign confirmation resolves active worker before outcome mutation.
- [ ] NewGame confirmation resolves active worker before generation replacement.
- [ ] MainMenu confirmation resolves active worker before session removal.
- [ ] Quit confirmation resolves active worker before quit state.

### Self-play keyboard controls

- [ ] Space while running pauses.
- [ ] Space pause resolves active search ownership.
- [ ] Space while paused resumes and schedules as appropriate.
- [ ] s while paused schedules exactly one ply.
- [ ] s while running does not schedule a second search.
- [ ] s while already thinking does not schedule a second search.
- [ ] self-play controls do not restart search after terminal outcome.

### Ctrl-C

- [ ] Ctrl-C with no worker exits cleanly.
- [ ] Ctrl-C with active worker cancels/joins worker before quit.
- [ ] Ctrl-C clears search state.
- [ ] no stale engine move can apply after Ctrl-C.

### Phase 4 acceptance

- [ ] Key behavior can be tested without a real terminal.
- [ ] Text-entry focus invariant is directly covered.
- [ ] Abandonment confirmations are directly covered.

## Phase 5 — `AppState` defensive/error-path coverage (P1)

### Configuration validation

- [ ] Human-vs-Engine depth `0` is rejected.
- [ ] Human-vs-Engine depth above `MAX_MENU_SEARCH_DEPTH` is rejected.
- [ ] Self-play White depth below minimum is rejected.
- [ ] Self-play White depth above maximum is rejected.
- [ ] Self-play Black depth below minimum is rejected.
- [ ] Self-play Black depth above maximum is rejected.
- [ ] valid min/max boundary depths are accepted.

### Missing/invalid session transitions

- [ ] restart with no session returns visible/typed error.
- [ ] mark-saved with no session returns error.
- [ ] step with no session returns error.
- [ ] pause with no session returns error.
- [ ] resume with no session returns error.
- [ ] resign with no session returns error.

### Mode/turn misuse

- [ ] human move during Self-play is rejected without mutation.
- [ ] human move while engine search is active is rejected without mutation.
- [ ] human move when it is the engine side's turn is rejected without mutation.
- [ ] resignation during Self-play is rejected visibly.
- [ ] pause in Human-vs-Engine mode is rejected visibly.
- [ ] resume in Human-vs-Engine mode is rejected visibly.
- [ ] step in Human-vs-Engine mode is rejected.
- [ ] step while self-play auto-play is running is rejected.
- [ ] step while search/pending request exists is rejected.

### Terminal-state misuse

- [ ] human move after game over is rejected.
- [ ] resignation after game over is rejected.
- [ ] resume after game over is rejected.
- [ ] step after game over is rejected.
- [ ] terminal state clears active search/pending/thinking/auto-play.

### Engine event defenses

- [ ] current-ticket illegal engine completion is rejected and not applied.
- [ ] current-ticket search failure clears active search and thinking.
- [ ] current-ticket cancellation clears active search and thinking.
- [ ] stale Progress ignored.
- [ ] stale Completed ignored.
- [ ] stale Failed ignored.
- [ ] stale Cancelled ignored.
- [ ] event with no session is harmless and cannot create state.

### Explicit state clearing

- [ ] `cancel_search_state(None)` clears pending/active/thinking without inventing a message.
- [ ] `cancel_search_state(Some(...))` clears search state and stores the requested visible message.
- [ ] `return_to_menu()` clears pending/session/overlay and sets MainMenu.
- [ ] `request_quit()` clears pending/overlay and sets quit.
- [ ] starting a new game clears stale overlay/status/search presentation as intended.

### Phase 5 acceptance

- [ ] Defensive branches produce typed/visible failures rather than silent mutation/no-op where a bug would otherwise be hidden.
- [ ] Coverage shows the important misuse branches executed.

## Phase 6 — Terminal chess-state coverage (P1)

Use authoritative `chess-core` state; do not duplicate adjudication logic.

### Check/checkmate/stalemate

- [ ] in-check ongoing position renders/checks `CHECK` but remains active.
- [ ] checkmate through human move stops scheduling.
- [ ] checkmate through engine move stops scheduling.
- [ ] stalemate fixture maps to `GameOutcome::Stalemate`.
- [ ] stalemate schedules no further search.

### Automatic draws

- [ ] dead-position/insufficient-material fixture maps to automatic draw if represented by the core.
- [ ] dead-position automatic draw schedules no further search.
- [ ] add at least one additional automatic draw fixture when deterministic without corrupting hidden history state.
- [ ] automatic draw result text includes the authoritative reason.

### Claimable draws

- [ ] claimable threefold state remains nonterminal unless an explicit claim feature exists.
- [ ] claimable fifty-move state remains nonterminal unless an explicit claim feature exists.
- [ ] both-claim status renders both reasons when constructible.
- [ ] claim availability does not silently stop engine scheduling unless core status is terminal.

### Formatting

- [ ] `format_outcome` covers Checkmate.
- [ ] `format_outcome` covers Stalemate.
- [ ] `format_outcome` covers Draw.
- [ ] `format_outcome` covers Resignation.
- [ ] `draw_reason_name` covers ThreefoldRepetition.
- [ ] `draw_reason_name` covers FivefoldRepetition.
- [ ] `draw_reason_name` covers FiftyMoveRule.
- [ ] `draw_reason_name` covers SeventyFiveMoveRule.
- [ ] `draw_reason_name` covers DeadPosition.

### Phase 6 acceptance

- [ ] Terminal-state tests demonstrate no TUI-local draw/checkmate reimplementation.
- [ ] At least stalemate and one automatic draw path are directly covered.

## Phase 7 — Save UI transaction coverage (P1)

### Overlay editing

- [ ] opening save overlay provides the defined default path.
- [ ] printable characters append to save path.
- [ ] Backspace removes one path character.
- [ ] Backspace on empty path is harmless.
- [ ] Esc dismisses save overlay without saving.
- [ ] control characters do not enter the save path.

### Save validation/error flow

- [ ] empty path fails visibly.
- [ ] whitespace-only path fails visibly.
- [ ] no-session save fails visibly and cannot panic.
- [ ] filesystem NotFound failure remains visible.
- [ ] permission-denied/read-only failure is covered where deterministic on CI; otherwise disposition explicitly.
- [ ] failed save does not set `saved_path`.
- [ ] failed save clears stale prior `saved_path`.
- [ ] failed save never emits a success message.

### Successful save flow

- [ ] successful UI save writes exact `serialize_game` output.
- [ ] successful UI save records exact selected path.
- [ ] successful UI save displays success.
- [ ] successful UI save closes overlay.
- [ ] a later move clears saved-path state.

### Serialization matrix

- [ ] Human-vs-Engine / White serialization.
- [ ] Human-vs-Engine / Black serialization.
- [ ] Self-play serialization with distinct White/Black depths.
- [ ] timestamp present.
- [ ] timestamp absent.
- [ ] zero moves.
- [ ] multiple moves in exact order.
- [ ] promotion move.
- [ ] ongoing result.
- [ ] checkmate result.
- [ ] stalemate result.
- [ ] draw result.
- [ ] resignation result.
- [ ] output never falsely claims PGN.

### Phase 7 acceptance

- [ ] Save tests prove user-visible transaction semantics, not only `fs::write` behavior.
- [ ] No save failure is silently converted into success.

## Phase 8 — Rendering/helper branch coverage (P2)

### Board/pieces/orientation

- [ ] piece symbol Pawn White/Black.
- [ ] Knight White/Black.
- [ ] Bishop White/Black.
- [ ] Rook White/Black.
- [ ] Queen White/Black.
- [ ] King White/Black.
- [ ] White human orientation.
- [ ] Black human orientation.
- [ ] Self-play White orientation.
- [ ] board output remains exactly 19 lines where expected.

### Move history

- [ ] empty history.
- [ ] one ply.
- [ ] two plies.
- [ ] odd multi-ply history.
- [ ] even multi-ply history.

### Search metrics

- [ ] no metrics -> unavailable markers, not fabricated zeroes.
- [ ] fully populated metrics.
- [ ] depth formatting.
- [ ] positive centipawn score.
- [ ] zero centipawn score.
- [ ] negative centipawn score.
- [ ] positive mate score.
- [ ] negative mate score.
- [ ] nodes formatting.
- [ ] NPS formatting.
- [ ] elapsed milliseconds formatting.
- [ ] elapsed seconds formatting.
- [ ] hash fullness formatting.
- [ ] empty PV -> `-`.
- [ ] nonempty PV -> ordered UCI string.

### Layout boundaries

- [ ] width immediately below wide threshold.
- [ ] width exactly at wide threshold.
- [ ] width immediately above wide threshold.
- [ ] height immediately below horizontal minimum.
- [ ] height exactly at horizontal minimum.
- [ ] stacked width immediately below minimum.
- [ ] stacked width exactly at minimum.
- [ ] stacked height immediately below minimum.
- [ ] stacked height exactly at minimum.
- [ ] large terminal remains supported.

### Overlay/render structural tests

- [ ] resignation confirmation text renders.
- [ ] new-game confirmation text renders.
- [ ] menu confirmation text renders.
- [ ] quit confirmation text renders.
- [ ] save overlay text/path renders.
- [ ] too-small message reports current and required dimensions.
- [ ] no-session Game screen renders explicit safe state rather than panicking.

### Phase 8 acceptance

- [ ] Prefer targeted structural assertions over huge brittle full-screen snapshots.
- [ ] Coverage improvements correspond to meaningful formatting branches.

## Phase 9 — Terminal guard failure-path testability (P2)

- [ ] Re-evaluate whether `TerminalGuard` failure branches justify a small internal test seam.
- [ ] Do not refactor terminal lifecycle merely to increase percentage if the seam adds more complexity than confidence.
- [ ] Retain real PTY launch/quit smoke regardless.

If a terminal-operations seam is introduced:

- [ ] production still uses Crossterm/stdout unconditionally.
- [ ] raw-mode enable success + alternate-screen failure attempts raw restore.
- [ ] terminal construction failure attempts required cleanup.
- [ ] explicit restore attempts raw disable.
- [ ] explicit restore attempts LeaveAlternateScreen even if raw disable failed.
- [ ] explicit restore attempts cursor show even if an earlier cleanup step failed.
- [ ] first cleanup error is preserved/returned.
- [ ] successful restore marks guard restored.
- [ ] Drop skips duplicate cleanup after successful explicit restore.
- [ ] Drop performs best-effort cleanup after incomplete explicit restore/new lifecycle.

If no seam is introduced:

- [ ] Record why PTY integration evidence plus current code structure is preferable to production abstraction solely for unit coverage.

### Phase 9 acceptance

- [ ] Terminal cleanup has stronger evidence without weakening explicit restoration errors.
- [ ] No `let _ = ...` on an explicit normal-path restoration result hides a failure that should be returned; Drop remains best-effort by necessity.

## Phase 10 — Coverage review and residual-gap disposition

After P0/P1/P2 tests are added:

- [ ] Run `cargo llvm-cov clean --workspace`.
- [ ] Run final focused TUI summary with the same configuration as baseline.
- [ ] Generate LCOV artifact.
- [ ] Generate/view HTML report during review if useful.
- [ ] Compare baseline and final line coverage.
- [ ] Compare baseline and final function coverage.
- [ ] Compare baseline and final region coverage.
- [ ] Identify every materially uncovered production TUI function.
- [ ] Identify materially uncovered safety/error branches even inside covered functions.
- [ ] Add additional tests where value is high and behavior is deterministic.
- [ ] Explicitly disposition residual gaps that are impractical or lower-value.
- [ ] Do not add meaningless assertions solely to move the percentage.
- [ ] Do not exclude residual gaps from the report merely to improve the number.

### Coverage acceptance

- [ ] Fallback-only rejection branch is covered.
- [ ] `EngineRuntime` final-event/disconnect/cancel behavior is covered.
- [ ] key/overlay state-machine behavior is substantially covered.
- [ ] save UI transaction is covered.
- [ ] stalemate/automatic draw paths are covered as specified.
- [ ] residual uncovered code is understood and documented.

## Phase 11 — Permanent CI coverage integration

- [ ] Choose permanent workflow/job location for focused TUI coverage.
- [ ] Run coverage on Linux.
- [ ] Install the required Rust LLVM tools component.
- [ ] Install `cargo-llvm-cov` with a reviewed reproducible mechanism.
- [ ] Record/pin the tool/action version appropriately for repository policy.
- [ ] Run focused `chess-tui` coverage tests.
- [ ] Print human-readable summary to CI log.
- [ ] Generate LCOV artifact.
- [ ] Upload LCOV artifact using GitHub Actions artifact storage if compatible with permanent CI policy.
- [ ] Do not require Codecov or another external coverage account/token.
- [ ] Coverage job fails if tests fail.
- [ ] Coverage job fails if instrumentation/report generation fails.
- [ ] Coverage job does not fail solely because an arbitrary percentage is below a threshold.
- [ ] Keep existing permanent quality/robustness gates unchanged.
- [ ] Keep explicit MSRV job/gate separate and green.
- [ ] Ensure coverage job does not activate tuning, generated weights, or other mutable engine state.

### Phase 11 acceptance

- [ ] A clean CI runner can reproduce the focused coverage report from repository configuration.
- [ ] LCOV/report artifact is tied to the exact tested SHA.
- [ ] No secret/token is required solely to view coverage evidence.

## Phase 12 — Full regression validation

Run on the exact intended final source SHA.

### Formatting/build/lint/tests

- [ ] `cargo fmt --all -- --check`
- [ ] `cargo check --locked --workspace --all-targets --all-features`
- [ ] `cargo clippy --locked --workspace --all-targets --all-features -- -D warnings`
- [ ] `cargo test --locked --workspace --all-targets --all-features`
- [ ] `cargo test --locked -p chess-tui --all-targets --all-features`
- [ ] `cargo build --locked --release -p chess-tui`

### Coverage

- [ ] `cargo llvm-cov -p chess-tui --all-features --summary-only`
- [ ] `cargo llvm-cov -p chess-tui --all-features --lcov --output-path target/chess-tui-lcov.info`
- [ ] LCOV output is nonempty and corresponds to the exact final SHA.

### Existing chess-engine gates

- [ ] authoritative release perft remains green.
- [ ] differential/core correctness remains green.
- [ ] UCI smoke/tests remain green.
- [ ] Miri subset remains green where permanent workflow requires it.
- [ ] ASan/LSan checks remain green.
- [ ] TSan cancellation/concurrency checks remain green.
- [ ] fuzz/corpus gates remain green.
- [ ] ARM64 workspace validation remains green where permanent workflow requires it.
- [ ] explicit Rust MSRV validation remains green.

### Behavior audit

- [ ] Diff against starting SHA contains no unintended `chess-core` rule changes.
- [ ] Diff contains no unintended `chess-search` behavior changes.
- [ ] Diff contains no evaluation-weight/search-strength changes.
- [ ] Diff contains no tuning/promotion activation changes.
- [ ] No first-legal fallback exists in TUI code.
- [ ] No random-legal fallback exists in TUI code.
- [ ] No silent depth-reduction retry exists.
- [ ] No Python fallback exists.
- [ ] No search failure is silently transformed into a legal-looking move.
- [ ] No worker failure can silently leave the application thinking indefinitely.

## Phase 13 — Evidence and closure

- [ ] Record implementation starting SHA.
- [ ] Record final source SHA.
- [ ] Record `cargo-llvm-cov` version.
- [ ] Record coverage Rust toolchain version.
- [ ] Record baseline coverage summary.
- [ ] Record final coverage summary.
- [ ] Record delta by line/function/region where available.
- [ ] Record important residual uncovered functions/branches and disposition.
- [ ] Record focused validation commands/results.
- [ ] Record focused CI run IDs/jobs.
- [ ] Record permanent CI run ID/jobs on exact final SHA.
- [ ] Record permanent robustness run ID/jobs on exact final SHA.
- [ ] Record coverage artifact identity/name on exact final SHA.
- [ ] Confirm fallback-only search-result rejection test executed in permanent validation.
- [ ] Confirm no silent fallback behavior was introduced.
- [ ] Confirm no engine search/evaluation/tuning/promotion behavior changed.
- [ ] Perform final diff audit against starting SHA.
- [ ] Remove any temporary coverage/debug workflows or helper artifacts not intended to be permanent.
- [ ] Reconcile TODO authority index/audit accurately.
- [ ] Do not mark this TODO complete while any required P0/P1 gate remains unresolved.

## Recommended test names

Names may differ, but these behaviors should remain individually discoverable:

```text
fallback_only_result_is_rejected_by_tui
discarded_result_cannot_become_completion
runtime_starts_one_pending_worker
runtime_progress_keeps_worker_active
runtime_final_event_joins_worker
runtime_worker_without_final_event_fails_visibly
runtime_cancel_with_active_worker_joins_cleanly
runtime_spawn_failure_clears_thinking
stale_failed_event_is_ignored
stale_cancelled_event_is_ignored
current_illegal_engine_completion_is_rejected
menu_depth_adjustment_clamps_at_bounds
move_editing_prevents_shortcut_activation
move_input_is_lowercased_and_length_limited
confirmation_cancel_does_not_execute_action
confirmation_new_game_cancels_search_before_restart
confirmation_menu_cancels_search_before_abandon
confirmation_quit_cancels_search_before_exit
self_play_space_pauses_and_cancels_active_search
ctrl_c_cancels_search_before_quit
stalemate_is_terminal_and_schedules_nothing
dead_position_draw_is_terminal_and_schedules_nothing
empty_save_path_fails_visibly
successful_save_transaction_records_path_and_contents
failed_save_transaction_never_marks_saved
all_search_metrics_render_without_fabricated_values
layout_decision_boundary_matrix
```

## Definition of done

- [ ] `cargo llvm-cov` has a documented reproducible focused TUI workflow.
- [ ] Baseline and final coverage are recorded comparably.
- [ ] P0 fallback rejection has deterministic direct branch coverage.
- [ ] `EngineRuntime` lifecycle/error handling has direct deterministic coverage.
- [ ] keyboard/input/overlay state transitions have direct coverage.
- [ ] important `AppState` defensive branches have direct coverage.
- [ ] stalemate and at least one authoritative automatic-draw path are covered.
- [ ] save UI transaction success/failure is covered.
- [ ] meaningful rendering/serialization branches are covered.
- [ ] terminal cleanup retains real PTY evidence and any new failure seam is covered.
- [ ] permanent CI produces a focused coverage report/artifact without arbitrary percentage gating.
- [ ] existing correctness, build, lint, MSRV, perft, differential, UCI, and robustness gates remain green.
- [ ] final exact SHA is validated by permanent CI/robustness evidence.
- [ ] final diff contains no unintended engine/search/evaluation/tuning/promotion behavior changes.
- [ ] no silent failure or forbidden fallback behavior exists.
- [ ] residual coverage gaps are explicitly understood/dispositioned.
- [ ] TODO authority bookkeeping is consistent and permanent audit is green.
