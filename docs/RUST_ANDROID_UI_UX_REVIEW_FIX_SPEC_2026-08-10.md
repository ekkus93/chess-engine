# Rust Android UI/UX Review Fix Spec — 2026-08-10

**Status:** proposed / not started
**Branch:** `master`
**Companion TODO:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md`
**Primary tracker:** `docs/RUST_ANDROID_UI_UX_REDESIGN_TODO_2026-08-10.md`
**Closure evidence under review:** `docs/RUST_ANDROID_UI_UX_REDESIGN_CLOSURE_EVIDENCE_2026-08-10.md`
**Review baseline SHA:** `98e21939b0665f2f54ade7f87cdcaba3fe48025f`

---

## 1. Purpose

`docs/RUST_ANDROID_UI_UX_REDESIGN_CLOSURE_EVIDENCE_2026-08-10.md` declares the Android UI/UX redesign program complete. An independent post-closure code review — eight parallel passes covering the Rust SAN formatter, the JNI snapshot protocol, and every Android/Compose subsystem named in `docs/RUST_ANDROID_UI_UX_REDESIGN_TODO_2026-08-10.md` (Phases 1–22) — found the closure to be substantively sound: no chess-correctness bug, no fallback/fail-open regression, and no Rust/Kotlin ownership-boundary violation anywhere in the shipped code. It also found:

1. One confirmed missing feature relative to an explicit checklist bullet (Phase 9.1's newest-move distinction).
2. Five design/consistency defects: a dead design-token, two files with color literals leaking outside the theme layer, internal architecture jargon leaking into player-facing copy, and a system-bar theming mechanism that is very likely non-functional on the app's own target SDK.
3. Two minor code-hardening items: an auto-scroll effect whose correctness depends on an undocumented Compose scheduling assumption, and three ViewModel methods that skip the busy-state re-check pattern used elsewhere.
4. Thirteen test-coverage gaps, the largest of which is that every automated layout/containment/spatial-stability test in the suite exercises only the White board orientation — the Black-oriented board has zero automated layout coverage despite being a materially different render.

This pass fixes the confirmed bug and design defects, hardens the two code-smell items, and closes every identified test-coverage gap. It does not reopen `docs/RUST_ANDROID_UI_UX_REDESIGN_TODO_2026-08-10.md`'s own checkbox state (that document remains superseded for shipped-state authority by the closure-evidence document, per `docs/LEGACY_TODO_INDEX.md`'s existing convention) and it does not perform Phase 17's still-open literal local `bash scripts/dev.sh android`/`fast` invocations or the Phase 20 physical-device UX pass — both remain honestly disclosed as open in the closure-evidence document and are outside this pass's scope.

---

## 2. Engineering constraints retained

- `chess-core`'s rules/SAN authority and `chess-search`'s search/evaluation authority are not touched behaviorally by this pass. `crates/chess-core/src/san.rs` gains additional tests only (AR-017); no formatting behavior changes.
- Rust remains authoritative for chess rules, legality, opening-book selection, and SAN generation. No task in this pass adds chess-rule, legality, disambiguation, or opening-book logic to Kotlin.
- The Android interactive fail-closed policy is not weakened: no task in this pass adds a random/first-legal fallback, silent retry, silent depth reduction, fake/default snapshot, or alternate engine path.
- The existing one-second post-human-move reveal delay, portrait-only lock, and no-root-page-scroll invariants are preserved exactly; no task changes their behavior, only their test coverage or presentation polish.
- No first-party lint suppression (`allow`/`expect`, Kotlin `@Suppress`) is added anywhere in this pass.
- No new production dependency is added without explicit justification recorded in this spec. AR-016's contrast check and AR-009/AR-010/AR-013's layout assertions must be built from existing `androidx.compose.ui:ui-test-junit4`/JVM-unit-test capability already present in the project; no new test dependency is introduced without being named here first.
- This pass touches: `android-harness/android-app/src/main/kotlin/**`, `android-harness/android-app/src/{test,androidTest}/kotlin/**`, `crates/chess-core/src/san.rs` (tests only), `crates/chess-jni/kotlin/**` (tests only), `crates/chess-jni/tests/jni_contract.rs`, and this spec/TODO pair. It does not touch `crates/chess-app`, `crates/chess-search`, `crates/chess-book`, `crates/chess-uci`, `crates/chess-tui`, or `crates/chess-console`.
- `docs/RUST_ANDROID_UI_UX_REDESIGN_TODO_2026-08-10.md` and `docs/RUST_ANDROID_UI_UX_REDESIGN_CLOSURE_EVIDENCE_2026-08-10.md` are left as historical/closure records and are not edited by this pass except where AR-021 records this pass's own closure evidence in a new document.
- Existing passing tests are not weakened or deleted to obtain a green run; every currently-green assertion named in the review remains green after this pass.

---

## 3. AR-001 — Implement the missing newest-move highlight in the Moves tab

### 3.1 Defect

`docs/RUST_ANDROID_UI_UX_REDESIGN_TODO_2026-08-10.md` Phase 9.1 explicitly requires: "Visually distinguish newest move subtly." No code in `GamePanels.kt`'s `MoveHistoryPanel` row-rendering loop (`GamePanels.kt:75-107`) checks whether a row is the most recent one; no weight, tint, or marker differs for the latest move. The board's separate last-move square highlight does not satisfy this bullet — it is a different surface (the board, not the Moves-tab row list).

### 3.2 Fix

- Add a subtle, restrained visual distinction (e.g. an accent-tinted background or accent-colored text weight on the newest row's active column) to the row in `MoveHistoryPanel` corresponding to the most recently played ply.
- Source the "newest" determination from the row/column index against `rows.lastIndex`/parity, not from a separately tracked mutable flag that could desync from `rows`.
- Use an existing or newly added `Theme.kt` token for the distinguishing color rather than a new literal (coordinate with AR-002).
- Must not change scroll position, row layout, or numbering — purely a presentation change to the affected cell(s).

### 3.3 Tests

- A rendered `MoveHistoryPanel` with N rows exposes a distinguishable semantic/visual marker on the row/column holding the most recent ply and not on any other row.
- Appending a new move moves the marker to the new row/column and removes it from the previous one.
- An empty move list renders with no marker and does not crash.

---

## 4. AR-002 — Centralize board/piece color literals; wire the dead `BoardLastMove` token into real rendering

### 4.1 Defect

`Theme.kt:30` defines `BoardLastMove` as a dedicated semantic token to satisfy Phase 1.1's "last-move ... semantic colors" requirement, but it is never referenced anywhere in the codebase — confirmed independently by two review passes. The actual last-move highlight is computed ad hoc at `ChessBoardView.kt:66` via `lerp(baseColor, PrimaryStrong, 0.30f)`, which means the "last-move color" is not actually one color; it renders differently depending on whether the tinted square is light or dark.

Separately, `ChessPiece.kt:25-26` hard-codes piece fill/stroke colors (`Color(0xFFF7F3EA)`, `Color(0xFF172033)`, `Color(0xFF26364D)`, `Color(0xFFE8EEF7)`) and `ChessBoardView.kt:131,142` hard-codes the rank/file coordinate-label color (`Color.Black.copy(alpha = 0.58f)`) — both outside `Theme.kt`, contradicting the "no major composable owns duplicated hard-coded product colors" acceptance bullet. The coordinate-label case is also a plausible legibility risk: a fixed near-black label at 58% alpha has materially different contrast against `BoardDark` (`#806A58`) than against `BoardLight` (`#E7D7C4`), and nothing today verifies both remain legible.

### 4.2 Fix

- Rewire the last-move highlight in `ChessBoardView.kt` to use `BoardLastMove` (or a corrected definition of it) as the actual rendered color, removing the ad hoc `lerp` computation — or, if a lerp-based blend is kept for visual reasons, derive its target color from a named token rather than an inline literal, and update `BoardLastMove`'s definition to match what actually renders.
- Add `PieceLightFill` / `PieceDarkFill` / `PieceLightStroke` / `PieceDarkStroke` (or equivalently named) tokens to `Theme.kt` with the same hex values `ChessPiece.kt` currently hard-codes, and reference them from `ChessPiece.kt` instead of literals.
- Add a `CoordinateLabel` (or equivalently named) token to `Theme.kt` for the rank/file label color, replacing the raw `Color.Black.copy(alpha = ...)` literal in `ChessBoardView.kt`.
- Verify by inspection (and record in the TODO) that the label color token maintains reasonable contrast against both `BoardLight` and `BoardDark`; adjust the token's alpha/hue if the two are not comparably legible.
- No other visual behavior changes; this is a token-centralization pass, not a redesign.

### 4.3 Tests

- A grep-based structural test (JVM unit test or a repo-level script check) asserts no `Color(0xFF...)` or `Color.Black`/`Color.White` literal appears in `ChessPiece.kt` or `ChessBoardView.kt` outside `Theme.kt` imports — mirroring the pattern already used elsewhere in this repo for source-level architectural assertions (see `crates/chess-tui/tests/no_incidental_filesystem_writes.rs` for precedent).
- Existing `BoardModelTest.kt` orientation/parity tests remain green.

---

## 5. AR-003 — Remove internal jargon from player-facing setup copy

### 5.1 Defect

`SetupScreen.kt:73,75` contains the word "native" in player-visible text: "Play against the native Rust chess engine." and "Native cleanup must succeed before another game can start." "Native" names an internal JNI/lifecycle implementation detail, not player-facing language, and directly contradicts Phase 4.1's "Do not mention JNI/shared-Rust-layer architecture in setup UI."

### 5.2 Fix

- Reword both strings to remove "native" while preserving their intended meaning to a player. Suggested (not mandatory) replacements: `"Play against the Rust chess engine."` for the subtitle, and something like `"Cleanup must finish before another game can start."` or `"Please retry cleanup before starting another game."` for the cleanup-required message — final wording is at the implementer's discretion provided it names no internal architecture concept.
- Grep the rest of `android-harness/android-app/src/main/kotlin` for "native", "JNI", "shared layer", and "architecture" in string literals reachable from player-visible UI and correct any other instance found.

### 5.3 Tests

- A JVM/unit or structural test asserts none of "native", "JNI" appear in the player-facing string literals of `SetupScreen.kt` (or equivalent string-resource source).
- Existing `ChessAppSemanticsInstrumentedTest.kt`/`ChessAppEndToEndInstrumentedTest.kt` assertions that reference setup copy remain green (update literal-text assertions if this pass changes matched strings).

---

## 6. AR-004 — Verify and, if needed, fix system-bar theming on target SDK 35

### 6.1 Defect

Dark status/navigation-bar coordination relies entirely on legacy XML theme attributes (`styles.xml:8-10`: `android:statusBarColor`, `android:navigationBarColor`, `android:windowLightStatusBar`). The app declares `compileSdk`/`targetSdk = 35` (`build.gradle.kts`). Android 15 (API 35) enforces edge-to-edge display by default for apps targeting SDK 35, and Google's own documentation states these exact attributes become deprecated/no-ops under that mode. No `WindowCompat`/`WindowInsetsControllerCompat` call exists anywhere in `MainActivity.kt` or elsewhere to explicitly control system-bar appearance under edge-to-edge. This is a plausible real regression on current-generation devices/emulators that no existing test would catch.

### 6.2 Fix

- In `MainActivity.kt` (or a small dedicated theming helper), add an explicit edge-to-edge-aware system-bar call: at minimum, use `WindowCompat.getInsetsController(window, view)` to set `isAppearanceLightStatusBars = false` / `isAppearanceLightNavigationBars = false` (the app is unconditionally dark, per AR-002/Phase 1.2), and apply `AppBackground`/`Surface` as the effective bar scrim consistent with the product theme, using `enableEdgeToEdge()` or `WindowCompat.setDecorFitsSystemWindows` as appropriate for the chosen approach.
- Keep the existing `styles.xml` attributes in place as a pre-Compose-render/legacy fallback (per Phase 1.3's launch-flash requirement) — this task adds the modern mechanism alongside them, it does not remove the XML attributes.
- Actually run the app on an API 35 emulator (via `bash scripts/dev.sh android`, once locally runnable, or the permanent Android CI's emulator job) and visually confirm the status/navigation bars render dark, not stock light, before marking this task complete — do not mark complete on code-inspection alone given this defect was specifically about a claim that could only be verified at runtime.

### 6.3 Tests

- An instrumentation test asserts the actual `WindowInsetsController` appearance flags (or the equivalent observable state) are set to dark/non-light after `MainActivity` launches.
- Existing screenshot evidence (`ChessAppVisualFixtureEvidenceInstrumentedTest.kt`/`ChessAppVisualFlowEvidenceInstrumentedTest.kt`) is manually re-reviewed post-fix to confirm the system bars are visibly dark in the captured PNGs, and this manual confirmation is recorded in the TODO (screenshots alone remain non-authoritative per this program's own operating rules; the instrumentation assertion above is the acceptance evidence, the screenshot review is corroboration only).

---

## 7. AR-005 — Document the board-size calculation

### 7.1 Defect

Phase 3.1 requires "Document the implemented board-size calculation." No inline comment exists near the sizing computation in `GameScreen.kt` (the `boardSize = minOf(maxWidth, (maxHeight - nonBoardHeight).coerceAtLeast(0.dp))` calculation and its constituent fixed-height constants), and neither `docs/RUST_ANDROID_APP.md` nor the closure-evidence document describes the formula or its constants.

### 7.2 Fix

- Add a concise inline comment directly above the board-size calculation in `GameScreen.kt` explaining the formula in one or two sentences: board size is the largest square bounded by available width and by available height minus the fixed status/tab/action/spacing regions, so the board shrinks before any fixed control is clipped.
- Add a short paragraph to `docs/RUST_ANDROID_APP.md`'s layout-structure section (already present per Phase 21) naming the fixed constants (`statusHeight`, `tabHeight`, `actionHeight`, `minimumPanelHeight` or their current equivalents) and the shrink-before-clip policy.

### 7.3 Tests

- No behavioral test required; this is a documentation-only task. Verified by review of the added comment/doc paragraph against the actual formula in code.

---

## 8. AR-006 — Document and harden the auto-scroll effect's scheduling dependency

### 8.1 Defect

`GamePanels.kt:38-49`'s "was near bottom" auto-scroll check reads `listState.layoutInfo` inside a `LaunchedEffect(rows.size)` and relies on that read happening before Compose's layout pass reflects the newly appended row. This was traced by hand and confirmed currently correct, and is covered by two dedicated tests (`MoveHistoryAutoScrollInstrumentedTest.kt`). However, the correctness depends on an implementation detail of Compose's effect-dispatch-vs-layout ordering, not a documented public contract — a future Compose runtime change could silently invert this behavior without any source-level signal.

### 8.2 Fix

- Add an inline comment directly above the `wasNearBottom` computation explaining the ordering dependency explicitly (effect body's synchronous prefix runs before the layout pass that would grow `totalItemsCount`), so a future reader (or future Compose upgrade investigation) understands exactly what assumption is being relied on and why the existing tests are the actual safety net for it.
- Evaluate whether a more robust formulation is practical without materially changing behavior — for example, capturing the pre-append `layoutInfo` snapshot explicitly via a `remember`ed previous-size comparison rather than relying on effect-ordering timing. If a materially more robust formulation is straightforward, implement it; if it would meaningfully change behavior or risk regressing the two existing auto-scroll tests, keep the current implementation and rely on the comment plus existing tests instead. Record the decision made and why in the TODO.

### 8.3 Tests

- The two existing `MoveHistoryAutoScrollInstrumentedTest.kt` tests (`newestRowStaysVisibleWhenHistoryWasAtBottom`, `newRowDoesNotStealManualHistoricalPosition`) remain green and unweakened after this task, regardless of which fix path (comment-only or reformulation) is chosen.

---

## 9. AR-007 — Add busy-state guard consistency to `restartGame`/`resign`/`submitMove`

### 9.1 Defect

`ChessViewModel.kt`'s `startGame()` explicitly re-checks `!configuration.isSetup || configuration.busy || configuration.cleanupRequired` before proceeding. `restartGame()`, `resign()`, and `submitMove()` do not perform an equivalent internal `busy` re-check — they rely solely on the UI's `enabled = !busy` guard on the triggering button, mitigated in practice by the generation/ticket mechanism (`nextOperation()` cancelling any prior in-flight operation). This is an architectural inconsistency, not a demonstrated live bug.

### 9.2 Fix

- Add the same defensive `busy`/`cleanupRequired` precondition re-check used by `startGame()` to `restartGame()`, `resign()`, and `submitMove()`, returning early (with the same "reject visibly, do not silently proceed" discipline used elsewhere in this codebase) if the precondition does not hold.
- Do not change the generation/ticket cancellation mechanism itself; this task adds a defensive guard in front of it, it does not replace it.

### 9.3 Tests

- A unit/instrumentation test drives a rapid double-invocation of each of `restartGame()`, `resign()`, and `submitMove()` while `busy == true` and asserts only one logical operation proceeds (the second call is rejected/no-ops rather than starting a second concurrent operation).

---

## 10. AR-008 — Extract a shared, tolerance-aware layout-bounds test helper

### 10.1 Defect

The bounds-containment helper (`bounds(tag): Rect`, `assertContained(rootTag, childTags)`, `assertNoRootScroll`, `assertSquare`) is duplicated verbatim across `ChessAppLayoutInstrumentedTest.kt` and `ChessAppAdaptiveLayoutInstrumentedTest.kt` as private functions, contradicting Phase 14.2's explicit "reusable test helper" requirement. Separately, every containment/equality comparison in the suite uses hard inequalities or exact `Rect` equality with no tolerance constant anywhere, contradicting Phase 14.2's "keep tolerance explicit and small" requirement (stricter than requested, but the deliverable as specified was never built).

### 10.2 Fix

- Extract `bounds`, `assertContained`, `assertNoRootScroll`, and `assertSquare` into a single shared top-level file (e.g. `LayoutTestSupport.kt` in `androidTest`, alongside the existing `VisualEvidenceTestSupport.kt` precedent) and update both existing test files to use it instead of their private duplicates.
- Introduce a small, explicit tolerance constant (e.g. `private const val BOUNDS_TOLERANCE_DP = 0.5f` or equivalent) and apply it to the containment/equality comparisons that currently use exact equality or zero-tolerance inequalities, without loosening them enough to mask a real regression — the tolerance should absorb only legitimate sub-pixel/density rounding, not meaningful layout drift.

### 10.3 Tests

- All existing callers of the old private helpers continue to pass using the new shared helper with no change in what they assert.
- A new test constructs two bounds differing by less than the tolerance and asserts they are treated as equal, and two bounds differing by more than the tolerance and asserts they are treated as different — proving the tolerance is real and bounded, not accidentally unlimited.

---

## 11. AR-009 — Add Black-orientation layout/containment/spatial-stability test coverage

### 11.1 Defect

Every Compose-level containment, no-root-scroll, and spatial-stability test in the suite hardcodes `HumanSide.WHITE` in its `gameState()`/fixture builder. The only two tests that exercise `HumanSide.BLACK` operate at the data-model or raw-screenshot level; neither runs `assertContained`, `assertNoRootScroll`, or `assertSquare` against the Black-oriented board. Board-orientation correctness for Black was hand-verified correct by this review (the square-color/coordinate-label math is orientation-independent by construction), but the automated safety net has no coverage for it and would not catch a future regression.

### 11.2 Fix

- Add a Black-orientation variant of the existing 360×640dp compact-layout containment test (mirroring `compactGameKeepsStatusBoardTabsPanelAndActionsFullyVisible` or equivalent) that builds its fixture with `humanSide = HumanSide.BLACK` and asserts the same containment/square/no-root-scroll invariants hold.
- Add a Black-orientation spatial-stability assertion analogous to `boardGeometryDoesNotMoveAcrossThinkingAndReplyStates`, at minimum covering idle and thinking states for Black.

### 11.3 Tests

This task's deliverable is itself the new test coverage described in 11.2; no separate test-of-tests is required beyond confirming the new tests fail if `humanSide` fixture wiring is reverted to White (a sanity check performed during implementation, not a permanent additional test).

---

## 12. AR-010 — Add board/action-row bounds-stability test across tab switches

### 12.1 Defect

Neither Phase 7's nor Phase 15.7's "board bounds equal before/after tab switch" and "action-row bounds equal before/after tab switch" bullets are directly tested. The existing spatial-stability test (`boardGeometryDoesNotMoveAcrossThinkingAndReplyStates`) never clicks a tab; the existing tab-switch test (`movesAndEngineTabsReuseTheSameBoundedRegion`) only compares `game-tab-body` bounds, never `chess-board`/`game-actions`. This gap was independently identified by two review passes. The underlying layout was independently traced and confirmed structurally correct by two reviewers, so this is a coverage gap, not a known defect.

### 12.2 Fix

- Extend or add a test that captures `chess-board` and `game-actions` bounds before clicking the Engine/Moves tab selector, clicks it, and asserts both are unchanged after the switch (using the AR-008 shared helper's tolerance-aware equality).

### 12.3 Tests

This task's deliverable is the test itself; verify it would fail against a deliberately-reverted `weight(1f)`-vs-fixed-height regression during implementation as a sanity check.

---

## 13. AR-011 — Add a functional promotion-dialog test

### 13.1 Defect

The only promotion-dialog coverage (`capturePromotionDialog` in `ChessAppVisualFixtureEvidenceInstrumentedTest.kt`) renders the dialog in isolation with a no-op `onChoose = {}` and only takes a screenshot — no test clicks a promotion option and asserts the callback fires with the correct authoritative move string, and no test exercises a real pawn-reaches-8th-rank board-tap path into the promotion dialog. The underlying `orderedPromotionMoves`/`choosePromotion` logic was independently hand-verified correct by this review (`PresentationMappingTest.kt` already pins the ordering), but the interactive click-through itself is untested.

### 13.2 Fix

- Add an instrumentation test that renders `PromotionDialog` with a real (non-no-op) `onChoose` callback capturing its argument, clicks each of the four options in turn across separate test invocations or a single parameterized test, and asserts the captured value matches the expected authoritative UCI move string for that option.
- If practical within existing fixture support, add or extend an end-to-end test that drives a real board through a promotion-eligible position (a deterministic FEN/move-sequence fixture) via taps, opens the promotion dialog through the real flow, selects a piece, and asserts the resulting move/snapshot reflects the correct promotion.

### 13.3 Tests

This task's deliverable is the test(s) themselves, described above.

---

## 14. AR-012 — Add a functional error-dialog test

### 14.1 Defect

The only error-dialog coverage (`captureBoundedErrorDialog` in `ChessAppVisualFixtureEvidenceInstrumentedTest.kt`) performs no assertion beyond `waitForIdle()` and a screenshot — no test asserts the error message text is actually rendered, and no test exercises the dismiss button's behavior. The underlying fail-closed behavior (no auto-retry, no silent reset, no fallback move) was independently and rigorously traced correct by two review passes; only the dialog's own rendering/dismissal is untested.

### 14.2 Fix

- Add an instrumentation test that renders `ChessEngineErrorDialog` with a known, non-trivial message string, asserts that exact text is present in the composed tree, clicks the dismiss control, and asserts the expected dismiss callback fires (or, for an end-to-end variant, that `errorMessage` clears in view state) without any other observable side effect.

### 14.3 Tests

This task's deliverable is the test itself, described above.

---

## 15. AR-013 — Add engine-metrics content-rendering test

### 15.1 Defect

Every existing reference to `"engine-panel"` across the instrumentation suite is `.fetchSemanticsNode()`/`.assertExists()` only — no test asserts that a specific metric value (score, nodes, NPS, PV) is actually rendered as visible text. A regression that blanked all metric fields while leaving the panel container in place would pass every current test.

### 15.2 Fix

- Add an instrumentation or Compose-unit test that supplies a snapshot with known, distinct metric values (depth, score, nodes, NPS, elapsed, PV) and asserts each expected formatted value is present as rendered text within the Engine tab body.
- Add a companion test for the partial-metrics case (some fields present, some genuinely absent) asserting present fields render their real value and absent fields render the "no value" placeholder (`"—"`), not a fabricated `"0"`.

### 15.3 Tests

This task's deliverable is the tests themselves, described above.

---

## 16. AR-014 — Add a Setup-title test tag and visibility test

### 16.1 Defect

No test references the "Rust Chess" setup title text or a title test tag; `SetupScreen.kt`'s title composable carries no `testTag`. Phase 15.1's "title visible" bullet has no automated evidence.

### 16.2 Fix

- Add a `testTag("setup-title")` (or equivalent) to the title composable in `SetupScreen.kt`.
- Add it to the existing `assertContained("setup-screen", listOf(...))` child-tag list in the compact-layout test(s) so its containment at 360×640dp is asserted alongside the other required Setup regions.

### 16.3 Tests

- The extended `assertContained` call from 16.2 is itself the test; additionally assert the title's rendered text equals the expected copy (coordinate wording with AR-003 if it changes).

---

## 17. AR-015 — Add busy-state layout-stability tests

### 17.1 Defect

Phase 4's "Busy state does not move Start Game or selector controls outside viewport" and Phase 11's "Busy state disables incompatible actions without moving them" are both correct by code inspection (buttons only toggle `enabled`, never removed/reflowed) but neither is exercised by a test that actually drives `busy = true` and checks bounds — the only related coverage tests the `snapshot.thinking` transition on the Game screen, not `ChessUiState.busy` on either screen.

### 17.2 Fix

- Add a Setup-screen test that sets `busy = true` in the fixture state, asserts `side-white`/`side-black`/`depth-control`/`start-game` bounds are unchanged relative to the non-busy state (using the AR-008 helper), and that the busy controls report `assertIsNotEnabled()` where applicable.
- Add a Game-screen test that sets `busy = true`, asserts `game-actions` bounds are unchanged relative to the non-busy state, and that the Resign button reflects `assertIsNotEnabled()` when disabled by busy state, and separately by `gameOver` state.

### 17.3 Tests

This task's deliverable is the tests themselves, described above.

---

## 18. AR-016 — Add automated contrast validation

### 18.1 Defect

Phase 13.3 requires validating primary/secondary text contrast, control-label contrast on accent/danger surfaces, and board-piece/overlay contrast. No contrast-checking tool or test exists anywhere in the repository; the review's supporting evidence was a manual hand-computed WCAG ratio for one representative token pair, not an executed, repeatable check.

### 18.2 Fix

- Add a JVM unit test (no Android instrumentation required — this is pure arithmetic over the `Theme.kt` token hex values) that computes the WCAG relative-luminance contrast ratio for each of the following pairs and asserts each meets or exceeds a stated threshold (4.5:1 for normal text, 3:1 for large text/UI components, matching WCAG AA): `OnBackground` on `AppBackground`; `OnSurfaceMuted` on `Surface`; `OnSurfaceMuted` on `SurfaceMuted`; `OnBackground`/button label color on `Primary`/`PrimaryStrong`; button label color on `Danger`; the new `PieceLightFill`/`PieceDarkFill` tokens (from AR-002) on `BoardLight`/`BoardDark` respectively; the new `CoordinateLabel` token (from AR-002) on both `BoardLight` and `BoardDark`.
- If any pair fails the threshold, adjust the offending token's value (in `Theme.kt`, coordinating with AR-002) until it passes, recording the before/after values in the TODO.

### 18.3 Tests

The contrast-ratio unit test described in 18.2 is itself this task's test; it must be added to a location `bash scripts/dev.sh android`'s unit-test step already runs (i.e. alongside `PresentationMappingTest.kt`/`BoardModelTest.kt`).

---

## 19. AR-017 — Add Rust SAN piece-capture and capture-promotion test coverage

### 19.1 Defect

Phase 8.2/8.4's "format captures"/"capture" and "promotion plus check/mate as applicable" bullets are only exercised by pawn captures (including one en passant) and quiet promotion, respectively. No test exists for a non-pawn piece capturing (e.g. `Nxe5`), no test combines disambiguation with a capture (e.g. `Ndxe4`), and no test combines promotion with a capture (e.g. `exd8=Q`). The shared capture code path was confirmed correct by code inspection for the piece case, but this was never independently proven by a dedicated test.

### 19.2 Fix

- Add a test in `crates/chess-core/src/san.rs` exercising a knight or bishop capturing an enemy piece, asserting the correct `Nxe5`-style SAN output against a hand-verified real FEN/position.
- Add a test combining file-or-rank disambiguation with a capture (e.g. two rooks, one capturing), asserting the correct combined SAN output.
- Add a test for a capture-promotion (e.g. a pawn on the 7th rank capturing onto the 8th rank with promotion), asserting the correct `exd8=Q`-style output, and a variant that also delivers check/mate if a compact fixture allows it without excessive complexity.

### 19.3 Tests

The new `san.rs` tests described in 19.2 are this task's deliverable; each must be hand-verified against real chess legality/rules before being accepted, matching this review's own verification standard.

---

## 20. AR-018 — Add Kotlin snapshot-parser negative-path unit tests

### 20.1 Defect

`ChessGameSnapshot.parse`'s fail-closed `require()` guards (wrong field count, wrong version, missing terminator) are correct by code inspection but are never exercised by any automated test — all existing coverage of the parser is positive-path only (`ChessEngineHostJvmTest.kt`'s real-JNI happy-path integration test).

### 20.2 Fix

- Add a JVM/unit test target for `ChessGameSnapshot.parse` (or the equivalent parsing entry point) that feeds it a string with the wrong field count and asserts it throws `IllegalArgumentException` rather than parsing partially or defaulting.
- Add a companion test with a correct field count but wrong version string, asserting the same failure mode.
- Add a companion test with a missing/corrupted terminator field, asserting the same failure mode.

### 20.3 Tests

The three negative-path tests described in 20.2 are this task's deliverable.

---

## 21. AR-019 — Add a static Rust↔Kotlin high-level snapshot contract test

### 21.1 Defect

`crates/chess-jni/tests/jni_contract.rs` only statically cross-references the low-level `ChessEngine`/`NativeChessEngineBindings` API (13-field compact search record) against its Rust exports. There is no equivalent static test asserting the high-level `ChessGame`/`NativeChessAppBindings` API's Kotlin-side `FIELD_COUNT`/`VERSION` constants match the Rust `SNAPSHOT_VERSION`/field-array length in `app_bridge.rs`. Today, a future change that bumps one side without the other would only be caught at runtime by the host-JVM integration test, not by `cargo test`.

### 21.2 Fix

- Extend `crates/chess-jni/tests/jni_contract.rs` (or add a sibling test in the same file) that statically parses `crates/chess-jni/kotlin/src/main/kotlin/com/ekkus93/chessengine/ChessGame.kt`'s source text for its `FIELD_COUNT`/`VERSION` constant literals and asserts they match `app_bridge.rs`'s `SNAPSHOT_VERSION` constant and actual encoded-field-array length, following the same string-matching contract-test pattern already established for the low-level API in that file.

### 21.3 Tests

The extended/new contract test described in 21.2 is this task's deliverable; verify it would fail if `SNAPSHOT_VERSION` or `FIELD_COUNT`/`VERSION` were deliberately desynced during implementation, as a sanity check.

---

## 22. AR-020 — Add a portrait rotation-attempt instrumentation test

### 22.1 Defect

Phase 2.2's "Confirm app remains portrait when device/emulator rotation is requested" and "Confirm game/session state is not reset merely because a rotation request is attempted" have no automated test — only a static `requestedOrientation` assertion exists (`ChessAppEndToEndInstrumentedTest.kt`). Phase 2's own test bullet for this is hedged ("if practical in permanent CI"), so this is a genuine gap against the spirit of the requirement, not an unambiguous violation.

### 22.2 Fix

- Add an instrumentation test that starts a game, captures the current snapshot/moves state, issues a rotation request via the available Android test API (e.g. `UiDevice.setOrientationLeft()`/`setOrientationNatural()` from `androidx.test.uiautomator`, adding that dependency if not already present and justified per the constraints in §2), and asserts both that the Activity's effective orientation remains portrait and that the captured game state is unchanged afterward.
- If `uiautomator`-based rotation proves impractical in the CI emulator environment, document the specific blocker in the TODO and fall back to asserting the manifest/runtime `requestedOrientation` lock is sufficient to prevent the OS from ever attempting a layout-changing rotation in the first place — do not mark this task complete without one of these two forms of evidence.

### 22.3 Tests

The rotation-attempt test described in 22.2, or the documented-blocker fallback, is this task's deliverable.

---

## 23. AR-021 — Final validation and closure

- Run the full applicable validation surface for this pass: Android app JVM/unit tests, Android lint, `crates/chess-core` tests (for AR-017), `crates/chess-jni` tests including the extended contract test (AR-019), and the full Android instrumentation suite including every test added by this pass.
- Run `bash scripts/dev.sh fast` to confirm no cross-workspace regression.
- Record exact commands, results, and (where obtained) CI run/job evidence in the companion TODO's closure section.
- Do not mark any AR task `[x]` without the specific test evidence named in its own section above.
