# Rust Chess Engine v0.2 S2-3 Baseline

**Status:** Implemented; permanent exact-head validation required before tracker closure  
**Date:** 2026-08-05  
**Diagnostics implementation:** `db05a9243afbfae95971b7715ea70f48757d5144`  
**Tactical and control harness implementation:** `58015782deb0573810a61140446bde37d9cd9a3e`  
**Production activation:** `false`

## Purpose

S2-3 freezes the observable v0.1 search baseline before any strength heuristic is implemented. It adds diagnostics and evidence only. It does not enable SEE, PVS, LMR, null-move pruning, futility pruning, razoring, late-move pruning, tablebases, or any candidate policy. The authoritative v0.1 search policy and baseline evaluation weights remain unchanged.

## Search diagnostics

`SearchDiagnostics` is a fixed-size value type. It adds no heap-backed per-node storage and performs no I/O from the search tree.

Recorded v0.1 counters:

- main-search nodes;
- quiescence nodes;
- beta cutoffs;
- first-move beta cutoffs;
- quiescence beta cutoffs;
- quiescence first-move beta cutoffs;
- quiescence stand-pat cutoffs.

Reserved zero counters establish stable names for later isolated candidates:

- PVS zero-window searches and researches;
- SEE calls and SEE pruning;
- quiescence SEE and delta pruning;
- LMR reductions and researches;
- null-move attempts and cutoffs;
- frontier futility and razor activity;
- late-move pruning.

Completed exact search results use checked accumulation and return a typed `SearchDiagnosticOverflow` naming the affected counter. Request-wide observation hooks cannot return errors, so they saturate only the affected counter and set an explicit `overflowed` bit. Overflow is therefore never silent.

The diagnostics include a deterministic semantic checksum. Tests establish that:

- node totals equal main plus quiescence counts;
- qnode totals equal the quiescence count;
- first-move cutoffs never exceed total cutoffs;
- reserved counters remain zero under the v0.1 policy;
- repeated searches produce identical scores, moves, PVs, node counts, and diagnostics;
- root position and history remain unchanged.

Transposition-table and check-extension diagnostics remain separately authoritative and unchanged.

## Versioned tactical corpus

The committed corpus is `fixtures/search_baseline_v1.tsv`, format marker `CHESS_SEARCH_BASELINE\t1`.

It freezes one explicit row for each required category:

- mate in one;
- mate in two or more;
- longest survival in a forced loss;
- stalemate;
- repetition;
- fifty-move draw;
- seventy-five-move draw;
- promotion race;
- en-passant tactic;
- quiet defense;
- zugzwang-sensitive pawn ending;
- poisoned capture;
- legal principal-variation replay.

Exact best-move sets are required only where the position has a stable exact contract. Other rows require a legal exact search result and a fully legal PV rather than freezing one incidental path. Every row checks root position/history restoration, invariant validity, diagnostic overflow, and reserved-counter inactivity.

The harness records:

- exact source SHA;
- explicit build identity;
- corpus schema and checksum;
- policy and weight checksums;
- best move, score, nodes, qnodes, selective depth, cutoff counters, and diagnostic checksum per row;
- aggregate checksum;
- `activated=false`.

## Identical-policy strength controls

The S2-3 harness uses the permanent S2-2 complete-engine-variant validator rather than a duplicate match implementation.

It deterministically derives 200 semantically distinct opening lines from the starting position. The exact generated opening file and checksum are preserved with each run. Both sides use:

- `SearchPolicySet::baseline()`;
- `EvaluationWeightSet::baseline()`;
- disabled opening book and tablebases;
- independent one-MiB transposition tables;
- the same fixed-node budget, draw policy, maximum ply, seed schedule, and build identity.

The baseline and candidate complete identities differ only in explicit role provenance, which is necessary because the S2-2 report rejects identical complete identity checksums. Their search policy, evaluator, resources, and chess behavior are identical.

Three controls run:

| Tier | Pairs | Games | Fixed nodes/move | Maximum plies | Required result |
|---|---:|---:|---:|---:|---|
| Smoke | 1 | 2 | 64 | 6 | exact symmetry, inactive, rejected strength |
| Development | 8 | 16 | 64 | 6 | exact symmetry, inactive, rejected strength |
| Production | 200 | 400 | 1 | 4 | exact symmetry, inactive, rejected strength |

The bounded games intentionally end at the maximum-ply boundary. Every result is therefore an unfinished 0.5 score, making the expected independent pair distribution exact rather than probabilistic:

- mean pair score: `0.5`;
- sample standard error: `0.0`;
- one-sided lower confidence bound: `0.5`;
- decision: `rejected_strength` because acceptance requires a strict value greater than `0.5 + minimum_score_margin`;
- activation: `false`.

Illegal moves, crashes, time forfeits, and infrastructure failures must all remain zero. Reports use the canonical S2-2 schema, strict checksum validation, and atomic caller-selected paths.

The complete evidence directory is generated twice and compared recursively. Any nondeterministic byte fails the workflow.

## Performance baseline

S2-3 intentionally reuses the existing Task 24 performance harness and does not rewrite its reference files or semantic checksums.

The permanent `Performance` workflow records seven-sample distributions on both Linux x86-64 and native Linux ARM64 and preserves exact-SHA artifacts. Its rows cover:

- legal move generation and perft;
- evaluation and quiescence;
- fixed-node search;
- transposition-table behavior;
- allocation audits;
- C ABI, safe Rust facade, and JNI adapter overhead.

Future SEE and candidate-search metrics must use new explicitly named rows or a new schema. They must not reinterpret an existing row, silently replace a reference, or change a current checksum under the same semantic name.

## Reproduction

```bash
cargo fmt --all -- --check
cargo check --locked --workspace --all-targets --all-features
cargo clippy --locked --workspace --all-targets --all-features -- -D warnings
cargo test --locked --workspace --all-targets --all-features
cargo build --locked --release -p chess-tools --bin s2_3_baseline

export S2_3_SOURCE_SHA="$(git rev-parse HEAD)"
export S2_3_BUILD_IDENTITY='rustc-1.97.1|x86_64-unknown-linux-gnu|release|locked'
target/release/s2_3_baseline s2-3-evidence-a
target/release/s2_3_baseline s2-3-evidence-b
diff -ru s2-3-evidence-a s2-3-evidence-b

cargo build --locked --release -p chess-tools --bin performance
target/release/performance allocation-audit
target/release/performance baseline 7 1
```

The source SHA and build identity are mandatory inputs. The harness does not read ambient policy, weights, opening files, books, tablebases, or configuration.

## Activation boundary

S2-3 is baseline instrumentation and evidence. It cannot activate a candidate and cannot alter any production default. Every generated manifest and variant report records `activated=false`.
