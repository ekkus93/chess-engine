# AGENTS.md

## Active implementation

The Rust workspace is the active chess engine. The Python tree is retained only as historical/reference material. Do not add Python features, repair Python-only behavior, or restore Python CI unless the user explicitly reverses that decision.

Authoritative documents:

- `docs/RUST_CHESS_ENGINE_PORT_SPEC_2026-08-01.md`;
- `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`;
- `docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md`;
- `docs/RUST_DEVELOPER_WORKFLOWS.md`.

## Repository workflow

- Work directly on `master`.
- Do not create a branch or pull request unless the user explicitly requests one.
- Do not mark a task complete merely because it compiles.
- Preserve exact commands, run URLs, job IDs, artifact IDs, and validated commit SHAs for major gates.
- Update the authoritative TODO, Ralph status, and `memory.md` only after exact evidence exists.

## Core architecture

- `chess-core` owns rules, position state, notation, history, hashing, and perft.
- `chess-search` owns evaluation, transposition storage, search, limits, and cancellation.
- `chess-book` owns the explicit opening-book abstraction/format.
- UCI, C ABI, JNI, Android, tooling, and tuning are outward adapters.
- `chess-core` and `chess-search` forbid unsafe code.
- Recursive search uses make/unmake, not clone-per-child.
- Search and repetition use typed/incremental identities, not string keys.
- No adapter discovers weights, books, datasets, or configuration from conventional paths.
- Rust panics must not cross C or JNI boundaries.
- Performance and strength evidence never override correctness gates.

## Coordinate contract

- `a8 = 0`, `h8 = 7`, `a1 = 56`, `h1 = 63`.
- White pawns move toward smaller internal row indices.
- Black pawns move toward larger internal row indices.

See `docs/RUST_CORE_VALUE_TYPES.md` and `docs/RUST_FEN_AND_UCI_NOTATION.md`.

## Developer commands

```bash
bash scripts/dev.sh bootstrap
bash scripts/dev.sh fast
bash scripts/dev.sh full
bash scripts/dev.sh perft
bash scripts/dev.sh uci
bash scripts/dev.sh android
bash scripts/dev.sh fuzz-smoke
```

Use `bash scripts/dev.sh help` for explicit self-play and tuning syntax. Generated outputs must follow `docs/RUST_GENERATED_ARTIFACT_POLICY.md`.

## Testing rules

- Add focused regressions for every behavioral fix.
- Keep exact perft, state restoration, hash identity, differential validation, fuzz/Miri/sanitizers, ABI/JNI lifecycle, Android instrumentation, performance, and strength gates independent.
- Do not suppress first-party Rust warnings with `allow` or `expect`; fix them structurally.
- Do not weaken a test or fixture merely to restore a green run.
- Preserve minimized fuzz regressions permanently.

## Memory file

`memory.md` is persistent project history. Before recording a new entry, obtain an exact UTC timestamp with:

```bash
date -u +"%Y-%m-%dT%H:%M:%SZ"
```

Use the actual commit timestamp when an entry is specifically tied to a commit. Include the model name in the heading. Never guess timestamps or claim validation without exact evidence.
