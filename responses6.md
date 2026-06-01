# responses6.md

These are the clarification questions and issues identified while reviewing the AI/test-runtime/repo-hygiene cleanup spec.

1. **`get_best_move()` API cleanup**
   - The spec wants explicit keyword-only opening-book parameters.
   - Do you want the `**kwargs` compatibility path removed entirely, or should I preserve it for any future unrelated keywords?

2. **Generated artifact cleanup**
   - The spec recommends removing `tmp/` generated audit output by default, but also allows documenting intentionally source-controlled artifacts.
   - Should I remove all `tmp/` content from the repo, or preserve any specific files and move/document them elsewhere?

3. **Recursion-limit changes**
   - The spec says to audit `sys.setrecursionlimit(...)` in `ai.py` and `self_play.py`.
   - Do you want those calls removed/reduced if safe, or just documented with a short comment if they must stay?

4. **Slow-test classification scope**
   - The spec says to move expensive depth-4/5, transcript-style, and multi-second tests to `slow`.
   - Please confirm there are no fast-test exceptions you want preserved even if they take multiple seconds.

5. **Pytest config cleanup**
   - The spec points at possible global `-v` / verbose pytest defaults in config.
   - Should I remove any global verbose default unconditionally if present, or preserve it if there is a repo-wide reason?

6. **Task 0 copy-doc subtasks**
   - The final-fix docs already exist in the repo.
   - Please confirm that Task 0’s copy-doc subtasks should simply be marked complete rather than re-copying files.
