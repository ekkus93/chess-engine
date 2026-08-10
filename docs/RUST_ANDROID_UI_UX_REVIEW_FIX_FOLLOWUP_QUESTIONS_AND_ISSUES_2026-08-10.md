# Rust Android UI/UX Review Fix — Follow-up Questions and Issues — 2026-08-10

**Status:** advisory / second pre-implementation review handoff  
**Branch:** `master`  
**Review-fix spec:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SPEC_2026-08-10.md`  
**Review-fix TODO:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md`  
**Original questions/issues handoff:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_QUESTIONS_AND_ISSUES_2026-08-10.md`  
**Review baseline SHA:** `98e21939b0665f2f54ade7f87cdcaba3fe48025f`  
**Revised spec/TODO commit reviewed here:** `85ae883369e5fc58e3cf8e50328b157369369ddb`

---

## Purpose

This document records the remaining questions and specification issues found after rereading the revised review-fix spec/TODO and the related authority/audit state following the first twelve-item handoff.

The revision materially improved the plan. In particular, it resolved or substantially hardened the `dev.sh fast` rule, review-baseline versus implementation-start SHA tracking, verify-first system-bar handling, auto-scroll timing dependence, busy-path intent, dp-normalized bounds tolerance, Black-orientation coverage, contrast coverage, rotation-test honesty, and exact-SHA CI closure requirements.

However, five issues remain. Three are substantive pre-implementation blockers or closure-policy contradictions, one is a significant test-specification issue that could force an unnecessary visual redesign, and one is minor scope bookkeeping.

**This file is advisory only. It is not a competing implementation authority.** Claude Code should resolve the items below by updating the authoritative spec/TODO and, where needed, the authority index/audit before AR-001 implementation begins.

---

# FQI-001 — BLOCKER: the authority-policy contradiction still exists

## Observation

The revised spec/TODO rejects QI-001 as a blocker by citing precedent: three earlier bounded review-fix passes were implemented while listed only in `docs/LEGACY_TODO_INDEX.md`'s historical inventory and were never placed in its active implementation table.

That precedent does not resolve the contradiction in the current authority document itself.

`docs/LEGACY_TODO_INDEX.md` currently states all of the following:

- there is **no active implementation TODO** registered by the index;
- every TODO-named document not explicitly registered as active is historical/planning evidence unless separately classified as closure authority;
- those historical/planning files are **not active instructions**;
- a future TODO becomes active by being explicitly registered in the authority table.

`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md` is explicitly listed in that historical inventory.

Therefore, the current repository policy still says this TODO is historical/planning evidence and not an active instruction, while the revised spec/TODO simultaneously says it can be Ralph-looped as the implementation tracker. The fact that earlier review-fix programs followed the same inconsistent convention demonstrates precedent, but it does not create an exception in the written rule.

## Question for Claude Code

What repository-level rule makes a bounded review-fix TODO executable while it remains classified as historical/planning evidence and while the authority index says historical TODOs are not active instructions?

## Recommended disposition

Resolve the contradiction explicitly before AR-001. Either:

### Preferred option A — register this TODO as active

- add `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md` to the authority table as the active bounded review-fix tracker;
- update the permanent authority audit accordingly;
- reclassify it at closure.

### Acceptable option B — define an explicit bounded-review-fix exception

If the project intentionally wants large programs and bounded review-fix passes to use different authority mechanics, amend `docs/LEGACY_TODO_INDEX.md` to say so explicitly. For example, define a classification such as "bounded executable review-fix tracker" that:

- is allowed to be implemented/Ralph-looped;
- is distinct from the single large-program "active implementation TODO" slot;
- is not described as mere historical/planning evidence while implementation is in progress;
- is enforced by the permanent authority audit;
- is reclassified at closure.

Do not rely only on prior inconsistent practice while leaving the written authority rules unchanged.

---

# FQI-002 — BLOCKER: AR-007 requires operation identity that the current state model does not contain

## Observation

The revised AR-007 correctly distinguishes two policies:

1. a rapid duplicate invocation of the **same already-in-flight operation** is idempotently suppressed with no error; and
2. a genuinely invalid invocation is visibly rejected.

The problem is that the current `ChessViewModel` does not track which operation is in flight.

Its relevant state is essentially:

- `ChessUiState.busy: Boolean`;
- `operationGeneration: Long`;
- a `monitorJob`;
- the current `game`.

There is no `OperationKind`, active-operation enum, operation token carrying type, or equivalent state that distinguishes "restart is busy" from "resign is busy" from "submit move is busy."

A simple guard such as `if (state.busy) return` can suppress all calls received while busy, but it cannot implement the more specific contract "suppress only a duplicate of the same operation while treating a different invalid operation differently."

The spec/TODO therefore defines product behavior that cannot be implemented from the state it currently says to inspect unless AR-007 also adds operation identity or simplifies the policy.

There is a second factual issue. The revised text says genuinely invalid state should be visibly rejected, "matching `startGame()`'s existing discipline." Current `startGame()` begins with:

```kotlin
val configuration = mutableState.value
if (!configuration.isSetup || configuration.busy || configuration.cleanupRequired) {
    return
}
```

So `cleanupRequired` at that guard is silently returned from. There may already be an error message in state from the earlier failure that established `cleanupRequired`, but that is not the same thing as `startGame()` visibly rejecting this new invocation. The spec should define the desired behavior directly instead of attributing behavior to `startGame()` that it does not currently perform at this guard.

## Questions for Claude Code

1. Does AR-007 actually require distinguishing the **type** of the in-flight operation?
2. If yes, what explicit operation-identity state will be added and where will it live?
3. If no, should the policy instead be simplified to "all invocations received while globally busy are idempotently ignored"?
4. What exactly does "visibly rejected" mean for `cleanupRequired`: set/refresh an error message on each rejected invocation, or merely preserve the already-visible cleanup error that caused the state?

## Recommended disposition

Choose one implementable policy and encode it precisely.

### Option A — track operation identity

Add an explicit internal operation kind/token, for example conceptually:

```text
None | Start | Restart | Resign | SubmitMove | Cleanup | Poll
```

Then AR-007 can distinguish a same-operation duplicate from a different invocation received during another operation. This is the closest implementation of the current prose, but it expands the state machine and therefore needs focused tests.

### Option B — global-busy duplicate suppression

If no product behavior actually needs different handling by operation type, simplify the rule:

- any invocation of `restartGame`, `resign`, or `submitMove` received while `busy == true` returns without launching another operation;
- this is documented as global duplicate/concurrent-input suppression;
- `cleanupRequired` is handled separately and visibly according to an explicitly defined error-state policy.

Whichever policy is selected, remove the inaccurate phrase that this already "matches `startGame()`'s existing discipline" unless `startGame()` is changed to actually exhibit the same visible-rejection behavior.

---

# FQI-003 — SIGNIFICANT: AR-016 may incorrectly require every piece paint component to contrast with every square

## Observation

AR-016 was correctly strengthened to test all four piece/square combinations and overlay-composited states. However, the current wording appears to require both `PieceLightFill`/`PieceLightStroke` and `PieceDarkFill`/`PieceDarkStroke` individually to meet the applicable contrast threshold against both board colors.

That is probably the wrong accessibility model for the rendered chess pieces.

Using the color values named in the spec, approximate WCAG contrast ratios are:

| Foreground component | Background | Approx. ratio |
|---|---|---:|
| Light piece fill `#F7F3EA` | Light square `#E7D7C4` | 1.27:1 |
| Light piece stroke `#26364D` | Light square `#E7D7C4` | 8.69:1 |
| Light piece fill `#F7F3EA` | Dark square `#806A58` | 4.60:1 |
| Light piece stroke `#26364D` | Dark square `#806A58` | 2.40:1 |
| Dark piece fill `#172033` | Light square `#E7D7C4` | 11.55:1 |
| Dark piece stroke `#E8EEF7` | Light square `#E7D7C4` | 1.21:1 |
| Dark piece fill `#172033` | Dark square `#806A58` | 3.19:1 |
| Dark piece stroke `#E8EEF7` | Dark square `#806A58` | 4.37:1 |

The internal fill/stroke pair itself is strongly contrasted:

- light fill vs dark stroke is approximately 11:1;
- dark fill vs light stroke is approximately 14:1.

That is a conventional outlined-piece design: the outline can establish the silhouette boundary when the fill is close to the square, and the fill can establish it where the outline is closer to the square.

Requiring **every internal paint component independently** to satisfy 3:1 against every possible square could force substantial palette changes even when the rendered piece silhouette remains clearly distinguishable. That would turn a test-hardening task into an unnecessary redesign.

## Question for Claude Code

Is AR-016 intended to validate the accessibility/recognizability of the **rendered piece as a composite visual object**, or to require every individual fill/stroke color independently to meet 3:1 against every board square?

## Recommended disposition

Specify the requirement in terms of effective non-text graphical-object contrast rather than raw-token independence.

For each light/dark piece on each light/dark square, validate that the rendered silhouette boundary remains sufficiently distinguishable. The test should account for which visible component actually forms the boundary against the background at the relevant pixels.

Possible implementation approaches include:

- require at least one continuous boundary component (fill edge or stroke) to meet the chosen non-text contrast threshold against the effective background;
- if the piece is always stroked, explicitly treat the stroke as the silhouette boundary and verify the stroke/background relationship where that is the actual rendered edge;
- supplement arithmetic token checks with a narrowly scoped render-level assertion if necessary to prove the expected stroke/fill compositing model.

Continue testing overlays using the actual composited board background, as the revised spec already requires.

Do not force all four raw fill/stroke tokens individually to 3:1 against both board colors unless that stricter requirement is an intentional product-design decision rather than an accessibility inference.

---

# FQI-004 — BLOCKER/CLOSURE CONTRADICTION: AR-020 can be blocked/manual, but AR-021 requires every AR task complete

## Observation

The revised AR-020 correctly fixes the original fallback weakness. It now says that if a runtime rotation attempt cannot be exercised in permanent CI/emulator infrastructure:

- the static manifest/`requestedOrientation` assertion is supporting evidence only;
- the runtime behavior must be recorded honestly as **blocked/manual**;
- the static assertion must not be treated as equivalent proof.

That is the right evidence policy.

However, it conflicts with the rest of the program's closure rules.

The spec still says the pass "closes every identified test-coverage gap." AR-021 acceptance then requires:

- every AR-001 through AR-020 task to be `[x]` with its own test evidence; and
- the program status to become `Complete` only after all of those conditions hold.

If AR-020's runtime portion is genuinely blocked/manual, then the runtime coverage gap is **not closed**, AR-020 cannot honestly be fully `[x]` under the normal meaning of `[x]`, and "closes every identified test-coverage gap" is false.

## Question for Claude Code

What is the intended program status if runtime rotation validation is genuinely impossible in the supported CI/emulator environment?

## Recommended disposition

Choose one closure policy explicitly.

### Option A — runtime rotation is mandatory

Treat AR-020 runtime validation as a hard closure gate. If it cannot be executed, the program remains incomplete until an environment exists where it can be validated.

This is the cleanest interpretation of the current `every AR task is [x]` requirement.

### Option B — allow qualified closure with an explicit open manual item

Permit a terminal status such as:

```text
Complete — automated review-fix implementation validated; runtime rotation-attempt validation remains blocked/manual
```

Under this policy:

- leave the runtime-validation sub-checkbox open or mark it with a distinct blocked/manual state rather than `[x]`;
- adjust AR-021 so full program closure does not falsely require every AR-020 runtime claim to be proven;
- change "closes every identified test-coverage gap" to something like "closes every automatable identified gap and records any environment-blocked runtime gap explicitly";
- carry the blocked/manual item into the closure-evidence document.

Do not mark the runtime requirement `[x]` merely because its inability to run was documented.

---

# FQI-005 — MINOR: the declared touched-file scope omits the closure-evidence file AR-021 explicitly creates

## Observation

The spec's engineering-constraints section has an explicit "This pass touches:" list. It now correctly includes:

- Android source/test trees;
- `android-app/build.gradle.kts` for a possible UIAutomator test dependency;
- Rust SAN/JNI test surfaces;
- `docs/RUST_ANDROID_APP.md`;
- the spec/TODO pair.

But the very next bullet says AR-021 creates:

`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md`

That file is not in the declared touched-file list.

## Question for Claude Code

Is the "This pass touches:" list intended to be exhaustive?

## Recommended disposition

If yes, add:

`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md`

to the list explicitly.

The already-landed `LEGACY_TODO_INDEX.md` / permanent-audit bookkeeping can remain outside that list if it is intentionally classified as pre-implementation preparation rather than AR-001-through-AR-021 implementation scope, but that distinction should remain clear.

---

## Suggested pre-Ralph-loop disposition checklist

Before AR-001 begins, I recommend confirming all of the following:

- [ ] FQI-001: authority rules no longer classify the executable review-fix tracker as mere non-active historical/planning evidence, either through active registration or an explicit bounded-review-fix authority category.
- [ ] FQI-002: AR-007's busy-input semantics are implementable from a defined state model; same-operation identity is either explicitly tracked or the policy is simplified to global-busy suppression; `cleanupRequired` visible-rejection behavior is defined directly.
- [ ] FQI-003: AR-016 measures rendered piece recognizability/non-text boundary contrast rather than accidentally requiring every fill/stroke token independently to contrast with every board square, unless that stricter palette rule is intentionally chosen.
- [ ] FQI-004: AR-020 blocked/manual behavior and AR-021 final closure rules are mutually consistent.
- [ ] FQI-005: the declared touched-file scope includes the closure-evidence document if the list is exhaustive.
- [ ] Implementation-start SHA is captured only after these final pre-implementation corrections have landed.

---

## Overall assessment

The revised review-fix plan is substantially stronger than the original version, and most of the first handoff's twelve issues are now resolved well. These five follow-up items are narrower. FQI-001, FQI-002, and FQI-004 should be resolved before the Ralph loop because they affect authority, implementability, or truthful closure semantics. FQI-003 should be resolved before AR-016 so an incorrect contrast model does not drive unnecessary palette changes. FQI-005 is bookkeeping but is easy to fix now.
