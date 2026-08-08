# Rust TUI Test Coverage Hardening Specification

Companion TODO: `docs/RUST_TUI_TEST_COVERAGE_HARDENING_TODO.md`

Status: proposed follow-up hardening specification

Baseline repository SHA: `1c83c40ff33fb77e9f19f6873b33561af64c9199`

## 1. Purpose

Harden the native Rust terminal UI with targeted unit, state-machine, integration, and failure-path tests, and add reproducible LLVM source-based coverage reporting through `cargo llvm-cov`.

The existing `crates/chess-tui` implementation already has meaningful workflow coverage. This follow-up is not a rewrite and is not a request to maximize a vanity percentage. Its purpose is to close identifiable gaps in safety-sensitive branches, make untested behavior visible, and provide repeatable coverage evidence for future Ralph loops and code reviews.

The highest-value targets are:

- deterministic proof that an emergency/fallback-only engine search result can never become a playable TUI move;
- direct coverage of `EngineRuntime` worker ownership, final-event handling, cancellation, join, disconnect, and failure visibility;
- direct coverage of keyboard, move-entry, confirmation, save-path, and self-play input state transitions;
- defensive `AppState` branches that currently rely mostly on surrounding integration behavior;
- terminal outcomes beyond checkmate, especially stalemate and automatic draws;
- UI save transactions rather than only serialization/filesystem helpers;
- rendering/serialization branch completion where inexpensive and deterministic;
- terminal restoration failure handling where a small, behavior-preserving test seam is justified;
- coverage tooling that records what is and is not exercised without silently excluding inconvenient production code.

## 2. Relationship to the existing Rust TUI program

This specification is a follow-up to:

- `docs/RUST_TUI_SPEC.md`
- `docs/RUST_TUI_TODO.md`

The original TUI TODO remains an authority record for its implementation and still contains manual real-terminal acceptance items. This hardening program does not retroactively mark those manual items complete and does not replace them.

This specification may add tests, test-only helpers, narrow presentation-neutral seams, developer scripts, and CI/reporting support. It must not change the intended TUI game behavior merely to make tests easier.

## 3. Non-goals

This milestone does not:

- change chess rules or legal-move semantics;
- change search strength, evaluation, pruning, extensions, move ordering, transposition behavior, opening-book behavior, tuning state, or promotion disposition;
- add a first-legal, random-legal, reduced-depth, Python, subprocess, or other search fallback;
- convert coverage percentage into a proxy for correctness;
- require 100% line, region, function, or branch coverage;
- fail production CI solely because an arbitrary coverage percentage decreases, unless a separate future policy explicitly adopts a reviewed threshold;
- exclude production modules from coverage merely because they are difficult to test;
- suppress errors or panic paths to make coverage runs green;
- weaken existing tests, Clippy, Miri, sanitizer, fuzz, perft, differential, UCI, or MSRV gates;
- add Codecov or another hosted coverage service as a requirement. Local/CI artifacts and summaries are sufficient for this milestone.

## 4. Core principles

### 4.1 Test invariants, not implementation trivia

Prefer tests that prove externally meaningful invariants:

- no stale or cancelled search result mutates the current game;
- no fallback-only result is promoted into `EngineEvent::Completed`;
- only an exact completed search iteration can supply a playable engine move;
- worker failure cannot leave the UI permanently thinking;
- only one TUI-owned search is active at a time;
- menu/new-game/quit/pause transitions resolve worker ownership before abandoning state;
- illegal input is transactional;
- save state is set only after a successful complete write;
- terminal outcomes stop future scheduling;
- user-visible failures stay visible rather than degrading to no-op behavior.

Do not add brittle tests that merely mirror private field assignments unless those assignments encode a state-machine contract.

### 4.2 Fail closed around engine results

The generic search layer may expose an emergency fallback result when no exact iterative-deepening depth completed. That behavior is not acceptable as a TUI move fallback.

The TUI contract remains:

1. an engine move is playable only when it came from `completed().best_move()`;
2. cancellation/discard prevents a final playable move from being delivered;
3. a non-discarded fallback-only result becomes a visible failure;
4. a result with no exact move and no fallback also becomes a visible failure;
5. no TUI code synthesizes another move after any of those failures.

This contract must have deterministic tests at the result-classification boundary, not only timing-dependent worker cancellation tests.

### 4.3 Coverage is observability

`cargo llvm-cov` is added to answer questions such as:

- which lines/functions/regions are never executed by tests;
- which error branches remain untested;
- whether a proposed hardening test actually reaches the intended branch;
- whether refactors create new untested production paths.

A higher number is useful only when it corresponds to meaningful behavior being exercised.

### 4.4 No silent exclusions

Any `cargo llvm-cov` exclusion must be documented with a reason. Do not hide low-coverage production code with broad filename/module exclusions.

Legitimate exclusions may include generated code or tooling artifacts that are outside the production TUI target, but such exclusions must be narrow and explicit.

## 5. `cargo llvm-cov` developer workflow

### 5.1 Tool installation

Coverage generation requires `cargo-llvm-cov` and the Rust LLVM tools component used by that tool.

The repository should provide a documented setup path. CI must use a reviewed, reproducible installation mechanism rather than implicitly trusting an unpinned moving `latest` forever.

Coverage tooling is development infrastructure, not a runtime dependency of `chess-tui` and not a reason to raise the product MSRV.

If the coverage tool itself requires a newer host toolchain than the repository MSRV, run coverage on a separately documented CI/developer toolchain while retaining the existing explicit MSRV compilation gate for product compatibility.

### 5.2 Canonical focused commands

The implementation should establish canonical equivalents of:

```bash
cargo llvm-cov clean --workspace
cargo llvm-cov -p chess-tui --all-features --summary-only
cargo llvm-cov -p chess-tui --all-features --lcov --output-path target/chess-tui-lcov.info
cargo llvm-cov -p chess-tui --all-features --html
```

The exact wrapper/script names may differ, but the repository must have one obvious supported command for:

- concise terminal summary;
- machine-readable LCOV artifact;
- optional local HTML inspection.

The coverage run must execute the real `chess-tui` test targets rather than a reduced synthetic suite that inflates the report.

### 5.3 Workspace coverage

A workspace-wide summary may be provided as an informational secondary command, for example:

```bash
cargo llvm-cov --workspace --all-features --summary-only
```

The primary scope of this hardening milestone is `chess-tui`. Workspace coverage must not become an excuse to expand this task into unrelated engine-test rewrites.

### 5.4 Baseline and final reports

Before adding hardening tests, record the focused `chess-tui` coverage summary on the baseline implementation.

After the hardening tests are complete, record the final summary using the same command/tool configuration.

At minimum retain/report:

- line coverage;
- function coverage where reported;
- region coverage where reported;
- uncovered files or major uncovered functions relevant to the TUI;
- tool version;
- Rust toolchain used for the coverage run;
- exact repository SHA.

The implementation report should explain important residual gaps rather than presenting only aggregate percentages.

## 6. Coverage and test architecture

### 6.1 Pure classification seam for search completion

Refactor only as much as necessary to make search-result classification deterministic under test.

Preferred shape:

- a small pure/internal helper classifies a completed search result plus discard state into a typed final disposition/event payload;
- `run_request`/`finish_request` remains responsible for channel delivery and worker lifecycle;
- production semantics remain byte-for-byte equivalent at the decision level.

Required classifications:

- discarded -> Cancelled;
- search error -> Failed;
- exact completed best move + exact metrics -> Completed;
- exact move but missing exact metrics/iteration -> Failed;
- fallback-only -> Failed with explicit fallback-rejected message;
- neither exact move nor fallback -> Failed.

Do not expose generic engine fallback moves to higher TUI layers merely for testing.

### 6.2 `EngineRuntime` test seam

`EngineRuntime` currently owns critical orchestration in `ui.rs`. Add direct tests for it.

If private concrete `SearchWorker` ownership makes deterministic error injection impossible, introduce the smallest testable abstraction that preserves these constraints:

- production still uses the real `SearchWorker`;
- no dynamic plugin architecture is needed;
- no alternate production search implementation is introduced;
- test doubles cannot leak into normal runtime selection;
- failure injection is explicit and local to tests.

A narrow worker handle/factory trait or internal enum is acceptable only if it materially improves deterministic lifecycle testing. Prefer simpler test-only constructors/channels when sufficient.

### 6.3 Key handling remains state-machine logic

Keyboard handlers may remain private functions in `ui.rs`; Rust unit tests in the same module can call them directly.

Use synthetic `KeyEvent` values to test controller transitions without a real terminal.

Do not use sleep-based terminal automation for behavior that can be proved synchronously through `AppState` and key handlers.

### 6.4 Filesystem seams

Keep `serialize_game` pure.

For UI save-flow tests, use temporary filesystem locations and naturally failing paths where deterministic. If a write abstraction is added, keep it minimal and ensure production still performs ordinary explicit writes with errors surfaced to the user.

### 6.5 Terminal restoration seams

`TerminalGuard` directly calls Crossterm/stdout and therefore has difficult failure branches.

A small internal terminal-operations abstraction may be introduced if it can deterministically prove cleanup sequencing and first-error preservation without changing the public/runtime behavior.

Do not overengineer this. The existing PTY smoke remains the strongest integration evidence for the real terminal happy path.

## 7. Required high-priority tests

## 7.1 Search fallback rejection

Add deterministic tests proving:

- fallback-only search disposition is `Failed`, not `Completed`;
- failure text clearly states that the TUI rejected the search fallback;
- no move is attached/applied;
- discard wins over any result and yields cancellation;
- exact completed result remains accepted;
- generic search fallback behavior is not modified globally to satisfy the TUI test.

This is P0 because it protects an explicit safety/fail-closed policy.

## 7.2 `EngineRuntime` lifecycle

Directly cover:

- pending request starts one worker;
- progress updates app presentation and retains worker ownership;
- Completed joins/removes the worker and permits subsequent scheduling;
- Failed joins/removes the worker and leaves visible failure state;
- Cancelled joins/removes the worker;
- finished worker with no final event becomes explicit visible failure;
- disconnected event channel is not silently ignored when the worker has ended;
- `cancel()` with no active worker is harmless;
- `cancel()` with an active worker requests cancellation and joins;
- worker spawn failure becomes a visible app failure and does not leave `thinking=true`;
- worker join/panic error propagates to the runtime boundary rather than becoming success;
- a replacement search is never started while an old worker is still owned.

## 7.3 Keyboard/input state machine

Directly cover at least:

### Main menu

- Up cannot underflow row zero;
- Down cannot exceed the last row;
- mode toggles through Left/Right/Enter where intended;
- Human color toggles;
- engine depths clamp to `MIN_SEARCH_DEPTH` and `MAX_MENU_SEARCH_DEPTH`;
- Self-play White/Black depths adjust independently;
- Enter on Start launches the selected configuration;
- q/Esc exits from the menu.

### Human game

- accepted move characters are appended lowercase;
- move input is capped at five characters;
- Backspace edits one character;
- Esc clears active move text rather than triggering menu abandonment;
- Enter submits the full typed move;
- malformed/illegal submission leaves the typed/error state understandable and does not mutate the game;
- shortcuts do not fire while move text is nonempty;
- human move characters are ignored when the engine owns the turn.

### Global/game shortcuts

- r opens resignation confirmation only in Human-vs-Engine active games;
- n opens new-game confirmation for an active game;
- m/Esc opens menu confirmation for an active game;
- q opens quit confirmation for an active game;
- completed games may take their defined direct post-game paths without unnecessary abandonment prompts;
- v opens save-path input.

### Confirmation overlay

- y confirms;
- Enter confirms;
- n cancels;
- Esc cancels;
- unrelated keys do not accidentally execute the action;
- confirmation execution resolves active engine ownership first.

### Self-play

- Space pauses a running active game and resolves search ownership;
- Space resumes a paused active game;
- s schedules one ply only while paused;
- s while running does not create a second search;
- controls are inert after terminal outcome as specified.

### Ctrl-C

- active worker is cancelled/joined before quit state is finalized;
- no stale completion can be applied after Ctrl-C.

## 8. `AppState` defensive coverage

Add direct tests for important defensive branches, including:

- invalid Human-vs-Engine depth below minimum;
- invalid Human-vs-Engine depth above maximum;
- invalid Self-play White depth;
- invalid Self-play Black depth;
- restart with no session;
- mark-saved with no session;
- human move during Self-play;
- human move while search is active;
- human move after game over;
- resignation during Self-play;
- resignation after game over;
- pause in Human-vs-Engine mode;
- resume in Human-vs-Engine mode;
- resume after terminal outcome;
- step while self-play is running;
- step while a search/pending request is active;
- step after terminal outcome;
- completion for current ticket containing a move no longer legal in current state;
- stale Cancelled and Failed events are ignored just like stale Progress/Completed;
- `cancel_search_state` clears pending/active/thinking while preserving or setting the requested visible message;
- returning to menu clears session/overlay/pending state;
- quitting clears pending search and overlay.

Where a branch is structurally unreachable through public state transitions, either document why or introduce a narrow invariant test; do not mutate production semantics simply to hit it.

## 9. Terminal-state coverage

Use authoritative `chess-core` positions/history.

Required additions:

- stalemate fixture becomes `GameOutcome::Stalemate` and schedules nothing;
- dead-position/insufficient-material automatic draw, where represented by the core, becomes terminal and schedules nothing;
- at least one other automatic draw path if practical without constructing unrealistic hidden state;
- claimable draw remains nonterminal unless the TUI implements an explicit claim action;
- check status renders `CHECK` without falsely declaring game over;
- result formatting covers all `GameOutcome` variants;
- draw-reason formatting covers all `DrawReason` variants.

Do not duplicate draw adjudication in the TUI.

## 10. Save-flow coverage

Add tests around the user-visible save transaction:

- default save overlay path is explicit;
- path editing appends printable characters;
- Backspace edits path;
- Esc dismisses without a write or Saved state change;
- empty/whitespace-only path produces visible failure;
- successful save writes exact serialized contents, records `saved_path`, displays success, and closes overlay;
- failed write clears/does not set `saved_path`, leaves failure visible, and does not report success;
- save requested with no game cannot panic or report false success;
- a subsequent game move clears prior saved state;
- serialization covers Human/White, Human/Black, Self-play, no timestamp, multiple moves, promotion, and representative terminal results.

Do not call the format PGN unless valid PGN support is separately implemented.

## 11. Rendering-helper coverage

Add cheap deterministic tests for meaningful formatting branches:

- all six piece kinds for White and Black;
- empty move history;
- odd/even move history remains stable;
- `orientation_for_config` for White human, Black human, and Self-play;
- `format_search_metrics` with all fields populated;
- metrics with a subset of optional fields absent;
- PV formatting;
- hash fullness formatting;
- duration formatting in millisecond and second ranges;
- positive/negative/zero centipawn scores;
- positive/negative mate scores;
- outcome and draw-reason strings;
- check and draw-claim status variants;
- exact layout boundary values immediately below/at/above wide and stacked thresholds;
- render snapshots/structural assertions for confirmation and save overlays where useful.

Avoid enormous full-screen golden snapshots that are noisy under harmless spacing changes. Prefer structural assertions for important text/state.

## 12. Terminal guard coverage

Retain the real PTY launch/quit smoke test.

If a narrow terminal-operations seam is introduced, cover:

- raw mode enabled -> alternate-screen entry failure attempts raw-mode restoration;
- terminal construction failure attempts both raw and alternate-screen cleanup as applicable;
- normal restore attempts raw-mode disable, alternate-screen leave, and cursor show;
- if one restore step fails, later cleanup steps are still attempted;
- the first restoration error is returned;
- successful restore sets the guard restored flag so `Drop` does not repeat cleanup;
- `Drop` performs best-effort cleanup only when explicit restoration did not complete.

Do not silently convert explicit `restore()` errors into success.

## 13. CI integration

Add an informational Rust TUI coverage job or step with these properties:

- runs on Linux where LLVM source coverage is supported by the chosen Rust toolchain;
- installs the LLVM tools component and `cargo-llvm-cov` reproducibly;
- runs the canonical focused TUI coverage command;
- emits a human-readable summary in the job log;
- generates an LCOV artifact;
- uploads the coverage artifact through GitHub Actions artifact storage if the permanent CI structure supports it cleanly;
- does not require a third-party coverage account/token;
- does not fail solely because a percentage is below an arbitrary threshold;
- does fail if instrumentation/test execution itself fails;
- does fail if report generation fails;
- preserves existing permanent CI/robustness gates.

The coverage job may be a separate permanent workflow or a clearly isolated job in an existing permanent workflow. Prefer the arrangement that avoids unnecessarily serializing the normal quality gate behind coverage instrumentation.

## 14. Coverage policy

For this milestone:

- baseline percentage: record it;
- final percentage: record it;
- hard minimum percentage: none;
- regression threshold: none initially;
- required uncovered-code review: yes;
- required P0/P1 branch coverage described in this specification: yes.

After enough history exists, a future task may define a modest reviewed threshold or changed-lines policy. That is outside this specification.

## 15. Validation gates

The final exact implementation SHA must pass at least:

```bash
cargo fmt --all -- --check
cargo check --locked --workspace --all-targets --all-features
cargo clippy --locked --workspace --all-targets --all-features -- -D warnings
cargo test --locked --workspace --all-targets --all-features
cargo test --locked -p chess-tui --all-targets --all-features
cargo build --locked --release -p chess-tui
cargo llvm-cov -p chess-tui --all-features --summary-only
cargo llvm-cov -p chess-tui --all-features --lcov --output-path target/chess-tui-lcov.info
```

In addition:

- existing authoritative perft gates remain green;
- differential/core correctness gates remain green;
- UCI gates remain green;
- Miri/sanitizer/fuzz robustness gates relevant to the repository remain green;
- explicit MSRV validation remains green independently of the coverage host toolchain;
- no search/evaluation/tuning/promotion source behavior changes unless separately authorized;
- no new production fallback is introduced.

## 16. Evidence requirements

The implementation/closure record must capture:

- starting SHA;
- final source SHA;
- `cargo-llvm-cov` version;
- Rust coverage toolchain version;
- baseline focused TUI coverage summary;
- final focused TUI coverage summary;
- list of major residual uncovered branches/functions and disposition;
- exact commands run;
- focused test/coverage CI run IDs;
- permanent CI run ID and job IDs;
- robustness run ID and job IDs where applicable;
- confirmation that fallback-only search results remain rejected;
- confirmation that no first-legal/random/depth-reduction/Python fallback exists;
- confirmation that no engine search/evaluation/tuning/promotion semantics changed;
- final diff audit against the starting SHA.

Do not create evidence recursion by repeatedly modifying the validated SHA merely to embed the latest workflow run ID. The final chat/report may record run IDs that validate the already-frozen SHA.

## 17. Definition of done

This hardening milestone is complete only when:

1. `cargo llvm-cov` has a documented, reproducible focused TUI workflow;
2. baseline and final coverage are recorded using equivalent configuration;
3. fallback-only result rejection has deterministic direct coverage;
4. `EngineRuntime` lifecycle/error branches identified in this spec have deterministic coverage or an explicit justified disposition;
5. keyboard/overlay/self-play input-state transitions have direct tests;
6. important `AppState` defensive branches have direct tests;
7. stalemate and automatic-draw behavior have authoritative fixtures where supported;
8. the save UI transaction is tested end-to-end at the controller/filesystem boundary;
9. meaningful rendering/serialization gaps are covered;
10. terminal cleanup remains integration-tested and any introduced restoration seam is unit-tested;
11. coverage instrumentation/report generation succeeds in CI;
12. existing correctness, lint, build, MSRV, and robustness gates remain green;
13. no silent failure/fallback behavior was introduced;
14. the exact final repository SHA has permanent validation evidence;
15. the companion TODO is reconciled honestly, with any intentionally untested residual branch left open or explicitly dispositioned rather than silently checked off.
