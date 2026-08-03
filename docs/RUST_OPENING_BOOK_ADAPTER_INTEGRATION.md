# Rust opening-book adapter integration

Task 19.4 connects the validated Task 19.3 book policy to explicit adapter boundaries.

All book bytes, paths, assets, enablement decisions, and RNG seeds remain caller- or adapter-owned. Neither `chess-core` nor `chess-search` discovers, loads, or depends on opening-book data.

## Safe Rust facade

`EngineConfig` keeps opening books disabled by default and selects deterministic highest-weight policy unless a caller explicitly chooses a seeded weighted policy. `Engine::new` owns no book and operates normally. Callers may inject a validated `IndexedBook` or complete indexed-format bytes, then query `opening_book_move()` before normal search. Disabled configuration, absent data, and a valid book without a current-position record return `Ok(None)`. Corrupt data and legality/policy errors remain typed.

## UCI adapter

The binary advertises `OwnBook`, default `false`. A backend exists only when the process is launched with `--book <path>`; no current-directory, environment, or default-path discovery occurs. When `OwnBook` is true, a legal hit emits `bestmove` immediately. No configured file, disabled `OwnBook`, or no position entry continues through the unchanged worker search. Load and selection failures are fail visible.

## C ABI, JNI, and Android asset example

The ABI adds construction from explicit indexed bytes and a selected-book-move query without changing the version-1 config record. JNI and Kotlin expose `createWithIndexedBook` and `openingBookMove`. The Android harness demonstrates reading `opening-book-v1.bin` from `AssetManager` and supplying those bytes explicitly; the shared host-JVM wrapper has no Android dependency.

## Deferred Task 19.5

Task 19.5 retains broader malformed-book, legality, deterministic-seed, no-entry, disabled-book, and platform regression coverage plus the overall Task 19 completion gate.
