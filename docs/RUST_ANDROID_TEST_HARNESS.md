# Android/JVM JNI test harness

Task 18.5 provides executable JVM and Android coverage for the Task 18.4 Kotlin/JNI adapter. Both Gradle modules compile the exact production wrapper at `crates/chess-jni/kotlin/src/main/kotlin`; no copied or test-specific engine implementation exists.

## Layout

- `android-harness/host-jvm` runs the public Kotlin API against the host `target/release/libchess_jni.so`.
- `android-harness/android-smoke` packages the same wrapper and generated Android JNI libraries into a minimal Android library and test APK.
- `scripts/build_android_jni.sh` supports the pinned `aarch64-linux-android` and `x86_64-linux-android` Rust targets.
- `scripts/prepare_android_harness_jni.sh` stages both outputs under the Android module's ignored `jniLibs` tree.
- `.github/workflows/android.yml` is the permanent read-only host/JVM, cross-build, APK-build, and emulator gate.

The Gradle build is pinned to Gradle 8.9, Android Gradle Plugin 8.7.3, Kotlin 2.0.21, Java 17, compile SDK 35, and minimum Android API 24.

## Host JVM contract

Build the host JNI library and run the JVM tests from the repository root:

```bash
cargo build --locked -p chess-jni --release
gradle -p android-harness :host-jvm:test \
  --no-daemon --stacktrace --console=plain
```

The host suite uses the real shared library and covers:

- construction, version, FEN, legal moves, status, weight identity, search, move application, reset, idempotent close, and post-close rejection;
- typed invalid-FEN exception mapping with state preservation;
- active infinite-search cancellation through the native stop token; and
- twenty-four repeated create/search-or-stop/destroy lifecycles.

During the cancellation test, the suite samples live JVM thread stacks and requires the deterministic `chess-engine-search` thread to be inside `NativeChessEngineBindings.nativeSearch`. This verifies execution of the actual synchronous JNI method on the worker rather than the test caller.

## Android native libraries

Set an installed Android NDK and stage both supported ABIs:

```bash
export ANDROID_NDK_HOME=/path/to/android-ndk
export ANDROID_API_LEVEL=24
bash scripts/prepare_android_harness_jni.sh
```

This produces ignored local artifacts:

```text
android-harness/android-smoke/src/main/jniLibs/arm64-v8a/libchess_jni.so
android-harness/android-smoke/src/main/jniLibs/x86_64/libchess_jni.so
```

Build the library and instrumentation APKs with:

```bash
gradle -p android-harness \
  :android-smoke:assembleDebug \
  :android-smoke:assembleDebugAndroidTest \
  --no-daemon --stacktrace --console=plain
```

## Emulator contract

The permanent workflow boots an Android API-35 x86_64 Google APIs emulator and runs:

```bash
gradle -p android-harness \
  :android-smoke:connectedDebugAndroidTest \
  --no-daemon --stacktrace --console=plain
```

Instrumentation coverage performs a real create, FEN/legal/status query, fixed-depth search, move, reset, and destroy lifecycle. It also runs sixteen alternating fixed-depth and infinite-search cancellation lifecycles.

`ChessEngineSampleController.startInfiniteSearch` is invoked from the Android main thread through `Instrumentation.runOnMainSync`. While that request is active, the test samples ART thread stacks and requires `NativeChessEngineBindings.nativeSearch` to be executing on `chess-engine-search`, never the Android main-loop thread. This proves the sample integration does not block the UI thread without adding a production test hook or changing the JNI request/result format.

## Ownership and generated-artifact policy

Explicit `ChessEngine.close` remains authoritative and is exercised in every successful test path. JNI libraries and Gradle build directories are ignored generated artifacts and are never committed. The workflow has only `contents: read`; it cannot rewrite source or trackers.

## Completion evidence

- Exact validated implementation SHA: `0af14c4bdb7e8de645f27182a788e5eef5297d5f`.
- Permanent Rust validation: run `30847895229`, job `91800574469`.
- Permanent Android validation: run `30847895345`.
- Host JVM job `91800574845` passed four tests, including 24 repeated lifecycles and live observation of `nativeSearch` on `chess-engine-search`.
- Android job `91800574914` produced and verified API-24 ARM64 and x86_64 JNI libraries, built the AAR and test APK, and passed three tests on an Android 15/API-35 x86_64 emulator, including 16 repeated lifecycles and Android-main-thread exclusion.
- Hosted toolchain: Ubuntu 24.04, Java 17.0.19, Gradle 8.9, AGP 8.7.3, Kotlin 2.0.21, compile SDK 35, NDK 29.0.14206865 with clang 21.0.0, and emulator 37.1.11.0.
- Tracker-closure SHA: `31ef73ef4c663cfbee5476817c6d0ba4ed1ac8c1`.
- Permanent Android workflow restoration SHA: `564c89786511cebb9fb4eda1239db7f128593719`.
- Temporary trigger cleanup SHA: `caf0c33ef19f359903f7f208bb2277b1782de8b5`.
- The exact clean post-closure branch is required to pass both permanent workflows before it is fast-forwarded to `rust-engine`.
- The permanent Android workflow is read-only and generated JNI/APK/Gradle outputs remain ignored.
- Task 18.5 and the overall Task 18 gate are complete.
