# Rust Chess Engine v0.2 S2-12 Syzygy Tablebase Decision

**Status:** Complete — deferred
**Date:** 2026-08-06
**Disposition:** `deferred_insufficient_evidence`
**Activation:** `false`
**Decision baseline SHA:** `302e59b1c935703a35cfc3cb95b44e7229472950`
**Production integration:** none

## Executive decision

Syzygy integration is deferred. A maintained permissive probing backend exists, but no currently published Rust integration satisfies this repository's complete contract without substantial new unsafe/global-state wrapper work and dedicated cross-platform data/lifecycle evidence. Adding a partial contract crate, a dead dependency, or a wrapper that converts failures into absence would create exactly the hidden fallback risk this program prohibits.

Production therefore remains explicitly tablebase-disabled. No dependency, code path, filesystem lookup, environment lookup, UCI option, Rust request field, C ABI/JNI record, Android asset convention, TT behavior, engine identity, package version, or default changed.

## Dependency and provenance review

### `shakmaty-syzygy`

- Reviewed current crate release `0.28.1`, published 2026-06-19.
- The crate is mature, pure Rust, documents WDL/DTZ and custom-filesystem support, and is actively maintained.
- License is `GPL-3.0-or-later`, which is not acceptable as an ordinary dependency of this MIT-distributed engine without deliberately changing the distribution/license model.
- The 0.28 line also introduces a second chess position/move model and the 0.28.0 normalized manifest declares Rust `1.88`, while this workspace deliberately declares Rust `1.75`.
- Disposition: rejected for this integration path on license/toolchain/duplicate-model grounds, not on functional quality.

### Maintained `jdart1/Fathom`

- Reviewed MIT-licensed Fathom at commit `c9c6fef0dddc05d2e242c183acf5833149ab676d` (2025-12-24).
- It provides C99/C++ WDL and root DTZ APIs and documents Windows, Linux, and macOS support.
- Its process-global initialization and `TB_LARGEST` state require a project-owned synchronized lifecycle wrapper. Fathom explicitly returns success with `TB_LARGEST == 0` when no tables are found, so an enabled adapter must add a fail-visible no-data check.
- Android/NDK, dual-ABI packaging, 16 KiB page-size compatibility, repeated JNI lifecycle, and sanitizer/TSan behavior are not established by this repository's current evidence.
- Disposition: preferred future low-level backend candidate, but not accepted without a pinned vendoring/update policy and a separately reviewed safe wrapper.

### Published `fathom-syzygy` Rust wrapper

- Reviewed crate `0.1.0` and repository head `417562c482e0938981c2fbb2dacae2e018849cd7` (2023-01-02).
- It pins Fathom submodule commit `03882f25149661595d82ea1ed393d744f03c907f`, not current maintained Fathom.
- `Fathom::reload` ignores the boolean return from `tb_init`, so initialization failure can be reported as success.
- Probe methods return `Option`, collapsing `TB_RESULT_FAILED`, terminal/special outcomes, and decode failures into absence. This cannot distinguish `not_applicable` from configured data/probe failure.
- The wrapper owns process-global C state through a singleton guard and exposes no repository-grade concurrent/repeated lifecycle contract. Its ordinary prober also calls the root probe path.
- Disposition: rejected as published. Forking it would be a new implementation task, not a safe dependency update.

### Remote tablebase API

- A remote API introduces network availability, response-version, privacy, latency, cancellation, retry, and service-license policy. It cannot satisfy deterministic local search or explicit configured-data identity.
- Disposition: rejected for the engine core and production adapters.

### Project-owned Syzygy parser/prober

- Implementing the binary formats and probing algorithm directly would be a large correctness/security surface with no independent in-repository oracle or fixture lifecycle yet.
- Disposition: deferred; not justified when a permissive maintained C backend can be wrapped later.

## Frozen future architecture

A future implementation must be isolated in a dedicated `chess-tablebase` crate that depends on `chess-core`. `chess-core` and `chess-search` must not open paths, inspect environment variables, locate assets, or own platform filesystem policy.

The outward contract must provide:

- explicit enabled/disabled configuration;
- an explicitly supplied provider or exact path set;
- a caller-selected supported piece-count limit and probe policy;
- backend implementation/version/commit identity;
- canonical table-file names, sizes, and cryptographic digest manifest;
- typed `hit`, typed `not_applicable(reason)`, and typed provider/data/probe failures;
- deterministic root move conversion and tie-breaking over exact legal engine move identities;
- lifecycle synchronization that prevents `tb_free` while any probe is active;
- no panic or foreign unwind crossing Rust, C ABI, JNI, or Android boundaries.

A Fathom adapter must treat enabled configuration with `TB_LARGEST == 0` as a visible configuration/data error. It must never reinterpret `TB_RESULT_FAILED` as a miss or normal search.

## Frozen chess-semantics gates

Before integration, the implementation report must specify and test:

- the five WDL states from the side-to-move perspective;
- rule-50 clock handling and the distinction between unconditional wins/losses and cursed/blessed outcomes;
- DTZ sign, rounding/ambiguity, zeroing-move, en-passant, and promotion behavior;
- deterministic root ranking and tie policy;
- score/UCI reporting without falsely claiming a mate distance;
- initial prohibition on storing tablebase values in the existing TT until provider identity, rule-50 state, bounds, and reuse semantics are proven;
- known-position oracle fixtures plus missing, truncated, corrupt, incompatible, and changed-after-open data tests.

## Reconsideration evidence

Reconsideration requires all of the following:

1. A pinned maintained Fathom revision or another permissive backend with reviewed provenance.
2. A project-owned wrapper that preserves every initialization and probe failure distinctly.
3. Small real WDL/DTZ fixtures with source URLs, filenames, sizes, and digests committed or deterministically acquired by a manual evidence workflow.
4. Linux x86-64 and native ARM64 correctness, sanitizer, TSan, performance, and repeated-lifecycle evidence.
5. C ABI/JNI and Android API-35 dual-ABI lifecycle/error tests if the feature crosses those adapters.
6. Explicit UCI/API configuration only in the later additive integration task.
7. A functional-correctness disposition separate from any strength claim.

No strength match or probe benchmark was run for S2-12 because there is no behaviorally distinct tablebase candidate. An identical disabled-policy match would measure noise and would not validate the dependency, data, or chess semantics.
