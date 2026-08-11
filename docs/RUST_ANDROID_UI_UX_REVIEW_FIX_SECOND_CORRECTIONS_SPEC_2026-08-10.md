# Rust Android UI/UX Review-Fix Second Corrections Spec — 2026-08-10

**Status:** proposed / not started
**Branch:** `master`
**Companion TODO:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SECOND_CORRECTIONS_TODO_2026-08-10.md`
**Program under correction:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md` (declared `Complete`)
**Closure evidence under partial correction:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md`
**Review baseline SHA:** `a943b67abf4b187f1840a790ad9372d27576c3c5`

---

## 1. Purpose

`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md` (the "CC" program) declares complete a bounded pass that fixed five confirmed false checkboxes and three hardening notes from the review-fix program before it. An independent post-closure verification — six parallel reviews, one per task cluster — found this closure markedly stronger than the one it corrects: the closure-SHA protocol (twice caught being logically impossible in earlier drafts) was genuinely honored, six of nine CC tasks are fully and rigorously correct, and no chess-correctness or fail-open regression exists anywhere. However, three real issues survived:

1. **CC-001 recurrence.** CC-001 genuinely fixed the two originally-flagged "native" jargon strings in `ChessViewModel.kt` and rebuilt the structural test to scan the whole `android-harness/android-app/src/main/kotlin` tree with a narrow allowlist — a real fix of the original defect. But Gradle compiles a *second* Kotlin source directory into this same app module (`crates/chess-jni/kotlin/src/main/kotlin`, added via `java.srcDir(...)` in `android-app/build.gradle.kts`), which sits outside both the spec's literal scope and the rebuilt test's scan root. That directory's `ChessGame.kt` still contains "native" in six string literals (lines 49, 52, 54, 78, 84, 215), at least one of which (`ChessGame.kt:215`, `"native Android game returned a null handle"`) is genuinely player-reachable through the exact same `ChessEngineErrorDialog` surface this entire thread has been fixing — traced end-to-end through `ChessGame.create()` → `ChessViewModel.startGame()`'s `catch (RuntimeException) { publishError(...) }` → `MainActivity.kt`'s dialog render.
2. **CC-002A evidence-completeness regression.** The observation-evidence contract spec §4.3 required (API level, device config, proof type, tolerance, artifact path, CI run/job ID) was genuinely and fully satisfied by an intermediate commit (`f8bd4fb`). The commit that closed the CC program (`0e71f13`) then rewrote that section to a shorter form and, in doing so, dropped three of the six required fields (emulator/device configuration, the numeric pixel tolerance, and the preserved-artifact path). The underlying evidence is real and recoverable from source, but the TODO as committed no longer satisfies its own contract.
3. **CC-004's core claim is unverifiable.** CC-004 correctly ruled out the "test-only fixture seam" disposition with independently-verifiable evidence (no seam exists in `ChessGame.kt`/`chess-jni`) and correctly recorded "documented blocker" as its disposition. But the substantive reasoning behind ruling out the preferred "UI-driven fixture" disposition — a claimed bounded search of legal move sequences that found no path to a promotion-eligible position — is asserted only in prose, with no CI run ID, artifact, or preserved script anywhere in the repository, unlike every comparable claim elsewhere in this same correction pass (which cites exact run/job/artifact IDs throughout).

This pass closes all three. It does not reopen any other CC-00N or AR-00N task.

### 1.1 Lessons applied from the start

This spec applies, from the outset, every convention the CC program's own three pre-implementation review rounds (QI/FQI/FFQI) had to establish iteratively: touched-file scope is stated by category, not an exhaustive list that later proves too narrow (§2); the closure-SHA protocol is the already-proven terminating form — repository-resident evidence lands in the last substantive commit, terminal exact-SHA CI run/job IDs are external metadata verified via `gh` and reported in the final handoff, never written back into the repository (§2.1); any task with a genuinely conditional outcome uses a disposition-oriented checklist with `N/A` for the untaken branch, not independent mandatory checkboxes per branch (§4); and any correction to prior tracker text preserves provenance rather than silently rewriting history (§5.3).

---

## 2. Engineering constraints retained

- Rust remains authoritative for chess rules, legality, opening-book selection, and SAN generation. No task in this pass adds chess-rule, legality, disambiguation, or opening-book logic to Kotlin.
- The Android interactive fail-closed policy is not weakened: no task in this pass adds a random/first-legal fallback, silent retry, silent depth reduction, fake/default snapshot, or alternate engine path.
- No first-party lint suppression (`allow`/`expect`, Kotlin `@Suppress`) is added anywhere in this pass.
- No new production dependency is added without explicit justification recorded in this spec.
- This pass touches, by category: Kotlin production/test sources in **both** Gradle-compiled source directories of the Android app module (`android-harness/android-app/src/main/kotlin/**` **and** `crates/chess-jni/kotlin/src/main/kotlin/**`, plus their `test`/`androidTest` counterparts) as needed by SC-001 and SC-003; `android-harness/host-jvm/**` if SC-001's re-sweep finds a stale hard-coded string there; the review-fix program's own documents (`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md`, `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md`) for SC-002/SC-004's corrections; `docs/LEGACY_TODO_INDEX.md` and `scripts/task_post_port_review_fix_audit.sh` for this pass's own authority registration; and this spec/TODO pair. It does not touch `crates/chess-app`, `crates/chess-core` production code, `crates/chess-search`, `crates/chess-book`, `crates/chess-uci`, `crates/chess-tui`, or `crates/chess-console`.
- Existing passing tests are not weakened or deleted to obtain a green run.
- This pass is itself a bounded review-fix tracker under `docs/LEGACY_TODO_INDEX.md`'s "Bounded review-fix trackers" classification, registered there as part of SC-000 baseline work.

### 2.1 Closure-SHA protocol (proven form, applied from the start)

1. **Review baseline SHA** (`a943b67...`) is fixed and never reinterpreted as anything else.
2. **Implementation-start SHA** is captured immediately after SC-000's baseline/authority-registration work lands.
3. SC-001 through SC-004 land normally, one task per commit.
4. All repository-resident evidence is written into its final form in the last substantive commit, which fully and accurately describes this pass without attempting to cite its own not-yet-existing CI results.
5. Whether an additional trigger commit is needed is decided by actual workflow execution against that exact SHA, not by classifying the changed files as documentation versus source. If both required permanent workflows (Android CI, general/Rust CI) already executed against the last substantive commit's SHA, that SHA is terminal. If not, push exactly one empty, tree-identical trigger commit to cause both to execute against the unchanged final tree.
6. **Terminal exact-SHA GitHub Actions run/job IDs and conclusions are external metadata, not repository content.** They are independently verified via `gh` after the trigger push and reported in this pass's final implementation handoff. No further commit is made to the repository to record them.
7. Citing an already-closed, already-existing SHA's CI runs in a document (as SC-002 does for the CC program's own historical evidence) is not self-referential and does not require this protocol — only a commit describing *its own* SHA's future CI results would be.

---

## 3. SC-001 — Fix the recurred "native" jargon defect in `ChessGame.kt`

### 3.1 Defect

`crates/chess-jni/kotlin/src/main/kotlin/com/ekkus93/chessengine/ChessGame.kt` contains "native" in six string literals:
- lines 49, 52, 54 (`ChessGameSnapshot.parse()`'s `require()` failure messages — wrong field count, wrong version, missing terminator);
- lines 78, 84 (`require()`/`error()` messages inside enum-mapping helpers);
- line 215 (`check(handle != 0L) { "native Android game returned a null handle" }` inside `ChessGame.create()`).

All six are reachable from `ChessViewModel.kt` through the identical `catch (error: RuntimeException) { publishError(generation, error) }` pattern used throughout (`startGame()`, `snapshot()`/`poll()`, `submitMove()`, `restart()`, `resign()`), and `publishError()`'s `displayMessage()` returns `error.message` verbatim, which `MainActivity.kt`'s `ChessEngineErrorDialog` renders to the player. This is the exact defect class CC-001 was created to close, recurring in a location neither the original AR-003 spec, CC-001's spec, nor CC-001's rebuilt structural test ever scoped, because all three anchored "the module" to the `android-harness/android-app/src/main/kotlin` directory name rather than to the Gradle-compiled source-set boundary (`android-app/build.gradle.kts`'s `java.srcDir("../../crates/chess-jni/kotlin/src/main/kotlin")`) that actually determines what ships in the app.

### 3.2 Fix

- For each of the six strings, determine whether it is genuinely player-reachable (per the trace above, all six currently are, via the shared `parse()`/`create()` → `publishError()` path) or whether a narrower, internal-only reachability actually applies to some. Reword every genuinely player-reachable string to remove "native" while preserving its intended meaning, following the same style already used for `ChessViewModel.kt`'s corrected strings.
- Check `android-harness/host-jvm/src/test/kotlin/**` (which also depends on `ChessGame.kt`/`ChessEngine.kt`) for any test hard-coding the old string text; update if found.
- **Root-cause the recurrence, not just this instance:** extend `ReviewFixArchitectureTest.kt`'s blanket forbid-with-allowlist scan (or add a sibling test with equivalent effect) to cover **both** Gradle-compiled source directories of this app module — `android-harness/android-app/src/main/kotlin` and `crates/chess-jni/kotlin/src/main/kotlin` — not just the first. Determine the correct scan root(s) by reading `android-app/build.gradle.kts`'s actual `sourceSets`/`java.srcDir` configuration rather than assuming a single directory, so a future third Gradle-added source directory would also be caught rather than requiring a fourth review round to discover.
- Any allowlist entry for a string judged genuinely internal-only must be exact/narrow and justified inline, matching the existing pattern.

### 3.3 Tests

- The extended structural test scans both source directories and passes on the corrected strings.
- Implementation-time sanity check: confirmed the extended test fails if "native" is temporarily reintroduced into `ChessGame.kt`.
- Any updated host-JVM test remains green.
- Existing Kotlin/JVM and instrumentation tests referencing `ChessGame`/`ChessGameSnapshot` remain green.

---

## 4. SC-002 — Restore CC-002A's dropped observation-evidence fields

### 4.1 Defect

`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md`'s CC-002A section satisfied the spec's six-field observation-evidence contract in an intermediate commit (`f8bd4fb`) but lost three fields — emulator/device configuration, the numeric pixel tolerance, and the preserved-artifact path — when the program's closing commit (`0e71f13`) rewrote the section to a shorter form.

### 4.2 Fix

- Restore the three dropped fields to CC-002A's TODO section, reconciled against what `SystemBarAppearanceInstrumentedTest.kt` actually implements today (do not simply paste back the old text without re-verifying it still matches the current test) — specifically device/emulator configuration, the numeric RGB tolerance and match-ratio threshold used by the pixel-sampling assertion, and the preserved-screenshot artifact path.
- This is a documentation-only correction; it does not reopen CC-002A's disposition or add new test coverage.

### 4.3 Tests

- N/A — documentation-only. Verified by re-reading `SystemBarAppearanceInstrumentedTest.kt`'s actual tolerance/threshold constants and confirming the restored text matches them exactly.

---

## 5. SC-003 — Get real evidence for CC-004's promotion-position claim

### 5.1 Defect

CC-004's "documented blocker" disposition rests on an unverifiable prose claim (a bounded search of legal move sequences found no path to a promotion-eligible position) with no CI run, artifact, or preserved script anywhere in the repository — the only claim in the entire CC program without this pass's otherwise-consistent evidentiary standard.

### 5.2 Fix

CC-004's own spec already named a second acceptable disposition beyond "documented blocker": a narrowly-scoped, test-only fixture seam (never production/player-reachable) that initializes the game session directly to a promotion-eligible position, without adding chess-rule logic to Kotlin or a general production FEN-loading feature. CC-004's independent verification already confirmed no such seam exists today, but did not attempt to build one. This task now does:

1. **Preferred:** attempt to build the test-only fixture seam. If practical, add it and use it to implement the end-to-end instrumentation test CC-004 was originally meant to deliver — driving the promotion dialog through the real production flow, tapping a real promotion choice, and asserting the resulting move/snapshot is correct. This directly closes the evidentiary gap by replacing an unverifiable claim with an executable, permanently-passing test.
2. **Fallback, only if the seam genuinely proves impractical after a real attempt:** produce artifact-backed evidence for the existing "no promotion path found" claim instead — a preserved CI run (with its own run/job ID) that actually executes the bounded search and records its result, matching the rigor standard the rest of this pass already set. A second unverifiable prose restatement of the same claim does not satisfy this task.

### 5.3 Tests

- If the seam is built: the new end-to-end promotion instrumentation test passes, is exercised in permanent CI, and its run/job ID is recorded.
- If the fallback is used: the preserved, artifact-backed search evidence is recorded with its CI run/job ID.
- Either way, CC-004's TODO section is updated to reflect the new evidentiary basis, provenance-preserving per §5.3 below (this task does not silently rewrite CC-004's own history — it records that SC-003 strengthened it).

---

## 6. SC-004 — Final validation and closure

### 6.1 Validation

- Run the applicable validation surface: Android app JVM/unit tests (including SC-001's structural test extension), Android lint, SC-003's new instrumentation test if built, and `bash scripts/task_post_port_review_fix_audit.sh`.
- Run `bash scripts/dev.sh fast` only if this pass's final diff touches non-documentation files (per the established convention: a docs-only diff needs only the targeted audit script, not the full gate); this pass is expected to touch real Kotlin source (SC-001, possibly SC-003), so `dev.sh fast` is expected to be required.
- Permanent Android CI and permanent general/Rust CI are both mandatory on the exact final SHA, following §2.1's protocol.

### 6.2 Authority closure

- This document's `Status:` header updated to `Complete`.
- `docs/LEGACY_TODO_INDEX.md`'s "Bounded review-fix trackers" entry for this tracker updated from "in progress" to "completed."
- `scripts/task_post_port_review_fix_audit.sh` updated to register this tracker, matching the pattern already established for its four predecessors.
- Confirmed no temporary correction/validation helper remains in the tree before final exact-SHA validation.

### 6.3 Provenance-preserving corrections

- CC-001's and CC-004's sections in `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md` are updated in place to record that SC-001/SC-003 respectively closed the gaps this independent verification found — using wording that distinguishes what CC-001/CC-004 originally established, what gap remained, and what SC-001/SC-003 added, not silently rewritten as though the CC program's own text was always complete.

### 6.4 Closure evidence

- Record all repository-resident evidence (commands, results, dispositions) in the companion TODO's closure section.
- Per §2.1, do not write the terminal trigger SHA's own permanent CI run/job IDs into any repository file — report them in the final implementation handoff instead.
- Do not mark any SC task `[x]` without the specific evidence named in its own section above.
