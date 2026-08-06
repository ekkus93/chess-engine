# Chess Engine

[![CI](https://github.com/ekkus93/chess-engine/actions/workflows/ci.yml/badge.svg?branch=master)](https://github.com/ekkus93/chess-engine/actions/workflows/ci.yml)
[![Android JNI](https://github.com/ekkus93/chess-engine/actions/workflows/android.yml/badge.svg?branch=master)](https://github.com/ekkus93/chess-engine/actions/workflows/android.yml)
[![Robustness](https://github.com/ekkus93/chess-engine/actions/workflows/robustness.yml/badge.svg?branch=master)](https://github.com/ekkus93/chess-engine/actions/workflows/robustness.yml)
[![Performance](https://github.com/ekkus93/chess-engine/actions/workflows/performance.yml/badge.svg?branch=master)](https://github.com/ekkus93/chess-engine/actions/workflows/performance.yml)
[![Variant validation](https://github.com/ekkus93/chess-engine/actions/workflows/variant-validation.yml/badge.svg?branch=master)](https://github.com/ekkus93/chess-engine/actions/workflows/variant-validation.yml)

A correctness-first Rust chess engine with a Linux UCI executable, portable engine/search crates, C and JNI adapters, Android integration, explicit opening-book support, offline self-play and tuning infrastructure, and permanent perft, differential, robustness, performance, and strength gates.

**Authoritative implementation:** the Rust workspace on `master`. New integrations should use the safe Rust facade, UCI executable, C ABI, or JNI boundary. The full migration, traceability, versions, evidence, and roadmap are recorded in [`docs/RUST_CHESS_ENGINE_PORT_IMPLEMENTATION_REPORT.md`](docs/RUST_CHESS_ENGINE_PORT_IMPLEMENTATION_REPORT.md).

The former Python implementation remains in the repository as historical reference material. Python development and Python engine CI are intentionally retired after migration signoff. Python remains permitted for the pinned independent `python-chess` differential oracle and repository validation tooling; production Rust crates do not embed or launch Python.

The built-in baseline evaluation weights remain authoritative. The production candidate-validation control completed 200 color-balanced opening pairs and 400 games but was rejected for insufficient strength, so it was never activated. Any future weight promotion must pass the unchanged fail-closed protocol and be applied by a separate explicit source change.

## Start here

```bash
git clone https://github.com/ekkus93/chess-engine.git
cd chess-engine
bash scripts/dev.sh bootstrap
bash scripts/dev.sh fast
```

All supported developer entry points are listed by:

```bash
bash scripts/dev.sh help
```

The full workflow, prerequisites, output ownership, and CI mapping are documented in [`docs/RUST_DEVELOPER_WORKFLOWS.md`](docs/RUST_DEVELOPER_WORKFLOWS.md).

## Common commands

```bash
# Fast Rust validation
bash scripts/dev.sh fast

# Complete local Rust validation
bash scripts/dev.sh full

# Authoritative perft suite through depth 4
bash scripts/dev.sh perft

# Linux UCI engine on stdin/stdout
bash scripts/dev.sh uci

# Build JNI libraries and Android harness
export ANDROID_NDK_HOME="$HOME/Android/Sdk/ndk/<version>"
bash scripts/dev.sh android

# Consolidated v0.2 authority audit
bash scripts/dev.sh strength-audit

# Stable fuzz corpus/regression replay
bash scripts/dev.sh fuzz-smoke
```

Offline self-play and tuning always use explicit paths:

```bash
mkdir -p self-play-output
bash scripts/dev.sh self-play \
  fixtures/self_play_config.example \
  self-play-output/dataset.txt

bash scripts/dev.sh tune \
  /path/to/tuning-config.txt \
  self-play-output/dataset.txt \
  tuning-output/candidate-001
```

A tuning run emits an inactive candidate and cannot change runtime defaults. Candidate validation and activation remain separate fail-closed processes.

## Workspace

- `crates/chess-core` — position representation, rules, legal generation, FEN, hashing, history, and exact perft.
- `crates/chess-search` — evaluation, transposition table, iterative deepening, limits, cancellation, and search.
- `crates/chess-book` — explicit opening-book abstraction and indexed format.
- `crates/chess-uci` — Linux UCI process adapter.
- `crates/chess-ffi` — safe facade and versioned C ABI.
- `crates/chess-jni` — JNI adapter.
- `crates/chess-tools` — perft, oracle, benchmarks, self-play, tuning orchestration, and candidate evidence.
- `crates/chess-tune` — loss, named weight schemas, SPSA, checkpoints, and artifacts.
- `android-harness` — Kotlin/JVM and API-35 integration tests.
- `fuzz` — separate fuzz workspace with committed corpora and minimized regressions.
- `fixtures` — versioned schemas and authoritative inputs.
- `benchmarks/task24` — accepted reference performance distributions.

Dependency direction and crate ownership are documented in [`docs/RUST_WORKSPACE_ARCHITECTURE.md`](docs/RUST_WORKSPACE_ARCHITECTURE.md).

## Design contracts

Core contracts include:

- canonical square mapping: `a8 = 0`, `h8 = 7`, `a1 = 56`, `h1 = 63`;
- one packed internal move identity, without exposing its bit layout as a stable ABI;
- strict six-field FEN and explicit promotion identity;
- private redundant position state with invariant checks;
- make/unmake recursive search rather than clone-per-child;
- incremental hash and repetition identity that normalize en-passant correctly;
- bounded transposition storage and normalized mate scores;
- no implicit filesystem discovery for weights, opening books, datasets, or configuration;
- no panic crossing C or JNI boundaries;
- correctness gates independent from strength and performance gates.

The authoritative port specification is [`docs/RUST_CHESS_ENGINE_PORT_SPEC_2026-08-01.md`](docs/RUST_CHESS_ENGINE_PORT_SPEC_2026-08-01.md).

## CI and evidence

Permanent workflows are intentionally separate:

- `CI` — Rust formatting, checks, Clippy, tests, release perft, rustdoc, x86-64 and ARM64 builds, and differential oracle;
- `Android JNI` — Kotlin lint, host-JVM JNI, dual native ABIs, APKs, API-35 lifecycle and metrics;
- `Robustness` — fuzzing, Miri, ASan/LSan, and TSan;
- `Performance` — x86-64 and ARM64 regression budgets plus scheduled Callgrind;
- `Slow perft` — scheduled/manual authoritative depth five;
- `Strength` — scheduled/manual historical weight-only 200-pair, 400-game control validation;
- `Variant validation` — native x86-64/ARM64 complete-identity smoke, development, and production controls.

Generated-output rules and deliberate evidence promotion are defined in [`docs/RUST_GENERATED_ARTIFACT_POLICY.md`](docs/RUST_GENERATED_ARTIFACT_POLICY.md).

## Additional documentation

- [`docs/RUST_CHESS_ENGINE_PORT_IMPLEMENTATION_REPORT.md`](docs/RUST_CHESS_ENGINE_PORT_IMPLEMENTATION_REPORT.md)
- [`docs/RUST_CHESS_ENGINE_V0_1_IMPLEMENTATION_REPORT.md`](docs/RUST_CHESS_ENGINE_V0_1_IMPLEMENTATION_REPORT.md)
- [`docs/RUST_DEVELOPER_WORKFLOWS.md`](docs/RUST_DEVELOPER_WORKFLOWS.md)
- [`docs/RUST_UCI_PROCESS_INTEGRATION.md`](docs/RUST_UCI_PROCESS_INTEGRATION.md)
- [`docs/RUST_ANDROID_JNI.md`](docs/RUST_ANDROID_JNI.md)
- [`docs/RUST_FUZZING.md`](docs/RUST_FUZZING.md)
- [`docs/RUST_SELF_PLAY_DATASET.md`](docs/RUST_SELF_PLAY_DATASET.md)
- [`docs/RUST_TUNING_WORKFLOW.md`](docs/RUST_TUNING_WORKFLOW.md)
- [`docs/RUST_PERFORMANCE_GATES.md`](docs/RUST_PERFORMANCE_GATES.md)
- [`docs/RUST_ROBUSTNESS_GATES.md`](docs/RUST_ROBUSTNESS_GATES.md)
- [`docs/RUST_CANDIDATE_VALIDATION.md`](docs/RUST_CANDIDATE_VALIDATION.md)

## License

MIT. See [`LICENSE`](LICENSE).
