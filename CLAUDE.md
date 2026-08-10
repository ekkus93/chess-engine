# Chess Engine — Rust project context

The Rust workspace is the active implementation. The Python engine remains historical/reference material; Python engine feature development and Python engine CI are retired.

## Mandatory workflow

- Work directly on `master`.
- Do not create a branch or pull request unless the user explicitly asks.
- Follow the authoritative Rust port documents and the active task tracker.
- Use `bash scripts/dev.sh help` for supported developer entry points.
- Do not mark completion until exact permanent CI evidence exists.
- Use `/lint-n-test` for fast validation and `/commit-push` to commit when those skills are available; both must preserve `scripts/dev.sh fast` semantics.

## Standard commands

```bash
bash scripts/dev.sh bootstrap
bash scripts/dev.sh fast
bash scripts/dev.sh full
bash scripts/dev.sh perft
bash scripts/dev.sh uci
bash scripts/dev.sh tui
bash scripts/dev.sh tui-pty-smoke
bash scripts/dev.sh tui-coverage COMMAND
bash scripts/dev.sh console
bash scripts/dev.sh console-smoke
bash scripts/dev.sh android
bash scripts/dev.sh self-play CONFIG OUTPUT
bash scripts/dev.sh tune CONFIG DATASET OUTPUT [CKPT]
bash scripts/dev.sh strength-audit
bash scripts/dev.sh variant-control OUT TIER PROTOCOL
bash scripts/dev.sh fuzz-smoke
bash scripts/dev.sh artifact-audit
```

`scripts/dev.sh` is the supported local command dispatcher. The complete command and artifact contract is `docs/RUST_DEVELOPER_WORKFLOWS.md`.

CI (`ci.yml`) runs stricter repository-wide gates than a narrow frontend test. Passing a focused console/TUI/Android check is not proof permanent CI is green.

## Architecture

- `chess-core`: values, positions, FEN/UCI notation, legal moves, make/unmake, game history, hashing, perft.
- `chess-search`: evaluation, TT, negamax/alpha-beta, quiescence, iterative deepening, limits, cancellation.
- `chess-book`: explicit book interfaces and indexed format.
- `chess-app`: shared presentation-neutral application/session layer for human-facing frontends. It owns interactive configuration/lifecycle, search workers/events, generation/ticket safety, stale-result rejection, shared text formatting, and atomic save primitives.
- `chess-tui`: retained full-screen Ratatui/Crossterm human frontend over `chess-app`. It owns TUI menus/screens/overlays, key editing, responsive rendering, and terminal lifecycle.
- `chess-console`: additional scrolling stdin/stdout human frontend over `chess-app`. It owns console prompts/commands, typed stdin events, confirmations, and console-specific save serialization.
- `android-harness/android-app`: playable Kotlin/Jetpack Compose frontend. It owns Android presentation/platform state and uses the high-level `ChessGame` JNI session backed by `chess-app`; it must not duplicate the game/search controller in Kotlin.
- `chess-uci`: independent machine-facing UCI protocol adapter; human frontends do not launch it as a subprocess.
- `chess-ffi`: outward C boundary.
- `chess-jni`: outward JNI boundary with the existing low-level `ChessEngine` API plus the high-level Android `ChessGame`/`chess-app` session adapter.
- `chess-tools`, `chess-tune`: offline evidence, self-play, loss, SPSA, reports, and validation.
- `android-harness/android-smoke`, `android-harness/host-jvm`: Android/JVM lifecycle integration tests, not Rust workspace members.
- `fuzz`: separate locked fuzz workspace.

Full crate dependency direction/ownership: `docs/RUST_WORKSPACE_ARCHITECTURE.md`.

The TUI, console, and Android app are supported human-facing products. Shared gameplay/search lifecycle belongs in `chess-app`; presentation-specific state must stay in its frontend.

## Interactive search policy

Interactive frontends are fail-closed:

- play only an exact completed search move;
- never play `SearchResult` fallback/emergency moves;
- never choose a random or first legal replacement move;
- never silently reduce depth or retry with changed limits/policy;
- never invoke Python or a UCI subprocess as a fallback;
- revalidate engine moves against current legal moves;
- ignore stale generation/ticket results;
- surface search worker/channel failures;
- resolve engine workers on cancellation/destructive/EOF/close paths rather than intentionally detaching them.

## Console lifecycle policy

The console uses ordinary line-oriented stdin/stdout. A background stdin reader may send typed input events only and must not own game/search state. EOF is distinct from an empty line and must resolve an active engine worker before exit. If an interactive OS stdin read is blocked during explicit process quit, document that process-lifetime reader honestly; do not pretend it was joined. This exception applies only to the state-free input reader, never an engine search worker.

## Android lifecycle policy

The playable app performs JNI calls off the Android main thread. The native high-level session owns the authoritative `GameController` plus at most one `SearchWorker`. Kotlin may project FEN/legal-move snapshots into UI state, but it must not independently implement move legality or engine scheduling.

Explicit close is authoritative. Native high-level handles remain registered until native cleanup succeeds; Kotlin clears its handle only after native destruction succeeds. A failed explicit close must stay visible and retryable. The phantom-reference reaper is a leak backstop for an unreachable owner, not a normal success path.

## Coordinate contract

`a8 = 0`, `h8 = 7`, `a1 = 56`, `h1 = 63`. White pawns move toward smaller indices; black pawns move toward larger indices. See `docs/RUST_CORE_VALUE_TYPES.md` and `docs/RUST_FEN_AND_UCI_NOTATION.md`.

## Correctness policy

Correctness comes before strength and speed. Keep exact perft, restoration, incremental hash/repetition identity, differential oracle, property tests, fuzz, Miri, sanitizers, Android/JNI lifecycle, performance, and strength evidence independent and fail-closed.

Miri/ASan/LSan/TSan use the separately pinned nightly documented in the robustness workflow, distinct from the normal stable/MSRV product toolchains.

Never add first-party `allow`/`expect` lint suppression. Never delete a regression input or weaken an assertion to obtain a green run.

## Generated artifacts

Follow `docs/RUST_GENERATED_ARTIFACT_POLICY.md`. Self-play data, tuning output, checkpoints, current benchmarks, Callgrind files, Android captures/APKs, and build output are transient unless deliberately promoted with schema, provenance, checksum, validator/replay, and review rationale.

Tuning candidates remain inactive until a separate explicit validation/activation decision.

## Tracking and memory

Update task TODO/status/evidence files after validated evidence. Obtain exact UTC timestamps with `date -u +"%Y-%m-%dT%H:%M:%SZ"`; never invent them. Use exact commit timestamps when recording commit-tied history in `memory.md`.
