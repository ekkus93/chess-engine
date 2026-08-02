from pathlib import Path
import sys

root = Path(sys.argv[1])


def replace_all(path: str, old: str, new: str) -> None:
    target = root / path
    text = target.read_text()
    if old not in text:
        raise SystemExit(f"expected text not found in {path}: {old[:160]!r}")
    target.write_text(text.replace(old, new))


todo = "docs/RUST_CHESS_ENGINE_PORT_TODO_2026-08-01.md"
replace_all(todo, "; The overall Task 15", "; the overall Task 15")
replace_all(todo, "Tasks 15.2–15.5 are complete", "Tasks 15.2–15.6 are complete")
replace_all(todo, "Tasks 15.3–15.5 are complete", "Tasks 15.3–15.6 are complete")
replace_all(todo, "Tasks 15.4–15.5 are complete", "Tasks 15.4–15.6 are complete")
replace_all(
    todo,
    "The public probe and deterministic store boundaries are complete, but production search still does not call them or activate TT move ordering; diagnostics remain Task 15.6 and search integration remains in the overall Task 15 gate.",
    "The public probe, deterministic store, and diagnostics boundaries are complete, but production search still does not call them or activate TT move ordering; integration remains the overall Task 15 gate.",
)
replace_all(
    todo,
    "Deterministic same-key updates and collision replacement are complete, but production search still does not call the probe/store boundaries or activate TT move ordering; diagnostics remain Task 15.6 and search integration remains in the overall Task 15 gate.",
    "Deterministic same-key updates, collision replacement, and diagnostics are complete, but production search still does not call the TT boundaries or activate TT move ordering; integration remains the overall Task 15 gate.",
)
replace_all(
    todo,
    "Diagnostics, hash-full estimation, microbenchmarks, and production search integration remain outside Task 15.5.",
    "Diagnostics, hash-full estimation, and microbenchmarks are complete under Task 15.6; production search integration remains outside Task 15.5 and is the overall Task 15 gate.",
)

ralph = "docs/RUST_CHESS_ENGINE_PORT_RALPH_STATUS.md"
replace_all(
    ralph,
    "Mate normalization, probe semantics, and replacement policy are complete; diagnostics and search integration remain intentionally outside Task 15.2.",
    "Mate normalization, probe semantics, replacement policy, and diagnostics are complete; production search integration remains intentionally outside Task 15.2.",
)
replace_all(
    ralph,
    "Probe semantics and replacement are complete; diagnostics and production search integration remain intentionally outside Task 15.3.",
    "Probe semantics, replacement, and diagnostics are complete; production search integration remains intentionally outside Task 15.3.",
)
replace_all(
    ralph,
    "Deterministic insertion and replacement are complete; diagnostics and production search integration remain intentionally outside Task 15.4.",
    "Deterministic insertion, replacement, and diagnostics are complete; production search integration remains intentionally outside Task 15.4.",
)
replace_all(
    ralph,
    "Diagnostics, hash-full estimation, microbenchmarks, and production search integration remain intentionally outside Task 15.5.",
    "Diagnostics, hash-full estimation, and microbenchmarks are complete under Task 15.6; production search integration remains intentionally outside Task 15.5.",
)
