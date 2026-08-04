# Minimized robustness regressions

No Task 23.2 fuzz failure was present when this directory was created.

For every future crash, invariant mismatch, sanitizer report, or differential mismatch:

1. reproduce it with the exact target and artifact;
2. minimize it with `cargo fuzz tmin` or an equivalent deterministic reducer;
3. store it under `fuzz/regressions/<target>/<descriptive-name>`;
4. add a named stable regression test that replays the minimized input;
5. fix the implementation only after the regression fails for the expected reason;
6. retain the minimized input permanently after the fix.

Generated `fuzz/artifacts/` files are transient and must not be treated as the permanent regression corpus.
