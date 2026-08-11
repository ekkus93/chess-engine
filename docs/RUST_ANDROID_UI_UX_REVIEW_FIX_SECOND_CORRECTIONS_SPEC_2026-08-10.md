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

### 1.0 Pre-implementation resolution note

A pre-implementation review of this spec/TODO pair (`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SECOND_CORRECTIONS_QUESTIONS_AND_ISSUES_2026-08-10.md`, six items) found the second-corrections program "technically justified" with the closure-SHA protocol already sound, and did not recommend redesigning it again. All six items were legitimate refinements, since resolved:

1. **Item 1** (SC-001's fix requirement was scoped to the six known `ChessGame.kt` strings, but the blanket-scan test policy will also encounter jargon strings elsewhere in the newly-included directory, e.g. in `ChessEngine.kt`) — resolved: SC-001 §3.2 now requires a disposition (reword or narrow allowlist) for *every* forbidden string the expanded scan actually finds in the newly-included directory, not only the six originally reported.
2. **Item 2** (the "derive scan roots from Gradle" requirement wasn't mechanically specified, so an implementation could still hard-code today's two known roots and silently miss a future third one) — resolved: §3.2 now requires either deriving production source roots from Gradle/source-set metadata at test runtime, or a structural assertion that parses `android-app/build.gradle.kts`'s actual `java.srcDir(...)` declarations and fails if any declared root is absent from the scanner's configured roots.
3. **Item 3** (SC-002 named `SystemBarAppearanceInstrumentedTest.kt` as the source of truth for emulator/device configuration, but that configuration actually lives in `.github/workflows/android.yml`) — resolved: §4.2 now requires both sources and three distinct artifact-location layers (device-side path, CI-workspace path after `adb pull`, uploaded GitHub Actions artifact name).
4. **Item 4** (the `artifact-backed-blocker` disposition needs a real CI run producing an artifact, which requires touching `.github/workflows/**` and cannot honestly land in one commit, mirroring the same before-the-run-exists sequencing constraint solved elsewhere in this thread) — resolved: §2 and §5.2 now explicitly authorize a bounded multi-commit sequence for this specific disposition, mirroring CC-002A's own established precedent (probe commit → CI run → evidence commit → temporary-helper removal).
5. **Item 5** (no explicit tripwire existed for when the preferred "test-only fixture seam" disposition should be abandoned in favor of the fallback, risking an implementer quietly expanding production/native API surface just to make a seam work) — resolved: §5.2 now states the boundary explicitly up front.
6. **Item 6** (a stale `§5.3` cross-reference, meant to point at the provenance-preserving rules actually in `§6.3`) — corrected throughout.

### 1.1 Lessons applied from the start

This spec applies, from the outset, every convention the CC program's own three pre-implementation review rounds (QI/FQI/FFQI) had to establish iteratively: touched-file scope is stated by category, not an exhaustive list that later proves too narrow (§2); the closure-SHA protocol is the already-proven terminating form — repository-resident evidence lands in the last substantive commit, terminal exact-SHA CI run/job IDs are external metadata verified via `gh` and reported in the final handoff, never written back into the repository (§2.1); any task with a genuinely conditional outcome uses a disposition-oriented checklist with `N/A` for the untaken branch, not independent mandatory checkboxes per branch (§4); and any correction to prior tracker text preserves provenance rather than silently rewriting history (§6.3).

---

## 2. Engineering constraints retained

- Rust remains authoritative for chess rules, legality, opening-book selection, and SAN generation. No task in this pass adds chess-rule, legality, disambiguation, or opening-book logic to Kotlin.
- The Android interactive fail-closed policy is not weakened: no task in this pass adds a random/first-legal fallback, silent retry, silent depth reduction, fake/default snapshot, or alternate engine path.
- No first-party lint suppression (`allow`/`expect`, Kotlin `@Suppress`) is added anywhere in this pass.
- No new production dependency is added without explicit justification recorded in this spec.
- This pass touches, by category: Kotlin production/test sources in **both** Gradle-compiled source directories of the Android app module (`android-harness/android-app/src/main/kotlin/**` **and** `crates/chess-jni/kotlin/src/main/kotlin/**`, plus their `test`/`androidTest` counterparts) as needed by SC-001 and SC-003; `android-harness/host-jvm/**` if SC-001's re-sweep finds a stale hard-coded string there; the review-fix program's own documents (`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md`, `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md`) for SC-002/SC-004's corrections; `docs/LEGACY_TODO_INDEX.md` and `scripts/task_post_port_review_fix_audit.sh` for this pass's own authority registration; **`.github/workflows/**` and a bounded temporary validation script/helper location, but only if SC-003 reaches the `artifact-backed-blocker` disposition** (§5.2), and only for the narrow purpose of executing and preserving the bounded promotion-path search — removed before final closure, matching CC-002A's own established precedent for this exact class of temporary CI machinery; and this spec/TODO pair. It does not touch `crates/chess-app`, `crates/chess-core` production code, `crates/chess-search`, `crates/chess-book`, `crates/chess-uci`, `crates/chess-tui`, or `crates/chess-console`.
- Existing passing tests are not weakened or deleted to obtain a green run.
- This pass is itself a bounded review-fix tracker under `docs/LEGACY_TODO_INDEX.md`'s "Bounded review-fix trackers" classification, registered there as part of SC-000 baseline work.

### 2.1 Closure-SHA protocol (proven form, applied from the start)

1. **Review baseline SHA** (`a943b67...`) is fixed and never reinterpreted as anything else.
2. **Implementation-start SHA** is captured immediately after SC-000's baseline/authority-registration work lands.
3. SC-001, SC-002, and SC-004 land normally, one task per commit. SC-003 is explicitly exempted from this rule if it reaches the `artifact-backed-blocker` disposition (§5.2), since a real CI run producing an artifact cannot exist before the commit that triggers it, mirroring the exact before-the-run-exists sequencing constraint solved elsewhere in this thread — in that case SC-003 lands as a bounded, explicitly-ordered multi-commit sequence instead.
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

- For each of the six originally-flagged strings, determine whether it is genuinely player-reachable (per the trace above, all six currently are, via the shared `parse()`/`create()` → `publishError()` path) or whether a narrower, internal-only reachability actually applies to some. Reword every genuinely player-reachable string to remove "native" while preserving its intended meaning, following the same style already used for `ChessViewModel.kt`'s corrected strings.
- Check `android-harness/host-jvm/src/test/kotlin/**` (which also depends on `ChessGame.kt`/`ChessEngine.kt`) for any test hard-coding the old string text; update if found.
- **Root-cause the recurrence, not just this instance:** extend `ReviewFixArchitectureTest.kt`'s blanket forbid-with-allowlist scan (or add a sibling test with equivalent effect) to cover **both** Gradle-compiled source directories of this app module — `android-harness/android-app/src/main/kotlin` and `crates/chess-jni/kotlin/src/main/kotlin` — not just the first.
- **The six originally-reported strings are the confirmed triggering defect, not the entire implementation boundary.** Once the scanner covers `crates/chess-jni/kotlin/src/main/kotlin/**`, it will encounter additional forbidden-term string literals outside `ChessGame.kt` — e.g. in `ChessEngine.kt` (the low-level API), which shares this directory. For **every** forbidden string the expanded scan actually finds there, apply one of the same two dispositions used elsewhere in this thread: reword it to remove player-visible architecture jargon, or classify it as genuinely internal-only with an exact, narrow, inline-justified allowlist entry. Do not scope the implementation to only the six strings named in §1's defect description.
- **Specify a mechanical invariant for future source-directory protection, not just today's two known roots.** A test that reads `build.gradle.kts` once during development and hard-codes today's two directories into itself would still silently miss a future third `java.srcDir(...)`, recreating this exact defect class a fourth time. Require one of:
  1. the test derives its production source roots from Gradle/source-set metadata at test runtime; or
  2. a structural assertion reads `android-app/build.gradle.kts`'s source text, discovers every declared production `java.srcDir(...)` call, and fails if any declared directory is absent from the scanner's configured roots.
  
  The acceptance criterion is that this test would fail — not silently pass — if Gradle gains a new production source directory without the scanner being updated to include it.
- Any allowlist entry for a string judged genuinely internal-only must be exact/narrow and justified inline, matching the existing pattern.

### 3.3 Tests

- The extended structural test scans both current source directories and passes on the corrected strings, including any additional forbidden strings found and dispositioned per §3.2.
- Implementation-time sanity check: confirmed the extended test fails if "native" is temporarily reintroduced into `ChessGame.kt`.
- A second implementation-time sanity check: confirmed the mechanical future-directory invariant actually fails when a hypothetical third `java.srcDir(...)` is temporarily added to `build.gradle.kts` without updating the scanner (then reverted).
- Any updated host-JVM test remains green.
- Existing Kotlin/JVM and instrumentation tests referencing `ChessGame`/`ChessGameSnapshot` remain green.

---

## 4. SC-002 — Restore CC-002A's dropped observation-evidence fields

### 4.1 Defect

`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md`'s CC-002A section satisfied the spec's six-field observation-evidence contract in an intermediate commit (`f8bd4fb`) but lost three fields — emulator/device configuration, the numeric pixel tolerance, and the preserved-artifact path — when the program's closing commit (`0e71f13`) rewrote the section to a shorter form.

### 4.2 Fix

`SystemBarAppearanceInstrumentedTest.kt` is not the sole source of truth for this contract: it defines the API level, RGB tolerance, and match-ratio threshold, but the actual emulator/device configuration (API 35, x86_64, `google_apis`, Pixel 2 profile, SwiftShader/headless options) is defined in `.github/workflows/android.yml`, which also defines how the device-side screenshot is pulled into the CI workspace and uploaded as a permanent artifact.

- Restore the fields dropped from CC-002A's TODO section, reconciled against **both** `SystemBarAppearanceInstrumentedTest.kt` (API level, tolerance, threshold) and `.github/workflows/android.yml` (emulator/device configuration) — do not simply paste back the old text without re-verifying it still matches both current sources.
- Record all **three** distinct artifact-location layers separately, rather than conflating them: (1) the device-side screenshot path (`/sdcard/Download/RustChessEvidence/system-bars-api35.png`), (2) the path after `adb pull` into the CI workspace, and (3) the uploaded GitHub Actions artifact name/path — as actually configured in `.github/workflows/android.yml`.
- This is a documentation-only correction; it does not reopen CC-002A's disposition or add new test coverage.

### 4.3 Tests

- N/A — documentation-only. Verified by re-reading `SystemBarAppearanceInstrumentedTest.kt`'s actual tolerance/threshold constants and `.github/workflows/android.yml`'s actual emulator/device and artifact-upload configuration, confirming the restored text matches both exactly.

---

## 5. SC-003 — Get real evidence for CC-004's promotion-position claim

### 5.1 Defect

CC-004's "documented blocker" disposition rests on an unverifiable prose claim (a bounded search of legal move sequences found no path to a promotion-eligible position) with no CI run, artifact, or preserved script anywhere in the repository — the only claim in the entire CC program without this pass's otherwise-consistent evidentiary standard.

### 5.2 Fix

CC-004's own spec already named a second acceptable disposition beyond "documented blocker": a narrowly-scoped, test-only fixture seam (never production/player-reachable) that initializes the game session directly to a promotion-eligible position, without adding chess-rule logic to Kotlin or a general production FEN-loading feature. CC-004's independent verification already confirmed no such seam exists today, but did not attempt to build one. This task now does:

1. **Preferred:** attempt to build the test-only fixture seam. If practical, add it and use it to implement the end-to-end instrumentation test CC-004 was originally meant to deliver — driving the promotion dialog through the real production flow, tapping a real promotion choice, and asserting the resulting move/snapshot is correct. This directly closes the evidentiary gap by replacing an unverifiable claim with an executable, permanently-passing test.

   **Explicit architectural boundary (decide before implementation, not during it):** the low-level `ChessEngine` API already supports position injection via `setPosition(fen)`, but the actual UI is driven through the separate high-level `ChessGame` API, which has a private constructor and exposes no arbitrary position/FEN injection — only `create`/`snapshot`/`poll`/`submitMove`/`restart`/`resign`. If making the real production UI flow start from a promotion-eligible high-level `ChessGame` state would require adding production/native API surface or changing `ChessGame`'s ownership model — even surface intended to be "test-only" in spirit — the seam disposition is considered impractical **immediately**, without further attempt, and this task proceeds directly to disposition 2. A test-only implementation must remain non-player-reachable and must not require Kotlin chess-rule logic; testability work must not become an accidental product/API expansion.
2. **Fallback, if the seam is impractical per the boundary above or proves impractical after a real attempt:** produce artifact-backed evidence for the existing "no promotion path found" claim instead — a preserved CI run (with its own run/job ID) that actually executes the bounded search and records its result, matching the rigor standard the rest of this pass already set. A second unverifiable prose restatement of the same claim does not satisfy this task.

   **This disposition requires a bounded, explicitly-ordered multi-commit sequence** (§2.1 point 3's exemption applies): a real CI run producing an artifact cannot exist before the commit that triggers it. The sequence is: (a) commit the search probe/helper plus a temporary CI workflow (or workflow step) that executes it and uploads its result as an artifact — scoped under this spec's §2 authorization; (b) let that commit's CI run execute and produce the artifact; (c) commit the evidence/disposition record, citing that run's real run/job ID and artifact ID (mirroring CC-002A's own established precedent for this exact class of temporary CI machinery); (d) remove the temporary workflow/helper in a final commit before SC-004's closure validation, so the final tree carries no leftover temporary machinery.

### 5.3 Tests

- If the seam is built: the new end-to-end promotion instrumentation test passes, is exercised in permanent CI, and its run/job ID is recorded.
- If the fallback is used: the preserved, artifact-backed search evidence is recorded with its CI run/job ID.
- Either way, CC-004's TODO section is updated to reflect the new evidentiary basis, provenance-preserving per §6.3 below (this task does not silently rewrite CC-004's own history — it records that SC-003 strengthened it).

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
