# Rust Console Ralph Status

Status: **automated implementation and repository validation complete**. The only remaining acceptance item is a short **human subjective UX/readability review** in a real terminal. Objective terminal behavior is now covered by permanent PTY CI and is no longer treated as manual-only evidence.

## Final automated source identity

- Clean automated-closure source SHA: `4875a7e29bf87d2e5026e3a25e419a4bbc3c93df`.
- `master` at automated closure: `4875a7e29bf87d2e5026e3a25e419a4bbc3c93df`.
- Permanent CI run: `31338059357`.
- Rust workspace quality job: `93307080189` — success.
- Linux ARM64 workspace build job: `93307080185` — success.
- Permanent `Run console PTY acceptance` step: success.

The permanent quality job passed repository authority audits, committed lockfile verification, workspace metadata, rustfmt, workspace check, strict Clippy, full workspace tests, console PTY acceptance, authoritative release perft, rustdoc, debug/release builds, UCI smoke, and the pinned Python differential oracle. ARM64 metadata/debug/test-compile/release also passed.

## Implemented architecture

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

The full-screen Ratatui/Crossterm `chess-tui` remains supported and was not replaced. `chess-console` is an additional line-oriented stdin/stdout frontend with normal scrollback.

Supported launch commands remain:

```bash
bash scripts/dev.sh tui
bash scripts/dev.sh console
```

## Fail-closed interactive search policy

The completed shared application layer and both human frontends preserve the repository's fail-closed policy:

- no random legal-move fallback;
- no first-legal-move production fallback;
- no playable emergency/fallback `SearchResult`;
- no silent depth reduction or alternate-limit retry;
- no Python runtime fallback;
- no UCI subprocess fallback;
- no implicit opening-book/config/save discovery;
- stale search completions cannot mutate a new/restarted/abandoned game;
- returned engine moves are revalidated before application;
- search worker/channel/panic failures remain visible;
- operational cancellation paths resolve the active engine worker rather than detaching it;
- save failures remain visible and cannot report success.

The dedicated fallback/silent-failure audit also removed two convenience behaviors: raw-input echo as a fallback after an authoritative human move, and discarded secondary temp-file cleanup errors after save failure.

## Core implementation evidence

### Shared layer

- Run `31330821745`, job `93288662605`: focused `chess-app` formatting, locked check, strict Clippy, and tests succeeded.

### TUI preservation/migration

- Run `31331840727`, job `93291224158`: shared/TUI locked checks, strict Clippy, focused tests, and the complete existing real-PTY TUI acceptance suite succeeded.
- Resulting validated migration checkpoint: `6972824e3751c2825ee33b218314cd9ca2e3e8a5`.

### Console implementation and fail-loud audit

- Corrected console validation run `31332121813`, job `93291926330`: focused shared/console/TUI tests, real-process console acceptance, strict Clippy, formatting/locked checks, and TUI PTY acceptance succeeded.
- Dedicated fail-loud audit validation run `31332721254`, job `93293413075`: success.
- Fail-loud implementation checkpoint: `d540b6b3f7db80ed1935a16a5ba8de551f1c318b`.

### Checklist-coverage closure

- Coverage-closure run `31334008959`, job `93296723675`: focused shared/console/TUI tests, expanded real-process console acceptance, and TUI PTY acceptance succeeded.
- Exact supported developer-workflow run `31334062722`, job `93296869345`, against implementation source `591e1d304275674b8f6b83f11a83944853615ac4`: `bash scripts/dev.sh fast`, `console-smoke`, and `tui-pty-smoke` succeeded.

### Broader repository evidence

The first permanent green implementation freeze also passed the repository's broader suites:

- CI `31332859799`: x86 job `93293761321` success; ARM64 job `93293761303` success.
- Performance `31332859798`: success.
- Robustness `31332859817`: Miri subset, fuzz/corpus/libFuzzer, ASan/LSan, and TSan success.
- Android JNI `31332859740`: host JVM JNI contract, Android lint, API 35 JNI smoke, and instrumented lifecycle success.

A later temporary evidence-writing workflow was rejected by the permanent v0.2 strength audit because it had source-write permission. That workflow was removed rather than weakening the audit. The clean replacement CI subsequently passed.

## Real-process console acceptance

`crates/chess-console/tests/process_acceptance.rs` drives the actual executable with bounded timeouts and captured stdout/stderr. Coverage includes startup/menu quit, Human White with real engine response, Human Black engine-first flow, visible/non-mutating illegal moves, explicit board output, confirmation behavior, save success/failure/overwrite, Self-play controls, active-search quit, and EOF shutdown.

## Real-PTY console acceptance

The console now has a permanent real-PTY acceptance layer, exposed through:

```bash
bash scripts/dev.sh console-pty-smoke
```

It builds the actual `chess-console` binary and drives it through an OS pseudo-terminal. Objective Phase 19 behavior covered includes:

- real PTY launch and terminal resize;
- Human White and Human Black flows;
- board orientation for both colors;
- `board`, `moves`, `status`, `engine`, and `help`;
- malformed and illegal move visibility;
- real engine replies;
- resignation confirmation;
- save success, save failure, and overwrite confirmation;
- Self-play automatic start, pause, repeated one-ply step, resume, and quit;
- confirmed quit while engine activity is present;
- normal scrollback semantics with explicit rejection of alternate-screen enter/leave and screen-clear escape sequences.

Focused PTY verification after correcting one obsolete test expectation:

- Run `31338021176`.
- Job `93306954822`.
- `bash scripts/dev.sh console-pty-smoke`: success, 5/5 scenarios.

The test expectation defect did not reflect a console bug: `engine` correctly renders unavailable metric fields as `-`; `info unavailable` is reserved for a separate progress-line formatting path.

The permanent CI run `31338059357` then passed the same `Run console PTY acceptance` gate on clean source SHA `4875a7e29bf87d2e5026e3a25e419a4bbc3c93df`.

## TODO disposition

The original `docs/RUST_CONSOLE_TODO.md` is retained as the detailed historical implementation checklist. It is **not** mass-backfilled with checkmarks where evidence was never captured. In particular, the exact pre-extraction `fast`/TUI-PTY baseline commands were not recorded before extraction, so those historical baseline items cannot truthfully be marked complete after the fact.

`docs/RUST_CONSOLE_TODO_CLOSURE_2026-08-09.md` is the evidence-backed closure disposition for the checklist: implementation phases are automated-complete where proved; missing historical baseline execution is recorded as an evidence exception; subjective human UX review remains open.

## Remaining manual acceptance

No objective command-path or terminal-lifecycle correctness check needs to be repeated manually. The remaining human pass is deliberately limited to subjective UX judgment:

1. Launch `bash scripts/dev.sh console` in a normal terminal.
2. Confirm the board and normal scrollback are visually readable.
3. Confirm prompts, confirmations, errors, engine metrics, and move history are understandable at a glance.
4. Confirm the overall scrolling-console interaction feels acceptable for normal use.
5. Record terminal/OS, source SHA, and any UX notes.

Until that human judgment is recorded, the full milestone should be described as **automated-complete / human UX signoff pending**, not as having a fabricated manual acceptance result.
