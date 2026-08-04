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

The existing differential-oracle, host JVM JNI, dual-ABI Android build, APK build, and API-35 instrumentation gates must also remain green. Exact completion evidence is recorded only after those permanent workflows finish successfully.
