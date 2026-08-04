# Rust Chess Engine Port Ralph Loop Status

**Updated:** 2026-08-04
**Branch:** `rust-engine`
**Authoritative TODO:** `docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md`  
**Current phase:** Task 23 robustness gate complete; Task 24 performance hardening is next while the independent Task 21 activation gate remains open

## Completed gates

| Task | Evidence SHA | CI run / job | Result |
|---:|---|---|---|
| 0 | `7ca6f8dc0d2577ca552a6bfe115828eb668d2133` | `30722127447` / `91427510964` | Python fast `1203`, slow `179`, perft `20/400/8902/197281`, UCI pass |
| 1 | `7ca6f8dc0d2577ca552a6bfe115828eb668d2133` | `30722127447` / `91427510938` | strict workspace gates pass |
| 2 | `b5f462aa73a69efcdc847ee215231a5064029902` | `30723952076` / `91432161445` | closure green; implementation tests `16` |
| 3 | `5578682bb2a6df5173ff7593649ac55509c277cd` | `30724744784` / `91434236030` | closure green; `24 passed` |
| 4 | `6cb975b35f4dbe898a0444b1b4c39778e89bcb40` | `30726795562` / `91439860915` | `35 passed`; all strict gates green |
| 5 | `78e9315369ff4552e5500d1a820767a1fd228f29` | `30727553897` / `91441947625` | closure green; implementation `42 passed` |
| 6 | `cb7124c5712f6b3f8f4540e9e8fabaa2aa242bc0` | `30727972433` | closure green; implementation `49 passed` |
| 7 | `334dc79b3ce0cbc1e7b5096387218c90a8365204` | `30730100518` / `91448776834` | closure green; implementation `59 passed` |
| 8 | `cecc39b9c9dcd8c90f9cdbdb4284be13c480bbd6` | `30730891252` / `91451022194` | closure green; implementation `67 passed` |
| 9 | `178583c15458cb29205201047bad8f4064a9342d` | `30731524205` / `91452671063` | strict implementation gate green; `72 passed` |
| 10 | `dd57b258fc8b9af647c30a1834f3d9e79a3d8ee3` | `30732542941` / `91455346591` | strict implementation gate green; `84 passed` |
| 11 | `1711fefe37b93163ec316ba9528742d6f87f8496` | `30733309460` / `91457298625` | strict gate, depth-four perft, and differential oracle green; 89 Rust tests |
| 12 | `d8547cc258ecc2e52b8e4eb7ef287d92d5d0a04f` | `30734451785` / `91460574656` | strict gate, depth-four perft, and differential oracle green; 103 Rust tests |
| Review fix | `81a7cd4a58a52695eca2ede10d5c73c803851d17` | `30739166607` / `91473334960` | strict gate, 112 Rust tests, depth-four perft, and differential oracle green |
| 13.1 | `7cf7fb027bf86f0658c14f4c9b452bce2cdcbe98` | `30741414286` / `91479443116` | unpruned reference negamax, 118 Rust tests, depth-four perft, and differential oracle green |
| 13.2 | `d662ca07cae6b0044c1ce620a0dc4f3249784d6c` | `30741988672` / `91480926153` | negamax alpha-beta, 124 Rust tests, depth-four perft, and differential oracle green |
| 13.3 | `bdf98a8e7c5cb6aadc55ba3638cd3af2f4ba9e91` | `30743024471` / `91483729312` | shallow equivalence, 127 Rust tests, depth-four perft, and differential oracle green |
| 13.4 | `3644e032504b604c210796f1e6c7ef056d05e94b` | `30743519630` / `91485044296` | completion/cancellation immutability, 131 Rust tests, depth-four perft, and differential oracle green |
| 13.5 / 13 | `7ca429b0c883bbb8484d3eb3a4af7d96cdb57201` | `30745120833` / `91489299233` | terminal/mate-distance fixtures and full Task 13 gate, 135 Rust tests, depth-four perft, and differential oracle green |
| 14.1 | `24e1090e17f8b39bdaac4989daffdeaea4b857e9` | `30749044761` / `91499685362` | correctness-first quiescence, 140 Rust tests, depth-four perft, and differential oracle green |
| 14.2 | `3688cb8e89a7da0c7fd34c3756d52d0fcc8d3d33` | `30753873602` / `91512570865` | bounded tactical ordering, 145 Rust tests, strict node-reduction witness, depth-four perft, and differential oracle green |
| 14.3 | `f08b2d519ffc066d8d6b18326e03ead278d908de` | `30762457921` / `91535329886` | bounded killer/history quiet ordering, 150 Rust tests, deterministic exact-score and strict node-reduction witnesses, depth-four perft, and differential oracle green |
| 14.4 | `dc758a3fc62e7f7002191993c73773dd2a71caef` | `30763226685` / `91537383867` | five explicit quiescence correctness witnesses, 155 Rust tests, depth-four perft, and differential oracle green |
| 14.5 / 14 | `f4dc989e97d8577f4c86bdbfb67ae47e3d5cd7f4` | `30764073097` / `91539614372` | permanent exclusion audit, exact-score boundary, 155 Rust tests, depth-four perft, and differential oracle green |
| 15.1 | `65ef70bfbff3d0bf5fd6e6a19ba20ed5214c3e26` | `30764647127` / `91541116562` | complete TT entry payload, five focused tests, 160 Rust tests, depth-four perft, and differential oracle green |
| 15.2 | `6b2ee0081cd47fd9069aeabb0d3ccb1d3659fea9` | `30765303745` / `91542820537` | fixed MiB storage, four-entry clusters, typed allocation failures, clear/generation operations, 165 Rust tests, depth-four perft, and differential oracle green |
| 15.3 | `ac68b99db53546c31f3aae68ad7337ba256eb982` | `30766126491` / `91545080021` | ply-correct mate normalization, typed conversion failures, six focused tests, 171 Rust tests, depth-four perft, and differential oracle green |
| 15.4 | `b6a015e6cc519aa0bbc8e7bde7dde06bdd660b44` | `30766760085` / `91546779835` | complete-key, depth- and bound-safe probes, repetition suppression, eight focused tests, 179 Rust tests, depth-four perft, and differential oracle green |
| 15.5 | `775013a6e11aad7625c88b0cd3b258819211e839` | `30767556904` / `91548869513` | deterministic same-key updates and depth/age replacement, five focused tests, 184 Rust tests, depth-four perft, and differential oracle green |
| 15.6 | `bd4d5d581c0e82f892435b2874732ac632c2e1f5` | `30768512470` / `91551420579` | bounded counters and hash-full sampling, reproducible probe/store benchmark, four focused tests, 188 Rust tests, depth-four perft, and differential oracle green |
| 15 / gate | `682114cd2452b04e1f24af1150928baaff779aa8` | `30770018597` / `91555458016` | production alpha-beta integration, 193 Rust tests, two release node-reduction witnesses, depth-four perft, and differential oracle green |
| 16.1 | `886ad953952b3a409800fcf7e8699365f94f0271` | `30772536115` / `91562076526` | full-window iterative deepening, five focused tests, 198 Rust tests, depth-four perft, and differential oracle green |
| 16.2 | `8af24520fd72faffff1cab74581f056a083cfb13` | `30779589438` / `91581508274` | bounded aspiration retries, fail-low/fail-high exact recovery, 206 Rust tests, depth-four perft, and differential oracle green |
| 16.3 | `e8afc9959a60519c6d5617963521e1707d37c6a9` | `30776274173` / `91572310565` | safe legal PV reconstruction, ponder support, 204 Rust tests, depth-four perft, and differential oracle green |
| 16.4 | `8a48ee45199e58db76adee4e4fc4adaf131566d2` | `30780915406` / `91585230626` | typed depth/node/time/infinite/stop limits, partial-depth discard, 214 Rust tests, depth-four perft, and differential oracle green |
| 16.5 | `128f52e8fb7d7e9974605fc840eb13d3ecc021a6` | `30782361257` / `91589434579` | one-node cancellation bound, deterministic fallback, latency benchmark, 218 Rust tests, depth-four perft, and differential oracle green |
| 16.6 | `dcde800f4c5a08c07fe57724ed672f2abd122157` | `30783666840` / `91593059900` | unified typed result snapshot, request-wide node/qnode/seldepth/time accounting, 222 Rust tests, depth-four perft, and differential oracle green |
| 16.7 | `836ca0563f9a8dce44eb78997e28335a9d8fcdce` | `30785853401` / `91599164384` | explicit one-ply-per-line check extension, path-safe TT/PV policy, diagnostics, 229 Rust tests, depth-four perft, and differential oracle green |
| 16 / gate | `836ca0563f9a8dce44eb78997e28335a9d8fcdce` | `30785853401` / `91599164384` | all iterative-deepening, aspiration, PV, limit, cancellation, result, and bounded-extension integration gates green |
| 17.1 | `60f70463c9ad9abf99c8b3d7923df8037bc6f894` | one-shot full preflight | protocol session, transactional position replay, typed go requests, 18 focused tests, and full workspace gate green |
| 17.2 | `d058353692f9f7c350e55dfae2d1a7c21ac64666` | documented permanent gate | adapter-owned worker, request-local cancellation, deterministic joins |
| 17.3 | `1c71f8dfa8449190ea8ae860386b6566b9176cbd` | documented permanent gate | side-to-move clock allocation with soft/hard budgets and safety reserve |
| 17.4 | `0f0ed39b31aca077173359c5807c1afaffb3e9e4` | final permanent gate recorded in output contract | synchronized iteration info, typed scores, nodes/NPS/time/hashfull/PV, exactly-once bestmove |
| 17.5 / 17 gate | `67b6c97a476e1323bc2bd96ecf14870fc2ed3139` | `30828959858` / `91737751003` | seven real subprocess workflows, bounded stop/quit, legal best moves, terminal null moves, and concurrent-session isolation; complete permanent gate green |
| 18.1 | `fc375ce7c35a9b8e82c83c8a0ac54e23a60986be` | `30832682431` / `91750223690` | safe stateful facade, transactional positions, legal UCI moves, immutable synchronous search, cross-thread cancellation, identities, and ownership/thread-safety contract; 285 Rust tests green |
| 18.2 | `d1c4a9195acfc63dc2f9af52531c4ba01e9a2dc9` | `30836228692` / `91761964507` | versioned opaque-token C ABI, explicit UTF-8 lengths, typed errors, verified owned buffers, synchronous search/cancellation boundary, and panic containment; 291 Rust tests green |
| 18.3 | `0789ac65590ccafb55b2b86b73873edfba1c7b55` | `30841137129` / `91778174797` | complete Rust-through-ABI lifecycle, 128× engine/cancellation churn, invalid-input preservation, active cross-thread cancellation, exact buffer ownership, and exported test-fault containment; 297 Rust tests green |
| 18.4 | `466c7b504832afa2bf993cb10dcc0c12aefcf1c5` | `30844134371` / `91788114660` | Android JNI exports and typed Kotlin owner, background search, request-local cancellation, error mapping, deterministic close/reaper policy, nine focused JNI tests, 306 Rust tests, and AArch64 ELF proof `1fc49b6126ecb9faa4c0f167b272945d65aebbf1` green |
| 18.5 / 18 gate | `0af14c4bdb7e8de645f27182a788e5eef5297d5f` | Rust `30847895229` / `91800574469`; Android `30847895345` / `91800574845`, `91800574914` | real host JVM JNI contract, ARM64/x86_64 Android builds, API-35 emulator lifecycle, live off-main native-search proof, 24 host and 16 Android repeated lifecycles; complete Task 18 gate green |
| 19.1 | `6ce31141d0d4516696f1e9d17ee018606ef7bd4b` | Rust `30852253445` / `91814805656`; Android `30852253399` / `91814815286`, `91814815151` | adapter-neutral `chess-book` crate, typed `OpeningBook`/`BookProvider`, generic weighted `BookMove`, four focused tests, no core/search I/O dependencies; 310 Rust tests and Android regressions green |
| 19.2 | `781e876563e8b21bb50e6fa83af6afe92b260910` | Rust `30855596855` / `91825754603`; Android `30855596897` / `91825818389`, `91825818440` | version-1 project-specific fixed-record indexed format, canonical four-field FEN keys, little-endian schema, header/payload CRC-32, strict structural corruption rejection, seven focused tests; 317 Rust tests and Android regressions green |
| 19.3 | `82b5100f501fe4e4a845d5fb3bdbb1c8fe7d34ef` | Rust `30859905206` / `91839380997`; Android `30859905203` / `91839428990`, `91839429013` | exact indexed UCI-to-legal-move resolution, generic candidate revalidation, deterministic highest-weight policy with canonical tie ordering, explicit local-seed SplitMix64 weighted policy, six focused tests; 323 Rust tests and Android regressions green |
| 19.4 | `5b8e2117c64922e97cbe356caa44a51075da7b52` | Rust `30863525297` / `91850371126`; Android `30863525289` / `91850370864`, `91850370917` | explicit UCI `OwnBook` and `--book` injection, safe-facade policy/configuration, additive C ABI/JNI byte injection, Android asset adapter, and disabled/absent/no-entry search fallback; 328 Rust tests and Android regressions green |
| 19.5 / 19 gate | `5d70737bf12cbfa16441730b7a64629212b28683` | Rust `30867122750` / `91861324627`; Android `30867122736` / `91861324588`, `91861324637` | four public-API regressions, permanent no-auto-discovery audit, 332 Rust tests, release perft, differential oracle, host JVM, dual-ABI Android, APK, and API-35 instrumentation green; Task 19 complete |
| 20 / gate | `1fae5fa8d830a524d6ff8d36ba42ed557112c79a` | Rust `30875333307` / `91885547979`; Android `30875333292` / `91885547947`, `91885547972` | deterministic offline self-play, strict version-1 game/position datasets, replay validation, full provenance, explicit splitting/filtering, four focused regressions, 336 Rust tests, release perft, differential oracle, host JVM, dual-ABI Android, APK, and API-35 instrumentation green; merged `333398c5913309193cb81b91c4af3deff2fd5adf` |
| 21.1 | `8410beb6dc22684052ded86a6f2fe71cf9d1e444` | Rust `30889939723 / 91929495312`; Android `30889939726 / 91929459955, 91929459977, 91929460081` | stable 810-scalar named schema, separately versioned structural evaluator contract, strict named artifacts, complete training provenance, semantic checksums, and all permanent gates green |
| 21.2 | `3d11b01a9de84913c6c1bfa43a37aea0197dc5be` | Rust `30894313165` / `91943462745`; Android `30894313169` / `91943477000`, `91943477036`, `91943477212` | side-to-move logistic targets, explicit training-only K calibration, occurrence-weighted MSE, held-out validation, strict Task 20 adapter, typed failure policy, and all permanent gates green |
| 21.3 | `fc69d7d7554ab325fd72ccfc5ac94c4bb1077ae8` | Rust `30897085986` / `91952447573`; Android `30897085023` / `91952460052`, `91952460064`, `91952460121` | deterministic seeded SPSA over the 810-scalar schema, explicit bounds and L2 regularization, training/validation isolation, checksummed data/config-bound resumable checkpoints, and all permanent gates green |
| 21.4 | `fd179e57462226392ab9c61bc9f26bc7cbb63cc1` | Rust `30929481202` / `92060204891`; Android `30929479894` / `92060200320`, `92060200325`, `92060200573` | versioned checksummed reports with initial/final train and validation MSE, all 810 named deltas, complete data/engine/source/checkpoint/weight identities, exact command/configuration, atomic persistence, inactive candidate artifacts, and all permanent gates green |
| 21.5 | `664bf7cb51fae8bff8298925513b242fd9f33cee` | Rust `30935448972` / `92080314407`; Android `30935448944` / `92080314104`, `92080314087`, `92080314012`; control `30935079798` / `92079069382` | explicit weighted search, correctness-first validation, 200 distinct color-balanced opening pairs, fixed provenance, one-sided 95% strength gate, atomic inactive evidence, 400-game baseline control correctly rejected, and all permanent gates green |
| 22 / gate | `3653f86148dca0bb7f4168706ffc47a28bc4a10e` | `30938602274` / `92090934559` | eight-area protocol, symmetry/cost/search/match evidence, explicit rejection decisions, checksum `0ad7dcc3dda4cdfb`, no activation |
| 23.1 | `4483c1661a975bc9f64c1f725618930e31968e74` | Rust `30940733222` / `92098127153`; Android `30940732968` / `92098189450`, `92098189412`, `92098189386` | deterministic legal-position properties cover square/move/FEN, make/unmake, hash, legal-move safety, internal invariants, evaluator symmetry, and legal reversible PVs; all permanent gates green |
| 23 / gate | `469c9c67ab53c276509fc7bad0c4adc209c815b7` | Robustness `30944117733 / 92109744098, 92109744189, 92109744065`; Rust `30944118025 / 92109744577`; Android `30944117802 / 92109760102, 92109760118, 92109760076` | seven fuzz targets / 1,792 bounded runs, Miri, ASan/LSan, TSan, one minimized permanent C ABI regression found and fixed; complete gate green |

## Task 17.1 completion

Implemented and validated:

- Linux stdin/stdout protocol entry point through `chess_uci::run_stdio`;
- reusable buffered `run_protocol_loop` without process-global I/O redirection;
- stateful `UciSession` ownership of one exact `Game` and supported options;
- UCI handshake, readiness, new-game reset, supported options, start-position and strict six-field FEN setup;
- transactional legal move replay with fail-visible malformed and illegal input handling;
- typed depth, node, move-time, clock, increment, moves-to-go, and infinite search requests;
- immutable game/options snapshots for the Task 17.2 worker boundary;
- distinct stop and quit events and clean buffered shutdown;
- `docs/RUST_UCI_PROTOCOL_LOOP.md`.

Evidence:

- Exact validated implementation SHA: `60f70463c9ad9abf99c8b3d7923df8037bc6f894`.
- Focused UCI tests: 18 passed.
- Full validation: rustfmt, locked workspace all-target check, strict Clippy with warnings denied, focused UCI tests, and complete workspace tests passed.
- First preflight correction removed one unnecessary leaked option-name allocation; the second corrected five test-only response borrows. No production behavior was weakened and no lint suppression was added.
- Task 17.2 owns the search worker, explicit stop-token lifecycle, and clean join behavior. Task 17.3 owns clock allocation, and Task 17.4 owns search output and `bestmove`.

## Task 17.4 completion

Implemented and validated in the Task 17.4 slice:

- protocol-neutral completed-iteration observation in `chess-search`;
- synchronized adapter output while the protocol thread waits for input;
- periodic exact-depth UCI information with typed score, nodes, NPS, time, hash fullness, and legal PV;
- exactly one final best move for natural completion and explicit stop;
- optional ponder from the legal PV;
- `bestmove 0000` for no-legal-move roots;
- stale-result suppression after position/new-game replacement, quit, EOF, and drop;
- fail-loud output errors tied into request-local cancellation;
- focused observer, formatter, lifecycle, and output-failure tests;
- `docs/RUST_UCI_SEARCH_OUTPUT.md`.

Implementation SHA: `0f0ed39b31aca077173359c5807c1afaffb3e9e4`.

Task 17.5 owns complete process transcripts and common GUI workflow integration tests.


## Task 17.5 and Task 17 gate completion

Implemented and validated:

- a real subprocess harness around the Cargo-built `chess-uci` executable;
- exact handshake and readiness transcripts;
- start-position replay and strict six-field FEN workflows;
- fail-visible, transactional illegal move handling;
- legal fixed-depth best moves checked against `chess-core`;
- checkmate and stalemate `bestmove 0000` behavior;
- bounded active-search `stop` and `quit` behavior;
- two concurrent engine sessions with isolated state and stdout;
- `docs/RUST_UCI_PROCESS_INTEGRATION.md`.

Evidence:

- implementation SHA: `67b6c97a476e1323bc2bd96ecf14870fc2ed3139`;
- permanent CI run/job: `30828959858` / `91737751003`;
- seven subprocess integration tests passed;
- the complete permanent workspace gate passed without lint suppression or production-code changes.

Task 17 is complete. Task 18.1 Rust facade work is next.


## Task 18.1 completion

Implemented and validated:

- `EngineConfig` with explicit fixed transposition-table capacity;
- stateful `Engine::new` owning one `Game` and one bounded table;
- transactional set/reset position and canonical FEN retrieval;
- deterministic legal UCI moves, legal move application, and game status;
- synchronous limit-controlled search on detached position/history state;
- clone-shareable request-local cancellation, including active infinite-search cancellation from another thread;
- engine version and validated baseline evaluation-weight identity;
- typed facade errors and explicit allocation failures;
- ownership and thread-safety rustdoc with compiler-derived `Send`/`Sync` assertions;
- a safe module that forbids unsafe code;
- `docs/RUST_SAFE_ENGINE_FACADE.md`.

Evidence:

- implementation SHA: `fc375ce7c35a9b8e82c83c8a0ac54e23a60986be`;
- permanent CI run/job: `30832682431` / `91750223690`;
- nine focused safe-facade tests passed;
- 285 executed non-doc Rust tests passed;
- the complete permanent workspace gate and independent differential oracle passed without lint suppression or lower-layer production changes.

Task 18.1 is complete. Task 18.2 C ABI work is next.


## Task 18.2 completion

Implemented and validated:

- stable ABI version `1` and exact-size versioned C records;
- opaque tagged engine and cancellation tokens with synchronized registry ownership;
- explicit create, destroy, reset, position, FEN, legal move, move application, status, weight identity, search, and cancellation operations;
- explicit-length UTF-8 input with no NUL dependency;
- structured result codes and thread-local retrievable errors;
- registry-owned immutable output bytes with verified single-free contracts;
- typed search snapshots with move/PV buffers, score, depth, nodes, time, termination, and fallback;
- null, stale, destroyed, fabricated, and wrong-type handle rejection without dereferencing caller tokens;
- `catch_unwind` containment at every exported boundary;
- `rlib`, `cdylib`, and `staticlib` products plus `crates/chess-ffi/include/chess_engine.h`;
- `docs/RUST_C_ABI.md`.

Evidence:

- implementation SHA: `d1c4a9195acfc63dc2f9af52531c4ba01e9a2dc9`;
- permanent CI run/job: `30836228692` / `91761964507`;
- six focused C ABI tests passed;
- 291 executed non-doc Rust tests passed;
- the complete permanent workspace gate and independent differential oracle passed without lint suppression or lower-layer production changes.

Task 18.2 is complete. Task 18.3 C ABI tests are next.


## Task 18.3 completion

Implemented and validated:

- a dedicated Rust-through-ABI harness that imports only the public C boundary;
- complete create, position, legal-move, play, status, search, reset, cleanup, and destroy workflow coverage;
- 128 repeated engine lifecycles and 128 repeated cancellation-token lifecycles with uniqueness and stale-token rejection;
- fail-loud null, UTF-8, FEN, move, flag, versioned-record, and output-pointer tests with exact state preservation;
- active infinite search on a worker thread, cancellation through a separate token, caller-visible token destruction, and bounded retained-reference completion;
- individual and compound output-buffer validation, all-or-nothing cleanup, stale-copy rejection, and repeatable empty cleanup;
- a non-default feature-gated exported panic fault that returns the contained-panic code and leaves the process usable;
- `docs/RUST_C_ABI_TESTS.md`.

Evidence:

- implementation SHA: `0789ac65590ccafb55b2b86b73873edfba1c7b55`;
- permanent CI run/job: `30841137129` / `91778174797`;
- six focused Task 18.3 lifecycle tests passed;
- 297 executed non-doc Rust tests passed;
- the complete permanent workspace gate and independent differential oracle passed without lint suppression or lower-layer production changes;
- the first validation correction was canonical rustfmt plus removal of one scheduler-sensitive assertion, with no product or gate weakening.

Task 18.3 is complete. Task 18.4 Android JNI is next.


## Task 18.4 completion

Implemented and validated:

- an Android `cdylib` adapter over the existing stable C ABI, with no duplicate engine registry or chess/search implementation;
- sixteen JNI exports for engine lifecycle, positions, legal moves, move/status, identity, search, and cancellation;
- shared panic containment and typed Java exception construction preserving stable native result codes;
- exact opaque-token bit preservation between Rust `u64` and JVM `long`;
- a typed Kotlin `Closeable` owner with deterministic handle destruction, lifecycle locking, one outstanding search, and a phantom-reference fallback;
- a private single-thread search worker so the public Kotlin API never runs synchronous native search on the caller thread;
- request-local cross-thread cancellation and cleanup in all completion paths;
- a locked NDK API-24 AArch64 build script producing and verifying `libchess_jni.so`;
- six bridge tests and three Kotlin/Rust source-contract tests;
- `docs/RUST_ANDROID_JNI.md`.

Evidence:

- host implementation SHA: `466c7b504832afa2bf993cb10dcc0c12aefcf1c5`;
- permanent host CI run/job: `30844134371` / `91788114660`;
- follow-up permanent CI run/job: `30844338897` / `91788828855`;
- Android AArch64 proof and one-shot cleanup SHA: `1fc49b6126ecb9faa4c0f167b272945d65aebbf1`;
- nine focused JNI tests and 306 executed non-doc Rust tests passed;
- the complete permanent workspace gate, authoritative release perft, and independent differential oracle passed without lint suppression or lower-layer behavior changes;
- the Android proof required a nonempty AArch64 ELF shared object and the exported JNI search symbol before its temporary workflow could remove itself.

Task 18.4 is complete. Task 18.5 Android harness work is next, and the overall Task 18 gate remains open.


## Task 18.5 and Task 18 completion

Implemented and validated:

- one pinned Gradle harness whose host and Android modules compile the exact production Kotlin wrapper;
- a real host JVM contract against the release JNI shared library, with four passing tests and 24 repeated lifecycles;
- explicit API-24 ARM64 and x86_64 Rust/NDK builds, ELF verification, symbol verification, and generated-artifact staging;
- a minimal Android sample controller and Android library/test APK;
- three passing tests on an Android 15/API-35 x86_64 emulator, including 16 repeated lifecycles;
- executable UI-thread exclusion: a request begins on the Android main loop while the synchronous native method is observed on `chess-engine-search`;
- permanent read-only Rust and Android CI, exact local commands, ownership policy, and generated-artifact policy;
- `docs/RUST_ANDROID_TEST_HARNESS.md`.

Evidence:

- exact validated implementation SHA: `0af14c4bdb7e8de645f27182a788e5eef5297d5f`;
- Rust run/job: `30847895229` / `91800574469`;
- Android run: `30847895345`;
- host JVM job: `91800574845`;
- Android emulator job: `91800574914`;
- NDK 29.0.14206865, Android clang 21.0.0, Java 17.0.19, Gradle 8.9, AGP 8.7.3, Kotlin 2.0.21, compile SDK 35, minimum/link API 24, and emulator 37.1.11.0;
- four host JVM tests and three emulator tests passed;
- both nonempty JNI libraries had the correct ELF machine and exported `nativeSearch` symbol;
- the complete permanent Rust quality, perft, documentation, build, and differential-oracle gate passed.

Task 18 is complete. Task 19.1 opening-book abstraction is next.

## Task 12 completion

Implemented and validated:

- typed centipawn scores from the side-to-move negamax perspective;
- a static-evaluation range separated from distance-aware mate scores;
- color, side-to-move, and vertical-mirror symmetry tests;
- tapered middlegame/endgame material and piece-square evaluation;
- mobility, pawn structure, bishop pair, rook activity, king safety, space, and king activity terms;
- fixed, allocation-free normal evaluation and fixed trace structures;
- exact trace-component summation against normal evaluation;
- typed and named phased weights with explicit defaults;
- versioned weight sets with stable identifiers and canonical checksums;
- validated explicit serialization in `chess-tools` with no automatic file discovery;
- stable evaluator trace and per-group benchmark commands;
- benchmark evidence for every major evaluator group;
- exclusion audit against transcript-specific and exact-scenario Python patches;
- `docs/RUST_BASELINE_EVALUATOR.md`.

Evidence:

- Formatted implementation head: `d8547cc258ecc2e52b8e4eb7ef287d92d5d0a04f`.
- Permanent implementation CI run/job: `30734451785` / `91460574656`.
- Results: workspace assets, lockfile, metadata, rustfmt, Cargo check, Clippy with `-D warnings`, 103 executed Rust tests, release depth-four perft, rustdoc with `-D warnings`, debug build, release build, and independent differential validation passed.
- Benchmark/tooling run/job: `30734335652` / `91460185440`.
- Full starting-position release evaluation: 20,000 iterations in 19,596,825 ns, approximately 979.8 ns per evaluation on the hosted runner.
- Baseline weight identifier/checksum: `424153454c494e45` / `d2cca7ae10ec6e34`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime and dependency `punycode` deprecation notices only.
- Task 13 owns correctness-first reference search and alpha-beta over this evaluator.

## Pre-Task-13 review-fix completion

Implemented and validated:

- opaque source-bound legal-move tokens usable by `chess-search`;
- bounded deterministic legal-token storage;
- valid-token application without legal-list regeneration;
- non-mutating stale and wrong-origin token rejection;
- exact token make/unmake and Zobrist restoration;
- cross-crate token API coverage in `chess-search`;
- explicit `Game::reset_to_starting` and `Game::set_position`;
- fresh-root move, hash, repetition, status, and search-history semantics;
- stable `elapsed_nanos` divide output;
- explicit strict structural analysis-FEN policy and downstream safety tests;
- corrected Task 25 coverage and Task 13 next-operation text;
- completed review-fix spec and TODO documents.

Evidence:

- Starting code/documentation SHA: `52377d09b713541044e24c8e3559be3f12002cc1`.
- Validated implementation SHA: `81a7cd4a58a52695eca2ede10d5c73c803851d17`.
- One-shot implementation control run: `30738801841`.
- Permanent implementation CI run/job: `30739166607` / `91473334960`.
- Results: workspace assets, lockfile, metadata, rustfmt, Cargo check, Clippy with `-D warnings`, 112 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with `-D warnings`, debug build, release build, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime and dependency `punycode` deprecation notices only.
- Temporary implementation and closure workflows/scripts were removed.
- Clean code/workflow SHA `9c27d2c1c4a39a975b30d3357b69b6c96bb64c68` compared against the validated candidate with zero changed files.
- Later commits finalize documentation only; they do not change the validated Rust or permanent workflow tree.
- No pull request was created.

## Task 13.1 completion

Implemented and validated:

- unpruned, full-tree reference negamax in `chess-search`;
- public score, deterministic best-move, and node-count result API;
- legal-token make/unmake with no clone-per-child;
- detached root plus reversible line repetition history;
- checkmate, stalemate, dead-position, repetition, fifty-move, and seventy-five-move scoring;
- checkmate precedence over a simultaneous move-count threshold;
- ply-relative mate scores;
- fail-loud history/root mismatch, depth-domain, and node-overflow errors;
- exact root position, Zobrist, and history restoration;
- `docs/RUST_REFERENCE_SEARCH.md`.

Evidence:

- Exact validated implementation SHA: `7cf7fb027bf86f0658c14f4c9b452bce2cdcbe98`.
- Permanent CI run/job: `30741414286` / `91479443116`.
- Results: workspace assets, lockfile, metadata, rustfmt, Cargo check, Clippy with `-D warnings`, 118 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with `-D warnings`, debug build, release build, and independent differential validation passed.
- Starting-position depth-two reference search visits exactly `421` nodes.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 13.2 remains not started.

## Task 13.2 completion

Implemented and validated:

- recursive fail-soft negamax alpha-beta with no maximizing/minimizing dual branches;
- full-window exact root search and recursive `(-beta, -alpha)` windows;
- side-to-move scoring and ply-relative mate distance;
- deterministic first-best tie behavior and legal root best moves;
- source-bound legal tokens, make/unmake, and detached line history;
- game-root plus search-line repetition handling;
- checked node accumulation and fail-loud root-history/depth validation;
- exact root position, Zobrist, and history restoration;
- a starting-position depth-three pruning regression below the complete `9,323`-node tree;
- `docs/RUST_NEGAMAX_ALPHA_BETA.md`.

Evidence:

- Exact validated implementation SHA: `d662ca07cae6b0044c1ce620a0dc4f3249784d6c`.
- Permanent CI run/job: `30741988672` / `91480926153`.
- Results: workspace assets, lockfile, metadata, rustfmt, Cargo check, Clippy with `-D warnings`, 124 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with `-D warnings`, debug build, release build, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 13.3 is complete.

## Task 13.3 completion

Implemented and validated:

- curated shallow score equivalence across quiet, tactical, terminal-adjacent, terminal, rule-draw, and repetition-aware positions;
- an independent root-child score oracle proving `d1d8` is the tactical fixture’s unique exact best move;
- alpha-beta node counts no greater than reference counts on every fixture;
- at least one strict pruning witness;
- exact root position, incremental Zobrist, and detached-history restoration after each paired successful search;
- `crates/chess-search/tests/search_equivalence.rs`;
- `docs/RUST_SEARCH_EQUIVALENCE.md`.

Evidence:

- Exact validated implementation SHA: `bdf98a8e7c5cb6aadc55ba3638cd3af2f4ba9e91`.
- Permanent CI run/job: `30743024471` / `91483729312`.
- Results: workspace assets, lockfile, metadata, rustfmt, Cargo check, Clippy with `-D warnings`, 127 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with `-D warnings`, debug build, release build, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 13.4 is complete.

## Task 13.4 completion

Implemented and validated:

- a public `SearchCancellationProbe` callback boundary implemented automatically by `FnMut() -> bool` closures;
- cancellable reference and alpha-beta entry points while preserving the existing never-cancel convenience APIs;
- cancellation checks at node and child boundaries;
- restoration-before-propagation for every recursive child result, including cancellation;
- explicit cancellation error variants with no incomplete score, move, node count, or principal variation;
- repeated-search stability on one mutable game-derived position and detached history;
- mid-tree cancellation after 64 probe checks for both search implementations;
- invariant, incremental/recomputed Zobrist, position snapshot, and history snapshot checks after completion, terminal resolution, validation failure, and cancellation;
- `crates/chess-search/tests/search_immutability.rs`;
- `docs/RUST_SEARCH_IMMUTABILITY.md`.

Evidence:

- Exact validated implementation SHA: `3644e032504b604c210796f1e6c7ef056d05e94b`.
- Permanent CI run/job: `30743519630` / `91485044296`.
- Results: workspace assets, lockfile, metadata, rustfmt, Cargo check, Clippy with `-D warnings`, 131 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with `-D warnings`, debug build, release build, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 13.5 and the overall Task 13 gate are complete; Task 16 still owns full limits, stop-token, iterative-deepening, and partial-result policy.

## Task 13.5 and Task 13 completion

Implemented and validated:

- fixed one-node terminal roots for checkmate precedence, stalemate, dead position, fifty/seventy-five-move draws, and threefold/fivefold repetition draws;
- exact reference/alpha-beta score, best-move, and node-count agreement;
- a shorter-mate witness where `f7e8` is `mate_in(1)` and `f7a7` is `mate_in(3)`;
- a longer-survival witness where `h8g7` is `mated_in(6)` and `h8h7` is `mated_in(4)`;
- deterministic immediate-mate selection at the winning root and unique `h8g7` selection at the forced-loss root;
- explicit one-ply mate normalization for independently searched child roots;
- exact logical-position, detached-history, invariant, and incremental/recomputed-Zobrist restoration after every full-root and per-move oracle search;
- `crates/chess-search/tests/search_terminals.rs`;
- `docs/RUST_SEARCH_TERMINAL_FIXTURES.md`.

Evidence:

- Exact validated implementation SHA: `7ca429b0c883bbb8484d3eb3a4af7d96cdb57201`.
- Permanent CI run/job: `30745120833` / `91489299233`.
- Results: workspace assets, lockfile, metadata, rustfmt, Cargo check, Clippy with `-D warnings`, 135 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with `-D warnings`, debug build, release build, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 13 is complete; Task 14.1 quiescence is next.

## Task 14.1 completion

Implemented and validated:

- standalone and alpha-beta-integrated fail-soft quiescence search;
- stand-pat only outside check and every legal evasion while checked;
- deterministic capture and promotion expansion through source-bound legal tokens;
- shared mate, stalemate, dead-position, repetition, and move-count draw semantics;
- cancellation checks at node and tactical-child boundaries with restoration before error propagation;
- a fail-loud 64-ply tactical guard, including explicit failure when the side remains in check;
- a separate unpruned reference search with quiescence leaves while preserving the original static Task 13 reference API;
- matching-oracle score and node-count equivalence on bounded fixtures;
- fixed hanging-capture, quiet-evasion, promotion, poisoned-capture, draw, cancellation, and guard regressions;
- exact root position, detached history, invariant, and incremental/recomputed-Zobrist restoration;
- `crates/chess-search/tests/search_quiescence.rs` and `docs/RUST_QUIESCENCE_SEARCH.md`.

Evidence:

- Exact validated implementation SHA: `24e1090e17f8b39bdaac4989daffdeaea4b857e9`.
- Permanent CI run/job: `30749044761` / `91499685362`.
- Results: workspace assets, lockfile, metadata, rustfmt, Cargo check, Clippy with `-D warnings`, 140 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with `-D warnings`, debug build, release build, and independent differential validation passed.
- Dedicated quiescence suite: 5 passed; matching reference/alpha-beta equivalence suite: 3 passed; terminal/mate-distance suite: 4 passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Tasks 14.2 and 14.3 ordering are complete. Task 14.4 correctness consolidation, Task 15 transposition storage, and Task 16 production limits remain open.

## Task 14.2 completion

Implemented and validated:

- fixed-capacity stack-backed stable ordering over opaque legal-move tokens;
- an explicit transposition-table move hook that returns `None` until Task 15;
- promotion ordering by promoted-piece value, including promotion captures;
- MVV-LVA capture ordering with explicit en-passant pawn-victim semantics;
- generation-stable remaining moves and equal-key ties;
- tactical ordering in production alpha-beta and quiescence search;
- exact generation-order control policy in the unpruned reference search;
- a typed alpha-beta window that preserves the strict lint-clean recursive boundary;
- a fixed narrow-window node-reduction witness with identical fail-soft score and best move;
- exact position, detached-history, invariant, and incremental/recomputed-Zobrist restoration;
- `crates/chess-search/src/move_ordering.rs` and `docs/RUST_TACTICAL_MOVE_ORDERING.md`.

Evidence:

- Exact validated implementation SHA: `3688cb8e89a7da0c7fd34c3756d52d0fcc8d3d33`.
- Permanent CI run/job: `30753873602` / `91512570865`.
- Results: workspace assets, lockfile, metadata, rustfmt, Cargo check, Clippy with `-D warnings`, 145 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with `-D warnings`, debug build, release build, and independent differential validation passed.
- New coverage: four move-ordering unit tests and one quiescence narrow-window node-reduction test.
- Existing search-equivalence, immutability/cancellation, quiescence, terminal/mate-distance, perft, and differential suites remained green.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- SEE remains intentionally absent; Task 14.3 now owns bounded killer/history/stable-tie quiet ordering, while Tasks 15 and 16 own TT storage and real previous-PV data.

## Task 14.3 completion

Implemented and validated:

- fixed-capacity, search-local quiet-ordering state with two killer slots at every supported ply;
- a fixed `2 x 64 x 64` history table keyed by side, source, and destination;
- quiet-cutoff-only learning with depth-squared saturating history bonuses;
- explicit capture/promotion exclusion from killer and history updates;
- deterministic order after tactical moves: primary killer, secondary killer, descending history, then ascending packed move identity;
- an explicit previous-PV hook that remains `None` until Task 16 provides completed-iteration PV data;
- production alpha-beta integration through a lint-clean recursive context carrying ordering state and cancellation;
- generation-order reference control and retained Task 14.2 tactical control;
- exact full-window determinism and a fixed seeded-killer narrow-window node-reduction witness;
- exact position, detached-history, invariant, and incremental/recomputed-Zobrist restoration;
- `docs/RUST_QUIET_MOVE_ORDERING.md`.

Evidence:

- Exact implementation SHA: `f08b2d519ffc066d8d6b18326e03ead278d908de`.
- Focused implementation run/job: `30762211967` / `91534658841`; Cargo check, strict Clippy, and all 51 `chess-search` tests passed.
- Full closure validation run/job: `30762457921` / `91535329886`.
- Results: workspace assets, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 150 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 14.4 consolidated correctness tests are complete; Tasks 14.5, 15, and 16 remain intentionally open.

## Task 14.4 completion

Implemented and validated:

- a true multi-capture horizon sequence (`Qxe5 Rxe5 Rxe5`) searched to a quiet position;
- an in-check leaf that must search a quiet legal evasion and cannot stand pat;
- a promotion sequence searched through forced recapture and counter-recapture;
- a poisoned capture whose static leaf score is explicitly corrected downward by quiescence before root move selection;
- finite guard behavior: one-node stand-pat outside check and fail-loud refusal to truncate while checked;
- exact position, detached-history, invariant, and incremental/recomputed-Zobrist restoration on every new path;
- `crates/chess-search/tests/search_quiescence_task_14_4.rs`.

Evidence:

- Exact validated implementation/evidence SHA: `dc758a3fc62e7f7002191993c73773dd2a71caef`.
- Permanent CI run/job: `30763226685` / `91537383867`.
- Results: workspace assets, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 155 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Dedicated Task 14.4 suite: 5 passed; original quiescence suite: 5 passed; search-equivalence suite: 3 passed; immutability suite: 4 passed; terminal/mate-distance suite: 4 passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 14.5 explicit-exclusion audit and the overall Task 14 gate are complete.

## Task 14.5 and Task 14 completion

Implemented and validated:

- a permanent CI audit over all 10 production `chess-search` Rust modules;
- fail-loud rejection of transcript/review-loop and anti-drift/scenario-scoring identifiers;
- an exact nine-field `MoveOrderKey` boundary containing only TT/PV hooks, tactical material categories, killers, history, and the stable encoded tie-break;
- a restricted ordering read boundary of `Position::piece_at` and `Position::side_to_move` only;
- fail-loud rejection of strategic evaluator identifiers in production move ordering;
- structural enforcement that root alpha-beta uses the complete score window and replaces the best move only for a strictly greater searched score;
- required exact-score and node-reduction witnesses retained in the Rust test tree;
- `scripts/task_14_5_exclusion_audit.py` and `docs/RUST_SEARCH_ORDERING_EXCLUSION_AUDIT.md`.

Evidence:

- Exact validated implementation SHA: `f4dc989e97d8577f4c86bdbfb67ae47e3d5cd7f4`.
- Permanent CI run/job: `30764073097` / `91539614372`.
- Audit output: 10 production Rust files scanned; approved nine ordering fields; ordering position queries limited to `piece_at` and `side_to_move`; all four exact-score/node-reduction witnesses present.
- Results: workspace assets, exclusion audit, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 155 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 14 is complete; Tasks 15.1–15.3 are complete and Task 15.4 safe probe semantics is next.

## Task 15.1 completion

Implemented and validated:

- a complete copyable transposition-entry payload in `crates/chess-search/src/transposition.rs`;
- the full 64-bit Zobrist verification key rather than an index-only fragment;
- `u16` depth and explicit one-byte `Exact`, `Lower`, and `Upper` bound tags;
- a distinct `TranspositionScore` storage-domain wrapper around `Score`;
- optional compact best-move identity and one-byte generation metadata;
- stable public accessors and `chess-search` re-exports;
- a bounded, predictable `repr(C)` layout of at most 24 bytes on supported targets;
- five focused entry-contract tests;
- `docs/RUST_TRANSPOSITION_TABLE_ENTRY.md`.

Evidence:

- Exact validated implementation SHA: `65ef70bfbff3d0bf5fd6e6a19ba20ed5214c3e26`.
- Permanent CI run/job: `30764647127` / `91541116562`.
- Results: workspace assets, Task 14.5 audit over 11 production search modules, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 160 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Storage allocation, buckets, empty slots, clearing, generation advancement, normalization, probes, replacement, and diagnostics remain intentionally outside Task 15.1.
- Tasks 15.2 fixed-memory storage and 15.3 mate normalization are complete; Task 15.4 safe probe semantics is next.

## Task 15.2 completion

Implemented and validated:

- a fixed-capacity `TranspositionTable` configured in MiB;
- checked MiB-to-byte conversion and whole-cluster budget rounding;
- one private, fallibly reserved `Vec` allocation with no growth or fallback storage;
- four-entry collision clusters and deterministic complete-key cluster indexing;
- typed failures for zero configuration, arithmetic overflow, no complete cluster, and allocator rejection;
- explicit in-place `clear()` preserving allocation and generation;
- explicit wrapping `advance_generation()` retaining existing entries;
- public capacity, allocation, generation, and cluster-index diagnostics required to verify the storage contract;
- five focused storage tests;
- `docs/RUST_TRANSPOSITION_TABLE_STORAGE.md`.

Evidence:

- Exact validated implementation SHA: `6b2ee0081cd47fd9069aeabb0d3ccb1d3659fea9`.
- Permanent CI run/job: `30765303745` / `91542820537`.
- Results: workspace assets, Task 14.5 audit over 11 production search modules, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 165 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Mate normalization, probe semantics, replacement policy, diagnostics, and production search integration are complete under Task 15.
- The overall Task 15 production integration gate is complete.

## Task 15.3 completion

Implemented and validated:

- root-relative to position-relative conversion in `crates/chess-search/src/transposition_score.rs`;
- winning-mate normalization by adding storage ply and denormalization by subtracting probe ply;
- losing-mate normalization by subtracting storage ply and denormalization by adding probe ply;
- exact preservation of every ordinary evaluation score;
- typed rejection of unsupported plies and out-of-domain conversions;
- a crate-private unchecked constructor so public callers must use the tested conversion boundary;
- six focused regressions, including the same winning and losing TT values reached at different plies;
- `docs/RUST_TRANSPOSITION_TABLE_MATE_NORMALIZATION.md`.

Evidence:

- Exact validated implementation SHA: `ac68b99db53546c31f3aae68ad7337ba256eb982`.
- Permanent CI run/job: `30766126491` / `91545080021`.
- Results: workspace assets, Task 14.5 audit over 12 production search modules, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 171 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Probe semantics, replacement, diagnostics, and production search integration are complete under Task 15.
- The overall Task 15 production integration gate is complete.


## Task 15.4 completion

Implemented and validated:

- a public, storage-only `TranspositionTable::probe` boundary in `crates/chess-search/src/transposition/probe.rs`;
- complete 64-bit verification-key matching after deterministic cluster selection;
- stored-depth sufficiency before score reuse;
- exact-score returns and fail-high/fail-low bound cutoffs at the correct beta/alpha edges;
- current-ply mate-score denormalization before comparison or return;
- verified best-move delivery even when depth or bounds do not permit score reuse;
- explicit `SuppressedForRepetition` handling that disables cached scores while retaining move ordering;
- typed invalid-window and score-conversion failures;
- eight focused probe regressions;
- `docs/RUST_TRANSPOSITION_TABLE_PROBE_SEMANTICS.md`.

Evidence:

- Exact validated implementation SHA: `b6a015e6cc519aa0bbc8e7bde7dde06bdd660b44`.
- Permanent CI run/job: `30766760085` / `91546779835`.
- Results: workspace assets, Task 14.5 audit over 12 production search modules, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 179 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Deterministic insertion, replacement, diagnostics, and production search integration are complete under Task 15.
- The overall Task 15 production integration gate is complete.

## Task 15.5 completion

Implemented and validated:

- public `TranspositionTable::store` insertion in `crates/chess-search/src/transposition/store.rs`;
- in-place complete-key updates with no duplicate same-key slot;
- authoritative assignment of the table's current generation;
- stable lowest-index empty-slot selection;
- full-cluster replacement ordered by shallowest depth, oldest wrapping generation age, and lowest slot index;
- observable update, insertion, and eviction results;
- five focused deterministic cluster regressions;
- `docs/RUST_TRANSPOSITION_TABLE_REPLACEMENT.md`.

Evidence:

- Exact validated implementation SHA: `775013a6e11aad7625c88b0cd3b258819211e839`.
- Permanent CI run/job: `30767556904` / `91548869513`.
- Results: workspace assets, Task 14.5 audit over 12 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 184 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- The first two validation iterations exposed only a test-only import scope issue and a strict-Clippy fixture-loop issue; both were corrected without suppressions or policy changes.
- Diagnostics, hash-full estimation, microbenchmarks, and production search integration are complete under Task 15.
- The overall Task 15 production integration gate is complete.

## Task 15.6 completion

Implemented and validated:

- saturating fixed-size probe, hit, score-reuse, store, and replacement counters in `crates/chess-search/src/transposition/diagnostics.rs`;
- complete-key hit accounting separated from exact/lower/upper score reuse accounting;
- deterministic diagnostic snapshots and reset without table-state mutation;
- bounded current-generation hash-full sampling over at most 1,000 evenly distributed slots;
- a release-mode `chess-tools tt-bench ITERATIONS` command over fixed one-MiB store and probe fixtures;
- deterministic benchmark checksums with timing treated as informational;
- three diagnostics/hash-full regressions and one benchmark reproducibility regression;
- `docs/RUST_TRANSPOSITION_TABLE_DIAGNOSTICS.md`.

Evidence:

- Exact validated implementation SHA: `bd4d5d581c0e82f892435b2874732ac632c2e1f5`.
- Permanent CI run/job: `30768512470` / `91551420579`.
- Results: workspace assets, Task 14.5 audit over 12 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy, 188 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Benchmark smoke: 100,000 stores in `3,064,736 ns`, checksum `7,945,805,154,409,997,841`; 100,000 probes in `1,339,856 ns`, checksum `405,729,600`.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- The initial compiler iteration found only a test-only import in production scope; the next control iteration found only a temporary patch-matcher mismatch. Neither required a lint suppression or semantic change.
- Production search integration is complete under the overall Task 15 gate.

## Task 15 completion

Implemented and validated:

- production alpha-beta ownership of a fresh bounded default table and public caller-owned fixed-table search APIs;
- generation advancement and diagnostic reset once per valid caller-owned search without resizing or clearing retained entries;
- terminal and rule-draw resolution before cached-score reuse;
- complete-key, depth, exact/lower/upper bound, mate-distance, and legal-root-move enforcement;
- irreversible-history-only score storage and reuse, with verified move-only ordering at reversible-history nodes;
- root determinism through suppression of ordering-only hints and legal canonical-move validation for exact root returns;
- normalized post-search exact/lower/upper storage only after complete child restoration;
- fixed-capacity operation with no production map or unbounded fallback;
- five focused integration/order regressions and two release-mode node-reduction witnesses;
- `docs/RUST_TRANSPOSITION_TABLE_SEARCH_INTEGRATION.md`.

Evidence:

- Production implementation commit: `c9eac6b8b7b4b6511d73155242dde08a554d8e88`.
- Exact clean validated SHA: `682114cd2452b04e1f24af1150928baaff779aa8`.
- Permanent CI run/job: `30770018597` / `91555458016`.
- Release-witness validation run/job: `30769901197` / `91555134018`.
- Results: permanent exclusion audit over 12 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 193 executed non-doc Rust tests, both release node-reduction witnesses, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- The move-ordering witness preserves score and best move while visiting strictly fewer nodes from an insufficient-depth move-only hit.
- The warm-table witness preserves the exact score and canonical root move while reducing the second identical search to one node.
- Reversible-history, illegal-root-move, allocation-capacity, position/history restoration, and incremental/recomputed Zobrist regressions all passed.
- The clean implementation delta is limited to three Rust modules, one integration-test file, and one contract document.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 15 and Tasks 16.1/16.3 are complete. Task 16.6 final result API is next.

## Task 16.1 completion

Implemented and validated:

- a correctness-first iterative-deepening layer over the established full-window fixed-depth alpha-beta boundary;
- ascending complete searches at every depth from one through the requested maximum;
- one retained exact result record for every completed iteration;
- one bounded default TT for convenience searches and one caller-owned fixed table reused across depths;
- reuse of the same detached root history with exact restoration before every next iteration;
- per-depth score, canonical best move, nodes, TT diagnostics, bounded hash-full estimate, and generation reporting;
- fallible iteration-record reservation bounded by `MAX_MATE_PLY` and typed failure categories;
- five integration regressions and `docs/RUST_ITERATIVE_DEEPENING.md`.

Evidence:

- Exact validated implementation SHA: `886ad953952b3a409800fcf7e8699365f94f0271`.
- Permanent CI run/job: `30772536115` / `91562076526`.
- Results: permanent exclusion audit over 13 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 198 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Every retained iteration matched an independent fixed-depth full-window score and canonical best move on the deterministic benchmark.
- Generation sequence, diagnostic isolation, terminal roots, invalid maximum depths, mismatched histories, table capacity, position/history restoration, and incremental/recomputed Zobrist identity are covered.
- The first validation iteration found canonical rustfmt differences only. The second found a test-only assumption that sparse bounded hash-full sampling must observe an occupied slot; the assertion was corrected to the documented sampling contract without production changes.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 16.1 and Task 16.3 are complete. Task 16.6 final result API is next.

## Task 16.2 completion

Implemented and validated:

- a typed internal root-window search boundary that classifies exact, fail-low, and fail-high outcomes;
- depth-one complete-window search and later ±50-centipawn windows centered on the prior exact completed score;
- exactly one complete-window recovery attempt after either bound outcome;
- an invariant that bound attempts expose no exact score and cannot populate the completed iteration, PV, or ponder result;
- one transposition-table generation per depth, including retries;
- immutable per-attempt alpha/beta, outcome, score, node, TT-counter, hash-full, and generation diagnostics;
- checked aggregate node accounting and saturating aggregate TT diagnostics across attempts;
- mate-boundary complete-window fallback and a fail-loud unexpected-full-window-bound error;
- deterministic fail-low/fail-high recovery regressions and updated iterative-deepening equivalence/restoration coverage;
- `docs/RUST_ASPIRATION_WINDOWS.md` and updated `docs/RUST_ITERATIVE_DEEPENING.md`.

Evidence:

- Production implementation commit: `c1d1c61caf85fd230b48a4b9026b9aa8b7ae79bf`.
- Exact clean validated SHA: `8af24520fd72faffff1cab74581f056a083cfb13`.
- Permanent CI run/job: `30779589438` / `91581508274`.
- Results: permanent exclusion audit over 15 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 206 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Both forced bound regressions prove `exact_score() == None` before one complete-window retry recovers the independent exact score and canonical move.
- Retry diagnostics prove one generation per logical depth and exact per-attempt plus aggregate accounting.
- Position, detached history, incremental Zobrist identity, PV legality, and ponder behavior remain restored and deterministic.
- The validation loop corrected the permanent audit witness, a private non-const comparison, and a strict-Clippy constructor shape without suppressions or semantic relaxation.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 16.6 final result API is next.

## Task 16.3 completion

Implemented and validated:

- bounded legal principal-variation reconstruction attached to every completed iterative-deepening iteration;
- exact root best-move anchoring and complete-key, exact-bound, sufficient-depth TT continuation;
- legal-token regeneration and validation before every returned move;
- explicit terminal, missing-entry, illegal-entry, root-without-move, requested-depth, and repeated-position termination;
- repeated-Zobrist cycle protection independent of the completed-depth hard bound;
- observational TT lookup that leaves diagnostics and table state unchanged;
- second-validated-move ponder extraction at both iteration and final-result boundaries;
- best-move retention in internal exact entries;
- focused unit/integration regressions and `docs/RUST_PRINCIPAL_VARIATION.md`.

Evidence:

- Exact clean validated implementation SHA: `e8afc9959a60519c6d5617963521e1707d37c6a9`.
- Permanent CI run/job: `30776274173` / `91572310565`.
- Results: permanent exclusion audit over 14 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 204 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Focused tests prove complete exact chains, legal sequential replay, ponder extraction, complete-key collision rejection, exact-bound/depth enforcement, illegal-move exclusion, repeated-position termination, terminal-root behavior, and diagnostic non-mutation.
- The initial compiler pass found only one test-only ambiguous integer literal; an explicit `u64` annotation resolved it without production semantic changes.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Tasks 16.1–16.6 are complete. Task 16.7 optional bounded check extension is next.

## Task 16.4 completion

Implemented and validated:

- typed depth, exact cumulative node, soft-time, hard-time, infinite, and explicit-stop limits;
- a clone-shareable atomic `SearchStopFlag` suitable for an external search controller;
- fail-loud validation and deterministic precedence for conflicting or simultaneously reached limits;
- exact production-node accounting through one `on_node` hook per alpha-beta or quiescence node;
- soft-time stopping only at exact iteration boundaries and hard/node/stop interruption inside the production tree;
- preservation of every fully completed exact iteration and rejection of all partial-depth result/PV/ponder data;
- exact searched-node and incomplete-node reporting, including interrupted aspiration work;
- reuse of one bounded TT and exact restoration of position, detached history, and incremental/recomputed Zobrist identity;
- deterministic integration and scripted-clock regressions;
- `docs/RUST_SEARCH_LIMITS.md` and updated `docs/RUST_ITERATIVE_DEEPENING.md`.

Evidence:

- Production implementation commit: `1cbe0264418afbcddc564b1e4972c4819fb0a6f8`.
- Exact clean validated SHA: `8a48ee45199e58db76adee4e4fc4adaf131566d2`.
- Permanent CI run/job: `30780915406` / `91585230626`.
- Results: permanent exclusion audit over 16 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 214 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- The exact node-budget regression completes depth one, enters exactly one node of depth two, reports that node as incomplete work, discards the partial depth, and preserves the complete depth-one result.
- Preset finite and infinite stop requests terminate before table generation or root mutation; invalid combinations fail before allocation or search mutation.
- Scripted clocks prove soft-time boundary stopping and hard-time precedence without wall-clock flakiness.
- The implementation passed its first compiler and strict-Clippy iteration without source corrections or suppressions.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 16 is complete. Task 17.1 protocol loop is next.

## Task 16.5 completion

Implemented and validated:

- an exported one-production-node maximum cancellation polling interval;
- cancellation checks at every alpha-beta and quiescence node plus child boundaries before move application;
- typed cancellation that unwinds every active move and reversible history entry before reaching the root;
- preservation of the deepest fully completed exact iterative-deepening result while discarding all partial-depth data;
- deterministic `FirstLegalMove` and terminal `NoLegalMove` fallbacks when depth one never completes;
- exact position, detached history, history identity, incremental Zobrist, and recomputed Zobrist restoration;
- a reproducible release cancellation benchmark with an enforced node bound, informational wall-clock measurements, and deterministic checksum;
- focused integration regressions and `docs/RUST_RESPONSIVE_CANCELLATION.md`.

Evidence:

- Production implementation commit: `68f86a53c31dd5f1448e99fb7def8bb220f2222f`.
- Exact clean validated SHA: `128f52e8fb7d7e9974605fc840eb13d3ecc021a6`.
- Permanent CI run/job: `30782361257` / `91589434579`.
- Results: permanent exclusion audit over 16 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 218 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- The deterministic in-tree witness issues a request after 64 nodes, observes it within the exported one-node bound, returns typed cancellation before depth completion, and restores every root invariant.
- The release smoke output was `cancel<TAB>4<TAB>64<TAB>0<TAB>404<TAB>186<TAB>5435046110819296062`: four samples, zero maximum additional nodes, 404 total measured nanoseconds, 186 maximum measured nanoseconds, and a stable checksum.
- One-node-budget and preset-stop tests prove a deterministic legal fallback; a terminal preset-stop test proves the explicit no-legal-move fallback; completed-depth tests prove fallback suppression and last-iteration preservation.
- The initial compiler iteration found one fallback iterator lifetime issue. A local materialized value fixed it without semantic relaxation or lint suppression.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 16 is complete. Task 17.1 protocol loop is next.

## Task 16.6 completion

Implemented and validated:

- one unified `SearchResult` snapshot for limit-controlled iterative deepening;
- authoritative best move, optional exact typed score, ponder move, completed depth, legal PV, and typed termination reason;
- request-wide production-node, quiescence-node, selective-depth, and elapsed-time accounting, including interrupted partial work;
- exact completed-iteration preservation with no promotion of partial aspiration or cancellation data;
- explicit unscored legal and terminal fallback semantics before depth one;
- compatibility through `LimitedIterativeDeepeningSearchResult` and `searched_nodes` while detailed per-depth diagnostics remain available;
- specialized alpha-beta and quiescence node hooks that preserve existing cancellation probes and the one-node bound;
- focused normal, interrupted, legal-fallback, and terminal-fallback regressions;
- `docs/RUST_SEARCH_RESULT_API.md` and updated iterative-deepening/limit contracts.

Evidence:

- Production implementation commit: `780bcc6bf9ba17afb9e9443e3a106b722d4c43fe`.
- Exact clean validated SHA: `dcde800f4c5a08c07fe57724ed672f2abd122157`.
- Permanent CI run/job: `30783666840` / `91593059900`.
- Results: permanent exclusion audit over 16 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 222 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- Exact completion tests prove all headline fields agree with the deepest exact iteration and that qnodes/selective depth are internally consistent.
- Interruption tests prove total work includes partial nodes/qnodes/seldepth/time while score, move, PV, ponder, and completed depth remain anchored to the prior exact iteration.
- Pre-depth-one tests prove the legal fallback never invents score or PV data and the terminal fallback returns no move.
- The implementation passed its first compiler and strict-Clippy iteration without source corrections or suppressions.
- The clean implementation delta contains only seven search modules, one integration-test file, and three contract documents.
- First-party warnings: none.
- Accepted external notices: GitHub Actions Node runtime, dependency `punycode`, and `url.parse()` deprecation notices only.
- Task 16 is complete. Task 17.1 protocol loop is next.

## Task 16.7 and Task 16 gate completion

Implemented and validated:

- explicit opt-in through `SearchLimits::with_check_extension`, with baseline behavior unchanged by default;
- exactly one additional check ply per root-to-leaf path, enforced by a value-passed finite budget;
- budget-exhausted and mate-domain-blocked decisions that never create an extension chain;
- path-safe suppression of TT scores and stores while preserving complete-key legal move-ordering hints;
- legal bounded root-PV behavior without following incompatible selective-search table chains;
- request-wide applied/exhausted/blocked diagnostics, including interrupted partial work;
- unchanged one-node cancellation responsiveness, node/time accounting, aspiration exactness, and exact root restoration;
- three focused unit tests, four integration tests, and updated search-limit/result contracts;
- `docs/RUST_CHECK_EXTENSION.md`.

Evidence:

- Production implementation commit: `54d98563f253df3ef055470a5fd4b2ee8b32947a`.
- Exact clean validated SHA: `836ca0563f9a8dce44eb78997e28335a9d8fcdce`.
- Permanent CI run/job: `30785853401` / `91599164384`.
- Results: permanent exclusion audit over 17 production Rust files, committed lockfile, metadata, rustfmt, Cargo check, strict Clippy without suppressions, 229 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, and independent differential validation passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- The deterministic extension witness records applied work only when opted in; the repeat search preserves move, score, node count, diagnostics, legal PV, position, and history.
- A seeded incompatible exact TT score cannot bypass extension search. A 64-node interrupted request preserves partial extension diagnostics and restores all root invariants.
- Validation fixes addressed generator matching, mechanical policy wiring, a test-only PV helper, strict-Clippy argument grouping, and temporary-script deletion; no production warning was suppressed and no gate was weakened.
- The clean implementation delta contains eight search modules, one integration-test file, and three contract documents; permanent CI is restored byte-for-byte.
- Task 16.1–16.7 and the overall Task 16 gate are complete. Task 17.1 protocol loop is next.

## Task 16 completed scope

- [x] Implement Task 16.1 iterative deepening.
- [x] Implement Task 16.2 aspiration windows.
- [x] Implement Task 16.3 principal variation.
- [x] Implement Task 16.4 search limits.
- [x] Implement Task 16.5 responsive cancellation.
- [x] Implement Task 16.6 final result API.
- [x] Implement Task 16.7 optional bounded check extension.
- [x] Pass the overall Task 16 gate.

## Task 15 completed scope

- [x] Complete Task 15.1 entry design.
- [x] Implement Task 15.2 fixed-memory storage.
- [x] Implement Task 15.3 mate-score normalization.
- [x] Implement Task 15.4 safe probe semantics.
- [x] Implement Task 15.5 deterministic replacement.
- [x] Implement Task 15.6 diagnostics and benchmarks.
- [x] Pass the overall Task 15 gate.

## Task 14 completed scope

- [x] Stand-pat only outside check.
- [x] Search every legal check evasion.
- [x] Search captures and all promotions.
- [x] Preserve fail-soft alpha-beta, draw, repetition, mate-distance, cancellation, and restoration semantics.
- [x] Enforce a bounded fail-loud tactical-ply guard.
- [x] Add independent tactical-oracle and fixed horizon-effect regressions.
- [x] Implement Task 14.2 tactical ordering.
- [x] Implement Task 14.3 quiet ordering.
- [x] Complete Task 14.4 consolidated correctness tests.
- [x] Complete Task 14.5 exclusion audit.
- [x] Pass the overall Task 14 gate.

## Task 13 completed scope

- [x] Implement an unpruned reference minimax/negamax search.
- [x] Count nodes and define terminal/draw scoring.
- [x] Implement negamax alpha-beta using legal tokens and make/unmake.
- [x] Integrate detached root and reversible line repetition history.
- [x] Prove shallow reference/alpha-beta score equivalence.
- [x] Compare uniquely best moves and node counts.
- [x] Prove search restores the root position, Zobrist key, and history exactly.
- [x] Add mate-in-one, mated, stalemate, draw, shorter-mate, and longer-survival fixtures.
- [x] Pass exact-head rustfmt, Cargo check, Clippy, tests, rustdoc, debug, release, perft, and differential gates.

No pull request has been created; work remains on `rust-engine`. Task 17.1 Linux UCI protocol loop is the next operation.

## Task 19.1 completion

Implemented and validated:

- dedicated platform-neutral `chess-book` workspace crate depending only on `chess-core`;
- `BookMove<M = ()>` with semantic engine move, `u32` relative weight, and optional backend metadata;
- `OpeningBook` as a `Send + Sync` validated-position query with typed fail-visible errors;
- `BookProvider` as an explicit adapter-owned construction boundary with `Ok(None)` for intentionally disabled book support;
- no filesystem, asset, environment, network, global-discovery, or platform dependency in `chess-core` or `chess-search`;
- four focused contract tests covering value preservation, dynamic injection, explicit enable/disable, and typed lookup failure;
- parser/format, selection, legality validation, UCI/safe-API integration, and Android assets remain explicitly deferred to Tasks 19.2–19.5.

Evidence:

- Exact validated implementation SHA: `6ce31141d0d4516696f1e9d17ee018606ef7bd4b`.
- Permanent Rust validation: run `30852253445`, job `91814805656`.
- Permanent Android regression validation: run `30852253399`, host JVM job `91814815286`, emulator job `91814815151`.
- Results: committed lockfile, metadata, rustfmt, workspace check, strict Clippy, 310 executed non-doc Rust tests, authoritative release depth-four perft, rustdoc with warnings denied, debug/release builds, differential oracle, host JVM JNI, dual Android ABI build, APK build, and API-35 emulator lifecycle all passed.
- Differential validation: 15 corpus positions, 293 child FENs, 272,991 oracle perft nodes, and 576 seeded plies with seed `0xC0FFEE`.
- The first executable validation found only canonical rustfmt output; no API, dependency boundary, error policy, test, or gate was weakened.
- Task 19.2 backend format is next. The overall Task 19 gate remains open.

## Task 20 completion

Implemented and validated:

- independent fixed White and Black search configurations with depth, node, or time limits;
- explicit seed, opening source, maximum-ply policy, claimable-draw policy, output path, and train/validation/test percentages;
- strict version-1 configuration, opening, game, and position formats;
- complete game moves, result, opening identity, engine/evaluator/search provenance, termination reason, and replay command;
- lossless canonical FEN position rows with side to move, game/ply identity, split, filtering metadata, and duplicate occurrence counts;
- replay validation of every game and retained position without rerunning search;
- explicit unfinished maximum-ply outcomes, opening-position policy, fail-loud empty output, and deterministic exact duplicate handling;
- `self-play`, `self-play-validate`, and `self-play-replay` commands plus example inputs and `docs/RUST_SELF_PLAY_DATASET.md`.

Evidence:

- merged implementation SHA: `333398c5913309193cb81b91c4af3deff2fd5adf`;
- exact validated evidence head: `1fae5fa8d830a524d6ff8d36ba42ed557112c79a`;
- Rust run/job: `30875333307` / `91885547979`;
- Android run/jobs: `30875333292` / `91885547947`, `91885547972`;
- 336 non-documentation Rust tests and all permanent quality, perft, documentation, build, differential, host JVM, dual-ABI, APK, and API-35 gates passed.

Task 20 is complete. Task 21.1 named weight-schema integration is complete; Task 21.2 loss-pipeline work is next.

## Task 21.1 completion

Implemented and validated:

- 810 stable named tunable scalars;
- separately versioned and checksummed evaluator structural constants consumed by runtime evaluation;
- strict version-1 named artifacts with complete trainer, source, dataset, split, seed, iteration, and timestamp provenance;
- semantic checksums over schemas, structure, metadata, parameter names, and values;
- explicit candidate non-activation and `docs/RUST_NAMED_WEIGHT_SCHEMA.md`.

Evidence:

- exact validated implementation head: `8410beb6dc22684052ded86a6f2fe71cf9d1e444`;
- Rust run/job: `30889939723 / 91929495312`;
- Android run/jobs: `30889939726 / 91929459955, 91929459977, 91929460081`;
- all permanent Rust, Android/Kotlin lint, host JNI, and API-35 gates passed.

Task 21.1 is complete. Task 21.2 loss-pipeline work is complete; Task 21.3 optimizer work is next.

## Task 21.2 completion

Implemented and validated:

- side-to-move loss, draw, and win targets;
- numerically stable base-10 Texel logistic mapping;
- finite positive `K` values and an explicit bounded inclusive calibration grid;
- training-only deterministic `K` calibration with smaller-value tie retention;
- occurrence-weighted mean-squared error preserving Task 20 duplicate multiplicity;
- nonempty independent training and validation partitions with the test split excluded;
- strict Task 20 parsing, eligibility filtering, result orientation, and canonical FEN reconstruction;
- typed failures and `docs/RUST_TEXEL_LOSS_PIPELINE.md`.

Evidence:

- exact validated implementation head: `3d11b01a9de84913c6c1bfa43a37aea0197dc5be`;
- Rust run/job: `30894313165` / `91943462745`;
- Android run/jobs: `30894313169` / `91943477000`, `91943477036`, `91943477212`;
- permanent formatting, workspace check, strict Clippy, complete Rust tests, authoritative release perft, warning-free rustdoc, debug/release builds, differential oracle, Android/Kotlin lint, host JNI, and API-35 instrumentation all passed.

Task 21.2 is complete. Task 21.3 optimizer work is complete; Task 21.4 report work is next.

## Task 21.3 completion

Implemented and validated:

- simultaneous perturbation stochastic approximation over all 810 stable named scalar parameters;
- explicit finite gain, decay, perturbation, stability, iteration, bound, and regularization configuration;
- deterministic SplitMix64 perturbation directions from a caller-supplied `u64` seed;
- training-only gradients and best-candidate selection, with validation loss observable but unable to change optimizer state;
- inclusive scalar projection plus deterministic positive material-order preservation;
- L2 regularization around the exact initial named vector;
- fixed-length little-endian version-1 checkpoints with optimizer/config/dataset/K binding, RNG state, continuous parameters, initial reference, best values, objectives, and FNV-1a checksum;
- exact uninterrupted-versus-resumed state equivalence and fail-loud corrupt/config/data/objective mismatch handling;
- `docs/RUST_SPSA_OPTIMIZER.md`.

Evidence:

- integration commit: `933d65d9cd2b617460829092c85361fa134afc7a`;
- exact helper-free validated implementation head: `fc69d7d7554ab325fd72ccfc5ac94c4bb1077ae8`;
- integration preflight run: `30896853476`;
- permanent Rust run/job: `30897085986` / `91952447573`;
- permanent Android run/jobs: `30897085023` / `91952460052`, `91952460064`, `91952460121`;
- formatting, locked workspace check, strict Clippy, complete Rust tests, authoritative release perft, warning-free rustdoc, debug/release builds, differential oracle, Android/Kotlin lint, host JVM JNI, dual-ABI native verification, APK build, and API-35 instrumentation all passed;
- temporary integration workflow was removed and no branch or pull request was created.

Task 21.3 is complete. Task 21.4 report work is complete; no optimized candidate has been activated.

## Task 21.4 completion

Implemented and validated:

- strict version-1 checksummed tuning reports;
- initial and final occurrence-weighted training and held-out validation MSE;
- final regularized training objective for the SPSA-selected checkpoint best;
- all 810 named parameters with initial value, candidate value, and signed delta;
- Task 20 schema/checksum/occurrence provenance plus the exact optimizer loss-dataset fingerprint;
- engine version/identifier, exact source commit, initial/candidate weight identities, optimizer/config/checkpoint identities, seed, iteration count, logistic `K`, and every schedule/bound/regularization value;
- exact command preservation using unambiguous UTF-8 hexadecimal encoding and exact IEEE-754 bit recording;
- semantic report checksums and fail-loud binding to the exact checkpoint, configuration, dataset, and initial weights;
- explicit same-directory temporary-file persistence with flush, synchronization, and atomic rename;
- separately versioned `NamedWeightArtifact` candidate output with no automatic activation;
- `docs/RUST_TUNING_REPORTS.md`.

Evidence:

- exact helper-free validated implementation head: `fd179e57462226392ab9c61bc9f26bc7cbb63cc1`;
- permanent Rust run/job: `30929481202` / `92060204891`;
- permanent Android run/jobs: `30929479894` / `92060200320`, `92060200325`, `92060200573`;
- formatting, locked workspace check, strict Clippy, complete Rust tests, authoritative release perft, warning-free rustdoc, debug/release builds, differential oracle, Android/Kotlin lint, host JVM JNI, dual-ABI native verification, APK build, and API-35 instrumentation all passed;
- the temporary validation workflow was removed before the recorded implementation head;
- candidate weights remain inactive and Task 21.5 owns controlled candidate validation and any later explicit activation decision.

Task 21.4 is complete. Task 21.5 candidate validation protocol is complete; no optimized candidate has been activated.

## Task 21.5 completion

Implemented and validated:

- explicit evaluation-weight injection through production iterative deepening, alpha-beta, and quiescence while existing APIs retain the built-in baseline;
- typed evaluator policies and separate evaluator-dependent transposition tables;
- reuse of the Task 20 game controller for legal play, history, draw claims, maximum-ply handling, search limits, and complete replay payloads;
- strict version-1 checksummed candidate-validation reports with engine/source/command, weight/artifact, opening-suite, correctness, game, statistical, and decision provenance;
- correctness-before-strength validation using all authoritative perft fixtures through depth four and weighted forced-mate fixtures;
- fixed seeded scheduling over at least 200 semantically distinct opening pairs, with the candidate playing both colors for 400 games;
- independent pair-score statistics, sample standard error, and a one-sided 95% lower confidence bound that must exceed 50% plus the configured margin;
- a separately enforced maximum-ply unfinished-game ceiling;
- fail-closed `rejected_correctness`, `rejected_unfinished_rate`, and `rejected_strength` outcomes;
- same-directory temporary-file persistence with flush, synchronization, and atomic rename;
- immutable `activated=false` output and no default-weight mutation;
- `docs/RUST_CANDIDATE_VALIDATION.md`.

Evidence:

- exact helper-free validated implementation head: `664bf7cb51fae8bff8298925513b242fd9f33cee`;
- production control run/job: `30935079798` / `92079069382`;
- production control result: 200 pairs, 400 games, 400 explicit maximum-ply unfinished games, mean pair score `0.5`, standard error `0.0`, one-sided lower bound `0.5`, decision `rejected_strength`, `activated=false`, checksum `9af9ee9ab36b0ab2`;
- permanent Rust run/job: `30935448972` / `92080314407`;
- permanent Android run/jobs: `30935448944` / `92080314104`, `92080314087`, `92080314012`;
- formatting, locked workspace check, strict Clippy, complete Rust tests, authoritative release perft, warning-free rustdoc, debug/release builds, differential oracle, Android/Kotlin lint, host JVM JNI, dual-ABI native verification, APK build, and API-35 instrumentation all passed;
- all temporary integration, hardening, control, and tracker workflows were removed from the implementation head;
- the control candidate was correctly rejected rather than accepted by equality, and no candidate weights were activated.

Task 21.5 is complete. The overall Task 21 gate remains open until a real tuned candidate passes this protocol and is explicitly activated by a separate validated change.


## Task 22 completion

Implemented and validated:

- a fail-closed version-1 advanced-evaluation evidence protocol in `crates/chess-tools/src/advanced_evaluation.rs`;
- stable identities, concise definitions, and explicit existing-term overlap for all eight retained candidate areas;
- two isolated legal fixtures per area plus generated color-swapped vertical mirrors;
- exact baseline and probe evaluator symmetry checks;
- fixed-iteration evaluation timing and fixed-node production-search comparisons with evaluator-specific transposition tables;
- fixed-seed, color-balanced candidate-versus-baseline matches using the shared Task 20/21 game controller;
- independent pair statistics and a hard minimum of 200 pairs before any strength acceptance;
- versioned semantic checksums, fail-loud validation, same-directory temporary persistence, flush, synchronization, atomic rename, and parent synchronization;
- immutable `activated=false` evidence and no production evaluator/default-weight mutation;
- `docs/RUST_ADVANCED_EVALUATION_PROTOCOL.md`.

Controlled evidence:

- run/job: `30938602274` / `92090934559`;
- 32 independent pairs and 64 games per area, seed `570425378`, depth 1, maximum 8 plies, 1 MiB TTs, 2,000 timing iterations, and 512 fixed nodes;
- all 16 base fixtures and their mirrors passed exact baseline/probe symmetry;
- all fixed-node searches consumed exactly 2,048 nodes per side and produced zero best-move changes;
- all 512 games reached the deliberate maximum-ply boundary and remained explicit `unfinished` games, so the run made no strength claim;
- defender coordination and extra endgame phase-specific scaling were rejected as overlap;
- pawn-majority/candidate-passer, king-zone units, rook/queen battery, minor outpost/bad bishop, king/passer race, and simplification probes were rejected for insufficient strength evidence;
- report checksum: `0ad7dcc3dda4cdfb`;
- formatting, locked workspace compilation, strict Clippy, 21 normal library tests plus binary/integration/doc tests, and the ignored controlled evidence run passed.

The prohibited Python guidance concepts remain excluded. Task 22 is complete with no advanced term accepted or activated. Task 23 robustness work is next; the separate overall Task 21 activation gate remains open.

## Task 23.1 completion

Implemented and validated:

- exhaustive square index/coordinate/algebraic round trips across all 64 squares;
- exhaustive packed-move source, destination, kind, and promotion preservation;
- deterministic legal-position generation from six real roots with four fixed seeds and up to 48 plies;
- canonical FEN parse/serialize/parse stability after every generated transition;
- generated legal-move acceptance through the checked public API and moving-king safety after every move;
- complete internal occupancy/king-cache/en-passant invariants and incremental/full Zobrist equality after every transition;
- immediate and full-sequence make/unmake exact restoration;
- 24 generated search cases with exact color-swapped vertical-mirror evaluator symmetry;
- depth-two principal variations proven legal, king-safe, invariant-preserving, hash-correct, and fully reversible;
- explicit caller-position and search-history immutability checks;
- fixed case/seed/root/ply/FEN/move diagnostics and a documented permanent counterexample-preservation policy in `docs/RUST_PROPERTY_TESTING.md`.

Evidence:

- helper-free implementation head: `4483c1661a975bc9f64c1f725618930e31968e74`;
- permanent Rust run/job: `30940733222` / `92098127153`;
- permanent Android run/jobs: `30940732968` / `92098189450`, `92098189412`, `92098189386`;
- formatting, locked workspace compilation, strict Clippy without first-party suppression, complete Rust tests, authoritative release perft, warning-free rustdoc, debug/release builds, differential validation, Android/Kotlin lint, host JVM JNI, dual-ABI native verification, APK/test-APK construction, and API-35 instrumentation all passed;
- no property counterexample was found in the committed deterministic corpus.

Task 23.1 is complete. Task 23 remains open for Task 23.2 fuzzing, Task 23.3 runtime analysis, and Task 23.4 minimized-failure preservation.

## Task 23 completion

Implemented and validated:

- seven production-boundary mutation targets in an independent locked fuzz workspace;
- deterministic seed corpora, stable success/rejection tests, and committed corpus replay;
- 256 bounded mutations per target, 1,792 total per workflow run;
- Miri strict-provenance core analysis;
- AddressSanitizer plus LeakSanitizer over the complete C ABI lifecycle suite;
- ThreadSanitizer over active cross-thread cancellation;
- explicit CI enforcement that general Rust UBSan is unsupported, with Miri retained as the UB gate;
- host-JVM and API-35 JNI lifecycle validation alongside native analysis;
- documented permanent minimization policy under `fuzz/regressions/<target>/`;
- one real minimized one-byte C ABI semantic counterexample, permanently retained and replayed before its production fix.

Evidence:

- helper-free implementation head: `469c9c67ab53c276509fc7bad0c4adc209c815b7`;
- robustness run/jobs: `30944117733 / 92109744098, 92109744189, 92109744065`;
- Rust run/job: `30944118025 / 92109744577`;
- Android run/jobs: `30944117802 / 92109760102, 92109760118, 92109760076`;
- contract: `docs/RUST_ROBUSTNESS_GATES.md`;
- minimized regression: `fuzz/regressions/c_abi_buffers_handles/forged-buffer-wrong-token-type.bin`;
- named replay: `fuzz/tests/regression_c_abi.rs`.

Task 23 is complete. Task 24 performance hardening is next. The independent Task 21 activation gate remains open until a real tuned candidate passes the 200-pair protocol and is explicitly activated.
