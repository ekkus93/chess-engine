# Rust Chess Engine v0.1 Implementation Report

**Status:** Task 26 functional-engine signoff complete
**Report date:** 2026-08-04
**Specification:** `docs/RUST_CHESS_ENGINE_PORT_SPEC_2026-08-01.md`
**Functional implementation baseline:** `332967613098f30348489a73249e822c9eb70bc3`
**Exact validated Task 26 signoff implementation:** `80cf18f77d3901e8285553211a45d51b530b5579`

## Evidence identity

This report signs off the functional Rust engine at commit
`332967613098f30348489a73249e822c9eb70bc3`. That exact commit was validated by
permanent GitHub Actions on Linux x86-64, native Linux AArch64, Android, Miri,
sanitizers, fuzzing, and the two architecture-specific performance gates.

The exact Task 26 signoff implementation adds only this evidence report, a
permanent fail-closed signoff audit, a real playable UCI transcript smoke, and
CI wiring. It does not change chess rules, evaluation, search, ABI, JNI, UCI,
or default weights. Task 21 remains an independent tuned-candidate activation
gate and is not silently satisfied by this functional v0.1 signoff.

Python engine development and Python engine CI are retired. Python remains only
as the pinned `python-chess` differential oracle and as repository validation
tooling; production Rust crates do not embed or launch a Python runtime.

## Exact validation commands and outputs

The permanent `CI` workflow executed these commands against the exact validated
implementation:

```text
cargo fmt --all -- --check
cargo check --locked --workspace --all-targets --all-features
cargo clippy --locked --workspace --all-targets --all-features -- -D warnings
cargo test --locked --workspace --all-features
cargo test --locked -p chess-core --release authoritative_perft_depth_four -- --ignored --exact
RUSTDOCFLAGS=-D warnings cargo doc --locked --workspace --all-features --no-deps
cargo build --locked --workspace --all-features
cargo build --locked --workspace --all-features --release
python scripts/differential_oracle.py \
  --binary target/release/chess-tools \
  --corpus fixtures/differential_corpus.tsv \
  --games 12 \
  --plies 48 \
  --seed 0xC0FFEE
```

Observed results:

```text
workspace tests: 377 passed; 4 ignored; 0 failed
release depth-four authoritative perft: 1 passed; 0 failed
differential validation: passed
documentation with warnings denied: passed
Linux x86-64 debug/release builds: passed
native Linux AArch64 debug/test-build/release builds: passed
```

Primary exact-SHA runs and jobs:

| Gate | Run | Job(s) | Result |
|---|---:|---:|---|
| Rust CI | `30962735433` | `92169954502`, `92169954449` | x86-64 and native AArch64 passed |
| Android | `30962735439` | `92169954247`, `92169954245`, `92169954196` | lint, host JVM, API-35 passed |
| Robustness | `30962735450` | `92169954171`, `92169954098`, `92169954164` | sanitizers, fuzzing, Miri passed |
| Performance | `30962735451` | `92169954438`, `92169954397` | x86-64 and AArch64 budgets passed |

## Rules signoff

| Requirement | Permanent evidence | Result |
|---|---|---|
| Strict FEN parsing | malformed-category, canonical-round-trip, UTF-8, castling, en-passant and counter tests in `chess-core` | Passed |
| Legal move generation | pseudo/legal separation, check/pin/evasion properties, legal-move differential corpus | Passed |
| Castling, en passant, promotion | focused unit tests plus authoritative perft positions | Passed |
| Exact make/unmake | all move categories, randomized legal sequences, byte-for-byte restoration properties | Passed |
| Correct incremental hash | full recomputation equality, move-category updates, en-passant identity and repetition tests | Passed |
| Mate and stalemate | terminal-state fixtures and search terminal tests | Passed |
| Claimable and automatic draws | threefold/fivefold, 50/75-move and dead-position tests | Passed |
| Exact perft | six committed positions through depth four in CI and depth five on the scheduled/manual gate | Passed |
| Differential corpus | committed corpus, child-FEN checks, oracle perft and seeded legal playouts | Passed |

No rules requirement is waived or inferred solely from a benchmark.

## Search signoff

| Requirement | Permanent evidence | Result |
|---|---|---|
| Baseline evaluator | symmetry, sign, term-trace and fixed-position tests | Passed |
| Reference search | independent unpruned negamax oracle | Passed |
| Negamax alpha-beta | shallow equivalence and exact-score fixtures | Passed |
| Quiescence | tactical oracle, in-check, promotion and evasion witnesses | Passed |
| Move ordering | exact-score preservation and strict node-reduction witnesses | Passed |
| Transposition table | key, depth, bound, generation, replacement and mate-normalization tests | Passed |
| Iterative deepening | completed-depth, partial-depth discard and accounting tests | Passed |
| Aspiration recovery | fail-low/fail-high widening to exact full-window result | Passed |
| Legal principal variation | replay-safe PV reconstruction properties | Passed |
| Responsive cancellation | one-node polling bound, C ABI active stop and Android latency measurement | Passed |
| Deterministic fixed limits | fixed-depth/fixed-node result and accounting tests | Passed |

The engine is single-threaded by design in v0.1. Cancellation may be requested
from another thread, but the search itself has one worker.

## Adapter signoff

### UCI

The real subprocess suite validates exact handshake text, readiness, start
position and FEN setup, legal fixed-depth best moves, invalid-position
transactionality, `stop`, `quit`, terminal `bestmove 0000`, and concurrent
process isolation.

### Safe Rust facade

The safe facade owns engine state, exposes transactional position changes,
legal UCI moves, immutable synchronous search snapshots, typed errors,
request-local cancellation, and explicit identity/configuration values. Public
Rust documentation builds with warnings denied.

### C ABI

The versioned C ABI uses opaque handles, explicit byte lengths, typed result
codes, owned output buffers, panic containment, stale-handle rejection and
exact free semantics. Lifecycle tests cover 128 engine and cancellation-token
create/destroy cycles, invalid input without mutation, active cross-thread
cancellation, and result/buffer tamper rejection.

### Android JNI

The Android gate builds and verifies both `arm64-v8a` and `x86_64` ELF shared
libraries, confirms the `nativeSearch` JNI export, assembles the library and
test APKs, runs host-JVM contract tests, and executes five instrumented tests on
an API-35 x86-64 emulator.

## Quality signoff

- Formatting, locked workspace check, strict Clippy and warning-free rustdoc pass.
- All workspace tests pass: **377 passed; 4 ignored; 0 failed**.
- Release depth-four perft passes.
- Native Linux AArch64 debug, test-build and release builds pass.
- Android ARM64 and x86-64 JNI builds and API-35 execution pass.
- Miri, AddressSanitizer/LeakSanitizer, ThreadSanitizer and bounded libFuzzer campaigns pass.
- Source audits reject clone-per-child search, FEN/String search keys, hidden evaluation tracing/allocation and prohibited ordering shortcuts.
- Repository issue searches found no open issue labeled `P0` or `P1`, and no open issue containing an unresolved `P0` or `P1` correctness designation on 2026-08-04.

## Authoritative perft table

Values are committed in `fixtures/perft.tsv`; depth four runs on every Rust CI
push, and depth five runs on the scheduled/manual slow-perft gate.

| Position | d1 | d2 | d3 | d4 | d5 |
|---|---:|---:|---:|---:|---:|
| Starting position | 20 | 400 | 8,902 | 197,281 | 4,865,609 |
| Kiwipete | 48 | 2,039 | 97,862 | 4,085,603 | 193,690,690 |
| En-passant rook ending | 14 | 191 | 2,812 | 43,238 | 674,624 |
| Castling, promotion and pins | 6 | 264 | 9,467 | 422,333 | 15,833,292 |
| Promotion check evasion | 44 | 1,486 | 62,379 | 2,103,487 | 89,941,194 |
| Tactical/positional | 46 | 2,079 | 89,890 | 3,894,594 | 164,075,551 |

## Differential-validation statistics

Exact clean-head output:

```text
differential validation passed: 15 corpus positions, 293 child FENs,
272,991 oracle perft nodes, 576 seeded plies, seed=12648430
```

The oracle is pinned through `requirements/oracle.txt`. It checks legal moves,
resulting child positions, perft totals and seeded legal playout behavior against
`python-chess`; it is validation infrastructure, not a production dependency.

## Benchmark environment and results

Clean-head benchmark environment:

```text
GitHub-hosted Ubuntu 24.04.4 LTS
x86_64 and native AArch64 runners
rustc 1.97.1 (8bab26f4f, 2026-07-14)
LLVM 22.1.6
release profile, seven baseline samples
```

Selected x86-64 medians from run `30962735451`, job `92169954438`:

| Benchmark | Median | Allocation result |
|---|---:|---|
| Leaper attack lookup | 1 ns/op | zero |
| Sliding attack sweep | 10,072 ns/op | zero |
| Legal move generation | 2,158 ns/op | zero |
| Make/unmake | 39 ns/op | zero |
| Full hash recomputation | 52 ns/op | zero |
| Incremental hash update | 77 ns/op | zero |
| Full evaluation | 717 ns/op | zero |
| Starting-position perft d4 | 14,712,461 ns | zero |
| Kiwipete perft d3 | 7,064,686 ns | zero |
| Starting search, 20,000 nodes | 76,994,469 ns | bounded |
| Tactical search, 20,000 nodes | 108,317,654 ns | bounded |
| FFI fixed-node search | 19,793,134 ns | bounded |

Every x86-64 and AArch64 comparator row passed. Evidence artifacts:

- x86-64: `8913539885`
- native AArch64: `8913538200`

Android API-35 measurements from artifact `8913595215`:

| Metric | Result |
|---|---:|
| Legal-move JNI average | 70,524 ns |
| Fixed-node total nodes | 89,106 |
| Fixed-node wall time | 1,252,134,961 ns |
| Fixed-node throughput | 71,163 nodes/s |
| Cancellation response | 1,715,438 ns |
| Native heap delta, 1 MiB TT | 1,053,504 bytes |
| Native heap delta, 16 MiB TT | 16,782,144 bytes |

## UCI transcript

The exact handshake contract validated by the real subprocess suite is:

```text
> uci
< id name chess-engine-rust 0.1.0
< id author Phillip Chin
< option name Hash type spin default 1 min 1 max 65536
< option name CheckExtension type check default false
< option name OwnBook type check default false
< uciok
> isready
< readyok
```

The permanent Task 26 runtime smoke produced this exact playable transcript:

```text
> position startpos
> go depth 1
< info depth 1 seldepth 1 score cp 44 nodes 21 nps 21000 time 0 hashfull 0 pv b1c3
< bestmove b1c3
```

The smoke requires one completed-depth `info` line with a legal PV followed by
one legal, non-null `bestmove`. The full subprocess integration suite remains
the authoritative protocol test.

## C ABI and Android JNI evidence

Clean-head C ABI evidence is part of the 377-test workspace run. Key lifecycle
witnesses include:

```text
rust_through_abi_smoke_covers_complete_lifecycle
repeated_create_destroy_is_unique_and_stale_safe
invalid_inputs_fail_loudly_without_mutation
active_infinite_search_cancels_from_another_thread
buffer_and_search_result_lifecycles_are_exact
exported_test_fault_is_contained_and_process_remains_usable
```

Clean-head JNI evidence:

```text
ARM64 ELF shared object: passed
x86-64 ELF shared object: passed
nativeSearch export in both ABIs: passed
host JVM JNI contract: passed
API-35 instrumented tests: 5 passed
Android lint: passed
metric artifact: 8913595215
```

## Known limitations and deferred features

These are explicit v0.1 boundaries, not hidden failures:

- Search is single-threaded; there is no Lazy SMP or parallel root search.
- There is no NNUE or other neural evaluator.
- There is no Syzygy/tablebase integration.
- There is no distributed search, network play, cloud service or WebAssembly target.
- `no_std` is not supported.
- Opening-book support exists, but a book is optional and explicitly injected.
- Tuned weight activation is not complete: Task 21 remains open until a real candidate passes the independent 200-pair protocol and is explicitly activated.
- The retired Python engine is not maintained as a second production implementation and has no engine-development CI.

## Signoff conclusion

The evidence supports the Task 26 conclusion: the Rust engine is a correct,
playable and portable functional v0.1. It is suitable as the preferred engine
implementation for new integrations through the safe Rust facade, UCI, C ABI
or Android JNI boundary.

This conclusion does not claim completion of Task 21 tuned-weight activation or
Task 27 full-port/release signoff.
