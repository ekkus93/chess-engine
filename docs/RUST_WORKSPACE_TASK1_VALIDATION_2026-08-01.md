# Rust Workspace Task 1 Validation

**Date:** 2026-08-01  
**Branch:** `rust-engine`  
**Workspace snapshot before this report:** `ddb54105aff8ad54c40db436872fceec968bfa06`  
**Task:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md` Task 1

---

## Result

The Task 1 workspace skeleton is implemented but the Task 1 gate is **not closed**.

Static structure and policy checks passed. Rust compilation, formatting, Clippy, tests, and rustdoc have not been executed in the current environment because no Rust toolchain is installed and outbound DNS is unavailable. Connector-authored commits did not start GitHub Actions.

No unexecuted command is represented as passing.

---

## Implemented workspace

The root workspace contains exactly these members:

```text
crates/chess-core
crates/chess-search
crates/chess-uci
crates/chess-ffi
crates/chess-jni
crates/chess-tools
crates/chess-tune
```

The workspace declares:

- resolver version 2;
- Rust 2021 edition;
- minimum supported Rust version 1.75;
- `publish = false` for every package;
- stable Rust with `rustfmt` and Clippy components;
- Rust warnings denied;
- `unsafe_op_in_unsafe_fn` denied;
- the Clippy `all` group denied;
- no lint `allow` attributes in the new Rust sources.

`chess-core` and `chess-search` explicitly use:

```rust
#![forbid(unsafe_code)]
```

---

## Dependency contract

The staged manifests were parsed with Python's standard-library `tomllib`. The following exact direct dependency sets were asserted:

| Package | Direct workspace dependencies |
|---|---|
| `chess-core` | none |
| `chess-search` | `chess-core` |
| `chess-uci` | `chess-search` |
| `chess-ffi` | `chess-search` |
| `chess-jni` | `chess-ffi` |
| `chess-tools` | `chess-core`, `chess-search` |
| `chess-tune` | `chess-core`, `chess-search` |

The static validation also asserted:

- seven unique workspace members exist;
- every member has a parseable `Cargo.toml`;
- every package inherits workspace lint policy;
- `chess-core` has no workspace dependency;
- `chess-search` depends only on `chess-core`;
- no new Rust file contains `#[allow(...)]` or `#![allow(...)]`;
- `chess-core` and `chess-search` forbid unsafe code.

Static validation result:

```text
wrote 25 staged files
static Task 1 validation passed
```

Only 18 of the staged files were required in the repository because crate-level rustdoc in each `src` entry point and the central architecture document satisfy the documentation requirement without duplicating per-crate README files.

---

## Repository diff audit

Comparing the Task 1 starting point `fcbb5930306e9957c9bdbed45aa3ea6f9b9a6c04` to snapshot `ddb54105aff8ad54c40db436872fceec968bfa06` produced exactly 19 changed paths:

- `.gitignore`;
- root `Cargo.toml`;
- seven crate manifests;
- seven crate source entry points;
- `docs/RUST_WORKSPACE_ARCHITECTURE.md`;
- `rust-toolchain.toml`;
- `rustfmt.toml`.

No file under `chess_game/` or `tests/` changed.

---

## First-party warning policy

The workspace does not use lint suppression as a substitute for repair.

For first-party Rust code:

- every compiler warning is a defect;
- every enabled Clippy warning is a defect;
- every rustdoc warning is a defect;
- every formatting failure is a defect;
- warnings must be corrected at their source;
- blanket or convenience `allow` attributes are prohibited unless the user explicitly approves a narrowly justified language/tool limitation.

Warnings originating solely in third-party, dependency, generated-vendor, or vendored source are not first-party defects. Integration code in this repository remains subject to the strict policy.

---

## License status

The repository has no top-level license file. The implementation therefore does not guess or assert a license. Every crate is marked `publish = false`.

Task 1's license/package-metadata checkbox remains open until the owner selects a license or explicitly records that the project is proprietary/unlicensed. Other package metadata is consistent across the workspace.

---

## Required dynamic validation

Run these commands from a clean `rust-engine` checkout with the stable Rust toolchain installed:

```bash
cargo fmt --all -- --check
cargo check --workspace --all-targets --all-features
cargo clippy --workspace --all-targets --all-features -- -D warnings
cargo test --workspace --all-features
RUSTDOCFLAGS="-D warnings" cargo doc --workspace --all-features --no-deps
cargo build --workspace --all-features
cargo build --workspace --all-features --release
```

Acceptance rules:

- every command must exit 0;
- no first-party warning may be filtered or suppressed;
- any first-party warning is fixed and the entire sequence rerun;
- generated `Cargo.lock` must be reviewed and committed if Cargo creates it;
- the exact passing commit SHA must be recorded;
- issue `#1` must report the same exact SHA before CI evidence is accepted.

---

## Gate decision

Task 1 remains **implemented but unverified**.

It may not be marked complete until:

1. Task 0's required Python baseline runtime evidence is recorded or explicitly dispositioned;
2. the dynamic Rust command sequence passes at one exact commit;
3. the license decision is recorded;
4. the authoritative TODO is updated with the evidence and completion note.
