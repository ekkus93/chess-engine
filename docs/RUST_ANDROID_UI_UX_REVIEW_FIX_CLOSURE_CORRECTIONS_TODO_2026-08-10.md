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

## CC-000.2b Pre-implementation review resolution (QI-001 through QI-012)

- [ ] Read `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_QUESTIONS_AND_ISSUES_2026-08-10.md` in full.
- [ ] Confirmed all twelve items were resolved and incorporated into the spec's §2.1 (closure-SHA protocol), CC-001 through CC-005, and CC-009, and into this TODO's matching sections. None was rejected on a factual-precedent basis (unlike one item in the parent program's first review round).

## CC-000.3 SHA tracking (§2.1 closure-SHA protocol)

- [ ] Review baseline SHA (state this spec/TODO pair reviewed): `e9ab0fc623c22bd372ba9c8c2609dfcf74609f84`.
- [ ] Implementation-start SHA (captured immediately after CC-000 lands): `_____________________________`
- [ ] Confirmed these are not conflated with each other or with the eventual final correction SHA anywhere in this document.

## CC-000.4 Scope discipline

- [ ] Reinspected each of the five confirmed findings and three minor notes immediately before implementing its fix, in case newer source already resolved it.
- [ ] Did not reopen any other AR-00N task from the parent program.
- [ ] Did not relitigate any already-resolved QI/FQI pre-implementation item from the prior two rounds.

---

# CC-001: Fix AR-003 — remove remaining "native" jargon

## CC-001.1 Fix

- [ ] `ChessViewModel.kt:71`'s error message no longer contains "native".
- [ ] `ChessViewModel.kt:117`'s error message no longer contains "native".
- [ ] Full re-sweep of `android-harness/android-app/src/main/kotlin` for "native"/"JNI"/"shared layer"/"architecture" in any production string literal completed; any further instance corrected.
- [ ] `ReviewFixArchitectureTest.kt`'s structural check rebuilt as a blanket forbid-with-narrow-allowlist rule over every production string literal in the module (not a player-reachability inference, and not scoped to one file), per spec §3.2/QI-009.
- [ ] Each allowlist entry (the `check()` messages and the one `Log.e` call) is exact/narrow, justified inline, and tied to a genuinely internal-only sink.

## CC-001.2 Tests

- [ ] Broadened structural test passes on corrected strings.
- [ ] Confirmed (implementation-time sanity check) the broadened test fails if "native" is temporarily reintroduced into `ChessViewModel.kt`'s error strings.
- [ ] Any test hard-coding the old error-string text is updated and remains green.

---

# CC-002: Fix AR-004 — perform the verify-first system-bar observation

**Note:** this task is explicitly exempted from the one-task/one-commit rule (spec §4.2/QI-003) and lands as two sub-tasks, CC-002A (always) and CC-002B (only if CC-002A finds a real defect).

## CC-002A: Runtime observation

- [ ] Genuine runtime observation performed (via permanent Android CI's emulator job if no local API 35 environment is available) distinguishing dark-background-correct from stock-light-regressed system-bar rendering, beyond the existing icon-appearance-only check.
- [ ] Observation-evidence contract satisfied (spec §4.3/QI-004), recorded here: API level; emulator/device configuration; programmatic vs. screenshot/pixel-based proof (or both); expected color/tolerance if pixel-based; preserved artifact location if any; exact CI run/job ID.
- [ ] If the existing icon-appearance-only check is judged sufficient after this investigation, that reasoning and its evidence recorded explicitly here.

## CC-002B: Conditional remediation (only if CC-002A found a defect)

- [ ] `WindowCompat`/`WindowInsetsControllerCompat`/`enableEdgeToEdge()` call added in `MainActivity.kt`.
- [ ] Re-verified against the same observation-evidence contract as CC-002A.
- [ ] Existing `styles.xml` legacy attributes retained regardless of outcome.
- [ ] If CC-002A found no defect: this sub-task explicitly recorded as not needed, referencing CC-002A's evidence, rather than left silently absent.

## CC-002 Tests

- [ ] CC-002A's observation evidence is the test evidence for that sub-task.
- [ ] If CC-002B landed, its re-verification is its test evidence.

---

# CC-003: Correct AR-007 behavioral-evidence claims; add behavioral coverage where practical

## CC-003.1 Fix

- [ ] Attempted a genuine behavioral test seam (fake/instrumented game handle, or a real androidTest driving the app end-to-end).
- [ ] If a seam was built: **all three** of `restartGame()`, `resign()`, and `submitMove()` tested behaviorally, not just one representative function (spec §5.2/QI-005) — each covering both the duplicate-invocation case and the `cleanupRequired` case, proving no second operation launches, no state mutation, no new error.
- [ ] If a genuine seam proved impractical: AR-007.2's checkboxes in `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md` reworded to accurately describe only what is actually proven (predicate correctness + static guard-ordering), with the stronger unproven claim removed or explicitly caveated — not a middle ground where one function is tested and the other two claimed by analogy.
- [ ] Whichever path taken is recorded explicitly here, with reasoning.

## CC-003.2 Tests

- [ ] `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md`'s AR-007.2 section accurately reflects actual test evidence after this task, for all three functions if a seam was built.

---

# CC-004: Fix AR-011 — add missing end-to-end promotion test

## CC-004.1 Fix

- [ ] End-to-end instrumentation test added: promotion-eligible position reached via one of the two bounded mechanisms (spec §6.2/QI-010) — preferably a real legal-move sequence driven through the UI, or a narrowly-scoped test-only fixture seam (never production/player-facing) if that proves impractical — promotion dialog opens through the real production flow (not direct `PromotionDialog` invocation), a real tap selects a promotion piece, resulting move/snapshot asserted correct.
- [ ] Confirmed no general/production FEN-loading capability or Kotlin chess-rule logic was added to make the fixture work.
- [ ] If genuinely impractical after a real attempt at both mechanisms: specific blocker documented here instead of the checkbox being left silently unexplained.

## CC-004.2 Tests

- [ ] The end-to-end test (or documented-blocker fallback) is this task's deliverable.

---

# CC-005: Fix closure-evidence CI citation

## CC-005.1 Fix

- [ ] `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md`'s "Permanent exact-source-SHA CI" section updated to cite general/Rust CI run `31419183264` and Android CI run `31419183273` (with their own job IDs/conclusions) against SHA `e9ab0fc623c22bd372ba9c8c2609dfcf74609f84`.
- [ ] The `6d9a84d` runs retained as supporting evidence, but **not** described as proof the two trees are source-identical (spec §7.2/QI-007) — instead, the literal output of an actual git comparison (`git diff --stat 6d9a84d..e9ab0fc` and/or a tree-hash comparison) is recorded in the closure-evidence document as the backing evidence for that specific claim.

## CC-005.2 Tests

- [ ] N/A — documentation-only. Both new run IDs independently re-queried via `gh` during implementation and confirmed to match what is written; the recorded git comparison command independently re-run and confirmed to match its recorded output.

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
- [ ] CC-002A's runtime observation was actually performed (CI-executed acceptable) and recorded; CC-002B's re-verification recorded if it landed.
- [ ] `bash scripts/dev.sh fast` passes.
- [ ] **Permanent CI is mandatory (spec §11.1/QI-011), not conditional**: permanent Android CI and permanent general/Rust CI are both green on the exact final correction SHA, following the closure-SHA protocol (spec §2.1).

## CC-009.2 Provenance-preserving correction of the parent TODO (QI-012)

- [ ] `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md`'s five previously-inaccurate checkboxes corrected in place, each using wording that distinguishes: what was originally claimed; that it was corrected by this pass (naming the specific CC-00N task); what the actual final evidence is now and as of which SHA. No corrected checkbox is reworded to imply the original AR-00N implementation satisfied it unaided.

## CC-009.3 Authority closure (QI-008)

- [ ] This document's `Status:` header updated to `Complete`.
- [ ] `docs/LEGACY_TODO_INDEX.md`'s "Bounded review-fix trackers" entry for this tracker updated from "in progress" to "completed."
- [ ] `scripts/task_post_port_review_fix_audit.sh` updated if any existing assertion assumed an in-progress state.
- [ ] Confirmed no active implementation TODO is registered as a side effect of this closure.
- [ ] Confirmed no temporary correction/validation helper remains in the tree before final exact-SHA validation.

## CC-009.4 Closure evidence

- [ ] `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md` updated per CC-005.
- [ ] Exact commands, results, and CI run/job evidence recorded below, per the closure-SHA protocol (spec §2.1) — recorded once, at the terminal trigger commit, with no further citation-chasing edit afterward.

```text
Review baseline SHA:        e9ab0fc623c22bd372ba9c8c2609dfcf74609f84
Implementation start SHA:
Final correction source SHA:

Android app unit/lint results:
CC-004 instrumentation result:
CC-002A runtime observation result:
CC-002B remediation result (if applicable):
bash scripts/dev.sh fast result:

Permanent Android CI run/job IDs:
Permanent general/Rust CI run/job IDs:
```

## CC-009 acceptance

- [ ] Every CC-001 through CC-008 task is `[x]` with its own recorded evidence.
- [ ] No first-party lint suppression was added anywhere in this pass.
- [ ] No existing green test was weakened or deleted to obtain a green run.
- [ ] Permanent CI (CC-009.1) is green on the exact final correction SHA, recorded once per the closure-SHA protocol.
- [ ] This document's Status header updated to `Complete` only once all of the above holds.
