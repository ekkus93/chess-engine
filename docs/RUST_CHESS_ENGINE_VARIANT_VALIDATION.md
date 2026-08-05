# Rust Chess Engine Complete Variant Validation

**Status:** Authoritative S2-2 validation infrastructure
**Schema:** `1`
**Protocol identifier:** `0x5641_5249_5641_4c31`
**Activation state:** Always `false`

## Purpose

The complete variant validator compares two fully identified engine variants rather than assuming that evaluation weights are the only behavioral difference. It complements the existing weight-only candidate validator. The historical `chess-candidate-validation-v1` format, schema, parser, reports, and production threshold remain unchanged.

A complete variant identity binds:

- exact source commit and engine version;
- search-policy schema, identifier, and checksum;
- evaluation-weight schema, identifier, and checksum;
- opening-book state and data identity;
- tablebase state and data identity;
- transposition-table size;
- target, toolchain, profile, and feature identity;
- exact invocation.

The runtime policy and evaluator must match the recorded identity before correctness work, transposition-table allocation, or match play. Different policy or evaluator identities use independent transposition tables.

## Validation tiers

### Smoke

Smoke validation uses between 1 and 16 independent opening pairs. It proves bounded plumbing, report generation, parsing, identity binding, and correctness behavior. A successful smoke report emits `passed_smoke`; it cannot authorize activation.

### Development

Development validation uses at least 8 pairs and fewer than 200 pairs. It provides paired statistical evidence suitable for candidate iteration. A successful development report emits `passed_development`; it cannot authorize activation.

### Production

Production validation requires at least 200 independent opening pairs, producing at least 400 color-swapped games. Only a production report may emit `accepted_for_activation`. Even that disposition is evidence for a later human-reviewed activation task; the report itself remains `activated=false`.

## Equal-resource protocols

Every comparison explicitly selects one equal-resource protocol for both variants.

- `fixed_nodes:<nodes>` provides deterministic workload comparison independent of machine speed.
- `clock_ms:<milliseconds>` provides release-relevant throughput comparison under an equal wall-clock budget.

The report records both the protocol and its purpose. Both variants receive the same protocol, transposition-table budget, check-extension setting, draw policy, maximum ply, opening, pair seed, and color-swapped schedule.

## Correctness pre-gate

Match play is prohibited until the complete correctness pre-gate passes. The pre-gate records:

- authoritative perft through depth four;
- forced-mate fixtures;
- longest-survival fixtures;
- tactical move and legal principal-variation fixtures;
- repeated-search equivalence fixtures;
- infrastructure failures and exact diagnostics.

A chess correctness failure produces `rejected_correctness`. A harness or infrastructure failure produces `infrastructure_failure`. No games may exist in either report. This prevents a correctness defect from being diluted or concealed by match statistics.

## Opening and pairing rules

Opening rows are canonicalized and checked for semantic duplicates. Duplicate positions are rejected even when identifiers differ. Pair selection is deterministic from the recorded seed.

Each independent pair contains exactly two games using the same opening and pair seed:

1. candidate as White;
2. candidate as Black.

The pair average, not each individual game, is the independent statistical observation.

## Outcome classification

Completed chess games are classified as candidate win, draw, candidate loss, or unfinished at the maximum-ply boundary. Non-chess failures are typed separately:

- `illegal_move`;
- `crash`;
- `time_forfeit`;
- `infrastructure_failure`.

Failures include the faulting side and an exact diagnostic. They are never silently converted into wins, losses, draws, or unfinished games. Any typed game failure prevents strength acceptance.

## Statistical decision

The validator computes, over independent pair averages:

- mean candidate score;
- sample standard error;
- one-sided 95% lower confidence bound using the protocol's fixed critical value.

Acceptance requires the lower confidence bound to be **strictly greater** than `0.5 + minimum_score_margin`. Equality at the threshold is rejection. The unfinished-game rate must also remain at or below the configured ceiling.

Possible report decisions are:

- `rejected_correctness`;
- `infrastructure_failure`;
- `rejected_game_failure`;
- `rejected_unfinished_rate`;
- `rejected_strength`;
- `passed_smoke`;
- `passed_development`;
- `accepted_for_activation`.

No manual interpretation changes the serialized decision.

## Report integrity

The versioned report records complete baseline and candidate identities, source/build/invocation data, protocol, TT size, limits, opening checksum, seeds, draw policy, maximum ply, correctness evidence, every game, classified totals, statistics, decision, and `activated=false`.

Serialization is canonical and checksummed. Deserialization rejects unsupported schemas, unknown or malformed fields, incomplete reports, corrupted checksums, inconsistent counts, invalid pairing, identity mismatch, and non-finite statistics. Reports are written through a temporary file and atomically renamed only after complete validation.

## Activation boundary

Validation never changes runtime defaults, policy, weights, package version, UCI behavior, ABI/JNI behavior, or Android behavior. A report with `accepted_for_activation` remains inactive and requires the separate S2-15 activation gate. Smoke and development reports cannot emit that disposition.

## Weight-only compatibility

`crates/chess-tools/src/candidate_validation.rs` remains the authoritative weight-only validator with:

- schema `1`;
- identifier `0x4341_4e44_5641_4c31`;
- format marker `chess-candidate-validation-v1`;
- production minimum of 200 opening pairs.

S2-2 adds a separate complete-variant schema and does not reinterpret or rewrite prior weight-only reports.

## Permanent validation

The permanent source audit is:

```text
bash scripts/task_s2_2_variant_validation_audit.sh
```

The focused CI workflow runs the audit, formatting, strict Clippy, complete-variant tests, and legacy weight-only tests. Full workspace CI also executes the permanent audit before compilation and the complete all-target validation matrix.
