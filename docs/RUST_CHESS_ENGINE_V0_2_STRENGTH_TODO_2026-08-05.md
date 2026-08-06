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

## S2-8 implementation record

- Disposition: complete; standalone LMR activation rejected; the corrected typed candidate remains inactive for possible explicitly identified combination experiments.
- Core implementation SHA: `6ecc8cce609a11d26dde81a03db38b9284a801f1`.
- Evidence-harness SHA: `12a959756864c01cc82e18d71f109c0eb0938786`.
- Explicit selective-depth evidence SHA: `ba565dea4afc2dcf074520d9cf5b7c55e60c9e6f`.
- Exact validation SHA: `c8d4e835f0946ccd385b32e9a03b62cba6112d4b`.
- Candidate policy identifier/checksum: `5332384c4d523031` / `250607d2af491286`; baseline remains `5630315f504f4c31` / `0c0769ef9d034770`.
- Parameters: minimum depth `4`; fifth ordered move; at least `6` legal moves and `10` total pieces; reduction table `[(4, 4, 1), (7, 8, 2)]`; reductions retain at least one full child ply.
- Protected: first/PV move, TT move, killers, captures, promotions, in-check nodes, checking moves, low-mobility nodes, low-material positions, mate windows, and underflowing depths.
- Every reduced alpha raise receives exactly one full-depth verification. Deterministic evidence recorded `29` reductions, `7` reduced fail-highs, and `7` verifications across 13 parity cases; zero differing best moves; checksum `60faa8a799565fc7`; repeated x86-64 output was byte-identical and ARM64 semantics matched.
- The first candidate exposed a forced-mate defect on `4Q2k/8/4K3/8/8/8/8/8 b - - 0 1`, returning `-1030` instead of `-29994`. Low-material and mate-window exclusions fixed it; the unchanged fixture is a permanent regression.
- Fixed-node development: 8 pairs / 16 games at 2,000 nodes; candidate W/D/L `2/0/2`, unfinished `12`, all failure categories zero, `rejected_strength`, checksum `b0f204ec892fb99d`.
- Clock development: 8 pairs / 16 games at 10 ms; candidate W/D/L `2/0/2`, unfinished `12`, all failure categories zero, `rejected_strength`, checksum `e837571ccedb820d`.
- Seven-sample x86-64 median ratio `1.001488`; ARM64 ratio `1.000153`; candidate was fractionally slower on both. Nodes remained `40,000`; qnodes `35,620/35,665`; selective depth `22/22`; allocations and bytes were unchanged.
- Exact permanent run `31065063892`: x86-64 job `92501001970`, artifact `8953737384`, digest `22844449c56536ae94957726ff5a378511bec99fffbdf2f839a9164e6b0818c0`; ARM64 job `92501001923`, artifact `8953681761`, digest `01c0563109c18ec0cb7a3204452f454cac66e897ee05646c592edfd1dee5be85`; all gates passed.
- Production UCI, safe Rust facade, C ABI, JNI, Android, package version, evaluation weights, authoritative v0.1 policy, and defaults remain unchanged. No silent fallback, implicit discovery, committed generated evidence, or write-capable permanent workflow remains.

## S2-9 feasibility record

- Disposition: `implement`; the architecture supports a dedicated reversible search-only null transition, but null pruning itself remains unimplemented and inactive.
- Feasibility baseline SHA: `76862f5730a518957bf0fbd3daf15af99f37ce6c`.
- Decision document: `docs/RUST_CHESS_ENGINE_V0_2_S2_9_NULL_MOVE_FEASIBILITY_2026-08-05.md`.
- Position contract: board state and castling remain unchanged; side toggles; en-passant clears; halfmove and fullmove counters remain unchanged; incremental Zobrist removes the prior canonical en-passant contribution and toggles the side key.
- API boundary: the transition receives a separate opaque undo token and is never represented as `Move`, accepted by legal move generation, written to `Game`, or exposed through UCI, C ABI, JNI, or Android.
- History contract: the synthetic null position is not pushed into `SearchHistory`; legal child positions continue to use ordinary push/pop restoration.
- TT contract: score probe reuse and score storage are suppressed throughout the speculative null subtree; a verified legal TT move may remain an ordering hint.
- Recursion contract: explicit state disables every nested/consecutive null attempt in the speculative subtree and disables null at any verification node.
- Risk contract: policy integration must initially exclude in-check, shallow, pawn-only, low-non-pawn-material, mate-sensitive, and zugzwang-prone contexts and must freeze verification behavior before pruning can land.
- Fifty/seventy-five-move contract: existing draws resolve before null; null does not advance clocks or history, and only the subsequent legal move changes the halfmove clock.
- Existing reserved null attempt/cutoff diagnostics are insufficient for the final candidate; S2-9.3 must add explicit disabled-node, speculative-fail-high, verification, and confirmed-cutoff accounting.
- S2-9.2 is limited to the transition primitive plus exact restoration/hash/failure tests. Production policy, defaults, adapters, package/UCI version, and activation remain unchanged.

## S2-9.2 transition record

- Disposition: complete; the reversible search-only position transition is accepted as infrastructure for S2-9.3, while null pruning remains unimplemented and inactive.
- Starting master SHA: `152b8a52b90989b113411a9dffc33cb520e45e6b`.
- Core implementation SHA: `ee65c38624df12c3d30ec954fd3157e66456373d`.
- Focused validation run: `31074949590`.
- Added `SearchNullUndo`, `SearchNullError`, `Position::make_search_null`, and `Position::unmake_search_null` in a dedicated `chess-core` position module.
- State contract: board representations and castling remain unchanged; side toggles; en-passant clears; legal clocks remain unchanged; incremental hash removes the prior canonical en-passant key and toggles the side key.
- Failure contract: checked positions and mismatched undo tokens fail before mutation; maximum counter values are preserved because the transition performs no clock arithmetic.
- History contract: the API accepts only a mutable position and cannot append to `Game` or `SearchHistory`; focused tests retain the legal parent hash while the synthetic state is active.
- Legal/API boundary: no `Move`, `MoveKind`, legal token, UCI history, PV, C ABI, JNI, or Android representation was added.
- Permanent tests cover en-passant identity, both sides, maximum counters, checked-position atomicity, mismatched-token atomicity, detached history, repeated restoration, and incremental/full-hash parity.
- S2-9.3 remains blocked from silently reusing/storing TT scores, nesting null attempts, or cutting off without its separately frozen conservative policy and diagnostics.
- Production search policy, defaults, package/UCI version, adapters, and activation remain unchanged.

## S2-9.3 conservative policy record

- Disposition: implementation complete; S2-9.4 validation is recorded below; standalone activation is rejected and activation remains false.
- Core implementation SHA: `029c16ed216a0fc84d6772c10ea8678ad202c6cf`.
- Staging validation workflow run: `31080097848`.
- Candidate policy identifier: `5332394e4d503031`; isolated null-move feature bit only.
- Frozen policy: minimum depth `4`; speculative reduction `2` after the synthetic pass ply; verification reduction `1`; side-to-move non-pawn minimum `2`; total non-pawn minimum `4`; every speculative fail-high requires verification.
- Disabled contexts: root, check, shallow depth, pawn-only/low non-pawn material, nested/speculative/verification subtrees, mate-sensitive bounds/domain, and static evaluation below beta.
- Synthetic subtrees suppress TT score reuse and storage through the explicit `SuppressedForNullMove` reason while retaining legal-checked TT move ordering hints. Verification searches return to ordinary TT score policy but keep null disabled for the complete verification subtree.
- Diagnostics now count eligibility attempts, disabled nodes with stable reason events, speculative fail-highs, verification searches, and confirmed cutoffs using checked exact-result accumulation.
- The authoritative v0.1 policy, production adapters, UCI, C ABI, JNI, Android, package version, and defaults remain unchanged.
- S2-9.3 itself did not claim S2-9.4 correctness, development strength, or final disposition; those are recorded independently below.

## S2-9.4 validation record

- Disposition: complete; standalone null-move activation rejected as `rejected_strength`; candidate remains inactive.
- Validated candidate source SHA: `8638611e38c712009e7f98bd4881fb266034df13`.
- Staging validation run: `31085412059`; evidence artifact `8961204541`; digest `sha256:1c7ed56774119f9d771453e045b03345d4aae31d840eec30a7c03b96a28d8a19`.
- Final record: `docs/RUST_CHESS_ENGINE_V0_2_S2_9_NULL_MOVE_2026-08-06.md`.
- Candidate identity/checksum: `5332394e4d503031` / `4364aad2ac2abc2a`; baseline remains `5630315f504f4c31` / `0c0769ef9d034770`.
- The versioned 14-case corpus covers zugzwang, root and synthetic-pass stalemate, threefold/fivefold repetition, halfmove clocks `99/100/149/150`, mate distance, longest survival, active speculative-null execution, repeated restoration, and bounded node cancellation.
- Every exact case matched baseline score and completed depth; all 14 best moves matched; all PVs replayed legally; position/history/Zobrist restoration passed.
- Aggregate diagnostics: `11071` attempts, `11066` disabled nodes, `0` speculative fail-highs, `0` verifications, `0` cutoffs; checksum `75da625a5ae9c6d7`; activated `false`.
- Fixed-node development: 8 pairs / 16 games at 2,000 nodes and 48 maximum plies; all 16 unfinished, all failure categories zero, `rejected_strength`, checksum `81a8a72c9242da64`.
- Clock development: 8 pairs / 16 games at 10 ms and 48 maximum plies; all 16 unfinished, all failure categories zero, `rejected_strength`, checksum `9054382ea9b188c5`.
- The evidence does not establish that null move is weaker; it supplies no positive standalone strength basis and therefore fails the project acceptance gate in both independent protocols.
- Production UCI, safe Rust facade, C ABI, JNI, Android, package version, evaluation weights, authoritative v0.1 policy, and defaults remain unchanged.

## S2-10.1 futility-pruning decision record

- Disposition: complete with `defer`; no futility candidate is retained or activated.
- Authoritative production baseline restored: `542509b07bc02f6754de7c1682224fd2aa249a1e` search-policy/source blobs, preserved by cleanup commit `e603d963f3de363406c47be6d8dafa8bfb6bea1d`.
- Initial generated draft SHA: `86004c11da96dad19455619c0fdb98cf8b97b66b`.
- Strict non-PV review staging SHA: `87fb97b7aed342cf79ba5765ed6696411a7677e6`.
- Focused proof run: `31092967077`; job `92588097246`.
- Final decision record: `docs/RUST_CHESS_ENGINE_V0_2_S2_10_1_FUTILITY_2026-08-06.md`.
- The generated draft was rejected because it allowed frontier pruning at wide-window/PV nodes, contrary to the frozen S2-10.1 contract.
- The corrected candidate required a one-centipawn null window, passed check, strict Clippy, 119 unit tests, property tests, and tactical/rule-sensitive tests, then failed its mandatory exercise assertion because it recorded exactly zero futility attempts.
- This is an architectural result rather than a missing fixture: the authoritative v0.1 baseline is full-window alpha-beta, while the only narrow-window main-search implementation is the rejected and inactive S2-7 PVS candidate. A standalone compliant futility policy therefore has no eligible non-PV frontier nodes.
- Widening eligibility would violate the task contract; combining futility with rejected PVS would violate candidate isolation. Retaining a policy flag, margin, counters, or tests for a behavior that cannot execute would create misleading dead configuration.
- No strength match was run because there was no executable behavioral candidate after the correctness pre-gate. A no-op comparison would duplicate the frozen identical-policy control and cannot supply acceptance evidence.
- The unsafe/no-op draft, candidate identity, margin, diagnostics changes, test, generator payloads, and write-capable temporary workflow were removed. Production UCI, safe Rust facade, C ABI, JNI, Android, package version, evaluation weights, authoritative policy, and defaults remain unchanged.
- Exact cleanup validation: CI run `31093244779`; performance run `31093244660`; robustness run `31093244674`; Android/JNI run `31093244043`; all successful.
- Reconsider only after a narrow-window main-search policy is independently accepted, or as an explicitly identified combination candidate with its own policy identity, correctness evidence, and strength disposition.

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
| S2-8 | Late Move Reductions candidate | **Complete — standalone rejected; inactive for combinations** |
| S2-9 | Optional null-move pruning decision/candidate | **Complete — standalone rejected; inactive** |
| S2-10 | Optional frontier and quiet-move pruning candidates | **Complete — S2-10.1, S2-10.2, and S2-10.3 deferred; inactive** |
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

# Task S2-8: Late Move Reductions candidate — COMPLETE

## S2-8.1 Reduction policy

- [x] Add a versioned inactive LMR policy.
- [x] Define minimum depth `4`, first eligible move index `4`, low-mobility/material guards, and reduction table `[(4, 4, 1), (7, 8, 2)]`.
- [x] Apply initial reductions only to quiet, non-checking, non-promotion late moves.
- [x] Protect TT move, first/PV move, captures, promotions, checks, killers, low-mobility nodes, low-material positions, and mate windows.
- [x] Bound reductions so effective depth retains at least one full child ply and cannot escape the mate domain.

## S2-8.2 Verification

- [x] A reduced search that raises alpha receives the required full-depth verification search.
- [x] Count reductions, reduced fail-highs, and full-depth verification searches independently.
- [x] Require reduced fail-high and verification totals to match exactly.
- [x] Never report or store a reduced speculative result as exact without verification.
- [x] Preserve TT bound/store, fail-soft score, mate normalization, and deterministic equal-score correctness across reduced searches.

## S2-8.3 Targeted correctness

- [x] Quiet tactical-resource fixtures.
- [x] Quiet defensive-resource fixtures.
- [x] Forced-mate and longest-survival fixtures, including the permanent sparse forced-mate regression discovered during implementation.
- [x] Promotion races and en-passant tactics.
- [x] Low-mobility, low-material, and zugzwang-sensitive endings.
- [x] Check-extension and mate-window interaction.
- [x] Cancellation, node/time limits, legal PV replay, and position/history/Zobrist restoration paths.

## S2-8.4 Evidence

- [x] Record nodes, qnodes, elapsed time, selective depth, cutoffs, reductions, reduced fail-highs, verification searches, allocations, and semantic checksums.
- [x] Run deterministic fixed-node development match; result `rejected_strength`.
- [x] Run clock-based development match; result `rejected_strength`.
- [x] Record independent standalone rejection and exact parameters in `docs/RUST_CHESS_ENGINE_V0_2_S2_8_LMR_2026-08-05.md`.
- [x] Keep default inactive and preserve all production adapters/defaults unchanged.

**S2-8 gate:** Complete. LMR is isolated, bounded, fully verified after reduced alpha raises, tactically protected, reproducible on x86-64 and native ARM64, and independently evaluated. Standalone activation is rejected and the candidate remains inactive.

---

# Task S2-9: Optional null-move pruning decision/candidate — COMPLETE

## S2-9.1 Feasibility decision

- [x] Decide whether null move fits the core/search architecture without corrupting legal-move APIs or history semantics.
- [x] Specify side, en-passant, clocks, hash, undo, TT, repetition/history, and consecutive-null behavior before coding.
- [x] Review zugzwang and fifty-move risks.
- [x] Record `implement`, `reject`, or `defer` with rationale.

## S2-9.2 Search-only transition if implemented

- [x] Add dedicated reversible search-only null transition.
- [x] It cannot be encoded or accepted as a legal `Move`.
- [x] It cannot enter UCI/game move history.
- [x] Exact make/unmake and incremental/full-hash parity.
- [x] Counter overflow and invalid state fail before mutation.

## S2-9.3 Conservative policy if implemented

- [x] Disable in check.
- [x] Disable at shallow depth.
- [x] Disable in low non-pawn material and pawn-only endings.
- [x] Disable consecutive null moves.
- [x] Disable in mate-sensitive windows/contexts as specified.
- [x] Add optional verification search policy.
- [x] Count attempts, disabled nodes, cutoffs, and verifications.

## S2-9.4 Validation if implemented

- [x] Zugzwang corpus.
- [x] Stalemate and repetition corpus.
- [x] Fifty/seventy-five move boundaries.
- [x] Mate-distance and longest-survival corpus.
- [x] Exact restoration and cancellation.
- [x] Development fixed-node and clock matches.
- [x] Explicit disposition; default inactive.

**S2-9 gate:** Complete. The conservative candidate passed the dedicated correctness/restoration matrix, both independent development protocols returned `rejected_strength`, standalone activation is rejected, and the candidate remains inactive.

---

# Task S2-10: Optional frontier and quiet-move pruning candidates — COMPLETE

## S2-10.1 Futility pruning — COMPLETE (DEFERRED)

- [x] Decide based on current profile and accepted prior candidates. Disposition: `defer`; the accepted full-window baseline has no eligible non-PV frontier nodes, and the narrow-window PVS candidate is rejected/inactive.
- [x] Add separate versioned policy if implemented. Not implemented: the unsafe/no-op draft identity was removed rather than retained as dead configuration.
- [x] Limit initial use to shallow non-PV, non-check nodes and quiet non-checking moves. The strict review required a one-centipawn null window and preserved the remaining guards; the resulting candidate recorded zero attempts.
- [x] Protect checks, promotions, captures, forced evasions, and mate-score windows. The draft protections were reviewed, but the complete candidate was removed because its node-level eligibility could not be satisfied independently.
- [x] Type and bound margins. The draft's checked `150 cp` depth-one margin was not adopted because no compliant node could exercise it.
- [x] Count attempts/prunes. Reserved baseline counters remain zero; the strict proof observed exactly zero candidate attempts and therefore no prunes.
- [x] Run independent correctness and strength disposition. Check, strict Clippy, 119 unit tests, property tests, and tactical/rule-sensitive tests passed; the mandatory exercise test failed closed on zero attempts. No strength match was run for a non-behavioral candidate; final disposition is `defer`, activation `false`.

**S2-10.1 gate:** Complete with `defer`. A wide-window implementation was rejected as contract-violating, the strict non-PV implementation was proven inert under the authoritative baseline, and all experimental code/configuration was removed.

## S2-10.2 Razoring — COMPLETE (DEFERRED)

- [x] Evaluate only after futility evidence. The prerequisite is not met: S2-10.1 produced no executable futility evidence under the accepted full-window baseline and was deferred.
- [x] Specify verification behavior. No candidate was implemented. Any future candidate must treat the razor test as a probe, verify a prospective fail-low through legal quiescence against the original alpha bound, and fall through to the normal full search whenever the probe raises alpha or is ambiguous.
- [x] Never convert uncertain frontier values into exact results without proof. A future verified fail-low may produce only an upper-bound result; it must not publish an exact transposition-table entry from the razor probe.
- [x] Protect tactical and mate-sensitive contexts. No candidate was retained. Future reconsideration must exclude checks, forced evasions, mate-score windows, promotions, and tactically unstable or low-material frontier positions unless separately proven safe.
- [x] Record independent disposition. `defer`, activation `false`; no correctness or strength match was run because no behaviorally distinct candidate passed the prerequisite gate.

**S2-10.2 gate:** Complete with `defer`. The required futility evidence does not exist. Implementing razoring now would bypass the ordered evidence gate or couple it to rejected/inactive search candidates. Production code, policy identity, diagnostics, evaluation, adapters, and defaults remain unchanged.

## S2-10.3 Late quiet-move pruning — COMPLETE (DEFERRED)

- [x] Evaluate only after LMR evidence. The corrected LMR candidate passed its correctness matrix but returned `rejected_strength` in both development protocols, was fractionally slower on x86-64 and ARM64, and did not reduce the bounded workload's main-node count. Its discovered sparse forced-mate regression also proves that a late quiet move cannot be omitted safely from move index alone.
- [x] Protect TT moves, killers, strong-history moves, checks, promotions, and low-mobility nodes. No pruning candidate was implemented. TT, killer, check, promotion, and mobility guards exist in the LMR infrastructure, but the search-local history table has no calibrated/versioned strong-history threshold suitable for a pruning proof.
- [x] Define move-count/depth thresholds explicitly. No thresholds were adopted: inventing depth, move-count, or history cutoffs without supporting node/resource evidence would create an unsafe policy. Any future candidate must version and bound every threshold before implementation.
- [x] Add quiet strategic/defensive regressions. No behaviorally distinct candidate reached implementation. The LMR quiet-resource, quiet-defense, mate-distance, low-mobility, low-material, promotion, en-passant, cancellation, and restoration corpus was reviewed as prerequisite evidence and remains mandatory for reconsideration.
- [x] Record independent disposition. `deferred_insufficient_evidence`, activation `false`; no candidate correctness matrix or strength match was run because no defensible pruning policy passed the design gate.

**S2-10 gate:** Complete. Futility, razoring, and late quiet-move pruning are independently deferred and inactive. No frontier/selectivity candidate changed production policy, search semantics, diagnostics, evaluation, adapters, package identity, or defaults.

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

Begin with **S2-10.1 only**: decide whether a separately versioned, shallow non-PV futility-pruning candidate is justified by the current profile and accepted baseline. Do not combine it with rejected PVS, LMR, SEE/delta, or null-move candidates, and do not activate or expose it through production adapters without its own correctness and strength disposition.
