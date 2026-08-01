# Rust Chess Engine Port Ralph Loop Status

**Updated:** 2026-08-01  
**Branch:** `rust-engine`  
**Authoritative TODO:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  
**Current phase:** Task 0 and Task 1 execution evidence pending  
**Latest repository snapshot before this status update:** `75d6316a4e19eb3012c20ae22894aef90b678cfc`

---

## Operating rules

- Work directly on `rust-engine`.
- Do not create branches or pull requests without explicit user instruction.
- Every first-party compiler, Clippy, rustdoc, formatting, lint, and test finding is a bug.
- Fix first-party findings at their source; do not hide, suppress, downgrade, ignore, or filter them.
- Third-party, dependency, generated-vendor, and vendored-code warnings are outside the first-party rule unless caused by this repository's integration code.
- Keep the authoritative TODO synchronized with repository reality.
- Do not claim a gate from another SHA or from unexecuted commands.

---

## Task 0 status

**In progress.** The following source-grounded work is complete:

- frozen Python baseline SHA: `f743013a84173b551eac5488c638cb48098ec6d0`;
- Python module inventory and retained/excluded concept mapping;
- fourteen known Python defect/non-copy constraints;
- fail-loud baseline capture script:
  - `scripts/capture-rust-port-python-baseline.sh`;
- unified Task 0/1 gate:
  - `scripts/validate-rust-port-task0-task1.sh`.

Still required:

- fresh fast Python suite;
- fresh slow Python suite;
- timed starting-position perft depths 1–4;
- UCI smoke transcript;
- reviewed and committed evidence.

---

## Task 1 status

**Implemented but unverified.** Repository implementation includes:

- seven-crate Cargo workspace;
- documented dependency direction;
- Rust 2021 and MSRV 1.75;
- stable rustfmt and Clippy components;
- denied first-party warnings;
- `#![forbid(unsafe_code)]` in `chess-core` and `chess-search`;
- Linux formatting, check, Clippy, test, docs, debug-build, and release-build CI steps;
- MIT license and shared `license = "MIT"` metadata;
- one-command local Task 0/1 validation with exact-SHA evidence.

Static source and manifest review found no obvious first-party defect. Dynamic execution is still required for:

```bash
cargo generate-lockfile
cargo metadata --locked --format-version 1 --no-deps
cargo fmt --all -- --check
cargo check --locked --workspace --all-targets --all-features
cargo clippy --locked --workspace --all-targets --all-features -- -D warnings
cargo test --locked --workspace --all-features
RUSTDOCFLAGS="-Dwarnings" cargo doc --locked --workspace --all-features --no-deps
cargo build --locked --workspace --all-features
cargo build --locked --workspace --all-features --release
```

Task 1 remains open until `Cargo.lock` and local evidence are reviewed and committed and CI issue `#1` reports the exact passing candidate SHA.

---

## Environment limitation

The current assistant execution environment has no Rust toolchain, no GitHub CLI, and no outbound package-download path. The connected GitHub interface can read/write repository content and inspect or rerun existing Actions jobs, but it cannot dispatch a new workflow. Connector-authored commits have not generated a new applicable CI status; issue `#1` still reports the obsolete Python run at SHA `2370607ff54596cd25ec3201f22f7a375baec67b`.

No runtime result has been inferred or fabricated.

---

## Next exact operation

From a clean local checkout:

```bash
git switch rust-engine
git pull --ff-only
bash scripts/validate-rust-port-task0-task1.sh
```

The script defaults to the required slow Python capture and then runs every Rust gate. It records results under:

```text
artifacts/rust-port-python-baseline/<candidate-sha>/
artifacts/rust-port-task0-task1/<candidate-sha>/
```

After a green run:

1. review every log and `Cargo.lock`;
2. commit `Cargo.lock`, evidence, and TODO updates directly to `rust-engine`;
3. manually run workflow `CI` for branch `rust-engine`;
4. verify issue `#1` reports the exact candidate SHA and `success`;
5. close Task 0 and Task 1 in the authoritative TODO;
6. begin Task 2.
