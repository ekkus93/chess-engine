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

## Completion evidence

- Exact merged implementation SHA: `5b8e2117c64922e97cbe356caa44a51075da7b52`.
- Exact validated implementation head before rebase merge: `d7f70e21fea900171ef5539f6ee9ee4b00c34d18`.
- Permanent Rust validation: run `30863525297`, job `91850371126`.
- Permanent Android validation: run `30863525289`, host JVM job `91850370864`, API-35 emulator job `91850370917`.
- The workspace executed 328 non-documentation Rust tests with zero failures, including focused safe-facade, additive C ABI, JNI declaration, UCI option, book-hit, disabled-book, absent-book, no-entry, and corrupt-book coverage.
- Committed lockfile verification, workspace metadata, rustfmt, all-target/all-feature compilation, strict Clippy with warnings denied, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and the independent differential oracle passed.
- Differential validation covered 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Host JVM JNI passed, ARM64/x86_64 native artifacts and exported symbols were verified, the Android AAR/test APK built, and the API-35 instrumentation lifecycle—including the packaged indexed-book asset example—passed.
- Task 19.4 is complete. Task 19.5 and the overall Task 19 gate remain open.
