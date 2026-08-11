# Rust Android UI/UX Review-Fix Closure Corrections TODO — 2026-08-10

**Status:** Complete
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

- [x] Direct API-35 framebuffer evidence was added; icon-appearance flags are supporting evidence only.
- [x] **API level:** 35, asserted directly by `SystemBarAppearanceInstrumentedTest.kt`.
- [x] **Emulator/device configuration:** x86_64 `google_apis` system image, Pixel 2 profile, headless emulator using `-gpu swiftshader_indirect`, as defined by `.github/workflows/android.yml`.
- [x] **Proof type:** `UiAutomation` framebuffer screenshot sampled inside the status/navigation-bar inset regions after `MainActivity` owns window focus and is the foreground package; appearance flags remain supporting assertions only.
- [x] **Expected color/tolerance:** product background `#0B1220`; RGB tolerance ±12 per channel; both sampled bar regions require a matching-pixel ratio of at least 0.70.
- [x] **Preserved artifact locations:** device `/sdcard/Download/RustChessEvidence/system-bars-api35.png`; CI workspace after `adb pull`: `android-ui-evidence/system-bars-api35.png`; uploaded Actions artifact `rust-chess-android-ui-evidence-05ec27dd099fa5ad74f5e5ff0bea2ae1cc5a801c` (artifact ID `9080725280`), containing that path under `android-ui-evidence/`.
- [x] **Stable CI evidence:** permanent Android run `31434848246`, API-35 job `93606568633`, exact SHA `05ec27dd099fa5ad74f5e5ff0bea2ae1cc5a801c`, conclusion `success`.
- [x] The earlier full-suite 0% sample remains provenance for the foreground-teardown investigation; the focus-bound diagnostic above is the authoritative stable observation.

## CC-002B: Conditional remediation

- [x] **Disposition reached:** `remediation-not-needed`; stable focus-bound rendered evidence shows the product bars are correct.

N/A — `remediation-required`: no production system-bar change was needed.

## CC-002 Tests

- [x] Final stable evidence is permanent Android run `31434848246`, API-35 job `93606568633`, success; the investigation also preserved artifact `9080478963` explaining the earlier false failure.

---

# CC-003: Correct AR-007 behavioral-evidence claims; add behavioral coverage where practical

## CC-003.1 Fix

- [x] Attempted a genuine behavioral-test-seam design by reinspecting the actual ownership boundary: `ChessViewModel` stores a concrete `ChessGame`; `ChessGame` has a private constructor and owns the native high-level session. There is no clean fake/injection seam available to the app tests.
- [x] **Disposition reached:** `claims-downgraded`. Adding a production abstraction solely for this test would expand/distort production architecture, so the tracker now states only what is genuinely proven.

N/A — `seam-built`: no production seam was added.

- [x] `claims-downgraded`: parent AR-007.2 now preserves the original overclaim as provenance and limits the accepted evidence to predicate truth-table coverage plus static guard-before-generation ordering.

## CC-003.2 Tests

- [x] `ActiveGameOperationGuardTest` and `ReviewFixArchitectureTest.activeGameOperationsGuardBeforeGenerationAdvance` pass, and parent AR-007.2 now matches that actual evidence.

---

# CC-004: Fix AR-011 — add missing end-to-end promotion test

## CC-004.1 Fix

- [x] **Disposition reached:** `documented blocker`.

N/A — `UI-driven fixture`: A genuine bounded attempt was executed with the real JNI `ChessEngine`, reproducing the high-level opponent policy (opening-book reply when present, otherwise deterministic depth-1 search) and beam-searching legal human moves for up to 12 human turns; it did not find a promotion path. The existing production `ChessGame` also exposes no test-only position-injection seam, and adding one would require production/native API expansion solely for this test.

N/A — `test-only fixture seam`: no existing test-only high-level session constructor/FEN seam exists; adding one would expand production/native API surface solely for this test.

- [x] Documented blocker: A genuine bounded attempt was executed with the real JNI `ChessEngine`, reproducing the high-level opponent policy (opening-book reply when present, otherwise deterministic depth-1 search) and beam-searching legal human moves for up to 12 human turns; it did not find a promotion path. The existing production `ChessGame` also exposes no test-only position-injection seam, and adding one would require production/native API expansion solely for this test.

## CC-004.2 Tests

- [x] The bounded real-engine path probe is the empirical blocker evidence; no new instrumentation test is claimed.

---

# CC-005: Fix closure-evidence CI citation

## CC-005.1 Fix

- [x] Parent closure evidence now cites authoritative final-tree general/Rust run `31419183264` and Android run `31419183273` against `e9ab0fc623c22bd372ba9c8c2609dfcf74609f84`, including their job IDs and successful conclusions.
- [x] Earlier `6d9a84d9` runs remain supporting evidence only. Product/test equality is proven by the path-scoped command below, not inferred from green CI:

```text
git diff --exit-code 6d9a84d910a3e6438aef390aa733a4b62a71dfdd..e9ab0fc623c22bd372ba9c8c2609dfcf74609f84 -- android-harness crates
(exit 0; empty output)
```

Supplementary unrestricted changed-file list:

```text
docs/LEGACY_TODO_INDEX.md
docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md
docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md
scripts/task_post_port_review_fix_audit.sh
```

## CC-005.2 Tests

- [x] `gh run view 31419183264` and `gh run view 31419183273` independently returned completed/success on `e9ab0fc623c22bd372ba9c8c2609dfcf74609f84` during this task.
- [x] The recorded path-scoped diff was independently executed in this task and returned exit 0 with empty output.

# CC-006: Document AR-006's residual auto-scroll assumption

## CC-006.1 Fix

- [x] `GamePanels.kt` now documents that `isScrollInProgress` also observes the automatic `animateScrollToItem`, that real gameplay appends one row at a time, and that a future bulk-history replacement must re-examine the assumption.

## CC-006.2 Tests

- [x] N/A — documentation-only behavior comment; Android instrumentation sources compile after the comment, and the existing two auto-scroll behavioral tests remain unchanged for the later full connected-test gate.

# CC-007: Strengthen AR-020's rotation test

## CC-007.1 Fix

- [x] `PortraitRotationInstrumentedTest.kt` asserts no `e2 pawn` node exists after rotation, alongside the existing `e4 pawn` presence assertion.

## CC-007.2 Tests

- [x] The strengthened assertion passed in the full API-35 connected suite in permanent Android run `31434848246`, job `93606568633`. It would fail if rotation duplicated the moved pawn onto both e2 and e4.

---

# CC-008: Add Resign-dialog contrast pairing

## CC-008.1 Fix

- [x] `ThemeContrastTest.kt` now includes `requireRatio("resign dialog confirm", Danger, SurfaceElevated, 4.5)`.

## CC-008.2 Tests

- [x] Android lint/app unit-test job `93608171310` in permanent Android run `31435363087` passed on source SHA `a16590502279750c21ce6afa7356cf755f7efcaa`, including the new contrast assertion.

---

# CC-009: Final validation and closure

## CC-009.1 Validation

- [x] Android app JVM/unit tests and Android lint pass in this closure run; CC-008 also passed permanent job `93608171310` / run `31435363087` on `a16590502279750c21ce6afa7356cf755f7efcaa`.
- [x] CC-004 disposition-dependent validation is complete: `documented blocker`, backed by the bounded real-JNI-engine path search; no E2E test is claimed.
- [x] CC-002A final focus-bound runtime observation and CC-002B `remediation-not-needed` disposition are recorded; permanent run `31434848246` is fully green.
- [x] `bash scripts/dev.sh fast` passes in this closure run.
- [x] Terminal permanent exact-SHA CI is an external post-commit gate per spec §2.1/FQI-001. The repository closure is complete, but the final implementation handoff is blocked until both permanent workflows are independently confirmed green on the terminal validation SHA; their run/job IDs are intentionally not written back into a new commit.

## CC-009.2 Provenance-preserving correction of the parent TODO

- [x] AR-003, AR-004, AR-007, AR-011, and AR-021/closure-CI citation history are corrected in place without pretending the original closure had the evidence supplied by CC-001/002/003/004/005.

## CC-009.3 Authority closure

- [x] This tracker's `Status:` is `Complete`.
- [x] `docs/LEGACY_TODO_INDEX.md` classifies this bounded tracker as completed; the active-implementation slot remains empty.
- [x] Permanent authority audit updated for the corrected closure state.
- [x] Temporary correction/validation helpers are removed before the closure commit is created.

## CC-009.4 Closure evidence

- [x] Parent closure evidence was corrected by CC-005 with authoritative `e9ab0fc...` runs and path-scoped historical source/test equivalence evidence.
- [x] All repository-resident correction evidence is recorded here; terminal CI metadata remains external by protocol.

```text
Review baseline SHA:          e9ab0fc623c22bd372ba9c8c2609dfcf74609f84
Implementation start SHA:     fe97117a9d5315a2ae4bff344ed8b22f52d8c86e
Final correction source SHA:  a16590502279750c21ce6afa7356cf755f7efcaa

Android app unit/lint:        pass — closure validation plus run 31435363087/job 93608171310
CC-004 disposition/result:    documented blocker — bounded real JNI-engine promotion-path search found no deterministic path
CC-002A runtime observation:  pass — final stable run 31434848246/job 93606568633; isolation artifact 9080478963 explains prior foreground race
CC-002B disposition/result:   remediation-not-needed — no production system-bar change
bash scripts/dev.sh fast:     pass — closure validation
first-party suppressions:     none added in android-harness/crates diff from implementation-start SHA

(Terminal permanent CI run/job IDs are reported externally in the final
implementation handoff after the terminal SHA is known and both workflows finish.)
```

## CC-009 acceptance

- [x] Every CC-001 through CC-008 task has its own recorded evidence or explicit permitted `N/A` branch.
- [x] No first-party lint suppression was added anywhere in this pass.
- [x] No existing green test was weakened or deleted to obtain a green run.
- [x] Terminal exact-SHA permanent CI remains the mandatory external gate; final handoff will not declare the Ralph loop closed until it is green.
- [x] Repository closure status is `Complete`; no repository mutation will occur after the terminal validation SHA is selected.
