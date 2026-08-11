# Rust Android UI/UX Review-Fix Second Corrections TODO — 2026-08-10

**Status:** Complete
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
- [x] Implementation-start SHA (captured immediately after SC-000 lands): `df9155171e84b1be295bf0cd482582d10e5b3d6c`

## SC-000.4 Scope discipline

- [x] Reinspected each finding immediately before implementation; all three remain present at activation.
- [x] Did not reopen any other CC-00N or AR-00N task.

---

# SC-001: Fix the recurred "native" jargon defect in `ChessGame.kt`

## SC-001.1 Fix

- [x] Read `android-app/build.gradle.kts`'s actual `sourceSets`/`java.srcDir` configuration: the app module compiles default `src/main/kotlin` plus `../../crates/chess-jni/kotlin/src/main/kotlin`.
- [x] Traced all six originally reported `ChessGame.kt` exception strings through the shared `RuntimeException` → `ChessViewModel.publishError()` path; all were treated as potentially player-visible and reworded without architecture jargon.
- [x] Reworded every additional forbidden-term string literal discovered by the expanded scan in `ChessEngine.kt`/`ChessGame.kt` rather than hiding them behind broad allowlists; this includes parser/error text and internal reaper thread names.
- [x] Checked host-JVM tests for hard-coded changed messages and synchronized any affected assertions.
- [x] `ReviewFixArchitectureTest.kt` now scans both current Gradle-compiled Kotlin production roots.
- [x] The only new JNI-root allowlist entries are the two exact `System.loadLibrary("chess_jni")` ABI/load-contract calls; the existing three exact `ChessViewModel` internal-only sinks remain narrowly justified.
- [x] Mechanical future-directory invariant implemented: the test parses every production `java.srcDir(...)` declaration in `android-app/build.gradle.kts` and fails if the configured scanner roots do not match the declared additional roots.

## SC-001.2 Tests

- [x] Extended `ReviewFixArchitectureTest` passes across both current production source directories.
- [x] Negative jargon sanity check passed: temporarily restoring `"native Android game returned a null handle"` made the structural test fail; restoring corrected text made it pass again.
- [x] Negative source-root sanity check passed: temporarily adding `java.srcDir("src/main/kotlin-third-fixture")` without scanner coverage made the structural test fail; reverting the declaration made it pass again.
- [x] `cargo build --locked -p chess-jni --release`, Android app lint/unit tests, host-JVM JNI tests, and Android instrumentation compilation all pass on the corrected working tree.

**Implementation-start SHA:** `df9155171e84b1be295bf0cd482582d10e5b3d6c`.

---

# SC-002: Restore CC-002A's dropped observation-evidence fields

## SC-002.1 Fix

- [x] Re-read `SystemBarAppearanceInstrumentedTest.kt`: API 35 assertion, ±12 RGB/channel tolerance, ≥0.70 matching-ratio threshold, and device-side screenshot filename/path verified.
- [x] Re-read `.github/workflows/android.yml`: API 35, x86_64, `google_apis`, Pixel 2 profile, SwiftShader/headless configuration, `adb pull`, and UI-evidence upload configuration verified.
- [x] CC-002A now records all six evidence-contract dimensions distinctly and reconciles them against both current sources.
- [x] All three artifact-location layers are explicit: device path, CI-workspace path, and uploaded artifact `rust-chess-android-ui-evidence-05ec27dd099fa5ad74f5e5ff0bea2ae1cc5a801c` / ID `9080725280`.

## SC-002.2 Tests

- [x] N/A — documentation-only correction; restored text was source-verified against both the instrumentation test and Android workflow before commit.

---

# SC-003: Replace CC-004's unverifiable promotion blocker with executable evidence

## SC-003.1 Fix

- [x] Checked the architectural boundary first: `ChessGame` has no arbitrary position/FEN injection and adding one solely for testing would expand production/native API surface, so no seam was added.
- [x] Converted the old blocker claim into a real, bounded, artifact-backed JNI search instead of accepting its prose assertion.
- [x] Evidence run `31447725972`, job `93645421851`, artifact `9085181028` disproved the blocker by finding a legal route within the original 12-human-turn bound.
- [x] Preserved discovered path: `a2a3 a3a4 a4a5 b2b3 e2e3 a5a6 b3b4 c2c3 g2g3 a6b7`, followed by promotion move `b7a8b`.
- [x] **Disposition reached:** `ui-driven-path-built`. The evidence made a fixture seam unnecessary and made `artifact-backed-blocker` factually invalid.

N/A — `seam-built`: no test-only or production position-injection seam was needed or added.

N/A — `artifact-backed-blocker`: the preserved real-JNI search found a promotion path, so retaining the blocker would be false.

- [x] Added `PromotionEndToEndInstrumentedTest`: normal production setup at depth 1, real board taps for the discovered path, real engine replies, real promotion dialog, Bishop tap, and authoritative `b7a8b`/white-bishop-on-`a8` snapshot assertions.
- [x] Temporary promotion probe test/workflow removed before clean permanent Android validation.

## SC-003.2 Tests

- [x] Historical discovery evidence: run `31447725972`, job `93645421851`, artifact `9085181028`; `RESULT=FOUND`, `FOUND_MOVE=b7a8b`.
- [x] Permanent Android source/test validation: run `31448304672` on exact SHA `99a5ffd277db22c8a3d383e0206dfa6c010e4506`, all three jobs successful.
- [x] API-35 connected job `93647206317` passed the full instrumentation suite including the real-flow promotion E2E test.
- [x] Host-JVM JNI job `93647206339` and Android lint/unit job `93647206354` also passed on the same SHA.

---

# SC-004: Final validation and closure

## SC-004.1 Validation

- [x] Android app JVM/unit tests and Android lint passed in bounded closure validation workflow run `31449306496` after `cargo build --locked -p chess-jni --release`.
- [x] Host-JVM JNI tests and Android instrumentation compilation passed in the same bounded closure validation run.
- [x] SC-003's real-flow promotion instrumentation test already passed in permanent Android run `31448304672`, API-35 job `93647206317`, on exact source/test SHA `99a5ffd277db22c8a3d383e0206dfa6c010e4506`.
- [x] `bash scripts/task_post_port_review_fix_audit.sh` passed before closure edits and again against the final candidate closure tree.
- [x] `bash scripts/dev.sh fast` passed against the final candidate closure tree.
- [x] No first-party Kotlin `@Suppress` or Rust `#[allow]`/`#[expect]` addition exists in the implementation diff from `df9155171e84b1be295bf0cd482582d10e5b3d6c` across `android-harness` and `crates`.
- [x] Permanent Android CI and permanent general/Rust CI are mandatory external terminal gates under spec §2.1. Repository-resident closure is finalized without self-referential run IDs; the implementation handoff must not claim completion until both are independently confirmed green on the terminal exact-SHA tree.

## SC-004.2 Authority closure

- [x] This document's `Status:` header is `Complete`.
- [x] `docs/LEGACY_TODO_INDEX.md` classifies this bounded tracker as completed; the active-implementation slot remains empty.
- [x] `scripts/task_post_port_review_fix_audit.sh` validates the completed second-corrections tracker, its evidence, and temporary-helper absence.
- [x] All temporary second-corrections Ralph/resume/probe/finalizer/closure helpers are removed from the final tree before exact-SHA validation.

## SC-004.3 Provenance-preserving corrections

- [x] CC-001 now records that its original scanner covered only the app-local root and that SC-001 added Gradle-wide source-root coverage plus future-root detection.
- [x] CC-004 now preserves its original `documented blocker` as historical provenance, records that SC-003's artifact-backed search disproved it, and names `ui-driven-path-built` as the current disposition with permanent E2E evidence.

## SC-004.4 Closure evidence

```text
Review baseline SHA:          a943b67abf4b187f1840a790ad9372d27576c3c5
Implementation start SHA:     df9155171e84b1be295bf0cd482582d10e5b3d6c
SC-001 source/test SHA:        92c01f33f19759c67c01aad73375084c72e3d1cb
SC-002 documentation SHA:      343d589b2181b6b2b355b3a809516f4acd20af1e
Final correction source SHA:   99a5ffd277db22c8a3d383e0206dfa6c010e4506
SC-003 provenance SHA:         e227e78bbbbf224440002d95e6dfa7993a850fc6

Android source/test evidence:  permanent run 31448304672; jobs 93647206317,
                               93647206339, 93647206354; all success
SC-003 discovery evidence:     run 31447725972; job 93645421851;
                               artifact 9085181028; RESULT=FOUND; b7a8b
Bounded closure validation:    workflow run 31449306496; app lint/unit,
                               host-JVM JNI, instrumentation compile, authority audit,
                               and scripts/dev.sh fast all success
Anti-suppression review:       no added @Suppress / #[allow] / #[expect]
Temporary helpers:             absent from candidate closure tree

(Terminal permanent CI run/job IDs are external metadata reported only in the
final implementation handoff per spec §2.1; no self-referential follow-up commit.)
```

## SC-004 acceptance

- [x] Every SC-001 through SC-003 task is complete with specific recorded evidence.
- [x] No first-party lint suppression was added anywhere in this pass.
- [x] No existing green test was weakened or deleted to obtain a green run.
- [x] The repository-resident closure tree is complete and immutable before terminal CI; exact-SHA permanent CI remains the external final handoff gate required by spec §2.1.
- [x] This document's Status header is `Complete`; external program closure is claimed only after both required terminal workflows are confirmed green.
