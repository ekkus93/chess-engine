# Rust Search Policy and Engine-Variant Identity

**Status:** S2-1 implementation contract
**Date:** 2026-08-05
**Program:** `docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md`
**Baseline:** `docs/RUST_CHESS_ENGINE_V0_2_BASELINE_2026-08-05.md`

## Purpose

S2-1 makes search semantics and complete engine-variant provenance explicit before any strength candidate is implemented. It does not enable SEE, PVS, LMR, pruning, tablebases, new weights, or any adapter-visible experiment.

The authoritative v0.1 engine remains the production default. Existing UCI, safe Rust facade, C ABI, JNI, and Android entry points continue to select that behavior without accepting experimental policy input.

## Search-policy schema

`chess-search::SearchPolicySet` binds:

- schema version;
- non-zero semantic identifier;
- complete typed policy parameters;
- canonical FNV-1a checksum.

The initial schema is `1`. The authoritative v0.1 policy identifier is `5630315f504f4c31`; its checksum is `0c0769ef9d034770`.

The policy records the current semantic families explicitly:

- full-window fail-soft negamax alpha-beta;
- clustered full-key transposition table;
- v0.1 TT/promotion/MVV-LVA/killer/history move ordering;
- stand-pat/capture/promotion/evasion quiescence;
- aspiration enablement and half-width;
- maximum quiescence ply;
- maximum optional check extensions per line;
- assigned future feature bits.

Only semantics already implemented by the engine may validate. Assigned future bits for SEE, PVS, LMR, null move, futility, razoring, delta pruning, and late-move pruning are represented in the checksum but fail validation when enabled. This prevents a configuration from claiming behavior that search silently ignores.

Malformed policy input fails before search mutation and, for the controlled caller-owned-table entry point, before table generation or diagnostics change.

## Canonical text format

`chess-tools` owns policy serialization because filesystem and text parsing remain outside the search core.

Commands:

```text
chess-tools policy-export
chess-tools policy-validate PATH
```

The marker is `chess-search-policy-v1`. Fields are explicit and order-independent when parsed. Serialization always emits canonical order. Unknown, duplicate, missing, malformed, unsupported, out-of-range, or checksum-inconsistent fields fail loudly.

No environment variable, conventional directory, startup scan, or implicit file may select a policy.

## Controlled search injection

The controlled Rust entry point is:

```text
iterative_deepening_search_with_limits_and_transposition_table_and_policy_and_weights
```

Existing public convenience functions delegate to `SearchPolicySet::baseline()` and `EvaluationWeights::DEFAULT` and retain their previous results and behavior.

A caller comparing different policy or evaluator identities must allocate separate transposition tables. Stored scores and moves may depend on both search semantics and evaluation weights; cross-identity table reuse is not permitted.

S2-1 does not expose policy configuration through UCI, the safe facade, C ABI, JNI, or Android.

## Engine-variant identity

`chess-tools::engine_variant::EngineVariantIdentity` binds the complete reproducibility surface:

- variant schema and identifier;
- exact 20-byte source commit;
- semantic engine version;
- search-policy schema, identifier, and checksum;
- evaluation-weight schema, identifier, and checksum;
- explicit opening-book state and, when enabled, implementation/data/checksum identity;
- explicit tablebase state and, when enabled, implementation/data/checksum identity;
- exact transposition-table size;
- exact target/toolchain/profile/features build identity;
- exact invocation;
- complete variant checksum.

Policy and weight identities are separate fields. A report can therefore state unambiguously whether a candidate changes search, evaluation, both, or neither.

Disabled optional capabilities are explicit. Enabled capabilities require non-zero implementation, data, and checksum identities. Missing or implicit provenance is invalid.

## Compatibility and activation boundary

S2-1 changes no production default and no package, UCI, ABI, or JNI version. It creates identity and controlled tooling only.

Future candidate tasks may add new policy fields or enable assigned feature bits only through a schema-compatible, validated implementation. Candidate acceptance still does not activate the policy. Activation remains a separate S2-15 commit and exact-SHA release gate.

## Validation requirements

Permanent tests and CI prove:

- the v0.1 policy checksum is stable;
- canonical and reordered text parse to the same identity;
- unknown, duplicate, missing, corrupt, out-of-range, and unsupported input fails;
- every semantic parameter change changes policy identity;
- explicit v0.1 search matches the existing default exactly;
- invalid policy fails before position, history, or TT mutation;
- policy and weight identities remain distinct in an engine variant;
- source, build, invocation, TT, book, tablebase, policy, and weight changes each change variant identity;
- no adapter exposes experimental policy configuration;
- no implicit policy discovery is present.
