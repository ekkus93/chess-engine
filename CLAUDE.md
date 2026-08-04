# Chess Engine — Rust project context

The Rust workspace is the active implementation. The Python engine remains only as historical/reference material; Python feature development and Python CI are retired.

## Mandatory workflow

- Work directly on `master`.
- Do not create a branch or pull request unless the user explicitly asks.
- Follow `docs/RUST_CHESS_ENGINE_PORT_SPEC_2026-08-01.md` and the authoritative Task tracker.
- Use `bash scripts/dev.sh help` for supported developer entry points.
- Do not mark completion until exact permanent CI evidence exists.

## Standard commands

```bash
bash scripts/dev.sh bootstrap
bash scripts/dev.sh fast
bash scripts/dev.sh full
bash scripts/dev.sh perft
bash scripts/dev.sh uci
bash scripts/dev.sh android
bash scripts/dev.sh fuzz-smoke
```

The complete command and artifact contract is `docs/RUST_DEVELOPER_WORKFLOWS.md`.

## Architecture

- `chess-core`: values, positions, FEN/UCI notation, legal moves, make/unmake, history, hashing, perft.
- `chess-search`: evaluation, TT, negamax/alpha-beta, quiescence, iterative deepening, limits, cancellation.
- `chess-book`: explicit book interfaces and indexed format.
- `chess-uci`, `chess-ffi`, `chess-jni`: outward adapters.
- `chess-tools`, `chess-tune`: offline evidence, self-play, loss, SPSA, reports, and validation.
- `android-harness`: Kotlin/JVM and API-35 lifecycle integration.
- `fuzz`: separate locked fuzz workspace.

Core/search forbid unsafe code. Recursive search must not clone positions per child or construct string keys. No conventional-path artifact discovery is allowed. C/JNI boundaries must catch panics and preserve ownership contracts.

## Correctness policy

Correctness comes before strength and speed. Keep exact perft, restoration, incremental hash/repetition identity, differential oracle, property tests, fuzz, Miri, sanitizers, Android/JNI lifecycle, performance, and strength evidence independent and fail-closed.

Never add first-party `allow`/`expect` lint suppression. Never delete a regression input or weaken an assertion to obtain a green run.

## Generated artifacts

Follow `docs/RUST_GENERATED_ARTIFACT_POLICY.md`. Self-play data, tuning output, checkpoints, current benchmarks, Callgrind files, Android captures, and build output are transient unless deliberately promoted with schema, provenance, checksum, validator/replay, and review rationale.

Tuning candidates are always inactive. Task 21 validation and activation are independent boundaries.

## Tracking and memory

Update the Task TODO, Ralph status, and `memory.md` after validated evidence. Obtain exact UTC timestamps with `date -u +"%Y-%m-%dT%H:%M:%SZ"`; never invent them. Include the model name in memory headings.
