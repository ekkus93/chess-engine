# Rust Android UI/UX Review-Fix Closure Corrections — Follow-Up Questions and Issues — 2026-08-10

**Review target:**
- `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_SPEC_2026-08-10.md`
- `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md`

**Review baseline named by those documents:** `e9ab0fc623c22bd372ba9c8c2609dfcf74609f84`

**Purpose:** Record the remaining pre-implementation questions/issues after the first QI-001 through QI-012 review was incorporated. This file is review feedback only. It does not authorize implementation and does not modify product code, tests, or the correction spec/TODO.

---

## FQI-001 — The revised terminal closure-SHA protocol is still self-referential

### Issue

The new §2.1 closure-SHA protocol correctly recognizes the recursive problem created by writing final CI run IDs into a repository document and thereby changing the SHA that those runs validated. However, the proposed termination step still contains an impossible sequencing claim.

The spec says, in substance:

1. Finish all substantive source/test/documentation changes.
2. If necessary, create one empty tree-identical trigger commit.
3. Run permanent Android and general/Rust CI against that trigger SHA.
4. Record the resulting run IDs once, "in that trigger commit's own citation."
5. Make no further commit.

The companion TODO similarly says the final run/job IDs are to be "recorded once, at the terminal trigger commit."

The run IDs do not exist until after the trigger commit has already been created and pushed. Therefore they cannot literally be written into that commit. Writing them into a Markdown file after the runs finish necessarily creates a new commit/SHA, recreating the recursion the protocol is trying to avoid.

### Question

What is the exact evidence convention intended at the terminal point?

### Recommended resolution

Use an explicitly non-self-referential convention:

- The final substantive repository commit contains all authoritative correction documentation and all evidence that exists at commit time.
- If a tree-identical CI trigger commit is needed, create exactly one such empty commit.
- Permanent Android and general/Rust CI validate that exact trigger SHA.
- The final run/job IDs and conclusions are treated as immutable external GitHub Actions metadata associated with that exact SHA.
- Do **not** edit repository files afterward merely to insert those run IDs, because doing so would create another SHA and restart the cycle.
- The final implementation report/chat handoff may quote those run/job IDs, but the repository remains unchanged after the exact-SHA CI pass.

If it is a hard requirement that the terminal CI run IDs themselves be stored in repository-associated metadata without changing the commit SHA, use a separate immutable/ref-level mechanism that does not rewrite the commit tree (for example an annotated tag or release/other external record, if consistent with project conventions). Do not claim that future run IDs can exist inside the commit that triggered them.

### Acceptance clarification requested

Please rewrite spec §2.1 and TODO CC-009.4 so they distinguish:

- repository-resident closure evidence available before the terminal CI run; and
- terminal exact-SHA GitHub run/job metadata produced after that commit exists.

The final acceptance gate should require the latter to be independently confirmed, but should not require another repository mutation to record it.

---

## FQI-002 — Conditional branches still conflict with the global checkbox semantics

### Issue

The TODO's status rule says:

- `[x]` means implemented, documented, tested, and supported by recorded evidence.
- `[ ]` remains incomplete.

Several tasks now intentionally permit mutually exclusive or conditional outcomes, but their checkboxes are still written as though every branch must become `[x]`.

Examples:

### CC-002B

If CC-002A proves the system bars are already correct, CC-002B must not land. In that valid outcome, these checkboxes cannot truthfully be checked:

- production `WindowCompat`/`WindowInsetsControllerCompat`/`enableEdgeToEdge()` call added;
- re-verified after remediation.

Yet leaving them `[ ]` conflicts with the global rule that `[ ]` means incomplete.

### CC-003

The task allows exactly two honest outcomes:

1. a clean seam is built and all three operations receive behavioral tests; or
2. a clean seam is not practical and the parent AR-007 evidence claims are downgraded to match the actual predicate/static evidence.

Those are mutually exclusive dispositions. A valid implementation cannot satisfy every branch-specific checkbox literally.

### CC-004

The task permits a documented-blocker fallback if neither bounded promotion-fixture mechanism is reasonably practical. But CC-009.1 currently requires "CC-004's instrumentation addition passes." If the accepted fallback is used, there is no new instrumentation addition to pass.

### Question

How should a valid conditional/fallback disposition be represented without leaving legitimate `[ ]` boxes that, by the document's own rules, mean the task is incomplete?

### Recommended resolution

Convert each conditional task to a disposition-oriented checklist. For example:

#### CC-002B disposition

- `[ ] CC-002B disposition complete: either remediation was required, landed, and re-verified; or CC-002A proved remediation unnecessary and that no-remediation disposition is recorded with evidence.`

Then place branch-specific details beneath it as prose/evidence fields or explicitly mark one branch `N/A — not required by observed result`, rather than treating mutually exclusive branches as independent mandatory checkboxes.

Apply the same pattern to CC-003 and CC-004.

Also change CC-009.1 from an unconditional "CC-004's instrumentation addition passes" to something equivalent to:

- `CC-004 disposition complete: the end-to-end promotion instrumentation test passes if implemented; otherwise the spec-authorized documented-blocker fallback is fully recorded and accepted.`

The acceptance section should test whether each task reached one valid, evidence-backed disposition, not whether every mutually exclusive branch box is checked.

---

## FQI-003 — CC-005's git equivalence evidence must be path-scoped to the actual claim

### Issue

CC-005 correctly incorporates the earlier criticism that green CI does not prove two trees are source-identical. However, the revised text suggests recording commands such as:

- `git diff --stat 6d9a84d..e9ab0fc`
- `git rev-parse 6d9a84d^{tree} e9ab0fc^{tree}`

The whole repository trees are intentionally not identical: closure documentation, authority-index state, and related metadata changed between those SHAs. Therefore unequal full-tree hashes are expected and do not establish or refute the narrower statement actually being made: that no relevant production source/test files differ between the two validation SHAs.

Likewise, an unrestricted `git diff --stat` may show documentation-only changes but does not by itself make the narrower source/test equality claim as precise as it should be.

### Question

Exactly which paths are intended to be covered by the "no source/test file differs" claim?

### Recommended resolution

Make the comparison explicitly path-scoped to the surfaces whose equality is asserted. For example, if the intended claim is that the Android and Rust product/test surfaces are identical:

```bash
git diff --exit-code 6d9a84d910a3e6438aef390aa733a4b62a71dfdd..e9ab0fc623c22bd372ba9c8c2609dfcf74609f84 -- \
  android-harness \
  crates
```

Adjust the path list to match the precise historical claim rather than adopting these paths mechanically.

Then, separately, if useful, record an unrestricted names-only comparison:

```bash
git diff --name-only 6d9a84d910a3e6438aef390aa733a4b62a71dfdd..e9ab0fc623c22bd372ba9c8c2609dfcf74609f84
```

That can show exactly which documentation/authority files did change.

The evidence should say something precise such as:

> The path-scoped product/test diff is empty; the unrestricted diff contains only the listed closure/documentation/authority files.

Do not use unequal whole-tree hashes as evidence for source/test equality. Full tree hashes answer a different question.

---

## Overall assessment

The updated correction spec/TODO successfully resolved the substance of the earlier twelve-item review: touched-file scope is no longer artificially exhaustive; CC-002 is correctly split into observation and conditional remediation with a concrete runtime evidence contract; CC-003 no longer permits one-operation-by-analogy behavioral claims; CC-004 constrains fixture design; CC-005 no longer treats CI as tree-equivalence proof; provenance preservation and authority closure are explicit; and permanent Android/general-Rust CI is mandatory.

The three items above are the remaining pre-implementation concerns. FQI-001 is the most important because it affects whether final exact-SHA closure can be represented truthfully at all. FQI-002 prevents valid conditional outcomes from appearing permanently incomplete. FQI-003 makes the historical source/test-equivalence claim reproducible and correctly scoped.
