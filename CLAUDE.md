# Chess Engine — Rust project context

The Rust workspace is the active implementation. The Python engine remains only as historical/reference material; Python feature development and Python CI are retired.

## Mandatory workflow

- Work directly on `master`.
- Do not create a branch or pull request unless the user explicitly asks.
- Follow `docs/RUST_CHESS_ENGINE_PORT_SPEC_2026-08-01.md` and the authoritative Task tracker.
- Use `bash scripts/dev.sh help` for supported developer entry points.
- Do not mark completion until exact permanent CI evidence exists.
- Use `/lint-n-test` for fast validation and `/commit-push` to commit — both wrap `scripts/dev.sh fast`.

## Standard commands

```bash
bash scripts/dev.sh bootstrap
bash scripts/dev.sh fast
bash scripts/dev.sh full
bash scripts/dev.sh perft
bash scripts/dev.sh uci
bash scripts/dev.sh tui
bash scripts/dev.sh tui-coverage COMMAND
bash scripts/dev.sh android
bash scripts/dev.sh self-play CONFIG OUTPUT
bash scripts/dev.sh tune CONFIG DATASET OUTPUT [CKPT]
bash scripts/dev.sh strength-audit
bash scripts/dev.sh variant-control OUT TIER PROTOCOL
bash scripts/dev.sh fuzz-smoke
bash scripts/dev.sh artifact-audit
```

`scripts/dev.sh` is the only supported local entry point — never invoke `cargo`/`clippy`/`rustfmt` directly. The complete command and artifact contract is `docs/RUST_DEVELOPER_WORKFLOWS.md`.

CI (`ci.yml`) runs strictly more than local `full`: per-task audit scripts, a `cargo update --locked --dry-run` lockfile-drift check, and `cargo test --all-targets` (vs. `full`'s plain `--all-features`). Passing `full` locally is not proof CI is green.

## Architecture

- `chess-core`: values, positions, FEN/UCI notation, legal moves, make/unmake, history, hashing, perft.
- `chess-search`: evaluation, TT, negamax/alpha-beta, quiescence, iterative deepening, limits, cancellation.
- `chess-book`: explicit book interfaces and indexed format.
- `chess-uci`, `chess-ffi`, `chess-jni`, `chess-tui`: outward adapters (UCI protocol, C ABI, JNI, native Ratatui terminal UI).
- `chess-tools`, `chess-tune`: offline evidence, self-play, loss, SPSA, reports, and validation.
- `android-harness`: Kotlin/JVM and API-35 lifecycle integration — a Gradle project at repo root, not a `crates/` workspace member.
- `fuzz`: separate locked fuzz workspace.

Full crate dependency direction/ownership: `docs/RUST_WORKSPACE_ARCHITECTURE.md`.

Core/search forbid unsafe code. Recursive search must not clone positions per child or construct string keys. No conventional-path artifact discovery is allowed. C/JNI boundaries must catch panics and preserve ownership contracts.

## Coordinate contract

`a8 = 0`, `h8 = 7`, `a1 = 56`, `h1 = 63`. White pawns move toward smaller indices; black pawns
move toward larger indices. See `docs/RUST_CORE_VALUE_TYPES.md` and `docs/RUST_FEN_AND_UCI_NOTATION.md`.

## Correctness policy

Correctness comes before strength and speed. Keep exact perft, restoration, incremental hash/repetition identity, differential oracle, property tests, fuzz, Miri, sanitizers, Android/JNI lifecycle, performance, and strength evidence independent and fail-closed.

Miri/ASan/LSan/TSan run on a separately pinned nightly (`nightly-2026-08-01` in `robustness.yml`),
distinct from the floating `stable` toolchain in `rust-toolchain.toml` used for `fast`/`full`.
Install that exact nightly before running Miri locally.

Never add first-party `allow`/`expect` lint suppression. Never delete a regression input or weaken an assertion to obtain a green run.

## Generated artifacts

Follow `docs/RUST_GENERATED_ARTIFACT_POLICY.md`. Self-play data, tuning output, checkpoints, current benchmarks, Callgrind files, Android captures, and build output are transient unless deliberately promoted with schema, provenance, checksum, validator/replay, and review rationale.

Tuning candidates are always inactive. Task 21 validation and activation are independent boundaries.

## Tracking and memory

Update the Task TODO, Ralph status, and `memory.md` after validated evidence. Obtain exact UTC timestamps with `date -u +"%Y-%m-%dT%H:%M:%SZ"`; never invent them. Include the model name in memory headings.
