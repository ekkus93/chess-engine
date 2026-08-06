# Rust Chess Engine v0.2 Strength Program TODO

**Status:** In progress
**Date:** 2026-08-05
**Branch:** `master`
**Specification:** `docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_SPEC_2026-08-05.md`
**Completed v0.1 tracker:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`
**Completed v0.1 report:** `docs/RUST_CHESS_ENGINE_PORT_IMPLEMENTATION_REPORT.md`
**Completed post-port review:** `docs/RUST_CHESS_ENGINE_POST_PORT_REVIEW_FIX_TODO_2026-08-04.md`
**Planning baseline:** `51cb4fa1b281bd1a6a7d7af20ff3f4a8d99a4e51`
**S2-0 engine baseline:** `1e28defb8835119881f2b03ea60dc5589bec01be`
**S2-0 baseline record:** `docs/RUST_CHESS_ENGINE_V0_2_BASELINE_2026-08-05.md`

## S2-0 implementation record

- Exact engine/search baseline SHA: `1e28defb8835119881f2b03ea60dc5589bec01be`.
- Baseline documentation commit: `ff83eb506d28c039292189dbf5bc69a1cdddfd78`.
- Rust CI baseline: run `30986317659`; jobs `92241821565` and `92241821561`; success.
- Performance baseline: run `30986317662`; jobs `92241817180` and `92241817103`; artifacts `8922221747` and `8922217103`; success.
- Strength status: no exact-head run was expected because the workflow is scheduled/manual and push-path-limited; latest 200-pair/400-game control run `30960468240` succeeded with `rejected_strength` and `activated=false`.
- Authority state: v0.2 TODO active; v0.1 tracker/definitions completed authority; post-port TODO historical; every top-level TODO-named document classified and unclassified additions fail the permanent authority audit.
- Search inventory: full-window fail-soft alpha-beta, tactical quiescence, aspiration recovery, bounded TT, MVV-LVA/killer/history ordering, request-local limits/cancellation, and one optional bounded check extension. SEE, PVS, LMR, null move, futility, razoring, late-move pruning, tablebases, NNUE, and parallel search are absent from production code.
- No labelled open P0 or P1 issue was found.
- No engine semantics, defaults, weights, adapters, ABI/JNI contracts, or performance references changed in S2-0.
- Exact S2-0 validation SHA: `c38b44d392f4c0de346f4e770cdfcc61f67479f2`.
- Exact Rust CI: run `30988357600`; jobs `92248343009` and `92248343120`; success.
- Exact performance: run `30988357606`; jobs `92248327612` and `92248327574`; artifacts `8923032392` and `8923029162`; success.
- Exact robustness: run `30988357637`; jobs `92248377273`, `92248377334`, and `92248377522`; success.
- S2-0 tracker closure is documentation-only and maps to the unchanged validated engine/search tree above.

## S2-1 implementation record

- Disposition: complete; identity infrastructure accepted for subsequent controlled validation work; activation remains false.
- Implementation SHA: `7e4e1aacb0160b96683646a29058ddd783043a6e`.
- Exact validation SHA: `d645aa625800238fba8d0be0cb7066ee56884120`.
- Search-policy schema: `1`.
- Authoritative v0.1 policy identifier: `5630315f504f4c31`.
- Authoritative v0.1 policy checksum: `0c0769ef9d034770`.
- Evaluation-weight identity remains baseline schema `1`, identifier `424153454c494e45`, checksum `d2cca7ae10ec6e34`.
- Added typed fail-closed search policy, canonical policy text I/O, controlled explicit-policy iterative search, complete engine-variant identity, permanent tests, documentation, audit, and focused CI workflow.
- Existing convenience search entry points continue to use the exact v0.1 policy and `EvaluationWeights::DEFAULT`.
- UCI, safe Rust facade, C ABI, JNI, Android, package version, and production defaults expose no experimental policy input and remain unchanged.
- Assigned future feature bits are identity-visible but validation rejects enabling SEE, PVS, LMR, null move, futility, razoring, delta pruning, and late-move pruning before their implementation tasks.
- Different policy or evaluator identities require separate caller-owned transposition tables.
- Permanent focused identity run `30995963744`, job `92272978556`: audit, formatting, strict Clippy, explicit v0.1 parity, policy schema, canonical text, variant identity, and CLI round-trip passed.
- Exact Rust CI run `30995963711`: x86-64 job `92273019216` and native ARM64 job `92273019344`; all audits, locked checks, strict Clippy, all-target tests, release perft, rustdoc, builds, UCI smoke, and differential oracle passed.
- Exact performance run `30995963716`: x86-64 job `92272978703`, artifact `8926152440`; ARM64 job `92272978813`, artifact `8926154375`; zero-allocation and reference-budget gates passed.
- Exact robustness run `30995963722`: fuzz job `92272978711`, sanitizer job `92272978801`, Miri job `92272978866`; all passed.
- Exact Android/JNI run `30995963800`: host JVM job `92272988350`, Android lint job `92272988457`, API-35 instrumented JNI job `92272988476`; all passed.
- No strength match was required or used because S2-1 changes identity/control infrastructure and preserves exact v0.1 production search behavior.
- Discovered integration defects were fixed at source or workflow level; no lint suppression, ignored failure, downgraded gate, silent fallback, implicit discovery, or temporary helper remains in the validated implementation tree.

## S2-2 implementation record

- Disposition: complete; generalized complete-engine-variant validation infrastructure accepted for later candidate work; activation remains false.
- Implementation SHA: `7077c0b2b97b17f1d0dd6ef42fc59e830dcc8069`.
- Exact validation SHA: `ead3be20f7ba027d3c6ab9629ca0e094e6e9eb0f`.
- Complete-variant report schema: `1`; protocol identifier: `5641524956414c31`.
- The historical weight-only report remains schema `1`, identifier `43414e4456414c31`, format `chess-candidate-validation-v1`, and production minimum 200 pairs.
- Added complete identity binding for source SHA, engine version, policy, weights, book/tablebase state, TT size, build identity, and exact invocation.
- Added bounded smoke, paired development, and production tiers; production requires at least 200 independent opening pairs / 400 color-swapped games.
- Added equal-resource `fixed_nodes` and `clock_ms` protocols with recorded purpose, shared limits/configuration, and independent variant transposition tables.
- Added correctness pre-gates for authoritative perft, forced mate, longest survival, tactical/legal-PV behavior, and repeated-search equivalence; failed correctness or infrastructure prevents all match games.
- Added semantic opening deduplication, deterministic seeded scheduling, color-swapped pairs, pair-average statistics, sample standard error, and a one-sided 95% lower confidence bound using the existing z-value.
- Acceptance is fail-closed: the lower bound must strictly exceed `0.5 + minimum_score_margin`, unfinished games have a separate ceiling, ties/inconclusive evidence reject, and only production may emit `accepted_for_activation`.
- Wins, draws, losses, unfinished games, illegal moves, crashes, time forfeits, and infrastructure failures are separate; typed failures are never silently converted into chess results.
- Reports are canonical, checksummed, strictly parsed, atomically persisted through caller-selected same-directory paths, and always serialize `activated=false`.
- Permanent focused run `31002053527`, job `92293045464`: source audit, formatting, strict Clippy, complete-variant tests, and legacy weight-only compatibility passed.
- Exact Rust CI run `31002053507`: x86-64 job `92293040865` and native ARM64 job `92293040807`; all audits, locked checks, strict Clippy, all-target tests, release perft, rustdoc, builds, UCI smoke, and differential oracle passed.
- Exact performance run `31002053545`: x86-64 job `92293062822`, artifact `8928690363`; ARM64 job `92293062784`, artifact `8928694029`; zero-allocation and reference-budget gates passed.
- Exact robustness run `31002053571`: Miri job `92293065411`, sanitizer job `92293065540`, fuzz job `92293065551`; all passed.
- Exact Android/JNI run `31002053564`: API-35 instrumented JNI job `92293579404`, host JVM job `92293579417`, Android lint job `92293579446`; all substantive gates passed.
- No production strength match was required or used because S2-2 adds inactive validation infrastructure and does not change production search, evaluation, adapters, package version, or defaults.
- Integration failures were fixed at source or audit-workflow level. No lint suppression, ignored failure, downgraded gate, silent fallback, implicit configuration discovery, write-capable staging workflow, or temporary payload remains.

## S2-3 implementation record

- Disposition: complete; the authoritative v0.1 search, tactical, performance, and identical-policy strength baselines are frozen for later isolated candidate comparisons; activation remains false.
- Deterministic diagnostics implementation SHA: `db05a9243afbfae95971b7715ea70f48757d5144`.
- Tactical corpus and strength-control harness implementation SHA: `58015782deb0573810a61140446bde37d9cd9a3e`.
- Exact validation SHA: `9a56a27552b5032860802db8fe5d82d65ac93d2d`.
- Authoritative v0.1 policy identifier/checksum: `5630315f504f4c31` / `0c0769ef9d034770`.
- Authoritative baseline weight identifier/checksum: `424153454c494e45` / `d2cca7ae10ec6e34`.
- Added fixed-size allocation-free search diagnostics for main nodes, qnodes, selective depth, beta cutoffs, first-move cutoffs, quiescence cutoffs, and stand-pat cutoffs while preserving existing TT and check-extension diagnostics.
- Reserved stable zero counters for PVS, SEE, quiescence SEE/delta pruning, LMR, null move, frontier futility/razoring, and late-move pruning. Exact-result aggregation fails with a typed counter-specific overflow; request-wide observation saturates the affected counter and sets an explicit overflow bit.
- Permanent tests prove node/count consistency, reserved-counter inactivity, deterministic checksums, exact repeated-search equivalence, legal PVs, and root position/history restoration. No per-node heap storage or tracing was added.
- Frozen tactical corpus schema `1` contains 13 required categories. Corpus checksum: `f9632e70214cd44a`; aggregate tactical result checksum: `6ab1d87d467d0a2b`; every row passed and records `activated=false`.
- Deterministically generated 200-opening control suite checksum: `1cf5dfa5ebbe0bc5`.
- Identical-policy smoke control: 1 pair / 2 games; mean `0.5`, sample standard error `0.0`, lower bound `0.5`, `rejected_strength`, `activated=false`; report checksum `68902aa6b915986e`.
- Identical-policy development control: 8 pairs / 16 games; mean `0.5`, sample standard error `0.0`, lower bound `0.5`, `rejected_strength`, `activated=false`; report checksum `4cdf0d802b6295e8`.
- Identical-policy production control: 200 pairs / 400 games; mean `0.5`, sample standard error `0.0`, lower bound `0.5`, `rejected_strength`, `activated=false`; report checksum `4df2e4004f4d960a`.
- Permanent focused run `31009413307`, job `92317414834`, artifact `8931829296` (`s2-3-baseline-9a56a27552b5032860802db8fe5d82d65ac93d2d`, artifact digest `6ef8a47a30387fc5038451317cd12cdb6cfeb0c43c2e17603c03357c42aacc2b`): audit, formatting, strict Clippy, focused tests, release build, two byte-identical full evidence generations, production control, and artifact preservation passed.
- Exact Rust CI run `31009414734`: x86-64 workspace-quality job `92317486379` and native ARM64 job `92317486396`; locked checks, strict Clippy, all-target tests, release perft, rustdoc, debug/release builds, UCI smoke, and differential oracle passed.
- Exact performance run `31009412488`: x86-64 job `92317412062`, artifact `8931750887`; ARM64 job `92317411999`, artifact `8931753848`; seven-sample distributions, zero-allocation audits, and unchanged reference-budget comparisons passed.
- Exact robustness run `31009413508`: fuzz job `92317415090`, Miri job `92317415217`, sanitizer/TSan job `92317415237`; all passed.
- Exact Android/JNI run `31009412535`: API-35 instrumented JNI job `92317424809`, host JVM job `92317424817`, Android lint job `92317424840`; all passed.
- Existing Task 24 performance rows, semantic checksums, x86-64/ARM64 reference files, UCI behavior, safe Rust facade, C ABI, JNI, Android, package version, search policy, evaluation weights, and production defaults remain unchanged.
- Integration defects were fixed at their source: exact staging witnesses, Clippy-clean tests, a mistakenly terminal proposed zugzwang fixture, canonical `key=value` report parsing, and one audit path overreach. No lint suppression, ignored failure, downgraded gate, silent fallback, implicit discovery, temporary payload, or write-capable permanent workflow remains.

## S2-4 implementation record

- Disposition: complete; the standalone allocation-free SEE primitive is accepted for later controlled ordering or pruning candidates, while production search remains unchanged and activation remains false.
- Starting `master` SHA: `f5a4217ca55a8b8d469b3e23e727f85706ba9aff`.
- Core implementation SHA: `cbffe1287f7a0c54eae63de71c18211fd75d9503`.
- Robustness/performance evidence implementation SHA: `995529687ce5fb3ab28ef37d30cecccfcbfcbaa8`.
- Exact validation SHA: `ffae5bf54555ae3f1224135010ef4ea71633056e`.
- SEE schema: `1`; policy identifier: `53454556414c3031`; semantic checksum: `0367223104886e8e`; maximum alternating recapture plies: `64`.
- Stable exchange-accounting values are pawn `100`, knight `320`, bishop `330`, rook `500`, queen `900`, and king `20000`; they are deliberately independent of tuned evaluation weights.
- Added a typed fail-loud `chess-core` SEE API for ordinary captures, en passant, quiet promotions, and capture promotions. Ordinary quiet moves, double pawn pushes, castling, contradictory occupancy/geometry/promotion state, illegal king exposure, capacity exhaustion, and arithmetic overflow cannot silently become neutral scores.
- The production algorithm uses fixed local bitboards and bounded recursion, removes the actual en-passant pawn before attack recomputation, reveals rook/queen and bishop/queen x-rays, excludes pinned attackers and illegal king recaptures, chooses least valuable legal attackers deterministically, evaluates all promotion identities, and never mutates the caller's position or allocates heap memory.
- The independent oracle is structurally different: it uses authoritative legal move generation plus make/unmake after every exchange, filters legal recaptures to the contested square, applies the same deterministic least-value/source ordering contract, permits a side to decline a losing continuation, and compares curated plus deterministic generated positions.
- Permanent regressions cover winning/equal/poisoned exchanges, multiple attackers and defenders, rook and bishop x-rays, pins, illegal king recaptures, en-passant occupancy, quiet promotions, all four capture-promotion identities, color symmetry, exact root restoration, malformed input, capacity bounds, and deterministic semantic identity.
- Focused SEE run `31017544295`: x86-64 job `92345450893`, artifact `8935144456`, digest `85eaaa82b3e0c71064d79c922ddc3beb7f1155f024b7781737965c2465dfd2fc`; ARM64 job `92345450837`, artifact `8935145060`, digest `ff3818f13144a60cf18beb07c2fd66e9f2891430f46ca5030b1eb0467c64ba7d`; audit, formatting, strict Clippy, focused core/oracle/fuzz/Miri tests, release builds, seven-sample distributions, zero allocations, and stable result/semantic checksums passed. Median `see.exchange` time was `115 ns` on x86-64 and `86 ns` on ARM64 for this run.
- Exact Rust CI run `31017544604`: x86-64 workspace-quality job `92345452117` and native ARM64 job `92345451984`; all inherited and S2-4 audits, locked checks, strict Clippy, all-target tests, release perft, rustdoc, debug/release builds, UCI smoke, and differential oracle passed.
- Exact performance run `31017544299`: x86-64 job `92345451159`, artifact `8935143722`; ARM64 job `92345451033`, artifact `8935142184`; existing seven-sample distributions, zero-allocation audits, semantic checksums, and reference budgets remained green and unchanged.
- Exact robustness run `31017545028`: fuzz job `92345454104`, Miri job `92345454070`, sanitizer/TSan job `92345454065`; the dedicated SEE corpus/campaign, strict fuzz checks, Miri SEE regression, ASan/LSan SEE suite, lifecycle sanitizers, and TSan cancellation gate passed.
- Exact Android/JNI run `31017544444`: API-35 instrumented JNI job `92346311916`, host JVM job `92346311727`, Android lint job `92346311811`, artifact `8935371724`; all passed.
- Exact tracker authority run `31017544324`, job `92345450787`; all inherited audits, S2-3 baseline audit, standalone S2-4 audit, and pre-closure progression checks passed.
- No strength match was required or used because S2-4 adds an inactive standalone primitive and does not change search decisions, evaluation weights, policy identity, UCI, safe Rust facade, C ABI, JNI, Android, package version, performance references, or production defaults.
- Integration defects were repaired at their source or validation boundary: temporary payload transcription, fuzz-workspace formatting order, workflow-token scope separation, and an audit witness for a stronger `const` API. No lint suppression, ignored failure, downgraded gate, silent fallback, implicit discovery, temporary payload, or write-capable permanent workflow remains in the validated tree.

## Status rules

- `[x]` means complete with implementation, documentation, and exact evidence.
- `[ ]` means incomplete, unverified, blocked, deferred, rejected without evidence, or not started.
- A candidate task may close as accepted, rejected, revised, or deferred, but its disposition must be explicit and evidence-backed.
- An implemented or accepted candidate remains inactive until a separate activation task completes.
- Documentation-only closure commits must identify the unchanged validated implementation SHA.
- GitHub Actions is the authoritative execution environment when local and CI evidence differ.

## S2-5 implementation record

- Disposition: complete; the standalone SEE capture-ordering candidate is **rejected for activation** because both development comparisons returned `rejected_strength` and the measured fixed-node search path was slower on x86-64 and ARM64. The implementation remains inactive and may be reused only as an explicitly identified component in later combination experiments.
- Starting `master` SHA: `5ccf5704ec1e1c94e03918b079be4abc4f37b038`.
- Core implementation SHA: `95d1917d986bc3f9ec808ba0f5f5a1a63619e5aa`.
- Permanent evidence implementation SHA: `c17791c4a8e4ddfdd150cd0b77720fa48dc53cb4`.
- Exact validated candidate SHA: `f5e4b1e1e630e5708444f9192a1436faac84090c`.
- Candidate policy identifier/checksum: `5332355345454f31` / `96fd6e0c744e326a`; authoritative v0.1 policy remains `5630315f504f4c31` / `0c0769ef9d034770`.
- Ordering contract: TT move first; previous-PV and promotion precedence preserved; captures ordered `winning > equal > losing`, then signed SEE, existing MVV-LVA, and packed move identity; quiet killer/history ordering unchanged; no legal move is removed.
- SEE is computed once per capture in a fixed-capacity construction pass. Temporary sort keys are discarded before recursive search retains the ordered legal-token list, permanently fixing the stack-overflow defect discovered by the first parity run.
- Contradictory internal SEE state propagates as typed `StaticExchangeError` / `AlphaBetaSearchError::StaticExchange`; there is no neutral score, MVV-LVA substitution, ignored error, or silent fallback.
- Exact diagnostics count SEE calls and winning/equal/losing classifications. Calls equal the sum of classes; `see_prunes` and `quiescence_see_prunes` remain zero.
- Frozen 13-case tactical parity: every exact score, mate distance, completed depth, best move, legal PV replay, root position, history, and Zobrist invariant matched; `differing_best_moves=0`, total SEE calls `48186`, aggregate checksum `950f8cb49057540f`, `activated=false`.
- Fixed-node development comparison: 8 pairs / 16 games at 2,000 nodes; candidate wins `2`, losses `2`, unfinished `12`; mean/lower bound `0.5`; zero illegal moves, crashes, time forfeits, or infrastructure failures; `rejected_strength`; checksum `1750c9ee353388aa`; `activated=false`.
- Clock development comparison: 8 pairs / 16 games at 10 ms; candidate wins `1`, losses `1`, unfinished `14`; mean `0.5`; zero illegal moves, crashes, time forfeits, or infrastructure failures; `rejected_strength`; checksum `6a5bdb753e670799`; `activated=false`.
- Seven-sample x86-64 distribution: baseline median `213586975 ns`, candidate `225341022 ns`, ratio `1.055032`; nodes `40000/40000`, qnodes `35620/35496`, beta cutoffs `3265/3386`, first-move cutoffs `2715/2894`.
- Seven-sample ARM64 distribution: baseline median `173970839 ns`, candidate `183633660 ns`, ratio `1.055543`; the same deterministic node, qnode, cutoff, and SEE-class counts were reproduced.
- End-to-end iterative-deepening allocation evidence is reported honestly: baseline/candidate maxima `42/44` calls and `27888/27906` bytes, a delta of `+2` calls / `+18` bytes. The separate permanent designated-hot-path audit remained zero-allocation on both architectures.
- Exact focused run `31038429453`: x86-64 job `92416527069`, artifact `8943661186`, digest `cea5bc9b09e24251ba2ff1d06028e853d1ddc9060d9f0b2f38f801c036050d64`; ARM64 job `92416526991`, artifact `8943638318`, digest `2e6392e08481b014c246070f6911cc8b64e9f4e6e29edda9b9a2f30b135dfbb7`; all focused correctness, deterministic evidence, strength, performance, allocation, and audit gates passed.
- Exact Rust CI run `31038429514`: x86-64 workspace-quality job `92416444304` and native ARM64 job `92416444199`; all audits, lockfile/metadata checks, formatting, strict Clippy, all-target/all-feature tests, release perft, rustdoc, debug/release builds, UCI smoke, and differential oracle passed.
- Exact robustness run `31038429455`, performance run `31038429707`, and Android/JNI run `31038429765` all passed on the same validation SHA.
- The Task 14.5 exclusion audit was repaired at source so it recognizes interleaved test-only helpers and the explicit SEE ordering fields while ignoring comments/string literals during lexical strategic-evaluator checks. No exclusion was weakened.
- Production UCI, safe Rust, C ABI, JNI, Android, package version, weights, v0.1 policy, and defaults remain unchanged. No first-party lint suppression, ignored failure, downgraded gate, implicit discovery, temporary helper, or write-capable permanent workflow remains in the validated candidate tree.

## S2-6 implementation record

- Disposition: complete; the isolated SEE-pruning candidate and the separately identified SEE-plus-delta candidate are both **rejected for activation**. Both remain typed, inactive controlled candidates; production search and all adapters continue to use the authoritative v0.1 policy.
- Starting `master` SHA: `4174c2bf69f4e30b49b669960c33ec506197d425`.
- Core implementation SHA: `e778864e470fb967d215c0dc08fb864222802619`.
- Permanent evidence implementation SHA: `3f59152650be324348008f5b7dfb248f33f6a7dd`.
- Exact validated candidate SHA: `199c893ecd50601491612b8b196f6e93169a32fa`.
- Baseline policy identifier/checksum: `5630315f504f4c31` / `0c0769ef9d034770`.
- SEE-pruning policy identifier/checksum: `5332365345455031` / `3638a5c288517f61`.
- SEE-plus-delta policy identifier/checksum: `53323644454c5031` / `9f2ec2d471425fb7`.
- Baseline contract remains exact: terminal and rule-draw resolution precede the tactical guard; stand-pat is allowed only outside check; checked nodes search every legal evasion; non-checked nodes search captures and every promotion; guard exhaustion in check remains typed `QuiescenceDepthLimitReachedInCheck`; cancellation and all error paths restore position, history, line length, and Zobrist identity.
- SEE pruning uses a strict `< -100 cp` threshold and excludes in-check nodes, promotions, en passant, checking moves, mate-score windows, and sole tactical responses. SEE/internal contradictions propagate as typed errors; there is no unpruned, MVV-LVA, neutral-score, or static-evaluation fallback.
- Delta pruning is a separate identity evaluated only after the SEE candidate received its disposition. It requires SEE pruning, uses a fixed `200 cp` margin plus typed captured-piece maximum gain, and initially excludes in-check nodes, promotions, checking moves, mate-score domains, and sole tactical responses. Attempts and prunes are counted independently.
- Frozen 13-case tactical parity passed for baseline, SEE, and delta identities. Seven explicitly bounded independent reference-quiescence comparisons passed. Aggregate checksum: `702e3076191d8a25`; total SEE prunes: `4197`; delta attempts/prunes: `9344/1566`; every report records `activated=false`.
- Fixed-node SEE comparison: 8 pairs / 16 games at 2,000 nodes; wins/losses `0/0`, unfinished `16`; no illegal moves, crashes, time forfeits, or infrastructure failures; `rejected_strength`; x86-64 report checksum `44edc6685584dc71`.
- Clock SEE comparison: 8 pairs / 16 games at 10 ms; wins/losses `0/0`, unfinished `16`; no illegal moves, crashes, time forfeits, or infrastructure failures; `rejected_strength`; checksum `c1dff6ae8f6ab694`.
- SEE was therefore rejected before delta interpretation. Delta fixed-node comparison: 8 pairs / 16 games, wins/losses `0/0`, unfinished `16`, `rejected_strength`, checksum `14ab1519be67e186`. Delta clock comparison: 8 pairs / 16 games, wins/losses `0/0`, unfinished `16`, `rejected_strength`, checksum `883ef0ea8c0eff10`. All failure categories remained zero.
- Seven-sample x86-64 distribution: baseline median `208614279 ns`; SEE `215341536 ns` (ratio `1.032247`); delta `226274520 ns` (ratio `1.084655`). Deterministic nodes remained `40000`; qnodes were `35620/35293/35047`; beta cutoffs `3265/3517/3745`; first-move cutoffs `2715/2928/3144`.
- Seven-sample ARM64 distribution: baseline median `173743305 ns`; SEE `178666293 ns` (ratio `1.028335`); delta `187212494 ns` (ratio `1.077523`). The same deterministic node, qnode, cutoff, SEE, and delta counts were reproduced.
- End-to-end allocation maxima are reported honestly: baseline `42` calls / `28400` bytes; SEE `44` / `28418` (`+2` / `+18`); delta `48` / `28484` (`+6` / `+84`). The separate designated recursive hot-path audit remained zero-allocation on x86-64 and ARM64.
- Permanent focused run `31049824797`: x86-64 job `92454143665`, artifact `8948044156`, digest `a263c00f7cf4aaf4ba0134832038f559290917d3cb091bcb3f0d04ad089f3b8f`; ARM64 job `92454143629`, artifact `8948004424`, digest `08b7cf67f4ad6b5185b22749448c4a35e973a320f0c5158ac5b540e95a6aadbc`; all focused correctness, duplicate deterministic evidence, strength, timing, allocation, and artifact gates passed.
- Exact Rust CI run `31049824721`: x86-64 workspace-quality job `92454153203` and native ARM64 job `92454153087`; all audits, locked checks, strict Clippy, all-target/all-feature tests, release perft, rustdoc, debug/release builds, UCI smoke, and differential oracle passed.
- Exact robustness run `31049825021`: fuzz job `92454158035`, Miri job `92454158042`, sanitizer/TSan job `92454158158`; all passed.
- Exact performance run `31049824916`: x86-64 job `92454205219` and ARM64 job `92454205258`; zero-allocation and reference-budget gates passed.
- Exact Android/JNI run `31049824819`: API-35 instrumented JNI job `92454146368`, host JVM job `92454146421`, Android lint job `92454146646`; all passed.
- Production UCI, safe Rust facade, C ABI, JNI, Android, package version, evaluation weights, authoritative v0.1 policy, and defaults remain unchanged. No first-party lint suppression, ignored failure, downgraded gate, silent fallback, implicit discovery, temporary helper, or write-capable permanent workflow remains in the validated candidate tree.

## S2-7 implementation record

- Disposition: complete; standalone PVS activation rejected; the typed candidate remains inactive for possible later combination experiments.
- Core implementation SHA: `c5ee43810355deaef062c1f7903bc410df2d883e`.
- Evidence-harness SHA: `06c20e219ad54227ee9c9ff4b7e43df2ee6d560d`.
- Exact validation SHA: `a6bd183065e77605c55459e750ac0ea2ffbd9dd3`.
- Candidate policy identifier/checksum: `5332375056533031` / `ef730d158002ccfa`.
- Baseline policy identifier/checksum: `5630315f504f4c31` / `0c0769ef9d034770`.
- Added first-move full-window search, later-move one-centipawn null-window search, mandatory exact re-search on strict alpha improvement below beta, typed window-construction failure, exact attempt aggregation, and PVS probe/re-search diagnostics.
- Full-window score, depth, best-move, mate-distance, longest-survival, aspiration recovery, cancellation/limits, legal PV, TT semantics, and position/history/Zobrist restoration remain exact. No unverified narrow result is reported or stored as exact.
- Deterministic parity: 13 cases, zero differing best moves, 62,133 zero-window searches, 310 re-searches, checksum `aeee18b6a927f146`; repeated x86-64 evidence was byte-identical and native ARM64 semantics matched.
- Fixed-node development: 8 pairs at 2,000 nodes per move; 2 candidate wins, 0 draws, 0 losses, 14 unfinished; no illegal moves, crashes, time forfeits, or infrastructure failures; `rejected_strength`; checksum `b05aa8e4b464ee2f`.
- Clock development: 8 pairs at 10 ms; 1 candidate win, 0 draws, 0 losses, 15 unfinished; no illegal moves, crashes, time forfeits, or infrastructure failures; `rejected_strength`; checksum `84bb4b1a050370f3`.
- Seven-sample x86-64 release median ratio: `1.010052`; candidate approximately 1.005% slower while reducing qnodes from 35,620 to 35,176.
- Seven-sample ARM64 release median ratio: `1.014173`; candidate approximately 1.417% slower.
- Exact permanent validation run `31059515279`: x86-64 job `92484209606` and native ARM64 job `92484209677`; audit, formatting, strict Clippy, complete search/evidence tests, byte-identical deterministic evidence, clock evidence, zero-allocation audit, seven-sample distributions, and artifact upload passed.
- x86-64 artifact `8951692759`, digest `cbef3feb8816de99899b66fa29d68c047e94e22b9015607a7a7c0553993d08f4`; ARM64 artifact `8951682899`, digest `2295ec2fe5a024d48b336f00dc2b39b6216f7be8fd05cacbcc4c99de1df369cb`.
- Production UCI, safe Rust facade, C ABI, JNI, Android, package version, evaluation weights, authoritative v0.1 policy, and defaults remain unchanged. No silent fallback, implicit discovery, committed generated evidence, temporary helper, or write-capable permanent workflow remains.

## Program guardrails

- Work directly on `master` unless the user explicitly requests a branch.
- Do not reopen the completed Rust port or post-port cleanup.
- Keep the v0.1 search policy and baseline weights authoritative until a separate activation commit passes.
- Do not combine unrelated search heuristics into one candidate.
- Do not accept a candidate because it is faster if fixed-node strength or correctness regresses.
- Do not accept a candidate because it scores better if it violates correctness, robustness, portability, lifecycle, or unfinished-game limits.
- Do not add first-party lint suppression, ignored failure, output filtering, downgraded gate, or silent fallback.
- Do not automatically rewrite performance references, weights, policy defaults, or report decisions.
- Do not expose experimental behavior through UCI, C ABI, JNI, or Android unless explicitly required and versioned.
- Do not implicitly discover books, weights, datasets, tablebases, or configuration.
- Preserve exact make/unmake restoration, mate-score semantics, draw/history behavior, cancellation, and panic containment.
- Every discovered bug receives a source fix and permanent regression before the loop advances.

---

# Program summary

| Task | Scope | Status |
|---:|---|---|
| S2-0 | Authority cleanup and exact baseline inspection | **Complete** |
| S2-1 | Versioned search-policy and engine-variant identity | **Complete** |
| S2-2 | Generalized strength-validation infrastructure | **Complete** |
| S2-3 | Baseline strength, diagnostics, and performance capture | **Complete** |
| S2-4 | Correct allocation-free Static Exchange Evaluation | **Complete** |
| S2-5 | SEE capture-ordering candidate | **Complete — standalone rejected; inactive for combinations** |
| S2-6 | Quiescence redesign candidates | **Complete — SEE and delta rejected; inactive** |
| S2-7 | Principal Variation Search candidate | **Complete — standalone rejected; inactive** |
| S2-8 | Late Move Reductions candidate | **Not started** |
| S2-9 | Optional null-move pruning decision/candidate | **Not started** |
| S2-10 | Optional frontier and quiet-move pruning candidates | **Not started** |
| S2-11 | Fresh profiling and measured hot-path decisions | **Not started** |
| S2-12 | Optional Syzygy tablebase decision/integration | **Not started** |
| S2-13 | API, UCI, ABI/JNI, Android, CI, and documentation integration | **Not started** |
| S2-14 | Production candidate selection and validation | **Not started** |
| S2-15 | Separate activation and v0.2 release gate | **Not started** |
| S2-16 | Final audit, report, and closure | **Not started** |

---

# Task S2-0: Authority cleanup and exact baseline inspection — COMPLETE

## S2-0.1 Confirm repository state

- [x] Record the exact current `master` SHA before implementation.
- [x] Confirm the specification and this TODO exist at their required paths.
- [x] Confirm the completed v0.1 tracker remains complete.
- [x] Confirm the completed post-port review TODO remains complete.
- [x] Confirm no unresolved P0/P1 correctness issue exists.
- [x] Record current Rust toolchain, LLVM version, runner images, package versions, ABI/JNI versions, weight identity, and search defaults.

## S2-0.2 Correct TODO authority

- [x] Update `docs/LEGACY_TODO_INDEX.md` so this v0.2 TODO is active.
- [x] Reclassify the completed post-port review TODO as a completed historical record.
- [x] Preserve the v0.1 tracker and definitions as completed authority documents.
- [x] Update `scripts/task_post_port_review_fix_audit.sh` or replace its authority portion with a permanent generalized TODO-authority audit.
- [x] Ensure every top-level `docs/*TODO*.md` file is classified.
- [x] Ensure an unclassified future TODO-named file fails CI.

## S2-0.3 Inventory current search behavior

- [x] Record current alpha-beta, quiescence, move-ordering, TT, iterative-deepening, aspiration, extension, limit, and cancellation behavior.
- [x] Confirm whether PVS, SEE, LMR, null move, futility, razoring, and late-move pruning are absent or partially present.
- [x] Record current search diagnostics and missing counters.
- [x] Record all public/internal entry points that assume the built-in search policy.
- [x] Record all tests that compare reference search, alpha-beta, iterative deepening, and legal PVs.

## S2-0.4 Baseline smoke validation

- [x] Run the permanent v0.1/post-port audits.
- [x] Run formatting, locked check, strict Clippy, and all-target/all-feature tests.
- [x] Run release perft depth four and the differential oracle.
- [x] Record current performance and strength workflow status.
- [x] Do not mark later implementation tasks complete using historical evidence alone.

**S2-0 gate:** Complete. Authority is unambiguous, the exact baseline is recorded, current search behavior is inventoried, and permanent exact-head validation passed before semantic changes.

---

# Task S2-1: Versioned search-policy and engine-variant identity — COMPLETE

## S2-1.1 Define policy schema

- [x] Add a typed search-policy structure in the appropriate search/tooling layer.
- [x] Assign a versioned schema and semantic identifier.
- [x] Represent the authoritative v0.1 policy exactly.
- [x] Represent experimental switches and parameters without ambient globals.
- [x] Reject unknown, duplicate, missing, out-of-range, or incompatible fields.
- [x] Produce a deterministic checksum covering schema, identifiers, flags, thresholds, and tables.
- [x] Ensure malformed policy input fails before search mutation or TT allocation where practical.

## S2-1.2 Preserve defaults

- [x] Existing production entry points continue to use the v0.1 policy.
- [x] Existing UCI defaults remain unchanged.
- [x] Existing safe Rust facade, C ABI, JNI, and Android behavior remain unchanged.
- [x] No environment variable or implicit file changes policy.
- [x] Experimental policy injection is initially restricted to controlled Rust tools/tests.

## S2-1.3 Engine-variant identity

- [x] Define an engine-variant identity binding source SHA, engine version, search policy, evaluation weights, book state, tablebase state, TT configuration, build identity, and exact invocation.
- [x] Candidate and baseline identities must differ whenever behavior differs.
- [x] Candidate reports must distinguish search-policy changes from weight changes.
- [x] Separate TT instances must be used when policy/evaluator identity can affect stored scores or moves.

## S2-1.4 Tests

- [x] v0.1 policy checksum is stable.
- [x] Equivalent policy text/order produces one canonical identity.
- [x] Every semantic change changes the checksum.
- [x] Corruption, unsupported versions, and unsafe combinations fail loudly.
- [x] Existing default search results remain unchanged with the explicit v0.1 policy.

**S2-1 gate:** Complete. A stable explicit engine/search identity exists, malformed and unsupported policy input fails closed, explicit v0.1 search is deterministic-equivalent to the existing default, and production adapters/defaults remain unchanged.

---

# Task S2-2: Generalized strength-validation infrastructure — COMPLETE

## S2-2.1 Generalize candidate scope

- [x] Extend or complement the existing weight-candidate validator to compare complete engine variants.
- [x] Preserve the existing weight-only protocol and reports.
- [x] Define a versioned engine-variant validation report.
- [x] Record exact baseline and candidate identities and checksums.
- [x] Record source SHA, toolchain/build identity, command, TT size, limits, opening suite, seeds, draw policy, and maximum ply.

## S2-2.2 Validation tiers

- [x] Define bounded smoke protocol.
- [x] Define development paired protocol.
- [x] Define production protocol with at least 200 independent opening pairs and 400 games.
- [x] Only production reports may emit `accepted_for_activation`.
- [x] Every report retains `activated=false`.

## S2-2.3 Correctness pre-gate

- [x] Run authoritative perft before games.
- [x] Run forced-mate and longest-survival fixtures.
- [x] Run candidate-specific tactical/equivalence fixtures.
- [x] Reject correctness failures before any games.
- [x] Record `rejected_correctness` distinctly from infrastructure failure.
- [x] Never let favorable games compensate for a correctness failure.

## S2-2.4 Pairing and statistics

- [x] Require semantically distinct openings.
- [x] Reject duplicate canonical opening lines under different names.
- [x] Play both colors from each opening.
- [x] Treat pair averages as independent statistical units.
- [x] Compute mean, sample standard error, and one-sided 95% lower confidence bound with the existing z-value.
- [x] Require the lower bound to exceed `0.5 + minimum_score_margin` strictly.
- [x] Track unfinished games separately and enforce the ceiling.
- [x] Treat tied/inconclusive evidence as rejection.

## S2-2.5 Failure classification

- [x] Record wins, draws, losses, unfinished games, illegal moves, crashes, time forfeits, and infrastructure failures separately.
- [x] Do not score an infrastructure failure as a chess result unless a symmetric predeclared protocol explicitly requires it.
- [x] Atomic report persistence uses caller-selected paths and checksums.
- [x] Partial/corrupt reports are rejected.

## S2-2.6 Fixed-node and clock protocols

- [x] Add at least one fixed-node engine-variant protocol.
- [x] Add at least one clock-based engine-variant protocol.
- [x] Record why each is used.
- [x] Ensure both engines receive identical resources/configuration within a protocol.

**S2-2 gate:** Complete. Complete engine variants can be compared reproducibly under fixed-node or clock protocols, fail closed before or during match play, preserve the existing weight-only protocol, and remain inactive.

---

# Task S2-3: Baseline strength, diagnostics, and performance capture — COMPLETE

## S2-3.1 Search diagnostics

- [x] Add or inventory main nodes and qnodes.
- [x] Add selective depth and beta-cutoff counters.
- [x] Add first-move cutoff counter.
- [x] Preserve existing TT diagnostics.
- [x] Reserve deterministic counters for PVS, SEE, quiescence pruning, LMR, null move, and frontier pruning.
- [x] Define counter overflow behavior and tests.
- [x] Ensure counters do not change search results.
- [x] Avoid per-node allocation or expensive tracing.

## S2-3.2 Baseline benchmark extensions

- [x] Record current seven-sample x86-64 and ARM64 distributions.
- [x] Record legal generation, quiescence, fixed-node search, TT, allocation, and adapter metrics.
- [x] Add benchmark rows required for future SEE and candidate comparisons without changing current semantic checksums incorrectly.
- [x] Preserve zero-allocation hot-path requirements.
- [x] Preserve old reference artifacts before any intentional update.

## S2-3.3 Baseline strength reports

- [x] Run deterministic smoke self-play of v0.1 against itself to verify protocol symmetry.
- [x] Run the selected development baseline protocol.
- [x] Run or schedule a production control proving an identical policy cannot pass the strength margin.
- [x] Preserve exact opening suite/checksum, seeds, limits, and reports.
- [x] Verify mean pair score and confidence behavior are symmetric for the control.

## S2-3.4 Baseline tactical corpus

- [x] Freeze a versioned candidate-search correctness corpus.
- [x] Include mate in 1, mate in 2+, longest survival, stalemate, repetition, fifty/seventy-five move, promotion races, en-passant tactics, quiet defense, zugzwang-sensitive endings, poisoned captures, and legal-PV replay.
- [x] Record exact expected values where semantics require parity.
- [x] Record pass/fail properties where pruning may legitimately change node paths.

**S2-3 gate:** Complete. The authoritative v0.1 policy has exact deterministic search diagnostics, a frozen tactical corpus, seven-sample x86-64 and ARM64 performance evidence, and symmetric smoke/development/200-pair production controls while remaining inactive.

---

# Task S2-4: Correct allocation-free Static Exchange Evaluation — COMPLETE

## S2-4.1 Design contract

- [x] Define stable piece values used only for exchange accounting.
- [x] Define SEE sign and side-to-move/capturing-side convention.
- [x] Define valid move categories.
- [x] Define typed errors for non-capture misuse and move/position contradiction.
- [x] Define bounded local storage and arithmetic domain.
- [x] Document that SEE is an estimate/order primitive, not a legal search replacement.

## S2-4.2 Core implementation

- [x] Model ordinary captures.
- [x] Model en-passant occupancy removal correctly.
- [x] Model promotion value changes for quiet/capture promotions as applicable.
- [x] Reveal rook/queen x-rays after occupancy removal.
- [x] Reveal bishop/queen x-rays after occupancy removal.
- [x] Handle pawn attack direction exactly.
- [x] Handle king recapture legality conservatively and correctly.
- [x] Choose least valuable attackers deterministically.
- [x] Do not mutate the caller's `Position`.
- [x] Allocate no heap memory.

## S2-4.3 Independent oracle

- [x] Implement an independent brute-force legal capture-sequence oracle in tests/tools.
- [x] Keep the oracle structurally different from the production swap algorithm.
- [x] Compare curated fixtures.
- [x] Compare deterministic generated legal positions and captures.
- [x] Preserve any mismatch as a minimized permanent regression.

## S2-4.4 Focused fixtures

- [x] Undefended winning capture.
- [x] Equal exchange.
- [x] Poisoned capture.
- [x] Multiple attackers/defenders.
- [x] X-ray rook/queen sequence.
- [x] X-ray bishop/queen sequence.
- [x] Pinned or illegal king recapture.
- [x] En-passant occupancy case.
- [x] Quiet promotion accounting if supported by the API.
- [x] Capture-promotion accounting for all four promotion identities.
- [x] Symmetry and no-mutation properties.

## S2-4.5 Robustness and performance

- [x] Add SEE fuzz target or corpus replay.
- [x] Add Miri coverage.
- [x] Add zero-allocation benchmark row.
- [x] Add deterministic semantic checksum.
- [x] Run sanitizers as applicable.

**S2-4 gate:** Complete. SEE matches an independent legal capture oracle, is deterministic, fail-loud, non-mutating, allocation-free, and remains inactive outside controlled tooling.

---

# Task S2-5: SEE capture-ordering candidate — COMPLETE

## S2-5.1 Define the candidate

- [x] Add an explicit inactive policy flag and parameter set.
- [x] Keep TT-move priority first.
- [x] Preserve promotion ordering.
- [x] Define exact capture classes, such as winning/equal/losing, using SEE.
- [x] Define deterministic tie-breaks inside each class.
- [x] Keep the candidate ordering-only; do not prune moves here.

## S2-5.2 Integrate safely

- [x] Compute SEE once per capture per ordering pass where practical.
- [x] Avoid heap allocation and repeated board reconstruction.
- [x] Integrate in both main-search tactical ordering and quiescence ordering where specified.
- [x] Preserve legal move sets exactly.
- [x] Propagate SEE failure explicitly; do not silently substitute MVV-LVA.

## S2-5.3 Add diagnostics

- [x] Count SEE calls.
- [x] Count winning/equal/losing classifications.
- [x] Count ordering cutoffs and first-move cutoffs.
- [x] Record deterministic diagnostics checksum.
- [x] Keep pruning counters zero.

## S2-5.4 Correctness validation

- [x] Exact root-score parity versus baseline on the frozen corpus.
- [x] Mate-distance parity.
- [x] Legal-PV replay.
- [x] Position/history/Zobrist restoration.
- [x] Deterministic repeated-run parity.
- [x] Baseline behavior remains unchanged when the flag is off.

## S2-5.5 Performance and allocation validation

- [x] Compare nodes and qnodes at fixed depth/nodes.
- [x] Compare first-move cutoffs and cutoff distribution.
- [x] Measure x86-64 and ARM64 timing distributions.
- [x] Audit allocation behavior in the measured search path.
- [x] Reject the candidate if SEE cost dominates ordering gain without strength benefit.

## S2-5.6 Strength validation

- [x] Run deterministic fixed-node development comparison.
- [x] Run clock-based development comparison where release relevance warrants it.
- [x] Record unfinished games and all failure categories separately.
- [x] Record one disposition: accept independently, reject, or retain only for later combination experiments.

**S2-5 gate:** Complete. The ordering implementation is exact, typed, deterministic, no-prune, and inactive. Standalone activation is rejected; the controlled candidate is retained only for later combination experiments.

---

# Task S2-6: Quiescence redesign candidates — COMPLETE

## S2-6.1 Preserve current contract

- [x] Record current quiescence move set, stand-pat rules, in-check behavior, mate/draw resolution, guard, and ordering.
- [x] Preserve fail-loud guard exhaustion in check.
- [x] Preserve legal-evasion search in check.
- [x] Preserve promotion handling and forced recapture fixtures.

## S2-6.2 SEE-pruning candidate

- [x] Add a separate inactive policy identity.
- [x] Define the exact losing-capture threshold.
- [x] Initially exclude checks, promotions, in-check nodes, only legal tactical responses, and mate-sensitive contexts.
- [x] Count every SEE prune.
- [x] Propagate SEE/internal errors rather than falling back to unpruned or static evaluation silently.
- [x] Add poisoned-capture, checking-sacrifice, promotion, en-passant, mate, and quiet-evasion regressions.

## S2-6.3 Delta-pruning candidate

- [x] Evaluate only after SEE pruning has a stable disposition.
- [x] Define typed bounded margins and material-gain assumptions.
- [x] Exclude in-check and mate-score domains.
- [x] Exclude promotions/checks under the initial policy.
- [x] Count attempts and prunes.
- [x] Record independent disposition.

## S2-6.4 Validation

- [x] Full tactical corpus.
- [x] Legal PV and exact restoration.
- [x] Reference/full tactical oracle comparisons where bounded.
- [x] Node/qnode/time/allocation diagnostics.
- [x] Fixed-node and clock-based development matches.
- [x] Production defaults remain inactive.

**S2-6 gate:** Complete. Both semantic candidates have isolated identities and exact correctness evidence. SEE pruning was evaluated first and rejected; SEE-plus-delta was then evaluated independently and rejected. Both remain inactive, and production defaults are unchanged.

---

# Task S2-7: Principal Variation Search candidate — COMPLETE

## S2-7.1 Implementation

- [x] Add inactive PVS policy identity.
- [x] Search the first ordered move with the full window.
- [x] Search later moves with a valid one-centipawn null window.
- [x] Re-search with the full window whenever required to establish the exact value.
- [x] Preserve fail-soft score semantics and bound classification.
- [x] Preserve TT mate normalization and score reuse policy.
- [x] Preserve deterministic equal-score handling.
- [x] Add zero-window and re-search diagnostics.

## S2-7.2 Correctness

- [x] Exact score parity with full-window alpha-beta over the deterministic corpus.
- [x] Best-move/PV parity subject only to documented equal-score ties; observed differing best moves: zero.
- [x] Mate-distance and longest-survival parity.
- [x] Aspiration fail-high/fail-low recovery remains exact.
- [x] Cancellation/node/time limit behavior remains exact.
- [x] No unverified narrow-window result is stored or reported as exact.
- [x] Position/history/Zobrist/table restoration passes successful, interrupted, and error paths.

## S2-7.3 Evidence

- [x] Record node, qnode, elapsed-time, cutoff, zero-window, and re-search distributions on x86-64 and ARM64.
- [x] Run the deterministic fixed-node development protocol; result `rejected_strength`.
- [x] Run the clock-based development protocol; result `rejected_strength`.
- [x] Record the independent standalone rejection in `docs/RUST_CHESS_ENGINE_V0_2_S2_7_PVS_2026-08-05.md`.
- [x] Keep default inactive and preserve all production adapters/defaults unchanged.

**S2-7 gate:** Complete. PVS is exact relative to full-window alpha-beta, deterministic evidence is reproducible, re-search behavior is bounded, performance was measured on x86-64 and native ARM64, and standalone activation is explicitly rejected. The candidate remains inactive.

---

# Task S2-8: Late Move Reductions candidate — NOT STARTED

## S2-8.1 Reduction policy

- [ ] Add versioned inactive LMR policy.
- [ ] Define minimum depth, move index, and reduction table.
- [ ] Initial reductions apply only to quiet, non-checking, non-promotion late moves.
- [ ] Protect TT move, first/PV move, captures, promotions, checks, and configured tactical candidates.
- [ ] Bound reductions so effective depth cannot underflow or escape mate domain.

## S2-8.2 Verification

- [ ] A reduced search that raises alpha receives the required full-depth re-search.
- [ ] Count reductions, reduced fail-highs, and full-depth verification searches.
- [ ] Never report a reduced speculative result as exact without verification.
- [ ] Preserve TT bound/store correctness across reduced searches.

## S2-8.3 Targeted correctness

- [ ] Quiet tactical resource fixtures.
- [ ] Quiet defensive resource fixtures.
- [ ] Forced mate and longest-survival fixtures.
- [ ] Promotion races.
- [ ] Low-mobility and zugzwang-sensitive endings.
- [ ] Check extension interaction.
- [ ] Cancellation/limit/restoration paths.

## S2-8.4 Evidence

- [ ] Node, time, selective depth, reduction, and verification diagnostics.
- [ ] Fixed-node development match.
- [ ] Clock-based development match.
- [ ] Independent disposition and parameters recorded.
- [ ] Default remains inactive.

**S2-8 gate:** LMR is bounded, verified, tactically protected, and independently evaluated.

---

# Task S2-9: Optional null-move pruning decision/candidate — NOT STARTED

## S2-9.1 Feasibility decision

- [ ] Decide whether null move fits the core/search architecture without corrupting legal-move APIs or history semantics.
- [ ] Specify side, en-passant, clocks, hash, undo, TT, repetition/history, and consecutive-null behavior before coding.
- [ ] Review zugzwang and fifty-move risks.
- [ ] Record `implement`, `reject`, or `defer` with rationale.

## S2-9.2 Search-only transition if implemented

- [ ] Add dedicated reversible search-only null transition.
- [ ] It cannot be encoded or accepted as a legal `Move`.
- [ ] It cannot enter UCI/game move history.
- [ ] Exact make/unmake and incremental/full-hash parity.
- [ ] Counter overflow and invalid state fail before mutation.

## S2-9.3 Conservative policy if implemented

- [ ] Disable in check.
- [ ] Disable at shallow depth.
- [ ] Disable in low non-pawn material and pawn-only endings.
- [ ] Disable consecutive null moves.
- [ ] Disable in mate-sensitive windows/contexts as specified.
- [ ] Add optional verification search policy.
- [ ] Count attempts, disabled nodes, cutoffs, and verifications.

## S2-9.4 Validation if implemented

- [ ] Zugzwang corpus.
- [ ] Stalemate and repetition corpus.
- [ ] Fifty/seventy-five move boundaries.
- [ ] Mate-distance and longest-survival corpus.
- [ ] Exact restoration and cancellation.
- [ ] Development fixed-node and clock matches.
- [ ] Explicit disposition; default inactive.

**S2-9 gate:** Null move is either rejected/deferred with architectural evidence or implemented conservatively with dedicated correctness and strength evidence.

---

# Task S2-10: Optional frontier and quiet-move pruning candidates — NOT STARTED

## S2-10.1 Futility pruning

- [ ] Decide based on current profile and accepted prior candidates.
- [ ] Add separate versioned policy if implemented.
- [ ] Limit initial use to shallow non-PV, non-check nodes and quiet non-checking moves.
- [ ] Protect checks, promotions, captures, forced evasions, and mate-score windows.
- [ ] Type and bound margins.
- [ ] Count attempts/prunes.
- [ ] Run independent correctness and strength disposition.

## S2-10.2 Razoring

- [ ] Evaluate only after futility evidence.
- [ ] Specify verification behavior.
- [ ] Never convert uncertain frontier values into exact results without proof.
- [ ] Protect tactical and mate-sensitive contexts.
- [ ] Record independent disposition.

## S2-10.3 Late quiet-move pruning

- [ ] Evaluate only after LMR evidence.
- [ ] Protect TT moves, killers, strong-history moves, checks, promotions, and low-mobility nodes.
- [ ] Define move-count/depth thresholds explicitly.
- [ ] Add quiet strategic/defensive regressions.
- [ ] Record independent disposition.

**S2-10 gate:** Every frontier/selectivity candidate is isolated, bounded, and accepted/rejected/deferred independently.

---

# Task S2-11: Fresh profiling and measured hot-path decisions — NOT STARTED

## S2-11.1 Reprofile

- [ ] Run Callgrind/profile-perft after current candidate set.
- [ ] Run profile-search after current candidate set.
- [ ] Capture x86-64 and native ARM64 performance distributions.
- [ ] Capture Android/JNI metrics if integration code or hot paths changed.
- [ ] Preserve old artifacts and exact provenance.

## S2-11.2 Decision: direct legal generation

- [ ] Compare current legal-generation cost and search share.
- [ ] Decide `implement`, `reject`, or `defer`.
- [ ] If implemented, retain old legal generation as a test oracle.
- [ ] Require exhaustive move-set equivalence, perft, differential, property, fuzz, and restoration evidence before activation.
- [ ] Keep fail-loud internal contradiction coverage.

## S2-11.3 Decision: sliding attacks

- [ ] Re-evaluate measured cost.
- [ ] Decide `implement`, `reject`, or `defer`.
- [ ] Reject speculative magic/PEXT/table rewrites without architecture evidence.
- [ ] Preserve exhaustive attack-oracle tests for any change.

## S2-11.4 Decision: incremental evaluation

- [ ] Re-evaluate measured evaluation cost.
- [ ] Decide `implement`, `reject`, or `defer`.
- [ ] If implemented, bind state to undo and prove full recomputation parity after every move category and random sequence.

## S2-11.5 Decision: move-list and TT layout

- [ ] Re-evaluate allocation, cache, and probe/store profile.
- [ ] Decide separately for move-list compaction and TT packing.
- [ ] Preserve semantic checksums, replacement policy, full-key verification, and mate normalization.

## S2-11.6 Reference update policy

- [ ] Do not overwrite references automatically.
- [ ] Preserve before/after distributions.
- [ ] Update references only in an intentional reviewed commit.
- [ ] Record semantic checksum changes and rationale.

**S2-11 gate:** Every optimization area has a fresh profile-backed disposition; implemented changes retain independent correctness proof.

---

# Task S2-12: Optional Syzygy tablebase decision/integration — NOT STARTED

## S2-12.1 Dependency and architecture review

- [ ] Review implementation/library options, licensing, maintenance, platform support, and provenance.
- [ ] Choose adapter-neutral interface/crate placement.
- [ ] Keep filesystem discovery out of `chess-core` and `chess-search` internals.
- [ ] Record `implement`, `reject`, or `defer`.

## S2-12.2 Explicit configuration if implemented

- [ ] Caller supplies enabled state and provider/path.
- [ ] Caller supplies supported piece-count/probe policy.
- [ ] Record implementation/version/data identity.
- [ ] No environment or conventional path discovery.
- [ ] Disabled/not configured is normal and explicit.

## S2-12.3 Failure semantics if implemented

- [ ] Distinguish `not_applicable` from probe/data failure.
- [ ] Missing/corrupt/incompatible configured data fails visible.
- [ ] No silent fallback after a configured probe error.
- [ ] Define adapter-specific error reporting without panic crossing boundaries.

## S2-12.4 Chess semantics if implemented

- [ ] Specify WDL mapping.
- [ ] Specify DTZ and fifty-move interaction.
- [ ] Specify root move selection and tie policy.
- [ ] Specify TT storage/reuse.
- [ ] Specify UCI score/info behavior.
- [ ] Add known-position oracle fixtures and lifecycle tests.

## S2-12.5 Evidence if implemented

- [ ] Unit/integration/oracle tests.
- [ ] Corrupt/missing data tests.
- [ ] Linux, C ABI/JNI, and Android behavior as applicable.
- [ ] Probe performance and allocation evidence.
- [ ] Strength disposition separate from functional correctness.

**S2-12 gate:** Syzygy is explicitly rejected/deferred or integrated without implicit discovery or silent probe fallback.

---

# Task S2-13: API, UCI, ABI/JNI, Android, CI, and documentation integration — NOT STARTED

## S2-13.1 Rust API

- [ ] Preserve existing production APIs and defaults.
- [ ] Add candidate-policy entry points only where required.
- [ ] Version new request/report structures.
- [ ] Keep ownership, cancellation, TT, and error semantics explicit.

## S2-13.2 UCI

- [ ] Do not advertise unsupported experimental options.
- [ ] For accepted configurable features, define exact option names, types, ranges, defaults, and transactional errors.
- [ ] Preserve handshake, `isready`, position, stop, quit, and stale-output behavior.
- [ ] Add subprocess tests for every new supported option.

## S2-13.3 C ABI/JNI/Android

- [ ] Keep old ABI records/functions stable.
- [ ] Use additive versioned functions/records if external policy configuration is required.
- [ ] Preserve opaque handles and all-or-nothing buffer validation.
- [ ] Preserve panic containment and exact error codes/messages.
- [ ] Update JNI/Kotlin declarations and ownership tests together.
- [ ] Preserve Android off-main search, cancellation, repeated lifecycle, dual ABI, and API-35 tests.

## S2-13.4 Permanent audits

- [ ] Add `scripts/task_v0_2_strength_audit.sh` or equivalent.
- [ ] Audit active TODO/spec/report paths.
- [ ] Audit policy/variant/report schema identities.
- [ ] Audit activation boundary and `activated=false` reports.
- [ ] Audit absence of temporary helpers and hidden Python/runtime fallback.
- [ ] Chain v0.1, Task 26, Task 27, and post-port audits.

## S2-13.5 Workflows

- [ ] Wire v0.2 audit into CI.
- [ ] Add bounded strength smoke workflow if practical.
- [ ] Add manual/scheduled development and production variant validation.
- [ ] Preserve artifacts with exact names/SHAs.
- [ ] Ensure workflows cannot edit source/default policy.
- [ ] Preserve x86-64, ARM64, Android, robustness, performance, slow perft, and strength gates.

## S2-13.6 Documentation

- [ ] Search-policy/variant schema.
- [ ] SEE contract and oracle.
- [ ] Quiescence/selectivity decisions.
- [ ] Strength protocol and report schema.
- [ ] Performance/profiling updates.
- [ ] Optional tablebase configuration/failure policy if implemented.
- [ ] Developer commands and artifact ownership.

**S2-13 gate:** Accepted/internal candidate infrastructure is integrated without breaking existing adapters or weakening permanent CI.

---

# Task S2-14: Production candidate selection and validation — NOT STARTED

## S2-14.1 Select candidate

- [ ] Select one exact candidate or evidence-backed combination from individually evaluated components.
- [ ] Record why each included component is present.
- [ ] Record why excluded/deferred components are absent.
- [ ] Freeze search-policy identity, weights, source SHA, toolchain, opening suite, TT, limits, seeds, and commands.
- [ ] Candidate remains inactive.

## S2-14.2 Full correctness matrix

- [ ] Formatting/check/Clippy/all-target tests.
- [ ] Release perft depth four.
- [ ] Differential oracle and seeded playouts.
- [ ] Tactical/mate/draw/zugzwang/promotion corpus.
- [ ] Legal PV replay and exact restoration.
- [ ] Cancellation, limits, UCI, safe facade, C ABI, JNI, Android.
- [ ] Fuzz, Miri, ASan/LSan, TSan.
- [ ] Candidate-specific audits.

## S2-14.3 Performance matrix

- [ ] x86-64 seven-sample baseline/comparator.
- [ ] Native ARM64 seven-sample baseline/comparator.
- [ ] Zero-allocation audit.
- [ ] Search diagnostics and checksum.
- [ ] Android metrics if applicable.
- [ ] Record any intentional reference update separately.

## S2-14.4 Production strength matrix

- [ ] At least 200 independent opening pairs / 400 games.
- [ ] Color-swapped identical openings.
- [ ] Fixed-node production evidence.
- [ ] Clock-based production evidence for release-relevant strength.
- [ ] Unfinished rate within ceiling.
- [ ] Lower confidence bound strictly exceeds required margin.
- [ ] Report checksum and atomic persistence pass.
- [ ] Report decision is explicit.
- [ ] Report records `activated=false`.

## S2-14.5 Disposition

- [ ] If rejected, preserve exact reason and keep v0.1 authoritative.
- [ ] If accepted, record `accepted_for_activation`; do not change defaults in this task.
- [ ] No manual interpretation may override the report rule.

**S2-14 gate:** One frozen candidate receives complete exact-SHA correctness, performance, and production strength evidence while remaining inactive.

---

# Task S2-15: Separate activation and v0.2 release gate — NOT STARTED

## S2-15.1 Preconditions

- [ ] S2-14 report is `accepted_for_activation`.
- [ ] Report is complete, checksummed, and preserved.
- [ ] No unresolved correctness/performance/robustness issue exists.
- [ ] Candidate source/policy/weight identities match the activation inputs exactly.

## S2-15.2 Activation commit

- [ ] Enable the accepted policy and/or weights in a separate reviewed commit.
- [ ] Update authoritative built-in policy checksum.
- [ ] Update authoritative weight identity only if accepted weights are included.
- [ ] Update package/UCI version to `0.2.0` only here.
- [ ] Preserve rollback instructions and prior v0.1 identity.
- [ ] Do not activate any candidate component not present in the accepted report.

## S2-15.3 Post-activation validation

- [ ] Complete Rust CI on exact activation SHA.
- [ ] Android/JNI exact-SHA validation.
- [ ] Robustness exact-SHA validation.
- [ ] Performance exact-SHA validation.
- [ ] Release perft and differential oracle.
- [ ] UCI playable smoke and option behavior.
- [ ] Production strength validation against prior authoritative v0.1 baseline or an explicitly justified unchanged accepted candidate tree.
- [ ] Verify default entry points now use exactly the activated identity.

## S2-15.4 Release documentation

- [ ] README identifies v0.2 authoritative policy and weights.
- [ ] Developer documentation lists exact commands/defaults.
- [ ] Changelog/release report lists accepted, rejected, deferred, and optional capabilities.
- [ ] Public API/ABI versions are accurate.
- [ ] No report is rewritten to claim it activated the engine.

**S2-15 gate:** A separately accepted candidate is explicitly activated and passes the full exact-SHA release matrix as v0.2.

---

# Task S2-16: Final audit, report, and closure — NOT STARTED

## S2-16.1 Final implementation report

- [ ] Create `docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_IMPLEMENTATION_REPORT.md`.
- [ ] Record whether v0.2 released or the program completed without promotion.
- [ ] Map every task to implementation/evidence/disposition.
- [ ] Record exact authoritative source, policy, weight, ABI/JNI, report, opening, and tablebase identities.
- [ ] Record all accepted, rejected, revised, and deferred candidates.
- [ ] Record exact workflow run/job/artifact IDs.
- [ ] Record known limitations and next roadmap.

## S2-16.2 Final permanent audit

- [ ] Require complete spec/TODO/report traceability.
- [ ] Require exact validated implementation SHA.
- [ ] Require active TODO authority consistency.
- [ ] Require activation boundary consistency.
- [ ] Reject placeholder SHAs/IDs/decisions.
- [ ] Reject temporary helper workflows/scripts.
- [ ] Reject hidden Python embedding/spawn in production crates.
- [ ] Reject implicit data discovery and silent optional-capability fallback.
- [ ] Chain all inherited permanent audits.

## S2-16.3 Closure consistency

- [ ] Mark tasks complete only after their gates pass.
- [ ] Reclassify this TODO as completed historical authority when the program closes.
- [ ] If no candidate passed, keep package/UCI v0.1 and say so explicitly.
- [ ] If v0.2 released, verify README/report/default identity agree.
- [ ] Verify no unresolved P0/P1 issue exists.
- [ ] Verify no rejected candidate is active.

## S2-16.4 Final gate

- [ ] S2-0 gate.
- [ ] S2-1 gate.
- [ ] S2-2 gate.
- [ ] S2-3 gate.
- [ ] S2-4 gate.
- [ ] S2-5 gate.
- [ ] S2-6 gate.
- [ ] S2-7 gate.
- [ ] S2-8 gate.
- [ ] S2-9 gate.
- [ ] S2-10 gate.
- [ ] S2-11 gate.
- [ ] S2-12 gate.
- [ ] S2-13 gate.
- [ ] S2-14 gate.
- [ ] S2-15 gate, or explicit no-release disposition if no candidate was accepted.
- [ ] S2-16 gate.

**S2-16 gate:** The strength program is completely auditable and either releases an evidence-backed v0.2 or truthfully closes without promotion.

---

## Required evidence template

Use this block for every completed task or candidate:

```text
Task/candidate:
Disposition:
Implementation SHA:
Validation SHA:
Baseline identity/checksum:
Candidate policy identity/checksum:
Candidate weight identity/checksum:
Files changed:
Commands:
Correctness results:
Performance results:
Strength results:
Workflow runs/jobs/artifacts:
Activation state: false/true
Deviations:
Discovered defects and permanent regressions:
Remaining risks:
```

## Initial next action

Begin with **S2-8 only**: the inactive Late Move Reductions candidate. Do not begin S2-9 or later work until S2-8 has an isolated policy identity, bounded reduction/verification semantics, exact correctness evidence, architecture-specific performance measurements, development strength evidence, and an explicit disposition.
