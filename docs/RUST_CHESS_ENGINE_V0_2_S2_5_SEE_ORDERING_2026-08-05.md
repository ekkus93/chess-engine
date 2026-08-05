# Rust Chess Engine v0.2 S2-5 SEE Capture Ordering

**Status:** Complete; standalone candidate rejected for activation and retained inactive for later combination experiments
**Task:** S2-5
**Starting master:** `5ccf5704ec1e1c94e03918b079be4abc4f37b038`
**Core implementation:** `95d1917d986bc3f9ec808ba0f5f5a1a63619e5aa`
**Permanent evidence implementation:** `c17791c4a8e4ddfdd150cd0b77720fa48dc53cb4`
**Exact validated candidate:** `f5e4b1e1e630e5708444f9192a1436faac84090c`

## Final disposition

The standalone S2-5 candidate is **rejected for activation**. It preserved correctness and improved several ordering diagnostics, but both development match protocols returned `rejected_strength`, while seven-sample fixed-node timing was approximately 5.5% slower on both x86-64 and ARM64. The implementation remains available only through the explicit controlled policy identity for possible later combination experiments. Production defaults remain unchanged and `activated=false` in every report.

## Candidate boundary

S2-5 integrates the S2-4 Static Exchange Evaluation primitive into main-search and quiescence capture ordering only. It does not prune, reduce, extend, or omit a move. The production v0.1 policy remains the default for UCI, safe Rust, C ABI, JNI, and Android entry points.

The candidate is available only through `SearchPolicySet::see_capture_ordering_candidate()`. Its policy identifier/checksum is `5332355345454f31` / `96fd6e0c744e326a`; the authoritative v0.1 policy remains `5630315f504f4c31` / `0c0769ef9d034770`.

## Ordering contract

1. A valid transposition-table move remains first.
2. Previous-PV and promotion precedence remains unchanged.
3. Non-promotion captures are classified `winning > equal > losing`.
4. Captures in one class use signed SEE value, then existing MVV-LVA terms, then packed move identity as deterministic ties.
5. Quiet killer/history ordering is unchanged.
6. Every legal move remains in the ordered list.

SEE is calculated once per capture in the fixed-capacity ordering pass. The recursively retained move list contains only legal tokens and a bounded diagnostic summary; temporary sort keys are dropped before recursive search begins. This design is permanently guarded after the initial implementation exposed and fixed a recursive test-stack overflow.

## Failure model and diagnostics

The ordering pass returns the existing typed `StaticExchangeError`. Alpha-beta exposes it as `AlphaBetaSearchError::StaticExchange`, and quiescence propagates the same error. Contradictory internal move state is never converted to MVV-LVA, a neutral SEE value, or an unvalidated fallback.

The candidate records SEE calls plus winning, equal, and losing classifications. Calls must equal the sum of the three classes. `see_prunes` and `quiescence_see_prunes` remain zero.

## Exact correctness evidence

The frozen 13-case tactical corpus produced exact baseline/candidate score, mate-distance, completed-depth, best-move, legal-PV, root-position, history, and Zobrist parity. All 13 best moves matched; total SEE calls were `48186`; aggregate checksum was `950f8cb49057540f`; no move was pruned; `activated=false`.

## Strength evidence

The 8-pair fixed-node development comparison at 2,000 nodes recorded 2 wins, 2 losses, and 12 unfinished games. Mean and lower confidence bound were `0.5`; decision `rejected_strength`; checksum `1750c9ee353388aa`.

The 8-pair clock comparison at 10 ms recorded 1 win, 1 loss, and 14 unfinished games. Mean was `0.5`; decision `rejected_strength`; checksum `6a5bdb753e670799`.

Both reports recorded zero illegal moves, crashes, time forfeits, and infrastructure failures, and both retained `activated=false`.

## Performance and allocation evidence

On x86-64, seven samples measured baseline/candidate medians of `213586975 ns` / `225341022 ns`, ratio `1.055032`. On ARM64, medians were `173970839 ns` / `183633660 ns`, ratio `1.055543`.

The deterministic 40,000-node aggregate changed qnodes from `35620` to `35496`, beta cutoffs from `3265` to `3386`, and first-move cutoffs from `2715` to `2894`. Candidate SEE classifications were `21138` winning, `1648` equal, and `13727` losing.

The broad iterative-deepening measurement reported baseline/candidate maxima of `42/44` allocation calls and `27888/27906` bytes. Those are recorded as an explicit `+2` call / `+18` byte delta rather than mislabeled as zero-allocation. The repository's separate permanent designated-hot-path allocation audit passed with zero allocations on both architectures.

## Validation record

Focused run `31038429453` passed on the exact validated candidate SHA:

- x86-64 job `92416527069`; artifact `8943661186`; digest `cea5bc9b09e24251ba2ff1d06028e853d1ddc9060d9f0b2f38f801c036050d64`;
- ARM64 job `92416526991`; artifact `8943638318`; digest `2e6392e08481b014c246070f6911cc8b64e9f4e6e29edda9b9a2f30b135dfbb7`.

Rust CI run `31038429514`, robustness run `31038429455`, performance run `31038429707`, and Android/JNI run `31038429765` all passed on the same SHA. No lint suppression, ignored failure, downgraded gate, silent fallback, temporary helper, or write-capable permanent workflow remains in the validated candidate tree.
