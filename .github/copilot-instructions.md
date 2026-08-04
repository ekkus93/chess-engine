# Active project instructions

The Rust workspace is the active chess engine. Treat `chess_game/` and Python tests as historical reference only. Do not add Python features or restore Python CI.

## Workflow

- Work directly on `master`; do not create branches or pull requests unless the user explicitly requests one.
- Follow `docs/RUST_CHESS_ENGINE_PORT_SPEC_2026-08-01.md` and the current Rust TODO/Ralph status.
- Use `bash scripts/dev.sh help` for supported commands.
- Run `bash scripts/dev.sh fast` for normal changes and `bash scripts/dev.sh full` for completion evidence where practical.
- Do not mark a task complete before permanent CI is green on the exact SHA.

## Architecture constraints

- Rules and state live in `chess-core`; search lives in `chess-search`; adapters point outward.
- No clone-per-child recursive search and no string position keys.
- No implicit weights/book/dataset/config discovery.
- No panic may cross C or JNI boundaries.
- No first-party Rust lint suppression.
- Correctness gates remain independent from robustness, performance, and strength.

## Artifacts

Follow `docs/RUST_GENERATED_ARTIFACT_POLICY.md`. Tuning and self-play output is transient and inactive unless explicitly promoted and separately validated.
