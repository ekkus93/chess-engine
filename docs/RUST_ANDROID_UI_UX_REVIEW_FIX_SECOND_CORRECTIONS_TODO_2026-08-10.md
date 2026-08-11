# Rust Android UI/UX Review-Fix Second Corrections TODO — 2026-08-10

**Status:** proposed / not started
**Branch:** `master`
**Spec:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SECOND_CORRECTIONS_SPEC_2026-08-10.md`
**Program under correction:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md`
**Review baseline SHA:** `a943b67abf4b187f1840a790ad9372d27576c3c5`

---

## Status rules

- `[x]` means implemented, documented, tested, and supported by recorded evidence.
- `[ ]` remains incomplete.
- `N/A — <reason>` is permitted only for an explicitly mutually-exclusive branch whose sibling disposition was selected and completed with evidence instead. An `N/A` branch does not make its enclosing task incomplete; the task's own disposition checkbox must still be `[x]`.
- No first-party lint suppression is accepted at any point in this pass.
- This pass does not touch `crates/chess-app`, `crates/chess-core` production code, `crates/chess-search`, `crates/chess-book`, `crates/chess-uci`, `crates/chess-tui`, or `crates/chess-console`.
- This pass is a bounded review-fix tracker under `docs/LEGACY_TODO_INDEX.md`'s "Bounded review-fix trackers" classification — registered there as part of SC-000 baseline work.
- Terminal permanent CI run/job IDs are external GitHub Actions metadata, independently verified via `gh` and reported in the final implementation handoff — never written back into the repository (spec §2.1).
- Work one SC task at a time; each task lands in its own commit with its own tests passing before the next task begins.

---

# SC-000: Baseline confirmation

## SC-000.1 Review context

- [x] Confirmed CC-001 fixed its two originally-flagged strings but the identical defect class recurs in `crates/chess-jni/kotlin/.../ChessGame.kt`, outside the original scanner root.
- [x] Confirmed CC-002A's closing TODO text dropped emulator/device configuration, numeric pixel tolerance/threshold detail, and preserved-artifact path information that existed in intermediate evidence.
- [x] Confirmed CC-004's `documented blocker` rested on prose only: no preserved CI run/artifact/script exists for the bounded promotion-path search.
- [x] Recorded the review baseline SHA: `a943b67abf4b187f1840a790ad9372d27576c3c5`.

## SC-000.1b Pre-implementation review resolution

- [x] Read `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SECOND_CORRECTIONS_QUESTIONS_AND_ISSUES_2026-08-10.md` in full.
- [x] Confirmed all six review items are incorporated into the current spec/TODO: whole-source-root jargon disposition, mechanical Gradle source-root coverage, dual-source system-bar evidence, bounded multi-commit artifact fallback, production-API seam tripwire, and the §6.3 provenance cross-reference.

## SC-000.2 Authority registration

- [x] Confirmed `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SECOND_CORRECTIONS_TODO_2026-08-10.md` is already registered in `docs/LEGACY_TODO_INDEX.md` as an in-progress bounded review-fix tracker by the pre-implementation spec-resolution commit.
- [x] Confirmed `scripts/task_post_port_review_fix_audit.sh` already registers the second-corrections spec/TODO and validates the tracker is listed under the bounded-review classification.

## SC-000.3 SHA tracking

- [x] Review baseline SHA: `a943b67abf4b187f1840a790ad9372d27576c3c5`.
- [ ] Implementation-start SHA (captured immediately after SC-000 lands): `PENDING_SC000_COMMIT_SHA`

## SC-000.4 Scope discipline

- [x] Reinspected each finding immediately before implementation; all three remain present at activation.
- [x] Did not reopen any other CC-00N or AR-00N task.

---

# SC-001: Fix the recurred "native" jargon defect in `ChessGame.kt`

## SC-001.1 Fix

- [ ] Read `android-app/build.gradle.kts`'s actual `sourceSets`/`java.srcDir` configuration to confirm the exact set of Gradle-compiled source directories for this app module (not assumed).
- [ ] For each of the six "native"-containing strings in `ChessGame.kt` (lines ~49, 52, 54, 78, 84, 215), determined genuine player-reachability by tracing to `ChessViewModel.kt`'s `publishError()` path.
- [ ] Every genuinely player-reachable string reworded to remove "native" while preserving meaning.
- [ ] Checked `android-harness/host-jvm/src/test/kotlin/**` for hard-coded old string text; updated if found.
- [ ] `ReviewFixArchitectureTest.kt` (or a sibling test) extended to scan **all** Gradle-compiled source directories of this module, not just `android-harness/android-app/src/main/kotlin`.
- [ ] The six originally-reported strings treated as the confirmed triggering defect, not the entire boundary: every additional forbidden-term string literal the expanded scan finds elsewhere in `crates/chess-jni/kotlin/src/main/kotlin/**` (e.g. in `ChessEngine.kt`) is individually dispositioned — reworded, or allowlisted narrowly with inline justification.
- [ ] Any string judged genuinely internal-only (original six or newly found) is allowlisted narrowly and justified inline, matching the existing pattern.
- [ ] Mechanical future-directory invariant implemented: either the test derives production source roots from Gradle/source-set metadata at runtime, or a structural assertion parses `build.gradle.kts`'s actual `java.srcDir(...)` declarations and fails if any declared root is absent from the scanner's configured roots.

## SC-001.2 Tests

- [ ] Extended structural test scans both current source directories and passes on all corrected strings (original six plus any newly found).
- [ ] Implementation-time sanity check: confirmed the extended test fails if "native" is temporarily reintroduced into `ChessGame.kt`.
- [ ] Implementation-time sanity check: confirmed the mechanical future-directory invariant fails when a hypothetical third `java.srcDir(...)` is temporarily added to `build.gradle.kts` without updating the scanner (then reverted).
- [ ] Any updated host-JVM test remains green.
- [ ] Existing Kotlin/JVM and instrumentation tests referencing `ChessGame`/`ChessGameSnapshot` remain green.

---

# SC-002: Restore CC-002A's dropped observation-evidence fields

## SC-002.1 Fix

- [ ] Re-read `SystemBarAppearanceInstrumentedTest.kt`'s actual API-level, tolerance, and threshold values.
- [ ] Re-read `.github/workflows/android.yml`'s actual emulator/device configuration (API level, ABI, system image, device profile, GPU/rendering mode) and its screenshot pull/artifact-upload steps — this, not the test file, is the source of truth for device/emulator configuration.
- [ ] `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md`'s CC-002A section updated to include all six required contract fields (spec §4.3 of the CC program), reconciled against **both** sources, not blindly pasted from the old text.
- [ ] All three artifact-location layers recorded distinctly: device-side path, CI-workspace path after `adb pull`, and uploaded GitHub Actions artifact name/path.

## SC-002.2 Tests

- [ ] N/A — documentation-only. Restored text independently re-verified against both `SystemBarAppearanceInstrumentedTest.kt`'s and `.github/workflows/android.yml`'s actual current values.

---

# SC-003: Get real evidence for CC-004's promotion-position claim

## SC-003.1 Fix

- [ ] Checked the explicit architectural boundary **before** attempting the seam: would making the real production UI flow start from a promotion-eligible `ChessGame` state require adding production/native API surface (position/FEN injection) or changing `ChessGame`'s ownership model? If yes, the seam disposition is impractical immediately, without further attempt — proceed directly to `artifact-backed-blocker`.
- [ ] If the boundary check didn't immediately rule it out: attempted to build a narrowly-scoped, test-only fixture seam (androidTest-only, never production-reachable, no Kotlin chess-rule logic, no general FEN-loading feature) initializing a promotion-eligible position.
- [ ] **Disposition reached:** either "seam-built" (new end-to-end promotion instrumentation test added and passing) or "artifact-backed-blocker" (the existing prose claim replaced with a preserved, CI-run-backed search log) — recorded explicitly here, with the untaken branch marked `N/A`.
- [ ] If seam-built: end-to-end test drives the promotion dialog through the real production flow, taps a real promotion choice, and asserts the resulting move/snapshot is correct.
- [ ] If artifact-backed-blocker: landed as the authorized bounded multi-commit sequence (spec §5.2/§2.1 point 3) — (a) probe/helper + temporary CI workflow committed; (b) that commit's CI run executed and produced the artifact; (c) evidence/disposition recorded citing the real run/job/artifact IDs; (d) temporary workflow/helper removed before SC-004's closure validation. Not a second unverifiable prose restatement.

## SC-003.2 Tests

- [ ] If seam-built: the new instrumentation test passes and its permanent-CI run/job ID is recorded.
- [ ] If artifact-backed-blocker: the preserved search evidence's CI run/job/artifact IDs are recorded, and the temporary workflow/helper's removal is confirmed before final closure.

---

# SC-004: Final validation and closure

## SC-004.1 Validation

- [ ] Android app JVM/unit tests pass, including SC-001's extended structural test.
- [ ] Android lint passes.
- [ ] SC-003's new instrumentation test passes, if built.
- [ ] `bash scripts/task_post_port_review_fix_audit.sh` passes.
- [ ] `bash scripts/dev.sh fast` passes (expected mandatory, since this pass touches Kotlin source).
- [ ] Permanent Android CI and permanent general/Rust CI are both green on the exact final SHA, confirmed via `gh` per §2.1 and reported in the final implementation handoff — not recorded in the repository.

## SC-004.2 Authority closure

- [ ] This document's `Status:` header updated to `Complete`.
- [ ] `docs/LEGACY_TODO_INDEX.md`'s "Bounded review-fix trackers" entry for this tracker updated from "in progress" to "completed."
- [ ] `scripts/task_post_port_review_fix_audit.sh` updated to match.
- [ ] Confirmed no temporary correction/validation helper remains in the tree before final exact-SHA validation.

## SC-004.3 Provenance-preserving corrections

- [ ] CC-001's section in `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md` updated to record that SC-001 closed the `ChessGame.kt` recurrence, distinguishing what CC-001 originally established from what SC-001 added.
- [ ] CC-004's section updated to record that SC-003 replaced the unverifiable claim with real evidence (or strengthened it per whichever disposition was reached), distinguishing original vs. corrected evidence.

## SC-004.4 Closure evidence

```text
Review baseline SHA:          a943b67abf4b187f1840a790ad9372d27576c3c5
Implementation start SHA:
Final correction source SHA:

Android app unit/lint results:
SC-001 structural-test result:
SC-003 disposition and result:
bash scripts/task_post_port_review_fix_audit.sh result:
bash scripts/dev.sh fast result:

(Terminal permanent CI run/job IDs: reported externally in the final
implementation handoff per §2.1 — not recorded in this file.)
```

## SC-004 acceptance

- [ ] Every SC-001 through SC-003 task is `[x]` with its own recorded evidence.
- [ ] No first-party lint suppression was added anywhere in this pass.
- [ ] No existing green test was weakened or deleted to obtain a green run.
- [ ] Permanent CI is green on the exact final correction SHA, independently confirmed via `gh` and reported in the final implementation handoff.
- [ ] This document's Status header updated to `Complete` only once all of the above holds.
