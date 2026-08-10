# Rust Chess Android App

**Status:** playable portrait Android v0.1 application with the production UI/UX redesign implemented over the shared Rust application/session layer.

## Purpose

`android-harness/android-app` is the repository's user-facing Kotlin/Jetpack Compose Android application. It is separate from `android-harness/android-smoke`, which remains a focused JNI/instrumentation harness, and from `android-harness/host-jvm`, which tests the JVM/JNI contract on the host.

Android remains a presentation adapter. Chess rules, SAN notation, human-move validation, engine-turn scheduling, opening-book/search policy, stale-result rejection, exact-search-result policy, and terminal outcomes remain authoritative in Rust.

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

`chess-jni` also retains the existing low-level `ChessEngine` API over `chess-ffi`. The playable application uses the high-level `ChessGame` API, whose native owner contains a real `chess_app::GameController` and at most one active `SearchWorker`.

Kotlin does not choose engine moves, apply fallback moves, retry failed searches, implement chess legality, implement SAN disambiguation, or independently reproduce the TUI/console session state machine.

## Product UI

The shipped Android UI is portrait-only and uses a fixed primary viewport rather than a vertically scrolling game page. The product theme is a first-party dark design system used by launch/system bars, setup, game shell, board chrome, panels, controls, and dialogs.

### Setup

Setup provides:

- explicit White/Black selection with selected-state semantics and a non-color checkmark cue;
- engine depth 1 through 12;
- stable player-facing descriptors: `Quick` (1–2), `Balanced` (3–5), `Strong` (6–8), and `Deep` (9–12);
- one fixed Start Game action;
- explicit cleanup-retry UI if a reachable native owner could not be closed.

Unsupported depth values are not given a presentation descriptor. The slider conversion is the only intended UI clamping point; native/session depth validation remains strict.

### Game shell

The game screen keeps all primary regions visible at once:

1. compact fixed-height turn/status region;
2. centered square board;
3. fixed `Moves` / `Engine` selector;
4. bounded shared tab body;
5. fixed New Game / Restart / Resign action row.

The root game screen is deliberately not vertically scrollable. Secondary content adapts inside the bounded tab body instead of pushing the board or actions off-screen.

### Board

The board:

- remains a presentation of authoritative Rust FEN/legal-move state;
- orients to the human side;
- uses first-party vector piece artwork drawn in Compose Canvas rather than Unicode chess glyphs or third-party piece images;
- preserves the standard square parity (`a1` dark);
- shows coordinates;
- uses an outline plus color for the selected square;
- uses a dot for an empty legal destination and a ring for a legal capture;
- highlights the exact latest authoritative UCI move;
- keeps board-square coordinate/piece/selection/legal-target semantics.

Move generation and legality are not duplicated in Kotlin. Selectable sources and legal destinations are projections of the Rust-provided legal UCI move list.

### Status and one-second reveal

The fixed status region shows the current turn/outcome, human side, configured depth, and concise status text. The spinner appears inside fixed bounds, so `Your move` -> `Engine thinking…` -> `Your move` does not move the board.

After a human move, Android immediately publishes the returned post-human snapshot. If Rust reports `thinking=true`, the ViewModel deliberately waits approximately one second before its first engine-result poll. Engine computation continues during that presentation interval. This keeps the human move visibly present before the engine reply while preserving shared Rust search ownership.

### Moves tab

Player-facing move history is SAN generated in `chess-core`. JNI snapshot v2 carries SAN history in addition to the existing authoritative UCI history. Kotlin only groups SAN strings into numbered White/Black display rows; it does not implement notation rules.

The Moves list is the only vertically scrollable game-content region. Its deterministic policy is:

- when the list is already at/near the bottom, a new row remains visible;
- when the user has manually moved to historical rows, a new move does not yank the list back to the bottom;
- tab switching preserves the move-list state;
- restart/new-game state resets naturally with the new history.

UCI history remains authoritative for exact move identity, tests, and board last-move highlighting.

### Engine tab

The bounded Engine tab shows available search data without inventing missing values:

- depth;
- score;
- nodes;
- NPS;
- elapsed time;
- principal variation;
- secondary data where available.

Large counts are formatted for presentation while retaining their underlying snapshot values. Long PV text is bounded inside the tab body. The UI does not infer a book hit from zero nodes/timing; book/search source policy remains Rust-owned.

### Actions and dialogs

New Game, Restart, and Resign remain simultaneously visible in a fixed action row. All three retain confirmation semantics. Resign has destructive styling and is disabled after a terminal outcome.

The themed modal flows include:

- New Game confirmation;
- Restart confirmation;
- Resign confirmation;
- Queen/Rook/Bishop/Knight promotion choice mapped back to the exact authoritative legal UCI promotion move;
- `Chess engine error` with real error text and bounded dialog-internal scrolling for long messages.

Dialogs do not auto-retry search, silently reset a game, or choose a fallback move.

## Native snapshot contract

`ChessGame` receives a versioned immutable high-level JNI snapshot containing:

- authoritative FEN;
- current legal UCI moves;
- ordered authoritative UCI history;
- ordered Rust-generated SAN history;
- human color and side to move;
- engine-thinking state;
- terminal outcome/status text;
- available engine metrics and principal variation.

Snapshot parsing validates the exact protocol version/shape. The Compose board parses FEN only for display. While `thinking=true`, `ChessViewModel` polls the high-level JNI session from `Dispatchers.Default`; typed worker events are drained into the shared Rust `GameController`, and a completed engine move is revalidated/applied in Rust before the next snapshot reaches Kotlin.

## Failure and lifecycle policy

The Android application inherits the shared fail-closed interactive search policy:

- no random legal-move fallback;
- no first-legal-move fallback;
- no silent search retry;
- no silent depth reduction;
- no UI-side opening-book move selection;
- no Python fallback;
- no UCI subprocess fallback;
- stale search completions cannot mutate a restarted or abandoned game;
- search/book/channel/worker failures remain visible rather than selecting another move source.

Native search workers are cancelled and joined on restart, resignation, and close. High-level native destroy removes an opaque game handle only after cleanup succeeds. Kotlin clears its corresponding handle only after native destruction succeeds.

Startup has the same reachable-owner guarantee. Once `ChessGame.create()` succeeds, the ViewModel retains that owner before requesting the first snapshot. If the first snapshot fails and the immediate explicit close also fails, the owner remains reachable, configuration is locked, both failures are visible, and Setup presents `Retry cleanup`. No silent retry occurs.

A PhantomReference reaper exists only as a last-resort leak backstop after an owner is already unreachable. Explicit `ChessGame.close()` is the authoritative lifecycle path.

## Accessibility and compact-layout contracts

Permanent Compose instrumentation covers a deterministic 360 × 640 dp viewport and enlarged `fontScale = 1.3`. Primary regions must be fully contained, the board must remain square, and the Setup/Game roots must not expose a root scroll action.

Interactive side/tab/action controls retain practical touch targets; selected side/tab/square state is exposed semantically and is not communicated by color alone. Legal-target geometry supplies a non-color spatial cue in addition to its semantic label.

## Build

The app stays on the repository's established Android toolchain generation:

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

The local gate does not launch an emulator.

## Permanent automated validation

`.github/workflows/android.yml` validates the low-level JNI contract and playable application together with least-privilege `contents: read` permissions. It runs:

- Android/Kotlin lint;
- app JVM unit tests for FEN/board presentation, board parity, SAN-row projection, depth descriptors, promotion mapping, and related pure presentation contracts;
- existing host JVM JNI contract tests;
- focused Rust high-level `chess-app` JNI bridge tests;
- ARM64 and x86_64 JNI cross-builds;
- JNI symbol/architecture checks;
- historical `android-smoke` library/test APK compilation and API-35 execution;
- playable app and instrumentation-APK compilation;
- compact 360 × 640 layout/containment assertions;
- enlarged-text layout assertions;
- selected-state/accessibility semantics;
- move-history internal scrolling and follow/preserve behavior;
- real Human White and Human Black shared-Rust-controller flows;
- one-second human-move visibility regression;
- themed dialog/promotion/error evidence;
- real device-framebuffer UI evidence capture from the API-35 emulator;
- SHA256 manifest generation for the UI evidence;
- performance evidence publication;
- debug APK publication.

The permanent UI evidence artifact is SHA-scoped and contains real emulator pixels rather than generated mockups. See `docs/RUST_ANDROID_UI_UX_REDESIGN_CLOSURE_EVIDENCE_2026-08-10.md` for the accepted exact-SHA run, artifact IDs/digests, screenshot hashes, before/after review, and manual-only follow-ups.

The smoke harness remains a test surface; it is not renamed or repurposed as the application.

### Board sizing

The playable Compose shell computes `boardSize` as the minimum of available width and available height after subtracting the fixed `statusHeight`, `tabHeight`, `actionHeight`, `minimumPanelHeight`, and four inter-region gaps. This is a shrink-before-clip policy: the board gives up size before the status, tabs, bounded panel, or action row can be clipped.
