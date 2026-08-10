# Chess Engine

[![CI](https://github.com/ekkus93/chess-engine/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/ekkus93/chess-engine/actions/workflows/ci.yml)
[![Android JNI](https://github.com/ekkus93/chess-engine/actions/workflows/android.yml/badge.svg?branch=master)](https://github.com/ekkus93/chess-engine/actions/workflows/android.yml)
[![Robustness](https://github.com/ekkus93/chess-engine/actions/workflows/robustness.yml/badge.svg?branch=master)](https://github.com/ekkus93/chess-engine/actions/workflows/robustness.yml)
[![Performance](https://github.com/ekkus93/chess-engine/actions/workflows/performance.yml/badge.svg?branch=master)](https://github.com/ekkus93/chess-engine/actions/workflows/performance.yml)
[![Variant validation](https://github.com/ekkus93/chess-engine/actions/workflows/variant-validation.yml/badge.svg?branch=master)](https://github.com/ekkus93/chess-engine/actions/workflows/variant-validation.yml)

A correctness-first Rust chess engine with Linux UCI, native TUI, scrolling-console, and Android applications; portable engine/search crates; C and JNI adapters; explicit opening-book support; offline self-play and tuning infrastructure; and permanent perft, differential, robustness, performance, and strength gates.

**Authoritative implementation:** the Rust workspace on `master`. New integrations should use the safe Rust crates, UCI executable, native Rust TUI, scrolling Rust console app, Android application/session API, C ABI, or JNI boundary. The full migration, traceability, versions, evidence, and roadmap are recorded in [`docs/RUST_CHESS_ENGINE_PORT_IMPLEMENTATION_REPORT.md`](docs/RUST_CHESS_ENGINE_PORT_IMPLEMENTATION_REPORT.md).

The former Python implementation remains in the repository as historical reference material. Python development and Python engine CI are intentionally retired after migration signoff. Python remains permitted for the pinned independent `python-chess` differential oracle and repository validation tooling; production Rust crates do not embed or launch Python.

The built-in baseline evaluation weights remain authoritative. The production candidate-validation control completed 200 color-balanced opening pairs and 400 games but was rejected for insufficient strength, so it was never activated. Any future weight promotion must pass the unchanged fail-closed protocol and be applied by a separate explicit source change.

## Start here

```bash
git clone https://github.com/ekkus93/chess-engine.git
cd chess-engine
bash scripts/dev.sh bootstrap
bash scripts/dev.sh fast
```

All supported developer entry points are listed by:

```bash
bash scripts/dev.sh help
```

The full workflow, prerequisites, output ownership, and CI mapping are documented in [`docs/RUST_DEVELOPER_WORKFLOWS.md`](docs/RUST_DEVELOPER_WORKFLOWS.md).

## Common commands

```bash
# Fast Rust validation
bash scripts/dev.sh fast

# Complete local Rust validation
bash scripts/dev.sh full

# Authoritative perft suite through depth 4
bash scripts/dev.sh perft

# Linux UCI protocol engine
bash scripts/dev.sh uci

# Native full-screen Rust TUI
bash scripts/dev.sh tui

# Human-facing scrolling Rust console
bash scripts/dev.sh console

# Real-process console acceptance coverage
bash scripts/dev.sh console-smoke

# Additional real-PTY TUI acceptance coverage
bash scripts/dev.sh tui-pty-smoke

# Build JNI, test harnesses, and the playable Android app
bash scripts/dev.sh android
```

## Human-facing applications

The native TUI, scrolling console, and Android application share presentation-neutral game/search behavior through `chess-app`. `chess-app` owns game configuration and lifecycle, generation/ticket state, exact search-worker events, cancellation, stale-result rejection, and the interactive fail-closed search policy. Chess rules and SAN notation remain in `chess-core`; search remains in `chess-search`.

### Native Rust TUI

`crates/chess-tui` is the existing Ratatui/Crossterm full-screen frontend. It retains menu state, overlays, move-entry editing, responsive layout, terminal raw/alternate-screen lifecycle, and TUI save UI. It does not launch `chess-uci` as a subprocess and has no Python runtime dependency.

Run it with:

```bash
bash scripts/dev.sh tui
```

Human games accept UCI coordinate input such as `e2e4` and `e7e8q`; board orientation follows the human color. Self-play supports pause/resume and a one-ply step while paused. Search uses the shared bounded worker with request-generation checks, explicit cancellation, visible failures, metrics, and no TUI-level random/first-legal fallback.

`bash scripts/dev.sh tui-pty-smoke` drives the real binary through an OS pseudo-terminal and preserves launch/quit, human move + engine reply, Self-play pause/step/resume, resignation, quit-during-search, resize, and save success/failure regressions.

### Scrolling Rust console

`crates/chess-console` is a separate line-oriented stdin/stdout frontend. It does not use Ratatui, Crossterm, raw mode, alternate screen, Python, or a `chess-uci` subprocess. Normal terminal scrollback remains available.

Run it with:

```bash
bash scripts/dev.sh console
```

Startup supports Human vs Engine, Self-play, and Quit. Human mode selects White/Black and an explicit engine depth; Self-play selects independent White/Black depths. Invalid depths are rejected rather than silently clamped.

Game commands are case-insensitive:

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

`pause`, `resume`, and `step` are Self-play controls. `resign` is Human-vs-Engine only. Destructive active-game actions and overwriting an existing save require explicit confirmation; empty confirmation means No. EOF is distinct from empty input and resolves an active engine worker before exit.

Console saves use deterministic text beginning with `Chess Engine Rust Console save v1`. The format records mode/configuration, ordered UCI moves, result, and an explicit timestamp label. It is intentionally **not PGN**. Saves use the shared same-directory atomic write/rename primitive, have no implicit destination or auto-save behavior, and report failures visibly.

`bash scripts/dev.sh console-smoke` runs real-process acceptance tests for startup/quit, Human White and Human Black engine flows, illegal-move visibility, resignation confirmation, save/overwrite/failure behavior, Self-play pause/step/resume, confirmed quit during active search, and EOF during active search.

### Android application

`android-harness/android-app` is a real portrait-only launcher application built with Kotlin and Jetpack Compose. It is separate from `android-harness/android-smoke`, which remains an instrumentation harness.

Android v0.1 supports Human vs Engine play, White/Black selection, engine depths 1–12, tap-to-move board input, explicit promotion choice, human-side board orientation, a fixed non-scrolling game shell, Rust-generated SAN move history, bounded engine metrics/PV, restart/resign/new-game confirmations, and visible errors. The redesigned dark UI keeps compact status, square board, Moves/Engine tabs, bounded tab content, and all three game actions visible in one portrait viewport.

The app uses the high-level Kotlin `ChessGame` API in `crates/chess-jni`. Its native owner contains the same Rust `chess_app::GameController` and `SearchWorker` used by the other interactive frontends. Kotlin projects Rust-provided FEN/legal moves/SAN history into UI state; it does not implement another chess rule engine, SAN rules, opening-book policy, fallback move selection, or independent engine-turn scheduling.

Permanent API-35 Compose instrumentation enforces compact 360 × 640 layout containment, enlarged-text behavior, selected-state semantics, stable board geometry, internal-only move-history scrolling, real Human White/Black flows, the one-second human-move reveal interval, dialogs, and SHA-scoped device-framebuffer visual evidence.

Build the Android app and both JNI ABIs with:

```bash
export ANDROID_NDK_HOME="$HOME/Android/Sdk/ndk/<version>"
export ANDROID_API_LEVEL=24
bash scripts/dev.sh android
```

The debug APK is produced at `android-harness/android-app/build/outputs/apk/debug/android-app-debug.apk`. See [`docs/RUST_ANDROID_APP.md`](docs/RUST_ANDROID_APP.md) and [`docs/RUST_ANDROID_UI_UX_REDESIGN_CLOSURE_EVIDENCE_2026-08-10.md`](docs/RUST_ANDROID_UI_UX_REDESIGN_CLOSURE_EVIDENCE_2026-08-10.md).

## Workspace

- `crates/chess-core` — position representation, rules, legal generation, FEN/UCI/SAN notation, hashing, history, and exact perft.
- `crates/chess-search` — evaluation, transposition table, iterative deepening, limits, cancellation, and search.
- `crates/chess-app` — shared human-facing game/session/search orchestration, pure text formatting, and atomic save primitives.
- `crates/chess-book` — explicit opening-book abstraction and indexed format.
- `crates/chess-uci` — standalone machine-facing Linux UCI process adapter.
- `crates/chess-tui` — native Ratatui/Crossterm full-screen frontend over `chess-app`.
- `crates/chess-console` — human-facing scrolling stdin/stdout frontend over `chess-app`.
- `crates/chess-ffi` — safe facade and versioned C ABI.
- `crates/chess-jni` — low-level engine JNI adapter plus high-level `chess-app` interactive session adapter.
- `crates/chess-tools` — perft, oracle, benchmarks, self-play, tuning orchestration, and candidate evidence.
- `crates/chess-tune` — loss, named weight schemas, SPSA, checkpoints, and artifacts.
- `android-harness/android-app` — playable Kotlin/Jetpack Compose Android application.
- `android-harness/android-smoke` and `android-harness/host-jvm` — Android/JVM JNI integration tests.
- `fuzz` — separate fuzz workspace with committed corpora and minimized regressions.
- `fixtures` — versioned schemas and authoritative inputs.
- `benchmarks/task24` — accepted reference performance distributions.

Dependency direction and crate ownership are documented in [`docs/RUST_WORKSPACE_ARCHITECTURE.md`](docs/RUST_WORKSPACE_ARCHITECTURE.md).

## Design contracts

Core contracts include:

- canonical square mapping: `a8 = 0`, `h8 = 7`, `a1 = 56`, `h1 = 63`;
- one packed internal move identity, without exposing its bit layout as a stable ABI;
- strict six-field FEN and explicit promotion identity;
- private redundant position state with invariant checks;
- make/unmake recursive search rather than clone-per-child;
- incremental hash and repetition identity that normalize en-passant correctly;
- bounded transposition storage and normalized mate scores;
- no implicit filesystem discovery for weights, opening books, datasets, configuration, or frontend saves;
- interactive frontends play only exact completed search results and never promote search fallback/emergency moves into gameplay;
- no panic crossing C or JNI boundaries;
- correctness gates independent from strength and performance gates.

The authoritative port specification is [`docs/RUST_CHESS_ENGINE_PORT_SPEC_2026-08-01.md`](docs/RUST_CHESS_ENGINE_PORT_SPEC_2026-08-01.md).

## CI and evidence

Permanent workflows are intentionally separate:

- `CI` — Rust formatting, checks, Clippy, tests, release perft, rustdoc, x86-64 and ARM64 builds, and differential oracle;
- `Android JNI` — Kotlin/app lint and unit tests, host-JVM JNI, focused shared-app bridge tests, dual native ABIs, playable/test APKs, API-35 JNI lifecycle and full redesigned-app instrumentation, SHA-scoped real-emulator UI evidence, performance evidence, and a downloadable debug APK artifact;
- `Robustness` — fuzzing, Miri, ASan/LSan, and TSan;
- `Performance` — x86-64 and ARM64 regression budgets plus scheduled Callgrind;
- `Slow perft` — scheduled/manual authoritative depth five;
- `Strength` — scheduled/manual historical weight-only 200-pair, 400-game control validation;
- `Variant validation` — native x86-64/ARM64 complete-identity smoke, development, and production controls.

Generated-output rules and deliberate evidence promotion are defined in [`docs/RUST_GENERATED_ARTIFACT_POLICY.md`](docs/RUST_GENERATED_ARTIFACT_POLICY.md).

## Additional documentation

- [`docs/RUST_CHESS_ENGINE_PORT_IMPLEMENTATION_REPORT.md`](docs/RUST_CHESS_ENGINE_PORT_IMPLEMENTATION_REPORT.md)
- [`docs/RUST_DEVELOPER_WORKFLOWS.md`](docs/RUST_DEVELOPER_WORKFLOWS.md)
- [`docs/RUST_UCI_PROCESS_INTEGRATION.md`](docs/RUST_UCI_PROCESS_INTEGRATION.md)
- [`docs/RUST_TUI_SPEC.md`](docs/RUST_TUI_SPEC.md)
- [`docs/RUST_TUI_IMPLEMENTATION.md`](docs/RUST_TUI_IMPLEMENTATION.md)
- [`docs/RUST_CONSOLE_SPEC.md`](docs/RUST_CONSOLE_SPEC.md)
- [`docs/RUST_CONSOLE_TODO.md`](docs/RUST_CONSOLE_TODO.md)
- [`docs/RUST_CONSOLE_IMPLEMENTATION.md`](docs/RUST_CONSOLE_IMPLEMENTATION.md)
- [`docs/RUST_ANDROID_JNI.md`](docs/RUST_ANDROID_JNI.md)
- [`docs/RUST_ANDROID_APP.md`](docs/RUST_ANDROID_APP.md)
- [`docs/RUST_ANDROID_UI_UX_REDESIGN_CLOSURE_EVIDENCE_2026-08-10.md`](docs/RUST_ANDROID_UI_UX_REDESIGN_CLOSURE_EVIDENCE_2026-08-10.md)
- [`docs/RUST_ANDROID_TEST_HARNESS.md`](docs/RUST_ANDROID_TEST_HARNESS.md)
- [`docs/RUST_FUZZING.md`](docs/RUST_FUZZING.md)
- [`docs/RUST_SELF_PLAY_DATASET.md`](docs/RUST_SELF_PLAY_DATASET.md)
- [`docs/RUST_TUNING_WORKFLOW.md`](docs/RUST_TUNING_WORKFLOW.md)
- [`docs/RUST_PERFORMANCE_GATES.md`](docs/RUST_PERFORMANCE_GATES.md)
- [`docs/RUST_ROBUSTNESS_GATES.md`](docs/RUST_ROBUSTNESS_GATES.md)
- [`docs/RUST_CANDIDATE_VALIDATION.md`](docs/RUST_CANDIDATE_VALIDATION.md)

## License

MIT. See [`LICENSE`](LICENSE).
