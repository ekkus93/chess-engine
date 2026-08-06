# Rust Chess Engine v0.2 S2-13 Integration

**Status:** Complete
**Date:** 2026-08-06
**Integration baseline SHA:** `670e432b6aa7639ab525833a7d69d30f890eaf5c`
**Activation:** `false`
**Public adapter change:** none
**Next task:** S2-14

## Executive result

S2-13 integrates the accepted internal v0.2 identity, validation, profiling, and decision evidence into one permanent audit and one complete-variant control workflow. It does not activate a search candidate and does not expose an experimental policy through the safe Rust facade, UCI, C ABI, JNI, or Android.

That absence is deliberate. S2-5 through S2-10 produced rejected or deferred search candidates, S2-11 accepted only a behaviorally equivalent architecture-specific sliding-attack dispatch, and S2-12 deferred tablebases. There is therefore no accepted externally configurable feature for an adapter to expose. Adding a public option that was ignored, rejected internally, or silently mapped back to the baseline would violate the fail-visible contract.

The authoritative production engine remains package version `0.1.0` with the v0.1 baseline search policy and baseline evaluation weights. S2-14 will select and validate one exact inactive production candidate; S2-15 remains the separate activation boundary.

## Rust API and ownership decision

Existing production Rust APIs and defaults are unchanged. Candidate-policy entry points remain confined to internal search/tooling APIs that already require explicit policy, weights, caller-owned transposition tables, limits, and cancellation state.

No new facade request was needed. Consequently:

- no public request or result structure was added;
- no ownership or lifetime rule changed;
- no cancellation or stop behavior changed;
- no transposition-table sharing rule changed;
- no error was converted to an implicit fallback;
- no experimental policy can enter through the ordinary safe facade.

The internal complete-variant structures remain explicitly versioned:

- search-policy schema: `1`;
- authoritative v0.1 policy identifier: `5630315f504f4c31`;
- authoritative v0.1 policy checksum: `0c0769ef9d034770`;
- evaluation-weight schema: `1`;
- engine-variant identity schema: `1`;
- complete-variant report schema: `1`;
- complete-variant protocol identifier: `5641524956414c31`;
- historical weight-only candidate report schema: `1`;
- historical weight-only protocol identifier: `43414e4456414c31`.

## UCI decision

The UCI handshake continues to advertise exactly the supported options:

- `Hash`, spin, default `1`, range `1..65536` MiB;
- `CheckExtension`, check, default `false`;
- `OwnBook`, check, default `false`.

No PVS, LMR, null-move, futility, razoring, late-move-pruning, Syzygy, tablebase, generic policy, or candidate option is advertised. Unsupported settings are not accepted and ignored.

Existing subprocess coverage remains authoritative for handshake ordering, `isready`, position replacement, stop, quit, malformed commands, and stale-output suppression. Because S2-13 added no UCI option, no synthetic option test was added merely to satisfy a count.

## C ABI, JNI, and Android decision

The C ABI remains version `1`. Existing records, result codes, functions, opaque engine handles, opaque cancellation handles, struct-size validation, ABI-version validation, and all-or-nothing buffer ownership remain unchanged.

No additive ABI record was justified because external policy configuration is not supported. JNI exports and Kotlin declarations therefore remain unchanged as well. Panic containment and exact C/JNI error mapping continue to be enforced at their existing boundaries.

Permanent Android coverage remains independent and unchanged:

- host-JVM JNI contract tests;
- Kotlin/Android lint;
- ARM64 and x86_64 native libraries;
- API-35 instrumentation;
- off-main-thread search;
- explicit cancellation;
- repeated create/search/stop/destroy lifecycle;
- packaged opening-book asset behavior;
- bounded JNI performance and native-heap evidence.

## Permanent v0.2 audit

`scripts/task_v0_2_strength_audit.sh` is the consolidated v0.2 authority audit. It chains the completed v0.1 signoff, full-port, post-port, and S2-1 through S2-9 audits, then verifies the later decision records and integration boundary.

The audit checks:

- active specification, tracker, report, and supporting-document paths;
- exact policy, weight, engine-variant, complete-report, and legacy-report schema identities;
- the `activated=false` parser and runtime boundary;
- v0.1 package/default authority;
- absence of experimental policy exposure in UCI, C ABI, and JNI;
- exact supported UCI options and stable protocol tests;
- C ABI version, opaque ownership, panic code, and all-or-nothing lifecycle evidence;
- JNI and Android lifecycle/cancellation evidence;
- complete-variant control provenance and atomic report persistence;
- read-only permanent workflows and exact-SHA artifact naming;
- preservation of CI, ARM64, Android, robustness, performance, slow-perft, legacy strength, and complete-variant gates;
- absence of temporary S2-13 machinery;
- absence of Python or subprocess fallback in production runtime crates.

The audit runs inside permanent `CI` and is also available through `bash scripts/dev.sh strength-audit`.

## Complete-variant control tooling

`crates/chess-tools/src/bin/s2_13_variant_control.rs` provides a bounded internal control, not a production candidate. It requires:

- an explicit output directory that must not already exist;
- tier `smoke`, `development`, or `production`;
- protocol `fixed_nodes` or `clock_ms`;
- exact `S2_13_SOURCE_SHA`;
- explicit `S2_13_BUILD_IDENTITY`;
- explicit `S2_13_EXACT_INVOCATION`.

It generates a deterministic versioned 200-opening suite, constructs two complete identities that differ only by their recorded baseline/candidate control role, runs the shared correctness pre-gate and color-swapped match harness, round-trips the strict report parser, persists the report atomically, and emits a manifest with source, build, invocation, schemas, identities, checksums, decision, and `activated=false`.

`chess-tools variant-report-validate PATH` independently parses and validates a complete report before printing its schema, protocol, tier, pair/game counts, decision, activation state, and checksum.

Control evidence cannot authorize activation. Its two sides deliberately use the same policy and weights, and its role-specific complete identities exist only so the harness can prove scheduling, report, persistence, and artifact plumbing. S2-14 must use a behaviorally distinct, frozen candidate identity.

## Workflow and artifact ownership

`.github/workflows/variant-validation.yml` is read-only and runs on native x86-64 and ARM64.

- Relevant pushes and pull requests run one-pair fixed-node smoke controls.
- Manual runs select smoke, development, or production and fixed-node or clock protocol explicitly.
- The weekly schedule runs development fixed-node controls.
- The monthly schedule runs production clock controls.

Each architecture uploads:

`variant-validation-control-<tier>-<protocol>-<architecture>-<source-sha>`

The artifact contains:

- `s2-13-control-openings.tsv`;
- one strict `.report` file;
- `s2-13-control-manifest.tsv`;
- `summary.tsv`;
- `report-validation.tsv`.

The workflow records `github.sha` as the source identity, uses explicit build and invocation identities, validates the emitted report through the general CLI, requires `activated=false`, and runs `git diff --exit-code`. It has `contents: read` and cannot commit, push, update refs, rewrite policy defaults, or promote evidence automatically.

The historical `Strength` workflow remains separate and unchanged. It continues to exercise the earlier weight-only 200-pair/400-game control. The new workflow exercises the complete engine-variant schema. Neither substitutes for S2-14 candidate evidence.

## Documentation authority

The integrated documentation set is:

- `docs/RUST_CHESS_ENGINE_SEARCH_POLICY_AND_VARIANT_IDENTITY.md` — policy and complete identity;
- `docs/RUST_CHESS_ENGINE_VARIANT_VALIDATION.md` — complete match/report protocol;
- `docs/RUST_CHESS_ENGINE_V0_2_S2_4_SEE_2026-08-05.md` — SEE contract and oracle;
- `docs/RUST_CHESS_ENGINE_V0_2_S2_6_QUIESCENCE_2026-08-05.md` through the S2-10 reports — selectivity decisions and rejection/defer evidence;
- `docs/RUST_CHESS_ENGINE_V0_2_S2_11_PROFILING_2026-08-06.md` — architecture-specific performance decision;
- `docs/RUST_CHESS_ENGINE_V0_2_S2_12_SYZYGY_DECISION_2026-08-06.md` — tablebase configuration and failure contract for reconsideration;
- `docs/RUST_DEVELOPER_WORKFLOWS.md` — reproducible commands;
- `docs/RUST_GENERATED_ARTIFACT_POLICY.md` — artifact ownership and promotion rules;
- this report — S2-13 integration boundary.

## Disposition

S2-13 is complete. Internal candidate infrastructure is integrated under permanent, read-only, exact-identity controls. Production APIs and adapters are unchanged, all experimental and tablebase features remain inactive, no hidden fallback was introduced, and S2-14 remains the next authority task.
