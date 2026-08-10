# Rust Android UI/UX Review-Fix Closure Corrections — Final Follow-Up Questions and Issues — 2026-08-10

**Review target:**
- `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_SPEC_2026-08-10.md`
- `docs/RUST_ANDROID_UI_UX_REVIEW_FIX_CLOSURE_CORRECTIONS_TODO_2026-08-10.md`

**Purpose:** final pre-implementation review after the first twelve QI items and three FQI items were incorporated.

The substantive correction program now looks sound. The remaining items are bookkeeping/specification clarifications that should be resolved before implementation so the TODO can be completed without ambiguity.

---

## FFQI-001 — Define `N/A` formally in the TODO status rules

### Issue

The TODO header currently defines only:

- `[x]` = implemented, documented, tested, and supported by recorded evidence;
- `[ ]` = incomplete.

However, CC-002B, CC-003, and CC-004 now correctly use mutually-exclusive dispositions and instruct the implementer to mark untaken alternatives `N/A`.

Without a formal definition, there is still a bookkeeping ambiguity: CC-009 says every CC-001 through CC-008 task must be `[x]`, while valid untaken branches are neither `[x]` nor `[ ]` under the stated rules.

### Requested clarification

Add an explicit status rule such as:

- `N/A` is permitted only for an explicitly mutually-exclusive branch whose sibling disposition was selected and completed with evidence;
- an `N/A` branch does not make the enclosing CC task incomplete;
- the enclosing disposition checkbox itself must be `[x]` before the task is considered complete.

Prefer writing untaken alternatives as plain `N/A — <reason>` rather than leaving an unchecked checkbox that could be mistaken for unfinished work.

### Question

Can the TODO status rules be updated so `N/A` has precise completion semantics and CC-009's acceptance language clearly treats a task with a valid selected disposition plus `N/A` alternatives as complete?

---

## FFQI-002 — Make the terminal-trigger rule depend on actual workflow execution, not file category

### Issue

Spec §2.1 currently distinguishes the final substantive commit as follows:

- documentation-only -> create one empty, tree-identical trigger commit;
- source/test change -> use the substantive commit itself as the CI trigger.

That leaves a middle case. CC-009 may modify repository files such as:

- `scripts/task_post_port_review_fix_audit.sh`;
- authority/index machinery;
- other non-documentation, non-product/test files.

Such a commit is neither "documentation-only" nor naturally classifiable as an Android/Rust source/test change. Whether both permanent workflows actually trigger is determined by the workflows' path/event configuration, not by our semantic description of the changed files.

### Requested clarification

Replace the file-category rule with an execution-based rule:

1. Finish the final substantive commit containing all repository-resident correction work.
2. Determine whether **both required permanent workflows actually execute against that exact SHA**.
3. If both execute against that SHA, that SHA is the terminal validation SHA; do not create an extra trigger commit.
4. If either required workflow does not execute against that SHA because of path filtering or trigger behavior, create exactly one empty/tree-identical trigger commit whose purpose is to cause both workflows to execute against the unchanged final tree.
5. No repository mutation occurs after that terminal validation SHA.

This removes ambiguity for script/authority-only final changes and directly tests the property the closure protocol actually cares about.

### Question

Can §2.1 be rewritten around actual workflow execution rather than "documentation-only" versus "source/test" classification?

---

## FFQI-003 — Clean up the remaining cross-reference and disposition-dependent wording

### Issue A: incorrect section cross-reference

Spec §2.1 currently says CC-002 is "explicitly two commits — see §6." CC-002 is in §4, while §6 is CC-004.

### Issue B: unconditional CC-004 instrumentation wording

Spec §11.1 initially says to run "the CC-004 instrumentation addition," but CC-004 now legitimately permits a `documented blocker` disposition in which no new instrumentation test is added. Later text in the same section correctly handles this disposition-dependent behavior.

### Requested corrections

- Change the CC-002 cross-reference from `see §6` to `see §4` (or reference CC-002 directly so future renumbering is less brittle).
- Replace unconditional wording such as `the CC-004 instrumentation addition` with `CC-004's disposition-dependent validation` or equivalent wherever it appears.

### Question

Can these wording/cross-reference inconsistencies be cleaned up so the spec has one consistent interpretation of CC-002 and CC-004?

---

## Final assessment

I do not currently see a substantive objection to the correction program itself. Once FFQI-001 through FFQI-003 are resolved, I consider the spec/TODO ready to execute as a bounded Ralph-loop correction pass.