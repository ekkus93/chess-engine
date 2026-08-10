# Rust Android UI/UX Review Fix — Questions and Issues Handoff — 2026-08-10

**Status:** advisory / pre-implementation review handoff  
**Branch:** `master`  
**Review-fix spec:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_SPEC_2026-08-10.md`  
**Review-fix TODO:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md`  
**Review baseline SHA:** `98e21939b0665f2f54ade7f87cdcaba3fe48025f`  
**Planning-doc commit / current master at handoff creation:** `8f7bf44a767cefd47d97ce1b58de7ccba3cc8671`

---

## Purpose

This document records questions and specification issues found during an independent read of the proposed Rust Android UI/UX review-fix spec and TODO before implementation begins.

The overall review-fix plan is strong. The findings are generally well scoped, the Rust/Kotlin ownership boundary is preserved, and the documents explicitly reject silent fallback/fail-open behavior. The issues below are primarily authority/process contradictions, acceptance-criteria ambiguities, and test-strengthening opportunities that should be resolved before starting the Ralph loop.

**This file is advisory only. It is not a competing implementation authority.** Claude Code should resolve the items below by updating the review-fix spec/TODO and any required authority/audit documents before implementation begins.

Two items are considered blockers:

1. The review-fix TODO is not currently registered as an active implementation authority.
2. The documents contradict each other about whether `bash scripts/dev.sh fast` is in scope.

The remaining items are specification hardening. They should still be resolved before implementation where practical so the Ralph loop has unambiguous acceptance criteria.

---

# QI-001 — BLOCKER: the review-fix TODO is not registered as active implementation authority

## Observation

`docs/LEGACY_TODO_INDEX.md` currently says there is **no active implementation TODO**. It also lists `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md` in the historical/planning TODO inventory.

The same authority index says that a newly added `docs/*TODO*.md` file is historical by default unless it is explicitly registered as active, and its maintenance rule requires a newly active TODO to be added to the authority table and the permanent TODO-authority audit to be updated.

That means starting a Ralph loop directly against the current review-fix TODO would intentionally implement a document that the repository itself says is non-authoritative planning history.

## Question for Claude Code

What exact activation sequence will make `RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md` the authoritative active implementation tracker before any production/test implementation commit lands?

## Recommended disposition

Make authority activation part of AR-000 and perform it before implementation:

- register `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md` as the active implementation TODO in `docs/LEGACY_TODO_INDEX.md`;
- update the repository's permanent TODO-authority audit/check so the new classification is enforced rather than merely documented;
- update the index's active/historical counts and inventory consistently;
- preserve the already-closed redesign tracker and closure evidence as historical/completed authority rather than reopening them;
- at review-fix closure, reclassify this TODO back to historical/completed status and register the new closure-evidence authority if one is created.

Do not begin AR-001 implementation while the repository still classifies the TODO as historical/planning evidence.

---

# QI-002 — BLOCKER: `dev.sh fast` is simultaneously excluded and required

## Observation

The review-fix spec/TODO says this pass does **not** perform the previous Phase 17 literal local `bash scripts/dev.sh android` / `fast` invocations.

However, AR-021 explicitly requires:

- `bash scripts/dev.sh fast` passes; and
- a `bash scripts/dev.sh fast result` in closure evidence.

Those rules cannot both be true.

## Question for Claude Code

Is `bash scripts/dev.sh fast` a required review-fix validation gate, or is the literal local command explicitly outside this program?

## Recommended disposition

Choose one policy and state it consistently in the spec, TODO status rules, and AR-021.

Preferred policy:

- require `bash scripts/dev.sh fast` for this review-fix pass when the environment can run it;
- if a literal local execution is genuinely unavailable for an environmental reason, require the equivalent permanent general CI on the exact final SHA and explicitly record that the literal local command was not run;
- do not silently treat an unrun local command as passed;
- do not retain prose saying `fast` is out of scope while AR-021 makes it mandatory.

The historical Phase 17 checkbox can remain untouched; running `fast` as a validation gate for this new program does not require reopening the old tracker.

---

# QI-003 — Separate the review baseline SHA from the implementation-start SHA

## Observation

The review correctly targets shipped redesign baseline SHA:

`98e21939b0665f2f54ade7f87cdcaba3fe48025f`

But the proposed review-fix spec/TODO themselves were subsequently added at:

`8f7bf44a767cefd47d97ce1b58de7ccba3cc8671`

These are different concepts:

- **review baseline SHA** = the product state that was independently reviewed;
- **implementation-start SHA** = the exact repository state from which the review-fix implementation actually begins.

AR-021 has a closure-evidence field for an implementation-start SHA, but AR-000 does not currently require it to be captured before work starts.

## Question for Claude Code

What exact SHA is the implementation-start boundary for this pass after the planning/authority corrections are committed?

## Recommended disposition

Add an explicit AR-000 requirement to record both values separately:

- review baseline SHA: fixed at `98e21939...`;
- implementation-start SHA: captured from `master` immediately before the first implementation task begins, after any pre-implementation spec/TODO/authority corrections.

Do not overwrite or reinterpret the review baseline to mean implementation start.

---

# QI-004 — The declared file scope is narrower than the work the TODO actually requires

## Observation

The spec's engineering-constraints section declares a relatively narrow touched-file scope, primarily Android source/tests, SAN tests, JNI tests, and the spec/TODO pair.

The actual tasks already imply additional files/categories:

- AR-005 explicitly edits `docs/RUST_ANDROID_APP.md`;
- QI-001 authority activation requires `docs/LEGACY_TODO_INDEX.md` plus the permanent authority audit/check;
- AR-020 may require Gradle dependency/configuration changes if UIAutomator is not already available;
- AR-021 implies a new closure-evidence document but does not name it;
- final exact-SHA CI/closure work may require evidence metadata beyond the original declared pair.

An inaccurate scope declaration makes later changes look like scope creep even when they are required by the TODO itself.

## Question for Claude Code

What is the complete intended allowed-file scope for this pass, including process documentation, build/test configuration, and closure evidence?

## Recommended disposition

Expand the spec's declared scope before implementation so it honestly covers the tasks already authorized. Explicitly name the intended closure record, preferably:

`docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_EVIDENCE_2026-08-10.md`

Also state whether Gradle/build configuration may be changed solely when needed for an explicitly authorized test dependency such as UIAutomator.

---

# QI-005 — AR-007 is ambiguous about visible rejection versus duplicate-input suppression

## Observation

AR-007 says `restartGame()`, `resign()`, and `submitMove()` should re-check busy/cleanup state and reject invalid invocations **visibly rather than silently no-oping or double-executing**.

The tests, however, primarily require rapid double-invocation to result in exactly one logical operation. That leaves at least two materially different UX policies possible:

1. second tap is an expected duplicate and is ignored/idempotently suppressed without surfacing an error; or
2. second tap is treated as an invalid operation and produces visible user-facing rejection.

Both can satisfy "exactly one logical operation," but they are not the same product behavior.

## Question for Claude Code

Should a rapid duplicate tap while an operation is already busy be treated as a normal idempotent duplicate-input suppression, or as a visible user error?

## Recommended disposition

Define the distinction explicitly.

Preferred policy:

- rapid duplicate UI input that refers to the same already-started operation may be idempotently suppressed without an error dialog, provided the behavior is deliberate, documented, and tested as duplicate-input suppression;
- this exception must **not** become a general silent-failure path;
- engine/native/JNI/cleanup failures and genuinely rejected operational states remain visible and fail closed;
- no second engine operation, cleanup operation, or state mutation may occur.

Update both the fix wording and tests so they assert the chosen policy rather than leaving "visible reject" and "no-op" interchangeable.

---

# QI-006 — AR-006 should prefer removing the Compose timing dependency, not merely documenting it

## Observation

The current auto-scroll behavior depends on an undocumented scheduling relationship between a `LaunchedEffect(rows.size)` and the layout pass that updates `LazyListState.layoutInfo`.

The proposed plan permits retaining this timing dependency and adding a comment if a more robust formulation is not straightforward.

That is safer than leaving it undocumented, but it still normalizes a fragile ordering assumption that could silently change under a future Compose upgrade.

## Question for Claude Code

Can the implementation capture the prior scroll/list state explicitly so correctness does not depend on effect-versus-layout ordering?

## Recommended disposition

Strengthen AR-006 to make the preference explicit:

1. first attempt a formulation that records the relevant pre-append state directly and bases the post-append decision on that captured state;
2. preserve the two existing behavior tests unchanged;
3. retain the timing-dependent approach only if the robust alternative is demonstrably impractical or creates greater correctness risk;
4. if retained, record the dependency as explicit technical debt and identify the tests that guard it.

A source comment alone should be the fallback, not the first-choice resolution.

---

# QI-007 — AR-008's tolerance must define its coordinate unit

## Observation

AR-008 requires a shared tolerance-aware layout-bounds helper and suggests a small tolerance such as `0.5f` / `BOUNDS_TOLERANCE_DP` in the spec discussion.

Compose test bounds can be represented in pixel-space `Rect`s even when the conceptual layout requirement is stated in dp. A tolerance named as dp but applied directly to raw pixel coordinates would change meaning across device densities.

## Question for Claude Code

Are shared layout bounds normalized to dp before comparison, or is the tolerance intentionally defined in physical pixels?

## Recommended disposition

Pick one coordinate system and make it explicit in the helper API, constant name, comments, and tests.

Preferred approach:

- normalize measurements to dp before applying a dp-named tolerance; or
- if raw pixel bounds are intentionally compared, name the constant in px and derive any dp threshold through test density.

Add a test with a non-1.0 density (or equivalent conversion-level unit test) so the helper cannot accidentally treat `0.5 dp` as `0.5 px`.

---

# QI-008 — The Black-orientation test must prove that it is actually exercising Black orientation

## Observation

AR-009 adds Black-orientation containment and spatial-stability tests. That is important because the current automated layout coverage is White-only.

But containment and stability geometry may remain identical in White orientation. A test accidentally wired back to White could therefore still pass all of its intended geometric assertions.

The TODO currently proposes an implementation-time sanity check that the test fails if the fixture is reverted to White, but the permanent test itself should carry a Black-specific assertion rather than relying only on a temporary mutation experiment.

## Question for Claude Code

What permanent semantic or coordinate assertion will prove the rendered board is Black-oriented?

## Recommended disposition

Keep the containment/stability checks, and add at least one permanent orientation-specific assertion, for example a known square/piece/file/rank relationship whose screen position differs between White and Black orientation.

The test should fail if `humanSide` or the fixture setup is accidentally changed back to White even when all generic containment geometry remains valid.

---

# QI-009 — AR-016 contrast coverage should test the full board/piece/overlay matrix

## Observation

The contrast task is useful, but the proposed matrix appears narrower than the real rendering combinations.

A light piece can occupy either a light or dark square, and a dark piece can occupy either a light or dark square. Testing only one "respective" square pairing per piece color leaves real board positions uncovered.

The original UI requirements also include selection, legal-move, and last-move overlays. Those overlays can materially alter the effective square color under a piece or coordinate label, but the proposed automated contrast gate does not clearly require worst-case overlay combinations.

## Question for Claude Code

Which actual rendered combinations are considered contrast-critical, and will the automated test cover all of them rather than only nominal token pairs?

## Recommended disposition

At minimum, test:

- light piece versus light square;
- light piece versus dark square;
- dark piece versus light square;
- dark piece versus dark square;
- coordinate labels against both board colors;
- relevant piece/text contrast after last-move overlay;
- relevant piece/text contrast after selection overlay;
- relevant piece/text contrast after legal-move overlay where that overlay can coincide with the rendered foreground.

If compositing is alpha-based, compute the effective composited background color rather than comparing only the raw overlay token to the raw foreground token.

The goal is to avoid an automated "contrast passed" claim that does not cover legal board states actually shown to a player.

---

# QI-010 — AR-020's fallback does not prove the runtime requirement

## Observation

AR-020's desired behavior is runtime-specific:

> attempt rotation → remain portrait → game state unchanged

The TODO currently allows an unavailable CI rotation attempt to fall back to asserting the manifest/runtime portrait lock is sufficient.

That verifies configuration intent, but it does **not** verify the requested runtime behavior or state preservation.

## Question for Claude Code

If emulator/device rotation cannot be exercised in permanent CI, should the runtime acceptance item be marked blocked/manual instead of complete?

## Recommended disposition

Yes.

- Keep static manifest/requested-orientation assertions as useful supporting evidence.
- Do not treat those assertions as equivalent to an actual rotation-attempt test.
- If runtime rotation cannot be executed in the supported CI/emulator environment, record the runtime portion explicitly as blocked/manual with the concrete environmental reason.
- Do not check off a runtime coverage gap merely because the configuration appears to make the bug unlikely.

This keeps evidence honest and avoids converting "not tested" into "verified."

---

# QI-011 — AR-004 must stay verify-first rather than assuming the system-bar defect exists

## Observation

The review identified a credible API-35 risk: the app appears to rely on legacy XML system-bar attributes under edge-to-edge behavior where those mechanisms may no longer control the actual rendered result.

The TODO title says "verify and fix," which is appropriate. Some surrounding prose, however, can be read as treating the runtime defect as already confirmed.

## Question for Claude Code

Can AR-004 preserve an explicit decision point after API-35 runtime verification instead of mandating window-management changes before observing the actual behavior?

## Recommended disposition

Use a verify-first workflow:

1. inspect the current API-35 runtime state and captured pixels/observable insets-controller state;
2. if the bars are incorrect or the intended appearance state is not actually established, add the modern explicit mechanism and test it;
3. if current runtime behavior is already correct through another mechanism, document why and avoid unnecessary production window-management code;
4. regardless, add/retain a regression test that proves the intended state rather than relying on XML inspection alone.

The legacy mechanism is suspicious enough to require runtime verification, but suspicion alone should not force a production change.

---

# QI-012 — Final closure should require permanent exact-SHA CI, not CI only "where obtained"

## Observation

This pass affects Android production/test code and also extends Rust SAN/JNI tests. The repository already has permanent Android/general validation infrastructure.

AR-021 currently enumerates local/focused gates but does not make permanent exact-final-SHA GitHub Actions success an explicit non-optional closure criterion.

For a post-closure hardening pass, allowing CI to be merely opportunistic would make the evidence chain weaker than the program it is repairing.

## Question for Claude Code

Which permanent GitHub Actions workflows must be green on the exact final source/evidence SHA before the TODO may be marked complete?

## Recommended disposition

Make exact-SHA permanent CI mandatory:

- require the permanent Android CI workflow/job to pass on the exact final SHA;
- require the permanent general/Rust CI workflow/job to pass on the exact final SHA because AR-017/AR-019 touch Rust/JNI test surfaces;
- record workflow run IDs, job IDs, conclusions, and the exact validated SHA in closure evidence;
- if a documentation-only closure commit changes the SHA after source CI passed, follow the repository's established exact-SHA evidence policy rather than claiming an earlier SHA validates a later one;
- no `where obtained`, `if available`, or equivalent optional language for required permanent gates.

Do not mark the review-fix program `Complete` until the required permanent CI is green for the authoritative final state.

---

# Suggested pre-implementation resolution order

Before starting AR-001 implementation, I recommend Claude Code resolve these in this order:

1. **QI-001:** activate the review-fix TODO as repository authority and update the authority audit.
2. **QI-002:** reconcile the `dev.sh fast` scope contradiction.
3. **QI-003:** record the implementation-start SHA separately from the review baseline.
4. **QI-004:** make the allowed file/document/build scope honest and name the closure-evidence file.
5. **QI-005 through QI-011:** tighten the affected task acceptance criteria so implementation cannot choose a weaker interpretation accidentally.
6. **QI-012:** strengthen final closure to require permanent exact-SHA CI.
7. Commit the corrected planning/authority documents.
8. Record that resulting `master` SHA as the implementation-start SHA.
9. Only then begin the Ralph loop at AR-001.

---

# Overall assessment

The review-fix spec/TODO should **not** be rejected. The underlying findings are strong and worth implementing. In particular, the newest-move omission, Black-orientation coverage gap, negative snapshot parsing tests, functional dialog tests, SAN edge-case tests, contrast validation, and lifecycle/busy-path review are all useful work.

The principal risk is not the technical direction; it is starting implementation while the repository's own authority rules classify the TODO as historical, and while a few acceptance criteria permit contradictory or weaker interpretations.

Once QI-001 and QI-002 are resolved, and the remaining items are incorporated as specification hardening, the pair should be in good shape for a Ralph loop.
