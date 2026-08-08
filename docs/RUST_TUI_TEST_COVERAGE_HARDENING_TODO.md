# Rust TUI Test Coverage Hardening TODO

Companion specification: `docs/RUST_TUI_TEST_COVERAGE_HARDENING_SPEC.md`

Status: complete — Rust TUI test/coverage hardening validated; coverage remains diagnostic and no engine/search/evaluation/tuning behavior changed.

Starting baseline SHA: `1c83c40ff33fb77e9f19f6873b33561af64c9199`

Implementation Ralph-loop start SHA: `e03f7cecba304571e0bc523c3991e93b85c079da`

TUI implementation/test source SHA: `2acd49c16267e6bc7e1e38cd2626dfed70f311ac`

Objective: add reproducible `cargo llvm-cov` coverage reporting and close the highest-value Rust TUI test gaps without changing engine/search/evaluation/tuning behavior or weakening the TUI's fail-closed search-result policy.

This TODO is intended to be Ralph-loop executable. Check an item only when its implementation and evidence exist on the repository SHA being validated. Do not infer completion from nearby tests with similar names.

## Hard constraints

- [x] Do not change chess rules, legal-move semantics, search strength, evaluation, move ordering, pruning, extensions, transposition policy, opening-book policy, tuning state, or promotion disposition.
- [x] Do not add a first-legal-move fallback.
- [x] Do not add a random-legal-move fallback.
- [x] Do not silently retry at lower depth.
- [x] Do not silently swap search policy/engine implementation.
- [x] Do not add a Python runtime/engine fallback.
- [x] Do not weaken existing tests or warning/lint gates to obtain higher coverage.
- [x] Do not broadly exclude low-coverage production code from `cargo llvm-cov` reports.
- [x] Treat coverage percentage as diagnostic evidence, not a correctness proof.
- [x] Keep the existing Rust TUI manual real-terminal acceptance TODO independent; do not retroactively mark those manual items complete here.

## Phase 0 — Authority registration and baseline freeze

- [x] Record the exact `master` SHA at implementation start.
- [x] Confirm `docs/RUST_TUI_TEST_COVERAGE_HARDENING_SPEC.md` and this TODO are registered as an active follow-up program in the TODO authority index/audit.
- [x] Re-read `docs/RUST_TUI_SPEC.md` and `docs/RUST_TUI_TODO.md` before editing production code.
- [x] Confirm current `crates/chess-tui` source files and tests.
- [x] Confirm no unrelated engine/search/evaluation/tuning changes are already mixed into the working diff.
- [x] Run the existing fast/permanent-supported Rust validation appropriate for the environment and record the result.
- [x] Record the current Rust toolchain/MSRV policy.
- [x] Record the exact current `cargo-llvm-cov` version chosen for implementation/CI.
- [x] Record whether coverage uses the repository MSRV toolchain or a separate coverage host toolchain.

### Phase 0 baseline coverage

Before adding hardening tests:

- [x] Install/enable the LLVM tools component required by the chosen coverage toolchain.
- [x] Run `cargo llvm-cov clean --workspace`.
- [x] Run focused baseline coverage for `chess-tui`.
- [x] Record baseline line coverage.
- [x] Record baseline function coverage where reported.
- [x] Record baseline region coverage where reported.
- [x] Record major uncovered `chess-tui` functions/branches.
- [x] Save the exact command and tool versions used so final coverage is comparable.

### Phase 0 acceptance

- [x] Baseline source SHA and coverage summary are recorded before hardening tests materially change the numbers.
- [x] No arbitrary minimum coverage percentage has been adopted.
- [x] High-risk uncovered branches are identified explicitly rather than hidden by aggregate percentage.

## Phase 1 — Add canonical `cargo llvm-cov` developer workflow

- [x] Add a documented supported command for focused terminal coverage summary.
- [x] Add a documented supported command for LCOV output.
- [x] Add a documented supported command for optional HTML output.
- [x] Prefer a repository script/helper if that makes the invocation stable and discoverable.
- [x] Ensure the focused command runs all relevant `chess-tui` test targets.
- [x] Use `--all-features` unless the crate has a documented reason not to.
- [x] Keep coverage artifacts under `target/` or another ignored generated-artifact path.
- [x] Ensure generated LCOV/HTML files are not accidentally committed.
- [x] Document `cargo llvm-cov clean --workspace` for clean baseline/reproduction when needed.
- [x] Add a secondary workspace-wide informational coverage command only if it remains cheap and does not expand task scope.
- [x] Document that coverage tooling is development infrastructure, not a `chess-tui` runtime dependency.
- [x] Do not raise the product MSRV solely to satisfy coverage tooling.

### Canonical command acceptance

The repository must have supported equivalents of:

```bash
cargo llvm-cov clean --workspace
bash scripts/tui_coverage.sh summary
bash scripts/tui_coverage.sh lcov
cargo llvm-cov -p chess-tui --all-features --html
```

- [x] Summary command succeeds.
- [x] LCOV command succeeds and produces a nonempty report.
- [x] HTML command succeeds locally/CI where requested.
- [x] No production source file is silently excluded merely because it is difficult to test.

## Phase 2 — Deterministic search-result fallback rejection coverage (P0)

Current risk: the existing `explicit_discard_never_emits_a_playable_fallback` test proves cancellation/discard behavior, but does not directly prove the non-discarded `result.fallback().is_some()` rejection branch.

### Refactor/test seam

- [x] Identify the smallest deterministic boundary around `finish_request` result classification.
- [x] If needed, extract a pure/internal classifier that does not alter production semantics.
- [x] Keep channel delivery/worker ownership separate from result classification where practical.
- [x] Do not expose a generic fallback move to `AppState` or UI code.
- [x] Do not modify `chess-search` fallback semantics globally merely to satisfy TUI tests.

### Required tests

- [x] `fallback_only_result_is_rejected_by_tui` or equivalent.
- [x] Assert fallback-only result produces `Failed`, never `Completed`.
- [x] Assert failure message explicitly identifies TUI fallback rejection.
- [x] Assert no playable move is returned with fallback-only disposition.
- [x] Assert discard state wins over an otherwise completed/fallback result and yields cancellation.
- [x] Assert exact completed best move still yields `Completed`.
- [x] Assert search error yields `Failed` with visible message.
- [x] Assert exact move with missing required exact-iteration metrics fails closed if that state is constructible/testable.
- [x] Assert result with neither exact move nor fallback fails closed.

### Phase 2 acceptance

- [x] Coverage report proves the fallback-only rejection branch executed.
- [x] No first-legal fallback path exists in TUI code after the change.
- [x] Existing worker exact-depth and explicit-cancellation tests remain green.

## Phase 3 — `EngineRuntime` lifecycle/error coverage (P0/P1)

Directly test `EngineRuntime::drive()` and `EngineRuntime::cancel()` behavior.

### Testability seam

- [x] Determine whether current private runtime types can be tested directly inside `ui.rs`.
- [x] Prefer same-module unit tests and synthetic channels over production abstraction changes.
- [x] If deterministic spawn/join/failure injection is impossible, add the smallest internal worker seam necessary.
- [x] Production selection must still unconditionally use the real `SearchWorker`.
- [x] Do not add a runtime-configurable alternate search engine/factory.

### Required lifecycle tests

- [x] pending `SearchRequest` -> exactly one active worker starts.
- [x] Progress event updates presentation state and retains active worker ownership.
- [x] Completed final event clears/joins active worker.
- [x] Failed final event clears/joins active worker and leaves visible failure state.
- [x] Cancelled final event clears/joins active worker.
- [x] finished worker with no final event becomes explicit `Failed` state.
- [x] event-channel disconnect after worker end is not silently treated as successful completion.
- [x] `cancel()` with no active worker succeeds harmlessly.
- [x] `cancel()` with active worker requests stop/discard and joins.
- [x] cancelled worker cannot later deliver/apply a playable completion.
- [x] spawn failure clears thinking state and becomes visible.
- [x] worker panic/join failure propagates to runtime boundary.
- [x] runtime application-error handling clears thinking rather than leaving a wedged UI.
- [x] next pending search does not start while previous worker ownership remains active.
- [x] after final worker cleanup, a legitimate next search can start.

### Race/invariant tests

- [x] stale final event after game generation change is ignored.
- [x] stale progress after game generation change is ignored.
- [x] stale Failed event does not overwrite current-game status.
- [x] stale Cancelled event does not clear a current search.
- [x] at most one TUI-owned worker/search is active at a time.

### Phase 3 acceptance

- [x] Worker ownership transitions are deterministic in tests; no sleep-based luck is required for unit-level behavior.
- [x] Runtime disconnect/failure branches are visible in coverage.
- [x] No lifecycle error path silently returns success while leaving `thinking=true`.

## Phase 4 — Keyboard and overlay state-machine coverage (P1)

Add direct synthetic-key tests around `handle_key`, menu/game handlers, overlays, and confirmation execution.

### Main-menu navigation

- [x] Up at row 0 does not underflow.
- [x] Down at last row does not overflow.
- [x] Up/Down move through expected rows.
- [x] Left/Right on mode toggles Human-vs-Engine/Self-play as intended.
- [x] Enter on adjustable menu rows performs the intended adjustment.
- [x] Human color toggles White/Black.
- [x] Human engine depth decrements/increments.
- [x] Human engine depth clamps at minimum.
- [x] Human engine depth clamps at maximum.
- [x] Self-play White depth adjusts independently.
- [x] Self-play Black depth adjusts independently.
- [x] Self-play depths clamp at minimum/maximum.
- [x] Enter on Start starts exactly the selected configuration.
- [x] q from menu requests quit.
- [x] Esc from menu requests quit.

### Human move-entry editing

- [x] legal move characters append to `move_input`.
- [x] uppercase input is normalized to lowercase.
- [x] input is capped at five characters.
- [x] Backspace removes one character.
- [x] Backspace on empty input is harmless.
- [x] Esc with nonempty move input clears input and does not open MainMenu confirmation.
- [x] Enter with a legal move submits it.
- [x] Enter with malformed input leaves game state unchanged and visible error set.
- [x] Enter with well-formed illegal input leaves game state unchanged and visible error set.
- [x] shortcut-looking letters inside nonempty move input are treated as input, not shortcuts.
- [x] move characters are ignored when engine owns the turn.
- [x] move characters are ignored in Self-play mode.

### Active-game shortcuts

- [x] r opens resignation confirmation only for active Human-vs-Engine game.
- [x] r does not create resignation action in Self-play.
- [x] n opens NewGame confirmation while active.
- [x] m opens MainMenu confirmation while active.
- [x] Esc opens MainMenu confirmation when not editing move text and game is active.
- [x] q opens Quit confirmation while active.
- [x] v opens SavePath overlay.

### Confirmation overlay

- [x] y executes confirmation.
- [x] Enter executes confirmation.
- [x] n dismisses confirmation without action.
- [x] Esc dismisses confirmation without action.
- [x] unrelated keys do nothing.
- [x] Resign confirmation resolves active worker before outcome mutation.
- [x] NewGame confirmation resolves active worker before generation replacement.
- [x] MainMenu confirmation resolves active worker before session removal.
- [x] Quit confirmation resolves active worker before quit state.

### Self-play keyboard controls

- [x] Space while running pauses.
- [x] Space pause resolves active search ownership.
- [x] Space while paused resumes and schedules as appropriate.
- [x] s while paused schedules exactly one ply.
- [x] s while running does not schedule a second search.
- [x] s while already thinking does not schedule a second search.
- [x] self-play controls do not restart search after terminal outcome.

### Ctrl-C

- [x] Ctrl-C with no worker exits cleanly.
- [x] Ctrl-C with active worker cancels/joins worker before quit.
- [x] Ctrl-C clears search state.
- [x] no stale engine move can apply after Ctrl-C.

### Phase 4 acceptance

- [x] Key behavior can be tested without a real terminal.
- [x] Text-entry focus invariant is directly covered.
- [x] Abandonment confirmations are directly covered.

## Phase 5 — `AppState` defensive/error-path coverage (P1)

### Configuration validation

- [x] Human-vs-Engine depth `0` is rejected.
- [x] Human-vs-Engine depth above `MAX_MENU_SEARCH_DEPTH` is rejected.
- [x] Self-play White depth below minimum is rejected.
- [x] Self-play White depth above maximum is rejected.
- [x] Self-play Black depth below minimum is rejected.
- [x] Self-play Black depth above maximum is rejected.
- [x] valid min/max boundary depths are accepted.

### Missing/invalid session transitions

- [x] restart with no session returns visible/typed error.
- [x] mark-saved with no session returns error.
- [x] step with no session returns error.
- [x] pause with no session returns error.
- [x] resume with no session returns error.
- [x] resign with no session returns error.

### Mode/turn misuse

- [x] human move during Self-play is rejected without mutation.
- [x] human move while engine search is active is rejected without mutation.
- [x] human move when it is the engine side's turn is rejected without mutation.
- [x] resignation during Self-play is rejected visibly.
- [x] pause in Human-vs-Engine mode is rejected visibly.
- [x] resume in Human-vs-Engine mode is rejected visibly.
- [x] step in Human-vs-Engine mode is rejected.
- [x] step while self-play auto-play is running is rejected.
- [x] step while search/pending request exists is rejected.

### Terminal-state misuse

- [x] human move after game over is rejected.
- [x] resignation after game over is rejected.
- [x] resume after game over is rejected.
- [x] step after game over is rejected.
- [x] terminal state clears active search/pending/thinking/auto-play.

### Engine event defenses

- [x] current-ticket illegal engine completion is rejected and not applied.
- [x] current-ticket search failure clears active search and thinking.
- [x] current-ticket cancellation clears active search and thinking.
- [x] stale Progress ignored.
- [x] stale Completed ignored.
- [x] stale Failed ignored.
- [x] stale Cancelled ignored.
- [x] event with no session is harmless and cannot create state.

### Explicit state clearing

- [x] `cancel_search_state(None)` clears pending/active/thinking without inventing a message.
- [x] `cancel_search_state(Some(...))` clears search state and stores the requested visible message.
- [x] `return_to_menu()` clears pending/session/overlay and sets MainMenu.
- [x] `request_quit()` clears pending/overlay and sets quit.
- [x] starting a new game clears stale overlay/status/search presentation as intended.

### Phase 5 acceptance

- [x] Defensive branches produce typed/visible failures rather than silent mutation/no-op where a bug would otherwise be hidden.
- [x] Coverage shows the important misuse branches executed.

## Phase 6 — Terminal chess-state coverage (P1)

Use authoritative `chess-core` state; do not duplicate adjudication logic.

### Check/checkmate/stalemate

- [x] in-check ongoing position renders/checks `CHECK` but remains active.
- [x] checkmate through human move stops scheduling.
- [x] checkmate through engine move stops scheduling.
- [x] stalemate fixture maps to `GameOutcome::Stalemate`.
- [x] stalemate schedules no further search.

### Automatic draws

- [x] dead-position/insufficient-material fixture maps to automatic draw if represented by the core.
- [x] dead-position automatic draw schedules no further search.
- [x] add at least one additional automatic draw fixture when deterministic without corrupting hidden history state.
- [x] automatic draw result text includes the authoritative reason.

### Claimable draws

- [x] claimable threefold state remains nonterminal unless an explicit claim feature exists.
- [x] claimable fifty-move state remains nonterminal unless an explicit claim feature exists.
- [x] both-claim status renders both reasons when constructible.
- [x] claim availability does not silently stop engine scheduling unless core status is terminal.

### Formatting

- [x] `format_outcome` covers Checkmate.
- [x] `format_outcome` covers Stalemate.
- [x] `format_outcome` covers Draw.
- [x] `format_outcome` covers Resignation.
- [x] `draw_reason_name` covers ThreefoldRepetition.
- [x] `draw_reason_name` covers FivefoldRepetition.
- [x] `draw_reason_name` covers FiftyMoveRule.
- [x] `draw_reason_name` covers SeventyFiveMoveRule.
- [x] `draw_reason_name` covers DeadPosition.

### Phase 6 acceptance

- [x] Terminal-state tests demonstrate no TUI-local draw/checkmate reimplementation.
- [x] At least stalemate and one automatic draw path are directly covered.

## Phase 7 — Save UI transaction coverage (P1)

### Overlay editing

- [x] opening save overlay provides the defined default path.
- [x] printable characters append to save path.
- [x] Backspace removes one path character.
- [x] Backspace on empty path is harmless.
- [x] Esc dismisses save overlay without saving.
- [x] control characters do not enter the save path.

### Save validation/error flow

- [x] empty path fails visibly.
- [x] whitespace-only path fails visibly.
- [x] no-session save fails visibly and cannot panic.
- [x] filesystem NotFound failure remains visible.
- [x] permission-denied/read-only failure is covered where deterministic on CI; otherwise disposition explicitly.
- [x] failed save does not set `saved_path`.
- [x] failed save clears stale prior `saved_path`.
- [x] failed save never emits a success message.

### Successful save flow

- [x] successful UI save writes exact `serialize_game` output.
- [x] successful UI save records exact selected path.
- [x] successful UI save displays success.
- [x] successful UI save closes overlay.
- [x] a later move clears saved-path state.

### Serialization matrix

- [x] Human-vs-Engine / White serialization.
- [x] Human-vs-Engine / Black serialization.
- [x] Self-play serialization with distinct White/Black depths.
- [x] timestamp present.
- [x] timestamp absent.
- [x] zero moves.
- [x] multiple moves in exact order.
- [x] promotion move.
- [x] ongoing result.
- [x] checkmate result.
- [x] stalemate result.
- [x] draw result.
- [x] resignation result.
- [x] output never falsely claims PGN.

### Phase 7 acceptance

- [x] Save tests prove user-visible transaction semantics, not only `fs::write` behavior.
- [x] No save failure is silently converted into success.

## Phase 8 — Rendering/helper branch coverage (P2)

### Board/pieces/orientation

- [x] piece symbol Pawn White/Black.
- [x] Knight White/Black.
- [x] Bishop White/Black.
- [x] Rook White/Black.
- [x] Queen White/Black.
- [x] King White/Black.
- [x] White human orientation.
- [x] Black human orientation.
- [x] Self-play White orientation.
- [x] board output remains exactly 19 lines where expected.

### Move history

- [x] empty history.
- [x] one ply.
- [x] two plies.
- [x] odd multi-ply history.
- [x] even multi-ply history.

### Search metrics

- [x] no metrics -> unavailable markers, not fabricated zeroes.
- [x] fully populated metrics.
- [x] depth formatting.
- [x] positive centipawn score.
- [x] zero centipawn score.
- [x] negative centipawn score.
- [x] positive mate score.
- [x] negative mate score.
- [x] nodes formatting.
- [x] NPS formatting.
- [x] elapsed milliseconds formatting.
- [x] elapsed seconds formatting.
- [x] hash fullness formatting.
- [x] empty PV -> `-`.
- [x] nonempty PV -> ordered UCI string.

### Layout boundaries

- [x] width immediately below wide threshold.
- [x] width exactly at wide threshold.
- [x] width immediately above wide threshold.
- [x] height immediately below horizontal minimum.
- [x] height exactly at horizontal minimum.
- [x] stacked width immediately below minimum.
- [x] stacked width exactly at minimum.
- [x] stacked height immediately below minimum.
- [x] stacked height exactly at minimum.
- [x] large terminal remains supported.

### Overlay/render structural tests

- [x] resignation confirmation text renders.
- [x] new-game confirmation text renders.
- [x] menu confirmation text renders.
- [x] quit confirmation text renders.
- [x] save overlay text/path renders.
- [x] too-small message reports current and required dimensions.
- [x] no-session Game screen renders explicit safe state rather than panicking.

### Phase 8 acceptance

- [x] Prefer targeted structural assertions over huge brittle full-screen snapshots.
- [x] Coverage improvements correspond to meaningful formatting branches.

## Phase 9 — Terminal guard failure-path testability (P2)

- [x] Re-evaluate whether `TerminalGuard` failure branches justify a small internal test seam.
- [x] Do not refactor terminal lifecycle merely to increase percentage if the seam adds more complexity than confidence.
- [x] Retain real PTY launch/quit smoke regardless.

If a terminal-operations seam is introduced:

> **Disposition:** no terminal-operations seam was introduced. The checkmarks in this conditional subsection record review/disposition, not synthetic execution of an unused abstraction. Production remains directly wired to Crossterm/stdout.


- [x] production still uses Crossterm/stdout unconditionally.
- [x] raw-mode enable success + alternate-screen failure attempts raw restore.
- [x] terminal construction failure attempts required cleanup.
- [x] explicit restore attempts raw disable.
- [x] explicit restore attempts LeaveAlternateScreen even if raw disable failed.
- [x] explicit restore attempts cursor show even if an earlier cleanup step failed.
- [x] first cleanup error is preserved/returned.
- [x] successful restore marks guard restored.
- [x] Drop skips duplicate cleanup after successful explicit restore.
- [x] Drop performs best-effort cleanup after incomplete explicit restore/new lifecycle.

If no seam is introduced:

- [x] Record why PTY integration evidence plus current code structure is preferable to production abstraction solely for unit coverage.

### Phase 9 acceptance

- [x] Terminal cleanup has stronger evidence without weakening explicit restoration errors.
- [x] No `let _ = ...` on an explicit normal-path restoration result hides a failure that should be returned; Drop remains best-effort by necessity.

## Phase 10 — Coverage review and residual-gap disposition

After P0/P1/P2 tests are added:

- [x] Run `cargo llvm-cov clean --workspace`.
- [x] Run final focused TUI summary with the same configuration as baseline.
- [x] Generate LCOV artifact.
- [x] Generate/view HTML report during review if useful.
- [x] Compare baseline and final line coverage.
- [x] Compare baseline and final function coverage.
- [x] Compare baseline and final region coverage.
- [x] Identify every materially uncovered production TUI function.
- [x] Identify materially uncovered safety/error branches even inside covered functions.
- [x] Add additional tests where value is high and behavior is deterministic.
- [x] Explicitly disposition residual gaps that are impractical or lower-value.
- [x] Do not add meaningless assertions solely to move the percentage.
- [x] Do not exclude residual gaps from the report merely to improve the number.

### Coverage acceptance

- [x] Fallback-only rejection branch is covered.
- [x] `EngineRuntime` final-event/disconnect/cancel behavior is covered.
- [x] key/overlay state-machine behavior is substantially covered.
- [x] save UI transaction is covered.
- [x] stalemate/automatic draw paths are covered as specified.
- [x] residual uncovered code is understood and documented.

## Phase 11 — Permanent CI coverage integration

- [x] Choose permanent workflow/job location for focused TUI coverage.
- [x] Run coverage on Linux.
- [x] Install the required Rust LLVM tools component.
- [x] Install `cargo-llvm-cov` with a reviewed reproducible mechanism.
- [x] Record/pin the tool/action version appropriately for repository policy.
- [x] Run focused `chess-tui` coverage tests.
- [x] Print human-readable summary to CI log.
- [x] Generate LCOV artifact.
- [x] Upload LCOV artifact using GitHub Actions artifact storage if compatible with permanent CI policy.
- [x] Do not require Codecov or another external coverage account/token.
- [x] Coverage job fails if tests fail.
- [x] Coverage job fails if instrumentation/report generation fails.
- [x] Coverage job does not fail solely because an arbitrary percentage is below a threshold.
- [x] Keep existing permanent quality/robustness gates unchanged.
- [x] Keep explicit MSRV job/gate separate and green.
- [x] Ensure coverage job does not activate tuning, generated weights, or other mutable engine state.

### Phase 11 acceptance

- [x] A clean CI runner can reproduce the focused coverage report from repository configuration.
- [x] LCOV/report artifact is tied to the exact tested SHA.
- [x] No secret/token is required solely to view coverage evidence.

## Phase 12 — Full regression validation

Run on the exact intended final source SHA.

### Formatting/build/lint/tests

- [x] `cargo fmt --all -- --check`
- [x] `cargo check --locked --workspace --all-targets --all-features`
- [x] `cargo clippy --locked --workspace --all-targets --all-features -- -D warnings`
- [x] `cargo test --locked --workspace --all-targets --all-features`
- [x] `cargo test --locked -p chess-tui --all-targets --all-features`
- [x] `cargo build --locked --release -p chess-tui`

### Coverage

- [x] `bash scripts/tui_coverage.sh summary`
- [x] `bash scripts/tui_coverage.sh lcov`
- [x] LCOV output is nonempty and corresponds to the exact final SHA.

### Existing chess-engine gates

- [x] authoritative release perft remains green.
- [x] differential/core correctness remains green.
- [x] UCI smoke/tests remain green.
- [x] Miri subset remains green where permanent workflow requires it.
- [x] ASan/LSan checks remain green.
- [x] TSan cancellation/concurrency checks remain green.
- [x] fuzz/corpus gates remain green.
- [x] ARM64 workspace validation remains green where permanent workflow requires it.
- [x] explicit Rust MSRV validation remains green.

### Behavior audit

- [x] Diff against starting SHA contains no unintended `chess-core` rule changes.
- [x] Diff contains no unintended `chess-search` behavior changes.
- [x] Diff contains no evaluation-weight/search-strength changes.
- [x] Diff contains no tuning/promotion activation changes.
- [x] No first-legal fallback exists in TUI code.
- [x] No random-legal fallback exists in TUI code.
- [x] No silent depth-reduction retry exists.
- [x] No Python fallback exists.
- [x] No search failure is silently transformed into a legal-looking move.
- [x] No worker failure can silently leave the application thinking indefinitely.

## Phase 13 — Evidence and closure

- [x] Record implementation starting SHA.
- [x] Record final source SHA.
- [x] Record `cargo-llvm-cov` version.
- [x] Record coverage Rust toolchain version.
- [x] Record baseline coverage summary.
- [x] Record final coverage summary.
- [x] Record delta by line/function/region where available.
- [x] Record important residual uncovered functions/branches and disposition.
- [x] Record focused validation commands/results.
- [x] Record focused CI run IDs/jobs.
- [x] Record permanent CI run ID/jobs on exact final SHA.
- [x] Record permanent robustness run ID/jobs on exact final SHA.
- [x] Record coverage artifact identity/name on exact final SHA.
- [x] Confirm fallback-only search-result rejection test executed in permanent validation.
- [x] Confirm no silent fallback behavior was introduced.
- [x] Confirm no engine search/evaluation/tuning/promotion behavior changed.
- [x] Perform final diff audit against starting SHA.
- [x] Remove any temporary coverage/debug workflows or helper artifacts not intended to be permanent.
- [x] Reconcile TODO authority index/audit accurately.
- [x] Do not mark this TODO complete while any required P0/P1 gate remains unresolved.

## Closure evidence

- Actual implementation-loop start: `e03f7cecba304571e0bc523c3991e93b85c079da`. The older `1c83c40...` field above is retained as the planning/baseline repository identity from the document's creation history.
- Baseline focused coverage source: `22df3480227c3f0938768b70f8d2594f9881b9f5`; permanent coverage run `31276416088`, job `93150555283`, artifact `9027129674` (`chess-tui-coverage-22df3480227c3f0938768b70f8d2594f9881b9f5`). Toolchain: rustc/cargo 1.97.1, LLVM 22.1.6, `cargo-llvm-cov 0.8.7`. Baseline totals: 62.09% regions, 57.14% functions, 61.25% lines; `ui.rs` line coverage was 36.42%.
- Primary hardening source commit: `d0e7a28374d9b3465c68b16782655f5248846f27`. Final TUI source/test refinement commit: `2acd49c16267e6bc7e1e38cd2626dfed70f311ac`.
- Focused final checklist validation: run `31277368933`, job `93153050871`. It passed 86/86 `chess-tui` library tests plus all integration targets, strict Clippy, Rust 1.75 compatibility, summary/JSON/LCOV/HTML coverage generation, bounded-diff verification, and the TODO-authority audit.
- Final focused coverage totals from that run: 87.77% regions, 85.38% functions, 89.26% lines. Module line coverage: `app.rs` 95.71%, `render.rs` 96.73%, `save.rs` 100%, `ui.rs` 86.14%, `worker.rs` 90.00%, `main.rs` 0%. The comparable deltas are +25.68 region points, +28.24 function points, +28.01 line points; `ui.rs` gained +49.72 line points. No production source exclusions were added.
- Permanent coverage infrastructure pre-closure proof: SHA `a4f7b4e82112117320362d8de4305e4481ae7466`, run `31277523302`; coverage job `93153454991` and Rust 1.75 MSRV job `93153454992` both succeeded. Artifact `9027442509`, `chess-tui-coverage-a4f7b4e82112117320362d8de4305e4481ae7466`, contains text, JSON, LCOV, and HTML evidence.
- **Fallback disposition:** the TUI directly classifies a fallback-only result as `Failed`; the deterministic `fallback_only_result_is_rejected_by_tui` test covers this branch. Cancellation/discard remains earlier and cannot turn into `Completed`. No first-legal, random, lower-depth, alternate-engine, or Python fallback was added.
- **TerminalGuard disposition:** `main.rs` remains uncovered by unit-level llvm-cov because real Crossterm/stdout lifecycle behavior is better evidenced by PTY integration than by a production abstraction added solely for coverage. Existing PTY run `31227882334`, job `93025710323`, proved alternate-screen enter/leave and clean launch/quit restoration. Explicit normal-path restoration errors remain returned; only `Drop` is best-effort by necessity.
- **Permission-denied save disposition:** root/CI privilege semantics make a real `PermissionDenied` fixture nonportable. The same UI error mapping is deterministically exercised through a `NotFound` write failure, stale saved state is cleared, no success message is emitted, and real permission/read-only behavior remains part of manual terminal/filesystem acceptance. No filesystem mock layer was introduced merely to move coverage.
- Two real UI defects were found by this hardening work and fixed: control/Alt-modified printable keys could enter save-path input, and the too-small-terminal message could clip its current-dimension suffix because it did not wrap.
- The original `docs/RUST_TUI_TODO.md` manual real-terminal acceptance items remain independent and open; this hardening closure does not claim them.
- Permanent exact-final-repository-SHA run IDs are intentionally recorded out-of-band after the closure/bookkeeping commit, avoiding evidence-recursion commits whose only purpose would be to change the SHA being evidenced.

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

- [x] `cargo llvm-cov` has a documented reproducible focused TUI workflow.
- [x] Baseline and final coverage are recorded comparably.
- [x] P0 fallback rejection has deterministic direct branch coverage.
- [x] `EngineRuntime` lifecycle/error handling has direct deterministic coverage.
- [x] keyboard/input/overlay state transitions have direct coverage.
- [x] important `AppState` defensive branches have direct coverage.
- [x] stalemate and at least one authoritative automatic-draw path are covered.
- [x] save UI transaction success/failure is covered.
- [x] meaningful rendering/serialization branches are covered.
- [x] terminal cleanup retains real PTY evidence and any new failure seam is covered.
- [x] permanent CI produces a focused coverage report/artifact without arbitrary percentage gating.
- [x] existing correctness, build, lint, MSRV, perft, differential, UCI, and robustness gates remain green.
- [x] final exact SHA is validated by permanent CI/robustness evidence.
- [x] final diff contains no unintended engine/search/evaluation/tuning/promotion behavior changes.
- [x] no silent failure or forbidden fallback behavior exists.
- [x] residual coverage gaps are explicitly understood/dispositioned.
- [x] TODO authority bookkeeping is consistent and permanent audit is green.
