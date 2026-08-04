# Rust developer workflows

The Rust workspace is the actively developed engine. The Python implementation remains historical reference material only: Python CI and Python feature development are intentionally retired after migration signoff.

All repository-supported local commands go through one dispatcher:

```bash
bash scripts/dev.sh help
```

The dispatcher uses the committed lockfiles and explicit input/output paths. It does not discover opening books, datasets, checkpoints, or weight artifacts from conventional locations.

## Bootstrap

Prerequisites:

- Linux x86-64 or ARM64;
- `rustup` and Cargo;
- Python 3 with `venv` support for the pinned `python-chess` differential oracle;
- Java 17, Gradle 8.9, and an Android NDK only for the Android command.

Run once after cloning or after dependency/toolchain changes:

```bash
bash scripts/dev.sh bootstrap
```

This installs the required Rust components and targets, fetches the locked Cargo dependencies, and creates `.venv-oracle` from `requirements/oracle.txt`. The generated virtual environment is ignored and must not be committed.

## Validation

Fast validation:

```bash
bash scripts/dev.sh fast
```

It runs the generated-artifact audit, script unit tests, shell syntax checks, rustfmt, locked all-target/all-feature check, strict Clippy, and the complete Rust workspace test suite.

Full local validation:

```bash
bash scripts/dev.sh full
```

It includes the fast gate plus release depth-four perft, warning-free rustdoc, debug/release workspace builds, and the pinned differential corpus/seeded-playout oracle. Run bootstrap first so `.venv-oracle` exists.

The slow depth-five perft, bounded fuzz campaigns, Miri, sanitizers, dual-architecture performance measurements, Android API-35 instrumentation, and 400-game strength control remain independent CI workflows because they require specialized runners or extended execution.

## Perft

```bash
bash scripts/dev.sh perft       # authoritative suite through depth 4
bash scripts/dev.sh perft 5     # full depth-five suite
```

For one position or divide output, use the underlying explicit tooling:

```bash
cargo run --locked --release -p chess-tools -- perft 4 '<six-field FEN>'
cargo run --locked --release -p chess-tools -- divide 4 '<six-field FEN>'
```

## UCI

Run the Linux UCI process on stdin/stdout:

```bash
bash scripts/dev.sh uci
```

Supply an opening book only through the explicit adapter argument:

```bash
bash scripts/dev.sh uci --book /absolute/path/opening-book-v1.bin
```

A smoke transcript can be sent without a GUI:

```bash
printf 'uci\nisready\nposition startpos\ngo depth 3\nquit\n' | bash scripts/dev.sh uci
```

See `docs/RUST_UCI_PROCESS_INTEGRATION.md` and `docs/RUST_OPENING_BOOK_ADAPTER_INTEGRATION.md` for protocol and ownership details.

## Android/JNI

Set the NDK explicitly, then build both JNI ABIs, lint/build the Android harness, build its test APK, and run the host-JVM JNI contract:

```bash
export ANDROID_NDK_HOME="$HOME/Android/Sdk/ndk/<version>"
export ANDROID_API_LEVEL=24
bash scripts/dev.sh android
```

The local command does not start an emulator. Permanent CI additionally runs API-35 instrumentation and lifecycle/performance assertions. See `docs/RUST_ANDROID_JNI.md` and `docs/RUST_ANDROID_TEST_HARNESS.md`.

## Offline self-play

```bash
mkdir -p self-play-output
bash scripts/dev.sh self-play \
  fixtures/self_play_config.example \
  self-play-output/dataset.txt
```

Every path is explicit. The output is generated evidence and is ignored by default. Promote a dataset into `fixtures/` only through an intentional review that records its schema, provenance, and purpose.

## Offline tuning

Create a real configuration from `fixtures/tuning_config.example`. Replace the source commit, timestamp, and candidate identifiers with exact values for the run.

```bash
bash scripts/dev.sh tune \
  /path/to/tuning-config.txt \
  /path/to/self-play-dataset.txt \
  tuning-output/candidate-001
```

Resume from a previous complete output directory into a new output directory:

```bash
bash scripts/dev.sh tune \
  /path/to/tuning-config.txt \
  /path/to/self-play-dataset.txt \
  tuning-output/candidate-002 \
  tuning-output/candidate-001
```

A successful output directory contains:

- `tuning-config.txt` — exact configuration required for strict resume;
- `checkpoint.bin` — strict checksummed resume state;
- `tuning-report.txt` — complete versioned provenance, losses, configuration, and all 810 deltas;
- `candidate-weights.txt` — versioned named candidate artifact;
- `summary.tsv` — concise numerical result;
- `ACTIVATION_DISABLED` — explicit proof that the run did not change runtime defaults.

The command refuses an existing output directory, publishes through a sibling staging directory, and deletes incomplete staging output on failure. Candidate activation remains the independent Task 21 process.

## Fuzzing

Stable parser/corpus regressions:

```bash
bash scripts/dev.sh fuzz-smoke
```

Bounded libFuzzer, Miri, and sanitizer commands are documented in `docs/RUST_FUZZING.md` and run permanently in `.github/workflows/robustness.yml`.

## CI matrix

Permanent independent workflows are:

- `CI`: x86-64 quality/release/perft/oracle plus native ARM64 workspace builds;
- `Android JNI`: lint, host JVM, dual JNI ABIs, APKs, and API-35 instrumentation;
- `Robustness`: fuzz, Miri, ASan/LSan, and TSan;
- `Performance`: x86-64/ARM64 budgets and scheduled Callgrind;
- `Slow perft`: scheduled/manual depth-five fixtures;
- `Strength`: scheduled/manual 200-pair/400-game baseline control.

`report-master-validation.yml` reports completed exact-`master` runs to the repository validation issue. No workflow combines a performance, strength, or robustness result with correctness in a way that can hide a failure.
