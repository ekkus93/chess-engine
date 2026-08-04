# Rust differential fuzzing and robustness commands

The fuzz workspace is separate from the production Cargo workspace and has its own committed `fuzz/Cargo.lock`. Corpus inputs and minimized regressions are versioned intentionally; transient engine output and local fuzz build products are not.

## Stable smoke gate

```bash
bash scripts/dev.sh fuzz-smoke
```

This checks formatting and strict Clippy for the fuzz workspace, then runs the stable entrypoint tests and every committed corpus/regression replay. It requires only stable Rust.

## Bounded libFuzzer campaigns

Install the pinned runner and a current nightly:

```bash
cargo +stable install cargo-fuzz --locked --version 0.13.2
rustup toolchain install nightly
```

Run the same bounded targets as permanent CI:

```bash
targets=(
  fen_parser
  uci_move_parser
  legal_sequence
  game_history
  weight_parser
  opening_book_parser
  c_abi_buffers_handles
)
for target in "${targets[@]}"; do
  RUSTFLAGS=-Adeprecated cargo +nightly fuzz run --features fuzzing \
    "${target}" "fuzz/corpus/${target}" -- \
    -runs=256 -max_len=4096 -timeout=10
done
```

A new crash must be minimized, reproduced, converted into a named permanent regression where possible, and accompanied by a production fix. Never delete a corpus input merely to restore a green run.

## Miri

```bash
rustup toolchain install nightly-2026-08-01 --component miri,rust-src
cargo +nightly-2026-08-01 miri setup
MIRIFLAGS=-Zmiri-strict-provenance \
  cargo +nightly-2026-08-01 miri test --locked \
  -p chess-core --test miri_core
```

## Sanitizers

ASan/LSan lifecycle gate:

```bash
RUSTFLAGS='-Zsanitizer=address -Adeprecated' \
RUSTDOCFLAGS='-Zsanitizer=address -Adeprecated' \
ASAN_OPTIONS='detect_leaks=1:halt_on_error=1:abort_on_error=1' \
  cargo +nightly-2026-08-01 test -Zbuild-std --locked \
  --target x86_64-unknown-linux-gnu \
  -p chess-ffi --test c_abi_lifecycle --all-features
```

TSan cancellation gate:

```bash
RUSTFLAGS='-Zsanitizer=thread -Adeprecated' \
RUSTDOCFLAGS='-Zsanitizer=thread -Adeprecated' \
TSAN_OPTIONS='halt_on_error=1:abort_on_error=1' \
  cargo +nightly-2026-08-01 test -Zbuild-std --locked \
  --target x86_64-unknown-linux-gnu \
  -p chess-ffi --test c_abi_lifecycle --all-features \
  active_infinite_search_cancels_from_another_thread -- --exact
```

Rust nightly does not expose a general UBSan mode for this workspace; Miri is the undefined-behavior gate. The permanent workflow fails if that documented support boundary becomes stale.
