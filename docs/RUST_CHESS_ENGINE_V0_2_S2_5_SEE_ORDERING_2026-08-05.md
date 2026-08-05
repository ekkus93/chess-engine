# Rust Chess Engine v0.2 S2-5 SEE Capture Ordering

**Status:** Implemented; inactive candidate under validation  
**Task:** S2-5  
**Starting master:** `5ccf5704ec1e1c94e03918b079be4abc4f37b038`  
**Core implementation:** `95d1917d986bc3f9ec808ba0f5f5a1a63619e5aa`

## Candidate boundary

S2-5 integrates the S2-4 Static Exchange Evaluation primitive into main-search and quiescence capture ordering only. It does not prune, reduce, extend, or omit a move. The production v0.1 policy remains the default for UCI, safe Rust, C ABI, JNI, and Android entry points.

The candidate is available only through the explicit controlled `SearchPolicySet::see_capture_ordering_candidate()` identity. Evidence reports always retain `activated=false`.

## Ordering contract

1. A valid transposition-table move remains first.
2. Previous-PV and promotion precedence remains unchanged.
3. Non-promotion captures are classified `winning > equal > losing`.
4. Captures in one class use signed SEE value, then existing MVV-LVA terms, then packed move identity as deterministic ties.
5. Quiet killer/history ordering is unchanged.
6. Every legal move remains in the ordered list.

SEE is calculated once per capture in the fixed-capacity ordering pass. The recursively retained move list contains only legal tokens and a bounded diagnostic summary; temporary sort keys are dropped before recursive search begins.

## Failure model

The ordering pass returns the existing typed `StaticExchangeError`. Alpha-beta exposes it as `AlphaBetaSearchError::StaticExchange`. Quiescence propagates the same error through the alpha-beta error boundary. Contradictory internal move state is never converted to MVV-LVA, a neutral SEE value, or an unvalidated fallback.

## Diagnostics

The candidate records exact counters for:

- SEE calls;
- winning capture classifications;
- equal capture classifications;
- losing capture classifications.

For every completed search, calls must equal the sum of the three classes. `see_prunes` and `quiescence_see_prunes` remain zero.

## Permanent evidence protocol

The focused S2-5 workflow runs on Linux x86-64 and native Linux ARM64. It provides:

- strict source audit, formatting, Clippy, and focused tests;
- full frozen S2-3 tactical-corpus baseline/candidate score parity;
- legal-PV replay and exact root position/history restoration;
- deterministic diagnostics and report checksums;
- an 8-pair fixed-node development comparison;
- an 8-pair clock-based development comparison on x86-64;
- seven-sample timing, node, qnode, cutoff, first-move-cutoff, SEE-class, and end-to-end allocation evidence;
- explicit baseline/candidate allocation counts and deltas without mislabeling the allocation-bearing iterative-deepening result path as zero-allocation;
- the repository's existing hard zero-allocation audit for designated core hot paths;
- read-only evidence artifacts bound to the exact source SHA and build identity.

A match result cannot activate the candidate. S2-5 records an independent disposition for later combination work; any production activation remains reserved for S2-14 and S2-15.
