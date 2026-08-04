# Rust Workspace Architecture

**Status:** Initial Task 1 architecture  
**Branch:** `master`  
**Minimum supported Rust version:** 1.75  
**Toolchain policy:** stable Rust with `rustfmt` and Clippy

## Purpose

The workspace isolates portable chess logic from protocols, operating-system adapters, and offline tooling. Dependencies point outward from the core. No adapter may become a dependency of a lower-level crate.

## Crates

| Crate | Type | Responsibility | Allowed direct workspace dependencies |
|---|---|---|---|
| `chess-core` | library | Position model, moves, attacks, rules, FEN, make/unmake, hashing, and game-rule primitives | none |
| `chess-search` | library | Evaluation, search, transposition table, move ordering, limits, diagnostics, and principal variation | `chess-core` |
| `chess-uci` | binary | Standalone Universal Chess Interface process adapter | `chess-search` |
| `chess-ffi` | library | Stable C ABI and opaque-handle boundary | `chess-search` |
| `chess-jni` | library | Android JNI adapter over the C/safe engine boundary | `chess-ffi` |
| `chess-tools` | binary | Perft, divide, fixtures, benchmarks, and self-play commands | `chess-core`, `chess-search` |
| `chess-tune` | binary | Offline datasets, parameter tuning, and candidate validation | `chess-core`, `chess-search` |

## Dependency graph

```text
chess-core
    ^
    |
chess-search
    ^       ^        ^
    |       |        |
chess-uci chess-ffi chess-tools
              ^       ^
              |       |
          chess-jni chess-tune
```

`chess-tools` and `chess-tune` also depend directly on `chess-core` for rule-level operations that do not require a search engine.

## Enforced boundaries

- `chess-core` has no workspace dependencies.
- `chess-search` depends only on `chess-core` among workspace crates.
- `chess-uci`, `chess-ffi`, `chess-jni`, `chess-tools`, and `chess-tune` are outward adapters or tools.
- `chess-core` and `chess-search` forbid unsafe code.
- FFI/JNI unsafe code is not present in the initial skeleton. Future unsafe blocks must be narrowly scoped, documented, and tested; warnings may not be suppressed.
- Core/search crates do not read files, print, own UI state, use Android APIs, or terminate processes.
- Optional files cannot silently change engine behavior. Books, weights, and configuration must be injected explicitly.

## Lint policy

Workspace Rust warnings and the Clippy `all` group are denied. The CI command additionally passes `-D warnings`. First-party findings must be fixed at their source; `allow` attributes and warning filters are not an accepted repair strategy.

Third-party or vendored warnings are not first-party defects unless this repository's integration code causes them. Vendor sources must not be modified merely to make this workspace appear warning-free.

## Version and publication policy

The workspace declares Rust 1.75 as its minimum supported Rust version and uses Rust 2021 edition. CI uses the current stable toolchain. A dedicated MSRV job can be added when the first nontrivial implementation lands.

All initial crates are `publish = false`. The repository currently has no top-level license file, so no package license is asserted. Selecting and adding a project license is an explicit owner decision and remains a Task 1 completion item; it must not be guessed by an implementation agent.

## Initial skeleton contract

The initial crates intentionally contain no chess behavior. They establish package names, dependency direction, crate documentation, safe-code boundaries, and CI entry points. Behavioral APIs and tests begin in Task 2.
