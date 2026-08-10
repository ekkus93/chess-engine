# Rust Android UI/UX Review Fix TODO — 2026-08-10

**Status:** proposed / not started
**Branch:** `master`
**Spec:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SPEC_2026-08-10.md`
**Primary tracker:** `docs/RUST_ANDROID_UI_UX_REDESIGN_TODO_2026-08-10.md`
**Review baseline SHA:** `98e21939b0665f2f54ade7f87cdcaba3fe48025f`

---

## Status rules

- `[x]` means implemented, documented, tested, and supported by recorded evidence.
- `[ ]` remains incomplete.
- Every first-party formatting, compiler, Clippy, lint, or test failure introduced or exposed by this pass is treated as a source defect, not a reason to weaken a gate.
- No first-party lint suppression is accepted at any point in this pass.
- This pass does not touch `crates/chess-app`, `crates/chess-search`, `crates/chess-book`, `crates/chess-uci`, `crates/chess-tui`, or `crates/chess-console`.
- This pass does not reopen `docs/RUST_ANDROID_UI_UX_REDESIGN_TODO_2026-08-10.md`'s own checkbox state, and does not perform Phase 17's still-open literal local `bash scripts/dev.sh android`/`fast` invocations or the Phase 20 physical-device UX pass — those remain tracked as open there, unchanged by this pass.
- Work one AR task at a time; each task lands in its own commit with its own tests passing before the next task begins.

---

# AR-000: Baseline confirmation

## AR-000.1 Review context

- [ ] Confirmed `docs/RUST_ANDROID_UI_UX_REDESIGN_CLOSURE_EVIDENCE_2026-08-10.md` declares the redesign complete and that the eight-pass independent review found no chess-correctness bug, no fallback/fail-open regression, and no Rust/Kotlin ownership-boundary violation.
- [ ] Confirmed one missing feature: Phase 9.1's newest-move distinction is not implemented anywhere in `GamePanels.kt`.
- [ ] Confirmed the dead `BoardLastMove` token (`Theme.kt:30`) and the literal-color leaks in `ChessPiece.kt`/`ChessBoardView.kt`.
- [ ] Confirmed "native" jargon in `SetupScreen.kt:73,75`.
- [ ] Confirmed the system-bar theming mechanism relies solely on legacy XML attributes that Android documents as deprecated/no-op under the app's own `targetSdk = 35` edge-to-edge enforcement.
- [ ] Confirmed the auto-scroll effect's ordering dependency and the busy-guard inconsistency across `restartGame`/`resign`/`submitMove`.
- [ ] Confirmed the thirteen test-coverage gaps named in the spec, most significantly the Black-orientation layout-coverage blind spot.
- [ ] Recorded the review baseline SHA: `98e21939b0665f2f54ade7f87cdcaba3fe48025f`.

## AR-000.2 Scope discipline

- [ ] Reinspected each finding immediately before implementing its fix, in case newer source already resolved it.
- [ ] Did not reopen `docs/RUST_ANDROID_UI_UX_REDESIGN_TODO_2026-08-10.md`'s checkbox state.
- [ ] Did not perform Phase 17's literal local `dev.sh android`/`fast` runs or Phase 20's physical-device pass as part of this program.

---

# AR-001: Implement the missing newest-move highlight

## AR-001.1 Fix

- [ ] Newest-ply row/column in `MoveHistoryPanel` carries a subtle, restrained visual distinction not present on other rows.
- [ ] Distinction is sourced from `rows.lastIndex`/parity against the actual `rows` list, not a separately tracked flag.
- [ ] Distinguishing color comes from a `Theme.kt` token (coordinated with AR-002), not a new literal.
- [ ] Scroll position, row layout, and numbering are unaffected.

## AR-001.2 Tests

- [ ] A rendered panel with N rows exposes the marker only on the most-recent-ply row/column.
- [ ] Appending a move moves the marker to the new row/column and removes it from the previous one.
- [ ] An empty move list renders with no marker and does not crash.

---

# AR-002: Centralize color literals; wire the dead `BoardLastMove` token

## AR-002.1 Fix

- [ ] Last-move highlight in `ChessBoardView.kt` renders from `BoardLastMove` (or a corrected definition of it), not an inline `lerp` literal.
- [ ] `PieceLightFill`/`PieceDarkFill`/`PieceLightStroke`/`PieceDarkStroke` (or equivalently named) tokens added to `Theme.kt`; `ChessPiece.kt` references them instead of literals.
- [ ] `CoordinateLabel` (or equivalently named) token added to `Theme.kt`; `ChessBoardView.kt`'s rank/file labels reference it instead of `Color.Black.copy(...)`.
- [ ] Coordinate-label token verified legible against both `BoardLight` and `BoardDark` (cross-reference AR-016's contrast test once it exists).

## AR-002.2 Tests

- [ ] A structural test asserts no `Color(0xFF...)`/`Color.Black`/`Color.White` literal remains in `ChessPiece.kt` or `ChessBoardView.kt` outside `Theme.kt`.
- [ ] Existing `BoardModelTest.kt` orientation/parity tests remain green.

---

# AR-003: Remove internal jargon from player-facing setup copy

## AR-003.1 Fix

- [ ] `SetupScreen.kt:73`'s subtitle no longer contains "native".
- [ ] `SetupScreen.kt:75`'s cleanup-required message no longer contains "native"/"Native".
- [ ] No other player-visible string literal in `android-harness/android-app/src/main/kotlin` contains "native", "JNI", "shared layer", or "architecture".

## AR-003.2 Tests

- [ ] A structural/unit test asserts the absence of "native"/"JNI" in `SetupScreen.kt`'s player-facing string literals.
- [ ] `ChessAppSemanticsInstrumentedTest.kt`/`ChessAppEndToEndInstrumentedTest.kt` updated for any changed literal-text assertions and remain green.

---

# AR-004: Verify and fix system-bar theming on target SDK 35

## AR-004.1 Fix

- [ ] Explicit `WindowCompat`/`WindowInsetsControllerCompat` call added in `MainActivity.kt` (or a dedicated theming helper) setting dark system-bar appearance under edge-to-edge.
- [ ] Existing `styles.xml` legacy attributes retained (not removed) as the pre-Compose-render fallback.
- [ ] Verified on an API 35 emulator/device (not code-inspection alone) that status/navigation bars render dark after this change.

## AR-004.2 Tests

- [ ] Instrumentation test asserts the actual system-bar appearance state is dark/non-light after `MainActivity` launches.
- [ ] Existing evidence screenshots manually re-reviewed post-fix; confirmation recorded here.

---

# AR-005: Document the board-size calculation

## AR-005.1 Fix

- [ ] Inline comment added directly above the board-size calculation in `GameScreen.kt` explaining the formula.
- [ ] `docs/RUST_ANDROID_APP.md`'s layout-structure section names the fixed constants and the shrink-before-clip policy.

## AR-005.2 Tests

- [ ] N/A — documentation-only; verified by review of the added text against the actual formula.

---

# AR-006: Document/harden the auto-scroll effect's scheduling dependency

## AR-006.1 Fix

- [ ] Inline comment added above `wasNearBottom` in `GamePanels.kt` explaining the effect-ordering dependency.
- [ ] Evaluated whether a more robust formulation is practical; either implemented it, or recorded here why the comment-plus-existing-tests approach was kept instead.

## AR-006.2 Tests

- [ ] `newestRowStaysVisibleWhenHistoryWasAtBottom` remains green.
- [ ] `newRowDoesNotStealManualHistoricalPosition` remains green.

---

# AR-007: Add busy-state guard consistency

## AR-007.1 Fix

- [ ] `restartGame()` re-checks `busy`/`cleanupRequired` before proceeding, rejecting visibly rather than silently no-oping or double-executing.
- [ ] `resign()` has the same guard.
- [ ] `submitMove()` has the same guard.
- [ ] Existing generation/ticket cancellation mechanism unchanged.

## AR-007.2 Tests

- [ ] Rapid double-invocation of `restartGame()` while busy results in exactly one logical operation.
- [ ] Same for `resign()`.
- [ ] Same for `submitMove()`.

---

# AR-008: Extract a shared, tolerance-aware layout-bounds test helper

## AR-008.1 Fix

- [ ] `bounds`/`assertContained`/`assertNoRootScroll`/`assertSquare` extracted into a single shared file (e.g. `LayoutTestSupport.kt`).
- [ ] `ChessAppLayoutInstrumentedTest.kt` and `ChessAppAdaptiveLayoutInstrumentedTest.kt` updated to use the shared helper, private duplicates removed.
- [ ] Explicit small tolerance constant introduced and applied to containment/equality comparisons.

## AR-008.2 Tests

- [ ] All prior callers continue to pass with unchanged assertions.
- [ ] A test proves two bounds within tolerance are treated equal, and two bounds outside tolerance are treated different.

---

# AR-009: Add Black-orientation layout/containment/spatial-stability coverage

## AR-009.1 Fix

- [ ] Black-orientation variant of the 360×640dp compact-layout containment test added.
- [ ] Black-orientation spatial-stability assertion added (at minimum idle and thinking states).

## AR-009.2 Tests

- [ ] New tests verified to fail if `humanSide` fixture wiring is reverted to White (implementation-time sanity check, not a permanent test).

---

# AR-010: Add board/action-row bounds-stability across tab switches

## AR-010.1 Fix

- [ ] Test captures `chess-board`/`game-actions` bounds before a tab click and asserts unchanged after, using the AR-008 helper.

## AR-010.2 Tests

- [ ] New test verified to fail against a deliberately-reverted fixed-height regression (implementation-time sanity check).

---

# AR-011: Add a functional promotion-dialog test

## AR-011.1 Fix

- [ ] Instrumentation test renders `PromotionDialog` with a real `onChoose` callback, clicks each of the four options, asserts the captured move string is correct for each.
- [ ] End-to-end promotion flow test added if a deterministic fixture/path is practical (or documented here why not practical).

## AR-011.2 Tests

- [ ] N/A — the tests above are this task's deliverable.

---

# AR-012: Add a functional error-dialog test

## AR-012.1 Fix

- [ ] Instrumentation test renders `ChessEngineErrorDialog` with a known message, asserts the text is present, clicks dismiss, asserts the expected callback/state-clear behavior and no other side effect.

## AR-012.2 Tests

- [ ] N/A — the test above is this task's deliverable.

---

# AR-013: Add engine-metrics content-rendering test

## AR-013.1 Fix

- [ ] Full-metrics test asserts each formatted metric value renders as visible text.
- [ ] Partial-metrics test asserts present fields show real values and absent fields show `"—"`, not fabricated zeros.

## AR-013.2 Tests

- [ ] N/A — the tests above are this task's deliverable.

---

# AR-014: Add Setup-title test tag and visibility test

## AR-014.1 Fix

- [ ] `testTag("setup-title")` (or equivalent) added to the Setup title composable.
- [ ] Title tag added to the existing `assertContained("setup-screen", ...)` child list.

## AR-014.2 Tests

- [ ] Extended containment assertion passes; rendered title text matches expected copy (coordinate with AR-003).

---

# AR-015: Add busy-state layout-stability tests

## AR-015.1 Fix

- [ ] Setup-screen busy-state test: bounds of side selector/depth control/Start Game unchanged vs. non-busy; disabled semantics correct.
- [ ] Game-screen busy-state test: `game-actions` bounds unchanged vs. non-busy; Resign disabled-semantics correct for both `busy` and `gameOver`.

## AR-015.2 Tests

- [ ] N/A — the tests above are this task's deliverable.

---

# AR-016: Add automated contrast validation

## AR-016.1 Fix

- [ ] JVM unit test computes WCAG contrast ratio for each named token pair (see spec §18.2) and asserts each meets its threshold.
- [ ] Any failing pair's token value adjusted in `Theme.kt`; before/after values recorded here.

## AR-016.2 Tests

- [ ] N/A — the unit test above is this task's deliverable; it runs as part of the app's normal unit-test step.

---

# AR-017: Add Rust SAN piece-capture and capture-promotion coverage

## AR-017.1 Fix

- [ ] Piece-capture SAN test added (e.g. `Nxe5`) against a hand-verified real position.
- [ ] Disambiguation-plus-capture SAN test added (e.g. `Ndxe4`).
- [ ] Capture-promotion SAN test added (e.g. `exd8=Q`), with a check/mate variant if practical.

## AR-017.2 Tests

- [ ] Every new test's expected SAN string hand-verified against real chess legality before being accepted.

---

# AR-018: Add Kotlin snapshot-parser negative-path unit tests

## AR-018.1 Fix

- [ ] Wrong-field-count input asserted to throw `IllegalArgumentException`.
- [ ] Correct-field-count-wrong-version input asserted to throw the same.
- [ ] Missing/corrupted-terminator input asserted to throw the same.

## AR-018.2 Tests

- [ ] N/A — the three tests above are this task's deliverable.

---

# AR-019: Add a static Rust↔Kotlin high-level snapshot contract test

## AR-019.1 Fix

- [ ] `crates/chess-jni/tests/jni_contract.rs` extended (or a sibling test added) to statically assert `ChessGame.kt`'s `FIELD_COUNT`/`VERSION` match `app_bridge.rs`'s `SNAPSHOT_VERSION`/encoded field-array length.

## AR-019.2 Tests

- [ ] New contract test verified to fail if `SNAPSHOT_VERSION` or `FIELD_COUNT`/`VERSION` are deliberately desynced (implementation-time sanity check).

---

# AR-020: Add a portrait rotation-attempt instrumentation test

## AR-020.1 Fix

- [ ] Instrumentation test starts a game, captures state, issues a rotation request via `uiautomator` (dependency addition justified here if newly added), asserts orientation stays portrait and game state is unchanged — **or** documents the specific CI-emulator blocker preventing this and falls back to asserting the manifest/runtime lock is sufficient.

## AR-020.2 Tests

- [ ] N/A — the test (or documented fallback) above is this task's deliverable.

---

# AR-021: Final validation and closure

## AR-021.1 Validation

- [ ] Android app JVM/unit tests pass, including every test added by AR-001 through AR-020.
- [ ] Android lint passes.
- [ ] `crates/chess-core` tests pass, including AR-017's additions.
- [ ] `crates/chess-jni` tests pass, including AR-019's extended contract test.
- [ ] Full Android instrumentation suite passes, including every test added by this pass.
- [ ] `bash scripts/dev.sh fast` passes.

## AR-021.2 Closure evidence

```text
Implementation start SHA:
Final source SHA:

Android app unit/lint results:
chess-core test results:
chess-jni test results:
Android instrumentation results:
bash scripts/dev.sh fast result:
```

## AR-021 acceptance

- [ ] Every AR-001 through AR-020 task is `[x]` with its own recorded test evidence.
- [ ] No first-party lint suppression was added anywhere in this pass.
- [ ] No existing green test was weakened or deleted to obtain a green run.
- [ ] This document's Status header updated to `Complete` only once all of the above holds.
