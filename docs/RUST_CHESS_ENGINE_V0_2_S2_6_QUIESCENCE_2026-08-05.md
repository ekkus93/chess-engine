# Rust Chess Engine v0.2 S2-6 Quiescence Redesign

**Status:** Complete; both isolated candidates rejected for activation and remain inactive
**Task:** S2-6
**Starting master:** `4174c2bf69f4e30b49b669960c33ec506197d425`
**Candidate implementation:** `e778864e470fb967d215c0dc08fb864222802619`

## Frozen v0.1 contract

The current quiescence implementation resolves terminal and rule-draw states before tactical expansion. Outside check, it evaluates stand-pat, permits a fail-soft stand-pat beta cutoff, raises alpha when appropriate, and searches legal captures plus every legal promotion. In check, stand-pat is forbidden and every legal evasion is searched, including quiet evasions.

The tactical-ply guard returns stand-pat outside check. Reaching the same guard in check returns `QuiescenceDepthLimitReachedInCheck`; it never returns zero, static evaluation, or a partially searched score. Search cancellation and every error path must restore position, history, line length, and incremental Zobrist identity.

## SEE-pruning candidate

The first inactive S2-6 candidate preserves baseline MVV-LVA ordering and prunes only a non-promotion, non-en-passant capture whose SEE value is strictly less than `-100 cp`. It is disabled in check, in narrowed mate-score windows, when the node has only one legal tactical response, and when the move gives check. SEE failures propagate through the existing typed search error. Every evaluated SEE value is classified, and every omitted move increments `quiescence_see_prunes`.

## Delta-pruning candidate boundary

Delta pruning is represented by a separate identity that requires SEE pruning in the same policy. Its fixed margin is `200 cp`; it is evaluated only after a move survives SEE pruning. Initial exclusions match the SEE candidate and additionally require a typed captured-piece maximum gain. Delta attempts and prunes are counted separately.

The SEE-pruning candidate must receive a stable correctness, performance, and strength disposition before delta evidence is interpreted. The two candidates retain separate policy identities and reports.

Neither candidate is reachable from UCI, the default Rust facade, C ABI, JNI, or Android. All reports must retain `activated=false`.

## Final evidence and disposition

The exact validated candidate tree is `199c893ecd50601491612b8b196f6e93169a32fa`. Permanent workflow run `31049824797` passed on x86-64 and native ARM64 and preserved exact-head artifacts. The frozen 13-case tactical corpus and seven bounded independent-reference cases passed with aggregate checksum `702e3076191d8a25`. The corpus observed `4197` SEE prunes and `9344/1566` delta attempts/prunes while preserving scores, completed depths, legal PVs, and root state.

SEE pruning was evaluated first. Its fixed-node and clock development reports both returned `rejected_strength`, with every one of the 16 games in each protocol reaching the explicit maximum-ply boundary and no illegal moves, crashes, time forfeits, or infrastructure failures. Its seven-sample median runtime was 3.22% slower than baseline on x86-64 and 2.83% slower on ARM64. It is rejected for activation.

Only after that disposition was fixed was the SEE-plus-delta identity interpreted. Its independent fixed-node and clock reports also returned `rejected_strength` with all failure categories zero. Its median runtime was 8.47% slower on x86-64 and 7.75% slower on ARM64. It is separately rejected for activation.

Both implementations remain explicit controlled identities for future experiments, but neither is reachable from production adapters or defaults. All exact-head CI, robustness, performance, ARM64, host-JNI, Android lint, and API-35 instrumented JNI gates passed. `activated=false` remains authoritative.
