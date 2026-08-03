#!/usr/bin/env python3
from pathlib import Path

# Comment-only trigger after the registered Android workflow is syntactically valid.
IMPLEMENTATION_SHA = "0af14c4bdb7e8de645f27182a788e5eef5297d5f"
RUST_RUN = "30847895229"
RUST_JOB = "91800574469"
ANDROID_RUN = "30847895345"
HOST_JOB = "91800574845"
EMULATOR_JOB = "91800574914"


def replace_once(text: str, old: str, new: str, label: str) -> str:
    count = text.count(old)
    if count != 1:
        raise SystemExit(f"{label}: expected one occurrence, found {count}")
    return text.replace(old, new)


definitions_path = Path(
    "docs/RUST_CHESS_ENGINE_PORT_TODO_TASK_DEFINITIONS_2026-08-01.md"
)
definitions = definitions_path.read_text()
open_block = """## 18.5 Android test harness

- [ ] Host JVM contract tests where possible.
- [ ] Instrumented or emulator smoke test.
- [ ] Verify no search on main thread in sample integration.
- [ ] Verify repeated lifecycle create/search/stop/destroy.
- [ ] Record Android target/toolchain instructions.
"""
closed_block = open_block.replace("- [ ]", "- [x]")
definitions = replace_once(
    definitions, open_block, closed_block, "Task 18.5 definition block"
)
task19 = definitions.split("# Task 19:", 1)[1]
if "- [x]" in task19.split("# Task 20:", 1)[0]:
    raise SystemExit("Task 19 must remain entirely open")
definitions_path.write_text(definitions)


todo_path = Path("docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md")
todo = todo_path.read_text()
todo = replace_once(
    todo,
    "# Task 18: Safe API, C ABI, and JNI — IN PROGRESS",
    "# Task 18: Safe API, C ABI, and JNI — COMPLETE",
    "Task 18 heading",
)
todo = replace_once(
    todo, "- [ ] 18.5 Android harness.", "- [x] 18.5 Android harness.", "18.5 marker"
)
todo = replace_once(
    todo, "- [ ] Task 18 gate.", "- [x] Task 18 gate.", "Task 18 gate marker"
)
todo = replace_once(
    todo,
    "| 17–24 | **Not started**. |",
    "| 17 | **Complete** — Linux UCI executable. |\n"
    "| 18 | **Complete** — safe API, C ABI, JNI, host JVM, and Android emulator harness. |\n"
    "| 19–24 | **Not started**. |",
    "program summary",
)
todo = replace_once(
    todo, "- [ ] AArch64 compile CI.", "- [x] AArch64 compile CI.", "AArch64 CI"
)
todo = replace_once(
    todo,
    "- [ ] Android compile and JNI CI.",
    "- [x] Android compile and JNI CI.",
    "Android JNI CI",
)
todo = replace_once(todo, "- [ ] ABI/JNI.", "- [x] ABI/JNI.", "ABI/JNI docs")
if "### Task 18.5 and Task 18 gate completion evidence" in todo:
    raise SystemExit("Task 18.5 evidence already exists")

evidence = f"""

### Task 18.5 and Task 18 gate completion evidence

- Harness: `android-harness/settings.gradle.kts`, the `host-jvm` and `android-smoke` modules, the exact production Kotlin source set, and `docs/RUST_ANDROID_TEST_HARNESS.md`.
- Permanent read-only Android gate: `.github/workflows/android.yml`; generated native staging: `scripts/prepare_android_harness_jni.sh`; dual-target build support: `scripts/build_android_jni.sh`.
- The host JVM module loads the real release `libchess_jni.so`; no mock binding or copied wrapper exists. Four JUnit tests cover the public lifecycle, typed invalid-FEN state preservation, active native cancellation with live worker-stack observation, and 24 repeated create/search-or-stop/destroy lifecycles.
- The Android module packages nonempty API-24 ARM64 and x86_64 JNI libraries, verifies both ELF architectures and the exact exported `nativeSearch` symbol, and builds the Android library plus test APK.
- Three instrumentation tests passed on an Android 15 / API-35 x86_64 Google APIs emulator: complete JNI lifecycle, Android-main-thread sample entry with the synchronous native method observed on `chess-engine-search`, and 16 repeated alternating fixed-depth/cancelled-infinite lifecycle runs.
- Main-thread exclusion is executable evidence: `Instrumentation.runOnMainSync` starts the sample request, while live ART stacks must show `NativeChessEngineBindings.nativeSearch` on `chess-engine-search` and not the Android main-loop thread.
- Toolchain: Ubuntu 24.04, Java 17.0.19, Gradle 8.9, Android Gradle Plugin 8.7.3, Kotlin 2.0.21, compile SDK 35, minimum/API link level 24, NDK 29.0.14206865, Android clang 21.0.0, and emulator 37.1.11.0.
- Exact validated implementation SHA: `{IMPLEMENTATION_SHA}`.
- Permanent Rust validation: run `{RUST_RUN}`, job `{RUST_JOB}`.
- Permanent Android validation: run `{ANDROID_RUN}`; host JVM job `{HOST_JOB}`; Android emulator job `{EMULATOR_JOB}`.
- Rust results: formatting, committed lockfile, all-target/all-feature compilation, strict Clippy without suppressions, 306 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc, debug/release builds, and independent differential validation passed.
- Android results: four host JVM tests, dual-ABI cross-build and ELF verification, 59-task Android AAR/test-APK build, and three emulator instrumentation tests all passed.
- Accepted external notices were limited to GitHub Actions Node runtime/dependency deprecations, an informational inability to strip the JNI debug library, and normal emulator startup/shutdown diagnostics. No product failure or ignored test occurred.
- Task 18 is complete: the safe Rust facade, stable C ABI, ABI lifecycle/panic tests, JNI adapter, host JVM contract, and Android emulator path can create an engine, set/reset positions, obtain legal moves, search, cancel, and destroy without crashes, leaked owned handles, or UI-thread search execution.
- Task 19.1 opening-book abstraction is next.
"""
todo = replace_once(
    todo, "\n# Task 19: Opening book", evidence + "\n# Task 19: Opening book", "Task 19 insertion"
)
old_next = """## Immediate next operations

1. Implement Task 18.5 host JVM contract tests around the committed Kotlin wrapper.
2. Add a minimal Android/Gradle harness that packages the validated AArch64 `libchess_jni.so`.
3. Run an instrumented or emulator smoke path for create, position, legal moves, search, stop, and destroy.
4. Prove sample integration never invokes search on the Android main thread.
5. Exercise repeated create/search/stop/destroy lifecycles and record the exact Android target, NDK, Gradle, and emulator commands.
6. Close the overall Task 18 gate only after the Android harness is green.
"""
new_next = """## Immediate next operations

1. Implement Task 19.1 as a deterministic opening-book abstraction with no mandatory book dependency.
2. Define explicit probe inputs and typed no-entry/error outcomes without coupling the core rules layer to a file format.
3. Preserve legal-move validation and deterministic policy hooks at the adapter/search boundary.
4. Keep all book loading explicit; do not add automatic filesystem discovery or process-global state.
5. Add focused abstraction tests before selecting the Task 19.2 persisted format.
6. Leave Tasks 19.2–19.5 and the overall Task 19 gate open until their own evidence is complete.
"""
todo = replace_once(todo, old_next, new_next, "immediate next operations")
todo_path.write_text(todo)


ralph_path = Path("docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md")
ralph = ralph_path.read_text()
ralph = replace_once(
    ralph,
    "**Current phase:** Task 18.4 Android JNI complete; Task 18.5 Android harness is next",
    "**Current phase:** Task 18 complete; Task 19.1 opening-book abstraction is next",
    "Ralph current phase",
)
row_anchor = "| 18.4 | `466c7b504832afa2bf993cb10dcc0c12aefcf1c5` | `30844134371` / `91788114660` | Android JNI exports and typed Kotlin owner, background search, request-local cancellation, error mapping, deterministic close/reaper policy, nine focused JNI tests, 306 Rust tests, and AArch64 ELF proof `1fc49b6126ecb9faa4c0f167b272945d65aebbf1` green |"
new_row = row_anchor + f"\n| 18.5 / 18 gate | `{IMPLEMENTATION_SHA}` | Rust `{RUST_RUN}` / `{RUST_JOB}`; Android `{ANDROID_RUN}` / `{HOST_JOB}`, `{EMULATOR_JOB}` | real host JVM JNI contract, ARM64/x86_64 Android builds, API-35 emulator lifecycle, live off-main native-search proof, 24 host and 16 Android repeated lifecycles; complete Task 18 gate green |"
ralph = replace_once(ralph, row_anchor, new_row, "Ralph Task 18.5 row")
if "## Task 18.5 and Task 18 completion" in ralph:
    raise SystemExit("Ralph Task 18.5 section already exists")
ralph_section = f"""

## Task 18.5 and Task 18 completion

Implemented and validated:

- one pinned Gradle harness whose host and Android modules compile the exact production Kotlin wrapper;
- a real host JVM contract against the release JNI shared library, with four passing tests and 24 repeated lifecycles;
- explicit API-24 ARM64 and x86_64 Rust/NDK builds, ELF verification, symbol verification, and generated-artifact staging;
- a minimal Android sample controller and Android library/test APK;
- three passing tests on an Android 15/API-35 x86_64 emulator, including 16 repeated lifecycles;
- executable UI-thread exclusion: a request begins on the Android main loop while the synchronous native method is observed on `chess-engine-search`;
- permanent read-only Rust and Android CI, exact local commands, ownership policy, and generated-artifact policy;
- `docs/RUST_ANDROID_TEST_HARNESS.md`.

Evidence:

- exact validated implementation SHA: `{IMPLEMENTATION_SHA}`;
- Rust run/job: `{RUST_RUN}` / `{RUST_JOB}`;
- Android run: `{ANDROID_RUN}`;
- host JVM job: `{HOST_JOB}`;
- Android emulator job: `{EMULATOR_JOB}`;
- NDK 29.0.14206865, Android clang 21.0.0, Java 17.0.19, Gradle 8.9, AGP 8.7.3, Kotlin 2.0.21, compile SDK 35, minimum/link API 24, and emulator 37.1.11.0;
- four host JVM tests and three emulator tests passed;
- both nonempty JNI libraries had the correct ELF machine and exported `nativeSearch` symbol;
- the complete permanent Rust quality, perft, documentation, build, and differential-oracle gate passed.

Task 18 is complete. Task 19.1 opening-book abstraction is next.
"""
ralph = replace_once(
    ralph, "\n## Task 12 completion", ralph_section + "\n## Task 12 completion", "Ralph insertion"
)
ralph_path.write_text(ralph)


harness_path = Path("docs/RUST_ANDROID_TEST_HARNESS.md")
harness = harness_path.read_text()
old_end = """## Validation state

The implementation branch is `task18-5-android-harness` and the validation pull request is `#235`. Task 18.5 evidence and the overall Task 18 gate remain open until the exact implementation head passes the permanent Rust quality job plus both permanent Android workflow jobs.
"""
new_end = f"""## Completion evidence

- Exact validated implementation SHA: `{IMPLEMENTATION_SHA}`.
- Permanent Rust validation: run `{RUST_RUN}`, job `{RUST_JOB}`.
- Permanent Android validation: run `{ANDROID_RUN}`.
- Host JVM job `{HOST_JOB}` passed four tests, including 24 repeated lifecycles and live observation of `nativeSearch` on `chess-engine-search`.
- Android job `{EMULATOR_JOB}` produced and verified API-24 ARM64 and x86_64 JNI libraries, built the AAR and test APK, and passed three tests on an Android 15/API-35 x86_64 emulator, including 16 repeated lifecycles and Android-main-thread exclusion.
- Hosted toolchain: Ubuntu 24.04, Java 17.0.19, Gradle 8.9, AGP 8.7.3, Kotlin 2.0.21, compile SDK 35, NDK 29.0.14206865 with clang 21.0.0, and emulator 37.1.11.0.
- The permanent Android workflow is read-only and generated JNI/APK/Gradle outputs remain ignored.
- Task 18.5 and the overall Task 18 gate are complete.
"""
harness = replace_once(harness, old_end, new_end, "harness completion")
harness_path.write_text(harness)


jni_path = Path("docs/RUST_ANDROID_JNI.md")
jni = jni_path.read_text()
if "## Task 18 integration closure" in jni:
    raise SystemExit("JNI integration closure already exists")
jni += f"""

## Task 18 integration closure

Task 18.5 executes this adapter through the exact production Kotlin source in both a host JVM and an Android API-35 emulator. The completed harness is documented in `docs/RUST_ANDROID_TEST_HARNESS.md`.

- Validated harness SHA: `{IMPLEMENTATION_SHA}`.
- Host JVM and Android workflow: `{ANDROID_RUN}` / `{HOST_JOB}`, `{EMULATOR_JOB}`.
- The host path passed four tests; the emulator path passed three tests.
- Live thread-stack evidence proves the synchronous JNI search executes on `chess-engine-search`, not the Android main loop.
- Task 18.5 and the overall Task 18 gate are complete.
"""
jni_path.write_text(jni)
