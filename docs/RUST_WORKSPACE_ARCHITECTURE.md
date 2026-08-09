# Rust Workspace Architecture

**Status:** authoritative current workspace architecture  
**Branch:** `master`  
**Minimum supported Rust version:** 1.75  
**Toolchain policy:** stable Rust with `rustfmt` and Clippy

## Purpose

The workspace isolates portable chess logic from protocol, presentation, platform, and offline-tooling layers. Dependencies point outward from the core. No frontend or adapter may become a dependency of a lower-level engine crate.

The human-facing applications share presentation-neutral lifecycle/search behavior through `chess-app`; the full-screen TUI and scrolling console remain separate frontends.

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
| `chess-jni` | library | Android JNI adapter over the C/safe engine boundary | `chess-ffi` |
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
chess-jni           -> chess-ffi
chess-tools         -> chess-core, chess-ffi, chess-search, chess-tune
chess-tune          -> chess-core, chess-search
```

`chess-app` is not an engine layer. It is an application/session layer for interactive human-facing frontends. Rules remain authoritative in `chess-core`; evaluation/search/cancellation remain authoritative in `chess-search`.

`chess-uci` deliberately does not depend on `chess-app`: UCI is a machine-facing protocol adapter with its own protocol lifecycle. Conversely, neither `chess-tui` nor `chess-console` launches `chess-uci` as a subprocess.

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

Engine workers are different: at most one frontend-owned search worker is active, and destructive/EOF shutdown paths cancel and join it explicitly. Search workers are never intentionally detached.

## Enforced boundaries

- `chess-core` has no workspace dependencies.
- `chess-book` and `chess-search` depend only on `chess-core` among workspace crates.
- `chess-app` depends only on engine-layer crates actually needed for interactive application behavior.
- `chess-app` must not acquire Ratatui, Crossterm, UCI, FFI, JNI, Android, Python, tuning, or implicit configuration dependencies.
- `chess-core`, `chess-book`, `chess-search`, `chess-app`, `chess-uci`, `chess-tui`, `chess-console`, `chess-tools`, and `chess-tune` forbid unsafe code (`#![forbid(unsafe_code)]`). Only `chess-ffi` and `chess-jni` own narrowly scoped necessary unsafe boundary code.
- Core/search crates do not read files, print, own UI state, use Android APIs, or terminate processes.
- Optional files cannot silently change engine behavior. Books, weights, datasets, configuration, and frontend save destinations must be explicit.
- Python is not a production/runtime dependency of the Rust engine or either human-facing Rust frontend.

## Lint policy

Workspace Rust warnings and the Clippy `all` group are denied. CI additionally passes `-D warnings`. First-party findings must be fixed at their source; lint suppression is not an accepted repair strategy.

## Version and publication policy

The workspace declares Rust 1.75 as its minimum supported Rust version and uses Rust 2021 edition. Workspace packages use the repository's shared license/publication metadata. New dependencies must remain compatible with the supported MSRV or receive an explicit policy change.
