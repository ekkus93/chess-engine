# AGENTS.md

## Active implementation

The Rust workspace is the active chess engine. The Python tree is retained only as historical/reference material. Do not add Python engine features, repair Python-only behavior, or restore Python engine CI unless the user explicitly reverses that decision.

Authoritative documents include:

- `docs/RUST_CHESS_ENGINE_PORT_SPEC_2026-08-01.md`;
- `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`;
- `docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md`;
- `docs/RUST_DEVELOPER_WORKFLOWS.md`;
- `docs/RUST_CONSOLE_SPEC.md`;
- `docs/RUST_CONSOLE_TODO.md`.

## Repository workflow

- Work directly on `master`.
- Do not create a branch or pull request unless the user explicitly requests one.
- Do not mark a task complete merely because it compiles.
- Preserve exact commands, run URLs, job IDs, artifact IDs, and validated commit SHAs for major gates.
- Update authoritative TODO/status/evidence files only after exact evidence exists.
- Update `memory.md` only with exact timestamp/commit evidence.

## Core architecture

- `chess-core` owns rules, position state, notation, history, hashing, and perft.
- `chess-search` owns evaluation, transposition storage, search, limits, and cancellation.
- `chess-book` owns the explicit opening-book abstraction/format.
- `chess-app` owns presentation-neutral interactive game/session lifecycle, search worker events, search ticket/generation safety, shared text formatting, and atomic save primitives.
- `chess-tui` is the retained full-screen Ratatui/Crossterm human frontend. It owns TUI presentation/input/terminal state and consumes `chess-app` for shared gameplay/search lifecycle.
- `chess-console` is an additional human-facing scrolling stdin/stdout frontend. It consumes `chess-app`; it does not replace `chess-tui`.
- `chess-uci` remains a separate machine-facing protocol adapter and does not become the implementation backend for either human frontend.
- C ABI, JNI, Android, tooling, and tuning remain outward adapters/tools.

Do not duplicate `GameController`/`SearchWorker` behavior in `chess-tui` or `chess-console`. Do not move Ratatui/Crossterm/console prompt concerns into `chess-app`.

## Interactive correctness policy

- Human move legality comes from `chess-core`.
- Interactive engine moves come from `chess-search` through the shared `chess-app::SearchWorker`/controller lifecycle.
- Only an exact completed search move may be played.
- Search fallback/emergency moves must never become an interactive move.
- Never substitute a random legal move or first legal move after search failure.
- Never silently reduce depth, retry with a different policy, launch Python, or launch `chess-uci` as a fallback.
- Revalidate returned engine moves against current legal moves before applying them.
- Preserve generation/ticket rejection so stale results cannot mutate a restarted/abandoned game.
- Search/channel/worker/save failures must be visible.
- Engine workers must not be detached; destructive and EOF paths must resolve them explicitly.

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
bash scripts/dev.sh tui
bash scripts/dev.sh tui-pty-smoke
bash scripts/dev.sh console
bash scripts/dev.sh console-smoke
bash scripts/dev.sh android
bash scripts/dev.sh fuzz-smoke
bash scripts/dev.sh strength-audit
bash scripts/dev.sh artifact-audit
```

Use `bash scripts/dev.sh help` for exact self-play, tuning, TUI coverage, and variant-control syntax. Generated outputs must follow `docs/RUST_GENERATED_ARTIFACT_POLICY.md`.

## Testing rules

- Add focused regressions for every behavioral fix.
- Preserve both console real-process acceptance and TUI real-PTY acceptance when changing `chess-app`.
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
