# Rust Chess Engine v0.2 S2-6 Quiescence Redesign

"
    "**Status:** In progress; baseline contract frozen and isolated candidates inactive
"
    "**Task:** S2-6
"
    "**Starting master:** `4174c2bf69f4e30b49b669960c33ec506197d425`

"
    "## Frozen v0.1 contract

"
    "The current quiescence implementation resolves terminal and rule-draw states before tactical expansion. Outside check, it evaluates stand-pat, permits a fail-soft stand-pat beta cutoff, raises alpha when appropriate, and searches legal captures plus every legal promotion. In check, stand-pat is forbidden and every legal evasion is searched, including quiet evasions.

"
    "The tactical-ply guard returns stand-pat outside check. Reaching the same guard in check returns `QuiescenceDepthLimitReachedInCheck`; it never returns zero, static evaluation, or a partially searched score. Search cancellation and every error path must restore position, history, line length, and incremental Zobrist identity.

"
    "## SEE-pruning candidate

"
    "The first inactive S2-6 candidate preserves baseline MVV-LVA ordering and prunes only a non-promotion, non-en-passant capture whose SEE value is strictly less than `-100 cp`. It is disabled in check, in narrowed mate-score windows, when the node has only one legal tactical response, and when the move gives check. SEE failures propagate through the existing typed search error. Every evaluated SEE value is classified, and every omitted move increments `quiescence_see_prunes`.

"
    "## Delta-pruning candidate boundary

"
    "Delta pruning is represented by a separate identity that requires SEE pruning in the same policy. Its fixed margin is `200 cp`; it is evaluated only after a move survives SEE pruning. Initial exclusions match the SEE candidate and additionally require a typed captured-piece maximum gain. Delta attempts and prunes are counted separately. The candidate remains blocked from disposition until SEE pruning has stable correctness, performance, and strength evidence.

"
    "Neither candidate is reachable from UCI, the default Rust facade, C ABI, JNI, or Android. All reports must retain `activated=false`.
"
    