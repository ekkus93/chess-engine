# Rust Chess Android App

**Status:** playable Android v0.1 application implemented over the shared Rust application/session layer.

## Purpose

`android-harness/android-app` is the repository's user-facing Android chess application. It is deliberately separate from `android-harness/android-smoke`, which remains a focused JNI/instrumentation harness.

The Android app is presentation code. Chess rules, human-move validation, engine-turn scheduling, stale-result rejection, exact-search-result policy, and terminal game outcomes remain authoritative in Rust.

## Architecture

```text
Jetpack Compose UI / ChessViewModel
              |
         Kotlin ChessGame
              |
   NativeChessAppBindings (JNI)
              |
          chess-jni
              |
          chess-app
         /         \
   chess-core    chess-search
```

`chess-jni` retains the existing low-level `ChessEngine` API over `chess-ffi` for engine/JNI consumers. The Android application uses the additional high-level `ChessGame` API, whose native owner contains a real `chess_app::GameController` and `SearchWorker`.

This means Kotlin does not choose engine moves, apply fallback moves, retry failed searches, perform chess legality checks, or independently reproduce the TUI/console session state machine.

## v0.1 user flow

The first Android application supports Human vs Engine play:

- choose White or Black;
- choose engine depth 1 through 12;
- tap a source square and then a legal destination;
- select Queen, Rook, Bishop, or Knight when promotion is required;
- Human Black starts with the engine's White move;
- orient the board from the human player's side;
- show engine thinking state and available depth, score, nodes, NPS, elapsed time, hash fullness, and PV;
- show ordered UCI move history;
- restart the current game with confirmation;
- resign with confirmation;
- close the current game and return to setup with confirmation;
- report native/application failures visibly.

Self-play remains available in `chess-app` but is intentionally not exposed by Android v0.1.

## Native session protocol

The Kotlin `ChessGame` owner receives versioned immutable snapshots from JNI. A snapshot contains:

- authoritative FEN;
- current legal UCI moves;
- ordered move history;
- human color and side to move;
- engine-thinking state;
- terminal outcome/status text;
- available engine metrics and principal variation.

The Compose board parses FEN only for presentation. Tap eligibility and legal destinations are projected from the Rust-provided legal move list; Android does not implement a second chess rule engine.

While a snapshot reports `thinking=true`, `ChessViewModel` polls the high-level JNI session from `Dispatchers.Default`. Each poll drains typed Rust worker events into `GameController`. The final engine move is therefore revalidated and applied by the shared Rust controller before the next snapshot reaches Kotlin.

## Failure and lifecycle policy

The Android application inherits the shared interactive fail-closed search policy:

- no random legal-move fallback;
- no first-legal-move fallback;
- no silent search retry;
- no silent depth reduction;
- no Python fallback;
- no UCI subprocess fallback;
- stale search completions cannot mutate a restarted or abandoned game;
- search/channel/worker failures remain visible rather than choosing another move source.

Native search workers are cancelled and joined on restart, resignation, and close. High-level native destroy removes its opaque handle only after cleanup succeeds. Kotlin likewise clears its handle only after native destruction succeeds, so an explicit close failure remains retryable rather than becoming an unreachable native leak.

A phantom-reference reaper exists only as a last-resort leak backstop for an unreachable owner. Explicit `ChessGame.close()` is the authoritative lifecycle path.

## Build

The app stays on the repository's existing Android toolchain generation rather than bundling a platform migration into this milestone:

- Gradle 8.9;
- Android Gradle Plugin 8.7.3;
- Kotlin 2.0.21;
- Java 17;
- compile/target SDK 35;
- minimum Android API 24.

Stage both native ABIs:

```bash
export ANDROID_NDK_HOME=/path/to/android-ndk
export ANDROID_API_LEVEL=24
bash scripts/prepare_android_harness_jni.sh
```

Build the playable debug APK:

```bash
gradle -p android-harness \
  :android-app:assembleDebug \
  --no-daemon --stacktrace --console=plain
```

The APK is written to:

```text
android-harness/android-app/build/outputs/apk/debug/android-app-debug.apk
```

The supported aggregate local Android gate is:

```bash
bash scripts/dev.sh android
```

## Automated validation

Permanent `.github/workflows/android.yml` validates the low-level JNI contract and the playable app together:

- Android/Kotlin lint;
- app JVM unit tests for FEN presentation and legal-move projection;
- existing host JVM JNI contract tests;
- focused Rust high-level `chess-app` JNI bridge tests;
- ARM64 and x86_64 JNI cross-builds;
- JNI symbol/architecture checks;
- historical `android-smoke` library/test APK compilation;
- playable app and instrumentation-APK compilation;
- API-35 emulator execution of the existing JNI lifecycle suite;
- API-35 emulator launcher smoke plus real Human White and Human Black shared-Rust-controller flows;
- debug APK publication as a workflow artifact.

The smoke harness remains a test surface; it is not renamed or repurposed as the application.
