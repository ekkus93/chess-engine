# Rust Chess Engine S4 Evaluation Tuning Calibration Implementation Report

**Status:** Complete — method accepted for future experimentation; selected candidate rejected; no production promotion
**Date:** 2026-08-07
**Planning baseline SHA:** `543dce22e51e71f821e37754a97ce0f33c3be122`
**Clean S4 operational baseline SHA:** `b02623f20417c7f5769b6a16fc94566239e7979a`
**Pre-closure implementation/evidence head:** `58dc897c18ae1bc21616086578206c2a2ecf88a5`
**Production/code baseline SHA:** `677cd2a4d2a4a4f3c376f7bf47fae412171206fb`
**Production package/UCI version:** `0.1.0`
**Production activation:** unchanged / none

## Executive disposition

S4 completed its technical objective: the integer-weight SPSA tuning stack is accepted as a reproducible experimental tuning method within the bounded S4 operating envelope. S3's zero-movement result was not caused by absent loss signal or a hidden optimizer failure; it was caused by an underpowered gain schedule whose floating updates were erased by integer materialization.

A predeclared stronger-corpus matrix produced reproducible nonzero evaluator movement with simultaneous training and held-out loss improvement and zero clipping. The selected candidate then reproduced byte-for-byte and registered as one inactive `advance` candidate. A separate development chess-strength smoke subsequently rejected that candidate under both fixed-node and clock protocols. Accordingly:

- **method disposition:** accepted for future S5 evaluator-feature experimentation;
- **selected S4 candidate:** rejected as positive development-strength evidence;
- **production evaluator:** unchanged v0.1 baseline;
- **activation:** none;
- **S2 search policies:** remain inactive;
- **release/version/ABI/JNI/Android surfaces:** unchanged.

## S4-0 baseline and authority

S4 was registered as the single active implementation tracker while the closed S3 program remained historical. The frozen release identities remained:

- v0.1 search-policy identifier/checksum: `5630315f504f4c31` / `0c0769ef9d034770`;
- baseline evaluation-weight identifier/checksum: `424153454c494e45` / `d2cca7ae10ec6e34`;
- runtime evaluation vector length / tunable count: `816 / 810`;
- C ABI version: `1`;
- tablebases disabled;
- opening book disabled by default;
- no public experimental S2/S3/S4 selector.

S4 also corrected inherited closure hygiene rather than hiding it: the stale write-capable S3 closure helper was removed, and the historical S3 audit was aligned with S4's stricter mask-direction invariant without weakening the invariant.

## S4-1 zero-movement diagnosis

Diagnostic run `31198269449`, job `92931740915`, artifact `9001742616` (ZIP SHA-256 `63e957572b1a872a6cc1c109332c7e09aef2c29b73449eb9887470dfdff5e39d`) reproduced the S3 full-evaluator pilot on the same chess dataset checksum `c691d1928ffda61b`.

Across 8 iterations × 810 active parameters:

- maximum absolute objective difference: `7.03043834947084112e-03`;
- maximum absolute gradient estimate: `2.02176406002437924e-03`;
- maximum proposed floating update: `2.06410316075983228e-04`;
- zero-after-quantization parameter-iterations: `6,480`;
- effective integer updates: `0`;
- clipped updates: `0`;
- classification: `quantization_limited`.

The evidence rules out zero objective signal, zero gradient, clipping, inactive-mask behavior, hidden optimizer early exit, and candidate-materialization replacement as the primary cause.

## S4-2 trace and S4-3 update diagnostics

The optimizer now emits strict provenance-bound per-iteration evidence:

- diagnostic schema: `1`;
- diagnostic identifier: `5334444941473031`;
- trace schema: `1`;
- trace identifier: `5334545241433031`;
- source/config/dataset/mask/initial-weight/seed/checkpoint binding;
- bit-canonical floating serialization;
- semantic checksum and strict canonical parser;
- positive/negative losses, objective difference, gradient statistics, floating update magnitudes, quantization counts, clipping counts, regularization contributions, candidate checksum and available losses.

The production update arithmetic is shared by traced and normal SPSA paths. Regression coverage proves sub-integer quantization, effective integer materialization, signed clipping, regularization accounting, checksum movement, inactive-parameter freezing, and bounds.

## S4-4 and S4-5 known-answer optimizer tests

Permanent Phase-4 validation run `31198700056`, job `92933158829`, passed workspace compilation, strict Clippy and optimizer regressions using the same production update helper.

- the one-parameter deterministic objective moved in the predeclared direction and finished closer to its known optimum;
- fixed seed/config reproduced exactly;
- bounds remained enforced;
- the multi-parameter objective converged with mixed movement directions while inactive values remained frozen;
- resume/config/mask identity invariants remained fail-closed.

## S4-6 degraded chess-evaluator recovery

Run `31199196735`, job `92934800859`, validated a test-only structurally valid queen-material degradation against real `LossDataset` positions. The fixture first proved the authoritative baseline had lower train and held-out loss than the degraded evaluator. Bounded tuning then moved degraded queen material toward baseline values, improved training loss, kept held-out loss within the frozen tolerance, and left inactive weights unchanged. The degraded identity exists only under test configuration and cannot escape through production adapters.

## S4-7 stronger deterministic corpus

Corpus run `31199370707`, job `92935372960`, artifact `9002250000`, ZIP SHA-256 `e83623d4323784b1ede8d44cc0b2d699d529aa8e96de3c447ae3de7414c97165`, generated both scales twice byte-identically.

The stronger admitted corpus used for calibration is:

- 96 games;
- 1,024 nodes/move per side;
- dataset checksum `85c0e5949cb329e3`;
- 1,530 eligible positions;
- 8,202 training occurrences;
- 2,465 held-out validation occurrences;
- zero excluded rows;
- explicit `70/20/10` split;
- `activated=false`.

Generated datasets remain workflow artifacts and are not committed to Git.

## S4-8 bounded hyperparameter matrix

The 12-row matrix was frozen before execution; canonical TSV SHA-256 `021a1f2cc30281b5167e0557fe68d8c3cf5d62b7f6d1789604d9d956920cad8e`. Run `31200184027`, job `92938059565`, artifact `9002551314`, ZIP SHA-256 `af86926588c2c3b8c9da7e5b15d2e7a039f128759a5209b8115d041d7b607ea2`, executed all rows without selective reruns.

All 12 rows produced nonbaseline runtime values, strict train and held-out improvement, zero clipping, and inactive artifacts. The deterministic selection rule chose row 11:

- learning rate `4096`;
- perturbation `8`;
- regularization `0`;
- iterations `32`;
- changed parameters `645 / 810`;
- max absolute integer delta `8`;
- mean absolute integer delta `1.41604938271604941`;
- training delta `-4.83858551862105524e-3`;
- held-out delta `-6.37062441281038838e-3`;
- clipping `0`;
- value checksum `520db5dd58086a8a`;
- activation `false`.

## S4-9 real-data reproducibility and registry gate

Run `31201066297`, job `92940904715`, artifact `9002851591`, ZIP SHA-256 `21eea3234afe7fd00ee69681536bad8e6fa21186f05ed1816888a40f02923242`, repeated selected row 11 twice under identical inputs. Complete publication directories and CLI logs were byte-identical.

The reproduced candidate retained value checksum `520db5dd58086a8a`, changed `645 / 810` parameters, reproduced both loss deltas and zero clipping, and the strict existing candidate registry accepted exactly one inactive candidate with decision `advance`.

This passed the S4 tuning-method gate. It did not authorize production activation.

## S4-10 development chess-strength smoke

Run `31203299756`, job `92948219087`, artifact `9003757817`, ZIP SHA-256 `df04923ebc25fe811b5e8c945181b7ce3b1cdb02eefff5f6e1c422600b6de0f5`, completed both diagnostic protocols and artifact publication successfully.

- fixed nodes: 32 games, candidate `12/4/16` W/D/L, mean pair score `0.4375`, lower bound `0.289710870349143224`, decision `rejected_strength`;
- clock: 32 games, candidate `14/2/15` W/D/L plus 1 unfinished, mean pair score `0.484375`, lower bound `0.318742454382700768`, decision `rejected_strength`;
- illegal moves / crashes / time forfeits / infrastructure failures: all `0` in both reports;
- activation: `false`.

The workflow success is evidence that the diagnostic match machinery completed correctly; both chess-strength decisions are explicit rejections. This candidate cannot be used as positive strength evidence.

## S4-11 method disposition and S5 readiness

The current integer-weight SPSA method is accepted only for future evaluator experimentation inside the tested envelope. S5 must preserve explicit feature registration, known-answer sensitivity tests, frozen data/protocols, quantization visibility, bounded predeclared calibration, held-out gates, exact reproducibility, separate chess-strength evidence, fail-closed artifacts, and no automatic activation.

The selected S4 row is a calibration witness, not an S5 production target.

## S4-12 closure state

S4 is closed without production promotion. The tuning method is accepted for future controlled evaluator experimentation, while the selected calibration candidate remains explicitly rejected by development chess-strength evidence.

The exact validated pre-closure implementation SHA is `b66b256a5b81621ba5310a749b7b93e650cc6067`. The permanent matrix on that same SHA is green:

- CI run `31206849862`: x86-64 workspace-quality job `92960021815` success; ARM64 workspace-build job `92960021848` success;
- Performance run `31206850107`: x86-64 job `92959950041` success; ARM64 job `92959950085` success;
- Robustness run `31206849667`: sanitizer/leak job `92959948563`, Miri job `92959948579`, and fuzz/corpus job `92959948606` all success;
- Android/JNI run `31206849700`: API-35 JNI smoke `92959948648`, Android/Kotlin lint `92959948684`, and host JVM JNI contract `92959948749` all success;
- S4 Evaluation Tuning Calibration run `31206849866`, job `92959950456`: success;
- bounded report publication run `31208328421`, job `92964797405`: success.

Closure also fixed three first-party repository defects without weakening gates: the obsolete lint suppression in `s3_candidate.rs` was removed, `fuzz/Cargo.lock` was deterministically refreshed under the existing drift check, and the saturated issue-comment reporter was converted to a serialized bounded issue-body update while retaining fail-on-error behavior.

The S4 TODO is historical after this closure. There is no active implementation TODO. The completed Rust-port authority documents and this authority index remain the standing authority until a future program is explicitly registered.

No activation occurred anywhere in S4. Package/UCI version `0.1.0`, the v0.1 evaluator/search policy, ABI/JNI/Android surface, opening default, and tablebase state remain unchanged.

## Final post-closure validation evidence correction

`docs/RUST_CHESS_ENGINE_S4_FINAL_VALIDATION_ADDENDUM_2026-08-07.md` records the completed permanent validation matrix for final closed SHA `bc406d78d673cc3258e8b522bcec25c4838f5e32`. The pre-closure matrix above remains valid implementation evidence; it is not the final closed-SHA signoff. The addendum records CI `31208874474`, Performance `31208875019`, Robustness `31208875521`, Android/JNI `31208874646`, S4 `31208874643`, and final report publication `31209467578`, all successful on the exact final closed SHA. The selected S4 candidate remains `rejected_strength`, inactive, and non-production.
