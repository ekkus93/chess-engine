# Rust TUI Review Fix TODO — 2026-08-09

**Status:** Not started
**Branch:** `master`
**Spec:** `docs/RUST_TUI_REVIEW_FIX_SPEC_2026-08-09.md`
**Primary tracker:** `docs/RUST_TUI_TODO.md`
**Review baseline SHA:** `97eb980ac1cec4a762d030ec0b054b3cc926bf26`
**Implementation SHA:** not yet recorded — fill in on completion.

---

## Status rules

- `[x]` means implemented, documented, tested, and supported by recorded evidence.
- `[ ]` remains incomplete.
- Every first-party formatting, compiler, Clippy, test, or build failure introduced or exposed by this pass is treated as a source defect, not a reason to weaken a gate.
- No first-party lint suppression is accepted at any point in this pass.
- This pass does not touch `chess-core`, `chess-search`, `chess-book`, or `chess-uci`.
- This pass does not perform the still-open manual real-terminal acceptance items in `docs/RUST_TUI_TODO.md` (Phase 12/13) — those remain tracked there, unchanged by this pass.

---

# RF-000: Baseline confirmation

## RF-000.1 Review context

- [x] Confirmed `docs/RUST_TUI_TODO.md` records automated implementation/regression validation as complete with only manual real-terminal acceptance open.
- [x] Confirmed two reproducible defects exist in `app.rs` (`resign_human`, `pause_self_play`) via direct code trace and, for the first, a compiled/executed reproduction.
- [x] Confirmed the Moves-pane truncation defect in `ui.rs` via direct code trace (no scroll offset on the history `Paragraph`).
- [x] Confirmed three `docs/RUST_TUI_TODO.md` Phase 4 checklist items are overclaimed or incomplete relative to the code.
- [x] Confirmed five test-coverage gaps between claimed and actually-asserted test behavior.
- [x] Confirmed `docs/RUST_WORKSPACE_ARCHITECTURE.md` omits `chess-tui` and `chess-book`.
- [x] Confirmed five lower-severity design smells (RF-006.1–8.5 in the spec).
- [x] Recorded the review baseline SHA: `97eb980ac1cec4a762d030ec0b054b3cc926bf26`.
- [x] Confirmed `cargo test -p chess-tui --all-targets` passes at the baseline SHA (102/102) — this pass must not regress that count.

## RF-000.2 Scope discipline

- [ ] Reinspected each finding immediately before implementing its fix, in case newer source already resolved it.
- [ ] Did not reopen any `docs/RUST_TUI_TODO.md` phase beyond the specific items named in RF-003/RF-004.
- [ ] Did not perform any Phase 12/13 manual real-terminal acceptance item as part of this pass.

---

# RF-001: Fix search-state corruption on rejected `resign_human`/`pause_self_play`

## RF-001.1 Fix

- [x] `resign_human` no longer mutates `pending_search`/`active_search`/`thinking` before every precondition has been validated.
- [x] `pause_self_play` no longer mutates `pending_search`/`active_search`/`thinking` before every precondition has been validated.
- [x] Preferred: both functions delegate their state-clearing to `cancel_search_state` rather than hand-rolling a partial clear.
- [x] Neither function's success-path return type or behavior changed.

## RF-001.2 Tests

- [x] A rejected `resign_human()` call leaves `pending_search`, `active_search`, and `thinking` byte-for-byte unchanged (`rejected_resign_leaves_search_state_untouched`).
- [x] A rejected `pause_self_play()` call leaves the same three fields unchanged (`rejected_pause_leaves_search_state_untouched`).
- [x] `mode_and_turn_misuse_is_rejected_without_game_mutation` extended to assert on `pending_search`/`active_search`/`thinking`, not only `session.game`.
- [x] Confirmed the reviewing agent's reproduction was accurate: both fixtures (`self_play_app()`, `human_app(Color::Black)`) start with a pending search and `thinking == true`, matching the original bug report.

## RF-001 gate

- [x] Every fallible `AppState` method validates all preconditions before mutating any field.

---

# RF-002: Fix Moves pane truncation on long games

## RF-002.1 Fix

- [ ] `render_side_panel`'s Moves pane keeps the most recent move(s) visible as the game grows, within the pane's available height (scroll-offset or tail-truncation approach — see spec section 4.2).
- [ ] `save.rs`'s serialization continues to include the full, untruncated move list, unaffected by the presentation-side fix.

## RF-002.2 Tests

- [ ] A rendering test plays enough plies to exceed the pane's line capacity at the smallest supported terminal size and asserts the most recent move pair's text is visible in the rendered buffer.
- [ ] A regression test proves `save.rs`'s serialized move list is unaffected by the pane-side fix.

## RF-002 gate

- [ ] The Moves pane shows the current tail of the game at every tested terminal size and ply count.

---

# RF-003: Correct overclaimed/incomplete `docs/RUST_TUI_TODO.md` Phase 4 items

## RF-003.1 Game-over panel/modal

- [ ] Decision recorded: implement a genuinely distinguishable game-over panel/modal, OR reword the `docs/RUST_TUI_TODO.md` line to describe the actual status-line presentation.
- [ ] If implemented: game-over result is shown via a distinguishable overlay (bordered block/title/state), consistent with `Overlay::Confirmation`/`Overlay::SavePath` rendering.
- [ ] If reworded: `docs/RUST_TUI_TODO.md`'s Phase 4 line no longer claims a panel/modal that does not exist.

## RF-003.2 Small-terminal menu guard

- [ ] `render_menu` has the same `LayoutDecision::TooSmall` handling `render_game` already has.
- [ ] `render_menu` no longer unconditionally calls `centered_rect(64, 15, ...)` below the minimum supported terminal size.

## RF-003.3 Tests

- [ ] If a game-over panel was implemented: a render test asserts its distinct presence in the buffer.
- [ ] A render test for `render_menu` at the smallest supported terminal size asserts the minimum-size message is shown, not a corrupted/panicking layout.

## RF-003 gate

- [ ] `docs/RUST_TUI_TODO.md`'s Phase 4 checklist accurately reflects the implementation for both items.
- [ ] The menu screen has the same small-terminal protection as the game screen.

---

# RF-004: Strengthen weak/tautological test coverage

## RF-004.1 Render-state content assertions

- [ ] Menu render test asserts specific expected content (e.g. mode label), not only "renders without panicking."
- [ ] Human-game render test asserts specific expected content.
- [ ] Self-play render test asserts self-play-specific text (e.g. running/paused indicator).
- [ ] Thinking-state render test asserts the "thinking…" indicator text is present in the buffer.
- [ ] None of the above removed the existing no-panic coverage.

## RF-004.2 Cancellation game-equality test

- [ ] A test spawns a real search, cancels it before completion, and asserts `session.game` is unchanged via `Game`'s `PartialEq`.

## RF-004.3 Self-play no-file-write test

- [ ] A test asserts self-play produces no filesystem writes other than through an explicit save action (temp-dir-based assertion, or a narrower code-path assertion if a filesystem-based test is impractical here — record which approach was used).

## RF-004.4 Failed-save app-level test

- [ ] A test calls the `AppState`-level save path with a failing destination and asserts `session.status_message` reflects the failure.
- [ ] The same test asserts `session.saved_path` remains `None` afterward.

## RF-004.5 PTY smoke-test decision

- [ ] Decision recorded: add a real PTY-driving test to the crate, OR correct `docs/RUST_TUI_TODO.md`'s Phase 1 line to cite only external historical CI evidence rather than implying a repository-resident test exists.
- [ ] If added: the test drives the release binary under a pseudo-terminal and asserts alternate-screen enter/leave on clean quit.
- [ ] If reworded: the TODO line no longer implies a test exists in the repository when it does not.

## RF-004 gate

- [ ] All five test-coverage gaps are closed with tests asserting the specific claimed behavior, or (RF-004.5 only) the TODO wording is corrected.

---

# RF-005: Correct stale documentation cross-reference

## RF-005.1 Fix

- [ ] `docs/RUST_WORKSPACE_ARCHITECTURE.md`'s crate table includes `chess-tui`.
- [ ] `docs/RUST_WORKSPACE_ARCHITECTURE.md`'s crate table includes `chess-book`.
- [ ] `docs/RUST_WORKSPACE_ARCHITECTURE.md`'s dependency graph reflects both additions consistently with how other adapter crates are described.

## RF-005 gate

- [ ] `docs/RUST_WORKSPACE_ARCHITECTURE.md` lists every crate in the current workspace.

---

# RF-006: Design-smell cleanup

## RF-006.1 Duplicated search-state-clear logic

- [ ] Confirmed no code path outside `cancel_search_state` mutates more than one of `pending_search`/`active_search`/`thinking` directly (post RF-001).
- [ ] Decision recorded: introduced a structurally-enforced `SearchSlot`-style type, OR confirmed convention (single helper) is sufficient for this pass.

## RF-006.2 Unnamed layout magic numbers

- [ ] `ui.rs`'s layout `Constraint`/`centered_rect` values that were tuned against `render.rs`'s named thresholds are themselves named, with a short derivation comment.

## RF-006.3 `EngineRuntime::drive` cleanup delay

- [ ] `self.active` is cleared at the point a worker-join failure is detected, not on a subsequent poll tick.
- [ ] Existing panic-path test(s) still pass and, if needed, are updated to assert immediate cleanup.

## RF-006.4 Save-path guardrails

- [ ] Decision recorded: overwrite confirmation added (reusing `Overlay::Confirmation`), and whether path-traversal sanitization was also added or explicitly deferred.
- [ ] If overwrite confirmation added: a test confirms saving to an existing path requires confirmation before it is overwritten.

## RF-006.5 Atomic save write

- [ ] `write_game` writes to a temporary file in the target directory and renames it into place, rather than truncating the target directly.
- [ ] I/O errors from either the temp-write or rename step propagate through the existing `io::Result<()>` return type.
- [ ] Existing save tests (golden serialization, successful write, failed write) still pass against the new implementation.

## RF-006 gate

- [ ] Items RF-006.1–RF-006.5 are each either fixed or explicitly deferred with a recorded reason.

---

# RF-007: Validation and closure evidence

## RF-007.1 Strict validation

- [ ] `cargo fmt --all -- --check`
- [ ] `bash scripts/dev.sh fast`
- [ ] `cargo test -p chess-tui --all-targets` (record pass count; must be ≥ the baseline's 102 passing tests plus every new test added by this pass)
- [ ] `bash scripts/dev.sh full`

## RF-007.2 Scoped-diff proof

- [ ] `git diff --stat <review-baseline-SHA> <implementation-SHA> -- crates/chess-core crates/chess-search crates/chess-book crates/chess-uci` is empty.

## RF-007.3 Evidence recorded

- [ ] Implementation SHA recorded in both this file and the companion spec.
- [ ] `docs/RUST_TUI_TODO.md`'s Phase 4/Phase 1 lines corrected per RF-003/RF-004 decisions.
- [ ] RF-003.1, RF-004.5, and RF-006.4 decisions (and reasons) recorded in the companion spec's Validation Evidence section.
- [ ] Any RF-006 sub-item explicitly deferred, and why, recorded in the companion spec.

## RF-007 gate

- [ ] The review-fix pass has exact implementation evidence, a scoped diff proof, and no unresolved first-party validation failure.

---

# Final completion checklist

- [ ] RF-000 baseline confirmation complete.
- [ ] RF-001 search-state corruption fix complete.
- [ ] RF-002 Moves pane truncation fix complete.
- [ ] RF-003 Phase 4 checklist correction complete.
- [ ] RF-004 test-coverage strengthening complete.
- [ ] RF-005 documentation cross-reference correction complete.
- [ ] RF-006 design-smell cleanup complete (or explicitly deferred per item).
- [ ] RF-007 validation and closure evidence complete.
- [ ] No changes to `crates/chess-core`, `crates/chess-search`, `crates/chess-book`, `crates/chess-uci`.
- [ ] `docs/RUST_TUI_TODO.md` Phase 12/13 manual real-terminal acceptance items remain untouched by this pass (still open, as before).

---

# Completion evidence

_Fill in on completion:_

- Implementation SHA:
- `cargo test -p chess-tui --all-targets` result:
- `bash scripts/dev.sh full` result:
- Scoped-diff proof command output:
- CI run/job IDs (if applicable):
