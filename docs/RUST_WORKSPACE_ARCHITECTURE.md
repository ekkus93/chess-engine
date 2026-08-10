# Rust Workspace Architecture

**Status:** authoritative current workspace architecture  
**Branch:** `master`  
**Minimum supported Rust version:** 1.75  
**Toolchain policy:** stable Rust with `rustfmt` and Clippy

## Purpose

The workspace isolates portable chess logic from protocol, presentation, platform, and offline-tooling layers. Dependencies point outward from the core. No frontend or adapter may become a dependency of a lower-level engine crate.

The human-facing applications share presentation-neutral lifecycle/search behavior through `chess-app`; the full-screen TUI, scrolling console, and Android application remain separate presentation adapters.

## Crates

| Crate | Type | Responsibility | Allowed direct workspace dependencies |
|---|---|---|---|
| `chess-core` | library | Position model, moves, attacks, rules, FEN/UCI notation, game history, hashing, and exact perft | none |
| `chess-book` | library | Explicit opening-book interfaces and indexed format | `chess-core` |
| `chess-search` | library | Evaluation, search, transposition table, move ordering, limits, cancellation, diagnostics, and principal variation | `chess-core` |
| `chess-app` | library | Presentation-neutral human-facing game/session lifecycle, search worker/events, generation/ticket safety, text formatting, and atomic save primitives | `chess-core`, `chess-search` |
| `chess-uci` | binary | Standalone machine-facing Universal Chess Interface process adapter | `chess-book`, `chess-core`, `chess-search` |
| `chess-tui` | binary | Full-screen Ratatui/Crossterm frontend; owns menus, overlays, terminal lifecycle, responsive layout, and TUI-specific input/save UI | `chess-app`, `chess-core`, `chess-search` |
| `chess-console` | binary/library | Human-facing scrolling stdin/stdout frontend; owns command/menu parsing, input pump, confirmations, and console serialization | `chess-app`, `chess-core` |
| `chess-ffi` | library | Stable C ABI and opaque-handle boundary | `chess-book`, `chess-core`, `chess-search` |
| `chess-jni` | library | Android JNI adapters: existing low-level engine API over `chess-ffi` plus high-level interactive session API over `chess-app` | `chess-app`, `chess-core`, `chess-ffi` |
| `chess-tools` | binary | Perft, divide, fixtures, benchmarks, self-play, and tuning-candidate commands | `chess-core`, `chess-ffi`, `chess-search`, `chess-tune` |
| `chess-tune` | binary | Offline datasets, parameter tuning, and candidate validation | `chess-core`, `chess-search` |

## Dependency graph

```text
chess-core                                      (no workspace dependencies)
chess-book          -> chess-core
chess-search        -> chess-core
chess-app           -> chess-core, chess-search
chess-uci           -> chess-book, chess-core, chess-search
chess-tui           -> chess-app, chess-core, chess-search
chess-console       -> chess-app, chess-core
chess-ffi           -> chess-book, chess-core, chess-search
chess-jni           -> chess-app, chess-core, chess-ffi
chess-tools         -> chess-core, chess-ffi, chess-search, chess-tune
chess-tune          -> chess-core, chess-search
```

`chess-app` is not an engine layer. It is an application/session layer for interactive human-facing frontends. Rules remain authoritative in `chess-core`; evaluation/search/cancellation remain authoritative in `chess-search`.

`chess-uci` deliberately does not depend on `chess-app`: UCI is a machine-facing protocol adapter with its own protocol lifecycle. Conversely, neither `chess-tui`, `chess-console`, nor the Android application launches `chess-uci` as a subprocess.

## Human-facing frontend boundary

### Shared in `chess-app`

- `GameConfig`, `GameOutcome`, and `GameSession`;
- authoritative `Game` ownership for an interactive session;
- game generation and search request/ticket identity;
- pending/current search state and stale-result rejection;
- exact `SearchWorker` lifecycle, progress/completion/cancel/failure events, and worker joining;
- rejection of search fallback/emergency moves as interactive gameplay;
- Human-vs-Engine and Self-play lifecycle transitions;
- legal human-move resolution through `chess-core`;
- shared board/history/status/score/search-metric text formatting;
- same-directory atomic write/rename primitive.

### Remains in `chess-tui`

- Ratatui/Crossterm dependencies;
- full-screen layout and responsive sizing;
- menu/screen/overlay state;
- move-entry editing buffer;
- save-path and overwrite overlay state;
- raw-mode/alternate-screen terminal lifecycle;
- TUI-specific key handling and rendering.

### Remains in `chess-console`

- ordinary line-oriented stdin/stdout behavior;
- startup menu and configuration prompts;
- command grammar and case/whitespace normalization;
- state-free stdin reader thread and typed input events;
- confirmation prompts;
- console-specific deterministic non-PGN serialization;
- normal scrolling terminal output.

### Remains in Android/Kotlin presentation

- Android Activity/ViewModel lifecycle and Compose rendering;
- setup controls such as human color and requested depth;
- FEN-to-visible-piece projection for drawing the board;
- board orientation and tap-selection presentation state;
- promotion, restart, resign, and new-game dialogs;
- engine metric/history presentation;
- off-main-thread JNI calls and bounded polling while the Rust snapshot reports an active search.

The Android application does **not** own a second chess rule engine or independent interactive game controller. `ChessGame` snapshots provide authoritative FEN, legal moves, move history, turn state, outcome, and search metrics from the Rust `GameController`. Android derives selectable squares from the Rust legal-move list and submits the selected UCI move back to Rust.

## Android JNI boundary

`chess-jni` intentionally exposes two layers from the same `libchess_jni.so` artifact:

1. the established low-level `ChessEngine` API over `chess-ffi`, used by engine integrations and contract tests;
2. the high-level `ChessGame` API over `chess-app`, used by the playable Android application.

The high-level native session owns one `GameController` and at most one active `SearchWorker`. Kotlin polls typed worker events only while the returned snapshot reports `thinking=true`; exact completion is joined, revalidated, and applied in Rust before Kotlin receives the updated position.

Opaque Android game handles remain registered until explicit native close completes successfully. Kotlin clears its corresponding handle only after native destruction succeeds, keeping cleanup failures visible and retryable. A phantom-reference reaper is a last-resort leak backstop, not a substitute for explicit close.

## Search correctness boundary

Interactive frontends consume only an exact completed search result from `chess-app::SearchWorker`.

- A fallback/emergency search result is not a playable move.
- Missing exact iteration metadata is a failure.
- Missing exact best move is a failure.
- Cancellation is distinct from failure and completion.
- Returned engine moves are revalidated against the current legal move set before application.
- Generation/request tickets prevent stale completions from mutating restarted or abandoned games.
- No frontend silently retries at a lower depth or selects a random/first legal replacement move.

## Input/shutdown boundary

The console keeps `GameController` on one application thread. Its background stdin reader sends typed input events only; it owns no game/search state or cleanup-sensitive engine resources. On EOF it terminates and is joinable. On explicit interactive quit, an OS-blocked stdin read may remain process-lifetime; this is documented rather than falsely reported as joined.

The Android high-level JNI owner serializes operations for a game handle, and Kotlin presentation performs JNI operations off the Android main thread. Restart, resignation, and close resolve any active native search worker before the operation is reported successful.

Engine workers are different from process-lifetime input plumbing: at most one frontend-owned search worker is active, and destructive/shutdown paths cancel and join it explicitly. Search workers are never intentionally detached.

## Enforced boundaries

- `chess-core` has no workspace dependencies.
- `chess-book` and `chess-search` depend only on `chess-core` among workspace crates.
- `chess-app` depends only on engine-layer crates actually needed for interactive application behavior.
- `chess-app` must not acquire Ratatui, Crossterm, UCI, FFI, JNI, Android, Python, tuning, or implicit configuration dependencies.
- `chess-jni` may adapt both the stable low-level engine boundary and the shared `chess-app` interactive boundary, but Android/Kotlin dependencies must never flow inward into `chess-app`, `chess-core`, or `chess-search`.
- `chess-core`, `chess-book`, `chess-search`, `chess-app`, `chess-uci`, `chess-tui`, `chess-console`, `chess-tools`, and `chess-tune` forbid unsafe code (`#![forbid(unsafe_code)]`). Only `chess-ffi` and `chess-jni` own narrowly scoped necessary unsafe boundary code.
- Core/search crates do not read files, print, own UI state, use Android APIs, or terminate processes.
- Optional files cannot silently change engine behavior. Books, weights, datasets, configuration, and frontend save destinations must be explicit.
- Python is not a production/runtime dependency of the Rust engine or human-facing Rust/Android frontends.

## Lint policy

Workspace Rust warnings and the Clippy `all` group are denied. CI additionally passes `-D warnings`. First-party findings must be fixed at their source; lint suppression is not an accepted repair strategy.

## Version and publication policy

The workspace declares Rust 1.75 as its minimum supported Rust version and uses Rust 2021 edition. Workspace packages use the repository's shared license/publication metadata. New dependencies must remain compatible with the supported MSRV or receive an explicit policy change.
