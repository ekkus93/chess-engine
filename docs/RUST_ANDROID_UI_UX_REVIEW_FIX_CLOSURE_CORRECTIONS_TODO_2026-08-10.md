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
- `N/A — <reason>` (FFQI-001) is permitted only for an explicitly mutually-exclusive branch (CC-002B, CC-003, CC-004) whose sibling disposition was selected and completed with evidence instead. An `N/A` branch does not make its enclosing task incomplete; the task's own disposition checkbox must still be `[x]` before the task is considered complete. Prefer writing `N/A — <reason>` over leaving an unchecked, unexplained `[ ]` for an untaken alternative — an unexplained `[ ]` reads as unfinished work, which it isn't.
- No first-party lint suppression is accepted at any point in this pass.
- This pass does not touch `crates/chess-app`, `crates/chess-core` production code, `crates/chess-search`, `crates/chess-book`, `crates/chess-uci`, `crates/chess-tui`, or `crates/chess-console`.
- This pass is a bounded review-fix tracker under `docs/LEGACY_TODO_INDEX.md`'s "Bounded review-fix trackers" classification — registered there as part of CC-000 baseline work.
- Work one CC task at a time; each task lands in its own commit with its own tests passing before the next task begins.

---

# CC-000: Baseline confirmation

## CC-000.1 Review context

- [x] Confirmed `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md` declares the review-fix program `Complete` and that an eight-pass independent verification found the large majority genuinely correct, but five specific claims false or overclaimed.
- [x] Confirmed AR-003: "native" jargon remains in `ChessViewModel.kt:71,117`, player-visible via `ChessEngineErrorDialog`.
- [x] Confirmed AR-004: no verify-first runtime observation is recorded anywhere; the added test is non-diagnostic of the actual regression.
- [x] Confirmed AR-007: production guard code is correct, but the claimed behavioral duplicate-invocation tests do not exist.
- [x] Confirmed AR-011: the required end-to-end promotion test (or documented-impractical fallback) is absent.
- [x] Confirmed the closure-evidence document cites CI run IDs for a superseded SHA (`6d9a84d`) rather than the actual final tree (`e9ab0fc`), whose own runs (`31419183264`, `31419183273`) exist and are green but are uncited.
- [x] Confirmed the three minor secondary notes: AR-006's undocumented `isScrollInProgress` scope assumption, AR-020's missing e2-emptiness assertion, AR-016's uncovered Resign-dialog contrast pairing.
- [x] Recorded the review baseline SHA: `e9ab0fc623c22bd372ba9c8c2609dfcf74609f84`.

## CC-000.2 Authority registration

- [x] Registered `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md` in `docs/LEGACY_TODO_INDEX.md`'s "Bounded review-fix trackers" section and historical inventory, following the identical precedent of the four trackers already listed there.
- [x] Updated `scripts/task_post_port_review_fix_audit.sh`'s registration/count checks to match.

## CC-000.2b Pre-implementation review resolution (QI-001 through QI-012)

- [x] Read `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_QUESTIONS_AND_ISSUES_2026-08-10.md` in full.
- [x] Confirmed all twelve items were resolved and incorporated into the spec's §2.1 (closure-SHA protocol), CC-001 through CC-005, and CC-009, and into this TODO's matching sections. None was rejected on a factual-precedent basis (unlike one item in the parent program's first review round).
- [x] Read `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_FOLLOWUP_QUESTIONS_AND_ISSUES_2026-08-10.md` in full.
- [x] Confirmed FQI-001 (the closure-SHA protocol's terminal step was literally impossible — it required recording CI run IDs inside the commit that triggers them, before those IDs exist), FQI-002 (several tasks' checkboxes couldn't honestly all reach `[x]` given their own legitimate mutually-exclusive dispositions), and FQI-003 (CC-005's git evidence needed to be path-scoped to the actual claim, not a whole-tree comparison that would show inequality for unrelated reasons) were all resolved and incorporated into spec §2.1/§11.4 and CC-002B/CC-003/CC-004/CC-005, and into this TODO's matching sections.
- [x] Read `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_FINAL_FOLLOWUP_QUESTIONS_AND_ISSUES_2026-08-10.md` in full.
- [x] Confirmed FFQI-001 (`N/A` had no formal completion semantics), FFQI-002 (the terminal-trigger decision was based on a "documentation vs. source" file-category guess rather than actual workflow execution), and FFQI-003 (a stale `§6` cross-reference and one remaining unconditional "CC-004 instrumentation addition" phrase) were resolved in the Status rules, spec §2.1, and spec §11.1.

## CC-000.3 SHA tracking (§2.1 closure-SHA protocol)

- [x] Review baseline SHA (state this spec/TODO pair reviewed): `e9ab0fc623c22bd372ba9c8c2609dfcf74609f84`.
- [x] Implementation-start SHA (captured immediately after CC-000 lands): `fe97117a9d5315a2ae4bff344ed8b22f52d8c86e`
- [x] Confirmed these are not conflated with each other or with the eventual final correction SHA anywhere in this document.

## CC-000.4 Scope discipline

- [x] Reinspected each of the five confirmed findings and three minor notes immediately before implementing its fix, in case newer source already resolved it.
- [x] Did not reopen any other AR-00N task from the parent program.
- [x] Did not relitigate any already-resolved QI/FQI pre-implementation item from the prior two rounds.

---

# CC-001: Fix AR-003 — remove remaining "native" jargon

## CC-001.1 Fix

- [x] `ChessViewModel.kt:71`'s error message no longer contains "native".
- [x] `ChessViewModel.kt:117`'s error message no longer contains "native".
- [x] Full re-sweep of `android-harness/android-app/src/main/kotlin` for "native"/"JNI"/"shared layer"/"architecture" in any production string literal completed; any further instance corrected.
- [x] `ReviewFixArchitectureTest.kt`'s structural check rebuilt as a blanket forbid-with-narrow-allowlist rule over every production string literal in the module (not a player-reachability inference, and not scoped to one file), per spec §3.2/QI-009.
- [x] Each allowlist entry (the `check()` messages and the one `Log.e` call) is exact/narrow, justified inline, and tied to a genuinely internal-only sink.

## CC-001.2 Tests

- [x] Broadened structural test passes on corrected strings.
- [x] Confirmed (implementation-time sanity check) the broadened test fails if "native" is temporarily reintroduced into `ChessViewModel.kt`'s error strings.
- [x] Any test hard-coding the old error-string text is updated and remains green.

---

# CC-002: Fix AR-004 — perform the verify-first system-bar observation

**Disposition:** `remediation-not-needed`.

## CC-002A: Runtime observation

- [x] Genuine rendered-state observation performed on permanent Android CI at exact SHA `6e5fdec216f013fae1257c67899fa26cce02d5e6`: workflow run `31431380577`, API-35 emulator job `93595365511`, conclusion `success`.
- [x] Observation-evidence contract satisfied: API 35, x86_64 `google_apis`, Pixel 2 profile, headless SwiftShader emulator; actual `UiAutomation` framebuffer screenshot sampled in the status/navigation-bar insets; expected product background `#0B1220`; RGB tolerance ±12/channel; each sampled bar region required at least 70% matching pixels. Screenshot `system-bars-api35.png` was preserved under `/sdcard/Download/RustChessEvidence` and included in the permanent UI-evidence artifact.
- [x] Existing icon-appearance flags remained supporting assertions only. CC-002A was satisfied by the new framebuffer/pixel diagnostic, not by those flags alone.

## CC-002B: Conditional remediation

- [x] **Disposition reached:** `remediation-not-needed` — CC-002A proved the API-35 system bars already render with the dark product background.

N/A — `remediation-required`: no `MainActivity.kt`/WindowCompat/edge-to-edge production change was needed because the diagnostic passed on the real API-35 emulator.

- [x] `remediation-not-needed` is backed by run `31431380577`, job `93595365511`, exact SHA `6e5fdec216f013fae1257c67899fa26cce02d5e6`.

## CC-002 Tests

- [x] CC-002A runtime diagnostic and the full Android connected-test step passed in job `93595365511`.

N/A — CC-002B re-verification: no remediation commit landed, so no post-fix rerun was required.

---

# CC-003: Correct AR-007 behavioral-evidence claims; add behavioral coverage where practical

## CC-003.1 Fix

CC-003 reaches exactly one of two dispositions (FQI-002); mark the untaken one `N/A`.

- [ ] Attempted a genuine behavioral test seam (fake/instrumented game handle, or a real androidTest driving the app end-to-end).
- [ ] **Disposition reached:** either "seam-built" or "claims-downgraded" — recorded explicitly here, with reasoning.
- [ ] If seam-built: **all three** of `restartGame()`, `resign()`, and `submitMove()` tested behaviorally, not just one representative function (spec §5.2/QI-005) — each covering both the duplicate-invocation case and the `cleanupRequired` case, proving no second operation launches, no state mutation, no new error. *(N/A if claims-downgraded.)*
- [ ] If claims-downgraded: AR-007.2's checkboxes in `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md` reworded to accurately describe only what is actually proven (predicate correctness + static guard-ordering), with the stronger unproven claim removed or explicitly caveated — not a middle ground where one function is tested and the other two claimed by analogy. *(N/A if seam-built.)*

## CC-003.2 Tests

- [ ] `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md`'s AR-007.2 section accurately reflects actual test evidence after this task, for all three functions if a seam was built.

---

# CC-004: Fix AR-011 — add missing end-to-end promotion test

## CC-004.1 Fix

CC-004 reaches exactly one of three dispositions (FQI-002); mark the other two `N/A`.

- [ ] **Disposition reached:** "UI-driven fixture," "test-only fixture seam," or "documented blocker" — recorded explicitly here.
- [ ] If UI-driven fixture or test-only fixture seam: end-to-end instrumentation test added — promotion dialog opens through the real production flow (not direct `PromotionDialog` invocation), a real tap selects a promotion piece, resulting move/snapshot asserted correct. Confirmed no general/production FEN-loading capability or Kotlin chess-rule logic was added to make the fixture work. *(N/A if documented blocker.)*
- [ ] If documented blocker: specific blocker documented here instead of the checkbox being left silently unexplained; no new instrumentation test added. *(N/A if a fixture disposition was reached.)*

## CC-004.2 Tests

- [ ] The end-to-end test (or documented-blocker fallback) is this task's deliverable.

---

# CC-005: Fix closure-evidence CI citation

## CC-005.1 Fix

- [ ] `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md`'s "Permanent exact-source-SHA CI" section updated to cite general/Rust CI run `31419183264` and Android CI run `31419183273` (with their own job IDs/conclusions) against SHA `e9ab0fc623c22bd372ba9c8c2609dfcf74609f84`.
- [ ] The `6d9a84d` runs retained as supporting evidence, but **not** described as proof the two trees are source-identical (spec §7.2/QI-007) — instead, the path-scoped comparison `git diff --exit-code 6d9a84d..e9ab0fc -- android-harness crates` (FQI-003 — scoped to the actual claim, not a whole-tree diff that would show inequality merely because documentation changed) is recorded, along with a supplementary unrestricted `git diff --name-only` showing exactly which documentation/authority files did change.

## CC-005.2 Tests

- [ ] N/A — documentation-only. Both new run IDs independently re-queried via `gh` during implementation and confirmed to match what is written; the recorded path-scoped git comparison independently re-run and confirmed to match its recorded output (empty/zero exit code).

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
- [ ] CC-004's disposition-dependent validation satisfied: its instrumentation test passes if a fixture disposition was reached, or its documented-blocker record is complete if that disposition was reached instead (FQI-002).
- [ ] CC-002A's runtime observation was actually performed (CI-executed acceptable) and recorded; CC-002B's disposition (remediation-required and re-verified, or remediation-not-needed) recorded.
- [ ] `bash scripts/dev.sh fast` passes.
- [ ] **Permanent CI is mandatory (spec §11.1/QI-011), not conditional**: permanent Android CI and permanent general/Rust CI are both green on the exact final correction SHA, following the closure-SHA protocol (spec §2.1) — confirmed by independently querying `gh` after the terminal trigger push and reported in the final implementation handoff (FQI-001 — not by writing those run IDs back into the repository).

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
- [ ] All repository-resident evidence recorded below (FQI-001/§2.1) — everything knowable before the terminal trigger push.
- [ ] Terminal permanent CI run/job IDs are **not** added to this template after the fact — per §2.1, they are external GitHub Actions metadata, independently verified via `gh`, and reported in this pass's final implementation handoff instead of being written back into the repository.

```text
Review baseline SHA:        e9ab0fc623c22bd372ba9c8c2609dfcf74609f84
Implementation start SHA:
Final correction source SHA:

Android app unit/lint results:
CC-004 disposition and result:
CC-002A runtime observation result:
CC-002B disposition and result:
bash scripts/dev.sh fast result:

(Terminal permanent CI run/job IDs: reported externally in the final
implementation handoff per §2.1 — not recorded in this file.)
```

## CC-009 acceptance

- [ ] Every CC-001 through CC-008 task is `[x]` with its own recorded evidence — for CC-002B/CC-003/CC-004, this means the task's disposition checkbox is `[x]` with the selected branch fully evidenced and the untaken branch marked `N/A`, per the Status rules' `N/A` definition.
- [ ] No first-party lint suppression was added anywhere in this pass.
- [ ] No existing green test was weakened or deleted to obtain a green run.
- [ ] Permanent CI (CC-009.1) is green on the exact final correction SHA, independently confirmed via `gh` per the closure-SHA protocol and reported in the final implementation handoff — not recorded in the repository.
- [ ] This document's Status header updated to `Complete` only once all of the above holds.
