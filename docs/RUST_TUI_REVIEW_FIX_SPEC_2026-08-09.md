# Rust TUI Review Fix Spec — 2026-08-09

**Status:** Not started
**Branch:** `master`
**Companion TODO:** `docs/RUST_TUI_REVIEW_FIX_TODO_2026-08-09.md`
**Primary tracker:** `docs/RUST_TUI_TODO.md`
**Review baseline SHA:** `97eb980ac1cec4a762d030ec0b054b3cc926bf26`
**Implementation SHA:** not yet recorded — fill in on completion.

---

## 1. Purpose

`docs/RUST_TUI_TODO.md` records automated implementation and permanent regression validation as complete for the `chess-tui` crate, with only manual real-terminal acceptance left open. A subsequent independent code review (six parallel module-scoped passes covering `app.rs`, `worker.rs`, `render.rs`/`ui.rs`, `save.rs`/`main.rs`/crate setup, the integration test suite, and the documentation/evidence trail) found that automated closure was not fully sound:

1. Two reproducible defects in `app.rs` that violate the "reject visibly without mutation" invariant the rest of the file upholds.
2. Three `docs/RUST_TUI_TODO.md` checklist items that are checked `[x]` but do not fully hold up against the code (an overclaimed game-over modal, a missing small-terminal guard on the menu screen, and a claimed PTY smoke-test artifact that does not exist in the repository).
3. Five test-coverage gaps where a checked-off "test" claim is either a panic-only smoke test with no content assertion, or tests a narrower thing than it claims.
4. A stale documentation cross-reference.
5. Five lower-severity design smells worth cleaning up while this crate is still young: duplicated search-state-clear logic, unnamed layout magic numbers, a one-tick cleanup delay on the worker-panic path, unguarded user-supplied save paths, and a non-atomic save write.

This pass fixes all of the above. It does not touch engine, search, or evaluation behavior, does not perform the still-open manual real-terminal acceptance items in `docs/RUST_TUI_TODO.md` (Phase 12/13), and does not reopen any already-closed phase of that document beyond correcting the specific overclaimed/weak items named here.

---

## 2. Engineering constraints retained

- `chess-core` and `chess-search` remain untouched by this pass; the scoped diff must contain zero changes to `crates/chess-core`, `crates/chess-search`, `crates/chess-book`, `crates/chess-uci`.
- `chess-tui` continues to forbid unsafe code (`#![forbid(unsafe_code)]` in `main.rs`/`lib.rs` unchanged).
- The "no fallback move" guarantee (`worker.rs`'s `result.completed().best_move()` discipline, the `SearchTicket` staleness check in `app.rs`) is not weakened by any change in this pass — RF-001 tightens the surrounding state machine, it does not touch the fallback-rejection logic itself.
- No first-party lint suppression (`allow`/`expect`) is added anywhere in this pass.
- No new production dependency is added without explicit justification recorded in this spec.
- Workspace lint configuration (`[lints] workspace = true`) remains applied to `chess-tui`.
- `docs/RUST_TUI_TODO.md` itself is corrected in place (three checklist items reworded/unchecked as appropriate) rather than superseded — it remains the primary implementation-history record for this crate.

---

## 3. RF-001 — Fix search-state corruption on rejected `resign_human`/`pause_self_play`

### 3.1 Defect

`crates/chess-tui/src/app.rs`:

- `resign_human` (around line 393) unconditionally executes `self.pending_search = None;` as its first statement, before validating that resignation is legal in the current mode/state.
- `pause_self_play` (around line 418) has the identical structure: `self.pending_search = None;` first, mode validation second.

In both functions, `session.active_search`/`session.thinking` are only cleared later, on the success path. If the precondition check subsequently fails (`resign_human` called outside Human-vs-Engine mode or with no active human color; `pause_self_play` called outside self-play mode), the function correctly returns `Err(AppError)`, but `pending_search` has already been discarded while `active_search`/`thinking` remain set. Because `schedule_if_needed` refuses to schedule while `session.thinking` is `true`, the session becomes permanently stuck "thinking" with no request left for the runtime to act on.

This is not reachable through the shipped keyboard-handling path today — `ui.rs` gates `pause_self_play` behind an `if self_play` check and always calls `cancel_search_state` before dispatching to `resign_human` via `execute_confirmation` — but the public `AppState` API itself is unsound, and every other fallible method in `app.rs` (`submit_human_move`, `resume_self_play`, `step_self_play`, `restart_current_game`) validates before mutating.

### 3.2 Required fix

- Reorder both functions so no field is mutated before every precondition has been checked, **or** — the preferred fix, since it also removes the duplication flagged in RF-006.1 — have both functions delegate their state-clearing to the existing correct helper (`cancel_search_state`) only after validation succeeds, instead of hand-rolling a partial clear.
- The fix must not change either function's success-path behavior or return type.

### 3.3 Required tests

Extend `crates/chess-tui/src/app/hardening_tests.rs`:

- A rejected `resign_human()` call (wrong mode, or self-play with a pending/active search already scheduled) leaves `pending_search`, `active_search`, and `thinking` byte-for-byte unchanged from their pre-call values.
- A rejected `pause_self_play()` call (Human-vs-Engine mode, with a pending/active search already scheduled) leaves the same three fields unchanged.
- Extend the existing `mode_and_turn_misuse_is_rejected_without_game_mutation` test (or add a sibling) to assert on `pending_search`/`active_search`/`thinking` in addition to `session.game` — this is the test gap the review identified as the reason the original bug shipped uncaught.

### RF-001 gate

- [ ] Every fallible `AppState` method validates all preconditions before mutating any field, with a passing regression test per function that previously violated this.

---

## 4. RF-002 — Fix Moves pane truncation on long games

### 4.1 Defect

`crates/chess-tui/src/ui.rs`, `render_side_panel`: the full move-history string (`format_move_history(session.game.moves())`) is rendered into a `Paragraph` with `Wrap { trim: false }` and no `.scroll(...)` offset. Ratatui's `Paragraph` always renders from the top of its text and clips whatever doesn't fit — there is no "last N moves" slicing or scroll-tracking anywhere in `ui.rs`/`render.rs`.

At the minimum supported terminal size (80×32), the Moves pane has room for roughly 8-9 lines of move-pair text. Past that point in any game — normal play reaches it quickly, and self-play mode runs unattended well past it — the pane freezes on the earliest moves of the game and never again reflects the current position. No existing test exercises a game long enough to catch this; the longest test fixtures are 3-4 plies.

### 4.2 Required fix

`render_side_panel` must keep the most recent move(s) visible as the game grows, within the pane's available height. Acceptable approaches, in order of preference:
1. Compute a scroll offset from the rendered pane height and the number of move-history lines, so the `Paragraph` always shows the tail of the move list (mirrors what a terminal chess UI user expects — "what just happened" stays visible).
2. If (1) is judged too invasive for this pass, truncate `format_move_history`'s output for the side panel specifically to the last N move-pairs that fit the pane, with an indicator (e.g. a leading `…`) that earlier moves exist.

Either approach must not change `save.rs`'s serialization, which must continue to include the full, untruncated move list — this defect and its fix are presentation-only.

### 4.3 Required tests

- A rendering test that plays enough plies (at minimum, enough to exceed the pane's line capacity at the smallest supported terminal size, e.g. 15+ plies at 80×32) and asserts, via buffer inspection, that the **most recent** move pair's text appears in the rendered Moves pane.
- A regression test proving `save.rs`'s serialized move list is unaffected by any pane-side truncation/scrolling logic (i.e. the fix lives in `ui.rs`/`render.rs` presentation code, not in data shared with `save.rs`).

### RF-002 gate

- [ ] The Moves pane shows the current tail of the game at every tested terminal size and ply count, verified by a buffer-inspecting test with a realistic ply count.

---

## 5. RF-003 — Correct overclaimed and incomplete `docs/RUST_TUI_TODO.md` Phase 4 items

### 5.1 Findings

- **"Implement game-over panel/modal" (Phase 4)** is checked `[x]`, but no dedicated panel or modal exists. Game-over text is rendered through the same status `Paragraph` used for ordinary turn status (`turn_status()` → `format_outcome()`), not a distinguishable panel (no `Clear`, no separate bordered block, no distinct title/state).
- **"For unusably small terminals, render a minimum-size message instead of panicking or corrupting layout" (Phase 4)** is checked `[x]`, but this is only implemented for the Game screen (`render_game`'s `LayoutDecision::TooSmall` branch). `render_menu` has no small-terminal guard at all and unconditionally calls `centered_rect(64, 15, frame.size())`.

### 5.2 Required fix

Choose and implement one of the following for each finding, then correct the TODO line to match reality:

- **Game-over panel**: either (a) implement a genuinely distinguishable game-over panel/modal (a bordered overlay block, consistent with how `Overlay::Confirmation`/`Overlay::SavePath` are already rendered), and keep the checklist item checked because it is now true, or (b) if the team decides the current status-line presentation is an intentional, sufficient design, reword the `docs/RUST_TUI_TODO.md` line to describe what is actually implemented ("game-over result is shown in the status area," not "panel/modal") so the checklist stops overclaiming. Record which choice was made and why in this spec's completion section.
- **Small-terminal menu guard**: add the same `LayoutDecision::TooSmall` handling to `render_menu` that `render_game` already has, so the menu screen never attempts `centered_rect(64, 15, ...)` below the minimum supported size.

### 5.3 Required tests

- If a real game-over panel is implemented: a render test asserting the panel's distinct presence (bordered block, title, or similar) in the buffer, separate from the ordinary in-game status assertions.
- A render test for `render_menu` at the smallest supported terminal size, asserting the minimum-size message (not a corrupted/panicking menu layout) is shown — mirroring the existing `render_game` small-terminal tests.

### RF-003 gate

- [ ] `docs/RUST_TUI_TODO.md`'s Phase 4 checklist accurately reflects the implementation for both items, and the menu screen has the same small-terminal protection as the game screen.

---

## 6. RF-004 — Strengthen weak/tautological test coverage

### 6.1 Findings

The review found five specific gaps between what `docs/RUST_TUI_TODO.md` claims a test proves and what the actual test asserts:

1. **Render tests for menu/human-game/self-play/thinking states** (Phase 4 tests) are panic-only smoke tests (`.expect("render succeeds")`) with no assertion on rendered content — in contrast to the game-over/error and small-dimension tests, which do inspect the buffer.
2. **"Cancellation does not mutate the game after abandonment"** (Phase 6/9 tests) is correct by code inspection (no test found a counter-example), but no test directly clones `session.game` before and after a genuine cancellation and asserts equality, the way the equivalent human-move and engine-completion tests already do.
3. **"No tuning/evaluation files are written by self-play TUI mode"** (Phase 9 tests) is structurally true (no filesystem writes exist outside the explicit save action) but is not asserted by any test — it is an architectural inference, not a checked claim.
4. **"Failed write remains visible and does not set Saved state"** (Phase 10 tests) is only tested at the `write_game`/`fs::write` level (a missing-parent-directory error propagates), not at the `AppState`/UI integration level the claim describes — no test calls `save_current_game`/`mark_save_failed` and asserts `session.saved_path.is_none()` plus a visible status message afterward.
5. **"Launch/quit smoke test restores the shell terminal correctly."** (Phase 1 tests/gates) has no corresponding test, script, or workflow step in the current repository tree — the only evidence is prose referencing historical, non-reproducible CI run/job IDs. See RF-005 for the documentation-side correction; this item tracks whether an actual reproducible test should be added.

### 6.2 Required fix

Add or strengthen tests for each of the five items above:

1. Add buffer-content assertions to the menu/human-game/self-play/thinking render tests (e.g. assert the mode label, "thinking…" indicator text, or self-play running/paused text actually appears), without removing their existing no-panic coverage.
2. Add a test that spawns a real search, cancels it before completion, and asserts `session.game` is unchanged via `Game`'s `PartialEq` (matching the pattern already used for human-move and engine-completion transactional tests).
3. Add a test that runs a short self-play sequence in a temporary/isolated working directory and asserts no files were created other than through an explicit save action (or, if a temp-dir-based filesystem assertion is impractical for this crate's test harness, add a narrower unit test that self-play code paths never call any `save`/`fs` function — grep-based or type-based, whichever is more idiomatic here).
4. Add a test that calls the `AppState`-level save path with a failing destination and asserts both `session.status_message` reflects the failure and `session.saved_path` remains `None` afterward.
5. Decide and record one of: (a) add a real PTY-driving test (e.g. via a `portable-pty`-style harness) to the crate, matching what the historical CI evidence claims was once done, or (b) if that is judged out of scope for this pass, correct `docs/RUST_TUI_TODO.md`'s Phase 1 line to cite only the historical CI run/job IDs as external evidence rather than implying a repository-resident test exists.

### RF-004 gate

- [ ] All five test-coverage gaps are closed with tests that assert the specific behavior the corresponding TODO line claims, or (for item 5 only) the TODO wording is corrected to match what evidence actually exists.

---

## 7. RF-005 — Correct stale documentation cross-reference

### 7.1 Finding

`README.md` points readers to `docs/RUST_WORKSPACE_ARCHITECTURE.md` for "Dependency direction and crate ownership." That file predates the `chess-tui` milestone and does not mention `chess-tui` (or `chess-book`) anywhere in its crate table or dependency graph, even though the TUI-crate relationship is otherwise well documented elsewhere (`README.md` itself, `docs/RUST_TUI_IMPLEMENTATION.md`).

### 7.2 Required fix

Update `docs/RUST_WORKSPACE_ARCHITECTURE.md`'s crate table and dependency graph to include `chess-tui` (and `chess-book`, which is also currently missing), consistent with how the other adapter crates are already described there.

### RF-005 gate

- [ ] `docs/RUST_WORKSPACE_ARCHITECTURE.md` lists every crate in the current workspace, including `chess-tui` and `chess-book`.

---

## 8. RF-006 — Design-smell cleanup

These are lower-severity than RF-001–RF-005; none of them are confirmed bugs, but all were flagged as real maintainability or latent-risk concerns worth addressing while the crate is small.

### 8.1 Duplicated search-state-clear logic

`cancel_search_state` correctly clears `pending_search`, `active_search`, and `thinking` together as a single unit. `resign_human` and `pause_self_play` each hand-roll a partial version of the same clear instead of calling it (this duplication is also the root cause of RF-001). Fix: after RF-001, confirm no code path outside `cancel_search_state` mutates more than one of these three fields directly; if a small owned type (e.g. a `SearchSlot` struct whose only mutator is `clear()`) makes this structurally enforced rather than convention-enforced, prefer that.

### 8.2 Unnamed layout magic numbers in `ui.rs`

`render.rs` names its layout thresholds (`MIN_TERMINAL_WIDTH`, `WIDE_TERMINAL_WIDTH`, `MIN_TERMINAL_HEIGHT`, `STACKED_MIN_TERMINAL_HEIGHT`), but `ui.rs` inlines the actual `Constraint`/`centered_rect` values that were tuned against those thresholds as bare literals (`Constraint::Length(44)`, `Percentage(60)/Percentage(40)`, the `Length(3), Min(10), Length(5), Length(3)` outer stack, `centered_rect(64, 15, …)`, `centered_rect(56, 9, …)`). Fix: name these constants in `ui.rs` (or co-locate them with `render.rs`'s constants) with a short comment on how each was derived, so a future change to the `render.rs` thresholds has a visible signal to also check `ui.rs`.

### 8.3 `EngineRuntime::drive` one-tick cleanup delay on worker panic

When `active.worker.join()` fails inside `drive()`'s "no final event" branch, the `?` short-circuits before `self.active` is cleared, leaving a defunct `ActiveWorker` occupying the "at most one active search" slot until the *next* `drive()` call re-detects it and cleans up. `thinking` is still cleared immediately by the caller (`run()`'s error handler), so this is a scheduling-latency wart, not a correctness bug. Fix: clear `self.active` at the point the join failure is detected, not on a subsequent poll.

### 8.4 Unsanitized/unconfirmed save paths

`save_current_game` passes user-typed `path_text` straight to `Path::new`/`fs::write` with no path-traversal guard and no overwrite confirmation. For a local single-user TUI where the user types their own destination this is a defensible design, but there is currently zero guardrail — a typo can silently overwrite an unrelated file the process can write to. Fix: at minimum, add an overwrite confirmation when the target path already exists (reusing the existing `Overlay::Confirmation` mechanism), matching the confirmation pattern already used for resignation/abandonment. Path-traversal sanitization is optional for this pass — record the decision either way in the completion section.

### 8.5 Non-atomic save write

`write_game` performs a direct `fs::write` (truncate-in-place, no `fsync`) rather than a write-to-temp-then-rename. Low practical risk for a small single-writer text file, but worth the standard hardening given the crate otherwise holds itself to a high correctness bar. Fix: write to a temporary file in the same directory as the target, then rename it into place, propagating any I/O error from either step through the existing `io::Result<()>` return type.

### RF-006 gate

- [ ] Items 8.1–8.5 are each either fixed or explicitly deferred with a recorded reason in this spec's completion section.

---

## 9. Completion criteria

This pass is complete when:

- RF-001 through RF-006 gates are all satisfied (or explicitly, individually deferred with a recorded reason for RF-006 sub-items only — RF-001 through RF-005 are not deferrable).
- The scoped diff between the review baseline SHA and the implementation SHA contains zero changes to `crates/chess-core`, `crates/chess-search`, `crates/chess-book`, `crates/chess-uci`.
- `docs/RUST_TUI_TODO.md`'s Phase 4 and Phase 1 lines corrected by RF-003/RF-004 accurately describe the implementation.
- The following pass on the exact implementation SHA:
  - [ ] `bash scripts/dev.sh fast`
  - [ ] `cargo test -p chess-tui --all-targets`
  - [ ] `bash scripts/dev.sh full`
- No first-party lint suppression was added.
- This pass's own manual/design decisions (game-over panel vs. status-line wording per RF-003.2, path-sanitization scope per RF-006.4) are recorded below with the choice made and why.

---

## 10. Validation evidence

_Fill in on completion:_

- Implementation SHA:
- `bash scripts/dev.sh fast` result:
- `cargo test -p chess-tui --all-targets` result (pass/fail counts):
- `bash scripts/dev.sh full` result:
- CI run/job IDs (if applicable):
- RF-003.2 decision (game-over panel implemented vs. TODO reworded) and reason:
- RF-004.5 decision (PTY test added vs. TODO reworded) and reason:
- RF-006.4 decision (overwrite confirmation only vs. also path sanitization) and reason:
- Any RF-006 sub-item explicitly deferred, and why:
