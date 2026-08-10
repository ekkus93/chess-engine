# Rust developer workflows

The Rust workspace is the actively developed engine. The Python implementation remains historical reference material only: Python engine feature development and Python engine CI are retired.

All repository-supported local commands go through one dispatcher:

```bash
bash scripts/dev.sh help
```

The dispatcher uses committed lockfiles and explicit input/output paths. It does not discover opening books, datasets, checkpoints, weights, configuration, or frontend save destinations from conventional locations.

## Bootstrap

Prerequisites:

- Linux x86-64 or ARM64;
- `rustup` and Cargo;
- Python 3 with `venv` support for the pinned `python-chess` differential oracle;
- Java 17, Gradle 8.9, and an Android NDK only for the Android command.

Run once after cloning or after dependency/toolchain changes:

```bash
bash scripts/dev.sh bootstrap
```

This installs required Rust components and targets, fetches locked Cargo dependencies, and creates `.venv-oracle` from `requirements/oracle.txt`.

## Validation

Fast validation:

```bash
bash scripts/dev.sh fast
```

It runs the generated-artifact audit, script unit tests, shell syntax checks, consolidated strength/authority audit, rustfmt, locked all-target/all-feature check, strict Clippy, and the complete Rust workspace test suite.

Full local validation:

```bash
bash scripts/dev.sh full
```

It includes the fast gate plus release depth-four perft, warning-free rustdoc, debug/release workspace builds, and the pinned differential corpus/seeded-playout oracle. Run bootstrap first so `.venv-oracle` exists.

The slow depth-five perft, bounded fuzz campaigns, Miri, sanitizers, dual-architecture performance measurements, Android API-35 instrumentation, historical strength control, and complete-variant controls remain independent CI workflows because they require specialized runners or extended execution.

Run the consolidated v0.2 authority audit directly with:

```bash
bash scripts/dev.sh strength-audit
```

## Perft

```bash
bash scripts/dev.sh perft       # authoritative suite through depth 4
bash scripts/dev.sh perft 5     # full depth-five suite
```

For one position or divide output, use the underlying explicit tooling as documented by `bash scripts/dev.sh help` and the perft documentation.

## UCI

Run the machine-facing Linux UCI process on stdin/stdout:

```bash
bash scripts/dev.sh uci
```

Supply an opening book only through the explicit adapter argument:

```bash
bash scripts/dev.sh uci --book /absolute/path/opening-book-v1.bin
```

A smoke transcript can be sent without a GUI:

```bash
printf 'uci\nisready\nposition startpos\ngo depth 3\nquit\n' | bash scripts/dev.sh uci
```

See `docs/RUST_UCI_PROCESS_INTEGRATION.md` and `docs/RUST_OPENING_BOOK_ADAPTER_INTEGRATION.md`.

## Native Rust TUI

Run the existing full-screen Ratatui/Crossterm frontend with:

```bash
bash scripts/dev.sh tui
```

The TUI is retained as a supported frontend. It consumes the shared `chess-app` game/session/search layer while keeping its own menus, overlays, key handling, responsive rendering, and raw/alternate-screen terminal lifecycle.

Additional real-PTY acceptance coverage:

```bash
bash scripts/dev.sh tui-pty-smoke
```

The PTY suite drives the actual `chess-tui` process and preserves launch/quit, Human White move + engine reply, Self-play pause/step/resume, resignation, quit-during-search, resize, and save success/failure behavior.

Focused source-based TUI coverage remains available through:

```bash
bash scripts/dev.sh tui-coverage clean
bash scripts/dev.sh tui-coverage summary
bash scripts/dev.sh tui-coverage json
bash scripts/dev.sh tui-coverage lcov
bash scripts/dev.sh tui-coverage html
```

## Scrolling Rust console

Run the separate human-facing line-oriented console frontend with:

```bash
bash scripts/dev.sh console
```

This application uses ordinary stdin/stdout and normal terminal scrollback. It does not use Ratatui/Crossterm raw mode or alternate screen, and it does not launch `chess-uci` or Python. Shared game/search lifecycle comes from `chess-app`.

Startup supports:

1. Human vs Engine;
2. Self-play;
3. Quit.

Human mode selects White/Black and engine depth. Self-play selects independent White/Black depths. Empty selections use documented defaults; invalid/out-of-range depths are rejected and reprompted rather than silently clamped.

During a game, supported commands are:

```text
e2e4 | move e2e4
board
moves
status
engine
help
resign
save <path>
new
menu
quit
pause
resume
step
```

Move legality remains core-owned. `pause`/`resume`/`step` are Self-play-only, and `resign` is Human-vs-Engine-only. Destructive active-game actions and overwrite of an existing save require explicit confirmation; empty confirmation defaults to No.

Console saves are deterministic versioned text, not PGN. They have explicit paths, no automatic save directory, and no auto-save. The final file is published through the shared atomic same-directory write/rename primitive; failures are printed and never reported as success.

The stdin reader is state-free: it sends typed input events but never owns `GameController` or an engine worker. EOF is distinct from an empty command, cancels/joins any active engine worker, and exits deterministically. An interactive OS stdin read may remain blocked after explicit process quit; this is documented rather than falsely described as joined. Engine workers are always resolved explicitly.

Run real-process acceptance coverage with:

```bash
bash scripts/dev.sh console-smoke
```

This drives the actual `chess-console` executable through piped stdin/stdout and covers menu quit, Human White and Black engine flows, illegal-move visibility, resignation confirmation, save/overwrite/failure behavior, Self-play pause/step/resume, confirmed quit during active search, and EOF during active search.

See `docs/RUST_CONSOLE_SPEC.md`, `docs/RUST_CONSOLE_TODO.md`, and `docs/RUST_CONSOLE_IMPLEMENTATION.md`.

## Android application and JNI

The Android project contains three separate surfaces:

- `android-harness/android-app` — the playable portrait Kotlin/Jetpack Compose application;
- `android-harness/android-smoke` — Android JNI/instrumentation harness;
- `android-harness/host-jvm` — host JVM JNI contract tests.

The playable app uses the high-level Kotlin `ChessGame` owner backed by `chess-app::GameController` and `SearchWorker`. The existing low-level Kotlin `ChessEngine` API over `chess-ffi` remains supported and independently tested. Rust `chess-core` owns SAN formatting; the high-level snapshot transports both UCI history and Rust-generated SAN, while Kotlin remains presentation/controller glue.

Set the NDK explicitly, then build both JNI ABIs, run app unit/lint gates, build the playable and test APKs, build the historical harness/test APKs, and run the host-JVM JNI contract:

```bash
export ANDROID_NDK_HOME="$HOME/Android/Sdk/ndk/<version>"
export ANDROID_API_LEVEL=24
bash scripts/dev.sh android
```

The local command does not start an emulator. The playable debug APK is written to:

```text
android-harness/android-app/build/outputs/apk/debug/android-app-debug.apk
```

Permanent Android CI additionally runs API-35 instrumentation. It validates the historical JNI lifecycle/performance suite and the redesigned playable application, including:

- deterministic 360 × 640 dp Setup/Game containment and no root scrolling;
- enlarged-text containment;
- selected side/tab/square semantics;
- stable board/action geometry across idle, thinking, engine reply, and tab changes;
- internal-only SAN move-history scrolling plus follow-bottom/preserve-history policy;
- exact promotion mapping;
- Human White and Human Black shared-Rust-controller flows;
- the approximately one-second post-human-move reveal interval;
- themed confirmation, promotion, and error dialogs;
- SHA-scoped real API-35 device-framebuffer screenshots with a SHA256 manifest;
- debug APK and performance-evidence artifacts.

The UI evidence capture is a permanent read-only CI behavior; it does not modify repository source or commit generated artifacts. The accepted redesign evidence and exact run/artifact identifiers are recorded in `docs/RUST_ANDROID_UI_UX_REDESIGN_CLOSURE_EVIDENCE_2026-08-10.md`.

See `docs/RUST_ANDROID_JNI.md`, `docs/RUST_ANDROID_TEST_HARNESS.md`, and `docs/RUST_ANDROID_APP.md`.

## Offline self-play

```bash
mkdir -p self-play-output
bash scripts/dev.sh self-play \
  fixtures/self_play_config.example \
  self-play-output/dataset.txt
```

Every path is explicit. The output is generated evidence and is ignored by default. Promote a dataset into `fixtures/` only through an intentional review that records schema, provenance, and purpose.

## Offline tuning

Create a real configuration from `fixtures/tuning_config.example`, then run:

```bash
bash scripts/dev.sh tune \
  /path/to/tuning-config.txt \
  /path/to/self-play-dataset.txt \
  tuning-output/candidate-001
```

Resume from a previous complete output directory into a new output directory by supplying the checkpoint/output path as the fourth argument. Candidates remain inactive until a separate explicit validation/activation process succeeds.

## Complete-variant control evidence

Run one local complete-variant control from a clean committed checkout:

```bash
bash scripts/dev.sh variant-control \
  variant-evidence-smoke \
  smoke \
  fixed_nodes
```

The command records exact source/build/invocation provenance, refuses a dirty checkout or existing output directory, and cannot activate runtime defaults.

## Fuzzing

Stable parser/corpus regressions:

```bash
bash scripts/dev.sh fuzz-smoke
```

Bounded libFuzzer, Miri, and sanitizer commands are documented in `docs/RUST_FUZZING.md` and run permanently in `.github/workflows/robustness.yml`.

## CI matrix

Permanent independent workflows include:

- `CI`: x86-64 quality/release/perft/oracle plus native ARM64 workspace builds;
- `Android JNI`: Android/Kotlin lint and app unit tests, host JVM low-level JNI contract, focused high-level shared-app bridge tests, dual JNI ABIs, harness/playable APKs, API-35 compact/adaptive/accessibility/end-to-end UI instrumentation, real-emulator visual evidence, performance evidence, and a debug-app artifact;
- `Robustness`: fuzz, Miri, ASan/LSan, and TSan;
- `Performance`: x86-64/ARM64 budgets and scheduled Callgrind;
- `Slow perft`: scheduled/manual depth-five fixtures;
- `Strength`: scheduled/manual historical strength control;
- `Variant validation`: native x86-64/ARM64 complete-identity smoke, development, and production controls.

`report-master-validation.yml` reports completed exact-`master` runs to the repository validation issue. No workflow combines performance, strength, or robustness results with correctness in a way that can hide a failure.
