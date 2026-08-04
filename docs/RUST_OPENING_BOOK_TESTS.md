# Rust opening-book verification gate

Task 19.5 consolidates the public behavioral and architecture guarantees established by Tasks 19.1–19.4.

## Public behavior regressions

`crates/chess-book/tests/task_19_5.rs` exercises only exported `chess-book` and `chess-core` APIs. It proves:

- a syntax-valid but position-illegal indexed move is rejected as a typed legality error;
- equal highest weights are resolved by ascending canonical UCI text;
- two weighted selectors initialized with the same explicit local seed produce the same selection sequence;
- unsupported format versions and checksum-corrupt payloads remain distinct typed errors.

The tests construct all book data in memory. They do not depend on a filesystem, environment variable, clock, process-global RNG, Android runtime, or network service.

## Permanent no-auto-discovery audit

`scripts/task_19_5_opening_book_audit.py` is a fail-closed permanent CI check. It verifies:

- `chess-book` depends only on `chess-core` and contains no filesystem, path, environment, network, process, or embedded-asset loading code;
- `chess-core` and `chess-search` do not depend on the outward `chess-book` crate;
- the safe facade and Rust JNI/C ABI adapters contain no file or environment discovery;
- the UCI process reads a book only from one explicitly supplied `--book <path>` argument;
- Kotlin accepts explicitly supplied indexed bytes;
- the Android example opens an explicitly selected `AssetManager` asset and passes its bytes to Kotlin.

The audit is part of `.github/workflows/ci.yml`, so future implicit loading, default-path lookup, environment-variable lookup, embedded Rust book data, or inward dependency inversion fails the standard Rust quality gate.

## Required validation

Task 19.5 and the overall Task 19 gate may close only after an exact commit passes:

```bash
python3 scripts/task_19_5_opening_book_audit.py
cargo fmt --all -- --check
cargo check --locked --workspace --all-targets --all-features
cargo clippy --locked --workspace --all-targets --all-features -- -D warnings
cargo test --locked --workspace --all-features
cargo test --locked -p chess-core --release authoritative_perft_depth_four -- --ignored --exact
RUSTDOCFLAGS="-D warnings" cargo doc --locked --workspace --all-features --no-deps
cargo build --locked --workspace --all-features
cargo build --locked --workspace --all-features --release
```

The existing differential-oracle, host JVM JNI, dual-ABI Android build, APK build, and API-35 instrumentation gates must also remain green.

## Validated implementation evidence

- Exact validated implementation head: `439c77e8a2ba2f98cbefd4f260823eb951fe1262`.
- Permanent Rust validation: run `30866788532`, job `91860310659`.
- Permanent Android validation: run `30866788525`, host JVM job `91860355455`, API-35 emulator job `91860355472`.
- The workspace executed 332 non-documentation Rust tests with zero failures, including the four dedicated Task 19.5 public-API regressions.
- The permanent no-auto-discovery audit passed and verified pure `chess-book`/core/search dependency direction plus explicit UCI path, safe byte, JNI byte, and Android asset injection.
- Committed lockfile verification, workspace metadata, rustfmt, all-target/all-feature compilation, strict Clippy with warnings denied, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and the independent differential oracle passed.
- Differential validation covered 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Host JVM JNI passed, ARM64/x86_64 native artifacts and exported symbols were verified, the Android AAR/test APK built, and the API-35 instrumentation lifecycle passed.
- The first validation correction applied canonical rustfmt output; the second used canonical hexadecimal digit grouping required by strict Clippy. No production behavior, test requirement, audit rule, or gate was weakened.

Task 19.5 behavior and architecture are validated. The implementation merged at `d7d8455e6279fab53451bad6a5d778ce66c0a001`; the exact evidence-bearing head `5d70737bf12cbfa16441730b7a64629212b28683` passed the permanent Rust and Android workflows. Task 19 and its overall gate are complete; Task 20 offline self-play is next.
