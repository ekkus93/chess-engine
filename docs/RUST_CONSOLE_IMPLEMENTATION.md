# Rust Console Implementation

Companion specification: `docs/RUST_CONSOLE_SPEC.md`  
Implementation tracker: `docs/RUST_CONSOLE_TODO.md`

## Status

The Rust scrolling-console frontend is implemented on `master` as an **additional** human-facing application. The existing Ratatui/Crossterm TUI remains supported and has not been replaced.

The architecture is:

```text
chess-core        chess-search
     \              /
      \            /
         chess-app
          /     \
         /       \
 chess-tui     chess-console

chess-uci remains a separate machine-facing protocol adapter.
```

`chess-app` is the shared presentation-neutral interactive application/session layer. `chess-tui` and `chess-console` are separate presentation adapters over that layer.

## Shared `chess-app` extraction

`crates/chess-app` owns reusable interactive behavior that previously lived in the TUI controller/worker implementation:

- Human-vs-Engine and Self-play configuration;
- current `chess_core::Game` session ownership;
- game generation and search request/ticket identity;
- pending/active search state;
- exact search worker lifecycle and typed progress/final events;
- cancellation and worker joining;
- stale-event rejection;
- legal human-move resolution through `chess-core`;
- engine-move revalidation before application;
- Self-play pause/resume/step state transitions;
- shared board/history/status/score/search-metric text formatting;
- same-directory atomic write/rename primitive.

It does **not** own Ratatui/Crossterm state, console prompts, UCI protocol state, Python integration, Android/JNI/FFI concerns, tuning, or implicit configuration discovery.

## TUI preservation

`crates/chess-tui` remains the full-screen terminal UI. The extraction leaves TUI-specific concerns in the TUI crate:

- menus and screen state;
- confirmation/save overlays;
- move-input editing buffer;
- saved-path UI state;
- Ratatui rendering and responsive layout;
- Crossterm event handling;
- raw mode and alternate-screen lifecycle.

The TUI now delegates shared game/search behavior to `GameController`/`SearchWorker` in `chess-app`; it does not keep an independent duplicate interactive controller or search worker implementation.

### TUI extraction evidence

The migration was validated before the console was attached:

- validation workflow run: `31331840727`;
- job: `93291224158`;
- tested migration source: `fc48e7870f15e5fc0ed5a0c9ae18a03cc52ce9ea`;
- validated/self-cleaned TUI checkpoint: `6972824e3751c2825ee33b218314cd9ca2e3e8a5`.

That validation passed locked checks, strict Clippy, `chess-app` and `chess-tui` tests, and the complete existing real-PTY TUI acceptance suite. This evidence is specifically intended to prevent the shared-layer refactor from being treated as permission to remove or regress the TUI.

## Console crate

`crates/chess-console` is a safe Rust binary/library crate with `#![forbid(unsafe_code)]`.

Direct workspace dependencies are limited to:

- `chess-app`;
- `chess-core` for frontend-visible value types.

It does not depend on:

- `chess-uci`;
- Ratatui;
- Crossterm;
- Python;
- JNI/FFI/Android crates.

Run it with:

```bash
bash scripts/dev.sh console
```

Run actual-process acceptance coverage with:

```bash
bash scripts/dev.sh console-smoke
```

## Startup/configuration workflow

Startup presents:

```text
1. Human vs Engine
2. Self-play
3. Quit
```

Human-vs-Engine configuration asks for:

- White or Black;
- engine search depth.

Self-play configuration asks for independent White and Black search depths.

Empty choices use the documented defaults. Invalid or out-of-range depth is reported and reprompted; it is never silently clamped or retried at a different value.

## Console command grammar

Commands are case-insensitive and deterministic with leading/trailing/repeated whitespace.

Supported game commands:

```text
<uci>
move <uci>
board
moves
status
engine
help
resign
save <path>
new
menu
quit
pause
resume
step
```

A bare token such as `e2e4` is treated as a move candidate. UCI syntax and legal-move resolution remain authoritative in `chess-core` through the shared controller.

Unknown commands and mode-invalid commands produce visible errors rather than being silently ignored.

`resign` is Human-vs-Engine only. `pause`, `resume`, and `step` are Self-play-only.

## Search lifecycle

The console owns at most one active shared `SearchWorker`.

The runtime sequence is:

1. `GameController` creates a current `SearchRequest` with generation/request ticket.
2. The console takes that request and starts `SearchWorker` in-process.
3. Progress arrives as typed `EngineEvent::Progress` events and updates shared metrics.
4. A final worker event is joined/resolved before gameplay continuation.
5. An exact completed engine move is passed back through `GameController`.
6. `GameController` verifies the ticket still matches and revalidates the move against current legal moves before applying it.
7. Only after successful application does the console print `Engine plays: <uci>`.

Search worker/channel/panic failures become visible `Search failed` state/output. They do not silently start another search or choose another move source.

## Fail-closed search policy

The shared worker deliberately rejects convenience fallbacks for interactive play:

- a search fallback/emergency move is not a playable completion;
- an exact move without an exact completed iteration is a failure;
- a search ending before completed depth one is failure/cancellation, not a move source;
- missing exact best move is a failure;
- no random legal move fallback exists;
- no first-legal-move fallback exists;
- no silent depth reduction/retry exists;
- no Python fallback exists;
- no UCI subprocess fallback exists.

The search crate may retain its own typed fallback information for non-interactive API semantics; `chess-app` explicitly prevents that information from becoming a human-frontend move.

## Self-play

Self-play automatically schedules White, then alternates exact legal engine moves.

`pause` cancels/joins a currently owned engine worker, clears obsolete shared search state, and stops automatic scheduling.

While paused, `step` schedules exactly one ply. Completion does not turn automatic play back on. `resume` restores automatic scheduling. A terminal game schedules no further search.

Self-play in the console does not write tuning/evaluation/weight-candidate files. Saving remains an explicit user command with an explicit path.

## Input and shutdown model

`GameController` is owned and mutated by one application thread.

A separate state-free stdin reader thread owns only the OS input handle and a typed event sender. It sends:

- `Line(String)`;
- `Eof`;
- `Error(String)`.

It never owns or mutates game/search state.

While an engine search is active, the application thread multiplexes typed input and engine events using bounded channel polling. This permits `pause`, `quit`, and EOF handling while search is active without raw terminal mode.

EOF is distinct from an empty line. EOF cancels/joins an active engine worker, clears current shared search state, and exits deterministically.

On explicit interactive quit, an OS-blocked stdin reader may remain blocked until process exit. This is an intentional, documented **state-free process-lifetime input-reader limitation**, not a claim that it was joined. Engine search workers do not receive this exception and are explicitly resolved.

## Confirmations

Active-game destructive actions require confirmation:

- `resign`;
- `new`;
- `menu`;
- `quit`.

Saving to an existing destination requires overwrite confirmation.

Empty confirmation means No. Only explicit `y`/`yes` performs the action. Search cancellation occurs after affirmative confirmation, not merely because a destructive command was typed.

## Save format

Console saves begin with:

```text
Chess Engine Rust Console save v1
```

The deterministic text records:

- explicit timestamp label;
- game mode;
- human color/engine depth or independent Self-play depths;
- ordered UCI move history from the authoritative `Game`;
- current/final result.

This format is intentionally **not PGN**.

The path is always explicit. There is no implicit save directory and no auto-save. Writes use `chess_app::save::atomic_write`, which writes a same-directory temporary file and publishes by rename. Success is printed only after the final write/rename succeeds; failures remain visible.

## Console validation evidence

The first compile run exposed one parser lifetime/type defect and stopped before behavioral validation. It was corrected by making the unexpected-argument error own its command name.

The corrected console checkpoint was then validated with:

- validation workflow run: `31332121813`;
- job: `93291926330`;
- tested console source: `e4f442a5961405be7490427052821abb4f0a5973`;
- validated/self-cleaned checkpoint: `cc181dcb2327bd10952fac70b81a98cdb006b09a`.

The run passed:

- formatting;
- unlocked lockfile resolution/compile, followed by locked console check;
- strict Clippy for `chess-app`, `chess-console`, and `chess-tui`;
- focused `chess-app`, `chess-console`, and `chess-tui` tests;
- real-process console acceptance;
- the complete existing TUI real-PTY acceptance suite.

The real console process suite covers:

- startup and menu quit;
- Human White `e2e4` followed by a real exact engine response;
- Human Black with engine first move and Black board orientation;
- visible/non-mutating illegal move handling;
- resignation decline/default-No and confirmed resignation;
- save overwrite decline, confirmed overwrite, successful save, and visible save failure;
- Self-play pause, repeated one-ply steps while paused, resume, and quit;
- confirmed quit during an active deeper search;
- EOF during active search without hanging.

Tests use bounded timeouts and wait for persistent output/state markers rather than depending on arbitrary fixed sleeps.

## Automated versus manual acceptance

The process/PTY suites are automated evidence. They are not mislabeled as a human-operated terminal smoke test.

The manual console-acceptance section in `docs/RUST_CONSOLE_TODO.md` should remain unchecked until a human actually runs the documented console workflows in a real terminal and records the result.

Permanent exact-`master` CI evidence and final TODO closure are recorded separately in `docs/RUST_CONSOLE_TODO.md` after the documentation/evidence source is frozen and CI completes.
