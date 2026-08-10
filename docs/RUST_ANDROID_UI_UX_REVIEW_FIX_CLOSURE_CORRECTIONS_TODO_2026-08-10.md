# Rust Android UI/UX Review-Fix Closure Corrections TODO — 2026-08-10

**Status:** proposed / not started
**Branch:** `master`
**Spec:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_SPEC_2026-08-10.md`
**Program under correction:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md`
**Review baseline SHA:** `e9ab0fc623c22bd372ba9c8c2609dfcf74609f84`

---

## Status rules

- `[x]` means implemented, documented, tested, and supported by recorded evidence.
- `[ ]` remains incomplete.
- No first-party lint suppression is accepted at any point in this pass.
- This pass does not touch `crates/chess-app`, `crates/chess-core` production code, `crates/chess-search`, `crates/chess-book`, `crates/chess-uci`, `crates/chess-tui`, or `crates/chess-console`.
- This pass is a bounded review-fix tracker under `docs/LEGACY_TODO_INDEX.md`'s "Bounded review-fix trackers" classification — registered there as part of CC-000 baseline work.
- Work one CC task at a time; each task lands in its own commit with its own tests passing before the next task begins.

---

# CC-000: Baseline confirmation

## CC-000.1 Review context

- [ ] Confirmed `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md` declares the review-fix program `Complete` and that an eight-pass independent verification found the large majority genuinely correct, but five specific claims false or overclaimed.
- [ ] Confirmed AR-003: "native" jargon remains in `ChessViewModel.kt:71,117`, player-visible via `ChessEngineErrorDialog`.
- [ ] Confirmed AR-004: no verify-first runtime observation is recorded anywhere; the added test is non-diagnostic of the actual regression.
- [ ] Confirmed AR-007: production guard code is correct, but the claimed behavioral duplicate-invocation tests do not exist.
- [ ] Confirmed AR-011: the required end-to-end promotion test (or documented-impractical fallback) is absent.
- [ ] Confirmed the closure-evidence document cites CI run IDs for a superseded SHA (`6d9a84d`) rather than the actual final tree (`e9ab0fc`), whose own runs (`31419183264`, `31419183273`) exist and are green but are uncited.
- [ ] Confirmed the three minor secondary notes: AR-006's undocumented `isScrollInProgress` scope assumption, AR-020's missing e2-emptiness assertion, AR-016's uncovered Resign-dialog contrast pairing.
- [ ] Recorded the review baseline SHA: `e9ab0fc623c22bd372ba9c8c2609dfcf74609f84`.

## CC-000.2 Authority registration

- [ ] Registered `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md` in `docs/LEGACY_TODO_INDEX.md`'s "Bounded review-fix trackers" section and historical inventory, following the identical precedent of the four trackers already listed there.
- [ ] Updated `scripts/task_post_port_review_fix_audit.sh`'s registration/count checks to match.

## CC-000.3 Scope discipline

- [ ] Reinspected each of the five confirmed findings and three minor notes immediately before implementing its fix, in case newer source already resolved it.
- [ ] Did not reopen any other AR-00N task from the parent program.
- [ ] Did not relitigate any already-resolved QI/FQI pre-implementation item from the prior two rounds.

---

# CC-001: Fix AR-003 — remove remaining "native" jargon

## CC-001.1 Fix

- [ ] `ChessViewModel.kt:71`'s error message no longer contains "native".
- [ ] `ChessViewModel.kt:117`'s error message no longer contains "native".
- [ ] Full re-sweep of `android-harness/android-app/src/main/kotlin` for "native"/"JNI"/"shared layer"/"architecture" in any player-reachable string completed; any further instance corrected.
- [ ] `ReviewFixArchitectureTest.kt`'s structural check broadened to cover the whole module (or an equivalent-coverage sibling test added), not just `SetupScreen.kt`, with any genuinely-internal-only allowlist entries justified inline.

## CC-001.2 Tests

- [ ] Broadened structural test passes on corrected strings.
- [ ] Confirmed (implementation-time sanity check) the broadened test fails if "native" is temporarily reintroduced into `ChessViewModel.kt`'s error strings.
- [ ] Any test hard-coding the old error-string text is updated and remains green.

---

# CC-002: Fix AR-004 — perform the verify-first system-bar observation

## CC-002.1 Fix

- [ ] Genuine runtime observation performed (via permanent Android CI's emulator job if no local API 35 environment is available) distinguishing dark-background-correct from stock-light-regressed system-bar rendering, beyond the existing icon-appearance-only check.
- [ ] If bars render incorrectly: `WindowCompat`/`WindowInsetsControllerCompat`/`enableEdgeToEdge()` call added in `MainActivity.kt`, re-verified.
- [ ] If bars already render correctly: the specific responsible mechanism recorded explicitly in this section, not left unexplained.
- [ ] Existing `styles.xml` legacy attributes retained regardless of outcome.

## CC-002.2 Tests

- [ ] The diagnostic check (new or existing) is shown to actually distinguish the two states it claims to — described here, not just asserted.

---

# CC-003: Fix AR-007 — add missing behavioral duplicate-invocation tests

## CC-003.1 Fix

- [ ] Attempted a genuine behavioral test seam (fake/instrumented game handle, or a real androidTest driving the app end-to-end) proving no second operation launches / no state mutation / no new error on rapid duplicate invocation, for at least one representative function.
- [ ] If a genuine seam proved impractical: AR-007.2's checkboxes in `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md` reworded to accurately describe only what is actually proven (predicate correctness + static guard-ordering), with the stronger unproven claim removed or explicitly caveated.
- [ ] Whichever path taken is recorded explicitly here, with reasoning.

## CC-003.2 Tests

- [ ] `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md`'s AR-007.2 section accurately reflects actual test evidence after this task.

---

# CC-004: Fix AR-011 — add missing end-to-end promotion test

## CC-004.1 Fix

- [ ] End-to-end instrumentation test added: real board taps reach a promotion-eligible position via a deterministic fixture, promotion dialog opens through the real production flow (not direct `PromotionDialog` invocation), a real tap selects a promotion piece, resulting move/snapshot asserted correct.
- [ ] If genuinely impractical after a real attempt: specific blocker documented here instead of the checkbox being left silently unexplained.

## CC-004.2 Tests

- [ ] The end-to-end test (or documented-blocker fallback) is this task's deliverable.

---

# CC-005: Fix closure-evidence CI citation

## CC-005.1 Fix

- [ ] `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md`'s "Permanent exact-source-SHA CI" section updated to cite general/Rust CI run `31419183264` and Android CI run `31419183273` (with their own job IDs/conclusions) against SHA `e9ab0fc623c22bd372ba9c8c2609dfcf74609f84`.
- [ ] The `6d9a84d` runs retained as supporting evidence that no source/test file differs between the two SHAs, clearly distinguished from the authoritative final-SHA citation.

## CC-005.2 Tests

- [ ] N/A — documentation-only. Both new run IDs independently re-queried via `gh` during implementation and confirmed to match what is written.

---

# CC-006: Document AR-006's residual auto-scroll assumption

## CC-006.1 Fix

- [ ] Inline comment added at the `followLatest`/`snapshotFlow` collector in `GamePanels.kt` documenting the single-row-append assumption and that a future bulk-history-replace would need re-examination.

## CC-006.2 Tests

- [ ] N/A — documentation-only; the two existing auto-scroll tests remain unaffected and green.

---

# CC-007: Strengthen AR-020's rotation test

## CC-007.1 Fix

- [ ] `PortraitRotationInstrumentedTest.kt` asserts no `"e2 pawn"` node exists after rotation, alongside the existing `"e4 pawn"` presence assertion.

## CC-007.2 Tests

- [ ] The strengthened assertion is itself the test; reasoned to be meaningful (would catch a hypothetical move-duplication bug).

---

# CC-008: Add Resign-dialog contrast pairing

## CC-008.1 Fix

- [ ] `ThemeContrastTest.kt` gains a `Danger`-on-`SurfaceElevated` assertion (or equivalent) for the Resign confirmation dialog's confirm button.

## CC-008.2 Tests

- [ ] The added assertion passes given current token values.

---

# CC-009: Final validation and closure

## CC-009.1 Validation

- [ ] Android app JVM/unit tests pass, including CC-001/CC-003/CC-008 additions.
- [ ] Android lint passes.
- [ ] CC-004's instrumentation addition passes.
- [ ] CC-002's runtime observation was actually performed (CI-executed acceptable) and recorded.
- [ ] `bash scripts/dev.sh fast` passes.

## CC-009.2 Closure

- [ ] `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md`'s five previously-inaccurate checkboxes/narrative corrected in place to reflect what CC-001 through CC-005 actually established.
- [ ] `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md` updated per CC-005.
- [ ] Exact commands, results, and CI run/job evidence recorded below.

```text
Implementation start SHA:
Final source SHA:

Android app unit/lint results:
CC-004 instrumentation result:
CC-002 runtime observation result:
bash scripts/dev.sh fast result:

Permanent CI run/job IDs (if cross-workspace changes require it):
```

## CC-009 acceptance

- [ ] Every CC-001 through CC-008 task is `[x]` with its own recorded evidence.
- [ ] No first-party lint suppression was added anywhere in this pass.
- [ ] No existing green test was weakened or deleted to obtain a green run.
- [ ] This document's Status header updated to `Complete` only once all of the above holds.
