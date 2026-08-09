# Rust Console TODO Closure — 2026-08-09

Companion checklist: `docs/RUST_CONSOLE_TODO.md`

Closure state: **automated implementation complete; subjective human terminal UX signoff pending**.

This document is the evidence-backed disposition of the original implementation checklist. It intentionally does not rewrite historical checkboxes where execution evidence was never captured.

## Exact automated closure

- Final clean automated source SHA: `4875a7e29bf87d2e5026e3a25e419a4bbc3c93df`.
- Permanent CI run: `31338059357`.
- Rust workspace quality job: `93307080189` — success.
- Linux ARM64 workspace build job: `93307080185` — success.
- Permanent console PTY acceptance step: success.
- Focused PTY run: `31338021176`.
- Focused PTY job: `93306954822` — success.
- Focused PTY command: `bash scripts/dev.sh console-pty-smoke` — 5/5 scenarios passed.

## Phase disposition

### Phase 0 — Establish exact baseline and implementation map

**Disposition: implementation-map complete; historical execution-evidence exception.**

The planning baseline and ownership boundaries were established and the final architecture matches the intended split. However, the exact pre-extraction `bash scripts/dev.sh fast` and pre-extraction TUI PTY executions were not recorded before extraction began. Those specific historical baseline boxes must remain unclaimed rather than being reconstructed after the fact.

The Ralph loop also discovered that adding the TODO itself triggered the repository's documentation authority audit because the new TODO was initially unclassified. That was repaired at `170b3dcc2c4223ee52205cfd68f87553b67c5d84` without weakening the audit.

### Phases 1–4 — Shared `chess-app`, worker/controller, text/save primitives

**Disposition: complete.**

Evidence includes focused shared-layer validation run `31330821745`, job `93288662605`, plus later strict Clippy/workspace/CI coverage. `chess-app` is safe Rust, presentation-neutral, and depends on engine-layer crates rather than frontend/protocol/runtime adapters.

### Phase 5 — Refactor `chess-tui` onto `chess-app`

**Disposition: complete.**

The TUI remains supported and preserves TUI-only menus, overlays, editing, layout, save UI state, and terminal lifecycle while delegating presentation-neutral game/search behavior to `chess-app`.

Evidence: run `31331840727`, job `93291224158`, including the complete existing TUI PTY suite. Validated migration checkpoint: `6972824e3751c2825ee33b218314cd9ca2e3e8a5`.

### Phases 6–13 — Console crate, commands, Human-vs-Engine, Self-play, lifecycle, confirmations, saves

**Disposition: complete.**

The Rust console is an additional scrolling stdin/stdout frontend. It supports both human colors, legal move validation, exact engine replies, commands, confirmations, explicit deterministic non-PGN saves, self-play pause/resume/step, EOF handling, and explicit active-worker resolution.

Evidence includes corrected console validation run `31332121813`, job `93291926330`, and dedicated fail-loud audit run `31332721254`, job `93293413075`.

### Phase 14 — Real-process console acceptance

**Disposition: complete.**

`crates/chess-console/tests/process_acceptance.rs` drives the real executable with bounded timeouts and captured stdout/stderr. Expanded checklist-coverage validation passed in run `31334008959`, job `93296723675`.

Coverage includes startup/menu, Human White/Black, real engine replies, illegal input, board output, confirmations, save success/failure/overwrite, Self-play controls, active-search quit, and EOF behavior.

### Phase 15 — Developer workflow and documentation

**Disposition: complete.**

Supported commands include:

```bash
bash scripts/dev.sh tui
bash scripts/dev.sh console
bash scripts/dev.sh console-smoke
bash scripts/dev.sh console-pty-smoke
```

The TUI and console remain separate supported frontends over shared application behavior; UCI remains a separate machine-facing protocol adapter.

Exact supported developer-workflow evidence: run `31334062722`, job `93296869345`, against implementation source `591e1d304275674b8f6b83f11a83944853615ac4`.

### Phase 16 — Dangerous-fallback and silent-failure audit

**Disposition: complete.**

The audit verified/repaired fail-closed behavior. No production random/first-legal fallback, silent depth reduction, alternate search retry, Python fallback, UCI subprocess fallback, implicit save destination, detached engine worker, or silent search-worker failure remains known.

Two convenience behaviors were removed during the audit:

1. raw-input display fallback after a successful authoritative human move;
2. discarded secondary temp-file cleanup errors after failed atomic save operations.

Validation: run `31332721254`, job `93293413075`, success.

### Phase 17 — Final local/supported validation

**Disposition: complete for the intended implementation source.**

- Intended implementation source: `591e1d304275674b8f6b83f11a83944853615ac4`.
- `bash scripts/dev.sh fast`: success in run `31334062722`, job `93296869345`.
- Focused console/process/TUI coverage: success in run `31334008959`, job `93296723675`.
- Broader permanent implementation freeze CI: `31332859799`, x86 `93293761321`, ARM64 `93293761303`, success.
- Performance: `31332859798`, success.
- Robustness: `31332859817`, success.
- Android JNI: `31332859740`, success.

### Phase 18 — Permanent CI and exact-SHA closure

**Disposition: complete.**

Final clean automated source SHA: `4875a7e29bf87d2e5026e3a25e419a4bbc3c93df`.

Permanent CI `31338059357` completed successfully on that exact SHA. The Rust workspace quality job `93307080189` and Linux ARM64 job `93307080185` both succeeded. The quality job explicitly passed the permanent console PTY acceptance gate along with authority audits, lockfile verification, formatting, workspace check, strict Clippy, full workspace tests, release perft, documentation, debug/release builds, UCI smoke, and differential oracle.

A temporary focused PTY verifier was used only to shorten feedback while fixing the PTY expectation and was removed afterward. The clean final source contains the permanent PTY gate in normal CI, not the temporary verifier.

### Phase 19 — Manual console acceptance

**Disposition: objective terminal behavior automated; subjective human UX judgment pending.**

The original Phase 19 mixed mechanically testable behavior with human judgment. The mechanically testable portion is now covered by a real OS PTY harness and permanent CI:

- real terminal/PTY launch;
- terminal resize;
- Human White and Human Black workflows;
- both board orientations;
- malformed and illegal move paths;
- `board`, `moves`, `status`, `engine`, and `help`;
- resignation confirmation;
- save success/failure/overwrite confirmation;
- Self-play automatic start, pause, repeated step, resume;
- confirmed quit during engine activity;
- normal scrollback with no alternate-screen enter/leave and no screen-clear sequence.

Focused PTY verification run `31338021176`, job `93306954822`, passed `bash scripts/dev.sh console-pty-smoke` with all five scenarios. Permanent CI `31338059357` then passed the same PTY gate on the clean source SHA.

The remaining human-only checks are:

- board/scrollback visual readability in a normal terminal;
- whether prompts and confirmation wording are easy to understand;
- whether error messages and engine metrics are understandable at a glance;
- overall interaction feel.

These must not be marked passed until a person actually runs the console and records the judgment.

## Final acceptance disposition

All objective implementation/correctness items in the milestone are supported by automated evidence, including shared-layer architecture, TUI preservation, Human White/Black console flows, exact search-result handling, fail-closed search policy, Self-play controls, save behavior, shutdown/EOF, real-process acceptance, real-PTY acceptance, strict linting, workspace correctness, perft/differential checks, robustness support, and permanent CI.

The milestone should therefore be described as:

> **Automated implementation complete and exact-SHA CI green; subjective human terminal UX signoff pending.**

No manual acceptance result has been fabricated, and the missing pre-extraction baseline executions remain explicitly recorded as historical evidence gaps rather than retroactively claimed.
