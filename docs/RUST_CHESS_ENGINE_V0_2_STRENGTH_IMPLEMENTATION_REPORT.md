# Rust Chess Engine v0.2 Strength Program Implementation Report

**Status:** Complete — program closed without v0.2 promotion
**Program outcome:** Completed without promotion
**Date:** 2026-08-07
**Specification:** `docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_SPEC_2026-08-05.md`
**Tracker:** `docs/RUST_CHESS_ENGINE_V0_2_STRENGTH_TODO_2026-08-05.md`
**S2-14 production report:** `docs/RUST_CHESS_ENGINE_V0_2_S2_14_PRODUCTION_VALIDATION_2026-08-06.md`
**S2-15 disposition:** Skipped — no `accepted_for_activation` candidate
**Validated production/code baseline SHA:** `677cd2a4d2a4a4f3c376f7bf47fae412171206fb`
**Closure type:** Documentation/audit-only; production code and defaults unchanged

## Executive disposition

The v0.2 strength-development program is complete, but no v0.2 engine was released. S2-14's frozen standalone PVS candidate passed correctness, robustness, platform, and predeclared performance gates, then failed the production strength rule independently under both fixed-node and clock protocols. Both authoritative reports are `rejected_strength` and `activated=false`.

Because S2-15 requires an `accepted_for_activation` S2-14 report, S2-15 was not activated and was not partially executed. Its release checklist remains unchecked. S2-16 therefore uses the specification's explicit completed-without-promotion outcome: v0.1 remains authoritative, package/UCI version stays `0.1.0`, and no rejected or deferred candidate is enabled by default.

The S2-16 closure changes only documentation, TODO authority classification, and permanent fail-closed audits. It does not change search/evaluation semantics, default policy/weights, public Rust APIs, C ABI, JNI/Kotlin surface, Android behavior, benchmark references, or activation state.

## Authoritative identities at closure

- Production/code baseline SHA: `677cd2a4d2a4a4f3c376f7bf47fae412171206fb`. This exact tree includes the fail-closed JNI diagnostic hardening and removal of its temporary staging helpers before S2-16 documentation closure.
- Package/UCI version: `0.1.0`.
- Search-policy schema: `1`.
- Search policy identifier/checksum: `5630315f504f4c31` / `0c0769ef9d034770`.
- Evaluation-weight schema: `1`.
- Evaluation-weight identifier/checksum: `424153454c494e45` / `d2cca7ae10ec6e34`.
- C ABI version: `1`; the public ABI remains the v0.1 boundary.
- JNI identity: public JNI/Kotlin method surface unchanged; error diagnostics are fail-closed, and no experimental search-policy input is exposed.
- S2-14 frozen PVS candidate source SHA: `21406b5e92b6bd42a3a902591dddae22c9b3f16f`.
- S2-14 PVS policy identifier/checksum: `5332375056533031` / `ef730d158002ccfa`.
- Production PVS report checksums: `bad7aa1f69e9d18e` / `d3b883442ec6107b`.
- Production opening file SHA-256: `6c3ff4cc9837bc66dd517d4a7c60d56e71a9b3a4e1fb1aabd904de81dad4e9b7`.
- Production opening semantic checksum: `36c98c850cff76ba`; 1,200 unique deterministic first-party openings.
- Frozen v0.1 control opening-suite checksum from S2-3: `1cf5dfa5ebbe0bc5`.
- Tablebase identity: disabled. S2-12 deferred Syzygy integration; no compliant backend dependency or production tablebase fallback is present.
- Opening book during S2-14 production candidate validation: disabled.
- Activation state: `false` for every candidate report used by this program.

## Exact validated baseline matrix before documentation closure

The unchanged production/code baseline `677cd2a4d2a4a4f3c376f7bf47fae412171206fb` passed the permanent exact-head matrix immediately before S2-16:

- CI run `31157401828`: x86-64 workspace-quality job `92799804433`; native ARM64 workspace job `92799804392`; success.
- Performance run `31157401863`: x86-64 job `92799804538`, artifact `8985678287` (`sha256:882a3c8d3b0814b5fd3e8c2c1dd201e604ed546f0fee3ec6c5eecca21ef46979`); ARM64 job `92799804704`, artifact `8985691446` (`sha256:28c7b61905ba5575fe554457177e54657bda9f05f0b7a3346a666d68daa6d54e`); success.
- Robustness run `31157401842`: sanitizer/TSan job `92799804452`, fuzz/corpus job `92799804504`, Miri job `92799804534`; success.
- Android/JNI run `31157401847`: Android lint job `92799815794`, API-35 instrumented JNI job `92799815833`, host-JVM JNI contract job `92799815859`; success.
- Strength tracker run `31157401822`: job `92799804477`; success through S2-14 on the unchanged code baseline.
- Report-master validation run `31158574619`: success after the exact-head code matrix.

S2-16 then reclassifies the tracker and strengthens permanent audits. Final closure commits are documentation/audit changes layered on this unchanged validated code tree; they are not new strength candidates and must not be described as such.

## Program task map

| Task | Scope | Final disposition |
|---|---|---|
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
| S2-11 | Fresh profiling and measured hot-path decisions | **Complete — x86-64 sliding dispatch accepted; non-x86 baseline preserved** |
| S2-12 | Optional Syzygy tablebase decision/integration | **Complete — deferred; no compliant backend integrated; inactive** |
| S2-13 | API, UCI, ABI/JNI, Android, CI, and documentation integration | **Complete — internal candidate infrastructure integrated; public adapters unchanged; inactive** |
| S2-14 | Production candidate selection and validation | **Complete — PVS rejected_strength; v0.1 remains authoritative; inactive** |
| S2-15 | Separate activation and v0.2 release gate | **Skipped — activation precondition unsatisfied; no v0.2 promotion** |
| S2-16 | Final audit, report, and closure | **Complete — program closed without promotion; v0.1 remains authoritative** |

## S2-15 explicit no-release disposition

S2-15 is intentionally skipped, not silently treated as passed. Its first precondition requires the S2-14 report to be `accepted_for_activation`; both frozen PVS production reports instead state `rejected_strength`. Therefore no activation commit was created, no built-in policy or weight identity was changed, package/UCI version was not changed to `0.2.0`, no public release surface was changed for v0.2, no rejected candidate was enabled by default, and no report was rewritten to claim activation.

## Accepted, rejected, revised, and deferred work

The detailed ledger below is authoritative for exact per-task evidence. Accepted infrastructure or non-release implementation includes typed policy/variant identity and validation controls, deterministic baseline diagnostics, the standalone SEE primitive, and the measured x86-64 sliding-attack dispatch decision. Rejected candidates include standalone SEE ordering, SEE/delta quiescence pruning variants, standalone PVS, standalone LMR, standalone null move, the S2-14 SEE+LMR preselection combination, and the final S2-14 standalone PVS production candidate. Deferred work includes the S2-10 frontier/quiet-move pruning experiments and S2-12 Syzygy integration. S2-14 revised candidate selection only by freezing a separately identified PVS candidate after the SEE+LMR preflight failure; no threshold was relaxed.

## Known limitations and next roadmap

- The released engine remains v0.1-strength authority; this program did not produce evidence for a v0.2 promotion.
- Syzygy/tablebase support remains absent from production.
- Experimental search-policy feature bits and candidate tooling may remain available only behind explicit typed identities; production adapters/defaults do not expose them.
- Future strength work should start under a new active specification/TODO authority with new candidate identities and fresh evidence. Rejected S2 reports cannot be reused as activation authorization.
- Any future release must repeat the separate acceptance → activation → exact-SHA release sequence.
- Permanent audits continue to reject hidden Python/subprocess production fallbacks, implicit optional-capability discovery, silent fallback, temporary write-capable helpers, and version/default/activation drift.

## P0/P1 closure check

GitHub issue searches at closure found no open issue labeled P0 and no open issue labeled P1. This is repository issue state, not a claim that no lower-priority future work exists.

## Detailed implementation and evidence ledger

The following ledger is copied from the authoritative tracker so the final report retains exact implementation SHAs, validation SHAs, workflow run/job/artifact IDs, checksums, architecture evidence, and per-task dispositions established during S2-0 through S2-14.

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

## S2-14 implementation record

- Disposition: complete with `rejected_strength`; standalone PVS remains inactive and v0.1 remains authoritative.
- Frozen candidate source SHA: `21406b5e92b6bd42a3a902591dddae22c9b3f16f`.
- Candidate policy identifier/checksum: `5332375056533031` / `ef730d158002ccfa`; baseline `5630315f504f4c31` / `0c0769ef9d034770`; weights `424153454c494e45` / `d2cca7ae10ec6e34`.
- Preflight run `31146057113`: x86-64 job `92765623932`, artifact `8981719767`, median ratio `1.012722`; ARM64 job `92765623863`, artifact `8981761297`, median ratio `1.013350`; frozen ceiling `1.05`; both passed.
- Exact full-matrix evidence on the candidate SHA: CI `31146057163`, performance `31146057128`, robustness `31146057142`, Android/JNI `31146057103`, tracker `31146057112`, report validation `31146990298`; all passed.
- Production run `31146807904` succeeded as evidence generation/validation. Fixed-node job `92767800034`: 1,000 pairs, W/D/L `862/144/977`, unfinished `17`, failures `0`, mean `0.47125`, LCB `0.4578061271735924`, `rejected_strength`, checksum `bad7aa1f69e9d18e`, artifact `8982304975`.
- Clock job `92767800098`: 1,000 pairs, W/D/L `857/144/972`, unfinished `27`, failures `0`, mean `0.47125`, LCB `0.45802189803116894`, `rejected_strength`, checksum `d3b883442ec6107b`, artifact `8982375018`.
- Required lower confidence bound was strictly `> 0.5`; both protocols failed it. Unfinished-rate, correctness, and infrastructure gates passed, so the rejection is specifically strength-based.
- Opening file SHA-256 `6c3ff4cc9837bc66dd517d4a7c60d56e71a9b3a4e1fb1aabd904de81dad4e9b7`; semantic suite checksum `36c98c850cff76ba`; 1,200 unique deterministic first-party openings.
- The earlier SEE+LMR preselection was rejected without threshold relaxation at x86-64 `1.054297` and ARM64 `1.055081` versus the frozen `1.05` performance ceiling; its active candidate code was removed before PVS freeze.
- No production API, UCI, package version, safe facade, C ABI, JNI, Kotlin/Android interface, policy default, weights, benchmark reference, or activation state changed in S2-14.
- Final evidence record: `docs/RUST_CHESS_ENGINE_V0_2_S2_14_PRODUCTION_VALIDATION_2026-08-06.md`.

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
| S2-11 | Fresh profiling and measured hot-path decisions | **Complete — x86-64 sliding dispatch accepted; non-x86 baseline preserved** |
| S2-12 | Optional Syzygy tablebase decision/integration | **Complete — deferred; no compliant backend integrated; inactive** |
| S2-13 | API, UCI, ABI/JNI, Android, CI, and documentation integration | **Complete — internal candidate infrastructure integrated; public adapters unchanged; inactive** |
| S2-14 | Production candidate selection and validation | **Complete — PVS rejected_strength; v0.1 remains authoritative; inactive** |
| S2-15 | Separate activation and v0.2 release gate | **Skipped — activation precondition unsatisfied; no v0.2 promotion** |
| S2-16 | Final audit, report, and closure | **Complete — program closed without promotion; v0.1 remains authoritative** |

---

## Final closure rule

The program is truthfully closed without promotion. v0.1 remains authoritative until a future, separately specified strength program produces an accepted candidate and a distinct activation/release gate succeeds. No evidence in this report authorizes activating a rejected or deferred S2 candidate.
