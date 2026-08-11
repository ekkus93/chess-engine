# Rust Android UI/UX Review-Fix Second Corrections — Questions and Issues — 2026-08-10

## Purpose

This file records the remaining questions/issues found after reviewing:

- `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SECOND_CORRECTIONS_SPEC_2026-08-10.md`
- `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SECOND_CORRECTIONS_TODO_2026-08-10.md`

No implementation changes are proposed here beyond clarifying the second-corrections program before execution.

---

## 1. SC-001's six-string framing is narrower than the test policy it requires

### Issue

The spec correctly identifies six `"native"`-containing string literals in:

`crates/chess-jni/kotlin/src/main/kotlin/com/ekkus93/chessengine/ChessGame.kt`

However, SC-001 also requires the blanket architecture-jargon structural test to expand across **all** Gradle-compiled production Kotlin source directories for the Android app module.

Once that scanner includes:

`crates/chess-jni/kotlin/src/main/kotlin/**`

it will encounter architecture-jargon string literals outside `ChessGame.kt`, including strings in `ChessEngine.kt`, for example messages containing `native` such as:

- `unknown native color code`
- `unknown native status code`
- `native game status must contain three fields`
- `native search result must contain exactly ... fields`
- other JNI/native-facing diagnostic strings

Therefore, the implementation cannot safely be scoped to only the six known `ChessGame.kt` strings while simultaneously adopting a blanket source-directory-wide forbid rule.

### Question / requested clarification

Please make SC-001 explicitly cover the **entire newly included Gradle production source directory**, not just the six initially reported strings.

For every forbidden production string encountered there, require one of two dispositions:

1. reword it to avoid player-visible architecture jargon; or
2. classify it as genuinely internal-only and add an exact, narrow, inline-justified allowlist entry.

The six `ChessGame.kt` strings should remain the confirmed triggering defect, but not the entire implementation boundary.

---

## 2. The promised future-source-directory protection is not mechanically specified

### Issue

The spec says the structural test should determine the scan roots from the actual Gradle `sourceSets` / `java.srcDir(...)` configuration rather than assuming one directory, specifically so a future third production Kotlin source directory cannot escape the guard.

That is the right goal, but the current wording still permits an implementation that merely reads `build.gradle.kts` once during development and then hard-codes these two roots into the test:

- `android-harness/android-app/src/main/kotlin`
- `crates/chess-jni/kotlin/src/main/kotlin`

Such a test would still silently miss a future third `java.srcDir(...)`, recreating the exact defect class this pass is intended to eliminate.

### Question / requested clarification

Please specify a mechanical invariant. For example, require either:

- the test to derive the production source roots from Gradle/source-set metadata at test runtime; **or**
- a structural assertion that reads `android-app/build.gradle.kts`, discovers every production `java.srcDir(...)`, and fails if any declared production Kotlin source directory is absent from the scanner's configured roots.

The acceptance criterion should explicitly fail when Gradle gains a new production source directory without the architecture-jargon scanner being updated.

---

## 3. SC-002 uses the wrong source of truth for emulator/device configuration

### Issue

The TODO says:

> Re-read `SystemBarAppearanceInstrumentedTest.kt`'s actual device-config, tolerance, threshold, and artifact-path values.

`SystemBarAppearanceInstrumentedTest.kt` is authoritative for several of those details:

- API-level assertion (`35`)
- RGB tolerance (`±12` per channel)
- match-ratio threshold (`>= 0.70`)
- device-side screenshot path (`/sdcard/Download/RustChessEvidence/system-bars-api35.png`)

But the actual emulator/device configuration is **not** defined by that test. It is defined in `.github/workflows/android.yml`, including:

- API 35
- x86_64
- `google_apis`
- Pixel 2 profile
- SwiftShader/headless emulator options

The workflow also defines how `/sdcard/Download/RustChessEvidence` is pulled into `android-ui-evidence/` and uploaded as the permanent UI-evidence artifact.

### Question / requested clarification

Please change SC-002 to explicitly verify the restored evidence against **both**:

- `SystemBarAppearanceInstrumentedTest.kt`; and
- `.github/workflows/android.yml`.

It would be better to record all three artifact-location layers distinctly:

1. device-side screenshot path;
2. path after `adb pull` in the CI workspace; and
3. uploaded GitHub Actions artifact name/path.

That would make the restored observation contract independently reproducible rather than conflating test constants with workflow configuration.

---

## 4. SC-003's artifact-backed fallback conflicts with current touched-file scope and one-task/one-commit rules

### Issue

The fallback disposition requires a **real preserved CI execution** of the bounded promotion-path search, with an artifact and exact run/job ID.

That likely requires some combination of:

- a committed search script/test/helper;
- a CI workflow or workflow modification that executes it;
- artifact upload logic;
- a CI run that produces the evidence;
- then cleanup of temporary validation machinery before final closure.

However, the spec's touched-file categories do not currently authorize `.github/workflows/**` or a general temporary validation script location for SC-003.

There is also a sequencing conflict with the global rule that each SC task lands in its own single commit. A CI run/job ID cannot exist until after the commit that triggers the run, and any temporary helper should not remain in the final tree.

### Question / requested clarification

Please explicitly allow SC-003 to use a bounded multi-commit sequence **if the `artifact-backed-blocker` disposition is selected**. For example:

1. committed probe/helper + temporary validation workflow;
2. CI run executes the bounded search and preserves an artifact;
3. evidence/disposition is recorded after the run exists;
4. temporary workflow/helper is removed before SC-004 final validation.

Also widen the touched-file scope to allow the necessary bounded temporary validation script/workflow.

The final tree should remain clean, but the evidence-producing machinery must exist long enough to make the claim independently verifiable.

---

## 5. Define the architectural boundary for SC-003's preferred fixture seam before implementation

### Issue

The low-level Kotlin `ChessEngine` API already supports position injection through `setPosition(fen)`, but the actual UI is driven through the separate high-level `ChessGame` API.

`ChessGame` currently:

- has a private constructor;
- owns the high-level JNI session;
- exposes create/snapshot/poll/submitMove/restart/resign;
- exposes no arbitrary position/FEN injection mechanism.

Therefore, making the **real production UI flow** start from a promotion-eligible high-level `ChessGame` state may require adding production JNI/high-level API surface solely for testing, which would contradict the stated constraint against adding a general FEN-loading feature or distorting production architecture.

### Question / requested clarification

Please make the decision boundary explicit before implementation:

> If a genuinely `androidTest`-only fixture seam cannot be built without adding production/native API surface or changing the production ownership model, the preferred seam disposition is considered impractical and SC-003 must immediately take the artifact-backed-search disposition.

This prevents testability work from becoming an accidental product/API expansion.

A test-only implementation should remain non-player-reachable and should not require Kotlin chess-rule logic.

---

## 6. Editorial cross-reference error

### Issue

SC-003 says its CC-004 TODO correction should be provenance-preserving "per §5.3 below."

But §5.3 is SC-003's tests section. The provenance-preserving correction rules are in **§6.3**.

### Requested fix

Change the cross-reference from `§5.3` to `§6.3`.

---

## Recommended pre-implementation disposition

The second-corrections program is technically justified and the closure-SHA protocol is already in a sound terminating form. I do **not** recommend another redesign of the closure protocol.

Before implementation, I recommend resolving items **1 through 5** above in the spec/TODO. Item 6 is a straightforward editorial correction.
