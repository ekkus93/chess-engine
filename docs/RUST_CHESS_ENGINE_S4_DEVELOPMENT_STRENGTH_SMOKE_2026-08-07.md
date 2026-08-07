# Rust Chess Engine S4 Development Strength Smoke — 2026-08-07

**Status:** Complete diagnostic evidence — candidate rejected on development strength
**Source SHA:** `3fa718ce8db1337fdef7f02833bb87b15f658970`
**Workflow run:** `31203299756`
**Workflow job:** `92948219087`
**Artifact ID:** `9003757817`
**Artifact ZIP SHA-256:** `df04923ebc25fe811b5e8c945181b7ce3b1cdb02eefff5f6e1c422600b6de0f5`
**Candidate value checksum:** `520db5dd58086a8a`
**Activation:** `false`

## Purpose and disposition

S4-10 is diagnostic chess-strength evidence only. It compares the reproducible S4-9 evaluator candidate against the untouched v0.1 baseline under paired equal-resource protocols. Passing the workflow means the reports, correctness gates, games, provenance, and artifact publication completed successfully; it does **not** mean the candidate passed the chess-strength decision.

Both development reports returned `rejected_strength`. Therefore the S4 tuning method remains accepted for future experimental evaluator work, but this particular calibration candidate is rejected as positive playing-strength evidence and is not eligible for production promotion.

## Fixed-node protocol

- pairs / games: `16 / 32`;
- candidate W/D/L: `12 / 4 / 16`;
- unfinished: `0`;
- mean independent-pair score: `0.4375`;
- standard error: `8.98494110535326129e-02`;
- one-sided 95% lower confidence bound: `2.89710870349143224e-01`;
- illegal moves: `0`;
- crashes: `0`;
- time forfeits: `0`;
- infrastructure failures: `0`;
- report checksum: `23a1882590738160`;
- decision: `rejected_strength`;
- activation: `false`.

## Clock protocol

- pairs / games: `16 / 32`;
- candidate W/D/L: `14 / 2 / 15`;
- unfinished: `1`;
- mean independent-pair score: `0.484375`;
- standard error: `1.00697437694974801e-01`;
- one-sided 95% lower confidence bound: `3.18742454382700768e-01`;
- illegal moves: `0`;
- crashes: `0`;
- time forfeits: `0`;
- infrastructure failures: `0`;
- report checksum: `6a227dd717e60de0`;
- decision: `rejected_strength`;
- activation: `false`.

## Guardrails

The workflow reproduced the selected row before both match protocols and required value checksum `520db5dd58086a8a`, changed-parameter count `645`, the exact S4-9 train/held-out deltas, zero clipping, registry decision `advance`, one registered candidate, and `activated=false`.

The match harness used the baseline search policy on both sides, paired color-swapped openings, equal resources, independent transposition tables, correctness pre-gates, and fail-closed classifications for illegal moves, crashes, time forfeits, infrastructure faults, and excessive unfinished games.

No package/UCI version, production evaluator, search policy, public adapter, ABI, opening default, tablebase state, or activation state changed.
