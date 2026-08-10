# Rust Android UI/UX Review-Fix Closure Corrections Spec — 2026-08-10

**Status:** proposed / not started
**Branch:** `master`
**Companion TODO:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md`
**Program under correction:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md` (declared `Complete`)
**Closure evidence under correction:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md`
**Review baseline SHA:** `e9ab0fc623c22bd372ba9c8c2609dfcf74609f84`

---

## 1. Purpose

`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md` declares the bounded Android UI/UX review-fix program (AR-001 through AR-021) `Complete`, with a companion closure-evidence document citing independently-confirmed-real permanent CI evidence. An independent post-closure verification pass — eight parallel reviews, one per task cluster, each re-checking the actual shipped code against the final, twice-revised spec rather than trusting the checkboxes — found the closure to be **substantively but not fully honest**: the large majority of the 21 tasks are genuinely and rigorously implemented (including the two highest-technical-risk items, AR-008's dp-normalized tolerance and AR-016's revised composite-contrast model, both independently hand-verified with real computed numbers), no chess-correctness bug was found, no fail-open/fallback regression was found, and the cited CI run IDs are all real and independently confirmed via `gh`. However, five specific claims do not match the tree:

1. **AR-003** — a checkbox claims no player-visible string contains "native" jargon anywhere in `android-harness/android-app/src/main/kotlin`. This is false: `ChessViewModel.kt:71,117` still contain "native" and are rendered verbatim through the same player-facing error dialog AR-012 added coverage for.
2. **AR-004** — the spec required an explicit verify-first process (observe real API 35 behavior before any fix, and document the finding either way). No observation is recorded anywhere, no production code changed, and the one added test only checks a flag that would plausibly pass by default regardless of whether the underlying regression exists.
3. **AR-007** — the production guard code is correct and matches the final, simplified policy, but the checkboxes claim specific behavioral duplicate-invocation tests exist. They don't; only a predicate unit test and a static source-text-ordering check exist.
4. **AR-011** — the spec required either an end-to-end tap-driven promotion test or a documented reason one wasn't practical. Neither exists, despite the checkbox being marked complete.
5. **The closure-evidence document** cites permanent CI run IDs for a superseded SHA (`6d9a84d`) rather than the actual final tree (`e9ab0fc`), even though the final tree's own CI runs exist, are green, and were found only by independent `gh` querying.

The same verification pass also surfaced three minor, non-blocking hardening notes that were not false claims but are worth closing while this area of the codebase is already under active review: AR-006's replacement auto-scroll logic carries a new, undocumented assumption about `isScrollInProgress` not distinguishing user-initiated from auto-follow scrolls; AR-020's rotation test never explicitly asserts the source square became empty after the move it preserves; and AR-016's contrast matrix does not cover the Resign confirmation dialog's own button-on-surface color pairing (a real rendered combination, hand-computed to pass, but untested).

This pass closes all eight items. It does not reopen any other AR-00N task, and it does not relitigate any already-resolved QI/FQI pre-implementation item from the prior two rounds.

---

## 2. Engineering constraints retained

- All constraints from `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SPEC_2026-08-10.md` §2 continue to apply unless explicitly widened below: Rust remains authoritative for rules/SAN/opening-book/search; no chess-rule, legality, disambiguation, or opening-book logic is added to Kotlin; the fail-closed policy (no random/first-legal fallback, no silent retry, no silent depth reduction, no fake/default snapshot, no alternate engine path) is not weakened; the one-second reveal delay, portrait-only lock, and no-root-page-scroll invariants are preserved exactly.
- No first-party lint suppression (`allow`/`expect`, Kotlin `@Suppress`) is added anywhere in this pass.
- No new production dependency is added without explicit justification recorded in this spec. This pass adds none.
- This pass touches: `android-harness/android-app/src/main/kotlin/com/ekkus93/chessapp/{ChessViewModel,GamePanels}.kt`, `android-harness/android-app/src/{test,androidTest}/kotlin/com/ekkus93/chessapp/{ReviewFixArchitectureTest,ActiveGameOperationGuardTest,PromotionDialogInstrumentedTest,PortraitRotationInstrumentedTest,ThemeContrastTest}.kt`, `android-harness/android-app/src/main/kotlin/com/ekkus93/chessapp/MainActivity.kt` (only if CC-002's runtime observation shows a fix is actually needed), `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md`, `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md`, and this spec/TODO pair. It does not touch `crates/chess-app`, `crates/chess-core` (production code — `san.rs` test-only additions are not in scope here, since AR-017 was independently verified correct), `crates/chess-search`, `crates/chess-book`, `crates/chess-uci`, `crates/chess-tui`, or `crates/chess-console`.
- Existing passing tests are not weakened or deleted to obtain a green run; every currently-green assertion remains green after this pass.
- This pass is itself a bounded review-fix tracker under `docs/LEGACY_TODO_INDEX.md`'s existing "Bounded review-fix trackers" classification (see that document's own section by that name) — it is registered there as part of this pass's baseline work, following the identical precedent already established by the four trackers already listed.

---

## 3. CC-001 — Fix AR-003: remove remaining "native" jargon from `ChessViewModel.kt`

### 3.1 Defect

`ChessViewModel.kt:71`: `errorMessage = "A native game is still active. Retry cleanup before starting another game."` and `ChessViewModel.kt:117`: `append("Initial native snapshot failed: ")` — both assigned into `ChessUiState.errorMessage`, which `MainActivity.kt:69-74` renders verbatim in `ChessEngineErrorDialog`, a normal-operation player-visible surface. Both strings existed unchanged since the review baseline and were missed because AR-003's own structural test (`ReviewFixArchitectureTest.kt`, `setupPlayerCopyDoesNotExposeNativeArchitectureJargon`) is scoped only to `SetupScreen.kt`, narrower than the original spec's instruction to sweep "the rest of `android-harness/android-app/src/main/kotlin`."

### 3.2 Fix

- Reword both strings to remove "native" while preserving intended meaning. Suggested (not mandatory): `"A previous game is still active. Retry cleanup before starting another game."` for line 71, and `"Initial game snapshot failed: "` for line 117.
- Grep the rest of `android-harness/android-app/src/main/kotlin` one more time for "native", "JNI", "shared layer", "architecture" reachable from any player-visible string (not just `errorMessage` — also check dialog titles/bodies, status text, any Composable `Text`/`contentDescription`) and correct any further instance found. The two `check()` internal-invariant messages and the one `Log.e` call in `ChessViewModel.kt` (lines 109, 176, 395 as of the review) are not player-visible and remain out of scope.
- Broaden the structural test so this defect class cannot recur silently: either extend `setupPlayerCopyDoesNotExposeNativeArchitectureJargon` to scan every `.kt` file under `android-harness/android-app/src/main/kotlin` for these keywords in string literals (with a narrow, explicit allowlist for genuinely internal-only strings like the `check()` messages and log calls, each allowlist entry justified inline), or add a sibling test with equivalent effective coverage. The test must fail if "native"/"JNI"/"shared layer"/"architecture" is reintroduced into any player-reachable string anywhere in the module, not only in `SetupScreen.kt`.

### 3.3 Tests

- The broadened structural test passes on the corrected strings and is confirmed, by temporarily reintroducing "native" into `ChessViewModel.kt`'s error strings during implementation, to actually fail (a sanity check, not a permanent test).
- Existing `ChessAppEndToEndInstrumentedTest.kt`/other tests that might reference these exact error strings (grep for `"A native game"`/`"Initial native snapshot"`) are updated if any hard-coded match exists, and remain green.

---

## 4. CC-002 — Fix AR-004: actually perform the verify-first system-bar observation

### 4.1 Defect

The spec required observing real API 35 runtime behavior before any production change, and recording the finding either way. Neither the observation nor a "no change needed" narrative exists anywhere. The instrumentation test added (`SystemBarAppearanceInstrumentedTest.kt`) only asserts `isAppearanceLightStatusBars`/`isAppearanceLightNavigationBars` are `false` — flags whose default value plausibly satisfies the assertion regardless of the actual edge-to-edge background/color regression the spec was concerned about.

### 4.2 Fix

This task requires an actual API 35 emulator/device to execute, which this implementation environment may not have locally — if so, use the permanent Android CI's emulator job as the observation vehicle, exactly as `bash scripts/dev.sh android`'s own environment-availability precedent already establishes for this repository (see the original redesign closure evidence's own disclosed local-execution limitation for the identical class of constraint).

1. Add a genuinely diagnostic runtime check — not just the icon-appearance-flag check already present, but an assertion (or, if a direct assertion isn't practical, a recorded visual/pixel observation from the existing screenshot-evidence mechanism) that actually distinguishes "system bars render with the dark product background" from "system bars render with a stock light background" on the exercised API level. If the existing icon-appearance-only test is judged sufficient after genuine investigation of what it can and cannot detect, record that reasoning explicitly instead of silently leaving it as-is.
2. Based on what step 1 actually observes:
   - If bars render incorrectly: add the explicit `WindowCompat`/`WindowInsetsControllerCompat` (or `enableEdgeToEdge()`) call the original spec described, in `MainActivity.kt`, and re-verify.
   - If bars already render correctly: write the specific mechanism responsible into this TODO's CC-002 section — do not leave the box unexplained.
3. Do not mark this task complete without a runtime observation genuinely performed in this pass (CI-executed is acceptable; code-inspection alone is not), recorded with enough specificity (what was observed, on what job/run, with what result) that a future reader does not have to take it on faith.

### 4.3 Tests

- The strengthened/added diagnostic check (or the recorded observation) is the test evidence for this task. If a new assertion is added, it must be shown to actually distinguish the two states it claims to distinguish — describe how in the TODO.

---

## 5. CC-003 — Fix AR-007: add the missing behavioral duplicate-invocation tests

### 5.1 Defect

`ChessViewModel.kt`'s `restartGame()`/`resign()`/`submitMove()` guard code is correct, but AR-007.2's checkboxes claim behavioral tests proving "rapid duplicate invocation... results in exactly one logical operation, no second engine/native/JNI/cleanup call" for each of the three functions, plus the `cleanupRequired` case. No such test exists — only `ActiveGameOperationGuardTest.kt`'s pure predicate unit test and `ReviewFixArchitectureTest.kt`'s static source-text-ordering check.

### 5.2 Fix

Add real behavioral evidence. `ChessGame` (the JNI-backed native session class) has a private constructor and no test seam, which is why this wasn't done directly against a live `ChessViewModel` before — this pass must either:

- **Preferred:** find or add a genuine, narrowly-scoped test seam (e.g., an internal/test-visible way to construct a `ChessViewModel` against a fake/instrumented game handle, or an androidTest that drives the real `ChessGame` through the full app and counts actual engine-call side effects across a rapid double-tap) sufficient to prove the claimed behavior directly — no second operation launches, no state mutation, no new error — for at least one of the three functions as a representative case, with the other two covered by an argument for why the identical guard code generalizes (not by three separately-unproven behavioral claims).
- **Acceptable fallback:** if a genuine behavioral test seam is impractical within this pass's scope, reword AR-007.2's checkboxes in the TODO to accurately describe what is actually proven (predicate correctness plus static guard-ordering), and do not leave the stronger "no second engine/native/JNI/cleanup call" claim checked without real evidence for it. Record explicitly which path was taken and why.

### 5.3 Tests

- Whichever path is taken, the TODO's AR-007.2 section accurately reflects what test evidence actually exists after this task — no checkbox may claim behavioral proof that isn't backed by an actual executed test.

---

## 6. CC-004 — Fix AR-011: add the missing end-to-end promotion test

### 6.1 Defect

AR-011's second required deliverable — an end-to-end tap-driven promotion test, or a documented reason one wasn't practical — is absent from both the code and the TODO, despite the checkbox being marked `[x]`.

### 6.2 Fix

- Add an end-to-end instrumentation test that drives a real board through a promotion-eligible position via taps (a deterministic FEN/move-sequence fixture reaching a pawn-on-7th-rank-with-a-legal-promotion-move state), opens the promotion dialog through the actual production flow (not by invoking `PromotionDialog` directly), selects a promotion piece via a real tap, and asserts the resulting snapshot/move reflects the correct promotion.
- If, after a genuine attempt, this proves impractical (e.g., no deterministic fixture reaches a promotion-eligible position within the existing opening-book/self-play test infrastructure without excessive new scaffolding), document the specific blocker in the TODO instead of leaving the checkbox silently unexplained.

### 6.3 Tests

- The end-to-end test described above, or the documented-blocker fallback, is this task's deliverable.

---

## 7. CC-005 — Fix the closure-evidence document's CI citation

### 7.1 Defect

`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md` describes pushing a tree-identical validation-trigger commit specifically so permanent CI would validate "the exact authoritative closure tree," and that mechanism genuinely worked — but the document only cites the CI run IDs for the earlier, superseded SHA (`6d9a84d`), not the actual final tree's own runs, which exist, are green, and were found only by independent querying (general/Rust CI run `31419183264`, Android CI run `31419183273`, both against SHA `e9ab0fc623c22bd372ba9c8c2609dfcf74609f84`).

### 7.2 Fix

- Update `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md`'s "Permanent exact-source-SHA CI" section to cite the actual final-tree run IDs (`31419183264` for general/Rust CI, `31419183273` for Android CI) with their own job IDs and conclusions, alongside or in place of the `6d9a84d` citation — the document should be self-evidencing for the tree it claims to validate without requiring a reader to independently query GitHub to find the real final-tree evidence.
- Note explicitly that the `6d9a84d` runs remain valid supporting evidence that no source/test file differs between the two SHAs (a real, still-true claim), but the authoritative "this exact SHA is green" citation must point at the actual final SHA.

### 7.3 Tests

- N/A — documentation-only. Verified by independently re-querying both new run IDs via `gh` during implementation and confirming they match what gets written.

---

## 8. CC-006 — Document AR-006's residual auto-scroll scheduling assumption

### 8.1 Note

The replacement auto-scroll implementation (`GamePanels.kt`, `followLatest`/`snapshotFlow` over `listState.isScrollInProgress`) genuinely removed the original Compose effect-ordering dependency, but introduced a narrower one: `isScrollInProgress` is also `true` during the auto-scroll's own `animateScrollToItem` call, so the mechanism does not structurally distinguish "user-initiated scroll" from "the auto-follow scroll updating its own state." For the app's actual one-ply-at-a-time usage this is safe (a single-row hop keeps `nearBottom` true throughout), but it is undocumented and would not necessarily generalize to a hypothetical bulk-history-replace scenario.

### 8.2 Fix

- Add an inline comment at the `followLatest`/`snapshotFlow` collector in `GamePanels.kt` documenting this specific scope: the mechanism assumes append operations are single-row (matching real gameplay), and a future bulk-replace of history would need re-examination of this assumption before being relied upon.

### 8.3 Tests

- N/A — documentation-only; the two existing auto-scroll tests remain the behavioral evidence and are unaffected.

---

## 9. CC-007 — Strengthen AR-020's rotation test to assert source-square emptiness

### 9.1 Note

`PortraitRotationInstrumentedTest.kt` asserts the destination square's occupant (`"e4 pawn"`) exists both before and after rotation, but never explicitly asserts the source square (`e2`) is empty afterward — a hypothetical bug that duplicated the pawn onto both squares during a rotation-triggered recomposition would not be caught.

### 9.2 Fix

- Add an assertion that no node with content description `"e2 pawn"` exists after the rotation (alongside the existing `"e4 pawn"` presence assertion), completing the state-preservation check.

### 9.3 Tests

- The strengthened assertion is itself the test; confirm it is meaningful by checking it would fail if the move were hypothetically duplicated (reasoned through, not necessarily executed against a deliberately-broken build).

---

## 10. CC-008 — Add the Resign-dialog button contrast pairing to AR-016's matrix

### 10.1 Note

The Resign confirmation dialog's confirm button renders `Danger` content color on `SurfaceElevated` background (`Dialogs.kt`) — a real, distinct rendered combination from the in-row Resign button (`Danger` on `AppBackground`) that `ThemeContrastTest.kt` already covers. The dialog pairing was hand-computed during review to pass (≈5.6:1, well above the 4.5:1 threshold) but is not part of the automated matrix.

### 10.2 Fix

- Add `requireRatio("resign dialog confirm", Danger, SurfaceElevated, 4.5)` (or equivalent) to `ThemeContrastTest.kt`'s existing text/control pair list.

### 10.3 Tests

- The added assertion passes given current token values; this task's deliverable is the assertion itself.

---

## 11. CC-009 — Final validation and closure

- Run the full applicable validation surface: Android app JVM/unit tests (including the CC-001/CC-003/CC-008 additions), Android lint, the CC-004 instrumentation addition, and any CI job needed to perform CC-002's runtime observation.
- Run `bash scripts/dev.sh fast` to confirm no cross-workspace regression, following the same mandatory-whenever-runnable policy established in the parent review-fix program's AR-021.
- Update `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md` in place: correct the five previously-inaccurate checkboxes (or their surrounding narrative) to reflect what CC-001 through CC-005 actually established, rather than superseding the document with a second parallel tracker for the same program.
- Update `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md` per CC-005.
- Record exact commands, results, and CI run/job evidence in the companion TODO's closure section.
- Do not mark any CC task `[x]` without the specific evidence named in its own section above.
