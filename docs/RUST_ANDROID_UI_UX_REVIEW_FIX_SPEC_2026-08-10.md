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

This pass fixes the confirmed bug and design defects, hardens the two code-smell items, and closes every automatable identified test-coverage gap, recording any genuinely environment-blocked runtime gap explicitly rather than silently claiming it closed (see AR-020 §22 and AR-021 §23). It does not reopen `docs/RUST_ANDROID_UI_UX_REDESIGN_TODO_2026-08-10.md`'s own checkbox state (that document remains superseded for shipped-state authority by the closure-evidence document, per `docs/LEGACY_TODO_INDEX.md`'s existing convention), and it does not retroactively satisfy Phase 17's still-open literal local `bash scripts/dev.sh android`/`fast` invocations from the prior program or the Phase 20 physical-device UX pass — those specific historical checkbox items remain honestly disclosed as open in the closure-evidence document and are outside this pass's scope. This is a distinct claim from whether `bash scripts/dev.sh fast` runs as *this pass's own* validation gate — it does; see AR-021 and the clarified rule in the companion TODO's Status rules.

### 1.1 Pre-implementation resolution note

Before implementation began, an independent pre-implementation review of this spec/TODO pair (`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_QUESTIONS_AND_ISSUES_2026-08-10.md`, twelve items, QI-001 through QI-012) was resolved and incorporated directly into the sections below. Two items were flagged as blockers:

- **QI-002** (real contradiction between "`dev.sh fast` is out of scope" and AR-021 requiring it) is resolved by the reworded paragraph above and by AR-021 §23 below: `dev.sh fast` is a mandatory validation gate for this pass itself.
- **QI-001** (the review-fix TODO is not registered in `docs/LEGACY_TODO_INDEX.md`'s "active implementation TODO" table) is **not** treated as a blocker. Three prior review-fix passes — `docs/RUST_ENGINE_REVIEW_FIX_TODO_2026-08-02.md`, `docs/RUST_CHESS_ENGINE_POST_PORT_REVIEW_FIX_TODO_2026-08-04.md`, and `docs/RUST_TUI_REVIEW_FIX_TODO_2026-08-09.md` (the last completed via an identical Ralph-loop pattern to the one this program will use) — were all implemented to completion while registered only in the index's historical inventory, never in the "active implementation TODO" table. That table is reserved for large multi-phase product programs (the Rust port, S3/S4 strength, the console/application-sharing program, the Android redesign itself); a bounded, self-contained review-fix pass against an already-shipped feature is an established distinct category that does not require table registration to be implemented. No change to `docs/LEGACY_TODO_INDEX.md`'s active-table state is made by this pass on that basis.

The remaining ten items (QI-003 through QI-012) were specification-hardening suggestions and are incorporated into the affected AR-00N sections below and into the companion TODO's AR-000 section.

### 1.2 Second pre-implementation resolution note

A second, follow-up pre-implementation review (`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_FOLLOWUP_QUESTIONS_AND_ISSUES_2026-08-10.md`, FQI-001 through FQI-005, reviewing commit `85ae883369e5fc58e3cf8e50328b157369369ddb`) found the QI-series revision materially improved but identified five further issues, since resolved:

- **FQI-001** (real contradiction: §1.1's precedent-based defense of QI-001 did not fix the actual written contradiction in `docs/LEGACY_TODO_INDEX.md`, which still classified this document as "not active instructions") — resolved at the source: `docs/LEGACY_TODO_INDEX.md` now defines an explicit "Bounded review-fix trackers" classification, retroactively naming all three prior review-fix passes plus this one, and the exhaustive classification rule was amended to reference it. This is enforced by `scripts/task_post_port_review_fix_audit.sh`, not merely documented.
- **FQI-002** (AR-007's original wording required distinguishing which operation was in flight — same-operation duplicate vs. a genuinely different invalid invocation — but `ChessViewModel` tracks no operation-identity state to make that distinction from, and the claim that visible rejection would "match `startGame()`'s existing discipline" was factually inaccurate, since `startGame()`'s own `cleanupRequired` guard already silently returns) — resolved by simplifying AR-007 §9 to global-busy/cleanup duplicate-input suppression, matching `startGame()`'s actual current guard verbatim rather than an idealized description of it.
- **FQI-003** (AR-016's original wording could be read as requiring every individual piece fill/stroke token to independently meet 3:1 contrast against every board square, which computed WCAG ratios show would force unnecessary palette changes to an already-legible outlined-piece design where the fill/stroke pair itself contrasts at roughly 11–14:1) — resolved by rewriting AR-016 §18 to validate the rendered piece as a composite silhouette-boundary object, not independent raw tokens.
- **FQI-004** (AR-020's honest blocked/manual fallback for CI-impractical rotation testing directly contradicted AR-021's "every AR task is `[x]`" and the Purpose's "closes every test-coverage gap" — a task that is honestly blocked/manual cannot also be `[x]`) — resolved by qualifying AR-021 §23's closure requirement to explicitly accommodate a genuinely blocked/manual AR-020 runtime sub-item without treating it as `[x]`, and by the Purpose wording changed above (§1).
- **FQI-005** (the closure-evidence document AR-021 creates was not listed in §2's "This pass touches:" scope) — resolved by adding it to §2 below.

---

## 2. Engineering constraints retained

- `chess-core`'s rules/SAN authority and `chess-search`'s search/evaluation authority are not touched behaviorally by this pass. `crates/chess-core/src/san.rs` gains additional tests only (AR-017); no formatting behavior changes.
- Rust remains authoritative for chess rules, legality, opening-book selection, and SAN generation. No task in this pass adds chess-rule, legality, disambiguation, or opening-book logic to Kotlin.
- The Android interactive fail-closed policy is not weakened: no task in this pass adds a random/first-legal fallback, silent retry, silent depth reduction, fake/default snapshot, or alternate engine path.
- The existing one-second post-human-move reveal delay, portrait-only lock, and no-root-page-scroll invariants are preserved exactly; no task changes their behavior, only their test coverage or presentation polish.
- No first-party lint suppression (`allow`/`expect`, Kotlin `@Suppress`) is added anywhere in this pass.
- No new production dependency is added without explicit justification recorded in this spec. AR-016's contrast check and AR-009/AR-010/AR-013's layout assertions must be built from existing `androidx.compose.ui:ui-test-junit4`/JVM-unit-test capability already present in the project; no new test dependency is introduced without being named here first.
- This pass touches: `android-harness/android-app/src/main/kotlin/**`, `android-harness/android-app/src/{test,androidTest}/kotlin/**`, `android-harness/android-app/build.gradle.kts` (solely to add the `androidx.test.uiautomator` test dependency if AR-020 needs it and it is not already present — no other build/dependency change is in scope), `crates/chess-core/src/san.rs` (tests only), `crates/chess-jni/kotlin/**` (tests only), `crates/chess-jni/tests/jni_contract.rs`, `docs/RUST_ANDROID_APP.md` (solely for AR-005's documentation addition), `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md` (created fresh by AR-021), and this spec/TODO pair. This list is exhaustive. The already-landed `docs/LEGACY_TODO_INDEX.md`/`scripts/task_post_port_review_fix_audit.sh` bookkeeping is intentionally outside it, as pre-implementation authority preparation rather than AR-001-through-AR-021 implementation scope. It does not touch `crates/chess-app`, `crates/chess-search`, `crates/chess-book`, `crates/chess-uci`, `crates/chess-tui`, or `crates/chess-console`.
- `docs/RUST_ANDROID_UI_UX_REDESIGN_TODO_2026-08-10.md` and `docs/RUST_ANDROID_UI_UX_REDESIGN_CLOSURE_EVIDENCE_2026-08-10.md` are left as historical/closure records and are not edited by this pass. This pass's own closure evidence is recorded in a new, explicitly named document: `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md`, created by AR-021.
- The review baseline SHA (`98e21939b0665f2f54ade7f87cdcaba3fe48025f`, the shipped-product state that was reviewed) is distinct from the implementation-start SHA (the exact `master` state immediately before AR-001 begins, captured after this spec/TODO pair and its pre-implementation corrections have landed). Both are recorded separately in the companion TODO's AR-000 section; the review baseline is never overwritten or reinterpreted to mean implementation start.
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

### 6.2 Fix — verify-first

This task is verify-first, not fix-first: the review found a credible risk, not a confirmed runtime defect. Do not add production window-management code before observing actual API 35 behavior.

1. Inspect the current API 35 runtime state first: run the app on an API 35 emulator/device (via `bash scripts/dev.sh android` once locally runnable, or the permanent Android CI's emulator job) and capture/observe the actual rendered status/navigation-bar appearance, or the observable `WindowInsetsController` appearance state if a direct API query is more reliable than pixel inspection.
2. If the bars render incorrectly (stock light, or the intended dark appearance is not actually established), add an explicit edge-to-edge-aware system-bar call — at minimum `WindowCompat.getInsetsController(window, view)` setting `isAppearanceLightStatusBars = false` / `isAppearanceLightNavigationBars = false` (the app is unconditionally dark, per AR-002/Phase 1.2), using `enableEdgeToEdge()` or `WindowCompat.setDecorFitsSystemWindows` as appropriate — in `MainActivity.kt` or a small dedicated theming helper, and re-verify at runtime.
3. If current runtime behavior is already correct through another mechanism (e.g. the legacy XML attributes are in fact still honored on the exercised API level), document that finding and the mechanism responsible in the TODO, and do not add unnecessary production code.
4. Keep the existing `styles.xml` attributes in place regardless of outcome, as the pre-Compose-render/legacy fallback (per Phase 1.3's launch-flash requirement) — this task never removes them.
5. Do not mark this task complete on code-inspection alone; the runtime observation in step 1 is mandatory evidence either way.

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

### 8.2 Fix — prefer removing the timing dependency, not merely documenting it

1. First attempt a formulation that records the relevant pre-append state explicitly and bases the "was near bottom" decision on that captured state — for example, a `remember`ed previous `rows.size`/last-visible-index snapshot compared against the new value, rather than relying on `LaunchedEffect`'s synchronous-prefix-runs-before-layout ordering. This is the preferred, first-choice resolution.
2. Preserve the two existing auto-scroll behavior tests unchanged throughout.
3. Retain the current timing-dependent formulation only if the robust alternative is demonstrably impractical or introduces greater correctness risk than it removes — a source comment alone is the fallback, not the default outcome.
4. If the timing-dependent formulation is retained, add an inline comment directly above `wasNearBottom` explaining the ordering dependency explicitly (effect body's synchronous prefix runs before the layout pass that would grow `totalItemsCount`), record the decision as explicit tracked technical debt in the TODO, and name the two tests that guard it.

### 8.3 Tests

- The two existing `MoveHistoryAutoScrollInstrumentedTest.kt` tests (`newestRowStaysVisibleWhenHistoryWasAtBottom`, `newRowDoesNotStealManualHistoricalPosition`) remain green and unweakened after this task, regardless of which fix path (comment-only or reformulation) is chosen.

---

## 9. AR-007 — Add busy-state guard consistency to `restartGame`/`resign`/`submitMove`

### 9.1 Defect

`ChessViewModel.kt`'s `startGame()` explicitly re-checks `!configuration.isSetup || configuration.busy || configuration.cleanupRequired` before proceeding. `restartGame()`, `resign()`, and `submitMove()` do not perform an equivalent internal `busy` re-check — they rely solely on the UI's `enabled = !busy` guard on the triggering button, mitigated in practice by the generation/ticket mechanism (`nextOperation()` cancelling any prior in-flight operation). This is an architectural inconsistency, not a demonstrated live bug.

### 9.2 Fix — global-busy/cleanup duplicate-input suppression, matching `startGame()`'s actual guard

`ChessViewModel` tracks no per-operation-type identity today — its relevant state is `ChessUiState.busy: Boolean`, `operationGeneration: Long`, a `monitorJob`, and the current `game`. There is no `restart-busy` vs. `resign-busy` vs. `submit-busy` distinction to inspect, so a policy that requires telling "a duplicate of the same operation" apart from "a different invocation received while busy" cannot be implemented from this state without first adding an operation-identity concept the product does not currently need. This task therefore adopts the simpler, implementable policy:

- Add to `restartGame()`, `resign()`, and `submitMove()` the exact same precondition guard `startGame()` already uses — `if (!configuration.isSetup || configuration.busy || configuration.cleanupRequired) { return }` adapted to each function's actual applicable preconditions — returning early without performing the operation, without any second engine/native/JNI/cleanup call, and without any state mutation, whenever `busy` or `cleanupRequired` is true. This applies uniformly regardless of whether the new invocation is a repeat of the same button or a different action attempted while another operation is in flight; the product does not currently distinguish these, and this task does not invent that distinction.
- This is documented as global duplicate/concurrent-input suppression: a silent no-op return, exactly matching what `startGame()`'s guard already does today (a plain `return`, not a fresh visible-rejection error) — this task does not claim or introduce a form of "visible rejection" that `startGame()` itself does not perform at this guard.
- `cleanupRequired` is handled the same way: the operation does not proceed; the cleanup-required error/action state that was already surfaced when `cleanupRequired` was first raised remains visible and unchanged. This task does not add a new per-invocation error message on every rejected tap.
- Do not change the generation/ticket cancellation mechanism itself; this task adds a defensive guard in front of it, it does not replace it.
- If a future product requirement genuinely needs to distinguish operation types (e.g. a different UX for "resign attempted while restart is busy" vs. "restart tapped twice"), that requires adding explicit operation-identity state as its own separate, deliberately scoped task — it is out of scope here.

### 9.3 Tests

- A unit/instrumentation test drives a rapid duplicate invocation of each of `restartGame()`, `resign()`, and `submitMove()` while `busy == true`, and asserts exactly one logical operation proceeds, with no second engine/native/JNI/cleanup call, no state mutation, and no new error surfaced — a silent no-op, matching `startGame()`'s existing behavior under the same condition.
- A separate test drives each of the three while `cleanupRequired == true` and asserts the same silent no-op — no operation proceeds, and the already-visible cleanup-required state is unchanged (not replaced by a new error).

---

## 10. AR-008 — Extract a shared, tolerance-aware layout-bounds test helper

### 10.1 Defect

The bounds-containment helper (`bounds(tag): Rect`, `assertContained(rootTag, childTags)`, `assertNoRootScroll`, `assertSquare`) is duplicated verbatim across `ChessAppLayoutInstrumentedTest.kt` and `ChessAppAdaptiveLayoutInstrumentedTest.kt` as private functions, contradicting Phase 14.2's explicit "reusable test helper" requirement. Separately, every containment/equality comparison in the suite uses hard inequalities or exact `Rect` equality with no tolerance constant anywhere, contradicting Phase 14.2's "keep tolerance explicit and small" requirement (stricter than requested, but the deliverable as specified was never built).

### 10.2 Fix

- Extract `bounds`, `assertContained`, `assertNoRootScroll`, and `assertSquare` into a single shared top-level file (e.g. `LayoutTestSupport.kt` in `androidTest`, alongside the existing `VisualEvidenceTestSupport.kt` precedent) and update both existing test files to use it instead of their private duplicates.
- Normalize measurements to dp before applying the tolerance: Compose's `boundsInRoot`/`Rect` values are in raw pixel space, which changes meaning across device densities, while the layout requirement itself is stated in dp. Convert captured bounds to dp (via the test's `Density`/`LocalDensity`) before comparing, and name the tolerance constant accordingly (e.g. `private const val BOUNDS_TOLERANCE_DP = 0.5f`), so the same nominal tolerance means the same physical slack regardless of the emulator/device density under test. Do not compare a dp-named tolerance directly against raw pixel `Rect`s.
- Apply the tolerance to containment/equality comparisons that currently use exact equality or zero-tolerance inequalities, without loosening them enough to mask a real regression — the tolerance should absorb only legitimate sub-pixel/density rounding, not meaningful layout drift.

### 10.3 Tests

- All existing callers of the old private helpers continue to pass using the new shared helper with no change in what they assert.
- A new test constructs two bounds differing by less than the tolerance (in dp) and asserts they are treated as equal, and two bounds differing by more than the tolerance and asserts they are treated as different — proving the tolerance is real and bounded, not accidentally unlimited.
- A test at a non-1.0 density (or an equivalent conversion-level unit test of the dp-normalization step) confirms the helper cannot accidentally treat `0.5 dp` as `0.5 px` — i.e. the tolerance's physical meaning does not silently change with device density.

---

## 11. AR-009 — Add Black-orientation layout/containment/spatial-stability test coverage

### 11.1 Defect

Every Compose-level containment, no-root-scroll, and spatial-stability test in the suite hardcodes `HumanSide.WHITE` in its `gameState()`/fixture builder. The only two tests that exercise `HumanSide.BLACK` operate at the data-model or raw-screenshot level; neither runs `assertContained`, `assertNoRootScroll`, or `assertSquare` against the Black-oriented board. Board-orientation correctness for Black was hand-verified correct by this review (the square-color/coordinate-label math is orientation-independent by construction), but the automated safety net has no coverage for it and would not catch a future regression.

### 11.2 Fix

- Add a Black-orientation variant of the existing 360×640dp compact-layout containment test (mirroring `compactGameKeepsStatusBoardTabsPanelAndActionsFullyVisible` or equivalent) that builds its fixture with `humanSide = HumanSide.BLACK` and asserts the same containment/square/no-root-scroll invariants hold.
- Add a Black-orientation spatial-stability assertion analogous to `boardGeometryDoesNotMoveAcrossThinkingAndReplyStates`, at minimum covering idle and thinking states for Black.
- Add at least one **permanent, Black-specific semantic/coordinate assertion**, not merely generic containment geometry — containment/squareness/no-root-scroll checks can pass identically regardless of which orientation is actually rendered, so a test accidentally wired back to White could still pass every generic geometric assertion. Assert a known square/piece/file/rank relationship whose screen position or content description genuinely differs between White and Black orientation (e.g. the square rendered at the bottom-left corner, or a specific file/rank label's position), so the test fails if `humanSide`/fixture wiring is reverted to White even when all generic containment geometry remains valid.

### 11.3 Tests

This task's deliverable is the new test coverage described in 11.2, including the permanent orientation-specific assertion — confirmed, as a one-time implementation-time sanity check, to fail both if `humanSide` fixture wiring is reverted to White and if the new orientation-specific assertion itself is deliberately inverted.

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

For the non-piece text/control pairs, add a JVM unit test (no Android instrumentation required — pure arithmetic over `Theme.kt` token hex values) that computes the WCAG relative-luminance contrast ratio and asserts each meets its threshold (4.5:1 normal text, 3:1 large text/UI components, WCAG AA):

- `OnBackground` on `AppBackground`; `OnSurfaceMuted` on `Surface`; `OnSurfaceMuted` on `SurfaceMuted`; `OnBackground`/button label color on `Primary`/`PrimaryStrong`; button label color on `Danger`.
- `CoordinateLabel` (from AR-002) on both `BoardLight` and `BoardDark`.

For the board pieces, use a **composite silhouette-boundary contrast model**, not an independent-token requirement. `ChessPiece.kt`'s pieces are outlined shapes (fill plus stroke): computed WCAG ratios for this palette show the fill/stroke pair internally contrasts at roughly 11–14:1, so the piece's recognizable boundary against the square is formed by whichever of {fill-vs-square, stroke-vs-square, the fill/stroke internal edge} is actually the higher-contrast boundary at that pixel — not by requiring every individual component to independently clear a threshold against every square color, which computed ratios show would force an unnecessary palette change to an already-legible design (e.g. light piece fill on light square is a low ~1.3:1, but the same piece's stroke on that same square is ~8.7:1, so the rendered silhouette is clearly bounded regardless). For each of the four light/dark-piece × light/dark-square combinations, assert that **at least one** of the piece's boundary-forming components (fill-vs-background or stroke-vs-background, whichever the rendering actually uses as the visible edge at that combination) meets the 3:1 non-text-graphical-object threshold against the effective background — do not require all four raw fill/stroke tokens independently to hit 3:1 against both board colors unless that stricter requirement becomes an intentional product-design decision rather than an accessibility inference.

For overlays: cover last-move highlight (`BoardLastMove`, per AR-002's rewiring), the selected-square treatment, and the legal-move-target marker, computed as the actual alpha-composited effective background color (overlay color/alpha blended onto the underlying square color) rather than the raw overlay token compared to the raw foreground token in isolation, applying the same composite-boundary model described above.

If the composite-boundary check fails for any combination, adjust the offending token's value (in `Theme.kt`, coordinating with AR-002) until it passes, recording the before/after values in the TODO. The goal is an automated "contrast passed" claim that actually covers legal board states shown to a player and reflects how the piece is actually rendered, not a naive raw-token sample that would force redesigning an already-legible outlined-piece style.

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
- If `uiautomator`-based rotation proves impractical in the CI emulator environment: the static manifest/`requestedOrientation` assertion verifies configuration *intent*, not the requested *runtime behavior* (remain-portrait-and-preserve-state under an actual rotation attempt), and the two are not equivalent evidence. In that case, do not mark this task's runtime-behavior requirement as satisfied by the static assertion alone. Instead, keep the static assertion as useful supporting evidence, and explicitly record the runtime-rotation portion as **blocked/manual** in the TODO with the concrete environmental reason it could not be exercised in the supported CI/emulator environment — do not convert "not tested" into "verified" merely because the configuration makes the underlying bug unlikely.

### 22.3 Tests

The rotation-attempt test described in 22.2 is this task's primary deliverable. If that proves impractical, the static assertion plus an honest blocked/manual record (not a claim of equivalent coverage) is the accepted fallback — a silently-substituted "sufficient" claim is not.

### 22.4 Closure status if genuinely blocked

If the runtime rotation-attempt test is added and passes, AR-020 is checked `[x]` in full, exactly like every other task. If it is genuinely impractical in the supported CI/emulator environment, AR-020's runtime-behavior sub-item is **not** checked `[x]` — it is left open and explicitly marked blocked/manual with the concrete environmental reason, and AR-020's static-assertion sub-items (which did complete) are checked normally. AR-021 §23 defines how this interacts with overall program closure; a blocked/manual sub-item does not silently become `[x]` merely because its inability to run was documented.

---

## 23. AR-021 — Final validation and closure

- Run the full applicable validation surface for this pass: Android app JVM/unit tests, Android lint, `crates/chess-core` tests (for AR-017), `crates/chess-jni` tests including the extended contract test (AR-019), and the full Android instrumentation suite including every test added by this pass.
- Run `bash scripts/dev.sh fast` — this is a mandatory gate for this pass whenever the environment can run it, not optional. If a literal local execution is genuinely unavailable for an environmental reason, require the equivalent permanent general CI to be green on the exact final SHA instead, and explicitly record that the literal local command was not run — do not silently treat an unrun local command as passed.
- **Permanent exact-SHA CI is a mandatory, non-optional closure criterion**, not "where obtained"/"if available" evidence:
  - the permanent Android CI workflow/job must be green on the exact final source SHA;
  - the permanent general/Rust CI workflow/job must also be green on the exact final source SHA, because AR-017 and AR-019 touch Rust/JNI test surfaces;
  - record exact workflow run IDs, job IDs, conclusions, and the exact validated SHA in the closure-evidence document (`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md`, per §2's naming);
  - if a documentation-only closure commit changes the SHA after source CI already passed, follow this repository's established exact-SHA evidence policy (do not claim an earlier SHA validates a later one) rather than treating them as interchangeable.
- Record exact commands and results in the companion TODO's closure section and the closure-evidence document.
- Do not mark any AR task `[x]` without the specific test evidence named in its own section above.
- Do not mark this program `Complete` until the required permanent CI is green for the authoritative final state, per the rule above.
- **Qualified closure for a genuinely blocked AR-020 runtime item (FQI-004):** every other AR-001 through AR-020 task must be fully `[x]` with recorded test evidence. If, and only if, AR-020's runtime rotation-attempt test proves genuinely impractical in the supported CI/emulator environment per §22.4, the program may still close with a qualified terminal status reading `Complete — automated review-fix implementation validated; runtime rotation-attempt validation remains blocked/manual`, provided: the blocked sub-item is left visibly open (not `[x]`) in the TODO with its concrete environmental reason; the closure-evidence document carries the same blocked/manual record; and every other task in this program is unaffected — this qualification is scoped narrowly to AR-020's specific runtime sub-item and must not be read as license to leave any other task's evidence incomplete.
