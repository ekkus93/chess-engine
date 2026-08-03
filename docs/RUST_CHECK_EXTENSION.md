# Rust bounded check extension

Task 16.7 adds one explicit, optional selective-search feature. It is disabled by
default and is enabled for a limit-controlled request with
`SearchLimits::with_check_extension()`.

## Exact bound

A checking move may add one ply to its child search. Each root-to-leaf path starts
with a budget of exactly one extension. Applying it consumes the complete budget;
later checks on that path are searched at their nominal depth and recorded as
budget-exhausted decisions. A second extension cannot occur on the same path.

The extension is also refused when the extra ply would leave the supported
mate-score domain. Quiescence retains its independent bounded tactical-ply guard.

## Transposition safety

The remaining extension budget is path-dependent and is not represented by the
normal position Zobrist key. Therefore an extension-enabled request suppresses TT
score reuse and TT score storage. Complete-key verified legal moves may still be
used only as move-ordering hints. This prevents a baseline or differently budgeted
entry from bypassing the selective search contract.

Because the current extension search does not create compatible exact TT chains,
PV reconstruction validates and returns the exact root move but does not continue
through pre-existing table entries. The returned PV remains legal and bounded by
the completed nominal depth.

## Diagnostics

`SearchResult::check_extension_diagnostics()` reports request-wide counts for:

- eligible checking children;
- applied extensions;
- checks skipped after the one-ply path budget was consumed;
- checks blocked by the mate-score ply ceiling.

The limit controller records events as they happen, so diagnostics include work
from a depth interrupted by node, time, or explicit-stop cancellation.

## Compatibility

Existing fixed-depth and limit-controlled calls remain extension-free unless the
new builder is selected. Node, qnode, selective-depth, elapsed-time, cancellation,
root-restoration, aspiration exactness, and legal-PV semantics remain unchanged.
