# Rust Console Ralph Status

Status: shared `chess-app` extraction, preserved Rust TUI migration, Rust console implementation, focused automated acceptance, and explicit fail-loud audit fixes are complete. Permanent exact-source repository CI is the remaining automated closure step. Human-operated real-terminal console acceptance remains a separate manual gate.

## Source identity

- Planning baseline recorded by the console documents: `0964371d93b5a54c340769acf2909b86b47da7a6`.
- Console specification commit: `a6880532a43d6cc1f85ae33049b5257b1750aa6f`.
- Console TODO commit: `45e315dfb01670b97f86f25f6ecfc627ad7b9be0`.
- Authority-index repair after the new TODO exposed an existing documentation-audit requirement: `170b3dcc2c4223ee52205cfd68f87553b67c5d84`.
- Shared application-layer checkpoint after lockfile repair: `a1551e863134c2502cae441a568b7e71942c7551`.
- TUI shared-layer migration checkpoint: `6972824e3751c2825ee33b218314cd9ca2e3e8a5`.
- Initial validated console checkpoint: `cc181dcb2327bd10952fac70b81a98cdb006b09a`.
- Current fail-loud implementation checkpoint after the dedicated fallback/silent-failure audit: `d540b6b3f7db80ed1935a16a5ba8de551f1c318b`.

## Implemented architecture

The intended architecture is now present:

```text
chess-core        chess-search
     \              /
      \            /
         chess-app
          /     \
         /       \
 chess-tui     chess-console

chess-uci remains an independent machine-facing adapter.
```

`chess-app` owns presentation-neutral interactive game/session lifecycle, search request/ticket identity, exact search worker events, stale-result rejection, shared text formatting, and atomic saves. `chess-core` remains authoritative for chess rules and move legality. `chess-search` remains authoritative for evaluation/search/cancellation.

The full-screen Ratatui/Crossterm `chess-tui` remains supported. It was not replaced by the console. TUI-only menus, overlays, move-entry editing, save UI state, layout, key handling, raw-mode/alternate-screen lifecycle, and rendering remain in `chess-tui`.

`chess-console` is an additional line-oriented stdin/stdout frontend with ordinary terminal scrollback, menu/configuration prompts, a command parser, confirmations, explicit saves, and a state-free stdin event reader.

## TUI preservation evidence

The shared-layer migration was deliberately validated before substantive console completion.

- Focused migration run: `31331840727`.
- Job: `93291224158`.
- Tested migration source: `fc48e7870f15e5fc0ed5a0c9ae18a03cc52ce9ea`.
- Resulting validated/self-cleaned checkpoint: `6972824e3751c2825ee33b218314cd9ca2e3e8a5`.
- Result: success.

That run passed locked checks, strict Clippy, `chess-app` and `chess-tui` tests, and the complete existing real-PTY TUI acceptance suite. `crates/chess-tui/src/worker.rs` is now a compatibility re-export/test shim over the shared worker rather than an independent worker implementation.

## Console implemented surface

- `crates/chess-console` safe Rust crate with `#![forbid(unsafe_code)]`.
- Direct dependencies limited to `chess-app` and `chess-core`.
- No `chess-uci`, Python, Ratatui, Crossterm, JNI, FFI, or Android runtime dependency.
- Startup Human-vs-Engine / Self-play / Quit workflow.
- Human White and Human Black configuration.
- Independent White/Black Self-play depths.
- Explicit supported depth validation with no silent clamping.
- White/Black board orientation and shared board/status/history rendering.
- Bare UCI moves and `move <uci>`.
- `board`, `moves`, `status`, `engine`, `help`, `resign`, `save <path>`, `new`, `menu`, `quit`, `pause`, `resume`, and `step`.
- Case-insensitive command words and deterministic whitespace handling.
- Visible malformed/illegal/mode-invalid input failures.
- Human White and Human Black engine workflows using the in-process shared search worker.
- Engine progress with only available depth/score/nodes/NPS/time/hash/PV fields.
- Self-play automatic alternation, pause, one-ply step, and resume.
- Explicit destructive confirmations with empty response defaulting to No.
- Deterministic explicit-path non-PGN save format and overwrite confirmation.
- State-free stdin reader and application-thread-owned `GameController`.
- EOF handling distinct from empty input.
- Active engine worker cancellation/join on EOF and confirmed destructive exits.

## Fail-closed interactive search policy

Interactive frontends accept only an exact completed search result.

- Search fallback/emergency moves are rejected as gameplay results.
- An exact move without exact completed-iteration metrics fails closed.
- A search ending before completed depth one does not provide a playable fallback.
- Missing exact best move fails closed.
- Returned engine moves are revalidated against the current legal move set before application.
- Generation/request tickets reject stale completions.
- Search failure does not schedule an alternate move source.
- No random legal move fallback exists.
- No first-legal-move production fallback exists.
- No silent depth reduction/retry exists.
- No Python runtime fallback exists.
- No `chess-uci` subprocess fallback exists.
- No implicit opening-book/config/save discovery was added.

`get(0)`/first-move selection that remains in shared/TUI worker code is confined to test-fixture helpers used to construct a known legal move; it is not a production search-failure fallback.

## Input/worker lifecycle

`GameController` is owned and mutated by one application thread. The background console stdin reader owns only the OS input handle and typed event sender.

The reader sends `Line`, `Eof`, or `Error` events. It does not own game/search state. On piped input/EOF it terminates and can be joined. On explicit interactive process quit an OS-blocked stdin read may remain process-lifetime; this is documented honestly and is not treated as a successfully joined thread.

Engine workers do not receive that exception. At most one console-owned engine worker is active, and operational cancellation/destructive/EOF paths explicitly resolve it. Worker/channel/panic failure is converted to visible failure state/output.

`SearchWorker::Drop` and `ConsoleGame::Drop` retain best-effort final cleanup because Rust destructors cannot return an error. Normal operational paths do not rely on destructor cleanup for success/failure reporting; explicit join/cancel methods are used where errors can be surfaced.

## Save failure policy

Console saves use an explicit path and shared same-directory temporary write + rename.

A successful save is reported only after the final write/rename succeeds. Primary write/rename failures remain visible. The final audit additionally changed shared atomic-save cleanup so a secondary failure to remove a temporary artifact is included in the returned error rather than silently discarded. `NotFound` during cleanup remains harmless because it means no temporary artifact remains.

## Focused Ralph evidence

### Shared layer

- Run `31330821745`, job `93288662605`: rustfmt, locked `chess-app` check, strict Clippy, and focused shared tests succeeded.

### TUI migration

- Run `31331840727`, job `93291224158`: shared/TUI locked checks, strict Clippy, focused tests, and complete real-PTY TUI acceptance succeeded.

### Console checkpoint

- Initial console compile run `31332075424`, job `93291810112` failed before behavioral validation because `CommandParseError::UnexpectedArgument` incorrectly required a `'static` borrow from a normalized local command string.
- The parser error variant was changed to own its command name rather than weakening the parser.
- Corrected run `31332121813`, job `93291926330`: formatting, lockfile resolution and locked checks, strict Clippy, focused shared/console/TUI tests, real-process console acceptance, and complete TUI PTY acceptance all succeeded.
- Resulting self-cleaned checkpoint: `cc181dcb2327bd10952fac70b81a98cdb006b09a`.

### Final fail-loud audit fixes

The explicit dangerous-fallback/silent-failure audit found two convenience behaviors worth removing:

1. After a successful human move the console used the authoritative last move for display, but silently fell back to echoing raw user input if authoritative move history was unexpectedly empty. That could mask an invariant failure. It now returns a visible invariant error instead.
2. Shared atomic save cleanup discarded a secondary temporary-file cleanup error after a primary write/rename failure. The returned error now includes that cleanup failure, with a focused regression.

Validation:

- Run `31332721254`.
- Job `93293413075`.
- Tested workflow source: `32118ea8e928e163770e247fba828f3e7232afee`.
- Result: success.
- Passed formatting/locked checks, strict Clippy, all focused shared/console/TUI tests, real console process acceptance, and complete TUI PTY acceptance.
- Resulting self-cleaned implementation checkpoint: `d540b6b3f7db80ed1935a16a5ba8de551f1c318b`.

## Real-process console acceptance coverage

`crates/chess-console/tests/process_acceptance.rs` drives the actual executable with bounded timeouts and waits for persistent output markers rather than arbitrary sleeps. It covers:

- startup/menu quit;
- Human White `e2e4` followed by a real exact engine response and return to White turn;
- Human Black engine-first move and Black-oriented board;
- visible/non-mutating illegal move;
- resignation default-No/decline and confirmed resignation;
- overwrite decline preserving an existing file;
- confirmed overwrite and deterministic non-PGN save;
- visible save failure;
- Self-play pause, repeated one-ply step while paused, resume, and quit;
- confirmed quit during a deeper active engine search;
- EOF during active engine search without hanging.

## Ralph-discovered defects and repairs

1. Adding the new TODO exposed the repository's historical authority-index rule for `docs/*TODO*.md`; the new document was classified rather than disabling the audit.
2. An early manually staged lockfile edit changed unrelated checksum lines; the diff was inspected and those changes were restored before continuing.
3. Initial TUI extraction exposed save-state ownership/test seams and a borrow issue; `saved_path` remained TUI presentation state, tests were retargeted to the correct owner, and the existing PTY suite was preserved.
4. The first console compile exposed an owned-vs-borrowed parser error; the error type now owns the normalized command name.
5. The explicit silent-failure audit removed the raw-input display fallback after successful human moves.
6. The explicit silent-failure audit made secondary atomic-save cleanup errors visible.

No first-party lint suppression was added to bypass these findings.

## Permanent validation evidence

Pending for the final evidence/source freeze. Permanent CI must validate the exact final source identity; earlier permanent runs are supporting evidence only and are not used to claim final exact-SHA closure.

## Remaining closure gates

Automated source behavior is focused-green at `d540b6b3f7db80ed1935a16a5ba8de551f1c318b`. Remaining gates are:

1. permanent exact-source repository validation after this evidence state is frozen;
2. update `docs/RUST_CONSOLE_TODO.md` from exact evidence rather than assumptions;
3. human-operated real-terminal console acceptance.

The manual console acceptance section intentionally remains open until a human actually launches `bash scripts/dev.sh console` in a real terminal and records the user-visible UX checks. Automated process tests do not substitute for that manual claim.
