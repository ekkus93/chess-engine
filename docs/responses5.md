# responses5.md

These are the clarification questions/issues identified while reviewing:

1. **CLI precedence policy lock**
   - The spec allows either:
     - `--no-opening-book` wins, or
     - reject combined flags.
   - Current docs say no-book-wins; please confirm this is the required final behavior.

2. **Falkbeer continuation requirement**
   - Preferred fix is adding `e4d5` to the Falkbeer line.
   - Confirm whether this should be treated as required, or whether omission-with-doc-justification is acceptable for final acceptance.

3. **Strength of required-candidate assertions**
   - Planned test behavior is: required candidate must be included.
   - Confirm whether this is sufficient, or if you want exact candidate-set equality assertions.

4. **Loader error contract**
   - Planned behavior: non-object JSON raises `OpeningBookError` through loader/file-path entrypoints.
   - Confirm whether exact error message text must be pinned, or exception type plus message fragment is enough.

5. **CLI testing style preference**
   - For the `--no-opening-book --opening-book /bad/path` case, confirm preferred test style:
     - function-level/monkeypatch test, or
     - subprocess CLI smoke test.

6. **Task 0 copy-doc subtasks**
   - The final-fix spec/TODO files are already present in the repo.
   - Confirm these subtasks should be marked complete as already satisfied.
