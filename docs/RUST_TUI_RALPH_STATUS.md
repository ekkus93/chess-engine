# Rust TUI Ralph Status

Status: Rust implementation plus focused and permanent automated acceptance are complete on implementation/source SHA `a41a61e6b673aaa249aab9c378d2bd6f5018e0d7`. Human-operated real-terminal acceptance remains the only closure gate.

## Source identity

- Pre-implementation Rust baseline: `925f2e33271cd7657757f4428544a698268b6a7d`.
- TUI source freeze: `473dc5fad2c1611cd022648a28e43b99876f78fb`.
- `docs/RUST_TUI_SPEC.md` and `docs/RUST_TUI_TODO.md` were recovered from the prior `agent/rust-tui-spec` work and fast-forwarded onto `master` before implementation.

## Implemented surface

- New `crates/chess-tui` workspace member using Ratatui and Crossterm.
- Human vs Engine as White or Black with UCI coordinate input and promotion suffixes.
- Engine-vs-engine Self-play with pause/resume and one-ply step.
- Authoritative `chess_core::Game` state and `UciMove` resolution; no TUI chess-rules model.
- Bounded background search worker over `chess-search`, request/generation identities, stale-event rejection, explicit stop/discard lifecycle, and visible failures.
- Search panel for exact completed depth, score/mate, nodes, NPS, elapsed time, PV, and hash fullness when available.
- White/Black board orientation, move history, check/result/status display, confirmations, and responsive minimum-size handling.
- Explicit deterministic text saves with injected timestamp boundary and visible filesystem failures; the format is not labeled PGN.
- `bash scripts/dev.sh tui`, direct Cargo launch documentation, README architecture/controls documentation, and no Python runtime dependency.

## Fail-closed search policy

`chess-search::SearchResult::best_move()` may expose the generic engine's deterministic first-legal emergency result when cancellation happens before depth one. That generic behavior is deliberately **not** a TUI fallback.

`chess-tui` accepts a playable result only from `result.completed().best_move()`. A search that has no exact completed iteration becomes a visible TUI search failure and applies no move. Discard/cancel transitions suppress move delivery. The TUI has no random-move fallback, first-legal fallback, silent depth reduction/retry, search-policy replacement, Python-engine fallback, implicit book discovery, or automatic tuning/weight mutation.

## Focused Ralph evidence

- Run `31227985266`, job `93025997708`: locked metadata, `cargo check --locked -p chess-tui --all-targets`, strict Clippy, TUI unit/integration tests, release build, PTY launch/quit terminal-cleanup smoke, and Rust 1.75 MSRV check all succeeded on the frozen source line.
- Run `31227882334`, job `93025710323`: actual release executable entered and left Crossterm's alternate screen under a PTY and exited successfully on `q`.
- Run `31227799491`, job `93025481233`: responsive-layout hardening passed after rejecting dimensions that would truncate the complete board.
- Run `31227684896`, job `93025160830`: Human White/Black, Self-play, stale progress/completion, search failure, terminal-move, and resignation workflow tests passed.
- Run `31227584266`, job `93024850224`: the dependency graph passed the explicit Rust 1.75 check after constraining `unicode-segmentation` to an MSRV-compatible release.

## Ralph-discovered defects fixed

1. Initial TUI source had one denied unused import; it was removed rather than suppressed.
2. Strict Clippy rejected four legacy `io::ErrorKind::Other` constructions; they were replaced structurally with `io::Error::other`.
3. Ratatui's transitive dependency range selected `unicode-segmentation` 1.13.3, which requires Rust 1.85. The TUI manifest now pins an MSRV-compatible resolution rather than raising the repository's Rust 1.75 contract.
4. The first responsive-layout thresholds could render a truncated board at dimensions called supported. Layout selection now requires enough rows for the complete board and uses a clear minimum-size message otherwise.
5. A temporary Ralph workflow revision had invalid YAML indentation. That run never created a job and is not counted as code validation evidence.

## Permanent validation evidence

- Implementation/source SHA `a41a61e6b673aaa249aab9c378d2bd6f5018e0d7`.
- Permanent CI run `31228282277`: success. Workspace quality job `93026823684` and Linux ARM64 workspace job `93026823636` both succeeded.
- Permanent Robustness run `31228282261`: success. Miri `93026823576`, native sanitizers `93026823565`, and fuzz/corpus `93026823590` all succeeded.
- Permanent CI covered the repository audits, lockfile reproduction, formatting, workspace check/Clippy/tests, authoritative release perft, rustdoc, debug/release builds, UCI smoke, and pinned differential validation.
- The baseline-to-implementation diff changes no existing core/search/book/UCI/evaluation/tuning/promotion implementation source.
## Remaining closure gates

Permanent CI and Robustness have passed on the exact implementation/source SHA recorded above. The evidence-only bookkeeping commit is separately revalidated before final reporting.

The following TODO items intentionally remain human-operated and are not satisfied by headless/unit/PTY automation: play several legal plies as White, play several legal plies as Black, interactively exercise Self-play pause/resume/step, resignation confirmation, menu/quit while thinking, live resize, save success/failure, and visually confirm shell restoration on every exercised exit path.
