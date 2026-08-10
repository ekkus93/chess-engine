# Rust Android UI/UX Review-Fix Closure Corrections — Questions and Issues — 2026-08-10

**Status:** review handoff only — no implementation changes requested by this document
**Branch reviewed:** `master`
**Spec reviewed:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_SPEC_2026-08-10.md`
**TODO reviewed:** `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md`
**Review baseline named by those documents:** `e9ab0fc623c22bd372ba9c8c2609dfcf74609f84`

---

## Purpose

This file records questions and specification issues found while reviewing the closure-corrections spec/TODO pair before implementation. It does **not** request any product-code change by itself. The correction program is directionally sound, but several contract/closure details should be resolved before a Ralph loop or other implementation pass starts.

The five substantive correction findings in the spec (AR-003, AR-004, AR-007, AR-011, and stale closure-evidence CI citation) and the three smaller hardening items (AR-006 auto-scroll assumption, AR-020 source-square emptiness assertion, AR-016 Resign-dialog contrast pairing) are reasonable targets. The issues below are about making the correction pass internally consistent, auditable, and resistant to another exact-SHA closure problem.

---

# QI-001 — The correction pass does not yet solve its own exact-SHA closure problem

## Issue

CC-005 correctly requires the existing closure evidence to cite the real final-tree permanent runs for SHA `e9ab0fc623c22bd372ba9c8c2609dfcf74609f84`:

- general/Rust CI run `31419183264`
- Android CI run `31419183273`

However, CC-001 through CC-009 will themselves change the repository tree. Once this correction pass lands, `e9ab0fc...` is only the **correction-review baseline**, not the final correction tree.

CC-009 currently leaves permanent CI conditional with wording equivalent to "if cross-workspace changes require it." That is too weak. This pass changes Android production/test code and authoritative closure documentation, so exact-final-SHA permanent validation should be mandatory.

There is also the known self-reference problem: if a closure document is updated *after* final CI merely to insert those final run IDs, that documentation update creates a new SHA which is no longer the SHA those runs validated.

## Question

What is the intended exact-SHA closure protocol for this correction pass?

## Recommended resolution

Define all of the following explicitly before implementation:

1. `e9ab0fc623c22bd372ba9c8c2609dfcf74609f84` is the **correction-review baseline SHA**, not the eventual final correction SHA.
2. Permanent Android CI and permanent general/Rust CI are mandatory on the exact final correction tree.
3. The corrections pass gets its own explicit closure-evidence record (or an equally explicit section in the corrections TODO) distinguishing:
   - review baseline SHA,
   - implementation-start SHA,
   - final correction source/evidence SHA,
   - exact permanent CI run/job IDs.
4. The spec defines how the repository avoids infinite "write run IDs -> new SHA -> revalidate -> write new run IDs" recursion. A practical convention should be chosen in advance rather than rediscovered during CC-009.

This is the highest-priority issue in the current documents.

---

# QI-002 — The declared touched-file scope is incomplete

## Issue

The spec's engineering-constraints section enumerates touched files, but CC-000 explicitly requires changes to:

- `docs/LEGACY_TODO_INDEX.md`
- `scripts/task_post_port_review_fix_audit.sh`

Those files are not included in the declared touched-file list.

CC-002 also discusses strengthening `SystemBarAppearanceInstrumentedTest.kt`, which is not listed. CC-004 may reasonably need a new end-to-end instrumentation test or an existing E2E test other than `PromotionDialogInstrumentedTest.kt`, but the scope list is currently narrower than the task contract.

## Question

Should the touched-file scope be widened before implementation so satisfying CC-000/CC-002/CC-004 does not require violating §2?

## Recommended resolution

Add at least:

- `docs/LEGACY_TODO_INDEX.md`
- `scripts/task_post_port_review_fix_audit.sh`
- `SystemBarAppearanceInstrumentedTest.kt`
- whichever existing/new end-to-end instrumentation test file is selected for CC-004

or rewrite the scope as an allowed surface/category list rather than an exhaustive filename list.

---

# QI-003 — CC-002 conflicts with the "one CC task = one commit" rule

## Issue

CC-002 explicitly requires a genuine **verify-first** process:

1. strengthen/add a diagnostic,
2. run it on API 35,
3. observe actual behavior,
4. only then decide whether production code needs a fix,
5. if needed, fix and re-run.

The TODO simultaneously says each CC task lands in its own commit.

If the diagnostic reveals a real system-bar problem, preserving evidence that the observation happened **before** the fix naturally requires at least two commits or two explicitly separated sub-stages. Forcing the diagnostic and conditional production fix into one commit would undercut the verify-first requirement the correction is meant to restore.

## Question

Should CC-002 be exempted from the one-task/one-commit convention, or split into two tasks?

## Recommended resolution

Either:

- allow CC-002 to use an observation commit followed by a conditional remediation commit; or
- split it into `CC-002A — runtime observation` and `CC-002B — conditional remediation`.

Do not compress the observation and fix into one commit merely to satisfy bookkeeping.

---

# QI-004 — CC-002's runtime-observation acceptance criterion is still too vague

## Issue

The requirement to distinguish "dark-background-correct" from "stock-light-regressed" system-bar rendering is directionally correct, but not yet precise enough for a task whose purpose is correcting an evidence-integrity failure.

A future implementer could still write "observed correct" without preserving enough evidence to reproduce or audit the claim.

## Question

What exact observable constitutes successful CC-002 evidence?

## Recommended resolution

Specify, before implementation, the observation contract. For example:

- API level: API 35;
- emulator/device configuration used;
- navigation mode if relevant;
- exact screen/state captured;
- whether proof is programmatic, screenshot/pixel-based, or both;
- expected product background/color and any numeric tolerance if pixel-based;
- preserved artifact/screenshot location;
- exact CI run/job ID in which the observation was made.

If visual inspection is used, preserve the screenshot/artifact rather than relying on an uncheckable narrative statement.

---

# QI-005 — CC-003's "one representative operation" path is weaker than the claim being corrected

## Issue

The parent AR-007.2 checklist claimed behavioral duplicate-invocation evidence for all three existing-game operations:

- `restartGame()`
- `resign()`
- `submitMove()`

The correction spec's preferred path says a real behavioral seam only needs to prove one representative function, with an argument that the identical guard generalizes to the other two.

That is weaker than the original claim. Although the guard predicate may be shared/identical, the post-guard bodies and side effects differ. If the project is going to pay the complexity cost of a genuine `ChessViewModel`/game-session test seam, testing all three is much stronger and avoids another "documentation claims more than execution proves" situation.

## Question

If a genuine behavioral seam is added, why not execute the duplicate/cleanupRequired behavior against all three operations?

## Recommended resolution

Use one of two clear policies:

### Preferred if a clean seam exists

Behaviorally test all three operations, including the `cleanupRequired` path and the claimed "no second operation / no state mutation / no new error" properties.

### Preferred if a clean seam does not exist

Do **not** distort production architecture solely to manufacture the test. Correct AR-007.2's old language to state exactly what is proven: predicate correctness plus static guard ordering, with the behavioral limitation explicitly documented.

Avoid the middle ground where one operation is executed and the other two are treated as behaviorally proven by analogy.

---

# QI-006 — CC-003's title conflicts with its acceptable fallback

## Issue

The task is titled roughly "add missing behavioral duplicate-invocation tests," but its acceptable fallback explicitly permits adding no behavioral test at all and instead correcting the parent TODO's overstated evidence claim.

That fallback is reasonable and honest, but the task name currently suggests only one acceptable outcome.

## Question

Should CC-003 be renamed to match both allowed resolution paths?

## Recommended resolution

Use wording such as:

> **CC-003 — Correct AR-007 behavioral-evidence claims; add behavioral coverage where practical**

This makes the acceptance semantics explicit and avoids pressure to add an awkward seam merely to satisfy the title.

---

# QI-007 — Green CI runs do not prove tree equivalence between `6d9a84d` and `e9ab0fc`

## Issue

CC-005 says the earlier `6d9a84d` runs may be retained as supporting evidence that no source/test file differs between that SHA and `e9ab0fc`.

The statement may be true, but the green CI runs themselves do **not** establish tree equivalence. A Git tree/commit comparison establishes that fact.

## Question

Should the closure evidence record an explicit commit/tree comparison instead of presenting the old runs as proof of no source/test differences?

## Recommended resolution

If the no-source/test-difference claim remains, record explicit Git evidence such as:

- a commit comparison,
- changed-file list,
- tree SHA comparison,
- or equivalent reproducible Git command/output.

The `6d9a84d` runs can remain valuable historical/supporting CI evidence, but they should not be described as the evidence that two trees are equivalent.

---

# QI-008 — CC-000 registers the new tracker, but CC-009 does not explicitly close its authority state

## Issue

CC-000 correctly requires adding the correction TODO to `docs/LEGACY_TODO_INDEX.md`'s bounded-review-fix classification and updating the audit.

CC-009 does not equally explicitly require closure of that authority state when the corrections finish.

## Question

What exact index/audit state should exist after CC-009 completes?

## Recommended resolution

CC-009 should explicitly require:

- correction TODO Status -> `Complete`;
- bounded-review-fix index entry changed from in-progress to completed;
- audit expectations updated accordingly;
- confirmation that no active implementation TODO is registered after closure, assuming that remains the intended authority model;
- temporary correction/validation helpers removed before final exact-SHA validation.

---

# QI-009 — CC-001's proposed "player-reachable string" structural test may be unnecessarily brittle

## Issue

The intent is correct: the existing test was too narrow because it scanned only `SetupScreen.kt` while player-visible architecture jargon remained in `ChessViewModel.kt` error strings.

However, statically determining whether an arbitrary Kotlin string literal is "player reachable" can become a brittle pseudo-reachability analysis.

## Question

Would a simpler, stricter structural rule be preferable?

## Recommended resolution

Consider forbidding `native` / `JNI` / `shared layer` / `architecture` in **all production string literals** under the Android app, with a tiny explicit allowlist for named internal-only invariant/log strings.

Each allowlisted string should be:

- exact/narrow;
- justified inline;
- tied to an internal-only sink such as `check()` or logging.

This is easier to audit and harder to accidentally bypass than trying to infer UI reachability from source text.

---

# QI-010 — CC-004 should define whether a test-only promotion-position seam is allowed

## Issue

The end-to-end promotion requirement is valuable: the production board flow should open the promotion dialog and apply the selected promotion, rather than testing `PromotionDialog` directly.

The unresolved design question is how instrumentation reaches a promotion-eligible position.

If the current app has no clean deterministic position/FEN fixture available to instrumentation, an implementer may be tempted to add a general production FEN-loading capability purely to make the test convenient. That would be unnecessary scope expansion.

## Question

What fixture mechanisms are allowed for CC-004?

## Recommended resolution

State one of these explicitly:

1. Prefer a deterministic legal move sequence driven through the real UI if practical; or
2. permit a narrowly scoped internal/test-only fixture seam that initializes a legal promotion position without adding a player-facing/general production FEN-loading feature.

Do not add chess-rule logic to Kotlin, and do not widen product functionality simply to accommodate the test.

---

# QI-011 — CC-009 should require permanent CI, not "if cross-workspace changes require it"

## Issue

This is related to QI-001 but should be fixed directly in the TODO text.

The CC-009 evidence template currently says:

```text
Permanent CI run/job IDs (if cross-workspace changes require it):
```

This corrections pass changes at least Android source/tests and authoritative documentation. The same closure standard applied to the parent review-fix pass should apply here.

## Recommended resolution

Replace the conditional field with mandatory evidence fields, for example:

```text
Permanent Android CI run/job IDs:
Permanent general/Rust CI run/job IDs:
Exact final correction SHA validated by both:
```

and add corresponding required `[ ]` gates to CC-009 acceptance.

---

# QI-012 — Clarify how prior parent-program claims are corrected without rewriting history ambiguously

## Issue

CC-009 says to update the parent `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_TODO_2026-08-10.md` "in place" so five inaccurate claims reflect what the correction pass actually established.

That is reasonable, but there are two distinct kinds of historical statement:

1. claims that were simply false at the time of the original closure; and
2. claims that become true only because this correction pass adds new implementation/test evidence later.

If old checkboxes are silently rewritten to look as though they were originally satisfied, the historical record becomes ambiguous.

## Question

How should the parent TODO distinguish original evidence from correction-pass evidence?

## Recommended resolution

When correcting the parent TODO, preserve provenance. For each affected AR item, use wording such as:

- original closure claim corrected by CC-00N;
- original evidence was narrower than stated;
- final claim satisfied as of correction SHA `<sha>` by `<specific test/evidence>`;

or explicitly downgrade the old claim if the correction chooses the documentation-only fallback.

The parent document should become accurate without erasing the fact that a post-closure correction was required.

---

## Suggested pre-implementation disposition

The correction program itself should proceed, but I recommend resolving at least the following **before** starting implementation:

1. **QI-001** — exact-SHA closure protocol for the corrections pass;
2. **QI-002** — incomplete touched-file scope;
3. **QI-003 / QI-004** — CC-002 verify-first commit/evidence mechanics;
4. **QI-005 / QI-006** — CC-003 behavioral-evidence policy;
5. **QI-008 / QI-011** — final authority and mandatory permanent-CI closure gates;
6. **QI-012** — provenance-preserving correction of the parent TODO.

The remaining items are lower-risk specification hardening but are still worth resolving before the tracker is activated.

---

## No-code-change note

Creation of this review file is the only requested repository change associated with this review handoff. No production code, tests, correction spec/TODO content, parent tracker, closure evidence, authority index, or audit script should be modified merely by creating this document.
