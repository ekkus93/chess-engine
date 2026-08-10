# Rust Android UI/UX Review-Fix Closure Corrections Spec — 2026-08-10

**Status:** proposed / not started
**Branch:** `master`
**Companion TODO:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md`
**Program under correction:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md` (declared `Complete`)
**Closure evidence under correction:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md`
**Review baseline SHA:** `e9ab0fc623c22bd372ba9c8c2609dfcf74609f84`

---

## 1. Purpose

`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md` declares the bounded Android UI/UX review-fix program (AR-001 through AR-021) `Complete`, with a companion closure-evidence document citing independently-confirmed-real permanent CI evidence. An independent post-closure verification pass — eight parallel reviews, one per task cluster, each re-checking the actual shipped code against the final, twice-revised spec rather than trusting the checkboxes — found the closure to be **substantively but not fully honest**: the large majority of the 21 tasks are genuinely and rigorously implemented (including the two highest-technical-risk items, AR-008's dp-normalized tolerance and AR-016's revised composite-contrast model, both independently hand-verified with real computed numbers), no chess-correctness bug was found, no fail-open/fallback regression was found, and the cited CI run IDs are all real and independently confirmed via `gh`. However, five specific claims do not match the tree:

1. **AR-003** — a checkbox claims no player-visible string contains "native" jargon anywhere in `android-harness/android-app/src/main/kotlin`. This is false: `ChessViewModel.kt:71,117` still contain "native" and are rendered verbatim through the same player-facing error dialog AR-012 added coverage for.
2. **AR-004** — the spec required an explicit verify-first process (observe real API 35 behavior before any fix, and document the finding either way). No observation is recorded anywhere, no production code changed, and the one added test only checks a flag that would plausibly pass by default regardless of whether the underlying regression exists.
3. **AR-007** — the production guard code is correct and matches the final, simplified policy, but the checkboxes claim specific behavioral duplicate-invocation tests exist. They don't; only a predicate unit test and a static source-text-ordering check exist.
4. **AR-011** — the spec required either an end-to-end tap-driven promotion test or a documented reason one wasn't practical. Neither exists, despite the checkbox being marked complete.
5. **The closure-evidence document** cites permanent CI run IDs for a superseded SHA (`6d9a84d`) rather than the actual final tree (`e9ab0fc`), even though the final tree's own CI runs exist, are green, and were found only by independent `gh` querying.

The same verification pass also surfaced three minor, non-blocking hardening notes that were not false claims but are worth closing while this area of the codebase is already under active review: AR-006's replacement auto-scroll logic carries a new, undocumented assumption about `isScrollInProgress` not distinguishing user-initiated from auto-follow scrolls; AR-020's rotation test never explicitly asserts the source square became empty after the move it preserves; and AR-016's contrast matrix does not cover the Resign confirmation dialog's own button-on-surface color pairing (a real rendered combination, hand-computed to pass, but untested).

This pass closes all eight items. It does not reopen any other AR-00N task, and it does not relitigate any already-resolved QI/FQI pre-implementation item from the prior two rounds.

### 1.1 Pre-implementation resolution note

A pre-implementation review of this spec/TODO pair (`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_QUESTIONS_AND_ISSUES_2026-08-10.md`, twelve items, QI-001 through QI-012) was resolved and incorporated below. All twelve were legitimate — none rested on a factual misunderstanding of this repository's conventions (unlike the very first review of the parent program, where one item was rejected on precedent grounds; no equivalent rejection applies here).

- **QI-001** (this correction pass changes the tree, so `e9ab0fc` becomes only a review baseline, not a final SHA — and naively "fixing" the citation gap by adding run IDs to a doc creates a new SHA, recursively reopening the same gap) — resolved by an explicit, terminating closure-SHA protocol added to §2 below: exactly one trigger-commit cycle is used at the very end of the pass, its run IDs are recorded once, and no further edit chases that citation forward. See §2's "Closure-SHA protocol" subsection.
- **QI-002** (touched-file scope omitted `docs/LEGACY_TODO_INDEX.md`, the audit script, and files implied by CC-002/CC-004) — resolved by rewriting §2's scope as a category/surface statement rather than an exhaustive filename list, per the reviewer's own suggested alternative.
- **QI-003 / QI-004** (CC-002's verify-first process cannot honestly land in one commit if a real defect is found, and "observed correct" needs a precise, reproducible evidence contract) — resolved by splitting CC-002 into CC-002A (observation, its own commit) and CC-002B (conditional remediation, a separate commit only if needed), with an explicit observation-evidence checklist.
- **QI-005 / QI-006** (CC-003's "one representative operation" is weaker than the original three-operation claim it's correcting, and the task's title implied only one acceptable outcome) — resolved by requiring all three operations be behaviorally tested if a genuine seam is built at all, and retitling the task to make both honest outcomes explicit.
- **QI-007** (a green CI run does not by itself prove two trees are source-identical; that requires an actual git comparison) — resolved by requiring CC-005 to record the literal git diff/tree-hash comparison output, not just cite the historical CI runs as a proxy for it.
- **QI-008** (CC-009 registers the new tracker's authority state at the start but never explicitly closes it) — resolved by adding explicit authority-closure requirements to CC-009.
- **QI-009** (CC-001's "player-reachable string" test risks becoming a brittle reachability inference) — resolved by simplifying CC-001 to a blanket forbid-with-narrow-allowlist rule over all production string literals, per the reviewer's suggested alternative.
- **QI-010** (CC-004 needed to specify what fixture mechanism is allowed, to prevent scope creep into a general production FEN-loading feature) — resolved by naming the two acceptable options explicitly in CC-004.
- **QI-011** (CC-009's permanent-CI requirement was conditional — "if cross-workspace changes require it" — despite this pass touching Android source/tests and authoritative docs) — resolved by making it unconditionally mandatory, matching the parent program's own AR-021 standard.
- **QI-012** (correcting the parent TODO "in place" risks erasing the historical fact that a correction was needed) — resolved by requiring provenance-preserving wording for every corrected claim, added to CC-009.

### 1.2 Second pre-implementation resolution note

A follow-up review (`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_FOLLOWUP_QUESTIONS_AND_ISSUES_2026-08-10.md`, FQI-001 through FQI-003) confirmed the first round's substance held up, but found three further issues, since resolved:

- **FQI-001** (§2.1's terminal step instructed recording the trigger commit's own CI run IDs "in that trigger commit's own citation" — a literal impossibility, since those run IDs don't exist until after the commit is already pushed; writing them into the repo afterward would create a new SHA and restart the exact recursion the protocol was built to stop) — resolved by removing the self-citation instruction entirely. §2.1 now distinguishes repository-resident evidence (everything knowable before the terminal trigger push) from terminal external GitHub Actions metadata (the trigger commit's own run/job IDs, which are verified independently via `gh` and reported in the final implementation handoff, never written back into a new commit).
- **FQI-002** (several tasks now have legitimate mutually-exclusive outcomes — e.g. CC-002B may correctly not exist as a commit at all — but their checkboxes were still phrased as though every branch must reach `[x]`, which is impossible for whichever branch wasn't taken) — resolved by converting CC-002B, CC-003, and CC-004 to disposition-oriented checklists: one checkbox confirms a valid, evidence-backed disposition was reached, with the untaken branch explicitly marked `N/A` rather than left as a false `[ ]`.
- **FQI-003** (CC-005's git-comparison evidence used unrestricted/whole-tree commands, which would show inequality merely because documentation changed — the actual claim being made is narrower: that no *product/test* file differs, not that the whole tree is identical) — resolved by path-scoping the comparison to the surfaces the claim is actually about.

### 1.3 Final pre-implementation resolution note

A final, small follow-up review (`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_FINAL_FOLLOWUP_QUESTIONS_AND_ISSUES_2026-08-10.md`, FFQI-001 through FFQI-003) found no further substantive objection — only three bookkeeping/wording clarifications, since resolved:

- **FFQI-001** (`N/A`, introduced by the FQI-002 fix, had no formal completion semantics in the TODO's Status rules, leaving genuinely untaken branches in an ambiguous state) — resolved by adding an explicit `N/A` definition to the Status rules and clarifying that a task's own disposition checkbox being `[x]` with the untaken branch marked `N/A` counts as that task being complete.
- **FFQI-002** (§2.1's terminal-trigger decision was based on classifying the final commit as "documentation-only" versus "source/test," but CC-009 can touch files, such as the audit script or authority-index machinery, that don't cleanly fit either category — and whether a permanent workflow actually fires is determined by its own trigger configuration, not by this classification) — resolved by rewriting the rule around actual workflow execution: check whether both required permanent workflows executed against the final SHA, and only push a trigger commit if one didn't.
- **FFQI-003** (a stale `§6` cross-reference for CC-002, which actually lives in §4, and one remaining unconditional "the CC-004 instrumentation addition" phrase in §11.1 that didn't account for CC-004's documented-blocker disposition) — both corrected.

---

## 2. Engineering constraints retained

- All constraints from `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SPEC_2026-08-10.md` §2 continue to apply unless explicitly widened below: Rust remains authoritative for rules/SAN/opening-book/search; no chess-rule, legality, disambiguation, or opening-book logic is added to Kotlin; the fail-closed policy (no random/first-legal fallback, no silent retry, no silent depth reduction, no fake/default snapshot, no alternate engine path) is not weakened; the one-second reveal delay, portrait-only lock, and no-root-page-scroll invariants are preserved exactly.
- No first-party lint suppression (`allow`/`expect`, Kotlin `@Suppress`) is added anywhere in this pass.
- No new production dependency is added without explicit justification recorded in this spec. This pass adds none.
- This pass touches, by category rather than an exhaustive filename list (QI-002 — an exhaustive list proved too narrow once already): production and test Kotlin source under `android-harness/android-app/src/{main,test,androidTest}/kotlin/com/ekkus93/chessapp/` as needed by CC-001 through CC-004 and CC-006 through CC-008 (including, but not limited to, `ChessViewModel.kt`, `GamePanels.kt`, `MainActivity.kt`, `ReviewFixArchitectureTest.kt`, `ActiveGameOperationGuardTest.kt`, `PromotionDialogInstrumentedTest.kt`, `SystemBarAppearanceInstrumentedTest.kt`, `PortraitRotationInstrumentedTest.kt`, `ThemeContrastTest.kt`); the review-fix program's own tracker and closure-evidence documents (`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md`, `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md`); the authority-registration documents this correction pass itself required at baseline (`docs/LEGACY_TODO_INDEX.md`, `scripts/task_post_port_review_fix_audit.sh`); and this spec/TODO pair. It does not touch `crates/chess-app`, `crates/chess-core` production code (`san.rs` test-only additions are out of scope here, since AR-017 was independently verified correct), `crates/chess-search`, `crates/chess-book`, `crates/chess-uci`, `crates/chess-tui`, or `crates/chess-console`.
- Existing passing tests are not weakened or deleted to obtain a green run; every currently-green assertion remains green after this pass.
- This pass is itself a bounded review-fix tracker under `docs/LEGACY_TODO_INDEX.md`'s existing "Bounded review-fix trackers" classification (see that document's own section by that name) — it is registered there as part of this pass's baseline work, following the identical precedent already established by the four trackers already listed.

### 2.1 Closure-SHA protocol (QI-001)

This pass changes the repository tree across CC-001 through CC-009, so `e9ab0fc623c22bd372ba9c8c2609dfcf74609f84` (this spec's stated review baseline) is **not** the eventual final correction SHA — it is only the state that was reviewed to produce this spec. To avoid the self-referential "write run IDs → new SHA → revalidate → write new run IDs" recursion QI-001 correctly identified, this pass follows a single, terminating protocol, executed once, at CC-009:

1. **Review baseline SHA** (`e9ab0fc...`) is fixed and never reinterpreted as anything else.
2. **Implementation-start SHA** is captured immediately after CC-000's baseline/authority-registration work lands, mirroring the parent program's own AR-000 pattern.
3. CC-001 through CC-008 land normally, one task per commit (except CC-002, which is explicitly two commits, CC-002A and CC-002B — see §4).
4. All **repository-resident** evidence — everything CC-001 through CC-008 establish, plus CC-009's own validation-surface results and provenance-preserving corrections to the parent TODO — is written into its final form in the last substantive commit. That commit fully and accurately describes the correction pass; it does not attempt to cite its own not-yet-existing CI results.
5. Whether an additional trigger commit is needed is decided by **actual workflow execution, not by classifying the changed files as "documentation" versus "source/test"** (FFQI-002 — CC-009 itself may touch files, such as `scripts/task_post_port_review_fix_audit.sh` or authority-index machinery, that are neither cleanly "documentation" nor "product/test source," and whether a permanent workflow fires is determined by its own path/event trigger configuration in `.github/workflows/`, not by our semantic guess about the changed files):
   1. After the last substantive commit lands, check whether **both** required permanent workflows (Android CI, general/Rust CI) actually executed against that exact SHA.
   2. If both did, that SHA is the terminal validation SHA — no additional commit is created.
   3. If either required workflow did not execute against that SHA (because its trigger configuration didn't match the changed paths), push exactly one empty, tree-identical trigger commit — the same mechanism the parent program used for `e9ab0fc` itself — solely to cause both workflows to execute against the unchanged final tree.
   4. No repository mutation occurs after whichever SHA is determined to be the terminal validation SHA by this process.
6. **Terminal exact-SHA GitHub Actions run/job IDs and conclusions are external metadata, not repository content** (FQI-001 — they cannot exist inside the commit that causes them, and writing them into the repo afterward would only create a new SHA and restart the exact recursion this protocol exists to stop). They are independently verified via `gh` after the trigger push, and reported in this pass's final implementation handoff — **no further commit is made to the repository to record them.** The CC-009 acceptance gate requires the terminal CI to be confirmed green by that independent verification; it does not require a further repository mutation to satisfy that requirement.
7. This protocol is distinct from CC-005, which edits the **parent** program's closure-evidence document to describe an already-immutable historical SHA (`e9ab0fc`) more completely — that edit does not reopen any self-referential cycle, since `e9ab0fc`'s own CI runs already existed (and were already queried) before CC-005's edit, so CC-005 is citing a fact about a prior, already-closed commit, not attempting to cite itself.

---

## 3. CC-001 — Fix AR-003: remove remaining "native" jargon from `ChessViewModel.kt`

### 3.1 Defect

`ChessViewModel.kt:71`: `errorMessage = "A native game is still active. Retry cleanup before starting another game."` and `ChessViewModel.kt:117`: `append("Initial native snapshot failed: ")` — both assigned into `ChessUiState.errorMessage`, which `MainActivity.kt:69-74` renders verbatim in `ChessEngineErrorDialog`, a normal-operation player-visible surface. Both strings existed unchanged since the review baseline and were missed because AR-003's own structural test (`ReviewFixArchitectureTest.kt`, `setupPlayerCopyDoesNotExposeNativeArchitectureJargon`) is scoped only to `SetupScreen.kt`, narrower than the original spec's instruction to sweep "the rest of `android-harness/android-app/src/main/kotlin`."

### 3.2 Fix

- Reword both strings to remove "native" while preserving intended meaning. Suggested (not mandatory): `"A previous game is still active. Retry cleanup before starting another game."` for line 71, and `"Initial game snapshot failed: "` for line 117.
- Grep the rest of `android-harness/android-app/src/main/kotlin` one more time for "native", "JNI", "shared layer", "architecture" and correct any further instance found in a production string literal.
- Rebuild the structural test as a blanket rule rather than a reachability inference (QI-009 — statically determining which string literals are "player reachable" risks becoming a brittle pseudo-reachability analysis, and a future implementer could always argue a given string is "not really reachable" to dodge the check). Instead: forbid "native"/"JNI"/"shared layer"/"architecture" in **every** production Kotlin string literal under `android-harness/android-app/src/main/kotlin`, with a small, explicit allowlist for genuinely internal-only sinks — specifically the `check()` invariant-failure messages and the one `Log.e` call already identified in `ChessViewModel.kt` (lines 109, 176, 395 as of the review). Each allowlist entry must be exact/narrow (matched by its specific surrounding function or line, not a broad exemption), justified inline with a one-line comment explaining why that specific sink is not player-visible, and tied to a sink that genuinely cannot reach the UI (a `check()` failure message or a `Log.e` call, not an `errorMessage`/dialog/status string). The test must scan the whole module, not one file.

### 3.3 Tests

- The broadened structural test passes on the corrected strings and is confirmed, by temporarily reintroducing "native" into `ChessViewModel.kt`'s error strings during implementation, to actually fail (a sanity check, not a permanent test).
- Existing `ChessAppEndToEndInstrumentedTest.kt`/other tests that might reference these exact error strings (grep for `"A native game"`/`"Initial native snapshot"`) are updated if any hard-coded match exists, and remain green.

---

## 4. CC-002 — Fix AR-004: actually perform the verify-first system-bar observation

### 4.1 Defect

The spec required observing real API 35 runtime behavior before any production change, and recording the finding either way. Neither the observation nor a "no change needed" narrative exists anywhere. The instrumentation test added (`SystemBarAppearanceInstrumentedTest.kt`) only asserts `isAppearanceLightStatusBars`/`isAppearanceLightNavigationBars` are `false` — flags whose default value plausibly satisfies the assertion regardless of the actual edge-to-edge background/color regression the spec was concerned about.

### 4.2 Task structure: two commits, not one (QI-003)

A genuine verify-first process cannot honestly compress "observe" and "conditionally fix" into a single commit — doing so would recreate the exact evidence-integrity problem this task exists to correct (a fix and its own justification landing simultaneously, indistinguishable from a fix that was never actually verified). This task is therefore explicitly exempted from the one-task/one-commit rule and is split into two sub-tasks, CC-002A and CC-002B, each its own commit; CC-002B only exists/lands if CC-002A's observation shows it's needed.

### 4.3 CC-002A — Runtime observation (always performed, always its own commit)

This task requires an actual API 35 emulator/device to execute, which this implementation environment may not have locally — if so, use the permanent Android CI's emulator job as the observation vehicle, exactly as `bash scripts/dev.sh android`'s own environment-availability precedent already establishes for this repository.

Add a genuinely diagnostic runtime check — not just the icon-appearance-flag check already present, but something that actually distinguishes "system bars render with the dark product background" from "system bars render with a stock light background" on the exercised API level.

**Observation-evidence contract (QI-004 — the finding must be precise and reproducible, not an uncheckable narrative):** record, at minimum:
- the exact API level exercised (35);
- the emulator/device configuration used (matching the existing permanent Android CI job's configuration, or naming the specific alternative);
- whether the proof is programmatic (an assertion against `WindowInsetsController`/actual rendered color), screenshot/pixel-based, or both;
- if pixel-based, the expected product background/color value and the numeric tolerance applied;
- the preserved artifact/screenshot location if one is captured;
- the exact CI run/job ID in which the observation was made.

If the existing icon-appearance-only test is judged sufficient after this genuine investigation, record that reasoning and the evidence for it explicitly — do not silently leave the task without a positive finding either way.

### 4.4 CC-002B — Conditional remediation (only if CC-002A found a real defect)

CC-002B has exactly two mutually exclusive valid dispositions (FQI-002 — checkbox-per-branch phrasing is impossible to satisfy honestly here, since only one branch can ever be true for a given observation): **remediation-required** or **remediation-not-needed**. Exactly one disposition is reached and recorded with evidence; the other is marked `N/A` rather than left as a false incomplete `[ ]`.

- **If CC-002A found bars render incorrectly (remediation-required disposition):** add the explicit `WindowCompat`/`WindowInsetsControllerCompat` (or `enableEdgeToEdge()`) call the original spec described, in `MainActivity.kt`, as its own commit; re-verify using the same observation contract as CC-002A.
- **If CC-002A found bars already correct (remediation-not-needed disposition):** CC-002B lands no commit; the TODO records this disposition explicitly, referencing CC-002A's evidence as the reason.

### 4.5 Tests

- CC-002A's observation evidence, recorded per the contract above, is the test evidence for that sub-task.
- If CC-002B lands, its re-verification against the same contract is its test evidence.

---

## 5. CC-003 — Correct AR-007 behavioral-evidence claims; add behavioral coverage where practical

### 5.1 Defect

`ChessViewModel.kt`'s `restartGame()`/`resign()`/`submitMove()` guard code is correct, but AR-007.2's checkboxes claim behavioral tests proving "rapid duplicate invocation... results in exactly one logical operation, no second engine/native/JNI/cleanup call" for each of the three functions, plus the `cleanupRequired` case. No such test exists — only `ActiveGameOperationGuardTest.kt`'s pure predicate unit test and `ReviewFixArchitectureTest.kt`'s static source-text-ordering check.

### 5.2 Fix

CC-003 has exactly two mutually exclusive valid dispositions (FQI-002): **seam-built** or **claims-downgraded**. Exactly one is reached and recorded with evidence; the other is marked `N/A` rather than treated as an independently-required checkbox.

- **Seam-built disposition (preferred if a clean test seam exists):** find or add a genuine, narrowly-scoped test seam (e.g., an internal/test-visible way to construct a `ChessViewModel` against a fake/instrumented game handle, or an androidTest that drives the real `ChessGame` through the full app and counts actual engine-call side effects across a rapid double-tap) and use it to behaviorally test **all three** of `restartGame()`, `resign()`, and `submitMove()` — not one representative function (QI-005 — a middle ground where only one operation is executed and the other two are treated as behaviorally proven "by analogy" is explicitly disallowed, since the post-guard bodies and side effects of the three functions genuinely differ even though the guard predicate is shared) — covering both the duplicate-invocation case and the `cleanupRequired` case for each, proving no second operation launches, no state mutation, and no new error is surfaced.
- **Claims-downgraded disposition (if a clean test seam does not exist):** do not distort production architecture solely to manufacture the test. Instead, correct AR-007.2's checkboxes in `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md` to state exactly what is proven — predicate correctness (`ActiveGameOperationGuardTest.kt`) plus static guard-ordering (`ReviewFixArchitectureTest.kt`) — with the behavioral-proof limitation explicitly and honestly documented, not implied to be stronger than it is.

Record explicitly in the TODO which disposition was reached and why.

### 5.3 Tests

- Whichever policy is taken, the TODO's AR-007.2 section accurately reflects what test evidence actually exists after this task — no checkbox may claim behavioral proof that isn't backed by an actual executed test, and if a seam is built, all three functions are covered by it, not just one.

---

## 6. CC-004 — Fix AR-011: add the missing end-to-end promotion test

### 6.1 Defect

AR-011's second required deliverable — an end-to-end tap-driven promotion test, or a documented reason one wasn't practical — is absent from both the code and the TODO, despite the checkbox being marked `[x]`.

### 6.2 Fix

Add an end-to-end instrumentation test that drives a real board through a promotion-eligible position, opens the promotion dialog through the actual production flow (not by invoking `PromotionDialog` directly), selects a promotion piece via a real tap, and asserts the resulting snapshot/move reflects the correct promotion.

CC-004 has exactly three mutually exclusive valid dispositions (FQI-002): **UI-driven fixture**, **test-only fixture seam**, or **documented blocker**. Exactly one is reached and recorded with evidence; the other two are marked `N/A`. Reaching the promotion-eligible position is bounded to the first two mechanisms only (QI-010 — this boundary exists specifically to prevent scope creep into a general production FEN-loading capability added only to make the test convenient):

1. **UI-driven fixture disposition (preferred):** a deterministic sequence of real legal moves, driven through the actual UI (the same board-tap mechanism `PortraitRotationInstrumentedTest.kt`/`ChessAppEndToEndInstrumentedTest.kt` already use), that reaches a promotion-eligible position through ordinary legal play — e.g. racing a pawn down an open file against a depth-1 engine opponent, or an equivalent short, reliable sequence.
2. **Test-only fixture seam disposition (if 1 is impractical):** a narrowly-scoped, **test-only** fixture seam (reachable only from `androidTest` sources, never compiled into or reachable from the production app) that initializes the underlying game session directly to a promotion-eligible position. This must not become, or require, a general/player-facing FEN-loading feature, and must not add any chess-rule/legality logic to Kotlin — the seam only needs to reach a state the real `chess-app`/JNI layer already supports constructing.
3. **Documented-blocker disposition (if both 1 and 2 prove impractical after a genuine attempt):** the specific blocker is documented in the TODO instead of the checkbox being left silently unexplained; no new instrumentation test is added under this disposition.

### 6.3 Tests

- The end-to-end test described above, or the documented-blocker fallback, is this task's deliverable.

---

## 7. CC-005 — Fix the closure-evidence document's CI citation

### 7.1 Defect

`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md` describes pushing a tree-identical validation-trigger commit specifically so permanent CI would validate "the exact authoritative closure tree," and that mechanism genuinely worked — but the document only cites the CI run IDs for the earlier, superseded SHA (`6d9a84d`), not the actual final tree's own runs, which exist, are green, and were found only by independent querying (general/Rust CI run `31419183264`, Android CI run `31419183273`, both against SHA `e9ab0fc623c22bd372ba9c8c2609dfcf74609f84`).

### 7.2 Fix

- Update `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md`'s "Permanent exact-source-SHA CI" section to cite the actual final-tree run IDs (`31419183264` for general/Rust CI, `31419183273` for Android CI) with their own job IDs and conclusions, alongside or in place of the `6d9a84d` citation — the document should be self-evidencing for the tree it claims to validate without requiring a reader to independently query GitHub to find the real final-tree evidence.
- Note explicitly that the `6d9a84d` runs remain valid supporting evidence, but do not describe green CI runs themselves as proof that the two trees are source-identical (QI-007 — passing CI is not a tree-equivalence proof; only a git comparison is). Instead, record the actual git evidence — **path-scoped to the specific claim being made** (FQI-003 — the whole-tree diff between these two SHAs is *not* empty, since closure documentation, the authority index, and the audit script all legitimately changed; an unrestricted or whole-tree comparison would show inequality regardless of whether product/test surfaces changed, so it does not establish or refute the narrower claim actually intended):
  ```bash
  git diff --exit-code 6d9a84d910a3e6438aef390aa733a4b62a71dfdd..e9ab0fc623c22bd372ba9c8c2609dfcf74609f84 -- android-harness crates
  ```
  A zero exit code / empty output from this path-scoped command is the actual evidence that no Android or Rust product/test file differs between the two SHAs. Record its literal output (or its exit code and "empty diff") in the closure-evidence document. Separately, record an unrestricted `git diff --name-only 6d9a84d910a3e6438aef390aa733a4b62a71dfdd..e9ab0fc623c22bd372ba9c8c2609dfcf74609f84` to show exactly which documentation/authority files did change, so the two facts — "product/test surfaces unchanged" and "these specific docs changed" — are each precisely evidenced rather than conflated.

### 7.3 Tests

- N/A — documentation-only. Verified by independently re-querying both new run IDs via `gh` during implementation and confirming they match what gets written, and by independently re-running the recorded git comparison command and confirming its output matches what gets written.

---

## 8. CC-006 — Document AR-006's residual auto-scroll scheduling assumption

### 8.1 Note

The replacement auto-scroll implementation (`GamePanels.kt`, `followLatest`/`snapshotFlow` over `listState.isScrollInProgress`) genuinely removed the original Compose effect-ordering dependency, but introduced a narrower one: `isScrollInProgress` is also `true` during the auto-scroll's own `animateScrollToItem` call, so the mechanism does not structurally distinguish "user-initiated scroll" from "the auto-follow scroll updating its own state." For the app's actual one-ply-at-a-time usage this is safe (a single-row hop keeps `nearBottom` true throughout), but it is undocumented and would not necessarily generalize to a hypothetical bulk-history-replace scenario.

### 8.2 Fix

- Add an inline comment at the `followLatest`/`snapshotFlow` collector in `GamePanels.kt` documenting this specific scope: the mechanism assumes append operations are single-row (matching real gameplay), and a future bulk-replace of history would need re-examination of this assumption before being relied upon.

### 8.3 Tests

- N/A — documentation-only; the two existing auto-scroll tests remain the behavioral evidence and are unaffected.

---

## 9. CC-007 — Strengthen AR-020's rotation test to assert source-square emptiness

### 9.1 Note

`PortraitRotationInstrumentedTest.kt` asserts the destination square's occupant (`"e4 pawn"`) exists both before and after rotation, but never explicitly asserts the source square (`e2`) is empty afterward — a hypothetical bug that duplicated the pawn onto both squares during a rotation-triggered recomposition would not be caught.

### 9.2 Fix

- Add an assertion that no node with content description `"e2 pawn"` exists after the rotation (alongside the existing `"e4 pawn"` presence assertion), completing the state-preservation check.

### 9.3 Tests

- The strengthened assertion is itself the test; confirm it is meaningful by checking it would fail if the move were hypothetically duplicated (reasoned through, not necessarily executed against a deliberately-broken build).

---

## 10. CC-008 — Add the Resign-dialog button contrast pairing to AR-016's matrix

### 10.1 Note

The Resign confirmation dialog's confirm button renders `Danger` content color on `SurfaceElevated` background (`Dialogs.kt`) — a real, distinct rendered combination from the in-row Resign button (`Danger` on `AppBackground`) that `ThemeContrastTest.kt` already covers. The dialog pairing was hand-computed during review to pass (≈5.6:1, well above the 4.5:1 threshold) but is not part of the automated matrix.

### 10.2 Fix

- Add `requireRatio("resign dialog confirm", Danger, SurfaceElevated, 4.5)` (or equivalent) to `ThemeContrastTest.kt`'s existing text/control pair list.

### 10.3 Tests

- The added assertion passes given current token values; this task's deliverable is the assertion itself.

---

## 11. CC-009 — Final validation and closure

### 11.1 Validation

- Run the full applicable validation surface: Android app JVM/unit tests (including the CC-001/CC-003/CC-008 additions), Android lint, CC-004's disposition-dependent validation (its instrumentation test if a fixture disposition was reached, or its documented-blocker record if not), and CC-002A's runtime observation (plus CC-002B's re-verification if it landed).
- Run `bash scripts/dev.sh fast` to confirm no cross-workspace regression.
- **Permanent CI is mandatory, not conditional** (QI-011 — this pass touches Android source/tests and authoritative documentation, the same standard the parent program's own AR-021 already applied to itself): the permanent Android CI workflow/job and the permanent general/Rust CI workflow/job must both be green on the exact final correction SHA, following the closure-SHA protocol in §2.1. This is not gated on "if cross-workspace changes require it" — it is required unconditionally for this pass. Per §2.1/FQI-001, satisfying this requirement means independently confirming (via `gh`) that the terminal trigger SHA's CI is green and reporting those run/job IDs in the final implementation handoff — it does not require writing those IDs back into the repository.
- **CC-004's disposition-dependent validation** (FQI-002): if CC-004 reached the UI-driven-fixture or test-only-fixture-seam disposition, its new instrumentation test passes as part of this validation surface. If CC-004 reached the documented-blocker disposition, there is no new instrumentation test to pass, and this bullet is satisfied by confirming the documented-blocker record is complete instead.

### 11.2 Provenance-preserving correction of the parent TODO (QI-012)

Update `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md` in place, but do not silently rewrite the five previously-inaccurate checkboxes as if they had always been true — that would erase the historical fact that a post-closure correction was required. For each of AR-003, AR-004, AR-007, AR-011, and the closure-evidence CI citation, use provenance-preserving wording distinguishing:

- what the original closure claimed;
- that it was corrected by this pass (naming the specific CC-00N task);
- what the actual final evidence is now, and as of which SHA.

Do not describe corrected checkboxes as though the original AR-00N implementation satisfied them unaided.

### 11.3 Authority closure (QI-008)

- `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md`'s own `Status:` header updated to `Complete`.
- `docs/LEGACY_TODO_INDEX.md`'s "Bounded review-fix trackers" entry for this tracker updated from "in progress" to "completed," matching the wording pattern already used for the other four entries in that list.
- `scripts/task_post_port_review_fix_audit.sh` updated if any of its existing assertions assumed an in-progress state.
- Confirmed no active implementation TODO is registered as a side effect of this closure (the single-slot "active implementation TODO" position remains unaffected by bounded review-fix tracker closure, per the classification's own stated scope).
- Confirmed no temporary correction/validation helper (any script/workflow added solely to drive this correction pass's own CI, analogous to the parent program's temporary Ralph runner) remains in the tree before final exact-SHA validation.

### 11.4 Closure evidence

- Update `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md` per CC-005 (this is a description of the already-immutable **parent** program's historical SHA, not a self-citation — see §2.1 point 7).
- Record all repository-resident evidence (exact local commands run, their results, and every CC-001 through CC-008 disposition) in the companion TODO's closure section.
- Per §2.1/FQI-001, do **not** attempt to write the terminal trigger SHA's own permanent CI run/job IDs into this file or any other repository file — that information is external GitHub Actions metadata, independently verified via `gh`, and reported in this pass's final implementation handoff instead.
- Do not mark any CC task `[x]` without the specific evidence named in its own section above.
